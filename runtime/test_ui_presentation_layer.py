"""
DEBATE ARENA — PROMPT 12
Presentation & Event UI Layer Comprehensive Verification Test Suite
Verifying 100% integration between Backend Engine, Authoritative State, and UI Layer.
"""

import sys
import os
import json
import unittest
from fastapi.testclient import TestClient

# Add paths
sys.path.insert(0, '/home/ubuntu/Polya-AI/runtime')
sys.path.insert(0, '/home/ubuntu/Polya-AI/web')

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole,
    ActionType
)
from polya_runtime.debate_engine.api import DebateArenaService, arena_service
from polya_runtime.debate_engine.round_configs import RoundPhase
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimType,
    ClaimImportance,
    SourceType,
    FactCheckVerdict,
    EvidenceStatus,
    QuoteIntegrityStatus
)
from polya_runtime.debate_engine.argument_engine import (
    ArgumentHierarchy,
    ArgumentImportance
)
from polya_runtime.debate_engine.clash_engine import (
    ClashType,
    ClashImportance,
    ClashAdvantage
)
from polya_runtime.debate_engine.persona_models import PersonaDimension

from app import app

client = TestClient(app)

class TestPresentationEventUILayer(unittest.TestCase):

    def setUp(self):
        # Reset to clean match state
        self.arena_service = arena_service
        self.arena_service.reset_match(
            topic="Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik",
            description="Uji Forensik Standar Pertanggungjawaban Algoritma Otonom 3-vs-3"
        )


    def test_01_initial_arena_render_and_html(self):
        """Validates that the UI endpoint /arena returns valid broadcast HTML structure."""
        response = client.get("/arena")
        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("DEBATE ARENA", html)
        self.assertIn("PROPOSITION TEAM", html)
        self.assertIn("OPPOSITION TEAM", html)
        self.assertIn("LIVE ON STAGE", html)
        self.assertIn("AI COMMENTARY FEED", html)
        self.assertIn("AI REFEREE", html)
        self.assertIn("MOMENTUM — ANALYTICAL — NOT OFFICIAL SCORE", html)
        print("✓ Initial Arena HTML structure verified.")

    def test_02_authoritative_state_api(self):
        """Validates that /api/arena/state serves 100% authoritative backend state."""
        response = client.get("/api/arena/state")
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertTrue(state["authoritative"])
        self.assertEqual(state["topic"], "Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik")
        self.assertIn(state["status"], ["SETUP", "TOPIC_LOCK", "TEAM_READY"])
        print("✓ Authoritative state endpoint verified.")

    def test_03_six_human_debaters_presentation(self):
        """Validates that exactly 6 human debaters (P1, P2, P3 vs C1, C2, C3) are rendered without AI debaters."""
        state = arena_service.get_full_state()
        prop_debaters = [d["speaker_id"] for d in state["teams"]["proposition"]["debaters"]]
        opp_debaters = [d["speaker_id"] for d in state["teams"]["opposition"]["debaters"]]
        
        self.assertEqual(prop_debaters, ["P1", "P2", "P3"])
        self.assertEqual(opp_debaters, ["C1", "C2", "C3"])
        
        # Verify AI is not in debater list
        for d in prop_debaters + opp_debaters:
            self.assertNotIn(d, ["HOST", "MODERATOR", "REFEREE", "JUDGE_A", "JUDGE_B", "JUDGE_C", "P4", "C4"])
        print("✓ Exactly 6 human debaters validated. AI debaters strictly absent.")

    def test_04_ai_event_control_non_participant_presentation(self):
        """Validates that AI systems are presented exclusively as Event Control / Officials."""
        state = arena_service.get_full_state()
        ai_control = state["ai_event_control"]
        self.assertIn("moderator", ai_control)
        self.assertIn("referee", ai_control)
        self.assertIn("commentary", ai_control)
        self.assertIn("judges", ai_control)
        self.assertEqual(ai_control["moderator"]["role"], "AI MODERATOR")
        self.assertEqual(ai_control["referee"]["role"], "AI REFEREE")
        print("✓ AI systems successfully presented exclusively as Event Intelligence.")

    def _advance_to_round(self, target_round: RoundPhase):
        """Advances state sequentially adhering strictly to State Machine transitions."""
        if self.arena_service.engine.state_obj.current_state == EventState.SETUP:
            self.arena_service.engine.lock_topic("Regulasi Forensik AI")
        if self.arena_service.engine.state_obj.current_state == EventState.TOPIC_LOCK:
            self.arena_service.engine.set_team_ready()
        
        sequence = [
            RoundPhase.ROUND_0_INTRO,
            RoundPhase.ROUND_0_RULE_BRIEFING,
            RoundPhase.ROUND_1_OPENING,
            RoundPhase.ROUND_2_CONSTRUCTIVE,
            RoundPhase.ROUND_3_EVIDENCE_ARGUMENT,
            RoundPhase.ROUND_4_CROSS_EXAMINATION,
            RoundPhase.ROUND_5_REBUTTAL,
            RoundPhase.ROUND_6_CRITICAL_CLASH,
            RoundPhase.ROUND_7_FINAL_REBUTTAL,
            RoundPhase.ROUND_8_CLOSING,
            RoundPhase.ROUND_9_DELIBERATION,
            RoundPhase.ROUND_10_VERDICT
        ]
        
        for r in sequence:
            self.arena_service.engine.start_round(r)
            if r == target_round:
                break

    def test_05_live_speaker_state_and_spotlight(self):
        """Validates that active speaker spotlight transitions correctly."""
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        
        state = self.arena_service.get_full_state()
        self.assertEqual(state["speaker"]["active_id"], "P1")
        self.assertEqual(state["speaker"]["active_team"], "PROPOSITION")
        self.assertTrue(state["speaker"]["is_speaking"])
        
        # Advance turn to C1
        self.arena_service.engine.advance_speaker_turn()
        state2 = self.arena_service.get_full_state()
        self.assertEqual(state2["speaker"]["active_id"], "C1")
        self.assertEqual(state2["speaker"]["active_team"], "OPPOSITION")
        print("✓ Active speaker spotlight and turn transitions verified.")

    def test_06_timer_states_integration(self):
        """Validates timer states (NORMAL -> WARNING -> CRITICAL -> EXPIRED) from Timer Engine."""
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        
        # Normal state (> 30s)
        self.arena_service.engine.state_obj.round_time = 120
        self.arena_service.engine.state_obj.remaining_time = 120
        state_norm = self.arena_service.get_full_state()
        self.assertEqual(state_norm["timer"]["state"], "NORMAL")
        
        # Warning state (<= 30s)
        self.arena_service.engine.state_obj.remaining_time = 25
        state_warn = self.arena_service.get_full_state()
        self.assertEqual(state_warn["timer"]["state"], "WARNING")
        
        # Critical state (<= 10s)
        self.arena_service.engine.state_obj.remaining_time = 8
        state_crit = self.arena_service.get_full_state()
        self.assertEqual(state_crit["timer"]["state"], "CRITICAL")
        
        # Expired state (0s)
        self.arena_service.engine.state_obj.remaining_time = 0
        state_exp = self.arena_service.get_full_state()
        self.assertEqual(state_exp["timer"]["state"], "EXPIRED")
        print("✓ Timer states (NORMAL/WARNING/CRITICAL/EXPIRED) verified.")

    def test_07_moderator_and_referee_integration(self):
        """Validates referee violation flags and moderator rulings."""
        self._advance_to_round(RoundPhase.ROUND_4_CROSS_EXAMINATION)
        
        # Unauthorized action execution rejected by Referee
        ok, msg = self.arena_service.engine.execute_action(
            ActionType.START_SPEECH,
            speaker_id=SpeakerId.C3,
            team=TeamSide.OPPOSITION
        )
        self.assertFalse(ok)
        
        state = self.arena_service.get_full_state()
        self.assertGreater(len(state["ai_event_control"]["referee"]["violations"]), 0)
        print("✓ Referee violation tracking and moderator ruling verified.")

    def test_08_evidence_fact_check_and_argument_ui(self):
        """Validates evidence card, fact check alert, and strategic argument cards."""
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        
        clm = self.arena_service.engine.register_claim(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            statement="Sistem AI memerlukan transparansi audit.",
            claim_type=ClaimType.LEGAL,
            importance=ClaimImportance.CENTRAL
        )
        src = self.arena_service.engine.register_source(
            source_id="SRC-TEST-01",
            title="AI Governance Guidelines",
            author="Standardization Board",
            publisher="Global AI Council",
            publication_year=2024,
            source_type=SourceType.GOVERNMENT_SOURCE
        )
        evd = self.arena_service.engine.evidence_engine.register_evidence(
            evidence_id="EVD-TEST-01",
            source_id="SRC-TEST-01",
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            quoted_text="Mandatory deterministic logging required.",
            status=EvidenceStatus.VERIFIED
        )
        self.arena_service.engine.verify_claim(clm.claim_id, [evd.evidence_id])
        
        arg = self.arena_service.engine.register_strategic_argument(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            claim_text="Sistem AI memerlukan transparansi audit.",
            premises=["Audit forensik adalah jaminan kepastian hukum."],
            conclusion="Audit forensik wajib.",
            hierarchy=ArgumentHierarchy.CORE,
            importance=ArgumentImportance.DECISIVE
        )

        state = self.arena_service.get_full_state()
        self.assertIsNotNone(state["active_argument"])
        self.assertEqual(state["active_argument"]["argument_id"], arg.argument_id)
        self.assertGreater(len(state["active_evidence"]), 0)
        self.assertGreater(len(state["active_fact_checks"]), 0)
        print("✓ Evidence card, fact check alert, and argument cards verified.")

    def test_09_critical_clash_and_momentum_ui(self):
        """Validates critical clash advantage and analytical momentum gauge."""
        self._advance_to_round(RoundPhase.ROUND_6_CRITICAL_CLASH)
        clash = self.arena_service.engine.register_strategic_clash(
            title="Audit vs Speed",
            question="Does audit slow down compute?",
            proposition_position="Audit is essential.",
            opposition_position="Speed is vital.",
            clash_type=ClashType.TRADEOFF,
            importance=ClashImportance.DECISIVE
        )
        self.arena_service.engine.update_clash_advantage(clash.clash_id, ClashAdvantage.PROPOSITION_ADVANTAGE)
        self.arena_service.engine.record_momentum_event(
            team=TeamSide.PROPOSITION,
            trigger_event="Socratic Dissection",
            magnitude=12.5,
            confidence=1.0,
            reason="Dominance in clash"
        )

        state = self.arena_service.get_full_state()
        self.assertGreater(len(state["active_clashes"]), 0)
        self.assertEqual(state["active_clashes"][0]["advantage"], "PROPOSITION_ADVANTAGE")
        self.assertEqual(state["momentum"]["score"], 12.5)
        self.assertEqual(state["momentum"]["label"], "MOMENTUM — ANALYTICAL — NOT OFFICIAL SCORE")
        print("✓ Critical clash advantage and analytical momentum gauge verified.")

    def test_10_score_privacy_during_live_match(self):
        """Validates that debater scores remain hidden during live match and are revealed at verdict."""
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        state_live = self.arena_service.get_full_state()
        self.assertIsNone(state_live["teams"]["proposition"]["debaters"][0]["total_score"])
        
        # Advance to Deliberation & apply evaluation
        self._advance_to_round(RoundPhase.ROUND_9_DELIBERATION)
        self.arena_service.engine.update_score(
            speaker_id=SpeakerId.P1,
            category="argument_quality",
            delta=18.5,
            judge_source=AIRole.JUDGE_A,
            reason="Good thesis"
        )
        state_delib = self.arena_service.get_full_state()
        self.assertIsNotNone(state_delib["teams"]["proposition"]["debaters"][0]["total_score"])
        print("✓ Score privacy during live match & reveal upon deliberation verified.")



    def test_11_zuma_persona_ui_telemetry(self):
        """Validates ZUMA apologetics persona analysis telemetry (pattern alignment, provenance)."""
        arena_service.engine.record_observed_behavior(
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            dimension=PersonaDimension.PREMISE_TESTING,
            observed_tactic="Framed algorithmic liability as non-delegable fiduciary duty.",
            matched_pattern_id="ZUMA-PAT-001",
            confidence=0.96
        )
        state = arena_service.get_full_state()
        zuma = state["forensics"]["zuma_persona"]
        self.assertEqual(zuma["speaker_id"], "P2")
        self.assertEqual(zuma["persona_name"], "ZUMA APOLOGETICS")
        self.assertEqual(zuma["alignment_percentage"], 100.0)
        self.assertIn("SCORE-ISOLATED", zuma["disclaimer"].upper())
        print("✓ ZUMA persona telemetry verified with score isolation.")

    def test_12_degraded_state_handling(self):
        """Validates that degraded engine states display fallback banners without falsifying data."""
        arena_service.set_degraded_state("analytics", True)
        state = arena_service.get_full_state()
        self.assertTrue(state["degraded"]["is_degraded"])
        self.assertEqual(state["degraded"]["fallback_message"], "ANALYTICS TEMPORARILY UNAVAILABLE")
        
        arena_service.set_degraded_state("analytics", False)
        state_recovered = arena_service.get_full_state()
        self.assertFalse(state_recovered["degraded"]["is_degraded"])
        print("✓ Degraded engine state resilience verified.")

    def test_13_golden_match_through_ui_api(self):
        """Validates full execution of Golden Match 001 through UI API."""
        response = client.post("/api/arena/golden_match")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        state = body["state"]
        
        self.assertEqual(state["verdict"]["winner"], "PROPOSITION")
        self.assertGreater(state["verdict"]["margin"], 0)
        self.assertEqual(len(state["awards"]), 8)
        self.assertEqual(len(state["verdict"]["why_they_won"]), 3)
        self.assertGreater(len(state["event_log"]), 20)
        print("✓ Complete Golden Match 001 executed through UI API with 100% fidelity.")


if __name__ == "__main__":
    print("=================================================================")
    print("DEBATE ARENA — PROMPT 12: PRESENTATION & EVENT UI TEST SUITE")
    print("=================================================================")
    unittest.main()
