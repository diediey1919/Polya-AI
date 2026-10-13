import json
import os
import sys
import tempfile
import uuid
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure repo root and web dir are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = REPO_ROOT / "web"
ORCHESTRATOR_DIR = REPO_ROOT / "orchestrator"

for p in [str(REPO_ROOT), str(WEB_DIR), str(ORCHESTRATOR_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from web.app import app
from web.models import UserApologeticsContext, UserPerspective, CaseFile
from web.services import CaseFileGenerator, SessionService, init_foundation_db
from orchestrator.evidence_engine import Evidence
from orchestrator.runtime import AgentResponse


@pytest.fixture
def temp_web_db(monkeypatch):
    """Provides an isolated SQLite database for web service tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    init_foundation_db(db_path)
    monkeypatch.setattr("web.services.DB_PATH", db_path)
    try:
        import services
        monkeypatch.setattr(services, "DB_PATH", db_path)
    except Exception:
        pass
    yield db_path
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


@pytest.fixture
def client(temp_web_db):
    """TestClient wired to isolated temporary database."""
    return TestClient(app)


# ============================================================================
# 1. API Mode Contract Tests (Phase 2 & Acceptance Gates)
# ============================================================================

def test_api_mode_contract_valid_research(client):
    """Verify AnalyzeRequest with explicit mode='research' succeeds (HTTP 200)."""
    payload = {
        "claim": "Apakah ada naskah kuno yang mencatat ucapan Yesus?",
        "mode": "research",
        "user_id": "guest_user"
    }
    res = client.post("/api/v1/calculator/analyze", json=payload)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    body = res.json()
    assert body["success"] is True
    assert "case_file" in body
    cf = body["case_file"]
    assert "RESEARCH" in cf["context"]


def test_api_mode_contract_valid_debate(client):
    """Verify AnalyzeRequest with explicit mode='debate' succeeds (HTTP 200)."""
    payload = {
        "claim": "Apakah ada naskah kuno yang mencatat ucapan Yesus?",
        "mode": "debate",
        "user_id": "guest_user"
    }
    res = client.post("/api/v1/calculator/analyze", json=payload)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    body = res.json()
    assert body["success"] is True
    assert "case_file" in body
    cf = body["case_file"]
    assert "DEBATE" in cf["context"]


def test_api_mode_contract_backward_compatibility(client):
    """Verify legacy client omitting mode defaults to 'research' without breaking."""
    payload = {
        "claim": "Apakah ada naskah kuno yang mencatat ucapan Yesus?",
        "user_id": "guest_user"
    }
    res = client.post("/api/v1/calculator/analyze", json=payload)
    assert res.status_code == 200, f"Expected 200 but got {res.status_code}: {res.text}"
    body = res.json()
    assert body["success"] is True
    assert "RESEARCH" in body["case_file"]["context"]


def test_api_mode_contract_invalid_mode_rejected(client):
    """Verify that unsupported/invalid mode strings trigger strict HTTP 422 validation failure."""
    payload = {
        "claim": "Yesus adalah firman",
        "mode": "super_adversarial_invalid_mode",
        "user_id": "guest_user"
    }
    res = client.post("/api/v1/calculator/analyze", json=payload)
    assert res.status_code == 422
    err_detail = str(res.json())
    assert "mode" in err_detail or "Literal" in err_detail


def test_api_mode_contract_empty_claim_rejected(client):
    """Verify that missing required claim produces HTTP 422."""
    payload = {
        "mode": "research",
        "user_id": "guest_user"
    }
    res = client.post("/api/v1/calculator/analyze", json=payload)
    assert res.status_code == 422


# ============================================================================
# 2. SENTINEL TEST: Proof of Model Output Propagation (Acceptance Requirement 2)
# ============================================================================

def test_sentinel_token_model_output_propagation_to_case_file_and_api(client):
    """
    CRITICAL ACCEPTANCE GATE:
    Inject a unique sentinel token into model output that DOES NOT exist in any template.
    Prove that this exact sentinel token flows through:
    1. AgentResponse.output
    2. research_dispatch_node synthesis_output
    3. CaseFileGenerator
    4. HTTP Response JSON from /api/v1/calculator/analyze
    The test will FAIL if the sentinel token is lost or replaced by a static template.
    """
    sentinel_token = f"SENTINEL_AI_PROOF_{uuid.uuid4().hex[:12].upper()}"
    sentinel_payload = {
        "claim_summary": f"SUMMARY_{sentinel_token}",
        "argument": f"ARGUMENT_{sentinel_token}: Analisis dialektis membuktikan kaitan langsung.",
        "counterargument": f"COUNTER_{sentinel_token}: Oposisi mendasarkan premis alternatif.",
        "rebuttal": f"REBUTTAL_{sentinel_token}: Penolakan tegas berdasarkan naskah primer.",
        "weakness": f"WEAKNESS_{sentinel_token}: Celah pada asumsi modern.",
        "open_questions": [f"QUESTION_{sentinel_token}?"],
        "debate_preparation": {
            "cross_examination_trap": f"TRAP_{sentinel_token}: Kunci lawan pada leksikon.",
            "recommended_tempo": f"TEMPO_{sentinel_token}"
        }
    }

    mock_resp = AgentResponse(
        agent_name="hermes",
        status="COMPLETED",
        live_dispatched=True,
        correlation_id=f"cid_{sentinel_token}",
        output=json.dumps(sentinel_payload),
        raw_response=json.dumps(sentinel_payload),
        execution_time_ms=12500,
        timestamp="2026-10-13T00:00:00Z"
    )

    with patch("orchestrator.runtime.AgentRuntimeManager.dispatch", return_value=mock_resp):
        # 1. Test via CaseFileGenerator
        claim_theological = f"Yesus adalah Tuhan dan firman yang hidup {sentinel_token}"
        cf = CaseFileGenerator.generate_case_file(
            claim=claim_theological,
            context=UserApologeticsContext(user_perspective=UserPerspective.CHRISTIAN),
            mode="debate"
        )
        assert f"ARGUMENT_{sentinel_token}" in cf.argument, "Sentinel argument was not propagated to CaseFile.argument!"
        assert f"COUNTER_{sentinel_token}" in cf.counterargument, "Sentinel counterargument was not propagated!"
        assert f"REBUTTAL_{sentinel_token}" in cf.rebuttal, "Sentinel rebuttal was not propagated!"
        assert f"WEAKNESS_{sentinel_token}" in cf.weakness, "Sentinel weakness was not propagated!"
        assert f"TRAP_{sentinel_token}" in cf.debate_preparation["cross_examination_trap"], "Sentinel trap was not propagated!"

        # 2. Test via API /api/v1/calculator/analyze
        res = client.post("/api/v1/calculator/analyze", json={
            "claim": claim_theological,
            "mode": "debate",
            "user_id": "guest_user"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        api_cf = data["case_file"]
        assert f"ARGUMENT_{sentinel_token}" in api_cf["argument"], "Sentinel argument not found in API response!"
        assert f"REBUTTAL_{sentinel_token}" in api_cf["rebuttal"], "Sentinel rebuttal not found in API response!"
        assert "AI_SYNTHESIS_SUCCESS" in api_cf["notice"], "Notice must acknowledge AI synthesis success"


# ============================================================================
# 3. Retrieval & Knowledge Base Tests (Phase 4)
# ============================================================================

def test_retrieval_theological_vs_science_domain_separation():
    """Verify theological claims retrieve evidence, while science claims produce insufficient_evidence."""
    # Claim A: Theological (Jesus Deity)
    res_a = Evidence.retrieve_all_evidence("Yesus tidak pernah secara langsung berkata, 'Aku adalah Tuhan'.")
    assert res_a["status"] == "sufficient"
    assert len(res_a["scripture_evidence"]) >= 1 or len(res_a["corpus_evidence"]) >= 1
    refs_a = [e.passage_reference for e in res_a["scripture_evidence"]]
    assert "Yohanes 10:30" in refs_a

    # Claim B: Theological (Trinity)
    res_b = Evidence.retrieve_all_evidence("Doktrin Tritunggal muncul kemudian dan bukan ajaran asli Yesus.")
    assert res_b["status"] == "sufficient"
    assert len(res_b["corpus_evidence"]) >= 1

    # Claim C: Science (Boiling point of water)
    res_c = Evidence.retrieve_all_evidence("Air mendidih pada 100°C pada tekanan 1 atmosfer.")
    assert res_c["status"] == "insufficient_evidence"
    assert len(res_c["scripture_evidence"]) == 0
    assert len(res_c["corpus_evidence"]) == 0
    assert "di luar domain" in res_c["reason"].lower()

    # Claim D: Out of corpus claim
    res_d = Evidence.retrieve_all_evidence("Spekulasi kosmologi kuantum multi-dimensi tanpa basis naskah kuno XZ99.")
    assert res_d["status"] == "insufficient_evidence"
    assert len(res_d["scripture_evidence"]) == 0
    assert len(res_d["corpus_evidence"]) == 0


def test_no_universal_romans_fallback_on_unrelated_claims():
    """Verify that unrelated theological claims do NOT retrieve Romans 3:31 universally."""
    res_john = Evidence.retrieve_scripture_evidence("Yohanes 10:30 dan hakikat Bapa")
    refs = [e.passage_reference for e in res_john]
    assert "Yohanes 10:30" in refs
    assert "Roma 3:31" not in refs


# ============================================================================
# 4. 4-Claim × 2-Mode End-to-End Tests (Phase 5 & 6)
# ============================================================================

@pytest.mark.parametrize("mode", ["debate", "research"])
def test_e2e_claim_a_jesus_deity(mode):
    """Claim A under Debate and Research modes."""
    claim = "Yesus tidak pernah secara langsung berkata, 'Aku adalah Tuhan'."
    cf = CaseFileGenerator.generate_case_file(
        claim=claim,
        context=UserApologeticsContext(user_perspective=UserPerspective.CHRISTIAN, opponent_perspective="MUSLIM"),
        mode=mode
    )
    assert cf.__class__.__name__ == "CaseFile"
    assert cf.claim == claim
    assert mode.upper() in cf.context
    assert len(cf.evidence) > 0
    assert any("Yohanes 10:30" in e["source_text"] for e in cf.evidence)
    assert "Paulus membatalkan Taurat" not in cf.argument
    assert "hukum Taurat" not in cf.counterargument.lower() or "tuhan" in cf.counterargument.lower()
    assert "DEMO / MOCK DATA" not in cf.notice


@pytest.mark.parametrize("mode", ["debate", "research"])
def test_e2e_claim_b_trinity(mode):
    """Claim B under Debate and Research modes."""
    claim = "Doktrin Tritunggal muncul kemudian dan bukan ajaran asli Yesus."
    cf = CaseFileGenerator.generate_case_file(
        claim=claim,
        context=UserApologeticsContext(user_perspective=UserPerspective.CHRISTIAN, opponent_perspective="ISLAMIC_COMPARATIVE"),
        mode=mode
    )
    assert cf.__class__.__name__ == "CaseFile"
    assert cf.claim == claim
    assert mode.upper() in cf.context
    assert len(cf.sources) > 0
    assert "Paulus membatalkan Taurat" not in cf.argument
    assert "DEMO / MOCK DATA" not in cf.notice


@pytest.mark.parametrize("mode", ["debate", "research"])
def test_e2e_claim_c_science_not_forced_to_scripture(mode):
    """Claim C: Science claim must result in transparent insufficient evidence notice and zero forced scripture."""
    claim = "Air mendidih pada 100°C pada tekanan 1 atmosfer."
    cf = CaseFileGenerator.generate_case_file(
        claim=claim,
        context=UserApologeticsContext(),
        mode=mode
    )
    assert cf.__class__.__name__ == "CaseFile"
    assert cf.claim == claim
    assert mode.upper() in cf.context
    assert len(cf.evidence) == 0
    assert len(cf.sources) == 0
    assert "INSUFFICIENT_EVIDENCE" in cf.notice
    assert "DEMO / MOCK DATA" not in cf.notice


@pytest.mark.parametrize("mode", ["debate", "research"])
def test_e2e_claim_d_out_of_corpus(mode):
    """Claim D: Out-of-corpus claim must result in insufficient evidence notice."""
    claim = "Spekulasi kosmologi kuantum multi-dimensi tanpa basis naskah kuno XZ99."
    cf = CaseFileGenerator.generate_case_file(
        claim=claim,
        context=UserApologeticsContext(),
        mode=mode
    )
    assert cf.__class__.__name__ == "CaseFile"
    assert cf.claim == claim
    assert mode.upper() in cf.context
    assert len(cf.evidence) == 0
    assert len(cf.sources) == 0
    assert "INSUFFICIENT_EVIDENCE" in cf.notice


# ============================================================================
# 5. Error Handling & Resilience Tests (Phase 3 & 5)
# ============================================================================

def test_model_timeout_handled_gracefully():
    """Verify that when agent dispatch times out, status is MODEL_ERROR without crashing."""
    timeout_resp = AgentResponse(
        agent_name="hermes",
        status="TIMEOUT",
        live_dispatched=False,
        correlation_id="err_to_123",
        output="",
        raw_response=None,
        execution_time_ms=60000,
        timestamp="2026-10-13T00:00:00Z",
        error="Hermes invocation timed out"
    )

    with patch("orchestrator.runtime.AgentRuntimeManager.dispatch", return_value=timeout_resp):
        cf = CaseFileGenerator.generate_case_file(
            claim="Yesus adalah Tuhan",
            context=UserApologeticsContext(),
            mode="research"
        )
        assert cf.__class__.__name__ == "CaseFile"
        assert "MODEL_ERROR" in cf.notice or "PARTIAL" in cf.notice
        assert "DEMO / MOCK DATA" not in cf.notice


def test_model_malformed_json_handled_as_partial():
    """Verify that malformed JSON from model is captured as PARTIAL synthesis without crash."""
    malformed_resp = AgentResponse(
        agent_name="hermes",
        status="COMPLETED",
        live_dispatched=True,
        correlation_id="test_malformed_123",
        output="I cannot provide JSON right now, but here is my unstructured answer.",
        raw_response="...",
        execution_time_ms=12000,
        timestamp="2026-10-13T00:00:00Z"
    )

    with patch("orchestrator.runtime.AgentRuntimeManager.dispatch", return_value=malformed_resp):
        cf = CaseFileGenerator.generate_case_file(
            claim="Yesus adalah Tuhan",
            context=UserApologeticsContext(),
            mode="debate"
        )
        assert cf.__class__.__name__ == "CaseFile"
        assert "PARTIAL" in cf.notice
        assert cf.argument != ""
        assert "DEMO / MOCK DATA" not in cf.notice


def test_session_isolation_no_leakage():
    """Verify two sequential analyses with different perspectives do not contaminate context."""
    cf1 = CaseFileGenerator.generate_case_file(
        claim="Yesus adalah firman",
        context=UserApologeticsContext(user_perspective=UserPerspective.CHRISTIAN, opponent_perspective="JEWISH"),
        user_id="user_alpha",
        mode="debate"
    )
    cf2 = CaseFileGenerator.generate_case_file(
        claim="Air mendidih pada 100°C",
        context=UserApologeticsContext(user_perspective=UserPerspective.ISLAM, opponent_perspective="ATHEIST"),
        user_id="user_beta",
        mode="research"
    )

    assert "CHRISTIAN" in cf1.context
    assert "JEWISH" in cf1.context
    assert "DEBATE" in cf1.context

    assert "ISLAM" in cf2.context
    assert "ATHEIST" in cf2.context
    assert "RESEARCH" in cf2.context
    assert cf1.case_id != cf2.case_id
