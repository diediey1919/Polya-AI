"""
Discourse & Context Foundation Subsystem for Polya Philological Bible Engine.
Task 2.7 — Architecture v2.0 — FROZEN.

Provides:
  - DISCOURSE UNITS:
      Clause-level discourse anchors (never a re-parse of syntax).
  - DISCOURSE SEGMENTS:
      Higher-level groupings above units (propositional, narrative, hortatory, ...).
  - DISCOURSE RELATIONS:
      Typed discourse links (ELABORATION, CONTRAST, RESULT, PURPOSE, ...) with an
      explicit justification basis and a required connector-token anchor whenever
      the relation claims a conjunction or grammatical marker. Discourse relations
      are NEVER derivable from morphology alone.
  - CONTEXT LAYERS:
      IMMEDIATE / PERICOPE / BOOK / CORPUS observations. Context layers carry
      observations, not evidence: `is_evidence` is pinned to 0 by schema CHECK.
  - DISCOURSE PARTICIPANTS:
      Speaker / addressee / narrator role inventory, optionally anchored to the
      entity catalog. Participant role NEVER asserts ontological or strict identity.
  - REFERENTIAL CONTINUITY CANDIDATES:
      Anaphoric / cataphoric / deictic candidate sets. Competing antecedents remain
      representable; resolution is never forced.
  - INFORMATION STRUCTURE:
      Topic / focus / prominence foundation with explicit marking device.
  - AMBIGUITY PRESERVATION:
      Unresolved ambiguity is a first-class immutable record with
      `preservation_required = 1` and `collapse_prohibited = 1`.
  - FIREWALLS:
      * Context Firewall: context is not automatically evidence.
      * Translation Firewall: discourse meaning is not derived from translation.
      * Morphology Firewall: discourse relations are not derived from morphology alone.
      * Syntax Firewall: clause / constituent anchors must belong to the same source text.
      * Theology Firewall: no doctrinal or theological assertion.
      * Identity Firewall: participants and antecedents never assert identity.
      * Frequency Firewall: contextual frequency never yields truth.
      * Language Firewall: discourse language must match the source text language.
  - IMMUTABILITY, PROVENANCE, & VERSIONING:
      Database triggers, ProvenanceTracker, and VersionManager integration.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DiscourseAmbiguityFirewallError,
    DiscourseConfidenceError,
    DiscourseContextFirewallError,
    DiscourseFrequencyFirewallError,
    DiscourseIdentityFirewallError,
    DiscourseInvalidProvenanceError,
    DiscourseInvalidVersionError,
    DiscourseLanguageMismatchError,
    DiscourseMorphologyFirewallError,
    DiscourseNotFoundError,
    DiscourseOrphanError,
    DiscourseRelationAnchorError,
    DiscourseSpanValidationError,
    DiscourseSubsystemError,
    DiscourseSyntaxFirewallError,
    DiscourseTheologyFirewallError,
    DiscourseTokenNotFoundError,
    DiscourseTranslationFirewallError,
    DuplicateDiscourseError,
    SourceTextNotFoundError,
)
from bible_engine.provenance import ProvenanceRecord, ProvenanceTracker, TargetType
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
)
from bible_engine.tokenization import TokenizationManager, TokenRecord
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)


# =============================================================================
# SHARED HELPERS
# =============================================================================

class EnumCodec:
    """Small enum/None coercion helpers shared by the row mappers."""

    @staticmethod
    def value(value: Any) -> Any:
        """Emit an enum member as its raw value; pass through everything else."""
        return value.value if isinstance(value, Enum) else value

    @staticmethod
    def enum(value: Any, enum_cls: Any, default: Any) -> Any:
        """Coerce a stored string into an enum member, falling back on default."""
        if value is None:
            return default
        try:
            return enum_cls(value)
        except ValueError:
            return default

    @staticmethod
    def opt_str(value: Any) -> Optional[str]:
        return str(value) if value else None


class DigestMixin:
    """Deterministic JSON digest used for configuration and payload hashes."""

    @staticmethod
    def digest_json(payload: Any) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


class FirewallScanner:
    """Rejects prohibited assertion patterns in free-text observations."""

    @staticmethod
    def assert_absent(
        lowered_text: str,
        patterns: Sequence[str],
        error_cls: Any,
        message: str,
    ) -> None:
        for pattern in patterns:
            if pattern in lowered_text:
                raise error_cls(message)


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMS
# =============================================================================

class DiscourseUnitType(str, Enum):
    """Controlled discourse unit inventory (schema CHECK domain)."""
    CLAUSE_UNIT = "CLAUSE_UNIT"
    SENTENCE_UNIT = "SENTENCE_UNIT"
    VERSE_UNIT = "VERSE_UNIT"
    UTTERANCE_UNIT = "UTTERANCE_UNIT"
    PARENTHETICAL_UNIT = "PARENTHETICAL_UNIT"
    QUOTATION_UNIT = "QUOTATION_UNIT"
    OTHER = "OTHER"


class DiscourseSegmentType(str, Enum):
    """Controlled discourse segment inventory (schema CHECK domain)."""
    PROPOSITIONAL = "PROPOSITIONAL"
    NARRATIVE = "NARRATIVE"
    DISCOURSE_UNIT = "DISCOURSE_UNIT"
    QUOTATION_FRAME = "QUOTATION_FRAME"
    CHAINTING = "CHAINTING"
    EPISTOLARY_FRAME = "EPISTOLARY_FRAME"
    HYMNIC = "HYMNIC"
    POLEMIC = "POLEMIC"
    EXHORTATIVE = "EXHORTATIVE"
    OTHER = "OTHER"


class DiscourseRelationType(str, Enum):
    """Controlled discourse relation inventory. Multiplicity of readings is preserved."""
    ELABORATION = "ELABORATION"
    CONTRAST = "CONTRAST"
    PARALLEL = "PARALLEL"
    RESULT = "RESULT"
    CAUSE = "CAUSE"
    PURPOSE = "PURPOSE"
    CONDITION = "CONDITION"
    CONCESSION = "CONCESSION"
    TEMPORAL_SEQUENCE = "TEMPORAL_SEQUENCE"
    GROUND = "GROUND"
    BACKGROUND = "BACKGROUND"
    MEANS = "MEANS"
    MANNER = "MANNER"
    SUMMARY = "SUMMARY"
    QUOTATION_FRAME = "QUOTATION_FRAME"
    BOUNDARY_UNRESOLVED = "BOUNDARY_UNRESOLVED"
    OTHER = "OTHER"


class RelationDirectionality(str, Enum):
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"
    SYMMETRIC = "SYMMETRIC"
    UNDIRECTED = "UNDIRECTED"


class JustificationBasis(str, Enum):
    """Observable basis for a discourse relation. Morphology alone is never sufficient."""
    EXPLICIT_CONJUNCTION = "EXPLICIT_CONJUNCTION"
    GRAMMATICAL_MARKER = "GRAMMATICAL_MARKER"
    LEXICAL_COHESION = "LEXICAL_COHESION"
    SYNTACTIC_STRUCTURE = "SYNTACTIC_STRUCTURE"
    INFORMATION_STRUCTURE = "INFORMATION_STRUCTURE"
    MULTIPLE_CONVERGING = "MULTIPLE_CONVERGING"
    UNSPECIFIED_OBSERVATION = "UNSPECIFIED_OBSERVATION"


class ContextLayerScope(str, Enum):
    """Immediate / pericope / book / corpus context scopes."""
    IMMEDIATE = "IMMEDIATE"
    PERICOPE = "PERICOPE"
    BOOK = "BOOK"
    CORPUS = "CORPUS"
    UNRESOLVED = "UNRESOLVED"


class ContextObservationKind(str, Enum):
    PARTICIPANT_CONTINUITY = "PARTICIPANT_CONTINUITY"
    TOPIC_CONTINUITY = "TOPIC_CONTINUITY"
    LEXICAL_REPETITION = "LEXICAL_REPETITION"
    SYNTACTIC_PATTERN = "SYNTACTIC_PATTERN"
    GENRE_FRAME = "GENRE_FRAME"
    QUOTATION_FRAME = "QUOTATION_FRAME"
    ARGUMENT_PROGRESSION = "ARGUMENT_PROGRESSION"
    BOUNDARY_OBSERVATION = "BOUNDARY_OBSERVATION"
    OTHER = "OTHER"


class ParticipantRole(str, Enum):
    SPEAKER = "SPEAKER"
    ADDRESSEE = "ADDRESSEE"
    THIRD_PARTY = "THIRD_PARTY"
    NARRATOR = "NARRATOR"
    AUTHORIAL_VOICE = "AUTHORIAL_VOICE"
    QUOTED_SPEAKER = "QUOTED_SPEAKER"
    COLLECTIVE_SPEAKER = "COLLECTIVE_SPEAKER"
    INDETERMINATE = "INDETERMINATE"
    OTHER = "OTHER"


class ParticipantRoleStatus(str, Enum):
    OBSERVED = "OBSERVED"
    DECLARED = "DECLARED"
    INFERRED = "INFERRED"
    CONTESTED = "CONTESTED"
    UNRESOLVED = "UNRESOLVED"


class GrammaticalPerson(str, Enum):
    FIRST = "FIRST"
    SECOND = "SECOND"
    THIRD = "THIRD"
    IMPERSONAL = "IMPERSONAL"
    UNSPECIFIED = "UNSPECIFIED"


class GrammaticalNumber(str, Enum):
    SINGULAR = "SINGULAR"
    DUAL = "DUAL"
    PLURAL = "PLURAL"
    UNSPECIFIED = "UNSPECIFIED"


class ContinuityType(str, Enum):
    """Anaphoric / cataphoric / deictic continuity taxonomy."""
    ANAPHORIC = "ANAPHORIC"
    CATAPHORIC = "CATAPHORIC"
    DEICTIC = "DEICTIC"
    EXOPHORIC = "EXOPHORIC"
    DISCOURSE_DEICTIC = "DISCOURSE_DEICTIC"
    UNRESOLVED = "UNRESOLVED"


class ContinuityResolutionStatus(str, Enum):
    CANDIDATE_SET = "CANDIDATE_SET"
    PREFERRED_CANDIDATE = "PREFERRED_CANDIDATE"
    UNRESOLVED_AMBIGUOUS = "UNRESOLVED_AMBIGUOUS"
    NO_CANDIDATE = "NO_CANDIDATE"
    CONTESTED = "CONTESTED"


class InformationRole(str, Enum):
    TOPIC = "TOPIC"
    FOCUS = "FOCUS"
    THEME = "THEME"
    RHEME = "RHEME"
    GIVEN = "GIVEN"
    NEW = "NEW"
    CONTRASTIVE_FOCUS = "CONTRASTIVE_FOCUS"
    TAIL = "TAIL"
    SETTING = "SETTING"
    UNMARKED = "UNMARKED"
    UNDETERMINED = "UNDETERMINED"


class Markedness(str, Enum):
    MARKED = "MARKED"
    UNMARKED = "UNMARKED"
    UNDETERMINED = "MARKEDNESS_UNDETERMINED"


class MarkingDevice(str, Enum):
    WORD_ORDER = "WORD_ORDER"
    PARTICLE = "PARTICLE"
    DETERMINER_USE = "DETERMINER_USE"
    PRONOMINAL_FORM = "PRONOMINAL_FORM"
    FRONTING = "FRONTING"
    POSTPOSITION = "POSTPOSITION"
    VERBAL_FORM = "VERBAL_FORM"
    MULTIPLE_DEVICES = "MULTIPLE_DEVICES"
    NONE_OBSERVED = "NONE_OBSERVED"


class DiscourseAmbiguityType(str, Enum):
    UNIT_BOUNDARY = "UNIT_BOUNDARY"
    SEGMENT_BOUNDARY = "SEGMENT_BOUNDARY"
    RELATION_TYPE = "RELATION_TYPE"
    RELATION_DIRECTION = "RELATION_DIRECTION"
    PARTICIPANT_ROLE = "PARTICIPANT_ROLE"
    ANAPHORIC_ANTECEDENT = "ANAPHORIC_ANTECEDENT"
    DEICTIC_ANCHOR = "DEICTIC_ANCHOR"
    INFORMATION_ROLE = "INFORMATION_ROLE"
    CONTEXT_LAYER_SCOPE = "CONTEXT_LAYER_SCOPE"
    OTHER = "OTHER"


class DiscourseAmbiguityResolution(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    RESOLVED = "RESOLVED"
    PERMANENTLY_UNDECIDABLE = "PERMANENTLY_UNDECIDABLE"


class DiscourseEvidenceStatus(str, Enum):
    """Epistemic status attached to a discourse observation."""
    EXPLICIT = "[EXPLICIT]"
    GRAMMATICALLY_ESTABLISHED = "[GRAMMATICALLY ESTABLISHED]"
    CONTEXTUALLY_STRONG = "[CONTEXTUALLY STRONG]"
    INFERRED = "[INFERRED]"
    PLAUSIBLE = "[PLAUSIBLE]"
    AMBIGUOUS = "[AMBIGUOUS]"
    UNSUPPORTED = "[UNSUPPORTED]"
    CONTRADICTED = "[CONTRADICTED]"


class DiscourseConfidence(str, Enum):
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"
    AMBIGUOUS = "AMBIGUOUS"


# Evidence statuses that may not be claimed by a context-layer observation.
CONTEXT_UNASSERTABLE_STATUSES = frozenset({
    DiscourseEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
})

# No discourse observation may be persisted while explicitly unsupported.
UNPERSISTABLE_EVIDENCE_STATUSES = frozenset({
    DiscourseEvidenceStatus.UNSUPPORTED,
})

# Prohibited theological / dogmatic assertions in discourse justification.
PROHIBITED_THEOLOGY_PATTERNS = (
    "proves the trinity",
    "proves trinity",
    "proves deity",
    "proves jesus is god",
    "proves jesus is divine",
    "refutes tauhid",
    "proves hypostatic union",
    "theological proof",
    "dogmatic truth",
    "doctrine requires",
)

# Prohibited modern target-language substitution markers.
PROHIBITED_TRANSLATION_PATTERNS = (
    "dynamic translation",
    "dynamic equivalence",
    "natural language rendering",
    "according to the translation",
    "translation therefore means",
)

# Prohibited identity assertions from discourse roles or antecedents.
PROHIBITED_IDENTITY_PATTERNS = (
    "ontologically identical to",
    "is strictly identical to god",
    "strict identity with divine essence",
    "consubstantial with the father",
    "same person as",
)

# Prohibited derivation of meaning or truth from contextual frequency.
PROHIBITED_FREQUENCY_PATTERNS = (
    "frequently therefore true",
    "majority of occurrences proves",
    "most common usage therefore",
    "frequency proves",
    "statistically therefore true",
)

# Prohibited derivation of a discourse relation from morphology alone.
PROHIBITED_MORPHOLOGY_PATTERNS = (
    "morphology alone",
    "case ending therefore",
    "gender proves",
    "the ending establishes the relation",
    "solely from the form",
)


# =============================================================================
# DATA DEFINITIONS & RECORDS
# =============================================================================

@dataclass(frozen=True)
class DiscourseUnitDefinition:
    """Input definition of a discourse unit anchored to a token span."""
    unit_id: str
    start_token_id: str
    end_token_id: str
    unit_type: DiscourseUnitType = DiscourseUnitType.CLAUSE_UNIT
    unit_order: int = 0
    clause_id: Optional[str] = None
    passage_id: Optional[str] = None
    parent_unit_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = False
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    raw_unit_surface: str = ""
    observation_note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DiscourseUnitRecord:
    """Immutable persistent discourse unit."""
    unit_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    start_token_id: str
    end_token_id: str
    unit_type: DiscourseUnitType
    unit_order: int
    clause_id: Optional[str] = None
    passage_id: Optional[str] = None
    parent_unit_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = False
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    raw_unit_surface: str = ""
    observation_note: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(self, ("unit_type", "confidence_level", "evidence_status", "language"))


@dataclass(frozen=True)
class DiscourseSegmentDefinition:
    """Input definition of a discourse segment spanning units and/or tokens."""
    segment_id: str
    start_token_id: str
    end_token_id: str
    segment_type: DiscourseSegmentType = DiscourseSegmentType.NARRATIVE
    segment_order: int = 0
    start_unit_id: Optional[str] = None
    end_unit_id: Optional[str] = None
    pericope_id: Optional[str] = None
    passage_id: Optional[str] = None
    parent_segment_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = False
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    raw_segment_surface: str = ""
    observation_note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DiscourseSegmentRecord:
    """Immutable persistent discourse segment."""
    segment_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    start_token_id: str
    end_token_id: str
    segment_type: DiscourseSegmentType
    segment_order: int
    start_unit_id: Optional[str] = None
    end_unit_id: Optional[str] = None
    pericope_id: Optional[str] = None
    passage_id: Optional[str] = None
    parent_segment_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = False
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    language: Optional[SourceTextLanguage] = None
    raw_segment_surface: str = ""
    observation_note: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(self, ("segment_type", "confidence_level", "evidence_status", "language"))


@dataclass(frozen=True)
class DiscourseRelationDefinition:
    """Input definition of a typed discourse relation between units or segments."""
    relation_id: str
    source_ref_id: str
    target_ref_id: str
    relation_type: DiscourseRelationType
    grammatical_justification: str
    source_kind: str = "UNIT"
    target_kind: str = "UNIT"
    directionality: RelationDirectionality = RelationDirectionality.FORWARD
    justification_basis: JustificationBasis = JustificationBasis.UNSPECIFIED_OBSERVATION
    connector_token_id: Optional[str] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    syntax_clause_span_cited: bool = False
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    is_ambiguity_flagged: bool = False
    observation_note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DiscourseRelationRecord:
    """Immutable persistent discourse relation."""
    relation_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    source_kind: str
    source_ref_id: str
    target_kind: str
    target_ref_id: str
    relation_type: DiscourseRelationType
    directionality: RelationDirectionality
    grammatical_justification: str
    justification_basis: JustificationBasis
    evidence_status: DiscourseEvidenceStatus
    connector_token_id: Optional[str] = None
    evidence_id: Optional[str] = None
    syntax_clause_span_cited: bool = False
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    is_ambiguity_flagged: bool = False
    observation_note: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            (
                "relation_type",
                "directionality",
                "justification_basis",
                "evidence_status",
                "confidence_level",
            ),
        )


@dataclass(frozen=True)
class ContextLayerDefinition:
    """Input definition of a contextual observation at a declared scope."""
    context_layer_id: str
    layer_scope: ContextLayerScope
    observation_kind: ContextObservationKind
    observation: str
    anchor_unit_id: Optional[str] = None
    anchor_segment_id: Optional[str] = None
    anchor_passage_id: Optional[str] = None
    anchor_pericope_id: Optional[str] = None
    anchor_book_id: Optional[str] = None
    span_start_passage_id: Optional[str] = None
    span_end_passage_id: Optional[str] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ContextLayerRecord:
    """Immutable persistent context-layer observation. Never evidence by itself."""
    context_layer_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    layer_scope: ContextLayerScope
    observation_kind: ContextObservationKind
    observation: str
    evidence_status: DiscourseEvidenceStatus
    is_evidence: bool = False
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    anchor_unit_id: Optional[str] = None
    anchor_segment_id: Optional[str] = None
    anchor_passage_id: Optional[str] = None
    anchor_pericope_id: Optional[str] = None
    anchor_book_id: Optional[str] = None
    span_start_passage_id: Optional[str] = None
    span_end_passage_id: Optional[str] = None
    evidence_id: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            ("layer_scope", "observation_kind", "evidence_status", "confidence_level"),
        )


@dataclass(frozen=True)
class ParticipantDefinition:
    """Input definition of a discourse participant role."""
    participant_id: str
    participant_role: ParticipantRole
    role_status: ParticipantRoleStatus = ParticipantRoleStatus.OBSERVED
    unit_id: Optional[str] = None
    segment_id: Optional[str] = None
    passage_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_mention_id: Optional[str] = None
    grammatical_person: Optional[GrammaticalPerson] = None
    grammatical_number: Optional[GrammaticalNumber] = None
    anchor_token_id: Optional[str] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ParticipantRecord:
    """Immutable persistent discourse participant. Identity is never asserted."""
    participant_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    participant_role: ParticipantRole
    role_status: ParticipantRoleStatus
    evidence_status: DiscourseEvidenceStatus
    unit_id: Optional[str] = None
    segment_id: Optional[str] = None
    passage_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_mention_id: Optional[str] = None
    grammatical_person: Optional[GrammaticalPerson] = None
    grammatical_number: Optional[GrammaticalNumber] = None
    anchor_token_id: Optional[str] = None
    evidence_id: Optional[str] = None
    identity_asserted: bool = False
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            ("participant_role", "role_status", "evidence_status", "confidence_level"),
        )


@dataclass(frozen=True)
class ContinuityCandidateDefinition:
    """
    Input definition of one antecedent candidate for an anaphoric/cataphoric/deictic
    referring token. Multiple candidates for the same token remain representable.
    """
    candidate_id: str
    referring_token_id: str
    continuity_type: ContinuityType
    resolution_status: ContinuityResolutionStatus = ContinuityResolutionStatus.CANDIDATE_SET
    candidate_rank: int = 1
    is_resolved: bool = False
    referring_mention_id: Optional[str] = None
    unit_id: Optional[str] = None
    passage_id: Optional[str] = None
    candidate_antecedent_token_id: Optional[str] = None
    candidate_antecedent_entity_id: Optional[str] = None
    candidate_antecedent_unit_id: Optional[str] = None
    antecedent_distance_tokens: Optional[int] = None
    resolution_rationale: Optional[str] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ContinuityCandidateRecord:
    """Immutable persistent continuity candidate. Antecedent identity is never asserted."""
    candidate_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    referring_token_id: str
    continuity_type: ContinuityType
    resolution_status: ContinuityResolutionStatus
    candidate_rank: int
    is_resolved: bool
    evidence_status: DiscourseEvidenceStatus
    referring_mention_id: Optional[str] = None
    unit_id: Optional[str] = None
    passage_id: Optional[str] = None
    candidate_antecedent_token_id: Optional[str] = None
    candidate_antecedent_entity_id: Optional[str] = None
    candidate_antecedent_unit_id: Optional[str] = None
    antecedent_distance_tokens: Optional[int] = None
    resolution_rationale: Optional[str] = None
    evidence_id: Optional[str] = None
    identity_asserted: bool = False
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            ("continuity_type", "resolution_status", "evidence_status", "confidence_level"),
        )


@dataclass(frozen=True)
class InformationStructureDefinition:
    """Input definition of an information-structure observation."""
    info_structure_id: str
    unit_id: str
    information_role: InformationRole
    markedness: Markedness = Markedness.UNDETERMINED
    marking_device: MarkingDevice = MarkingDevice.NONE_OBSERVED
    token_id: Optional[str] = None
    passage_id: Optional[str] = None
    constituent_id: Optional[str] = None
    syntax_clause_id: Optional[str] = None
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED
    evidence_id: Optional[str] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    confidence_score: Optional[float] = None
    observation_note: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class InformationStructureRecord:
    """Immutable persistent information-structure observation."""
    info_structure_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    unit_id: str
    information_role: InformationRole
    markedness: Markedness
    marking_device: MarkingDevice
    evidence_status: DiscourseEvidenceStatus
    token_id: Optional[str] = None
    passage_id: Optional[str] = None
    constituent_id: Optional[str] = None
    syntax_clause_id: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: DiscourseConfidence = DiscourseConfidence.PROVISIONAL
    observation_note: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            ("information_role", "markedness", "marking_device", "evidence_status", "confidence_level"),
        )


@dataclass(frozen=True)
class DiscourseAmbiguityDefinition:
    """Input definition of an unresolved discourse ambiguity."""
    ambiguity_id: str
    ambiguity_type: DiscourseAmbiguityType
    subject_ref_id: str
    description: str
    competing_interpretations: Sequence[str] = ()
    resolution_status: DiscourseAmbiguityResolution = DiscourseAmbiguityResolution.UNRESOLVED
    evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.AMBIGUOUS
    evidence_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DiscourseAmbiguityRecord:
    """Immutable persistent ambiguity record. Collapse is prohibited."""
    ambiguity_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    ambiguity_type: DiscourseAmbiguityType
    subject_ref_id: str
    description: str
    competing_interpretations_json: str
    competing_interpretation_count: int
    resolution_status: DiscourseAmbiguityResolution
    evidence_status: DiscourseEvidenceStatus
    preservation_required: bool = True
    collapse_prohibited: bool = True
    evidence_id: Optional[str] = None
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(
            self,
            ("ambiguity_type", "resolution_status", "evidence_status"),
            extra={"competing_interpretations_json": self.competing_interpretations_json},
        )


@dataclass(frozen=True)
class DiscourseAnalyzerConfig:
    """Configuration governing discourse & context analysis."""
    analyzer_id: str = "polya-discourse-engine"
    analyzer_version: str = "2.0.0"
    representation_type: RepresentationType = RepresentationType.RAW
    is_deterministic: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "representation_type": self.representation_type.value,
            "is_deterministic": self.is_deterministic,
            "parameters": self.parameters,
        }

    def compute_hash(self) -> str:
        return DigestMixin.digest_json(self.to_dict())


@dataclass(frozen=True)
class DiscourseRunRecord:
    """Immutable ledger record for a discourse analysis run."""
    run_id: str
    source_text_id: Optional[str]
    tokenization_id: Optional[str]
    morphology_run_id: Optional[str]
    syntax_run_id: Optional[str]
    semantic_run_id: Optional[str]
    referential_run_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    language: SourceTextLanguage
    representation_type: RepresentationType
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    unit_count: int
    segment_count: int
    relation_count: int
    participant_count: int
    continuity_candidate_count: int
    information_structure_count: int
    ambiguity_count: int
    is_exact_reproducible: bool
    created_at: str
    is_immutable: bool
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _record_dict(self, ("language", "representation_type"))


@dataclass(frozen=True)
class DiscourseResult:
    """Complete discourse & context analysis package."""
    run: DiscourseRunRecord
    units: List[DiscourseUnitRecord]
    segments: List[DiscourseSegmentRecord]
    relations: List[DiscourseRelationRecord]
    context_layers: List[ContextLayerRecord]
    participants: List[ParticipantRecord]
    continuity_candidates: List[ContinuityCandidateRecord]
    information_structure: List[InformationStructureRecord]
    ambiguities: List[DiscourseAmbiguityRecord]
    version: ObjectVersion
    provenance: ProvenanceRecord


# =============================================================================
# RECORD / HASH HELPERS
# =============================================================================

def _record_dict(record: Any, enum_fields: Sequence[str], extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Serialize a frozen record, emitting enum fields by value."""
    out: Dict[str, Any] = {}
    for fname in record.__dataclass_fields__:
        value = getattr(record, fname)
        out[fname] = EnumCodec.value(value) if fname in enum_fields else value
    if extra:
        out.update(extra)
    return out


def compute_discourse_output_hash(
    units: Sequence[DiscourseUnitDefinition],
    segments: Sequence[DiscourseSegmentDefinition] = (),
    relations: Sequence[DiscourseRelationDefinition] = (),
    context_layers: Sequence[ContextLayerDefinition] = (),
    participants: Sequence[ParticipantDefinition] = (),
    continuity_candidates: Sequence[ContinuityCandidateDefinition] = (),
    information_structure: Sequence[InformationStructureDefinition] = (),
    ambiguities: Sequence[DiscourseAmbiguityDefinition] = (),
) -> str:
    """
    Compute a deterministic SHA-256 hash over the submitted discourse payload.

    Ordering is normalized so that submission order never changes the digest.
    """
    payload = {
        "units": sorted(
            (
                {
                    "unit_id": u.unit_id,
                    "unit_type": u.unit_type.value,
                    "unit_order": u.unit_order,
                    "parse_index": u.parse_index,
                    "start_token_id": u.start_token_id,
                    "end_token_id": u.end_token_id,
                    "clause_id": u.clause_id,
                    "evidence_status": u.evidence_status.value,
                    "confidence_level": u.confidence_level.value,
                    "raw_unit_surface": u.raw_unit_surface,
                }
                for u in units
            ),
            key=lambda x: (x["unit_order"], x["parse_index"], x["unit_id"]),
        ),
        "segments": sorted(
            (
                {
                    "segment_id": s.segment_id,
                    "segment_type": s.segment_type.value,
                    "segment_order": s.segment_order,
                    "parse_index": s.parse_index,
                    "start_token_id": s.start_token_id,
                    "end_token_id": s.end_token_id,
                    "evidence_status": s.evidence_status.value,
                    "confidence_level": s.confidence_level.value,
                }
                for s in segments
            ),
            key=lambda x: (x["segment_order"], x["parse_index"], x["segment_id"]),
        ),
        "relations": sorted(
            (
                {
                    "relation_id": r.relation_id,
                    "source_kind": r.source_kind,
                    "source_ref_id": r.source_ref_id,
                    "target_kind": r.target_kind,
                    "target_ref_id": r.target_ref_id,
                    "relation_type": r.relation_type.value,
                    "directionality": r.directionality.value,
                    "justification_basis": r.justification_basis.value,
                    "connector_token_id": r.connector_token_id,
                    "evidence_status": r.evidence_status.value,
                    "grammatical_justification": r.grammatical_justification,
                }
                for r in relations
            ),
            key=lambda x: x["relation_id"],
        ),
        "context_layers": sorted(
            (
                {
                    "context_layer_id": c.context_layer_id,
                    "layer_scope": c.layer_scope.value,
                    "observation_kind": c.observation_kind.value,
                    "observation": c.observation,
                    "evidence_status": c.evidence_status.value,
                }
                for c in context_layers
            ),
            key=lambda x: x["context_layer_id"],
        ),
        "participants": sorted(
            (
                {
                    "participant_id": p.participant_id,
                    "participant_role": p.participant_role.value,
                    "role_status": p.role_status.value,
                    "entity_id": p.entity_id,
                    "evidence_status": p.evidence_status.value,
                }
                for p in participants
            ),
            key=lambda x: x["participant_id"],
        ),
        "continuity_candidates": sorted(
            (
                {
                    "candidate_id": c.candidate_id,
                    "referring_token_id": c.referring_token_id,
                    "continuity_type": c.continuity_type.value,
                    "resolution_status": c.resolution_status.value,
                    "candidate_rank": c.candidate_rank,
                    "is_resolved": bool(c.is_resolved),
                    "candidate_antecedent_token_id": c.candidate_antecedent_token_id,
                    "candidate_antecedent_entity_id": c.candidate_antecedent_entity_id,
                    "candidate_antecedent_unit_id": c.candidate_antecedent_unit_id,
                    "evidence_status": c.evidence_status.value,
                }
                for c in continuity_candidates
            ),
            key=lambda x: (x["referring_token_id"], x["candidate_rank"], x["candidate_id"]),
        ),
        "information_structure": sorted(
            (
                {
                    "info_structure_id": i.info_structure_id,
                    "unit_id": i.unit_id,
                    "information_role": i.information_role.value,
                    "markedness": i.markedness.value,
                    "marking_device": i.marking_device.value,
                    "token_id": i.token_id,
                    "evidence_status": i.evidence_status.value,
                }
                for i in information_structure
            ),
            key=lambda x: x["info_structure_id"],
        ),
        "ambiguities": sorted(
            (
                {
                    "ambiguity_id": a.ambiguity_id,
                    "ambiguity_type": a.ambiguity_type.value,
                    "subject_ref_id": a.subject_ref_id,
                    "resolution_status": a.resolution_status.value,
                    "description": a.description,
                    "competing_interpretations": sorted(a.competing_interpretations),
                }
                for a in ambiguities
            ),
            key=lambda x: x["ambiguity_id"],
        ),
    }
    return DigestMixin.digest_json(payload)


# =============================================================================
# DISCOURSE MANAGER ENGINE
# =============================================================================

class DiscourseManager:
    """
    Core engine managing discourse units, segments, relations, context layers,
    participants, referential continuity candidates, information structure, and
    preserved ambiguities under strict context/evidence firewalls.
    """

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine
        self.provenance_tracker = ProvenanceTracker(engine)
        self.version_mgr = VersionManager(engine)
        self.source_text_mgr = SourceTextManager(engine)
        self.token_mgr = TokenizationManager(engine)

    # -------------------------------------------------------------------------
    # Read accessors
    # -------------------------------------------------------------------------

    def get_run(self, run_id: str) -> DiscourseRunRecord:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM discourse_runs WHERE run_id = ?;", (run_id,))
            row = cur.fetchone()
        if row is None:
            raise DiscourseNotFoundError(f"Discourse run '{run_id}' does not exist.")
        return _run_from_row(row)

    def get_units_for_run(self, run_id: str) -> List[DiscourseUnitRecord]:
        return self._list(
            "SELECT * FROM discourse_units WHERE run_id = ? ORDER BY unit_order ASC, parse_index ASC;",
            (run_id,),
            _unit_from_row,
        )

    def get_segments_for_run(self, run_id: str) -> List[DiscourseSegmentRecord]:
        return self._list(
            "SELECT * FROM discourse_segments WHERE run_id = ? ORDER BY segment_order ASC, parse_index ASC;",
            (run_id,),
            _segment_from_row,
        )

    def get_relations_for_run(self, run_id: str) -> List[DiscourseRelationRecord]:
        return self._list(
            "SELECT * FROM discourse_relations WHERE run_id = ? ORDER BY relation_id ASC;",
            (run_id,),
            _relation_from_row,
        )

    def get_context_layers_for_run(self, run_id: str) -> List[ContextLayerRecord]:
        return self._list(
            "SELECT * FROM discourse_context_layers WHERE run_id = ? ORDER BY context_layer_id ASC;",
            (run_id,),
            _context_from_row,
        )

    def get_participants_for_run(self, run_id: str) -> List[ParticipantRecord]:
        return self._list(
            "SELECT * FROM discourse_participants WHERE run_id = ? ORDER BY participant_id ASC;",
            (run_id,),
            _participant_from_row,
        )

    def get_continuity_candidates_for_token(self, token_id: str) -> List[ContinuityCandidateRecord]:
        return self._list(
            "SELECT * FROM referential_continuity_candidates WHERE referring_token_id = ? "
            "ORDER BY candidate_rank ASC;",
            (token_id,),
            _continuity_from_row,
        )

    def get_continuity_candidates_for_run(self, run_id: str) -> List[ContinuityCandidateRecord]:
        return self._list(
            "SELECT * FROM referential_continuity_candidates WHERE run_id = ? "
            "ORDER BY referring_token_id ASC, candidate_rank ASC;",
            (run_id,),
            _continuity_from_row,
        )

    def get_information_structure_for_run(self, run_id: str) -> List[InformationStructureRecord]:
        return self._list(
            "SELECT * FROM information_structure WHERE run_id = ? ORDER BY info_structure_id ASC;",
            (run_id,),
            _information_from_row,
        )

    def get_ambiguities_for_run(self, run_id: str) -> List[DiscourseAmbiguityRecord]:
        return self._list(
            "SELECT * FROM discourse_ambiguities WHERE run_id = ? ORDER BY ambiguity_id ASC;",
            (run_id,),
            _ambiguity_from_row,
        )

    def _list(self, sql: str, params: Tuple[Any, ...], mapper: Any) -> List[Any]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
        return [mapper(r) for r in rows]

    # -------------------------------------------------------------------------
    # Firewall enforcement
    # -------------------------------------------------------------------------

    @staticmethod
    def _enforce_text_firewalls(resource: str, label: str, *texts: Optional[str]) -> None:
        """Reject theological, translation, identity, frequency, and morphology-only assertions."""
        for text in texts:
            if not text:
                continue
            lowered = text.lower()
            FirewallScanner.assert_absent(
                lowered,
                PROHIBITED_THEOLOGY_PATTERNS,
                DiscourseTheologyFirewallError,
                f"{resource} '{label}' asserts a theological or doctrinal claim: {text!r}",
            )
            FirewallScanner.assert_absent(
                lowered,
                PROHIBITED_TRANSLATION_PATTERNS,
                DiscourseTranslationFirewallError,
                f"{resource} '{label}' derives discourse meaning from a translation: {text!r}",
            )
            FirewallScanner.assert_absent(
                lowered,
                PROHIBITED_IDENTITY_PATTERNS,
                DiscourseIdentityFirewallError,
                f"{resource} '{label}' asserts ontological or strict identity: {text!r}",
            )
            FirewallScanner.assert_absent(
                lowered,
                PROHIBITED_FREQUENCY_PATTERNS,
                DiscourseFrequencyFirewallError,
                f"{resource} '{label}' derives truth from contextual frequency: {text!r}",
            )
            FirewallScanner.assert_absent(
                lowered,
                PROHIBITED_MORPHOLOGY_PATTERNS,
                DiscourseMorphologyFirewallError,
                f"{resource} '{label}' derives a discourse observation from morphology alone: {text!r}",
            )

    def _enforce_relation_firewalls(
        self,
        relation: DiscourseRelationDefinition,
        context_layer_evidence_ids: set,
    ) -> None:
        """Discourse relations: no morphology-only derivation, no unsupported claims."""
        self._enforce_text_firewalls(
            "Discourse relation",
            relation.relation_id,
            relation.grammatical_justification,
            relation.observation_note,
        )

        if relation.evidence_status in UNPERSISTABLE_EVIDENCE_STATUSES:
            raise DiscourseSubsystemError(
                f"Discourse relation '{relation.relation_id}' cannot be persisted with "
                f"evidence status {relation.evidence_status.value}."
            )

        # Discourse relations are never derivable from morphology alone: a
        # conjunction/marker-based justification must cite the connector token.
        if relation.justification_basis in (
            JustificationBasis.EXPLICIT_CONJUNCTION,
            JustificationBasis.GRAMMATICAL_MARKER,
        ) and not relation.connector_token_id:
            raise DiscourseMorphologyFirewallError(
                f"Discourse relation '{relation.relation_id}' claims justification basis "
                f"'{relation.justification_basis.value}' without citing a connector token. "
                "A discourse relation is not derivable from morphology alone."
            )

        if relation.source_ref_id == relation.target_ref_id and relation.source_kind == relation.target_kind:
            raise DiscourseSubsystemError(
                f"Discourse relation '{relation.relation_id}' cannot relate a unit or segment to itself."
            )

    def _enforce_context_firewall(self, layer: ContextLayerDefinition) -> None:
        """CONTEXT IS NOT AUTOMATICALLY EVIDENCE."""
        self._enforce_text_firewalls("Context layer observation", layer.context_layer_id, layer.observation)

        if layer.evidence_status in CONTEXT_UNASSERTABLE_STATUSES:
            raise DiscourseContextFirewallError(
                f"Context layer '{layer.context_layer_id}' claims evidence status "
                f"'{layer.evidence_status.value}'. Context is not automatically evidence: "
                "a context observation must remain an observation."
            )

        if layer.evidence_status in (DiscourseEvidenceStatus.EXPLICIT,) and not layer.evidence_id:
            raise DiscourseContextFirewallError(
                f"Context layer '{layer.context_layer_id}' claims '[EXPLICIT]' status without an "
                "evidence_ledger anchor. Context is not automatically evidence."
            )

    def _enforce_continuity_firewalls(self, candidate: ContinuityCandidateDefinition) -> None:
        self._enforce_text_firewalls(
            "Referential continuity candidate",
            candidate.candidate_id,
            candidate.resolution_rationale,
        )

        if candidate.is_resolved:
            if not any(
                (
                    candidate.candidate_antecedent_token_id,
                    candidate.candidate_antecedent_entity_id,
                    candidate.candidate_antecedent_unit_id,
                )
            ):
                raise DiscourseOrphanError(
                    f"Continuity candidate '{candidate.candidate_id}' is marked resolved but "
                    "cites no antecedent anchor."
                )
        elif candidate.resolution_status == ContinuityResolutionStatus.UNRESOLVED_AMBIGUOUS:
            # Ambiguity must remain representable: no collapse is permitted.
            pass

    def _enforce_ambiguity_firewalls(self, ambiguity: DiscourseAmbiguityDefinition) -> None:
        self._enforce_text_firewalls("Discourse ambiguity", ambiguity.ambiguity_id, ambiguity.description)

        if len(list(ambiguity.competing_interpretations)) == 0:
            raise DiscourseAmbiguityFirewallError(
                f"Discourse ambiguity '{ambiguity.ambiguity_id}' states no competing interpretation. "
                "Unresolved ambiguity must remain representable."
            )

        if (
            ambiguity.resolution_status
            in (DiscourseAmbiguityResolution.RESOLVED, DiscourseAmbiguityResolution.PARTIALLY_RESOLVED)
            and not ambiguity.evidence_id
        ):
            raise DiscourseAmbiguityFirewallError(
                f"Discourse ambiguity '{ambiguity.ambiguity_id}' claims resolution "
                f"'{ambiguity.resolution_status.value}' without an evidence_ledger anchor."
            )

    # -------------------------------------------------------------------------
    # Record discourse analysis
    # -------------------------------------------------------------------------

    def record_discourse_analysis(
        self,
        source_text_id: Optional[str],
        units: Sequence[DiscourseUnitDefinition],
        segments: Sequence[DiscourseSegmentDefinition] = (),
        relations: Sequence[DiscourseRelationDefinition] = (),
        context_layers: Sequence[ContextLayerDefinition] = (),
        participants: Sequence[ParticipantDefinition] = (),
        continuity_candidates: Sequence[ContinuityCandidateDefinition] = (),
        information_structure: Sequence[InformationStructureDefinition] = (),
        ambiguities: Sequence[DiscourseAmbiguityDefinition] = (),
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        referential_run_id: Optional[str] = None,
        config: Optional[DiscourseAnalyzerConfig] = None,
        agent: str = "polya-discourse-engine",
        conn: Optional[sqlite3.Connection] = None,
    ) -> DiscourseResult:
        """
        Record a complete discourse & context analysis in one atomic run.

        Enforces:
          - Token existence, span ordering, and language firewall
          - Upstream run firewall (syntax / semantics / referential belong to same source text)
          - Clause / constituent anchor firewall
          - Context-is-not-evidence firewall
          - Morphology-only derivation firewall
          - Theology / translation / identity / frequency firewalls
          - Ambiguity preservation firewall
        """
        config = config or DiscourseAnalyzerConfig()
        config_hash = config.compute_hash()
        now_iso = datetime.now(timezone.utc).isoformat()

        if not units and not segments and not context_layers:
            raise DiscourseSubsystemError(
                "At least one discourse unit, segment, or context layer must be provided."
            )

        if not source_text_id:
            raise DiscourseOrphanError(
                "Discourse analysis requires a source_text_id: every discourse artifact is "
                "anchored to a source text."
            )

        # Step 1: Resolve source text, language, and tokens
        source_lang = SourceTextLanguage.OTHER
        token_by_id: Dict[str, TokenRecord] = {}
        tok_id_in_run: Optional[str] = None

        if source_text_id:
            try:
                st_rec = self.source_text_mgr.get_source_text(source_text_id)
            except Exception as exc:
                raise SourceTextNotFoundError(
                    f"Discourse analysis cannot anchor to source text '{source_text_id}': {exc}"
                ) from exc
            raw_lang = st_rec.language
            if hasattr(raw_lang, "value"):
                raw_lang = raw_lang.value
            try:
                source_lang = SourceTextLanguage(raw_lang)
            except ValueError:
                source_lang = SourceTextLanguage.OTHER

            raw_tokens = self.token_mgr.get_tokens_for_source_text(
                source_text_id,
                representation_type=config.representation_type,
                conn=conn,
            )
            token_by_id = {t.token_id: t for t in raw_tokens}
            if raw_tokens:
                tok_id_in_run = raw_tokens[0].tokenization_id

        # Step 2: Validate upstream run firewalls
        def _validate_upstream(c: sqlite3.Connection) -> None:
            chk = c.cursor()
            for run_col, table, label in (
                ("morphology_run_id", "morphology_runs", "morphology"),
                ("syntax_run_id", "syntax_runs", "syntax"),
                ("semantic_run_id", "semantic_runs", "semantic"),
                ("referential_run_id", "referential_runs", "referential"),
            ):
                run_id = {
                    "morphology_run_id": morphology_run_id,
                    "syntax_run_id": syntax_run_id,
                    "semantic_run_id": semantic_run_id,
                    "referential_run_id": referential_run_id,
                }[run_col]
                if not run_id:
                    continue
                chk.execute(f"SELECT source_text_id FROM {table} WHERE run_id = ?;", (run_id,))
                row = chk.fetchone()
                if row is None:
                    raise DiscourseNotFoundError(
                        f"Referenced {label} run '{run_id}' does not exist."
                    )
                if source_text_id and row[0] != source_text_id:
                    raise DiscourseSyntaxFirewallError(
                        f"{label.capitalize()} run '{run_id}' belongs to text '{row[0]}', "
                        f"not '{source_text_id}'."
                    )

        if conn is not None:
            _validate_upstream(conn)
        else:
            with self.engine.connect() as chk_c:
                _validate_upstream(chk_c)

        # Step 3: Validate unit spans and collect anchors
        seen_unit_ids: set = set()
        resolved_units: List[DiscourseUnitDefinition] = []
        for u in units:
            if u.unit_id in seen_unit_ids:
                raise DuplicateDiscourseError(f"Duplicate unit_id '{u.unit_id}' in submission.")
            seen_unit_ids.add(u.unit_id)
            self._enforce_text_firewalls(
                "Discourse unit", u.unit_id, u.observation_note, u.raw_unit_surface
            )
            if u.evidence_status in UNPERSISTABLE_EVIDENCE_STATUSES:
                raise DiscourseSubsystemError(
                    f"Discourse unit '{u.unit_id}' cannot be persisted with evidence status "
                    f"{u.evidence_status.value}."
                )
            if source_text_id:
                self._validate_span_against_tokens(
                    token_by_id, u.unit_id, "Discourse unit", u.start_token_id, u.end_token_id
                )
            resolved_units.append(u)

        unit_ids_in_run = {u.unit_id for u in resolved_units}

        # Step 4: Validate segment spans and unit anchors
        seen_segment_ids: set = set()
        resolved_segments: List[DiscourseSegmentDefinition] = []
        for s in segments:
            if s.segment_id in seen_segment_ids:
                raise DuplicateDiscourseError(f"Duplicate segment_id '{s.segment_id}' in submission.")
            seen_segment_ids.add(s.segment_id)
            self._enforce_text_firewalls(
                "Discourse segment", s.segment_id, s.observation_note, s.raw_segment_surface
            )
            if s.evidence_status in UNPERSISTABLE_EVIDENCE_STATUSES:
                raise DiscourseSubsystemError(
                    f"Discourse segment '{s.segment_id}' cannot be persisted with evidence status "
                    f"{s.evidence_status.value}."
                )
            if source_text_id:
                self._validate_span_against_tokens(
                    token_by_id, s.segment_id, "Discourse segment", s.start_token_id, s.end_token_id
                )
            for boundary_unit_id in (s.start_unit_id, s.end_unit_id):
                if boundary_unit_id and boundary_unit_id not in unit_ids_in_run:
                    raise DiscourseOrphanError(
                        f"Discourse segment '{s.segment_id}' references unit '{boundary_unit_id}' "
                        "absent from this run."
                    )
            resolved_segments.append(s)

        segment_ids_in_run = {s.segment_id for s in resolved_segments}

        # Step 5: Validate relations (anchor existence, firewalls)
        seen_relation_ids: set = set()
        for r in relations:
            if r.relation_id in seen_relation_ids:
                raise DuplicateDiscourseError(f"Duplicate relation_id '{r.relation_id}' in submission.")
            seen_relation_ids.add(r.relation_id)

            for kind, ref_id in ((r.source_kind, r.source_ref_id), (r.target_kind, r.target_ref_id)):
                if kind == "UNIT" and ref_id not in unit_ids_in_run:
                    raise DiscourseOrphanError(
                        f"Discourse relation '{r.relation_id}' references unit '{ref_id}' "
                        "absent from this run."
                    )
                if kind == "SEGMENT" and ref_id not in segment_ids_in_run:
                    raise DiscourseOrphanError(
                        f"Discourse relation '{r.relation_id}' references segment '{ref_id}' "
                        "absent from this run."
                    )
                if kind not in ("UNIT", "SEGMENT"):
                    raise DiscourseRelationAnchorError(
                        f"Discourse relation '{r.relation_id}' declares unsupported source/target "
                        f"kind '{kind}'."
                    )

            if r.connector_token_id and source_text_id and r.connector_token_id not in token_by_id:
                raise DiscourseTokenNotFoundError(
                    f"Discourse relation '{r.relation_id}' cites connector token "
                    f"'{r.connector_token_id}' absent from source text '{source_text_id}'."
                )

            self._enforce_relation_firewalls(r, set())

        # Step 6: Validate context layers (anchor existence + context firewall)
        seen_context_ids: set = set()
        for c in context_layers:
            if c.context_layer_id in seen_context_ids:
                raise DuplicateDiscourseError(
                    f"Duplicate context_layer_id '{c.context_layer_id}' in submission."
                )
            seen_context_ids.add(c.context_layer_id)
            self._enforce_context_firewall(c)
            if c.anchor_unit_id and c.anchor_unit_id not in unit_ids_in_run:
                raise DiscourseOrphanError(
                    f"Context layer '{c.context_layer_id}' references unit '{c.anchor_unit_id}' "
                    "absent from this run."
                )
            if c.anchor_segment_id and c.anchor_segment_id not in segment_ids_in_run:
                raise DiscourseOrphanError(
                    f"Context layer '{c.context_layer_id}' references segment '{c.anchor_segment_id}' "
                    "absent from this run."
                )
            if c.layer_scope == ContextLayerScope.UNRESOLVED and c.evidence_id:
                raise DiscourseContextFirewallError(
                    f"Context layer '{c.context_layer_id}' declares an unresolved scope while citing "
                    "evidence. Unresolved scope must not be converted into evidence."
                )

        # Step 7: Validate participants (entity language firewall, role anchors)
        seen_participant_ids: set = set()
        entity_languages: Dict[str, Optional[str]] = {}
        for p in participants:
            if p.participant_id in seen_participant_ids:
                raise DuplicateDiscourseError(
                    f"Duplicate participant_id '{p.participant_id}' in submission."
                )
            seen_participant_ids.add(p.participant_id)
            if p.unit_id and p.unit_id not in unit_ids_in_run:
                raise DiscourseOrphanError(
                    f"Participant '{p.participant_id}' references unit '{p.unit_id}' absent from this run."
                )
            if p.segment_id and p.segment_id not in segment_ids_in_run:
                raise DiscourseOrphanError(
                    f"Participant '{p.participant_id}' references segment '{p.segment_id}' "
                    "absent from this run."
                )
            if p.entity_id:
                entity_languages[p.entity_id] = None
            if p.anchor_token_id and source_text_id and p.anchor_token_id not in token_by_id:
                raise DiscourseTokenNotFoundError(
                    f"Participant '{p.participant_id}' cites anchor token '{p.anchor_token_id}' "
                    f"absent from source text '{source_text_id}'."
                )
            if p.evidence_status in UNPERSISTABLE_EVIDENCE_STATUSES:
                raise DiscourseSubsystemError(
                    f"Participant '{p.participant_id}' cannot be persisted with evidence status "
                    f"{p.evidence_status.value}."
                )

        # Step 8: Validate continuity candidates (antecedents, multiplicity)
        seen_candidate_ids: set = set()
        for c in continuity_candidates:
            if c.candidate_id in seen_candidate_ids:
                raise DuplicateDiscourseError(
                    f"Duplicate candidate_id '{c.candidate_id}' in submission."
                )
            seen_candidate_ids.add(c.candidate_id)
            self._enforce_continuity_firewalls(c)
            if source_text_id:
                if c.referring_token_id not in token_by_id:
                    raise DiscourseTokenNotFoundError(
                        f"Continuity candidate '{c.candidate_id}' anchors to nonexistent referring "
                        f"token '{c.referring_token_id}'."
                    )
                if c.candidate_antecedent_token_id and c.candidate_antecedent_token_id not in token_by_id:
                    raise DiscourseTokenNotFoundError(
                        f"Continuity candidate '{c.candidate_id}' cites antecedent token "
                        f"'{c.candidate_antecedent_token_id}' absent from source text '{source_text_id}'."
                    )
            if c.candidate_antecedent_unit_id and c.candidate_antecedent_unit_id not in unit_ids_in_run:
                raise DiscourseOrphanError(
                    f"Continuity candidate '{c.candidate_id}' cites antecedent unit "
                    f"'{c.candidate_antecedent_unit_id}' absent from this run."
                )
            if c.unit_id and c.unit_id not in unit_ids_in_run:
                raise DiscourseOrphanError(
                    f"Continuity candidate '{c.candidate_id}' references unit '{c.unit_id}' "
                    "absent from this run."
                )
            if c.candidate_antecedent_entity_id:
                entity_languages[c.candidate_antecedent_entity_id] = None

        # Step 9: Validate information structure (unit + anchor firewalls)
        seen_info_ids: set = set()
        for i in information_structure:
            if i.info_structure_id in seen_info_ids:
                raise DuplicateDiscourseError(
                    f"Duplicate info_structure_id '{i.info_structure_id}' in submission."
                )
            seen_info_ids.add(i.info_structure_id)
            self._enforce_text_firewalls(
                "Information-structure observation", i.info_structure_id, i.observation_note
            )
            if i.unit_id not in unit_ids_in_run:
                raise DiscourseOrphanError(
                    f"Information-structure record '{i.info_structure_id}' references unit "
                    f"'{i.unit_id}' absent from this run."
                )
            if i.token_id and source_text_id and i.token_id not in token_by_id:
                raise DiscourseTokenNotFoundError(
                    f"Information-structure record '{i.info_structure_id}' cites token "
                    f"'{i.token_id}' absent from source text '{source_text_id}'."
                )

        # Step 10: Validate ambiguities (preservation firewall)
        seen_ambiguity_ids: set = set()
        for a in ambiguities:
            if a.ambiguity_id in seen_ambiguity_ids:
                raise DuplicateDiscourseError(
                    f"Duplicate ambiguity_id '{a.ambiguity_id}' in submission."
                )
            seen_ambiguity_ids.add(a.ambiguity_id)
            self._enforce_ambiguity_firewalls(a)

        # Step 11: Validate entity existence + language firewall
        evidence_ids_seen = {
            x.evidence_id
            for x in (
                *units,
                *segments,
                *relations,
                *context_layers,
                *participants,
                *continuity_candidates,
                *information_structure,
                *ambiguities,
            )
            if getattr(x, "evidence_id", None)
        }

        def _validate_refs(c: sqlite3.Connection) -> Tuple[Dict[str, Optional[str]], set, set]:
            chk = c.cursor()
            langs: Dict[str, Optional[str]] = {}
            for e_id in sorted(entity_languages):
                chk.execute("SELECT language FROM entities WHERE entity_id = ?;", (e_id,))
                row = chk.fetchone()
                if row is None:
                    raise DiscourseNotFoundError(
                        f"Referenced entity '{e_id}' does not exist in the entity catalog."
                    )
                langs[e_id] = row[0]
                if row[0] and source_text_id and row[0] != source_lang.value:
                    raise DiscourseLanguageMismatchError(
                        f"Entity '{e_id}' language '{row[0]}' conflicts with source text language "
                        f"'{source_lang.value}'."
                    )

            evidence_present: set = set()
            for ev_id in sorted(evidence_ids_seen):
                chk.execute("SELECT evidence_id FROM evidence_ledger WHERE evidence_id = ?;", (ev_id,))
                if chk.fetchone() is not None:
                    evidence_present.add(ev_id)

            clause_ids: set = set()
            for u in units:
                if not u.clause_id:
                    continue
                chk.execute("SELECT source_text_id FROM clauses WHERE clause_id = ?;", (u.clause_id,))
                row = chk.fetchone()
                if row is None:
                    raise DiscourseNotFoundError(
                        f"Referenced syntax_clause_id '{u.clause_id}' does not exist."
                    )
                if source_text_id and row[0] != source_text_id:
                    raise DiscourseSyntaxFirewallError(
                        f"Syntax clause '{u.clause_id}' belongs to text '{row[0]}', "
                        f"not '{source_text_id}'."
                    )
                clause_ids.add(u.clause_id)

            for i in information_structure:
                if not i.syntax_clause_id:
                    continue
                chk.execute(
                    "SELECT source_text_id FROM clauses WHERE clause_id = ?;", (i.syntax_clause_id,)
                )
                row = chk.fetchone()
                if row is None:
                    raise DiscourseNotFoundError(
                        f"Referenced syntax_clause_id '{i.syntax_clause_id}' does not exist."
                    )
                if source_text_id and row[0] != source_text_id:
                    raise DiscourseSyntaxFirewallError(
                        f"Syntax clause '{i.syntax_clause_id}' belongs to text '{row[0]}', "
                        f"not '{source_text_id}'."
                    )
                clause_ids.add(i.syntax_clause_id)

            constituent_ids: set = set()
            for i in information_structure:
                if not i.constituent_id:
                    continue
                chk.execute(
                    "SELECT run_id FROM syntactic_constituents WHERE constituent_id = ?;",
                    (i.constituent_id,),
                )
                row = chk.fetchone()
                if row is None:
                    raise DiscourseNotFoundError(
                        f"Referenced constituent_id '{i.constituent_id}' does not exist."
                    )
                constituent_ids.add(i.constituent_id)

            return langs, evidence_present, clause_ids | constituent_ids

        if conn is not None:
            _validate_refs(conn)
        else:
            with self.engine.connect() as chk_c:
                _validate_refs(chk_c)

        # Step 12: Deterministic identifiers and hashes
        input_token_hashes = [
            hashlib.sha256(t.surface_form.encode("utf-8")).hexdigest()[:16]
            for t in sorted(token_by_id.values(), key=lambda x: x.token_id)
        ]
        input_content_hash = hashlib.sha256(":".join(input_token_hashes).encode("utf-8")).hexdigest().lower()
        output_hash = compute_discourse_output_hash(
            units,
            segments,
            relations,
            context_layers,
            participants,
            continuity_candidates,
            information_structure,
            ambiguities,
        )
        run_id = f"DSCRUN-{(source_text_id or 'GLOBAL')[:16]}-{config_hash[:8]}-{output_hash[:8]}"

        # Step 13: Atomic persistence
        def _execute_persistence(tx_conn: sqlite3.Connection) -> DiscourseResult:
            cur = tx_conn.cursor()

            cur.execute("SELECT run_id FROM discourse_runs WHERE run_id = ?;", (run_id,))
            if cur.fetchone() is not None:
                raise DuplicateDiscourseError(f"Discourse run '{run_id}' has already been registered.")

            parent_prov_id = None
            if token_by_id:
                first_token = sorted(token_by_id.values(), key=lambda x: x.token_id)[0]
                parent_prov_id = first_token.provenance_id or None

            if config.is_deterministic:
                prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    input_data={
                        "source_text_id": source_text_id,
                        "syntax_run_id": syntax_run_id,
                        "semantic_run_id": semantic_run_id,
                        "referential_run_id": referential_run_id,
                        "input_content_hash": input_content_hash,
                        "config_hash": config_hash,
                        "unit_count": len(units),
                        "segment_count": len(segments),
                        "relation_count": len(relations),
                    },
                    agent_id=agent,
                    config=config.to_dict(),
                    conn=tx_conn,
                )
            else:
                prov_rec = self.provenance_tracker.record_generative(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    prompt=":".join(input_token_hashes),
                    model=config.analyzer_id,
                    model_version=config.analyzer_version,
                    agent_id=agent,
                    config=config.to_dict(),
                    conn=tx_conn,
                )

            ver_rec = self.version_mgr.create_version(
                object_id=run_id,
                object_type="discourse",
                content_hash=output_hash,
                provenance_id=prov_rec.provenance_id,
                created_by=agent,
                change_reason=ChangeReason.INITIAL_CREATION,
                status=VersionStatus.ACTIVE,
                metadata={
                    "source_text_id": source_text_id,
                    "syntax_run_id": syntax_run_id,
                    "semantic_run_id": semantic_run_id,
                    "referential_run_id": referential_run_id,
                    "configuration_hash": config_hash,
                },
                conn=tx_conn,
            )

            cur.execute(
                """
                INSERT INTO discourse_runs (
                    run_id, source_text_id, tokenization_id, morphology_run_id,
                    syntax_run_id, semantic_run_id, referential_run_id, version_id,
                    provenance_id, analyzer_id, analyzer_version, language,
                    representation_type, configuration_hash, input_content_hash,
                    output_hash, unit_count, segment_count, relation_count,
                    participant_count, continuity_candidate_count,
                    information_structure_count, ambiguity_count,
                    is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?,
                    ?, ?,
                    ?, ?, 1, ?
                );
                """,
                (
                    run_id,
                    source_text_id,
                    tokenization_id or tok_id_in_run,
                    morphology_run_id,
                    syntax_run_id,
                    semantic_run_id,
                    referential_run_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.analyzer_id,
                    config.analyzer_version,
                    source_lang.value,
                    config.representation_type.value,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    len(units),
                    len(segments),
                    len(relations),
                    len(participants),
                    len(continuity_candidates),
                    len(information_structure),
                    len(ambiguities),
                    1 if config.is_deterministic else 0,
                    now_iso,
                    json.dumps(config.to_dict()),
                ),
            )

            persisted_units: List[DiscourseUnitRecord] = []
            for u in units:
                rec = DiscourseUnitRecord(
                    unit_id=u.unit_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    start_token_id=u.start_token_id,
                    end_token_id=u.end_token_id,
                    unit_type=u.unit_type,
                    unit_order=u.unit_order,
                    clause_id=u.clause_id,
                    passage_id=u.passage_id or self._passage_for_token(token_by_id, u.start_token_id),
                    parent_unit_id=u.parent_unit_id,
                    parse_index=u.parse_index,
                    is_preferred=u.is_preferred,
                    confidence_score=u.confidence_score,
                    confidence_level=u.confidence_level,
                    evidence_status=u.evidence_status,
                    evidence_id=u.evidence_id,
                    language=u.language or (source_lang if source_text_id else None),
                    raw_unit_surface=u.raw_unit_surface,
                    observation_note=u.observation_note,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(u.metadata) if u.metadata else None,
                )
                persisted_units.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_units (
                        unit_id, run_id, source_text_id, version_id, provenance_id,
                        clause_id, passage_id, unit_order, unit_type, parent_unit_id,
                        start_token_id, end_token_id, parse_index, is_preferred,
                        confidence_score, confidence_level, evidence_status, evidence_id,
                        language, raw_unit_surface, observation_note, created_at,
                        is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        1, ?
                    );
                    """,
                    (
                        rec.unit_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.clause_id,
                        rec.passage_id,
                        rec.unit_order,
                        rec.unit_type.value,
                        rec.parent_unit_id,
                        rec.start_token_id,
                        rec.end_token_id,
                        rec.parse_index,
                        1 if rec.is_preferred else 0,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.language.value if rec.language else None,
                        rec.raw_unit_surface,
                        rec.observation_note,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_segments: List[DiscourseSegmentRecord] = []
            for s in segments:
                rec = DiscourseSegmentRecord(
                    segment_id=s.segment_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    start_token_id=s.start_token_id,
                    end_token_id=s.end_token_id,
                    segment_type=s.segment_type,
                    segment_order=s.segment_order,
                    start_unit_id=s.start_unit_id,
                    end_unit_id=s.end_unit_id,
                    pericope_id=s.pericope_id,
                    passage_id=s.passage_id or self._passage_for_token(token_by_id, s.start_token_id),
                    parent_segment_id=s.parent_segment_id,
                    parse_index=s.parse_index,
                    is_preferred=s.is_preferred,
                    confidence_score=s.confidence_score,
                    confidence_level=s.confidence_level,
                    evidence_status=s.evidence_status,
                    evidence_id=s.evidence_id,
                    language=s.language or (source_lang if source_text_id else None),
                    raw_segment_surface=s.raw_segment_surface,
                    observation_note=s.observation_note,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(s.metadata) if s.metadata else None,
                )
                persisted_segments.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_segments (
                        segment_id, run_id, source_text_id, version_id, provenance_id,
                        pericope_id, passage_id, parent_segment_id, segment_order,
                        segment_type, start_unit_id, end_unit_id, start_token_id,
                        end_token_id, parse_index, is_preferred, confidence_score,
                        confidence_level, evidence_status, evidence_id, language,
                        raw_segment_surface, observation_note, created_at, is_immutable,
                        metadata_json
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        1, ?
                    );
                    """,
                    (
                        rec.segment_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.pericope_id,
                        rec.passage_id,
                        rec.parent_segment_id,
                        rec.segment_order,
                        rec.segment_type.value,
                        rec.start_unit_id,
                        rec.end_unit_id,
                        rec.start_token_id,
                        rec.end_token_id,
                        rec.parse_index,
                        1 if rec.is_preferred else 0,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.language.value if rec.language else None,
                        rec.raw_segment_surface,
                        rec.observation_note,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_relations: List[DiscourseRelationRecord] = []
            for r in relations:
                rec = DiscourseRelationRecord(
                    relation_id=r.relation_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    source_kind=r.source_kind,
                    source_ref_id=r.source_ref_id,
                    target_kind=r.target_kind,
                    target_ref_id=r.target_ref_id,
                    relation_type=r.relation_type,
                    directionality=r.directionality,
                    grammatical_justification=r.grammatical_justification,
                    justification_basis=r.justification_basis,
                    evidence_status=r.evidence_status,
                    connector_token_id=r.connector_token_id,
                    evidence_id=r.evidence_id,
                    syntax_clause_span_cited=r.syntax_clause_span_cited,
                    confidence_score=r.confidence_score,
                    confidence_level=r.confidence_level,
                    is_ambiguity_flagged=r.is_ambiguity_flagged,
                    observation_note=r.observation_note,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(r.metadata) if r.metadata else None,
                )
                persisted_relations.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_relations (
                        relation_id, run_id, source_text_id, version_id, provenance_id,
                        source_kind, source_ref_id, target_kind, target_ref_id,
                        relation_type, directionality, grammatical_justification,
                        connector_token_id, justification_basis, evidence_status,
                        evidence_id, syntax_clause_span_cited, confidence_score,
                        confidence_level, is_ambiguity_flagged, observation_note,
                        created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, 1, ?
                    );
                    """,
                    (
                        rec.relation_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.source_kind,
                        rec.source_ref_id,
                        rec.target_kind,
                        rec.target_ref_id,
                        rec.relation_type.value,
                        rec.directionality.value,
                        rec.grammatical_justification,
                        rec.connector_token_id,
                        rec.justification_basis.value,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        1 if rec.syntax_clause_span_cited else 0,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        1 if rec.is_ambiguity_flagged else 0,
                        rec.observation_note,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_context: List[ContextLayerRecord] = []
            for c in context_layers:
                rec = ContextLayerRecord(
                    context_layer_id=c.context_layer_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    layer_scope=c.layer_scope,
                    observation_kind=c.observation_kind,
                    observation=c.observation,
                    evidence_status=c.evidence_status,
                    is_evidence=False,
                    confidence_level=c.confidence_level,
                    confidence_score=c.confidence_score,
                    anchor_unit_id=c.anchor_unit_id,
                    anchor_segment_id=c.anchor_segment_id,
                    anchor_passage_id=c.anchor_passage_id,
                    anchor_pericope_id=c.anchor_pericope_id,
                    anchor_book_id=c.anchor_book_id,
                    span_start_passage_id=c.span_start_passage_id,
                    span_end_passage_id=c.span_end_passage_id,
                    evidence_id=c.evidence_id,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(c.metadata) if c.metadata else None,
                )
                persisted_context.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_context_layers (
                        context_layer_id, run_id, source_text_id, version_id, provenance_id,
                        layer_scope, anchor_unit_id, anchor_segment_id, anchor_passage_id,
                        anchor_pericope_id, anchor_book_id, span_start_passage_id,
                        span_end_passage_id, scope_declared, observation_kind, observation,
                        evidence_status, evidence_id, is_evidence, confidence_score,
                        confidence_level, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, 1, ?, ?,
                        ?, ?, 0, ?,
                        ?, ?, 1, ?
                    );
                    """,
                    (
                        rec.context_layer_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.layer_scope.value,
                        rec.anchor_unit_id,
                        rec.anchor_segment_id,
                        rec.anchor_passage_id,
                        rec.anchor_pericope_id,
                        rec.anchor_book_id,
                        rec.span_start_passage_id,
                        rec.span_end_passage_id,
                        rec.observation_kind.value,
                        rec.observation,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_participants: List[ParticipantRecord] = []
            for p in participants:
                rec = ParticipantRecord(
                    participant_id=p.participant_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    participant_role=p.participant_role,
                    role_status=p.role_status,
                    evidence_status=p.evidence_status,
                    unit_id=p.unit_id,
                    segment_id=p.segment_id,
                    passage_id=p.passage_id,
                    entity_id=p.entity_id,
                    entity_mention_id=p.entity_mention_id,
                    grammatical_person=p.grammatical_person,
                    grammatical_number=p.grammatical_number,
                    anchor_token_id=p.anchor_token_id,
                    evidence_id=p.evidence_id,
                    identity_asserted=False,
                    confidence_score=p.confidence_score,
                    confidence_level=p.confidence_level,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(p.metadata) if p.metadata else None,
                )
                persisted_participants.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_participants (
                        participant_id, run_id, source_text_id, version_id, provenance_id,
                        unit_id, segment_id, passage_id, entity_id, entity_mention_id,
                        participant_role, role_status, grammatical_person,
                        grammatical_number, anchor_token_id, evidence_status, evidence_id,
                        identity_asserted, confidence_score, confidence_level, created_at,
                        is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        0, ?, ?, ?,
                        1, ?
                    );
                    """,
                    (
                        rec.participant_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.unit_id,
                        rec.segment_id,
                        rec.passage_id,
                        rec.entity_id,
                        rec.entity_mention_id,
                        rec.participant_role.value,
                        rec.role_status.value,
                        rec.grammatical_person.value if rec.grammatical_person else None,
                        rec.grammatical_number.value if rec.grammatical_number else None,
                        rec.anchor_token_id,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_continuity: List[ContinuityCandidateRecord] = []
            for c in continuity_candidates:
                rec = ContinuityCandidateRecord(
                    candidate_id=c.candidate_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    referring_token_id=c.referring_token_id,
                    continuity_type=c.continuity_type,
                    resolution_status=c.resolution_status,
                    candidate_rank=c.candidate_rank,
                    is_resolved=c.is_resolved,
                    evidence_status=c.evidence_status,
                    referring_mention_id=c.referring_mention_id,
                    unit_id=c.unit_id,
                    passage_id=c.passage_id
                    or self._passage_for_token(token_by_id, c.referring_token_id),
                    candidate_antecedent_token_id=c.candidate_antecedent_token_id,
                    candidate_antecedent_entity_id=c.candidate_antecedent_entity_id,
                    candidate_antecedent_unit_id=c.candidate_antecedent_unit_id,
                    antecedent_distance_tokens=c.antecedent_distance_tokens,
                    resolution_rationale=c.resolution_rationale,
                    evidence_id=c.evidence_id,
                    identity_asserted=False,
                    confidence_score=c.confidence_score,
                    confidence_level=c.confidence_level,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(c.metadata) if c.metadata else None,
                )
                persisted_continuity.append(rec)
                cur.execute(
                    """
                    INSERT INTO referential_continuity_candidates (
                        candidate_id, run_id, source_text_id, version_id, provenance_id,
                        referring_token_id, referring_mention_id, unit_id, passage_id,
                        continuity_type, candidate_antecedent_token_id,
                        candidate_antecedent_entity_id, candidate_antecedent_unit_id,
                        antecedent_distance_tokens, candidate_rank, is_resolved,
                        resolution_status, multiplicity_preserved, resolution_rationale,
                        evidence_status, evidence_id, identity_asserted, confidence_score,
                        confidence_level, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?,
                        ?, ?,
                        ?, ?, ?,
                        ?, 1, ?,
                        ?, ?, 0, ?,
                        ?, ?, 1, ?
                    );
                    """,
                    (
                        rec.candidate_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.referring_token_id,
                        rec.referring_mention_id,
                        rec.unit_id,
                        rec.passage_id,
                        rec.continuity_type.value,
                        rec.candidate_antecedent_token_id,
                        rec.candidate_antecedent_entity_id,
                        rec.candidate_antecedent_unit_id,
                        rec.antecedent_distance_tokens,
                        rec.candidate_rank,
                        1 if rec.is_resolved else 0,
                        rec.resolution_status.value,
                        rec.resolution_rationale,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_info: List[InformationStructureRecord] = []
            for i in information_structure:
                rec = InformationStructureRecord(
                    info_structure_id=i.info_structure_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    unit_id=i.unit_id,
                    information_role=i.information_role,
                    markedness=i.markedness,
                    marking_device=i.marking_device,
                    evidence_status=i.evidence_status,
                    token_id=i.token_id,
                    passage_id=i.passage_id
                    or (self._passage_for_token(token_by_id, i.token_id) if i.token_id else None),
                    constituent_id=i.constituent_id,
                    syntax_clause_id=i.syntax_clause_id,
                    evidence_id=i.evidence_id,
                    confidence_score=i.confidence_score,
                    confidence_level=i.confidence_level,
                    observation_note=i.observation_note,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(i.metadata) if i.metadata else None,
                )
                persisted_info.append(rec)
                cur.execute(
                    """
                    INSERT INTO information_structure (
                        info_structure_id, run_id, source_text_id, version_id, provenance_id,
                        unit_id, passage_id, token_id, constituent_id, information_role,
                        markedness, marking_device, syntax_clause_id, evidence_status,
                        evidence_id, confidence_score, confidence_level, observation_note,
                        created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, 1, ?
                    );
                    """,
                    (
                        rec.info_structure_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.unit_id,
                        rec.passage_id,
                        rec.token_id,
                        rec.constituent_id,
                        rec.information_role.value,
                        rec.markedness.value,
                        rec.marking_device.value,
                        rec.syntax_clause_id,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.confidence_score,
                        rec.confidence_level.value,
                        rec.observation_note,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            persisted_ambiguities: List[DiscourseAmbiguityRecord] = []
            for a in ambiguities:
                interpretations = sorted(a.competing_interpretations)
                rec = DiscourseAmbiguityRecord(
                    ambiguity_id=a.ambiguity_id,
                    run_id=run_id,
                    source_text_id=source_text_id or "",
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    ambiguity_type=a.ambiguity_type,
                    subject_ref_id=a.subject_ref_id,
                    description=a.description,
                    competing_interpretations_json=json.dumps(interpretations),
                    competing_interpretation_count=len(interpretations),
                    resolution_status=a.resolution_status,
                    evidence_status=a.evidence_status,
                    preservation_required=True,
                    collapse_prohibited=True,
                    evidence_id=a.evidence_id,
                    created_at=now_iso,
                    is_immutable=True,
                    metadata_json=json.dumps(a.metadata) if a.metadata else None,
                )
                persisted_ambiguities.append(rec)
                cur.execute(
                    """
                    INSERT INTO discourse_ambiguities (
                        ambiguity_id, run_id, source_text_id, version_id, provenance_id,
                        ambiguity_type, subject_ref_id, competing_interpretations_json,
                        competing_interpretation_count, resolution_status,
                        preservation_required, collapse_prohibited, description,
                        evidence_status, evidence_id, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?,
                        1, 1, ?,
                        ?, ?, ?, 1, ?
                    );
                    """,
                    (
                        rec.ambiguity_id,
                        rec.run_id,
                        rec.source_text_id,
                        rec.version_id,
                        rec.provenance_id,
                        rec.ambiguity_type.value,
                        rec.subject_ref_id,
                        rec.competing_interpretations_json,
                        rec.competing_interpretation_count,
                        rec.resolution_status.value,
                        rec.description,
                        rec.evidence_status.value,
                        rec.evidence_id,
                        rec.created_at,
                        rec.metadata_json,
                    ),
                )

            run_record = DiscourseRunRecord(
                run_id=run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id or tok_id_in_run,
                morphology_run_id=morphology_run_id,
                syntax_run_id=syntax_run_id,
                semantic_run_id=semantic_run_id,
                referential_run_id=referential_run_id,
                version_id=ver_rec.version_id,
                provenance_id=prov_rec.provenance_id,
                analyzer_id=config.analyzer_id,
                analyzer_version=config.analyzer_version,
                language=source_lang,
                representation_type=config.representation_type,
                configuration_hash=config_hash,
                input_content_hash=input_content_hash,
                output_hash=output_hash,
                unit_count=len(units),
                segment_count=len(segments),
                relation_count=len(relations),
                participant_count=len(participants),
                continuity_candidate_count=len(continuity_candidates),
                information_structure_count=len(information_structure),
                ambiguity_count=len(ambiguities),
                is_exact_reproducible=config.is_deterministic,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=json.dumps(config.to_dict()),
            )

            return DiscourseResult(
                run=run_record,
                units=persisted_units,
                segments=persisted_segments,
                relations=persisted_relations,
                context_layers=persisted_context,
                participants=persisted_participants,
                continuity_candidates=persisted_continuity,
                information_structure=persisted_info,
                ambiguities=persisted_ambiguities,
                version=ver_rec,
                provenance=prov_rec,
            )

        if conn is not None:
            return _execute_persistence(conn)
        with self.engine.transaction() as tx_conn:
            return _execute_persistence(tx_conn)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _passage_for_token(token_by_id: Dict[str, TokenRecord], token_id: Optional[str]) -> Optional[str]:
        if not token_id:
            return None
        token = token_by_id.get(token_id)
        return token.passage_id if token else None

    @staticmethod
    def _validate_span_against_tokens(
        token_by_id: Dict[str, TokenRecord],
        resource_id: str,
        resource_label: str,
        start_token_id: str,
        end_token_id: str,
    ) -> None:
        """Reject spans anchored to unknown tokens or reversed token order."""
        start = token_by_id.get(start_token_id)
        end = token_by_id.get(end_token_id)
        if start is None:
            raise DiscourseTokenNotFoundError(
                f"{resource_label} '{resource_id}' anchors to nonexistent start token '{start_token_id}'."
            )
        if end is None:
            raise DiscourseTokenNotFoundError(
                f"{resource_label} '{resource_id}' anchors to nonexistent end token '{end_token_id}'."
            )
        if start.token_index > end.token_index:
            raise DiscourseSpanValidationError(
                f"{resource_label} '{resource_id}' has a reversed span: start token index "
                f"{start.token_index} exceeds end token index {end.token_index}."
            )

    # -------------------------------------------------------------------------
    # Reanalysis & lineage evolution
    # -------------------------------------------------------------------------

    def reanalyze(
        self,
        source_text_id: Optional[str],
        units: Sequence[DiscourseUnitDefinition],
        segments: Sequence[DiscourseSegmentDefinition] = (),
        relations: Sequence[DiscourseRelationDefinition] = (),
        context_layers: Sequence[ContextLayerDefinition] = (),
        participants: Sequence[ParticipantDefinition] = (),
        continuity_candidates: Sequence[ContinuityCandidateDefinition] = (),
        information_structure: Sequence[InformationStructureDefinition] = (),
        ambiguities: Sequence[DiscourseAmbiguityDefinition] = (),
        tokenization_id: Optional[str] = None,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        referential_run_id: Optional[str] = None,
        new_config: Optional[DiscourseAnalyzerConfig] = None,
        agent: str = "polya-discourse-engine",
    ) -> DiscourseResult:
        """
        Produce a new versioned discourse run superseding the prior active run for
        the given source text, without mutating historical records.
        """
        new_config = new_config or DiscourseAnalyzerConfig()

        prior_run_id: Optional[str] = None
        prior_version_id: Optional[str] = None
        if source_text_id:
            with self.engine.connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT run_id, version_id FROM discourse_runs
                    WHERE source_text_id = ?
                    ORDER BY created_at DESC;
                    """,
                    (source_text_id,),
                )
                rows = cur.fetchall()
            if rows:
                prior_run_id = rows[0][0]
                prior_version_id = rows[0][1]

        new_result = self.record_discourse_analysis(
            source_text_id=source_text_id,
            units=units,
            segments=segments,
            relations=relations,
            context_layers=context_layers,
            participants=participants,
            continuity_candidates=continuity_candidates,
            information_structure=information_structure,
            ambiguities=ambiguities,
            tokenization_id=tokenization_id,
            morphology_run_id=morphology_run_id,
            syntax_run_id=syntax_run_id,
            semantic_run_id=semantic_run_id,
            referential_run_id=referential_run_id,
            config=new_config,
            agent=agent,
        )

        if prior_run_id and prior_version_id:
            with self.engine.transaction() as conn:
                try:
                    self.version_mgr.supersede_version(
                        version_id=prior_version_id,
                        superseded_by_version_id=new_result.run.version_id,
                        conn=conn,
                    )
                except Exception:
                    pass

        return new_result


# =============================================================================
# ROW MAPPERS
# =============================================================================

def _run_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> DiscourseRunRecord:
    d = dict(row)
    return DiscourseRunRecord(
        run_id=str(d["run_id"]),
        source_text_id=EnumCodec.opt_str(d.get("source_text_id")),
        tokenization_id=EnumCodec.opt_str(d.get("tokenization_id")),
        morphology_run_id=EnumCodec.opt_str(d.get("morphology_run_id")),
        syntax_run_id=EnumCodec.opt_str(d.get("syntax_run_id")),
        semantic_run_id=EnumCodec.opt_str(d.get("semantic_run_id")),
        referential_run_id=EnumCodec.opt_str(d.get("referential_run_id")),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        analyzer_id=str(d["analyzer_id"]),
        analyzer_version=str(d["analyzer_version"]),
        language=EnumCodec.enum(d.get("language"), SourceTextLanguage, SourceTextLanguage.OTHER),
        representation_type=EnumCodec.enum(
            d.get("representation_type"), RepresentationType, RepresentationType.RAW
        ),
        configuration_hash=str(d["configuration_hash"]),
        input_content_hash=str(d["input_content_hash"]),
        output_hash=str(d["output_hash"]),
        unit_count=int(d.get("unit_count", 0)),
        segment_count=int(d.get("segment_count", 0)),
        relation_count=int(d.get("relation_count", 0)),
        participant_count=int(d.get("participant_count", 0)),
        continuity_candidate_count=int(d.get("continuity_candidate_count", 0)),
        information_structure_count=int(d.get("information_structure_count", 0)),
        ambiguity_count=int(d.get("ambiguity_count", 0)),
        is_exact_reproducible=bool(d.get("is_exact_reproducible", True)),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _unit_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> DiscourseUnitRecord:
    d = dict(row)
    return DiscourseUnitRecord(
        unit_id=str(d["unit_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        start_token_id=str(d["start_token_id"]),
        end_token_id=str(d["end_token_id"]),
        unit_type=EnumCodec.enum(d.get("unit_type"), DiscourseUnitType, DiscourseUnitType.OTHER),
        unit_order=int(d.get("unit_order", 0)),
        clause_id=EnumCodec.opt_str(d.get("clause_id")),
        passage_id=EnumCodec.opt_str(d.get("passage_id")),
        parent_unit_id=EnumCodec.opt_str(d.get("parent_unit_id")),
        parse_index=int(d.get("parse_index", 0)),
        is_preferred=bool(d.get("is_preferred", False)),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        language=EnumCodec.enum(d.get("language"), SourceTextLanguage, None)
        if d.get("language")
        else None,
        raw_unit_surface=str(d.get("raw_unit_surface", "")),
        observation_note=EnumCodec.opt_str(d.get("observation_note")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _segment_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> DiscourseSegmentRecord:
    d = dict(row)
    return DiscourseSegmentRecord(
        segment_id=str(d["segment_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        start_token_id=str(d["start_token_id"]),
        end_token_id=str(d["end_token_id"]),
        segment_type=EnumCodec.enum(
            d.get("segment_type"), DiscourseSegmentType, DiscourseSegmentType.OTHER
        ),
        segment_order=int(d.get("segment_order", 0)),
        start_unit_id=EnumCodec.opt_str(d.get("start_unit_id")),
        end_unit_id=EnumCodec.opt_str(d.get("end_unit_id")),
        pericope_id=EnumCodec.opt_str(d.get("pericope_id")),
        passage_id=EnumCodec.opt_str(d.get("passage_id")),
        parent_segment_id=EnumCodec.opt_str(d.get("parent_segment_id")),
        parse_index=int(d.get("parse_index", 0)),
        is_preferred=bool(d.get("is_preferred", False)),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        language=EnumCodec.enum(d.get("language"), SourceTextLanguage, None)
        if d.get("language")
        else None,
        raw_segment_surface=str(d.get("raw_segment_surface", "")),
        observation_note=EnumCodec.opt_str(d.get("observation_note")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _relation_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> DiscourseRelationRecord:
    d = dict(row)
    return DiscourseRelationRecord(
        relation_id=str(d["relation_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        source_kind=str(d["source_kind"]),
        source_ref_id=str(d["source_ref_id"]),
        target_kind=str(d["target_kind"]),
        target_ref_id=str(d["target_ref_id"]),
        relation_type=EnumCodec.enum(
            d.get("relation_type"), DiscourseRelationType, DiscourseRelationType.OTHER
        ),
        directionality=EnumCodec.enum(
            d.get("directionality"), RelationDirectionality, RelationDirectionality.FORWARD
        ),
        grammatical_justification=str(d.get("grammatical_justification", "")),
        justification_basis=EnumCodec.enum(
            d.get("justification_basis"), JustificationBasis, JustificationBasis.UNSPECIFIED_OBSERVATION
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        connector_token_id=EnumCodec.opt_str(d.get("connector_token_id")),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        syntax_clause_span_cited=bool(d.get("syntax_clause_span_cited", False)),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        is_ambiguity_flagged=bool(d.get("is_ambiguity_flagged", False)),
        observation_note=EnumCodec.opt_str(d.get("observation_note")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _context_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> ContextLayerRecord:
    d = dict(row)
    return ContextLayerRecord(
        context_layer_id=str(d["context_layer_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        layer_scope=EnumCodec.enum(d.get("layer_scope"), ContextLayerScope, ContextLayerScope.UNRESOLVED),
        observation_kind=EnumCodec.enum(
            d.get("observation_kind"), ContextObservationKind, ContextObservationKind.OTHER
        ),
        observation=str(d.get("observation", "")),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        is_evidence=bool(d.get("is_evidence", False)),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        confidence_score=d.get("confidence_score"),
        anchor_unit_id=EnumCodec.opt_str(d.get("anchor_unit_id")),
        anchor_segment_id=EnumCodec.opt_str(d.get("anchor_segment_id")),
        anchor_passage_id=EnumCodec.opt_str(d.get("anchor_passage_id")),
        anchor_pericope_id=EnumCodec.opt_str(d.get("anchor_pericope_id")),
        anchor_book_id=EnumCodec.opt_str(d.get("anchor_book_id")),
        span_start_passage_id=EnumCodec.opt_str(d.get("span_start_passage_id")),
        span_end_passage_id=EnumCodec.opt_str(d.get("span_end_passage_id")),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _participant_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> ParticipantRecord:
    d = dict(row)
    return ParticipantRecord(
        participant_id=str(d["participant_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        participant_role=EnumCodec.enum(d.get("participant_role"), ParticipantRole, ParticipantRole.OTHER),
        role_status=EnumCodec.enum(
            d.get("role_status"), ParticipantRoleStatus, ParticipantRoleStatus.UNRESOLVED
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        unit_id=EnumCodec.opt_str(d.get("unit_id")),
        segment_id=EnumCodec.opt_str(d.get("segment_id")),
        passage_id=EnumCodec.opt_str(d.get("passage_id")),
        entity_id=EnumCodec.opt_str(d.get("entity_id")),
        entity_mention_id=EnumCodec.opt_str(d.get("entity_mention_id")),
        grammatical_person=EnumCodec.enum(d.get("grammatical_person"), GrammaticalPerson, None)
        if d.get("grammatical_person")
        else None,
        grammatical_number=EnumCodec.enum(d.get("grammatical_number"), GrammaticalNumber, None)
        if d.get("grammatical_number")
        else None,
        anchor_token_id=EnumCodec.opt_str(d.get("anchor_token_id")),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        identity_asserted=bool(d.get("identity_asserted", False)),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _continuity_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> ContinuityCandidateRecord:
    d = dict(row)
    return ContinuityCandidateRecord(
        candidate_id=str(d["candidate_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        referring_token_id=str(d["referring_token_id"]),
        continuity_type=EnumCodec.enum(
            d.get("continuity_type"), ContinuityType, ContinuityType.UNRESOLVED
        ),
        resolution_status=EnumCodec.enum(
            d.get("resolution_status"),
            ContinuityResolutionStatus,
            ContinuityResolutionStatus.UNRESOLVED_AMBIGUOUS,
        ),
        candidate_rank=int(d.get("candidate_rank", 1)),
        is_resolved=bool(d.get("is_resolved", False)),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        referring_mention_id=EnumCodec.opt_str(d.get("referring_mention_id")),
        unit_id=EnumCodec.opt_str(d.get("unit_id")),
        passage_id=EnumCodec.opt_str(d.get("passage_id")),
        candidate_antecedent_token_id=EnumCodec.opt_str(d.get("candidate_antecedent_token_id")),
        candidate_antecedent_entity_id=EnumCodec.opt_str(d.get("candidate_antecedent_entity_id")),
        candidate_antecedent_unit_id=EnumCodec.opt_str(d.get("candidate_antecedent_unit_id")),
        antecedent_distance_tokens=d.get("antecedent_distance_tokens"),
        resolution_rationale=EnumCodec.opt_str(d.get("resolution_rationale")),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        identity_asserted=bool(d.get("identity_asserted", False)),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _information_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> InformationStructureRecord:
    d = dict(row)
    return InformationStructureRecord(
        info_structure_id=str(d["info_structure_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        unit_id=str(d["unit_id"]),
        information_role=EnumCodec.enum(
            d.get("information_role"), InformationRole, InformationRole.UNDETERMINED
        ),
        markedness=EnumCodec.enum(d.get("markedness"), Markedness, Markedness.UNDETERMINED),
        marking_device=EnumCodec.enum(
            d.get("marking_device"), MarkingDevice, MarkingDevice.NONE_OBSERVED
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.INFERRED
        ),
        token_id=EnumCodec.opt_str(d.get("token_id")),
        passage_id=EnumCodec.opt_str(d.get("passage_id")),
        constituent_id=EnumCodec.opt_str(d.get("constituent_id")),
        syntax_clause_id=EnumCodec.opt_str(d.get("syntax_clause_id")),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        confidence_score=d.get("confidence_score"),
        confidence_level=EnumCodec.enum(
            d.get("confidence_level"), DiscourseConfidence, DiscourseConfidence.PROVISIONAL
        ),
        observation_note=EnumCodec.opt_str(d.get("observation_note")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )


def _ambiguity_from_row(row: Union[sqlite3.Row, Dict[str, Any]]) -> DiscourseAmbiguityRecord:
    d = dict(row)
    return DiscourseAmbiguityRecord(
        ambiguity_id=str(d["ambiguity_id"]),
        run_id=str(d["run_id"]),
        source_text_id=str(d["source_text_id"]),
        version_id=str(d["version_id"]),
        provenance_id=str(d["provenance_id"]),
        ambiguity_type=EnumCodec.enum(
            d.get("ambiguity_type"), DiscourseAmbiguityType, DiscourseAmbiguityType.OTHER
        ),
        subject_ref_id=str(d["subject_ref_id"]),
        description=str(d.get("description", "")),
        competing_interpretations_json=str(d.get("competing_interpretations_json", "[]")),
        competing_interpretation_count=int(d.get("competing_interpretation_count", 0)),
        resolution_status=EnumCodec.enum(
            d.get("resolution_status"),
            DiscourseAmbiguityResolution,
            DiscourseAmbiguityResolution.UNRESOLVED,
        ),
        evidence_status=EnumCodec.enum(
            d.get("evidence_status"), DiscourseEvidenceStatus, DiscourseEvidenceStatus.AMBIGUOUS
        ),
        preservation_required=bool(d.get("preservation_required", True)),
        collapse_prohibited=bool(d.get("collapse_prohibited", True)),
        evidence_id=EnumCodec.opt_str(d.get("evidence_id")),
        created_at=str(d.get("created_at", "")),
        is_immutable=bool(d.get("is_immutable", True)),
        metadata_json=EnumCodec.opt_str(d.get("metadata_json")),
    )
