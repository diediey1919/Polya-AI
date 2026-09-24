"""
Debate Arena - Moderator Engine
Adheres to 04_DEBATE_MODERATOR_REFEREE_ENGINE.md.
Controls procedural communication, announcements, neutral interventions, and broadcast flow.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    EventState,
    SpeakerId,
    TeamSide,
    EventStateObject
)
from polya_runtime.debate_engine.referee_engine import RefereeDecision, ProceduralViolation, PenaltyType

class InterventionType(str, Enum):
    EVENT_OPENING = "EVENT_OPENING"
    TOPIC_ANNOUNCEMENT = "TOPIC_ANNOUNCEMENT"
    TEAM_INTRODUCTION = "TEAM_INTRODUCTION"
    RULE_BRIEFING = "RULE_BRIEFING"
    ROUND_ANNOUNCEMENT = "ROUND_ANNOUNCEMENT"
    SPEAKER_ANNOUNCEMENT = "SPEAKER_ANNOUNCEMENT"
    TIME_WARNING = "TIME_WARNING"
    TIME_EXPIRED = "TIME_EXPIRED"
    RELEVANCE_WARNING = "RELEVANCE_WARNING"
    REPETITION_WARNING = "REPETITION_WARNING"
    EVIDENCE_REQUEST = "EVIDENCE_REQUEST"
    INTERRUPTION_CONTROL = "INTERRUPTION_CONTROL"
    PROCEDURAL_WARNING = "PROCEDURAL_WARNING"
    DELIBERATION_ANNOUNCEMENT = "DELIBERATION_ANNOUNCEMENT"
    VERDICT_ANNOUNCEMENT = "VERDICT_ANNOUNCEMENT"

@dataclass
class ModeratorIntervention:
    intervention_id: str = field(default_factory=lambda: f"INT-{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    state: str = ""
    round_name: str = ""
    speaker_id: Optional[SpeakerId] = None
    team: Optional[TeamSide] = None
    intervention_type: InterventionType = InterventionType.PROCEDURAL_WARNING
    spoken_text: str = ""
    reason: str = ""
    score_effect: str = "NONE"

class ModeratorEngine:
    """Procedural host and announcer for Debate Arena."""

    def __init__(self):
        self.intervention_history: List[ModeratorIntervention] = []

    def announce_event_opening(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = (
            f"Selamat datang di Debate Arena. Hari ini kita akan menyaksikan debat terstruktur 3 lawan 3 "
            f"yang menguji ketajaman nalar, integritas bukti, dan konsistensi argumentasi."
        )
        return self._record_intervention(state_obj, None, None, InterventionType.EVENT_OPENING, text, "Event opening announced.")

    def announce_topic(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = (
            f"Mosi resmi yang telah dikunci untuk sesi debat ini adalah: \"{state_obj.topic}\". "
            f"Kedua tim terikat pada mosi ini tanpa perubahan."
        )
        return self._record_intervention(state_obj, None, None, InterventionType.TOPIC_ANNOUNCEMENT, text, "Topic locked motion announced.")

    def introduce_teams(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = (
            f"Di sisi Proposisi: P1, P2, dan P3. Di sisi Oposisi: C1, C2, dan C3. "
            f"Kedua tim hadir dalam formasi lengkap dan siap berdialektika."
        )
        return self._record_intervention(state_obj, None, None, InterventionType.TEAM_INTRODUCTION, text, "Both 3-speaker teams introduced.")

    def announce_rule_briefing(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = (
            f"Berikut tata tertib arena: Setiap pembicara wajib mematuhi batas waktu yang telah ditentukan. "
            f"Interupsi hanya diizinkan pada fase yang ditentukan sesuai protokol. "
            f"Seluruh klaim faktual wajib didukung bukti primer atau rujukan kanon yang valid. "
            f"Penilaian dilakukan secara independen oleh panel multi-juri berbasis rubrik 100 poin."
        )
        return self._record_intervention(state_obj, None, None, InterventionType.RULE_BRIEFING, text, "Debate rules briefed.")

    def announce_round_start(self, state_obj: EventStateObject, round_name: str, objective: str) -> ModeratorIntervention:
        text = f"Kita memasuki {round_name}. Tujuan fase ini: {objective}."
        return self._record_intervention(state_obj, None, None, InterventionType.ROUND_ANNOUNCEMENT, text, f"Round {round_name} started.")

    def grant_floor_to_speaker(self, state_obj: EventStateObject, speaker_id: SpeakerId, team: TeamSide) -> ModeratorIntervention:
        team_label = "Tim Proposisi" if team == TeamSide.PROPOSITION else "Tim Oposisi"
        text = f"{team_label}, pembicara {speaker_id.value}, panggung dipersilakan."
        return self._record_intervention(state_obj, speaker_id, team, InterventionType.SPEAKER_ANNOUNCEMENT, text, f"Floor granted to {speaker_id.value}.")

    def announce_time_warning(self, state_obj: EventStateObject, seconds_remaining: int) -> ModeratorIntervention:
        text = f"Peringatan waktu: {seconds_remaining} detik tersisa."
        return self._record_intervention(state_obj, state_obj.current_speaker, state_obj.current_team, InterventionType.TIME_WARNING, text, f"Time warning: {seconds_remaining}s.")

    def announce_time_expired(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = "Waktu habis. Silakan selesaikan kalimat penutup Anda; panggung berpindah ke giliran berikutnya."
        return self._record_intervention(state_obj, state_obj.current_speaker, state_obj.current_team, InterventionType.TIME_EXPIRED, text, "Time expired announced.")

    def handle_referee_rejection(self, state_obj: EventStateObject, decision: RefereeDecision) -> ModeratorIntervention:
        """Generates appropriate neutral procedural communication for a rejected action."""
        action_key = decision.recommended_moderator_action

        if action_key == "ENFORCE_SPEAKER_FLOOR":
            text = f"Interupsi tidak sah. Hak bicara saat ini sepenuhnya berada pada {state_obj.current_speaker.value if state_obj.current_speaker else 'pembicara aktif'}."
        elif action_key == "REJECT_INTERRUPTION":
            text = "Interupsi tidak diizinkan pada fase ini sesuai tata tertib."
        elif action_key == "PASS_FLOOR_TIME_EXPIRED":
            text = "Waktu bicara telah selesai. Panggung dialihkan ke pembicara berikutnya."
        elif action_key == "WARN_ACTION_FORBIDDEN":
            text = f"Aksi tersebut tidak diperkenankan dalam fase {state_obj.current_state.value}."
        elif action_key == "REMIND_PAUSED":
            text = "Debat sedang dijeda. Seluruh aksi dibekukan sementara."
        else:
            text = f"Aksi ditolak oleh wasit: {decision.reason}"

        return self._record_intervention(
            state_obj,
            decision.violation.speaker_id if decision.violation else None,
            decision.violation.team if decision.violation else None,
            InterventionType.PROCEDURAL_WARNING,
            text,
            decision.reason
        )

    def request_relevance(self, state_obj: EventStateObject, speaker_id: SpeakerId) -> ModeratorIntervention:
        text = "Harap fokuskan pernyataan Anda langsung pada mosi dan argumen yang sedang diperdebatkan."
        return self._record_intervention(state_obj, speaker_id, None, InterventionType.RELEVANCE_WARNING, text, "Relevance redirection requested.")

    def request_evidence_citation(self, state_obj: EventStateObject, speaker_id: SpeakerId) -> ModeratorIntervention:
        text = "Harap sebutkan nomor pasal, ayat, atau rujukan naskah primer yang mendasari klaim faktual Anda."
        return self._record_intervention(state_obj, speaker_id, None, InterventionType.EVIDENCE_REQUEST, text, "Evidence citation requested.")

    def announce_deliberation(self, state_obj: EventStateObject) -> ModeratorIntervention:
        text = (
            "Seluruh rangkaian sesi debat telah selesai. Sesi debat resmi ditutup. "
            "Panel juri AI independen saat ini sedang melakukan deliberasi dan audit komprehensif atas 9 kategori penilaian."
        )
        return self._record_intervention(state_obj, None, None, InterventionType.DELIBERATION_ANNOUNCEMENT, text, "Deliberation announced.")

    def announce_verdict(self, state_obj: EventStateObject, winning_team: TeamSide, margin_summary: str = "") -> ModeratorIntervention:
        winner_str = "TIM PROPOSISI" if winning_team == TeamSide.PROPOSITION else "TIM OPOSISI"
        text = (
            f"Berdasarkan hasil audit independen dan agregasi penilaian panel juri, pemenang debat ini adalah: {winner_str}. "
            f"{margin_summary}"
        )
        return self._record_intervention(state_obj, None, winning_team, InterventionType.VERDICT_ANNOUNCEMENT, text, "Official verdict announced.")

    def _record_intervention(
        self,
        state_obj: EventStateObject,
        speaker_id: Optional[SpeakerId],
        team: Optional[TeamSide],
        int_type: InterventionType,
        text: str,
        reason: str
    ) -> ModeratorIntervention:
        intervention = ModeratorIntervention(
            state=state_obj.current_state.value,
            round_name=state_obj.current_round,
            speaker_id=speaker_id,
            team=team,
            intervention_type=int_type,
            spoken_text=text,
            reason=reason
        )
        self.intervention_history.append(intervention)
        return intervention
