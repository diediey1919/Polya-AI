"""
Task 2 Test Suite: Pericope Batch Runner Isolation & Lifecycle Tests.
Validates scheduler wake-up, lease locking, idempotency, graceful shutdown,
exit codes, and production DB safety without external network or LLM calls.
"""

import os
import signal
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch

from orchestrator.automation.controller import AutomationController
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
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.runners.pericope_batch_runner import (
    BatchExecutionSummary,
    PericopeBatchRunner,
    PericopeDiscoveryItem,
    RunnerExitCode,
    main,
    parse_args,
)
from orchestrator.automation.states import JobState
from tests.test_automation_controller import MockGitGuard


@pytest.fixture
def temp_controller_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def temp_domain_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    # Seed mock pericopes table
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE pericopes (
            pericope_id TEXT PRIMARY KEY,
            book_id TEXT,
            status TEXT
        );
    """)
    conn.execute("INSERT INTO pericopes VALUES ('PER-ROM-01', 'ROM', 'REGISTERED');")
    conn.execute("INSERT INTO pericopes VALUES ('PER-ROM-02', 'ROM', 'INGESTED');")
    conn.execute("INSERT INTO pericopes VALUES ('PER-ROM-03', 'ROM', 'REGISTERED');")
    conn.execute("INSERT INTO pericopes VALUES ('PER-ROM-04', 'ROM', 'VALIDATED');") # not eligible
    conn.commit()
    conn.close()

    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def mock_controller(temp_controller_db):
    ctrl = AutomationController(db_path=temp_controller_db)
    ctrl.git_guard = MockGitGuard(
        commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
        is_dirty=False,
        fail_git=False,
    )
    return ctrl


def make_mock_pipeline_result(job_id: str, status: JobState, error: str = None) -> JobExecutionResult:
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return JobExecutionResult(
        job_id=job_id,
        status=status,
        definition_hash="mock_def_hash_12345",
        audit_report=AuditReport(
            project_name="Polya-AI",
            repository="/home/ubuntu/Polya-AI",
            branch="main",
            commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
            is_dirty=False,
            baseline_status_porcelain="",
            baseline_dirty_files=[],
            target=f"pericope:{job_id}",
            timestamp=now_iso,
        ),
        plan=StructuredPlan(
            plan_id="plan_123",
            target=f"pericope:{job_id}",
            architecture="domain_pipeline",
            files_expected_to_change=[],
            implementation_steps=[],
            verification_steps=[],
            side_effects=[],
            risks=[],
            plan_hash="mock_plan_hash"
        ),
        agent_result={"status": "COMPLETED"},
        verification=VerificationBundle(
            overall_status="PASS" if status == JobState.READY_FOR_APPROVAL else "FAIL",
            checks=[],
            newly_modified_files=[],
            unexpected_modified_files=[],
            baseline_preserved=True
        ),
        stage_results=[],
        error=error,
        completed_at=now_iso,
    )


# =============================================================================
# TEST CASES
# =============================================================================

def test_01_discover_eligible_pericopes(mock_controller, temp_domain_db):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=temp_domain_db,
    )
    discovered = runner.discover_eligible_pericopes(limit=10)
    assert len(discovered) == 3
    ids = [d.pericope_id for d in discovered]
    assert ids == ["PER-ROM-01", "PER-ROM-02", "PER-ROM-03"]


def test_02_batch_size_respected(mock_controller, temp_domain_db):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=temp_domain_db,
    )
    discovered = runner.discover_eligible_pericopes(limit=2)
    assert len(discovered) == 2


def test_03_deterministic_job_identity(mock_controller):
    item = PericopeDiscoveryItem(
        pericope_id="PER-GAL-01",
        source_version_id="ver_na28_v1",
    )
    payload = PericopeExecutionPayload(
        pericope_id=item.pericope_id,
        source_version_id=item.source_version_id,
    )
    job_id_1 = PericopeExegesisJobAdapter.build_job_id(payload)
    job_id_2 = PericopeExegesisJobAdapter.build_job_id(payload)
    assert job_id_1 == job_id_2
    assert "PER-GAL-01" in job_id_1


def test_04_completed_job_skipped_idempotently(mock_controller):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
    )
    item = PericopeDiscoveryItem(pericope_id="PER-EPH-01", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)

    # Pre-seed job in COMPLETED state
    mock_controller.job_store.create_job(
        AutomationJob(
            job_id=job_id,
            commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
            plan_hash="p_hash",
            config_hash="c_hash",
            state=JobState.COMPLETED,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            created_by="test",
        )
    )

    summary = runner.run_batch(batch_size=5, items=[item])
    assert summary.total_discovered == 1
    assert summary.skipped_count == 1
    assert summary.leased_count == 0
    assert summary.completed_count == 0


def test_05_lease_acquired_and_released_on_success(mock_controller):
    mock_pipeline = MagicMock()
    mock_pipeline.execute_job.return_value = make_mock_pipeline_result(
        job_id="test_job",
        status=JobState.READY_FOR_APPROVAL
    )

    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
        pipeline_factory=lambda c, r: mock_pipeline,
    )

    item = PericopeDiscoveryItem(pericope_id="PER-COL-01", source_version_id="ver_na28_v1")
    summary = runner.run_batch(batch_size=1, items=[item])

    assert summary.completed_count == 1
    assert summary.leased_count == 1
    assert summary.failed_terminal_count == 0

    # Ensure lease is released
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    assert not mock_controller.lease_store.is_locked_by_other(job_id, "different_worker")


def test_06_lease_rejection_skipped_safely(mock_controller):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
    )
    item = PericopeDiscoveryItem(pericope_id="PER-TIT-01", source_version_id="ver_na28_v1")
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)

    # Pre-register job to satisfy foreign key constraint, then pre-lock
    mock_controller.job_store.create_job(
        AutomationJob(
            job_id=job_id,
            commit_sha="8995f5e1dec570c1968c69c027584e9c71b7aa81",
            plan_hash="plan_pre",
            config_hash="cfg_pre",
            state=JobState.RUNNING,
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="other_worker",
            worker_id="other_worker",
        )
    )
    mock_controller.lease_store.acquire_lease(job_id=job_id, worker_id="other_worker_xyz", ttl_seconds=600)

    summary = runner.run_batch(batch_size=1, items=[item])
    assert summary.skipped_count == 1
    assert summary.leased_count == 0
    assert summary.details[0]["status"] == "SKIPPED_LEASE_LOCKED"


def test_07_lease_released_on_failure(mock_controller):
    mock_pipeline = MagicMock()
    mock_pipeline.execute_job.return_value = make_mock_pipeline_result(
        job_id="test_job",
        status=JobState.FAILED,
        error="Verification check rejected candidate exegesis"
    )

    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
        pipeline_factory=lambda c, r: mock_pipeline,
    )

    item = PericopeDiscoveryItem(pericope_id="PER-PHM-01", source_version_id="ver_na28_v1")
    summary = runner.run_batch(batch_size=1, items=[item])

    assert summary.failed_terminal_count == 1
    payload = PericopeExecutionPayload(pericope_id=item.pericope_id, source_version_id=item.source_version_id)
    job_id = PericopeExegesisJobAdapter.build_job_id(payload)
    assert not mock_controller.lease_store.is_locked_by_other(job_id, "different_worker")


def test_08_graceful_shutdown_on_signal(mock_controller):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
    )

    # Simulate shutdown request before loop
    runner.request_shutdown(signal.SIGINT, None)

    items = [
        PericopeDiscoveryItem(pericope_id="PER-1TH-01", source_version_id="ver_na28_v1"),
        PericopeDiscoveryItem(pericope_id="PER-1TH-02", source_version_id="ver_na28_v1"),
    ]

    summary = runner.run_batch(batch_size=5, items=items)
    assert summary.interrupted is True
    assert summary.leased_count == 0
    assert summary.completed_count == 0


def test_09_production_db_safety_protection(mock_controller):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path="/home/ubuntu/.polya/bible_engine.db",
    )

    with pytest.raises(PermissionError) as exc_info:
        runner.discover_eligible_pericopes(limit=5)
    assert "Direct discovery on production DB without authorization is prohibited" in str(exc_info.value)


def test_10_empty_queue_exits_cleanly(mock_controller):
    runner = PericopeBatchRunner(
        controller=mock_controller,
        domain_db_path=":memory:",
    )
    summary = runner.run_batch(batch_size=5, items=[])
    assert summary.total_discovered == 0
    assert summary.leased_count == 0
    assert summary.completed_count == 0
    assert summary.failed_terminal_count == 0


def test_11_cli_argument_parsing():
    args = parse_args(["--batch-size", "4", "--domain-db", "/tmp/mock.db", "--allow-production-db"])
    assert args.batch_size == 4
    assert args.domain_db == "/tmp/mock.db"
    assert args.allow_production_db is True
