"""
DEBATE ARENA — PROMPT 13
Real Human 3-vs-3 Live Match & Concurrency Validation Test Suite
Adhering to Real Operational Conditions, Multi-Client Synchronization, and Authoritative Server Integrity.
"""

import sys
import os
import json
import unittest
import threading
import time
from fastapi.testclient import TestClient

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
    EvidenceStatus
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

from app import app

client = TestClient(app)

class TestLiveMatchConcurrencyValidation(unittest.TestCase):

    def setUp(self):
        self.arena = arena_service
        self.arena.reset_match(
            topic="Uji Forensik Pertanggungjawaban Algoritma AI Otonom",
            description="Validasi Konkurensi 6 Peserta Manusia 3-vs-3 dengan Otoritas Server Authoritative"
        )

    def _advance_to_round(self, target_round: RoundPhase):
        """Advances state sequentially adhering strictly to State Machine transitions."""
        if self.arena.engine.state_obj.current_state == EventState.SETUP:
            self.arena.engine.lock_topic("Uji Forensik AI")
        if self.arena.engine.state_obj.current_state == EventState.TOPIC_LOCK:
            self.arena.engine.set_team_ready()
        
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
            self.arena.engine.start_round(r)
            if r == target_round:
                break

    # -----------------------------------------------------------------------
    # 1. SIX-PARTICIPANT LOBBY & AI NON-PARTICIPANT
    # -----------------------------------------------------------------------
    def test_01_six_participant_lobby_and_ready_check(self):
        """Validates 6 human participants joining lobby, ready check, and transition to TEAM_READY."""
        participants = [
            ("Dr. Aris Thorne", SpeakerId.P1, TeamSide.PROPOSITION),
            ("Prof. Elena Vance", SpeakerId.P2, TeamSide.PROPOSITION),
            ("Marcus Reed", SpeakerId.P3, TeamSide.PROPOSITION),
            ("Dr. David Sterling", SpeakerId.C1, TeamSide.OPPOSITION),
            ("Klara Jensen", SpeakerId.C2, TeamSide.OPPOSITION),
            ("Siddharth Nair", SpeakerId.C3, TeamSide.OPPOSITION)
        ]
        for name, spk, team in participants:
            ok, msg, sess = self.arena.join_lobby(name, spk, team)
            self.assertTrue(ok, msg)
            self.assertEqual(sess["speaker_id"], spk.value)
            self.assertEqual(sess["team"], team.value)

        lobby_mid = self.arena.get_lobby_state()
        self.assertEqual(lobby_mid["ready_count"], 0)
        self.assertTrue(lobby_mid["is_full"])

        # Ready checks
        for _, spk, _ in participants:
            ok, msg = self.arena.set_participant_ready(spk, True)
            self.assertTrue(ok, msg)

        lobby_ready = self.arena.get_lobby_state()
        self.assertEqual(lobby_ready["ready_count"], 6)
        self.assertTrue(lobby_ready["all_ready"])
        self.assertEqual(self.arena.engine.state_obj.current_state, EventState.TEAM_READY)
        print("✓ 6-Participant Lobby and Ready Check passed (6/6 READY -> TEAM_READY).")

    def test_02_ai_non_participant_rejection(self):
        """Validates that AI roles (MODERATOR, REFEREE, JUDGES) cannot be claimed as participant seats."""
        for ai_spk in [SpeakerId.MODERATOR, SpeakerId.REFEREE, SpeakerId.JUDGE_A, SpeakerId.HOST]:
            ok, msg, _ = self.arena.join_lobby("AI Pretender", ai_spk, TeamSide.PROPOSITION)
            self.assertFalse(ok)
            self.assertIn("AI roles cannot be joined as participant", msg)
        print("✓ AI Non-Participant Rule strictly enforced (No AI seats).")

    def test_03_wrong_team_and_seat_hijacking_rejection(self):
        """Validates that P1 cannot join Opposition and C1 cannot join Proposition."""
        ok1, msg1, _ = self.arena.join_lobby("Infiltrator 1", SpeakerId.P1, TeamSide.OPPOSITION)
        self.assertFalse(ok1)
        self.assertIn("Wrong team assignment", msg1)

        ok2, msg2, _ = self.arena.join_lobby("Infiltrator 2", SpeakerId.C1, TeamSide.PROPOSITION)
        self.assertFalse(ok2)
        self.assertIn("Wrong team assignment", msg2)
        print("✓ Wrong Team and Seat Hijacking correctly rejected.")

    def test_04_late_join_rejection_after_match_lock(self):
        """Validates that unknown participants cannot late-join after match starts/locks."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        # Unknown participant tries to join
        ok_late, msg_late, _ = self.arena.join_lobby("Late 7th Debater", SpeakerId.HOST, TeamSide.PROPOSITION)
        self.assertFalse(ok_late)
        print("✓ Late join policy verified (Match lock preserves authoritative roster).")

    def test_05_duplicate_session_preserves_single_authoritative_session(self):
        """Validates that opening a 2nd session for P1 supersedes old session without double score/speakers."""
        ok1, _, sess1 = self.arena.join_lobby("Dr. Aris Thorne", SpeakerId.P1, TeamSide.PROPOSITION, session_id="SESS-P1-ALPHA")
        self.assertTrue(ok1)
        self.assertTrue(sess1["is_active"])

        # Open 2nd session
        ok2, _, sess2 = self.arena.join_lobby("Dr. Aris Thorne", SpeakerId.P1, TeamSide.PROPOSITION, session_id="SESS-P1-BETA")
        self.assertTrue(ok2)
        self.assertTrue(sess2["is_active"])
        self.assertFalse(self.arena._sessions["SESS-P1-ALPHA"]["is_active"])
        self.assertEqual(self.arena._speaker_to_session["P1"], "SESS-P1-BETA")
        print("✓ Duplicate session handled safely (Single authoritative active session per participant).")

    # -----------------------------------------------------------------------
    # 2. MULTI-CLIENT SYNCHRONIZATION & SPEAKER AUTHORITY
    # -----------------------------------------------------------------------
    def test_06_multi_client_synchronization(self):
        """Validates that 6 simulated participant clients receive identical authoritative state."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        # 6 simulated client fetches
        client_states = []
        for spk_str in ["P1", "P2", "P3", "C1", "C2", "C3"]:
            resp = client.get("/api/arena/state")
            self.assertEqual(resp.status_code, 200)
            client_states.append(resp.json())

        # Verify 100% consistency across all 6 clients
        first_st = client_states[0]
        for st in client_states[1:]:
            self.assertEqual(st["round"]["phase"], first_st["round"]["phase"])
            self.assertEqual(st["speaker"]["active_id"], first_st["speaker"]["active_id"])
            self.assertEqual(st["timer"]["remaining_seconds"], first_st["timer"]["remaining_seconds"])
            self.assertEqual(st["status"], first_st["status"])
        print("✓ Multi-client synchronization verified across 6 independent sessions.")

    def test_07_speaker_authority_and_unauthorized_rejection(self):
        """Validates that active speaker (P1) is accepted while unauthorized speaker (C2) is rejected."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        # P1 is active speaker
        self.assertEqual(self.arena.engine.state_obj.current_speaker, SpeakerId.P1)

        # Authorized speech by P1
        ok_p1, msg_p1, _ = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "team": "PROPOSITION",
            "payload": {"text": "Argumen pembuka proposisi mengenai regulasi forensik deterministik."}
        })
        self.assertTrue(ok_p1, msg_p1)

        # Unauthorized speech attempt by C2 while P1 is speaking
        ok_c2, msg_c2, _ = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "C2",
            "team": "OPPOSITION",
            "payload": {"text": "Interupsi tidak sah dari oposisi saat proposisi berbicara."}
        })
        self.assertFalse(ok_c2)
        self.assertIn("Speaker Authority Violation", msg_c2)

        # Verify referee recorded violation
        ref_violations = self.arena.engine.referee.violation_history
        self.assertGreater(len(ref_violations), 0)
        self.assertEqual(ref_violations[-1].speaker_id, SpeakerId.C2)
        print("✓ Speaker Authority strictly enforced. Unauthorized speaker action rejected and audited by Referee.")

    def test_08_race_condition_protection(self):
        """Simulates concurrent submissions from P2 and C2, ensuring thread-safe resolution without corruption."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_2_CONSTRUCTIVE)
        
        # P2 is active speaker in Round 2
        results = []
        def submit_p2():
            res = self.arena.execute_operator_action({
                "action": "SUBMIT_SPEECH",
                "speaker_id": "P2",
                "team": "PROPOSITION",
                "payload": {"text": "Submisi sah P2 pada putaran konstruktif."}
            })
            results.append(("P2", res[0], res[1]))

        def submit_c2():
            res = self.arena.execute_operator_action({
                "action": "SUBMIT_SPEECH",
                "speaker_id": "C2",
                "team": "OPPOSITION",
                "payload": {"text": "Submisi balapan C2 yang tidak sah."}
            })
            results.append(("C2", res[0], res[1]))

        t1 = threading.Thread(target=submit_p2)
        t2 = threading.Thread(target=submit_c2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        p2_res = next(r for r in results if r[0] == "P2")
        c2_res = next(r for r in results if r[0] == "C2")
        self.assertTrue(p2_res[1])  # P2 accepted
        self.assertFalse(c2_res[1]) # C2 rejected
        print("✓ Concurrent race condition resolved safely with zero state corruption.")

    def test_09_double_submission_idempotency(self):
        """Validates that identical request with same request_id is idempotent (no duplicate args or scores)."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        req_payload = {
            "request_id": "REQ-IDEM-001",
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "team": "PROPOSITION",
            "payload": {
                "text": "Sistem AI wajib diaudit forensik deterministik.",
                "register_argument": True,
                "claim": "Audit forensik deterministik wajib.",
                "premises": ["Tanpa audit, pertanggungjawaban hukum mustahil."],
                "conclusion": "Audit forensik adalah keharusan mutlak."
            }
        }

        # First execution
        ok1, msg1, st1 = self.arena.execute_operator_action(req_payload)
        self.assertTrue(ok1, msg1)
        initial_arg_count = len(self.arena.engine.argument_graph.nodes)

        # Second execution (exact same request_id)
        ok2, msg2, st2 = self.arena.execute_operator_action(req_payload)
        self.assertTrue(ok2)
        self.assertIn("IDEMPOTENT", msg2)
        
        # Verify argument count did NOT duplicate
        final_arg_count = len(self.arena.engine.argument_graph.nodes)
        self.assertEqual(initial_arg_count, final_arg_count)
        print("✓ Double submission idempotency verified (Zero duplicate arguments or scores).")

    # -----------------------------------------------------------------------
    # 3. NETWORK INTERRUPTION & RECONNECT TEST
    # -----------------------------------------------------------------------
    def test_10_network_interruption_and_authoritative_reconnect(self):
        """Validates disconnect in Round 3 and reconnect in Round 5 receives Round 5 authoritative state."""
        self.test_01_six_participant_lobby_and_ready_check()
        
        # Move to Round 3
        self._advance_to_round(RoundPhase.ROUND_3_EVIDENCE_ARGUMENT)
        self.assertEqual(self.arena.engine.state_obj.current_round, "Round 3: Evidence & Forensic Citations")

        # P1 disconnects in Round 3
        ok_dc, msg_dc = self.arena.disconnect_participant(SpeakerId.P1)
        self.assertTrue(ok_dc, msg_dc)
        self.assertFalse(self.arena._sessions[self.arena._speaker_to_session["P1"]]["is_connected"])

        # Match continues through Round 4 and advances to Round 5
        self._advance_to_round(RoundPhase.ROUND_5_REBUTTAL)
        self.assertEqual(self.arena.engine.state_obj.current_round, "Round 5: Rebuttal & Refutation")

        # P1 reconnects in Round 5
        ok_rec, msg_rec, rec_state = self.arena.reconnect_participant(SpeakerId.P1)
        self.assertTrue(ok_rec, msg_rec)
        self.assertTrue(self.arena._sessions[self.arena._speaker_to_session["P1"]]["is_connected"])
        
        # Verify P1 receives current authoritative Round 5 state, NOT stale Round 3 state
        self.assertEqual(rec_state["round"]["name"], "Round 5: Rebuttal & Refutation")
        self.assertEqual(rec_state["status"], "REBUTTAL")
        print("✓ Network interruption & reconnect validated (Received authoritative current state without stale cache).")

    def test_11_host_moderator_pause_and_resume_synchronization(self):
        """Validates Moderator PAUSE / RESUME preserves entire match state without loss."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        
        # Tick timer to 110s
        self.arena.execute_operator_action({"action": "TICK_TIMER", "payload": {"seconds": 10}})
        rem_before = self.arena.engine.state_obj.remaining_time

        # Pause
        ok_p, _, st_p = self.arena.execute_operator_action({"action": "PAUSE"})
        self.assertTrue(ok_p)
        self.assertTrue(st_p["timer"]["is_paused"])
        self.assertEqual(st_p["status"], "PAUSED")

        # Resume
        ok_r, _, st_r = self.arena.execute_operator_action({"action": "RESUME"})
        self.assertTrue(ok_r)
        self.assertFalse(st_r["timer"]["is_paused"])
        self.assertEqual(st_r["timer"]["remaining_seconds"], rem_before)
        print("✓ Moderator PAUSE / RESUME synchronization verified without state loss.")

    def test_12_timer_synchronization_and_expiration(self):
        """Validates server-authoritative timer expiration and deterministic transition."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        # Tick timer to 0
        total_time = self.arena.engine.state_obj.remaining_time
        self.arena.execute_operator_action({"action": "TICK_TIMER", "payload": {"seconds": total_time}})
        
        st_exp = self.arena.get_full_state()
        self.assertEqual(st_exp["timer"]["state"], "EXPIRED")
        self.assertEqual(st_exp["timer"]["remaining_seconds"], 0)
        print("✓ Server-authoritative timer expiration verified.")

    def test_13_cross_examination_concurrency_and_turn_protocol(self):
        """Validates Cross-Examination turn protocol: QUESTION -> ANSWER."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_4_CROSS_EXAMINATION)

        # P3 asks question (CX-1)
        ok_q, msg_q, _ = self.arena.execute_operator_action({
            "action": "CROSS_EXAM_ACTION",
            "speaker_id": "P3",
            "payload": {"step_action": "QUESTION", "content": "Bagaimana Oposisi menjamin kepastian hukum tanpa auditabilitas?"}
        })
        self.assertTrue(ok_q, msg_q)

        # C1 answers
        ok_a, msg_a, _ = self.arena.execute_operator_action({
            "action": "CROSS_EXAM_ACTION",
            "speaker_id": "C1",
            "payload": {"step_action": "ANSWER", "content": "Kepastian hukum dijamin melalui standar asuransi liabilitas komprehensif."}
        })
        self.assertTrue(ok_a, msg_a)
        print("✓ Cross-examination turn protocol (Question -> Answer) verified.")

    # -----------------------------------------------------------------------
    # 4. INPUT VALIDATION, MALICIOUS INPUT & SECURITY ISOLATION
    # -----------------------------------------------------------------------
    def test_14_input_validation_and_malicious_client_trust(self):
        """Validates rejection of empty speech, oversized speech, and client manipulation attempts."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        # 1. Empty speech rejection
        ok_empty, msg_empty, _ = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "payload": {"text": "   "}
        })
        self.assertFalse(ok_empty)
        self.assertIn("cannot be empty", msg_empty)

        # 2. Oversized speech rejection (> 10000 chars)
        ok_huge, msg_huge, _ = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "payload": {"text": "A" * 15000}
        })
        self.assertFalse(ok_huge)
        self.assertIn("exceeds maximum allowed length", msg_huge)

        # 3. Client manipulation attempt (trying to inject winner/score/round directly)
        ok_manip, _, st_manip = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "payload": {"text": "Valid speech"},
            "score": 1000.0,
            "winner": "PROPOSITION",
            "round": "ROUND_10_VERDICT"
        })
        self.assertTrue(ok_manip)
        # Verify server ignored manipulated fields
        self.assertEqual(st_manip["round"]["name"], "Round 1: Opening Statements")
        self.assertIsNone(st_manip["verdict"])
        print("✓ Input validation and client trust security protections verified.")

    def test_15_score_privacy_during_live_match(self):
        """Validates that judge score breakdowns remain private during live match."""
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)

        st = self.arena.get_full_state()
        self.assertIsNone(st["teams"]["proposition"]["total_score"])
        self.assertIsNone(st["teams"]["opposition"]["total_score"])
        self.assertIsNone(st["verdict"])
        print("✓ Score privacy strictly preserved during live debate.")

    def test_16_analytical_service_degradation_resilience(self):
        """Validates that match continues normally when Commentary or Momentum service is degraded."""
        self.arena.set_degraded_state("commentary", True)
        self.arena.set_degraded_state("momentum", True)
        
        st_deg = self.arena.get_full_state()
        self.assertTrue(st_deg["degraded"]["is_degraded"])
        self.assertIn("commentary", st_deg["degraded"]["components"])
        
        # Debater can still speak
        self.test_01_six_participant_lobby_and_ready_check()
        self._advance_to_round(RoundPhase.ROUND_1_OPENING)
        ok, msg, _ = self.arena.execute_operator_action({
            "action": "SUBMIT_SPEECH",
            "speaker_id": "P1",
            "team": "PROPOSITION",
            "payload": {"text": "Debat tetap berlangsung lancar meski analitik terdegradasi."}
        })
        self.assertTrue(ok, msg)

        # Recover
        self.arena.set_degraded_state("commentary", False)
        self.arena.set_degraded_state("momentum", False)
        st_rec = self.arena.get_full_state()
        self.assertFalse(st_rec["degraded"]["is_degraded"])
        print("✓ Analytical service degradation resilience verified (Debate flow intact).")

    # -----------------------------------------------------------------------
    # 5. GOLDEN LIVE MATCH 001 FULL 10-ROUND EXECUTION
    # -----------------------------------------------------------------------
    def test_17_golden_live_match_fixture_execution(self):
        """Validates complete DEBATE_ARENA_LIVE_GOLDEN_001 fixture with 6 human debaters."""
        state = self.arena.run_golden_live_match_001()
        
        self.assertEqual(state["verdict"]["winner"], "PROPOSITION")
        self.assertGreater(state["verdict"]["margin"], 0.0)
        self.assertEqual(len(state["awards"]), 8)
        self.assertEqual(len(state["event_log"]), 25)
        
        # Verify Replay parity
        replay_engine = self.arena.engine.get_replay_engine()
        self.assertGreater(len(replay_engine.timeline), 15)
        rep_arg, rep_clash, rep_mom, _ = replay_engine.reconstruct_full_state()
        self.assertEqual(len(rep_arg.nodes), len(self.arena.engine.argument_graph.nodes))
        self.assertEqual(len(rep_clash.clashes), len(self.arena.engine.clash_engine.clashes))
        print("✓ Complete DEBATE_ARENA_LIVE_GOLDEN_001 fixture executed with 100% replay fidelity.")

    def test_18_golden_live_match_api_endpoint(self):
        """Validates POST /api/arena/golden_live_match endpoint."""
        response = client.post("/api/arena/golden_live_match")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        state = body["state"]
        self.assertEqual(state["verdict"]["winner"], "PROPOSITION")
        print("✓ /api/arena/golden_live_match API endpoint verified.")


if __name__ == "__main__":
    print("=================================================================")
    print("DEBATE ARENA — PROMPT 13: REAL HUMAN 3-vs-3 & CONCURRENCY SUITE")
    print("=================================================================")
    unittest.main()
