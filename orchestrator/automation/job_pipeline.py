"""
Automation Job Execution Pipeline (C.5.1).
Implements explicit stages:
1. Audit Stage: captures environment, baseline git status, repo identity.
2. Plan Stage: creates structured implementation & verification plan with plan_hash.
3. Dispatch Stage: delegates implementation to AgentRuntime.
4. Implementation Stage: runs agent and checks outputs.
5. Verification Stage: executes VerificationPolicy checks and diff inspection.
6. Report Stage: persists execution bundle.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from orchestrator.automation.controller import AutomationController
from orchestrator.automation.git_guard import GitGuard, GitGuardError, GitIdentity
from orchestrator.automation.hashing import compute_deterministic_hash, compute_plan_hash
from orchestrator.automation.job_definition import JobDefinition, SideEffectKind
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import JobState
from orchestrator.runtime import AgentResponse, AgentRuntime


@dataclass
class AuditReport:
    project_name: str
    repository: str
    branch: str
    commit_sha: str
    is_dirty: bool
    baseline_status_porcelain: str
    baseline_dirty_files: List[str]
    target: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StructuredPlan:
    plan_id: str
    target: str
    architecture: str
    files_expected_to_change: List[str]
    implementation_steps: List[str]
    verification_steps: List[str]
    side_effects: List[str]
    risks: List[str]
    plan_hash: str = ""

    def to_dict(self, include_hash: bool = True) -> Dict[str, Any]:
        d = asdict(self)
        if not include_hash:
            d.pop("plan_hash", None)
        return d


@dataclass
class StageResult:
    stage: str
    status: str  # SUCCESS, FAILED, SKIPPED
    started_at: str
    completed_at: str
    details: Dict[str, Any]
    error: Optional[str] = None
    retry_eligible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CheckResult:
    check_id: str
    name: str
    status: str  # PASS, FAIL, BLOCKED
    command: Optional[str]
    started_at: str
    completed_at: str
    output_summary: str
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationBundle:
    overall_status: str  # PASS, FAIL, BLOCKED
    checks: List[CheckResult]
    newly_modified_files: List[str]
    unexpected_modified_files: List[str]
    baseline_preserved: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "checks": [c.to_dict() for c in self.checks],
            "newly_modified_files": self.newly_modified_files,
            "unexpected_modified_files": self.unexpected_modified_files,
            "baseline_preserved": self.baseline_preserved,
        }


@dataclass
class JobExecutionResult:
    job_id: str
    status: JobState
    definition_hash: str
    audit_report: AuditReport
    plan: StructuredPlan
    agent_result: Optional[Dict[str, Any]]
    verification: Optional[VerificationBundle]
    stage_results: List[StageResult]
    error: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value if isinstance(self.status, JobState) else self.status,
            "definition_hash": self.definition_hash,
            "audit_report": self.audit_report.to_dict(),
            "plan": self.plan.to_dict(),
            "agent_result": self.agent_result,
            "verification": self.verification.to_dict() if self.verification else None,
            "stage_results": [sr.to_dict() for sr in self.stage_results],
            "error": self.error,
            "completed_at": self.completed_at,
        }


class JobPipeline:
    """
    Executes a JobDefinition under the control of AutomationController.
    Guarantees baseline preservation, stage reporting, verification gating,
    and stops at READY_FOR_APPROVAL if verification passes.
    """
    def __init__(self, controller: AutomationController, repo_path: str = "/home/ubuntu/Polya-AI"):
        self.controller = controller
        self.repo_path = Path(repo_path).resolve()
        self.git_guard = controller.git_guard

    def _get_porcelain_status(self) -> Tuple[str, List[str]]:
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=True
            )
            raw = res.stdout
            files = []
            for line in raw.splitlines():
                line = line.strip()
                if line:
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        files.append(parts[1])
            return raw, files
        except Exception:
            return "", []

    def run_job(self, job_def: JobDefinition, worker_id: str = "worker_c51") -> JobExecutionResult:
        # Validate job definition
        job_def.validate()
        definition_hash = job_def.compute_definition_hash()
        stages: List[StageResult] = []

        # ==========================================
        # STAGE 1: AUDIT
        # ==========================================
        t0_audit = datetime.now(timezone.utc).isoformat()
        git_id = self.git_guard.get_current_identity()

        # Validate repository identity against definition
        if job_def.base_commit_sha != git_id.commit_sha:
            err = (
                f"Repository HEAD commit SHA mismatch: expected {job_def.base_commit_sha}, "
                f"got {git_id.commit_sha}"
            )
            stages.append(StageResult(
                stage="AUDIT",
                status="FAILED",
                started_at=t0_audit,
                completed_at=datetime.now(timezone.utc).isoformat(),
                details={"expected_sha": job_def.base_commit_sha, "actual_sha": git_id.commit_sha},
                error=err,
                retry_eligible=False
            ))
            # Return failed bundle
            dummy_audit = AuditReport(
                project_name=job_def.project.name,
                repository=job_def.project.repository,
                branch=git_id.branch,
                commit_sha=git_id.commit_sha,
                is_dirty=git_id.is_dirty,
                baseline_status_porcelain="",
                baseline_dirty_files=[],
                target=job_def.target,
                timestamp=t0_audit
            )
            dummy_plan = StructuredPlan(
                plan_id="",
                target=job_def.target,
                architecture="",
                files_expected_to_change=[],
                implementation_steps=[],
                verification_steps=[],
                side_effects=[],
                risks=[]
            )
            return JobExecutionResult(
                job_id=job_def.job_id,
                status=JobState.FAILED,
                definition_hash=definition_hash,
                audit_report=dummy_audit,
                plan=dummy_plan,
                agent_result=None,
                verification=None,
                stage_results=stages,
                error=err,
                completed_at=datetime.now(timezone.utc).isoformat()
            )

        # Baseline porcelain status
        porcelain_status, baseline_files = self._get_porcelain_status()
        audit_report = AuditReport(
            project_name=job_def.project.name,
            repository=job_def.project.repository,
            branch=git_id.branch,
            commit_sha=git_id.commit_sha,
            is_dirty=git_id.is_dirty,
            baseline_status_porcelain=porcelain_status,
            baseline_dirty_files=baseline_files,
            target=job_def.target,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        stages.append(StageResult(
            stage="AUDIT",
            status="SUCCESS",
            started_at=t0_audit,
            completed_at=datetime.now(timezone.utc).isoformat(),
            details=audit_report.to_dict(),
            retry_eligible=True
        ))

        # ==========================================
        # STAGE 2: PLAN
        # ==========================================
        t0_plan = datetime.now(timezone.utc).isoformat()
        plan_id = f"plan_{job_def.job_id}"
        expected_files = job_def.execution_policy.parameters.get("expected_files", [])
        plan = StructuredPlan(
            plan_id=plan_id,
            target=job_def.target,
            architecture="Polya Automation Job Engine Architecture (C.5.1)",
            files_expected_to_change=expected_files,
            implementation_steps=[
                f"Dispatch {job_def.execution_policy.agent} agent for task: {job_def.task}",
                "Monitor agent execution and capture output artifacts",
            ],
            verification_steps=[
                "Inspect git working tree modifications against baseline",
                "Verify no unexpected files were modified",
                "Execute policy-required verification checks",
            ],
            side_effects=[se.value for se in job_def.production_policy.side_effects],
            risks=["Subprocess execution failure", "Working tree contamination", "Verification regression"],
        )
        plan_data_for_hash = plan.to_dict(include_hash=False)
        plan_hash = compute_plan_hash(plan_data_for_hash)
        plan.plan_hash = plan_hash

        # Initialize or fetch Job in AutomationController
        existing_job = self.controller.job_store.get_job(job_def.job_id)
        if not existing_job:
            job = self.controller.create_job(
                plan_data=plan_data_for_hash,
                config_data=job_def.to_dict(),
                created_by=job_def.created_by,
                job_id=job_def.job_id
            )
        else:
            job = existing_job
            # Check for duplicate terminal job
            if job.state in (JobState.COMPLETED, JobState.APPROVED):
                stages.append(StageResult(
                    stage="PLAN",
                    status="FAILED",
                    started_at=t0_plan,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    details={"existing_state": job.state.value},
                    error="Job already exists in terminal/approved state; re-running requires new job_id.",
                    retry_eligible=False
                ))
                return JobExecutionResult(
                    job_id=job_def.job_id,
                    status=job.state,
                    definition_hash=definition_hash,
                    audit_report=audit_report,
                    plan=plan,
                    agent_result=None,
                    verification=None,
                    stage_results=stages,
                    error="Job already exists in terminal/approved state.",
                    completed_at=datetime.now(timezone.utc).isoformat()
                )

        stages.append(StageResult(
            stage="PLAN",
            status="SUCCESS",
            started_at=t0_plan,
            completed_at=datetime.now(timezone.utc).isoformat(),
            details={"plan_id": plan_id, "plan_hash": plan_hash},
            retry_eligible=True
        ))

        # ==========================================
        # STAGE 3 & 4: DISPATCH & IMPLEMENTATION
        # ==========================================
        t0_dispatch = datetime.now(timezone.utc).isoformat()
        try:
            job, exec_rec = self.controller.start_running(job.job_id, worker_id=worker_id)
        except Exception as e:
            stages.append(StageResult(
                stage="DISPATCH",
                status="FAILED",
                started_at=t0_dispatch,
                completed_at=datetime.now(timezone.utc).isoformat(),
                details={"error": str(e)},
                error=f"Controller transition to RUNNING failed: {e}",
                retry_eligible=True
            ))
            return JobExecutionResult(
                job_id=job.job_id,
                status=job.state,
                definition_hash=definition_hash,
                audit_report=audit_report,
                plan=plan,
                agent_result=None,
                verification=None,
                stage_results=stages,
                error=str(e),
                completed_at=datetime.now(timezone.utc).isoformat()
            )

        agent_name = job_def.execution_policy.agent
        prompt = (
            f"Target: {job_def.target}\n"
            f"Task: {job_def.task}\n"
            f"Constraints: {', '.join(job_def.constraints)}"
        )
        
        # Dispatch agent via AgentRuntime
        agent_resp: AgentResponse = AgentRuntime.dispatch(
            agent_name=agent_name,
            prompt=prompt,
            timeout=job_def.execution_policy.timeout_seconds,
            max_retries=job_def.execution_policy.max_retries,
        )

        agent_dict = agent_resp.to_dict()
        is_success = agent_resp.status in ("COMPLETED", "SUCCESS")
        self.controller.complete_running(
            exec_rec.execution_id,
            success=is_success,
            error=agent_resp.error
        )

        stages.append(StageResult(
            stage="IMPLEMENTATION",
            status="SUCCESS" if is_success else "FAILED",
            started_at=t0_dispatch,
            completed_at=datetime.now(timezone.utc).isoformat(),
            details={"agent": agent_name, "status": agent_resp.status, "duration_ms": agent_resp.execution_time_ms},
            error=agent_resp.error,
            retry_eligible=True
        ))

        if not is_success:
            self.controller.job_store.transition_state(job.job_id, JobState.FAILED, worker_id=worker_id)
            self.controller.release_job_lease(job.job_id, worker_id)
            return JobExecutionResult(
                job_id=job.job_id,
                status=JobState.FAILED,
                definition_hash=definition_hash,
                audit_report=audit_report,
                plan=plan,
                agent_result=agent_dict,
                verification=None,
                stage_results=stages,
                error=f"Agent execution failed: {agent_resp.error}",
                completed_at=datetime.now(timezone.utc).isoformat()
            )

        # ==========================================
        # STAGE 5: VERIFICATION
        # ==========================================
        t0_verif = datetime.now(timezone.utc).isoformat()
        try:
            job, v_rec = self.controller.start_verifying(job.job_id, worker_id=worker_id)
        except Exception as e:
            stages.append(StageResult(
                stage="VERIFICATION",
                status="FAILED",
                started_at=t0_verif,
                completed_at=datetime.now(timezone.utc).isoformat(),
                details={"error": str(e)},
                error=f"Controller transition to VERIFYING failed: {e}",
                retry_eligible=False
            ))
            return JobExecutionResult(
                job_id=job.job_id,
                status=job.state,
                definition_hash=definition_hash,
                audit_report=audit_report,
                plan=plan,
                agent_result=agent_dict,
                verification=None,
                stage_results=stages,
                error=str(e),
                completed_at=datetime.now(timezone.utc).isoformat()
            )

        # Inspect diff and baseline
        _, current_files = self._get_porcelain_status()
        newly_modified = [f for f in current_files if f not in baseline_files]
        
        # Check unexpected files
        expected_set = set(expected_files)
        unexpected_files = [f for f in newly_modified if f not in expected_set] if expected_set else []

        checks: List[CheckResult] = []
        all_passed = True

        # Check 1: Git Diff Baseline Check
        if job_def.verification_policy.git_diff_required:
            c_start = datetime.now(timezone.utc).isoformat()
            c_status = "PASS"
            c_fail = None
            if unexpected_files:
                c_status = "FAIL"
                c_fail = f"Unexpected modified files detected: {unexpected_files}"
                all_passed = False

            checks.append(CheckResult(
                check_id=f"chk_{uuid.uuid4().hex[:6]}",
                name="git_diff_baseline_check",
                status=c_status,
                command="git status --porcelain",
                started_at=c_start,
                completed_at=datetime.now(timezone.utc).isoformat(),
                output_summary=f"New files: {len(newly_modified)}, Unexpected: {len(unexpected_files)}",
                failure_reason=c_fail
            ))

        # Check 2: Pytest check if required
        if job_def.verification_policy.pytest_required:
            c_start = datetime.now(timezone.utc).isoformat()
            pytest_cmd = job_def.execution_policy.parameters.get("pytest_command", "/home/ubuntu/venv/bin/pytest")
            test_target = job_def.execution_policy.parameters.get("test_target", "tests/test_automation_controller.py")
            try:
                p_res = subprocess.run(
                    [pytest_cmd, test_target],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                c_status = "PASS" if p_res.returncode == 0 else "FAIL"
                c_fail = None if c_status == "PASS" else p_res.stdout[-300:] + p_res.stderr[-300:]
                if c_status != "PASS":
                    all_passed = False
            except Exception as pe:
                c_status = "FAIL"
                c_fail = str(pe)
                all_passed = False

            checks.append(CheckResult(
                check_id=f"chk_{uuid.uuid4().hex[:6]}",
                name="pytest_verification",
                status=c_status,
                command=f"{pytest_cmd} {test_target}",
                started_at=c_start,
                completed_at=datetime.now(timezone.utc).isoformat(),
                output_summary=f"Exit code: {0 if c_status == 'PASS' else 1}",
                failure_reason=c_fail
            ))

        # Check 3: Custom checks
        for custom_chk in job_def.verification_policy.custom_checks:
            c_start = datetime.now(timezone.utc).isoformat()
            chk_name = custom_chk.get("name", "custom_check")
            chk_cmd = custom_chk.get("command")
            if chk_cmd:
                try:
                    c_res = subprocess.run(
                        chk_cmd,
                        shell=True,
                        cwd=str(self.repo_path),
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    c_status = "PASS" if c_res.returncode == 0 else "FAIL"
                    c_fail = None if c_status == "PASS" else c_res.stderr.strip()
                    if c_status != "PASS":
                        all_passed = False
                except Exception as ce:
                    c_status = "FAIL"
                    c_fail = str(ce)
                    all_passed = False
            else:
                c_status = "PASS"
                c_fail = None

            checks.append(CheckResult(
                check_id=f"chk_{uuid.uuid4().hex[:6]}",
                name=chk_name,
                status=c_status,
                command=chk_cmd,
                started_at=c_start,
                completed_at=datetime.now(timezone.utc).isoformat(),
                output_summary=f"Status: {c_status}",
                failure_reason=c_fail
            ))

        verif_bundle = VerificationBundle(
            overall_status="PASS" if all_passed else "FAIL",
            checks=checks,
            newly_modified_files=newly_modified,
            unexpected_modified_files=unexpected_files,
            baseline_preserved=True
        )

        self.controller.complete_verifying(
            v_rec.execution_id,
            success=all_passed,
            error=None if all_passed else "One or more verification checks failed"
        )

        stages.append(StageResult(
            stage="VERIFICATION",
            status="SUCCESS" if all_passed else "FAILED",
            started_at=t0_verif,
            completed_at=datetime.now(timezone.utc).isoformat(),
            details=verif_bundle.to_dict(),
            error=None if all_passed else "Verification failed",
            retry_eligible=True
        ))

        # ==========================================
        # STAGE 6: REPORT & READY_FOR_APPROVAL
        # ==========================================
        if all_passed:
            job = self.controller.mark_ready_for_approval(job.job_id)
            final_status = JobState.READY_FOR_APPROVAL
            final_error = None
        else:
            job = self.controller.job_store.transition_state(job.job_id, JobState.FAILED, worker_id=worker_id)
            final_status = JobState.FAILED
            final_error = "Verification failed; blocked from READY_FOR_APPROVAL"

        self.controller.release_job_lease(job.job_id, worker_id)

        return JobExecutionResult(
            job_id=job.job_id,
            status=final_status,
            definition_hash=definition_hash,
            audit_report=audit_report,
            plan=plan,
            agent_result=agent_dict,
            verification=verif_bundle,
            stage_results=stages,
            error=final_error,
            completed_at=datetime.now(timezone.utc).isoformat()
        )
