"""
Debate Arena - Canonical Data Models & Definitions
Adhering strictly to 01_DEBATE_CORE_CONSTITUTION.md & 02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
import time
import uuid

class ExecutionContext(str, Enum):
    OFFICIAL_ARENA = "OFFICIAL_ARENA"
    TRAINING_MODE = "TRAINING_MODE"

class EventState(str, Enum):
    SETUP = "SETUP"
    TOPIC_LOCK = "TOPIC_LOCK"
    TEAM_READY = "TEAM_READY"
    INTRODUCTION = "INTRODUCTION"
    RULE_BRIEFING = "RULE_BRIEFING"
    OPENING = "OPENING"
    CONSTRUCTIVE = "CONSTRUCTIVE"
    EVIDENCE_ARGUMENT = "EVIDENCE_ARGUMENT"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    REBUTTAL = "REBUTTAL"
    CLASH_ROUND = "CLASH_ROUND"
    FINAL_REBUTTAL = "FINAL_REBUTTAL"
    CLOSING = "CLOSING"
    DELIBERATION = "DELIBERATION"
    VERDICT = "VERDICT"
    POST_DEBATE_ANALYSIS = "POST_DEBATE_ANALYSIS"
    ARCHIVE = "ARCHIVE"
    PAUSED = "PAUSED"

class TeamSide(str, Enum):
    PROPOSITION = "PROPOSITION"
    OPPOSITION = "OPPOSITION"
    NEUTRAL = "NEUTRAL"

class SpeakerId(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    HOST = "HOST"
    MODERATOR = "MODERATOR"
    REFEREE = "REFEREE"
    JUDGE_A = "JUDGE_A"
    JUDGE_B = "JUDGE_B"
    JUDGE_C = "JUDGE_C"

class AIRole(str, Enum):
    HOST = "HOST"
    MODERATOR = "MODERATOR"
    TIMEKEEPER = "TIMEKEEPER"
    REFEREE = "REFEREE"
    FACT_CHECKER = "FACT_CHECKER"
    EVIDENCE_ANALYST = "EVIDENCE_ANALYST"
    ARGUMENT_ANALYST = "ARGUMENT_ANALYST"
    CROSS_EXAM_ANALYST = "CROSS_EXAM_ANALYST"
    REBUTTAL_ANALYST = "REBUTTAL_ANALYST"
    CLASH_ANALYST = "CLASH_ANALYST"
    JUDGE_A = "JUDGE_A"  # Logic & Argument
    JUDGE_B = "JUDGE_B"  # Evidence & Factuality
    JUDGE_C = "JUDGE_C"  # Strategy & Responsiveness
    SCORE_ENGINE = "SCORE_ENGINE"
    COMMENTATOR = "COMMENTATOR"
    POST_DEBATE_ANALYST = "POST_DEBATE_ANALYST"

class ActionType(str, Enum):
    # Setup & Admin
    CREATE_EVENT = "CREATE_EVENT"
    LOCK_TOPIC = "LOCK_TOPIC"
    READY_TEAM = "READY_TEAM"
    START_EVENT = "START_EVENT"
    TRANSITION_STATE = "TRANSITION_STATE"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    
    # Speech Actions
    START_SPEECH = "START_SPEECH"
    SPEAK = "SPEAK"
    END_SPEECH = "END_SPEECH"
    
    # Cross Examination Actions
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    FOLLOW_UP = "FOLLOW_UP"
    RESPONSE = "RESPONSE"
    
    # Rebuttal & Argument Actions
    PRESENT_ARGUMENT = "PRESENT_ARGUMENT"
    PRESENT_EVIDENCE = "PRESENT_EVIDENCE"
    PRESENT_CLAIM = "PRESENT_CLAIM"
    REBUT = "REBUT"
    
    # Interruptions / Points
    POINT_OF_ORDER = "POINT_OF_ORDER"
    POINT_OF_CLARIFICATION = "POINT_OF_CLARIFICATION"
    CHALLENGE = "CHALLENGE"
    
    # Moderation & Adjudication
    MODERATOR_INTERVENTION = "MODERATOR_INTERVENTION"
    WARNING = "WARNING"
    SCORE_UPDATE = "SCORE_UPDATE"
    VERDICT_ISSUE = "VERDICT_ISSUE"

class EventFlag(str, Enum):
    TIME_WARNING = "TIME_WARNING"
    TIME_EXPIRED = "TIME_EXPIRED"
    RULE_VIOLATION = "RULE_VIOLATION"
    RELEVANCE_WARNING = "RELEVANCE_WARNING"
    REPETITION_WARNING = "REPETITION_WARNING"
    EVASION_DETECTED = "EVASION_DETECTED"
    EVIDENCE_CHALLENGE = "EVIDENCE_CHALLENGE"
    FACT_CHECK_REQUIRED = "FACT_CHECK_REQUIRED"
    MODERATOR_INTERVENTION = "MODERATOR_INTERVENTION"
    SPEAKER_CHANGE = "SPEAKER_CHANGE"
    ROUND_COMPLETE = "ROUND_COMPLETE"
    CLASH_UPDATED = "CLASH_UPDATED"
    SCORING_EVENT = "SCORING_EVENT"

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    OUTDATED = "OUTDATED"
    MISREPRESENTED = "MISREPRESENTED"

class RelationshipType(str, Enum):
    SUPPORTS = "SUPPORTS"
    ATTACKS = "ATTACKS"
    DEFENDS = "DEFENDS"
    CONTRADICTS = "CONTRADICTS"
    QUALIFIES = "QUALIFIES"
    DEPENDS_ON = "DEPENDS_ON"
    UNANSWERED_BY = "UNANSWERED_BY"

# ---------------------------------------------------------------------------
# Core Entities
# ---------------------------------------------------------------------------

class DebaterProfile(BaseModel):
    speaker_id: SpeakerId
    name: str
    team: TeamSide
    role_description: str = ""
    user_id: Optional[str] = None
    avatar_url: Optional[str] = None
    is_ready: bool = False
    is_speaking: bool = False
    is_muted: bool = False

class EvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"EVD-{uuid.uuid4().hex[:8]}")
    speaker_id: SpeakerId
    team: TeamSide
    source_citation: str
    source_type: str  # MANUSCRIPT, SCRIPTURE, ACADEMIC_LEXICON, PATRISTIC, HISTORICAL
    verse_or_passage: Optional[str] = None
    lemma_greek_hebrew: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    integrity_notes: str = ""
    timestamp: float = Field(default_factory=time.time)

class ClaimItem(BaseModel):
    claim_id: str = Field(default_factory=lambda: f"CLM-{uuid.uuid4().hex[:8]}")
    speaker_id: SpeakerId
    team: TeamSide
    statement: str
    timestamp: float = Field(default_factory=time.time)
    evidence_ids: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    opposing_response_ids: List[str] = Field(default_factory=list)
    status: str = "ACTIVE"

class ArgumentItem(BaseModel):
    argument_id: str = Field(default_factory=lambda: f"ARG-{uuid.uuid4().hex[:8]}")
    speaker_id: SpeakerId
    team: TeamSide
    claim: str
    premises: List[str] = Field(default_factory=list)
    reasoning: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    impact: str = ""
    target_argument_id: Optional[str] = None
    relationship: Optional[RelationshipType] = None
    opposing_response_ids: List[str] = Field(default_factory=list)
    status: str = "ACTIVE"  # ACTIVE, REBUTTED, UNANSWERED, CONCEDED
    timestamp: float = Field(default_factory=time.time)

class CriticalClash(BaseModel):
    clash_id: str = Field(default_factory=lambda: f"CLASH-{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    proposition_arguments: List[str] = Field(default_factory=list)
    opposition_arguments: List[str] = Field(default_factory=list)
    current_advantage: Optional[TeamSide] = None
    resolved: bool = False
    outcome_summary: str = ""

# ---------------------------------------------------------------------------
# Scoring (100 Points Rubric)
# ---------------------------------------------------------------------------

class DebaterScoreCategory(BaseModel):
    argument_quality: float = 0.0      # Max 20
    evidence_factuality: float = 0.0   # Max 15
    logical_reasoning: float = 0.0     # Max 15
    rebuttal: float = 0.0              # Max 15
    cross_examination: float = 0.0     # Max 10
    responsiveness: float = 0.0        # Max 10
    clarity_structure: float = 0.0     # Max 5
    debate_strategy: float = 0.0       # Max 5
    team_contribution: float = 0.0     # Max 5

    @property
    def total_score(self) -> float:
        return sum([
            self.argument_quality,
            self.evidence_factuality,
            self.logical_reasoning,
            self.rebuttal,
            self.cross_examination,
            self.responsiveness,
            self.clarity_structure,
            self.debate_strategy,
            self.team_contribution
        ])

class ScoreAuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"SCR-{uuid.uuid4().hex[:8]}")
    timestamp: float = Field(default_factory=time.time)
    judge_source: AIRole  # JUDGE_A, JUDGE_B, JUDGE_C, SCORE_ENGINE
    speaker_id: SpeakerId
    team: TeamSide
    category: str
    delta: float
    new_value: float
    reason: str
    evidence_ref: Optional[str] = None
    confidence: float = 1.0

# ---------------------------------------------------------------------------
# Canonical Event State Object
# ---------------------------------------------------------------------------

class EventStateObject(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid.uuid4().hex[:8]}")
    mode: ExecutionContext = ExecutionContext.OFFICIAL_ARENA
    topic: str = ""
    topic_description: str = ""
    status: str = "INITIALIZED"
    current_state: EventState = EventState.SETUP
    previous_state: Optional[EventState] = None
    current_round: str = "SETUP"
    current_team: Optional[TeamSide] = None
    current_speaker: Optional[SpeakerId] = None
    speaker_role: str = ""
    turn_index: int = 0
    remaining_time: int = 0
    round_time: int = 0
    is_paused: bool = False
    
    # Roster (6 Human Debaters)
    debaters: Dict[str, DebaterProfile] = Field(default_factory=dict)
    
    # Active Models
    allowed_actions: List[ActionType] = Field(default_factory=list)
    forbidden_actions: List[ActionType] = Field(default_factory=list)
    active_clashes: List[CriticalClash] = Field(default_factory=list)
    active_arguments: List[ArgumentItem] = Field(default_factory=list)
    active_claims: List[ClaimItem] = Field(default_factory=list)
    active_evidence: List[EvidenceItem] = Field(default_factory=list)
    
    # Scoring State
    individual_scores: Dict[str, DebaterScoreCategory] = Field(default_factory=dict)
    score_audit_log: List[ScoreAuditEvent] = Field(default_factory=list)
    
    # Moderation & Flags
    moderator_notes: List[str] = Field(default_factory=list)
    event_flags: List[EventFlag] = Field(default_factory=list)
    
    # Deliberation & Verdict
    winning_team: Optional[TeamSide] = None
    verdict_summary: str = ""
    post_debate_report: Optional[Dict[str, Any]] = None
