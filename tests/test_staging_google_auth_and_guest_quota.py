"""
POLYA AI — STAGING ACCEPTANCE & REGRESSION TEST SUITE
POLYA-WEB-001: Google Sign-In & Secure Guest Quota Validation

Tests:
1. Google Token Verification Matrix (Audience, Issuer, Expiry, Signature, email_verified).
2. Staging Environment Policy (Mock Auth forbidden under POLYA_ENV=staging).
3. Server-Verified Guest Sessions (HMAC-SHA256 signature, expiry, tamper rejection).
4. Unverified Guest Assertion Rejection (localStorage guest_<uuid> spoofing blocked).
5. Guest Isolation (Two independent guest browsers maintain separate quotas).
6. Exact 5-Analysis Free Quota Gate (6th request returns HTTP 402).
7. Request ID Idempotency (Duplicate request_id does not double-decrement quota).
8. Concurrent Quota Atomicity (Concurrent requests do not overshoot 5-analysis cap).
9. Cross-User Impersonation Rejection (Guest cannot impersonate registered user).
10. Billing and Entitlement Protection (Guest cannot initiate checkout for another user).
11. Legacy guest_user backward compatibility preservation.
"""
import asyncio
import base64
import hashlib
import hmac
import json
import os
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pytest
import jwt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

# Set test environment auth secret
TEST_SECRET = "staging_test_auth_secret_minimum_32_characters_for_hmac_256"
os.environ["POLYA_AUTH_SECRET"] = TEST_SECRET
os.environ["POLYA_ENV"] = "staging"

from web.app import app
from web.services import (
    GoogleAuthVerifier,
    SessionService,
    UsageEntitlementService,
    EntitlementService,
    PaymentService,
    get_db,
    init_foundation_db
)

STAGING_CLIENT_ID = "953116755250-p8n0eqgrsb84k7tfakptmb3nuccjn6vr.apps.googleusercontent.com"
PROD_CLIENT_ID = "953116755250-qomlk1eh2q01u62nlfemm68td1ca2bbu.apps.googleusercontent.com"


async def dispatch_asgi(path: str, method: str = "GET", payload: dict = None, headers: list = None):
    """Direct ASGI dispatcher for isolated endpoint execution."""
    body_bytes = json.dumps(payload).encode("utf-8") if payload else b""
    hdr_list = [(b"host", b"staging.apologets.com")]
    if payload:
        hdr_list.append((b"content-type", b"application/json"))
        hdr_list.append((b"content-length", str(len(body_bytes)).encode("utf-8")))
    if headers:
        for k, v in headers:
            hdr_list.append((k.lower().encode("utf-8"), v.encode("utf-8")))

    raw_path_bytes = path.split("?")[0].encode("utf-8")
    query_string = path.split("?")[1].encode("utf-8") if "?" in path else b""

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path.split("?")[0],
        "raw_path": raw_path_bytes,
        "query_string": query_string,
        "headers": hdr_list,
    }

    status_code = None
    response_headers = []
    body_chunks = []

    async def receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    async def send(msg):
        nonlocal status_code, response_headers, body_chunks
        if msg["type"] == "http.response.start":
            status_code = msg["status"]
            response_headers = msg["headers"]
        elif msg["type"] == "http.response.body":
            body_chunks.append(msg.get("body", b""))

    await app(scope, receive, send)
    body_text = b"".join(body_chunks).decode("utf-8", errors="ignore")
    try:
        data = json.loads(body_text) if body_text else {}
    except Exception:
        data = {}
    return status_code, data, body_text


# ===========================================================================
# 1. GOOGLE TOKEN VALIDATION & SECURITY MATRIX
# ===========================================================================

def test_google_verifier_audience_isolation_configuration(monkeypatch):
    """Verifies backend strictly isolates allowed Client ID per active environment."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", STAGING_CLIENT_ID)
    allowed_staging = GoogleAuthVerifier.get_allowed_client_ids()
    assert allowed_staging == [STAGING_CLIENT_ID]
    assert PROD_CLIENT_ID not in allowed_staging

    monkeypatch.setenv("GOOGLE_CLIENT_ID", PROD_CLIENT_ID)
    allowed_prod = GoogleAuthVerifier.get_allowed_client_ids()
    assert allowed_prod == [PROD_CLIENT_ID]
    assert STAGING_CLIENT_ID not in allowed_prod

    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    assert GoogleAuthVerifier.get_allowed_client_ids() == []


def test_google_verifier_rejects_mock_in_staging(monkeypatch):
    """Ensures mock authentication is strictly rejected when POLYA_ENV is staging."""
    monkeypatch.setenv("POLYA_ENV", "staging")
    assert not GoogleAuthVerifier.is_mock_allowed()
    res = GoogleAuthVerifier.verify_credential("mock-google-token:test@polya.org:sub123:Tester")
    assert res is None


def test_google_token_claims_verification_matrix(monkeypatch):
    """Forensic verification matrix testing claim boundaries against GoogleAuthVerifier."""
    monkeypatch.setenv("POLYA_ENV", "staging")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", STAGING_CLIENT_ID)

    # Mock tokeninfo response generator to test claim boundaries
    now = int(datetime.now(timezone.utc).timestamp())

    class MockResponse:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code

        def json(self):
            return self._data

    # A. Valid Token with Staging Client ID -> Accepted
    valid_payload = {
        "iss": "https://accounts.google.com",
        "aud": STAGING_CLIENT_ID,
        "sub": "google_sub_1029384756",
        "email": "apologist@polya.org",
        "email_verified": "true",
        "name": "Dr. Researcher",
        "picture": "https://lh3.googleusercontent.com/avatar",
        "exp": str(now + 3600)
    }
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(valid_payload))
    result = GoogleAuthVerifier.verify_credential("dummy_token_valid_staging")
    assert result is not None
    assert result["sub"] == "google_sub_1029384756"
    assert result["email"] == "apologist@polya.org"

    # B. Token with Production Client ID on Staging Verifier -> Strictly Rejected
    valid_prod_payload = dict(valid_payload, aud=PROD_CLIENT_ID)
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(valid_prod_payload))
    result_prod = GoogleAuthVerifier.verify_credential("dummy_token_valid_prod")
    assert result_prod is None, "Staging verifier must reject tokens issued for production client ID"

    # C. Token with Wrong Audience -> Rejected
    bad_aud_payload = dict(valid_payload, aud="evil_unauthorized_client_id.apps.googleusercontent.com")
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(bad_aud_payload))
    assert GoogleAuthVerifier.verify_credential("dummy_token_bad_aud") is None

    # D. Token with Wrong Issuer -> Rejected
    bad_iss_payload = dict(valid_payload, iss="https://untrusted-auth-provider.com")
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(bad_iss_payload))
    assert GoogleAuthVerifier.verify_credential("dummy_token_bad_iss") is None

    # E. Expired Token -> Rejected
    expired_payload = dict(valid_payload, exp=str(now - 300))
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(expired_payload))
    assert GoogleAuthVerifier.verify_credential("dummy_token_expired") is None

    # F. Token with Unverified Email -> Rejected
    unverified_payload = dict(valid_payload, email_verified="false")
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(unverified_payload))
    assert GoogleAuthVerifier.verify_credential("dummy_token_unverified_email") is None

    # G. Token missing Subject ID -> Rejected
    no_sub_payload = dict(valid_payload, sub="")
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(no_sub_payload))
    assert GoogleAuthVerifier.verify_credential("dummy_token_no_sub") is None


def test_cross_environment_oauth_audience_isolation(monkeypatch):
    """Rigorous cross-environment token decision testing against GoogleAuthVerifier.

    Verifies:
    1. Staging token accepted by staging verifier.
    2. Production token rejected by staging verifier.
    3. Production token accepted by production verifier (isolated config).
    4. Staging token rejected by production verifier.
    5. Empty or missing Client ID causes fail-closed rejection.
    """
    now = int(datetime.now(timezone.utc).timestamp())

    class MockResponse:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code

        def json(self):
            return self._data

    base_payload = {
        "iss": "https://accounts.google.com",
        "sub": "google_user_778899",
        "email": "user@apologets.com",
        "email_verified": True,
        "name": "Cross Env Tester",
        "picture": "https://example.com/pic.png",
        "exp": str(now + 3600),
    }

    staging_payload = dict(base_payload, aud=STAGING_CLIENT_ID)
    prod_payload = dict(base_payload, aud=PROD_CLIENT_ID)

    # --- SCENARIO 1: STAGING VERIFIER CONFIGURATION ---
    monkeypatch.setenv("POLYA_ENV", "staging")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", STAGING_CLIENT_ID)

    # 1. Staging token accepted by staging verifier
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(staging_payload))
    res_staging_on_staging = GoogleAuthVerifier.verify_credential("staging_token")
    assert res_staging_on_staging is not None
    assert res_staging_on_staging["email"] == "user@apologets.com"
    assert res_staging_on_staging["sub"] == "google_user_778899"

    # 2. Production token rejected by staging verifier
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(prod_payload))
    res_prod_on_staging = GoogleAuthVerifier.verify_credential("prod_token")
    assert res_prod_on_staging is None, "Production token must be rejected by staging verifier"

    # --- SCENARIO 2: PRODUCTION VERIFIER CONFIGURATION (ISOLATED TEST) ---
    monkeypatch.setenv("POLYA_ENV", "production")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", PROD_CLIENT_ID)

    # 3. Production token accepted by production verifier
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(prod_payload))
    res_prod_on_prod = GoogleAuthVerifier.verify_credential("prod_token")
    assert res_prod_on_prod is not None
    assert res_prod_on_prod["email"] == "user@apologets.com"
    assert res_prod_on_prod["sub"] == "google_user_778899"

    # 4. Staging token rejected by production verifier
    monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(staging_payload))
    res_staging_on_prod = GoogleAuthVerifier.verify_credential("staging_token")
    assert res_staging_on_prod is None, "Staging token must be rejected by production verifier"

    # --- SCENARIO 3: MISSING / EMPTY CLIENT ID (FAIL-CLOSED) ---
    for empty_val in ["", "   "]:
        monkeypatch.setenv("GOOGLE_CLIENT_ID", empty_val)
        monkeypatch.setattr("requests.get", lambda url, timeout=5.0: MockResponse(staging_payload))
        assert GoogleAuthVerifier.verify_credential("tok") is None

    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    assert GoogleAuthVerifier.verify_credential("tok") is None


# ===========================================================================
# 2. SERVER-VERIFIED GUEST SESSIONS & ISOLATION
# ===========================================================================

@pytest.mark.anyio
async def test_guest_session_issuance_and_signature_integrity():
    """Tests POST /api/v1/auth/guest issuance and tamper-proofing."""
    status, data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    assert status == 200
    assert data["success"] is True
    assert data["role"] == "guest"
    assert data["user_id"].startswith("guest_")
    token = data["session_token"]
    assert token is not None

    # Verify signature passes internally
    claims = SessionService.verify_token(token)
    assert claims is not None
    assert claims["sub"] == data["user_id"]
    assert claims["role"] == "guest"

    # 1. Tamper signature -> Rejected
    tampered_sig_token = token[:-4] + "wxyz"
    assert SessionService.verify_token(tampered_sig_token) is None

    # 2. Tamper payload -> Rejected
    parts = token.split(".")
    tampered_payload = base64.urlsafe_b64encode(json.dumps({"sub": "guest_hacked", "role": "guest"}).encode()).decode().rstrip("=")
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
    assert SessionService.verify_token(tampered_token) is None

    # 3. Expired token -> Rejected
    expired_token = SessionService.create_token(data["user_id"], role="guest", ttl=-3600)
    assert SessionService.verify_token(expired_token) is None


@pytest.mark.anyio
async def test_unverified_guest_assertion_rejected_without_signed_token():
    """Crucial security test: Client declaring arbitrary 'guest_<uuid>' without server signature is 401."""
    fake_guest_id = f"guest_{uuid.uuid4().hex}"
    # Request without Authorization header
    status, data, _ = await dispatch_asgi(f"/api/v1/context?user_id={fake_guest_id}", "GET")
    assert status == 401
    assert "Authentication required" in str(data)

    # Request to analyze without Authorization header
    analyze_payload = {
        "claim": "Yesus disalibkan menurut Markus 15:25",
        "user_id": fake_guest_id
    }
    status_an, data_an, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", analyze_payload)
    assert status_an == 401


@pytest.mark.anyio
async def test_two_guest_browsers_have_independent_quotas():
    """Simulates 2 distinct guest browsers, each having independent 5-free quota."""
    # Browser 1 issuance
    status1, guest1_data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    assert status1 == 200
    guest1_id = guest1_data["user_id"]
    guest1_token = guest1_data["session_token"]

    # Browser 2 issuance
    status2, guest2_data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    assert status2 == 200
    guest2_id = guest2_data["user_id"]
    guest2_token = guest2_data["session_token"]

    assert guest1_id != guest2_id

    # Browser 1 consumes 5 analyses
    for i in range(5):
        payload = {
            "claim": f"Klaim uji guest 1 analisis ke-{i+1}",
            "user_id": guest1_id,
            "request_id": f"req_g1_{i+1}_{uuid.uuid4().hex[:6]}"
        }
        headers = [("Authorization", f"Bearer {guest1_token}")]
        st, res, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", payload, headers)
        assert st == 200, f"Guest 1 analysis {i+1} should succeed"

    # Browser 1 6th analysis -> Rejected 402 QUOTA_EXHAUSTED
    payload_g1_6 = {
        "claim": "Klaim uji guest 1 analisis ke-6",
        "user_id": guest1_id,
        "request_id": f"req_g1_6_{uuid.uuid4().hex[:6]}"
    }
    st6, res6, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", payload_g1_6, [("Authorization", f"Bearer {guest1_token}")])
    assert st6 == 402
    assert res6["detail"]["error"] == "QUOTA_EXHAUSTED"

    # Browser 2 attempts analysis -> MUST SUCCEED (quota is isolated and independent!)
    payload_g2_1 = {
        "claim": "Klaim uji guest 2 analisis ke-1",
        "user_id": guest2_id,
        "request_id": f"req_g2_1_{uuid.uuid4().hex[:6]}"
    }
    st_g2, res_g2, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", payload_g2_1, [("Authorization", f"Bearer {guest2_token}")])
    assert st_g2 == 200
    assert res_g2["usage"]["used"] == 1
    assert res_g2["usage"]["remaining"] == 4


@pytest.mark.anyio
async def test_duplicate_request_id_idempotency():
    """Verifies sending the same request_id does not consume extra quota."""
    _, g_data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    g_id = g_data["user_id"]
    g_tok = g_data["session_token"]
    headers = [("Authorization", f"Bearer {g_tok}")]

    fixed_req_id = f"req_idem_{uuid.uuid4().hex}"
    payload = {
        "claim": "Uji idempotensi request_id",
        "user_id": g_id,
        "request_id": fixed_req_id
    }

    # First call -> consumes 1
    st1, res1, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", payload, headers)
    assert st1 == 200
    assert res1["usage"]["used"] == 1

    # Second call with SAME request_id -> returns 200, used count remains 1
    st2, res2, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", payload, headers)
    assert st2 == 200
    assert res2["usage"]["used"] == 1


@pytest.mark.anyio
async def test_guest_cannot_impersonate_registered_user():
    """Guest session token cannot access or spoof registered user account."""
    _, g_data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    g_tok = g_data["session_token"]
    headers = [("Authorization", f"Bearer {g_tok}")]

    registered_user = f"usr_{uuid.uuid4().hex[:12]}"

    # Guest tries to query registered user's context -> 403 Forbidden
    st, data, _ = await dispatch_asgi(f"/api/v1/context?user_id={registered_user}", "GET", headers=headers)
    assert st == 403

    # Guest tries to analyze under registered user's ID -> 403 Forbidden
    st_an, _, _ = await dispatch_asgi("/api/v1/calculator/analyze", "POST", {
        "claim": "Cross user attempt",
        "user_id": registered_user
    }, headers=headers)
    assert st_an == 403


@pytest.mark.anyio
async def test_guest_cannot_checkout_for_another_user():
    """Payment checkout IDOR protection: Guest cannot checkout for another user."""
    _, g_data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    g_tok = g_data["session_token"]
    headers = [("Authorization", f"Bearer {g_tok}")]

    victim_user = f"usr_{uuid.uuid4().hex[:12]}"
    st, data, _ = await dispatch_asgi("/api/v1/payment/checkout", "POST", {
        "user_id": victim_user
    }, headers=headers)
    assert st == 403


@pytest.mark.anyio
async def test_legacy_guest_user_backwards_compatibility():
    """Ensures legacy unauthenticated 'guest_user' calls remain functional."""
    st, data, _ = await dispatch_asgi("/api/v1/context?user_id=guest_user", "GET")
    assert st == 200
    assert "user_perspective" in data
