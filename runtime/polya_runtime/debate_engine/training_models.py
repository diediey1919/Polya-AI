"""
Debate Arena - Training Models & Definitions (Prompt 14)
Adheres strictly to PROMPT 14 — TRAINING MODE / AI DEBATER ARCHITECTURE.

Absolute separation:
- OFFICIAL_ARENA: Human vs Human (3v3), AI = Event Control only.
- TRAINING_MODE: Human vs AI, AI = Debate Participant Allowed.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time
import uuid

from polya_runtime.debate_engine.models import (
    ExecutionContext,
    TeamSide,
    VerificationStatus,
    RelationshipType
)

class TrainingType(str, Enum):
    PRACTICE_DEBATE = "PRACTICE_DEBATE"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    REBUTTAL_TRAINING = "REBUTTAL_TRAINING"
    EVIDENCE_CHALLENGE = "EVIDENCE_CHALLENGE"
    RAPID_FIRE = "RAPID_FIRE"
    FULL_MOCK_DEBATE = "FULL_MOCK_DEBATE"
    COACH_MODE = "COACH_MODE"

class TrainingDifficulty(str, Enum):
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"
    EXPERT = "EXPERT"
    ELITE = "ELITE"

class TrainingPersona(str, Enum):
    ZUMA_STYLE = "ZUMA_STYLE"
    SOCRATIC = "SOCRATIC"
    SKEPTICAL = "SKEPTICAL"
    ACADEMIC = "ACADEMIC"
    ADVERSARIAL = "ADVERSARIAL"
    EVIDENCE_DRIVEN = "EVIDENCE_DRIVEN"
    LOGIC_HEAVY = "LOGIC_HEAVY"
    CROSS_EXAMINER = "CROSS_EXAMINER"

class TrainingState(str, Enum):
    TRAINING_SETUP = "TRAINING_SETUP"
    TOPIC_LOCK = "TOPIC_LOCK"
    POSITION_ASSIGNMENT = "POSITION_ASSIGNMENT"
    OPENING = "OPENING"
    CONSTRUCTIVE = "CONSTRUCTIVE"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    REBUTTAL = "REBUTTAL"
    CLASH = "CLASH"
    FINAL_REBUTTAL = "FINAL_REBUTTAL"
    CLOSING = "CLOSING"
    EVALUATION = "EVALUATION"
    COACHING = "COACHING"
    ARCHIVE = "ARCHIVE"
    PAUSED = "PAUSED"

class TrainingSpeakerId(str, Enum):
    USER_DEBATER = "USER_DEBATER"
    AI_TRAINING_DEBATER = "AI_TRAINING_DEBATER"
    TRAINING_COACH = "TRAINING_COACH"
    TRAINING_EXAMINER = "TRAINING_EXAMINER"
    TRAINING_MODERATOR = "TRAINING_MODERATOR"

class TrainingActionType(str, Enum):
    # Setup & Admin
    CREATE_TRAINING = "CREATE_TRAINING"
    LOCK_TOPIC = "LOCK_TOPIC"
    ASSIGN_POSITION = "ASSIGN_POSITION"
    START_TRAINING = "START_TRAINING"
    TRANSITION_STATE = "TRANSITION_STATE"
    PAUSE = "PAUSE"
    RESUME = "RESUME"
    
    # Debater Actions
    START_SPEECH = "START_SPEECH"
    SPEAK = "SPEAK"
    END_SPEECH = "END_SPEECH"
    PRESENT_CLAIM = "PRESENT_CLAIM"
    PRESENT_ARGUMENT = "PRESENT_ARGUMENT"
    PRESENT_EVIDENCE = "PRESENT_EVIDENCE"
    REBUT = "REBUT"
    DEFEND = "DEFEND"
    CHALLENGE = "CHALLENGE"
    CLOSE = "CLOSE"
    
    # Cross Examination
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    FOLLOW_UP = "FOLLOW_UP"
    RESPONSE = "RESPONSE"
    
    # AI Self-Correction
    SELF_CORRECT = "SELF_CORRECT"
    
    # Evaluation & Coaching
    EVALUATE = "EVALUATE"
    PROVIDE_COACHING = "PROVIDE_COACHING"
    COMPLETE_TRAINING = "COMPLETE_TRAINING"

# ---------------------------------------------------------------------------
# Training Entities with Isolated Namespaces
# ---------------------------------------------------------------------------

class TrainingEvidenceItem(BaseModel):
    evidence_id: str = Field(default_factory=lambda: f"TRAIN-EVD-{uuid.uuid4().hex[:8]}")
    speaker_id: TrainingSpeakerId
    team: TeamSide
    source_citation: str
    source_type: str = "ACADEMIC_SOURCE"
    verse_or_passage: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    integrity_notes: str = ""
    is_hypothetical: bool = False
    timestamp: float = Field(default_factory=time.time)

class TrainingClaimItem(BaseModel):
    claim_id: str = Field(default_factory=lambda: f"TRAIN-CLAIM-{uuid.uuid4().hex[:8]}")
    speaker_id: TrainingSpeakerId
    team: TeamSide
    statement: str
    evidence_ids: List[str] = Field(default_factory=list)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    fact_check_notes: str = ""
    timestamp: float = Field(default_factory=time.time)

class TrainingArgumentItem(BaseModel):
    argument_id: str = Field(default_factory=lambda: f"USER-ARG-{uuid.uuid4().hex[:8]}")
    speaker_id: TrainingSpeakerId
    team: TeamSide
    claim: str
    premises: List[str] = Field(default_factory=list)
    reasoning: str = ""
    evidence_ids: List[str] = Field(default_factory=list)
    impact: str = ""
    target_argument_id: Optional[str] = None
    relationship: Optional[RelationshipType] = None
    status: str = "ACTIVE"
    is_hypothetical: bool = False
    timestamp: float = Field(default_factory=time.time)

class TrainingClash(BaseModel):
    clash_id: str = Field(default_factory=lambda: f"TRAIN-CLASH-{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    user_argument_ids: List[str] = Field(default_factory=list)
    ai_argument_ids: List[str] = Field(default_factory=list)
    current_advantage: Optional[TeamSide] = None
    resolved: bool = False
    outcome_summary: str = ""

# ---------------------------------------------------------------------------
# Diagnostic Scoring Rubric (Training Diagnostic Score)
# ---------------------------------------------------------------------------

class TrainingScoreCategory(BaseModel):
    argument_quality: float = 0.0      # Max 20
    evidence_factuality: float = 0.0   # Max 15
    logical_reasoning: float = 0.0     # Max 15
    rebuttal: float = 0.0              # Max 15
    cross_examination: float = 0.0     # Max 10
    responsiveness: float = 0.0        # Max 10
    clarity_structure: float = 0.0     # Max 5
    debate_strategy: float = 0.0       # Max 10

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
            self.debate_strategy
        ])

# ---------------------------------------------------------------------------
# Training Feedback (9-Point Structured Feedback)
# ---------------------------------------------------------------------------

class TrainingFeedback(BaseModel):
    feedback_id: str = Field(default_factory=lambda: f"FDBK-{uuid.uuid4().hex[:8]}")
    session_id: str
    what_you_did_well: List[str] = Field(default_factory=list)
    weak_arguments: List[str] = Field(default_factory=list)
    missed_rebuttals: List[str] = Field(default_factory=list)
    unanswered_questions: List[str] = Field(default_factory=list)
    evidence_problems: List[str] = Field(default_factory=list)
    logical_weaknesses: List[str] = Field(default_factory=list)
    best_moment: str = ""
    turning_point: str = ""
    what_to_improve: List[str] = Field(default_factory=list)
    overall_feedback: str = ""
    recommended_training_type: TrainingType = TrainingType.PRACTICE_DEBATE
    timestamp: float = Field(default_factory=time.time)

# ---------------------------------------------------------------------------
# Training Event Log & Session
# ---------------------------------------------------------------------------

class TrainingEventLogItem(BaseModel):
    event_id: str = Field(default_factory=lambda: f"TRAIN-EVT-{uuid.uuid4().hex[:8]}")
    session_id: str
    timestamp: float = Field(default_factory=time.time)
    state: str
    speaker_id: Optional[TrainingSpeakerId] = None
    team: Optional[TeamSide] = None
    action_type: str
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TrainingSessionObject(BaseModel):
    training_session_id: str = Field(default_factory=lambda: f"TRN-{uuid.uuid4().hex[:8]}")
    user_id: str = "user-default"
    mode: ExecutionContext = ExecutionContext.TRAINING_MODE
    topic: str = ""
    topic_description: str = ""
    user_position: TeamSide = TeamSide.PROPOSITION
    ai_position: TeamSide = TeamSide.OPPOSITION
    training_type: TrainingType = TrainingType.PRACTICE_DEBATE
    difficulty: TrainingDifficulty = TrainingDifficulty.NORMAL
    persona: TrainingPersona = TrainingPersona.ZUMA_STYLE
    
    current_state: TrainingState = TrainingState.TRAINING_SETUP
    round_name: str = "SETUP"
    turn_index: int = 0
    active_speaker: Optional[TrainingSpeakerId] = None
    remaining_time: int = 180
    round_time: int = 180
    is_paused: bool = False
    
    # State Models
    arguments: List[TrainingArgumentItem] = Field(default_factory=list)
    claims: List[TrainingClaimItem] = Field(default_factory=list)
    evidence: List[TrainingEvidenceItem] = Field(default_factory=list)
    clashes: List[TrainingClash] = Field(default_factory=list)
    cross_examination_turns: List[Dict[str, Any]] = Field(default_factory=list)
    rebuttals: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Diagnostic Score (Never leaked to official leaderboards)
    user_score: TrainingScoreCategory = Field(default_factory=TrainingScoreCategory)
    user_context: Dict[str, Any] = Field(default_factory=dict)
    ai_score: TrainingScoreCategory = Field(default_factory=TrainingScoreCategory)
    
    # Feedback & Self-Correction
    feedback: Optional[TrainingFeedback] = None
    ai_self_corrections: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Immutable Log
    event_log: List[TrainingEventLogItem] = Field(default_factory=list)
    
    is_completed: bool = False
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

# ---------------------------------------------------------------------------
# Training Achievement & Curriculum
# ---------------------------------------------------------------------------

class TrainingAchievement(BaseModel):
    achievement_id: str
    name: str
    description: str
    badge_icon: str
    unlocked_at: Optional[float] = None
    is_unlocked: bool = False

class TrainingCurriculum(BaseModel):
    user_id: str
    weaknesses_identified: List[str] = Field(default_factory=list)
    strengths_identified: List[str] = Field(default_factory=list)
    recommended_modules: List[Dict[str, Any]] = Field(default_factory=list)
    completion_rate: float = 0.0
