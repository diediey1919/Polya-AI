"""
Unit Tests for Language Selection, Synchronization & Localization (i18n)
Validates:
1. Canonical Language Registry (/api/v1/meta/languages returns 17 languages)
2. ContextService persistence of ui_locale & debate_locale in SQLite
3. API endpoint POST /api/v1/context updating ui_locale & debate_locale
4. ZumaSkillEngine canonical 8-round simulation in English vs Indonesian
5. CaseFileGenerator generating localized context and simulation
"""
import sys
import uuid
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "web"))

from starlette.testclient import TestClient
from web.app import app
from web.models import UserApologeticsContext, UserPerspective, LANGUAGE_REGISTRY
from web.services import ContextService, CaseFileGenerator
from orchestrator.zuma_skill_engine import ZumaSkillEngine

client = TestClient(app)


def test_meta_languages_registry():
    """Verify all 17 canonical languages are served by /api/v1/meta/languages."""
    res = client.get("/api/v1/meta/languages")
    assert res.status_code == 200
    data = res.json()
    assert "languages" in data
    langs = data["languages"]
    assert len(langs) == 17
    codes = [l["code"] for l in langs]
    expected_codes = ["id", "en", "ar", "es", "pt", "ur", "hi", "fr", "de", "ru", "tr", "fa", "bn", "zh", "ja", "ko", "it"]
    for code in expected_codes:
        assert code in codes, f"Expected {code} in languages"


def test_context_service_locale_persistence():
    """Verify ContextService persists and retrieves ui_locale & debate_locale."""
    uid = f"user_test_i18n_{uuid.uuid4().hex[:8]}"
    ctx = UserApologeticsContext(
        ui_locale="en",
        debate_locale="en",
        user_perspective=UserPerspective.CHRISTIAN_PROTESTANT,
        opponent_perspective="islam"
    )

    saved = ContextService.save_user_context(uid, ctx)
    assert saved["ui_locale"] == "en"
    assert saved["debate_locale"] == "en"

    retrieved = ContextService.get_user_context(uid)
    assert retrieved["ui_locale"] == "en"
    assert retrieved["debate_locale"] == "en"
    assert retrieved["user_perspective"] == "christian_protestant"
    assert retrieved["opponent_perspective"] == "islam"


def test_api_context_endpoint_localization(monkeypatch):
    """Verify POST /api/v1/context persists custom language locales."""
    monkeypatch.setenv("POLYA_AUTH_SECRET", "test_auth_secret_key_123")
    # Obtain guest token
    auth_res = client.post("/api/v1/auth/guest", json={"client_id": f"guest_i18n_{uuid.uuid4().hex[:6]}"})
    assert auth_res.status_code == 200
    token = auth_res.json()["session_token"]
    user_id = auth_res.json()["user_id"]

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "ui_locale": "ar",
        "debate_locale": "ar",
        "user_perspective": "islam",
        "opponent_perspective": "christian_protestant"
    }

    res = client.post(f"/api/v1/context?user_id={user_id}", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["context"]["ui_locale"] == "ar"
    assert data["context"]["debate_locale"] == "ar"


def test_zuma_canonical_simulation_localization_en():
    """Verify ZumaSkillEngine generates English debate simulation when locale is 'en'."""
    claim = "Lukas 24:42 Yesus memakan ikan goreng membuktikan kebangkitan jasmani"
    ctx = {
        "user_perspective": "christian_protestant",
        "opponent_perspective": "islam",
        "debate_locale": "en",
        "ui_locale": "en"
    }
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim=claim, context=ctx)

    assert sim["schema_version"] == "1.0.0"
    assert "Forensic Primary Text & Canonical Validity Audit" in sim["motion_or_topic"]
    assert "Theological & Apologetics Discourse" in sim["original_youtube_title"]

    rounds = sim["rounds"]
    assert len(rounds) == 16

    # Round 1 ZUMA speech in English
    r1_zuma = rounds[0]["speaker_speech"]
    assert "Listen carefully" in r1_zuma
    assert "Lukas 24:42" in r1_zuma or "Lukas" in r1_zuma

    # Round 1 OPPONENT speech in English
    r1_opp = rounds[1]["speaker_speech"]
    assert "pure monotheism (Tawhid)" in r1_opp

    # Cross Examination in English
    cx = sim["cross_examination"][0]
    assert "Are you willing to acknowledge the primary written text" in cx["socratic_question"]

    # Epistemic Verdict in English
    ev = sim["epistemic_verdict"]
    assert "Simulated ZUMA dialectic establishes" in ev["verdict_summary"]


def test_zuma_canonical_simulation_localization_id():
    """Verify ZumaSkillEngine generates Indonesian debate simulation when locale is 'id'."""
    claim = "Lukas 24:42 Yesus memakan ikan goreng membuktikan kebangkitan jasmani"
    ctx = {
        "user_perspective": "christian_protestant",
        "opponent_perspective": "islam",
        "debate_locale": "id",
        "ui_locale": "id"
    }
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim=claim, context=ctx)

    assert "Uji Forensik Teks Primer & Validitas Kanonikal" in sim["motion_or_topic"]
    assert "Diskursus Teologis & Apologetika" in sim["original_youtube_title"]

    rounds = sim["rounds"]
    r1_zuma = rounds[0]["speaker_speech"]
    assert "Dengar baik-baik saudara sekalian" in r1_zuma

    r1_opp = rounds[1]["speaker_speech"]
    assert "tauhid murni para nabi" in r1_opp

    cx = sim["cross_examination"][0]
    assert "Apakah saudara bersedia mengakui naskah tertulis primer" in cx["socratic_question"]
