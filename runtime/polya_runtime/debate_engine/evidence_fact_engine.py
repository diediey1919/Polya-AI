"""
Debate Arena - Fact Check & Evidence Engine
Adheres to 06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md.
Provides claim classification, source provenance auditing, evidence-claim matching,
evidence laundering detection, and Evidence Graph management.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
import time
import uuid

from polya_runtime.debate_engine.models import (
    SpeakerId,
    TeamSide,
    EventStateObject
)

class ClaimType(str, Enum):
    FACTUAL = "FACTUAL"
    STATISTICAL = "STATISTICAL"
    HISTORICAL = "HISTORICAL"
    SCIENTIFIC = "SCIENTIFIC"
    LEGAL = "LEGAL"
    ECONOMIC = "ECONOMIC"
    CAUSAL = "CAUSAL"
    PREDICTIVE = "PREDICTIVE"
    DEFINITIONAL = "DEFINITIONAL"
    COMPARATIVE = "COMPARATIVE"
    NORMATIVE = "NORMATIVE"
    HYPOTHETICAL = "HYPOTHETICAL"

class ClaimImportance(str, Enum):
    CENTRAL = "CENTRAL"
    IMPORTANT = "IMPORTANT"
    SUPPORTING = "SUPPORTING"
    MINOR = "MINOR"

class FactCheckVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    MOSTLY_SUPPORTED = "MOSTLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVERIFIED = "UNVERIFIED"
    OUTDATED = "OUTDATED"
    MISLEADING = "MISLEADING"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"

class SourceType(str, Enum):
    PRIMARY_SOURCE = "PRIMARY_SOURCE"
    MANUSCRIPT = "MANUSCRIPT"
    ACADEMIC_SOURCE = "ACADEMIC_SOURCE"
    PATRISTIC = "PATRISTIC"
    GOVERNMENT_SOURCE = "GOVERNMENT_SOURCE"
    OFFICIAL_STATISTICS = "OFFICIAL_STATISTICS"
    COURT_DOCUMENT = "COURT_DOCUMENT"
    NEWS_SOURCE = "NEWS_SOURCE"
    SECONDARY_SOURCE = "SECONDARY_SOURCE"
    UNKNOWN = "UNKNOWN"

class EvidenceStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    OUTDATED = "OUTDATED"
    MISREPRESENTED = "MISREPRESENTED"
    INSUFFICIENT = "INSUFFICIENT"
    PENDING = "PENDING"

class QuoteIntegrityStatus(str, Enum):
    QUOTE_VERIFIED = "QUOTE_VERIFIED"
    QUOTE_PARTIAL = "QUOTE_PARTIAL"
    QUOTE_MISREPRESENTED = "QUOTE_MISREPRESENTED"
    QUOTE_UNVERIFIED = "QUOTE_UNVERIFIED"

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SourceItem:
    source_id: str
    title: str
    author: str
    publisher: str
    publication_year: int
    source_type: SourceType
    quality_score: float = 8.0  # Out of 10
    primary_origin_id: Optional[str] = None # Tracks shared origin for evidence laundering detection

@dataclass
class EvidenceDetail:
    evidence_id: str
    source_id: str
    speaker_id: SpeakerId
    team: TeamSide
    quoted_text: str
    context_notes: str = ""
    quote_status: QuoteIntegrityStatus = QuoteIntegrityStatus.QUOTE_VERIFIED
    is_cherry_picked: bool = False
    is_context_stripped: bool = False
    is_causality_overclaim: bool = False
    status: EvidenceStatus = EvidenceStatus.VERIFIED
    confidence: float = 0.90
    timestamp: float = field(default_factory=time.time)

@dataclass
class ClaimDetail:
    claim_id: str
    speaker_id: SpeakerId
    team: TeamSide
    statement: str
    claim_type: ClaimType = ClaimType.FACTUAL
    importance: ClaimImportance = ClaimImportance.IMPORTANT
    evidence_ids: List[str] = field(default_factory=list)
    verification_status: FactCheckVerdict = FactCheckVerdict.UNVERIFIED
    confidence: float = 0.80
    related_argument_ids: List[str] = field(default_factory=list)
    related_clash_ids: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

@dataclass
class FactCheckResult:
    fact_check_id: str
    claim_id: str
    speaker_id: SpeakerId
    team: TeamSide
    verdict: FactCheckVerdict
    confidence: float
    basis: str
    source_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    is_reused_from_cache: bool = False
    timestamp: float = field(default_factory=time.time)

# ---------------------------------------------------------------------------
# Core Subsystems
# ---------------------------------------------------------------------------

class ClaimEngine:
    """Manages claim identification, classification, deduplication, and lifecycle."""

    def __init__(self):
        self.claims: Dict[str, ClaimDetail] = {}
        self._claim_counter: int = 0

    def register_claim(
        self,
        speaker_id: SpeakerId,
        team: TeamSide,
        statement: str,
        claim_type: ClaimType = ClaimType.FACTUAL,
        importance: ClaimImportance = ClaimImportance.IMPORTANT,
        related_argument_ids: Optional[List[str]] = None,
        related_clash_ids: Optional[List[str]] = None
    ) -> ClaimDetail:
        self._claim_counter += 1
        prefix = "PRO" if team == TeamSide.PROPOSITION else "CON"
        cid = f"{prefix}-CLM-{self._claim_counter:03d}"

        # Deduplication check: detect existing identical statement
        for existing in self.claims.values():
            if existing.statement.strip().lower() == statement.strip().lower() and existing.team == team:
                return existing

        claim = ClaimDetail(
            claim_id=cid,
            speaker_id=speaker_id,
            team=team,
            statement=statement,
            claim_type=claim_type,
            importance=importance,
            related_argument_ids=related_argument_ids or [],
            related_clash_ids=related_clash_ids or []
        )
        self.claims[cid] = claim
        return claim

    def is_normative(self, claim: ClaimDetail) -> bool:
        return claim.claim_type == ClaimType.NORMATIVE

class SourceAnalyzer:
    """Evaluates source reliability, provenance, and detects evidence laundering."""

    def __init__(self):
        self.sources: Dict[str, SourceItem] = {}

    def register_source(
        self,
        source_id: str,
        title: str,
        author: str,
        publisher: str,
        publication_year: int,
        source_type: SourceType,
        quality_score: float = 8.0,
        primary_origin_id: Optional[str] = None
    ) -> SourceItem:
        src = SourceItem(
            source_id=source_id,
            title=title,
            author=author,
            publisher=publisher,
            publication_year=publication_year,
            source_type=source_type,
            quality_score=quality_score,
            primary_origin_id=primary_origin_id
        )
        self.sources[source_id] = src
        return src

    def detect_evidence_laundering(self, source_ids: List[str]) -> Tuple[bool, int, str]:
        """
        Determines if multiple citations actually trace back to a single shared origin.
        Returns (is_laundered, independent_count, analysis).
        """
        origins: Set[str] = set()
        for sid in source_ids:
            src = self.sources.get(sid)
            if src:
                origin = src.primary_origin_id or src.source_id
                origins.add(origin)
            else:
                origins.add(sid)

        is_laundered = len(source_ids) > 1 and len(origins) == 1
        ind_count = len(origins)
        analysis = (
            f"Evidence laundering detected: {len(source_ids)} citations trace back to 1 single origin ({list(origins)[0]})."
            if is_laundered else f"{ind_count} independent source origins verified."
        )
        return is_laundered, ind_count, analysis

class EvidenceEngine:
    """Evaluates claim-to-evidence match, context stripping, correlation vs causation, and quotation integrity."""

    def __init__(self):
        self.evidence_registry: Dict[str, EvidenceDetail] = {}

    def register_evidence(
        self,
        evidence_id: str,
        source_id: str,
        speaker_id: SpeakerId,
        team: TeamSide,
        quoted_text: str,
        context_notes: str = "",
        quote_status: QuoteIntegrityStatus = QuoteIntegrityStatus.QUOTE_VERIFIED,
        is_cherry_picked: bool = False,
        is_context_stripped: bool = False,
        is_causality_overclaim: bool = False,
        status: EvidenceStatus = EvidenceStatus.VERIFIED,
        confidence: float = 0.90
    ) -> EvidenceDetail:
        evd = EvidenceDetail(
            evidence_id=evidence_id,
            source_id=source_id,
            speaker_id=speaker_id,
            team=team,
            quoted_text=quoted_text,
            context_notes=context_notes,
            quote_status=quote_status,
            is_cherry_picked=is_cherry_picked,
            is_context_stripped=is_context_stripped,
            is_causality_overclaim=is_causality_overclaim,
            status=status,
            confidence=confidence
        )
        self.evidence_registry[evidence_id] = evd
        return evd

class FactCheckEngine:
    """Main verification engine producing nuanced verdicts while preserving uncertainty."""

    def __init__(self, claim_engine: ClaimEngine, source_analyzer: SourceAnalyzer, evidence_engine: EvidenceEngine):
        self.claim_engine = claim_engine
        self.source_analyzer = source_analyzer
        self.evidence_engine = evidence_engine
        self.results_history: List[FactCheckResult] = []
        self._verification_cache: Dict[str, FactCheckResult] = {}

    def verify_claim(
        self,
        claim_id: str,
        evidence_ids: List[str],
        basis_explanation: str = "",
        override_verdict: Optional[FactCheckVerdict] = None,
        confidence: float = 0.90
    ) -> FactCheckResult:
        claim = self.claim_engine.claims.get(claim_id)
        if not claim:
            raise ValueError(f"Claim {claim_id} not found in ClaimEngine.")

        # Normative claims cannot be given factual verdicts
        if claim.claim_type == ClaimType.NORMATIVE:
            res = FactCheckResult(
                fact_check_id=f"FC-{uuid.uuid4().hex[:8]}",
                claim_id=claim_id,
                speaker_id=claim.speaker_id,
                team=claim.team,
                verdict=FactCheckVerdict.UNVERIFIED,
                confidence=1.0,
                basis="Normative statement: evaluated by reasoning and values, not empirical fact-check.",
                source_refs=[],
                evidence_refs=[]
            )
            return res

        # Cache check for performance
        cache_key = f"{claim.statement.strip().lower()}:{sorted(evidence_ids)}"
        if cache_key in self._verification_cache:
            cached = self._verification_cache[cache_key]
            reused = FactCheckResult(
                fact_check_id=f"FC-{uuid.uuid4().hex[:8]}",
                claim_id=claim_id,
                speaker_id=claim.speaker_id,
                team=claim.team,
                verdict=cached.verdict,
                confidence=cached.confidence,
                basis=f"{cached.basis} (Reused from cache)",
                source_refs=cached.source_refs,
                evidence_refs=evidence_ids,
                is_reused_from_cache=True
            )
            self.results_history.append(reused)
            claim.verification_status = cached.verdict
            return reused

        # Determine verdict
        if override_verdict is not None:
            verdict = override_verdict
        elif not evidence_ids:
            verdict = FactCheckVerdict.UNVERIFIED
            basis_explanation = "No evidence provided for factual assertion. (Unverified is not false)."
        else:
            # Check evidence properties
            has_overclaim = any(self.evidence_engine.evidence_registry[e].is_causality_overclaim for e in evidence_ids if e in self.evidence_engine.evidence_registry)
            has_misleading = any(self.evidence_engine.evidence_registry[e].is_context_stripped for e in evidence_ids if e in self.evidence_engine.evidence_registry)
            
            if has_overclaim:
                verdict = FactCheckVerdict.MISLEADING
                basis_explanation = "Causality overclaim: associative/correlation evidence cited as proof of causation."
            elif has_misleading:
                verdict = FactCheckVerdict.PARTIALLY_SUPPORTED
                basis_explanation = "Contextual stripping detected: statistic accurate within specific parameters but misrepresented as universal."
            else:
                verdict = FactCheckVerdict.SUPPORTED
                basis_explanation = basis_explanation or "Empirically supported by primary evidence and critical manuscripts."

        # Collect source refs
        src_refs = []
        for eid in evidence_ids:
            evd = self.evidence_engine.evidence_registry.get(eid)
            if evd and evd.source_id:
                src_refs.append(evd.source_id)

        result = FactCheckResult(
            fact_check_id=f"FC-{uuid.uuid4().hex[:8]}",
            claim_id=claim_id,
            speaker_id=claim.speaker_id,
            team=claim.team,
            verdict=verdict,
            confidence=confidence,
            basis=basis_explanation,
            source_refs=src_refs,
            evidence_refs=evidence_ids
        )
        self.results_history.append(result)
        self._verification_cache[cache_key] = result
        claim.verification_status = verdict
        return result

class EvidenceGraphManager:
    """Maintains the full bidirectional graph: SOURCE -> EVIDENCE -> CLAIM -> ARGUMENT -> CLASH -> SCORING."""

    def __init__(self, claim_engine: ClaimEngine, source_analyzer: SourceAnalyzer, evidence_engine: EvidenceEngine, fact_checker: FactCheckEngine):
        self.claim_engine = claim_engine
        self.source_analyzer = source_analyzer
        self.evidence_engine = evidence_engine
        self.fact_checker = fact_checker
        self.claim_to_argument_map: Dict[str, Set[str]] = {}
        self.claim_to_clash_map: Dict[str, Set[str]] = {}

    def link_claim_to_argument(self, claim_id: str, argument_id: str):
        if claim_id not in self.claim_to_argument_map:
            self.claim_to_argument_map[claim_id] = set()
        self.claim_to_argument_map[claim_id].add(argument_id)

    def link_claim_to_clash(self, claim_id: str, clash_id: str):
        if claim_id not in self.claim_to_clash_map:
            self.claim_to_clash_map[claim_id] = set()
        self.claim_to_clash_map[claim_id].add(clash_id)

    def get_lineage(self, claim_id: str) -> Dict[str, Any]:
        claim = self.claim_engine.claims.get(claim_id)
        if not claim:
            return {}
        
        ev_list = [self.evidence_engine.evidence_registry.get(e) for e in claim.evidence_ids if e in self.evidence_engine.evidence_registry]
        src_list = [self.source_analyzer.sources.get(e.source_id) for e in ev_list if e and e.source_id in self.source_analyzer.sources]

        return {
            "claim_id": claim.claim_id,
            "statement": claim.statement,
            "type": claim.claim_type.value,
            "verdict": claim.verification_status.value,
            "evidence_count": len(ev_list),
            "sources": [s.title for s in src_list if s],
            "related_arguments": list(self.claim_to_argument_map.get(claim_id, set())),
            "related_clashes": list(self.claim_to_clash_map.get(claim_id, set()))
        }
