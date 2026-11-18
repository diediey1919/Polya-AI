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

    assert sim["schema_version"] in ("1.0.0", "1.1.0")
    assert "Forensic Primary Text & Canonical Validity Audit" in sim["motion_or_topic"]
    assert "Theological & Apologetics Discourse" in sim["original_youtube_title"]

    rounds = sim["rounds"]
    assert len(rounds) == 16

    # Round 1 ZUMA speech in English
    r1_zuma = rounds[0]["speaker_speech"]
    assert ("Let us examine this topic" in r1_zuma or "Listen carefully" in r1_zuma)
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
    assert ("Mari kita bedah topik ini" in r1_zuma or "Dengar baik-baik saudara sekalian" in r1_zuma)

    r1_opp = rounds[1]["speaker_speech"]
    assert "tauhid murni para nabi" in r1_opp

    cx = sim["cross_examination"][0]
    assert "Apakah saudara bersedia mengakui naskah tertulis primer" in cx["socratic_question"]


def test_zuma_canonical_simulation_localization_ja():
    """Verify ZumaSkillEngine generates localized motion and non-id simulation when locale is 'ja'."""
    claim = "Lukas 24:42 Yesus memakan ikan goreng membuktikan kebangkitan jasmani"
    ctx = {
        "user_perspective": "christian_protestant",
        "opponent_perspective": "islam",
        "debate_locale": "ja",
        "ui_locale": "ja"
    }
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim=claim, context=ctx)
    assert sim["schema_version"] in ("1.0.0", "1.1.0")
    assert "主張に対する原典テキストおよび正典的妥当性の科学的監査" in sim["motion_or_topic"]
    # Verify it does NOT fall back to Indonesian
    assert "Uji Forensik Teks Primer" not in sim["motion_or_topic"]
    assert "Dengar baik-baik saudara sekalian" not in sim["rounds"][0]["speaker_speech"]


def test_index_html_17_languages_dictionary():
    """Verify web/static/index.html contains full 17 languages in I18N_DICTIONARY."""
    index_file = REPO_ROOT / "web" / "static" / "index.html"
    assert index_file.exists()
    content = index_file.read_text(encoding="utf-8")
    
    # Check all 17 canonical codes exist in I18N_DICTIONARY
    for code in ["id", "en", "ar", "es", "pt", "ur", "hi", "fr", "de", "ru", "tr", "fa", "bn", "zh", "ja", "ko", "it"]:
        assert f'"{code}": {{' in content or f'"{code}":' in content, f"Expected {code} in index.html I18N_DICTIONARY"

    # Check key Japanese tokens
    assert "弁証論マシン" in content
    assert "弁証論計算機" in content
    assert "プロテスタント" in content
    assert "カトリック" in content
    assert "イスラム" in content
    assert "ユダヤ教" in content
    assert "無神論 / 世俗主義" in content
    assert "設定が正常に保存されました！" in content


def test_zuma_canonical_simulation_localization_it():
    """Verify ZumaSkillEngine generates Italian simulation with universal role tokens."""
    claim = "Giovanni 10:30 afferma l'unità essenziale del Padre e del Figlio"
    ctx = {
        "user_perspective": "christian_catholic",
        "opponent_perspective": "islam",
        "debate_locale": "it",
        "ui_locale": "it"
    }
    sim = ZumaSkillEngine.generate_canonical_8_round_simulation(claim=claim, context=ctx)
    assert "Audit forense dei testi primari" in sim["motion_or_topic"]

    # Verify participants use universal tokens
    participants = sim.get("participants", [])
    assert len(participants) == 2
    assert participants[0]["name"] == "AFFIRMATIVE_CRITIQUE"
    assert participants[0]["role"] == "AFFIRMATIVE_CRITIQUE"
    assert "manoscritti" in participants[0]["core_stance"].lower()
    assert participants[1]["name"] == "NEGATIVE_DEFENSE"
    assert participants[1]["role"] == "NEGATIVE_DEFENSE"

    # Verify round speeches are in Italian
    r1_zuma = sim["rounds"][0]["speaker_speech"]
    assert "Esaminiamo questo argomento con rigore" in r1_zuma
    r1_opp = sim["rounds"][1]["speaker_speech"]
    assert "Tawhid" in r1_opp or "monoteismo" in r1_opp

    # Verify cross examination
    cx = sim["cross_examination"][0]
    assert cx["examiner"] == "AFFIRMATIVE_CRITIQUE"
    assert cx["target"] == "NEGATIVE_DEFENSE"
    assert "Siete disposti a riconoscere il testo scritto primario" in cx["socratic_question"]

    # Verify verdict summary
    ev = sim["epistemic_verdict"]
    assert "L'addebito dialettico forense dimostra" in ev["verdict_summary"]


def test_exegesis_engine_localization_it_and_en():
    """Verify ExegesisEngine provides CEI for Italian and NIV for English in translation comparison."""
    from orchestrator.exegesis_engine import ExegesisEngine

    # Italian package
    pkg_it = ExegesisEngine.get_canonical_package("Yohanes 1:1", locale="it")
    assert pkg_it is not None
    d_it = pkg_it.model_dump() if hasattr(pkg_it, "model_dump") else dict(pkg_it)
    assert "Nel principio" in d_it["literal_translation"]
    assert "Nel principio sussisteva la Parola" in d_it["natural_translation"]
    versions_it = [c["version"] for c in d_it["translation_comparison"]]
    assert versions_it[0] == "Significato del Greco Koine del I Secolo"
    assert versions_it[1] == "CEI"
    assert "KJV" in versions_it
    assert "ESV" in versions_it

    # English package
    pkg_en = ExegesisEngine.get_canonical_package("Yohanes 1:1", locale="en")
    assert pkg_en is not None
    d_en = pkg_en.model_dump() if hasattr(pkg_en, "model_dump") else dict(pkg_en)
    assert "In the beginning" in d_en["literal_translation"]
    versions_en = [c["version"] for c in d_en["translation_comparison"]]
    assert versions_en[0] == "1st-Century Koine Greek Meaning"
    assert versions_en[1] == "NIV"


def test_canonical_motions_priority_order():
    """Verify that get_corpus_debate_motions sorts the 18 canonical IDs to the top."""
    from web.motion_generator import get_corpus_debate_motions
    motions = get_corpus_debate_motions()
    assert len(motions) >= 18
    canonical_expected = [
        'Rp9118ln4yo', '-97f2FrX5M0', 'lYMnwmwC34w', 'OO_BJpt1NUk', 'W3z8vlpbh_I',
        'ffDYCmZfmxQ', 'QC81ZxksAaI', 'ijHavMINev4', 'evS7T0gijYw', 'La9B66ZZw1s',
        '8v45xJQBV7s', 'zOQn4TYqmBE', 'w1BTZmG-HGo', 'w2tdKAGC2us', 'mMjwLoPx-Is',
        'X3GjCotsHKo', '2hS2F9BPnxI', 'g7mmqv4Y6XE'
    ]
    top_18_ids = [m.get("theme_id") or m.get("id") for m in motions[:18]]
    assert top_18_ids == canonical_expected


def test_index_html_tdz_and_i18n_bindings():
    """Verify index.html has CANONICAL_MOTIONS_I18N before getLocalizedMotion to avoid TDZ error."""
    index_file = REPO_ROOT / "web" / "static" / "index.html"
    content = index_file.read_text(encoding="utf-8")

    idx_canonical = content.find("const CANONICAL_MOTIONS_I18N =")
    idx_func = content.find("function getLocalizedMotion")
    assert idx_canonical != -1, "CANONICAL_MOTIONS_I18N declaration not found"
    assert idx_func != -1, "getLocalizedMotion function not found"
    assert idx_canonical < idx_func, "CANONICAL_MOTIONS_I18N must precede getLocalizedMotion to prevent TDZ error"

    # Verify I18N keys
    assert "speakerAffirmativeCritique" in content
    assert "speakerNegativeDefense" in content
    assert "benchmarkKoineNT" in content
    assert "subMotionPrefix" in content


def test_knowledge_graph_endpoints_localization():
    """Verify /api/v1/knowledge/graph and /claims localize prefixes and text across multiple locales."""
    # 1. English (en)
    res_en = client.get("/api/v1/knowledge/graph?locale=en")
    assert res_en.status_code == 200
    data_en = res_en.json()
    assert data_en["success"] is True
    assert "Paul upholds" in data_en["query"]
    assert any("Premise" in n.get("label", "") and "(Supporting Reason)" in n.get("label", "") for n in data_en["nodes"])
    assert any("Primary Manuscript Witness for" in e.get("description", "") for e in data_en["edges"])

    # 2. Chinese (zh)
    res_zh = client.get("/api/v1/knowledge/graph?locale=zh")
    assert res_zh.status_code == 200
    data_zh = res_zh.json()
    assert data_zh["success"] is True
    assert "保罗坚立摩西律法" in data_zh["query"]
    assert any("前提" in n.get("label", "") and "(支持理由)" in n.get("label", "") for n in data_zh["nodes"])
    assert any("一手手抄本见证" in e.get("description", "") for e in data_zh["edges"])

    # 3. Arabic (ar)
    res_ar = client.get("/api/v1/knowledge/graph?locale=ar")
    assert res_ar.status_code == 200
    data_ar = res_ar.json()
    assert data_ar["success"] is True
    assert "بولس يثبت" in data_ar["query"]
    assert any("مقدمة" in n.get("label", "") and "(سبب داعم)" in n.get("label", "") for n in data_ar["nodes"])
    assert any("شاهد مخطوطة أولية" in e.get("description", "") for e in data_ar["edges"])

    # 4. Claims endpoint Chinese (zh)
    res_claims_zh = client.get("/api/v1/knowledge/claims?q=Paul&locale=zh")
    assert res_claims_zh.status_code == 200
    data_claims_zh = res_claims_zh.json()
    assert data_claims_zh["success"] is True
    assert any(c.get("status") == "核心主张 (辩题)" for c in data_claims_zh["claims"])
    assert any("前提" in c.get("friendly_label", "") and "(支持理由)" in c.get("friendly_label", "") for c in data_claims_zh["claims"])



