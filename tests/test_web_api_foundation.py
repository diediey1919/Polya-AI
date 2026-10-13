import os
import sys
from pathlib import Path

# Ensure web directory is in sys.path so 'from models import ...' succeeds
WEB_DIR = str(Path(__file__).resolve().parent.parent / "web")
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

import sqlite3
import tempfile
import threading
import time
import pytest
from fastapi.testclient import TestClient

from web.app import app
from web.services import (
    init_foundation_db,
    db_transaction,
    execute_with_retry,
    UsageEntitlementService,
    EntitlementService,
    EntitlementState,
)


@pytest.fixture
def temp_web_db(monkeypatch):
    """Provides an isolated SQLite database for web service tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Initialize schema
    init_foundation_db(db_path)

    # Patch DB_PATH in web.services, services, and web.api_foundation
    monkeypatch.setattr("web.services.DB_PATH", db_path)
    try:
        import services
        monkeypatch.setattr(services, "DB_PATH", db_path)
    except Exception:
        pass
    if hasattr(app.state, "db_path"):
        monkeypatch.setattr(app.state, "db_path", db_path)

    yield db_path

    if os.path.exists(db_path):
        os.remove(db_path)


def test_01_db_transaction_commit_and_close(temp_web_db):
    """Verifies that transactions commit and close handles cleanly."""
    with db_transaction(temp_web_db) as conn:
        conn.execute("INSERT INTO arena_users (user_id, name) VALUES ('u1', 'Alice')")

    # Verify persisted in a separate connection
    conn2 = sqlite3.connect(temp_web_db)
    row = conn2.execute("SELECT name FROM arena_users WHERE user_id = 'u1'").fetchone()
    conn2.close()
    assert row is not None
    assert row[0] == "Alice"


def test_02_db_transaction_rollback_on_exception(temp_web_db):
    """Verifies that exceptions trigger rollback and handle close."""
    with pytest.raises(ValueError):
        with db_transaction(temp_web_db) as conn:
            conn.execute("INSERT INTO arena_users (user_id, name) VALUES ('u2', 'Bob')")
            raise ValueError("Deliberate failure")

    conn2 = sqlite3.connect(temp_web_db)
    row = conn2.execute("SELECT name FROM arena_users WHERE user_id = 'u2'").fetchone()
    conn2.close()
    assert row is None


def test_03_transient_lock_recovers_with_retry(temp_web_db):
    """Verifies that transient database locks recover gracefully via execute_with_retry."""
    recovered = False

    def flaky_op():
        nonlocal recovered
        if not recovered:
            recovered = True
            raise sqlite3.OperationalError("database is locked")
        with db_transaction(temp_web_db) as conn:
            conn.execute("INSERT INTO arena_users (user_id, name) VALUES ('u3', 'Charlie')")
        return True

    res = execute_with_retry(flaky_op, max_retries=5, retry_delay=0.01)
    assert res is True
    assert recovered is True

    conn2 = sqlite3.connect(temp_web_db)
    row = conn2.execute("SELECT name FROM arena_users WHERE user_id = 'u3'").fetchone()
    conn2.close()
    assert row is not None
    assert row[0] == "Charlie"


def test_04_consume_analysis_idempotency_no_double_spend(temp_web_db, monkeypatch):
    """Verifies that retrying the same request_id does not double-spend free analysis quota."""
    monkeypatch.setattr("web.services.DB_PATH", temp_web_db)
    user_id = "test_user_idempotent"
    req_id = "req_fixed_123"

    # First consumption
    ok1, msg1 = UsageEntitlementService.consume_analysis(user_id, req_id)
    assert ok1 is True

    # Second consumption with same request_id (idempotent call)
    ok2, msg2 = UsageEntitlementService.consume_analysis(user_id, req_id)
    assert ok2 is True
    assert "already" in msg2.lower()

    # Verify only 1 record created
    conn = sqlite3.connect(temp_web_db)
    cnt = conn.execute("SELECT COUNT(*) FROM usage_entitlement_records WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    assert cnt == 1


def test_05_quota_exhausted_distinct_from_db_lock(temp_web_db, monkeypatch):
    """Verifies that free quota exhaustion is returned as business failure, distinct from db lock."""
    monkeypatch.setattr("web.services.DB_PATH", temp_web_db)
    user_id = "test_user_quota"

    # Consume 5 free units
    for i in range(5):
        ok, _ = UsageEntitlementService.consume_analysis(user_id, f"req_{i}")
        assert ok is True

    # 6th attempt must fail with quota message
    ok6, msg6 = UsageEntitlementService.consume_analysis(user_id, "req_6")
    assert ok6 is False
    assert "5 analisis gratis kamu telah digunakan" in msg6


def test_06_concurrent_analysis_requests_preserve_quota_invariants(temp_web_db, monkeypatch):
    """
    Executes 10 concurrent requests from a new user with 5 free quotas.
    Verifies exactly 5 succeed, 5 fail, and total records == 5 with zero corruption.
    """
    monkeypatch.setattr("web.services.DB_PATH", temp_web_db)
    user_id = "user_concurrent_test"

    results = []

    def worker(req_num):
        req_id = f"concurrent_req_{req_num}"
        ok, msg = UsageEntitlementService.consume_analysis(user_id, req_id)
        results.append((ok, msg))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    successes = sum(1 for ok, _ in results if ok)
    failures = sum(1 for ok, _ in results if not ok)

    # Invariant: exactly 5 can succeed (max free quota is 5)
    assert successes == 5
    assert failures == 5

    # Check database count
    conn = sqlite3.connect(temp_web_db)
    cnt = conn.execute("SELECT COUNT(*) FROM usage_entitlement_records WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    assert cnt == 5


def test_07_api_foundation_client_status_codes(temp_web_db, monkeypatch):
    """FastAPI TestClient verifies proper status codes and error masking."""
    monkeypatch.setattr("web.services.DB_PATH", temp_web_db)
    client = TestClient(app)

    # Meta languages should work
    res_meta = client.get("/api/v1/meta/languages")
    assert res_meta.status_code == 200
    assert "languages" in res_meta.json()

    # Context query
    res_ctx = client.get("/api/v1/context?user_id=test_api_user")
    assert res_ctx.status_code == 200


def test_08_webhook_rejects_invalid_signature_and_simulator_flags(temp_web_db):
    """POLYA-WEB-04: Test simulator bypass is strictly closed."""
    from services import PaymentService

    checkout = PaymentService.create_checkout("victim_user")
    order_id = checkout["order_id"]

    # 1. Attacker tries simulator flag with bogus signature
    payload = {
        "order_id": order_id,
        "status_code": "200",
        "gross_amount": "99000.00",
        "signature_key": "bad_bogus_signature_hash",
        "transaction_status": "settlement",
        "is_simulator": True,
        "test_mode": True,
        "is_simulation": True
    }
    success, msg = PaymentService.process_webhook(payload, server_key="test_secret_key_123")
    assert success is False
    assert "Invalid SHA-512" in msg


def test_09_webhook_valid_signature_settles_and_activates_entitlement(temp_web_db):
    """POLYA-WEB-04: Valid Midtrans SHA-512 signature settles transaction."""
    from services import PaymentService, EntitlementService, EntitlementState
    import hashlib

    secret = "midtrans_test_secret_key_456"
    checkout = PaymentService.create_checkout("paying_user")
    order_id = checkout["order_id"]
    status_code = "200"
    gross_amount = "99000.00"

    raw = f"{order_id}{status_code}{gross_amount}{secret}"
    valid_sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": valid_sig,
        "transaction_status": "settlement"
    }
    success, msg = PaymentService.process_webhook(payload, server_key=secret)
    assert success is True

    # Entitlement must be PREMIUM_ACTIVE
    status = EntitlementService.get_entitlement("paying_user")
    assert status["state"] == EntitlementState.PREMIUM_ACTIVE.value


def test_10_webhook_rejects_gross_amount_or_order_tampering(temp_web_db):
    """POLYA-WEB-04: Tampering with amount or order fails."""
    from services import PaymentService
    import hashlib

    secret = "midtrans_test_secret_key_456"
    checkout = PaymentService.create_checkout("tamper_user")
    order_id = checkout["order_id"]
    status_code = "200"

    # Attacker tries to pay Rp1000 instead of Rp99000
    tampered_amount = "1000.00"
    raw = f"{order_id}{status_code}{tampered_amount}{secret}"
    sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": tampered_amount,
        "signature_key": sig,
        "transaction_status": "settlement"
    }
    success, msg = PaymentService.process_webhook(payload, server_key=secret)
    assert success is False
    assert "Gross amount mismatch" in msg


def test_11_webhook_non_settlement_does_not_activate_premium(temp_web_db):
    """POLYA-WEB-04: Pending, deny, or expire does not grant premium."""
    from services import PaymentService, EntitlementService, EntitlementState
    import hashlib

    secret = "midtrans_test_secret_key_456"
    checkout = PaymentService.create_checkout("pending_user")
    order_id = checkout["order_id"]
    status_code = "201"
    gross_amount = "99000"

    raw = f"{order_id}{status_code}{gross_amount}{secret}"
    sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": sig,
        "transaction_status": "pending"
    }
    success, msg = PaymentService.process_webhook(payload, server_key=secret)
    assert success is True

    status = EntitlementService.get_entitlement("pending_user")
    assert status["state"] == EntitlementState.PAYMENT_PENDING.value
    assert status["state"] == EntitlementState.PAYMENT_PENDING.value


def test_12_webhook_idempotency_and_out_of_order_protection(temp_web_db):
    """POLYA-WEB-04: Replay does not duplicate and out-of-order pending cannot downgrade settled."""
    from services import PaymentService, EntitlementService, EntitlementState
    import hashlib

    secret = "midtrans_test_secret_key_456"
    checkout = PaymentService.create_checkout("replay_user")
    order_id = checkout["order_id"]
    status_code = "200"
    gross_amount = "99000"

    raw = f"{order_id}{status_code}{gross_amount}{secret}"
    sig = hashlib.sha512(raw.encode("utf-8")).hexdigest()

    payload_settle = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": sig,
        "transaction_status": "settlement"
    }
    # First settle
    success, msg = PaymentService.process_webhook(payload_settle, server_key=secret)
    assert success is True

    # Replay settle (idempotent)
    success, msg = PaymentService.process_webhook(payload_settle, server_key=secret)
    assert success is True
    assert EntitlementService.get_entitlement("replay_user")["state"] == EntitlementState.PREMIUM_ACTIVE.value

    # Delayed out-of-order "pending" arrives
    raw_pending = f"{order_id}201{gross_amount}{secret}"
    sig_pending = hashlib.sha512(raw_pending.encode("utf-8")).hexdigest()
    payload_pending = {
        "order_id": order_id,
        "status_code": "201",
        "gross_amount": gross_amount,
        "signature_key": sig_pending,
        "transaction_status": "pending"
    }
    success, msg = PaymentService.process_webhook(payload_pending, server_key=secret)
    assert success is True
    # Invariant: state remains PREMIUM_ACTIVE
    assert EntitlementService.get_entitlement("replay_user")["state"] == EntitlementState.PREMIUM_ACTIVE.value


def test_13_webhook_missing_server_key_fails_closed(temp_web_db):
    """POLYA-WEB-04: Unconfigured server key fails closed."""
    from services import PaymentService

    payload = {
        "order_id": "POLYA-ANY",
        "status_code": "200",
        "gross_amount": "99000",
        "signature_key": "any",
        "transaction_status": "settlement"
    }
    # Pass empty server_key explicitly
    success, msg = PaymentService.process_webhook(payload, server_key="")
    assert success is False
    assert "Invalid SHA-512" in msg


def test_14_session_token_cryptographic_verification(temp_web_db, monkeypatch):
    """POLYA-WEB-05A: SessionService issues and strictly verifies HMAC-SHA256 tokens."""
    from services import SessionService

    test_secret = "polya_test_secret_key_secure_123"
    monkeypatch.setenv("POLYA_AUTH_SECRET", test_secret)

    # 1. Valid issuance and verification
    token = SessionService.create_token("user_alice", role="apologist")
    claims = SessionService.verify_token(token)
    assert claims is not None
    assert claims["sub"] == "user_alice"
    assert claims["role"] == "apologist"
    assert claims["exp"] > claims["iat"]

    # 2. Tampered signature rejected
    tampered_sig = token[:-4] + "XXXX"
    assert SessionService.verify_token(tampered_sig) is None

    # 3. Payload tampering rejected
    parts = token.split(".")
    import base64, json
    header_b64, payload_b64, sig_b64 = parts
    pad = 4 - (len(payload_b64) % 4)
    payload_data = json.loads(base64.urlsafe_b64decode(payload_b64 + ("=" * (pad if pad != 4 else 0))))
    payload_data["sub"] = "user_bob"  # Attack: change identity
    tampered_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    tampered_token = f"{header_b64}.{tampered_payload_b64}.{sig_b64}"
    assert SessionService.verify_token(tampered_token) is None

    # 4. Expired token rejected
    payload_data["sub"] = "user_alice"
    payload_data["exp"] = claims["iat"] - 100  # in the past
    exp_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    unsigned = f"{header_b64}.{exp_payload_b64}"
    import hmac, hashlib
    valid_sig_expired = base64.urlsafe_b64encode(
        hmac.new(test_secret.encode(), unsigned.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    expired_token = f"{unsigned}.{valid_sig_expired}"
    assert SessionService.verify_token(expired_token) is None


def test_15_unauthenticated_request_rejected_on_private_endpoints(temp_web_db):
    """POLYA-WEB-05A: Missing Authorization header results in HTTP 401."""
    client = TestClient(app)

    # Billing
    res_billing = client.get("/api/v1/account/billing")
    assert res_billing.status_code == 401
    assert "missing" in res_billing.json()["detail"].lower()

    # Wallet
    res_wallet = client.get("/api/user/usr_test/wallet")
    assert res_wallet.status_code == 401

    # Profile Update
    res_profile = client.post("/api/profile/update", json={"name": "New Name"})
    assert res_profile.status_code == 401

    # Donation
    res_donate = client.post("/api/donate", json={
        "donor_user_id": "usr_test",
        "recipient_user_id": "usr_rec",
        "gross_amount": 50000,
        "payment_method": "QRIS"
    })
    assert res_donate.status_code == 401


def test_16_idor_cross_user_billing_and_wallet_protection(temp_web_db, monkeypatch):
    """POLYA-WEB-05A: User A cannot read or mutate User B's billing, wallet, or profile."""
    from services import SessionService
    test_secret = "polya_test_secret_key_secure_123"
    monkeypatch.setenv("POLYA_AUTH_SECRET", test_secret)

    client = TestClient(app)
    token_a = SessionService.create_token("user_alice")
    token_b = SessionService.create_token("user_bob")

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 1. Billing IDOR: User A querying User B's billing records -> 403 Forbidden
    res = client.get("/api/v1/account/billing?user_id=user_bob", headers=headers_a)
    assert res.status_code == 403
    assert "cannot access another user" in res.json()["detail"].lower()

    # User A querying own billing -> 200 OK
    res_own = client.get("/api/v1/account/billing?user_id=user_alice", headers=headers_a)
    assert res_own.status_code == 200
    assert res_own.json()["user_id"] == "user_alice"

    # User A omitting user_id param -> defaults cleanly to User A
    res_default = client.get("/api/v1/account/billing", headers=headers_a)
    assert res_default.status_code == 200
    assert res_default.json()["user_id"] == "user_alice"

    # 2. Wallet IDOR: User A accessing User B's wallet -> 403 Forbidden
    res_wallet = client.get("/api/user/user_bob/wallet", headers=headers_a)
    assert res_wallet.status_code == 403
    assert "cannot access another user" in res_wallet.json()["detail"].lower()

    # 3. Profile IDOR: User A mutating User B's profile -> 403 Forbidden
    res_prof = client.post(
        "/api/profile/update",
        json={"user_id": "user_bob", "name": "Hacked Name"},
        headers=headers_a
    )
    assert res_prof.status_code == 403

    # 4. Donation Forgery: User A donating on behalf of User B -> 403 Forbidden
    res_don = client.post(
        "/api/donate",
        json={
            "donor_user_id": "user_bob",
            "recipient_user_id": "user_alice",
            "gross_amount": 50000,
            "payment_method": "QRIS"
        },
        headers=headers_a
    )
    assert res_don.status_code == 403


def test_17_identity_assertion_remediation_and_gates(temp_web_db, monkeypatch):
    """POLYA-WEB-06A: Verify identity assertion remediation and security gates."""
    from services import SessionService, GoogleAuthVerifier
    client = TestClient(app)

    # 1. Secret missing fails closed
    monkeypatch.delenv("POLYA_AUTH_SECRET", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        SessionService.create_token("any_user")
    assert "not configured" in str(exc_info.value).lower()

    # Restore secret for remaining assertions
    test_secret = "polya_test_secure_secret_06a_987654321"
    monkeypatch.setenv("POLYA_AUTH_SECRET", test_secret)

    # 2. Reject raw email assertion without credential
    res_raw = client.post(
        "/api/v1/auth/session",
        json={"email": "victim@polya.org", "name": "Victim User"}
    )
    assert res_raw.status_code == 401
    assert "credential required" in res_raw.json()["detail"].lower()

    # 3. Reject is_mock: true in production environment
    monkeypatch.setenv("POLYA_ENV", "production")
    res_prod_mock = client.post(
        "/api/v1/auth/session",
        json={
            "credential": "mock-google-token:victim@polya.org:sub123:Victim",
            "email": "victim@polya.org",
            "is_mock": True
        }
    )
    assert res_prod_mock.status_code in [401, 403]

    # Also verify GoogleAuthVerifier directly rejects mock in prod
    assert GoogleAuthVerifier.verify_credential("mock-google-token:victim@polya.org:sub123:Victim") is None

    # 4. Allow controlled mock token only in dev/test environment
    monkeypatch.setenv("POLYA_ENV", "development")
    res_dev_mock = client.post(
        "/api/v1/auth/session",
        json={
            "credential": "mock-google-token:scholar@polya.org:sub_999:Scholar",
            "is_mock": True
        }
    )
    assert res_dev_mock.status_code == 200
    data_dev = res_dev_mock.json()
    assert data_dev["success"] is True
    assert "usr_" in data_dev["user"]["user_id"]
    assert data_dev["user"]["email"] == "scholar@polya.org"
    assert data_dev["user"]["role"] == "visitor"  # Server-dictated role policy

    # Verify session token is valid and verifiable
    claims = SessionService.verify_token(data_dev["session_token"])
    assert claims is not None
    assert claims["sub"] == data_dev["user"]["user_id"]
    assert claims["role"] == "visitor"

    # 5. /api/auth/google rejects invalid / unverified credential
    res_g_invalid = client.post(
        "/api/auth/google",
        json={"credential": "invalid_jwt_format_abc", "email": "any@gmail.com"}
    )
    assert res_g_invalid.status_code == 401
    assert "invalid or missing id token" in res_g_invalid.json()["detail"].lower()

    # 6. /api/auth/google succeeds with valid mock credential in dev mode
    res_g_valid = client.post(
        "/api/auth/google",
        json={"credential": "mock-google-token:google_user@gmail.com:google_sub_888:Google Tester"}
    )
    assert res_g_valid.status_code == 200
    data_g = res_g_valid.json()
    assert data_g["status"] == "ok"
    assert "usr_" in data_g["user"]["user_id"]
    assert data_g["user"]["email"] == "google_user@gmail.com"
    assert data_g["user"]["role"] == "visitor"

    # Invariant: Tokens issued can authenticate to own billing
    auth_header = {"Authorization": f"Bearer {data_g['session_token']}"}
    res_billing = client.get(f"/api/v1/account/billing?user_id={data_g['user']['user_id']}", headers=auth_header)
    assert res_billing.status_code == 200
    assert res_billing.json()["user_id"] == data_g["user"]["user_id"]


def test_18_oauth_validation_hardening_and_adversarial_gates(temp_web_db, monkeypatch):
    """POLYA-WEB-06C: Hardened OAuth validation, allowlist gating, and adversarial edge cases."""
    from services import GoogleAuthVerifier, SessionService
    import requests
    client = TestClient(app)

    test_secret = "polya_test_secure_secret_06c_abcdef123456"
    monkeypatch.setenv("POLYA_AUTH_SECRET", test_secret)

    # 1. Environment allowlist: empty, typo, unknown environments fail-closed
    for bad_env in ["", "   ", "prduction", "stage", "preview", "prod"]:
        monkeypatch.setenv("POLYA_ENV", bad_env)
        assert GoogleAuthVerifier.is_mock_allowed() is False
        assert GoogleAuthVerifier.verify_credential("mock-google-token:test@polya.org:sub1:User") is None
        res_bad = client.post(
            "/api/v1/auth/session",
            json={"credential": "mock-google-token:test@polya.org:sub1:User", "is_mock": True}
        )
        assert res_bad.status_code in [401, 403]

    # Explicit allowed environments
    for good_env in ["test", "development", "local"]:
        monkeypatch.setenv("POLYA_ENV", good_env)
        assert GoogleAuthVerifier.is_mock_allowed() is True

    # 2. Real Google OAuth validation edge cases via mocked response
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self._json = json_data
            self.status_code = status_code
        def json(self):
            return self._json

    # Edge case 2a: email_verified is False -> Rejected
    def mock_get_unverified(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_1001",
            "email": "unverified@gmail.com",
            "email_verified": "false",
            "iss": "accounts.google.com",
            "aud": "valid-client-id"
        })
    monkeypatch.setattr(requests, "get", mock_get_unverified)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "valid-client-id")
    assert GoogleAuthVerifier.verify_credential("dummy_jwt_credential") is None

    # Edge case 2b: Untrusted issuer -> Rejected
    def mock_get_bad_iss(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_1001",
            "email": "attacker@gmail.com",
            "email_verified": "true",
            "iss": "https://evil-issuer.com",
            "aud": "valid-client-id"
        })
    monkeypatch.setattr(requests, "get", mock_get_bad_iss)
    assert GoogleAuthVerifier.verify_credential("dummy_jwt_credential") is None

    # Edge case 2c: Audience mismatch -> Rejected with sanitized log
    def mock_get_bad_aud(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_1001",
            "email": "valid@gmail.com",
            "email_verified": "true",
            "iss": "https://accounts.google.com",
            "aud": "different-client-id"
        })
    monkeypatch.setattr(requests, "get", mock_get_bad_aud)
    assert GoogleAuthVerifier.verify_credential("dummy_jwt_credential") is None

    # Edge case 2d: Provider network timeout / ConnectionError -> Fail-closed cleanly
    def mock_get_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Connection timed out to Google OAuth2 tokeninfo")
    monkeypatch.setattr(requests, "get", mock_get_timeout)
    assert GoogleAuthVerifier.verify_credential("dummy_jwt_credential") is None

    # Edge case 2e: Legitimate verified Google Token -> Succeeded
    def mock_get_valid(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_1001",
            "email": "scholar@gmail.com",
            "email_verified": True,
            "iss": "https://accounts.google.com",
            "aud": "valid-client-id",
            "name": "Dr. Scholar",
            "picture": "https://lh3.googleusercontent.com/avatar1"
        })
    monkeypatch.setattr(requests, "get", mock_get_valid)
    res_verified = GoogleAuthVerifier.verify_credential("dummy_jwt_credential")
    assert res_verified is not None
    assert res_verified["sub"] == "google_sub_1001"
    assert res_verified["email"] == "scholar@gmail.com"

    # 3. Stable identity anchor: user changing email in Google keeps the same user_id & wallet
    # Initial login with email A
    res_auth1 = client.post("/api/auth/google", json={"credential": "dummy_jwt_credential"})
    assert res_auth1.status_code == 200
    user_id_1 = res_auth1.json()["user"]["user_id"]

    # Same user logs in later after changing primary email in Google account to email B
    def mock_get_changed_email(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_1001",  # Identical permanent provider subject
            "email": "scholar.new.email@gmail.com",
            "email_verified": True,
            "iss": "https://accounts.google.com",
            "aud": "valid-client-id",
            "name": "Dr. Scholar"
        })
    monkeypatch.setattr(requests, "get", mock_get_changed_email)
    res_auth2 = client.post("/api/auth/google", json={"credential": "dummy_jwt_credential"})
    assert res_auth2.status_code == 200
    user_id_2 = res_auth2.json()["user"]["user_id"]

    # Invariant: user_id is anchored strictly to provider subject 'google_sub_1001'
    assert user_id_1 == user_id_2
    assert res_auth2.json()["user"]["email"] == "scholar.new.email@gmail.com"


def test_19_mandatory_google_client_id_in_production(temp_web_db, monkeypatch):
    """POLYA-WEB-06E: Verify mandatory GOOGLE_CLIENT_ID gate in production."""
    from services import GoogleAuthVerifier
    import requests

    class MockResponse:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code

        def json(self):
            return self._data

    def mock_get(*args, **kwargs):
        return MockResponse({
            "sub": "google_sub_2026",
            "email": "user@gmail.com",
            "email_verified": True,
            "iss": "https://accounts.google.com",
            "aud": "expected-prod-client-id.apps.googleusercontent.com",
            "name": "Prod User"
        })

    monkeypatch.setattr(requests, "get", mock_get)

    # 1. In production, missing GOOGLE_CLIENT_ID fails closed
    monkeypatch.setenv("POLYA_ENV", "production")
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    assert GoogleAuthVerifier.verify_credential("any_token") is None

    # 2. In production, empty GOOGLE_CLIENT_ID fails closed
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "   ")
    assert GoogleAuthVerifier.verify_credential("any_token") is None

    # 3. In production, audience mismatch fails closed
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "different-client-id.apps.googleusercontent.com")
    assert GoogleAuthVerifier.verify_credential("any_token") is None

    # 4. In production, exact matching GOOGLE_CLIENT_ID succeeds
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "expected-prod-client-id.apps.googleusercontent.com")
    verified = GoogleAuthVerifier.verify_credential("any_token")
    assert verified is not None
    assert verified["sub"] == "google_sub_2026"
    assert verified["email"] == "user@gmail.com"


def test_20_staging_google_auth_and_midtrans_idempotency(temp_web_db, monkeypatch):
    """POLYA-WEB-09C: Regression suite for Google Sign-In & Midtrans Sandbox staging gates."""
    from services import GoogleAuthVerifier, PaymentService, EntitlementService, EntitlementState, get_db
    import requests
    import hashlib
    from datetime import datetime, timezone

    # --- 1. GOOGLE SIGN-IN STAGING GATES ---
    staging_client_id = "953116755250-p8n0eqgrsb84k7tfakptmb3nuccjn6vr.apps.googleusercontent.com"
    monkeypatch.setenv("POLYA_ENV", "staging")

    # A. Mock tokens strictly rejected in staging
    mock_token = "mock-google-token:test@polya.org:sub_123:Tester"
    assert GoogleAuthVerifier.is_mock_allowed() is False
    assert GoogleAuthVerifier.verify_credential(mock_token) is None

    # B. Missing or blank GOOGLE_CLIENT_ID fails closed in staging
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "   ")
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None

    # Setup tokeninfo response mock
    mock_token_payload = {
        "sub": "staging_google_sub_777",
        "email": "apologist@staging.apologets.com",
        "email_verified": True,
        "iss": "https://accounts.google.com",
        "aud": staging_client_id,
        "name": "Staging Scholar",
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600
    }

    class MockResp:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code
        def json(self):
            return self._data

    current_mock_payload = dict(mock_token_payload)
    def mock_get(*args, **kwargs):
        return MockResp(current_mock_payload)

    monkeypatch.setattr(requests, "get", mock_get)

    # C. Audience mismatch in staging fails closed
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "wrong-staging-client-id.apps.googleusercontent.com")
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None

    # D. Correct audience in staging succeeds
    monkeypatch.setenv("GOOGLE_CLIENT_ID", staging_client_id)
    verified = GoogleAuthVerifier.verify_credential("dummy_token")
    assert verified is not None
    assert verified["sub"] == "staging_google_sub_777"
    assert verified["email"] == "apologist@staging.apologets.com"

    # E. Invalid issuer rejected
    current_mock_payload["iss"] = "https://malicious-issuer.com"
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None
    current_mock_payload["iss"] = "https://accounts.google.com"

    # F. Unverified email rejected
    current_mock_payload["email_verified"] = False
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None
    current_mock_payload["email_verified"] = True

    # G. Expired token rejected
    current_mock_payload["exp"] = int(datetime.now(timezone.utc).timestamp()) - 100
    assert GoogleAuthVerifier.verify_credential("dummy_token") is None
    current_mock_payload["exp"] = int(datetime.now(timezone.utc).timestamp()) + 3600

    # --- 2. MIDTRANS SANDBOX IDEMPOTENCY & DOWNGRADE PROTECTION ---
    secret_key = "SB-Mid-server-test-sandbox-secret"
    checkout = PaymentService.create_checkout("staging_test_user")
    order_id = checkout["order_id"]
    status_code = "200"
    gross_amount = "99000"

    raw_sig = f"{order_id}{status_code}{gross_amount}{secret_key}"
    valid_sig = hashlib.sha512(raw_sig.encode("utf-8")).hexdigest()

    # A. Wrong signature rejected
    bad_payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": "wrong_hash_512",
        "transaction_status": "settlement"
    }
    success, msg = PaymentService.process_webhook(bad_payload, server_key=secret_key)
    assert success is False
    assert "Invalid SHA-512 signature key" in msg

    # B. Gross amount mismatch rejected
    tampered_amount_payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": "50000",
        "signature_key": hashlib.sha512(f"{order_id}{status_code}50000{secret_key}".encode()).hexdigest(),
        "transaction_status": "settlement"
    }
    success, msg = PaymentService.process_webhook(tampered_amount_payload, server_key=secret_key)
    assert success is False
    assert "Gross amount mismatch" in msg

    # C. Valid settlement webhook succeeds and activates entitlement
    valid_payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": valid_sig,
        "transaction_status": "settlement"
    }
    success, msg = PaymentService.process_webhook(valid_payload, server_key=secret_key)
    assert success is True
    ent = EntitlementService.get_entitlement("staging_test_user")
    assert ent["state"] == EntitlementState.PREMIUM_ACTIVE.value
    initial_activated_at = ent["activated_at"]
    assert initial_activated_at is not None

    # D. Duplicate settlement webhook is idempotent and preserves initial activated_at
    success, msg = PaymentService.process_webhook(valid_payload, server_key=secret_key)
    assert success is True
    assert "already settled" in msg
    ent_after_dup = EntitlementService.get_entitlement("staging_test_user")
    assert ent_after_dup["state"] == EntitlementState.PREMIUM_ACTIVE.value
    assert ent_after_dup["activated_at"] == initial_activated_at

    # E. Status downgrade attempt after settlement is ignored
    pending_sig = hashlib.sha512(f"{order_id}201{gross_amount}{secret_key}".encode()).hexdigest()
    pending_payload = {
        "order_id": order_id,
        "status_code": "201",
        "gross_amount": gross_amount,
        "signature_key": pending_sig,
        "transaction_status": "pending"
    }
    success, msg = PaymentService.process_webhook(pending_payload, server_key=secret_key)
    assert success is True
    assert "downgrade ignored" in msg
    assert EntitlementService.get_entitlement("staging_test_user")["state"] == EntitlementState.PREMIUM_ACTIVE.value

    # F. Out-of-sync healing: if entitlement was somehow lost, re-process restores it
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_entitlements SET state = 'FREE_TIER' WHERE user_id = 'staging_test_user'")
    conn.commit()
    conn.close()

    success, msg = PaymentService.process_webhook(valid_payload, server_key=secret_key)
    assert success is True
    healed_ent = EntitlementService.get_entitlement("staging_test_user")
    assert healed_ent["state"] == EntitlementState.PREMIUM_ACTIVE.value



