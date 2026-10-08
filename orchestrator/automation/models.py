"""
Canonical Data Models for Automation Controller.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from orchestrator.automation.states import JobState, ApprovalDecision, ExecutionPhase, ExecutionStatus


@dataclass
class AutomationJob:
    job_id: str
    commit_sha: str
    plan_hash: str
    config_hash: str
    state: JobState
    created_at: str
    created_by: str
    worker_id: Optional[str] = None
    correlation_id: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "commit_sha": self.commit_sha,
            "plan_hash": self.plan_hash,
            "config_hash": self.config_hash,
            "state": self.state.value if isinstance(self.state, JobState) else self.state,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "worker_id": self.worker_id,
            "correlation_id": self.correlation_id,
            "updated_at": self.updated_at,
        }


@dataclass
class ApprovalRecord:
    approval_id: str
    job_id: str
    plan_hash: str
    commit_sha: str
    approved_by: str
    approved_at: str
    decision: ApprovalDecision
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "job_id": self.job_id,
            "plan_hash": self.plan_hash,
            "commit_sha": self.commit_sha,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "decision": self.decision.value if isinstance(self.decision, ApprovalDecision) else self.decision,
            "notes": self.notes,
        }


@dataclass
class ExecutionRecord:
    execution_id: str
    job_id: str
    phase: ExecutionPhase
    started_at: str
    status: ExecutionStatus
    worker_id: str
    completed_at: Optional[str] = None
    error_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "job_id": self.job_id,
            "phase": self.phase.value if isinstance(self.phase, ExecutionPhase) else self.phase,
            "started_at": self.started_at,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else self.status,
            "worker_id": self.worker_id,
            "completed_at": self.completed_at,
            "error_summary": self.error_summary,
            "metadata": self.metadata or {},
        }
