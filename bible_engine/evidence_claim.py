"""
Evidence & Claim Foundation Subsystem (Task 2.8).
Specification: Architecture v2.0 — FROZEN.

Core principle: NO CONCLUSION MAY OUTRUN ITS EVIDENCE.

Epistemic rules:
  1. CONFIDENCE MUST NEVER BECOME EVIDENCE.
     A model confidence score cannot:
       - upgrade E-level
       - upgrade claim tier
       - establish identity
       - establish theology
       - establish historical fact
  2. AI output is never automatically E0-E12 primary evidence.
  3. Translation output cannot become E0 DIRECT_TEXT.
  4. Morphology cannot directly create T3/T4 claims.
  5. Syntax cannot directly create T3/T4 claims.
  6. Semantic sense cannot directly create T3/T4 claims.
  7. Discourse relation cannot directly create T3/T4 claims.
  8. Entity association cannot directly create STRICT_IDENTITY.
  9. Claims must preserve uncertainty.
  10. Counter-evidence must be representable independently.
  11. A claim with unresolved contradiction must not be silently marked established.
  12. Weakest-critical-dependency confidence propagation:
      final confidence must not exceed the weakest critical evidence dependency.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AIPrimaryEvidenceFirewallError,
    ClaimEvidenceLinkNotFoundError,
    ClaimNotFoundError,
    ConfidenceUpgradeFirewallError,
    DiscourseTheologyFirewallError,
    DuplicateClaimError,
    DuplicateClaimEvidenceLinkError,
    DuplicateEvidenceError,
    EvidenceClaimImmutabilityError,
    EvidenceClaimInvalidProvenanceError,
    EvidenceClaimInvalidVersionError,
    EvidenceClaimOrphanError,
    EvidenceClaimSubsystemError,
    EvidenceConfidenceError,
    EvidenceNotFoundError,
    IdentityFirewallError,
    InvalidClaimTierError,
    InvalidEpistemicTypeError,
    InvalidEvidenceClassError,
    InvalidEvidenceRelationshipError,
    MissingProvenanceError,
    MorphologyTheologyFirewallError,
    SemanticTheologyFirewallError,
    SourceTextNotFoundError,
    SyntaxTheologyFirewallError,
    TranslationToE0FirewallError,
    UnresolvedContradictionFirewallError,
    UnsupportedClaimError,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class EvidenceClass(str, Enum):
    """Controlled evidence classes (E0 through E12)."""
    E0_DIRECT_TEXT = "E0_DIRECT_TEXT"
    E1_TEXTUAL_MANUSCRIPT = "E1_TEXTUAL_MANUSCRIPT"
    E2_MORPHOLOGY = "E2_MORPHOLOGY"
    E3_SYNTAX = "E3_SYNTAX"
    E4_LEXICAL = "E4_LEXICAL"
    E5_DISCOURSE = "E5_DISCOURSE"
    E6_IMMEDIATE_CONTEXT = "E6_IMMEDIATE_CONTEXT"
    E7_BOOK_CONTEXT = "E7_BOOK_CONTEXT"
    E8_CORPUS_CONTEXT = "E8_CORPUS_CONTEXT"
    E9_HISTORICAL_LINGUISTIC = "E9_HISTORICAL_LINGUISTIC"
    E10_INTERTEXTUAL = "E10_INTERTEXTUAL"
    E11_EARLY_RECEPTION = "E11_EARLY_RECEPTION"
    E12_LATER_INTERPRETATION = "E12_LATER_INTERPRETATION"


class ClaimTier(str, Enum):
    """Epistemic claim tiers (T0 through T4)."""
    T0_RAW_OBSERVATION = "T0_RAW_OBSERVATION"
    T1_LINGUISTIC_FACT = "T1_LINGUISTIC_FACT"
    T2_CONTEXTUAL_CLAIM = "T2_CONTEXTUAL_CLAIM"
    T3_INTERPRETIVE_CLAIM = "T3_INTERPRETIVE_CLAIM"
    T4_THEOLOGICAL_CLAIM = "T4_THEOLOGICAL_CLAIM"


class EpistemicType(str, Enum):
    """Required epistemic types."""
    RAW_OBSERVATION = "RAW_OBSERVATION"
    LINGUISTIC_FACT = "LINGUISTIC_FACT"
    CONTEXTUAL_FACT = "CONTEXTUAL_FACT"
    HISTORICAL_FACT = "HISTORICAL_FACT"
    INFERENCE = "INFERENCE"
    INTERPRETATION = "INTERPRETATION"
    THEOLOGICAL_CLAIM = "THEOLOGICAL_CLAIM"


class EvidenceRelationship(str, Enum):
    """Evidence to claim relationship types."""
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    QUALIFY = "QUALIFY"
    LIMIT = "LIMIT"
    REFINE = "REFINE"


class EvidenceStatus(str, Enum):
    """Evidence status designations."""
    EXPLICIT = "[EXPLICIT]"
    GRAMMATICALLY_ESTABLISHED = "[GRAMMATICALLY ESTABLISHED]"
    LEXICALLY_SUPPORTED = "[LEXICALLY SUPPORTED]"
    CONTEXTUALLY_STRONG = "[CONTEXTUALLY STRONG]"
    INFERRED = "[INFERRED]"
    PLAUSIBLE = "[PLAUSIBLE]"
    AMBIGUOUS = "[AMBIGUOUS]"
    UNSUPPORTED = "[UNSUPPORTED]"
    CONTRADICTED = "[CONTRADICTED]"


class EpistemicStatus(str, Enum):
    """Epistemic status designations for claims."""
    VERIFIED_FACT = "VERIFIED_FACT"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    POSSIBLE_INTERPRETATION = "POSSIBLE_INTERPRETATION"
    UNPROVEN_DOGMA = "UNPROVEN_DOGMA"
    CONTRADICTED_BY_TEXT = "CONTRADICTED_BY_TEXT"
    UNRESOLVED_CONTRADICTION = "UNRESOLVED_CONTRADICTION"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"


class ConfidenceLevel(str, Enum):
    """Standardized discrete confidence levels."""
    CERTAIN = "CERTAIN"
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNSUPPORTED = "UNSUPPORTED"


# Mapping dictionaries for resilient coercion
_EVIDENCE_CLASS_MAP = {
    "E0": EvidenceClass.E0_DIRECT_TEXT,
    "E0_DIRECT_TEXT": EvidenceClass.E0_DIRECT_TEXT,
    "DIRECT_TEXT": EvidenceClass.E0_DIRECT_TEXT,
    "E1": EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
    "E1_TEXTUAL_MANUSCRIPT": EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
    "TEXTUAL_MANUSCRIPT": EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
    "E2": EvidenceClass.E2_MORPHOLOGY,
    "E2_MORPHOLOGY": EvidenceClass.E2_MORPHOLOGY,
    "MORPHOLOGY": EvidenceClass.E2_MORPHOLOGY,
    "E3": EvidenceClass.E3_SYNTAX,
    "E3_SYNTAX": EvidenceClass.E3_SYNTAX,
    "SYNTAX": EvidenceClass.E3_SYNTAX,
    "E4": EvidenceClass.E4_LEXICAL,
    "E4_LEXICAL": EvidenceClass.E4_LEXICAL,
    "LEXICAL": EvidenceClass.E4_LEXICAL,
    "E5": EvidenceClass.E5_DISCOURSE,
    "E5_DISCOURSE": EvidenceClass.E5_DISCOURSE,
    "DISCOURSE": EvidenceClass.E5_DISCOURSE,
    "E6": EvidenceClass.E6_IMMEDIATE_CONTEXT,
    "E6_IMMEDIATE_CONTEXT": EvidenceClass.E6_IMMEDIATE_CONTEXT,
    "IMMEDIATE_CONTEXT": EvidenceClass.E6_IMMEDIATE_CONTEXT,
    "E7": EvidenceClass.E7_BOOK_CONTEXT,
    "E7_BOOK_CONTEXT": EvidenceClass.E7_BOOK_CONTEXT,
    "BOOK_CONTEXT": EvidenceClass.E7_BOOK_CONTEXT,
    "E8": EvidenceClass.E8_CORPUS_CONTEXT,
    "E8_CORPUS_CONTEXT": EvidenceClass.E8_CORPUS_CONTEXT,
    "CORPUS_CONTEXT": EvidenceClass.E8_CORPUS_CONTEXT,
    "E9": EvidenceClass.E9_HISTORICAL_LINGUISTIC,
    "E9_HISTORICAL_LINGUISTIC": EvidenceClass.E9_HISTORICAL_LINGUISTIC,
    "HISTORICAL_LINGUISTIC": EvidenceClass.E9_HISTORICAL_LINGUISTIC,
    "E10": EvidenceClass.E10_INTERTEXTUAL,
    "E10_INTERTEXTUAL": EvidenceClass.E10_INTERTEXTUAL,
    "INTERTEXTUAL": EvidenceClass.E10_INTERTEXTUAL,
    "E11": EvidenceClass.E11_EARLY_RECEPTION,
    "E11_EARLY_RECEPTION": EvidenceClass.E11_EARLY_RECEPTION,
    "EARLY_RECEPTION": EvidenceClass.E11_EARLY_RECEPTION,
    "E12": EvidenceClass.E12_LATER_INTERPRETATION,
    "E12_LATER_INTERPRETATION": EvidenceClass.E12_LATER_INTERPRETATION,
    "LATER_INTERPRETATION": EvidenceClass.E12_LATER_INTERPRETATION,
}

_CLAIM_TIER_MAP = {
    "T0": ClaimTier.T0_RAW_OBSERVATION,
    "T0_RAW_OBSERVATION": ClaimTier.T0_RAW_OBSERVATION,
    "TIER_0_RAW_OBSERVATION": ClaimTier.T0_RAW_OBSERVATION,
    "RAW_OBSERVATION": ClaimTier.T0_RAW_OBSERVATION,
    "T1": ClaimTier.T1_LINGUISTIC_FACT,
    "T1_LINGUISTIC_FACT": ClaimTier.T1_LINGUISTIC_FACT,
    "TIER_1_LINGUISTIC_FACT": ClaimTier.T1_LINGUISTIC_FACT,
    "LINGUISTIC_FACT": ClaimTier.T1_LINGUISTIC_FACT,
    "T2": ClaimTier.T2_CONTEXTUAL_CLAIM,
    "T2_CONTEXTUAL_CLAIM": ClaimTier.T2_CONTEXTUAL_CLAIM,
    "TIER_2_CONTEXTUAL_CLAIM": ClaimTier.T2_CONTEXTUAL_CLAIM,
    "CONTEXTUAL_CLAIM": ClaimTier.T2_CONTEXTUAL_CLAIM,
    "T3": ClaimTier.T3_INTERPRETIVE_CLAIM,
    "T3_INTERPRETIVE_CLAIM": ClaimTier.T3_INTERPRETIVE_CLAIM,
    "TIER_3_INTERPRETIVE_CLAIM": ClaimTier.T3_INTERPRETIVE_CLAIM,
    "INTERPRETIVE_CLAIM": ClaimTier.T3_INTERPRETIVE_CLAIM,
    "T4": ClaimTier.T4_THEOLOGICAL_CLAIM,
    "T4_THEOLOGICAL_CLAIM": ClaimTier.T4_THEOLOGICAL_CLAIM,
    "TIER_4_THEOLOGICAL_CLAIM": ClaimTier.T4_THEOLOGICAL_CLAIM,
    "THEOLOGICAL_CLAIM": ClaimTier.T4_THEOLOGICAL_CLAIM,
}

_RELATIONSHIP_MAP = {
    "SUPPORT": EvidenceRelationship.SUPPORT,
    "SUPPORTS": EvidenceRelationship.SUPPORT,
    "CONTRADICT": EvidenceRelationship.CONTRADICT,
    "CONTRADICTS": EvidenceRelationship.CONTRADICT,
    "QUALIFY": EvidenceRelationship.QUALIFY,
    "QUALIFIES": EvidenceRelationship.QUALIFY,
    "LIMIT": EvidenceRelationship.LIMIT,
    "LIMITS": EvidenceRelationship.LIMIT,
    "REFINE": EvidenceRelationship.REFINE,
    "REFINES": EvidenceRelationship.REFINE,
}


def coerce_evidence_class(value: Any) -> EvidenceClass:
    if isinstance(value, EvidenceClass):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _EVIDENCE_CLASS_MAP:
            return _EVIDENCE_CLASS_MAP[key]
    raise InvalidEvidenceClassError(f"Invalid evidence class: '{value}'. Expected E0-E12.")


def coerce_claim_tier(value: Any) -> ClaimTier:
    if isinstance(value, ClaimTier):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _CLAIM_TIER_MAP:
            return _CLAIM_TIER_MAP[key]
    raise InvalidClaimTierError(f"Invalid claim tier: '{value}'. Expected T0-T4.")


def coerce_epistemic_type(value: Any) -> EpistemicType:
    if isinstance(value, EpistemicType):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        for member in EpistemicType:
            if member.value == key:
                return member
    raise InvalidEpistemicTypeError(
        f"Invalid epistemic type: '{value}'. Expected one of: "
        f"{[e.value for e in EpistemicType]}"
    )


def coerce_evidence_relationship(value: Any) -> EvidenceRelationship:
    if isinstance(value, EvidenceRelationship):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _RELATIONSHIP_MAP:
            return _RELATIONSHIP_MAP[key]
    raise InvalidEvidenceRelationshipError(
        f"Invalid evidence relationship: '{value}'. Expected SUPPORT, CONTRADICT, QUALIFY, LIMIT, REFINE."
    )


def coerce_confidence_level(value: Any) -> ConfidenceLevel:
    if isinstance(value, ConfidenceLevel):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        for member in ConfidenceLevel:
            if member.value == key:
                return member
    raise EvidenceConfidenceError(f"Invalid confidence level: '{value}'.")


def confidence_level_to_numeric(level: ConfidenceLevel) -> float:
    mapping = {
        ConfidenceLevel.CERTAIN: 1.0,
        ConfidenceLevel.VERY_HIGH: 0.9,
        ConfidenceLevel.HIGH: 0.8,
        ConfidenceLevel.MEDIUM: 0.5,
        ConfidenceLevel.LOW: 0.2,
        ConfidenceLevel.UNSUPPORTED: 0.0,
    }
    return mapping.get(level, 0.0)


# =============================================================================
# DEFINITIONS (Analyzer/User Inputs)
# =============================================================================

@dataclass(frozen=True)
class EvidenceDefinition:
    evidence_id: str
    pericope_id: str
    passage_id: str
    evidence_class: EvidenceClass | str
    epistemic_tier: ClaimTier | str
    source_reference: str
    extracted_text_or_data: str
    token_id: Optional[str] = None
    epistemic_type: Optional[EpistemicType | str] = None
    status: EvidenceStatus | str = EvidenceStatus.EXPLICIT
    confidence: ConfidenceLevel | str = ConfidenceLevel.HIGH
    confidence_score: Optional[float] = None
    is_counter_evidence: bool = False
    is_ai_generated: bool = False
    is_translation_derived: bool = False
    is_contradicted: bool = False
    provenance_id: Optional[str] = None
    version_id: Optional[str] = None
    metadata_json: Optional[str] = None


@dataclass
class ClaimDefinition:
    claim_id: str
    pericope_id: str
    claim_tier: ClaimTier | str
    epistemic_type: EpistemicType | str
    claim_text: str
    claimed_by: str
    passage_id: Optional[str] = None
    epistemic_status: EpistemicStatus | str = EpistemicStatus.PROVISIONAL
    confidence_score: float = 0.0
    calculated_confidence: float = 0.0
    is_unresolved_contradiction: bool = False
    has_counter_evidence: bool = False
    doctrinal_system: Optional[str] = None
    is_theology_independent: bool = False
    provenance_id: Optional[str] = None
    version_id: Optional[str] = None
    metadata_json: Optional[str] = None


@dataclass(frozen=True)
class ClaimEvidenceLinkDefinition:
    link_id: str
    claim_id: str
    evidence_id: str
    relationship: EvidenceRelationship | str
    reasoning: str
    is_critical_dependency: bool = False
    weight: float = 1.0
    metadata_json: Optional[str] = None


# =============================================================================
# PERSISTED RECORDS
# =============================================================================

@dataclass(frozen=True)
class EvidenceRunRecord:
    run_id: str
    source_text_id: Optional[str]
    tokenization_id: Optional[str]
    morphology_run_id: Optional[str]
    syntax_run_id: Optional[str]
    semantic_run_id: Optional[str]
    referential_run_id: Optional[str]
    discourse_run_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    evidence_count: int
    claim_count: int
    link_count: int
    is_exact_reproducible: bool
    created_at: str
    is_immutable: bool
    metadata_json: Optional[str]


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    run_id: Optional[str]
    pericope_id: str
    passage_id: str
    token_id: Optional[str]
    evidence_class: EvidenceClass
    epistemic_tier: ClaimTier
    epistemic_type: Optional[EpistemicType]
    source_reference: str
    extracted_text_or_data: str
    status: str
    confidence: ConfidenceLevel
    confidence_score: Optional[float]
    is_counter_evidence: bool
    is_ai_generated: bool
    is_translation_derived: bool
    is_contradicted: bool
    provenance_id: Optional[str]
    version_id: Optional[str]
    created_at: str
    provenance_hash: str
    is_immutable: bool
    metadata_json: Optional[str]


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    run_id: Optional[str]
    pericope_id: str
    passage_id: Optional[str]
    claim_tier: ClaimTier
    epistemic_type: EpistemicType
    claim_text: str
    claimed_by: str
    epistemic_status: str
    confidence_score: float
    calculated_confidence: float
    is_unresolved_contradiction: bool
    has_counter_evidence: bool
    doctrinal_system: Optional[str]
    is_theology_independent: bool
    provenance_id: Optional[str]
    version_id: Optional[str]
    created_at: str
    is_immutable: bool
    metadata_json: Optional[str]


@dataclass(frozen=True)
class ClaimEvidenceLinkRecord:
    link_id: str
    run_id: Optional[str]
    claim_id: str
    evidence_id: str
    relationship: EvidenceRelationship
    is_critical_dependency: bool
    weight: float
    reasoning: str
    created_at: str
    is_immutable: bool
    metadata_json: Optional[str]


@dataclass(frozen=True)
class EvidenceClaimConfig:
    analyzer_id: str = "POLYA-EVIDENCE-CLAIM-FOUNDATION"
    analyzer_version: str = "2.0.0"
    enforce_weakest_link: bool = True
    reject_unsupported_claims: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceClaimResult:
    run: EvidenceRunRecord
    evidence_records: List[EvidenceRecord]
    claim_records: List[ClaimRecord]
    link_records: List[ClaimEvidenceLinkRecord]


# =============================================================================
# HASHING HELPERS
# =============================================================================

def compute_evidence_claim_output_hash(
    evidence_records: Sequence[EvidenceRecord],
    claim_records: Sequence[ClaimRecord],
    link_records: Sequence[ClaimEvidenceLinkRecord],
) -> str:
    """Compute a deterministic SHA-256 digest over all records."""
    hasher = hashlib.sha256()

    sorted_ev = sorted(evidence_records, key=lambda e: e.evidence_id)
    for ev in sorted_ev:
        chunk = (
            f"EV:{ev.evidence_id}:{ev.evidence_class.value}:{ev.epistemic_tier.value}:"
            f"{ev.source_reference}:{ev.extracted_text_or_data}:{ev.status}:"
            f"{ev.confidence.value}:{ev.is_counter_evidence}:{ev.is_ai_generated}:"
            f"{ev.is_translation_derived}:{ev.provenance_hash}"
        )
        hasher.update(chunk.encode("utf-8"))

    sorted_cl = sorted(claim_records, key=lambda c: c.claim_id)
    for cl in sorted_cl:
        chunk = (
            f"CL:{cl.claim_id}:{cl.claim_tier.value}:{cl.epistemic_type.value}:"
            f"{cl.claim_text}:{cl.claimed_by}:{cl.epistemic_status}:"
            f"{cl.confidence_score:.4f}:{cl.calculated_confidence:.4f}:"
            f"{cl.is_unresolved_contradiction}:{cl.has_counter_evidence}"
        )
        hasher.update(chunk.encode("utf-8"))

    sorted_lk = sorted(link_records, key=lambda l: l.link_id)
    for lk in sorted_lk:
        chunk = (
            f"LK:{lk.link_id}:{lk.claim_id}:{lk.evidence_id}:{lk.relationship.value}:"
            f"{lk.is_critical_dependency}:{lk.weight:.4f}:{lk.reasoning}"
        )
        hasher.update(chunk.encode("utf-8"))

    return hasher.hexdigest().lower()


# =============================================================================
# EVIDENCE & CLAIM MANAGER
# =============================================================================

class EvidenceClaimManager:
    """Core manager for evidence ledger, claim catalog, and relationship links."""

    def __init__(self, engine: DatabaseEngine):
        self.engine = engine
        self.provenance_tracker = ProvenanceTracker(engine)
        self.version_manager = VersionManager(engine)

    def _validate_source_text(self, conn, source_text_id: Optional[str]) -> None:
        if source_text_id is None:
            return
        row = conn.execute(
            "SELECT source_text_id FROM source_texts WHERE source_text_id = ?;",
            (source_text_id,),
        ).fetchone()
        if not row:
            raise SourceTextNotFoundError(f"Source text '{source_text_id}' not found.")

    def _validate_foreign_anchors(
        self,
        conn,
        evidence_defs: Sequence[EvidenceDefinition],
        claim_defs: Sequence[ClaimDefinition],
    ) -> None:
        """Verify pericope_id, passage_id, and token_id references exist in the database."""
        for ev in evidence_defs:
            p_row = conn.execute(
                "SELECT pericope_id FROM pericopes WHERE pericope_id = ?;",
                (ev.pericope_id,),
            ).fetchone()
            if not p_row:
                raise EvidenceClaimOrphanError(
                    f"Evidence '{ev.evidence_id}' references nonexistent pericope '{ev.pericope_id}'."
                )

            pas_row = conn.execute(
                "SELECT passage_id FROM passages WHERE passage_id = ?;",
                (ev.passage_id,),
            ).fetchone()
            if not pas_row:
                raise EvidenceClaimOrphanError(
                    f"Evidence '{ev.evidence_id}' references nonexistent passage '{ev.passage_id}'."
                )

            if ev.token_id:
                t_row = conn.execute(
                    "SELECT token_id FROM tokens WHERE token_id = ?;",
                    (ev.token_id,),
                ).fetchone()
                if not t_row:
                    raise EvidenceClaimOrphanError(
                        f"Evidence '{ev.evidence_id}' references nonexistent token '{ev.token_id}'."
                    )

        for cl in claim_defs:
            p_row = conn.execute(
                "SELECT pericope_id FROM pericopes WHERE pericope_id = ?;",
                (cl.pericope_id,),
            ).fetchone()
            if not p_row:
                raise EvidenceClaimOrphanError(
                    f"Claim '{cl.claim_id}' references nonexistent pericope '{cl.pericope_id}'."
                )
            if cl.passage_id:
                pas_row = conn.execute(
                    "SELECT passage_id FROM passages WHERE passage_id = ?;",
                    (cl.passage_id,),
                ).fetchone()
                if not pas_row:
                    raise EvidenceClaimOrphanError(
                        f"Claim '{cl.claim_id}' references nonexistent passage '{cl.passage_id}'."
                    )

    def _enforce_epistemic_firewalls(
        self,
        evidence_map: Dict[str, EvidenceDefinition],
        claim_map: Dict[str, ClaimDefinition],
        link_defs: Sequence[ClaimEvidenceLinkDefinition],
        config: EvidenceClaimConfig,
    ) -> None:
        """Enforce strict epistemic firewalls and validation rules."""

        # 1. Evidence-level firewalls
        for ev in evidence_map.values():
            ev_class = coerce_evidence_class(ev.evidence_class)
            ev_tier = coerce_claim_tier(ev.epistemic_tier)
            if ev.epistemic_type:
                coerce_epistemic_type(ev.epistemic_type)
            coerce_confidence_level(ev.confidence)

            if ev.confidence_score is not None:
                if not (0.0 <= ev.confidence_score <= 1.0):
                    raise EvidenceConfidenceError(
                        f"Confidence score {ev.confidence_score} must be between 0.0 and 1.0."
                    )

            # Translation output cannot become E0 DIRECT_TEXT
            if ev.is_translation_derived and ev_class == EvidenceClass.E0_DIRECT_TEXT:
                raise TranslationToE0FirewallError(
                    f"Evidence '{ev.evidence_id}' is translation-derived and CANNOT become E0 DIRECT_TEXT."
                )

            # AI output is never automatically primary evidence (E0-E1)
            if ev.is_ai_generated and ev_class in (
                EvidenceClass.E0_DIRECT_TEXT,
                EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            ):
                raise AIPrimaryEvidenceFirewallError(
                    f"Evidence '{ev.evidence_id}' is AI-generated and cannot be primary evidence ({ev_class.value})."
                )

            # Confidence score cannot upgrade E-level
            # E0 requires direct text; E1 requires manuscript. High confidence on interpretation does not make it E0.
            if ev.confidence_score is not None and ev.confidence_score >= 0.95:
                if ev_class in (EvidenceClass.E0_DIRECT_TEXT, EvidenceClass.E1_TEXTUAL_MANUSCRIPT):
                    if ev.is_translation_derived or ev.is_ai_generated:
                        raise ConfidenceUpgradeFirewallError(
                            f"Confidence score cannot upgrade evidence '{ev.evidence_id}' to primary evidence."
                        )

        # 2. Claim-level firewalls
        for cl in claim_map.values():
            cl_tier = coerce_claim_tier(cl.claim_tier)
            cl_type = coerce_epistemic_type(cl.epistemic_type)

            if not (0.0 <= cl.confidence_score <= 1.0):
                raise EvidenceConfidenceError(
                    f"Claim confidence score {cl.confidence_score} must be between 0.0 and 1.0."
                )

            # Unresolved contradiction firewall
            if cl.is_unresolved_contradiction and cl.epistemic_status in (
                EpistemicStatus.VERIFIED_FACT,
                "VERIFIED_FACT",
                "ESTABLISHED",
            ):
                raise UnresolvedContradictionFirewallError(
                    f"Claim '{cl.claim_id}' has an unresolved contradiction and must not be marked established/VERIFIED_FACT."
                )

            # Confidence score cannot upgrade claim tier or establish theology as verified fact
            if cl_tier in (ClaimTier.T3_INTERPRETIVE_CLAIM, ClaimTier.T4_THEOLOGICAL_CLAIM):
                if cl.epistemic_status in (EpistemicStatus.VERIFIED_FACT, "VERIFIED_FACT"):
                    raise ConfidenceUpgradeFirewallError(
                        f"Confidence score cannot upgrade claim '{cl.claim_id}' ({cl_tier.value}) to VERIFIED_FACT."
                    )

            if cl_type == EpistemicType.THEOLOGICAL_CLAIM and cl.epistemic_status in (
                EpistemicStatus.VERIFIED_FACT,
                "VERIFIED_FACT",
            ):
                raise ConfidenceUpgradeFirewallError(
                    f"Confidence score cannot establish theological claim '{cl.claim_id}' as VERIFIED_FACT."
                )

        # 3. Relationship-level firewalls & propagation
        claims_supporting_evs: Dict[str, List[EvidenceDefinition]] = {c: [] for c in claim_map}
        claims_counter_evs: Dict[str, List[EvidenceDefinition]] = {c: [] for c in claim_map}
        claims_critical_evs: Dict[str, List[EvidenceDefinition]] = {c: [] for c in claim_map}

        for lk in link_defs:
            if lk.claim_id not in claim_map:
                raise ClaimNotFoundError(f"Link '{lk.link_id}' references unknown claim '{lk.claim_id}'.")
            if lk.evidence_id not in evidence_map:
                raise EvidenceNotFoundError(f"Link '{lk.link_id}' references unknown evidence '{lk.evidence_id}'.")

            rel = coerce_evidence_relationship(lk.relationship)
            ev = evidence_map[lk.evidence_id]

            if rel == EvidenceRelationship.SUPPORT:
                claims_supporting_evs[lk.claim_id].append(ev)
            elif rel == EvidenceRelationship.CONTRADICT:
                claims_counter_evs[lk.claim_id].append(ev)

            # Check critical dependency across all relationship types
            if lk.is_critical_dependency:
                claims_critical_evs[lk.claim_id].append(ev)

        for cl_id, cl in claim_map.items():
            supp_evs = claims_supporting_evs[cl_id]
            counter_evs = claims_counter_evs[cl_id]
            critical_evs = claims_critical_evs[cl_id]

            # Mark counter evidence presence across all linked evidence (CONTRADICT relation or is_counter_evidence)
            all_linked_for_claim = [
                evidence_map[l.evidence_id]
                for l in link_defs
                if l.claim_id == cl_id and l.evidence_id in evidence_map
            ]
            if counter_evs or any(e.is_counter_evidence for e in all_linked_for_claim):
                cl.has_counter_evidence = True

            # If contradictory evidence exists and is marked unresolved, reject VERIFIED_FACT
            if (counter_evs or cl.is_unresolved_contradiction) and cl.epistemic_status in (
                EpistemicStatus.VERIFIED_FACT,
                "VERIFIED_FACT",
            ):
                raise UnresolvedContradictionFirewallError(
                    f"Claim '{cl_id}' contains contradictory evidence and cannot be marked VERIFIED_FACT."
                )

            # Unsupported claim check
            if config.reject_unsupported_claims:
                if len(supp_evs) == 0 and cl.epistemic_status in (
                    EpistemicStatus.VERIFIED_FACT,
                    EpistemicStatus.STRONG_INFERENCE,
                    "VERIFIED_FACT",
                    "STRONG_INFERENCE",
                ):
                    raise UnsupportedClaimError(
                        f"Claim '{cl_id}' has zero supporting evidence and cannot be marked established/VERIFIED_FACT."
                    )

            # Lower-tier direct creation firewalls
            if supp_evs:
                classes_present = {coerce_evidence_class(e.evidence_class) for e in supp_evs}
                cl_tier = coerce_claim_tier(cl.claim_tier)
                cl_type = coerce_epistemic_type(cl.epistemic_type)

                is_t3_or_t4 = cl_tier in (
                    ClaimTier.T3_INTERPRETIVE_CLAIM,
                    ClaimTier.T4_THEOLOGICAL_CLAIM,
                ) or cl_type in (
                    EpistemicType.INTERPRETATION,
                    EpistemicType.THEOLOGICAL_CLAIM,
                )

                # Morphology cannot directly create T3/T4
                if classes_present == {EvidenceClass.E2_MORPHOLOGY} and is_t3_or_t4:
                    raise MorphologyTheologyFirewallError(
                        f"Claim '{cl_id}' is a T3/T4 claim derived from morphology alone. "
                        "Morphology cannot directly create interpretive or theological claims."
                    )

                # Syntax cannot directly create T3/T4
                if classes_present == {EvidenceClass.E3_SYNTAX} and is_t3_or_t4:
                    raise SyntaxTheologyFirewallError(
                        f"Claim '{cl_id}' is a T3/T4 claim derived from syntax alone. "
                        "Syntax cannot directly create interpretive or theological claims."
                    )

                # Semantic sense cannot directly create T3/T4
                if classes_present == {EvidenceClass.E4_LEXICAL} and is_t3_or_t4:
                    raise SemanticTheologyFirewallError(
                        f"Claim '{cl_id}' is a T3/T4 claim derived from semantic sense alone. "
                        "Semantic sense cannot directly create interpretive or theological claims."
                    )

                # Discourse relation cannot directly create T3/T4
                if classes_present == {EvidenceClass.E5_DISCOURSE} and is_t3_or_t4:
                    raise DiscourseTheologyFirewallError(
                        f"Claim '{cl_id}' is a T3/T4 claim derived from discourse relations alone. "
                        "Discourse cannot directly create interpretive or theological claims."
                    )

            # Entity association cannot directly create STRICT_IDENTITY
            lowered_text = cl.claim_text.lower()
            if "strict_identity" in lowered_text or "ontological identity" in lowered_text or "strict identity" in lowered_text:
                has_explicit_direct_evidence = False
                for ev in supp_evs:
                    ev_cls = coerce_evidence_class(ev.evidence_class)
                    if ev_cls in (EvidenceClass.E0_DIRECT_TEXT, EvidenceClass.E1_TEXTUAL_MANUSCRIPT):
                        has_explicit_direct_evidence = True
                        break
                if not has_explicit_direct_evidence:
                    raise IdentityFirewallError(
                        f"Claim '{cl_id}' asserts strict identity without explicit direct primary textual evidence. "
                        "Entity association cannot directly create STRICT_IDENTITY."
                    )

            # Confidence score cannot establish historical fact without primary evidence
            if cl.epistemic_type == EpistemicType.HISTORICAL_FACT:
                has_hist_text = any(
                    coerce_evidence_class(e.evidence_class)
                    in (
                        EvidenceClass.E0_DIRECT_TEXT,
                        EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
                        EvidenceClass.E9_HISTORICAL_LINGUISTIC,
                    )
                    for e in supp_evs
                )
                if not has_hist_text:
                    raise ConfidenceUpgradeFirewallError(
                        f"Claim '{cl_id}' asserts HISTORICAL_FACT without primary textual/historical evidence."
                    )

            # Weakest-critical-dependency confidence propagation:
            # final confidence must not exceed the weakest critical evidence dependency.
            if config.enforce_weakest_link and critical_evs:
                crit_scores = []
                for ev in critical_evs:
                    if ev.confidence_score is not None:
                        crit_scores.append(ev.confidence_score)
                    else:
                        lvl = coerce_confidence_level(ev.confidence)
                        crit_scores.append(confidence_level_to_numeric(lvl))
                weakest_crit = min(crit_scores)
                cl.calculated_confidence = min(cl.confidence_score, weakest_crit)
            else:
                cl.calculated_confidence = cl.confidence_score

    def record_evidence_and_claims(
        self,
        source_text_id: Optional[str],
        evidence_defs: Sequence[EvidenceDefinition],
        claim_defs: Sequence[ClaimDefinition],
        link_defs: Sequence[ClaimEvidenceLinkDefinition],
        config: Optional[EvidenceClaimConfig] = None,
        run_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
        version_id: Optional[str] = None,
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        referential_run_id: Optional[str] = None,
        discourse_run_id: Optional[str] = None,
        created_at: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> EvidenceClaimResult:
        """Atomically validate and record evidence, claims, and links."""
        cfg = config or EvidenceClaimConfig()
        timestamp = created_at or datetime.now(timezone.utc).isoformat()

        # Deduplication checks on inputs
        evidence_ids = set()
        for ev in evidence_defs:
            if ev.evidence_id in evidence_ids:
                raise DuplicateEvidenceError(f"Duplicate evidence_id '{ev.evidence_id}' in input.")
            evidence_ids.add(ev.evidence_id)

        claim_ids = set()
        for cl in claim_defs:
            if cl.claim_id in claim_ids:
                raise DuplicateClaimError(f"Duplicate claim_id '{cl.claim_id}' in input.")
            claim_ids.add(cl.claim_id)

        link_ids = set()
        link_pairs = set()
        for lk in link_defs:
            if lk.link_id in link_ids:
                raise DuplicateClaimEvidenceLinkError(f"Duplicate link_id '{lk.link_id}' in input.")
            pair = (lk.claim_id, lk.evidence_id)
            if pair in link_pairs:
                raise DuplicateClaimEvidenceLinkError(
                    f"Duplicate claim-evidence pair ({lk.claim_id}, {lk.evidence_id}) in input."
                )
            link_ids.add(lk.link_id)
            link_pairs.add(pair)

        evidence_map = {ev.evidence_id: ev for ev in evidence_defs}
        claim_map = {cl.claim_id: cl for cl in claim_defs}

        # Epistemic firewall verification
        self._enforce_epistemic_firewalls(evidence_map, claim_map, link_defs, cfg)

        # Atomic transaction execution
        with self.engine.transaction() as conn:
            # 1. Foreign anchor validations
            self._validate_source_text(conn, source_text_id)
            self._validate_foreign_anchors(conn, evidence_defs, claim_defs)

            actual_run_id = run_id or f"EVRUN-{int(datetime.now(timezone.utc).timestamp()*1000)}"

            # 2. Provenance and versioning resolution
            if provenance_id is None:
                p_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=actual_run_id,
                    content=f"EVIDENCE_CLAIM:{actual_run_id}",
                    input_data={"source_text_id": source_text_id or "NONE"},
                    agent_id=cfg.analyzer_id,
                    agent_version=cfg.analyzer_version,
                    config=cfg.metadata,
                    conn=conn,
                )
                actual_provenance_id = p_rec.provenance_id
            else:
                prov_row = conn.execute(
                    "SELECT provenance_id FROM provenance_records WHERE provenance_id = ?;",
                    (provenance_id,),
                ).fetchone()
                if not prov_row:
                    raise EvidenceClaimInvalidProvenanceError(
                        f"Provenance record '{provenance_id}' not found."
                    )
                actual_provenance_id = provenance_id

            if version_id is None:
                v_rec = self.version_manager.create_version(
                    object_type="EVIDENCE_RUN",
                    object_id=actual_run_id,
                    content=f"EVIDENCE_RUN:{actual_run_id}",
                    version_number=1,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    parent_version_id=None,
                    provenance_id=actual_provenance_id,
                    created_by=cfg.analyzer_id,
                    conn=conn,
                )
                actual_version_id = v_rec.version_id
            else:
                ver_row = conn.execute(
                    "SELECT version_id FROM object_versions WHERE version_id = ?;",
                    (version_id,),
                ).fetchone()
                if not ver_row:
                    raise EvidenceClaimInvalidVersionError(
                        f"Object version '{version_id}' not found."
                    )
                actual_version_id = version_id

            # Ensure run does not exist
            existing_run = conn.execute(
                "SELECT run_id FROM evidence_runs WHERE run_id = ?;",
                (actual_run_id,),
            ).fetchone()
            if existing_run:
                raise DuplicateEvidenceError(f"Evidence run '{actual_run_id}' already exists.")

            # 3. Build Record representations
            ev_records: List[EvidenceRecord] = []
            for ev in evidence_defs:
                ev_class = coerce_evidence_class(ev.evidence_class)
                ev_tier = coerce_claim_tier(ev.epistemic_tier)
                ep_type = coerce_epistemic_type(ev.epistemic_type) if ev.epistemic_type else None
                conf_lvl = coerce_confidence_level(ev.confidence)
                stat = ev.status.value if isinstance(ev.status, EvidenceStatus) else str(ev.status)

                # Provenance hash for individual evidence
                prov_hasher = hashlib.sha256()
                prov_hasher.update(
                    f"{ev.evidence_id}:{ev.pericope_id}:{ev.passage_id}:{ev.source_reference}:{ev.extracted_text_or_data}".encode(
                        "utf-8"
                    )
                )
                prov_hash = prov_hasher.hexdigest().lower()

                ev_records.append(
                    EvidenceRecord(
                        evidence_id=ev.evidence_id,
                        run_id=actual_run_id,
                        pericope_id=ev.pericope_id,
                        passage_id=ev.passage_id,
                        token_id=ev.token_id,
                        evidence_class=ev_class,
                        epistemic_tier=ev_tier,
                        epistemic_type=ep_type,
                        source_reference=ev.source_reference,
                        extracted_text_or_data=ev.extracted_text_or_data,
                        status=stat,
                        confidence=conf_lvl,
                        confidence_score=ev.confidence_score,
                        is_counter_evidence=ev.is_counter_evidence,
                        is_ai_generated=ev.is_ai_generated,
                        is_translation_derived=ev.is_translation_derived,
                        is_contradicted=ev.is_contradicted,
                        provenance_id=ev.provenance_id or actual_provenance_id,
                        version_id=ev.version_id or actual_version_id,
                        created_at=timestamp,
                        provenance_hash=prov_hash,
                        is_immutable=True,
                        metadata_json=ev.metadata_json,
                    )
                )

            cl_records: List[ClaimRecord] = []
            for cl in claim_defs:
                cl_tier = coerce_claim_tier(cl.claim_tier)
                cl_type = coerce_epistemic_type(cl.epistemic_type)
                ep_stat = (
                    cl.epistemic_status.value
                    if isinstance(cl.epistemic_status, EpistemicStatus)
                    else str(cl.epistemic_status)
                )

                cl_records.append(
                    ClaimRecord(
                        claim_id=cl.claim_id,
                        run_id=actual_run_id,
                        pericope_id=cl.pericope_id,
                        passage_id=cl.passage_id,
                        claim_tier=cl_tier,
                        epistemic_type=cl_type,
                        claim_text=cl.claim_text,
                        claimed_by=cl.claimed_by,
                        epistemic_status=ep_stat,
                        confidence_score=cl.confidence_score,
                        calculated_confidence=cl.calculated_confidence,
                        is_unresolved_contradiction=cl.is_unresolved_contradiction,
                        has_counter_evidence=cl.has_counter_evidence,
                        doctrinal_system=cl.doctrinal_system,
                        is_theology_independent=cl.is_theology_independent,
                        provenance_id=cl.provenance_id or actual_provenance_id,
                        version_id=cl.version_id or actual_version_id,
                        created_at=timestamp,
                        is_immutable=True,
                        metadata_json=cl.metadata_json,
                    )
                )

            lk_records: List[ClaimEvidenceLinkRecord] = []
            for lk in link_defs:
                rel = coerce_evidence_relationship(lk.relationship)
                lk_records.append(
                    ClaimEvidenceLinkRecord(
                        link_id=lk.link_id,
                        run_id=actual_run_id,
                        claim_id=lk.claim_id,
                        evidence_id=lk.evidence_id,
                        relationship=rel,
                        is_critical_dependency=lk.is_critical_dependency,
                        weight=lk.weight,
                        reasoning=lk.reasoning,
                        created_at=timestamp,
                        is_immutable=True,
                        metadata_json=lk.metadata_json,
                    )
                )

            # 4. Deterministic hashes
            config_hash = hashlib.sha256(
                json.dumps(
                    {
                        "analyzer_id": cfg.analyzer_id,
                        "analyzer_version": cfg.analyzer_version,
                        "enforce_weakest_link": cfg.enforce_weakest_link,
                        "reject_unsupported_claims": cfg.reject_unsupported_claims,
                        "metadata": cfg.metadata,
                    },
                    sort_keys=True,
                ).encode("utf-8")
            ).hexdigest().lower()

            input_hash = hashlib.sha256(
                f"{source_text_id}:{len(evidence_defs)}:{len(claim_defs)}:{len(link_defs)}".encode(
                    "utf-8"
                )
            ).hexdigest().lower()

            output_hash = compute_evidence_claim_output_hash(ev_records, cl_records, lk_records)

            run_record = EvidenceRunRecord(
                run_id=actual_run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id,
                morphology_run_id=morphology_run_id,
                syntax_run_id=syntax_run_id,
                semantic_run_id=semantic_run_id,
                referential_run_id=referential_run_id,
                discourse_run_id=discourse_run_id,
                version_id=actual_version_id,
                provenance_id=actual_provenance_id,
                analyzer_id=cfg.analyzer_id,
                analyzer_version=cfg.analyzer_version,
                configuration_hash=config_hash,
                input_content_hash=input_hash,
                output_hash=output_hash,
                evidence_count=len(ev_records),
                claim_count=len(cl_records),
                link_count=len(lk_records),
                is_exact_reproducible=True,
                created_at=timestamp,
                is_immutable=True,
                metadata_json=metadata_json,
            )

            # 5. Insert execution run
            conn.execute(
                """
                INSERT INTO evidence_runs (
                    run_id, source_text_id, tokenization_id, morphology_run_id,
                    syntax_run_id, semantic_run_id, referential_run_id, discourse_run_id,
                    version_id, provenance_id, analyzer_id, analyzer_version,
                    configuration_hash, input_content_hash, output_hash,
                    evidence_count, claim_count, link_count, is_exact_reproducible,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    run_record.run_id,
                    run_record.source_text_id,
                    run_record.tokenization_id,
                    run_record.morphology_run_id,
                    run_record.syntax_run_id,
                    run_record.semantic_run_id,
                    run_record.referential_run_id,
                    run_record.discourse_run_id,
                    run_record.version_id,
                    run_record.provenance_id,
                    run_record.analyzer_id,
                    run_record.analyzer_version,
                    run_record.configuration_hash,
                    run_record.input_content_hash,
                    run_record.output_hash,
                    run_record.evidence_count,
                    run_record.claim_count,
                    run_record.link_count,
                    1 if run_record.is_exact_reproducible else 0,
                    run_record.created_at,
                    1 if run_record.is_immutable else 0,
                    run_record.metadata_json,
                ),
            )

            # 6. Insert evidence ledger items
            for ev in ev_records:
                conn.execute(
                    """
                    INSERT INTO evidence_ledger (
                        evidence_id, run_id, pericope_id, passage_id, token_id,
                        evidence_class, epistemic_tier, epistemic_type, source_reference,
                        extracted_text_or_data, status, confidence, confidence_score,
                        is_counter_evidence, is_ai_generated, is_translation_derived,
                        is_contradicted, provenance_id, version_id, created_at,
                        provenance_hash, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        ev.evidence_id,
                        ev.run_id,
                        ev.pericope_id,
                        ev.passage_id,
                        ev.token_id,
                        ev.evidence_class.value,
                        ev.epistemic_tier.value,
                        ev.epistemic_type.value if ev.epistemic_type else None,
                        ev.source_reference,
                        ev.extracted_text_or_data,
                        ev.status,
                        ev.confidence.value,
                        ev.confidence_score,
                        1 if ev.is_counter_evidence else 0,
                        1 if ev.is_ai_generated else 0,
                        1 if ev.is_translation_derived else 0,
                        1 if ev.is_contradicted else 0,
                        ev.provenance_id,
                        ev.version_id,
                        ev.created_at,
                        ev.provenance_hash,
                        1 if ev.is_immutable else 0,
                        ev.metadata_json,
                    ),
                )

            # 7. Insert claims
            for cl in cl_records:
                conn.execute(
                    """
                    INSERT INTO claims (
                        claim_id, run_id, pericope_id, passage_id, claim_tier,
                        epistemic_type, claim_text, claimed_by, epistemic_status,
                        confidence_score, calculated_confidence, is_unresolved_contradiction,
                        has_counter_evidence, doctrinal_system, is_theology_independent,
                        provenance_id, version_id, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        cl.claim_id,
                        cl.run_id,
                        cl.pericope_id,
                        cl.passage_id,
                        cl.claim_tier.value,
                        cl.epistemic_type.value,
                        cl.claim_text,
                        cl.claimed_by,
                        cl.epistemic_status,
                        cl.confidence_score,
                        cl.calculated_confidence,
                        1 if cl.is_unresolved_contradiction else 0,
                        1 if cl.has_counter_evidence else 0,
                        cl.doctrinal_system,
                        1 if cl.is_theology_independent else 0,
                        cl.provenance_id,
                        cl.version_id,
                        cl.created_at,
                        1 if cl.is_immutable else 0,
                        cl.metadata_json,
                    ),
                )

            # 8. Insert links
            for lk in lk_records:
                conn.execute(
                    """
                    INSERT INTO claim_evidence_links (
                        link_id, run_id, claim_id, evidence_id, relationship,
                        is_critical_dependency, weight, reasoning, created_at,
                        is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        lk.link_id,
                        lk.run_id,
                        lk.claim_id,
                        lk.evidence_id,
                        lk.relationship.value,
                        1 if lk.is_critical_dependency else 0,
                        lk.weight,
                        lk.reasoning,
                        lk.created_at,
                        1 if lk.is_immutable else 0,
                        lk.metadata_json,
                    ),
                )

        return EvidenceClaimResult(
            run=run_record,
            evidence_records=ev_records,
            claim_records=cl_records,
            link_records=lk_records,
        )

    def get_evidence(self, evidence_id: str) -> EvidenceRecord:
        """Fetch an evidence record by ID."""
        with self.engine.connect() as conn:
            row = conn.execute(
                """
                SELECT evidence_id, run_id, pericope_id, passage_id, token_id,
                       evidence_class, epistemic_tier, epistemic_type, source_reference,
                       extracted_text_or_data, status, confidence, confidence_score,
                       is_counter_evidence, is_ai_generated, is_translation_derived,
                       is_contradicted, provenance_id, version_id, created_at,
                       provenance_hash, is_immutable, metadata_json
                FROM evidence_ledger
                WHERE evidence_id = ?;
                """,
                (evidence_id,),
            ).fetchone()
            if not row:
                raise EvidenceNotFoundError(f"Evidence '{evidence_id}' not found.")
            return EvidenceRecord(
                evidence_id=row["evidence_id"],
                run_id=row["run_id"],
                pericope_id=row["pericope_id"],
                passage_id=row["passage_id"],
                token_id=row["token_id"],
                evidence_class=coerce_evidence_class(row["evidence_class"]),
                epistemic_tier=coerce_claim_tier(row["epistemic_tier"]),
                epistemic_type=coerce_epistemic_type(row["epistemic_type"]) if row["epistemic_type"] else None,
                source_reference=row["source_reference"],
                extracted_text_or_data=row["extracted_text_or_data"],
                status=row["status"],
                confidence=coerce_confidence_level(row["confidence"]),
                confidence_score=row["confidence_score"],
                is_counter_evidence=bool(row["is_counter_evidence"]),
                is_ai_generated=bool(row["is_ai_generated"]),
                is_translation_derived=bool(row["is_translation_derived"]),
                is_contradicted=bool(row["is_contradicted"]),
                provenance_id=row["provenance_id"],
                version_id=row["version_id"],
                created_at=row["created_at"],
                provenance_hash=row["provenance_hash"],
                is_immutable=bool(row["is_immutable"]),
                metadata_json=row["metadata_json"],
            )

    def get_claim(self, claim_id: str) -> ClaimRecord:
        """Fetch a claim record by ID."""
        with self.engine.connect() as conn:
            row = conn.execute(
                """
                SELECT claim_id, run_id, pericope_id, passage_id, claim_tier,
                       epistemic_type, claim_text, claimed_by, epistemic_status,
                       confidence_score, calculated_confidence, is_unresolved_contradiction,
                       has_counter_evidence, doctrinal_system, is_theology_independent,
                       provenance_id, version_id, created_at, is_immutable, metadata_json
                FROM claims
                WHERE claim_id = ?;
                """,
                (claim_id,),
            ).fetchone()
            if not row:
                raise ClaimNotFoundError(f"Claim '{claim_id}' not found.")
            return ClaimRecord(
                claim_id=row["claim_id"],
                run_id=row["run_id"],
                pericope_id=row["pericope_id"],
                passage_id=row["passage_id"],
                claim_tier=coerce_claim_tier(row["claim_tier"]),
                epistemic_type=coerce_epistemic_type(row["epistemic_type"]),
                claim_text=row["claim_text"],
                claimed_by=row["claimed_by"],
                epistemic_status=row["epistemic_status"],
                confidence_score=row["confidence_score"],
                calculated_confidence=row["calculated_confidence"],
                is_unresolved_contradiction=bool(row["is_unresolved_contradiction"]),
                has_counter_evidence=bool(row["has_counter_evidence"]),
                doctrinal_system=row["doctrinal_system"],
                is_theology_independent=bool(row["is_theology_independent"]),
                provenance_id=row["provenance_id"],
                version_id=row["version_id"],
                created_at=row["created_at"],
                is_immutable=bool(row["is_immutable"]),
                metadata_json=row["metadata_json"],
            )

    def get_evidence_for_claim(self, claim_id: str) -> List[Tuple[ClaimEvidenceLinkRecord, EvidenceRecord]]:
        """Fetch all evidence linked to a claim along with link records."""
        with self.engine.connect() as conn:
            rows = conn.execute(
                """
                SELECT lk.link_id, lk.run_id AS lk_run_id, lk.claim_id, lk.evidence_id,
                       lk.relationship, lk.is_critical_dependency, lk.weight, lk.reasoning,
                       lk.created_at AS lk_created_at, lk.is_immutable AS lk_is_immutable,
                       lk.metadata_json AS lk_metadata_json,
                       ev.evidence_id AS ev_evidence_id, ev.run_id AS ev_run_id,
                       ev.pericope_id, ev.passage_id, ev.token_id, ev.evidence_class,
                       ev.epistemic_tier, ev.epistemic_type, ev.source_reference,
                       ev.extracted_text_or_data, ev.status, ev.confidence, ev.confidence_score,
                       ev.is_counter_evidence, ev.is_ai_generated, ev.is_translation_derived,
                       ev.is_contradicted, ev.provenance_id, ev.version_id, ev.created_at AS ev_created_at,
                       ev.provenance_hash, ev.is_immutable AS ev_is_immutable, ev.metadata_json AS ev_metadata_json
                FROM claim_evidence_links lk
                JOIN evidence_ledger ev ON lk.evidence_id = ev.evidence_id
                WHERE lk.claim_id = ?
                ORDER BY lk.link_id ASC;
                """,
                (claim_id,),
            ).fetchall()

            result = []
            for r in rows:
                lk_rec = ClaimEvidenceLinkRecord(
                    link_id=r["link_id"],
                    run_id=r["lk_run_id"],
                    claim_id=r["claim_id"],
                    evidence_id=r["evidence_id"],
                    relationship=coerce_evidence_relationship(r["relationship"]),
                    is_critical_dependency=bool(r["is_critical_dependency"]),
                    weight=r["weight"],
                    reasoning=r["reasoning"],
                    created_at=r["lk_created_at"],
                    is_immutable=bool(r["lk_is_immutable"]),
                    metadata_json=r["lk_metadata_json"],
                )
                ev_rec = EvidenceRecord(
                    evidence_id=r["ev_evidence_id"],
                    run_id=r["ev_run_id"],
                    pericope_id=r["pericope_id"],
                    passage_id=r["passage_id"],
                    token_id=r["token_id"],
                    evidence_class=coerce_evidence_class(r["evidence_class"]),
                    epistemic_tier=coerce_claim_tier(r["epistemic_tier"]),
                    epistemic_type=coerce_epistemic_type(r["epistemic_type"]) if r["epistemic_type"] else None,
                    source_reference=r["source_reference"],
                    extracted_text_or_data=r["extracted_text_or_data"],
                    status=r["status"],
                    confidence=coerce_confidence_level(r["confidence"]),
                    confidence_score=r["confidence_score"],
                    is_counter_evidence=bool(r["is_counter_evidence"]),
                    is_ai_generated=bool(r["is_ai_generated"]),
                    is_translation_derived=bool(r["is_translation_derived"]),
                    is_contradicted=bool(r["is_contradicted"]),
                    provenance_id=r["provenance_id"],
                    version_id=r["version_id"],
                    created_at=r["ev_created_at"],
                    provenance_hash=r["provenance_hash"],
                    is_immutable=bool(r["ev_is_immutable"]),
                    metadata_json=r["ev_metadata_json"],
                )
                result.append((lk_rec, ev_rec))
            return result

    def get_counter_evidence_for_claim(self, claim_id: str) -> List[Tuple[ClaimEvidenceLinkRecord, EvidenceRecord]]:
        """Fetch all counter-evidence linked to a claim (CONTRADICT or is_counter_evidence)."""
        all_links = self.get_evidence_for_claim(claim_id)
        return [
            (lk, ev)
            for (lk, ev) in all_links
            if lk.relationship == EvidenceRelationship.CONTRADICT or ev.is_counter_evidence
        ]

    def get_claims_for_pericope(self, pericope_id: str) -> List[ClaimRecord]:
        """Fetch all claims associated with a given pericope."""
        with self.engine.connect() as conn:
            rows = conn.execute(
                """
                SELECT claim_id, run_id, pericope_id, passage_id, claim_tier,
                       epistemic_type, claim_text, claimed_by, epistemic_status,
                       confidence_score, calculated_confidence, is_unresolved_contradiction,
                       has_counter_evidence, doctrinal_system, is_theology_independent,
                       provenance_id, version_id, created_at, is_immutable, metadata_json
                FROM claims
                WHERE pericope_id = ?
                ORDER BY claim_id ASC;
                """,
                (pericope_id,),
            ).fetchall()
            return [
                ClaimRecord(
                    claim_id=r["claim_id"],
                    run_id=r["run_id"],
                    pericope_id=r["pericope_id"],
                    passage_id=r["passage_id"],
                    claim_tier=coerce_claim_tier(r["claim_tier"]),
                    epistemic_type=coerce_epistemic_type(r["epistemic_type"]),
                    claim_text=r["claim_text"],
                    claimed_by=r["claimed_by"],
                    epistemic_status=r["epistemic_status"],
                    confidence_score=r["confidence_score"],
                    calculated_confidence=r["calculated_confidence"],
                    is_unresolved_contradiction=bool(r["is_unresolved_contradiction"]),
                    has_counter_evidence=bool(r["has_counter_evidence"]),
                    doctrinal_system=r["doctrinal_system"],
                    is_theology_independent=bool(r["is_theology_independent"]),
                    provenance_id=r["provenance_id"],
                    version_id=r["version_id"],
                    created_at=r["created_at"],
                    is_immutable=bool(r["is_immutable"]),
                    metadata_json=r["metadata_json"],
                )
                for r in rows
            ]

    def reanalyze(
        self,
        previous_run_id: str,
        evidence_defs: Sequence[EvidenceDefinition],
        claim_defs: Sequence[ClaimDefinition],
        link_defs: Sequence[ClaimEvidenceLinkDefinition],
        config: Optional[EvidenceClaimConfig] = None,
        change_reason: ChangeReason = ChangeReason.REANALYSIS,
    ) -> EvidenceClaimResult:
        """Supersede a previous evidence run with updated records while preserving audit history."""
        with self.engine.connect() as conn:
            prev_row = conn.execute(
                "SELECT * FROM evidence_runs WHERE run_id = ?;",
                (previous_run_id,),
            ).fetchone()
            if not prev_row:
                raise EvidenceNotFoundError(f"Previous evidence run '{previous_run_id}' not found.")

        cfg = config or EvidenceClaimConfig()
        new_run_id = f"{previous_run_id}-v2"

        # Create new version chained to previous run's version
        new_version = self.version_manager.create_version(
            object_type="EVIDENCE_RUN",
            object_id=new_run_id,
            content=f"EVIDENCE_RUN:{new_run_id}",
            version_number=2,
            change_reason=change_reason,
            parent_version_id=prev_row["version_id"],
            created_by=cfg.analyzer_id,
        )

        return self.record_evidence_and_claims(
            source_text_id=prev_row["source_text_id"],
            evidence_defs=evidence_defs,
            claim_defs=claim_defs,
            link_defs=link_defs,
            config=cfg,
            run_id=new_run_id,
            version_id=new_version.version_id,
            tokenization_id=prev_row["tokenization_id"],
            morphology_run_id=prev_row["morphology_run_id"],
            syntax_run_id=prev_row["syntax_run_id"],
            semantic_run_id=prev_row["semantic_run_id"],
            referential_run_id=prev_row["referential_run_id"],
            discourse_run_id=prev_row["discourse_run_id"],
        )
