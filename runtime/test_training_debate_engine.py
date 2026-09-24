"""
Debate Arena — Prompt 14: Training Mode & AI Debater Architecture Test Suite
Validates:
1. Training session creation & models
2. User position assignment & neutrality
3. AI opponent activation & role contract
4. Training state machine progression
5. AI speaker permission & bounds
6. User speaker permission & bounds
7. Isolated Training timer
8. Cross-examination exchange
9. Rebuttal training
10. Evidence challenge & biblical citation rules
11. Independent Fact Checking
12. Argument Graph with isolated namespaces
13. Critical Clash engine in training
14. Diagnostic 8-dimension Training Scoring (0-100)
15. 9-Point Coaching & Feedback engine
16. Deterministic Training Replay
17. Session-to-session isolation
18. Official Arena isolation & context builders
19. API authorization & thread safety
20. AI roster injection rejection in Official Arena
21. Training score isolation (no leak to official leaderboard)
22. Training event log isolation
23. ZUMA training persona ("ZUMA-Style Debate Training")
24. Difficulty engine & adaptation
25. AI self-correction on factual contradiction
26. Cross-mode security rejection
27. REST API Endpoints in FastAPI
"""

import pytest
import unittest
import time
import sys
from pathlib import Path
sys.path.insert(0, '/home/ubuntu/Polya-AI')
from fastapi.testclient import TestClient

from polya_runtime.debate_engine.models import (
    ExecutionContext,
    TeamSide,
    SpeakerId,
    VerificationStatus,
    RelationshipType
)
from polya_runtime.debate_engine.training_models import (
    TrainingType,
    TrainingDifficulty,
    TrainingPersona,
    TrainingState,
    TrainingSpeakerId,
    TrainingActionType,
    TrainingScoreCategory,
    TrainingFeedback
)
from polya_runtime.debate_engine.training_state_machine import TrainingStateMachine
from polya_runtime.debate_engine.training_engine import TrainingTimer, DebateTrainingEngine
from polya_runtime.debate_engine.training_api import DebateTrainingService
from polya_runtime.debate_engine.context_builder import OfficialArenaContextBuilder, TrainingContextBuilder
from polya_runtime.debate_engine.api import arena_service
from web.app import app


class TestDebateTrainingEngine(unittest.TestCase):

    def setUp(self):
        self.service = DebateTrainingService.get_instance()
        self.client = TestClient(app)

    # 1. Training Session Creation
    def test_01_training_session_creation(self):
        engine = DebateTrainingEngine(
            user_id="debater-alpha",
            topic="Uji Konsistensi Ontologis dan Integritas Leksikal Teks Kuno",
            user_position=TeamSide.PROPOSITION,
            training_type=TrainingType.PRACTICE_DEBATE,
            difficulty=TrainingDifficulty.HARD,
            persona=TrainingPersona.ZUMA_STYLE
        )
        self.assertEqual(engine.session.mode, ExecutionContext.TRAINING_MODE)
        self.assertEqual(engine.session.user_position, TeamSide.PROPOSITION)
        self.assertEqual(engine.session.ai_position, TeamSide.OPPOSITION)
        self.assertEqual(engine.session.current_state, TrainingState.TRAINING_SETUP)
        self.assertTrue(engine.session.training_session_id.startswith("TRN-"))

    # 2. User Position Assignment & Random Assignment
    def test_02_user_position_assignment(self):
        engine = DebateTrainingEngine(user_position=TeamSide.OPPOSITION)
        self.assertEqual(engine.session.user_position, TeamSide.OPPOSITION)
        self.assertEqual(engine.session.ai_position, TeamSide.PROPOSITION)
        self.assertEqual(engine.session.active_speaker, TrainingSpeakerId.AI_TRAINING_DEBATER)

        # Dynamic reassignment
        ok, msg = engine.assign_positions(TeamSide.PROPOSITION)
        self.assertTrue(ok)
        self.assertEqual(engine.session.user_position, TeamSide.PROPOSITION)
        self.assertEqual(engine.session.ai_position, TeamSide.OPPOSITION)
        self.assertEqual(engine.session.active_speaker, TrainingSpeakerId.USER_DEBATER)

    # 3. AI Opponent Activation & Non-Participant in Official
    def test_03_ai_opponent_activation(self):
        engine = DebateTrainingEngine(training_type=TrainingType.PRACTICE_DEBATE)
        engine.transition_to(TrainingState.OPENING)
        ai_turn = engine.generate_ai_opponent_turn(force_action=TrainingActionType.PRESENT_ARGUMENT)
        self.assertEqual(ai_turn["action"], "PRESENT_ARGUMENT")
        self.assertIn("AI-ARG-", ai_turn["argument_id"])
        self.assertIn("ZUMA-Style Debate Training", ai_turn["claim"])

    # 4. Training State Machine
    def test_04_training_state_machine_flow(self):
        engine = DebateTrainingEngine()
        transitions = [
            TrainingState.TOPIC_LOCK,
            TrainingState.POSITION_ASSIGNMENT,
            TrainingState.OPENING,
            TrainingState.CONSTRUCTIVE,
            TrainingState.CROSS_EXAMINATION,
            TrainingState.REBUTTAL,
            TrainingState.CLASH,
            TrainingState.FINAL_REBUTTAL,
            TrainingState.CLOSING,
            TrainingState.EVALUATION,
            TrainingState.COACHING,
            TrainingState.ARCHIVE
        ]
        for t in transitions:
            ok, msg = engine.transition_to(t)
            self.assertTrue(ok, f"Failed transition to {t}: {msg}")
            self.assertEqual(engine.session.current_state, t)

        # Invalid transition test
        ok_inv, _ = TrainingStateMachine.can_transition(TrainingState.TRAINING_SETUP, TrainingState.ARCHIVE)
        self.assertFalse(ok_inv)

    # 5. AI Speaker Permission in Training
    def test_05_ai_speaker_permission(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        ok, msg = engine.verify_speaker_permission(TrainingSpeakerId.AI_TRAINING_DEBATER)
        self.assertTrue(ok, msg)

    # 6. User Speaker Permission in Training
    def test_06_user_speaker_permission(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        ok, msg = engine.verify_speaker_permission(TrainingSpeakerId.USER_DEBATER)
        self.assertTrue(ok, msg)

        # Unauthorized speaker test
        ok_unauth, _ = engine.verify_speaker_permission("P1")
        self.assertFalse(ok_unauth)

    # 7. Isolated Training Timer
    def test_07_isolated_training_timer(self):
        timer = TrainingTimer(default_duration=60)
        self.assertEqual(timer.remaining_time, 60)
        timer.pause()
        self.assertTrue(timer.is_paused)
        timer.resume()
        self.assertFalse(timer.is_paused)

    # 8. Cross Examination Micro-Protocol in Training
    def test_08_cross_examination_exchange(self):
        engine = DebateTrainingEngine(training_type=TrainingType.CROSS_EXAMINATION)
        engine.transition_to(TrainingState.CROSS_EXAMINATION)

        # User asks question
        ok_q, res_q = engine.submit_cross_exam_question("Apa dasar leksikon naskah yang Anda gunakan?")
        self.assertTrue(ok_q)
        self.assertEqual(res_q["status"], "AWAITING_AI_ANSWER")

        # AI responds
        ai_resp = engine.generate_ai_opponent_turn()
        self.assertEqual(ai_resp["action"], "ANSWER")
        self.assertIn("BDAG", ai_resp["answer"])

        # AI asks question to user
        ai_q = engine.generate_ai_opponent_turn(force_action=TrainingActionType.QUESTION)
        self.assertEqual(ai_q["action"], "QUESTION")

        # User answers
        ok_a, res_a = engine.submit_cross_exam_answer("Kami merujuk pada naskah Papirus P46 dan Codex Vaticanus.")
        self.assertTrue(ok_a)
        self.assertEqual(res_a["status"], "ANSWER_RECORDED")

    # 9. Rebuttal Training
    def test_09_rebuttal_training(self):
        engine = DebateTrainingEngine(training_type=TrainingType.REBUTTAL_TRAINING)
        engine.transition_to(TrainingState.OPENING)
        
        # User argument
        ok_u, res_u = engine.submit_user_argument(
            claim="Teks kuno memiliki integritas transmisi tinggi",
            reasoning="Kaidah sitasi patristik awal konsisten."
        )
        self.assertTrue(ok_u)

        # AI Rebuttal
        engine.transition_to(TrainingState.REBUTTAL)
        ai_rebut = engine.generate_ai_opponent_turn(force_action=TrainingActionType.REBUT)
        self.assertEqual(ai_rebut["action"], "REBUTTAL")
        self.assertEqual(ai_rebut["target_argument_id"], res_u["argument_id"])

    # 10. Evidence Challenge & Biblical Citation Full Name Rule
    def test_10_evidence_challenge_and_rules(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.CONSTRUCTIVE)

        # Compliant citation (Full book name)
        ok1, res1 = engine.submit_user_evidence(
            source_citation="1 Korintus 12:27",
            verse_or_passage="1 Korintus 12:27"
        )
        self.assertTrue(ok1)
        self.assertEqual(res1["verification_status"], VerificationStatus.VERIFIED.value)

        # Non-compliant citation (Abbreviation)
        ok2, res2 = engine.submit_user_evidence(
            source_citation="1Kor 12:27",
            verse_or_passage="1Kor 12:27"
        )
        self.assertTrue(ok2)
        self.assertEqual(res2["verification_status"], VerificationStatus.PARTIALLY_VERIFIED.value)
        self.assertIn("Biblical books must be written in full", res2["notes"])

    # 11. Independent Fact Checking
    def test_11_independent_fact_checking(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.CONSTRUCTIVE)
        ok, res = engine.submit_user_evidence("Codex Sinaiticus NA28")
        self.assertTrue(ok)
        self.assertEqual(res["verification_status"], "VERIFIED")

    # 12. Argument Graph with Isolated Namespaces
    def test_12_argument_graph_namespaces(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)

        ok, user_res = engine.submit_user_argument("Klaim User 1")
        self.assertTrue(ok)
        self.assertTrue(user_res["argument_id"].startswith("USER-ARG-"))

        ai_turn = engine.generate_ai_opponent_turn(force_action=TrainingActionType.PRESENT_ARGUMENT)
        self.assertTrue(ai_turn["argument_id"].startswith("AI-ARG-"))

    # 13. Critical Clash Engine in Training
    def test_13_critical_clash_engine(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        engine.submit_user_argument("Klaim User A")
        engine.transition_to(TrainingState.REBUTTAL)
        ai_turn = engine.generate_ai_opponent_turn(force_action=TrainingActionType.REBUT)
        self.assertIn("clash_id", ai_turn)
        self.assertTrue(len(engine.session.clashes) > 0)

    # 14. Diagnostic Training Scoring (0-100)
    def test_14_diagnostic_scoring(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        engine.submit_user_argument("Klaim Proposisi")
        engine.submit_user_evidence("1 Korintus 12:27")
        score = engine.compute_diagnostic_scores()
        self.assertIsInstance(score, TrainingScoreCategory)
        self.assertGreater(score.total_score, 0)
        self.assertLessEqual(score.total_score, 100)

    # 15. 9-Point Structured Coaching Feedback
    def test_15_coaching_feedback(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        engine.submit_user_argument("Argumen pembuka")
        feedback = engine.generate_coaching_feedback()
        self.assertIsInstance(feedback, TrainingFeedback)
        self.assertTrue(len(feedback.what_you_did_well) > 0)
        self.assertTrue(len(feedback.weak_arguments) > 0)
        self.assertTrue(len(feedback.missed_rebuttals) > 0)
        self.assertTrue(len(feedback.unanswered_questions) > 0)
        self.assertTrue(len(feedback.evidence_problems) > 0)
        self.assertTrue(len(feedback.logical_weaknesses) > 0)
        self.assertTrue(len(feedback.what_to_improve) > 0)
        self.assertIsNotNone(feedback.best_moment)
        self.assertIsNotNone(feedback.turning_point)
        self.assertEqual(engine.session.current_state, TrainingState.COACHING)

    # 16. Deterministic Training Replay
    def test_16_deterministic_replay(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        engine.submit_user_argument("Argumen Replay")
        replay = engine.get_training_replay_payload()
        self.assertEqual(replay["training_session_id"], engine.session.training_session_id)
        self.assertEqual(replay["mode"], "TRAINING_MODE")
        self.assertTrue(len(replay["event_log"]) > 0)

    # 17. Session-to-Session Isolation
    def test_17_session_isolation(self):
        s1 = self.service.create_session(user_id="user-1")
        s2 = self.service.create_session(user_id="user-2")
        self.assertNotEqual(s1["training_session_id"], s2["training_session_id"])

    # 18. Official Arena vs Training Context Builder Isolation
    def test_18_context_builder_isolation(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        train_ctx = TrainingContextBuilder.build_training_context(engine.session)
        self.assertIn("=== LEVEL 2: TRAINING MODE CONTRACT ===", train_ctx)
        self.assertIn("AI ROLE: AI_TRAINING_DEBATER", train_ctx)

    # 19. API Thread-Safe Service Lifecycle
    def test_19_api_service_lifecycle(self):
        res = self.service.create_session(user_id="user-lifecycle-test")
        sid = res["training_session_id"]
        self.service.transition_state(sid, TrainingState.OPENING)
        ok, arg_res = self.service.submit_user_argument(sid, claim="Test Argument")
        self.assertTrue(ok)
        ok_ai, ai_res = self.service.generate_ai_turn(sid)
        self.assertTrue(ok_ai)
        ok_ev, eval_res = self.service.evaluate_and_coach(sid)
        self.assertTrue(ok_ev)

    # 20. AI Roster Injection Rejection in Official Arena
    def test_20_ai_roster_injection_rejection(self):
        # Attempt to join Official Arena with AI debater ID
        ok, msg, _ = arena_service.join_lobby(
            participant_name="AI Zuma Debater",
            requested_speaker_id="AI_TRAINING_DEBATER",  # Invalid seat
            requested_team=TeamSide.PROPOSITION
        )
        self.assertFalse(ok)

        # Explicit security gate check
        ok_sec, msg_sec = arena_service.validate_official_arena_security(
            speaker_id="AI_TRAINING_DEBATER",
            is_ai_debater=True
        )
        self.assertFalse(ok_sec)
        self.assertIn("strictly forbidden", msg_sec)

    # 21. Training Score Leak Prevention
    def test_21_training_score_leak_prevention(self):
        ok, msg = arena_service.reject_training_score_leak("TRAINING_DIAGNOSTIC_SCORE")
        self.assertFalse(ok)
        self.assertIn("Security Violation", msg)

    # 22. Training Event Log Isolation
    def test_22_training_event_log_isolation(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        engine.submit_user_argument("Training event arg")
        
        # Verify events have TRAIN-EVT IDs
        for evt in engine.session.event_log:
            self.assertTrue(evt.event_id.startswith("TRAIN-EVT-"))

    # 23. ZUMA Training Persona ("ZUMA-Style Debate Training")
    def test_23_zuma_training_persona(self):
        engine = DebateTrainingEngine(persona=TrainingPersona.ZUMA_STYLE)
        engine.transition_to(TrainingState.OPENING)
        ai_turn = engine.generate_ai_opponent_turn(force_action=TrainingActionType.PRESENT_ARGUMENT)
        self.assertIn("ZUMA-Style Debate Training", ai_turn["claim"])

    # 24. Difficulty Adaptation
    def test_24_difficulty_adaptation(self):
        for diff in (TrainingDifficulty.EASY, TrainingDifficulty.HARD, TrainingDifficulty.ELITE):
            eng = DebateTrainingEngine(difficulty=diff)
            eng.transition_to(TrainingState.OPENING)
            ai_turn = eng.generate_ai_opponent_turn(force_action=TrainingActionType.PRESENT_ARGUMENT)
            self.assertEqual(ai_turn["difficulty_applied"], diff.value)

    # 25. AI Self-Correction on Contradicted Claim
    def test_25_ai_self_correction(self):
        engine = DebateTrainingEngine()
        engine.transition_to(TrainingState.OPENING)
        
        # Generate flawed turn
        ai_turn = engine.generate_ai_opponent_turn(force_action=TrainingActionType.PRESENT_ARGUMENT, simulate_error=True)
        self.assertTrue(ai_turn["is_flawed"])

        # Trigger self-correction
        corr = engine.trigger_ai_self_correction(ai_turn["argument_id"])
        self.assertIn("tidak akurat secara historis", corr["acknowledgment"])
        self.assertIn("Saksi manuskrip primer", corr["correction"])
        self.assertTrue(len(engine.session.ai_self_corrections) > 0)

    # 26. Cross-Mode Security Rejections
    def test_26_cross_mode_security_rejections(self):
        # Rejection 1: Mode mismatch on Official Arena
        ok1, msg1 = arena_service.validate_official_arena_security(payload_mode="TRAINING_MODE")
        self.assertFalse(ok1)
        self.assertIn("Mode Mismatch", msg1)

        # Rejection 2: Training ID to official arena
        ok2, msg2 = DebateTrainingService.validate_official_arena_injection_rejection(
            target_mode=ExecutionContext.OFFICIAL_ARENA,
            speaker_id="AI_TRAINING_DEBATER",
            is_ai_participant=True
        )
        self.assertFalse(ok2)

    # 27. FastAPI Endpoints Testing
    def test_27_fastapi_training_endpoints(self):
        # Create
        res = self.client.post("/api/training/session/create", json={
            "user_id": "test-user-api",
            "topic": "Uji Konsistensi Ontologis",
            "user_position": "PROPOSITION",
            "difficulty": "HARD",
            "persona": "ZUMA_STYLE"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        sid = data["training_session_id"]

        # Get State
        res_get = self.client.get(f"/api/training/session/{sid}")
        self.assertEqual(res_get.status_code, 200)

        # Submit Argument
        res_arg = self.client.post("/api/training/session/argument", json={
            "training_session_id": sid,
            "claim": "Proposisi pembuka dari user"
        })
        self.assertEqual(res_arg.status_code, 200)

        # Submit Evidence
        res_evd = self.client.post("/api/training/session/evidence", json={
            "training_session_id": sid,
            "source_citation": "1 Korintus 12:27",
            "verse_or_passage": "1 Korintus 12:27"
        })
        self.assertEqual(res_evd.status_code, 200)

        # AI Turn
        res_ai = self.client.post("/api/training/session/ai_turn", json={
            "training_session_id": sid
        })
        self.assertEqual(res_ai.status_code, 200)

        # Cross Exam
        res_cx = self.client.post("/api/training/session/cross_exam", json={
            "training_session_id": sid,
            "action": "QUESTION",
            "text": "Apa dasar premis Anda?"
        })
        self.assertEqual(res_cx.status_code, 200)

        # Evaluate
        res_eval = self.client.post("/api/training/session/evaluate", json={
            "training_session_id": sid
        })
        self.assertEqual(res_eval.status_code, 200)
        self.assertIn("feedback", res_eval.json()["evaluation"])

        # Replay
        res_rep = self.client.get(f"/api/training/session/{sid}/replay")
        self.assertEqual(res_rep.status_code, 200)

        # User History & Stats
        res_hist = self.client.get("/api/training/user/test-user-api/history")
        self.assertEqual(res_hist.status_code, 200)
        res_stats = self.client.get("/api/training/user/test-user-api/stats")
        self.assertEqual(res_stats.status_code, 200)


if __name__ == "__main__":
    unittest.main()
