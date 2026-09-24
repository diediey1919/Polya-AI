"""
Debate Arena - Round Engine Controller
Implements the internal state, micro-protocols, speaker rotations, and memory per round.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time

from polya_runtime.debate_engine.models import (
    EventState,
    SpeakerId,
    TeamSide,
    ActionType,
    ArgumentItem,
    ClaimItem,
    EvidenceItem,
    CriticalClash,
    RelationshipType,
    EventStateObject
)
from polya_runtime.debate_engine.round_configs import (
    RoundPhase,
    RoundConfiguration,
    SpeakerTurnConfig,
    CrossExamExchangeConfig,
    CrossExamStep,
    DEFAULT_ROUND_CONFIGS
)

@dataclass
class CrossExamRuntimeState:
    exchange_index: int = 0
    current_exchange: Optional[CrossExamExchangeConfig] = None
    step: CrossExamStep = CrossExamStep.QUESTION
    follow_up_count: int = 0
    question_text: str = ""
    answer_text: str = ""
    follow_up_text: str = ""
    response_text: str = ""

@dataclass
class ArgumentLineage:
    argument_id: str
    origin_speaker: SpeakerId
    origin_round: RoundPhase
    claim_text: str
    premises: List[str]
    supporting_evidence_ids: List[str] = field(default_factory=list)
    attacks: List[Dict[str, Any]] = field(default_factory=list)  # {speaker, round, rebuttal_text, strawman_flag}
    defenses: List[Dict[str, Any]] = field(default_factory=list) # {speaker, round, defense_text}
    associated_clash_ids: List[str] = field(default_factory=list)
    status: str = "ACTIVE"

class RoundController:
    """Controls turn sequence, micro-protocols, and contextual memory within a round."""

    def __init__(self, configs: Optional[Dict[RoundPhase, RoundConfiguration]] = None):
        self.configs = configs or DEFAULT_ROUND_CONFIGS
        self.current_phase: Optional[RoundPhase] = None
        self.current_config: Optional[RoundConfiguration] = None
        self.turn_index: int = 0
        self.active_speaker_turn: Optional[SpeakerTurnConfig] = None
        
        # Cross Examination Runtime
        self.cross_exam_state = CrossExamRuntimeState()
        
        # Round Memory & Argument Lineage
        self.argument_lineages: Dict[str, ArgumentLineage] = {}
        self.clash_registry: Dict[str, CriticalClash] = {}

    def start_round(self, phase: RoundPhase, state_obj: EventStateObject) -> Tuple[bool, str]:
        if phase not in self.configs:
            return False, f"Unknown RoundPhase: {phase}"

        config = self.configs[phase]
        self.current_phase = phase
        self.current_config = config
        self.turn_index = 0

        # Update State Object
        state_obj.current_round = config.name
        state_obj.allowed_actions = [ActionType.TRANSITION_STATE, ActionType.PAUSE, ActionType.MODERATOR_INTERVENTION]

        if config.speaker_turns:
            self.active_speaker_turn = config.speaker_turns[0]
            state_obj.current_speaker = self.active_speaker_turn.speaker_id
            state_obj.current_team = self.active_speaker_turn.team
            state_obj.round_time = self.active_speaker_turn.duration_sec
            state_obj.remaining_time = self.active_speaker_turn.duration_sec
            state_obj.allowed_actions.extend(self.active_speaker_turn.allowed_actions)
        elif config.cross_exam_exchanges:
            # Initialize Cross-Ex
            self.cross_exam_state = CrossExamRuntimeState(
                exchange_index=0,
                current_exchange=config.cross_exam_exchanges[0],
                step=CrossExamStep.QUESTION,
                follow_up_count=0
            )
            state_obj.current_speaker = config.cross_exam_exchanges[0].questioner
            state_obj.current_team = config.cross_exam_exchanges[0].questioner_team
            state_obj.round_time = config.cross_exam_exchanges[0].question_duration_sec
            state_obj.remaining_time = config.cross_exam_exchanges[0].question_duration_sec
            state_obj.allowed_actions.extend([ActionType.QUESTION, ActionType.POINT_OF_ORDER])
        else:
            state_obj.current_speaker = None
            state_obj.current_team = None
            state_obj.round_time = config.default_duration_sec
            state_obj.remaining_time = config.default_duration_sec

        return True, f"{config.name} started successfully."

    def advance_turn(self, state_obj: EventStateObject) -> Tuple[bool, str]:
        """Advances to the next speaker turn or next cross-ex exchange within current round."""
        if not self.current_config:
            return False, "No active round configuration."

        if self.current_config.speaker_turns:
            self.turn_index += 1
            if self.turn_index < len(self.current_config.speaker_turns):
                self.active_speaker_turn = self.current_config.speaker_turns[self.turn_index]
                state_obj.current_speaker = self.active_speaker_turn.speaker_id
                state_obj.current_team = self.active_speaker_turn.team
                state_obj.round_time = self.active_speaker_turn.duration_sec
                state_obj.remaining_time = self.active_speaker_turn.duration_sec
                state_obj.allowed_actions = [ActionType.TRANSITION_STATE, ActionType.PAUSE, ActionType.MODERATOR_INTERVENTION] + self.active_speaker_turn.allowed_actions
                return True, f"Turn advanced to {self.active_speaker_turn.speaker_id.value} ({self.active_speaker_turn.team.value})."
            else:
                return False, "All speaker turns in this round are completed."

        elif self.current_config.cross_exam_exchanges:
            cx = self.cross_exam_state
            cx.exchange_index += 1
            if cx.exchange_index < len(self.current_config.cross_exam_exchanges):
                new_ex = self.current_config.cross_exam_exchanges[cx.exchange_index]
                cx.current_exchange = new_ex
                cx.step = CrossExamStep.QUESTION
                cx.follow_up_count = 0
                state_obj.current_speaker = new_ex.questioner
                state_obj.current_team = new_ex.questioner_team
                state_obj.round_time = new_ex.question_duration_sec
                state_obj.remaining_time = new_ex.question_duration_sec
                state_obj.allowed_actions = [ActionType.TRANSITION_STATE, ActionType.PAUSE, ActionType.MODERATOR_INTERVENTION, ActionType.QUESTION, ActionType.POINT_OF_ORDER]
                return True, f"Cross-Ex exchange advanced to {new_ex.exchange_id} ({new_ex.questioner.value} -> {new_ex.respondent.value})."
            else:
                return False, "All cross-examination exchanges in this round are completed."

        return False, "No turns to advance."

    def is_round_complete(self) -> bool:
        if not self.current_config:
            return True
        if self.current_config.speaker_turns:
            return self.turn_index >= len(self.current_config.speaker_turns)
        if self.current_config.cross_exam_exchanges:
            return self.cross_exam_state.exchange_index >= len(self.current_config.cross_exam_exchanges)
        return True

    # -----------------------------------------------------------------------
    # Cross Examination Micro-Protocol
    # -----------------------------------------------------------------------
    def handle_cross_exam_step(
        self,
        step_action: ActionType,
        speaker_id: SpeakerId,
        content: str,
        state_obj: EventStateObject
    ) -> Tuple[bool, str]:
        cx = self.cross_exam_state
        if not cx.current_exchange:
            return False, "No active cross-examination exchange."

        curr_ex = cx.current_exchange

        if cx.step == CrossExamStep.QUESTION:
            if step_action != ActionType.QUESTION or speaker_id != curr_ex.questioner:
                return False, f"Expected QUESTION from {curr_ex.questioner.value}."
            cx.question_text = content
            cx.step = CrossExamStep.ANSWER
            # Set respondent active
            state_obj.current_speaker = curr_ex.respondent
            state_obj.current_team = curr_ex.respondent_team
            state_obj.round_time = curr_ex.answer_duration_sec
            state_obj.remaining_time = curr_ex.answer_duration_sec
            state_obj.allowed_actions = [ActionType.ANSWER, ActionType.POINT_OF_ORDER, ActionType.MODERATOR_INTERVENTION]
            return True, f"Question recorded from {speaker_id.value}. Now awaiting answer from {curr_ex.respondent.value}."

        elif cx.step == CrossExamStep.ANSWER:
            if step_action != ActionType.ANSWER or speaker_id != curr_ex.respondent:
                return False, f"Expected ANSWER from {curr_ex.respondent.value}."
            cx.answer_text = content
            if cx.follow_up_count < curr_ex.max_follow_ups:
                cx.step = CrossExamStep.FOLLOW_UP
                state_obj.current_speaker = curr_ex.questioner
                state_obj.current_team = curr_ex.questioner_team
                state_obj.round_time = curr_ex.follow_up_duration_sec
                state_obj.remaining_time = curr_ex.follow_up_duration_sec
                state_obj.allowed_actions = [ActionType.FOLLOW_UP, ActionType.POINT_OF_ORDER, ActionType.MODERATOR_INTERVENTION]
                return True, f"Answer recorded. Questioner {curr_ex.questioner.value} may issue follow-up."
            else:
                cx.step = CrossExamStep.COMPLETE
                return True, "Exchange completed (max follow-ups reached)."

        elif cx.step == CrossExamStep.FOLLOW_UP:
            if step_action != ActionType.FOLLOW_UP or speaker_id != curr_ex.questioner:
                return False, f"Expected FOLLOW_UP from {curr_ex.questioner.value}."
            cx.follow_up_text = content
            cx.follow_up_count += 1
            cx.step = CrossExamStep.RESPONSE
            state_obj.current_speaker = curr_ex.respondent
            state_obj.current_team = curr_ex.respondent_team
            state_obj.round_time = curr_ex.response_duration_sec
            state_obj.remaining_time = curr_ex.response_duration_sec
            state_obj.allowed_actions = [ActionType.RESPONSE, ActionType.POINT_OF_ORDER, ActionType.MODERATOR_INTERVENTION]
            return True, f"Follow-up recorded. Awaiting final response from {curr_ex.respondent.value}."

        elif cx.step == CrossExamStep.RESPONSE:
            if step_action != ActionType.RESPONSE or speaker_id != curr_ex.respondent:
                return False, f"Expected RESPONSE from {curr_ex.respondent.value}."
            cx.response_text = content
            cx.step = CrossExamStep.COMPLETE
            return True, "Cross-examination exchange fully concluded."

        return False, f"Invalid step transition in cross-examination: {cx.step}"

    # -----------------------------------------------------------------------
    # Argument Lineage & Strawman Tracking
    # -----------------------------------------------------------------------
    def track_new_argument(self, argument: ArgumentItem, round_phase: RoundPhase):
        self.argument_lineages[argument.argument_id] = ArgumentLineage(
            argument_id=argument.argument_id,
            origin_speaker=argument.speaker_id,
            origin_round=round_phase,
            claim_text=argument.claim,
            premises=argument.premises,
            supporting_evidence_ids=argument.evidence_ids
        )

    def track_rebuttal(
        self,
        target_argument_id: str,
        speaker_id: SpeakerId,
        round_phase: RoundPhase,
        rebuttal_text: str,
        is_strawman: bool = False
    ) -> bool:
        if target_argument_id in self.argument_lineages:
            self.argument_lineages[target_argument_id].attacks.append({
                "speaker": speaker_id.value,
                "round": round_phase.value,
                "rebuttal_text": rebuttal_text,
                "is_strawman": is_strawman,
                "timestamp": time.time()
            })
            if not is_strawman:
                self.argument_lineages[target_argument_id].status = "CONTESTED"
            return True
        return False

    def get_compressed_context(self, current_speaker: Optional[SpeakerId] = None) -> str:
        """Returns compressed, lineage-aware context for AI prompt injection."""
        lines = ["=== COMPRESSED ROUND MEMORY & ARGUMENT GRAPH ==="]
        for arg_id, lin in self.argument_lineages.items():
            attacks_cnt = len(lin.attacks)
            strawmans = sum(1 for a in lin.attacks if a.get("is_strawman"))
            lines.append(
                f"- [{arg_id}] {lin.origin_speaker.value} ({lin.origin_round.value}): \"{lin.claim_text}\" "
                f"| Attacks: {attacks_cnt} (Strawmans: {strawmans}) | Status: {lin.status}"
            )
        return "\n".join(lines)
