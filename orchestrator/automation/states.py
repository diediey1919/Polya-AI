"""
Automation Controller State Machine Definitions.
Enforces explicit lifecycle states and immutable transition guards.
"""
from enum import Enum
from typing import Dict, Set


class JobState(str, Enum):
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    PRODUCTION_EXECUTION = "PRODUCTION_EXECUTION"
    PRODUCTION_VERIFICATION = "PRODUCTION_VERIFICATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    REJECTED = "REJECTED"
    PLAN_CHANGED = "PLAN_CHANGED"


class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ExecutionPhase(str, Enum):
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    VERIFYING = "VERIFYING"
    PRODUCTION_EXECUTION = "PRODUCTION_EXECUTION"
    PRODUCTION_VERIFICATION = "PRODUCTION_VERIFICATION"


class ExecutionStatus(str, Enum):
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


# Explicit valid state transition map
ALLOWED_TRANSITIONS: Dict[JobState, Set[JobState]] = {
    JobState.PLANNING: {
        JobState.RUNNING,
        JobState.FAILED,
        JobState.ABORTED,
        JobState.PLAN_CHANGED,
    },
    JobState.RUNNING: {
        JobState.VERIFYING,
        JobState.FAILED,
        JobState.ABORTED,
        JobState.PLAN_CHANGED,
    },
    JobState.VERIFYING: {
        JobState.READY_FOR_APPROVAL,
        JobState.FAILED,
        JobState.ABORTED,
        JobState.PLAN_CHANGED,
    },
    JobState.READY_FOR_APPROVAL: {
        JobState.APPROVED,
        JobState.REJECTED,
        JobState.FAILED,
        JobState.ABORTED,
        JobState.PLAN_CHANGED,
    },
    JobState.APPROVED: {
        JobState.PRODUCTION_EXECUTION,
        JobState.ABORTED,
        JobState.PLAN_CHANGED,
    },
    JobState.PRODUCTION_EXECUTION: {
        JobState.PRODUCTION_VERIFICATION,
        JobState.FAILED,
        JobState.ABORTED,
    },
    JobState.PRODUCTION_VERIFICATION: {
        JobState.COMPLETED,
        JobState.FAILED,
        JobState.ABORTED,
    },
    JobState.COMPLETED: set(),
    JobState.FAILED: set(),
    JobState.ABORTED: set(),
    JobState.REJECTED: set(),
    JobState.PLAN_CHANGED: set(),
}
