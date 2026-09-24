"""
Debate Arena - Deterministic State Machine
Implements strict state definitions, entry/exit criteria, and valid transitions.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from polya_runtime.debate_engine.models import (
    EventState,
    ActionType,
    SpeakerId,
    TeamSide,
    EventStateObject
)

@dataclass
class StateDefinition:
    state: EventState
    purpose: str
    allowed_actions: List[ActionType]
    forbidden_actions: List[ActionType]
    next_valid_states: List[EventState]
    requires_timer: bool = True
    default_duration_sec: int = 0
    moderator_authority: str = "PASSIVE"
    scoring_mode: str = "LIVE"  # NONE, LIVE, DELIBERATION

STATE_DEFINITIONS: Dict[EventState, StateDefinition] = {
    EventState.SETUP: StateDefinition(
        state=EventState.SETUP,
        purpose="Prepare match configuration, motion, teams, and debater rosters.",
        allowed_actions=[ActionType.CREATE_EVENT, ActionType.LOCK_TOPIC, ActionType.PAUSE],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.ANSWER, ActionType.REBUT, ActionType.VERDICT_ISSUE],
        next_valid_states=[EventState.TOPIC_LOCK],
        requires_timer=False,
        scoring_mode="NONE"
    ),
    EventState.TOPIC_LOCK: StateDefinition(
        state=EventState.TOPIC_LOCK,
        purpose="Lock debate motion, definitions, and team sides.",
        allowed_actions=[ActionType.READY_TEAM, ActionType.PAUSE],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.ANSWER, ActionType.REBUT],
        next_valid_states=[EventState.TEAM_READY, EventState.SETUP],
        requires_timer=False,
        scoring_mode="NONE"
    ),
    EventState.TEAM_READY: StateDefinition(
        state=EventState.TEAM_READY,
        purpose="Verify all 6 speakers present (P1-P3, C1-C3) and system readiness.",
        allowed_actions=[ActionType.START_EVENT, ActionType.PAUSE],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.REBUT],
        next_valid_states=[EventState.INTRODUCTION, EventState.TOPIC_LOCK],
        requires_timer=False,
        scoring_mode="NONE"
    ),
    EventState.INTRODUCTION: StateDefinition(
        state=EventState.INTRODUCTION,
        purpose="Host introduces event, topic, and debater teams neutrally.",
        allowed_actions=[ActionType.SPEAK, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.REBUT, ActionType.CHALLENGE],
        next_valid_states=[EventState.RULE_BRIEFING],
        requires_timer=True,
        default_duration_sec=90,
        scoring_mode="NONE"
    ),
    EventState.RULE_BRIEFING: StateDefinition(
        state=EventState.RULE_BRIEFING,
        purpose="Moderator establishes ground rules, time limits, and conduct standards.",
        allowed_actions=[ActionType.SPEAK, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.REBUT],
        next_valid_states=[EventState.OPENING],
        requires_timer=True,
        default_duration_sec=90,
        scoring_mode="NONE"
    ),
    EventState.OPENING: StateDefinition(
        state=EventState.OPENING,
        purpose="P1 and C1 establish framing, definitions, and core thesis.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.ANSWER, ActionType.FOLLOW_UP],
        next_valid_states=[EventState.CONSTRUCTIVE],
        requires_timer=True,
        default_duration_sec=180,
        scoring_mode="LIVE"
    ),
    EventState.CONSTRUCTIVE: StateDefinition(
        state=EventState.CONSTRUCTIVE,
        purpose="P2 and C2 build out substantive case, logic, and core arguments.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM, ActionType.PRESENT_EVIDENCE, ActionType.POINT_OF_CLARIFICATION, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.ANSWER, ActionType.FOLLOW_UP],
        next_valid_states=[EventState.EVIDENCE_ARGUMENT],
        requires_timer=True,
        default_duration_sec=180,
        scoring_mode="LIVE"
    ),
    EventState.EVIDENCE_ARGUMENT: StateDefinition(
        state=EventState.EVIDENCE_ARGUMENT,
        purpose="Strengthen arguments with forensic citations, manuscripts, and evidence.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_EVIDENCE, ActionType.CHALLENGE, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.FOLLOW_UP],
        next_valid_states=[EventState.CROSS_EXAMINATION],
        requires_timer=True,
        default_duration_sec=180,
        scoring_mode="LIVE"
    ),
    EventState.CROSS_EXAMINATION: StateDefinition(
        state=EventState.CROSS_EXAMINATION,
        purpose="Structured interactive Q&A and dialectical pressure between opposing debaters.",
        allowed_actions=[ActionType.QUESTION, ActionType.ANSWER, ActionType.FOLLOW_UP, ActionType.RESPONSE, ActionType.POINT_OF_ORDER, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.START_SPEECH, ActionType.PRESENT_ARGUMENT],
        next_valid_states=[EventState.REBUTTAL],
        requires_timer=True,
        default_duration_sec=150,
        scoring_mode="LIVE"
    ),
    EventState.REBUTTAL: StateDefinition(
        state=EventState.REBUTTAL,
        purpose="P3 and C3 directly attack vulnerabilities in opposing premises and evidence.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT, ActionType.PRESENT_EVIDENCE, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.ANSWER],
        next_valid_states=[EventState.CLASH_ROUND],
        requires_timer=True,
        default_duration_sec=180,
        scoring_mode="LIVE"
    ),
    EventState.CLASH_ROUND: StateDefinition(
        state=EventState.CLASH_ROUND,
        purpose="Direct engagement focused exclusively on identified decisive clashes.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT, ActionType.CHALLENGE, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION],
        next_valid_states=[EventState.FINAL_REBUTTAL],
        requires_timer=True,
        default_duration_sec=180,
        scoring_mode="LIVE"
    ),
    EventState.FINAL_REBUTTAL: StateDefinition(
        state=EventState.FINAL_REBUTTAL,
        purpose="Final opportunity to answer attacks and crystallize team standing.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.CHALLENGE],
        next_valid_states=[EventState.CLOSING],
        requires_timer=True,
        default_duration_sec=120,
        scoring_mode="LIVE"
    ),
    EventState.CLOSING: StateDefinition(
        state=EventState.CLOSING,
        purpose="Final synthesis, strategic framing, and summary of superiority.",
        allowed_actions=[ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.MODERATOR_INTERVENTION, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.CHALLENGE, ActionType.POINT_OF_ORDER],
        next_valid_states=[EventState.DELIBERATION],
        requires_timer=True,
        default_duration_sec=120,
        scoring_mode="LIVE"
    ),
    EventState.DELIBERATION: StateDefinition(
        state=EventState.DELIBERATION,
        purpose="Debate closed. Multi-judge AI evaluates rubrics, clashes, and scores.",
        allowed_actions=[ActionType.SCORE_UPDATE, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.ANSWER, ActionType.REBUT, ActionType.CHALLENGE],
        next_valid_states=[EventState.VERDICT],
        requires_timer=True,
        default_duration_sec=60,
        scoring_mode="DELIBERATION"
    ),
    EventState.VERDICT: StateDefinition(
        state=EventState.VERDICT,
        purpose="Announce adjudicated winner, final score breakdown, margin, and key clashes.",
        allowed_actions=[ActionType.VERDICT_ISSUE, ActionType.SPEAK, ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.QUESTION, ActionType.REBUT, ActionType.CHALLENGE],
        next_valid_states=[EventState.POST_DEBATE_ANALYSIS],
        requires_timer=False,
        scoring_mode="NONE"
    ),
    EventState.POST_DEBATE_ANALYSIS: StateDefinition(
        state=EventState.POST_DEBATE_ANALYSIS,
        purpose="Generate deep analytical report, argument graph, and coaching points.",
        allowed_actions=[ActionType.TRANSITION_STATE, ActionType.PAUSE],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.REBUT],
        next_valid_states=[EventState.ARCHIVE],
        requires_timer=False,
        scoring_mode="NONE"
    ),
    EventState.ARCHIVE: StateDefinition(
        state=EventState.ARCHIVE,
        purpose="Immutable archive of completed debate record and logs.",
        allowed_actions=[],
        forbidden_actions=[ActionType.SPEAK, ActionType.QUESTION, ActionType.ANSWER, ActionType.REBUT, ActionType.SCORE_UPDATE],
        next_valid_states=[],
        requires_timer=False,
        scoring_mode="NONE"
    )
}

class DebateStateMachine:
    """Deterministic State Transition Controller."""
    
    @staticmethod
    def get_state_definition(state: EventState) -> StateDefinition:
        if state not in STATE_DEFINITIONS:
            raise ValueError(f"Unknown EventState: {state}")
        return STATE_DEFINITIONS[state]

    @staticmethod
    def can_transition(current_state: EventState, target_state: EventState) -> Tuple[bool, str]:
        if target_state == EventState.PAUSED:
            return True, "Pause allowed from any active state."
        if current_state == EventState.PAUSED:
            return True, "Resume allowed to restore previous state."

        state_def = STATE_DEFINITIONS.get(current_state)
        if not state_def:
            return False, f"Invalid current state: {current_state}"
        
        if target_state in state_def.next_valid_states:
            return True, f"Transition from {current_state} to {target_state} is valid."
        
        return False, f"Invalid transition: Cannot transition directly from {current_state} to {target_state}. Valid: {state_def.next_valid_states}"

    @staticmethod
    def apply_transition(event: EventStateObject, target_state: EventState) -> Tuple[bool, str]:
        if target_state == EventState.PAUSED:
            if not event.is_paused:
                event.previous_state = event.current_state
                event.current_state = EventState.PAUSED
                event.is_paused = True
                return True, "Event paused."
            return False, "Event is already paused."

        if event.current_state == EventState.PAUSED:
            # Resuming
            prev = event.previous_state or EventState.SETUP
            event.current_state = prev
            event.is_paused = False
            return True, f"Event resumed to {prev}."

        valid, reason = DebateStateMachine.can_transition(event.current_state, target_state)
        if not valid:
            return False, reason

        event.previous_state = event.current_state
        event.current_state = target_state
        event.current_round = target_state.value
        
        state_def = STATE_DEFINITIONS[target_state]
        event.allowed_actions = state_def.allowed_actions
        event.forbidden_actions = state_def.forbidden_actions
        if state_def.requires_timer and state_def.default_duration_sec > 0:
            event.round_time = state_def.default_duration_sec
            event.remaining_time = state_def.default_duration_sec
            
        return True, f"State transitioned to {target_state.value}"
