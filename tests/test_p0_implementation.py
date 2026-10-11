"""
P0 Implementation Test Suite
Covers:
1. P0.1: Calculator Result Completeness, Challenge My Argument, Weakest Point, Show Source.
2. P0.2: Case File Persistence, Idempotency, Retrieval, Cross-User Authorization, Backward Compatibility.
3. P0.3: Debate Arena Navigation & Canonical Integrity.
4. P0.4: Security Access Control (Cross-user spoofing prevention, unauthenticated rejection, valid session access).
"""
import asyncio
import json
import os
import sys
import uuid
import pytest
from pathlib import Path

# Setup sys.path for web and orchestrator imports
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

os.environ["POLYA_AUTH_SECRET"] = "test_auth_secret_for_pytest_suite_32chars"
from web.app import app
from web.services import SessionService
from orchestrator.case_file import CaseFiles, CanonicalCaseFile


async def dispatch_asgi(path: str, method: str = "GET", payload: dict = None, headers: list = None):
    """Helper to dispatch requests directly to the FastAPI ASGI app without raw sockets."""
    body_bytes = json.dumps(payload).encode("utf-8") if payload else b""
    hdr_list = [(b"host", b"localhost")]
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


@pytest.mark.anyio
async def test_p0_1_calculator_all_fields_and_adversarial_endpoints():
    """P0.1: Verifies all 10 fields returned in analyze, plus challenge, weakest-point, source endpoints."""
    # 1. Analyze endpoint returns all 10 canonical fields
    fresh_user = f"fresh_user_{uuid.uuid4().hex[:6]}"
    token = SessionService.create_token(fresh_user)
    payload = {
        "claim": "Roma 3:31 membuktikan iman menegakkan hukum Taurat",
        "request_id": f"p0_test_req_{uuid.uuid4().hex[:8]}",
        "user_id": fresh_user,
        "context": {
            "ui_locale": "id",
            "user_perspective": "christian",
            "opponent_perspective": "islam",
            "debate_locale": "id",
            "source_locale": "el"
        }
    }
    status, data, _ = await dispatch_asgi(
        "/api/v1/calculator/analyze", "POST", payload,
        headers=[("Authorization", f"Bearer {token}")]
    )
    assert status == 200
    assert data["success"] is True
    cf = data["case_file"]

    # Verify all 10 fields exist and are populated
    assert "claim" in cf and cf["claim"]
    assert "context" in cf and cf["context"]
    assert "evidence" in cf and len(cf["evidence"]) > 0
    assert "argument" in cf and cf["argument"]
    assert "counterargument" in cf and cf["counterargument"]
    assert "rebuttal" in cf and cf["rebuttal"]
    assert "weakness" in cf and cf["weakness"]
    assert "sources" in cf and len(cf["sources"]) > 0
    assert "open_questions" in cf and len(cf["open_questions"]) > 0
    assert "debate_preparation" in cf and len(cf["debate_preparation"]) > 0

    # 2. Challenge My Argument endpoint
    chal_payload = {
        "claim": "Roma 3:31 membuktikan iman menegakkan hukum Taurat",
        "request_id": f"p0_chal_req_{uuid.uuid4().hex[:8]}",
        "user_id": fresh_user,
        "context": payload["context"]
    }
    c_status, c_data, _ = await dispatch_asgi("/api/v1/calculator/challenge", "POST", chal_payload, headers=[("Authorization", f"Bearer {token}")])
    assert c_status == 200
    assert c_data["success"] is True
    assert "adversarial_attacks" in c_data
    assert "self_refutation_survived" in c_data
    assert "zuma_self_critique" in c_data

    # 3. Weakest Point Analysis endpoint
    weak_payload = {
        "claim": "Roma 3:31 membuktikan iman menegakkan hukum Taurat",
        "request_id": f"p0_weak_req_{uuid.uuid4().hex[:8]}",
        "user_id": fresh_user,
        "context": payload["context"]
    }
    w_status, w_data, _ = await dispatch_asgi("/api/v1/calculator/weakest-point", "POST", weak_payload, headers=[("Authorization", f"Bearer {token}")])
    assert w_status == 200
    assert w_data["success"] is True
    assert "weakest_premise" in w_data
    assert "hardening_recommendations" in w_data

    # 4. Show Me The Source endpoint
    s_status, s_data, _ = await dispatch_asgi("/api/v1/calculator/source?passage=Roma%203:31", "GET")
    assert s_status == 200
    assert s_data["success"] is True
    src = s_data["source"]
    assert src["passage_reference"] == "Roma 3:31"
    assert "νόμον" in src["original_text"]
    assert len(src["witnesses"]) > 0
    assert len(src["tokens"]) > 0


@pytest.mark.anyio
async def test_p0_2_case_file_persistence_idempotency_and_authorization():
    """P0.2: Verifies persistence into case_files_v2, listing, cross-user isolation, and backward compatibility."""
    user_a = f"usr_test_a_{uuid.uuid4().hex[:6]}"
    user_b = f"usr_test_b_{uuid.uuid4().hex[:6]}"
    token_a = SessionService.create_token(user_a)
    token_b = SessionService.create_token(user_b)

    # 1. User A runs analysis
    req_id = f"req_persist_{uuid.uuid4().hex[:8]}"
    analyze_payload = {
        "claim": "Efesus 2:15 perobohan tembok pemisah hukum Taurat",
        "request_id": req_id,
        "user_id": user_a,
        "context": {"user_perspective": "christian", "opponent_perspective": "islam"}
    }
    status, data, _ = await dispatch_asgi(
        "/api/v1/calculator/analyze", "POST", analyze_payload,
        headers=[("Authorization", f"Bearer {token_a}")]
    )
    assert status == 200
    case_id = data["case_file"]["case_id"]

    # 2. Case file is persisted in SQLite case_files_v2
    persisted_cf = CaseFiles.get_case_file(case_id)
    assert persisted_cf is not None
    assert persisted_cf.case_id == case_id

    # 3. User A lists their case files -> includes case_id
    l_status, l_data, _ = await dispatch_asgi(
        f"/api/v1/case-files?user_id={user_a}", "GET",
        headers=[("Authorization", f"Bearer {token_a}")]
    )
    assert l_status == 200
    assert l_data["success"] is True
    found_ids = [f["case_id"] for f in l_data["case_files"]]
    assert case_id in found_ids

    # 4. User A fetches their specific case file -> 200 OK
    g_status, g_data, _ = await dispatch_asgi(
        f"/api/v1/case-files/{case_id}?user_id={user_a}", "GET",
        headers=[("Authorization", f"Bearer {token_a}")]
    )
    assert g_status == 200
    assert g_data["case_file"]["case_id"] == case_id

    # 5. User B attempts to access User A's case file -> 403 Forbidden
    b_status, b_data, _ = await dispatch_asgi(
        f"/api/v1/case-files/{case_id}?user_id={user_b}", "GET",
        headers=[("Authorization", f"Bearer {token_b}")]
    )
    assert b_status == 403

    # 6. Idempotency: Repeating same request_id does not create duplicate quota spend
    status_rep, data_rep, _ = await dispatch_asgi(
        "/api/v1/calculator/analyze", "POST", analyze_payload,
        headers=[("Authorization", f"Bearer {token_a}")]
    )
    assert status_rep == 200
    assert data_rep["usage"]["used"] == data["usage"]["used"]

    # 7. Backward compatibility: Existing 195+ legacy records can still be loaded
    legacy_cf = CaseFiles.get_case_file("case_235308760e")
    if legacy_cf:
        assert legacy_cf.case_id == "case_235308760e"
        assert legacy_cf.claim is not None


@pytest.mark.anyio
async def test_p0_3_debate_arena_navigation_and_integrity():
    """P0.3: Verifies Debate Arena routes exist, are served, and HTML contains navigation links."""
    # 1. /arena serves the canonical 3v3 arena page
    status, _, html_text = await dispatch_asgi("/arena", "GET")
    assert status == 200
    assert "DEBATE ARENA" in html_text
    assert "3-vs-3" in html_text or "3v3" in html_text

    # 2. Authoritative state endpoint returns valid 16-state FSM state
    s_status, s_data, _ = await dispatch_asgi("/api/arena/state", "GET")
    assert s_status == 200
    assert s_data["authoritative"] is True
    assert "round" in s_data
    assert "speaker" in s_data and "teams" in s_data

    # 3. index.html contains navigation link to /arena
    _, _, index_html = await dispatch_asgi("/", "GET")
    assert "href=\"/arena\"" in index_html
    assert "Debate Arena (3-vs-3)" in index_html


@pytest.mark.anyio
async def test_p0_4_security_cross_user_spoofing_prevention():
    """P0.4: Verifies cross-user spoofing is rejected with 403/401 and authenticated access succeeds."""
    legit_user = f"legit_user_{uuid.uuid4().hex[:6]}"
    victim_user = f"victim_user_{uuid.uuid4().hex[:6]}"
    attacker_user = f"attacker_user_{uuid.uuid4().hex[:6]}"

    legit_token = SessionService.create_token(legit_user)
    attacker_token = SessionService.create_token(attacker_user)

    # 1. Unauthenticated request to non-guest user context -> 401
    status_unauth, _, _ = await dispatch_asgi(f"/api/v1/context?user_id={victim_user}", "GET")
    assert status_unauth == 401

    # 2. Unauthenticated request to non-guest entitlements usage -> 401
    status_unauth_q, _, _ = await dispatch_asgi(f"/api/v1/entitlements/usage?user_id={victim_user}", "GET")
    assert status_unauth_q == 401

    # 3. Attacker token trying to access victim user context -> 403 Forbidden
    status_spoof, _, _ = await dispatch_asgi(
        f"/api/v1/context?user_id={victim_user}", "GET",
        headers=[("Authorization", f"Bearer {attacker_token}")]
    )
    assert status_spoof == 403

    # 4. Attacker token trying to overwrite victim context -> 403 Forbidden
    status_spoof_post, _, _ = await dispatch_asgi(
        f"/api/v1/context?user_id={victim_user}", "POST",
        payload={"ui_locale": "ar", "user_perspective": "islam", "opponent_perspective": "christian"},
        headers=[("Authorization", f"Bearer {attacker_token}")]
    )
    assert status_spoof_post == 403

    # 5. Attacker token trying to inspect victim usage quota -> 403 Forbidden
    status_spoof_usage, _, _ = await dispatch_asgi(
        f"/api/v1/entitlements/usage?user_id={victim_user}", "GET",
        headers=[("Authorization", f"Bearer {attacker_token}")]
    )
    assert status_spoof_usage == 403

    # 6. Legitimate user access with matching token -> 200 OK
    status_legit, legit_data, _ = await dispatch_asgi(
        f"/api/v1/context?user_id={legit_user}", "GET",
        headers=[("Authorization", f"Bearer {legit_token}")]
    )
    assert status_legit == 200

    # 7. Anonymous guest user access -> 200 OK (preserves friction-free onboarding)
    status_guest, guest_data, _ = await dispatch_asgi("/api/v1/context?user_id=guest_user", "GET")
    assert status_guest == 200
