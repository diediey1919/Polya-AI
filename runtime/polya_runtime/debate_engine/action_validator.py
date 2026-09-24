"""
Debate Arena - Action Validator Pipeline
Adheres to Article 27 of 02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md.
"""

from typing import Tuple, Optional, Any, Dict
from polya_runtime.debate_engine.models import (
    ActionType,
    SpeakerId,
    TeamSide,
    EventState,
    EventStateObject
)
from polya_runtime.debate_engine.permission_matrix import SpeakerPermissionMatrix
from polya_runtime.debate_engine.state_machine import DebateStateMachine

class ActionValidator:
    """Validates every incoming action against state, speaker permissions, and rules."""

    @staticmethod
    def validate_action(
        state_obj: EventStateObject,
        action: ActionType,
        speaker_id: Optional[SpeakerId] = None,
        team: Optional[TeamSide] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        
        # 1. State Check
        current_state = state_obj.current_state
        if current_state == EventState.PAUSED and action not in (ActionType.RESUME, ActionType.MODERATOR_INTERVENTION):
            return False, "Debate is paused. Only RESUME or moderator actions are permitted."

        state_def = DebateStateMachine.get_state_definition(current_state)
        if action in state_def.forbidden_actions:
            return False, f"Action '{action.value}' is strictly forbidden in state {current_state.value}."

        if action not in state_def.allowed_actions and action not in (ActionType.PAUSE, ActionType.RESUME, ActionType.MODERATOR_INTERVENTION):
            return False, f"Action '{action.value}' is not permitted in state {current_state.value}."

        # 2. Speaker Permission Check
        if speaker_id is not None:
            if action in (ActionType.SPEAK, ActionType.START_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_EVIDENCE, ActionType.PRESENT_CLAIM, ActionType.REBUT):
                can_spk, reason = SpeakerPermissionMatrix.can_speak(state_obj, speaker_id)
                if not can_spk:
                    return False, reason
            
            elif action == ActionType.QUESTION:
                respondent = payload.get("respondent") if payload else None
                if not respondent:
                    return False, "Question action requires a target respondent."
                can_q, reason = SpeakerPermissionMatrix.can_ask(state_obj, speaker_id, SpeakerId(respondent))
                if not can_q:
                    return False, reason

            elif action in (ActionType.ANSWER, ActionType.RESPONSE):
                can_ans, reason = SpeakerPermissionMatrix.can_answer(state_obj, speaker_id)
                if not can_ans:
                    return False, reason

            elif action in (ActionType.POINT_OF_ORDER, ActionType.POINT_OF_CLARIFICATION):
                can_int, reason = SpeakerPermissionMatrix.can_interrupt(state_obj, speaker_id, action)
                if not can_int:
                    return False, reason

        # 3. Time Check
        if state_def.requires_timer and state_obj.remaining_time <= 0 and action in (ActionType.SPEAK, ActionType.START_SPEECH, ActionType.QUESTION, ActionType.ANSWER):
            return False, f"Time expired for current round ({state_obj.remaining_time}s remaining). Speech action rejected."

        # 4. Team Validation
        if team is not None and speaker_id is not None:
            profile = state_obj.debaters.get(speaker_id.value)
            if profile and profile.team != team and team != TeamSide.NEUTRAL:
                return False, f"Team mismatch: Speaker {speaker_id.value} belongs to {profile.team.value}, not {team.value}."

        return True, "Action validated successfully."
