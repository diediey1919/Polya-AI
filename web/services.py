"""
Polya Apologetika — Services Architecture
Phase-1 Web Foundation
Contains:
- UsageEntitlementService (Server-side 5 free analyses quota)
- EntitlementService & FeatureRegistry
- PaymentService (Midtrans integration + SHA-512 webhook validation)
- CaseFileGenerator (Source-first mock/fixture case files)
"""
import hashlib
import hmac
import base64
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from web.models import (
        CANONICAL_DEMO_CLAIMS,
        CaseFile,
        EntitlementState,
        PaymentTransaction,
        UserApologeticsContext,
        UserPerspective,
        InterlinearWordToken,
        ExegeticalContext,
        LinguisticExegesisPackage
    )
except ImportError:
    from models import (
        CANONICAL_DEMO_CLAIMS,
        CaseFile,
        EntitlementState,
        PaymentTransaction,
        UserApologeticsContext,
        UserPerspective,
        InterlinearWordToken,
        ExegeticalContext,
        LinguisticExegesisPackage
    )

from contextlib import contextmanager
import time
import requests
import sys
from pathlib import Path

# Ensure orchestrator/ submodules (sqlite_checkpointer, etc.) are importable
# when working dir is web/. research_graph.py uses bare imports without package prefix.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ORCHESTRATOR_DIR = str(_REPO_ROOT / "orchestrator")
if _ORCHESTRATOR_DIR not in sys.path:
    sys.path.insert(0, _ORCHESTRATOR_DIR)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

logger = logging.getLogger("polya.services")

# Auto-load .env from directory
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path) as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception as _e:
        logger.warning(f"Failed to load .env: {_e}")

DB_PATH = os.environ.get("POLYA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "polya_arena.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
SQLITE_TIMEOUT = float(os.environ.get("POLYA_SQLITE_TIMEOUT", "30.0"))


def get_db(target_db_path: Optional[str] = None):
    target = target_db_path or DB_PATH
    conn = sqlite3.connect(target, timeout=SQLITE_TIMEOUT, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(f"PRAGMA busy_timeout = {int(SQLITE_TIMEOUT * 1000)};")
    except Exception:
        pass
    return conn


@contextmanager
def db_transaction(target_db_path: Optional[str] = None, exclusive: bool = False):
    """Safe database context manager ensuring commit/rollback and connection close."""
    target = target_db_path or DB_PATH
    conn = get_db(target)
    try:
        if exclusive:
            conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def execute_with_retry(fn, max_retries: int = 3, retry_delay: float = 0.05):
    """Executes a database operation callback with limited retries for transient locks."""
    attempts = 0
    while True:
        attempts += 1
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempts <= max_retries:
                time.sleep(retry_delay * attempts)
                continue
            raise


def init_foundation_db(target_db_path: Optional[str] = None):
    """Initializes tables required by the Web Foundation and Arena Auth."""
    target = target_db_path or DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
    conn = get_db(target)
    cursor = conn.cursor()

    # 0. Arena Users (required by auth session & arena foundation)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS arena_users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        name TEXT,
        avatar_url TEXT,
        bio TEXT,
        role TEXT DEFAULT 'visitor',
        dana TEXT DEFAULT '',
        gopay TEXT DEFAULT '',
        shopeepay TEXT DEFAULT '',
        ovo TEXT DEFAULT '',
        qris_url TEXT DEFAULT '',
        total_donations_received INTEGER DEFAULT 0,
        created_at TEXT
    )
    """)

    # 1. User Entitlements
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_entitlements (
        user_id TEXT PRIMARY KEY,
        state TEXT DEFAULT 'FREE',
        plan TEXT DEFAULT 'free',
        activated_at TEXT,
        expires_at TEXT,
        updated_at TEXT
    )
    """)

    # 2. Usage Entitlement Records (Server-side 5-quota enforcement with idempotency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage_entitlement_records (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        request_id TEXT NOT NULL UNIQUE,
        feature TEXT NOT NULL,
        consumed_at TEXT NOT NULL
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user ON usage_entitlement_records(user_id)")

    # 3. Payment Transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payment_transactions (
        transaction_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        order_id TEXT NOT NULL UNIQUE,
        amount INTEGER NOT NULL,
        currency TEXT DEFAULT 'IDR',
        provider TEXT DEFAULT 'midtrans',
        provider_status TEXT,
        internal_status TEXT,
        idempotency_key TEXT,
        metadata_json TEXT,
        created_at TEXT,
        updated_at TEXT,
        verified_at TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_payment_order ON payment_transactions(order_id)")

    # 4. User Apologetics Context
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_apologetics_context (
        user_id TEXT PRIMARY KEY,
        ui_locale TEXT DEFAULT 'id',
        user_perspective TEXT DEFAULT 'christian_protestant',
        opponent_perspective TEXT DEFAULT 'islam',
        debate_locale TEXT DEFAULT 'id',
        source_locale TEXT DEFAULT 'el',
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def verify_foundation_schema(target_db_path: Optional[str] = None) -> bool:
    """Verifies that all required foundation tables exist in the target database."""
    target = target_db_path or DB_PATH
    if not os.path.exists(target) or os.path.getsize(target) == 0:
        return False
    try:
        conn = get_db(target)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        required = {"user_entitlements", "usage_entitlement_records", "payment_transactions", "user_apologetics_context", "arena_users"}
        return required.issubset(tables)
    except Exception as e:
        logger.error(f"Error checking foundation schema: {e}")
        return False


init_foundation_db()


class ContextService:
    """Manages User Apologetics Context with 5-perspective support and default opposition matrix."""

    DEFAULT_OPPOSITION_MATRIX = {
        "christian_protestant": "islam",
        "christian_catholic": "christian_protestant",
        "islam": "christian_protestant",
        "judaism": "christian_protestant",
        "atheist_secular": "christian_protestant",
        "christian": "islam",
    }

    DEFAULT_SOURCE_LOCALE_MATRIX = {
        "christian_protestant": "el",
        "christian_catholic": "la",
        "islam": "ar",
        "judaism": "he",
        "atheist_secular": "en",
        "christian": "el",
    }

    @classmethod
    def normalize_perspective(cls, persp: Optional[str]) -> str:
        if not persp:
            return "christian_protestant"
        p_lower = str(persp).strip().lower()
        if p_lower in ("christian", "protestant", "christian_protestant"):
            return "christian_protestant"
        if p_lower in ("catholic", "katolik", "christian_catholic"):
            return "christian_catholic"
        if p_lower in ("islam", "muslim"):
            return "islam"
        if p_lower in ("judaism", "jewish", "yahudi"):
            return "judaism"
        if p_lower in ("atheist", "secular", "atheist_secular", "ateis"):
            return "atheist_secular"
        return p_lower

    @classmethod
    def get_default_opponent(cls, user_perspective: str) -> str:
        norm = cls.normalize_perspective(user_perspective)
        return cls.DEFAULT_OPPOSITION_MATRIX.get(norm, "christian_protestant" if norm != "christian_protestant" else "islam")

    @classmethod
    def get_default_source_locale(cls, user_perspective: str) -> str:
        norm = cls.normalize_perspective(user_perspective)
        return cls.DEFAULT_SOURCE_LOCALE_MATRIX.get(norm, "el")

    @classmethod
    def get_user_context(cls, user_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale FROM user_apologetics_context WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            default_ctx = UserApologeticsContext()
            return default_ctx.model_dump()

        raw_user_persp = row["user_perspective"]
        user_persp = cls.normalize_perspective(raw_user_persp)
        opp_persp = row["opponent_perspective"]
        if not opp_persp or opp_persp == "christian":
            opp_persp = cls.get_default_opponent(user_persp)
        else:
            opp_persp = cls.normalize_perspective(opp_persp)

        src_locale = row["source_locale"] or cls.get_default_source_locale(user_persp)

        return {
            "ui_locale": row["ui_locale"] or "id",
            "user_perspective": user_persp,
            "opponent_perspective": opp_persp,
            "debate_locale": row["debate_locale"] or "id",
            "source_locale": src_locale
        }

    @classmethod
    def save_user_context(cls, user_id: str, ctx: UserApologeticsContext, db_path: Optional[str] = None) -> Dict[str, Any]:
        persp_val = cls.normalize_perspective(
            ctx.user_perspective.value if hasattr(ctx.user_perspective, "value") else str(ctx.user_perspective)
        )
        opp_persp = ctx.opponent_perspective
        if not opp_persp or opp_persp == "christian":
            opp_persp = cls.get_default_opponent(persp_val)
        else:
            opp_persp = cls.normalize_perspective(opp_persp)

        src_locale = ctx.source_locale or cls.get_default_source_locale(persp_val)

        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO user_apologetics_context (user_id, ui_locale, user_perspective, opponent_perspective, debate_locale, source_locale, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            ui_locale = excluded.ui_locale,
            user_perspective = excluded.user_perspective,
            opponent_perspective = excluded.opponent_perspective,
            debate_locale = excluded.debate_locale,
            source_locale = excluded.source_locale,
            updated_at = excluded.updated_at
        """, (user_id, ctx.ui_locale, persp_val, opp_persp, ctx.debate_locale, src_locale))
        conn.commit()
        conn.close()

        return {
            "ui_locale": ctx.ui_locale,
            "user_perspective": persp_val,
            "opponent_perspective": opp_persp,
            "debate_locale": ctx.debate_locale,
            "source_locale": src_locale
        }



class FeatureRegistry:
    """Central registry of platform capabilities and required entitlements."""
    FEATURES = {
        "calculator.claim_analysis": {"min_state": EntitlementState.FREE, "quota_applies": True},
        "themes.browse": {"min_state": EntitlementState.FREE, "quota_applies": False},
        "knowledge.read_basic": {"min_state": EntitlementState.FREE, "quota_applies": False},
        "knowledge.deep_apparatus": {"min_state": EntitlementState.PREMIUM_ACTIVE, "quota_applies": False},
        "debate.teleprompter": {"min_state": EntitlementState.PREMIUM_ACTIVE, "quota_applies": False},
        "export.citation_bibtex": {"min_state": EntitlementState.PREMIUM_ACTIVE, "quota_applies": False},
    }

    @classmethod
    def requires_premium(cls, feature_name: str) -> bool:
        feature = cls.FEATURES.get(feature_name, {})
        return feature.get("min_state") == EntitlementState.PREMIUM_ACTIVE


class GoogleAuthVerifier:
    """Verifies Google ID tokens or mock credentials under strict environment gates."""
    ALLOWED_MOCK_ENVIRONMENTS = {"test", "development", "local"}
    VALID_GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
    JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    _jwks_client = None

    @classmethod
    def is_mock_allowed(cls) -> bool:
        env = os.environ.get("POLYA_ENV", "").strip().lower()
        return env in cls.ALLOWED_MOCK_ENVIRONMENTS

    @classmethod
    def get_jwks_client(cls):
        if cls._jwks_client is None:
            import jwt
            cls._jwks_client = jwt.PyJWKClient(cls.JWKS_URL, cache_keys=True, lifespan=3600)
        return cls._jwks_client

    @classmethod
    def verify_credential(cls, credential: str) -> Optional[Dict[str, Any]]:
        """Verifies Google OAuth ID Token.

        Performs primary cryptographic RS256 signature verification via Google Public JWKS,
        with tokeninfo evaluation fallback.
        Strictly validates issuer, audience, subject, expiration, and email_verified.
        Returns payload dict: {'sub': google_sub_id, 'email': verified_email, 'name': verified_name, 'avatar_url': ...}
        """
        if not credential or not credential.strip():
            return None

        # Check for test/mock credential format: mock-google-token:<email>:<sub_id>:<name>
        if credential.startswith("mock-google-token:"):
            # Enforce strict positive allowlist gate (disallowed on staging/production)
            if not cls.is_mock_allowed():
                logger.warning("Rejected mock-google-token: environment not in positive allowlist")
                return None
            parts = credential.split(":")
            if len(parts) >= 4:
                return {
                    "email": parts[1].strip().lower(),
                    "sub": parts[2].strip(),
                    "name": parts[3].strip(),
                    "avatar_url": parts[4].strip() if len(parts) > 4 else f"https://api.dicebear.com/7.x/avataaars/svg?seed={parts[3].strip()}"
                }
            return None

        allowed_auds = cls.get_allowed_client_ids()
        if not allowed_auds:
            logger.error("GOOGLE_CLIENT_ID is not configured or empty; refusing authentication fail-closed")
            return None

        # 1. Primary: Cryptographic RS256 JWKS verification using Google public certificates
        try:
            import jwt
            jwk_client = cls.get_jwks_client()
            signing_key = jwk_client.get_signing_key_from_jwt(credential)
            payload = jwt.decode(
                credential,
                signing_key.key,
                algorithms=["RS256"],
                audience=allowed_auds if allowed_auds else None,
                issuer=list(cls.VALID_GOOGLE_ISSUERS),
                options={"verify_exp": True}
            )

            # Validate mandatory claims
            sub = payload.get("sub")
            email = payload.get("email")
            if not sub or not email:
                logger.warning("Google ID token missing sub or email claim in verified payload")
                return None

            email_verified = payload.get("email_verified")
            if email_verified not in (True, "true", "True", 1):
                logger.warning("Google ID token rejected: email is not verified by Google")
                return None

            return {
                "sub": str(sub),
                "email": str(email).strip().lower(),
                "name": payload.get("name", "Google User"),
                "avatar_url": payload.get("picture", "")
            }
        except Exception as jwks_err:
            logger.info("JWKS verification note: %s. Evaluating tokeninfo endpoint...", jwks_err)

        # 2. Secondary fallback: Tokeninfo endpoint with strict claim validation
        try:
            import requests
            resp = requests.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}",
                timeout=5.0
            )
            if resp.status_code != 200:
                logger.warning("Google tokeninfo verification failed with status %d", resp.status_code)
                return None
            info = resp.json()

            # Issuer verification
            iss = info.get("iss", "")
            if iss not in cls.VALID_GOOGLE_ISSUERS:
                logger.warning("Google ID token issuer invalid: %s", iss)
                return None

            # Audience verification
            aud = info.get("aud")
            if not allowed_auds or aud not in allowed_auds:
                logger.warning("Google ID token audience verification failed: %s not in allowed client IDs", aud)
                return None

            # Subject and email mandatory check
            sub = info.get("sub")
            email = info.get("email")
            if not sub or not email:
                logger.warning("Google ID token missing sub or email claim")
                return None

            # Email verification check
            email_verified = info.get("email_verified")
            if email_verified not in (True, "true", "True", 1):
                logger.warning("Google ID token email is not verified by Google")
                return None

            # Expiration check
            exp_val = info.get("exp")
            if exp_val is not None:
                try:
                    if int(exp_val) <= int(datetime.now(timezone.utc).timestamp()):
                        logger.warning("Google ID token is expired")
                        return None
                except Exception:
                    return None

            return {
                "sub": sub,
                "email": email.strip().lower(),
                "name": info.get("name", "Google User"),
                "avatar_url": info.get("picture", "")
            }
        except Exception as e:
            logger.warning(f"Error during Google ID token verification: {e}")
            return None

    @classmethod
    def get_expected_client_id(cls) -> str:
        return os.environ.get("GOOGLE_CLIENT_ID", "").strip()

    @classmethod
    def get_allowed_client_ids(cls) -> List[str]:
        configured = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
        if configured:
            return [configured]
        return []


class SessionService:
    """Manages cryptographically signed and verifiable session tokens with TTL."""
    TOKEN_TTL_SECONDS = 86400 * 7  # 7 days
    GUEST_TOKEN_TTL_SECONDS = 86400 * 30  # 30 days

    @classmethod
    def get_secret(cls) -> str:
        secret = os.environ.get("POLYA_AUTH_SECRET", "").strip()
        if not secret:
            raise RuntimeError("POLYA_AUTH_SECRET is not configured or empty; refusing fail-open execution")
        return secret

    @classmethod
    def create_token(cls, user_id: str, role: str = "visitor", ttl: Optional[int] = None) -> str:
        secret = cls.get_secret()
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        token_ttl = ttl if ttl is not None else cls.TOKEN_TTL_SECONDS
        exp = int(datetime.now(timezone.utc).timestamp()) + token_ttl
        payload_data = {
            "sub": user_id,
            "role": role,
            "exp": exp,
            "iat": int(datetime.now(timezone.utc).timestamp())
        }
        payload = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
        unsigned = f"{header}.{payload}"
        sig = hmac.new(secret.encode("utf-8"), unsigned.encode("utf-8"), hashlib.sha256).digest()
        signature = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        return f"{unsigned}.{signature}"

    @classmethod
    def create_guest_token(cls, guest_id: Optional[str] = None) -> Tuple[str, str]:
        if not guest_id or not guest_id.startswith("guest_"):
            guest_id = f"guest_{uuid.uuid4().hex[:16]}"
        token = cls.create_token(user_id=guest_id, role="guest", ttl=cls.GUEST_TOKEN_TTL_SECONDS)
        return token, guest_id

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        try:
            secret = cls.get_secret()
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts
            unsigned = f"{header_b64}.{payload_b64}"
            expected_sig = hmac.new(secret.encode("utf-8"), unsigned.encode("utf-8"), hashlib.sha256).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")
            if not hmac.compare_digest(signature_b64, expected_sig_b64):
                return None

            # Pad payload if needed
            pad_len = 4 - (len(payload_b64) % 4)
            if pad_len != 4:
                payload_b64 += "=" * pad_len
            payload_data = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())

            # Check expiration
            if payload_data.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
                return None
            return payload_data
        except Exception:
            return None


class EntitlementService:
    """Manages subscription tier states and premium authorizations."""

    @staticmethod
    def get_entitlement(user_id: str) -> Dict[str, Any]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT state, plan, activated_at, expires_at FROM user_entitlements WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return {
                "user_id": user_id,
                "state": EntitlementState.FREE.value,
                "plan": "free",
                "is_premium": False,
                "activated_at": None,
                "expires_at": None
            }

        state_val = row["state"]
        is_premium = (state_val == EntitlementState.PREMIUM_ACTIVE.value)
        return {
            "user_id": user_id,
            "state": state_val,
            "plan": row["plan"],
            "is_premium": is_premium,
            "activated_at": row["activated_at"],
            "expires_at": row["expires_at"]
        }

    @staticmethod
    def set_entitlement_state(user_id: str, state: EntitlementState, plan: str = "premium") -> None:
        conn = get_db()
        cursor = conn.cursor()
        now_iso = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
        INSERT INTO user_entitlements (user_id, state, plan, activated_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            state = excluded.state,
            plan = excluded.plan,
            activated_at = CASE WHEN excluded.state = 'PREMIUM_ACTIVE' THEN excluded.activated_at ELSE user_entitlements.activated_at END,
            updated_at = excluded.updated_at
        """, (user_id, state.value, plan, now_iso, now_iso))
        conn.commit()
        conn.close()


class UsageEntitlementService:
    """Strict server-side usage accounting with idempotency protection.
    Free tier is granted exactly 5 valid claim analyses.
    """
    MAX_FREE_ANALYSES = 5

    @classmethod
    def get_usage(cls, user_id: str) -> Dict[str, Any]:
        # If user is active premium, they have unlimited analyses
        entitlement = EntitlementService.get_entitlement(user_id)
        if entitlement["is_premium"]:
            return {
                "user_id": user_id,
                "used": 0,
                "max": cls.MAX_FREE_ANALYSES,
                "remaining": 999999,
                "is_locked": False,
                "is_premium": True,
                "state": entitlement["state"]
            }

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM usage_entitlement_records WHERE user_id = ? AND feature = 'calculator.claim_analysis'", (user_id,))
        used = cursor.fetchone()["cnt"]
        conn.close()

        remaining = max(0, cls.MAX_FREE_ANALYSES - used)
        is_locked = (remaining <= 0)

        return {
            "user_id": user_id,
            "used": used,
            "max": cls.MAX_FREE_ANALYSES,
            "remaining": remaining,
            "is_locked": is_locked,
            "is_premium": False,
            "state": entitlement["state"]
        }

    @classmethod
    def can_analyze(cls, user_id: str) -> bool:
        usage = cls.get_usage(user_id)
        return not usage["is_locked"]

    @classmethod
    def consume_analysis(cls, user_id: str, request_id: str) -> Tuple[bool, str]:
        """Atomically consumes one analysis unit with idempotency protection.
        Returns: (success: bool, message: str)
        """
        def _operation():
            with db_transaction(exclusive=True) as conn:
                cursor = conn.cursor()
                # 1. Check if request_id already consumed (Idempotency)
                cursor.execute("SELECT id FROM usage_entitlement_records WHERE request_id = ?", (request_id,))
                if cursor.fetchone():
                    return True, "Request ID already verified (idempotent call)."

                # 2. Check entitlement inside the transaction
                cursor.execute("SELECT state FROM user_entitlements WHERE user_id = ?", (user_id,))
                ent_row = cursor.fetchone()
                is_premium = (ent_row and ent_row["state"] == EntitlementState.PREMIUM_ACTIVE.value)

                if not is_premium:
                    cursor.execute(
                        "SELECT COUNT(*) AS cnt FROM usage_entitlement_records WHERE user_id = ? AND feature = 'calculator.claim_analysis'",
                        (user_id,)
                    )
                    used_cnt = cursor.fetchone()["cnt"]
                    if used_cnt >= cls.MAX_FREE_ANALYSES:
                        return False, "5 analisis gratis kamu telah digunakan. Lanjutkan dengan Polya Premium."

                # 3. Consume
                record_id = str(uuid.uuid4())
                now_iso = datetime.now(timezone.utc).isoformat()
                cursor.execute("""
                INSERT INTO usage_entitlement_records (id, user_id, request_id, feature, consumed_at)
                VALUES (?, ?, ?, 'calculator.claim_analysis', ?)
                """, (record_id, user_id, request_id, now_iso))
            return True, "Analysis usage unit consumed successfully."

        try:
            return execute_with_retry(_operation, max_retries=3, retry_delay=0.05)
        except sqlite3.IntegrityError:
            return True, "Request already recorded (idempotent conflict handled)."
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                logger.error(f"Database lock contention during consume_analysis: {e}")
                return False, "DATABASE_LOCKED"
            return False, f"Database operational error: {str(e)}"
        except Exception as e:
            logger.error(f"Error consuming usage: {e}")
            return False, f"Usage deduction failed: {str(e)}"


class PaymentGatewayError(Exception):
    """Raised when payment gateway rejects request or token unavailable."""
    def __init__(self, message: str = "Payment gateway unavailable or rejected request", status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PaymentService:
    """Midtrans Payment Service with strict SHA-512 Signature verification."""
    DEFAULT_AMOUNT = 99000

    @classmethod
    def get_server_key(cls) -> str:
        return os.environ.get("MIDTRANS_SERVER_KEY", "").strip()

    @classmethod
    def get_client_key(cls) -> str:
        return os.environ.get("MIDTRANS_CLIENT_KEY", "").strip()

    @classmethod
    def is_production(cls) -> bool:
        server_key = cls.get_server_key()
        if server_key.startswith("SB-"):
            return False
        if server_key.startswith("Mid-"):
            return True
        return os.environ.get("MIDTRANS_IS_PRODUCTION", "true").lower() in ("true", "1", "yes")

    @classmethod
    def get_snap_api_url(cls) -> str:
        return "https://app.midtrans.com/snap/v1/transactions" if cls.is_production() else "https://app.sandbox.midtrans.com/snap/v1/transactions"

    @classmethod
    def create_checkout(cls, user_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        order_id = f"POLYA-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        tx_id = f"TX-{uuid.uuid4().hex}"
        now_iso = datetime.now(timezone.utc).isoformat()
        server_key = cls.get_server_key()
        client_key = cls.get_client_key()

        snap_token = None
        redirect_url = None
        metadata = {
            "plan": "polya_premium_unlimited",
            "user_id": user_id
        }

        # Request genuine Midtrans Snap Token if Server Key is configured
        if server_key:
            try:
                auth_header = "Basic " + base64.b64encode(f"{server_key}:".encode("utf-8")).decode("utf-8")
                headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": auth_header
                }
                payload = {
                    "transaction_details": {
                        "order_id": order_id,
                        "gross_amount": cls.DEFAULT_AMOUNT
                    },
                    "item_details": [
                        {
                            "id": "polya_premium_unlimited",
                            "price": cls.DEFAULT_AMOUNT,
                            "quantity": 1,
                            "name": "Polya Premium Access (Full Capability)"
                        }
                    ],
                    "customer_details": {
                        "first_name": user_id,
                        "email": f"{user_id}@polya.org" if "@" not in user_id else user_id
                    }
                }
                resp = requests.post(
                    cls.get_snap_api_url(),
                    headers=headers,
                    json=payload,
                    timeout=10.0
                )
                if resp.status_code in (200, 201):
                    res_data = resp.json()
                    snap_token = res_data.get("token")
                    redirect_url = res_data.get("redirect_url")
                    metadata["snap_token"] = snap_token
                    metadata["redirect_url"] = redirect_url
                    logger.info(f"Midtrans Snap token acquired successfully for {order_id}: {snap_token}")
                else:
                    logger.error(f"Midtrans Snap API error [status_code={resp.status_code}]")
            except requests.Timeout:
                logger.error("Midtrans Snap API request timed out")
            except Exception as e:
                logger.error(f"Failed to communicate with Midtrans Snap API: {type(e).__name__}")

        if not snap_token:
            logger.error("Checkout aborted: Midtrans Snap token not available or rejected by gateway.")
            raise PaymentGatewayError("Payment gateway unavailable or rejected request", status_code=502)

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO payment_transactions (
                transaction_id, user_id, order_id, amount, currency, provider,
                provider_status, internal_status, idempotency_key, metadata_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'IDR', 'midtrans', 'pending', 'PAYMENT_PENDING', ?, ?, ?, ?)
            """, (
                tx_id, user_id, order_id, cls.DEFAULT_AMOUNT, idempotency_key or tx_id,
                json.dumps(metadata),
                now_iso, now_iso
            ))

        # Update user entitlement to PAYMENT_PENDING only if not already active premium
        current_ent = EntitlementService.get_entitlement(user_id)
        if not current_ent.get("is_premium"):
            EntitlementService.set_entitlement_state(user_id, EntitlementState.PAYMENT_PENDING)

        return {
            "transaction_id": tx_id,
            "order_id": order_id,
            "amount": cls.DEFAULT_AMOUNT,
            "currency": "IDR",
            "formatted_amount": "Rp99.000",
            "status": "PAYMENT_PENDING",
            "redirect_url": redirect_url,
            "snap_token": snap_token,
            "client_key": client_key,
            "is_production": cls.is_production()
        }

    @classmethod
    def verify_midtrans_signature(
        cls, order_id: str, status_code: str, gross_amount: str, signature_key: str, server_key: Optional[str] = None
    ) -> bool:
        """Verifies Midtrans SHA-512 signature hash:
        SHA512(order_id + status_code + gross_amount + ServerKey)
        """
        key = server_key if server_key is not None else cls.get_server_key()
        if not key:
            logger.error("MIDTRANS_SERVER_KEY not configured. Webhook signature verification rejected.")
            return False
        # Normalize gross_amount to handle decimal .00 formatting from Midtrans
        amount_clean = gross_amount.strip()
        raw_payload = f"{order_id.strip()}{status_code.strip()}{amount_clean}{key}"
        expected = hashlib.sha512(raw_payload.encode("utf-8")).hexdigest()
        return expected.lower() == signature_key.strip().lower()

    @classmethod
    def process_webhook(cls, payload: Dict[str, Any], server_key: Optional[str] = None) -> Tuple[bool, str]:
        order_id = payload.get("order_id")
        status_code = str(payload.get("status_code", ""))
        gross_amount = str(payload.get("gross_amount", ""))
        signature_key = payload.get("signature_key", "")
        transaction_status = payload.get("transaction_status", "")

        if not order_id:
            return False, "Missing order_id in webhook payload"

        if not signature_key:
            return False, "Missing signature_key in webhook payload"

        # 1. Strict signature verification
        is_valid_signature = cls.verify_midtrans_signature(
            order_id, status_code, gross_amount, signature_key, server_key=server_key
        )
        if not is_valid_signature:
            return False, "Invalid SHA-512 signature key"

        # 2. Determine target status
        if transaction_status in ["capture", "settlement"]:
            new_internal_state = EntitlementState.PREMIUM_ACTIVE
        elif transaction_status in ["pending"]:
            new_internal_state = EntitlementState.PAYMENT_PENDING
        elif transaction_status in ["deny", "expire"]:
            new_internal_state = EntitlementState.PAYMENT_FAILED
        elif transaction_status in ["cancel"]:
            new_internal_state = EntitlementState.CANCELLED
        else:
            new_internal_state = EntitlementState.PAYMENT_PENDING

        now_iso = datetime.now(timezone.utc).isoformat()

        # 3. Transactional update with idempotency & out-of-order protection
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, amount, internal_status FROM payment_transactions WHERE order_id = ?", (order_id,))
            tx_row = cursor.fetchone()

            if not tx_row:
                return False, f"Transaction for order {order_id} not found"

            user_id = tx_row["user_id"]
            current_status = tx_row["internal_status"]

            # Out-of-order protection: once settled, do not downgrade to pending or failed
            if current_status == EntitlementState.PREMIUM_ACTIVE.value and new_internal_state != EntitlementState.PREMIUM_ACTIVE:
                logger.warning(f"Ignoring out-of-order webhook for settled order {order_id}: attempted downgrade to {new_internal_state.value}")
                return True, f"Transaction {order_id} already settled; downgrade ignored."

            # Gross amount validation against stored transaction
            try:
                stored_amount = float(tx_row["amount"])
                webhook_amount = float(gross_amount)
                if abs(stored_amount - webhook_amount) > 0.01:
                    return False, f"Gross amount mismatch: expected {stored_amount}, got {webhook_amount}"
            except ValueError:
                return False, "Invalid gross_amount number in payload"

            # Check if user entitlement is also in sync
            cursor.execute("SELECT state FROM user_entitlements WHERE user_id = ?", (user_id,))
            ent_row = cursor.fetchone()
            is_entitlement_settled = (ent_row and ent_row["state"] == EntitlementState.PREMIUM_ACTIVE.value)

            # Duplicate settlement idempotency: do not re-process if already settled AND entitlement in sync
            if current_status == EntitlementState.PREMIUM_ACTIVE.value and new_internal_state == EntitlementState.PREMIUM_ACTIVE:
                if is_entitlement_settled:
                    logger.info(f"Duplicate settlement webhook received for {order_id}; idempotent success.")
                    return True, f"Transaction {order_id} already settled (idempotent duplicate)."
                logger.warning(f"Order {order_id} marked settled but entitlement out-of-sync ({ent_row['state'] if ent_row else 'none'}); re-synchronizing.")

            cursor.execute("""
            UPDATE payment_transactions
            SET provider_status = ?, internal_status = ?, updated_at = ?, verified_at = ?
            WHERE order_id = ?
            """, (transaction_status, new_internal_state.value, now_iso, now_iso, order_id))

            # Update entitlement state inside the transaction; preserve existing activated_at timestamp
            cursor.execute("""
            INSERT INTO user_entitlements (user_id, state, plan, activated_at, updated_at)
            VALUES (?, ?, 'premium', ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                state = excluded.state,
                plan = excluded.plan,
                activated_at = CASE WHEN excluded.state = 'PREMIUM_ACTIVE' THEN COALESCE(user_entitlements.activated_at, excluded.activated_at) ELSE user_entitlements.activated_at END,
                updated_at = excluded.updated_at
            """, (user_id, new_internal_state.value, now_iso, now_iso))

        return True, f"Transaction {order_id} updated to {new_internal_state.value}"

    @classmethod
    def get_user_transactions(cls, user_id: str) -> List[Dict[str, Any]]:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT transaction_id, order_id, amount, currency, provider_status, internal_status, created_at, verified_at
        FROM payment_transactions WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "transaction_id": r["transaction_id"],
                "order_id": r["order_id"],
                "amount": r["amount"],
                "currency": r["currency"],
                "provider_status": r["provider_status"],
                "internal_status": r["internal_status"],
                "created_at": r["created_at"],
                "verified_at": r["verified_at"]
            }
            for r in rows
        ]


class CaseFileGenerator:
    """Produces canonical 10-point Case Files using the Master Prompt #2 Autonomous Intelligence Engine."""

    @classmethod
    def _resolve_final_provenance(cls, model_inv, synth):
        """Resolve final provenance after integrity check on synthesis_output.

        If provenance is verified_success but any critical field is missing from
        synthesis_output (meaning it fell back to template/structural sources),
        downgrade to fallback. If synthesis_output has all keys but no actual content,
        downgrade to unknown.
        """
        final_provider = model_inv.get("provider", "unknown") if model_inv else "unknown"
        final_provenance = model_inv.get("provenance", "unknown") if model_inv else "unknown"

        # Critical synthesis fields that must come from live provider output
        critical_fields = ["argument", "counterargument", "rebuttal", "weakness", "open_questions", "debate_preparation"]

        # Check 1: All critical fields MUST be present in synthesis_output (key existence)
        all_keys_present = all(field in synth for field in critical_fields)

        if final_provenance == "verified_success" and not all_keys_present:
            # Downgrade: some fields missing entirely -> used template/fallback sources
            final_provenance = "fallback"
            final_provider = "fallback"
        elif final_provenance == "verified_success" and all_keys_present:
            # Check 2: All keys present, but verify there's actually non-trivial content
            has_content = any(synth.get(f) for f in critical_fields)
            if not has_content:
                final_provenance = "unknown"
                final_provider = "unknown"

        return final_provider, final_provenance


    @classmethod
    def generate_case_file(
        cls,
        claim: str,
        context: Optional[UserApologeticsContext] = None,
        user_id: str = "guest_user",
        mode: str = "research"
    ) -> CaseFile:
        ctx = context or UserApologeticsContext()
        persp_raw = ctx.user_perspective.value if hasattr(ctx.user_perspective, "value") else str(ctx.user_perspective)
        persp = ContextService.normalize_perspective(persp_raw)
        opp_persp_raw = getattr(ctx, "opponent_perspective", None) or ContextService.get_default_opponent(persp)
        opp_persp = ContextService.normalize_perspective(opp_persp_raw)
        norm_mode = mode.lower() if mode else "research"
        requested_mode = "DEBATE" if norm_mode == "debate" else "RESEARCH"
        ui_locale = getattr(ctx, "ui_locale", "id") or "id"
        debate_locale = getattr(ctx, "debate_locale", "id") or ui_locale or "id"

        try:
            from orchestrator.research_graph import build_research_graph
            graph = build_research_graph()
            run_id = f"run_{uuid.uuid4().hex[:8]}"
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"

            initial_state = {
                "claim_input": claim,
                "run_id": run_id,
                "thread_id": thread_id,
                "user_id": user_id,
                "user_perspective": persp,
                "opponent_perspective": opp_persp,
                "ui_locale": ui_locale,
                "debate_locale": debate_locale,
                "requested_mode": requested_mode,
                "tasks": [],
                "dispatched_agent_records": [],
                "evidence_items": [],
                "provenance_hashes": [],
                "claim_object": None,
                "argument_graph": None,
                "steelman_counterarg": None,
                "contradiction_report": None,
                "verification_records": [],
                "verification_status": "",
                "research_iterations": 0,
                "max_research_iterations": 2,
                "knowledge_gaps": [],
                "evaluation_scorecard": None,
                "debate_preparation": None,
                "case_id": None,
                "execution_traces": [],
                "final_response": None,
                "errors": []
            }
            config = {"configurable": {"thread_id": thread_id}}
            result = graph.invoke(initial_state, config=config)

            case_id = result.get("case_id") or f"CASE-{hashlib.md5(claim.encode('utf-8')).hexdigest()[:8].upper()}"
            # Ensure case_files_v2 record is directly linked to user_id
            try:
                conn_cf = sqlite3.connect(DB_PATH)
                conn_cf.execute("UPDATE case_files_v2 SET user_id = ? WHERE case_id = ?", (user_id, case_id))
                conn_cf.commit()
                conn_cf.close()
            except Exception as e_cf:
                logger.warning(f"Direct case_file user_id update notice: {e_cf}")

            synth = result.get("synthesis_output") or {}
            synth_status = result.get("synthesis_status", "MODEL_ERROR")
            model_inv = result.get("model_invocation") or {}
            retrieval_status = result.get("retrieval_status", "insufficient_evidence")

            # Ingest dynamic primary_evidence if evidence_items is empty
            if not result.get("evidence_items") and synth and isinstance(synth.get("primary_evidence"), dict):
                pe = synth["primary_evidence"]
                pref = pe.get("passage_reference") or pe.get("passage")
                if pref:
                    try:
                        from orchestrator.evidence_engine import Evidence
                        dyn_item = Evidence.create_dynamic_evidence_item(
                            passage_reference=pref,
                            original_language=pe.get("original_language", "Koine Greek"),
                            original_text=pe.get("original_text", ""),
                            transliteration=pe.get("transliteration", ""),
                            indonesian_translation=pe.get("indonesian_translation", ""),
                            english_translation=pe.get("english_translation", ""),
                            witnesses=pe.get("witnesses") or ["Codex Sinaiticus", "Codex Vaticanus"],
                            tokens=pe.get("tokens") or [],
                            critical_apparatus=pe.get("critical_apparatus", "")
                        )
                        result["evidence_items"] = [dyn_item.to_dict()]
                        retrieval_status = "sufficient"
                    except Exception as e_dyn:
                        logger.warning(f"Services dynamic evidence ingestion error: {e_dyn}")

            ev_list = []
            sources_list = []
            if retrieval_status == "sufficient" or result.get("evidence_items"):
                for e in result.get("evidence_items", []):
                    # Format morphology breakdown from tokens if available
                    raw_tokens = e.get("tokens") or []
                    morph_parts = []
                    if isinstance(raw_tokens, list) and raw_tokens:
                        for t in raw_tokens:
                            if isinstance(t, dict):
                                sf = t.get("surface_form", "")
                                lem = t.get("lemma", "")
                                m = t.get("morph") or t.get("morphology", "")
                                lm = t.get("meaning") or t.get("lexical_meaning", "")
                                if sf or lem or m:
                                    morph_parts.append(f"{sf} ({lem}): {m} — {lm}" if lem else f"{sf}: {m} — {lm}")
                            elif isinstance(t, str):
                                morph_parts.append(t)
                    morph_display = " | ".join(morph_parts) if morph_parts else f"Witnesses: {', '.join(e.get('witnesses', []))}"

                    ev_list.append({
                        "language": e.get("original_language", "Koine Greek"),
                        "source_text": f"{e.get('original_text', '')} ({e.get('passage_reference', '')})",
                        "transliteration": e.get("transliteration", ""),
                        "morphology": morph_display,
                        "manuscripts": e.get("witnesses", []),
                        "critical_apparatus": e.get("theological_implication") or f"Provenance SHA-256: {e.get('provenance_hash', '')}"
                    })
                sources_list = [
                    {"citation": f"{e.get('passage_reference')} ({e.get('source_id')})", "type": "Primary Scripture Witness"}
                    for e in result.get("evidence_items", [])
                ]
                for ce in result.get("corpus_evidence", []):
                    sources_list.append({"citation": ce.get("title", ""), "type": "Academic Corpus Index"})
            else:
                ev_list = []
                sources_list = []

            prep = result.get("debate_preparation") or {}
            arg_data = result.get("argument_graph") or {}
            steelman = result.get("steelman_counterarg") or {}

            # Dynamic synthesis extraction with locale-sensitive fallbacks
            eff_loc = (debate_locale or ui_locale or "id").strip().lower()
            is_zh_loc = eff_loc.startswith("zh")
            is_en_loc = eff_loc.startswith("en")

            if is_zh_loc:
                def_arg = f"针对主张 '{claim}' 的文献语言学法医分析证实了原典文本的内在一致性。"
                def_counter = "反对方在缺乏原始手抄本检验的情况下提出了传统神学抗辩。"
                def_rebuttal = "客观反驳揭示了经文意义的扭曲，确立了正典的内在一致性。"
                def_weakness = "词汇学薄弱性与对源语言文本语境的忽视。"
                def_questions = [
                    "反对方如何在缺乏原始手抄本引证的情况下证实其主张？",
                    "学术标准词典是否支持对方对源语言的诠释？"
                ]
                def_trap = "将反对方锁定在源语言词汇的严格学术定义上。"
                def_tempo = "提出精炼有力的苏格拉底式质询，锁定反对方在原始文献上的妥协。"
            elif is_en_loc:
                def_arg = f"Forensic analysis of the claim '{claim}' demonstrates internal primary text integrity."
                def_counter = "The opposition asserts objections without primary manuscript verification."
                def_rebuttal = "Objective rebuttal dismantling semantic distortion and upholding canonical consistency."
                def_weakness = "Lexicographical vulnerability and disregard of original source language context."
                def_questions = [
                    "How does the opposition substantiate the claim without primary manuscript citations?",
                    "Do standard academic lexicons support the opposition's interpretation?"
                ]
                def_trap = "Lock the interlocutor to the strict definition of source language vocabulary."
                def_tempo = "Ask short, structured Socratic questions, securing concessions on primary texts."
            else:
                def_arg = f"Analisis forensik atas klaim '{claim}' membuktikan integritas teks primer."
                def_counter = "Pihak lawan mendalilkan keberatan tanpa verifikasi naskah primer."
                def_rebuttal = "Rebuttal objektif membongkar distorsi makna dan menegakkan konsistensi kanon."
                def_weakness = "Kelemahan leksikografi dan pengabaian konteks bahasa sumber."
                def_questions = [
                    "Bagaimana lawan membuktikan klaim tanpa rujukan naskah primer?",
                    "Apakah leksikon akademik standar mendukung pemaknaan lawan?"
                ]
                def_trap = "Kuncilah lawan pada definisi kata bahasa asli."
                def_tempo = "Ajukan pertanyaan Sokratik terstruktur, kunci lawan pada konsesi naskah primer."

            arg_val = synth.get("argument") or arg_data.get("claim", def_arg)
            counterarg_val = synth.get("counterargument") or steelman.get("opponent_reasoning", def_counter)
            rebuttal_val = synth.get("rebuttal") or steelman.get("rebuttal", def_rebuttal)
            weakness_val = synth.get("weakness") or "; ".join(steelman.get("weaknesses", [def_weakness]))

            open_q_val = synth.get("open_questions") or prep.get("follow_up_questions", def_questions)

            if synth.get("debate_preparation"):
                db_prep = synth["debate_preparation"]
                trap_val = db_prep.get("cross_examination_trap") or def_trap
                tempo_val = db_prep.get("recommended_tempo") or def_tempo
            else:
                trap_val = prep.get("cross_examination_questions", [def_trap])[0] if prep.get("cross_examination_questions") else def_trap
                tempo_val = def_tempo

            prep_val = {
                "cross_examination_trap": trap_val,
                "recommended_tempo": tempo_val
            }

            # Inject canonical 8-round dialectical simulation (ZUMA vs Interlocutor) ONLY in DEBATE mode
            canonical_sim = None
            if requested_mode == "DEBATE":
                try:
                    from orchestrator.zuma_skill_engine import ZumaSkillEngine
                    z_ctx = {
                        "user_perspective": persp,
                        "opponent_perspective": opp_persp,
                        "debate_locale": debate_locale,
                        "ui_locale": ui_locale,
                        "source_locale": getattr(ctx, "source_locale", None) or ContextService.get_default_source_locale(persp)
                    }
                    canonical_sim = ZumaSkillEngine.generate_canonical_8_round_simulation(
                        claim=claim,
                        evidence_items=result.get("evidence_items", []),
                        context=z_ctx,
                        debate_prep=prep,
                        synthesis_output=synth
                    )
                    prep_val["canonical_8_rounds"] = canonical_sim
                except Exception as e_sim:
                    logger.warning(f"Canonical 8-round debate simulation injection skipped: {e_sim}")
            else:
                canonical_sim = None
                prep_val["canonical_8_rounds"] = None

            # Generate full LinguisticExegesisPackage (BibleHub text analysis standard)
            linguistic_exegesis = None
            try:
                from orchestrator.exegesis_engine import ExegesisEngine
                linguistic_exegesis = ExegesisEngine.generate_linguistic_exegesis_package(
                    claim=claim,
                    evidence_items=result.get("evidence_items", []),
                    synthesis_output=synth,
                    context=ctx
                )
            except Exception as e_exegesis:
                logger.warning(f"Linguistic exegesis package generation notice: {e_exegesis}")

            # Inject dynamic ZUMA 8-point simulated debate into output (mode DEBATE only).
            if requested_mode == "DEBATE":
                try:
                    from orchestrator.zuma_skill_engine import ZumaSkillEngine
                    zuma_prep = dict(prep_val)
                    if prep and isinstance(prep, dict):
                        zuma_prep["evidence"] = prep.get("evidence", [])
                        zuma_prep["strongest_opponent_argument"] = prep.get("strongest_opponent_argument", "")
                        zuma_prep["cross_examination_questions"] = prep.get("cross_examination_questions", [])
                        zuma_prep["defensive_responses"] = prep.get("defensive_responses", [])
                        zuma_prep["responses"] = prep.get("responses", [])
                        zuma_prep["closing"] = prep.get("closing", "")
                    z_ctx = {
                        "user_perspective": persp,
                        "opponent_perspective": opp_persp,
                        "debate_locale": debate_locale,
                        "ui_locale": ui_locale,
                        "source_locale": getattr(ctx, "source_locale", None) or ContextService.get_default_source_locale(persp)
                    }
                    sim_deb = ZumaSkillEngine.generate_zuma_forensic_simulation(
                        claim, context=z_ctx
                    )
                    prep_val["forensic_simulation"] = sim_deb
                    prep_val["header_simulasi"] = sim_deb.get("header")
                    prep_val["babak_1_postulat"] = sim_deb.get("babak_1", {}).get("paparan_pihak_a")
                    prep_val["babak_2_cross_exam"] = sim_deb.get("babak_2", {}).get("pertanyaan_presisi")
                    prep_val["babak_3_forensik"] = sim_deb.get("babak_3", {}).get("bedah_bahasa_sumber")
                    prep_val["babak_4_evaluasi"] = sim_deb.get("babak_4", {}).get("evaluasi_kekuatan_bukti")
                except Exception as e:
                    logger.warning(f"ZUMA simulated debate injection skipped: {e}")

            verif_val = result.get("verification_status") or ("UNSUPPORTED" if retrieval_status == "insufficient_evidence" else "PARTIALLY_SUPPORTED")
            if retrieval_status == "insufficient_evidence":
                notice_val = f"INSUFFICIENT_EVIDENCE — Klaim berada di luar cakupan korpus atau bukti naskah tidak mencukupi | Verification: {verif_val}"
            elif synth_status == "SUCCESS":
                agent_name = model_inv.get("agent", "hermes")
                notice_val = f"AI_SYNTHESIS_SUCCESS — Mode: {norm_mode} (Agent: {agent_name}) | Verification: {verif_val}"
            elif synth_status == "PARTIAL":
                notice_val = f"PARTIAL_SYNTHESIS — Model output unstructured or fallback used | Verification: {verif_val}"
            elif synth_status == "MODEL_ERROR":
                notice_val = f"MODEL_ERROR — Model dispatch failed; structural analysis returned | Verification: {verif_val}"
            else:
                notice_val = f"{synth_status} — Structural analysis returned | Verification: {verif_val}"

            # Recovery-016: provenance integrity check.
            final_provider, final_provenance = CaseFileGenerator._resolve_final_provenance(model_inv, synth)

            opp_display = "JEWISH" if "JEWISH" in str(opp_persp_raw).upper() else opp_persp.upper()
            ctx_summary_templates = {
                "en": f"Analyzed in {requested_mode} mode from {persp.upper()} perspective versus {opp_display} (Debate Language: {debate_locale}).",
                "id": f"Dianalisis dalam mode {requested_mode} perspektif {persp.upper()} versus {opp_display} (Bahasa Debat: {debate_locale}).",
                "ja": f"{persp.upper()}の視点から{opp_display}に対抗して{requested_mode}モードで分析（討論言語: {debate_locale}）。",
                "ar": f"تم التحليل في وضع {requested_mode} من منظور {persp.upper()} ضد {opp_display} (لغة المناظرة: {debate_locale}).",
                "zh": f"在{requested_mode}模式下从{persp.upper()}视角对决{opp_display}进行分析（辩论语言: {debate_locale}）。",
                "ko": f"{persp.upper()} 관점에서 {opp_display}를 상대로 {requested_mode} 모드로 분석됨 (토론 언어: {debate_locale}).",
                "es": f"Analizado en modo {requested_mode} desde la perspectiva {persp.upper()} frente a {opp_display} (Idioma del debate: {debate_locale}).",
                "fr": f"Analysé en mode {requested_mode} du point de vue de {persp.upper()} contre {opp_display} (Langue du débat: {debate_locale}).",
                "de": f"Analysiert im {requested_mode}-Modus aus der Perspektive {persp.upper()} gegen {opp_display} (Debattensprache: {debate_locale}).",
                "ru": f"Анализ проведен в режиме {requested_mode} с позиции {persp.upper()} против {opp_display} (Язык дебатов: {debate_locale}).",
                "pt": f"Analisado no modo {requested_mode} sob a perspectiva {persp.upper()} contra {opp_display} (Idioma do debate: {debate_locale}).",
                "it": f"Analizzato in modalità {requested_mode} dalla prospettiva {persp.upper()} contro {opp_display} (Lingua del dibattito: {debate_locale}).",
                "tr": f"{persp.upper()} perspektifinden {opp_display} karşısında {requested_mode} modunda analiz edildi (Münazara Dili: {debate_locale}).",
                "ur": f"{persp.upper()} کے نقطہ نظر سے {opp_display} کے خلاف {requested_mode} موڈ میں تجزیہ کیا گیا (مناظرے کی زبان: {debate_locale})۔",
                "fa": f"در حالت {requested_mode} از دیدگاه {persp.upper()} در برابر {opp_display} تحلیل شد (زبان مناظره: {debate_locale}).",
                "hi": f"{persp.upper()} दृष्टिकोण से {opp_display} के विरुद्ध {requested_mode} मोड में विश्लेषण किया गया (बहस की भाषा: {debate_locale})।",
                "bn": f"{persp.upper()} দৃষ্টিকোণ থেকে {opp_display} এর বিরুদ্ধে {requested_mode} মোডে বিশ্লেষণ করা হয়েছে (বিতর্কের ভাষা: {debate_locale})।"
            }
            ctx_summary = ctx_summary_templates.get(debate_locale, ctx_summary_templates["en"] if debate_locale != "id" else ctx_summary_templates["id"])
            return CaseFile(
                case_id=case_id,
                claim=claim,
                context=ctx_summary,
                evidence=ev_list,
                argument=arg_val,
                counterargument=counterarg_val,
                rebuttal=rebuttal_val,
                weakness=weakness_val,
                sources=sources_list,
                open_questions=open_q_val,
                debate_preparation=prep_val,
                canonical_simulation=canonical_sim,
                linguistic_exegesis=linguistic_exegesis,
                is_demo=False,
                notice=notice_val,
                synthesis_status=synth_status,
                retrieval_status=retrieval_status,
                fallback_used=bool(model_inv.get("fallback_used") if model_inv else False),
                provider=final_provider,
                provenance=final_provenance
            )
        except Exception as exc:
            logger.error(f"Real intelligence execution fallback: {exc}")
            case_id = f"CASE-{hashlib.md5(claim.encode('utf-8')).hexdigest()[:8].upper()}"
            opp_display = "JEWISH" if "JEWISH" in str(opp_persp_raw).upper() else opp_persp.upper()
            sim_deb = []
            fallback_prep = {}
            fallback_canonical_sim = None
            if requested_mode == "DEBATE":
                try:
                    from orchestrator.zuma_skill_engine import ZumaSkillEngine
                    z_ctx = {
                        "user_perspective": persp,
                        "opponent_perspective": opp_persp,
                        "debate_locale": getattr(ctx, "debate_locale", "id"),
                        "source_locale": getattr(ctx, "source_locale", None) or ContextService.get_default_source_locale(persp)
                    }
                    fallback_canonical_sim = ZumaSkillEngine.generate_canonical_8_round_simulation(
                        claim=claim,
                        evidence_items=[],
                        context=z_ctx,
                        debate_prep={},
                        synthesis_output={}
                    )
                except Exception:
                    pass

            fallback_exegesis = None
            try:
                from orchestrator.exegesis_engine import ExegesisEngine
                fallback_exegesis = ExegesisEngine.generate_linguistic_exegesis_package(
                    claim=claim,
                    evidence_items=[],
                    synthesis_output={},
                    context=ctx
                )
            except Exception:
                pass

            if requested_mode == "DEBATE":
                try:
                    from orchestrator.zuma_skill_engine import ZumaSkillEngine
                    z_ctx = {
                        "user_perspective": persp,
                        "opponent_perspective": opp_persp,
                        "debate_locale": getattr(ctx, "debate_locale", "id"),
                        "source_locale": getattr(ctx, "source_locale", None) or ContextService.get_default_source_locale(persp)
                    }
                    sim_deb = ZumaSkillEngine.generate_zuma_forensic_simulation(
                        claim, context=z_ctx
                    )
                    fallback_prep = {
                        "opening": "Analisis forensik dialektika ZUMA diaktifkan.",
                        "opening_strategy": "Bedah teks primer dan konsistensi ontologis.",
                        "cross_examination_trap": "Tuntut bukti teks primer tanpa asumsi dogmatis.",
                        "tempo": "Tegas, presisi, dingin.",
                        "forensic_simulation": sim_deb,
                        "header_simulasi": sim_deb.get("header"),
                        "babak_1_postulat": sim_deb.get("babak_1", {}).get("paparan_pihak_a"),
                        "babak_2_cross_exam": sim_deb.get("babak_2", {}).get("pertanyaan_presisi"),
                        "babak_3_forensik": sim_deb.get("babak_3", {}).get("bedah_bahasa_sumber"),
                        "babak_4_evaluasi": sim_deb.get("babak_4", {}).get("evaluasi_kekuatan_bukti"),
                        "canonical_8_rounds": fallback_canonical_sim
                    }
                except Exception:
                    pass

            return CaseFile(
                case_id=case_id,
                claim=claim,
                context=f"Dianalisis dalam kerangka perspektif {ctx.user_perspective.value.upper()} versus {opp_persp}.",
                evidence=[
                    {
                        "language": "Koine Greek",
                        "source_text": "νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν. (Roma 3:31)",
                        "transliteration": "nomon oun katargoumen dia tēs pisteōs? mē genoito; alla nomon histanomen.",
                        "morphology": "histanomen = present active indicative durative (we establish/uphold)",
                        "manuscripts": ["P46", "Codex Sinaiticus", "Codex Vaticanus"],
                        "critical_apparatus": "NA28 reading identical; zero variant on 'histanomen'"
                    }
                ],
                argument=f"Secara forensik teks, premis klaim '{claim[:40]}...' gagal memperhitungkan sintaksis gramatika bahasa sumber asli.",
                counterargument="Tinjauan pembacaan alternatif akademis terhadap konteks naskah primer.",
                rebuttal="Konteks sastra terdekat membuktikan Paulus menegakkan hukum Taurat.",
                weakness="Batasan hermeneutik memerlukan pengujian kritis terhadap varian naskah kuno.",
                sources=[{"citation": "Nestle-Aland Novum Testamentum Graece, 28th Edition", "type": "Critical Edition"}],
                open_questions=["Bagaimana naskah primer bahasa sumber menjelaskan klaim ini?"],
                debate_preparation=fallback_prep if requested_mode == "DEBATE" else {
                    "cross_examination_trap": "",
                    "recommended_tempo": "",
                    "simulated_debate": [],
                    "canonical_8_rounds": None
                },
                canonical_simulation=fallback_canonical_sim,
                linguistic_exegesis=fallback_exegesis,
                is_demo=True,
                notice="DEMO / MOCK DATA — Strictly for testing UI and structure",
                provider="unknown",
                provenance="template"
            )
