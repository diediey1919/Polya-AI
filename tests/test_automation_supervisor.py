"""
Isolated Test Suite for Polya C5 Supervisor (TASK AUTO-ORCH-2B).

Covers:
- Dual supervisor concurrency & single-instance lock prevention
- Lease active, expiration, and collision handling
- Stale fencing token & crashed worker recovery
- Dependency DAG enforcement
- Retry limits and loop termination
- Awaiting approval and production state protection (AuthorizationBoundary)
- Git dirty working tree execution blocking
- No runnable jobs handling
- CLI modes: --status, --dry-run, --once, --help
- Production DB integrity verification
"""

import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.automation.controller import AutomationController
from orchestrator.automation.git_guard import GitGuard, GitIdentity
from orchestrator.automation.job_definition import JobDefinition, ProjectIdentity
from orchestrator.automation.job_pipeline import (
    AuditReport,
    CheckResult,
    JobExecutionResult,
    JobPipeline,
    StageResult,
    StructuredPlan,
    VerificationBundle,
)
from orchestrator.automation.job_store import DatabaseManager, JobStore, LeaseLockStore
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import JobState
from orchestrator.automation.supervisor import (
    SingleInstanceLock,
    Supervisor,
    SupervisorConfig,
    main,
)


@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "test_supervisor.db"
    return str(db_file)


@pytest.fixture
def temp_repo_dir(tmp_path):
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    return str(repo_dir)


@pytest.fixture
def mock_pipeline():
    pipe = MagicMock(spec=JobPipeline)
    pipe.run_job.return_value = JobExecutionResult(
        job_id="test_job",
        status=JobState.READY_FOR_APPROVAL,
        definition_hash="def_hash_abc",
        audit_report=MagicMock(spec=AuditReport),
        plan=MagicMock(spec=StructuredPlan),
        agent_result={"status": "ok"},
        verification=MagicMock(spec=VerificationBundle),
        stage_results=[],
        error=None,
    )
    return pipe


def create_test_job(
    store: JobStore,
    job_id: str,
    state: JobState = JobState.PLANNING,
    commit_sha: str = "abc1234",
    plan_hash: str = "plan_hash_1",
    config_hash: str = "cfg_hash_1",
) -> AutomationJob:
    job = AutomationJob(
        job_id=job_id,
        commit_sha=commit_sha,
        plan_hash=plan_hash,
        config_hash=config_hash,
        state=state,
        created_at="2026-10-09T00:00:00Z",
        created_by="test_harness",
    )
    return store.create_job(job)


# 1. Single Instance Lock Test
def test_single_instance_lock(tmp_path):
    lock_file = str(tmp_path / "sup.lock")
    lock1 = SingleInstanceLock(lock_file)
    lock2 = SingleInstanceLock(lock_file)

    assert lock1.acquire() is True
    assert lock2.acquire() is False

    lock1.release()
    assert lock2.acquire() is True
    lock2.release()


# 2. Concurrency Lease between two supervisors
def test_two_supervisors_concurrent_lease(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg1 = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_1")
    cfg2 = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_2")

    s1 = Supervisor(config=cfg1, job_pipeline=mock_pipeline)
    s2 = Supervisor(config=cfg2, job_pipeline=mock_pipeline)

    job = create_test_job(s1.job_store, "job_concurrent")

    # Worker 1 acquires lease
    assert s1.lease_store.acquire_lease(job.job_id, "sup_1", ttl_seconds=60.0) is True

    # Worker 2 should see it locked and not runnable
    runnable, blocked = s2.filter_runnable_jobs()
    assert len(runnable) == 0
    assert any("Active lease held" in reason for _, reason in blocked)

    # Release lease from Worker 1
    s1.lease_store.release_lease(job.job_id, "sup_1")

    # Now Worker 2 sees it runnable
    runnable, _ = s2.filter_runnable_jobs()
    assert len(runnable) == 1
    assert runnable[0].job_id == job.job_id


# 3. Stale lease expiration allows takeover
def test_stale_lease_takeover(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_taker")
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)

    job = create_test_job(s.job_store, "job_stale")

    # Acquired with 0.01s TTL
    s.lease_store.acquire_lease(job.job_id, "old_dead_worker", ttl_seconds=0.01)

    import time
    time.sleep(0.05)

    # Dead worker lease is expired, current worker can take over
    assert s.lease_store.acquire_lease(job.job_id, "sup_taker", ttl_seconds=60.0) is True
    s.lease_store.release_lease(job.job_id, "sup_taker")


# 4. Crash recovery recovers orphaned intermediate jobs
def test_crash_recovery(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_main")
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)

    job = create_test_job(s.job_store, "job_crashed", state=JobState.PLANNING)
    s.job_store.transition_state(job.job_id, JobState.RUNNING, worker_id="crashed_worker")

    # Orphaned job in RUNNING without lease
    recovered_count = s.recover_crashed_jobs()
    assert recovered_count == 1

    updated_job = s.job_store.get_job(job.job_id)
    assert updated_job is not None
    assert updated_job.state == JobState.FAILED


# 5. DAG dependency enforcement
def test_dag_dependency_enforcement(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_dag")
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)

    parent_job = create_test_job(s.job_store, "parent_task", state=JobState.PLANNING)
    child_job = create_test_job(s.job_store, "child_task", state=JobState.PLANNING)

    child_def = JobDefinition(
        job_id="child_task",
        project=ProjectIdentity(name="polya", repository="Polya-AI", branch="main"),
        base_commit_sha="abc1234",
        target="child_target",
        task="Child task needing parent",
    )
    # inject dependencies attribute dynamically
    setattr(child_def, "dependencies", ["parent_task"])
    s.register_job_definition(child_def)

    # Child should be blocked because parent is not COMPLETED
    runnable, blocked = s.filter_runnable_jobs()
    runnable_ids = [j.job_id for j in runnable]
    assert "parent_task" in runnable_ids
    assert "child_task" not in runnable_ids

    # Once parent completes, child becomes runnable
    s.job_store.transition_state("parent_task", JobState.RUNNING)
    s.job_store.transition_state("parent_task", JobState.VERIFYING)
    s.job_store.transition_state("parent_task", JobState.READY_FOR_APPROVAL)
    s.job_store.transition_state("parent_task", JobState.APPROVED)
    s.job_store.transition_state("parent_task", JobState.PRODUCTION_EXECUTION)
    s.job_store.transition_state("parent_task", JobState.PRODUCTION_VERIFICATION)
    s.job_store.transition_state("parent_task", JobState.COMPLETED)

    runnable_after, _ = s.filter_runnable_jobs()
    assert "child_task" in [j.job_id for j in runnable_after]


# 6. Retry limits & circuit breaker
def test_max_retries_circuit_breaker(temp_db_path, temp_repo_dir):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_retry", max_retries=2)
    failing_pipeline = MagicMock(spec=JobPipeline)
    failing_pipeline.run_job.return_value = JobExecutionResult(
        job_id="failing_job",
        status=JobState.FAILED,
        definition_hash="def_failed",
        audit_report=MagicMock(spec=AuditReport),
        plan=MagicMock(spec=StructuredPlan),
        agent_result=None,
        verification=None,
        stage_results=[],
        error="Simulation error",
    )

    s = Supervisor(config=cfg, job_pipeline=failing_pipeline)
    with patch.object(
        s.git_guard,
        "get_current_identity",
        return_value=GitIdentity(commit_sha="a" * 40, branch="main", is_dirty=False),
    ):
        job = create_test_job(s.job_store, "failing_job")

        # Cycle 1
        s.run_cycle()
        assert s._retry_counts["failing_job"] == 1

        # Cycle 2
        s.run_cycle()
        assert s._retry_counts["failing_job"] == 2

        # Cycle 3: Exceeds max_retries, now blocked
        runnable, blocked = s.filter_runnable_jobs()
        assert len(runnable) == 0
        assert any("Max retries" in r for _, r in blocked)


# 7. Non-runnable states: READY_FOR_APPROVAL, APPROVED, PRODUCTION_EXECUTION
def test_approval_and_production_protection(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir)
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)

    j_approval = create_test_job(s.job_store, "job_approval", state=JobState.READY_FOR_APPROVAL)
    j_prod = create_test_job(s.job_store, "job_prod", state=JobState.PRODUCTION_EXECUTION)

    runnable, blocked = s.filter_runnable_jobs()
    assert len(runnable) == 0
    blocked_reasons = {b[0].job_id: b[1] for b in blocked}
    assert "Awaiting manual human approval" in blocked_reasons["job_approval"]
    assert "Production state requires manual operator execution" in blocked_reasons["job_prod"]


# 8. Git dirty worktree blocks execution
def test_git_dirty_blocks_execution(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir)
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)
    job = create_test_job(s.job_store, "job_dirty")

    with patch.object(
        s.git_guard,
        "get_current_identity",
        return_value=GitIdentity(commit_sha="a" * 40, branch="main", is_dirty=True),
    ):
        result = s.execute_job(job)
        assert result.status == JobState.FAILED
        assert result.error is not None and "Git worktree dirty" in result.error
        updated_job = s.job_store.get_job(job.job_id)
        assert updated_job is not None
        assert updated_job.state == JobState.FAILED


# 10. Fencing: a worker whose lease was stolen mid-execution must discard its result
def test_fencing_discards_result_after_takeover(temp_db_path, temp_repo_dir):
    cfg = SupervisorConfig(
        db_path=temp_db_path,
        repo_path=temp_repo_dir,
        worker_id="sup_stale",
        lease_ttl=60.0,
    )
    steal_pipeline = MagicMock(spec=JobPipeline)

    def _steal_then_succeed(job_def, worker_id="x"):
        # Simulate a slow pipeline during which a new worker takes over the expired lease.
        other = LeaseLockStore(s.db_manager, default_lease_ttl=60.0)
        with s.db_manager._get_connection() as conn:
            conn.execute(
                "UPDATE automation_job_leases SET worker_id = ?, expires_at = ? WHERE job_id = ?",
                ("sup_newcomer", time.time() + 300.0, job_def.job_id),
            )
        steal_pipeline.run_job.return_value = JobExecutionResult(
            job_id=job_def.job_id,
            status=JobState.READY_FOR_APPROVAL,
            definition_hash="def_stale",
            audit_report=MagicMock(spec=AuditReport),
            plan=MagicMock(spec=StructuredPlan),
            agent_result={"status": "ok"},
            verification=MagicMock(spec=VerificationBundle),
            stage_results=[],
            error=None,
        )
        return steal_pipeline.run_job.return_value

    steal_pipeline.run_job.side_effect = _steal_then_succeed

    s = Supervisor(config=cfg, job_pipeline=steal_pipeline)
    job = create_test_job(s.job_store, "job_fenced")

    with patch.object(
        s.git_guard,
        "get_current_identity",
        return_value=GitIdentity(commit_sha="a" * 40, branch="main", is_dirty=False),
    ):
        result = s.execute_job(job)

    assert result.status == JobState.ABORTED
    assert result.definition_hash == "fence_lost"
    assert result.error is not None and "fencing" in result.error.lower()
    # No retry accounting should be applied for a fenced-off execution
    assert "job_fenced" not in s._retry_counts


# 11. Heartbeat thread actually renews the lease during a long pipeline run
def test_heartbeat_renews_lease_during_pipeline(temp_db_path, temp_repo_dir):
    cfg = SupervisorConfig(
        db_path=temp_db_path,
        repo_path=temp_repo_dir,
        worker_id="sup_hb",
        lease_ttl=1.0,
        heartbeat_interval=0.05,
    )
    observed = {}

    slow_pipeline = MagicMock(spec=JobPipeline)

    def _run_and_probe(job_def, worker_id="x"):
        time.sleep(0.35)
        with s.db_manager._get_connection() as conn:
            row = conn.execute(
                "SELECT worker_id, expires_at FROM automation_job_leases WHERE job_id = ?",
                (job_def.job_id,),
            ).fetchone()
        observed["worker_id"] = row["worker_id"]
        observed["expires_at"] = row["expires_at"]
        observed["now"] = time.time()
        return JobExecutionResult(
            job_id=job_def.job_id,
            status=JobState.READY_FOR_APPROVAL,
            definition_hash="def_hb",
            audit_report=MagicMock(spec=AuditReport),
            plan=MagicMock(spec=StructuredPlan),
            agent_result={"status": "ok"},
            verification=MagicMock(spec=VerificationBundle),
            stage_results=[],
            error=None,
        )

    slow_pipeline.run_job.side_effect = _run_and_probe

    s = Supervisor(config=cfg, job_pipeline=slow_pipeline)
    job = create_test_job(s.job_store, "job_hb")

    with patch.object(
        s.git_guard,
        "get_current_identity",
        return_value=GitIdentity(commit_sha="a" * 40, branch="main", is_dirty=False),
    ):
        result = s.execute_job(job)

    assert result.status == JobState.READY_FOR_APPROVAL
    assert observed["worker_id"] == "sup_hb"
    # Lease must still be live at the end of a pipeline running longer than the original TTL
    assert observed["expires_at"] > observed["now"], "Heartbeat did not renew the lease during execution"


# 12. Retry limit is persistent across supervisor instances (no unbounded repeat loops)
def test_retry_limit_is_persistent_across_supervisors(temp_db_path, temp_repo_dir):
    from orchestrator.automation.models import ExecutionRecord
    from orchestrator.automation.states import ExecutionPhase, ExecutionStatus

    cfg = SupervisorConfig(
        db_path=temp_db_path,
        repo_path=temp_repo_dir,
        worker_id="sup_fresh",
        max_retries=2,
    )
    s = Supervisor(config=cfg, job_pipeline=MagicMock(spec=JobPipeline))
    job = create_test_job(s.job_store, "job_persist_retry")

    # Simulate a previous supervisor process that already recorded 2 failed RUNNING attempts.
    for i in range(2):
        exec_id = f"exec_prev_{i}"
        s.execution_store.record_start(
            ExecutionRecord(
                execution_id=exec_id,
                job_id=job.job_id,
                phase=ExecutionPhase.RUNNING,
                started_at=f"2026-10-09T00:00:0{i}Z",
                status=ExecutionStatus.STARTED,
                worker_id="sup_previous",
            )
        )
        s.execution_store.record_completion(
            exec_id,
            ExecutionStatus.FAILED,
            error_summary="previous failure",
            authorized_by="human_operator",
        )

    runnable, blocked = s.filter_runnable_jobs()
    assert len(runnable) == 0, "A brand new supervisor instance bypassed the persisted retry limit"
    assert any("Max retries" in reason for _, reason in blocked)


# 13. Crash recovery must NOT steal a job whose lease is still actively held
def test_recovery_does_not_steal_active_job(temp_db_path, temp_repo_dir, mock_pipeline):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_other")
    s = Supervisor(config=cfg, job_pipeline=mock_pipeline)

    job = create_test_job(s.job_store, "job_active", state=JobState.PLANNING)
    s.job_store.transition_state(job.job_id, JobState.RUNNING, worker_id="live_worker")
    assert s.lease_store.acquire_lease(job.job_id, "live_worker", ttl_seconds=300.0) is True

    recovered = s.recover_crashed_jobs()
    assert recovered == 0, "Recovery wrongly took over a job still owned by a live worker"

    still = s.job_store.get_job(job.job_id)
    assert still is not None
    assert still.state == JobState.RUNNING


# 14. Supervisor never transitions a job to READY_FOR_APPROVAL or production on its own
def test_supervisor_never_auto_advances_to_production(temp_db_path, temp_repo_dir):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir, worker_id="sup_prod_guard")
    s = Supervisor(config=cfg, job_pipeline=MagicMock(spec=JobPipeline))

    # Walk each job forward to the states that require human authorization
    j_ready = create_test_job(s.job_store, "job_ready_for_approval", state=JobState.PLANNING)
    s.job_store.transition_state(j_ready.job_id, JobState.RUNNING)
    s.job_store.transition_state(j_ready.job_id, JobState.VERIFYING)
    s.job_store.transition_state(j_ready.job_id, JobState.READY_FOR_APPROVAL)

    j_approved = create_test_job(s.job_store, "job_approved", state=JobState.PLANNING)
    s.job_store.transition_state(j_approved.job_id, JobState.RUNNING)
    s.job_store.transition_state(j_approved.job_id, JobState.VERIFYING)
    s.job_store.transition_state(j_approved.job_id, JobState.READY_FOR_APPROVAL)
    s.job_store.transition_state(j_approved.job_id, JobState.APPROVED)

    runnable, blocked = s.filter_runnable_jobs()
    assert len(runnable) == 0, f"Human-gated jobs were treated as runnable: {[j.job_id for j in runnable]}"
    blocked_ids = {j.job_id for j, _ in blocked}
    assert {"job_ready_for_approval", "job_approved"} <= blocked_ids

    # And the ApprovalStore must be untouched by supervisor scheduling
    assert s.approval_store.get_approval_for_job("job_approved") is None


def test_dry_run_is_zero_mutation(temp_db_path, temp_repo_dir):
    cfg = SupervisorConfig(db_path=temp_db_path, repo_path=temp_repo_dir)
    mock_pipe = MagicMock(spec=JobPipeline)
    s = Supervisor(config=cfg, job_pipeline=mock_pipe)

    job = create_test_job(s.job_store, "dry_job_1", state=JobState.PLANNING)
    executed = s.run_cycle(dry_run=True)
    assert executed == 1

    # Database state must remain PLANNING
    db_job = s.job_store.get_job("dry_job_1")
    assert db_job is not None
    assert db_job.state == JobState.PLANNING

    # Lease must not be acquired or left behind
    assert not s.lease_store.is_locked_by_other("dry_job_1", "someone_else")

    # Pipeline must never be called during dry run
    mock_pipe.run_job.assert_not_called()


# 9. CLI arguments and exit codes
def test_cli_interface(temp_db_path, temp_repo_dir):
    # --status
    code = main(["--status", f"--db-path={temp_db_path}", f"--repo-path={temp_repo_dir}"])
    assert code == 0

    # --dry-run
    code = main(["--dry-run", f"--db-path={temp_db_path}", f"--repo-path={temp_repo_dir}"])
    assert code == 0

    # --once with no jobs
    code = main(["--once", f"--db-path={temp_db_path}", f"--repo-path={temp_repo_dir}"])
    assert code == 0
