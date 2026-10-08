"""
Authorization Boundary and Production Gate.
Validates all 12 security checkpoints before permitting PRODUCTION_EXECUTION.
Enforces that AGENT and CRON cannot approve or execute without authorization.
"""
from dataclasses import dataclass
from typing import Optional

from orchestrator.automation.git_guard import GitGuard
from orchestrator.automation.hashing import compute_plan_hash, compute_config_hash
from orchestrator.automation.job_store import ApprovalStore, ExecutionStore, JobStore
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import JobState, ApprovalDecision, ExecutionPhase, ExecutionStatus


@dataclass
class AuthorizationResult:
    authorized: bool
    job_id: str
    reason: str
    job: Optional[AutomationJob] = None


class AuthorizationBoundary:
    def __init__(
        self,
        job_store: JobStore,
        approval_store: ApprovalStore,
        execution_store: ExecutionStore,
        git_guard: Optional[GitGuard] = None,
    ):
        self.job_store = job_store
        self.approval_store = approval_store
        self.execution_store = execution_store
        self.git_guard = git_guard or GitGuard()

    def authorize_production_execution(
        self,
        job_id: str,
        current_plan_data: any,
        current_config_data: any,
        caller_identity: str
    ) -> AuthorizationResult:
        """
        Validates all 12 mandatory gates before permitting production execution:
        1. job exists
        2. state == APPROVED
        3. approval exists
        4. approval decision == APPROVED
        5. approval.job_id == job.job_id
        6. approval.plan_hash == job.plan_hash
        7. approval.commit_sha == job.commit_sha
        8. current Git commit == job.commit_sha
        9. current plan hash == approved plan hash
        10. current config hash == approved config hash
        11. job has not already executed production phase successfully
        12. job is not in FAILED, ABORTED, REJECTED, or PLAN_CHANGED state
        """
        # Security invariant: callers starting with 'agent' or 'cron' or 'scheduler' cannot authorize directly
        caller_lower = caller_identity.lower()
        if caller_lower.startswith("cron") or caller_lower.startswith("scheduler"):
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="CRON / SCHEDULER is strictly forbidden from initiating production execution."
            )
        if caller_lower.startswith("agent"):
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="AGENT is strictly forbidden from initiating production execution."
            )

        job = self.job_store.get_job(job_id)
        if not job:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 1 Failed: Job {job_id} does not exist."
            )

        # Gate 12: Terminal / invalid failure states
        if job.state in {JobState.FAILED, JobState.ABORTED, JobState.REJECTED, JobState.PLAN_CHANGED}:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 12 Failed: Job is in invalid state {job.state.value}.",
                job=job
            )

        # Gate 2: State must be APPROVED
        if job.state != JobState.APPROVED:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 2 Failed: Job state is {job.state.value}, expected APPROVED.",
                job=job
            )

        approval = self.approval_store.get_approval_for_job(job_id)
        if not approval:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="Gate 3 Failed: No approval record exists for job.",
                job=job
            )

        # Gate 4: Decision must be APPROVED
        if approval.decision != ApprovalDecision.APPROVED:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 4 Failed: Approval decision is {approval.decision.value}.",
                job=job
            )

        # Gate 5: approval.job_id == job.job_id
        if approval.job_id != job.job_id:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="Gate 5 Failed: Approval job_id mismatch.",
                job=job
            )

        # Gate 6: approval.plan_hash == job.plan_hash
        if approval.plan_hash != job.plan_hash:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="Gate 6 Failed: Approval plan_hash does not match job plan_hash.",
                job=job
            )

        # Gate 7: approval.commit_sha == job.commit_sha
        if approval.commit_sha.lower() != job.commit_sha.lower():
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="Gate 7 Failed: Approval commit_sha does not match job commit_sha.",
                job=job
            )

        # Gate 8: current Git commit == job.commit_sha
        if not self.git_guard.verify_commit_match(job.commit_sha):
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 8 Failed: Current repository Git HEAD does not match job commit_sha {job.commit_sha}.",
                job=job
            )

        # Gate 9: current plan hash == approved plan hash
        current_plan_hash = compute_plan_hash(current_plan_data)
        if current_plan_hash != approval.plan_hash:
            # Detect plan mutation
            self.job_store.transition_state(job_id, JobState.PLAN_CHANGED)
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 9 Failed: Plan mutation detected. Current plan hash ({current_plan_hash}) != approved ({approval.plan_hash}). State changed to PLAN_CHANGED.",
                job=job
            )

        # Gate 10: current config hash == approved config hash
        current_cfg_hash = compute_config_hash(current_config_data)
        if current_cfg_hash != job.config_hash:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason=f"Gate 10 Failed: Config hash mismatch. Current ({current_cfg_hash}) != expected ({job.config_hash}).",
                job=job
            )

        # Gate 11: job has not already executed production phase successfully (Idempotency)
        successful_executions = self.execution_store.get_successful_production_executions(job_id)
        if successful_executions:
            return AuthorizationResult(
                authorized=False,
                job_id=job_id,
                reason="Gate 11 Failed: Idempotency check failed. Job has already executed PRODUCTION_EXECUTION successfully.",
                job=job
            )

        return AuthorizationResult(
            authorized=True,
            job_id=job_id,
            reason="All 12 authorization gates passed successfully.",
            job=job
        )
