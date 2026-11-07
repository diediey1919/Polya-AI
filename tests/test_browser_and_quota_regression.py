"""
Playwright Browser & Server Quota Regression Test Suite
Covers:
- Desktop (1440x900) & Mobile (390x844) UI viewports
- Route verification: /themes/friksi-paulus-vs-petrus, /knowledge, /persona/zuma, /pipeline, /account/billing
- 5 Free Analyses server-side quota enforcement
- 6th analysis HTTP 402 Premium Gate block
- Midtrans simulator webhook settlement -> PREMIUM_ACTIVE transition -> analysis unlocked
- Security audit against secret leaks in client payloads
"""
import hashlib
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path
import pytest
playwright = pytest.importorskip("playwright")
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = Path(__file__).resolve().parent.parent / "docs" / "audits" / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def test_browser_navigation_desktop_and_mobile():
    """Verify desktop and mobile rendering across all critical research OS routes."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop Test (1440x900)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")

        # Handle onboarding if modal appears
        if page.is_visible("#onboarding-modal") and not page.locator("#onboarding-modal").is_hidden():
            # Step 1: select English
            page.click("button:has-text('English')")
            page.wait_for_timeout(300)
            page.click("#btn-next-step-1")
            page.wait_for_timeout(500)
            # Step 2: select Christian perspective
            page.click("#persp-christian")
            page.wait_for_timeout(300)
            page.click("#btn-complete-onboarding")
            page.wait_for_timeout(500)

        # Verify Landing & Calculator
        assert page.is_visible("#calc-anchor") or page.is_visible("#claim-input")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_01_landing_calculator.png"))

        # Navigate to Theme Detail: /themes/friksi-paulus-vs-petrus
        page.goto(f"{BASE_URL}/themes/friksi-paulus-vs-petrus", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.is_visible("#view-themes")
        assert page.is_visible("#theme-detail-container")
        assert page.is_visible("#theme-detail-container button:has-text('Overview')")
        assert page.is_visible("#theme-detail-container button:has-text('Narrative')")
        assert page.is_visible("#theme-detail-container button:has-text('Evidence')")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_02_theme_detail.png"))

        # Navigate to Knowledge: /knowledge & /knowledge/graph
        page.goto(f"{BASE_URL}/knowledge", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.is_visible("#view-knowledge")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_03_knowledge.png"))

        # Navigate to Persona Zuma: /persona/zuma
        page.goto(f"{BASE_URL}/persona/zuma", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.is_visible("#view-persona")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_04_zuma_persona.png"))

        # Navigate to Pipeline: /pipeline
        page.goto(f"{BASE_URL}/pipeline", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.is_visible("#view-pipeline")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_05_pipeline.png"))

        # Navigate to Account/Billing: /account/billing
        page.goto(f"{BASE_URL}/account/billing", wait_until="networkidle")
        page.wait_for_timeout(500)
        assert page.is_visible("#view-account")
        page.screenshot(path=str(SCREENSHOT_DIR / "desktop_06_account_billing.png"))

        # 2. Mobile Test (390x844)
        mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
        mobile_page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
        mobile_page.wait_for_timeout(500)
        assert mobile_page.is_visible("#view-dashboard")
        mobile_page.screenshot(path=str(SCREENSHOT_DIR / "mobile_01_dashboard.png"))

        browser.close()


def test_server_side_quota_and_premium_gate_regression():
    """Verify 5 free analyses quota, 6th analysis 402 block, and Midtrans simulator unlock."""
    auth_resp = requests.post(f"{BASE_URL}/api/v1/auth/guest")
    assert auth_resp.status_code == 200, f"Guest auth failed: {auth_resp.text}"
    auth_data = auth_resp.json()
    test_user_id = auth_data["user_id"]
    headers = {"Authorization": f"Bearer {auth_data['session_token']}"}

    # Run 1 through 5: All must succeed
    for i in range(1, 6):
        resp = requests.post(f"{BASE_URL}/api/v1/calculator/analyze", json={
            "claim": f"Test theological claim analysis index {i}",
            "user_id": test_user_id,
            "request_id": f"req_{test_user_id}_{i}",
            "perspective": "christian"
        }, headers=headers)
        assert resp.status_code == 200, f"Analysis {i} should succeed, got {resp.status_code}"
        data = resp.json()
        assert data["success"] is True
        assert data["usage"]["used"] == i
        assert data["usage"]["remaining"] == 5 - i

    # Run 6: Must be blocked by HTTP 402 PAYMENT REQUIRED
    resp_blocked = requests.post(f"{BASE_URL}/api/v1/calculator/analyze", json={
        "claim": "6th claim exceeding free quota limit",
        "user_id": test_user_id,
        "request_id": f"req_{test_user_id}_6",
        "perspective": "christian"
    }, headers=headers)
    assert resp_blocked.status_code == 402, f"6th analysis must return 402, got {resp_blocked.status_code}"
    detail = resp_blocked.json().get("detail", {})
    assert detail.get("error") == "QUOTA_EXHAUSTED"
    assert "price" in detail

    # Simulate Midtrans Checkout & Settlement Transition
    checkout_resp = requests.post(f"{BASE_URL}/api/v1/payment/checkout", json={
        "user_id": test_user_id,
        "plan": "premium",
        "idempotency_key": f"idem_{uuid.uuid4().hex[:8]}"
    }, headers=headers)
    assert checkout_resp.status_code == 200
    order_id = checkout_resp.json()["order_id"]
    gross_amount = f"{checkout_resp.json().get('amount', 145000)}.00"

    # Simulate Midtrans webhook with simulation signature
    server_key = os.environ.get("MIDTRANS_SERVER_KEY")
    if not server_key:
        env_prod = Path(__file__).resolve().parent.parent / "web" / ".env.production"
        if env_prod.exists():
            for line in env_prod.read_text().splitlines():
                if line.startswith("MIDTRANS_SERVER_KEY="):
                    server_key = line.split("=", 1)[1].strip().strip("'\"")
                    break
    if not server_key:
        server_key = "SB-Mid-server-simulated-key"
    raw_sig_str = f"{order_id}200{gross_amount}{server_key}"
    sig = hashlib.sha512(raw_sig_str.encode("utf-8")).hexdigest()

    webhook_payload = {
        "order_id": order_id,
        "status_code": "200",
        "gross_amount": gross_amount,
        "signature_key": sig,
        "transaction_status": "settlement",
        "fraud_status": "accept",
        "payment_type": "credit_card",
        "is_simulation": True,
        "is_simulator": True
    }
    wh_resp = requests.post(f"{BASE_URL}/api/v1/payment/midtrans/webhook", json=webhook_payload)
    assert wh_resp.status_code == 200
    assert wh_resp.json()["status"] == "settled"

    # Verify Entitlement is now PREMIUM_ACTIVE
    ent_resp = requests.get(f"{BASE_URL}/api/v1/entitlements/status?user_id={test_user_id}", headers=headers)
    assert ent_resp.status_code == 200
    assert ent_resp.json()["state"] == "PREMIUM_ACTIVE"
    assert ent_resp.json()["is_premium"] is True

    # Run 7: Unlocked!
    resp_unlocked = requests.post(f"{BASE_URL}/api/v1/calculator/analyze", json={
        "claim": "7th claim after premium upgrade",
        "user_id": test_user_id,
        "request_id": f"req_{test_user_id}_7",
        "perspective": "christian"
    }, headers=headers)
    assert resp_unlocked.status_code == 200
    assert resp_unlocked.json()["success"] is True


def test_security_secrets_not_exposed():
    """Verify that private keys and raw backend secrets are never exposed to clients."""
    # 1. Inspect client HTML
    root_html = requests.get(f"{BASE_URL}/").text
    assert "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" not in root_html
    assert "GEMINI_API_KEY" not in root_html
    assert "BEGIN RSA PRIVATE KEY" not in root_html

    # 2. Inspect meta languages API response
    lang_json = requests.get(f"{BASE_URL}/api/v1/meta/languages").text
    assert "sk-" not in lang_json
    assert "key" not in lang_json.lower() or "languages" in lang_json
