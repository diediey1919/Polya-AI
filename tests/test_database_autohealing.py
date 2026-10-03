"""
Test Suite: Database Auto-Healing & Lifespan Verification
Tests:
1. Fresh nonexistent DB initialization
2. Corrupt / 0-byte DB self-healing
3. Existing DB data preservation (non-destructive DDL)
4. Full API entitlement and session operations on healed DB
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
import pytest

# Add web directory to sys.path
WEB_DIR = Path(__file__).resolve().parent.parent / "web"
if str(WEB_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_DIR))

import services
from services import (
    get_db,
    init_foundation_db,
    verify_foundation_schema,
    UsageEntitlementService,
    EntitlementService,
    PaymentService,
)


def test_fresh_nonexistent_database():
    """Verify that a non-existent database file is created and fully seeded with required schema."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "new_arena.db")
        assert not os.path.exists(db_path)

        # Schema should verify False before init
        assert not verify_foundation_schema(db_path)

        # Run initialization
        init_foundation_db(db_path)

        # File must exist and be non-empty
        assert os.path.exists(db_path)
        assert os.path.getsize(db_path) > 0

        # Schema must be verified
        assert verify_foundation_schema(db_path)

        # Verify tables directly via sqlite3
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {
            "user_entitlements",
            "usage_entitlement_records",
            "payment_transactions",
            "user_apologetics_context",
            "arena_users",
        }
        assert expected.issubset(tables)


def test_corrupt_zero_byte_database():
    """Verify that a 0-byte empty file is safely healed without operational failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "zero_byte.db")
        # Create explicit 0-byte file
        with open(db_path, "wb") as f:
            pass
        assert os.path.exists(db_path)
        assert os.path.getsize(db_path) == 0

        # Schema should verify False on 0-byte file
        assert not verify_foundation_schema(db_path)

        # Run initialization
        init_foundation_db(db_path)

        # Size must be > 0 and schema verified
        assert os.path.getsize(db_path) > 0
        assert verify_foundation_schema(db_path)

        # Ensure operations succeed
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_entitlements;")
        count = cursor.fetchone()[0]
        assert count == 0
        conn.close()


def test_existing_valid_database_data_preservation():
    """Verify that auto-healing is non-destructive and preserves existing records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "persistent.db")
        init_foundation_db(db_path)

        # Insert test records
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO arena_users (user_id, email, name, role)
            VALUES ('usr_test_1', 'researcher@polya.ai', 'Dr. Zuma', 'apologist');
        """)
        cursor.execute("""
            INSERT INTO user_entitlements (user_id, state, plan)
            VALUES ('usr_test_1', 'PREMIUM_ACTIVE', 'premium');
        """)
        cursor.execute("""
            INSERT INTO usage_entitlement_records (id, user_id, request_id, feature, consumed_at)
            VALUES ('rec_1', 'usr_test_1', 'req_abc', 'calculator.claim_analysis', '2026-10-04T00:00:00Z');
        """)
        conn.commit()
        conn.close()

        # Re-run initialization (simulating service restart / lifespan hook)
        init_foundation_db(db_path)

        # Verify records are preserved
        conn = get_db(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, role FROM arena_users WHERE user_id = 'usr_test_1';")
        user = cursor.fetchone()
        assert user["name"] == "Dr. Zuma"
        assert user["role"] == "apologist"

        cursor.execute("SELECT state, plan FROM user_entitlements WHERE user_id = 'usr_test_1';")
        ent = cursor.fetchone()
        assert ent["state"] == "PREMIUM_ACTIVE"
        assert ent["plan"] == "premium"

        cursor.execute("SELECT request_id FROM usage_entitlement_records WHERE user_id = 'usr_test_1';")
        rec = cursor.fetchone()
        assert rec["request_id"] == "req_abc"
        conn.close()


def test_api_works_with_autohealed_db(monkeypatch):
    """Test FastAPI TestClient interacting with an auto-healed database."""
    from fastapi.testclient import TestClient
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "api_test.db")
        
        # Point services DB_PATH to temporary test database
        monkeypatch.setattr(services, "DB_PATH", db_path)
        
        # Create 0-byte file to test real lifecycle auto-healing
        with open(db_path, "wb") as f:
            pass
        assert os.path.getsize(db_path) == 0

        # Import app
        from app import app
        with TestClient(app) as client:
            # 1. Check meta languages endpoint
            resp = client.get("/api/v1/meta/languages")
            assert resp.status_code == 200
            assert len(resp.json()["languages"]) == 17

            # 2. Check auth session creation (creates user in arena_users)
            resp = client.post("/api/v1/auth/session", json={
                "email": "test_user@polya.ai",
                "name": "Test Scholar",
                "provider": "google",
                "token": "mock_token"
            })
            assert resp.status_code == 200
            user_id = resp.json()["profile"]["user_id"]
            assert user_id.startswith("usr_")

            # 3. Check calculator analysis (records usage in usage_entitlement_records)
            calc_resp = client.post("/api/v1/calculator/analyze", json={
                "claim": "Yesus menyebut diri-Nya Anak Allah",
                "user_id": user_id,
                "request_id": "test_req_001",
                "perspective": "christian"
            })
            assert calc_resp.status_code == 200
            data = calc_resp.json()
            assert data["success"] is True
            assert data["usage"]["remaining"] == 4
            assert data["case_file"]["case_id"].upper().startswith("CASE")
            assert len(data["case_file"]["sources"]) > 0
