"""
Test Suite for Prompt 16: Official Arena -> Home Integration
Validates that the Official Debate Arena 3-vs-3 is integrated at the top of the Home page (index.html),
above the Social Media Feed, with zero regression on existing backend and feed features.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient

from web.app import app
from polya_runtime.debate_engine.api import arena_service
from polya_runtime.debate_engine.training_api import DebateTrainingService

client = TestClient(app)


def test_home_page_serves_index_html_with_official_arena():
    """Verify GET / returns Home with Official Arena at top and Social Feed below."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # 1. Verify Official Arena presence
    assert 'OFFICIAL ARENA' in html
    assert 'id="arena-section"' in html

    # 2. Verify 6 Human Debaters
    assert 'id="debater-card-P1"' in html
    assert 'id="debater-card-P2"' in html
    assert 'id="debater-card-P3"' in html
    assert 'id="debater-card-C1"' in html
    assert 'id="debater-card-C2"' in html
    assert 'id="debater-card-C3"' in html

    # 3. Verify Team Pods
    assert 'PROPOSITION TEAM' in html
    assert 'OPPOSITION TEAM' in html

    # 4. Verify AI Event Control Components
    assert 'id="roundNameDisplay"' in html
    assert 'id="timerDisplay"' in html
    assert 'id="activeSpeakerPodium"' in html
    assert 'id="refereeViolationsCount"' in html
    assert 'id="activeEvidenceCard"' in html
    assert 'id="factCheckAlert"' in html
    assert 'id="commentaryFeed"' in html
    assert 'id="propMomentumBar"' in html
    assert 'id="oppMomentumBar"' in html

    # 5. Verify Social Media Feed preserved below Arena
    assert 'id="social-feed-section"' in html
    assert 'id="feed-posts-container"' in html
    assert 'id="stories-container"' in html

    # 6. Verify Layout Hierarchy: Arena is ABOVE Social Feed
    arena_pos = html.find('id="arena-section"')
    feed_pos = html.find('id="social-feed-section"')
    assert arena_pos != -1
    assert feed_pos != -1
    assert arena_pos < feed_pos, "Official Arena MUST be located above Social Media Feed"


def test_arena_standalone_view_remains_available():
    """Verify GET /arena continues to serve standalone/debug view."""
    res = client.get("/arena")
    assert res.status_code == 200
    assert 'DEBATE ARENA' in res.text


def test_home_arena_api_state_integration():
    """Verify GET /api/arena/state returns complete authoritative 3-vs-3 state."""
    res = client.get("/api/arena/state")
    assert res.status_code == 200
    state = res.json()

    assert "status" in state
    assert "round" in state
    assert "timer" in state
    assert "speaker" in state
    assert "teams" in state
    assert "ai_event_control" in state
    assert "active_clashes" in state
    assert "momentum" in state
    assert "event_log" in state

    # Verify 6 debater roster
    prop_debaters = state["teams"]["proposition"]["debaters"]
    opp_debaters = state["teams"]["opposition"]["debaters"]
    assert len(prop_debaters) == 3
    assert len(opp_debaters) == 3
    assert [d["speaker_id"] for d in prop_debaters] == ["P1", "P2", "P3"]
    assert [d["speaker_id"] for d in opp_debaters] == ["C1", "C2", "C3"]


def test_home_arena_action_execution_flow():
    """Verify POST /api/arena/action drives match flow synchronously."""
    # Reset
    res_reset = client.post("/api/arena/reset")
    assert res_reset.status_code == 200

    # Start match
    res_start = client.post("/api/arena/action", json={
        "action": "START_MATCH",
        "speaker_id": "P1"
    })
    assert res_start.status_code == 200
    start_state = res_start.json()["state"]
    assert start_state["status"] in ["LIVE_SPEECH", "ACTIVE", "SETUP", "INTRODUCTION"]

    # Submit speech
    res_speech = client.post("/api/arena/action", json={
        "action": "SUBMIT_SPEECH",
        "speaker_id": "P1",
        "payload": {
            "text": "Audit forensik deterministik memastikan transparansi model AI.",
            "register_argument": True
        }
    })
    assert res_speech.status_code == 200
    speech_state = res_speech.json()["state"]
    assert speech_state["speaker"]["active_id"] in ["P1", "HOST"]


def test_golden_match_simulation_e2e():
    """Verify Golden Match simulation generates full 6-turn match and verdict."""
    res = client.post("/api/arena/golden_match")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    state = data["state"]
    assert state["verdict"] is not None
    assert "winner" in state["verdict"]
    assert "why_they_won" in state["verdict"]


def test_social_feed_api_regression():
    """Verify Social Feed endpoints continue to operate without interference."""
    res_feed = client.get("/api/feed?tab=all")
    assert res_feed.status_code == 200
    data = res_feed.json()
    assert "posts" in data
    assert isinstance(data["posts"], list)


def test_mode_isolation_rule_verified():
    """Verify Official Arena does NOT allow AI as debater participant."""
    state = client.get("/api/arena/state").json()
    all_debaters = state["teams"]["proposition"]["debaters"] + state["teams"]["opposition"]["debaters"]
    for d in all_debaters:
        assert not d.get("is_ai", False), "AI debater is strictly prohibited in Official Arena"
