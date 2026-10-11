"""
Automation Controller Orchestrator Interface.
Provides high-level lifecycle methods:
- create_job
- advance_to_running
- advance_to_verifying
- mark_ready_for_approval
- submit_approval (Human only)
- initiate_production_execution
- complete_production_verification
- mark_failed
- mark_aborted
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from orchestrator.automation.authorization import AuthorizationBoundary, AuthorizationResult
from orchestrator.automation.git_guard import GitGuard
from orchestrator.automation.hashing import compute_plan_hash, compute_config_hash
from orchestrator.automation.job_store import (
    ApprovalStore,
    DatabaseManager,
    ExecutionStore,
    FencedCommitRejected,
    JobStore,
    LeaseLockStore,
)
from orchestrator.automation.models import AutomationJob, ApprovalRecord, ExecutionRecord
from orchestrator.automation.states import (
    JobState,
    ApprovalDecision,
    ExecutionPhase,
    ExecutionStatus,
)


class AutomationController:
    def __init__(self, db_path: str = "/home/ubuntu/.polya/automation_controller.db", repo_path: str = "/home/ubuntu/Polya-AI"):
        self.db_manager = DatabaseManager(db_path)
        self.job_store = JobStore(self.db_manager)
        self.approval_store = ApprovalStore(self.db_manager)
        self.execution_store = ExecutionStore(self.db_manager)
        self.lease_store = LeaseLockStore(self.db_manager)
        self.git_guard = GitGuard(repo_path)
        self.authorization_boundary = AuthorizationBoundary(
            self.job_store,
            self.approval_store,
            self.execution_store,
            self.git_guard,
        )

    def create_job(
        self,
        plan_data: Any,
        config_data: Any,
        created_by: str,
        correlation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        initial_state: JobState = JobState.PLANNING,
    ) -> AutomationJob:
        """Creates a new automation job anchored to current Git commit and deterministic plan hash."""
        git_identity = self.git_guard.get_current_identity()
        plan_hash = compute_plan_hash(plan_data)
        config_hash = compute_config_hash(config_data)
        now_iso = datetime.now(timezone.utc).isoformat()
        jid = job_id or f"job_{uuid.uuid4().hex[:12]}"

        job = AutomationJob(
            job_id=jid,
            commit_sha=git_identity.commit_sha,
            plan_hash=plan_hash,
            config_hash=config_hash,
            state=initial_state,
            created_at=now_iso,
            created_by=created_by,
            correlation_id=correlation_id,
        )
        return self.job_store.create_job(job)

    def acquire_job_lease(self, job_id: str, worker_id: str, ttl_seconds: float = 60.0) -> bool:
        return self.lease_store.acquire_lease(job_id, worker_id, ttl_seconds)

    def release_job_lease(self, job_id: str, worker_id: str) -> bool:
        return self.lease_store.release_lease(job_id, worker_id)

    def current_fencing_token(self, job_id: str) -> Optional[int]:
        """Returns the fencing token currently stored for the job's lease, or None."""
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT fencing_token FROM automation_job_leases WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()
        if row is None:
            return None
        return int(row["fencing_token"] or 0)

    def _worker_for_execution(self, execution_id: str) -> str:
        """Resolves the worker_id that owns a given execution record."""
        record = self.execution_store.get_execution(execution_id)
        if record is None:
            raise ValueError(f"Execution {execution_id} does not exist.")
        return record.worker_id

    def fenced_transition(
        self,
        job_id: str,
        new_state: JobState,
        worker_id: str,
        fencing_token: Optional[int],
    ) -> AutomationJob:
        """Worker-originated state transition guarded by lease ownership + fencing token."""
        if fencing_token is None:
            raise FencedCommitRejected(
                f"Worker transition of job {job_id} to {new_state} requires a fencing token."
            )
        return self.job_store.transition_state(
            job_id,
            new_state,
            worker_id=worker_id,
            require_lease=True,
            fencing_token=fencing_token,
        )

    def start_running(self, job_id: str, worker_id: str) -> Tuple[AutomationJob, ExecutionRecord]:
        """Transitions job from PLANNING to RUNNING and records execution record."""
        if not self.acquire_job_lease(job_id, worker_id):
            raise PermissionError(f"Cannot run job {job_id}: worker {worker_id} failed to acquire lease (concurrency locked).")

        job = self.fenced_transition(job_id, JobState.RUNNING, worker_id, self.current_fencing_token(job_id))
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        exec_rec = ExecutionRecord(
            execution_id=exec_id,
            job_id=job_id,
            phase=ExecutionPhase.RUNNING,
            started_at=now_iso,
            status=ExecutionStatus.STARTED,
            worker_id=worker_id,
            fencing_token=self.current_fencing_token(job_id),
        )
        self.execution_store.record_start(exec_rec)
        return job, exec_rec

    def complete_running(
        self,
        execution_id: str,
        success: bool,
        error: Optional[str] = None,
        job_id: Optional[str] = None,
        fencing_token: Optional[int] = None,
    ) -> Optional[ExecutionRecord]:
        """Completes a RUNNING execution.

        Fenced whenever job_id is supplied: a fencing token is mandatory, and the token
        is validated against the live lease in the same transaction as the write.
        """
        status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
        if job_id is not None:
            if fencing_token is None:
                raise FencedCommitRejected(
                    f"Fenced completion for job {job_id} requires a fencing token; none supplied."
                )
            return self.execution_store.complete_execution_fenced(
                execution_id=execution_id,
                job_id=job_id,
                worker_id=self._worker_for_execution(execution_id),
                fencing_token=fencing_token,
                status=status,
                error_summary=error,
            )
        raise FencedCommitRejected(
            f"Worker completion of {execution_id} refused: job_id and fencing_token are "
            "required. There is no unfenced worker completion path."
        )

    def start_verifying(self, job_id: str, worker_id: str) -> Tuple[AutomationJob, ExecutionRecord]:
        """Transitions job from RUNNING to VERIFYING."""
        if not self.acquire_job_lease(job_id, worker_id):
            raise PermissionError(f"Cannot verify job {job_id}: lease not acquired.")

        job = self.fenced_transition(job_id, JobState.VERIFYING, worker_id, self.current_fencing_token(job_id))
        exec_id = f"exec_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        exec_rec = ExecutionRecord(
            execution_id=exec_id,
            job_id=job_id,
            phase=ExecutionPhase.VERIFYING,
            started_at=now_iso,
            status=ExecutionStatus.STARTED,
            worker_id=worker_id,
            fencing_token=self.current_fencing_token(job_id),
        )
        self.execution_store.record_start(exec_rec)
        return job, exec_rec

    def complete_verifying(
        self,
        execution_id: str,
        success: bool,
        error: Optional[str] = None,
        job_id: Optional[str] = None,
        fencing_token: Optional[int] = None,
    ) -> Optional[ExecutionRecord]:
        """Completes a VERIFYING execution.

        When job_id and fencing_token are supplied the write is fenced: the token is
        validated against the live lease inside the same transaction as the write,
        so a worker that lost its lease can never persist an outcome.
        """
        status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
        if job_id is not None:
            if fencing_token is None:
                raise FencedCommitRejected(
                    f"Fenced completion for job {job_id} requires a fencing token; none supplied."
                )
            return self.execution_store.complete_execution_fenced(
                execution_id=execution_id,
                job_id=job_id,
                worker_id=self._worker_for_execution(execution_id),
                fencing_token=fencing_token,
                status=status,
                error_summary=error,
            )
        raise FencedCommitRejected(
            f"Worker completion of {execution_id} refused: job_id and fencing_token are "
            "required. There is no unfenced worker completion path."
        )

    def mark_ready_for_approval(self, job_id: str) -> AutomationJob:
        return self.job_store.transition_state(job_id, JobState.READY_FOR_APPROVAL)

    def submit_human_approval(
        self,
        job_id: str,
        decision: ApprovalDecision,
        approved_by: str,
        notes: Optional[str] = None
    ) -> ApprovalRecord:
        """
        Human Approval Gate.
        Security Invariant: AGENT and CRON are forbidden from submitting approval.
        """
        approver_lower = approved_by.lower()
        if (
            approver_lower.startswith("agent")
            or approver_lower.startswith("cron")
            or approver_lower.startswith("scheduler")
        ):
            raise PermissionError("Security Violation: Agents and Cron are forbidden from submitting approvals.")

        job = self.job_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        if job.state != JobState.READY_FOR_APPROVAL:
            raise ValueError(f"Cannot approve job in state {job.state.value}. Must be READY_FOR_APPROVAL.")

        now_iso = datetime.now(timezone.utc).isoformat()
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        record = ApprovalRecord(
            approval_id=approval_id,
            job_id=job_id,
            plan_hash=job.plan_hash,
            commit_sha=job.commit_sha,
            approved_by=approved_by,
            approved_at=now_iso,
            decision=decision,
            notes=notes,
        )
        self.approval_store.record_approval(record)

        if decision == ApprovalDecision.APPROVED:
            self.job_store.transition_state(job_id, JobState.APPROVED)
        else:
            self.job_store.transition_state(job_id, JobState.REJECTED)

        return record

    def initiate_production_execution(
        self,
        job_id: str,
        current_plan_data: Any,
        current_config_data: Any,
        caller_identity: str,
        worker_id: str
    ) -> Tuple[bool, str, Optional[ExecutionRecord]]:
        """
        Authorization-gated entry point for PRODUCTION_EXECUTION.
        """
        # 1. Acquire exclusive worker lease first to establish execution ownership
        if not self.acquire_job_lease(job_id, worker_id):
            return False, f"Concurrency Lock: Worker {worker_id} failed to acquire execution lease.", None

        # 2. Evaluate authorization boundary with execution ownership established
        auth_res = self.authorization_boundary.authorize_production_execution(
            job_id=job_id,
            current_plan_data=current_plan_data,
            current_config_data=current_config_data,
            caller_identity=caller_identity
        )

        if not auth_res.authorized:
            # Release lease safely upon authorization failure to avoid orphan lease
            self.release_job_lease(job_id, worker_id)
            return False, f"Authorization Denied: {auth_res.reason}", None

        # Transition to PRODUCTION_EXECUTION
        self.job_store.transition_state(job_id, JobState.PRODUCTION_EXECUTION, worker_id=worker_id)
        exec_id = f"exec_prod_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        exec_rec = ExecutionRecord(
            execution_id=exec_id,
            job_id=job_id,
            phase=ExecutionPhase.PRODUCTION_EXECUTION,
            started_at=now_iso,
            status=ExecutionStatus.STARTED,
            worker_id=worker_id,
            fencing_token=self.current_fencing_token(job_id),
        )
        self.execution_store.record_start(exec_rec)
        return True, "Authorized and Started PRODUCTION_EXECUTION", exec_rec

    def complete_production_execution(
        self,
        job_id: str,
        execution_id: str,
        success: bool,
        worker_id: str,
        error: Optional[str] = None,
        fencing_token: Optional[int] = None,
    ) -> AutomationJob:
        """Completes a PRODUCTION_EXECUTION run under fencing enforcement.

        A fencing token is mandatory: production results must never be writable by a
        worker that does not hold the current lease token. Callers read the token from
        the ExecutionRecord returned by initiate_production_execution.
        """
        if fencing_token is None:
            record = self.execution_store.get_execution(execution_id)
            if record is None or record.fencing_token is None:
                raise FencedCommitRejected(
                    f"Production completion for job {job_id} requires a fencing token; none available."
                )
            fencing_token = record.fencing_token

        status = ExecutionStatus.SUCCESS if success else ExecutionStatus.FAILED
        self.execution_store.complete_execution_fenced(
            execution_id=execution_id,
            job_id=job_id,
            worker_id=worker_id,
            fencing_token=fencing_token,
            status=status,
            error_summary=error,
        )

        if success:
            return self.job_store.transition_state(job_id, JobState.PRODUCTION_VERIFICATION, worker_id=worker_id)
        else:
            return self.job_store.transition_state(job_id, JobState.FAILED, worker_id=worker_id)

    def complete_production_verification(
        self,
        job_id: str,
        success: bool,
        worker_id: str,
        operator_identity: Optional[str] = None,
    ) -> AutomationJob:
        """Operator-only terminal transition out of PRODUCTION_VERIFICATION.

        Entering COMPLETED is the most consequential write in the system, so it is NOT
        fenced on a worker token: it is gated on an explicit, non-agent operator
        identity and verified approval binding instead. A caller that merely labels itself
        "admin"/"operator" is not enough -- the identity must be supplied, must not be an
        agent/cron/scheduler/worker/supervisor identity, and must correspond to an active,
        matching APPROVED record in ApprovalStore. The lease release is token-guarded so a
        stale holder cannot delete a newer owner's lease.
        """
        if not operator_identity:
            raise PermissionError(
                f"complete_production_verification for job {job_id} requires an explicit "
                "operator_identity. This transition cannot be performed by an autonomous worker."
            )
        identity = operator_identity.lower()
        if (
            identity.startswith("agent")
            or identity.startswith("cron")
            or identity.startswith("scheduler")
            or identity.startswith("worker")
            or identity.startswith("sup")
            or identity.startswith("pipeline")
            or identity.startswith("autom")
        ):
            raise PermissionError(
                f"Security Violation: identity '{operator_identity}' is not permitted to "
                "complete production verification."
            )

        # Must actually be in PRODUCTION_VERIFICATION; the state machine enforces the
        # rest. This also blocks any attempt to reach COMPLETED from an earlier state.
        job = self.job_store.get_job(job_id)
        if job is None:
            raise ValueError(f"Job {job_id} not found.")
        if job.state != JobState.PRODUCTION_VERIFICATION:
            raise ValueError(
                f"Cannot complete production verification for job {job_id} in state "
                f"{job.state.value}; must be PRODUCTION_VERIFICATION."
            )

        if success:
            # Enforce strict approval binding before allowing transition to COMPLETED
            approval = self.approval_store.get_approval_for_job(job_id)
            if approval is None:
                raise PermissionError(
                    f"Security Violation: Cannot complete production verification for job {job_id}. "
                    "No approval record found in ApprovalStore."
                )

            decision_val = approval.decision.value if hasattr(approval.decision, "value") else approval.decision
            if decision_val != ApprovalDecision.APPROVED.value:
                raise PermissionError(
                    f"Security Violation: Cannot complete production verification for job {job_id}. "
                    f"Approval status is '{decision_val}', expected '{ApprovalDecision.APPROVED.value}'."
                )

            approver_lower = (approval.approved_by or "").lower()
            if (
                not approver_lower
                or approver_lower.startswith("agent")
                or approver_lower.startswith("cron")
                or approver_lower.startswith("scheduler")
                or approver_lower.startswith("worker")
                or approver_lower.startswith("sup")
                or approver_lower.startswith("pipeline")
                or approver_lower.startswith("autom")
            ):
                raise PermissionError(
                    f"Security Violation: Approval for job {job_id} was submitted by unauthorized "
                    f"or non-human identity '{approval.approved_by}'."
                )

            if approval.job_id != job.job_id:
                raise PermissionError(
                    f"Security Violation: Approval job_id mismatch ({approval.job_id} != {job.job_id})."
                )

            if approval.plan_hash != job.plan_hash:
                raise PermissionError(
                    f"Security Violation: Approval plan_hash mismatch for job {job_id}. "
                    f"Approved: {approval.plan_hash}, Job: {job.plan_hash}."
                )

            if approval.commit_sha != job.commit_sha:
                raise PermissionError(
                    f"Security Violation: Approval commit_sha mismatch for job {job_id}. "
                    f"Approved: {approval.commit_sha}, Job: {job.commit_sha}."
                )

            job = self.job_store.transition_state(job_id, JobState.COMPLETED, worker_id=worker_id)
        else:
            job = self.job_store.transition_state(job_id, JobState.FAILED, worker_id=worker_id)
        self.release_job_lease(job_id, worker_id)
        return job
