"""
Debate Arena - AI Commentary Engine
Adheres to 08_DEBATE_AI_COMMENTARY_ENGINE.md.
Provides neutral, real-time, event-driven broadcast analysis without coaching,
score leaks, role collision, or debate state mutation.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time
import uuid
import re

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventState,
    AIRole
)
from polya_runtime.debate_engine.argument_engine import (
    ArgumentNode,
    ArgumentHierarchy,
    ArgumentStatus,
    AttackType,
    DefenseType,
    AnswerStatus
)
from polya_runtime.debate_engine.clash_engine import (
    ClashItem,
    ClashAdvantage,
    ClashStatus
)
from polya_runtime.debate_engine.momentum_engine import (
    MomentumEvent,
    TurningPointItem
)
from polya_runtime.debate_engine.evidence_fact_engine import (
    FactCheckResult,
    FactCheckVerdict
)

# ---------------------------------------------------------------------------
# Enums & Configurations
# ---------------------------------------------------------------------------

class CommentaryType(str, Enum):
    OPENING_COMMENTARY = "OPENING_COMMENTARY"
    ROUND_COMMENTARY = "ROUND_COMMENTARY"
    ARGUMENT_COMMENTARY = "ARGUMENT_COMMENTARY"
    ATTACK_COMMENTARY = "ATTACK_COMMENTARY"
    DEFENSE_COMMENTARY = "DEFENSE_COMMENTARY"
    EVIDENCE_COMMENTARY = "EVIDENCE_COMMENTARY"
    CROSS_EXAM_COMMENTARY = "CROSS_EXAM_COMMENTARY"
    REBUTTAL_COMMENTARY = "REBUTTAL_COMMENTARY"
    CLASH_COMMENTARY = "CLASH_COMMENTARY"
    MOMENTUM_COMMENTARY = "MOMENTUM_COMMENTARY"
    TURNING_POINT_COMMENTARY = "TURNING_POINT_COMMENTARY"
    TEAM_COMMENTARY = "TEAM_COMMENTARY"
    UNANSWERED_COMMENTARY = "UNANSWERED_COMMENTARY"
    CONCESSION_COMMENTARY = "CONCESSION_COMMENTARY"
    TRANSITION_COMMENTARY = "TRANSITION_COMMENTARY"
    POST_ROUND_COMMENTARY = "POST_ROUND_COMMENTARY"
    FINAL_ANALYSIS = "FINAL_ANALYSIS"

class CommentaryStyle(str, Enum):
    PROFESSIONAL_BROADCAST = "PROFESSIONAL_BROADCAST"
    ANALYTICAL = "ANALYTICAL"
    ACADEMIC = "ACADEMIC"
    MINIMAL = "MINIMAL"

class CommentaryFrequency(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    BROADCAST = "BROADCAST"

class CommentaryPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class CommentaryItem:
    commentary_id: str
    timestamp: float
    round_name: str
    commentary_type: CommentaryType
    priority: CommentaryPriority
    text: str
    confidence: float = 0.90
    speaker_context: Optional[str] = None
    team_context: Optional[str] = None
    event_id: Optional[str] = None
    source_events: List[str] = field(default_factory=list)
    source_arguments: List[str] = field(default_factory=list)
    source_clashes: List[str] = field(default_factory=list)
    source_evidence: List[str] = field(default_factory=list)
    momentum_context: Optional[Dict[str, Any]] = None
    visibility: str = "PUBLIC"
    is_suppressed: bool = False
    suppression_reason: Optional[str] = None

# ---------------------------------------------------------------------------
# Safety Filter
# ---------------------------------------------------------------------------

class CommentarySafetyFilter:
    """Enforces strict neutrality, no coaching, no score leak, and factual calibration."""

    COACHING_PATTERNS = [
        re.compile(r"\b(should|seharusnya|harus|perlu|ought to|needs to)\s+(attack|ask|say|bring|refute|counter|menyerang|bertanya|menjawab|membantah|mengajukan)\b", re.IGNORECASE),
        re.compile(r"\b(advise|suggest|sarankan|rekomendasikan)\s+(that|the|tim|speaker)\b", re.IGNORECASE),
        re.compile(r"\b(best move for|langkah terbaik untuk)\b", re.IGNORECASE)
    ]

    SCORE_LEAK_PATTERNS = [
        re.compile(r"\b\d+(\.\d+)?\s*(points?|pts|poin|nilai)\b", re.IGNORECASE),
        re.compile(r"\b(score is|current score|skor saat ini|memiliki nilai)\s*\d+", re.IGNORECASE),
        re.compile(r"\b(judge [abc]|juri [abc])\s*(gave|gives|memberikan)\b", re.IGNORECASE)
    ]

    FALSE_CERTAINTY_PATTERNS = [
        re.compile(r"\b(definitely false|pasti bohong|terbukti salah total|100% false)\b", re.IGNORECASE)
    ]

    PREMATURE_WINNER_PATTERNS = [
        re.compile(r"\b(has won the debate|telah memenangkan debat|guaranteed victory|pasti menang)\b", re.IGNORECASE)
    ]

    @classmethod
    def validate_and_filter(
        cls,
        text: str,
        confidence: float,
        is_live_match: bool = True,
        is_official_verdict_announced: bool = False
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validates commentary text.
        Returns: (is_valid, calibrated_text, rejection_reason)
        """
        # 1. Coaching Check
        for pattern in cls.COACHING_PATTERNS:
            if pattern.search(text):
                return False, text, "Coaching violation: Commentary attempts to prescribe debater actions."

        # 2. Score Leak Check (Live competition before verdict)
        if is_live_match and not is_official_verdict_announced:
            for pattern in cls.SCORE_LEAK_PATTERNS:
                if pattern.search(text):
                    return False, text, "Score leak violation: Commentary reveals unadjudicated or private scoring data."

        # 3. Premature Winner Declaration
        if is_live_match and not is_official_verdict_announced:
            for pattern in cls.PREMATURE_WINNER_PATTERNS:
                if pattern.search(text):
                    return False, text, "Premature verdict violation: Commentary declares winner before official adjudication."

        # 4. False Certainty Check on Unverified Evidence
        for pattern in cls.FALSE_CERTAINTY_PATTERNS:
            if pattern.search(text):
                return False, text, "Uncertainty violation: Commentary asserts definitive falsity on contested/unverified claim."

        # 5. Confidence-Based Language Calibration
        calibrated = text
        if confidence < 0.60:
            return False, text, "Low confidence suppression: Analysis confidence below minimum threshold (0.60)."
        elif confidence < 0.80:
            # Soften assertions if overly definitive
            if "directly refutes" in calibrated.lower():
                calibrated = re.sub(r"directly refutes", "appears to challenge", calibrated, flags=re.IGNORECASE)
            if "has proven" in calibrated.lower():
                calibrated = re.sub(r"has proven", "presents evidence indicating", calibrated, flags=re.IGNORECASE)

        return True, calibrated, None

# ---------------------------------------------------------------------------
# Commentary Engine
# ---------------------------------------------------------------------------

class CommentaryEngine:
    """
    Read-only, event-driven strategic broadcast analyst.
    Translates live debate state into structured broadcast commentary.
    """

    def __init__(
        self,
        frequency: CommentaryFrequency = CommentaryFrequency.MEDIUM,
        style: CommentaryStyle = CommentaryStyle.PROFESSIONAL_BROADCAST,
        cooldown_sec: float = 5.0
    ):
        self.frequency = frequency
        self.style = style
        self.cooldown_sec = cooldown_sec
        self.last_commentary_time: float = 0.0
        self.published_commentary: List[CommentaryItem] = []
        self.queued_commentary: List[CommentaryItem] = []
        self.pending_dedup_window: List[Dict[str, Any]] = []

    def set_frequency(self, frequency: CommentaryFrequency):
        self.frequency = frequency

    def set_style(self, style: CommentaryStyle):
        self.style = style

    def can_broadcast_now(self, priority: CommentaryPriority, is_active_speech: bool = False) -> bool:
        """Determines if commentary can be broadcast immediately without interrupting speakers."""
        if is_active_speech and priority != CommentaryPriority.CRITICAL:
            return False
        if priority in (CommentaryPriority.HIGH, CommentaryPriority.CRITICAL):
            return True
        now = time.time()
        return (now - self.last_commentary_time) >= self.cooldown_sec

    # -----------------------------------------------------------------------
    # Commentary Generators (Event-Driven & Read-Only)
    # -----------------------------------------------------------------------

    def generate_opening_commentary(self, topic: str, description: str = "") -> Optional[CommentaryItem]:
        text = f"The debate opens on the motion: \"{topic}\". Strategically, key clash points will likely center on the policy's empirical viability and systemic trade-offs."
        return self._create_and_publish(
            commentary_type=CommentaryType.OPENING_COMMENTARY,
            priority=CommentaryPriority.HIGH,
            text=text,
            round_name="ROUND_0_INTRO",
            confidence=0.95
        )

    def generate_round_commentary(self, round_name: str, objective: str, speaker_id: Optional[SpeakerId] = None) -> Optional[CommentaryItem]:
        spk_desc = f" with {speaker_id.value} holding the floor" if speaker_id else ""
        text = f"We enter {round_name}{spk_desc}. This session tests: {objective}."
        return self._create_and_publish(
            commentary_type=CommentaryType.ROUND_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            speaker_context=speaker_id.value if speaker_id else None,
            confidence=0.92
        )

    def generate_argument_commentary(
        self,
        node: ArgumentNode,
        round_name: str,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        prefix = f"{node.speaker_id.value} ({node.team.value})"
        if node.hierarchy == ArgumentHierarchy.CORE:
            text = f"{prefix} establishes a core argument: \"{node.claim_text}\", framing the foundational thesis for {node.team.value}."
        elif node.relation:
            text = f"{prefix} advances a {node.hierarchy.value.lower()} ({node.relation.value.lower()}) regarding: \"{node.claim_text}\"."
        else:
            text = f"{prefix} introduces: \"{node.claim_text}\"."

        return self._create_and_publish(
            commentary_type=CommentaryType.ARGUMENT_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            speaker_context=node.speaker_id.value,
            team_context=node.team.value,
            source_arguments=[node.argument_id],
            confidence=node.confidence,
            is_active_speech=is_active_speech
        )

    def generate_attack_commentary(
        self,
        attacker: SpeakerId,
        attacker_team: TeamSide,
        target_argument_id: str,
        attack_type: AttackType,
        reason: str,
        round_name: str,
        confidence: float = 0.90,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        text = f"{attacker.value} launches a {attack_type.value.lower().replace('_', ' ')} against [{target_argument_id}]: {reason}"
        return self._create_and_publish(
            commentary_type=CommentaryType.ATTACK_COMMENTARY,
            priority=CommentaryPriority.HIGH,
            text=text,
            round_name=round_name,
            speaker_context=attacker.value,
            team_context=attacker_team.value,
            source_arguments=[target_argument_id],
            confidence=confidence,
            is_active_speech=is_active_speech
        )

    def generate_defense_commentary(
        self,
        defender: SpeakerId,
        defender_team: TeamSide,
        protected_argument_id: str,
        defense_type: DefenseType,
        reason: str,
        round_name: str,
        is_rebuilt: bool = False,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        rebuild_note = " The argument has been restructured to defend against the objection." if is_rebuilt else ""
        text = f"{defender.value} mounts a {defense_type.value.lower().replace('_', ' ')} to protect [{protected_argument_id}].{rebuild_note}"
        return self._create_and_publish(
            commentary_type=CommentaryType.DEFENSE_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            speaker_context=defender.value,
            team_context=defender_team.value,
            source_arguments=[protected_argument_id],
            confidence=0.88,
            is_active_speech=is_active_speech
        )

    def generate_evidence_commentary(
        self,
        fact_check: FactCheckResult,
        round_name: str,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        if fact_check.verdict == FactCheckVerdict.SUPPORTED:
            text = f"Fact-check update: Claim [{fact_check.claim_id}] is supported by verified source documentation."
        elif fact_check.verdict == FactCheckVerdict.CONTRADICTED:
            text = f"Fact-check update: Claim [{fact_check.claim_id}] is contradicted by verified source material ({fact_check.basis})."
        elif fact_check.verdict == FactCheckVerdict.MISLEADING:
            text = f"Fact-check update: Claim [{fact_check.claim_id}] has been marked as misleading contextually ({fact_check.basis})."
        else:
            text = f"Fact-check update: Claim [{fact_check.claim_id}] remains unverified pending corroborating primary evidence."

        return self._create_and_publish(
            commentary_type=CommentaryType.EVIDENCE_COMMENTARY,
            priority=CommentaryPriority.HIGH if fact_check.verdict in (FactCheckVerdict.CONTRADICTED, FactCheckVerdict.MISLEADING) else CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            speaker_context=fact_check.speaker_id.value,
            team_context=fact_check.team.value,
            source_evidence=[fact_check.claim_id],
            confidence=fact_check.confidence,
            is_active_speech=is_active_speech
        )

    def generate_clash_commentary(
        self,
        clash: ClashItem,
        round_name: str,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        adv_text = ""
        if clash.advantage == ClashAdvantage.PROPOSITION_ADVANTAGE:
            adv_text = " Proposition currently maintains strategic advantage on this front."
        elif clash.advantage == ClashAdvantage.OPPOSITION_ADVANTAGE:
            adv_text = " Opposition currently holds strategic advantage on this front."
        elif clash.advantage == ClashAdvantage.CONTESTED:
            adv_text = " Both sides remain heavily contested on this issue."

        text = f"Critical Clash [{clash.clash_id}] '{clash.title}': The central question is \"{clash.question}\".{adv_text}"
        return self._create_and_publish(
            commentary_type=CommentaryType.CLASH_COMMENTARY,
            priority=CommentaryPriority.HIGH,
            text=text,
            round_name=round_name,
            source_clashes=[clash.clash_id],
            confidence=clash.confidence,
            is_active_speech=is_active_speech
        )

    def generate_momentum_commentary(
        self,
        momentum_event: MomentumEvent,
        current_momentum_score: float,
        round_name: str,
        is_active_speech: bool = False
    ) -> Optional[CommentaryItem]:
        # Only comment on significant shifts (|delta| >= 10.0)
        if abs(momentum_event.delta) < 10.0 and self.frequency != CommentaryFrequency.HIGH:
            return None

        leader = "Proposition" if current_momentum_score > 5.0 else ("Opposition" if current_momentum_score < -5.0 else "Neither team")
        text = f"Strategic Momentum shift: {momentum_event.team.value} gains ground following '{momentum_event.trigger_event}'. {leader} currently controls overall debate tempo."
        
        return self._create_and_publish(
            commentary_type=CommentaryType.MOMENTUM_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            team_context=momentum_event.team.value,
            momentum_context={"delta": momentum_event.delta, "total_score": current_momentum_score},
            confidence=momentum_event.confidence,
            is_active_speech=is_active_speech
        )

    def generate_turning_point_commentary(
        self,
        turning_point: TurningPointItem,
        round_name: str
    ) -> Optional[CommentaryItem]:
        text = f"Turning Point identified: Decisive momentum reversal triggered by '{turning_point.trigger_event}'. {turning_point.reason}"
        return self._create_and_publish(
            commentary_type=CommentaryType.TURNING_POINT_COMMENTARY,
            priority=CommentaryPriority.CRITICAL,  # Bypasses cooldown
            text=text,
            round_name=round_name,
            source_arguments=[turning_point.related_argument_id] if turning_point.related_argument_id else [],
            source_clashes=[turning_point.related_clash_id] if turning_point.related_clash_id else [],
            confidence=0.92
        )

    def generate_unanswered_commentary(
        self,
        argument_id: str,
        claim_text: str,
        team: TeamSide,
        round_name: str
    ) -> Optional[CommentaryItem]:
        text = f"Strategic Observation: Argument [{argument_id}] (\"{claim_text}\") by {team.value} currently stands without a direct response at this stage."
        return self._create_and_publish(
            commentary_type=CommentaryType.UNANSWERED_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=text,
            round_name=round_name,
            team_context=team.value,
            source_arguments=[argument_id],
            confidence=0.88
        )

    def generate_concession_commentary(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        conceded_point: str,
        strategic_framing: str,
        round_name: str
    ) -> Optional[CommentaryItem]:
        text = f"{speaker_id.value} ({team.value}) strategically concedes: \"{conceded_point}\", shifting emphasis to {strategic_framing}."
        return self._create_and_publish(
            commentary_type=CommentaryType.CONCESSION_COMMENTARY,
            priority=CommentaryPriority.HIGH,
            text=text,
            round_name=round_name,
            speaker_context=speaker_id.value,
            team_context=team.value,
            confidence=0.90
        )

    def generate_final_analysis(
        self,
        winning_team: TeamSide,
        margin: float,
        top_clashes: List[str],
        round_name: str = "ROUND_10_VERDICT"
    ) -> Optional[CommentaryItem]:
        clash_summary = f" Decisive clashes resolved were: {', '.join(top_clashes)}." if top_clashes else ""
        text = f"Final Match Analysis: Official adjudication confirms victory for {winning_team.value} with a margin of {margin:.1f} points.{clash_summary}"
        return self._create_and_publish(
            commentary_type=CommentaryType.FINAL_ANALYSIS,
            priority=CommentaryPriority.CRITICAL,
            text=text,
            round_name=round_name,
            confidence=0.98,
            is_official_verdict_announced=True
        )

    # -----------------------------------------------------------------------
    # Deduplication & Publishing Pipeline
    # -----------------------------------------------------------------------

    def merge_and_deduplicate(self, events: List[Dict[str, Any]], round_name: str) -> Optional[CommentaryItem]:
        """Merges multiple co-occurring events into a single coherent commentary."""
        if not events:
            return None

        # Extract event types and summaries
        has_evidence_contradicted = any(e.get("type") == "EVIDENCE_CONTRADICTED" for e in events)
        has_argument_weakened = any(e.get("type") == "ARGUMENT_WEAKENED" for e in events)
        has_momentum_shift = any(e.get("type") == "MOMENTUM_SHIFT" for e in events)

        if has_evidence_contradicted and has_argument_weakened:
            text = "Strategic development: Evidence contradiction has weakened the associated argument, impacting the contested critical clash."
            return self._create_and_publish(
                commentary_type=CommentaryType.ARGUMENT_COMMENTARY,
                priority=CommentaryPriority.HIGH,
                text=text,
                round_name=round_name,
                confidence=0.92
            )
        
        # Fallback to the highest priority event
        first_event = events[0]
        return self._create_and_publish(
            commentary_type=CommentaryType.ARGUMENT_COMMENTARY,
            priority=CommentaryPriority.MEDIUM,
            text=first_event.get("text", "Strategic adjustment observed."),
            round_name=round_name,
            confidence=0.85
        )

    def _create_and_publish(
        self,
        commentary_type: CommentaryType,
        priority: CommentaryPriority,
        text: str,
        round_name: str,
        confidence: float = 0.90,
        speaker_context: Optional[str] = None,
        team_context: Optional[str] = None,
        source_arguments: Optional[List[str]] = None,
        source_clashes: Optional[List[str]] = None,
        source_evidence: Optional[List[str]] = None,
        momentum_context: Optional[Dict[str, Any]] = None,
        is_active_speech: bool = False,
        is_official_verdict_announced: bool = False
    ) -> Optional[CommentaryItem]:
        cid = f"COM-{uuid.uuid4().hex[:8]}"

        # 1. Run Safety Filter
        is_valid, calibrated_text, rejection_reason = CommentarySafetyFilter.validate_and_filter(
            text=text,
            confidence=confidence,
            is_live_match=True,
            is_official_verdict_announced=is_official_verdict_announced
        )

        item = CommentaryItem(
            commentary_id=cid,
            timestamp=time.time(),
            round_name=round_name,
            commentary_type=commentary_type,
            priority=priority,
            text=calibrated_text,
            confidence=confidence,
            speaker_context=speaker_context,
            team_context=team_context,
            source_arguments=source_arguments or [],
            source_clashes=source_clashes or [],
            source_evidence=source_evidence or [],
            momentum_context=momentum_context,
            is_suppressed=not is_valid,
            suppression_reason=rejection_reason
        )

        if not is_valid:
            # Record suppressed item for audit trail
            self.published_commentary.append(item)
            return None

        # 2. Check Cooldown & Speaker Active
        if not self.can_broadcast_now(priority, is_active_speech):
            self.queued_commentary.append(item)
            return item

        # 3. Publish
        self.last_commentary_time = time.time()
        self.published_commentary.append(item)
        return item

    def flush_queue(self) -> List[CommentaryItem]:
        """Flushes queued commentary items when speaker turn ends or transition occurs."""
        flushed = []
        while self.queued_commentary:
            item = self.queued_commentary.pop(0)
            self.last_commentary_time = time.time()
            flushed.append(item)
        return flushed
