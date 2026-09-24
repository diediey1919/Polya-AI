"""
Debate Arena - Speaker Permission Matrix
Adheres to Article 26 of 02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md.
"""

from typing import Dict, Optional, Tuple
from polya_runtime.debate_engine.models import (
    EventState,
    SpeakerId,
    TeamSide,
    ActionType,
    EventStateObject
)

class SpeakerPermissionMatrix:
    """Evaluates strict speaker permissions based on current round, state, and team."""

    # Default assigned speaker for standard phases
    ROUND_SPEAKER_MAP = {
        EventState.INTRODUCTION: [SpeakerId.HOST],
        EventState.RULE_BRIEFING: [SpeakerId.MODERATOR],
        EventState.OPENING: [SpeakerId.P1, SpeakerId.C1],
        EventState.CONSTRUCTIVE: [SpeakerId.P2, SpeakerId.C2],
        EventState.EVIDENCE_ARGUMENT: [SpeakerId.P2, SpeakerId.C2],
        EventState.CROSS_EXAMINATION: [SpeakerId.P1, SpeakerId.P2, SpeakerId.P3, SpeakerId.C1, SpeakerId.C2, SpeakerId.C3],
        EventState.REBUTTAL: [SpeakerId.P3, SpeakerId.C3],
        EventState.CLASH_ROUND: [SpeakerId.P1, SpeakerId.P2, SpeakerId.P3, SpeakerId.C1, SpeakerId.C2, SpeakerId.C3],
        EventState.FINAL_REBUTTAL: [SpeakerId.P3, SpeakerId.C3],
        EventState.CLOSING: [SpeakerId.P1, SpeakerId.C1],
        EventState.VERDICT: [SpeakerId.HOST, SpeakerId.MODERATOR]
    }

    @staticmethod
    def can_speak(state_obj: EventStateObject, speaker_id: SpeakerId) -> Tuple[bool, str]:
        state = state_obj.current_state
        if state == EventState.PAUSED:
            return False, "Debate is currently paused. No speaking allowed."

        if state in (EventState.SETUP, EventState.TOPIC_LOCK, EventState.TEAM_READY, EventState.DELIBERATION, EventState.ARCHIVE):
            return False, f"Speaking is forbidden during {state.value} phase."

        # Host / Moderator Authority
        if speaker_id in (SpeakerId.HOST, SpeakerId.MODERATOR, SpeakerId.REFEREE):
            if state in (EventState.INTRODUCTION, EventState.VERDICT) and speaker_id == SpeakerId.HOST:
                return True, "Host authorized to speak."
            if state == EventState.RULE_BRIEFING and speaker_id == SpeakerId.MODERATOR:
                return True, "Moderator authorized to speak."
            if speaker_id in (SpeakerId.MODERATOR, SpeakerId.REFEREE):
                return True, "Moderator / Referee intervention permitted."

        # Cross examination handled by specific turn logic
        if state == EventState.CROSS_EXAMINATION:
            if state_obj.current_speaker == speaker_id:
                return True, f"{speaker_id.value} is active speaker in Cross-Examination."
            return False, f"{speaker_id.value} is not the designated active speaker in Cross-Examination."

        # Standard Speech Round
        if state_obj.current_speaker is not None:
            if state_obj.current_speaker == speaker_id:
                return True, f"{speaker_id.value} is the designated speaker for this round."
            return False, f"Unauthorized: Current floor belongs to {state_obj.current_speaker.value}, not {speaker_id.value}."

        allowed_speakers = SpeakerPermissionMatrix.ROUND_SPEAKER_MAP.get(state, [])
        if speaker_id in allowed_speakers:
            return True, f"{speaker_id.value} is eligible to speak in {state.value}."

        return False, f"{speaker_id.value} is not permitted to speak during {state.value}."

    @staticmethod
    def can_ask(state_obj: EventStateObject, questioner: SpeakerId, respondent: SpeakerId) -> Tuple[bool, str]:
        state = state_obj.current_state
        if state != EventState.CROSS_EXAMINATION:
            return False, f"Questions are only permitted in CROSS_EXAMINATION, not in {state.value}."

        if questioner == respondent:
            return False, "Speaker cannot cross-examine themselves."

        # Verify opposing teams
        q_debater = state_obj.debaters.get(questioner.value)
        r_debater = state_obj.debaters.get(respondent.value)
        if q_debater and r_debater:
            if q_debater.team == r_debater.team:
                return False, "Cross-examination must be between opposing teams."

        return True, f"{questioner.value} is permitted to ask {respondent.value}."

    @staticmethod
    def can_answer(state_obj: EventStateObject, respondent: SpeakerId) -> Tuple[bool, str]:
        state = state_obj.current_state
        if state != EventState.CROSS_EXAMINATION:
            return False, f"Answers are only valid in CROSS_EXAMINATION, not in {state.value}."
        if state_obj.current_speaker != respondent:
            return False, f"It is not {respondent.value}'s turn to answer."
        return True, f"{respondent.value} is authorized to answer."

    @staticmethod
    def can_interrupt(state_obj: EventStateObject, speaker_id: SpeakerId, interrupt_type: ActionType) -> Tuple[bool, str]:
        state = state_obj.current_state
        if state in (EventState.OPENING, EventState.CLOSING, EventState.DELIBERATION, EventState.VERDICT, EventState.ARCHIVE):
            return False, f"Interruptions are strictly prohibited during {state.value}."

        if interrupt_type == ActionType.POINT_OF_ORDER:
            return True, f"Point of Order permitted by {speaker_id.value} subject to moderator review."
        if interrupt_type == ActionType.POINT_OF_CLARIFICATION:
            if state in (EventState.CONSTRUCTIVE, EventState.EVIDENCE_ARGUMENT):
                return True, f"Point of Clarification permitted during {state.value}."
            return False, f"Point of Clarification not allowed in {state.value}."

        return False, f"Interruption type {interrupt_type.value} not permitted."
