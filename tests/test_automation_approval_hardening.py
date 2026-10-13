import os
import pytest
from orchestrator.automation.controller import AutomationController
from orchestrator.automation.job_store import ApprovalStore
from orchestrator.automation.models import ApprovalRecord
from orchestrator.automation.states import JobState, ApprovalDecision
from orchestrator.automation.hashing import compute_plan_hash

def _setup_job_in_verification(controller, plan=None, cfg=None, worker_id="w1"):
    if plan is None:
        plan = {"cmd": "build_index"}
    if cfg is None:
        cfg = {"env": "prod"}
    job = controller.create_job(plan, cfg, created_by="tester")
    
    # Fast-forward state to PRODUCTION_VERIFICATION using direct DB or legal flow
    # Since we want to test complete_production_verification, set state in DB directly
    with controller.db_manager._get_connection() as conn:
        conn.execute(
            "UPDATE automation_jobs SET state = ?, worker_id = ? WHERE job_id = ?",
            (JobState.PRODUCTION_VERIFICATION.value, worker_id, job.job_id)
        )
    return controller.job_store.get_job(job.job_id), plan, cfg


def test_complete_production_verification_valid_approval(tmp_path):
    """Test successful verification with valid approval and verified human operator."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    # Record valid human approval
    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-1",
        job_id=job.job_id,
        plan_hash=job.plan_hash,
        commit_sha=job.commit_sha,
        approved_by="human_reviewer",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.APPROVED,
        notes="All checks passed",
    )
    appr_store.record_approval(record)

    # Complete production verification
    completed_job = controller.complete_production_verification(
        job.job_id,
        success=True,
        worker_id="w1",
        operator_identity="sec_human_operator",
    )
    assert completed_job.state == JobState.COMPLETED


def test_complete_production_verification_rejects_missing_approval(tmp_path):
    """Test rejection when no approval record exists."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    with pytest.raises(PermissionError, match="No approval record found"):
        controller.complete_production_verification(
            job.job_id,
            success=True,
            worker_id="w1",
            operator_identity="sec_human_operator",
        )
    
    # Ensure job state remained unchanged (fail-closed)
    fresh_job = controller.job_store.get_job(job.job_id)
    assert fresh_job.state == JobState.PRODUCTION_VERIFICATION


def test_complete_production_verification_rejects_rejected_approval(tmp_path):
    """Test rejection when approval record is REJECTED."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-2",
        job_id=job.job_id,
        plan_hash=job.plan_hash,
        commit_sha=job.commit_sha,
        approved_by="human_reviewer",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.REJECTED,
        notes="Rejected by reviewer",
    )
    appr_store.record_approval(record)

    with pytest.raises(PermissionError, match="expected 'APPROVED'"):
        controller.complete_production_verification(
            job.job_id,
            success=True,
            worker_id="w1",
            operator_identity="sec_human_operator",
        )

    fresh_job = controller.job_store.get_job(job.job_id)
    assert fresh_job.state == JobState.PRODUCTION_VERIFICATION


def test_complete_production_verification_rejects_agent_operator(tmp_path):
    """Test rejection when operator_identity is an agent or autonomous worker."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-3",
        job_id=job.job_id,
        plan_hash=job.plan_hash,
        commit_sha=job.commit_sha,
        approved_by="human_reviewer",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.APPROVED,
        notes="Approved",
    )
    appr_store.record_approval(record)

    for invalid_op in ["agent_auto", "cron_worker", "scheduler_daemon", "worker_node", "supervisor"]:
        with pytest.raises(PermissionError):
            controller.complete_production_verification(
                job.job_id,
                success=True,
                worker_id="w1",
                operator_identity=invalid_op,
            )


def test_complete_production_verification_rejects_plan_hash_mismatch(tmp_path):
    """Test rejection when job plan_hash mutated after approval."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-4",
        job_id=job.job_id,
        plan_hash="different_plan_hash",
        commit_sha=job.commit_sha,
        approved_by="human_reviewer",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.APPROVED,
        notes="Approved for old plan",
    )
    appr_store.record_approval(record)

    with pytest.raises(PermissionError, match="plan_hash mismatch"):
        controller.complete_production_verification(
            job.job_id,
            success=True,
            worker_id="w1",
            operator_identity="sec_human_operator",
        )

    fresh_job = controller.job_store.get_job(job.job_id)
    assert fresh_job.state == JobState.PRODUCTION_VERIFICATION


def test_complete_production_verification_rejects_commit_sha_mismatch(tmp_path):
    """Test rejection when job commit_sha changed after approval."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-5",
        job_id=job.job_id,
        plan_hash=job.plan_hash,
        commit_sha="stale_commit_sha",
        approved_by="human_reviewer",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.APPROVED,
        notes="Approved for old commit",
    )
    appr_store.record_approval(record)

    with pytest.raises(PermissionError, match="commit_sha mismatch"):
        controller.complete_production_verification(
            job.job_id,
            success=True,
            worker_id="w1",
            operator_identity="sec_human_operator",
        )

    fresh_job = controller.job_store.get_job(job.job_id)
    assert fresh_job.state == JobState.PRODUCTION_VERIFICATION


def test_complete_production_verification_rejects_agent_approved_by(tmp_path):
    """Test rejection if approved_by in approval record was an agent."""
    db_file = str(tmp_path / "auto.db")
    controller = AutomationController(db_file)

    job, plan, cfg = _setup_job_in_verification(controller)

    appr_store = ApprovalStore(controller.db_manager)
    record = ApprovalRecord(
        approval_id="appr-6",
        job_id=job.job_id,
        plan_hash=job.plan_hash,
        commit_sha=job.commit_sha,
        approved_by="agent:rogue_ai",
        approved_at="2026-10-01T00:00:00Z",
        decision=ApprovalDecision.APPROVED,
        notes="Rogue approval",
    )
    appr_store.record_approval(record)

    with pytest.raises(PermissionError, match="unauthorized or non-human identity"):
        controller.complete_production_verification(
            job.job_id,
            success=True,
            worker_id="w1",
            operator_identity="human_reviewer",
        )

    fresh_job = controller.job_store.get_job(job.job_id)
    assert fresh_job.state == JobState.PRODUCTION_VERIFICATION
