"""
Debate Arena - Debater Persona Engine
Adheres to 10_DEBATE_PERSONA_ZUMA_INTEGRATION.md.
Manages debater personas, ZUMA skill integration, alignment tracking, and training mode coaching.
"""

from typing import Dict, List, Optional, Tuple, Any, Set
import uuid
import time

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState
)
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

class PersonaEngine:
    """Controls persona activation, behavior observation, alignment calculation, and training coaching."""

    def __init__(self, mode: ArenaMode = ArenaMode.OFFICIAL_ARENA):
        self.mode: ArenaMode = mode
        self.personas: Dict[str, DebaterPersona] = {}
        self.active_personas: Dict[str, str] = {} # SpeakerId (str) -> persona_id
        self.observations: Dict[str, List[ObservedBehaviorItem]] = {} # SpeakerId -> List[ObservedBehaviorItem]
        self.pattern_catalog: Dict[str, PersonaPattern] = {}

        self._init_default_catalog()

    def _init_default_catalog(self):
        # Register default ZUMA patterns
        for p in ZUMA_PATTERNS_V1:
            self.pattern_catalog[p.pattern_id] = p
        for p in GENERIC_COMMON_PATTERNS:
            self.pattern_catalog[p.pattern_id] = p

        # Register default ZUMA Apologetics Persona
        zuma_p = build_zuma_apologetics_persona()
        self.register_persona(zuma_p)

    def set_arena_mode(self, mode: ArenaMode):
        self.mode = mode

    def register_persona(self, persona: DebaterPersona):
        self.personas[persona.persona_id] = persona

    def activate_debater_persona(self, speaker_id: SpeakerId, persona_id: str) -> bool:
        if persona_id not in self.personas:
            return False
        self.active_personas[speaker_id.value] = persona_id
        if speaker_id.value not in self.observations:
            self.observations[speaker_id.value] = []
        return True

    def get_active_persona(self, speaker_id: SpeakerId) -> Optional[DebaterPersona]:
        pid = self.active_personas.get(speaker_id.value)
        return self.personas.get(pid) if pid else None

    # -----------------------------------------------------------------------
    # Pattern Provenance & Attribution Verification
    # -----------------------------------------------------------------------

    def verify_pattern_attribution(self, pattern_id: str) -> Tuple[bool, str, float]:
        """
        Verifies whether a pattern is legitimately ZUMA-specific with proven source data.
        Returns: (is_zuma_specific, provenance_info, confidence)
        """
        pattern = self.pattern_catalog.get(pattern_id)
        if not pattern:
            return False, "Unknown pattern: Not found in catalog.", 0.0

        if pattern.pattern_type == PatternType.COMMON_DEBATE_PATTERN:
            return False, f"Common debate behavior: {pattern.name} is generic, not ZUMA-specific.", pattern.confidence

        provenance = f"Source: {pattern.source_video} [{pattern.source_segment}] (Freq={pattern.frequency}, Sources={pattern.source_count})"
        return True, provenance, pattern.confidence

    # -----------------------------------------------------------------------
    # Behavior Observation & Alignment Tracking
    # -----------------------------------------------------------------------

    def record_observed_behavior(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        round_name: str,
        dimension: PersonaDimension,
        observed_tactic: str,
        matched_pattern_id: Optional[str] = None,
        confidence: float = 0.90
    ) -> ObservedBehaviorItem:
        obs = ObservedBehaviorItem(
            observation_id=f"OBS-{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            speaker_id=speaker_id,
            team=team,
            round_name=round_name,
            dimension=dimension,
            observed_tactic=observed_tactic,
            matched_pattern_id=matched_pattern_id,
            confidence=confidence
        )
        if speaker_id.value not in self.observations:
            self.observations[speaker_id.value] = []
        self.observations[speaker_id.value].append(obs)
        return obs

    def calculate_alignment(self, speaker_id: SpeakerId) -> PersonaAlignmentReport:
        """
        Computes Persona Alignment Score (0-100).
        Strictly isolated from the official 100-point debate score.
        """
        persona = self.get_active_persona(speaker_id)
        if not persona:
            return PersonaAlignmentReport(
                speaker_id=speaker_id,
                persona_id="NONE",
                overall_alignment_score=0.0,
                recommendation="No active persona configured."
            )

        obs_list = self.observations.get(speaker_id.value, [])
        if not obs_list:
            return PersonaAlignmentReport(
                speaker_id=speaker_id,
                persona_id=persona.persona_id,
                overall_alignment_score=50.0,
                recommendation="Insufficient observations to compute robust alignment."
            )

        # Calculate dimension match
        dimension_counts: Dict[str, int] = {}
        dimension_matches: Dict[str, int] = {}

        for obs in obs_list:
            dim = obs.dimension.value
            dimension_counts[dim] = dimension_counts.get(dim, 0) + 1
            if obs.matched_pattern_id:
                is_zuma, _, _ = self.verify_pattern_attribution(obs.matched_pattern_id)
                if is_zuma or obs.matched_pattern_id in [p.pattern_id for s in persona.skills for p in s.patterns]:
                    dimension_matches[dim] = dimension_matches.get(dim, 0) + 1

        dimension_scores: Dict[str, float] = {}
        for dim, count in dimension_counts.items():
            matches = dimension_matches.get(dim, 0)
            ratio = matches / count
            dimension_scores[dim] = round(ratio * 100.0, 1)

        overall = sum(dimension_scores.values()) / max(1, len(dimension_scores)) if dimension_scores else 50.0

        # Drift Detection: divergence >= 40% from expected profile
        drift = overall < 50.0
        drift_msg = "Observed behavior shows substantial divergence from selected persona profile." if drift else "Consistent alignment with persona strategy."

        return PersonaAlignmentReport(
            speaker_id=speaker_id,
            persona_id=persona.persona_id,
            overall_alignment_score=round(overall, 1),
            dimension_scores=dimension_scores,
            detected_drift=drift,
            drift_explanation=drift_msg,
            strengths=persona.strengths[:2],
            weaknesses=persona.weaknesses[:2],
            recommendation="Maintain Socratic focus on premise locking during cross-examination." if overall >= 75.0 else "Increase direct textual and premise engagement."
        )

    # -----------------------------------------------------------------------
    # Conflict Resolution: Hierarchy Enforcement
    # -----------------------------------------------------------------------

    def resolve_action_conflict(self, rule_allowed: bool, persona_desired: bool) -> bool:
        """
        Enforces Article 37-38: EVENT RULES > ROLE > PERSONA > SKILL > STYLE.
        Event rules strictly overrule persona desires.
        """
        if not rule_allowed:
            return False
        return persona_desired

    # -----------------------------------------------------------------------
    # Training Mode Coaching (Isolated from Official Arena)
    # -----------------------------------------------------------------------

    def generate_training_feedback(
        self,
        speaker_id: SpeakerId,
        round_name: str,
        opponent_statement: str
    ) -> TrainingFeedbackItem:
        """
        Provides tactical suggestions strictly inside TRAINING_ARENA mode.
        Raises PermissionError if attempted in OFFICIAL_ARENA.
        """
        if self.mode == ArenaMode.OFFICIAL_ARENA:
            raise PermissionError("Coaching Violation: Cannot generate live coaching in OFFICIAL_ARENA mode.")

        persona = self.get_active_persona(speaker_id)
        pname = persona.name if persona else "Standard Debater"

        return TrainingFeedbackItem(
            feedback_id=f"TRN-{uuid.uuid4().hex[:8]}",
            speaker_id=speaker_id,
            round_name=round_name,
            suggested_questions=[
                f"Socratic check: What is the underlying premise of '{opponent_statement[:30]}...'?",
                "Ask opponent to provide primary source documentation for the factual claim."
            ],
            rebuttal_options=[
                "Ilzam al-Khasm: Demonstrate internal inconsistency within opponent's authoritative sources.",
                "Scope qualification: Concede minor empirical point while maintaining strategic principle."
            ],
            evidence_recommendations=[
                "Cite Codex Sinaiticus or primary academic peer-reviewed surveys."
            ],
            strategic_alternatives=[
                "Prioritize premise locking rather than general conclusion denial."
            ]
        )
