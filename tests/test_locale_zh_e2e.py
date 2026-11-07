import pytest
import re
from fastapi.testclient import TestClient
from web.app import app
from web.api_foundation import AnalyzeRequest
from web.models import UserApologeticsContext
from web.services import SessionService
from orchestrator.zuma_skill_engine import ZumaSkillEngine

client = TestClient(app)

def test_frontend_index_html_i18n_sidebar_and_calculator():
    """Verify that all sidebar and calculator elements in index.html have data-i18n and resolve in zh."""
    with open("/home/ubuntu/Polya-AI/web/static/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # 1. Sidebar elements have data-i18n
    sidebar_ids = [
        "side-heading-workspace", "side-item-calc", "side-item-dash",
        "side-item-themes-title", "side-heading-evidence", "side-item-knowledge",
        "side-item-persona", "side-item-pipeline", "side-heading-prep",
        "side-item-settings", "side-item-account", "side-item-arena", "side-item-about"
    ]
    for sid in sidebar_ids:
        pattern = rf'id="{sid}"[^>]*data-i18n="([^"]+)"'
        m = re.search(pattern, html)
        if not m:
            # check reverse order
            pattern2 = rf'data-i18n="([^"]+)"[^>]*id="{sid}"'
            m = re.search(pattern2, html)
        assert m is not None, f"Sidebar element #{sid} is missing data-i18n attribute"

    # 2. Calculator elements have data-i18n
    calc_ids = [
        "calc-hero-title", "calc-hero-copy", "hero-cta-btn", "calc-header-title",
        "btn-mode-debate", "btn-mode-research", "btn-calc-text",
        "canonical-cases-title", "canonical-cases-sub",
        "case-claim-display", "case-zuma-header", "case-primary-ev-header",
        "case-ctx-ling-header", "case-opp-counter-header", "case-rebuttal-header",
        "case-weakness-header", "case-open-q-header", "case-provenance-header",
        "btn-weakest-point", "adv-title"
    ]
    for cid in calc_ids:
        pattern = rf'id="{cid}"[^>]*data-i18n="([^"]+)"'
        m = re.search(pattern, html)
        if not m:
            pattern2 = rf'data-i18n="([^"]+)"[^>]*id="{cid}"'
            m = re.search(pattern2, html)
        assert m is not None, f"Calculator element #{cid} is missing data-i18n attribute"

    # 3. Check CANONICAL_MOTIONS_I18N exists in index.html
    assert "const CANONICAL_MOTIONS_I18N = {" in html
    assert '"W3z8vlpbh_I"' in html
    assert '"zh"' in html

def test_zuma_canonical_8_rounds_simulation_zh():
    """Verify ZumaSkillEngine generates 8 rounds in Chinese when target_locale is zh."""
    ctx = {
        "user_perspective": "christian_protestant",
        "opponent_perspective": "islam",
        "ui_locale": "zh",
        "debate_locale": "zh"
    }
    claim = "通过耶稣吃烤鱼（路加福音 24:42）的事实反驳幽灵/幻影假说"
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim=claim, context=ctx)
    
    assert sim is not None
    assert sim["motion_or_topic"].startswith("对主张的原典文本与正典有效性法医审计")
    assert len(sim["rounds"]) == 16  # 8 rounds * 2 speakers
    
    # Check that ZUMA and Opponent speeches contain Chinese text in Socratic style
    r1_zuma = sim["rounds"][0]["speaker_speech"]
    r1_opp = sim["rounds"][1]["speaker_speech"]
    
    assert ("苏格拉底" in r1_zuma or "手抄本" in r1_zuma)
    assert "纯正一神论" in r1_opp
    
    # Check cross examination in Chinese
    ce = sim["cross_examination"][0]
    assert "你是否愿意逐字承认" in ce["socratic_question"]
    assert "肯定性批判" in sim["epistemic_verdict"]["logical_superiority"]

def test_calculator_analyze_endpoint_zh():
    """Verify POST /api/v1/calculator/analyze with zh locale produces Chinese output."""
    token, guest_id = SessionService.create_guest_token()
    payload = {
        "claim": "通过耶稣吃烤鱼（路加福音 24:42）的事实反驳幽灵/幻影假说",
        "mode": "debate",
        "user_id": guest_id,
        "context": {
            "user_perspective": "christian_protestant",
            "opponent_perspective": "islam",
            "ui_locale": "zh",
            "debate_locale": "zh"
        }
    }
    headers = {"Authorization": f"Bearer {token}"}
    res = client.post("/api/v1/calculator/analyze", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    cf = data["case_file"]
    
    # Verify debate_preparation contains canonical 8 rounds in Chinese
    prep = cf.get("debate_preparation", {})
    sim = prep.get("canonical_8_rounds", {})
    assert sim is not None
    assert len(sim.get("rounds", [])) == 16
    
    r1_zuma = sim["rounds"][0]["speaker_speech"]
    assert len(r1_zuma) > 0
    assert any('\u4e00' <= char <= '\u9fff' for char in r1_zuma)
    assert "[ZUMA 模拟发言]" not in r1_zuma
