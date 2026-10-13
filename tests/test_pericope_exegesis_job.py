"""
Task 1 Test Suite: Pericope Exegesis C5.1 Job Adapter Isolation Tests.
Validates that C5.1 JobDefinition and JobPipeline lifecycle functions
seamlessly with PericopeExegesisJobAdapter without modifying production DB or C5.1 core.
"""

import os
import tempfile
import uuid
import pytest
from unittest.mock import MagicMock, patch

from bible_engine.database import DatabaseEngine
from bible_engine.pipeline import (
    ExegeticalPipeline,
    PipelineConfig,
    PipelineExecutionResult,
    PipelineStage,
)
from bible_engine.validation import ValidationOutcome
from orchestrator.automation.controller import AutomationController
from orchestrator.automation.git_guard import GitGuard, GitIdentity
from orchestrator.automation.job_definition import JobDefinition, SideEffectKind
from orchestrator.automation.job_pipeline import JobPipeline
from orchestrator.automation.job_store import DatabaseManager, JobStore
from orchestrator.automation.jobs.pericope_exegesis_job import (
    PericopeExecutionPayload,
    PericopeExegesisJobAdapter,
)
from orchestrator.automation.states import JobState, ApprovalDecision
from tests.test_automation_controller import MockGitGuard
from tests.test_automation_job_engine_c51 import MockSuccessAgentAdapter, MockFailAgentAdapter
from orchestrator.runtime import AgentRuntime


@pytest.fixture
def temp_job_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def isolated_domain_db():
    engine = DatabaseEngine(":memory:")
    return engine


@pytest.fixture
def mock_controller(temp_job_db):
    ctrl = AutomationController(db_path=temp_job_db)
    ctrl.git_guard = MockGitGuard(
        commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
        is_dirty=False,
        fail_git=False,
    )
    return ctrl


def test_01_job_definition_creation_valid():
    payload = PericopeExecutionPayload(
        pericope_id="PER-ROM-08",
        source_version_id="ver_na28_v1",
        engine_version="4.1.0",
        prompt_config_hash="cfg_hash_test_123",
        model_identity="hermes",
    )

    job_def = PericopeExegesisJobAdapter.create_job_definition(
        payload=payload,
        base_commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
        created_by="test_runner",
    )

    assert isinstance(job_def, JobDefinition)
    assert job_def.job_id.startswith("job_pericope_PER-ROM-08_")
    assert job_def.base_commit_sha == "8995f5e1dec570c1968c69c027584e9c71b7aa81"
    assert job_def.target == "pericope:PER-ROM-08"
    assert job_def.execution_policy.agent == "hermes"
    assert SideEffectKind.READ_ONLY in job_def.production_policy.side_effects
    assert job_def.retry_policy.idempotent is True
    # Validation passes without error
    job_def.validate()


def test_02_job_definition_hash_deterministic():
    payload = PericopeExecutionPayload(
        pericope_id="PER-JOH-01",
        source_version_id="ver_na28_v1",
    )
    job_def1 = PericopeExegesisJobAdapter.create_job_definition(payload)
    job_def2 = PericopeExegesisJobAdapter.create_job_definition(payload)

    hash1 = job_def1.compute_definition_hash()
    hash2 = job_def2.compute_definition_hash()

    assert hash1 == hash2
    assert len(hash1) == 64


def test_03_pericope_identity_deterministic():
    payload1 = PericopeExecutionPayload(
        pericope_id="PER-MAT-05",
        source_version_id="ver_na28_v1",
        source_corpus="NA28",
        target_corpus="AL_QURAN",
    )
    payload2 = PericopeExecutionPayload(
        pericope_id="PER-MAT-05",
        source_version_id="ver_na28_v1",
        source_corpus="NA28",
        target_corpus="AL_QURAN",
    )

    assert payload1.compute_identity_hash() == payload2.compute_identity_hash()


def test_04_job_pipeline_executes_adapter_job(mock_controller, tmp_path):
    orig = AgentRuntime.adapters.get("hermes")
    AgentRuntime.adapters["hermes"] = MockSuccessAgentAdapter("hermes")
    try:
        pipeline = JobPipeline(controller=mock_controller, repo_path=str(tmp_path))
        pipeline._get_porcelain_status = lambda: ("", [])

        payload = PericopeExecutionPayload(
            pericope_id="PER-GAL-02",
            source_version_id="ver_na28_v1",
        )
        job_def = PericopeExegesisJobAdapter.create_job_definition(payload)

        result = pipeline.run_job(job_def=job_def, worker_id="worker_test_1")
        assert result.status == JobState.READY_FOR_APPROVAL
        assert result.error is None
        assert any(s.stage == "IMPLEMENTATION" and s.status == "SUCCESS" for s in result.stage_results)
    finally:
        if orig:
            AgentRuntime.adapters["hermes"] = orig
        else:
            AgentRuntime.adapters.pop("hermes", None)


def test_05_delegates_to_bible_engine_pipeline(isolated_domain_db):
    mock_pipeline = MagicMock(spec=ExegeticalPipeline)
    mock_result = PipelineExecutionResult(
        pipeline_id="pipe-12345",
        status="SUCCESS",
        calibration_run_id="cal-123",
        calibration_identity="ident-abc",
        total_comparisons=5,
        validation_outcome=ValidationOutcome.VALID,
        validation_run_id="val-123",
        certificate_id="cert-123",
        executed_stages=(PipelineStage.RETRIEVAL, PipelineStage.FINAL_VALIDATION),
        committed=True,
    )
    mock_pipeline.execute_pipeline.return_value = mock_result

    payload = PericopeExecutionPayload(
        pericope_id="PER-EPH-02",
        source_version_id="ver_na28_v1",
    )

    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=isolated_domain_db,
        pipeline_factory=lambda db: mock_pipeline,
    )

    assert res == mock_result
    assert mock_pipeline.execute_pipeline.called
    args, kwargs = mock_pipeline.execute_pipeline.call_args
    assert kwargs["source_corpus"] == "NA28"
    assert kwargs["target_corpus"] == "AL_QURAN"
    assert kwargs["retrieval_target"].target_id == "PER-EPH-02"


def test_06_verification_failure_blocks_ready_for_approval(mock_controller, tmp_path):
    orig = AgentRuntime.adapters.get("hermes")
    AgentRuntime.adapters["hermes"] = MockSuccessAgentAdapter("hermes")
    try:
        pipeline = JobPipeline(controller=mock_controller, repo_path=str(tmp_path))
        pipeline._get_porcelain_status = lambda: ("", [])

        payload = PericopeExecutionPayload(
            pericope_id="PER-COL-01",
            source_version_id="ver_na28_v1",
        )
        job_def = PericopeExegesisJobAdapter.create_job_definition(payload)
        job_def.verification_policy.custom_checks = [
            {"name": "failing_domain_validation", "command": "exit 1"}
        ]

        result = pipeline.run_job(job_def=job_def, worker_id="worker_test_fail")
        assert result.status == JobState.FAILED
        assert "Verification failed" in (result.error or "")
    finally:
        if orig:
            AgentRuntime.adapters["hermes"] = orig
        else:
            AgentRuntime.adapters.pop("hermes", None)


def test_07_agent_failure_transitions_to_failed(mock_controller, tmp_path):
    orig = AgentRuntime.adapters.get("hermes")
    AgentRuntime.adapters["hermes"] = MockFailAgentAdapter("hermes")
    try:
        pipeline = JobPipeline(controller=mock_controller, repo_path=str(tmp_path))
        pipeline._get_porcelain_status = lambda: ("", [])

        payload = PericopeExecutionPayload(
            pericope_id="PER-1CO-15",
            source_version_id="ver_na28_v1",
        )
        job_def = PericopeExegesisJobAdapter.create_job_definition(payload)

        result = pipeline.run_job(job_def=job_def, worker_id="worker_test_agent_fail")
        assert result.status == JobState.FAILED
        assert "Agent crashed" in (result.error or "")
    finally:
        if orig:
            AgentRuntime.adapters["hermes"] = orig
        else:
            AgentRuntime.adapters.pop("hermes", None)


def test_08_idempotent_duplicate_job_detection(mock_controller, tmp_path):
    orig = AgentRuntime.adapters.get("hermes")
    AgentRuntime.adapters["hermes"] = MockSuccessAgentAdapter("hermes")
    try:
        pipeline = JobPipeline(controller=mock_controller, repo_path=str(tmp_path))
        pipeline._get_porcelain_status = lambda: ("", [])

        payload = PericopeExecutionPayload(
            pericope_id="PER-HEB-11",
            source_version_id="ver_na28_v1",
        )
        job_def = PericopeExegesisJobAdapter.create_job_definition(payload)

        # First run succeeds to READY_FOR_APPROVAL
        res1 = pipeline.run_job(job_def=job_def, worker_id="worker_test_1")
        assert res1.status == JobState.READY_FOR_APPROVAL

        # Human approves
        mock_controller.submit_human_approval(
            job_id=job_def.job_id,
            decision=ApprovalDecision.APPROVED,
            approved_by="lead_reviewer"
        )

        # Re-running same job_id fails cleanly with terminal message
        res2 = pipeline.run_job(job_def=job_def, worker_id="worker_test_1")
        assert "already exists in terminal/approved state" in (res2.error or "")
    finally:
        if orig:
            AgentRuntime.adapters["hermes"] = orig
        else:
            AgentRuntime.adapters.pop("hermes", None)


def test_09_production_db_path_strictly_prohibited():
    fake_prod_engine = DatabaseEngine("/home/ubuntu/.polya/bible_engine.db")
    payload = PericopeExecutionPayload(
        pericope_id="PER-PROD-01",
        source_version_id="ver_na28_v1",
    )

    with pytest.raises(PermissionError) as exc_info:
        PericopeExegesisJobAdapter.execute_domain_pipeline(
            payload=payload,
            db_engine=fake_prod_engine,
        )
    assert "Production DB execution is prohibited" in str(exc_info.value)
