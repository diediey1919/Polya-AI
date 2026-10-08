"""
Polya Automation Controller Architecture.
Foundational state machine, Git guard, approval ledger, and authorization boundary.
"""
from orchestrator.automation.states import (
    JobState,
    ApprovalDecision,
    ExecutionPhase,
    ExecutionStatus,
    ALLOWED_TRANSITIONS,
)
from orchestrator.automation.models import (
    AutomationJob,
    ApprovalRecord,
    ExecutionRecord,
)
from orchestrator.automation.hashing import (
    compute_deterministic_hash,
    compute_plan_hash,
    compute_config_hash,
)
from orchestrator.automation.git_guard import (
    GitGuard,
    GitIdentity,
    GitGuardError,
)
from orchestrator.automation.job_store import (
    DatabaseManager,
    JobStore,
    ApprovalStore,
    ExecutionStore,
    LeaseLockStore,
)
from orchestrator.automation.authorization import (
    AuthorizationBoundary,
    AuthorizationResult,
)
from orchestrator.automation.controller import (
    AutomationController,
)
from orchestrator.automation.job_definition import (
    JobDefinition,
    ProjectIdentity,
    ExecutionPolicy,
    VerificationPolicy,
    ProductionPolicy,
    RetryPolicy,
    SideEffectKind,
)
from orchestrator.automation.job_pipeline import (
    JobPipeline,
    AuditReport,
    StructuredPlan,
    StageResult,
    CheckResult,
    VerificationBundle,
    JobExecutionResult,
)

__all__ = [
    "JobState",
    "ApprovalDecision",
    "ExecutionPhase",
    "ExecutionStatus",
    "ALLOWED_TRANSITIONS",
    "AutomationJob",
    "ApprovalRecord",
    "ExecutionRecord",
    "compute_deterministic_hash",
    "compute_plan_hash",
    "compute_config_hash",
    "GitGuard",
    "GitIdentity",
    "GitGuardError",
    "DatabaseManager",
    "JobStore",
    "ApprovalStore",
    "ExecutionStore",
    "LeaseLockStore",
    "AuthorizationBoundary",
    "AuthorizationResult",
    "AutomationController",
    "JobDefinition",
    "ProjectIdentity",
    "ExecutionPolicy",
    "VerificationPolicy",
    "ProductionPolicy",
    "RetryPolicy",
    "SideEffectKind",
    "JobPipeline",
    "AuditReport",
    "StructuredPlan",
    "StageResult",
    "CheckResult",
    "VerificationBundle",
    "JobExecutionResult",
]
