"""
Debate Arena - Training Service & API Bridge (Prompt 14)
Manages training session instances, thread-safe mutations, and cross-mode security boundaries.
"""

from typing import Dict, List, Optional, Any, Tuple
import threading
import time
import logging

from polya_runtime.debate_engine.models import (
    ExecutionContext,
    TeamSide,
    SpeakerId
)
from polya_runtime.debate_engine.training_models import (
    TrainingType,
    TrainingDifficulty,
    TrainingPersona,
    TrainingState,
    TrainingSpeakerId,
    TrainingActionType,
    TrainingSessionObject,
    TrainingFeedback,
    TrainingAchievement,
    TrainingCurriculum
)
from polya_runtime.debate_engine.training_engine import DebateTrainingEngine

logger = logging.getLogger("polya.training_api")

class DebateTrainingService:
    """Thread-safe manager for all active Human vs AI Debate Training sessions."""

    _instance: Optional['DebateTrainingService'] = None
    _lock = threading.RLock()

    def __init__(self):
        self._sessions: Dict[str, DebateTrainingEngine] = {}
        self._user_sessions: Dict[str, List[str]] = {}

    @classmethod
    def get_instance(cls) -> 'DebateTrainingService':
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    # -----------------------------------------------------------------------
    # Session Lifecycle & Security Guard
    # -----------------------------------------------------------------------

    def create_session(
        self,
        user_id: str = "user-default",
        topic: str = "Uji Konsistensi Ontologis dan Integritas Leksikal Teks Kuno",
        topic_description: str = "Sesi latihan dialektika dan pembuktian forensik melawan AI Debater",
        user_position: TeamSide = TeamSide.PROPOSITION,
        training_type: TrainingType = TrainingType.PRACTICE_DEBATE,
        difficulty: TrainingDifficulty = TrainingDifficulty.NORMAL,
        persona: TrainingPersona = TrainingPersona.ZUMA_STYLE
    ) -> Dict[str, Any]:
        with self._lock:
            engine = DebateTrainingEngine(
                user_id=user_id,
                topic=topic,
                topic_description=topic_description,
                user_position=user_position,
                training_type=training_type,
                difficulty=difficulty,
                persona=persona
            )
            session_id = engine.session.training_session_id
            self._sessions[session_id] = engine

            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)

            logger.info(f"[Training API] Created training session {session_id} for user {user_id} in mode {engine.session.mode.value}")
            return {
                "status": "CREATED",
                "training_session_id": session_id,
                "mode": engine.session.mode.value,
                "topic": topic,
                "user_position": user_position.value,
                "ai_position": engine.session.ai_position.value,
                "training_type": training_type.value,
                "difficulty": difficulty.value,
                "persona": persona.value,
                "current_state": engine.session.current_state.value
            }

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return None
            engine.timer.tick()
            self._sync_session_timer(engine)
            return engine.session.model_dump()

    def _sync_session_timer(self, engine: DebateTrainingEngine):
        engine.session.remaining_time = engine.timer.remaining_time
        engine.session.is_paused = engine.timer.is_paused

    # -----------------------------------------------------------------------
    # Interactive Actions
    # -----------------------------------------------------------------------

    def transition_state(self, session_id: str, target_state: TrainingState, round_name: Optional[str] = None) -> Tuple[bool, str]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, f"Session {session_id} not found."
            return engine.transition_to(target_state, round_name)

    def submit_user_argument(
        self,
        session_id: str,
        claim: str,
        premises: Optional[List[str]] = None,
        reasoning: str = "",
        impact: str = "",
        target_argument_id: Optional[str] = None,
        is_hypothetical: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            return engine.submit_user_argument(
                claim=claim,
                premises=premises,
                reasoning=reasoning,
                impact=impact,
                target_argument_id=target_argument_id,
                is_hypothetical=is_hypothetical
            )

    def submit_user_evidence(
        self,
        session_id: str,
        source_citation: str,
        source_type: str = "ACADEMIC_SOURCE",
        verse_or_passage: Optional[str] = None,
        is_hypothetical: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            return engine.submit_user_evidence(
                source_citation=source_citation,
                source_type=source_type,
                verse_or_passage=verse_or_passage,
                is_hypothetical=is_hypothetical
            )

    def submit_cross_exam_question(self, session_id: str, question: str) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            return engine.submit_cross_exam_question(question)

    def submit_cross_exam_answer(self, session_id: str, answer: str) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            return engine.submit_cross_exam_answer(answer)

    def generate_ai_turn(
        self,
        session_id: str,
        force_action: Optional[TrainingActionType] = None,
        simulate_error: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            try:
                payload = engine.generate_ai_opponent_turn(force_action=force_action, simulate_error=simulate_error)
                return True, payload
            except Exception as e:
                logger.error(f"Error generating AI turn: {e}", exc_info=True)
                return False, {"error": str(e)}

    def trigger_ai_self_correction(self, session_id: str, contradicted_claim_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            corr = engine.trigger_ai_self_correction(contradicted_claim_id)
            return True, corr

    def evaluate_and_coach(self, session_id: str) -> Tuple[bool, Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return False, {"error": f"Session {session_id} not found."}
            feedback = engine.generate_coaching_feedback()
            achievements = engine.evaluate_training_achievements()
            curriculum = engine.generate_curriculum_plan()
            return True, {
                "feedback": feedback.model_dump(),
                "score": engine.session.user_score.model_dump(),
                "achievements": [a.model_dump() for a in achievements],
                "curriculum": curriculum.model_dump()
            }

    def get_training_replay(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            engine = self._sessions.get(session_id)
            if not engine:
                return None
            return engine.get_training_replay_payload()

    # -----------------------------------------------------------------------
    # User Profile, History, Stats & Curriculum
    # -----------------------------------------------------------------------

    def get_user_training_history(self, user_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            session_ids = self._user_sessions.get(user_id, [])
            history = []
            for sid in session_ids:
                eng = self._sessions.get(sid)
                if eng:
                    history.append({
                        "training_session_id": sid,
                        "topic": eng.session.topic,
                        "training_type": eng.session.training_type.value,
                        "difficulty": eng.session.difficulty.value,
                        "persona": eng.session.persona.value,
                        "user_position": eng.session.user_position.value,
                        "is_completed": eng.session.is_completed,
                        "final_score": eng.session.user_score.total_score,
                        "created_at": eng.session.created_at
                    })
            return history

    def get_user_training_stats(self, user_id: str) -> Dict[str, Any]:
        with self._lock:
            session_ids = self._user_sessions.get(user_id, [])
            if not session_ids:
                return {
                    "sessions_completed": 0,
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "weakest_category": "None",
                    "strongest_category": "None",
                    "improvement_rate": "0.0%"
                }

            scores = []
            for sid in session_ids:
                eng = self._sessions.get(sid)
                if eng and eng.session.is_completed:
                    scores.append(eng.session.user_score.total_score)

            if not scores:
                return {
                    "sessions_completed": len(session_ids),
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "weakest_category": "In Progress",
                    "strongest_category": "In Progress",
                    "improvement_rate": "0.0%"
                }

            avg_score = round(sum(scores) / len(scores), 1)
            best_score = round(max(scores), 1)

            return {
                "sessions_completed": len(scores),
                "average_score": avg_score,
                "best_score": best_score,
                "weakest_category": "Evidence Citation Precision",
                "strongest_category": "Logical Reasoning",
                "improvement_rate": f"+{min(25.0, len(scores) * 4.5):.1f}%"
            }

    # -----------------------------------------------------------------------
    # Cross-Mode Security Verification Gate (Section 28, 29, 42)
    # -----------------------------------------------------------------------

    @staticmethod
    def validate_official_arena_injection_rejection(
        target_mode: ExecutionContext,
        speaker_id: str,
        is_ai_participant: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates security barrier between Official Arena and Training Mode.
        Guarantees that AI Debater or Training IDs are STRICTLY REJECTED from Official Arena.
        """
        if target_mode == ExecutionContext.OFFICIAL_ARENA:
            if is_ai_participant or speaker_id in (
                TrainingSpeakerId.AI_TRAINING_DEBATER.value,
                TrainingSpeakerId.TRAINING_EXAMINER.value,
                TrainingSpeakerId.USER_DEBATER.value,
                "AI_TRAINING_DEBATER"
            ):
                return False, "Security Violation: AI debater and training identities are strictly forbidden in OFFICIAL_ARENA."

        return True, "Security validation passed."
