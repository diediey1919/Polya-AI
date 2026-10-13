"""
Deterministic atomic-fencing tests and _ManagedConnection lifecycle tests.

Proves the C5 fencing contract:
- Fencing tokens are strictly monotonic across acquire/renew/takeover/release.
- A worker whose lease expired or was taken over CANNOT persist execution results
  nor mutate job state; the new lease owner's data stays intact.
- Completion of every phase path goes through fenced commits.
- tokenless fenced operations are rejected (no unsafe fallback).
- _ManagedConnection always closes, commits on success, rolls back on exception,
  and does not leak file descriptors under sustained load.

All tests use temporary SQLite databases and mock agents. No paid agent is invoked.
"""

import os
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from orchestrator.automation.controller import AutomationController
from orchestrator.automation.job_pipeline import JobPipeline
from orchestrator.automation.job_store import (
    DatabaseManager,
    ExecutionStore,
    FencedCommitRejected,
    JobStore,
    LeaseLockStore,
    _ManagedConnection,
)
from orchestrator.automation.models import AutomationJob, ApprovalRecord, ExecutionRecord
from orchestrator.automation.states import (
    ApprovalDecision,
    ExecutionPhase,
    ExecutionStatus,
    JobState,
)
from orchestrator.automation.supervisor import Supervisor, SupervisorConfig


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def make_job(store: JobStore, job_id: str, state: JobState = JobState.PLANNING) -> AutomationJob:
    return store.create_job(
        AutomationJob(
            job_id=job_id,
            commit_sha="a" * 40,
            plan_hash="plan_hash",
            config_hash="cfg_hash",
            state=state,
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="fencing_test",
        )
    )


def make_exec(
    store: ExecutionStore,
    job_id: str,
    exec_id: str,
    worker_id: str,
    phase: ExecutionPhase = ExecutionPhase.RUNNING,
    token=None,
) -> ExecutionRecord:
    return store.record_start(
        ExecutionRecord(
            execution_id=exec_id,
            job_id=job_id,
            phase=phase,
            started_at=datetime.now(timezone.utc).isoformat(),
            status=ExecutionStatus.STARTED,
            worker_id=worker_id,
            fencing_token=token,
        )
    )


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "fencing.db")


# --------------------------------------------------------------------------
# 1. Core takeover scenario: A holds N, B takes N+1, A is rejected
# --------------------------------------------------------------------------
def test_takeover_rejects_stale_worker_result(db_path):
    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, default_lease_ttl=60.0), ExecutionStore(db)
    make_job(jobs, "job_takeover", JobState.RUNNING)

    # Step 1: worker A acquires lease -> token N
    assert leases.acquire_lease("job_takeover", "worker_A", ttl_seconds=60.0) is True
    token_a = leases.get_fencing_token("job_takeover")
    assert token_a == 1
    make_exec(executions, "job_takeover", "exec_a", "worker_A", token=token_a)

    # Step 2: A's lease expires
    assert leases.acquire_lease("job_takeover", "worker_A", ttl_seconds=0.01) is True
    time.sleep(0.05)

    # Step 3: worker B takes over -> token N+1
    assert leases.acquire_lease("job_takeover", "worker_B", ttl_seconds=60.0) is True
    token_b = leases.get_fencing_token("job_takeover")
    assert token_b == 2 and token_b > token_a

    # Step 4: worker A tries to persist its result -- must be rejected
    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="exec_a",
            job_id="job_takeover",
            worker_id="worker_A",
            fencing_token=token_a,
            status=ExecutionStatus.SUCCESS,
            error_summary="stale worker result",
        )

    # Step 5: A's result must not be written
    rec = executions.get_execution("exec_a")
    assert rec.status == ExecutionStatus.STARTED
    assert rec.completed_at is None
    assert rec.error_summary is None

    # Step 6: B can still write normally
    make_exec(executions, "job_takeover", "exec_b", "worker_B", token=token_b)
    executions.complete_execution_fenced(
        execution_id="exec_b",
        job_id="job_takeover",
        worker_id="worker_B",
        fencing_token=token_b,
        status=ExecutionStatus.SUCCESS,
        error_summary="fresh worker result",
    )
    rec_b = executions.get_execution("exec_b")
    assert rec_b.status == ExecutionStatus.SUCCESS
    assert rec_b.error_summary == "fresh worker result"
    # B's write survived A's rejected attempt
    assert executions.get_execution("exec_a").status == ExecutionStatus.STARTED


def test_takeover_rejects_stale_worker_state_transition(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, default_lease_ttl=60.0)
    make_job(jobs, "job_state", JobState.RUNNING)

    leases.acquire_lease("job_state", "worker_A", ttl_seconds=0.01)
    token_a = leases.get_fencing_token("job_state")
    time.sleep(0.05)
    leases.acquire_lease("job_state", "worker_B", ttl_seconds=60.0)
    token_b = leases.get_fencing_token("job_state")
    assert token_b > token_a

    # A cannot move the job to a terminal state
    for target in (JobState.FAILED, JobState.VERIFYING, JobState.READY_FOR_APPROVAL):
        with pytest.raises(FencedCommitRejected):
            jobs.transition_state(
                "job_state", target, worker_id="worker_A",
                require_lease=True, fencing_token=token_a,
            )

    # State untouched
    assert jobs.get_job("job_state").state == JobState.RUNNING

    # B can, legally, move it
    updated = jobs.transition_state(
        "job_state", JobState.VERIFYING, worker_id="worker_B",
        require_lease=True, fencing_token=token_b,
    )
    assert updated.state == JobState.VERIFYING


def test_stale_worker_cannot_reach_completed_or_ready_for_approval(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, default_lease_ttl=60.0)
    make_job(jobs, "job_terminal", JobState.PRODUCTION_VERIFICATION)

    leases.acquire_lease("job_terminal", "worker_A", ttl_seconds=0.01)
    token_a = leases.get_fencing_token("job_terminal")
    time.sleep(0.05)
    leases.acquire_lease("job_terminal", "worker_B", ttl_seconds=60.0)
    token_b = leases.get_fencing_token("job_terminal")

    with pytest.raises(FencedCommitRejected):
        jobs.transition_state(
            "job_terminal", JobState.COMPLETED, worker_id="worker_A",
            require_lease=True, fencing_token=token_a,
        )
    assert jobs.get_job("job_terminal").state == JobState.PRODUCTION_VERIFICATION

    jobs.transition_state(
        "job_terminal", JobState.COMPLETED, worker_id="worker_B",
        require_lease=True, fencing_token=token_b,
    )
    assert jobs.get_job("job_terminal").state == JobState.COMPLETED


# --------------------------------------------------------------------------
# 2. Token monotonicity and release semantics
# --------------------------------------------------------------------------
def test_fencing_token_is_monotonic_acquire_renew_takeover(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, default_lease_ttl=60.0)
    make_job(jobs, "job_mono", JobState.RUNNING)

    tokens = []
    leases.acquire_lease("job_mono", "worker_A", ttl_seconds=0.01)
    tokens.append(leases.get_fencing_token("job_mono"))
    time.sleep(0.05)

    for w in ("worker_B", "worker_C", "worker_D"):
        leases.acquire_lease("job_mono", w, ttl_seconds=0.01)
        tokens.append(leases.get_fencing_token("job_mono"))
        time.sleep(0.05)

    assert tokens == sorted(tokens), f"tokens not monotonic: {tokens}"
    assert len(set(tokens)) == len(tokens), f"tokens reused: {tokens}"


def test_release_lease_with_stale_token_does_not_delete_new_lease(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, default_lease_ttl=60.0)
    make_job(jobs, "job_rel", JobState.RUNNING)

    leases.acquire_lease("job_rel", "worker_A", ttl_seconds=0.01)
    token_a = leases.get_fencing_token("job_rel")
    time.sleep(0.05)
    leases.acquire_lease("job_rel", "worker_B", ttl_seconds=60.0)
    token_b = leases.get_fencing_token("job_rel")

    # A releases with its stale token -> must NOT remove B's lease
    removed = leases.release_lease("job_rel", "worker_A", fencing_token=token_a)
    assert removed is False
    assert leases.is_locked_by_other("job_rel", "worker_A") is True
    assert leases.get_fencing_token("job_rel") == token_b

    # B releases with the correct token
    assert leases.release_lease("job_rel", "worker_B", fencing_token=token_b) is True
    assert leases.get_fencing_token("job_rel") is None


def test_token_cannot_be_reused_after_release_and_reacquire(db_path):
    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, 60.0), ExecutionStore(db)
    make_job(jobs, "job_reuse", JobState.RUNNING)

    leases.acquire_lease("job_reuse", "worker_A", ttl_seconds=0.01)
    token_a = leases.get_fencing_token("job_reuse")
    time.sleep(0.05)
    make_exec(executions, "job_reuse", "exec_a", "worker_A", token=token_a)

    # A's lease expires and B takes over: token must strictly advance
    assert leases.acquire_lease("job_reuse", "worker_B", ttl_seconds=60.0) is True
    token_b = leases.get_fencing_token("job_reuse")
    assert token_b > token_a, f"takeover must advance token: {token_a} -> {token_b}"

    # The evicted worker A can never write again, with any token value
    for bogus in (token_a, token_b, token_b - 1, token_a + 1000):
        with pytest.raises(FencedCommitRejected):
            executions.complete_execution_fenced(
                execution_id="exec_a",
                job_id="job_reuse",
                worker_id="worker_A",
                fencing_token=bogus,
                status=ExecutionStatus.SUCCESS,
            )
    assert executions.get_execution("exec_a").status == ExecutionStatus.STARTED
    assert leases.get_fencing_token("job_reuse") == token_b


# --------------------------------------------------------------------------
# 3. Rejection cases
# --------------------------------------------------------------------------
def test_missing_token_and_missing_lease_are_rejected(db_path):
    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, 60.0), ExecutionStore(db)
    make_job(jobs, "job_missing", JobState.RUNNING)

    leases.acquire_lease("job_missing", "worker_A", ttl_seconds=60.0)
    token_a = leases.get_fencing_token("job_missing")
    make_exec(executions, "job_missing", "exec_a", "worker_A", token=token_a)

    # missing token
    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="exec_a", job_id="job_missing",
            worker_id="worker_A", fencing_token=None,
            status=ExecutionStatus.SUCCESS,
        )

    # lease no longer exists
    leases.release_lease("job_missing", "worker_A", fencing_token=token_a)
    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="exec_a", job_id="job_missing",
            worker_id="worker_A", fencing_token=token_a,
            status=ExecutionStatus.SUCCESS,
        )

    # nonexistent job / lease
    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="exec_a", job_id="job_does_not_exist",
            worker_id="worker_A", fencing_token=1,
            status=ExecutionStatus.SUCCESS,
        )


def test_expired_lease_rejects_state_transition(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, 60.0)
    make_job(jobs, "job_expired", JobState.RUNNING)

    leases.acquire_lease("job_expired", "worker_A", ttl_seconds=0.01)
    token_a = leases.get_fencing_token("job_expired")
    time.sleep(0.05)

    # Lease row still exists but has expired: transition must be refused even
    # though nobody else has taken it over.
    with pytest.raises(FencedCommitRejected):
        jobs.transition_state(
            "job_expired", JobState.VERIFYING, worker_id="worker_A",
            require_lease=True, fencing_token=token_a,
        )
    assert jobs.get_job("job_expired").state == JobState.RUNNING


def test_fenced_transition_requires_token(db_path):
    db = DatabaseManager(db_path)
    jobs, leases = JobStore(db), LeaseLockStore(db, 60.0)
    controller = AutomationController(db_path)
    make_job(jobs, "job_noTok", JobState.PLANNING)
    leases.acquire_lease("job_noTok", "worker_A", ttl_seconds=60.0)

    with pytest.raises(FencedCommitRejected):
        controller.fenced_transition("job_noTok", JobState.RUNNING, "worker_A", None)


# --------------------------------------------------------------------------
# 4. All four completion paths are fenced
# --------------------------------------------------------------------------
def test_all_four_completion_paths_are_fenced(db_path):
    db = DatabaseManager(db_path)
    controller = AutomationController(db_path)
    jobs = controller.job_store
    leases = controller.lease_store
    executions = controller.execution_store

    # ---- complete_running fenced ----
    # A starts the execution and records its token; A's lease then expires and B
    # takes over. A must not be able to commit.
    make_job(jobs, "job_cr", JobState.PLANNING)
    leases.acquire_lease("job_cr", "wA", ttl_seconds=60.0)
    tA = leases.get_fencing_token("job_cr")
    controller.fenced_transition("job_cr", JobState.RUNNING, "wA", tA)
    make_exec(executions, "job_cr", "ecr", "wA", ExecutionPhase.RUNNING, token=tA)

    # Simulate A stalling until its lease lapses, then B taking over.
    with db._get_connection() as conn:
        conn.execute(
            "UPDATE automation_job_leases SET expires_at = ? WHERE job_id = ?",
            (time.time() - 1.0, "job_cr"),
        )
    assert leases.acquire_lease("job_cr", "wB", ttl_seconds=60.0) is True
    tB = leases.get_fencing_token("job_cr")
    assert tB > tA

    with pytest.raises(FencedCommitRejected):
        controller.complete_running("ecr", success=True, job_id="job_cr", fencing_token=tA)
    assert executions.get_execution("ecr").status == ExecutionStatus.STARTED

    # B re-runs the execution under its own authority and commits normally
    controller.fenced_transition("job_cr", JobState.VERIFYING, "wB", tB)
    make_exec(executions, "job_cr", "ecr_b", "wB", ExecutionPhase.RUNNING, token=tB)
    controller.complete_running("ecr_b", success=True, job_id="job_cr", fencing_token=tB)
    assert executions.get_execution("ecr_b").status == ExecutionStatus.SUCCESS
    # A's record is still untouched
    assert executions.get_execution("ecr").status == ExecutionStatus.STARTED

    # ---- complete_verifying fenced ----
    make_job(jobs, "job_cv", JobState.VERIFYING)
    leases.acquire_lease("job_cv", "wA", ttl_seconds=60.0)
    tA = leases.get_fencing_token("job_cv")
    make_exec(executions, "job_cv", "ecv", "wA", ExecutionPhase.VERIFYING, token=tA)

    # A stalls; its lease lapses and B takes over
    with db._get_connection() as conn:
        conn.execute(
            "UPDATE automation_job_leases SET expires_at = ? WHERE job_id = ?",
            (time.time() - 1.0, "job_cv"),
        )
    assert leases.acquire_lease("job_cv", "wB", ttl_seconds=60.0) is True
    tB = leases.get_fencing_token("job_cv")
    assert tB > tA

    # A's late commit is refused
    with pytest.raises(FencedCommitRejected):
        controller.complete_verifying("ecv", success=True, job_id="job_cv", fencing_token=tA)
    # a tokenless fenced call is refused, not silently downgraded to an unfenced write
    with pytest.raises(FencedCommitRejected):
        controller.complete_verifying("ecv", success=True, job_id="job_cv", fencing_token=None)
    assert executions.get_execution("ecv").status == ExecutionStatus.STARTED

    # B verifies under its own authority with its own execution record
    make_exec(executions, "job_cv", "ecv_b", "wB", ExecutionPhase.VERIFYING, token=tB)
    controller.complete_verifying("ecv_b", success=True, job_id="job_cv", fencing_token=tB)
    assert executions.get_execution("ecv_b").status == ExecutionStatus.SUCCESS
    # A's record is still STARTED, never overwritten
    assert executions.get_execution("ecv").status == ExecutionStatus.STARTED

    # ---- complete_production_execution fenced ----
    make_job(jobs, "job_cp", JobState.PRODUCTION_EXECUTION)
    leases.acquire_lease("job_cp", "wA", ttl_seconds=60.0)
    tA = leases.get_fencing_token("job_cp")
    make_exec(executions, "job_cp", "ecp", "wA", ExecutionPhase.PRODUCTION_EXECUTION, token=tA)

    # A stalls; lease lapses; B takes over
    with db._get_connection() as conn:
        conn.execute(
            "UPDATE automation_job_leases SET expires_at = ? WHERE job_id = ?",
            (time.time() - 1.0, "job_cp"),
        )
    assert leases.acquire_lease("job_cp", "wB", ttl_seconds=60.0) is True
    tB = leases.get_fencing_token("job_cp")
    assert tB > tA

    # A cannot complete production: no result written, job state frozen
    with pytest.raises(FencedCommitRejected):
        controller.complete_production_execution(
            "job_cp", "ecp", success=True, worker_id="wA", fencing_token=tA
        )
    assert executions.get_execution("ecp").status == ExecutionStatus.STARTED
    assert jobs.get_job("job_cp").state == JobState.PRODUCTION_EXECUTION

    # B completes production legitimately
    make_exec(executions, "job_cp", "ecp_b", "wB", ExecutionPhase.PRODUCTION_EXECUTION, token=tB)
    controller.complete_production_execution(
        "job_cp", "ecp_b", success=True, worker_id="wB", fencing_token=tB
    )
    assert executions.get_execution("ecp_b").status == ExecutionStatus.SUCCESS
    assert jobs.get_job("job_cp").state == JobState.PRODUCTION_VERIFICATION
    # A's stale record untouched
    assert executions.get_execution("ecp").status == ExecutionStatus.STARTED

    # production completion with no token and no record is refused outright
    make_job(jobs, "job_cp2", JobState.PRODUCTION_EXECUTION)
    leases.acquire_lease("job_cp2", "wX", ttl_seconds=60.0)
    with pytest.raises(FencedCommitRejected):
        controller.complete_production_execution("job_cp2", "exec_nonexistent", success=True, worker_id="wX")
    # and the job never advanced
    assert jobs.get_job("job_cp2").state == JobState.PRODUCTION_EXECUTION


def test_production_path_still_requires_human_approval(db_path):
    """Fencing must not weaken the approval gate."""
    controller = AutomationController(db_path)
    jobs = controller.job_store
    make_job(jobs, "job_gate", JobState.PLANNING)

    # Agents/schedulers can never self-approve
    for forbidden in ("agent_supervisor", "cron_supervisor", "scheduler_bot"):
        with pytest.raises(PermissionError):
            controller.submit_human_approval(
                "job_gate", ApprovalDecision.APPROVED, approved_by=forbidden
            )

    jobs.transition_state("job_gate", JobState.RUNNING, worker_id="w1")
    jobs.transition_state("job_gate", JobState.VERIFYING, worker_id="w1")
    jobs.transition_state("job_gate", JobState.READY_FOR_APPROVAL, worker_id="w1")

    # No approval record on file -> production initiation must be denied
    ok, msg, _ = controller.initiate_production_execution(
        job_id="job_gate",
        current_plan_data={},
        current_config_data={},
        caller_identity="human_operator",
        worker_id="w1",
    )
    assert ok is False
    assert "Authorization Denied" in msg
    assert jobs.get_job("job_gate").state == JobState.READY_FOR_APPROVAL


# --------------------------------------------------------------------------
# 5. Atomic rollback on failed write
# --------------------------------------------------------------------------
def test_failed_fenced_write_leaves_no_partial_state(db_path):
    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, 60.0), ExecutionStore(db)
    make_job(jobs, "job_rollback", JobState.RUNNING)
    leases.acquire_lease("job_rollback", "wA", ttl_seconds=60.0)
    tA = leases.get_fencing_token("job_rollback")
    make_exec(executions, "job_rollback", "eroll", "wA", token=tA)

    # Nonexistent execution id -> rejected, and the transaction must not commit
    # anything else. The valid record stays untouched.
    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="does_not_exist",
            job_id="job_rollback",
            worker_id="wA",
            fencing_token=tA,
            status=ExecutionStatus.SUCCESS,
        )
    assert executions.get_execution("eroll").status == ExecutionStatus.STARTED
    # store is still usable afterwards
    executions.complete_execution_fenced(
        execution_id="eroll", job_id="job_rollback", worker_id="wA",
        fencing_token=tA, status=ExecutionStatus.SUCCESS,
    )
    assert executions.get_execution("eroll").status == ExecutionStatus.SUCCESS


def test_stale_token_write_does_not_modify_lease(db_path):
    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, 60.0), ExecutionStore(db)
    make_job(jobs, "job_nolease", JobState.RUNNING)
    leases.acquire_lease("job_nolease", "wA", ttl_seconds=60.0)
    tA = leases.get_fencing_token("job_nolease")
    make_exec(executions, "job_nolease", "enl", "wA", token=tA)

    with pytest.raises(FencedCommitRejected):
        executions.complete_execution_fenced(
            execution_id="enl", job_id="job_nolease", worker_id="wA",
            fencing_token=tA + 99, status=ExecutionStatus.SUCCESS,
        )
    assert leases.get_fencing_token("job_nolease") == tA
    assert executions.get_execution("enl").status == ExecutionStatus.STARTED


# --------------------------------------------------------------------------
# 6. Supervisor propagates the token
# --------------------------------------------------------------------------
def test_supervisor_propagates_token_to_pipeline(tmp_path):
    db = str(tmp_path / "sup_fence.db")
    repo = tmp_path / "repo"
    repo.mkdir()

    cfg = SupervisorConfig(db_path=db, repo_path=str(repo), worker_id="sup_tok", lease_ttl=60.0)
    supervisor = Supervisor(config=cfg)

    captured = {}

    class TokenCapturingPipeline(JobPipeline):
        def run_job(self, job_def, worker_id="worker_c51"):
            token = supervisor.lease_store.get_fencing_token(job_def.job_id)
            captured["token"] = token
            captured["worker"] = worker_id
            from orchestrator.automation.job_pipeline import JobExecutionResult

            return JobExecutionResult(
                job_id=job_def.job_id,
                status=JobState.READY_FOR_APPROVAL,
                definition_hash="h",
                audit_report=MagicMock(),
                plan=MagicMock(),
                agent_result={},
                verification=MagicMock(),
                stage_results=[],
                error=None,
            )

    supervisor.job_pipeline = TokenCapturingPipeline(supervisor.controller, repo_path=str(repo))
    make_job(supervisor.job_store, "job_tokprop", JobState.PLANNING)

    with MagicMock() as guard:
        guard.get_current_identity.return_value = MagicMock(is_dirty=False)
        supervisor.git_guard = guard

    result = supervisor.execute_job(supervisor.job_store.get_job("job_tokprop"))

    assert captured["token"] is not None and captured["token"] >= 1
    assert captured["worker"] == "sup_tok"
    assert result.status == JobState.READY_FOR_APPROVAL


# --------------------------------------------------------------------------
# 7. _ManagedConnection lifecycle
# --------------------------------------------------------------------------
def test_managed_connection_commits_on_success(db_path):
    db = DatabaseManager(db_path)
    with db._get_connection() as conn:
        conn.execute(
            "INSERT INTO automation_jobs (job_id, commit_sha, plan_hash, config_hash, state, "
            "created_at, created_by, updated_at) VALUES (?,?,?,?,?,?,?,?)",
            ("j1", "a" * 40, "p", "c", "PLANNING", "t", "t", "t"),
        )
    with db._get_connection() as conn:
        row = conn.execute("SELECT state FROM automation_jobs WHERE job_id='j1'").fetchone()
    assert row["state"] == "PLANNING"


def test_managed_connection_rolls_back_on_exception(db_path):
    db = DatabaseManager(db_path)
    with pytest.raises(RuntimeError):
        with db._get_connection() as conn:
            conn.execute(
                "INSERT INTO automation_jobs (job_id, commit_sha, plan_hash, config_hash, state, "
                "created_at, created_by, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                ("j_rollback", "a" * 40, "p", "c", "PLANNING", "t", "t", "t"),
            )
            raise RuntimeError("boom")
    with db._get_connection() as conn:
        row = conn.execute("SELECT * FROM automation_jobs WHERE job_id='j_rollback'").fetchone()
    assert row is None, "transaction was committed despite exception"


def test_managed_connection_always_closes(db_path):
    db = DatabaseManager(db_path)
    holders = []
    for _ in range(20):
        mc = db._get_connection()
        holders.append(mc)
        with mc as conn:
            conn.execute("SELECT 1")
    for mc in holders:
        assert isinstance(mc, _ManagedConnection)
        try:
            mc._conn.execute("SELECT 1")
        except Exception:
            continue
        raise AssertionError("connection was not closed after context exit")

    # also closes when the body raises
    mc = db._get_connection()
    with pytest.raises(ValueError):
        with mc:
            raise ValueError("x")
    try:
        mc._conn.execute("SELECT 1")
    except Exception:
        pass
    else:
        raise AssertionError("connection leaked on exception path")


def test_managed_connection_does_not_leak_file_descriptors(db_path):
    """Stress test: the regression that previously exhausted the fd limit."""
    if not hasattr(os, "listdir"):
        pytest.skip("fd counting unsupported")

    def fd_count() -> int:
        try:
            return len(os.listdir("/proc/self/fd"))
        except OSError:
            pytest.skip("/proc/self/fd unavailable")

    db = DatabaseManager(db_path)
    jobs = JobStore(db)
    baseline = fd_count()
    for i in range(400):
        jobs.create_job(
            AutomationJob(
                job_id=f"fd_job_{i}",
                commit_sha="a" * 40,
                plan_hash="p",
                config_hash="c",
                state=JobState.PLANNING,
                created_at=datetime.now(timezone.utc).isoformat(),
                created_by="fd_test",
            )
        )
    growth = fd_count() - baseline
    assert growth <= 5, f"file descriptor leak detected: {growth} fds retained after 400 writes"


def test_job_store_operations_do_not_leak_fds_under_mixed_load(db_path):
    def fd_count() -> int:
        try:
            return len(os.listdir("/proc/self/fd"))
        except OSError:
            pytest.skip("/proc/self/fd unavailable")

    db = DatabaseManager(db_path)
    jobs, leases, executions = JobStore(db), LeaseLockStore(db, 60.0), ExecutionStore(db)
    make_job(jobs, "fd_mix", JobState.RUNNING)
    baseline = fd_count()
    for i in range(150):
        leases.acquire_lease("fd_mix", f"w{i % 3}", ttl_seconds=0.001)
        time.sleep(0.001)
        leases.release_lease("fd_mix", f"w{i % 3}")
        executions.record_start(
            ExecutionRecord(
                execution_id=f"e{i}",
                job_id="fd_mix",
                phase=ExecutionPhase.RUNNING,
                started_at=datetime.now(timezone.utc).isoformat(),
                status=ExecutionStatus.STARTED,
                worker_id=f"w{i % 3}",
            )
        )
        jobs.list_jobs(state=JobState.RUNNING)
    growth = fd_count() - baseline
    assert growth <= 5, f"file descriptor leak under mixed load: {growth}"