"""
Autonomous Multi-Agent Supervisor for Polya C5 Automation Subsystem.

Coordinates deterministic job execution using C5 primitives:
- JobStore, LeaseLockStore, JobPipeline, AuthorizationBoundary, GitGuard.
- Roles: Planner, Implementer, Test Engineer, Independent Reviewer.
- Enforces lease fencing, heartbeat renewals, crash recovery, DAG dependency resolution,
  circuit breakers, single-instance execution, and CLI modes (--once, --dry-run, --status).
"""

import argparse
import fcntl
import json
import logging
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from orchestrator.automation.authorization import AuthorizationBoundary
from orchestrator.automation.controller import AutomationController
from orchestrator.automation.git_guard import GitGuard
from orchestrator.automation.job_definition import JobDefinition
from orchestrator.automation.job_pipeline import JobExecutionResult, JobPipeline
from orchestrator.automation.job_store import (
    DatabaseManager,
    JobStore,
    LeaseLockStore,
    ApprovalStore,
    ExecutionStore,
)
from orchestrator.automation.migrations import SchemaVersionError, check_schema_version
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import ExecutionPhase, ExecutionStatus, JobState

logger = logging.getLogger("orchestrator.automation.supervisor")


@dataclass
class SupervisorConfig:
    db_path: str = "/home/ubuntu/.polya/automation.db"
    repo_path: str = "/home/ubuntu/Polya-AI"
    worker_id: str = "supervisor_worker"
    lease_ttl: float = 60.0
    heartbeat_interval: float = 15.0
    max_retries: int = 3
    lock_file_path: str = "/tmp/polya_supervisor.lock"
    poll_interval: float = 5.0


@dataclass
class SupervisorStatus:
    active_worker_id: str
    total_jobs: int
    jobs_by_state: Dict[str, int] = field(default_factory=dict)
    runnable_count: int = 0
    blocked_count: int = 0
    awaiting_approval_count: int = 0


class SingleInstanceLock:
    """Enforces single supervisor instance execution using OS-level file locking."""

    def __init__(self, lock_file_path: str):
        self.lock_file_path = lock_file_path
        self._fd: Optional[int] = None
        # Ensure parent directory exists with secure permissions (0700)
        parent_dir = Path(self.lock_file_path).parent
        parent_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent_dir, 0o700)
        except OSError:
            pass

    def acquire(self) -> bool:
        try:
            self._fd = os.open(self.lock_file_path, os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.write(self._fd, f"{os.getpid()}\n".encode("utf-8"))
            return True
        except (BlockingIOError, OSError):
            if self._fd is not None:
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None
            return False

    def release(self) -> None:
        if self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
            try:
                if os.path.exists(self.lock_file_path):
                    os.unlink(self.lock_file_path)
            except OSError:
                pass


class Supervisor:
    """Deterministic Multi-Agent Supervisor implementing Plan -> Audit -> Execute -> Monitor."""

    def __init__(
        self,
        config: Optional[SupervisorConfig] = None,
        controller: Optional[AutomationController] = None,
        job_pipeline: Optional[JobPipeline] = None,
    ):
        self.config = config or SupervisorConfig()
        self.db_manager = DatabaseManager(self.config.db_path)
        # Stamp the migration ledger on databases this process just created.
        # check_schema_version() below still refuses to RUN jobs on a legacy DB.
        self.job_store = JobStore(self.db_manager)
        self.approval_store = ApprovalStore(self.db_manager)
        self.execution_store = ExecutionStore(self.db_manager)
        self.lease_store = LeaseLockStore(self.db_manager, default_lease_ttl=self.config.lease_ttl)
        self.controller = controller or AutomationController(self.config.db_path)
        self.git_guard = GitGuard(self.config.repo_path)
        self.job_pipeline = job_pipeline or JobPipeline(self.controller, repo_path=self.config.repo_path)
        self.auth_boundary = AuthorizationBoundary(
            job_store=self.job_store,
            approval_store=self.approval_store,
            execution_store=self.execution_store,
            git_guard=self.git_guard,
        )

        self.instance_lock = SingleInstanceLock(self.config.lock_file_path)
        self._stop_requested = False
        self._retry_counts: Dict[str, int] = {}
        self._job_definitions: Dict[str, JobDefinition] = {}

    def request_stop(self) -> None:
        """Triggers graceful stop after finishing current unit of work."""
        logger.info("Supervisor shutdown requested.")
        self._stop_requested = True

    def register_job_definition(self, job_def: JobDefinition) -> None:
        """Registers a recognized JobDefinition metadata in supervisor registry."""
        self._job_definitions[job_def.job_id] = job_def

    def get_status(self) -> SupervisorStatus:
        """Queries current automation state distribution and runnable workload."""
        all_jobs = self.job_store.list_jobs(limit=1000)
        jobs_by_state: Dict[str, int] = {}
        for j in all_jobs:
            s = j.state.value if isinstance(j.state, JobState) else j.state
            jobs_by_state[s] = jobs_by_state.get(s, 0) + 1

        runnable_jobs, blocked_jobs = self.filter_runnable_jobs(all_jobs)

        return SupervisorStatus(
            active_worker_id=self.config.worker_id,
            total_jobs=len(all_jobs),
            jobs_by_state=jobs_by_state,
            runnable_count=len(runnable_jobs),
            blocked_count=len(blocked_jobs),
            awaiting_approval_count=jobs_by_state.get(JobState.READY_FOR_APPROVAL.value, 0),
        )

    def filter_runnable_jobs(
        self, candidates: Optional[List[AutomationJob]] = None
    ) -> Tuple[List[AutomationJob], List[Tuple[AutomationJob, str]]]:
        """
        Determines runnable jobs adhering to:
        1. State is strictly JobState.PLANNING (runnable entry state).
        2. Not locked by another active worker.
        3. DAG dependencies must be satisfied (COMPLETED status).
        4. Retry limit not exceeded.
        """
        if candidates is None:
            candidates = self.job_store.list_jobs(limit=500)

        runnable: List[AutomationJob] = []
        blocked: List[Tuple[AutomationJob, str]] = []

        completed_ids = {
            j.job_id for j in candidates if j.state == JobState.COMPLETED
        }

        for job in candidates:
            # Check terminal or non-runnable states
            if job.state in {
                JobState.COMPLETED,
                JobState.FAILED,
                JobState.ABORTED,
                JobState.REJECTED,
                JobState.PLAN_CHANGED,
            }:
                continue

            # READY_FOR_APPROVAL is gated for humans; not runnable autonomously
            if job.state == JobState.READY_FOR_APPROVAL:
                blocked.append((job, "Awaiting manual human approval"))
                continue

            # APPROVED or PRODUCTION_EXECUTION requires explicit authorized production operator
            if job.state in {JobState.APPROVED, JobState.PRODUCTION_EXECUTION, JobState.PRODUCTION_VERIFICATION}:
                blocked.append((job, "Production state requires manual operator execution"))
                continue

            # Only PLANNING is autonomous entry state
            if job.state != JobState.PLANNING:
                blocked.append((job, f"Non-runnable state: {job.state.value}"))
                continue

            # Retry count check (in-memory fast path + persistent execution audit)
            retries = max(self._retry_counts.get(job.job_id, 0), self._persistent_failure_count(job.job_id))
            if retries >= self.config.max_retries:
                blocked.append((job, f"Max retries ({self.config.max_retries}) exceeded"))
                continue

            # Concurrency lease check
            if self.lease_store.is_locked_by_other(job.job_id, self.config.worker_id):
                blocked.append((job, "Active lease held by another worker"))
                continue

            # DAG dependency check if definition is registered
            job_def = self._job_definitions.get(job.job_id)
            if job_def and getattr(job_def, "dependencies", None):
                deps = job_def.dependencies or []
                missing_deps = [dep for dep in deps if dep not in completed_ids]
                if missing_deps:
                    blocked.append((job, f"Unsatisfied dependencies: {missing_deps}"))
                    continue

            runnable.append(job)

        return runnable, blocked

    def _lease_expired(self, job_id: str) -> bool:
        """Returns True only when a lease row exists and is expired, or no lease row exists at all."""
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT worker_id, expires_at FROM automation_job_leases WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
        if row is None:
            return True
        return row["expires_at"] <= time.time()

    def recover_crashed_jobs(self) -> int:
        """Recovers jobs whose worker lease has expired while stuck in intermediate non-terminal states.

        Never takes over a job whose lease is still actively held by a live worker.
        """
        interm_states = [JobState.RUNNING, JobState.VERIFYING]
        recovered = 0
        for st in interm_states:
            jobs = self.job_store.list_jobs(state=st)
            for j in jobs:
                if self.lease_store.is_locked_by_other(j.job_id, self.config.worker_id):
                    continue  # Live worker still owns it
                if not self._lease_expired(j.job_id):
                    continue  # Lease still valid; do not steal from an active worker
                logger.warning(f"Recovering orphaned job {j.job_id} from state {st.value} (expired lease)")
                try:
                    self.job_store.transition_state(j.job_id, JobState.FAILED, worker_id="supervisor_recovery")
                    recovered += 1
                except Exception as e:
                    logger.error(f"Failed to reset crashed job {j.job_id}: {e}")
        return recovered

    def _persistent_failure_count(self, job_id: str) -> int:
        """Counts persisted failed/aborted execution attempts for a job (cross-process retry guard).

        Uses the existing ExecutionStore audit table; no parallel state store is created.
        """
        try:
            records = self.execution_store.list_executions_for_job(job_id, phase=ExecutionPhase.RUNNING)
        except Exception as e:
            logger.warning(f"Persistent failure audit unavailable for {job_id}: {e}")
            return 0
        return sum(
            1 for r in records if r.status in {ExecutionStatus.FAILED, ExecutionStatus.ABORTED}
        )

    def _lease_still_owned(self, job_id: str) -> bool:
        """Verifies this worker still owns the lease for the job (fencing guard).

        Returns False when no lease row exists or the lease belongs to another worker,
        preventing a stale worker from persisting results after takeover.
        """
        if self.lease_store.is_locked_by_other(job_id, self.config.worker_id):
            return False
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT worker_id, expires_at FROM automation_job_leases WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
        if row is None:
            return False
        if row["worker_id"] != self.config.worker_id:
            return False
        return row["expires_at"] > time.time()

    def _heartbeat_loop(self, job_id: str, stop_event: threading.Event) -> None:
        """Renews the job lease periodically while the pipeline is executing."""
        while not stop_event.wait(self.config.heartbeat_interval):
            try:
                if not self.renew_heartbeat(job_id):
                    logger.error(f"[{job_id}] Heartbeat renewal failed; lease may be lost.")
                    return
            except Exception as e:
                logger.warning(f"[{job_id}] Heartbeat error: {e}")
                return

    def renew_heartbeat(self, job_id: str) -> bool:
        """Renews concurrency lease for the current worker."""
        return self.lease_store.acquire_lease(job_id, self.config.worker_id, ttl_seconds=self.config.lease_ttl)

    def execute_job(self, job: AutomationJob, dry_run: bool = False) -> JobExecutionResult:
        """
        Executes a single job deterministically:
        1. Acquire lease.
        2. Check GitGuard clean tree.
        3. Dispatch to multi-agent JobPipeline.
        4. Heartbeat during execution.
        5. Release lease.
        """
        if dry_run:
            logger.info(f"[DRY-RUN] Would acquire lease and execute job: {job.job_id}")
            return JobExecutionResult(
                job_id=job.job_id,
                status=job.state,
                definition_hash="dry_run_hash",
                audit_report=None,  # type: ignore
                plan=None,  # type: ignore
                agent_result=None,
                verification=None,
                stage_results=[],
                error=None,
            )

        if not self.lease_store.acquire_lease(job.job_id, self.config.worker_id, ttl_seconds=self.config.lease_ttl):
            logger.warning(f"Could not acquire lease for job {job.job_id}. Skipping.")
            return JobExecutionResult(
                job_id=job.job_id,
                status=job.state,
                definition_hash="unacquired_lease",
                audit_report=None,  # type: ignore
                plan=None,  # type: ignore
                agent_result=None,
                verification=None,
                stage_results=[],
                error="Lease acquisition failed",
            )

        try:
            # Fencing guard: the token issued by acquire_lease governs all result writes
            self._lease_token_at_exit = self.lease_store.get_fencing_token(job.job_id)
            logger.debug(f"[{job.job_id}] Acquired lease with fencing token {self._lease_token_at_exit}")

            # Check Git clean state before executing mutations
            try:
                git_id = self.git_guard.get_current_identity()
                if git_id.is_dirty:
                    err_msg = "Git worktree dirty. Execution blocked."
                    logger.error(err_msg)
                    self.job_store.transition_state(job.job_id, JobState.FAILED, worker_id=self.config.worker_id)
                    return JobExecutionResult(
                        job_id=job.job_id,
                        status=JobState.FAILED,
                        definition_hash="dirty_git",
                        audit_report=None,  # type: ignore
                        plan=None,  # type: ignore
                        agent_result=None,
                        verification=None,
                        stage_results=[],
                        error=err_msg,
                    )
            except Exception as e:
                logger.warning(f"GitGuard inspection warning: {e}")

            # Retrieve or construct JobDefinition
            job_def = self._job_definitions.get(job.job_id)
            if not job_def:
                from orchestrator.automation.job_definition import ProjectIdentity
                job_def = JobDefinition(
                    job_id=job.job_id,
                    project=ProjectIdentity(name="polya", repository="Polya-AI", branch="main"),
                    base_commit_sha=job.commit_sha,
                    target="test_target",
                    task=f"Automated execution for {job.job_id}",
                )

            # Start heartbeat thread to keep lease alive during long-running pipeline
            heartbeat_stop = threading.Event()
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                args=(job.job_id, heartbeat_stop),
                daemon=True,
            )
            heartbeat_thread.start()

            # Execute pipeline
            try:
                result = self.job_pipeline.run_job(job_def, worker_id=self.config.worker_id)
            finally:
                heartbeat_stop.set()
                heartbeat_thread.join(timeout=2.0)

            # Fencing: verify lease ownership was never lost before persisting outcome.
            if not self._lease_still_owned(job.job_id):
                err_msg = (
                    "Lease fencing violation: lease for this job was lost or taken over "
                    "during execution; result discarded."
                )
                logger.error(f"[{job.job_id}] {err_msg}")
                return JobExecutionResult(
                    job_id=job.job_id,
                    status=JobState.ABORTED,
                    definition_hash="fence_lost",
                    audit_report=None,  # type: ignore
                    plan=None,  # type: ignore
                    agent_result=None,
                    verification=None,
                    stage_results=[],
                    error=err_msg,
                )

            is_success = (result.status == JobState.READY_FOR_APPROVAL or result.status == JobState.COMPLETED)
            if not is_success:
                self._retry_counts[job.job_id] = self._retry_counts.get(job.job_id, 0) + 1
                logger.warning(
                    f"Job {job.job_id} did not succeed (status: {result.status}). Retry count: {self._retry_counts[job.job_id]}/{self.config.max_retries}"
                )

            return result
        finally:
            # Cleanup only removes OUR lease; the predicate includes the fencing token so a
            # worker can never delete a lease that has been taken over by someone else.
            self.lease_store.release_lease(job.job_id, self.config.worker_id, fencing_token=self._lease_token_at_exit)

    def run_cycle(self, dry_run: bool = False) -> int:
        """Runs a single deterministic supervision cycle. Returns count of executed jobs."""
        if not dry_run:
            self.recover_crashed_jobs()

        runnable, blocked = self.filter_runnable_jobs()
        if not runnable:
            logger.info("No runnable jobs found in state store.")
            return 0

        executed_count = 0
        for job in runnable:
            if self._stop_requested:
                logger.info("Stopping cycle due to graceful shutdown request.")
                break

            logger.info(f"Processing runnable job: {job.job_id} (state: {job.state.value})")
            self.execute_job(job, dry_run=dry_run)
            executed_count += 1

        return executed_count

    def run_forever(self, dry_run: bool = False) -> None:
        """Polls continuously with graceful shutdown signal handlers."""
        def handle_signal(sig, frame):
            self.request_stop()

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)

        logger.info(f"Supervisor started (worker_id={self.config.worker_id}, dry_run={dry_run}).")
        while not self._stop_requested:
            self.run_cycle(dry_run=dry_run)
            if not self._stop_requested:
                time.sleep(self.config.poll_interval)
        logger.info("Supervisor stopped gracefully.")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous Multi-Agent Supervisor for Polya C5 Subsystem.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--once", action="store_true", help="Execute a single supervision cycle and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and simulate runnable jobs without mutating state.")
    parser.add_argument("--status", action="store_true", help="Display current automation state distribution and exit.")
    parser.add_argument("--db-path", default="/home/ubuntu/.polya/automation.db", help="Path to automation database.")
    parser.add_argument("--repo-path", default="/home/ubuntu/Polya-AI", help="Path to repository root.")
    parser.add_argument("--worker-id", default=f"sup_{os.getpid()}", help="Worker identifier.")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = SupervisorConfig(
        db_path=args.db_path,
        repo_path=args.repo_path,
        worker_id=args.worker_id,
    )

    # Read-only startup guard. --status and --dry-run must stay usable on an
    # un-migrated database, so the hard refusal only applies to job execution.
    schema_ok = True
    try:
        check_schema_version(args.db_path)
    except SchemaVersionError as e:
        if args.status or args.dry_run:
            logger.warning("Schema not current: %s", e)
            schema_ok = False
        else:
            logger.error("%s", e)
            return 2

    supervisor = Supervisor(config=config)

    if args.status:
        st = supervisor.get_status()
        print("=== C5 SUPERVISOR STATUS ===")
        print(f"Worker ID:         {st.active_worker_id}")
        print(f"Total Jobs:        {st.total_jobs}")
        print(f"Runnable Jobs:     {st.runnable_count}")
        print(f"Blocked Jobs:      {st.blocked_count}")
        print(f"Awaiting Approval: {st.awaiting_approval_count}")
        print(f"Schema Current:    {'yes' if schema_ok else 'NO - migrations pending'}")
        print("Distribution by State:")
        for s, count in sorted(st.jobs_by_state.items()):
            print(f"  - {s:<22}: {count}")
        return 0

    if args.dry_run:
        count = supervisor.run_cycle(dry_run=True)
        logger.info(f"[DRY-RUN] Evaluated runnable jobs: {count} would be executed.")
        return 0

    if not supervisor.instance_lock.acquire():
        logger.error("Another supervisor instance is already running (single-instance lock held).")
        return 1

    try:
        if args.once:
            count = supervisor.run_cycle(dry_run=False)
            logger.info(f"Supervision cycle completed. Executed: {count} job(s).")
            return 0
        else:
            supervisor.run_forever(dry_run=False)
            return 0
    finally:
        supervisor.instance_lock.release()


if __name__ == "__main__":
    sys.exit(main())
