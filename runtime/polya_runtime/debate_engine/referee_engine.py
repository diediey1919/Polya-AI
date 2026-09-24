"""
Debate Arena - Referee Engine
Adheres to 04_DEBATE_MODERATOR_REFEREE_ENGINE.md.
Validates actions, classifies procedural violations, escalates penalties, and preserves rule integrity.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    EventState,
    SpeakerId,
    TeamSide,
    ActionType,
    EventStateObject
)
from polya_runtime.debate_engine.permission_matrix import SpeakerPermissionMatrix
from polya_runtime.debate_engine.state_machine import DebateStateMachine

class ViolationType(str, Enum):
    SPEAKER_PERMISSION = "SPEAKER_PERMISSION"
    TIME = "TIME"
    INTERRUPTION = "INTERRUPTION"
    RELEVANCE = "RELEVANCE"
    CONDUCT = "CONDUCT"
    EVIDENCE_PROCEDURE = "EVIDENCE_PROCEDURE"
    FORMAT = "FORMAT"

class ViolationSeverity(str, Enum):
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    MAJOR = "MAJOR"
    SEVERE = "SEVERE"

class PenaltyType(str, Enum):
    WARNING = "WARNING"
    FORMAL_WARNING = "FORMAL_WARNING"
    TIME_DEDUCTION = "TIME_DEDUCTION"
    PROCEDURAL_SCORE_PENALTY = "PROCEDURAL_SCORE_PENALTY"
    LOSS_OF_PRIVILEGE = "LOSS_OF_PRIVILEGE"
    DISQUALIFICATION = "DISQUALIFICATION"

@dataclass
class ProceduralViolation:
    violation_id: str = field(default_factory=lambda: f"VIO-{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    speaker_id: Optional[SpeakerId] = None
    team: Optional[TeamSide] = None
    violation_type: ViolationType = ViolationType.FORMAT
    severity: ViolationSeverity = ViolationSeverity.MINOR
    rule_id: str = ""
    description: str = ""
    state: str = ""
    round_name: str = ""

@dataclass
class ProceduralPenalty:
    penalty_id: str = field(default_factory=lambda: f"PEN-{uuid.uuid4().hex[:8]}")
    violation_id: str = ""
    timestamp: float = field(default_factory=time.time)
    speaker_id: Optional[SpeakerId] = None
    team: Optional[TeamSide] = None
    penalty_type: PenaltyType = PenaltyType.WARNING
    score_effect: float = 0.0  # Procedural penalty points (tracked separately from argument score)
    notes: str = ""

@dataclass
class RefereeDecision:
    is_allowed: bool
    reason: str
    violation: Optional[ProceduralViolation] = None
    penalty: Optional[ProceduralPenalty] = None
    recommended_moderator_action: str = ""

class RefereeEngine:
    """Enforces rules, validates action compliance, and manages violation escalations."""

    def __init__(self):
        self.violation_history: List[ProceduralViolation] = []
        self.penalty_history: List[ProceduralPenalty] = []
        self.speaker_violation_counts: Dict[str, int] = {}

    def validate_and_adjudicate(
        self,
        state_obj: EventStateObject,
        action: ActionType,
        speaker_id: Optional[SpeakerId] = None,
        team: Optional[TeamSide] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> RefereeDecision:
        """
        Validates action against state, speaker permissions, round rules, and timing.
        Returns explicit RefereeDecision.
        """
        current_state = state_obj.current_state

        # 1. State check
        if current_state == EventState.PAUSED and action not in (ActionType.RESUME, ActionType.MODERATOR_INTERVENTION):
            vio = self._record_violation(
                speaker_id, team, ViolationType.FORMAT, ViolationSeverity.MINOR,
                "ACTION_DURING_PAUSE", "Attempted action while match is paused.", state_obj
            )
            pen = self._determine_penalty(vio)
            return RefereeDecision(
                is_allowed=False,
                reason="Match is paused. Only RESUME or Moderator actions allowed.",
                violation=vio,
                penalty=pen,
                recommended_moderator_action="REMIND_PAUSED"
            )

        state_def = DebateStateMachine.get_state_definition(current_state)
        if action in state_def.forbidden_actions:
            vio = self._record_violation(
                speaker_id, team, ViolationType.FORMAT, ViolationSeverity.MODERATE,
                "FORBIDDEN_STATE_ACTION", f"Action {action.value} is strictly forbidden in {current_state.value}.", state_obj
            )
            pen = self._determine_penalty(vio)
            return RefereeDecision(
                is_allowed=False,
                reason=f"Action '{action.value}' is forbidden during {current_state.value}.",
                violation=vio,
                penalty=pen,
                recommended_moderator_action="WARN_ACTION_FORBIDDEN"
            )

        # 2. Speaker Permission Check
        if speaker_id is not None:
            if action in (ActionType.SPEAK, ActionType.START_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_EVIDENCE, ActionType.PRESENT_CLAIM, ActionType.REBUT):
                can_spk, reason = SpeakerPermissionMatrix.can_speak(state_obj, speaker_id)
                if not can_spk:
                    vio = self._record_violation(
                        speaker_id, team, ViolationType.SPEAKER_PERMISSION, ViolationSeverity.MODERATE,
                        "UNAUTHORIZED_SPEAKER", reason, state_obj
                    )
                    pen = self._determine_penalty(vio)
                    return RefereeDecision(
                        is_allowed=False,
                        reason=reason,
                        violation=vio,
                        penalty=pen,
                        recommended_moderator_action="ENFORCE_SPEAKER_FLOOR"
                    )

            elif action == ActionType.QUESTION:
                respondent = payload.get("respondent") if payload else None
                if not respondent:
                    return RefereeDecision(is_allowed=False, reason="Question requires a target respondent.")
                can_q, reason = SpeakerPermissionMatrix.can_ask(state_obj, speaker_id, SpeakerId(respondent))
                if not can_q:
                    vio = self._record_violation(
                        speaker_id, team, ViolationType.FORMAT, ViolationSeverity.MINOR,
                        "INVALID_QUESTION_TARGET", reason, state_obj
                    )
                    pen = self._determine_penalty(vio)
                    return RefereeDecision(
                        is_allowed=False,
                        reason=reason,
                        violation=vio,
                        penalty=pen,
                        recommended_moderator_action="REJECT_QUESTION_PAIRING"
                    )

            elif action in (ActionType.POINT_OF_ORDER, ActionType.POINT_OF_CLARIFICATION):
                can_int, reason = SpeakerPermissionMatrix.can_interrupt(state_obj, speaker_id, action)
                if not can_int:
                    vio = self._record_violation(
                        speaker_id, team, ViolationType.INTERRUPTION, ViolationSeverity.MINOR,
                        "INVALID_INTERRUPTION", reason, state_obj
                    )
                    pen = self._determine_penalty(vio)
                    return RefereeDecision(
                        is_allowed=False,
                        reason=reason,
                        violation=vio,
                        penalty=pen,
                        recommended_moderator_action="REJECT_INTERRUPTION"
                    )

        # 3. Timer Expiration Check
        if state_def.requires_timer and state_obj.remaining_time <= 0 and action in (ActionType.SPEAK, ActionType.START_SPEECH, ActionType.QUESTION, ActionType.ANSWER):
            vio = self._record_violation(
                speaker_id, team, ViolationType.TIME, ViolationSeverity.MINOR,
                "SPEECH_AFTER_EXPIRATION", "Attempted speech after time expired.", state_obj
            )
            pen = self._determine_penalty(vio)
            return RefereeDecision(
                is_allowed=False,
                reason="Time has expired for this speaking turn.",
                violation=vio,
                penalty=pen,
                recommended_moderator_action="PASS_FLOOR_TIME_EXPIRED"
            )

        # 4. Team Mismatch Check
        if team is not None and speaker_id is not None:
            debater = state_obj.debaters.get(speaker_id.value)
            if debater and debater.team != team and team != TeamSide.NEUTRAL:
                vio = self._record_violation(
                    speaker_id, team, ViolationType.SPEAKER_PERMISSION, ViolationSeverity.MODERATE,
                    "TEAM_MISMATCH", f"Speaker {speaker_id.value} does not belong to team {team.value}.", state_obj
                )
                pen = self._determine_penalty(vio)
                return RefereeDecision(
                    is_allowed=False,
                    reason=f"Speaker {speaker_id.value} belongs to {debater.team.value}, not {team.value}.",
                    violation=vio,
                    penalty=pen,
                    recommended_moderator_action="WARN_TEAM_MISMATCH"
                )

        return RefereeDecision(
            is_allowed=True,
            reason="Action approved by Referee."
        )

    def record_violation(
        self,
        speaker_id: Optional[SpeakerId],
        team: Optional[TeamSide],
        violation_type: ViolationType,
        severity: ViolationSeverity,
        description: str,
        rule_id: str = "RULE-SPEAKER-AUTHORITY",
        state_obj: Optional[EventStateObject] = None
    ) -> ProceduralViolation:
        vio = ProceduralViolation(
            speaker_id=speaker_id,
            team=team,
            violation_type=violation_type,
            severity=severity,
            rule_id=rule_id,
            description=description,
            state=state_obj.current_state.value if state_obj else "LIVE",
            round_name=state_obj.current_round if state_obj else "LIVE"
        )
        self.violation_history.append(vio)
        if speaker_id:
            count = self.speaker_violation_counts.get(speaker_id.value, 0) + 1
            self.speaker_violation_counts[speaker_id.value] = count
        return vio

    def _record_violation(
        self,
        speaker_id: Optional[SpeakerId],
        team: Optional[TeamSide],
        v_type: ViolationType,
        severity: ViolationSeverity,
        rule_id: str,
        description: str,
        state_obj: EventStateObject
    ) -> ProceduralViolation:
        vio = ProceduralViolation(
            speaker_id=speaker_id,
            team=team,
            violation_type=v_type,
            severity=severity,
            rule_id=rule_id,
            description=description,
            state=state_obj.current_state.value,
            round_name=state_obj.current_round
        )
        self.violation_history.append(vio)
        if speaker_id:
            count = self.speaker_violation_counts.get(speaker_id.value, 0) + 1
            self.speaker_violation_counts[speaker_id.value] = count
        return vio

    def _determine_penalty(self, violation: ProceduralViolation) -> ProceduralPenalty:
        count = self.speaker_violation_counts.get(violation.speaker_id.value, 1) if violation.speaker_id else 1
        
        # Escalation Policy: 1st = WARNING, 2nd = FORMAL_WARNING, 3rd+ = PROCEDURAL_SCORE_PENALTY
        if count == 1:
            p_type = PenaltyType.WARNING
            score_eff = 0.0
        elif count == 2:
            p_type = PenaltyType.FORMAL_WARNING
            score_eff = 0.0
        else:
            p_type = PenaltyType.PROCEDURAL_SCORE_PENALTY
            score_eff = -1.0

        penalty = ProceduralPenalty(
            violation_id=violation.violation_id,
            speaker_id=violation.speaker_id,
            team=violation.team,
            penalty_type=p_type,
            score_effect=score_eff,
            notes=f"Violation #{count} ({violation.rule_id}): {violation.description}"
        )
        self.penalty_history.append(penalty)
        return penalty
