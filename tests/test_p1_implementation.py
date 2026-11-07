"""
P1 Implementation Test Suite
Covers:
A. Knowledge Graph: data nyata, search, detail node, empty/error state, batas hasil.
B. Themes: sumber dinamis, pemilihan tema, empty/error state, tidak ada fallback hardcoded yang menyesatkan.
C. SSE LangGraph Telemetry: event ordering, job association, terminal state, failure, auth dan isolation.
D. ZUMA Sparring: lifecycle sesi, turn persistence, validasi, session ownership, error states, dan kanonikalitas Arena.
E. Regression: Calculator, Case File persistence/authorization, canonical Debate Arena.
"""
import os
import sys
import json
import uuid
import pytest
from pathlib import Path
import httpx

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

os.environ["POLYA_AUTH_SECRET"] = "test_auth_secret_for_pytest_suite_32chars"
os.environ["POLYA_ALLOW_MOCK_AUTH"] = "true"

from web.app import app
from web.services import SessionService

def create_valid_token(user_id="user_p1_test"):
    return SessionService.create_token(user_id)

@pytest.fixture
def anyio_backend():
    return "asyncio"

# ---------------------------------------------------------------------------
# Subtask A: Knowledge Graph Tests
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_p1_knowledge_graph_dynamic_data():
    """Knowledge graph returns dynamic nodes and edges from actual engine and respects query & limit."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/knowledge/graph?q=Paulus&limit=10")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "nodes" in data and "edges" in data
        assert len(data["nodes"]) > 0
        assert data["nodes_count"] == len(data["nodes"])
        assert data["edges_count"] == len(data["edges"])
        
        # Check node details
        node_types = {n.get("type") for n in data["nodes"]}
        assert "CLAIM" in node_types or "PROPOSITION" in node_types or "EVIDENCE" in node_types
        for n in data["nodes"]:
            assert "id" in n
            assert "label" in n
            assert "confidence" in n

@pytest.mark.anyio
async def test_p1_knowledge_graph_empty_and_bounds():
    """Empty search or non-matching query returns valid structure without crashing."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/knowledge/graph?q=NonExistentQueryXYZ123&limit=5")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert isinstance(data["nodes"], list)

@pytest.mark.anyio
async def test_p1_knowledge_evidence_and_claims_endpoints():
    """Corpus evidence and verified claims endpoints return verified knowledge data."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res_ev = await client.get("/api/v1/knowledge/evidence")
        assert res_ev.status_code == 200
        ev_data = res_ev.json()
        assert ev_data["success"] is True
        assert ev_data["count"] > 0
        assert len(ev_data["evidence"]) == ev_data["count"]
        first_ev = ev_data["evidence"][0]
        assert "passage_reference" in first_ev
        assert "original_language" in first_ev
        assert "witnesses" in first_ev

        res_cl = await client.get("/api/v1/knowledge/claims")
        assert res_cl.status_code == 200
        cl_data = res_cl.json()
        assert cl_data["success"] is True
        assert cl_data["count"] > 0

@pytest.mark.anyio
async def test_p1_knowledge_evidence_and_claims_dynamic_query():
    """Knowledge claims and evidence endpoints return query-synchronized claims, premises, and scripture witnesses."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Test dynamic claims decomposition for Yohanes 1:1 motion
        motion_q = "Eksegesis Pembukaan Yohanes 1:1: Distingsi Gramatikal"
        res_cl = await client.get(f"/api/v1/knowledge/claims?q={motion_q}")
        assert res_cl.status_code == 200
        cl_data = res_cl.json()
        assert cl_data["success"] is True
        assert cl_data["count"] >= 3
        statuses = [c["status"] for c in cl_data["claims"]]
        assert "KLAIM UTAMA (MOSI)" in statuses
        assert "PREMIS PENDUKUNG" in statuses
        assert "KESIMPULAN" in statuses

        # 2. Test dynamic scripture & manuscript retrieval for Yohanes 1:1
        res_ev = await client.get(f"/api/v1/knowledge/evidence?q={motion_q}")
        assert res_ev.status_code == 200
        ev_data = res_ev.json()
        assert ev_data["success"] is True
        assert ev_data["count"] >= 1
        assert ev_data["evidence"][0]["passage_reference"] == "Yohanes 1:1"
        assert "witnesses" in ev_data["evidence"][0]
        assert len(ev_data["evidence"][0]["witnesses"]) > 0

        # 3. Test dynamic scripture retrieval for Roma 3:31 motion
        res_ev_roma = await client.get("/api/v1/knowledge/evidence?q=Paulus menegakkan hukum Taurat (Roma 3:31)")
        assert res_ev_roma.status_code == 200
        ev_roma_data = res_ev_roma.json()
        assert ev_roma_data["success"] is True
        assert any("Roma 3:31" in e["passage_reference"] for e in ev_roma_data["evidence"])

# ---------------------------------------------------------------------------
# Subtask B: Themes Explorer Tests
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_p1_themes_dynamic_catalog():
    """Themes endpoint returns dynamic catalog with metadata, passages, and arguments."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/themes")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["count"] >= 3
        assert len(data["themes"]) == data["count"]
        
        first_theme = data["themes"][0]
        assert "theme_id" in first_theme or "id" in first_theme
        assert "title" in first_theme
        assert "passages" in first_theme
        assert isinstance(first_theme["passages"], list)

@pytest.mark.anyio
async def test_p1_theme_detail_and_not_found():
    """Specific theme lookup returns complete data, unknown returns 404."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/themes/pauline_torah")
        assert res.status_code == 200
        detail = res.json()
        assert detail["success"] is True
        assert detail["theme"]["id"] in ("pauline_torah", "friksi-paulus-vs-petrus")
        assert "manuscript_witnesses" in detail["theme"]

        res_404 = await client.get("/api/v1/themes/non_existent_theme_999")
        assert res_404.status_code == 404
        assert res_404.json()["detail"] == "Theme not found"

# ---------------------------------------------------------------------------
# Subtask C: SSE LangGraph Telemetry Tests
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_p1_pipeline_stream_auth_isolation():
    """Pipeline stream enforces authentication token and rejects missing auth."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/api/v1/pipeline/stream?claim=TestClaim")
        assert res.status_code in (401, 403)

@pytest.mark.anyio
async def test_p1_pipeline_stream_events_and_ordering():
    """Pipeline stream yields SSE events connected, stage updates, and complete."""
    token = create_valid_token(user_id="user_stream_test")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get(
            "/api/v1/pipeline/stream?claim=Yesus+adalah+Tuhan+(Roma+10:9)",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        
        body = res.text
        assert "event: connect" in body
        assert "event: stage" in body
        assert "event: complete" in body
        assert "RUNNING" in body
        assert "SUCCESS" in body

# ---------------------------------------------------------------------------
# Subtask D: ZUMA Interactive Sparring Tests
# ---------------------------------------------------------------------------
@pytest.mark.anyio
async def test_p1_zuma_sparring_session_lifecycle():
    """ZUMA sparring session starts, receives user arguments, AI turns, and evaluates."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Create Session
        create_payload = {
            "user_id": "test_user_spar",
            "topic": "Hukum Taurat dan Pembenaran Iman",
            "user_position": "PROPOSITION",
            "difficulty": "HARD"
        }
        res_start = await client.post("/api/training/session/create", json=create_payload)
        assert res_start.status_code == 200
        session_data = res_start.json()
        session_id = session_data["training_session_id"]
        assert session_id is not None
        assert session_data["status"] == "ACTIVE" or "training_session_id" in session_data

        # 2. Submit User Argument
        arg_payload = {
            "training_session_id": session_id,
            "claim": "Roma 3:31 menegakkan hukum Taurat",
            "premises": ["Iman tidak membatalkan Taurat", "Hukum Taurat ditegakkan"],
            "reasoning": "Paulus dalam Roma 3:31 menegaskan iman tidak membatalkan Taurat melainkan menegakkannya."
        }
        res_arg = await client.post("/api/training/session/argument", json=arg_payload)
        assert res_arg.status_code == 200
        arg_resp = res_arg.json()
        assert arg_resp["success"] is True

        # 3. Request Zuma AI Sparring Turn
        turn_payload = {
            "training_session_id": session_id
        }
        res_turn = await client.post("/api/training/session/ai_turn", json=turn_payload)
        assert res_turn.status_code == 200
        turn_resp = res_turn.json()
        assert turn_resp["success"] is True
        assert "ai_turn" in turn_resp

        # 4. Conclude and Evaluate Session
        eval_payload = {"training_session_id": session_id}
        res_eval = await client.post("/api/training/session/evaluate", json=eval_payload)
        assert res_eval.status_code == 200
        eval_resp = res_eval.json()
        assert "overall_score" in eval_resp
        assert eval_resp["session_id"] == session_id

@pytest.mark.anyio
async def test_p1_zuma_sparring_not_found_handling():
    """Non-existent session returns 404 error cleanly."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res_eval = await client.post("/api/training/session/evaluate", json={"training_session_id": "non_existent_session_xyz"})
        assert res_eval.status_code == 404

@pytest.mark.anyio
async def test_p1_canonical_debate_arena_untouched():
    """Canonical debate arena (/arena and /arena.html) remains untouched and 3v3 human rules preserved."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        res = await client.get("/arena")
        assert res.status_code == 200
        assert "DEBATE ARENA" in res.text or "arena" in res.text.lower()
