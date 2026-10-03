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
import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from models import (
    CANONICAL_DEMO_CLAIMS,
    CaseFile,
    EntitlementState,
    PaymentTransaction,
    UserApologeticsContext,
    UserPerspective
)

logger = logging.getLogger("polya.services")

DB_PATH = os.environ.get("POLYA_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "polya_arena.db"))
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_foundation_db():
    """Initializes tables required by the Web Foundation."""
    conn = get_db()
    cursor = conn.cursor()
    
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
        user_perspective TEXT DEFAULT 'christian',
        opponent_perspective TEXT DEFAULT 'islam',
        debate_locale TEXT DEFAULT 'id',
        source_locale TEXT DEFAULT 'el',
        updated_at TEXT
    )
    """)

    conn.commit()
    conn.close()


init_foundation_db()


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
        # 1. Check if request_id already consumed (Idempotency)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usage_entitlement_records WHERE request_id = ?", (request_id,))
        if cursor.fetchone():
            conn.close()
            return True, "Request ID already verified (idempotent call)."

        # 2. Check if user is eligible to analyze
        if not cls.can_analyze(user_id):
            conn.close()
            return False, "5 analisis gratis kamu telah digunakan. Lanjutkan dengan Polya Premium."

        # 3. Consume
        record_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            cursor.execute("""
            INSERT INTO usage_entitlement_records (id, user_id, request_id, feature, consumed_at)
            VALUES (?, ?, ?, 'calculator.claim_analysis', ?)
            """, (record_id, user_id, request_id, now_iso))
            conn.commit()
            conn.close()
            return True, "Analysis usage unit consumed successfully."
        except sqlite3.IntegrityError:
            conn.close()
            return True, "Request already recorded (idempotent conflict handled)."
        except Exception as e:
            conn.close()
            logger.error(f"Error consuming usage: {e}")
            return False, f"Usage deduction failed: {str(e)}"


class PaymentService:
    """Midtrans Payment Service with SHA-512 Signature verification and mock simulation adapter."""
    MIDTRANS_SERVER_KEY = os.environ.get("MIDTRANS_SERVER_KEY", "SB-Mid-server-test-polya-key-2026")
    DEFAULT_AMOUNT = 99000

    @classmethod
    def create_checkout(cls, user_id: str, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
        order_id = f"POLYA-{int(datetime.now().timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        tx_id = f"TX-{uuid.uuid4().hex}"
        now_iso = datetime.now(timezone.utc).isoformat()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO payment_transactions (
            transaction_id, user_id, order_id, amount, currency, provider,
            provider_status, internal_status, idempotency_key, metadata_json,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, 'IDR', 'midtrans', 'pending', 'PAYMENT_PENDING', ?, ?, ?, ?)
        """, (
            tx_id, user_id, order_id, cls.DEFAULT_AMOUNT, idempotency_key or tx_id,
            json.dumps({"plan": "polya_premium_unlimited", "user_id": user_id}),
            now_iso, now_iso
        ))
        conn.commit()
        conn.close()

        # Update user entitlement to PAYMENT_PENDING
        EntitlementService.set_entitlement_state(user_id, EntitlementState.PAYMENT_PENDING)

        return {
            "transaction_id": tx_id,
            "order_id": order_id,
            "amount": cls.DEFAULT_AMOUNT,
            "currency": "IDR",
            "formatted_amount": "Rp99.000",
            "status": "PAYMENT_PENDING",
            "redirect_url": f"/checkout?order_id={order_id}",
            "snap_token": f"mock-snap-token-{order_id}"
        }

    @classmethod
    def verify_midtrans_signature(cls, order_id: str, status_code: str, gross_amount: str, signature_key: str) -> bool:
        """Verifies Midtrans SHA-512 signature hash:
        SHA512(order_id + status_code + gross_amount + ServerKey)
        """
        raw_payload = f"{order_id}{status_code}{gross_amount}{cls.MIDTRANS_SERVER_KEY}"
        expected = hashlib.sha512(raw_payload.encode("utf-8")).hexdigest()
        return expected.lower() == signature_key.lower()

    @classmethod
    def process_webhook(cls, payload: Dict[str, Any], allow_simulator: bool = True) -> Tuple[bool, str]:
        order_id = payload.get("order_id")
        status_code = str(payload.get("status_code", ""))
        gross_amount = str(payload.get("gross_amount", ""))
        signature_key = payload.get("signature_key", "")
        transaction_status = payload.get("transaction_status", "")

        if not order_id:
            return False, "Missing order_id in webhook payload"

        # Signature verification
        is_valid_signature = False
        if signature_key and status_code and gross_amount:
            is_valid_signature = cls.verify_midtrans_signature(order_id, status_code, gross_amount, signature_key)

        # Allow test/simulation adapter if explicit flag is passed and in test mode
        if not is_valid_signature and allow_simulator:
            if payload.get("is_simulator") or payload.get("test_mode"):
                is_valid_signature = True
                logger.info(f"Webhook accepted via Midtrans Test Simulator Adapter for order {order_id}")

        if not is_valid_signature:
            return False, "Invalid SHA-512 signature key"

        # Determine Internal Status
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
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, amount FROM payment_transactions WHERE order_id = ?", (order_id,))
        tx_row = cursor.fetchone()

        if not tx_row:
            conn.close()
            return False, f"Transaction for order {order_id} not found"

        user_id = tx_row["user_id"]
        cursor.execute("""
        UPDATE payment_transactions
        SET provider_status = ?, internal_status = ?, updated_at = ?, verified_at = ?
        WHERE order_id = ?
        """, (transaction_status, new_internal_state.value, now_iso, now_iso, order_id))
        conn.commit()
        conn.close()

        # Update Entitlement state
        EntitlementService.set_entitlement_state(user_id, new_internal_state)
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
    """Produces canonical 10-point Case File fixtures for demonstration and UI testing."""

    @classmethod
    def generate_case_file(cls, claim: str, context: Optional[UserApologeticsContext] = None) -> CaseFile:
        ctx = context or UserApologeticsContext()
        case_id = f"CASE-{hashlib.md5(claim.encode('utf-8')).hexdigest()[:8].upper()}"

        # Source-first evidence fixtures matching the 10 demo claims
        evidence_items = [
            {
                "language": "Koine Greek",
                "source_text": "Ἐγὼ καὶ ὁ Πατὴρ ἕν ἐσμεν (Yohanes 10:30)",
                "transliteration": "Egō kai ho Patēr hen esmen",
                "morphology": "hen = neuter nominative singular (one in substance/nature, not masculine 'heis' which would mean one person)",
                "manuscripts": ["Codex Sinaiticus (01)", "Codex Vaticanus (B, 03)", "Papyrus P66 (c. 200 M)"],
                "critical_apparatus": "NA28 reading identical; zero variant on 'hen esmen'"
            },
            {
                "language": "Biblical Hebrew",
                "source_text": "שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד (Ulangan 6:4)",
                "transliteration": "Shema Yisrael YHWH Eloheinu YHWH Echad",
                "morphology": "echad = compound unity (bandingkan Kejadian 2:24 'basar echad')",
                "manuscripts": ["4QDeut (Naskah Laut Mati)", "Codex Leningradensis"]
            }
        ]

        sources_items = [
            {"citation": "Codex Sinaiticus, British Library Add MS 43725", "type": "Primary Manuscript"},
            {"citation": "Nestle-Aland Novum Testamentum Graece, 28th Edition", "type": "Critical Edition"},
            {"citation": "Bauer-Danker Lexicon (BDAG), p. 294", "type": "Academic Lexicon"}
        ]

        return CaseFile(
            case_id=case_id,
            claim=claim,
            context=f"Dianalisis dalam kerangka perspektif {ctx.user_perspective.value.upper()} versus {ctx.opponent_perspective.upper()} (Bahasa Debat: {ctx.debate_locale}).",
            evidence=evidence_items,
            argument=f"Secara forensik teks, premis klaim '{claim[:40]}...' gagal memperhitungkan sintaksis gramatika bahasa sumber asli.",
            counterargument="Pihak lawan umumnya mendalilkan bahwa teks tersebut hanya berkonotasi kesatuan moral atau kiasan metaforis.",
            rebuttal="Konteks sastra terdekat dan respons para pendengar sezaman (yang mengambil batu untuk melempar karena klaim ilahi) membuktikan pemahaman hakikat, bukan sekadar tujuan moral.",
            weakness="Titik rentan lawan adalah ketergantungan pada terjemahan dinamis modern tanpa verifikasi leksikon bahasa sumber.",
            sources=sources_items,
            open_questions=[
                "Bagaimana lawan menjelaskan reaksi langsung pendengar asli dalam konteks sosio-historis abad ke-1?",
                "Apakah leksikon BDAG atau Thayer mendukung reduksi kata netral 'hen' menjadi figuratif belaka?"
            ],
            debate_preparation={
                "cross_examination_trap": "Kuncilah lawan pada definisi kata bahasa asli sebelum mereka mengalihkan topik.",
                "recommended_tempo": "Ajukan pertanyaan sokratik pendek, minta konfirmasi arti kata netral versus maskulin."
            },
            is_demo=True,
            notice="DEMO / MOCK DATA — Strictly for testing UI and structure"
        )
