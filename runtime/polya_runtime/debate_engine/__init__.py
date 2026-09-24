"""
Debate Arena Event Engine & State Protocol Module
"""

from polya_runtime.debate_engine.models import (
    ExecutionContext,
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
from polya_runtime.debate_engine.training_engine import TrainingTimer, DebateTrainingEngine
from polya_runtime.debate_engine.training_api import DebateTrainingService
from polya_runtime.debate_engine.context_builder import OfficialArenaContextBuilder, TrainingContextBuilder
from polya_runtime.debate_engine.state_machine import DebateStateMachine, STATE_DEFINITIONS
from polya_runtime.debate_engine.permission_matrix import SpeakerPermissionMatrix
from polya_runtime.debate_engine.timer_engine import TimerEngine
from polya_runtime.debate_engine.action_validator import ActionValidator
from polya_runtime.debate_engine.event_log import EventLogManager, DebateLogEntry
from polya_runtime.debate_engine.context_builder import AIContextBuilder
from polya_runtime.debate_engine.round_configs import (
    RoundPhase,
    CrossExamStep,
    SpeakerTurnConfig,
    CrossExamExchangeConfig,
    RoundConfiguration,
    DEFAULT_ROUND_CONFIGS
)
from polya_runtime.debate_engine.round_engine import (
    RoundController,
    CrossExamRuntimeState,
    ArgumentLineage
)
from polya_runtime.debate_engine.referee_engine import (
    RefereeEngine,
    RefereeDecision,
    ProceduralViolation,
    ProceduralPenalty,
    ViolationType,
    ViolationSeverity,
    PenaltyType
)
from polya_runtime.debate_engine.moderator_engine import (
    ModeratorEngine,
    ModeratorIntervention,
    InterventionType
)
from polya_runtime.debate_engine.judge_engine import (
    MultiJudgePanel,
    JudgeEvaluationItem,
    JudgeA,
    JudgeB,
    JudgeC
)
from polya_runtime.debate_engine.score_aggregator import (
    ScoreAggregator,
    TeamScoreCategory,
    AdjudicationVerdict,
    CATEGORY_CAPS,
    TEAM_CATEGORY_CAPS
)
from polya_runtime.debate_engine.evidence_fact_engine import (
    ClaimEngine,
    SourceAnalyzer,
    EvidenceEngine,
    FactCheckEngine,
    EvidenceGraphManager,
    ClaimType,
    ClaimImportance,
    FactCheckVerdict,
    SourceType,
    EvidenceStatus,
    QuoteIntegrityStatus,
    SourceItem,
    EvidenceDetail,
    ClaimDetail,
    FactCheckResult
)
from polya_runtime.debate_engine.commentary_engine import (
    CommentaryEngine,
    CommentaryItem,
    CommentaryType,
    CommentaryPriority,
    CommentaryStyle,
    CommentaryFrequency,
    CommentarySafetyFilter
)
from polya_runtime.debate_engine.replay_models import (
    ReplayMode,
    CausalRelationType,
    CheckpointType,
    ReplaySpeed,
    AnalyticsVisibility,
    EngineVersionInfo,
    TimelineEvent,
    CausalNode,
    CausalLink,
    TurningPointAnalytics,
    WinReasonItem,
    ExecutiveSummary,
    ReplayCheckpoint
)
from polya_runtime.debate_engine.causal_graph import CausalGraphEngine
from polya_runtime.debate_engine.turning_point_engine import TurningPointEngine
from polya_runtime.debate_engine.analytics_engine import DebateAnalyticsEngine
from polya_runtime.debate_engine.replay_engine import DebateReplayEngine
from polya_runtime.debate_engine.persona_models import (
    ArenaMode,
    PatternType,
    PersonaDimension,
    PersonaPattern,
    PersonaSkill,
    PersonaStyleProfile,
    DebaterPersona,
    ObservedBehaviorItem,
    PersonaAlignmentReport,
    TrainingFeedbackItem
)
from polya_runtime.debate_engine.zuma_dataset import (
    build_zuma_apologetics_persona,
    ZUMA_PATTERNS_V1,
    GENERIC_COMMON_PATTERNS
)
from polya_runtime.debate_engine.persona_engine import PersonaEngine
from polya_runtime.debate_engine.engine import DebateArenaEventEngine
from polya_runtime.debate_engine.api import DebateArenaService, arena_service


__all__ = [
    "EventState",
    "TeamSide",
    "SpeakerId",
    "AIRole",
    "ActionType",
    "EventFlag",
    "VerificationStatus",
    "RelationshipType",
    "DebaterProfile",
    "EvidenceItem",
    "ClaimItem",
    "ArgumentItem",
    "CriticalClash",
    "DebaterScoreCategory",
    "ScoreAuditEvent",
    "EventStateObject",
    "DebateStateMachine",
    "STATE_DEFINITIONS",
    "SpeakerPermissionMatrix",
    "TimerEngine",
    "ActionValidator",
    "EventLogManager",
    "DebateLogEntry",
    "AIContextBuilder",
    "RoundPhase",
    "CrossExamStep",
    "SpeakerTurnConfig",
    "CrossExamExchangeConfig",
    "RoundConfiguration",
    "DEFAULT_ROUND_CONFIGS",
    "RoundController",
    "CrossExamRuntimeState",
    "ArgumentLineage",
    "RefereeEngine",
    "RefereeDecision",
    "ProceduralViolation",
    "ProceduralPenalty",
    "ViolationType",
    "ViolationSeverity",
    "PenaltyType",
    "ModeratorEngine",
    "ModeratorIntervention",
    "InterventionType",
    "MultiJudgePanel",
    "JudgeEvaluationItem",
    "JudgeA",
    "JudgeB",
    "JudgeC",
    "ScoreAggregator",
    "TeamScoreCategory",
    "AdjudicationVerdict",
    "CATEGORY_CAPS",
    "TEAM_CATEGORY_CAPS",
    "ClaimEngine",
    "SourceAnalyzer",
    "EvidenceEngine",
    "FactCheckEngine",
    "EvidenceGraphManager",
    "ClaimType",
    "ClaimImportance",
    "FactCheckVerdict",
    "SourceType",
    "EvidenceStatus",
    "QuoteIntegrityStatus",
    "SourceItem",
    "EvidenceDetail",
    "ClaimDetail",
    "FactCheckResult",
    "CommentaryEngine",
    "CommentaryItem",
    "CommentaryType",
    "CommentaryPriority",
    "CommentaryStyle",
    "CommentaryFrequency",
    "CommentarySafetyFilter",
    "ReplayMode",
    "CausalRelationType",
    "CheckpointType",
    "ReplaySpeed",
    "AnalyticsVisibility",
    "EngineVersionInfo",
    "TimelineEvent",
    "CausalNode",
    "CausalLink",
    "TurningPointAnalytics",
    "WinReasonItem",
    "ExecutiveSummary",
    "ReplayCheckpoint",
    "CausalGraphEngine",
    "TurningPointEngine",
    "DebateAnalyticsEngine",
    "DebateReplayEngine",
    "ArenaMode",
    "PatternType",
    "PersonaDimension",
    "PersonaPattern",
    "PersonaSkill",
    "PersonaStyleProfile",
    "DebaterPersona",
    "ObservedBehaviorItem",
    "PersonaAlignmentReport",
    "TrainingFeedbackItem",
    "build_zuma_apologetics_persona",
    "PersonaEngine",
    "DebateArenaEventEngine",
    "DebateArenaService",
    "arena_service",
    "ExecutionContext",
    "TrainingType",
    "TrainingDifficulty",
    "TrainingPersona",
    "TrainingState",
    "TrainingSpeakerId",
    "TrainingActionType",
    "TrainingEvidenceItem",
    "TrainingClaimItem",
    "TrainingArgumentItem",
    "TrainingClash",
    "TrainingScoreCategory",
    "TrainingFeedback",
    "TrainingEventLogItem",
    "TrainingSessionObject",
    "TrainingAchievement",
    "TrainingCurriculum",
    "TrainingStateMachine",
    "TrainingTimer",
    "DebateTrainingEngine",
    "DebateTrainingService",
    "OfficialArenaContextBuilder",
    "TrainingContextBuilder"
]

