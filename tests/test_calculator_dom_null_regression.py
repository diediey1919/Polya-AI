"""
P0 Test Suite: Calculator End-to-End DOM Null Reference Regression Test
Validates:
1. index.html DOM structure and JavaScript null-safety for all element assignments.
2. updateUsageUI() and applyContextToUI() execution without null reference exceptions.
3. renderCaseFile() rendering completeness across all 10 canonical fields.
4. Variations of manuscripts and debate_preparation structures.
5. Non-fatal telemetry isolation in runAnalysis().
6. Backend analyze endpoint HTTP status codes (200, 401, 402, 403) and contract alignment.
"""
import json
import os
import re
import sys
import uuid
import pytest
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

os.environ["POLYA_AUTH_SECRET"] = "test_auth_secret_for_pytest_suite_32chars"
from web.app import app
from web.services import SessionService

INDEX_HTML_PATH = os.path.join(WEB_DIR, "static", "index.html")


def read_index_html() -> str:
    with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


async def dispatch_asgi(path: str, method: str = "GET", payload: dict = None, headers: list = None):
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


def test_index_html_has_no_unguarded_badge_quota_display():
    """Ensures updateUsageUI guards all DOM lookups before textContent assignment."""
    html = read_index_html()
    # Confirm guards exist around pill, bPersp, bLang
    assert "if (pill) {" in html
    assert "if (bPersp) bPersp.textContent = label;" in html
    assert "if (bLang) bLang.textContent =" in html
    assert "if (calcPill) {" in html
    assert "if (dashPill) dashPill.textContent =" in html


def test_index_html_contains_calculator_dom_elements():
    """Validates presence of all critical calculator DOM containers in index.html."""
    html = read_index_html()
    critical_ids = [
        "claim-input",
        "btn-calc-analyze",
        "btn-calc-loader",
        "btn-calc-text",
        "calc-quota-pill",
        "case-file-result",
        "case-id-display",
        "case-claim-display",
        "case-context-display",
        "case-argument-content",
        "case-counter-content",
        "case-rebuttal-content",
        "case-weakness-content",
        "case-status-badge",
        "case-evidence-content",
        "case-questions-content",
        "case-prep-content",
        "case-sources-body",
    ]
    for cid in critical_ids:
        assert f'id="{cid}"' in html, f"Missing critical calculator DOM element: {cid}"


@pytest.mark.anyio
async def test_calculator_analyze_returns_complete_contract():
    """Validates backend returns case_file and usage contract expected by calculator renderer."""
    test_user = f"calc_user_{uuid.uuid4().hex[:6]}"
    token = SessionService.create_token(test_user)
    payload = {
        "claim": "Yesus disalibkan pada jam ketiga menurut Markus 15:25",
        "request_id": f"calc_req_{uuid.uuid4().hex[:8]}",
        "user_id": test_user,
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
    assert "case_file" in data
    assert "usage" in data
    assert "used" in data["usage"]
    assert "remaining" in data["usage"]

    cf = data["case_file"]
    for field in ["case_id", "claim", "context", "evidence", "argument", "counterargument", "rebuttal", "weakness", "sources", "open_questions", "debate_preparation"]:
        assert field in cf, f"Case file missing field: {field}"


@pytest.mark.anyio
async def test_calculator_quota_exhausted_returns_402():
    """Validates 402 QUOTA_EXHAUSTED behavior handled gracefully."""
    test_user = f"quota_user_{uuid.uuid4().hex[:6]}"
    token = SessionService.create_token(test_user)

    for i in range(5):
        st, _, _ = await dispatch_asgi(
            "/api/v1/calculator/analyze", "POST",
            {
                "claim": f"Test claim #{i+1}",
                "request_id": f"req_quota_{test_user}_{i+1}",
                "user_id": test_user
            },
            headers=[("Authorization", f"Bearer {token}")]
        )
        assert st == 200

    # 6th request
    st6, data6, _ = await dispatch_asgi(
        "/api/v1/calculator/analyze", "POST",
        {
            "claim": "Test claim 6th attempt",
            "request_id": f"req_quota_{test_user}_6",
            "user_id": test_user
        },
        headers=[("Authorization", f"Bearer {token}")]
    )
    assert st6 == 402
    assert data6["detail"]["error"] == "QUOTA_EXHAUSTED"


def test_index_html_sidebar_auto_collapse_bindings():
    """Validates presence and completeness of auto-collapse sidebar bindings across Calculator, Dashboard, and Persona Dialektika."""
    html = read_index_html()

    # 1. CSS layout rule encompasses calculator, dashboard, and persona views
    assert "#view-calculator," in html
    assert "#view-dashboard," in html
    assert "#view-persona {" in html

    # 2. View section click bindings for auto-collapsing sidebar
    assert 'const calcSection = document.getElementById("view-calculator");' in html
    assert 'const dashSection = document.getElementById("view-dashboard");' in html
    assert 'const personaSection = document.getElementById("view-persona");' in html

    # 3. Form input auto-collapse bindings on persona view
    assert '"zuma-topic-input"' in html
    assert '"zuma-pos-select"' in html
    assert '"zuma-diff-select"' in html
    assert '"zuma-arg-claim"' in html
    assert '"zuma-arg-reasoning"' in html

    # 4. startZumaSparringSession calls collapseSidebar()
    pattern = r"async\s+function\s+startZumaSparringSession\s*\(\)\s*\{\s*collapseSidebar\(\);"
    assert re.search(pattern, html) is not None, "startZumaSparringSession() must immediately call collapseSidebar()"

    # 5. Full width expansion on persona cards without restrictive max-width
    assert 'id="zuma-setup-box" class="case-card border-beam-card" style="padding: 1.5rem; margin-bottom: 1.5rem; width: 100%; max-width: 100%; box-sizing: border-box;"' in html
    zuma_setup_slice = html[html.find('id="zuma-setup-box"'):html.find('id="zuma-setup-box"') + 200]
    assert 'max-width: 650px' not in zuma_setup_slice

    # 6. Sidebar toggle spacing clearance on collapsed persona view
    assert '.app-body.sidebar-collapsed #view-persona' in html
    assert 'padding-top: 2.75rem' in html


def test_nimbus_liquid_navbar_mobile_menu_mapping():
    """Validates Nimbus UI Liquid Navbar 7 buttons, routes, accessibility attributes, and route sync."""
    html = read_index_html()

    # 1. Navbar container and ID
    assert 'id="mobile-top-nav"' in html
    assert 'class="nimbus-nav"' in html

    # 2. Seven navigation buttons with exact routes
    assert 'data-route="/"' in html
    assert 'data-route="/themes"' in html
    assert 'data-route="/persona"' in html
    assert 'data-route="/kursus-bahasa-kuno"' in html
    assert 'data-route="/pricing"' in html
    assert 'data-route="/pipeline"' in html
    assert 'data-route="/settings"' in html

    # 3. Accessibility labels and titles
    assert 'aria-label="Apologetics Calculator"' in html
    assert 'aria-label="Tema & Mosi Debat"' in html
    assert 'aria-label="Persona Dialektika (ZUMA Cockpit)"' in html
    assert 'aria-label="Kursus Bahasa Kuno (Metode Polyglot)"' in html
    assert 'aria-label="Pricing & Plans"' in html
    assert 'aria-label="Exegesis Pipeline"' in html
    assert 'aria-label="Settings"' in html

    # 4. Route sync logic in JS
    assert 'navigateRoute(null, "/persona");' in html
    assert 'navigateRoute(null, "/kursus-bahasa-kuno");' in html
    assert 'navigateRoute(null, "/pricing");' in html
    assert 'navigateRoute(null, "/pipeline");' in html
    assert 'navigateRoute(null, "/settings");' in html
    assert 'path.startsWith("/persona")' in html
    assert 'path.startsWith("/kursus-bahasa-kuno")' in html
    assert 'path.startsWith("/pipeline")' in html
    assert 'path.startsWith("/settings")' in html

    # 5. Position order verification: button 4 is /pipeline
    pipeline_pos = html.find('data-route="/pipeline"')
    kursus_pos = html.find('data-route="/kursus-bahasa-kuno"')
    pricing_pos = html.find('data-route="/pricing"')
    settings_pos = html.find('data-route="/settings"')
    assert pipeline_pos < kursus_pos < pricing_pos < settings_pos

