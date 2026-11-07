import base64
import os
import secrets
import tempfile
import time
import pytest
cryptography = pytest.importorskip("cryptography")
from cryptography.hazmat.primitives.asymmetric import ed25519

from orchestrator.automation.controller import AutomationController
from orchestrator.automation.git_guard import GitIdentity
from orchestrator.automation.job_store import DatabaseManager, JobStore
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.operator_gate import (
    ChallengeExpiredError,
    InvalidSignatureError,
    NonceReplayError,
    OperatorReleaseGate,
    PayloadIntegrityError,
    ReleaseChallenge,
    ReleaseSecurityError,
    StateNotEligibleError,
)
from orchestrator.automation.states import JobState
from orchestrator.automation.supervisor import Supervisor, SupervisorConfig
from tests.test_automation_controller import MockGitGuard


@pytest.fixture
def test_keypair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes_raw()
    b64_pub = base64.b64encode(pub_bytes).decode("utf-8")
    return private_key, public_key, b64_pub


@pytest.fixture
def isolated_env(test_keypair):
    priv, pub, b64_pub = test_keypair
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test_automation.db")

    controller = AutomationController(db_path=db_path)
    controller.git_guard = MockGitGuard(
        commit_sha="d3646005bf56bda2d89e7f16cbd9abf4f1fcbc18",
        is_dirty=False,
        fail_git=False,
    )
    gate = OperatorReleaseGate(
        job_store=controller.job_store,
        trusted_public_keys={"op_key_1": b64_pub},
        challenge_ttl_seconds=10.0,
    )
    yield controller, gate, priv, db_path
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_01_valid_signature_releases_job_to_planning(isolated_env):
    controller, gate, priv, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_001",
        initial_state=JobState.STAGED,
    )
    assert job.state == JobState.STAGED

    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")
    sig_bytes = priv.sign(challenge.canonical_bytes())
    sig_b64 = base64.b64encode(sig_bytes).decode("utf-8")

    released_job = gate.verify_and_release(
        challenge=challenge,
        signature_base64=sig_b64,
        current_commit_sha="d3646005bf56bda2d89e7f16cbd9abf4f1fcbc18",
    )
    assert released_job.state == JobState.PLANNING
    assert controller.job_store.get_job(job.job_id).state == JobState.PLANNING


def test_02_forged_signature_rejected(isolated_env):
    controller, gate, _, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_002",
        initial_state=JobState.STAGED,
    )
    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")

    # Attacker signs with different key
    attacker_priv = ed25519.Ed25519PrivateKey.generate()
    forged_sig = base64.b64encode(attacker_priv.sign(challenge.canonical_bytes())).decode("utf-8")

    with pytest.raises(InvalidSignatureError, match="Ed25519 signature verification failed"):
        gate.verify_and_release(challenge, forged_sig)
    assert controller.job_store.get_job(job.job_id).state == JobState.STAGED


def test_03_nonce_replay_rejected(isolated_env):
    controller, gate, priv, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_003",
        initial_state=JobState.STAGED,
    )
    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")
    sig_b64 = base64.b64encode(priv.sign(challenge.canonical_bytes())).decode("utf-8")

    # First release succeeds
    gate.verify_and_release(challenge, sig_b64)

    # Replay of the same challenge/nonce must be rejected
    with pytest.raises(NonceReplayError, match="Challenge nonce .* has already been consumed"):
        gate.verify_and_release(challenge, sig_b64)


def test_04_expired_challenge_rejected(isolated_env):
    controller, gate, priv, _ = isolated_env
    gate.challenge_ttl_seconds = 0.05
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_004",
        initial_state=JobState.STAGED,
    )
    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")
    sig_b64 = base64.b64encode(priv.sign(challenge.canonical_bytes())).decode("utf-8")

    time.sleep(0.06)
    with pytest.raises(ChallengeExpiredError, match="Release challenge expired"):
        gate.verify_and_release(challenge, sig_b64)


def test_05_tampered_payload_rejected(isolated_env):
    controller, gate, priv, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_005",
        initial_state=JobState.STAGED,
    )
    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")
    
    # Tamper with challenge plan_hash
    tampered_challenge = ReleaseChallenge(
        challenge_version=challenge.challenge_version,
        job_id=challenge.job_id,
        plan_hash="tampered_hash_1234567890abcdef",
        commit_sha=challenge.commit_sha,
        nonce=challenge.nonce,
        issued_at=challenge.issued_at,
        expires_at=challenge.expires_at,
        operator_key_id=challenge.operator_key_id,
    )
    sig_b64 = base64.b64encode(priv.sign(tampered_challenge.canonical_bytes())).decode("utf-8")

    with pytest.raises(PayloadIntegrityError, match="Plan hash mismatch"):
        gate.verify_and_release(tampered_challenge, sig_b64)


def test_06_non_staged_state_rejected(isolated_env):
    controller, gate, priv, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_006",
        initial_state=JobState.PLANNING,
    )
    with pytest.raises(StateNotEligibleError, match="must be STAGED"):
        gate.generate_challenge(job.job_id, operator_key_id="op_key_1")


def test_07_git_drift_rejected(isolated_env):
    controller, gate, priv, _ = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_007",
        initial_state=JobState.STAGED,
    )
    challenge = gate.generate_challenge(job.job_id, operator_key_id="op_key_1")
    sig_b64 = base64.b64encode(priv.sign(challenge.canonical_bytes())).decode("utf-8")

    with pytest.raises(PayloadIntegrityError, match="Git repository drift"):
        gate.verify_and_release(
            challenge, sig_b64, current_commit_sha="new_drifted_commit_sha_123"
        )


def test_08_supervisor_ignores_staged_jobs(isolated_env):
    controller, _, _, db_path = isolated_env
    job = controller.create_job(
        plan_data={"steps": ["task1"]},
        config_data={"cfg": "test"},
        created_by="operator",
        job_id="job_staged_008",
        initial_state=JobState.STAGED,
    )
    cfg = SupervisorConfig(db_path=db_path)
    supervisor = Supervisor(config=cfg)
    runnable, blocked = supervisor.filter_runnable_jobs()

    assert not any(j.job_id == job.job_id for j in runnable)
    assert any(j.job_id == job.job_id and "STAGED" in reason for j, reason in blocked)


def test_09_backward_compatibility_default_planning(isolated_env):
    controller, _, _, _ = isolated_env
    legacy_job = controller.create_job(
        plan_data={"steps": ["legacy"]},
        config_data={"cfg": "legacy"},
        created_by="legacy_caller",
        job_id="job_legacy_001",
    )
    assert legacy_job.state == JobState.PLANNING


def test_10_migration_v3_rehearsal(tmp_path):
    from orchestrator.automation.migrations import migrate, current_version, SCHEMA_VERSION
    test_db = str(tmp_path / "migration_v3.db")
    res = migrate(test_db)
    assert current_version(sqlite3_conn := __import__("sqlite3").connect(test_db)) == SCHEMA_VERSION
    assert SCHEMA_VERSION == 3
    # Check automation_release_nonces table exists
    cur = sqlite3_conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='automation_release_nonces'")
    assert cur.fetchone() is not None
