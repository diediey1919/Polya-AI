"""
Debate Arena - Persona & Skill Data Models
Adheres to 10_DEBATE_PERSONA_ZUMA_INTEGRATION.md.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState
)

class ArenaMode(str, Enum):
    OFFICIAL_ARENA = "OFFICIAL_ARENA"   # Strict competition: AI is observer/official, zero coaching
    TRAINING_ARENA = "TRAINING_ARENA"   # Training environment: AI provides coaching & suggestions

class PatternType(str, Enum):
    ZUMA_SPECIFIC_PATTERN = "ZUMA_SPECIFIC_PATTERN"
    COMMON_DEBATE_PATTERN = "COMMON_DEBATE_PATTERN"

class PersonaDimension(str, Enum):
    ARGUMENT_FRAMING = "ARGUMENT_FRAMING"
    PREMISE_TESTING = "PREMISE_TESTING"
    EVIDENCE_HANDLING = "EVIDENCE_HANDLING"
    CROSS_EXAMINATION = "CROSS_EXAMINATION"
    REBUTTAL = "REBUTTAL"
    CLASH_SELECTION = "CLASH_SELECTION"
    BURDEN_OF_PROOF = "BURDEN_OF_PROOF"
    CONCESSION_HANDLING = "CONCESSION_HANDLING"
    TEXTUAL_ANALYSIS = "TEXTUAL_ANALYSIS"
    CLOSING_SYNTHESIS = "CLOSING_SYNTHESIS"
    COMMUNICATION = "COMMUNICATION"

@dataclass
class PersonaPattern:
    pattern_id: str
    name: str
    dimension: PersonaDimension
    description: str
    pattern_type: PatternType
    source_video: str
    source_segment: str
    frequency: int = 1
    source_count: int = 1
    confidence: float = 0.90

@dataclass
class PersonaSkill:
    skill_id: str
    name: str
    description: str
    category: str
    patterns: List[PersonaPattern] = field(default_factory=list)

@dataclass
class PersonaStyleProfile:
    style_id: str
    name: str
    tone: str = "Calm, precise, analytical"
    pacing: str = "Measured, deliberate"
    vocabulary: str = "Scholarly, forensic, legalistic"
    rhetorical_devices: List[str] = field(default_factory=list)

@dataclass
class DebaterPersona:
    persona_id: str
    name: str
    description: str
    version: str = "1.0.0"
    dimensions_profile: Dict[str, float] = field(default_factory=dict) # Dimension -> Expected Weight (0-100)
    skills: List[PersonaSkill] = field(default_factory=list)
    style_profile: Optional[PersonaStyleProfile] = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    preferred_tactics: List[str] = field(default_factory=list)
    avoid_tactics: List[str] = field(default_factory=list)

@dataclass
class ObservedBehaviorItem:
    observation_id: str
    timestamp: float
    speaker_id: SpeakerId
    team: TeamSide
    round_name: str
    dimension: PersonaDimension
    observed_tactic: str
    matched_pattern_id: Optional[str] = None
    confidence: float = 0.90

@dataclass
class PersonaAlignmentReport:
    speaker_id: SpeakerId
    persona_id: str
    overall_alignment_score: float # 0.0 - 100.0 (Strictly isolated from official 100pt debate score)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    detected_drift: bool = False
    drift_explanation: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendation: str = ""

@dataclass
class TrainingFeedbackItem:
    feedback_id: str
    speaker_id: SpeakerId
    round_name: str
    suggested_questions: List[str] = field(default_factory=list)
    rebuttal_options: List[str] = field(default_factory=list)
    evidence_recommendations: List[str] = field(default_factory=list)
    strategic_alternatives: List[str] = field(default_factory=list)
