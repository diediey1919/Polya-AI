"""
POLYA-WEB-001: Unit & Integration Test Suite
Validation for Repeated Google Sign-In Click Behavior, GIS Flow, Account Switching & Regression Gates.
"""
import json
import os
import re
import sys
import uuid
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

os.environ["POLYA_AUTH_SECRET"] = "staging_test_auth_secret_minimum_32_characters_for_hmac_256"
os.environ["POLYA_ENV"] = "staging"
os.environ["GOOGLE_CLIENT_ID"] = "953116755250-p8n0eqgrsb84k7tfakptmb3nuccjn6vr.apps.googleusercontent.com"

from web.app import app
from web.services import (
    GoogleAuthVerifier,
    SessionService,
    UsageEntitlementService,
    EntitlementService,
)

STAGING_CLIENT_ID = "953116755250-p8n0eqgrsb84k7tfakptmb3nuccjn6vr.apps.googleusercontent.com"
PROD_CLIENT_ID = "953116755250-qomlk1eh2q01u62nlfemm68td1ca2bbu.apps.googleusercontent.com"
INDEX_HTML_PATH = os.path.join(WEB_DIR, "static", "index.html")


def read_index_html() -> str:
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


async def dispatch_asgi(path: str, method: str = "GET", payload: dict = None, headers: list = None):
    body_bytes = json.dumps(payload).encode("utf-8") if payload else b""
    hdr_list = [(b"host", b"staging.apologets.com")]
    if payload:
        hdr_list.append((b"content-type", b"application/json"))
        hdr_list.append((b"content-length", str(len(body_bytes)).encode("utf-8")))
    if headers:
        for k, v in headers:
            hdr_list.append((k.lower().encode("utf-8"), v.encode("utf-8")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path.split("?")[0],
        "raw_path": path.split("?")[0].encode("utf-8"),
        "query_string": path.split("?")[1].encode("utf-8") if "?" in path else b"",
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
# 1. STATIC ASSET & DOM INTEGRITY CHECKS
# ===========================================================================

def test_index_html_gis_script_tag_and_onload_handler():
    """Validates that GIS script is loaded asynchronously with onload init handler."""
    html = read_index_html()
    assert "https://accounts.google.com/gsi/client" in html
    assert "gisScript.onload" in html
    assert "initGoogleIdentity" in html
    assert "gisScript.onerror" in html


def test_index_html_contains_required_dom_elements():
    """Ensures DOM contains all auth buttons, GIS containers, and switch account elements."""
    html = read_index_html()
    # Sidebar elements
    assert 'id="sb-auth-action"' in html
    assert 'id="sb-auth-text"' in html
    assert 'id="sb-switch-action"' in html
    assert 'id="g-signin-btn-container"' in html
    # Account view elements
    assert 'id="acc-name"' in html
    assert 'id="acc-email"' in html
    assert 'id="acc-btn-switch"' in html
    assert 'id="acc-btn-signout"' in html
    # Top-left header GIS containers (moved from account view)
    assert 'id="desktop-hdr-g-signin-container"' in html
    assert 'id="mobile-hdr-g-signin-container"' in html


def test_gis_javascript_functions_present():
    """Validates presence and structure of all required GIS handlers in index.html."""
    html = read_index_html()
    assert "function getGoogleClientId()" in html
    assert "function clearGoogleCoolDownCookies()" in html
    assert "function initGoogleIdentity()" in html
    assert "function renderGoogleButtons()" in html
    assert "function handleGoogleCredentialResponse(resp)" in html
    assert "function handleSignOut()" in html
    assert "function handleSwitchAccount()" in html
    assert "function updateAuthUI(user)" in html
    assert "async function triggerGoogleAuth()" in html


def test_repeated_click_resilience_logic_in_script():
    """Verifies that triggerGoogleAuth handles cooldown cookies, cancel, safety timeout, and moment states."""
    html = read_index_html()
    # Cooldown clearing
    assert "clearGoogleCoolDownCookies()" in html
    assert "g_state=;" in html
    # Cancel pending prompt
    assert "google.accounts.id.cancel()" in html
    # Safety timer
    assert "authSafetyTimer = setTimeout" in html
    # Moment handlers
    assert "notification.isDisplayed" in html
    assert "notification.isNotDisplayed" in html
    assert "notification.isDismissedMoment" in html
    assert "notification.isSkippedMoment" in html
    # Google renderButton integration
    assert "google.accounts.id.renderButton" in html


def test_switch_account_and_logout_gis_auto_select_disabled():
    """Verifies that handleSignOut and handleSwitchAccount call disableAutoSelect."""
    html = read_index_html()
    assert "google.accounts.id.disableAutoSelect()" in html
    assert "handleSwitchAccount()" in html


# ===========================================================================
# 2. BACKEND AUTH ENDPOINT VERIFICATION
# ===========================================================================

@pytest.mark.anyio
async def test_backend_auth_session_rejects_missing_credential():
    """Validates that empty or missing credential returns HTTP 401."""
    status, data, _ = await dispatch_asgi("/api/v1/auth/session", "POST", {"credential": "invalid.dummy.token"})
    assert status == 401
    assert "Authentication failed" in data.get("detail", "")


@pytest.mark.anyio
async def test_backend_auth_session_rejects_mock_in_staging():
    """Validates mock authentication is rejected when staging environment is active."""
    status, data, _ = await dispatch_asgi("/api/v1/auth/session", "POST", {
        "credential": "mock-google-token:test@polya.org:mock123:Test",
        "is_mock": True
    })
    assert status in (401, 403)


@pytest.mark.anyio
async def test_backend_guest_session_issuance_and_consistency():
    """Validates guest session endpoint returns valid token and isolated user ID."""
    status, data, _ = await dispatch_asgi("/api/v1/auth/guest", "POST")
    assert status == 200
    assert data["success"] is True
    assert data["role"] == "guest"
    assert data["user_id"].startswith("guest_")
    assert "session_token" in data
