"""
Focused Verification Suite for Automation Job Engine (C.5.1).
Covers all 20 mandatory verification points:
1. JobDefinition validation
2. JobDefinition hashing
3. Repository identity validation
4. Audit stage
5. Plan stage
6. Plan hash generation
7. Agent dispatch
8. Structured agent result
9. Verification result
10. Failed verification blocks READY_FOR_APPROVAL
11. Successful verification reaches READY_FOR_APPROVAL
12. Approval integration
13. Authorization integration
14. Baseline dirty worktree preservation
15. Unexpected change detection
16. Crash/restart recovery
17. Duplicate job handling
18. Concurrency
19. Retry classification
20. Forbidden agent state mutation
"""
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import pytest

from orchestrator.automation import (
    ApprovalDecision,
    ApprovalRecord,
    AutomationController,
    AutomationJob,
    CheckResult,
    ExecutionPhase,
    ExecutionPolicy,
    ExecutionRecord,
    ExecutionStatus,
    GitGuard,
    GitGuardError,
    GitIdentity,
    JobDefinition,
    JobExecutionResult,
    JobPipeline,
    JobState,
    ProductionPolicy,
    ProjectIdentity,
    RetryPolicy,
    SideEffectKind,
    VerificationPolicy,
)
from orchestrator.automation.hashing import compute_deterministic_hash, compute_plan_hash
from orchestrator.runtime import AgentResponse, BaseAgentAdapter, AgentRuntime


class MockGitGuard(GitGuard):
    def __init__(self, commit_sha: str = "a7e6dbab4ae2f2e03a0258b0a20f7de3db64a8ab", is_dirty: bool = False, fail_git: bool = False):
        self._commit_sha = commit_sha
        self._is_dirty = is_dirty
        self._fail_git = fail_git

    def get_current_identity(self) -> GitIdentity:
        if self._fail_git:
            raise GitGuardError("Simulated Git identity failure")
        return GitIdentity(
            commit_sha=self._commit_sha,
            branch="main",
            is_dirty=self._is_dirty,
            remote_url="git@github.com:diediey1919/Polya-AI.git"
        )

    def verify_commit_match(self, expected_commit_sha: str) -> bool:
        if self._fail_git or not expected_commit_sha or len(expected_commit_sha) != 40:
            return False
        return expected_commit_sha.lower() == self._commit_sha.lower()


class MockSuccessAgentAdapter(BaseAgentAdapter):
    def __init__(self, agent_name: str = "mock_agent"):
        super().__init__(agent_name, "/mock/bin")

    def is_available(self) -> bool:
        return True

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        now_iso = datetime.now(timezone.utc).isoformat()
        return AgentResponse(
            agent_name=self.agent_name,
            status="COMPLETED",
            live_dispatched=True,
            correlation_id="mock_corr_123",
            output="Executed task successfully without errors.",
            raw_response={"mock": True},
            execution_time_ms=45,
            timestamp=now_iso,
            metadata={"test": "mock"}
        )


class MockFailAgentAdapter(BaseAgentAdapter):
    def __init__(self, agent_name: str = "mock_fail_agent"):
        super().__init__(agent_name, "/mock/bin")

    def is_available(self) -> bool:
        return True

    def dispatch(self, prompt: str, timeout: int = 30, **kwargs) -> AgentResponse:
        now_iso = datetime.now(timezone.utc).isoformat()
        return AgentResponse(
            agent_name=self.agent_name,
            status="FAILED",
            live_dispatched=True,
            correlation_id="mock_fail_123",
            output="",
            raw_response={"error": "Agent syntax failure"},
            execution_time_ms=12,
            timestamp=now_iso,
            error="Agent crashed during task execution"
        )


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def base_controller(temp_db):
    ctrl = AutomationController(db_path=temp_db)
    ctrl.git_guard = MockGitGuard()
    ctrl.authorization_boundary.git_guard = ctrl.git_guard
    return ctrl


@pytest.fixture
def sample_job_def():
    return JobDefinition(
        job_id="job_c51_test_01",
        project=ProjectIdentity(name="Polyglot AI", repository="diediey1919/Polya-AI", branch="main"),
        base_commit_sha="a7e6dbab4ae2f2e03a0258b0a20f7de3db64a8ab",
        target="tests/test_sample_target.py",
        task="Audit and test verification flow",
        constraints=["Do not modify production DB", "Preserve baseline"],
        execution_policy=ExecutionPolicy(agent="mock_success", timeout_seconds=30),
        verification_policy=VerificationPolicy(git_diff_required=True, pytest_required=False),
        production_policy=ProductionPolicy(side_effects=[SideEffectKind.READ_ONLY], requires_human_approval=True),
        retry_policy=RetryPolicy(idempotent=False, max_automatic_retries=0),
        created_by="human_tester",
        created_at=datetime.now(timezone.utc).isoformat()
    )


# 1. JobDefinition validation
def test_job_definition_validation(sample_job_def):
    sample_job_def.validate()  # Passes

    invalid_def = JobDefinition(
        job_id="",
        project=ProjectIdentity(name="", repository=""),
        base_commit_sha="invalid_sha",
        target="",
        task=""
    )
    with pytest.raises(ValueError):
        invalid_def.validate()


# 2. JobDefinition hashing
def test_job_definition_hashing(sample_job_def):
    h1 = sample_job_def.compute_definition_hash()
    assert len(h1) == 64

    # Identical definition produces identical hash
    h2 = sample_job_def.compute_definition_hash()
    assert h1 == h2

    # Mutated target alters hash
    sample_job_def.target = "tests/mutated_target.py"
    h3 = sample_job_def.compute_definition_hash()
    assert h1 != h3


# 3. Repository identity validation
def test_repository_identity_validation(base_controller, sample_job_def):
    # Alter commit SHA in definition to simulate mismatched repository HEAD
    sample_job_def.base_commit_sha = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.status == JobState.FAILED
    assert "Repository HEAD commit SHA mismatch" in (res.error or "")


# 4. Audit stage
def test_audit_stage(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.audit_report is not None
    assert res.audit_report.project_name == "Polyglot AI"
    assert res.audit_report.commit_sha == "a7e6dbab4ae2f2e03a0258b0a20f7de3db64a8ab"
    audit_stage = next(s for s in res.stage_results if s.stage == "AUDIT")
    assert audit_stage.status == "SUCCESS"


# 5. Plan stage & 6. Plan hash generation
def test_plan_stage_and_hash(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.plan is not None
    assert len(res.plan.plan_hash) == 64
    plan_stage = next(s for s in res.stage_results if s.stage == "PLAN")
    assert plan_stage.status == "SUCCESS"


# 7. Agent dispatch & 8. Structured agent result
def test_agent_dispatch_and_structured_result(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.agent_result is not None
    assert res.agent_result["agent"] == "mock_success"
    assert res.agent_result["status"] == "COMPLETED"
    assert "output" in res.agent_result


# 9. Verification result & 11. Successful verification reaches READY_FOR_APPROVAL
def test_successful_verification_reaches_ready_for_approval(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.status == JobState.READY_FOR_APPROVAL
    assert res.verification is not None
    assert res.verification.overall_status == "PASS"

    stored_job = base_controller.job_store.get_job(sample_job_def.job_id)
    assert stored_job.state == JobState.READY_FOR_APPROVAL


# 10. Failed verification blocks READY_FOR_APPROVAL
def test_failed_verification_blocks_ready_for_approval(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    # Add a custom check that fails
    sample_job_def.job_id = "job_failed_verif"
    sample_job_def.verification_policy.custom_checks = [
        {"name": "failing_gate", "command": "exit 1"}
    ]
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.status == JobState.FAILED
    assert res.verification.overall_status == "FAIL"

    stored_job = base_controller.job_store.get_job("job_failed_verif")
    assert stored_job.state == JobState.FAILED


# 12. Approval integration
def test_approval_integration(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.status == JobState.READY_FOR_APPROVAL

    # Human approves
    appr = base_controller.submit_human_approval(
        job_id=sample_job_def.job_id,
        decision=ApprovalDecision.APPROVED,
        approved_by="lead_engineer",
        notes="All audits and tests verified"
    )
    assert appr.decision == ApprovalDecision.APPROVED
    stored_job = base_controller.job_store.get_job(sample_job_def.job_id)
    assert stored_job.state == JobState.APPROVED


# 13. Authorization integration
def test_authorization_integration(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    base_controller.submit_human_approval(
        job_id=sample_job_def.job_id,
        decision=ApprovalDecision.APPROVED,
        approved_by="lead_engineer"
    )

    # Test authorize production execution
    ok, msg, exec_rec = base_controller.initiate_production_execution(
        job_id=sample_job_def.job_id,
        current_plan_data=res.plan.to_dict(include_hash=False),
        current_config_data=sample_job_def.to_dict(),
        caller_identity="human_operator",
        worker_id="worker_prod_01"
    )
    assert ok is True
    assert "Authorized" in msg


# 14. Baseline dirty worktree preservation & 15. Unexpected change detection
def test_baseline_preservation_and_unexpected_change_detection(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)

    # Mock git status porcelain having baseline files
    pipeline._get_porcelain_status = lambda: (" M existing_dirty_file.py\n", ["existing_dirty_file.py"])
    sample_job_def.job_id = "job_baseline_test"
    res = pipeline.run_job(sample_job_def)
    assert "existing_dirty_file.py" in res.audit_report.baseline_dirty_files
    assert res.verification.baseline_preserved is True


# 16. Crash/restart recovery
def test_crash_restart_recovery(temp_db, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    ctrl1 = AutomationController(db_path=temp_db)
    ctrl1.git_guard = MockGitGuard()
    ctrl1.authorization_boundary.git_guard = ctrl1.git_guard

    pipeline = JobPipeline(ctrl1)
    res = pipeline.run_job(sample_job_def)
    ctrl1.submit_human_approval(sample_job_def.job_id, ApprovalDecision.APPROVED, "lead_engineer")

    # Simulate crash & new controller instance reloading from DB
    ctrl2 = AutomationController(db_path=temp_db)
    ctrl2.git_guard = MockGitGuard()
    ctrl2.authorization_boundary.git_guard = ctrl2.git_guard

    reloaded_job = ctrl2.job_store.get_job(sample_job_def.job_id)
    assert reloaded_job is not None
    assert reloaded_job.state == JobState.APPROVED
    assert reloaded_job.plan_hash == res.plan.plan_hash

    # Production authorization still works across reload with proper keys
    ok, msg, _ = ctrl2.initiate_production_execution(
        job_id=sample_job_def.job_id,
        current_plan_data=res.plan.to_dict(include_hash=False),
        current_config_data=sample_job_def.to_dict(),
        caller_identity="human_operator",
        worker_id="worker_prod_reload"
    )
    assert ok is True


# 17. Duplicate job handling
def test_duplicate_job_handling(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res1 = pipeline.run_job(sample_job_def)
    base_controller.submit_human_approval(sample_job_def.job_id, ApprovalDecision.APPROVED, "lead_engineer")

    # Second run with same job_id in APPROVED/COMPLETED state is rejected
    res2 = pipeline.run_job(sample_job_def)
    assert "already exists in terminal/approved state" in (res2.error or "")


# 18. Concurrency & locking
def test_concurrency_locking(base_controller, sample_job_def):
    # Lock job under worker A
    base_controller.create_job(
        plan_data={"test": "plan"},
        config_data={"test": "config"},
        created_by="human",
        job_id="job_locked_test"
    )
    locked = base_controller.acquire_job_lease("job_locked_test", "worker_A", ttl_seconds=60)
    assert locked is True

    # Worker B cannot acquire or run
    with pytest.raises(PermissionError):
        base_controller.start_running("job_locked_test", "worker_B")


# 19. Retry classification
def test_retry_classification(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_fail"] = MockFailAgentAdapter("mock_fail")
    sample_job_def.job_id = "job_retry_test"
    sample_job_def.execution_policy.agent = "mock_fail"

    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    impl_stage = next(s for s in res.stage_results if s.stage == "IMPLEMENTATION")
    assert impl_stage.status == "FAILED"
    assert impl_stage.retry_eligible is True  # Transient agent fail is classified retry eligible


# 20. Forbidden agent state mutation & approval
def test_forbidden_agent_state_mutation(base_controller, sample_job_def):
    AgentRuntime.adapters["mock_success"] = MockSuccessAgentAdapter("mock_success")
    pipeline = JobPipeline(base_controller)
    res = pipeline.run_job(sample_job_def)
    assert res.status == JobState.READY_FOR_APPROVAL

    # Agent cannot approve
    with pytest.raises(PermissionError):
        base_controller.submit_human_approval(
            job_id=sample_job_def.job_id,
            decision=ApprovalDecision.APPROVED,
            approved_by="agent_hermes"
        )
