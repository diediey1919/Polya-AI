"""
Debate Arena - Replay & Analytics Data Models
Adheres to 09_DEBATE_REPLAY_ANALYTICS_ENGINE.md.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole
)
from polya_runtime.debate_engine.round_configs import RoundPhase

class ReplayMode(str, Enum):
    FULL_REPLAY = "FULL_REPLAY"
    ROUND_REPLAY = "ROUND_REPLAY"
    CLASH_REPLAY = "CLASH_REPLAY"
    ARGUMENT_REPLAY = "ARGUMENT_REPLAY"
    EVIDENCE_REPLAY = "EVIDENCE_REPLAY"
    MOMENTUM_REPLAY = "MOMENTUM_REPLAY"
    SCORE_REPLAY = "SCORE_REPLAY"
    COMMENTARY_REPLAY = "COMMENTARY_REPLAY"

class CausalRelationType(str, Enum):
    CAUSED = "CAUSED"
    SUPPORTED = "SUPPORTED"
    ATTACKED = "ATTACKED"
    DEFENDED = "DEFENDED"
    AFFECTED = "AFFECTED"
    TRIGGERED = "TRIGGERED"
    RESPONDED_TO = "RESPONDED_TO"
    EVALUATED = "EVALUATED"
    RESULTED_IN = "RESULTED_IN"

class CheckpointType(str, Enum):
    ROUND_START = "ROUND_START"
    ROUND_END = "ROUND_END"
    MAJOR_CLASH_CHANGE = "MAJOR_CLASH_CHANGE"
    MAJOR_MOMENTUM_SHIFT = "MAJOR_MOMENTUM_SHIFT"
    VERDICT = "VERDICT"

class ReplaySpeed(str, Enum):
    SPEED_0_25X = "0.25x"
    SPEED_0_5X = "0.5x"
    SPEED_1X = "1x"
    SPEED_2X = "2x"
    SPEED_4X = "4x"
    SPEED_8X = "8x"

class AnalyticsVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PARTICIPANT = "PARTICIPANT"
    JUDGE = "JUDGE"
    ADMIN = "ADMIN"
    FORENSIC = "FORENSIC"

@dataclass
class EngineVersionInfo:
    engine_version: str = "1.0.0"
    rules_version: str = "1.0.0"
    scoring_version: str = "1.0.0"
    evidence_engine_version: str = "1.0.0"
    analytics_version: str = "1.0.0"

@dataclass
class TimelineEvent:
    event_id: str
    event_index: int
    timestamp: float
    round_name: str
    event_type: str
    summary: str
    actor: Optional[str] = None
    team: Optional[str] = None
    speaker: Optional[str] = None
    source_refs: List[str] = field(default_factory=list)
    target_refs: List[str] = field(default_factory=list)
    strategic_impact: str = "NEUTRAL"
    payload: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CausalNode:
    node_id: str
    node_type: str   # CLAIM, EVIDENCE, ARGUMENT, ATTACK, DEFENSE, CLASH, MOMENTUM, JUDGE, SCORE
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CausalLink:
    link_id: str
    source_id: str
    target_id: str
    relation_type: CausalRelationType
    description: str = ""
    confidence: float = 0.90

@dataclass
class TurningPointAnalytics:
    turning_point_id: str
    timestamp: float
    round_name: str
    source_event_id: str
    importance_score: float # 0.0 - 100.0
    reason: str
    affected_argument_id: Optional[str] = None
    affected_clash_id: Optional[str] = None
    momentum_shift: float = 0.0
    confidence: float = 0.90

@dataclass
class WinReasonItem:
    reason_title: str
    explanation: str
    decisive_clash_refs: List[str] = field(default_factory=list)
    argument_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    judge_evaluation_refs: List[str] = field(default_factory=list)

@dataclass
class ExecutiveSummary:
    topic: str
    topic_description: str
    winning_team: TeamSide
    margin: float
    proposition_score: float
    opposition_score: float
    decisive_clashes: List[str]
    major_arguments: List[str]
    evidence_developments: List[str]
    turning_points: List[str]
    strongest_rebuttals: List[str]
    major_concessions: List[str]
    unresolved_questions: List[str]
    win_reasons: List[WinReasonItem] = field(default_factory=list)

@dataclass
class ReplayCheckpoint:
    checkpoint_id: str
    checkpoint_type: CheckpointType
    event_index: int
    timestamp: float
    round_name: str
    active_arguments_count: int
    active_clashes_count: int
    momentum_score: float
    scores_snapshot: Dict[str, float]
