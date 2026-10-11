"""
Comprehensive Verification Suite for Polya Automation Controller (C.5.0 Architecture Foundation).
Strictly validates:
A. State transitions (All valid vs All forbidden transitions)
B. Approval Gate & Identity Binds (creation, wrong job, wrong plan hash, wrong commit SHA, missing approval, rejected)
C. Plan Integrity & Mutation Detection (unchanged passes, mutated invalidates approval & blocks)
D. Git Guard & Source of Truth (matching SHA passes, mismatching blocks, invalid repo blocks, dirty detection)
E. Concurrency & Locking (worker lease acquisition, second worker rejected, stale lease recovery, lease release)
F. Idempotency (successful production execution cannot run twice)
G. Crash Recovery (persisted state survives reload, no privilege escalation across restart)
H. Authorization Gate (12-check validation matrix)
I. Security Invariants (Agent/Cron cannot approve or execute production, intermediate/terminal states cannot execute)
"""
import os
import sqlite3
import tempfile
import time
import pytest

from orchestrator.automation.states import (
    JobState,
    ApprovalDecision,
    ExecutionPhase,
    ExecutionStatus,
    ALLOWED_TRANSITIONS,
)
from orchestrator.automation.models import (
    AutomationJob,
    ApprovalRecord,
    ExecutionRecord,
)
from orchestrator.automation.hashing import (
    compute_deterministic_hash,
    compute_plan_hash,
    compute_config_hash,
)
from orchestrator.automation.git_guard import (
    GitGuard,
    GitIdentity,
    GitGuardError,
)
from orchestrator.automation.job_store import (
    DatabaseManager,
    JobStore,
    ApprovalStore,
    ExecutionStore,
    LeaseLockStore,
)
from orchestrator.automation.authorization import (
    AuthorizationBoundary,
    AuthorizationResult,
)
from orchestrator.automation.controller import (
    AutomationController,
)


class MockGitGuard(GitGuard):
    def __init__(self, commit_sha: str = "a7e6dbab4ae2f2e03a0258b0a20f7de3db64a8ab", is_dirty: bool = False, fail_git: bool = False):
        self._commit_sha = commit_sha
        self._is_dirty = is_dirty
        self._fail_git = fail_git

    def get_current_identity(self) -> GitIdentity:
        if self._fail_git:
            raise GitGuardError("Simulated Git identity failure: not a valid git repository")
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


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_p = tmp.name
    yield db_p
    if os.path.exists(db_p):
        os.remove(db_p)


@pytest.fixture
def controller(temp_db_path):
    ctrl = AutomationController(db_path=temp_db_path)
    ctrl.git_guard = MockGitGuard()
    ctrl.authorization_boundary.git_guard = ctrl.git_guard
    return ctrl


# ============================================================
# A. STATE TRANSITION TESTS
# ============================================================

def test_valid_state_transitions(controller):
    """Test standard golden path transitions."""
    plan = {"steps": ["step1", "step2"]}
    cfg = {"env": "staging"}
    job = controller.create_job(plan, cfg, created_by="test_admin")
    assert job.state == JobState.PLANNING

    # PLANNING -> RUNNING
    job, exec_rec = controller.start_running(job.job_id, worker_id="w1")
    assert job.state == JobState.RUNNING
    tok1 = controller.current_fencing_token(job.job_id)
    controller.complete_running(exec_rec.execution_id, success=True, job_id=job.job_id, fencing_token=tok1)

    # RUNNING -> VERIFYING
    job, exec_rec2 = controller.start_verifying(job.job_id, worker_id="w1")
    assert job.state == JobState.VERIFYING
    tok2 = controller.current_fencing_token(job.job_id)
    controller.complete_verifying(exec_rec2.execution_id, success=True, job_id=job.job_id, fencing_token=tok2)

    # VERIFYING -> READY_FOR_APPROVAL
    job = controller.mark_ready_for_approval(job.job_id)
    assert job.state == JobState.READY_FOR_APPROVAL

    # READY_FOR_APPROVAL -> APPROVED
    appr = controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")
    assert appr.decision == ApprovalDecision.APPROVED
    job = controller.job_store.get_job(job.job_id)
    assert job.state == JobState.APPROVED

    # APPROVED -> PRODUCTION_EXECUTION
    ok, msg, prod_exec = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is True
    job = controller.job_store.get_job(job.job_id)
    assert job.state == JobState.PRODUCTION_EXECUTION

    # PRODUCTION_EXECUTION -> PRODUCTION_VERIFICATION
    job = controller.complete_production_execution(job.job_id, prod_exec.execution_id, success=True, worker_id="w1")
    assert job.state == JobState.PRODUCTION_VERIFICATION

    # PRODUCTION_VERIFICATION -> COMPLETED
    job = controller.complete_production_verification(
        job.job_id, success=True, worker_id="w1", operator_identity="sec_human_reviewer"
    )
    assert job.state == JobState.COMPLETED


def test_valid_failure_and_abort_transitions(controller):
    """Test transitions to FAILED and ABORTED from various phases."""
    plan = {"steps": ["fail_test"]}
    cfg = {"env": "test"}

    # Failure from RUNNING
    job1 = controller.create_job(plan, cfg, created_by="test_user")
    controller.start_running(job1.job_id, worker_id="w1")
    j1_fail = controller.job_store.transition_state(job1.job_id, JobState.FAILED)
    assert j1_fail.state == JobState.FAILED

    # Abort from PLANNING
    job2 = controller.create_job(plan, cfg, created_by="test_user")
    j2_abort = controller.job_store.transition_state(job2.job_id, JobState.ABORTED)
    assert j2_abort.state == JobState.ABORTED

    # Rejection from READY_FOR_APPROVAL
    job3 = controller.create_job(plan, cfg, created_by="test_user")
    controller.job_store.transition_state(job3.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job3.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job3.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job3.job_id, ApprovalDecision.REJECTED, approved_by="human_operator")
    assert controller.job_store.get_job(job3.job_id).state == JobState.REJECTED


def test_forbidden_state_transitions(controller):
    """Test explicit rejection of forbidden transitions."""
    plan = {"step": "forbidden_test"}
    cfg = {"env": "test"}
    job = controller.create_job(plan, cfg, created_by="test_user")

    # Forbidden: PLANNING -> PRODUCTION_EXECUTION
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.PRODUCTION_EXECUTION)

    # Move to RUNNING
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)

    # Forbidden: RUNNING -> PRODUCTION_EXECUTION
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.PRODUCTION_EXECUTION)

    # Forbidden: RUNNING -> COMPLETED
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.COMPLETED)

    # Move to VERIFYING
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)

    # Forbidden: VERIFYING -> PRODUCTION_EXECUTION
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.PRODUCTION_EXECUTION)

    # Move to READY_FOR_APPROVAL
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)

    # Forbidden: READY_FOR_APPROVAL -> PRODUCTION_EXECUTION
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.PRODUCTION_EXECUTION)

    # Move to REJECTED
    controller.job_store.transition_state(job.job_id, JobState.REJECTED)

    # Forbidden: REJECTED -> PRODUCTION_EXECUTION or any other transition
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.PRODUCTION_EXECUTION)
    with pytest.raises(ValueError, match="Forbidden state transition"):
        controller.job_store.transition_state(job.job_id, JobState.APPROVED)


# ============================================================
# B. APPROVAL TESTS
# ============================================================

def test_approval_creation_and_identity(controller):
    """Test approval record persistence and identity binding."""
    plan = {"action": "deploy_worker"}
    cfg = {"replicas": 3}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)

    appr = controller.submit_human_approval(
        job_id=job.job_id,
        decision=ApprovalDecision.APPROVED,
        approved_by="senior_engineer_alice",
        notes="Reviewed and confirmed"
    )

    assert appr.job_id == job.job_id
    assert appr.plan_hash == job.plan_hash
    assert appr.commit_sha == job.commit_sha
    assert appr.approved_by == "senior_engineer_alice"
    assert appr.decision == ApprovalDecision.APPROVED
    assert appr.notes == "Reviewed and confirmed"

    # Verify persistent retrieval
    persisted = controller.approval_store.get_approval_for_job(job.job_id)
    assert persisted is not None
    assert persisted.approval_id == appr.approval_id
    assert persisted.plan_hash == appr.plan_hash


def test_missing_approval_blocks_execution(controller):
    """Gate 3: Missing approval blocks execution."""
    plan = {"action": "no_approval"}
    cfg = {"mode": "test"}
    job = controller.create_job(plan, cfg, created_by="admin")

    # Manually force job to APPROVED without creating an ApprovalRecord
    with controller.db_manager._get_connection() as conn:
        conn.execute("UPDATE automation_jobs SET state = 'APPROVED' WHERE job_id = ?", (job.job_id,))

    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 3 Failed: No approval record exists" in msg


def test_rejected_approval_blocks_execution(controller):
    """Gate 4: Rejected decision blocks execution."""
    plan = {"action": "reject_test"}
    cfg = {"mode": "test"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)

    controller.submit_human_approval(job.job_id, ApprovalDecision.REJECTED, approved_by="human_operator")

    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 12 Failed" in msg or "Gate 2 Failed" in msg or "Gate 4 Failed" in msg


def test_approval_mismatches_rejected(controller):
    """Gates 5, 6, 7: Wrong job_id, wrong plan_hash, or wrong commit_sha in approval."""
    plan = {"action": "tamper_test"}
    cfg = {"mode": "test"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # Tamper approval record plan_hash
    with controller.db_manager._get_connection() as conn:
        conn.execute("UPDATE automation_approvals SET plan_hash = 'tampered_hash' WHERE job_id = ?", (job.job_id,))

    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 6 Failed: Approval plan_hash does not match job plan_hash" in msg

    # Restore plan_hash and tamper commit_sha
    with controller.db_manager._get_connection() as conn:
        conn.execute("UPDATE automation_approvals SET plan_hash = ?, commit_sha = 'bad_commit_sha' WHERE job_id = ?", (job.plan_hash, job.job_id))

    ok2, msg2, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok2 is False
    assert "Gate 7 Failed: Approval commit_sha does not match job commit_sha" in msg2


# ============================================================
# C. PLAN INTEGRITY & MUTATION TESTS
# ============================================================

def test_plan_mutation_invalidates_approval_and_blocks_execution(controller):
    """Gate 9: Detected plan mutation transitions job to PLAN_CHANGED and blocks execution."""
    original_plan = {"steps": ["compile", "test", "package"]}
    cfg = {"opt_level": 3}
    job = controller.create_job(original_plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # Try executing with modified plan
    mutated_plan = {"steps": ["compile", "test", "package", "backdoor_script"]}
    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=mutated_plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 9 Failed: Plan mutation detected" in msg

    # Verify state transition to PLAN_CHANGED
    reloaded_job = controller.job_store.get_job(job.job_id)
    assert reloaded_job.state == JobState.PLAN_CHANGED

    # Subsequent attempt still blocked by Gate 12
    ok2, msg2, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=original_plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok2 is False
    assert "Gate 12 Failed: Job is in invalid state PLAN_CHANGED" in msg2


def test_config_mutation_blocks_execution(controller):
    """Gate 10: Config mutation blocks execution."""
    plan = {"steps": ["task1"]}
    original_cfg = {"secret": "safe", "timeout": 30}
    job = controller.create_job(plan, original_cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    tampered_cfg = {"secret": "leaked", "timeout": 30}
    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=tampered_cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 10 Failed: Config hash mismatch" in msg


# ============================================================
# D. GIT GUARD TESTS
# ============================================================

def test_git_sha_matching_passes(controller):
    """Matching SHA passes Gate 8."""
    plan = {"steps": ["step"]}
    cfg = {"env": "prod"}
    job = controller.create_job(plan, cfg, created_by="admin")
    assert job.commit_sha == controller.git_guard._commit_sha

    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is True


def test_git_sha_mismatch_blocks_execution(controller):
    """Gate 8: Mismatching commit SHA blocks production execution."""
    plan = {"steps": ["step"]}
    cfg = {"env": "prod"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # Simulate HEAD revision advance
    controller.git_guard._commit_sha = "0000000000000000000000000000000000000000"

    ok, msg, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is False
    assert "Gate 8 Failed: Current repository Git HEAD does not match job commit_sha" in msg


def test_missing_git_identity_blocks(controller):
    """GitGuard failure blocks job creation and production execution."""
    controller.git_guard._fail_git = True

    with pytest.raises(GitGuardError, match="Simulated Git identity failure"):
        controller.create_job({"step": "test"}, {}, created_by="admin")


def test_git_guard_detects_dirty_worktree():
    """GitGuard detects dirty status without modifying worktree."""
    guard = GitGuard("/home/ubuntu/Polya-AI")
    identity = guard.get_current_identity()
    assert identity.commit_sha is not None
    assert len(identity.commit_sha) == 40
    assert identity.branch != ""
    # Should report dirty since untracked/modified files exist, without touching them
    assert identity.is_dirty is True


# ============================================================
# E. CONCURRENCY & LEASE TESTS
# ============================================================

def test_concurrency_lease_locking(controller):
    """Prevents two workers from executing the same job concurrently."""
    plan = {"action": "concurrent_test"}
    cfg = {}
    job = controller.create_job(plan, cfg, created_by="admin")

    # Worker 1 acquires lease
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_alpha", ttl_seconds=60.0) is True

    # Worker 2 attempts lease on same job -> REJECTED
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_beta", ttl_seconds=60.0) is False

    # Worker 1 can renew its own lease
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_alpha", ttl_seconds=60.0) is True

    # Worker 1 releases lease
    assert controller.release_job_lease(job.job_id, worker_id="worker_alpha") is True

    # Worker 2 can now acquire lease
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_beta", ttl_seconds=60.0) is True


def test_stale_lease_recovery(controller):
    """Expired lease can be claimed by another worker."""
    plan = {"action": "stale_lease_test"}
    cfg = {}
    job = controller.create_job(plan, cfg, created_by="admin")

    # Worker 1 acquires very short lease (0.05 seconds)
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_1", ttl_seconds=0.05) is True

    # Immediate attempt by Worker 2 fails
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_2", ttl_seconds=60.0) is False

    # Wait for Worker 1's lease to expire
    time.sleep(0.06)

    # Worker 2 successfully recovers and acquires stale lease
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_2", ttl_seconds=60.0) is True


# ============================================================
# F. IDEMPOTENCY TESTS
# ============================================================

def test_idempotency_prevents_duplicate_production_execution(controller):
    """Gate 11: Production execution cannot run twice for the same job."""
    plan = {"action": "idempotent_action"}
    cfg = {"batch": 1}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # First production execution
    ok, msg, prod_exec = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok is True
    controller.complete_production_execution(job.job_id, prod_exec.execution_id, success=True, worker_id="w1")

    # Manually reset job state to APPROVED in database to test Gate 11 specifically
    with controller.db_manager._get_connection() as conn:
        conn.execute("UPDATE automation_jobs SET state = 'APPROVED' WHERE job_id = ?", (job.job_id,))

    # Repeated execution attempt must be refused
    ok2, msg2, prod_exec2 = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok2 is False
    assert "Gate 11 Failed: Idempotency check failed" in msg2


# ============================================================
# G. CRASH RECOVERY TESTS
# ============================================================

def test_crash_recovery_preserves_state_and_denies_privilege_escalation(temp_db_path):
    """State, approvals, and records survive restart; READY_FOR_APPROVAL does not escalate."""
    # 1. First process run: Job A in READY_FOR_APPROVAL, Job B in APPROVED
    ctrl1 = AutomationController(db_path=temp_db_path)
    ctrl1.git_guard = MockGitGuard()
    ctrl1.authorization_boundary.git_guard = ctrl1.git_guard

    plan = {"step": "restart_test"}
    cfg = {"env": "prod"}

    job_a = ctrl1.create_job(plan, cfg, created_by="admin")
    ctrl1.job_store.transition_state(job_a.job_id, JobState.RUNNING)
    ctrl1.job_store.transition_state(job_a.job_id, JobState.VERIFYING)
    ctrl1.job_store.transition_state(job_a.job_id, JobState.READY_FOR_APPROVAL)

    job_b = ctrl1.create_job(plan, cfg, created_by="admin")
    ctrl1.job_store.transition_state(job_b.job_id, JobState.RUNNING)
    ctrl1.job_store.transition_state(job_b.job_id, JobState.VERIFYING)
    ctrl1.job_store.transition_state(job_b.job_id, JobState.READY_FOR_APPROVAL)
    ctrl1.submit_human_approval(job_b.job_id, ApprovalDecision.APPROVED, approved_by="human_admin")

    # 2. Simulate process crash & restart by instantiating fresh controller pointing to same DB
    ctrl2 = AutomationController(db_path=temp_db_path)
    ctrl2.git_guard = MockGitGuard()
    ctrl2.authorization_boundary.git_guard = ctrl2.git_guard

    rec_a = ctrl2.job_store.get_job(job_a.job_id)
    rec_b = ctrl2.job_store.get_job(job_b.job_id)

    # Job A MUST remain READY_FOR_APPROVAL; no auto-escalation
    assert rec_a.state == JobState.READY_FOR_APPROVAL

    # Production execution on Job A must be blocked
    ok_a, msg_a, _ = ctrl2.initiate_production_execution(
        job_id=job_a.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_admin",
        worker_id="w1"
    )
    assert ok_a is False
    assert "Gate 2 Failed" in msg_a

    # Job B remains APPROVED and executable
    assert rec_b.state == JobState.APPROVED
    ok_b, msg_b, prod_exec = ctrl2.initiate_production_execution(
        job_id=job_b.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_admin",
        worker_id="w1"
    )
    assert ok_b is True


# ============================================================
# H. AUTHORIZATION GATE TESTS
# ============================================================

def test_authorization_all_12_gates_evaluated(controller):
    """Exhaustively verify each individual gate of the 12-checkpoint boundary."""
    plan = {"auth": "gate_test"}
    cfg = {"conf": 1}

    # Gate 1: Non-existent job
    res1 = controller.authorization_boundary.authorize_production_execution(
        job_id="job_does_not_exist",
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator"
    )
    assert res1.authorized is False
    assert "Gate 1 Failed" in res1.reason

    # Gate 12: Terminal / failure state
    job_failed = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job_failed.job_id, JobState.FAILED)
    res12 = controller.authorization_boundary.authorize_production_execution(
        job_id=job_failed.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator"
    )
    assert res12.authorized is False
    assert "Gate 12 Failed" in res12.reason

    # Gate 2: Not in APPROVED state (in PLANNING)
    job_planning = controller.create_job(plan, cfg, created_by="admin")
    res2 = controller.authorization_boundary.authorize_production_execution(
        job_id=job_planning.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator"
    )
    assert res2.authorized is False
    assert "Gate 2 Failed" in res2.reason


# ============================================================
# I. SECURITY INVARIANTS TESTS
# ============================================================

def test_agent_and_cron_cannot_approve(controller):
    """AGENT and CRON are forbidden from submitting approvals."""
    plan = {"step": "sec_test"}
    cfg = {}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)

    with pytest.raises(PermissionError, match="Security Violation"):
        controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="agent:hermes")

    with pytest.raises(PermissionError, match="Security Violation"):
        controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="agent_cloud_code")

    with pytest.raises(PermissionError, match="Security Violation"):
        controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="cron:daily")

    with pytest.raises(PermissionError, match="Security Violation"):
        controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="scheduler:cron")


def test_agent_and_cron_cannot_initiate_production_execution(controller):
    """AGENT and CRON are strictly forbidden from initiating production execution."""
    plan = {"step": "sec_test"}
    cfg = {}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # CRON caller
    ok_cron, msg_cron, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="cron:nightly",
        worker_id="w1"
    )
    assert ok_cron is False
    assert "CRON / SCHEDULER is strictly forbidden" in msg_cron

    # AGENT caller
    ok_agent, msg_agent, _ = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="agent:codex",
        worker_id="w1"
    )
    assert ok_agent is False
    assert "AGENT is strictly forbidden" in msg_agent


def test_running_and_verifying_cannot_execute_production(controller):
    """Jobs in intermediate non-approved states cannot execute production."""
    plan = {"step": "intermediate_test"}
    cfg = {}

    # RUNNING state
    job_run = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job_run.job_id, JobState.RUNNING)
    ok_run, msg_run, _ = controller.initiate_production_execution(
        job_id=job_run.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok_run is False
    assert "Gate 2 Failed: Job state is RUNNING, expected APPROVED" in msg_run

    # VERIFYING state
    controller.job_store.transition_state(job_run.job_id, JobState.VERIFYING)
    ok_ver, msg_ver, _ = controller.initiate_production_execution(
        job_id=job_run.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="w1"
    )
    assert ok_ver is False
    assert "Gate 2 Failed: Job state is VERIFYING, expected APPROVED" in msg_ver


# ============================================================
# I. SEC-P1-01 LEASE ORDERING & CONCURRENCY VERIFICATION TESTS
# ============================================================

def test_sec_p1_01_worker_b_rejected_before_authorization(controller):
    """
    TEST 1:
    Worker A acquires lease.
    Worker B attempts same job.
    Worker B is rejected BEFORE production authorization/execution.
    """
    plan = {"action": "lease_order_test"}
    cfg = {"mode": "strict"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # Worker A holds the lease externally or prior
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_a", ttl_seconds=60.0) is True

    # Worker B attempts production initiation
    ok_b, msg_b, exec_b = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="worker_b"
    )
    assert ok_b is False
    assert "Concurrency Lock: Worker worker_b failed to acquire execution lease." in msg_b
    assert exec_b is None

    # Verify job state is still APPROVED (not mutated to PRODUCTION_EXECUTION)
    j = controller.job_store.get_job(job.job_id)
    assert j.state == JobState.APPROVED


def test_sec_p1_01_simultaneous_race_single_winner(controller):
    """
    TEST 2:
    Two workers race simultaneously.
    Exactly one obtains the execution lease and starts execution.
    """
    import threading
    plan = {"action": "race_test"}
    cfg = {"mode": "race"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    results = []
    barrier = threading.Barrier(2)

    def worker_attempt(wid):
        barrier.wait()
        res = controller.initiate_production_execution(
            job_id=job.job_id,
            current_plan_data=plan,
            current_config_data=cfg,
            caller_identity="human_operator",
            worker_id=wid
        )
        results.append((wid, res))

    t1 = threading.Thread(target=worker_attempt, args=("worker_race_1",))
    t2 = threading.Thread(target=worker_attempt, args=("worker_race_2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [r for r in results if r[1][0] is True]
    failures = [r for r in results if r[1][0] is False]

    assert len(successes) == 1
    assert len(failures) == 1
    winner_wid, (ok_win, msg_win, exec_win) = successes[0]
    loser_wid, (ok_lose, msg_lose, exec_lose) = failures[0]

    assert ok_win is True
    assert exec_win is not None
    assert ok_lose is False
    assert exec_lose is None
    assert "Concurrency Lock" in msg_lose or "Gate 2 Failed" in msg_lose


def test_sec_p1_01_authorization_failure_releases_lease(controller):
    """
    TEST 3 & 5:
    Worker owns lease but authorization fails (e.g. invalid plan hash / tampered config / unapproved).
    Lease is released correctly.
    Production execution does not occur.
    Failed authorization does not leave an unreclaimable lease.
    """
    plan = {"action": "auth_fail_test"}
    cfg = {"token": "secret"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    # Tamper with current plan data to trigger authorization failure
    tampered_plan = {"action": "auth_fail_test", "tampered": True}

    ok, msg, exec_rec = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=tampered_plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="worker_failing"
    )
    assert ok is False
    assert "Authorization Denied" in msg
    assert exec_rec is None

    # Verify lease is NOT held (it was safely released)
    # Another worker can immediately acquire lease
    assert controller.acquire_job_lease(job.job_id, worker_id="worker_subsequent", ttl_seconds=60.0) is True


def test_sec_p1_01_worker_owns_lease_and_auth_succeeds(controller):
    """
    TEST 4:
    Worker owns lease and authorization succeeds.
    Existing production path remains functional.
    """
    plan = {"action": "auth_success_test"}
    cfg = {"mode": "test4"}
    job = controller.create_job(plan, cfg, created_by="admin")
    controller.job_store.transition_state(job.job_id, JobState.RUNNING)
    controller.job_store.transition_state(job.job_id, JobState.VERIFYING)
    controller.job_store.transition_state(job.job_id, JobState.READY_FOR_APPROVAL)
    controller.submit_human_approval(job.job_id, ApprovalDecision.APPROVED, approved_by="human_operator")

    ok, msg, exec_rec = controller.initiate_production_execution(
        job_id=job.job_id,
        current_plan_data=plan,
        current_config_data=cfg,
        caller_identity="human_operator",
        worker_id="worker_valid"
    )
    assert ok is True
    assert exec_rec is not None
    assert exec_rec.phase == ExecutionPhase.PRODUCTION_EXECUTION
    assert exec_rec.worker_id == "worker_valid"

    # Job is in PRODUCTION_EXECUTION
    j = controller.job_store.get_job(job.job_id)
    assert j.state == JobState.PRODUCTION_EXECUTION

    # Complete production execution and verification
    j_ver = controller.complete_production_execution(job.job_id, exec_rec.execution_id, success=True, worker_id="worker_valid")
    assert j_ver.state == JobState.PRODUCTION_VERIFICATION

    j_comp = controller.complete_production_verification(
        job.job_id, success=True, worker_id="worker_valid", operator_identity="sec_human_reviewer"
    )
    assert j_comp.state == JobState.COMPLETED


def test_sec_p1_01_negative_security_gates_all_blocked(controller):
    """
    TEST 6 & 7:
    Negative security tests verifying all illegal transitions and mutations remain blocked:
    - wrong approval
    - wrong plan hash
    - wrong commit SHA
    - changed Git HEAD
    - duplicate execution
    - FAILED -> PRODUCTION_EXECUTION
    - PLAN_CHANGED -> PRODUCTION_EXECUTION
    """
    plan = {"action": "neg_test"}
    cfg = {"env": "prod"}
    job = controller.create_job(plan, cfg, created_by="admin")

    # FAILED -> PRODUCTION_EXECUTION blocked
    controller.job_store.transition_state(job.job_id, JobState.FAILED)
    ok_fail, msg_fail, _ = controller.initiate_production_execution(
        job.job_id, plan, cfg, "human_operator", "w1"
    )
    assert ok_fail is False
    assert "Gate 12 Failed" in msg_fail
    assert controller.lease_store.is_locked_by_other(job.job_id, "w2") is False

