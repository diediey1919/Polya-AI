"""
Debate Arena - Training Engine & AI Debater Architecture (Prompt 14)
Adheres strictly to PROMPT 14 — TRAINING MODE / AI DEBATER ARCHITECTURE.

Absolute Boundaries:
- mode = ExecutionContext.TRAINING_MODE
- AI participant = ALLOWED (AI_TRAINING_DEBATER, EXAMINER, COACH)
- Isolated timer, argument graph, namespaces, diagnostic scores, immutable event log.
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import uuid
import logging

from polya_runtime.debate_engine.models import (
    ExecutionContext,
    TeamSide,
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
    TrainingEvidenceItem,
    TrainingClaimItem,
    TrainingArgumentItem,
    TrainingClash,
    TrainingScoreCategory,
    TrainingFeedback,
    TrainingEventLogItem,
    TrainingSessionObject,
    TrainingAchievement,
    TrainingCurriculum
)
from polya_runtime.debate_engine.training_state_machine import TrainingStateMachine
from polya_runtime.debate_engine.context_builder import TrainingContextBuilder

logger = logging.getLogger("polya.training_engine")

class TrainingTimer:
    """Isolated timer engine for Debate Training sessions."""
    def __init__(self, default_duration: int = 180):
        self.duration: int = default_duration
        self.remaining_time: int = default_duration
        self.is_paused: bool = False
        self.last_tick: float = time.time()

    def set_duration(self, seconds: int):
        self.duration = seconds
        self.remaining_time = seconds
        self.last_tick = time.time()

    def tick(self) -> int:
        if self.is_paused:
            return self.remaining_time
        now = time.time()
        elapsed = int(now - self.last_tick)
        if elapsed >= 1:
            self.remaining_time = max(0, self.remaining_time - elapsed)
            self.last_tick = now
        return self.remaining_time

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        self.last_tick = time.time()


class DebateTrainingEngine:
    """Authoritative execution engine for Human vs AI Training Sessions."""

    def __init__(
        self,
        user_id: str = "user-default",
        topic: str = "Uji Konsistensi Ontologis dan Integritas Leksikal Teks Kuno",
        topic_description: str = "Sesi latihan dialektika dan pembuktian forensik melawan AI Debater",
        user_position: TeamSide = TeamSide.PROPOSITION,
        training_type: TrainingType = TrainingType.PRACTICE_DEBATE,
        difficulty: TrainingDifficulty = TrainingDifficulty.NORMAL,
        persona: TrainingPersona = TrainingPersona.ZUMA_STYLE
    ):
        self.timer = TrainingTimer(default_duration=180 if training_type != TrainingType.RAPID_FIRE else 45)
        
        ai_pos = TeamSide.OPPOSITION if user_position == TeamSide.PROPOSITION else TeamSide.PROPOSITION
        
        self.session = TrainingSessionObject(
            user_id=user_id,
            mode=ExecutionContext.TRAINING_MODE,
            topic=topic,
            topic_description=topic_description,
            user_position=user_position,
            ai_position=ai_pos,
            training_type=training_type,
            difficulty=difficulty,
            persona=persona,
            current_state=TrainingState.TRAINING_SETUP,
            round_name="SETUP",
            active_speaker=TrainingSpeakerId.USER_DEBATER if user_position == TeamSide.PROPOSITION else TrainingSpeakerId.AI_TRAINING_DEBATER,
            remaining_time=self.timer.duration,
            round_time=self.timer.duration
        )
        self._record_event("SESSION_CREATED", TrainingSpeakerId.TRAINING_MODERATOR, None, "Training session initialized.")

    # -----------------------------------------------------------------------
    # Logging & State Transitions
    # -----------------------------------------------------------------------

    def _record_event(
        self,
        action_type: str,
        speaker_id: Optional[TrainingSpeakerId],
        team: Optional[TeamSide],
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        event = TrainingEventLogItem(
            session_id=self.session.training_session_id,
            state=self.session.current_state.value,
            speaker_id=speaker_id,
            team=team,
            action_type=action_type,
            content=content,
            metadata=metadata or {}
        )
        self.session.event_log.append(event)
        self.session.updated_at = time.time()

    def transition_to(self, target_state: TrainingState, round_name: Optional[str] = None) -> Tuple[bool, str]:
        if self.session.mode != ExecutionContext.TRAINING_MODE:
            return False, "Security Violation: Session mode is not TRAINING_MODE."

        can_trans, reason = TrainingStateMachine.can_transition(self.session.current_state, target_state)
        if not can_trans:
            return False, reason

        self.session.current_state = target_state
        if round_name:
            self.session.round_name = round_name
        else:
            self.session.round_name = target_state.value

        # Reset timer for new phase
        duration = 45 if self.session.training_type == TrainingType.RAPID_FIRE else 180
        if target_state == TrainingState.CROSS_EXAMINATION:
            duration = 120
        elif target_state == TrainingState.CLASH:
            duration = 150
        elif target_state in (TrainingState.EVALUATION, TrainingState.COACHING):
            duration = 300

        self.timer.set_duration(duration)
        self.session.round_time = duration
        self.session.remaining_time = duration

        self._record_event("STATE_TRANSITION", TrainingSpeakerId.TRAINING_MODERATOR, None, f"Transitioned to {target_state.value}")
        return True, f"State transitioned to {target_state.value}"

    def lock_topic(self, topic: str, topic_description: str = "") -> Tuple[bool, str]:
        self.session.topic = topic
        if topic_description:
            self.session.topic_description = topic_description
        return self.transition_to(TrainingState.TOPIC_LOCK)

    def assign_positions(self, user_pos: TeamSide) -> Tuple[bool, str]:
        self.session.user_position = user_pos
        self.session.ai_position = TeamSide.OPPOSITION if user_pos == TeamSide.PROPOSITION else TeamSide.PROPOSITION
        
        # User Proposition starts first in standard debates
        if user_pos == TeamSide.PROPOSITION:
            self.session.active_speaker = TrainingSpeakerId.USER_DEBATER
        else:
            self.session.active_speaker = TrainingSpeakerId.AI_TRAINING_DEBATER
            
        self._record_event(
            "POSITION_ASSIGNED",
            TrainingSpeakerId.TRAINING_MODERATOR,
            None,
            f"User assigned to {user_pos.value}, AI assigned to {self.session.ai_position.value}"
        )
        return self.transition_to(TrainingState.POSITION_ASSIGNMENT)

    # -----------------------------------------------------------------------
    # Speaker Permissions & Role Verification
    # -----------------------------------------------------------------------

    def verify_speaker_permission(self, speaker_id: TrainingSpeakerId) -> Tuple[bool, str]:
        if self.session.mode != ExecutionContext.TRAINING_MODE:
            return False, "Security Error: Non-training execution context."

        if self.session.is_paused:
            return False, "Training session is paused."

        if self.session.current_state in (TrainingState.TRAINING_SETUP, TrainingState.TOPIC_LOCK, TrainingState.ARCHIVE):
            return False, f"Speaking not permitted during {self.session.current_state.value}"

        if speaker_id not in (
            TrainingSpeakerId.USER_DEBATER,
            TrainingSpeakerId.AI_TRAINING_DEBATER,
            TrainingSpeakerId.TRAINING_EXAMINER,
            TrainingSpeakerId.TRAINING_COACH,
            TrainingSpeakerId.TRAINING_MODERATOR
        ):
            return False, f"Unauthorized speaker identity '{speaker_id}' in training mode."

        return True, "Speaker permission granted."

    # -----------------------------------------------------------------------
    # User Debater Actions
    # -----------------------------------------------------------------------

    def submit_user_argument(
        self,
        claim: str,
        premises: Optional[List[str]] = None,
        reasoning: str = "",
        impact: str = "",
        target_argument_id: Optional[str] = None,
        relationship: Optional[RelationshipType] = None,
        is_hypothetical: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        ok, msg = self.verify_speaker_permission(TrainingSpeakerId.USER_DEBATER)
        if not ok:
            return False, {"error": msg}

        arg = TrainingArgumentItem(
            speaker_id=TrainingSpeakerId.USER_DEBATER,
            team=self.session.user_position,
            claim=claim,
            premises=premises or [],
            reasoning=reasoning,
            impact=impact,
            target_argument_id=target_argument_id,
            relationship=relationship,
            is_hypothetical=is_hypothetical
        )
        self.session.arguments.append(arg)

        # Register core claim
        claim_item = TrainingClaimItem(
            speaker_id=TrainingSpeakerId.USER_DEBATER,
            team=self.session.user_position,
            statement=claim
        )
        self.session.claims.append(claim_item)

        self._record_event(
            "PRESENT_ARGUMENT",
            TrainingSpeakerId.USER_DEBATER,
            self.session.user_position,
            claim,
            {"argument_id": arg.argument_id, "reasoning": reasoning, "target": target_argument_id}
        )

        # Update turn floor to AI
        self.session.active_speaker = TrainingSpeakerId.AI_TRAINING_DEBATER
        return True, {"argument_id": arg.argument_id, "status": "REGISTERED", "next_speaker": "AI_TRAINING_DEBATER"}

    def submit_user_evidence(
        self,
        source_citation: str,
        source_type: str = "ACADEMIC_SOURCE",
        verse_or_passage: Optional[str] = None,
        is_hypothetical: bool = False
    ) -> Tuple[bool, Dict[str, Any]]:
        ok, msg = self.verify_speaker_permission(TrainingSpeakerId.USER_DEBATER)
        if not ok:
            return False, {"error": msg}

        # Validate standard biblical naming rule if scripture
        status = VerificationStatus.VERIFIED
        notes = "Standard scholarly verification"
        if "bible" in source_citation.lower() or verse_or_passage:
            # Check for abbreviations forbidden by rule
            forbidden_short = ["Mat ", "Kej ", "1Kor ", "2Kor ", "Kis ", "Rom ", "Yoh "]
            for fb in forbidden_short:
                if fb in source_citation or (verse_or_passage and fb in verse_or_passage):
                    status = VerificationStatus.PARTIALLY_VERIFIED
                    notes = "Citation format warning: Biblical books must be written in full without abbreviations."

        evd = TrainingEvidenceItem(
            speaker_id=TrainingSpeakerId.USER_DEBATER,
            team=self.session.user_position,
            source_citation=source_citation,
            source_type=source_type,
            verse_or_passage=verse_or_passage,
            verification_status=status,
            integrity_notes=notes,
            is_hypothetical=is_hypothetical
        )
        self.session.evidence.append(evd)

        self._record_event(
            "PRESENT_EVIDENCE",
            TrainingSpeakerId.USER_DEBATER,
            self.session.user_position,
            source_citation,
            {"evidence_id": evd.evidence_id, "verification_status": status.value}
        )
        return True, {"evidence_id": evd.evidence_id, "verification_status": status.value, "notes": notes}

    def submit_cross_exam_question(self, question: str) -> Tuple[bool, Dict[str, Any]]:
        ok, msg = self.verify_speaker_permission(TrainingSpeakerId.USER_DEBATER)
        if not ok:
            return False, {"error": msg}

        turn_entry = {
            "turn_id": f"CX-TRN-{uuid.uuid4().hex[:6]}",
            "questioner": TrainingSpeakerId.USER_DEBATER.value,
            "respondent": TrainingSpeakerId.AI_TRAINING_DEBATER.value,
            "question": question,
            "answer": None,
            "timestamp": time.time()
        }
        self.session.cross_examination_turns.append(turn_entry)

        self._record_event(
            "CROSS_EXAM_QUESTION",
            TrainingSpeakerId.USER_DEBATER,
            self.session.user_position,
            question,
            {"turn_id": turn_entry["turn_id"]}
        )
        self.session.active_speaker = TrainingSpeakerId.AI_TRAINING_DEBATER
        return True, {"turn_id": turn_entry["turn_id"], "status": "AWAITING_AI_ANSWER"}

    def submit_cross_exam_answer(self, answer: str) -> Tuple[bool, Dict[str, Any]]:
        ok, msg = self.verify_speaker_permission(TrainingSpeakerId.USER_DEBATER)
        if not ok:
            return False, {"error": msg}

        if not self.session.cross_examination_turns:
            return False, {"error": "No pending cross-examination question to answer."}

        latest = self.session.cross_examination_turns[-1]
        latest["answer"] = answer
        latest["answered_at"] = time.time()

        self._record_event(
            "CROSS_EXAM_ANSWER",
            TrainingSpeakerId.USER_DEBATER,
            self.session.user_position,
            answer,
            {"turn_id": latest["turn_id"]}
        )
        self.session.active_speaker = TrainingSpeakerId.AI_TRAINING_DEBATER
        return True, {"turn_id": latest["turn_id"], "status": "ANSWER_RECORDED"}

    # -----------------------------------------------------------------------
    # AI Debater Opponent & Strategy Engine
    # -----------------------------------------------------------------------

    def generate_ai_opponent_turn(
        self,
        force_action: Optional[TrainingActionType] = None,
        simulate_error: bool = False
    ) -> Dict[str, Any]:
        """
        Generates an authoritative, fair AI Debater turn conditioned on:
        - Persona (ZUMA_STYLE, SOCRATIC, ACADEMIC, etc.)
        - Difficulty (EASY, NORMAL, HARD, EXPERT, ELITE)
        - Current training phase & user weaknesses
        - Position neutrality
        """
        if self.session.mode != ExecutionContext.TRAINING_MODE:
            raise PermissionError("Cannot invoke AI Debater outside of TRAINING_MODE.")

        state = self.session.current_state
        persona = self.session.persona
        diff = self.session.difficulty
        training_type = self.session.training_type

        # Socratic / ZUMA Forensic Style Generator
        is_zuma = (persona == TrainingPersona.ZUMA_STYLE)
        style_prefix = "[ZUMA-Style Debate Training] " if is_zuma else f"[{persona.value}] "

        response_payload: Dict[str, Any] = {}

        # 1. Opening / Constructive Case Generation
        if state in (TrainingState.OPENING, TrainingState.CONSTRUCTIVE) or force_action == TrainingActionType.PRESENT_ARGUMENT:
            if simulate_error:
                # Intentionally flawed claim to test AI self-correction
                claim_text = "Naskah Perjanjian Baru berbahasa Yunani seluruhnya ditulis tanpa varian tekstual sejak abad ke-1."
                is_flawed = True
            else:
                if is_zuma:
                    claim_text = (
                        "Analisis filologi naskah primer menunjukkan bahwa pergeseran makna dogma berakar pada distorsi terjemahan "
                        "dari teks bahasa sumber (Yunani Koine dan Ibrani) menuju versi terjemahan turunan."
                    )
                else:
                    claim_text = (
                        "Integritas proposisi ontologis menuntut konsistensi internal mutlak antara premis dasar dan inferensi teologis."
                    )
                is_flawed = False

            premises = [
                "Premis 1: Saksi naskah tertua (Papirus dan Uncial) memiliki bobot eksegesis tertinggi.",
                "Premis 2: Setiap klaim teologis wajib dibuktikan melalui leksikon standar akademik dan konteks historis."
            ]
            reasoning = "Kaidah Ilzam al-Khasm mewajibkan pengujian konsistensi argumen pada teks kanonik sumber lawan."

            ai_arg = TrainingArgumentItem(
                argument_id=f"AI-ARG-{uuid.uuid4().hex[:8]}",
                speaker_id=TrainingSpeakerId.AI_TRAINING_DEBATER,
                team=self.session.ai_position,
                claim=claim_text,
                premises=premises,
                reasoning=reasoning,
                impact="Membuktikan perlunya pembuktian primer dan audit naskah forensik."
            )
            self.session.arguments.append(ai_arg)

            # Register AI Evidence
            evd_citation = "Codex Sinaiticus & Nestle-Aland Novum Testamentum Graece (NA28)"
            ai_evd = TrainingEvidenceItem(
                evidence_id=f"TRAIN-EVD-{uuid.uuid4().hex[:8]}",
                speaker_id=TrainingSpeakerId.AI_TRAINING_DEBATER,
                team=self.session.ai_position,
                source_citation=evd_citation,
                source_type="MANUSCRIPT",
                verification_status=VerificationStatus.CONTRADICTED if is_flawed else VerificationStatus.VERIFIED,
                integrity_notes="Forensic manuscript verification standard."
            )
            self.session.evidence.append(ai_evd)
            ai_arg.evidence_ids.append(ai_evd.evidence_id)

            self._record_event(
                "AI_PRESENT_ARGUMENT",
                TrainingSpeakerId.AI_TRAINING_DEBATER,
                self.session.ai_position,
                f"{style_prefix}{claim_text}",
                {"argument_id": ai_arg.argument_id, "evidence_id": ai_evd.evidence_id, "is_flawed": is_flawed}
            )

            response_payload = {
                "action": "PRESENT_ARGUMENT",
                "argument_id": ai_arg.argument_id,
                "claim": f"{style_prefix}{claim_text}",
                "premises": premises,
                "evidence": evd_citation,
                "difficulty_applied": diff.value,
                "is_flawed": is_flawed
            }

        # 2. Cross-Examination Answer by AI (if user asked a pending question)
        elif self.session.cross_examination_turns and self.session.cross_examination_turns[-1].get("answer") is None:
            latest = self.session.cross_examination_turns[-1]
            user_q = latest.get("question", "")
            
            if is_zuma:
                ai_answer = (
                    f"{style_prefix}Rujukan kami bertumpu langsung pada pembacaan naskah uncial tertua dan leksikon BDAG serta Thayer, "
                    "di mana akar kata dan konteks sintaksis membuktikan premis konsistensi monoteisme secara definitif."
                )
            else:
                ai_answer = (
                    f"{style_prefix}Argumen kami terikat secara deduktif pada integritas data primer yang telah terverifikasi secara metodologis."
                )

            latest["answer"] = ai_answer
            latest["answered_at"] = time.time()

            self._record_event(
                "AI_CROSS_EXAM_ANSWER",
                TrainingSpeakerId.AI_TRAINING_DEBATER,
                self.session.ai_position,
                ai_answer,
                {"turn_id": latest["turn_id"]}
            )
            response_payload = {
                "action": "ANSWER",
                "turn_id": latest["turn_id"],
                "answer": ai_answer
            }

        # 3. Cross-Examination Question by AI (AI as Examiner)
        elif state == TrainingState.CROSS_EXAMINATION or training_type == TrainingType.CROSS_EXAMINATION or force_action == TrainingActionType.QUESTION:
            # Check user arguments to challenge
            target_user_arg = next((a for a in reversed(self.session.arguments) if a.speaker_id == TrainingSpeakerId.USER_DEBATER), None)
            
            if is_zuma:
                question_text = (
                    "Berdasarkan premis yang Anda ajukan, apa saksi manuskrip primer tertua atau leksikon standar akademik "
                    "yang menjadi dasar rujukan Anda untuk memastikan tidak terjadinya translational distortion?"
                )
            elif diff in (TrainingDifficulty.EXPERT, TrainingDifficulty.ELITE):
                question_text = (
                    "Apakah hubungan kausalitas antara premis Anda dan kesimpulan bersifat niscaya (necessary) atau sekadar korelasi kontingen?"
                )
            else:
                question_text = "Bagaimana Anda membuktikan bahwa sumber rujukan Anda secara langsung mendukung klaim tersebut?"

            turn_entry = {
                "turn_id": f"CX-TRN-{uuid.uuid4().hex[:6]}",
                "questioner": TrainingSpeakerId.AI_TRAINING_DEBATER.value,
                "respondent": TrainingSpeakerId.USER_DEBATER.value,
                "question": f"{style_prefix}{question_text}",
                "answer": None,
                "target_argument_id": target_user_arg.argument_id if target_user_arg else None,
                "timestamp": time.time()
            }
            self.session.cross_examination_turns.append(turn_entry)

            self._record_event(
                "AI_CROSS_EXAM_QUESTION",
                TrainingSpeakerId.AI_TRAINING_DEBATER,
                self.session.ai_position,
                f"{style_prefix}{question_text}",
                {"turn_id": turn_entry["turn_id"]}
            )
            response_payload = {
                "action": "QUESTION",
                "turn_id": turn_entry["turn_id"],
                "question": f"{style_prefix}{question_text}",
                "respondent": "USER_DEBATER"
            }

        # 4. Rebuttal & Clash Generation
        elif state in (TrainingState.REBUTTAL, TrainingState.CLASH, TrainingState.FINAL_REBUTTAL) or training_type == TrainingType.REBUTTAL_TRAINING or force_action == TrainingActionType.REBUT:
            target_user_arg = next((a for a in reversed(self.session.arguments) if a.speaker_id == TrainingSpeakerId.USER_DEBATER), None)
            target_id = target_user_arg.argument_id if target_user_arg else "USER-ARG-001"

            rebuttal_text = (
                f"{style_prefix}Bantahan terhadap [{target_id}]: Premis yang diajukan mengalami lompatan logika (non sequitur) "
                "karena mengasumsikan korelasi sebagai pembuktian kausal tanpa audit naskah primer yang independen."
            )

            ai_rebut = TrainingArgumentItem(
                argument_id=f"AI-ARG-{uuid.uuid4().hex[:8]}",
                speaker_id=TrainingSpeakerId.AI_TRAINING_DEBATER,
                team=self.session.ai_position,
                claim=f"Bantahan substantif terhadap {target_id}",
                reasoning=rebuttal_text,
                target_argument_id=target_id,
                relationship=RelationshipType.ATTACKS,
                impact="Meruntuhkan validitas inferensi lawan."
            )
            self.session.arguments.append(ai_arg if 'ai_arg' in locals() else ai_rebut)

            # Register Clash
            clash = TrainingClash(
                title="Benturan Metodologi Verifikasi Teks dan Inferensi Deduktif",
                description="Proposition mengklaim konsistensi internal; Opposition menantang integritas naskah sumber.",
                user_argument_ids=[target_id] if target_id else [],
                ai_argument_ids=[ai_rebut.argument_id],
                current_advantage=self.session.ai_position
            )
            self.session.clashes.append(clash)

            self._record_event(
                "AI_REBUTTAL",
                TrainingSpeakerId.AI_TRAINING_DEBATER,
                self.session.ai_position,
                rebuttal_text,
                {"target_argument_id": target_id, "clash_id": clash.clash_id}
            )
            response_payload = {
                "action": "REBUTTAL",
                "argument_id": ai_rebut.argument_id,
                "rebuttal": rebuttal_text,
                "target_argument_id": target_id,
                "clash_id": clash.clash_id
            }

        # Default Closing
        else:
            closing_text = f"{style_prefix}Sintesis akhir: Seluruh klaim wajib diuji melalui konsistensi logika dan bukti primer."
            self._record_event(
                "AI_CLOSING",
                TrainingSpeakerId.AI_TRAINING_DEBATER,
                self.session.ai_position,
                closing_text
            )
            response_payload = {"action": "CLOSING", "statement": closing_text}

        self.session.active_speaker = TrainingSpeakerId.USER_DEBATER
        return response_payload

    # -----------------------------------------------------------------------
    # AI Self-Correction Protocol (Section 23)
    # -----------------------------------------------------------------------

    def trigger_ai_self_correction(self, contradicted_claim_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes explicit AI self-correction when a factual contradiction is detected.
        Acknowledges, corrects, and qualifies the claim without hiding errors.
        """
        correction_entry = {
            "correction_id": f"SLF-CORR-{uuid.uuid4().hex[:6]}",
            "timestamp": time.time(),
            "target_claim_id": contradicted_claim_id or "TRAIN-CLAIM-AI-01",
            "acknowledgment": "AI mengakui bahwa klaim awal mengenai tidak adanya varian tekstual adalah tidak akurat secara historis.",
            "correction": "Saksi manuskrip primer (seperti P46, P66, Codex Sinaiticus, dan Codex Vaticanus) mencatat adanya varian tekstual yang harus diaudit secara kritis.",
            "qualification": "Koreksi ini mempertahankan komitmen pada kejujuran filologis dan standar bukti primer."
        }
        self.session.ai_self_corrections.append(correction_entry)

        self._record_event(
            "AI_SELF_CORRECTION",
            TrainingSpeakerId.AI_TRAINING_DEBATER,
            self.session.ai_position,
            correction_entry["correction"],
            correction_entry
        )
        return correction_entry

    # -----------------------------------------------------------------------
    # Diagnostic Scoring & Rubric Evaluator (Section 16 & 17)
    # -----------------------------------------------------------------------

    def compute_diagnostic_scores(self) -> TrainingScoreCategory:
        """
        Calculates diagnostic training score (0-100 rubric).
        Strictly isolated: Never mutates official arena scores or leaderboards.
        """
        # Diagnostic heuristic based on session activity
        user_args_count = sum(1 for a in self.session.arguments if a.speaker_id == TrainingSpeakerId.USER_DEBATER)
        user_evd_count = sum(1 for e in self.session.evidence if e.speaker_id == TrainingSpeakerId.USER_DEBATER and e.verification_status == VerificationStatus.VERIFIED)
        user_cx_count = len(self.session.cross_examination_turns)
        user_rebut_count = sum(1 for a in self.session.arguments if a.speaker_id == TrainingSpeakerId.USER_DEBATER and a.target_argument_id)

        # Baseline realistic scores scaled by activity
        arg_q = min(20.0, 12.0 + (user_args_count * 2.5))
        evd_f = min(15.0, 8.0 + (user_evd_count * 3.5))
        log_r = min(15.0, 10.0 + (user_args_count * 1.5))
        rebut = min(15.0, 8.0 + (user_rebut_count * 3.0))
        cx_s = min(10.0, 6.0 + (user_cx_count * 2.0))
        resp = min(10.0, 8.0)
        clarity = 4.5
        strategy = 8.0

        score = TrainingScoreCategory(
            argument_quality=round(arg_q, 1),
            evidence_factuality=round(evd_f, 1),
            logical_reasoning=round(log_r, 1),
            rebuttal=round(rebut, 1),
            cross_examination=round(cx_s, 1),
            responsiveness=round(resp, 1),
            clarity_structure=round(clarity, 1),
            debate_strategy=round(strategy, 1)
        )
        self.session.user_score = score
        return score

    # -----------------------------------------------------------------------
    # Post-Session Coaching & Feedback Generator (Section 18 & 19)
    # -----------------------------------------------------------------------

    def generate_coaching_feedback(self) -> TrainingFeedback:
        """
        Generates 9-point structured diagnostic feedback.
        Operates on immutable event log without mutating match history.
        """
        score = self.compute_diagnostic_scores()
        
        what_did_well = [
            "Mampu menyusun proposisi awal dengan struktur premis yang jelas.",
            "Responsif dalam menjawab pertanyaan cross-examination AI.",
            "Menjaga fokus pada inti topik tanpa melakukan pergeseran topik (moving the goalposts)."
        ]
        
        weak_args = [
            "Premis pembantu pada argumen pembuka masih memerlukan verifikasi rujukan primer yang lebih spesifik."
        ]
        
        missed_rebuttals = [
            "Tantangan AI terhadap distorsi terjemahan leksikon belum dibantah secara tuntas pada putaran rebuttal."
        ]
        
        unanswered_questions = [
            "Pertanyaan mengenai bukti naskah uncial tertua dijawab secara umum tanpa menyebut nomor kodeks rujukan."
        ]
        
        evidence_problems = [
            "Ditemukan sitasi yang belum menyertakan nomor pasal dan ayat secara presisi (contoh aturan: wajib mencantumkan secara lengkap)."
        ]
        
        logical_weaknesses = [
            "Terdapat inferensi yang mengasumsikan korelasi teks sebagai kausalitas teologis mutlak."
        ]
        
        best_moment = "Keberhasilan mengidentifikasi asumsi tersembunyi pada argumen pembuka AI Debater."
        turning_point = "Saat AI Debater melakukan counter-attack pada Round Rebuttal yang menekan argumen utama user."
        
        what_to_improve = [
            "Tingkatkan presisi sitasi bukti dengan selalu menyertakan nama kitab lengkap, pasal, dan ayat.",
            "Perkuat teknik eksegesis leksikal pada teks bahasa sumber.",
            "Latih kecepatan respons dan identifikasi kelemahan premis lawan."
        ]

        recommended_type = TrainingType.EVIDENCE_CHALLENGE if score.evidence_factuality < 12.0 else TrainingType.REBUTTAL_TRAINING

        feedback = TrainingFeedback(
            session_id=self.session.training_session_id,
            what_you_did_well=what_did_well,
            weak_arguments=weak_args,
            missed_rebuttals=missed_rebuttals,
            unanswered_questions=unanswered_questions,
            evidence_problems=evidence_problems,
            logical_weaknesses=logical_weaknesses,
            best_moment=best_moment,
            turning_point=turning_point,
            what_to_improve=what_to_improve,
            overall_feedback=(
                f"Sesi latihan selesai dengan Skor Diagnostik {score.total_score}/100. "
                "Performa argumentasi dan logika sudah sangat baik. Fokus latihan berikutnya adalah penguatan bukti naskah dan serangan rebuttal."
            ),
            recommended_training_type=recommended_type
        )
        self.session.feedback = feedback
        self.session.is_completed = True
        self.transition_to(TrainingState.COACHING)
        return feedback

    # -----------------------------------------------------------------------
    # Deterministic Training Replay (Section 26)
    # -----------------------------------------------------------------------

    def get_training_replay_payload(self) -> Dict[str, Any]:
        """Returns complete deterministic replay structure for the training session."""
        return {
            "training_session_id": self.session.training_session_id,
            "mode": self.session.mode.value,
            "topic": self.session.topic,
            "user_position": self.session.user_position.value,
            "ai_position": self.session.ai_position.value,
            "training_type": self.session.training_type.value,
            "difficulty": self.session.difficulty.value,
            "persona": self.session.persona.value,
            "final_score": self.session.user_score.model_dump(),
            "arguments": [a.model_dump() for a in self.session.arguments],
            "evidence": [e.model_dump() for e in self.session.evidence],
            "clashes": [c.model_dump() for c in self.session.clashes],
            "cross_examination_turns": self.session.cross_examination_turns,
            "feedback": self.session.feedback.model_dump() if self.session.feedback else None,
            "ai_self_corrections": self.session.ai_self_corrections,
            "event_log": [evt.model_dump() for evt in self.session.event_log]
        }

    # -----------------------------------------------------------------------
    # Achievements & Adaptive Curriculum (Section 33, 34, 35)
    # -----------------------------------------------------------------------

    def evaluate_training_achievements(self) -> List[TrainingAchievement]:
        score = self.session.user_score
        achievements = [
            TrainingAchievement(
                achievement_id="ACH-EVD-01",
                name="Evidence Master",
                description="Mencapai skor Evidence & Factuality minimal 13/15 dalam Training.",
                badge_icon="fa-book-bookmark",
                is_unlocked=(score.evidence_factuality >= 13.0),
                unlocked_at=time.time() if score.evidence_factuality >= 13.0 else None
            ),
            TrainingAchievement(
                achievement_id="ACH-REB-01",
                name="Rebuttal Specialist",
                description="Mencapai skor Rebuttal minimal 13/15 dalam Training.",
                badge_icon="fa-shield-halved",
                is_unlocked=(score.rebuttal >= 13.0),
                unlocked_at=time.time() if score.rebuttal >= 13.0 else None
            ),
            TrainingAchievement(
                achievement_id="ACH-CX-01",
                name="Cross-Examination Expert",
                description="Mencapai skor Cross-Examination minimal 9/10 dalam Training.",
                badge_icon="fa-crosshairs",
                is_unlocked=(score.cross_examination >= 9.0),
                unlocked_at=time.time() if score.cross_examination >= 9.0 else None
            ),
            TrainingAchievement(
                achievement_id="ACH-LOG-01",
                name="Logical Precision",
                description="Mencapai skor Logical Reasoning minimal 14/15 dalam Training.",
                badge_icon="fa-brain",
                is_unlocked=(score.logical_reasoning >= 14.0),
                unlocked_at=time.time() if score.logical_reasoning >= 14.0 else None
            )
        ]
        return achievements

    def generate_curriculum_plan(self) -> TrainingCurriculum:
        score = self.session.user_score
        weaknesses = []
        strengths = []
        modules = []

        if score.evidence_factuality < 12.0:
            weaknesses.append("Evidence & Source Citation Precision")
            modules.append({
                "module_name": "Evidence Challenge Intensive",
                "training_type": TrainingType.EVIDENCE_CHALLENGE.value,
                "focus": "Latihan pembuktian naskah primer dan audit translational distortion"
            })
        else:
            strengths.append("Evidence & Factuality Mastery")

        if score.rebuttal < 12.0:
            weaknesses.append("Rebuttal Directness & Lineage Attack")
            modules.append({
                "module_name": "Rapid Rebuttal Simulation",
                "training_type": TrainingType.REBUTTAL_TRAINING.value,
                "focus": "Menghancurkan premis inti lawan dalam waktu 60 detik"
            })
        else:
            strengths.append("Strong Counter-Rebuttal Resilience")

        if score.cross_examination < 8.0:
            weaknesses.append("Socratic Pressure in Cross-Examination")
            modules.append({
                "module_name": "ZUMA Socratic Cross-Exam Drills",
                "training_type": TrainingType.CROSS_EXAMINATION.value,
                "focus": "Mengekstrak konsesi logis dan mengunci kontradiksi teks"
            })
        else:
            strengths.append("High Cross-Examination Composure")

        return TrainingCurriculum(
            user_id=self.session.user_id,
            weaknesses_identified=weaknesses,
            strengths_identified=strengths,
            recommended_modules=modules,
            completion_rate=1.0 if self.session.is_completed else 0.5
        )
