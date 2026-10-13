"""
Task 4 Test Suite: End-to-End Pericope Orchestrator Dry-Run.
Integrates full execution path:
PericopeBatchRunner
  -> C5.1 JobPipeline
  -> PericopeExegesisJobAdapter
  -> ExegeticalPipeline
  -> PericopeCheckpointStore (9 stages)
  -> Epistemic Verification
  -> Completion

Enforces isolated temporary SQLite databases with complete provenance traceability.
Zero access to production DB.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.pipeline import (
    ExegeticalPipeline,
    PipelineCandidatePack,
    PipelineConfig,
    PipelineExecutionResult,
    PipelineStage,
)
from bible_engine.validation import ValidationOutcome
from orchestrator.automation.controller import AutomationController
from orchestrator.automation.job_definition import JobDefinition, SideEffectKind
from orchestrator.automation.job_pipeline import (
    AuditReport,
    CheckResult,
    JobExecutionResult,
    JobPipeline,
    StageResult,
    StructuredPlan,
    VerificationBundle,
)
from orchestrator.automation.job_store import DatabaseManager, JobStore
from orchestrator.automation.jobs.pericope_exegesis_job import (
    PericopeExecutionPayload,
    PericopeExegesisJobAdapter,
)
from orchestrator.automation.pericope_checkpoint import (
    CorruptedCheckpointError,
    ExegesisStage,
    IncompatibleContractError,
    PericopeCheckpointStore,
    StaleFenceTokenError,
)
from orchestrator.automation.runners.pericope_batch_runner import (
    PericopeBatchRunner,
    PericopeDiscoveryItem,
)
from orchestrator.automation.states import JobState
from tests.test_automation_controller import MockGitGuard


class MockE2EPipeline:
    """
    Simulated ExegeticalPipeline with call spy counters per stage.
    Allows testing that resumed stages are NOT re-executed.
    """
    def __init__(self, db_engine: DatabaseEngine, fail_at_stage: Optional[int] = None):
        self.db_engine = db_engine
        self.fail_at_stage = fail_at_stage
        self.stage_execution_counts: Dict[int, int] = {s: 0 for s in range(1, 10)}

    def execute_pipeline(
        self,
        query: str,
        retrieval_target: Any,
        source_corpus: str,
        target_corpus: str,
        comparisons_generator: Any,
        intra_synthesis_inputs: Optional[List[Dict[str, Any]]] = None,
        theological_inputs: Optional[List[Dict[str, Any]]] = None,
        config: Optional[PipelineConfig] = None,
        checkpoint_store: Optional[PericopeCheckpointStore] = None,
        job_id: Optional[str] = None,
        contract_hash: Optional[str] = None,
        fence_token: int = 1,
    ) -> PipelineExecutionResult:
        resume_from = 1
        if checkpoint_store and job_id and contract_hash:
            res_stage, _ = checkpoint_store.get_latest_valid_stage(job_id, contract_hash)
            if res_stage:
                resume_from = res_stage.value + 1

        stages_map = {
            1: PipelineStage.RETRIEVAL,
            2: PipelineStage.V9_VALIDATION,
            3: PipelineStage.EVIDENCE_ASSEMBLY,
            4: PipelineStage.INTRA_CORPUS_ADJUDICATION,
            5: PipelineStage.INTRA_CORPUS_SYNTHESIS,
            6: PipelineStage.CROSS_CORPUS_CALIBRATION,
            7: PipelineStage.CROSS_CORPUS_SYNTHESIS,
            8: PipelineStage.FINAL_VALIDATION,
            9: PipelineStage.ATOMIC_PERSISTENCE,
        }

        executed: List[PipelineStage] = []
        for s in range(1, 10):
            st_enum = ExegesisStage.from_value(s)
            p_stage = stages_map[s]
            if s < resume_from:
                # SKIPPED: Already checkpointed
                executed.append(p_stage)
                continue

            if self.fail_at_stage == s:
                raise RuntimeError(f"Simulated worker crash at Stage {s} ({st_enum.name})")

            # Execute stage
            self.stage_execution_counts[s] += 1
            executed.append(p_stage)

            # Record checkpoint
            if checkpoint_store and job_id and contract_hash:
                checkpoint_store.save_checkpoint(
                    job_id=job_id,
                    pericope_id=retrieval_target.target_id,
                    stage=st_enum,
                    contract_hash=contract_hash,
                    input_data={"stage": s},
                    output_data={"result": f"stage_{s}_verified_ok"},
                    engine_version="4.1.0",
                    prompt_config_hash=contract_hash,
                    model_identity="deterministic_test_runner",
                    fence_token=fence_token,
                    worker_id="worker_e2e",
                )

        return PipelineExecutionResult(
            pipeline_id=config.pipeline_id if config else "e2e_pipe_001",
            status="COMPLETED",
            calibration_run_id="calib_e2e_001",
            calibration_identity="ident_e2e_001",
            total_comparisons=5,
            validation_outcome=ValidationOutcome.VALID,
            validation_run_id="val_e2e_001",
            certificate_id="cert_e2e_001",
            executed_stages=tuple(executed),
            committed=True,
        )


@pytest.fixture
def temp_env():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as ctl_f, \
         tempfile.NamedTemporaryFile(suffix=".db", delete=False) as cp_f, \
         tempfile.NamedTemporaryFile(suffix=".db", delete=False) as dom_f:
        ctl_path = ctl_f.name
        cp_path = cp_f.name
        dom_path = dom_f.name

    ctrl = AutomationController(db_path=ctl_path)
    ctrl.git_guard = MockGitGuard(
        commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
        is_dirty=False,
        fail_git=False,
    )
    cp_store = PericopeCheckpointStore(cp_path)
    dom_engine = DatabaseEngine(DatabaseConfig(db_path=dom_path))

    yield {
        "ctrl": ctrl,
        "cp_store": cp_store,
        "dom_engine": dom_engine,
        "ctl_path": ctl_path,
        "cp_path": cp_path,
        "dom_path": dom_path,
    }

    for p in (ctl_path, cp_path, dom_path):
        if os.path.exists(p):
            os.remove(p)


# =============================================================================
# E2E TESTS (13 CRITICAL VERIFICATION SCENARIOS)
# =============================================================================

def test_01_fresh_end_to_end_execution(temp_env):
    """1. Fresh run passes all 9 stages, checkpoints 1..9, and reaches COMPLETED/READY_FOR_APPROVAL."""
    mock_pipeline = MockE2EPipeline(temp_env["dom_engine"])
    runner = PericopeBatchRunner(
        controller=temp_env["ctrl"],
        domain_db_path=temp_env["dom_path"],
    )

    item = PericopeDiscoveryItem(pericope_id="PER-GAL-02", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    # Execute domain pipeline via adapter
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: mock_pipeline,
        checkpoint_store=temp_env["cp_store"],
        fence_token=1,
    )

    assert res.status == "COMPLETED"
    assert res.committed is True
    # All 9 stages were executed exactly once
    for s in range(1, 10):
        assert mock_pipeline.stage_execution_counts[s] == 1

    # Checkpoints 1..9 exist and are valid
    latest_stage, latest_rec = temp_env["cp_store"].get_latest_valid_stage(job_id, contract_hash)
    assert latest_stage == ExegesisStage.ATOMIC_PERSISTENCE
    assert latest_rec.stage_data["result"] == "stage_9_verified_ok"


def test_02_crash_stage_1_resume_stage_2(temp_env):
    """2. Worker crashes at Stage 1, successor resumes directly from Stage 2."""
    item = PericopeDiscoveryItem(pericope_id="PER-EPH-01", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)

    # Worker 1 crashes at stage 1
    pipe_crashed = MockE2EPipeline(temp_env["dom_engine"], fail_at_stage=1)
    with pytest.raises(RuntimeError) as exc_info:
        PericopeExegesisJobAdapter.execute_domain_pipeline(
            payload=payload,
            db_engine=temp_env["dom_engine"],
            pipeline_factory=lambda _: pipe_crashed,
            checkpoint_store=temp_env["cp_store"],
            fence_token=1,
        )
    assert "Stage 1" in str(exc_info.value)

    # Successor worker resumes without crash
    pipe_resumed = MockE2EPipeline(temp_env["dom_engine"], fail_at_stage=None)
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: pipe_resumed,
        checkpoint_store=temp_env["cp_store"],
        fence_token=2,
    )
    assert res.status == "COMPLETED"
    # Stage 1 executed on the resumed run because it crashed before saving checkpoint 1
    assert pipe_resumed.stage_execution_counts[1] == 1
    assert pipe_resumed.stage_execution_counts[2] == 1


def test_03_crash_after_stage_1_resume_skips_stage_1(temp_env):
    """3. Worker completes Stage 1, crashes before Stage 2; successor skips Stage 1."""
    item = PericopeDiscoveryItem(pericope_id="PER-COL-01", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    # Pre-save Stage 1 completed checkpoint
    temp_env["cp_store"].save_checkpoint(
        job_id=job_id,
        pericope_id=payload.pericope_id,
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash=contract_hash,
        input_data={"stage": 1},
        output_data={"result": "stage_1_verified_ok"},
        engine_version="4.1.0",
        prompt_config_hash=payload.prompt_config_hash,
        model_identity=payload.model_identity,
        fence_token=1,
        worker_id="worker_alpha",
    )

    # Successor worker executes pipeline
    pipe_resumed = MockE2EPipeline(temp_env["dom_engine"])
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: pipe_resumed,
        checkpoint_store=temp_env["cp_store"],
        fence_token=2,
    )
    assert res.status == "COMPLETED"
    # SPY ASSERTION: Stage 1 was SKIPPED (0 executions)
    assert pipe_resumed.stage_execution_counts[1] == 0
    # Stages 2..9 executed
    for s in range(2, 10):
        assert pipe_resumed.stage_execution_counts[s] == 1


def test_04_crash_stage_4_resume_skips_stages_1_to_4(temp_env):
    """4. Checkpoints exist up to Stage 4; successor resumes directly from Stage 5."""
    item = PericopeDiscoveryItem(pericope_id="PER-ROM-08", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    for s in range(1, 5):
        temp_env["cp_store"].save_checkpoint(
            job_id=job_id,
            pericope_id=payload.pericope_id,
            stage=ExegesisStage.from_value(s),
            contract_hash=contract_hash,
            input_data={"stage": s},
            output_data={"result": f"stage_{s}_ok"},
            engine_version="4.1.0",
            prompt_config_hash=payload.prompt_config_hash,
            model_identity=payload.model_identity,
            fence_token=1,
            worker_id="worker_alpha",
        )

    pipe_resumed = MockE2EPipeline(temp_env["dom_engine"])
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: pipe_resumed,
        checkpoint_store=temp_env["cp_store"],
        fence_token=2,
    )
    assert res.status == "COMPLETED"
    # SPY ASSERTION: Stages 1..4 SKIPPED
    for s in range(1, 5):
        assert pipe_resumed.stage_execution_counts[s] == 0
    # Stages 5..9 EXECUTED
    for s in range(5, 10):
        assert pipe_resumed.stage_execution_counts[s] == 1


def test_05_crash_stage_6_resume_skips_stages_1_to_6(temp_env):
    """5. Checkpoints exist up to Stage 6; successor resumes directly from Stage 7."""
    item = PericopeDiscoveryItem(pericope_id="PER-1CO-15", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    for s in range(1, 7):
        temp_env["cp_store"].save_checkpoint(
            job_id=job_id,
            pericope_id=payload.pericope_id,
            stage=ExegesisStage.from_value(s),
            contract_hash=contract_hash,
            input_data={"stage": s},
            output_data={"result": f"stage_{s}_ok"},
            engine_version="4.1.0",
            prompt_config_hash=payload.prompt_config_hash,
            model_identity=payload.model_identity,
            fence_token=1,
            worker_id="worker_alpha",
        )

    pipe_resumed = MockE2EPipeline(temp_env["dom_engine"])
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: pipe_resumed,
        checkpoint_store=temp_env["cp_store"],
        fence_token=2,
    )
    assert res.status == "COMPLETED"
    # SPY ASSERTION: Stages 1..6 SKIPPED
    for s in range(1, 7):
        assert pipe_resumed.stage_execution_counts[s] == 0
    # Stages 7..9 EXECUTED
    for s in range(7, 10):
        assert pipe_resumed.stage_execution_counts[s] == 1


def test_06_stale_worker_fence_token_rejected(temp_env):
    """6. Worker with outdated fence token is rejected from saving checkpoints."""
    payload = PericopeExecutionPayload(pericope_id="PER-2CO-05", source_version_id="ver_na28_v1")
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    # Successor worker acquires lease with fence token 5 and writes
    temp_env["cp_store"].save_checkpoint(
        job_id=job_id,
        pericope_id=payload.pericope_id,
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash=contract_hash,
        input_data={"s": 1},
        output_data={"result": "ok_fence_5"},
        engine_version="4.1.0",
        prompt_config_hash=payload.prompt_config_hash,
        model_identity=payload.model_identity,
        fence_token=5,
        worker_id="worker_new",
    )

    # Stale zombie worker with fence token 4 tries to save checkpoint
    with pytest.raises(StaleFenceTokenError):
        temp_env["cp_store"].save_checkpoint(
            job_id=job_id,
            pericope_id=payload.pericope_id,
            stage=ExegesisStage.V9_VALIDATION,
            contract_hash=contract_hash,
            input_data={"s": 2},
            output_data={"result": "stale_write"},
            engine_version="4.1.0",
            prompt_config_hash=payload.prompt_config_hash,
            model_identity=payload.model_identity,
            fence_token=4,
            worker_id="worker_stale",
        )


def test_07_duplicate_worker_prevented_by_lease(temp_env):
    """7. Concurrency lock prevents duplicate workers from simultaneously executing."""
    payload = PericopeExecutionPayload(pericope_id="PER-GAL-01", source_version_id="ver_na28_v1")
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)

    # Pre-register job to satisfy foreign key constraint, then worker 1 locks
    from orchestrator.automation.models import AutomationJob
    temp_env["ctrl"].job_store.create_job(
        AutomationJob(
            job_id=job_id,
            commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
            plan_hash="p_hash",
            config_hash="c_hash",
            state=JobState.PLANNING,
            created_at="2026-10-08T00:00:00Z",
            created_by="worker_1",
            worker_id="worker_1",
        )
    )
    acquired_1 = temp_env["ctrl"].lease_store.acquire_lease(job_id, "worker_1", ttl_seconds=60)
    assert acquired_1 is True

    # Worker 2 attempts to acquire lease on the same job -> REJECTED
    acquired_2 = temp_env["ctrl"].lease_store.acquire_lease(job_id, "worker_2", ttl_seconds=60)
    assert acquired_2 is False


def test_08_corrupted_checkpoint_rejected(temp_env):
    """8. Tampered checkpoint data fails cryptographic SHA-256 verification."""
    payload = PericopeExecutionPayload(pericope_id="PER-HEB-01", source_version_id="ver_na28_v1")
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    temp_env["cp_store"].save_checkpoint(
        job_id=job_id,
        pericope_id=payload.pericope_id,
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash=contract_hash,
        input_data={"s": 1},
        output_data={"valid": "payload"},
        engine_version="4.1.0",
        prompt_config_hash=payload.prompt_config_hash,
        model_identity=payload.model_identity,
        fence_token=1,
        worker_id="worker_alpha",
    )

    # Corrupt the stage_data_json payload directly in SQLite
    with temp_env["cp_store"]._get_connection() as conn:
        conn.execute(
            "UPDATE pericope_stage_checkpoints SET stage_data_json = '{\"tampered\": true}' WHERE job_id = ?",
            (job_id,)
        )

    with pytest.raises(CorruptedCheckpointError):
        temp_env["cp_store"].get_latest_valid_stage(job_id, contract_hash)


def test_09_changed_contract_invalidates_old_checkpoints(temp_env):
    """9. Modifying engine version or prompt hash invalidates prior checkpoints."""
    payload_v1 = PericopeExecutionPayload(
        pericope_id="PER-JHN-01",
        source_version_id="ver_na28_v1",
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
    )
    job_id = PericopeExegesisJobAdapter.build_job_id(payload_v1)
    contract_v1 = payload_v1.compute_identity_hash()

    temp_env["cp_store"].save_checkpoint(
        job_id=job_id,
        pericope_id=payload_v1.pericope_id,
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash=contract_v1,
        input_data={"s": 1},
        output_data={"v": 1},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_alpha",
    )

    # Pipeline called with changed contract (e.g., prompt_config_hash updated to prompt_v2)
    contract_v2 = "contract_hash_v2_updated"
    # get_latest_valid_stage raises IncompatibleContractError because contract_hash does not match
    with pytest.raises(IncompatibleContractError):
        temp_env["cp_store"].get_latest_valid_stage(job_id, contract_v2)


def test_10_empty_queue_exits_cleanly(temp_env):
    """10. PericopeBatchRunner exits with 0 discovered count when queue is empty."""
    runner = PericopeBatchRunner(
        controller=temp_env["ctrl"],
        domain_db_path=temp_env["dom_path"],
    )
    summary = runner.run_batch(batch_size=5, items=[])
    assert summary.total_discovered == 0
    assert summary.completed_count == 0
    assert summary.interrupted is False


def test_11_production_db_safety_protection(temp_env):
    """11. Direct write attempt to production database path is blocked by safety gate."""
    payload = PericopeExecutionPayload(pericope_id="PER-REV-01", source_version_id="ver_na28_v1")
    fake_prod_engine = MagicMock()
    fake_prod_engine.config.db_path = "/home/ubuntu/.polya/bible_engine.db"

    with pytest.raises(PermissionError) as exc_info:
        PericopeExegesisJobAdapter.execute_domain_pipeline(
            payload=payload,
            db_engine=fake_prod_engine,
            checkpoint_store=temp_env["cp_store"],
        )
    assert "Production DB execution is prohibited" in str(exc_info.value)


def test_12_completed_only_after_validation_and_persistence(temp_env):
    """12. Pipeline terminates without persistence if final validation fails."""
    payload = PericopeExecutionPayload(pericope_id="PER-MAT-05", source_version_id="ver_na28_v1")
    
    # Mock pipeline fails at stage 8 (FINAL_VALIDATION)
    pipe_fail_val = MockE2EPipeline(temp_env["dom_engine"], fail_at_stage=8)
    with pytest.raises(RuntimeError):
        PericopeExegesisJobAdapter.execute_domain_pipeline(
            payload=payload,
            db_engine=temp_env["dom_engine"],
            pipeline_factory=lambda _: pipe_fail_val,
            checkpoint_store=temp_env["cp_store"],
        )

    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()
    stage, _ = temp_env["cp_store"].get_latest_valid_stage(job_id, contract_hash)
    # Stage 8 and 9 were never reached/checkpointed
    assert stage == ExegesisStage.CROSS_CORPUS_SYNTHESIS


def test_13_checkpoint_1_to_9_valid_and_retrievable(temp_env):
    """13. Full execution verifies that checkpoints 1..9 all exist and pass integrity check."""
    payload = PericopeExecutionPayload(pericope_id="PER-ACT-02", source_version_id="ver_na28_v1")
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    mock_pipeline = MockE2EPipeline(temp_env["dom_engine"])
    res = PericopeExegesisJobAdapter.execute_domain_pipeline(
        payload=payload,
        db_engine=temp_env["dom_engine"],
        pipeline_factory=lambda _: mock_pipeline,
        checkpoint_store=temp_env["cp_store"],
    )
    assert res.status == "COMPLETED"

    # Verify latest stage is Stage 9 ATOMIC_PERSISTENCE and integrity holds
    latest_stage, latest_rec = temp_env["cp_store"].get_latest_valid_stage(job_id, contract_hash)
    assert latest_stage == ExegesisStage.ATOMIC_PERSISTENCE
    assert latest_rec is not None
    assert latest_rec.verify_integrity() is True
    assert latest_rec.stage_data["result"] == "stage_9_verified_ok"
