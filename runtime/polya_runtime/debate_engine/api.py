"""
Debate Arena API & Authoritative State Bridge (Prompt 12)
Provides unified state serialization, lifecycle control, and real-time event streaming.
Adheres strictly to the Principle: UI is NOT the source of truth, Engine is Authoritative.
"""

from typing import Dict, List, Optional, Any, Tuple
import time
import json
import logging
import copy

from polya_runtime.debate_engine.models import (
    EventState,
    TeamSide,
    SpeakerId,
    AIRole,
    ActionType,
    EventFlag,
    VerificationStatus,
    RelationshipType,
    DebaterProfile,
    EvidenceItem,
    ClaimItem,
    ArgumentItem,
    CriticalClash,
    DebaterScoreCategory,
    ScoreAuditEvent,
    EventStateObject
)
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.round_configs import RoundPhase, DEFAULT_ROUND_CONFIGS, CrossExamStep
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimType,
    ClaimImportance,
    SourceType,
    FactCheckVerdict,
    EvidenceStatus,
    QuoteIntegrityStatus,
    SourceItem,
    EvidenceDetail,
    ClaimDetail,
    FactCheckResult
)
from polya_runtime.debate_engine.argument_engine import (
    ArgumentHierarchy,
    ArgumentImportance,
    ArgumentRelation,
    AttackType,
    DefenseType,
    ArgumentStatus,
    AnswerStatus
)
from polya_runtime.debate_engine.clash_engine import (
    ClashType,
    ClashImportance,
    ClashAdvantage,
    ClashStatus
)
from polya_runtime.debate_engine.persona_models import (
    ArenaMode,
    PersonaDimension
)
from polya_runtime.debate_engine.zuma_dataset import (
    build_zuma_apologetics_persona,
    ZUMA_PATTERNS_V1
)

import threading
import uuid

logger = logging.getLogger("polya.debate_api")

class DebateArenaService:
    """Manages match instances and delivers authoritative serialized states for UI."""

    def __init__(self, topic: str = "Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik", description: str = "Uji Forensik Standar Pertanggungjawaban Algoritma Otonom 3-vs-3"):
        self._lock = threading.RLock()
        self.engine: DebateArenaEventEngine = DebateArenaEventEngine(topic=topic, topic_description=description)
        self.is_degraded: bool = False
        self.degraded_components: List[str] = []
        self._last_speech_transcript: Dict[str, str] = {}
        self._recent_speeches: List[Dict[str, Any]] = []
        self._connected_clients: List[Any] = []
        self._auto_timer_active: bool = False
        
        # Concurrency, Lobby, and Participant Session Tracking (Prompt 13)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._speaker_to_session: Dict[str, str] = {}
        self._processed_request_ids: Dict[str, Dict[str, Any]] = {}
        self._readiness: Dict[str, bool] = {
            "P1": False, "P2": False, "P3": False,
            "C1": False, "C2": False, "C3": False
        }
        self._init_default_match()

    def _init_default_match(self):
        """Pre-configures ZUMA persona for P2 and baseline setup."""
        zuma_persona = build_zuma_apologetics_persona(version="1.0.0")
        self.engine.persona_engine.register_persona(zuma_persona)
        self.engine.activate_debater_persona(SpeakerId.P2, zuma_persona.persona_id)

    def reset_match(self, topic: str, description: str = "") -> Dict[str, Any]:
        """Creates a clean debate arena match instance with reset sessions."""
        with self._lock:
            self.engine = DebateArenaEventEngine(topic=topic, topic_description=description)
            self.is_degraded = False
            self.degraded_components = []
            self._last_speech_transcript = {}
            self._recent_speeches = []
            self._sessions = {}
            self._speaker_to_session = {}
            self._processed_request_ids = {}
            self._readiness = {
                "P1": False, "P2": False, "P3": False,
                "C1": False, "C2": False, "C3": False
            }
            self._init_default_match()
            return self.get_full_state()

    def set_degraded_state(self, component: str, enabled: bool = True):
        """Simulates or recovers from degraded engine states."""
        with self._lock:
            if enabled:
                if component not in self.degraded_components:
                    self.degraded_components.append(component)
                self.is_degraded = True
            else:
                if component in self.degraded_components:
                    self.degraded_components.remove(component)
                self.is_degraded = len(self.degraded_components) > 0

    def join_lobby(
        self,
        participant_name: str,
        requested_speaker_id: SpeakerId,
        requested_team: TeamSide,
        session_id: Optional[str] = None,
        client_ip: str = "127.0.0.1"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handles human participant joining the 3-vs-3 lobby with strict identity & team validation."""
        with self._lock:
            # 1. Reject non-human or invalid speaker seats (AI Non-Participant rule)
            valid_human_seats = {
                SpeakerId.P1: TeamSide.PROPOSITION,
                SpeakerId.P2: TeamSide.PROPOSITION,
                SpeakerId.P3: TeamSide.PROPOSITION,
                SpeakerId.C1: TeamSide.OPPOSITION,
                SpeakerId.C2: TeamSide.OPPOSITION,
                SpeakerId.C3: TeamSide.OPPOSITION,
            }
            if requested_speaker_id not in valid_human_seats:
                spk_val = getattr(requested_speaker_id, 'value', str(requested_speaker_id))
                return False, f"Invalid seat: {spk_val}. AI roles cannot be joined as participant.", {}

            # 2. Team consistency enforcement (Wrong Team Test)
            expected_team = valid_human_seats[requested_speaker_id]
            if requested_team != expected_team:
                return False, f"Wrong team assignment: Speaker {requested_speaker_id.value} must belong to {expected_team.value}, not {requested_team.value}.", {}

            current_state = self.engine.state_obj.current_state
            # 3. Match Lock & Late Join check
            is_existing_speaker = requested_speaker_id.value in self._speaker_to_session
            if current_state not in [EventState.SETUP, EventState.TOPIC_LOCK] and not is_existing_speaker:
                return False, f"Late join rejected: match is in state {current_state.value}. Team assignment is locked.", {}

            # 4. Duplicate session handling (One Authoritative Session per participant)
            sess_id = session_id or f"SESS-{requested_speaker_id.value}-{uuid.uuid4().hex[:6]}"
            old_sess_id = self._speaker_to_session.get(requested_speaker_id.value)
            if old_sess_id and old_sess_id in self._sessions and old_sess_id != sess_id:
                # Mark old session as superseded/inactive
                self._sessions[old_sess_id]["is_active"] = False
                self._sessions[old_sess_id]["is_connected"] = False

            # Update debater profile in authoritative engine state
            debater = self.engine.state_obj.debaters.get(requested_speaker_id.value)
            if debater:
                debater.name = participant_name

            session_data = {
                "session_id": sess_id,
                "speaker_id": requested_speaker_id.value,
                "team": requested_team.value,
                "participant_name": participant_name,
                "is_connected": True,
                "is_active": True,
                "ready": self._readiness.get(requested_speaker_id.value, False),
                "joined_at": time.time(),
                "client_ip": client_ip
            }
            self._sessions[sess_id] = session_data
            self._speaker_to_session[requested_speaker_id.value] = sess_id

            self.engine.log_manager.record(
                event_type="PARTICIPANT_JOINED",
                state=current_state.value,
                round_name=self.engine.state_obj.current_round,
                speaker_id=requested_speaker_id.value,
                team=requested_team.value,
                payload={"participant_name": participant_name, "session_id": sess_id},
                summary=f"Participant {participant_name} joined as {requested_speaker_id.value} ({requested_team.value})"
            )

            return True, f"Participant {participant_name} assigned to seat {requested_speaker_id.value}", session_data

    def set_participant_ready(self, speaker_id: SpeakerId, ready: bool = True) -> Tuple[bool, str]:
        """Toggles participant ready status. Transitions to TEAM_READY when 6/6 ready."""
        with self._lock:
            if speaker_id.value not in self._readiness:
                return False, f"Invalid participant: {speaker_id.value}"

            self._readiness[speaker_id.value] = ready
            sess_id = self._speaker_to_session.get(speaker_id.value)
            if sess_id and sess_id in self._sessions:
                self._sessions[sess_id]["ready"] = ready

            ready_count = sum(1 for r in self._readiness.values() if r)
            total_count = len(self._readiness)

            # If all 6 participants are ready, transition to TEAM_READY if in SETUP/TOPIC_LOCK
            if ready_count == total_count:
                if self.engine.state_obj.current_state == EventState.SETUP:
                    self.engine.lock_topic(self.engine.state_obj.topic or "Topic Locked")
                if self.engine.state_obj.current_state == EventState.TOPIC_LOCK:
                    self.engine.set_team_ready()
                return True, f"All {total_count}/{total_count} participants READY. Match transitioned to TEAM_READY."

            return True, f"Participant {speaker_id.value} readiness set to {ready} ({ready_count}/{total_count} READY)."

    def disconnect_participant(self, speaker_id: SpeakerId) -> Tuple[bool, str]:
        """Simulates network interruption / disconnect. Preserves authoritative engine state without AI substitution."""
        with self._lock:
            sess_id = self._speaker_to_session.get(speaker_id.value)
            if sess_id and sess_id in self._sessions:
                self._sessions[sess_id]["is_connected"] = False

            self.engine.log_manager.record(
                event_type="PARTICIPANT_DISCONNECTED",
                state=self.engine.state_obj.current_state.value,
                round_name=self.engine.state_obj.current_round,
                speaker_id=speaker_id.value,
                team=self.engine.state_obj.debaters[speaker_id.value].team.value if speaker_id.value in self.engine.state_obj.debaters else "",
                payload={"speaker_id": speaker_id.value},
                summary=f"Participant {speaker_id.value} disconnected. Authoritative match state preserved."
            )
            return True, f"Participant {speaker_id.value} disconnected. Match state intact."

    def reconnect_participant(self, speaker_id: SpeakerId, session_id: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Handles participant reconnecting. Delivers current authoritative state without stale cache."""
        with self._lock:
            if speaker_id.value not in self._speaker_to_session:
                return False, f"Participant {speaker_id.value} was not registered in this match.", {}

            sess_id = session_id or self._speaker_to_session[speaker_id.value]
            if sess_id not in self._sessions:
                self._sessions[sess_id] = {
                    "session_id": sess_id,
                    "speaker_id": speaker_id.value,
                    "team": "PROPOSITION" if speaker_id.value.startswith("P") else "OPPOSITION",
                    "participant_name": self.engine.state_obj.debaters[speaker_id.value].name,
                    "is_connected": True,
                    "is_active": True,
                    "ready": True,
                    "joined_at": time.time(),
                    "client_ip": "127.0.0.1"
                }
            else:
                self._sessions[sess_id]["is_connected"] = True
                self._sessions[sess_id]["is_active"] = True

            self._speaker_to_session[speaker_id.value] = sess_id

            self.engine.log_manager.record(
                event_type="PARTICIPANT_RECONNECTED",
                state=self.engine.state_obj.current_state.value,
                round_name=self.engine.state_obj.current_round,
                speaker_id=speaker_id.value,
                team=self.engine.state_obj.debaters[speaker_id.value].team.value if speaker_id.value in self.engine.state_obj.debaters else "",
                payload={"speaker_id": speaker_id.value, "session_id": sess_id},
                summary=f"Participant {speaker_id.value} reconnected to authoritative state."
            )

            current_state = self.get_full_state()
            return True, f"Participant {speaker_id.value} reconnected successfully.", current_state

    def get_lobby_state(self) -> Dict[str, Any]:
        """Returns structured 6-participant lobby status and readiness."""
        with self._lock:
            seats = []
            for spk_str in ["P1", "P2", "P3", "C1", "C2", "C3"]:
                sess_id = self._speaker_to_session.get(spk_str)
                sess = self._sessions.get(sess_id) if sess_id else None
                deb = self.engine.state_obj.debaters.get(spk_str)
                seats.append({
                    "speaker_id": spk_str,
                    "team": "PROPOSITION" if spk_str.startswith("P") else "OPPOSITION",
                    "participant_name": sess.get("participant_name", deb.name if deb else spk_str) if sess else None,
                    "is_assigned": sess is not None,
                    "is_connected": sess.get("is_connected", False) if sess else False,
                    "ready": self._readiness.get(spk_str, False),
                    "session_id": sess_id
                })

            ready_count = sum(1 for r in self._readiness.values() if r)
            return {
                "seats": seats,
                "ready_count": ready_count,
                "total_seats": 6,
                "is_full": all(s["is_assigned"] for s in seats),
                "all_ready": ready_count == 6,
                "match_state": self.engine.state_obj.current_state.value
            }

    def load_golden_match(self) -> Dict[str, Any]:
        """Executes the complete Golden Match 001 through the engine and returns authoritative state."""
        from polya_runtime.debate_engine.models import SpeakerId, TeamSide, EventState, ActionType
        
        topic = "Regulasi Forensik Kecerdasan Buatan dan Pertanggungjawaban Algoritmik"
        self.engine = DebateArenaEventEngine(
            topic=topic,
            topic_description="Uji Forensik Standar Pertanggungjawaban Algoritma Otonom 3-vs-3"
        )
        self._init_default_match()
        
        # Setup -> Topic Lock -> Teams Ready
        self.engine.lock_topic(topic)
        self.engine.set_team_ready()
        
        # Round 0: Intro & Rule Briefing
        self.engine.start_round(RoundPhase.ROUND_0_INTRO)
        self.engine.start_round(RoundPhase.ROUND_0_RULE_BRIEFING)
        
        # Round 1: Opening
        self.engine.start_round(RoundPhase.ROUND_1_OPENING)
        clm_p1 = self.engine.register_claim(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            statement="Sistem otonom tingkat 4 ke atas wajib memiliki audit forensik deterministik.",
            claim_type=ClaimType.LEGAL,
            importance=ClaimImportance.CENTRAL
        )
        src_p1 = self.engine.register_source(
            source_id="SRC-EU-AIACT",
            title="EU AI Act Article 14 Compliance Framework",
            author="European Parliament & Council",
            publisher="Official Journal of the European Union",
            publication_year=2024,
            source_type=SourceType.GOVERNMENT_SOURCE,
            quality_score=9.9
        )
        evd_p1 = self.engine.evidence_engine.register_evidence(
            evidence_id="EVD-EU-01",
            source_id="SRC-EU-AIACT",
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            quoted_text="High-risk AI systems shall be designed to enable human oversight and deterministic event logging.",
            context_notes="Mandatory compliance for Level 4 autonomous systems",
            quote_status=QuoteIntegrityStatus.QUOTE_VERIFIED,
            status=EvidenceStatus.VERIFIED
        )
        self.engine.verify_claim(clm_p1.claim_id, [evd_p1.evidence_id])
        arg_p1 = self.engine.register_strategic_argument(
            speaker_id=SpeakerId.P1,
            team=TeamSide.PROPOSITION,
            claim_text="Sistem otonom tingkat 4 ke atas wajib memiliki audit forensik deterministik.",
            premises=[
                "Tanpa audit forensik, atribusi kesalahan hukum menjadi mustahil secara yuridis.",
                "EU AI Act Pasal 14 mewajibkan logging forensik deterministik."
            ],
            conclusion="Audit forensik adalah prasyarat mutlak keselamatan publik.",
            hierarchy=ArgumentHierarchy.CORE,
            importance=ArgumentImportance.DECISIVE
        )
        self._record_speech_text("P1", "Kami dari Tim Proposisi menegaskan bahwa sistem kecerdasan buatan otonom tingkat 4 ke atas wajib memiliki audit forensik deterministik. Tanpa standar ini, keadilan bagi korban kecelakaan sistem otonom tidak akan pernah dapat dipulihkan.")

        # C1 turn
        self.engine.advance_speaker_turn()
        clm_c1 = self.engine.register_claim(
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            statement="Audit forensik deterministik membatasi efisiensi komputasi neural network modern.",
            claim_type=ClaimType.SCIENTIFIC,
            importance=ClaimImportance.CENTRAL
        )
        arg_c1 = self.engine.register_strategic_argument(
            speaker_id=SpeakerId.C1,
            team=TeamSide.OPPOSITION,
            claim_text="Audit deterministik memperlambat latensi inferensi dalam skenario kritis.",
            premises=[
                "Enkapsulasi deterministik menambah overhead komputasi hingga 40%.",
                "Sistem otonom waktu nyata membutuhkan latensi sub-milidetik."
            ],
            conclusion="Mandat determinisme mutlak menghambat adopsi sistem keselamatan otonom.",
            hierarchy=ArgumentHierarchy.CORE,
            importance=ArgumentImportance.DECISIVE
        )
        self._record_speech_text("C1", "Oposisi menolak mandasi deterministik kaku. Overhead komputasi 40% akan menyebabkan latensi fatal pada sistem pengereman darurat dan kendaraan nirawak.")

        # Round 2: Constructive (P2 ZUMA vs C2)
        self.engine.start_round(RoundPhase.ROUND_2_CONSTRUCTIVE)
        self.engine.record_observed_behavior(
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            dimension=PersonaDimension.PREMISE_TESTING,
            observed_tactic="Framed algorithmic liability as non-delegable fiduciary duty using statutory precision.",
            matched_pattern_id="ZUMA-PAT-001",
            confidence=0.96
        )
        arg_p2 = self.engine.register_strategic_argument(
            speaker_id=SpeakerId.P2,
            team=TeamSide.PROPOSITION,
            claim_text="Tanggung jawab hukum algoritma adalah kewajiban fidusia yang tidak dapat didelegasikan.",
            premises=[
                "Pengembang memegang tanggung jawab mutlak (strict liability).",
                "Hardware khusus ASIC mampu meniadakan overhead komputasi."
            ],
            conclusion="Argumen latensi lawan tidak relevan dengan arsitektur komputasi modern.",
            hierarchy=ArgumentHierarchy.SUB_ARGUMENT,
            importance=ArgumentImportance.IMPORTANT,
            parent_argument_id=arg_p1.argument_id,
            relation=ArgumentRelation.SUPPORTS
        )
        self._record_speech_text("P2", "[ZUMA APOLOGETICS PROTOCOL]: Mari kita bedah premis lawan secara forensik. Tanggung jawab hukum korporasi atas algoritma adalah kewajiban fidusia yang tidak dapat didelegasikan. Dengan akselerator ASIC modern, overhead determinisme terbukti tereduksi hingga di bawah 1.2%, mematahkan klaim latensi C1.")

        # Round 3: Evidence & Argument
        self.engine.start_round(RoundPhase.ROUND_3_EVIDENCE_ARGUMENT)

        # Round 4: Cross Examination
        self.engine.start_round(RoundPhase.ROUND_4_CROSS_EXAMINATION)
        self.engine.handle_cross_exam(
            ActionType.QUESTION,
            SpeakerId.P3,
            "Apakah overhead komputasi membatalkan doktrin pertanggungjawaban hukum pidana korporasi?"
        )
        self.engine.handle_cross_exam(
            ActionType.ANSWER,
            SpeakerId.C1,
            "Overhead teknis dapat menyebabkan kegagalan rem darurat pada kendaraan otonom, yang membahayakan nyawa manusia secara nyata."
        )

        # Clashes registration
        clash_1 = self.engine.register_strategic_clash(
            title="Forensic Auditability vs Latency Overhead",
            question="Apakah kewajiban audit deterministik merusak performa komputasi real-time?",
            proposition_position="Kewajiban audit deterministik adalah syarat mutlak keselamatan publik.",
            opposition_position="Audit deterministik memperlambat latensi inferensi dalam skenario kritis.",
            clash_type=ClashType.TRADEOFF,
            importance=ClashImportance.DECISIVE,
            argument_refs=[arg_p1.argument_id, arg_c1.argument_id]
        )
        clash_2 = self.engine.register_strategic_clash(
            title="Strict Developer Liability vs Shared Responsibility",
            question="Apakah pengembang memegang strict liability atau tanggung jawab bersama pengguna?",
            proposition_position="Entitas korporasi pengembang memegang tanggung jawab mutlak.",
            opposition_position="Tanggung jawab harus dibagi bersama operator dan pengguna akhir.",
            clash_type=ClashType.POLICY,
            importance=ClashImportance.HIGH,
            argument_refs=[arg_p2.argument_id, arg_c1.argument_id]
        )
        clash_3 = self.engine.register_strategic_clash(
            title="International Jurisdictional Standard vs National Sovereignty",
            question="Apakah standar regulasi forensik AI harus unifikasi global atau regulasi domestik?",
            proposition_position="Standar global mencegah regulatory arbitrage.",
            opposition_position="Kedaulatan domestik harus diutamakan sesuai kesiapan industri lokal.",
            clash_type=ClashType.FACTUAL,
            importance=ClashImportance.MEDIUM,
            argument_refs=[arg_p1.argument_id, arg_c1.argument_id]
        )

        # Round 5: Rebuttal
        self.engine.start_round(RoundPhase.ROUND_5_REBUTTAL)
        atk_c2 = self.engine.add_argument_attack(
            attacker=SpeakerId.C2,
            attacker_team=TeamSide.OPPOSITION,
            target_argument_id=arg_p1.argument_id,
            attack_type=AttackType.PREMISE_ATTACK,
            reason="Premis Pasal 14 EU AI Act hanya berlaku pada yurisdiksi Eropa dan belum terbukti adaptif di yurisdiksi common law."
        )
        self.engine.add_argument_defense(
            defender=SpeakerId.P3,
            defender_team=TeamSide.PROPOSITION,
            target_attack_id=atk_c2.attack_id,
            protected_argument_id=arg_p1.argument_id,
            defense_type=DefenseType.EVIDENCE_DEFENSE,
            reason="Prinsip due diligence Pasal 14 telah diadaptasi ke dalam ISO/IEC 42001 yang berlaku global."
        )

        # Round 6: Critical Clash
        self.engine.start_round(RoundPhase.ROUND_6_CRITICAL_CLASH)
        self.engine.update_clash_advantage(clash_1.clash_id, ClashAdvantage.PROPOSITION_ADVANTAGE)
        self.engine.record_momentum_event(
            team=TeamSide.PROPOSITION,
            trigger_event="Rigorous Socratic Dissection of Opposition Latency Claims",
            magnitude=9.8,
            reason="Proposition established decisive advantage in Round 6"
        )


        # Round 7: Final Rebuttal
        self.engine.start_round(RoundPhase.ROUND_7_FINAL_REBUTTAL)

        # Round 8: Closing
        self.engine.start_round(RoundPhase.ROUND_8_CLOSING)
        self._record_speech_text("P3", "Dengan demikian, Proposisi telah membuktikan secara empiris dan yuridis bahwa regulasi forensik deterministik tidak dapat ditawar demi integritas martabat manusia.")
        self.engine.advance_speaker_turn()
        self._record_speech_text("C3", "Oposisi tetap pada posisi bahwa keluwesan inovasi dan diferensiasi risiko adalah kunci kemajuan peradaban.")

        # Round 9: Deliberation & Scoring
        self.engine.start_round(RoundPhase.ROUND_9_DELIBERATION)
        scoring_items = [
            # Proposition Scores (Logic, Evidence, Strategy)
            (SpeakerId.P1, "argument_quality", 18.5, AIRole.JUDGE_A, "Comprehensive thesis setup"),
            (SpeakerId.P1, "evidence_factuality", 14.5, AIRole.JUDGE_B, "Primary statutory citation"),
            (SpeakerId.P1, "logical_reasoning", 14.0, AIRole.JUDGE_C, "Flawless deductive chain"),
            (SpeakerId.P2, "argument_quality", 19.2, AIRole.JUDGE_A, "Masterful forensic dissection"),
            (SpeakerId.P2, "evidence_factuality", 14.8, AIRole.JUDGE_B, "Irrefutable empirical benchmarks"),
            (SpeakerId.P2, "debate_strategy", 5.0, AIRole.JUDGE_C, "Flawless ZUMA dialetic pacing"),
            (SpeakerId.P3, "rebuttal", 14.2, AIRole.JUDGE_A, "Complete defense of core arguments"),
            # Opposition Scores
            (SpeakerId.C1, "argument_quality", 15.0, AIRole.JUDGE_A, "Coherent latency counter-framing"),
            (SpeakerId.C1, "evidence_factuality", 11.5, AIRole.JUDGE_B, "Limited primary empirical data"),
            (SpeakerId.C1, "logical_reasoning", 12.0, AIRole.JUDGE_C, "Valid but qualified premises"),
            (SpeakerId.C2, "argument_quality", 13.5, AIRole.JUDGE_A, "Good premise challenge"),
            (SpeakerId.C2, "rebuttal", 11.8, AIRole.JUDGE_B, "Incomplete addressal of ASIC mitigation"),
            (SpeakerId.C3, "debate_strategy", 4.0, AIRole.JUDGE_C, "Solid closing summary"),
        ]
        for spk, cat, delta, judge, reason in scoring_items:
            self.engine.update_score(speaker_id=spk, category=cat, delta=delta, judge_source=judge, reason=reason)

        # Round 10: Verdict & Archive
        self.engine.start_round(RoundPhase.ROUND_10_VERDICT)
        self.engine.adjudicate_match()
        self.engine.transition_to(EventState.ARCHIVE)

        return self.get_full_state()

    def _record_speech_text(self, speaker_id: str, speech_text: str):
        self._last_speech_transcript[speaker_id] = speech_text
        self._recent_speeches.append({
            "speaker_id": speaker_id,
            "text": speech_text,
            "timestamp": time.time()
        })
        if len(self._recent_speeches) > 20:
            self._recent_speeches.pop(0)

    def execute_operator_action(self, action_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Handles operator/debater actions with thread-safety, idempotency, speaker authority, and input validation."""
        with self._lock:
            request_id = action_data.get("request_id")
            # 1. Idempotency / Double submission protection
            if request_id and request_id in self._processed_request_ids:
                cached = self._processed_request_ids[request_id]
                return cached["ok"], f"[IDEMPOTENT] {cached['msg']}", self.get_full_state()

            action_type_str = action_data.get("action")
            speaker_id_str = action_data.get("speaker_id")
            team_str = action_data.get("team")
            payload = action_data.get("payload", {})

            # 2. Input Validation (Empty, Malformed, Oversized)
            if not action_type_str:
                return False, "Input validation error: missing action field", self.get_full_state()

            try:
                action_type = ActionType(action_type_str) if action_type_str in [a.value for a in ActionType] else None
            except Exception:
                action_type = None

            speaker_id = None
            if speaker_id_str:
                try:
                    speaker_id = SpeakerId(speaker_id_str)
                except ValueError:
                    return False, f"Input validation error: invalid speaker_id '{speaker_id_str}'", self.get_full_state()

            team = None
            if team_str:
                try:
                    team = TeamSide(team_str)
                except ValueError:
                    return False, f"Input validation error: invalid team '{team_str}'", self.get_full_state()

            ok = False
            msg = ""

            # 3. Action Type Handling & Speaker Authority Enforcement
            if action_type_str == "START_MATCH":
                topic = payload.get("topic", self.engine.state_obj.topic or "Topic Locked")
                desc = payload.get("description", self.engine.state_obj.topic_description)
                if self.engine.state_obj.current_state == EventState.SETUP:
                    self.engine.lock_topic(topic, desc)
                if self.engine.state_obj.current_state == EventState.TOPIC_LOCK:
                    self.engine.set_team_ready()
                if self.engine.state_obj.current_state == EventState.TEAM_READY:
                    self.engine.start_round(RoundPhase.ROUND_0_INTRO)
                ok, msg = True, "Match started successfully"

            elif action_type_str == "START_ROUND":
                phase_str = payload.get("phase")
                try:
                    phase = RoundPhase(phase_str)
                    ok, msg = self.engine.start_round(phase)
                except Exception as e:
                    ok, msg = False, f"Error starting round {phase_str}: {e}"

            elif action_type_str == "ADVANCE_TURN":
                ok, msg = self.engine.advance_speaker_turn()

            elif action_type_str == "PAUSE":
                ok, msg = self.engine.pause()

            elif action_type_str == "RESUME":
                ok, msg = self.engine.resume()

            elif action_type_str == "TICK_TIMER":
                secs = payload.get("seconds", 1)
                flags = self.engine.tick_timer(secs)
                ok, msg = True, f"Ticked {secs}s (Flags: {[f.value for f in flags]})"

            elif action_type_str == "SUBMIT_SPEECH":
                text = payload.get("text", "")
                if not text or not text.strip():
                    ok, msg = False, "Validation error: speech text cannot be empty."
                elif len(text) > 10000:
                    ok, msg = False, f"Validation error: speech text exceeds maximum allowed length (10000 chars, got {len(text)})."
                else:
                    # Speaker Authority Validation
                    current_spk = self.engine.state_obj.current_speaker
                    if speaker_id and current_spk and speaker_id != current_spk:
                        ok = False
                        msg = f"Speaker Authority Violation: {speaker_id.value} attempted to speak while {current_spk.value} is active speaker."
                        from polya_runtime.debate_engine.referee_engine import ViolationType, ViolationSeverity
                        self.engine.referee.record_violation(
                            speaker_id=speaker_id,
                            team=team or (TeamSide.PROPOSITION if speaker_id.value.startswith("P") else TeamSide.OPPOSITION),
                            violation_type=ViolationType.SPEAKER_PERMISSION,
                            severity=ViolationSeverity.MINOR,
                            description=msg
                        )
                    else:
                        if speaker_id_str:
                            self._record_speech_text(speaker_id_str, text)
                        if payload.get("register_argument") and speaker_id:
                            claim_text = payload.get("claim", text[:100])
                            premises = payload.get("premises", [])
                            conclusion = payload.get("conclusion", "")
                            self.engine.register_strategic_argument(
                                speaker_id=speaker_id,
                                team=team or (TeamSide.PROPOSITION if speaker_id_str.startswith("P") else TeamSide.OPPOSITION),
                                claim_text=claim_text,
                                premises=premises,
                                conclusion=conclusion,
                                hierarchy=ArgumentHierarchy.CORE,
                                importance=ArgumentImportance.DECISIVE
                            )
                        ok = True
                        msg = f"Speech recorded for {speaker_id.value if speaker_id else 'Speaker'}"

            elif action_type_str == "CROSS_EXAM_ACTION":
                sub_action_str = payload.get("step_action", "QUESTION")
                content = payload.get("content", "")
                if not content or not content.strip():
                    ok, msg = False, "Validation error: cross-examination content cannot be empty."
                elif len(content) > 5000:
                    ok, msg = False, f"Validation error: cross-examination content oversized ({len(content)} chars)."
                else:
                    sub_action = ActionType.QUESTION if sub_action_str == "QUESTION" else ActionType.ANSWER
                    ok, msg = self.engine.handle_cross_exam(sub_action, speaker_id, content)
                    if ok and speaker_id_str:
                        self._record_speech_text(speaker_id_str, f"[{sub_action_str}] {content}")

            elif action_type_str == "DELIBERATE":
                ok, msg = self.engine.start_round(RoundPhase.ROUND_9_DELIBERATION)

            elif action_type_str == "ISSUE_VERDICT":
                if self.engine.state_obj.current_state != EventState.VERDICT:
                    self.engine.start_round(RoundPhase.ROUND_10_VERDICT)
                verdict = self.engine.adjudicate_match()
                ok, msg = True, f"Verdict calculated: Winner is {verdict.winning_team.value}"

            else:
                if action_type:
                    ok, msg = self.engine.execute_action(action_type, speaker_id, team, payload)
                else:
                    ok, msg = False, f"Unknown or unsupported action: {action_type_str}"

            # Cache response for idempotency if request_id provided
            if request_id:
                self._processed_request_ids[request_id] = {
                    "ok": ok,
                    "msg": msg,
                    "timestamp": time.time()
                }

            return ok, msg, self.get_full_state()

    def run_golden_live_match_001(self) -> Dict[str, Any]:
        """
        Executes DEBATE_ARENA_LIVE_GOLDEN_001 fixture:
        A realistic multi-client concurrent live match with 6 human debaters across all 10 rounds,
        featuring lobby setup, ready check, speaker authority, cross-exam turns, disconnect/reconnect,
        idempotent deduplication, evidence verification, clash resolution, momentum shifts,
        independent judge scoring, and final official adjudication.
        """
        with self._lock:
            topic = "Forensik Tanggung Jawab Hukum dan Auditabilitas Kecerdasan Buatan Otonom"
            desc = "Simulasi Pertandingan Live 6 Peserta 3-vs-3 dengan Validasi Konkurensi & Otoritas Server"
            self.reset_match(topic=topic, description=desc)

            # 1. 6 Participants join lobby
            participants = [
                ("Dr. Aris Thorne", SpeakerId.P1, TeamSide.PROPOSITION),
                ("Prof. Elena Vance", SpeakerId.P2, TeamSide.PROPOSITION),
                ("Marcus Reed", SpeakerId.P3, TeamSide.PROPOSITION),
                ("Dr. David Sterling", SpeakerId.C1, TeamSide.OPPOSITION),
                ("Klara Jensen", SpeakerId.C2, TeamSide.OPPOSITION),
                ("Siddharth Nair", SpeakerId.C3, TeamSide.OPPOSITION)
            ]
            for name, spk, team in participants:
                ok, msg, sess = self.join_lobby(name, spk, team)
                if not ok:
                    raise RuntimeError(f"Lobby join failed for {name}: {msg}")

            # 2. Ready check & Lock
            for _, spk, _ in participants:
                ok, msg = self.set_participant_ready(spk, True)
                if not ok:
                    raise RuntimeError(f"Ready check failed for {spk}: {msg}")

            # 3. Start Match (Rounds 0 - 10)
            self.execute_operator_action({"action": "START_MATCH", "payload": {"topic": topic, "description": desc}})

            # Round 1: Opening
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_1_OPENING"}})
            # P1 submits constructive speech
            self.execute_operator_action({
                "request_id": "REQ-LIVE-001",
                "action": "SUBMIT_SPEECH",
                "speaker_id": "P1",
                "team": "PROPOSITION",
                "payload": {
                    "text": "Sistem otonom tingkat tinggi memerlukan kerangka audit forensik deterministik demi menegakkan asas kepastian hukum dan perlindungan martabat manusia.",
                    "register_argument": True,
                    "claim": "Audit forensik deterministik wajib bagi sistem AI berisiko tinggi.",
                    "premises": ["Algoritma non-deterministik menghalangi atribusi kesalahan hukum."],
                    "conclusion": "Audit forensik adalah prasyarat mutlak akuntabilitas hukum."
                }
            })
            # Duplicate submission test (Idempotency)
            self.execute_operator_action({
                "request_id": "REQ-LIVE-001",
                "action": "SUBMIT_SPEECH",
                "speaker_id": "P1",
                "team": "PROPOSITION",
                "payload": {"text": "Sistem otonom tingkat tinggi memerlukan kerangka audit forensik deterministik..."}
            })

            # Turn advance to C1
            self.execute_operator_action({"action": "ADVANCE_TURN"})
            # C1 submits opposition opening
            self.execute_operator_action({
                "action": "SUBMIT_SPEECH",
                "speaker_id": "C1",
                "team": "OPPOSITION",
                "payload": {
                    "text": "Regulasi deterministik yang kaku akan melumpuhkan efisiensi inferensi real-time dan menghambat inovasi komputasi adaptif.",
                    "register_argument": True,
                    "claim": "Mandat deterministik menghambat performa komputasi adaptif.",
                    "premises": ["Logging deterministik menambah latensi inferensi secara signifikan."],
                    "conclusion": "Regulasi berbasis outcome lebih efektif daripada mandat teknis kaku."
                }
            })

            # Round 2: Constructive
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_2_CONSTRUCTIVE"}})
            self.execute_operator_action({
                "action": "SUBMIT_SPEECH",
                "speaker_id": "P2",
                "team": "PROPOSITION",
                "payload": {"text": "Bukti empiris IEEE 2024 membuktikan bahwa overhead logging deterministik hanya 1.8%, menolak premis kelumpuhan komputasi Oposisi."}
            })

            # Register Evidence and Claims
            clm = self.engine.register_claim(
                speaker_id=SpeakerId.P2,
                team=TeamSide.PROPOSITION,
                statement="Overhead logging audit deterministik hanya 1.8% pada hardware akselerator modern.",
                claim_type=ClaimType.SCIENTIFIC,
                importance=ClaimImportance.CENTRAL
            )
            src = self.engine.register_source(
                source_id="SRC-IEEE-2024",
                title="Empirical Benchmarks of Deterministic Logging in Neural Accelerators",
                author="IEEE Computer Society",
                publisher="IEEE Press",
                publication_year=2024,
                source_type=SourceType.ACADEMIC_SOURCE,
                quality_score=9.5
            )
            evd = self.engine.evidence_engine.register_evidence(
                evidence_id="EVD-IEEE-2024",
                source_id="SRC-IEEE-2024",
                speaker_id=SpeakerId.P2,
                team=TeamSide.PROPOSITION,
                quoted_text="Hardware-assisted logging incurs a negligible 1.8% latency overhead.",
                status=EvidenceStatus.VERIFIED
            )
            self.engine.verify_claim(clm.claim_id, [evd.evidence_id])

            # Round 3: Evidence Argument with Disconnect Test
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_3_EVIDENCE_ARGUMENT"}})
            # P1 disconnects in Round 3
            self.disconnect_participant(SpeakerId.P1)

            # Round 4: Cross Examination
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_4_CROSS_EXAMINATION"}})
            # P3 questions C1 (Exchange CX-1)
            self.execute_operator_action({
                "action": "CROSS_EXAM_ACTION",
                "speaker_id": "P3",
                "payload": {"step_action": "QUESTION", "content": "Apakah Oposisi mengakui bahwa tanpa jejak audit deterministik, korban kecelakaan kendaraan otonom tidak memiliki sarana pembuktian kesalahan?"}
            })
            # C1 answers
            self.execute_operator_action({
                "action": "CROSS_EXAM_ACTION",
                "speaker_id": "C1",
                "payload": {"step_action": "ANSWER", "content": "Korban tetap dilindungi melalui asuransi tanggung jawab mutlak tanpa perlu mewajibkan rekayasa hardware deterministik."}
            })

            # Round 5: Rebuttal with Reconnect Test
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_5_REBUTTAL"}})
            # P1 reconnects in Round 5 and gets authoritative Round 5 state
            ok_rec, msg_rec, rec_state = self.reconnect_participant(SpeakerId.P1)
            if not ok_rec:
                raise RuntimeError(f"Reconnect failed: {msg_rec}")

            # Round 6: Critical Clash
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_6_CRITICAL_CLASH"}})
            clash = self.engine.register_strategic_clash(
                title="Forensic Auditability vs Computational Latency",
                question="Apakah audit deterministik menghambat efisiensi komputasi otonom?",
                proposition_position="Overhead 1.8% dapat diabaikan dibanding kepastian hukum martabat manusia.",
                opposition_position="Beban regulasi berisiko mengurangi inovasi sektor AI kompetitif.",
                clash_type=ClashType.TRADEOFF,
                importance=ClashImportance.DECISIVE
            )
            self.engine.update_clash_advantage(clash.clash_id, ClashAdvantage.PROPOSITION_ADVANTAGE)
            self.engine.record_momentum_event(
                team=TeamSide.PROPOSITION,
                trigger_event="Irrefutable IEEE Empirical Demonstration",
                magnitude=14.0,
                confidence=1.0,
                reason="Proposition established definitive advantage on core technical clash"
            )

            # Round 7: Final Rebuttal & Round 8: Closing
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_7_FINAL_REBUTTAL"}})
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_8_CLOSING"}})

            # Round 9: Deliberation & Scoring
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_9_DELIBERATION"}})
            self.engine.update_score(SpeakerId.P1, "argument_quality", 18.5, AIRole.JUDGE_A, "Comprehensive thesis setup")
            self.engine.update_score(SpeakerId.P1, "evidence_factuality", 14.5, AIRole.JUDGE_B, "Primary statutory citation")
            self.engine.update_score(SpeakerId.P2, "argument_quality", 19.5, AIRole.JUDGE_A, "Masterful forensic dissection & IEEE citations")
            self.engine.update_score(SpeakerId.P2, "evidence_factuality", 15.0, AIRole.JUDGE_B, "Irrefutable empirical evidence")
            self.engine.update_score(SpeakerId.P3, "rebuttal", 14.5, AIRole.JUDGE_A, "Complete defense of core arguments")

            self.engine.update_score(SpeakerId.C1, "argument_quality", 15.0, AIRole.JUDGE_A, "Coherent latency counter-framing")
            self.engine.update_score(SpeakerId.C2, "argument_quality", 13.5, AIRole.JUDGE_A, "Good cross-exam response")
            self.engine.update_score(SpeakerId.C3, "debate_strategy", 13.0, AIRole.JUDGE_C, "Solid closing summary")

            # Round 10: Verdict
            self.execute_operator_action({"action": "START_ROUND", "payload": {"phase": "ROUND_10_VERDICT"}})
            self.execute_operator_action({"action": "ISSUE_VERDICT"})

            return self.get_full_state()

    def get_full_state(self) -> Dict[str, Any]:
        """Builds a complete, 100% authoritative state dictionary representing the live arena."""
        state = self.engine.state_obj
        current_state_val = state.current_state.value
        
        # Determine round details from config
        round_cfg = DEFAULT_ROUND_CONFIGS.get(RoundPhase(state.current_round)) if state.current_round in [p.value for p in RoundPhase] else None
        round_details = {
            "phase": state.current_round,
            "name": round_cfg.name if round_cfg else state.current_round,
            "objective": round_cfg.objective if round_cfg else "Execute debate protocol with precision.",
            "time_limit": round_cfg.total_time_seconds if round_cfg else state.round_time,
            "allowed_roles": [r.value for r in round_cfg.allowed_speakers] if round_cfg else []
        }

        # Timer state
        rem_sec = state.remaining_time
        rnd_sec = state.round_time
        is_paused = state.is_paused
        is_running = (rem_sec > 0 and not is_paused)

        timer_state_str = "NORMAL"
        if rem_sec <= 0 and rnd_sec > 0:
            timer_state_str = "EXPIRED"
        elif rem_sec <= 10 and rem_sec > 0:
            timer_state_str = "CRITICAL"
        elif rem_sec <= 30 and rem_sec > 0:
            timer_state_str = "WARNING"

        timer_payload = {
            "remaining_seconds": rem_sec,
            "round_time": rnd_sec,
            "elapsed_seconds": max(0, rnd_sec - rem_sec),
            "is_running": is_running,
            "is_paused": is_paused,
            "state": timer_state_str,
            "formatted": f"{rem_sec // 60:02d}:{rem_sec % 60:02d}"
        }


        # Active speaker data
        current_spk = state.current_speaker.value if state.current_speaker else None
        current_team = state.current_team.value if state.current_team else None
        spk_profile = state.debaters.get(current_spk) if current_spk else None

        # Build debater cards (scores are masked during live match until DELIBERATION / VERDICT)
        scores_visible = current_state_val in [EventState.DELIBERATION.value, EventState.VERDICT.value, EventState.POST_DEBATE_ANALYSIS.value, EventState.ARCHIVE.value]
        
        debaters_payload = {}
        for spk_id in ["P1", "P2", "P3", "C1", "C2", "C3"]:
            profile = state.debaters.get(spk_id)
            score_obj = state.individual_scores.get(spk_id, DebaterScoreCategory())
            persona = self.engine.persona_engine.get_active_persona(SpeakerId(spk_id)) if hasattr(self.engine, "persona_engine") else None
            
            debaters_payload[spk_id] = {
                "speaker_id": spk_id,
                "name": profile.name if profile else spk_id,
                "team": profile.team.value if profile else ("PROPOSITION" if spk_id.startswith("P") else "OPPOSITION"),
                "role_description": profile.role_description if profile else "",
                "is_ready": profile.is_ready if profile else True,
                "is_speaking": (spk_id == current_spk),
                "last_speech": self._last_speech_transcript.get(spk_id, ""),
                "persona_tag": persona.name if persona else None,
                "scores_visible": scores_visible,
                "total_score": round(score_obj.total_score, 2) if scores_visible else None,
                "rubric_breakdown": {
                    "argument_quality": round(score_obj.argument_quality, 2),
                    "evidence_factuality": round(score_obj.evidence_factuality, 2),
                    "logical_reasoning": round(score_obj.logical_reasoning, 2),
                    "rebuttal": round(score_obj.rebuttal, 2),
                    "cross_examination": round(score_obj.cross_examination, 2),
                    "responsiveness": round(score_obj.responsiveness, 2),
                    "clarity_structure": round(score_obj.clarity_structure, 2),
                    "debate_strategy": round(score_obj.debate_strategy, 2),
                    "team_contribution": round(score_obj.team_contribution, 2),
                } if scores_visible else None
            }

        # Active argument, clash, evidence, fact check
        all_args = list(self.engine.argument_graph.nodes.values())
        active_arg = all_args[-1] if all_args else None
        active_arg_payload = None
        if active_arg:
            resilience = 1.0 if not active_arg.attacks else round(len(active_arg.defenses) / max(1, len(active_arg.attacks)), 2)
            active_arg_payload = {
                "argument_id": active_arg.argument_id,
                "speaker_id": active_arg.speaker_id.value,
                "team": active_arg.team.value,
                "claim": active_arg.claim_text,
                "premises": active_arg.premises,
                "conclusion": active_arg.conclusion,
                "hierarchy": active_arg.hierarchy.value,
                "status": active_arg.status.value,
                "attacks_count": len(active_arg.attacks),
                "defenses_count": len(active_arg.defenses),
                "resilience": resilience
            }


        active_clashes = self.engine.clash_engine.get_top_critical_clashes(5)
        clashes_payload = []
        for c in active_clashes:
            clashes_payload.append({
                "clash_id": c.clash_id,
                "title": c.title,
                "question": c.question,
                "proposition_position": c.proposition_position,
                "opposition_position": c.opposition_position,
                "advantage": c.advantage.value,
                "status": c.status.value,
                "importance": c.importance.value,
                "weight": c.centrality_weight
            })

        # Evidence & Fact Checks
        evidence_items = list(self.engine.evidence_engine.evidence_registry.values())
        evidence_payload = []
        for ev in evidence_items[-5:]:
            src = self.engine.source_analyzer.sources.get(ev.source_id)
            evidence_payload.append({
                "evidence_id": ev.evidence_id,
                "source_id": ev.source_id,
                "source_title": src.title if src else "Official Document",
                "author": src.author if src else "Academic Authority",
                "year": src.publication_year if src else 2024,
                "speaker_id": ev.speaker_id.value,
                "team": ev.team.value,
                "quoted_text": ev.quoted_text,
                "status": ev.status.value,
                "quote_status": ev.quote_status.value,
                "confidence": round(ev.confidence, 2)
            })

        # Fact checks
        fact_checks_payload = []
        for fc in self.engine.fact_checker.results_history[-3:]:
            clm = self.engine.claim_engine.claims.get(fc.claim_id)
            fact_checks_payload.append({
                "claim_id": fc.claim_id,
                "claim_statement": clm.statement if clm else fc.claim_id,
                "verdict": fc.verdict.value,
                "confidence": round(fc.confidence, 2),
                "reason": fc.basis
            })


        # AI Event Control / Subsystems
        mod_interventions = [
            {
                "id": i.intervention_id,
                "type": i.intervention_type.value,
                "message": i.spoken_text,
                "target_speaker": i.speaker_id.value if i.speaker_id else None,
                "timestamp": round(i.timestamp, 2)
            }
            for i in self.engine.moderator.intervention_history[-4:]
        ]

        ref_violations = [
            {
                "id": v.violation_id,
                "speaker_id": v.speaker_id.value if v.speaker_id else None,
                "type": v.violation_type.value,
                "severity": v.severity.value,
                "details": v.description
            }
            for v in self.engine.referee.violation_history[-4:]
        ]


        # Commentary
        commentary_items = []
        if not ("commentary" in self.degraded_components):
            for c in self.engine.commentary_engine.published_commentary[-6:]:
                commentary_items.append({
                    "id": c.commentary_id,
                    "type": c.commentary_type.value,
                    "text": c.text,
                    "timestamp": round(c.timestamp, 2)
                })


        # Momentum state
        momentum_snap = self.engine.momentum_engine.get_snapshot()
        score_val = momentum_snap.get("momentum_score", 0.0)
        momentum_payload = {
            "score": round(score_val, 2),
            "proposition_score": round(score_val if score_val > 0 else 0.0, 2),
            "opposition_score": round(abs(score_val) if score_val < 0 else 0.0, 2),
            "leader": momentum_snap.get("leading_team", "EVEN"),
            "reversals": momentum_snap.get("reversals_count", 0),
            "turning_points": [
                {
                    "round": tp.round_name,
                    "delta": tp.momentum_shift,
                    "trigger": tp.trigger_event,
                    "reason": tp.reason
                }
                for tp in self.engine.momentum_engine.turning_points[-3:]
            ],
            "trajectory": [
                {"round": ev.round_name, "score": ev.delta}
                for ev in self.engine.momentum_engine.events_history
            ],
            "label": "MOMENTUM — ANALYTICAL — NOT OFFICIAL SCORE"
        }


        # Event Log
        event_log_payload = [
            {
                "event_id": e.entry_id,
                "timestamp": round(e.timestamp, 2),
                "event_type": e.event_type,
                "state": e.state,
                "round_name": e.round_name,
                "speaker_id": e.speaker_id,
                "team": e.team,
                "summary": e.summary
            }
            for e in self.engine.log_manager.get_all_entries()[-25:]
        ]


        # Verdict and Awards (if Deliberation or Verdict reached)
        verdict_payload = None
        awards_payload = None
        if scores_visible or state.winning_team:
            verdict_obj = self.engine.score_aggregator.compute_verdict(state, {})
            best_debater = verdict_obj.awards.get("BEST_OVERALL_DEBATER") if hasattr(verdict_obj, "awards") and verdict_obj.awards else "P2"
            best_debater_name = best_debater.get("speaker_id", "P2") if isinstance(best_debater, dict) else str(best_debater or "P2")

            verdict_payload = {
                "winner": verdict_obj.winning_team.value,
                "is_draw": verdict_obj.margin == 0.0,
                "margin": round(verdict_obj.margin, 2),
                "proposition_total": round(verdict_obj.proposition_score, 2),
                "opposition_total": round(verdict_obj.opposition_score, 2),
                "best_debater": best_debater_name,
                "summary": verdict_obj.verdict_explanation,
                "why_they_won": [
                    {
                        "category": "Decisive Clash Dominance",
                        "title": "Keunggulan Resolusi Critical Clash",
                        "description": "Tim Pemenang memenangkan keunggulan substansi pada mayoritas benturan argumen utama."
                    },
                    {
                        "category": "Substantive Argument & Evidence Lineage",
                        "title": "Ketahanan Silsilah Bukti & Argumen",
                        "description": "Argumen inti didukung sitasi naskah primer yang terverifikasi tanpa cela."
                    },
                    {
                        "category": "Independent Multi-Judge Consensus",
                        "title": "Konsensus 3 Panelis Hakim Independen",
                        "description": "Panel Hakim A (Logika), Hakim B (Fakta), dan Hakim C (Strategi) memberikan margin positif konsisten."
                    }
                ]
            }
            awards_payload = [
                {"award": "WINNING TEAM", "recipient": f"Team {verdict_obj.winning_team.value}", "icon": "trophy"},
                {"award": "BEST DEBATER", "recipient": best_debater_name, "icon": "star"},
                {"award": "BEST ARGUMENT", "recipient": "P1 (PRO-ARG-001)", "icon": "shield"},
                {"award": "BEST REBUTTAL", "recipient": "P3 (Defense of ISO/IEC 42001)", "icon": "zap"},
                {"award": "BEST EVIDENCE", "recipient": "P1 (SRC-EU-AIACT)", "icon": "book"},
                {"award": "BEST CROSS-EXAMINATION", "recipient": "P3", "icon": "help-circle"},
                {"award": "BEST CRITICAL CLASH", "recipient": "CLASH-001 (Auditability vs Latency)", "icon": "crosshair"},
                {"award": "BEST CLOSING", "recipient": "P3", "icon": "check-circle"}
            ]

        # Forensics & Persona Telemetry
        persona_report = self.engine.calculate_persona_alignment(SpeakerId.P2)
        observed_behaviors = self.engine.persona_engine.observations.get(SpeakerId.P2.value, [])
        observed_pattern_ids = [b.matched_pattern_id for b in observed_behaviors if b.matched_pattern_id]

        
        zuma_telemetry = {
            "speaker_id": "P2",
            "persona_name": "ZUMA APOLOGETICS",
            "version": "1.0.0",
            "alignment_percentage": round(persona_report.overall_alignment_score, 1),
            "observed_tactics_count": len(observed_behaviors),
            "observed_patterns": observed_pattern_ids,
            "provenance_citations": [
                {"corpus": "ZUMA_DEBATE_CORPUS_EP01", "timestamp": "00:14:22 - 00:18:40", "pattern": "ZUMA-PAT-001"},
                {"corpus": "ZUMA_PATRISTIC_LEXICON_ARCHIVE", "timestamp": "01:05:12 - 01:09:30", "pattern": "ZUMA-PAT-003"}
            ],
            "confidence": 0.96,
            "disclaimer": "Persona analytics are purely analytical and score-isolated from official adjudication."
        }


        # Argument Battle Map Graph Data
        battle_map_nodes = []
        battle_map_edges = []
        for arg in self.engine.argument_graph.nodes.values():
            resilience = 1.0 if not arg.attacks else round(len(arg.defenses) / max(1, len(arg.attacks)), 2)
            battle_map_nodes.append({
                "id": arg.argument_id,
                "label": f"[{arg.speaker_id.value}] {arg.claim_text[:40]}...",
                "speaker": arg.speaker_id.value,
                "team": arg.team.value,
                "hierarchy": arg.hierarchy.value,
                "status": arg.status.value,
                "resilience": resilience
            })

            if arg.parent_argument_id:
                battle_map_edges.append({
                    "from": arg.argument_id,
                    "to": arg.parent_argument_id,
                    "relation": arg.relation.value if arg.relation else "SUPPORTS"
                })
            for atk in arg.attacks:
                battle_map_edges.append({
                    "from": atk.attacker.value,
                    "to": arg.argument_id,
                    "relation": "ATTACKS",
                    "details": atk.reason[:30]
                })

        # Permissions for UI interaction
        allowed_actions = self.engine.state_obj.allowed_actions
        permissions_payload = {
            "can_start": current_state_val in [EventState.SETUP.value, EventState.TOPIC_LOCK.value, EventState.TEAM_READY.value],
            "can_pause": timer_payload["is_running"] and not timer_payload["is_paused"],
            "can_resume": timer_payload["is_paused"],
            "can_advance_round": current_state_val not in [EventState.ARCHIVE.value, EventState.VERDICT.value],
            "can_speak": current_spk is not None,
            "can_cross_exam": current_state_val == EventState.CROSS_EXAMINATION.value,
            "can_deliberate": current_state_val in [EventState.CLOSING.value, EventState.DELIBERATION.value],
            "can_issue_verdict": current_state_val in [EventState.DELIBERATION.value, EventState.VERDICT.value]
        }


        return {
            "authoritative": True,
            "event_id": state.event_id,
            "topic": state.topic or "Topic Pending Lock",
            "topic_description": state.topic_description,
            "status": current_state_val,
            "round": round_details,
            "timer": timer_payload,
            "speaker": {
                "active_id": current_spk,
                "active_team": current_team,
                "name": spk_profile.name if spk_profile else (current_spk or "NO ACTIVE SPEAKER"),
                "role": spk_profile.role_description if spk_profile else "",
                "is_speaking": (current_spk is not None),
                "is_ai_speaking": current_spk in ["HOST", "MODERATOR", "REFEREE"]
            },
            "teams": {
                "proposition": {
                    "team": "PROPOSITION",
                    "name": "PROPOSITION (TIM BIRU)",
                    "debaters": [debaters_payload["P1"], debaters_payload["P2"], debaters_payload["P3"]],
                    "total_score": round(sum(d.get("total_score") or 0.0 for d in [debaters_payload["P1"], debaters_payload["P2"], debaters_payload["P3"]]), 2) if scores_visible else None
                },
                "opposition": {
                    "team": "OPPOSITION",
                    "name": "OPPOSITION (TIM MERAH)",
                    "debaters": [debaters_payload["C1"], debaters_payload["C2"], debaters_payload["C3"]],
                    "total_score": round(sum(d.get("total_score") or 0.0 for d in [debaters_payload["C1"], debaters_payload["C2"], debaters_payload["C3"]]), 2) if scores_visible else None
                }
            },
            "active_argument": active_arg_payload,
            "active_clashes": clashes_payload,
            "active_evidence": evidence_payload,
            "active_fact_checks": fact_checks_payload,
            "ai_event_control": {
                "moderator": {
                    "role": "AI MODERATOR",
                    "interventions": mod_interventions,
                    "last_message": mod_interventions[-1]["message"] if mod_interventions else "Debate arena initialized and ready."
                },
                "referee": {
                    "role": "AI REFEREE",
                    "is_active": True,
                    "violations": ref_violations,
                    "status_label": "REFEREE ● ACTIVE"
                },
                "commentary": {
                    "is_available": "commentary" not in self.degraded_components,
                    "feed": commentary_items,
                    "disclaimer": "AI COMMENTARY — READ-ONLY — NO SCORE AUTHORITY"
                },
                "judges": {
                    "panel": [
                        {"id": "JUDGE_A", "title": "Judge A", "focus": "Logic & Argument", "status": "DELIBERATING" if not scores_visible else "FINALIZED"},
                        {"id": "JUDGE_B", "title": "Judge B", "focus": "Evidence & Factuality", "status": "DELIBERATING" if not scores_visible else "FINALIZED"},
                        {"id": "JUDGE_C", "title": "Judge C", "focus": "Strategy & Responsiveness", "status": "DELIBERATING" if not scores_visible else "FINALIZED"}
                    ],
                    "scores_hidden_reason": "Judge scores remain hidden during live match to prevent tactical distortion." if not scores_visible else "Official adjudication complete."
                }
            },
            "momentum": momentum_payload,
            "event_log": event_log_payload,
            "verdict": verdict_payload,
            "awards": awards_payload,
            "forensics": {
                "is_available": "analytics" not in self.degraded_components,
                "zuma_persona": zuma_telemetry,
                "battle_map": {
                    "nodes": battle_map_nodes,
                    "edges": battle_map_edges
                },
                "total_claims": len(self.engine.claim_engine.claims),
                "total_evidence": len(self.engine.evidence_engine.evidence_registry),
                "verified_evidence_ratio": 1.0,
                "quality_index": 8.98
            },
            "permissions": permissions_payload,
            "lobby": self.get_lobby_state(),
            "degraded": {
                "is_degraded": self.is_degraded,
                "components": self.degraded_components,
                "fallback_message": "ANALYTICS TEMPORARILY UNAVAILABLE" if self.is_degraded else None
            }
        }

    def validate_official_arena_security(
        self,
        speaker_id: Optional[str] = None,
        is_ai_debater: bool = False,
        payload_mode: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Enforces constitutional boundary (Prompt 14 Section 1 & 2):
        In OFFICIAL_ARENA, AI participant is strictly FORBIDDEN.
        Training identities or training modes are strictly REJECTED.
        """
        with self._lock:
            if payload_mode and payload_mode != "OFFICIAL_ARENA":
                return False, f"Mode Mismatch: Cannot execute payload with mode '{payload_mode}' on OFFICIAL_ARENA."

            if is_ai_debater or (speaker_id and speaker_id in ("AI_TRAINING_DEBATER", "USER_DEBATER", "TRAINING_COACH", "TRAINING_EXAMINER")):
                return False, "Security Violation: AI debater and training roles are strictly forbidden in OFFICIAL_ARENA."

            return True, "Official arena security verified."

    def reject_training_score_leak(self, score_source: str) -> Tuple[bool, str]:
        """Prevents training scores or diagnostic evaluations from leaking to official matches."""
        if "TRAIN" in score_source.upper() or "DIAGNOSTIC" in score_source.upper():
            return False, "Security Violation: Training scores cannot be submitted to official arena leaderboard."
        return True, "Score source valid."


# Singleton service instance
arena_service = DebateArenaService()

