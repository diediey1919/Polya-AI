import base64
import json
import secrets
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from orchestrator.automation.job_store import DatabaseManager, JobStore
from orchestrator.automation.models import AutomationJob
from orchestrator.automation.states import JobState


class ReleaseSecurityError(Exception):
    """Base exception for release gate violations."""


class ChallengeExpiredError(ReleaseSecurityError):
    """Raised when release challenge timestamp exceeds validity window."""


class NonceReplayError(ReleaseSecurityError):
    """Raised when a challenge nonce was already consumed."""


class InvalidSignatureError(ReleaseSecurityError):
    """Raised when Ed25519 cryptographic signature fails verification."""


class StateNotEligibleError(ReleaseSecurityError):
    """Raised when job is not in STAGED state."""


class PayloadIntegrityError(ReleaseSecurityError):
    """Raised when challenge fields do not match stored job state."""


@dataclass(frozen=True)
class ReleaseChallenge:
    challenge_version: str
    job_id: str
    plan_hash: str
    commit_sha: str
    nonce: str
    issued_at: float
    expires_at: float
    operator_key_id: str

    def to_canonical_dict(self) -> Dict[str, Any]:
        return {
            "challenge_version": self.challenge_version,
            "commit_sha": self.commit_sha,
            "expires_at": round(self.expires_at, 3),
            "issued_at": round(self.issued_at, 3),
            "job_id": self.job_id,
            "nonce": self.nonce,
            "operator_key_id": self.operator_key_id,
            "plan_hash": self.plan_hash,
        }

    def canonical_bytes(self) -> bytes:
        canonical_str = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return canonical_str.encode("utf-8")


class NonceStore:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def is_nonce_used(self, nonce: str) -> bool:
        with self.db._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM automation_release_nonces WHERE nonce = ?", (nonce,))
            return cur.fetchone() is not None

    def record_nonce_consumption(
        self,
        conn,
        nonce: str,
        job_id: str,
        operator_key_id: str,
        expires_at: float,
    ) -> None:
        """Atomic nonce consumption within caller transaction."""
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        conn.execute(
            """
            INSERT INTO automation_release_nonces (
                nonce, job_id, operator_key_id, used_at, expires_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (nonce, job_id, operator_key_id, now_iso, expires_at),
        )


class OperatorReleaseGate:
    """Off-host Ed25519 verification gate.
    
    The server NEVER holds or creates operator private keys.
    Public keys are loaded at instantiation and cannot be mutated by agent runtime.
    """

    def __init__(
        self,
        job_store: JobStore,
        trusted_public_keys: Dict[str, str],  # operator_key_id -> base64_public_key
        challenge_ttl_seconds: float = 300.0,
    ):
        self.job_store = job_store
        self.nonce_store = NonceStore(job_store.db)
        self.challenge_ttl_seconds = challenge_ttl_seconds
        self._trusted_public_keys: Dict[str, ed25519.Ed25519PublicKey] = {}
        for key_id, b64_pub in trusted_public_keys.items():
            raw_pub = base64.b64decode(b64_pub)
            self._trusted_public_keys[key_id] = ed25519.Ed25519PublicKey.from_public_bytes(raw_pub)

    def generate_challenge(self, job_id: str, operator_key_id: str) -> ReleaseChallenge:
        if operator_key_id not in self._trusted_public_keys:
            raise ReleaseSecurityError(f"Untrusted or unregistered operator_key_id: {operator_key_id}")

        job = self.job_store.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found.")

        if job.state != JobState.STAGED:
            raise StateNotEligibleError(
                f"Cannot generate release challenge for job in state {job.state.value}; must be STAGED."
            )

        now = time.time()
        nonce = secrets.token_hex(24)  # 192-bit CSPRNG nonce
        return ReleaseChallenge(
            challenge_version="1.0",
            job_id=job.job_id,
            plan_hash=job.plan_hash,
            commit_sha=job.commit_sha,
            nonce=nonce,
            issued_at=now,
            expires_at=now + self.challenge_ttl_seconds,
            operator_key_id=operator_key_id,
        )

    def verify_and_release(
        self,
        challenge: ReleaseChallenge,
        signature_base64: str,
        current_commit_sha: Optional[str] = None,
    ) -> AutomationJob:
        """Atomically verifies Ed25519 signature, consumes nonce, and releases job to PLANNING."""
        now = time.time()
        if now > challenge.expires_at:
            raise ChallengeExpiredError(
                f"Release challenge expired at {challenge.expires_at} (current: {now})."
            )

        public_key = self._trusted_public_keys.get(challenge.operator_key_id)
        if not public_key:
            raise ReleaseSecurityError(f"Unknown operator_key_id: {challenge.operator_key_id}")

        # Decode signature
        try:
            signature_bytes = base64.b64decode(signature_base64)
        except Exception as e:
            raise InvalidSignatureError(f"Malformed base64 signature: {e}")

        # Verify cryptographic signature against canonical bytes
        canonical_bytes = challenge.canonical_bytes()
        try:
            public_key.verify(signature_bytes, canonical_bytes)
        except InvalidSignature:
            raise InvalidSignatureError("Ed25519 signature verification failed.")

        # Single exclusive transaction: re-check DB state, nonce replay, and update
        with self.job_store.db._get_connection() as conn:
            conn.execute("BEGIN EXCLUSIVE")
            cur = conn.cursor()

            # Check nonce replay
            cur.execute(
                "SELECT 1 FROM automation_release_nonces WHERE nonce = ?",
                (challenge.nonce,),
            )
            if cur.fetchone() is not None:
                raise NonceReplayError(f"Challenge nonce {challenge.nonce} has already been consumed.")

            # Check job integrity in DB
            cur.execute("SELECT * FROM automation_jobs WHERE job_id = ?", (challenge.job_id,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Job {challenge.job_id} not found in database.")

            if row["state"] != JobState.STAGED.value:
                raise StateNotEligibleError(
                    f"Job {challenge.job_id} is in state {row['state']}; cannot release to PLANNING."
                )

            if row["plan_hash"] != challenge.plan_hash:
                raise PayloadIntegrityError(
                    f"Plan hash mismatch: DB has {row['plan_hash']}, challenge has {challenge.plan_hash}"
                )

            if row["commit_sha"] != challenge.commit_sha:
                raise PayloadIntegrityError(
                    f"Commit SHA mismatch: DB has {row['commit_sha']}, challenge has {challenge.commit_sha}"
                )

            if current_commit_sha and current_commit_sha != challenge.commit_sha:
                raise PayloadIntegrityError(
                    f"Git repository drift: HEAD is {current_commit_sha}, challenge expects {challenge.commit_sha}"
                )

            # 1. Consume nonce
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            cur.execute(
                """
                INSERT INTO automation_release_nonces (
                    nonce, job_id, operator_key_id, used_at, expires_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    challenge.nonce,
                    challenge.job_id,
                    challenge.operator_key_id,
                    now_iso,
                    challenge.expires_at,
                ),
            )

            # 2. Transition state STAGED -> PLANNING
            cur.execute(
                """
                UPDATE automation_jobs
                SET state = ?, updated_at = ?
                WHERE job_id = ? AND state = ?
                """,
                (JobState.PLANNING.value, now_iso, challenge.job_id, JobState.STAGED.value),
            )

            if cur.rowcount != 1:
                raise ReleaseSecurityError("Atomic state transition failed; race condition detected.")

            conn.commit()

        return self.job_store.get_job(challenge.job_id)
