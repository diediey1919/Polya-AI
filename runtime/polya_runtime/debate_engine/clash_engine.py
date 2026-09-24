"""
Debate Arena - Critical Clash Engine
Adheres to 07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md.
Identifies, ranks, prioritizes top 3-5 decisive clashes, and tracks clash advantage over time.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import TeamSide

class ClashType(str, Enum):
    FACTUAL = "FACTUAL"
    CAUSAL = "CAUSAL"
    DEFINITIONAL = "DEFINITIONAL"
    POLICY = "POLICY"
    TRADEOFF = "TRADEOFF"
    VALUE = "VALUE"
    PREDICTIVE = "PREDICTIVE"
    EMPIRICAL = "EMPIRICAL"
    STRATEGIC = "STRATEGIC"

class ClashImportance(str, Enum):
    DECISIVE = "DECISIVE"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ClashStatus(str, Enum):
    EMERGING = "EMERGING"
    ACTIVE = "ACTIVE"
    CONTESTED = "CONTESTED"
    PROPOSITION_ADVANTAGE = "PROPOSITION_ADVANTAGE"
    OPPOSITION_ADVANTAGE = "OPPOSITION_ADVANTAGE"
    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"

class ClashAdvantage(str, Enum):
    PROPOSITION_ADVANTAGE = "PROPOSITION_ADVANTAGE"
    OPPOSITION_ADVANTAGE = "OPPOSITION_ADVANTAGE"
    CONTESTED = "CONTESTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

@dataclass
class ClashItem:
    clash_id: str
    title: str
    question: str
    proposition_position: str
    opposition_position: str
    clash_type: ClashType = ClashType.EMPIRICAL
    importance: ClashImportance = ClashImportance.HIGH
    motion_relevance: float = 8.0     # 1-10 scale
    centrality_weight: float = 8.0    # 1-10 scale
    evidence_significance: float = 8.0 # 1-10 scale
    strategic_attention: float = 8.0  # 1-10 scale
    argument_refs: List[str] = field(default_factory=list)
    claim_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    status: ClashStatus = ClashStatus.ACTIVE
    advantage: ClashAdvantage = ClashAdvantage.CONTESTED
    confidence: float = 0.85
    resolution_summary: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def composite_rank_score(self) -> float:
        """Computes deterministic importance rank score based on Prompt 7 Article 26 formula."""
        return (
            (self.motion_relevance * 0.30) +
            (self.centrality_weight * 0.25) +
            (self.evidence_significance * 0.20) +
            (self.strategic_attention * 0.15) +
            (len(self.argument_refs) * 0.10)
        )

class CriticalClashEngine:
    """Tracks, evaluates, and dynamically ranks the core disputes of the debate."""

    def __init__(self):
        self.clashes: Dict[str, ClashItem] = {}
        self._clash_counter: int = 0

    def register_clash(
        self,
        title: str,
        question: str,
        proposition_position: str,
        opposition_position: str,
        clash_type: ClashType = ClashType.EMPIRICAL,
        importance: ClashImportance = ClashImportance.HIGH,
        motion_relevance: float = 8.0,
        centrality_weight: float = 8.0,
        evidence_significance: float = 8.0,
        strategic_attention: float = 8.0,
        argument_refs: Optional[List[str]] = None,
        claim_refs: Optional[List[str]] = None,
        evidence_refs: Optional[List[str]] = None
    ) -> ClashItem:
        self._clash_counter += 1
        cid = f"CLASH-{self._clash_counter:03d}"

        clash = ClashItem(
            clash_id=cid,
            title=title,
            question=question,
            proposition_position=proposition_position,
            opposition_position=opposition_position,
            clash_type=clash_type,
            importance=importance,
            motion_relevance=motion_relevance,
            centrality_weight=centrality_weight,
            evidence_significance=evidence_significance,
            strategic_attention=strategic_attention,
            argument_refs=argument_refs or [],
            claim_refs=claim_refs or [],
            evidence_refs=evidence_refs or []
        )
        self.clashes[cid] = clash
        return clash

    def update_advantage(
        self,
        clash_id: str,
        advantage: ClashAdvantage,
        confidence: float = 0.85,
        reason: str = ""
    ) -> bool:
        if clash_id not in self.clashes:
            return False
        clash = self.clashes[clash_id]
        clash.advantage = advantage
        clash.confidence = confidence
        if advantage == ClashAdvantage.PROPOSITION_ADVANTAGE:
            clash.status = ClashStatus.PROPOSITION_ADVANTAGE
        elif advantage == ClashAdvantage.OPPOSITION_ADVANTAGE:
            clash.status = ClashStatus.OPPOSITION_ADVANTAGE
        else:
            clash.status = ClashStatus.CONTESTED

        clash.updated_at = time.time()
        return True

    def get_top_critical_clashes(self, limit: int = 3) -> List[ClashItem]:
        """Returns top 3-5 critical clashes sorted deterministically by composite rank score."""
        sorted_clashes = sorted(
            self.clashes.values(),
            key=lambda c: c.composite_rank_score,
            reverse=True
        )
        return sorted_clashes[:limit]

    def resolve_clash(self, clash_id: str, resolution_summary: str) -> bool:
        if clash_id in self.clashes:
            self.clashes[clash_id].status = ClashStatus.RESOLVED
            self.clashes[clash_id].resolution_summary = resolution_summary
            self.clashes[clash_id].updated_at = time.time()
            return True
        return False
