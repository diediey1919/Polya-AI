"""
Job Definition and Policy Models for Automation Job Engine (C.5.1).
Defines immutable job specifications, side-effect categorizations,
deterministic definition hashing, and validation logic.
"""
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json

from orchestrator.automation.hashing import compute_deterministic_hash


class SideEffectKind(str, Enum):
    READ_ONLY = "READ_ONLY"
    WORKTREE_WRITE = "WORKTREE_WRITE"
    GIT_COMMIT = "GIT_COMMIT"
    GIT_PUSH = "GIT_PUSH"
    PRODUCTION_DB = "PRODUCTION_DB"
    DEPLOYMENT = "DEPLOYMENT"
    EAS_UPDATE = "EAS_UPDATE"
    APK_RELEASE = "APK_RELEASE"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"


@dataclass
class ProjectIdentity:
    name: str
    repository: str
    branch: str = "main"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPolicy:
    agent: str = "hermes"
    timeout_seconds: int = 120
    max_retries: int = 0
    allow_worktree_modifications: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationPolicy:
    git_diff_required: bool = True
    pytest_required: bool = False
    typescript_required: bool = False
    custom_checks: List[Dict[str, Any]] = field(default_factory=list)
    allow_unrelated_baseline_diff: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionPolicy:
    side_effects: List[SideEffectKind] = field(default_factory=lambda: [SideEffectKind.READ_ONLY])
    requires_human_approval: bool = True
    execution_adapter: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "side_effects": [se.value if isinstance(se, SideEffectKind) else se for se in self.side_effects],
            "requires_human_approval": self.requires_human_approval,
            "execution_adapter": self.execution_adapter,
        }


@dataclass
class RetryPolicy:
    idempotent: bool = False
    max_automatic_retries: int = 0
    retry_on_phases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class JobDefinition:
    job_id: str
    project: ProjectIdentity
    base_commit_sha: str
    target: str
    task: str
    constraints: List[str] = field(default_factory=list)
    execution_policy: ExecutionPolicy = field(default_factory=ExecutionPolicy)
    verification_policy: VerificationPolicy = field(default_factory=VerificationPolicy)
    production_policy: ProductionPolicy = field(default_factory=ProductionPolicy)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    created_by: str = "system"
    created_at: str = ""

    def validate(self) -> None:
        if not self.job_id or not self.job_id.strip():
            raise ValueError("job_id must be non-empty")
        if not self.project or not self.project.repository:
            raise ValueError("project.repository must be specified")
        if not self.project.name:
            raise ValueError("project.name must be specified")
        if not self.base_commit_sha or len(self.base_commit_sha) != 40:
            raise ValueError("base_commit_sha must be a valid 40-character commit SHA")
        if not self.task or not self.task.strip():
            raise ValueError("task description must be non-empty")
        if not self.target or not self.target.strip():
            raise ValueError("target must be non-empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "project": self.project.to_dict(),
            "base_commit_sha": self.base_commit_sha,
            "target": self.target,
            "task": self.task,
            "constraints": self.constraints,
            "execution_policy": self.execution_policy.to_dict(),
            "verification_policy": self.verification_policy.to_dict(),
            "production_policy": self.production_policy.to_dict(),
            "retry_policy": self.retry_policy.to_dict(),
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    def compute_definition_hash(self) -> str:
        """
        Computes SHA-256 over entire executable definition payload.
        Ensures execution parameters, policies, target, repo and commit are locked.
        """
        self.validate()
        payload = {
            "project": self.project.to_dict(),
            "base_commit_sha": self.base_commit_sha,
            "target": self.target,
            "task": self.task,
            "constraints": sorted(self.constraints),
            "execution_policy": self.execution_policy.to_dict(),
            "verification_policy": self.verification_policy.to_dict(),
            "production_policy": self.production_policy.to_dict(),
            "retry_policy": self.retry_policy.to_dict(),
        }
        return compute_deterministic_hash(payload)
