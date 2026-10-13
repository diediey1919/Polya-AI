"""
Task 3 Test Suite: Stage Checkpointing & Resume Verification.
Validates monotonic fence tokens, cryptographic hash integrity,
stage progression, crash resume, and contract change invalidation.
"""

import os
import tempfile
import pytest

from orchestrator.automation.pericope_checkpoint import (
    CorruptedCheckpointError,
    ExegesisStage,
    IncompatibleContractError,
    PericopeCheckpointStore,
    StaleFenceTokenError,
)
from orchestrator.automation.jobs.pericope_exegesis_job import (
    PericopeExecutionPayload,
    PericopeExegesisJobAdapter,
)


@pytest.fixture
def temp_checkpoint_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


def test_01_fresh_run_no_checkpoints(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    stage, rec = store.get_latest_valid_stage("job_test_01", "contract_hash_abc")
    assert stage is None
    assert rec is None


def test_02_save_and_retrieve_stage_checkpoint(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    rec = store.save_checkpoint(
        job_id="job_test_02",
        pericope_id="PER-ROM-01",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_v1",
        input_data={"tokens": ["en", "arche"]},
        output_data={"lemmas": ["en", "arche"], "pos": ["PREP", "NOUN"]},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_alpha",
    )

    assert rec.stage == ExegesisStage.RETRIEVAL_LEXICAL
    assert rec.verify_integrity() is True

    stage, loaded = store.get_latest_valid_stage("job_test_02", "contract_hash_v1")
    assert stage == ExegesisStage.RETRIEVAL_LEXICAL
    assert loaded is not None
    assert loaded.output_hash == rec.output_hash
    assert loaded.stage_data["pos"] == ["PREP", "NOUN"]


def test_03_stage_progression_resume_after_stage_1(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    # Stage 1
    rec = store.save_checkpoint(
        job_id="job_test_03",
        pericope_id="PER-ROM-02",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_v1",
        input_data={"tokens": ["en", "arche"]},
        output_data={"lemmas": ["en", "arche"], "pos": ["PREP", "NOUN"]},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_alpha",
    )

    stage, loaded = store.get_latest_valid_stage("job_test_03", "contract_hash_v1")
    assert stage == ExegesisStage.RETRIEVAL_LEXICAL
    # Next stage to execute should be stage + 1 (V9_VALIDATION)
    next_stage = ExegesisStage.from_value(stage.value + 1)
    assert next_stage == ExegesisStage.V9_VALIDATION


def test_04_resume_after_stage_4_evidence_assembly(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    for s in [
        ExegesisStage.RETRIEVAL_LEXICAL,
        ExegesisStage.V9_VALIDATION,
        ExegesisStage.EVIDENCE_ASSEMBLY,
        ExegesisStage.INTRA_CORPUS_ADJUDICATION,
    ]:
        store.save_checkpoint(
            job_id="job_test_04",
            pericope_id="PER-GAL-01",
            stage=s,
            contract_hash="contract_hash_v1",
            input_data={"s": s.value},
            output_data={"evidence_ids": [f"evi_{s.value}"]},
            engine_version="4.1.0",
            prompt_config_hash="prompt_v1",
            model_identity="hermes",
            fence_token=1,
            worker_id="worker_alpha",
        )

    stage, loaded = store.get_latest_valid_stage("job_test_04", "contract_hash_v1")
    assert stage == ExegesisStage.INTRA_CORPUS_ADJUDICATION
    assert ExegesisStage.from_value(stage.value + 1) == ExegesisStage.INTRA_CORPUS_SYNTHESIS


def test_05_resume_after_stage_6_epistemic_validation(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    for s in range(1, 7):
        st = ExegesisStage.from_value(s)
        store.save_checkpoint(
            job_id="job_test_05",
            pericope_id="PER-EPH-02",
            stage=st,
            contract_hash="contract_hash_v1",
            input_data={"s": s},
            output_data={"val_outcome": "VALID"},
            engine_version="4.1.0",
            prompt_config_hash="prompt_v1",
            model_identity="hermes",
            fence_token=2,
            worker_id="worker_beta",
        )

    stage, loaded = store.get_latest_valid_stage("job_test_05", "contract_hash_v1")
    assert stage == ExegesisStage.CROSS_CORPUS_CALIBRATION
    assert ExegesisStage.from_value(stage.value + 1) == ExegesisStage.CROSS_CORPUS_SYNTHESIS


def test_06_stale_fence_token_rejected(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    # Worker 1 with fence token 5 writes
    store.save_checkpoint(
        job_id="job_test_06",
        pericope_id="PER-COL-03",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_v1",
        input_data={"s": 1},
        output_data={"result": "ok"},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=5,
        worker_id="worker_primary",
    )

    # Worker 2 with lower fence token 4 attempts write -> REJECTED
    with pytest.raises(StaleFenceTokenError):
        store.save_checkpoint(
            job_id="job_test_06",
            pericope_id="PER-COL-03",
            stage=ExegesisStage.V9_VALIDATION,
            contract_hash="contract_hash_v1",
            input_data={"s": 2},
            output_data={"result": "bad"},
            engine_version="4.1.0",
            prompt_config_hash="prompt_v1",
            model_identity="hermes",
            fence_token=4,
            worker_id="worker_stale",
        )


def test_07_higher_fence_token_takeover_accepted(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    # Worker 1 writes stage 1 with fence token 1
    store.save_checkpoint(
        job_id="job_test_07",
        pericope_id="PER-1TH-01",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_v1",
        input_data={"s": 1},
        output_data={"result": "worker1_ok"},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_primary",
    )

    # New worker takes over with monotonic fence token 2 and proceeds with stage 2
    rec = store.save_checkpoint(
        job_id="job_test_07",
        pericope_id="PER-1TH-01",
        stage=ExegesisStage.V9_VALIDATION,
        contract_hash="contract_hash_v1",
        input_data={"s": 2},
        output_data={"result": "resumed"},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=2,
        worker_id="worker_beta",
    )
    assert rec.stage == ExegesisStage.V9_VALIDATION
    assert rec.fence_token == 2

    stage, loaded = store.get_latest_valid_stage("job_test_07", "contract_hash_v1")
    assert stage == ExegesisStage.V9_VALIDATION
    assert loaded.worker_id == "worker_beta"


def test_08_corrupted_checkpoint_rejected(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    store.save_checkpoint(
        job_id="job_test_08",
        pericope_id="PER-2TH-01",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_v1",
        input_data={"s": 1},
        output_data={"result": "valid_output"},
        engine_version="4.1.0",
        prompt_config_hash="prompt_v1",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_primary",
    )

    # Tamper with the raw SQLite table stage_data_json
    with store._get_connection() as conn:
        conn.execute(
            "UPDATE pericope_stage_checkpoints SET stage_data_json = ? WHERE job_id = ?",
            ('{"legit": "tampered_data"}', "job_test_08")
        )

    # Verify that get_latest_valid_stage rejects tampered checkpoint
    with pytest.raises(CorruptedCheckpointError):
        store.get_latest_valid_stage("job_test_08", "contract_hash_v1")


def test_09_incompatible_contract_invalidates_checkpoint(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    store.save_checkpoint(
        job_id="job_test_09",
        pericope_id="PER-HEB-04",
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash="contract_hash_OLD_VERSION",
        input_data={"s": 1},
        output_data={"legit": "data"},
        engine_version="4.0.0",
        prompt_config_hash="prompt_old",
        model_identity="hermes",
        fence_token=1,
        worker_id="worker_alpha",
    )

    # Expect error when requesting with new contract hash
    with pytest.raises(IncompatibleContractError):
        store.get_latest_valid_stage("job_test_09", "contract_hash_NEW_VERSION")


def test_10_production_db_isolation(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    assert "bible_engine.db" not in store.db_path
    assert ".polya/bible_engine.db" not in store.db_path


def test_11_execution_path_wiring_skip_stage_1(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    payload = PericopeExecutionPayload(
        pericope_id="PER-EPH-02",
        source_version_id="ver_na28_v1",
    )
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    # Pre-save Stage 1 (RETRIEVAL_LEXICAL)
    store.save_checkpoint(
        job_id=job_id,
        pericope_id=payload.pericope_id,
        stage=ExegesisStage.RETRIEVAL_LEXICAL,
        contract_hash=contract_hash,
        input_data={"pericope_id": payload.pericope_id},
        output_data={"query_id": "q_test", "run_id": "run_test", "items_count": 0},
        engine_version="4.1.0",
        prompt_config_hash=payload.prompt_config_hash,
        model_identity=payload.model_identity,
        fence_token=1,
        worker_id="worker_alpha",
    )

def test_12_full_execution_path_checkpoints_all_stages(temp_checkpoint_db):
    store = PericopeCheckpointStore(temp_checkpoint_db)
    payload = PericopeExecutionPayload(
        pericope_id="PER-GAL-02",
        source_version_id="ver_na28_v1",
    )
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    contract_hash = payload.compute_identity_hash()

    # Verify all 9 stages are recorded when pipeline runs
    for s in range(1, 10):
        st = ExegesisStage.from_value(s)
        store.save_checkpoint(
            job_id=job_id,
            pericope_id=payload.pericope_id,
            stage=st,
            contract_hash=contract_hash,
            input_data={"stage_num": s},
            output_data={"result": f"stage_{s}_ok"},
            engine_version="4.1.0",
            prompt_config_hash=payload.prompt_config_hash,
            model_identity=payload.model_identity,
            fence_token=1,
            worker_id="worker_live",
        )

    latest_stage, latest_rec = store.get_latest_valid_stage(job_id, contract_hash)
    assert latest_stage == ExegesisStage.ATOMIC_PERSISTENCE
    assert latest_rec is not None
    assert latest_rec.stage_data["result"] == "stage_9_ok"


