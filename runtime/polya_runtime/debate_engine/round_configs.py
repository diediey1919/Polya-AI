"""
Debate Arena - Round Configurations & Specifications
Adheres to 03_DEBATE_ROUND_ENGINE_RULES.md.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from polya_runtime.debate_engine.models import (
    EventState,
    SpeakerId,
    TeamSide,
    ActionType
)

class RoundPhase(str, Enum):
    ROUND_0_INTRO = "ROUND_0_INTRO"
    ROUND_0_RULE_BRIEFING = "ROUND_0_RULE_BRIEFING"
    ROUND_1_OPENING = "ROUND_1_OPENING"
    ROUND_2_CONSTRUCTIVE = "ROUND_2_CONSTRUCTIVE"
    ROUND_3_EVIDENCE_ARGUMENT = "ROUND_3_EVIDENCE_ARGUMENT"
    ROUND_4_CROSS_EXAMINATION = "ROUND_4_CROSS_EXAMINATION"
    ROUND_5_REBUTTAL = "ROUND_5_REBUTTAL"
    ROUND_6_CRITICAL_CLASH = "ROUND_6_CRITICAL_CLASH"
    ROUND_7_FINAL_REBUTTAL = "ROUND_7_FINAL_REBUTTAL"
    ROUND_8_CLOSING = "ROUND_8_CLOSING"
    ROUND_9_DELIBERATION = "ROUND_9_DELIBERATION"
    ROUND_10_VERDICT = "ROUND_10_VERDICT"

class CrossExamStep(str, Enum):
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    FOLLOW_UP = "FOLLOW_UP"
    RESPONSE = "RESPONSE"
    COMPLETE = "COMPLETE"

@dataclass
class SpeakerTurnConfig:
    speaker_id: SpeakerId
    team: TeamSide
    role_description: str
    duration_sec: int
    allowed_actions: List[ActionType]
    scoring_priorities: List[str] = field(default_factory=list)
    allow_new_arguments: bool = True
    allow_interruptions: bool = False

@dataclass
class CrossExamExchangeConfig:
    exchange_id: str
    questioner: SpeakerId
    respondent: SpeakerId
    questioner_team: TeamSide
    respondent_team: TeamSide
    max_follow_ups: int = 1
    question_duration_sec: int = 45
    answer_duration_sec: int = 60
    follow_up_duration_sec: int = 30
    response_duration_sec: int = 45

@dataclass
class RoundConfiguration:
    phase: RoundPhase
    name: str
    event_state: EventState
    objective: str
    speaker_turns: List[SpeakerTurnConfig] = field(default_factory=list)
    cross_exam_exchanges: List[CrossExamExchangeConfig] = field(default_factory=list)
    default_duration_sec: int = 180
    allow_new_arguments: bool = True
    allow_evidence: bool = True
    scoring_priorities: List[str] = field(default_factory=list)

DEFAULT_ROUND_CONFIGS: Dict[RoundPhase, RoundConfiguration] = {
    RoundPhase.ROUND_0_INTRO: RoundConfiguration(
        phase=RoundPhase.ROUND_0_INTRO,
        name="Event Introduction",
        event_state=EventState.INTRODUCTION,
        objective="Introduce debate topic, teams, and debaters neutrally.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.HOST, TeamSide.NEUTRAL, "Host Event Intro", 90, [ActionType.SPEAK], [])
        ],
        allow_new_arguments=False,
        scoring_priorities=[]
    ),
    RoundPhase.ROUND_0_RULE_BRIEFING: RoundConfiguration(
        phase=RoundPhase.ROUND_0_RULE_BRIEFING,
        name="Rule Briefing",
        event_state=EventState.RULE_BRIEFING,
        objective="Explain rules, format, speaking order, time limits, and conduct standards.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.MODERATOR, TeamSide.NEUTRAL, "Rule Briefing", 90, [ActionType.SPEAK, ActionType.MODERATOR_INTERVENTION], [])
        ],
        allow_new_arguments=False,
        scoring_priorities=[]
    ),
    RoundPhase.ROUND_1_OPENING: RoundConfiguration(
        phase=RoundPhase.ROUND_1_OPENING,
        name="Round 1: Opening Statements",
        event_state=EventState.OPENING,
        objective="Establish core case, framing, definitions, and thesis.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P1, TeamSide.PROPOSITION, "Proposition Opening (P1)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM], ["argument_quality", "logical_reasoning", "clarity_structure", "debate_strategy"]),
            SpeakerTurnConfig(SpeakerId.C1, TeamSide.OPPOSITION, "Opposition Opening (C1)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM], ["argument_quality", "logical_reasoning", "clarity_structure", "debate_strategy"])
        ],
        scoring_priorities=["argument_quality", "logical_reasoning", "clarity_structure", "debate_strategy"]
    ),
    RoundPhase.ROUND_2_CONSTRUCTIVE: RoundConfiguration(
        phase=RoundPhase.ROUND_2_CONSTRUCTIVE,
        name="Round 2: Constructive Case",
        event_state=EventState.CONSTRUCTIVE,
        objective="Develop substantive case, reasoning, and logical premises.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P2, TeamSide.PROPOSITION, "Proposition Constructive (P2)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM, ActionType.PRESENT_EVIDENCE], ["argument_quality", "logical_reasoning", "team_contribution"]),
            SpeakerTurnConfig(SpeakerId.C2, TeamSide.OPPOSITION, "Opposition Constructive (C2)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_ARGUMENT, ActionType.PRESENT_CLAIM, ActionType.PRESENT_EVIDENCE], ["argument_quality", "logical_reasoning", "team_contribution"])
        ],
        scoring_priorities=["argument_quality", "logical_reasoning", "team_contribution"]
    ),
    RoundPhase.ROUND_3_EVIDENCE_ARGUMENT: RoundConfiguration(
        phase=RoundPhase.ROUND_3_EVIDENCE_ARGUMENT,
        name="Round 3: Evidence & Forensic Citations",
        event_state=EventState.EVIDENCE_ARGUMENT,
        objective="Deep forensic citations, manuscripts, and evidence-grounded arguments.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P2, TeamSide.PROPOSITION, "Proposition Evidence (P2)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_EVIDENCE, ActionType.PRESENT_CLAIM], ["evidence_factuality", "argument_quality", "logical_reasoning"]),
            SpeakerTurnConfig(SpeakerId.C2, TeamSide.OPPOSITION, "Opposition Evidence (C2)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.PRESENT_EVIDENCE, ActionType.PRESENT_CLAIM], ["evidence_factuality", "argument_quality", "logical_reasoning"])
        ],
        scoring_priorities=["evidence_factuality", "argument_quality", "logical_reasoning"]
    ),
    RoundPhase.ROUND_4_CROSS_EXAMINATION: RoundConfiguration(
        phase=RoundPhase.ROUND_4_CROSS_EXAMINATION,
        name="Round 4: Cross Examination",
        event_state=EventState.CROSS_EXAMINATION,
        objective="Dialectical pressure, testing opposing claims and logical premises.",
        cross_exam_exchanges=[
            CrossExamExchangeConfig("CX-1", SpeakerId.P3, SpeakerId.C1, TeamSide.PROPOSITION, TeamSide.OPPOSITION, max_follow_ups=1),
            CrossExamExchangeConfig("CX-2", SpeakerId.P3, SpeakerId.C2, TeamSide.PROPOSITION, TeamSide.OPPOSITION, max_follow_ups=1),
            CrossExamExchangeConfig("CX-3", SpeakerId.C3, SpeakerId.P1, TeamSide.OPPOSITION, TeamSide.PROPOSITION, max_follow_ups=1),
            CrossExamExchangeConfig("CX-4", SpeakerId.C3, SpeakerId.P2, TeamSide.OPPOSITION, TeamSide.PROPOSITION, max_follow_ups=1)
        ],
        allow_new_arguments=False,
        scoring_priorities=["cross_examination", "responsiveness", "logical_reasoning", "debate_strategy"]
    ),
    RoundPhase.ROUND_5_REBUTTAL: RoundConfiguration(
        phase=RoundPhase.ROUND_5_REBUTTAL,
        name="Round 5: Rebuttal & Refutation",
        event_state=EventState.REBUTTAL,
        objective="Directly attack and expose vulnerabilities in opposing arguments.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P3, TeamSide.PROPOSITION, "Proposition Rebuttal (P3)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT, ActionType.PRESENT_EVIDENCE], ["rebuttal", "responsiveness", "argument_quality"]),
            SpeakerTurnConfig(SpeakerId.C3, TeamSide.OPPOSITION, "Opposition Rebuttal (C3)", 180, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT, ActionType.PRESENT_EVIDENCE], ["rebuttal", "responsiveness", "argument_quality"])
        ],
        scoring_priorities=["rebuttal", "responsiveness", "argument_quality"]
    ),
    RoundPhase.ROUND_6_CRITICAL_CLASH: RoundConfiguration(
        phase=RoundPhase.ROUND_6_CRITICAL_CLASH,
        name="Round 6: Critical Clash Round",
        event_state=EventState.CLASH_ROUND,
        objective="Decisive engagement on primary clashes of the debate.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P1, TeamSide.PROPOSITION, "Proposition Clash (P1/P3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "logical_reasoning", "debate_strategy", "team_contribution"]),
            SpeakerTurnConfig(SpeakerId.C1, TeamSide.OPPOSITION, "Opposition Clash (C1/C3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "logical_reasoning", "debate_strategy", "team_contribution"]),
            SpeakerTurnConfig(SpeakerId.P3, TeamSide.PROPOSITION, "Proposition Clash Synthesis (P3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "logical_reasoning", "debate_strategy", "team_contribution"]),
            SpeakerTurnConfig(SpeakerId.C3, TeamSide.OPPOSITION, "Opposition Clash Synthesis (C3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "logical_reasoning", "debate_strategy", "team_contribution"])
        ],
        scoring_priorities=["rebuttal", "logical_reasoning", "debate_strategy", "team_contribution"]
    ),
    RoundPhase.ROUND_7_FINAL_REBUTTAL: RoundConfiguration(
        phase=RoundPhase.ROUND_7_FINAL_REBUTTAL,
        name="Round 7: Final Rebuttal",
        event_state=EventState.FINAL_REBUTTAL,
        objective="Final answers to critical clashes and major remaining attacks.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P3, TeamSide.PROPOSITION, "Proposition Final Rebuttal (P3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "responsiveness", "argument_quality"]),
            SpeakerTurnConfig(SpeakerId.C3, TeamSide.OPPOSITION, "Opposition Final Rebuttal (C3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH, ActionType.REBUT], ["rebuttal", "responsiveness", "argument_quality"])
        ],
        allow_new_arguments=False,
        scoring_priorities=["rebuttal", "responsiveness", "argument_quality"]
    ),
    RoundPhase.ROUND_8_CLOSING: RoundConfiguration(
        phase=RoundPhase.ROUND_8_CLOSING,
        name="Round 8: Closing Statements",
        event_state=EventState.CLOSING,
        objective="Final synthesis, strategic framing, and summary of superiority.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.P3, TeamSide.PROPOSITION, "Proposition Closing (P3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH], ["argument_quality", "debate_strategy", "clarity_structure", "team_contribution"], allow_new_arguments=False),
            SpeakerTurnConfig(SpeakerId.C3, TeamSide.OPPOSITION, "Opposition Closing (C3)", 120, [ActionType.START_SPEECH, ActionType.SPEAK, ActionType.END_SPEECH], ["argument_quality", "debate_strategy", "clarity_structure", "team_contribution"], allow_new_arguments=False)
        ],
        allow_new_arguments=False,
        scoring_priorities=["argument_quality", "debate_strategy", "clarity_structure", "team_contribution"]
    ),
    RoundPhase.ROUND_9_DELIBERATION: RoundConfiguration(
        phase=RoundPhase.ROUND_9_DELIBERATION,
        name="Round 9: Multi-Judge AI Deliberation",
        event_state=EventState.DELIBERATION,
        objective="Multi-judge AI adjudication across 9 categories and critical clashes.",
        speaker_turns=[],
        allow_new_arguments=False,
        scoring_priorities=[]
    ),
    RoundPhase.ROUND_10_VERDICT: RoundConfiguration(
        phase=RoundPhase.ROUND_10_VERDICT,
        name="Round 10: Official Adjudicated Verdict",
        event_state=EventState.VERDICT,
        objective="Announce official winning team, scores, margin, and key clash results.",
        speaker_turns=[
            SpeakerTurnConfig(SpeakerId.HOST, TeamSide.NEUTRAL, "Host Verdict Presentation", 90, [ActionType.SPEAK, ActionType.VERDICT_ISSUE], [])
        ],
        allow_new_arguments=False,
        scoring_priorities=[]
    )
}
