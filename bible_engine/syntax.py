"""
Source-Language Syntax Foundation Subsystem for Polya Philological Bible Engine.
Task 2.4 — Architecture v2.0 — FROZEN.

Provides:
  - SYNTAX MODEL: Explicit dependency relations, constituency phrase structures, and clause boundaries.
  - TOKEN LINKAGE & ORPHAN REJECTION: Every syntactic node/relation binds to validated source tokens.
  - CLAUSE MODEL: Clauses preserved independently of verse or sentence boundaries.
  - MULTIPLE COMPETING PARSES: Represents alternative parses (Parse 1 vs Parse 2) without overwriting.
  - CONFIDENCE & EVIDENCE FIREWALL: Confidence is metadata, strictly separated from empirical evidence.
  - MORPHOLOGY FIREWALL: Syntax references morphology but CANNOT mutate morphological features.
  - SEMANTICS & THEOLOGY FIREWALL: Zero automatic inference of semantic roles or theological claims.
  - REFERENTIAL IDENTITY FIREWALL: Syntactic relations (e.g. apposition, predicate) never create strict identity.
  - CYCLE DETECTION: Validates that dependency trees contain no illegal directed cycles or self-loops.
  - IMMUTABILITY: SQLite triggers prevent row mutations or unauthorized deletions.
  - PROVENANCE & VERSIONING: Full object_versions lineage and cryptographic provenance ledger integration.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSyntaxError,
    LemmaNotFoundError,
    MorphologyNotFoundError,
    SyntaxClauseNotFoundError,
    SyntaxConfidenceError,
    SyntaxConstituentNotFoundError,
    SyntaxCycleError,
    SyntaxFeatureValidationError,
    SyntaxIdentityFirewallError,
    SyntaxImmutabilityError,
    SyntaxInvalidProvenanceError,
    SyntaxInvalidVersionError,
    SyntaxLanguageMismatchError,
    SyntaxMorphologyFirewallError,
    SyntaxNotFoundError,
    SyntaxOrphanError,
    SyntaxSemanticsFirewallError,
    SyntaxSpanValidationError,
    SyntaxSubsystemError,
    SyntaxTheologyFirewallError,
    SyntaxTokenNotFoundError,
    TokenNotFoundError,
)
from bible_engine.provenance import ProvenanceRecord, ProvenanceTracker, TargetType
from bible_engine.source_text import RepresentationType, SourceTextLanguage, SourceTextManager
from bible_engine.tokenization import TokenizationManager, TokenRecord
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionRelationType,
    VersionStatus,
    generate_relation_id,
)


# =============================================================================
# CONTROLLED TAXONOMIES & ENUMERATIONS
# =============================================================================

class SyntaxModelType(str, Enum):
    """Supported analytical syntactic frameworks."""
    DEPENDENCY = "DEPENDENCY"
    CONSTITUENCY = "CONSTITUENCY"
    HYBRID = "HYBRID"


class SyntaxRelationType(str, Enum):
    """
    Standard grammatical dependency relation categories.
    At minimum implements the 14 core types required by specification plus explicit extensions.
    """
    SUBJECT = "SUBJECT"
    PREDICATE = "PREDICATE"
    OBJECT = "OBJECT"
    INDIRECT_OBJECT = "INDIRECT_OBJECT"
    MODIFIER = "MODIFIER"
    ADJUNCT = "ADJUNCT"
    COMPLEMENT = "COMPLEMENT"
    APPOSITION = "APPOSITION"
    COORDINATION = "COORDINATION"
    SUBORDINATION = "SUBORDINATION"
    RELATIVE = "RELATIVE"
    PREPOSITIONAL_COMPLEMENT = "PREPOSITIONAL_COMPLEMENT"
    VOCATIVE = "VOCATIVE"
    OTHER = "OTHER"

    # Explicit Linguistic Extensions
    SPECIFIER = "SPECIFIER"
    CONJUNCT = "CONJUNCT"
    COPULA = "COPULA"
    DETERMINER = "DETERMINER"
    ADVERBIAL = "ADVERBIAL"
    CONSTRUCT_GENITIVE = "CONSTRUCT_GENITIVE"
    ROOT = "ROOT"


class ClauseType(str, Enum):
    """Independent clause boundary categories."""
    INDEPENDENT = "INDEPENDENT"
    SUBORDINATE_PURPOSE = "SUBORDINATE_PURPOSE"
    SUBORDINATE_CAUSAL = "SUBORDINATE_CAUSAL"
    SUBORDINATE_RELATIVE = "SUBORDINATE_RELATIVE"
    SUBORDINATE_TEMPORAL = "SUBORDINATE_TEMPORAL"
    SUBORDINATE_CONDITIONAL = "SUBORDINATE_CONDITIONAL"
    SUBORDINATE_RESULT = "SUBORDINATE_RESULT"
    SUBORDINATE_COMPARATIVE = "SUBORDINATE_COMPARATIVE"
    VERBLESS_NOMINAL = "VERBLESS_NOMINAL"
    PARTICIPIAL_CONSTRUCTION = "PARTICIPIAL_CONSTRUCTION"
    CONDITIONAL_PROTASIS = "CONDITIONAL_PROTASIS"
    CONDITIONAL_APODOSIS = "CONDITIONAL_APODOSIS"
    INFINITIVAL = "INFINITIVAL"
    COORDINATE = "COORDINATE"
    PARENT_EMBEDDED = "PARENT_EMBEDDED"
    OTHER = "OTHER"


class ClauseRelationToParent(str, Enum):
    """Relational attachment of a clause to its parent clause."""
    COORDINATION = "COORDINATION"
    SUBORDINATION = "SUBORDINATION"
    APPOSITION = "APPOSITION"
    PARENT_EMBEDDED = "PARENT_EMBEDDED"
    COMPLEMENT = "COMPLEMENT"
    ADJUNCT = "ADJUNCT"
    RELATIVE = "RELATIVE"
    OTHER = "OTHER"


class ConstituentType(str, Enum):
    """Hierarchical constituent phrase types."""
    NOUN_PHRASE = "NOUN_PHRASE"
    VERB_PHRASE = "VERB_PHRASE"
    PREPOSITIONAL_PHRASE = "PREPOSITIONAL_PHRASE"
    ADJECTIVAL_PHRASE = "ADJECTIVAL_PHRASE"
    ADVERBIAL_PHRASE = "ADVERBIAL_PHRASE"
    PARTICIPIAL_PHRASE = "PARTICIPIAL_PHRASE"
    INFINITIVE_PHRASE = "INFINITIVE_PHRASE"
    CONSTRUCT_CHAIN = "CONSTRUCT_CHAIN"
    CLAUSE_CONSTITUENT = "CLAUSE_CONSTITUENT"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    """Standardized confidence level metadata."""
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    PROVISIONAL = "PROVISIONAL"
    DISPUTED = "DISPUTED"
    AMBIGUOUS = "AMBIGUOUS"


# =============================================================================
# INPUT DEFINITIONS & IMMUTABLE DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class ClauseDefinition:
    """Input definition for an independent clause boundary and classification."""
    clause_id: str
    clause_order: int
    clause_type: ClauseType
    start_token_id: str
    end_token_id: str
    raw_clause_string: str
    parent_clause_id: Optional[str] = None
    relation_to_parent: Optional[ClauseRelationToParent] = None
    lead_conjunction_token_id: Optional[str] = None
    passage_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_ref: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate_confidence(self) -> None:
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise SyntaxConfidenceError(
                    f"Clause confidence_score {self.confidence_score} must be within [0.0, 1.0]."
                )


@dataclass(frozen=True)
class ConstituentDefinition:
    """Input definition for a syntactic constituent / phrase span."""
    constituent_id: str
    clause_id: str
    constituent_type: ConstituentType
    start_token_id: str
    end_token_id: str
    parent_constituent_id: Optional[str] = None
    grammatical_role: Optional[SyntaxRelationType] = None
    head_token_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_ref: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate_confidence(self) -> None:
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise SyntaxConfidenceError(
                    f"Constituent confidence_score {self.confidence_score} must be within [0.0, 1.0]."
                )


@dataclass(frozen=True)
class DependencyRelationDefinition:
    """Input definition for a directed dependency relation between tokens."""
    dependency_id: str
    clause_id: str
    dependent_token_id: str
    head_token_id: Optional[str] = None  # None indicates clause/sentence root
    relation_type: SyntaxRelationType = SyntaxRelationType.OTHER
    language_specific_tag: Optional[str] = None
    morphology_annotation_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    evidence_ref: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate_confidence(self) -> None:
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise SyntaxConfidenceError(
                    f"Dependency relation confidence_score {self.confidence_score} must be within [0.0, 1.0]."
                )


# =============================================================================
# PERSISTED RECORD DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class ClauseRecord:
    """Authoritative persisted clause boundary record."""
    clause_id: str
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    clause_order: int
    clause_type: ClauseType
    start_token_id: str
    end_token_id: str
    raw_clause_string: str
    parent_clause_id: Optional[str] = None
    relation_to_parent: Optional[ClauseRelationToParent] = None
    lead_conjunction_token_id: Optional[str] = None
    passage_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    evidence_ref: Optional[str] = None
    is_immutable: bool = True
    created_at: str = ""
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clause_id": self.clause_id,
            "run_id": self.run_id,
            "source_text_id": self.source_text_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "parent_clause_id": self.parent_clause_id,
            "clause_order": self.clause_order,
            "clause_type": self.clause_type.value,
            "relation_to_parent": self.relation_to_parent.value if self.relation_to_parent else None,
            "start_token_id": self.start_token_id,
            "end_token_id": self.end_token_id,
            "lead_conjunction_token_id": self.lead_conjunction_token_id,
            "passage_id": self.passage_id,
            "parse_index": self.parse_index,
            "is_preferred": 1 if self.is_preferred else 0,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "evidence_ref": self.evidence_ref,
            "raw_clause_string": self.raw_clause_string,
            "is_immutable": 1 if self.is_immutable else 0,
            "created_at": self.created_at,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> ClauseRecord:
        d = dict(row)
        raw_ctype = d.get("clause_type") or "INDEPENDENT"
        try:
            ctype = ClauseType(raw_ctype)
        except ValueError:
            ctype = ClauseType.OTHER

        raw_rel = d.get("relation_to_parent")
        rel_to_parent = None
        if raw_rel:
            try:
                rel_to_parent = ClauseRelationToParent(raw_rel)
            except ValueError:
                rel_to_parent = ClauseRelationToParent.OTHER

        return cls(
            clause_id=str(d["clause_id"]),
            run_id=str(d["run_id"]),
            source_text_id=str(d["source_text_id"]),
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            parent_clause_id=str(d["parent_clause_id"]) if d.get("parent_clause_id") else None,
            clause_order=int(d["clause_order"]),
            clause_type=ctype,
            relation_to_parent=rel_to_parent,
            start_token_id=str(d["start_token_id"]),
            end_token_id=str(d["end_token_id"]),
            lead_conjunction_token_id=str(d["lead_conjunction_token_id"]) if d.get("lead_conjunction_token_id") else None,
            passage_id=str(d["passage_id"]) if d.get("passage_id") else None,
            parse_index=int(d.get("parse_index", 0)),
            is_preferred=bool(d.get("is_preferred", 1)),
            confidence_score=float(d["confidence_score"]) if d.get("confidence_score") is not None else None,
            confidence_level=str(d["confidence_level"]) if d.get("confidence_level") else None,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            raw_clause_string=str(d.get("raw_clause_string", "")),
            is_immutable=bool(d.get("is_immutable", 1)),
            created_at=str(d.get("created_at", "")),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SyntacticConstituentRecord:
    """Authoritative persisted constituent phrase span record."""
    constituent_id: str
    run_id: str
    clause_id: str
    constituent_type: ConstituentType
    start_token_id: str
    end_token_id: str
    parent_constituent_id: Optional[str] = None
    grammatical_role: Optional[SyntaxRelationType] = None
    head_token_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    evidence_ref: Optional[str] = None
    is_immutable: bool = True
    created_at: str = ""
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "constituent_id": self.constituent_id,
            "run_id": self.run_id,
            "clause_id": self.clause_id,
            "parent_constituent_id": self.parent_constituent_id,
            "constituent_type": self.constituent_type.value,
            "grammatical_role": self.grammatical_role.value if self.grammatical_role else None,
            "head_token_id": self.head_token_id,
            "start_token_id": self.start_token_id,
            "end_token_id": self.end_token_id,
            "parse_index": self.parse_index,
            "is_preferred": 1 if self.is_preferred else 0,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "evidence_ref": self.evidence_ref,
            "is_immutable": 1 if self.is_immutable else 0,
            "created_at": self.created_at,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SyntacticConstituentRecord:
        d = dict(row)
        raw_ctype = d.get("constituent_type") or "NOUN_PHRASE"
        try:
            ctype = ConstituentType(raw_ctype)
        except ValueError:
            ctype = ConstituentType.OTHER

        raw_role = d.get("grammatical_role")
        role = None
        if raw_role:
            try:
                role = SyntaxRelationType(raw_role)
            except ValueError:
                role = SyntaxRelationType.OTHER

        return cls(
            constituent_id=str(d["constituent_id"]),
            run_id=str(d["run_id"]),
            clause_id=str(d["clause_id"]),
            parent_constituent_id=str(d["parent_constituent_id"]) if d.get("parent_constituent_id") else None,
            constituent_type=ctype,
            grammatical_role=role,
            head_token_id=str(d["head_token_id"]) if d.get("head_token_id") else None,
            start_token_id=str(d["start_token_id"]),
            end_token_id=str(d["end_token_id"]),
            parse_index=int(d.get("parse_index", 0)),
            is_preferred=bool(d.get("is_preferred", 1)),
            confidence_score=float(d["confidence_score"]) if d.get("confidence_score") is not None else None,
            confidence_level=str(d["confidence_level"]) if d.get("confidence_level") else None,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            is_immutable=bool(d.get("is_immutable", 1)),
            created_at=str(d.get("created_at", "")),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SyntaxDependencyRecord:
    """Authoritative persisted dependency relation record."""
    dependency_id: str
    run_id: str
    clause_id: str
    dependent_token_id: str
    relation_type: SyntaxRelationType
    head_token_id: Optional[str] = None
    language_specific_tag: Optional[str] = None
    morphology_annotation_id: Optional[str] = None
    parse_index: int = 0
    is_preferred: bool = True
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None
    evidence_ref: Optional[str] = None
    is_immutable: bool = True
    created_at: str = ""
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dependency_id": self.dependency_id,
            "run_id": self.run_id,
            "clause_id": self.clause_id,
            "head_token_id": self.head_token_id,
            "dependent_token_id": self.dependent_token_id,
            "relation_type": self.relation_type.value,
            "language_specific_tag": self.language_specific_tag,
            "morphology_annotation_id": self.morphology_annotation_id,
            "parse_index": self.parse_index,
            "is_preferred": 1 if self.is_preferred else 0,
            "confidence_score": self.confidence_score,
            "confidence_level": self.confidence_level,
            "evidence_ref": self.evidence_ref,
            "is_immutable": 1 if self.is_immutable else 0,
            "created_at": self.created_at,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SyntaxDependencyRecord:
        d = dict(row)
        raw_rel = d.get("relation_type") or "OTHER"
        try:
            rel = SyntaxRelationType(raw_rel)
        except ValueError:
            rel = SyntaxRelationType.OTHER

        return cls(
            dependency_id=str(d["dependency_id"]),
            run_id=str(d["run_id"]),
            clause_id=str(d["clause_id"]),
            head_token_id=str(d["head_token_id"]) if d.get("head_token_id") else None,
            dependent_token_id=str(d["dependent_token_id"]),
            relation_type=rel,
            language_specific_tag=str(d["language_specific_tag"]) if d.get("language_specific_tag") else None,
            morphology_annotation_id=str(d["morphology_annotation_id"]) if d.get("morphology_annotation_id") else None,
            parse_index=int(d.get("parse_index", 0)),
            is_preferred=bool(d.get("is_preferred", 1)),
            confidence_score=float(d["confidence_score"]) if d.get("confidence_score") is not None else None,
            confidence_level=str(d["confidence_level"]) if d.get("confidence_level") else None,
            evidence_ref=str(d["evidence_ref"]) if d.get("evidence_ref") else None,
            is_immutable=bool(d.get("is_immutable", 1)),
            created_at=str(d.get("created_at", "")),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SyntaxRunRecord:
    """Authoritative ledger entry for an immutable syntax derivation run."""
    run_id: str
    source_text_id: str
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    language: SourceTextLanguage
    representation_type: RepresentationType
    syntax_model_type: SyntaxModelType
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    tokenization_id: Optional[str] = None
    morphology_run_id: Optional[str] = None
    clause_count: int = 0
    dependency_count: int = 0
    constituent_count: int = 0
    is_exact_reproducible: bool = True
    created_at: str = ""
    is_immutable: bool = True
    metadata_json: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "source_text_id": self.source_text_id,
            "tokenization_id": self.tokenization_id,
            "morphology_run_id": self.morphology_run_id,
            "version_id": self.version_id,
            "provenance_id": self.provenance_id,
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "language": self.language.value,
            "representation_type": self.representation_type.value,
            "syntax_model_type": self.syntax_model_type.value,
            "configuration_hash": self.configuration_hash,
            "input_content_hash": self.input_content_hash,
            "output_hash": self.output_hash,
            "clause_count": self.clause_count,
            "dependency_count": self.dependency_count,
            "constituent_count": self.constituent_count,
            "is_exact_reproducible": 1 if self.is_exact_reproducible else 0,
            "created_at": self.created_at,
            "is_immutable": 1 if self.is_immutable else 0,
            "metadata_json": self.metadata_json,
        }

    @classmethod
    def from_row(cls, row: Union[sqlite3.Row, Dict[str, Any]]) -> SyntaxRunRecord:
        d = dict(row)
        raw_lang = d.get("language") or "GREEK"
        try:
            lang = SourceTextLanguage(raw_lang)
        except ValueError:
            lang = SourceTextLanguage.OTHER

        raw_rep = d.get("representation_type") or "RAW"
        try:
            rep = RepresentationType(raw_rep)
        except ValueError:
            rep = RepresentationType.RAW

        raw_mtype = d.get("syntax_model_type") or "DEPENDENCY"
        try:
            mtype = SyntaxModelType(raw_mtype)
        except ValueError:
            mtype = SyntaxModelType.DEPENDENCY

        return cls(
            run_id=str(d["run_id"]),
            source_text_id=str(d["source_text_id"]),
            tokenization_id=str(d["tokenization_id"]) if d.get("tokenization_id") else None,
            morphology_run_id=str(d["morphology_run_id"]) if d.get("morphology_run_id") else None,
            version_id=str(d["version_id"]),
            provenance_id=str(d["provenance_id"]),
            analyzer_id=str(d["analyzer_id"]),
            analyzer_version=str(d["analyzer_version"]),
            language=lang,
            representation_type=rep,
            syntax_model_type=mtype,
            configuration_hash=str(d["configuration_hash"]),
            input_content_hash=str(d["input_content_hash"]),
            output_hash=str(d["output_hash"]),
            clause_count=int(d.get("clause_count", 0)),
            dependency_count=int(d.get("dependency_count", 0)),
            constituent_count=int(d.get("constituent_count", 0)),
            is_exact_reproducible=bool(d.get("is_exact_reproducible", 1)),
            created_at=str(d.get("created_at", "")),
            is_immutable=bool(d.get("is_immutable", 1)),
            metadata_json=str(d["metadata_json"]) if d.get("metadata_json") else None,
        )


@dataclass(frozen=True)
class SyntaxAnalyzerConfig:
    """Execution configuration parameters for syntax parsing."""
    analyzer_id: str = "polya-syntax-engine"
    analyzer_version: str = "1.0.0"
    is_deterministic: bool = True
    representation_type: RepresentationType = RepresentationType.RAW
    syntax_model_type: SyntaxModelType = SyntaxModelType.DEPENDENCY
    custom_params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "is_deterministic": self.is_deterministic,
            "representation_type": self.representation_type.value,
            "syntax_model_type": self.syntax_model_type.value,
            "custom_params": self.custom_params or {},
        }

    def compute_config_hash(self) -> str:
        serialized = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class SyntaxResult:
    """Aggregated output of a syntax derivation run."""
    run: SyntaxRunRecord
    clauses: List[ClauseRecord]
    dependencies: List[SyntaxDependencyRecord]
    constituents: List[SyntacticConstituentRecord]
    token_dependencies_map: Dict[str, List[SyntaxDependencyRecord]]


# =============================================================================
# HASHING & GRAPH INTEGRITY UTILITIES
# =============================================================================

def compute_syntax_output_hash(
    clauses: Sequence[Union[ClauseRecord, ClauseDefinition]],
    dependencies: Sequence[Union[SyntaxDependencyRecord, DependencyRelationDefinition]],
    constituents: Sequence[Union[SyntacticConstituentRecord, ConstituentDefinition]],
) -> str:
    """
    Compute deterministic SHA-256 digest over canonically ordered syntax observations.
    Guarantees roundtrip hash stability between in-memory structures and database rows.
    """
    sorted_clauses = sorted(clauses, key=lambda c: (c.clause_order, c.parse_index, c.clause_id))
    sorted_deps = sorted(dependencies, key=lambda d: (d.clause_id, d.dependent_token_id, d.parse_index))
    sorted_consts = sorted(constituents, key=lambda k: (k.clause_id, k.start_token_id, k.end_token_id, k.parse_index))

    payload = {
        "clauses": [
            {
                "clause_id": c.clause_id,
                "clause_order": c.clause_order,
                "clause_type": c.clause_type.value if hasattr(c.clause_type, "value") else str(c.clause_type),
                "start_token_id": c.start_token_id,
                "end_token_id": c.end_token_id,
                "parse_index": c.parse_index,
                "confidence_score": c.confidence_score,
            }
            for c in sorted_clauses
        ],
        "dependencies": [
            {
                "dependency_id": d.dependency_id,
                "clause_id": d.clause_id,
                "head_token_id": d.head_token_id,
                "dependent_token_id": d.dependent_token_id,
                "relation_type": d.relation_type.value if hasattr(d.relation_type, "value") else str(d.relation_type),
                "parse_index": d.parse_index,
                "confidence_score": d.confidence_score,
            }
            for d in sorted_deps
        ],
        "constituents": [
            {
                "constituent_id": k.constituent_id,
                "clause_id": k.clause_id,
                "constituent_type": k.constituent_type.value if hasattr(k.constituent_type, "value") else str(k.constituent_type),
                "start_token_id": k.start_token_id,
                "end_token_id": k.end_token_id,
                "parse_index": k.parse_index,
                "confidence_score": k.confidence_score,
            }
            for k in sorted_consts
        ],
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


def detect_dependency_cycles(
    dependencies: Sequence[Union[DependencyRelationDefinition, SyntaxDependencyRecord]]
) -> None:
    """
    Detect illegal directed cycles in a dependency graph for each (clause_id, parse_index).
    In standard dependency grammars, head -> dependent relations must form a directed tree/forest (DAG).
    Self-loops (head == dependent) or mutual loops (A -> B -> A) violate tree acyclicity.
    """
    # Group dependencies by (clause_id, parse_index)
    parses_map: Dict[Tuple[str, int], List[Tuple[str, str]]] = {}
    for dep in dependencies:
        if dep.head_token_id is not None:
            if dep.head_token_id == dep.dependent_token_id:
                raise SyntaxCycleError(
                    f"Illegal self-loop cycle detected: token '{dep.dependent_token_id}' cannot be its own head."
                )
            key = (dep.clause_id, dep.parse_index)
            parses_map.setdefault(key, []).append((dep.head_token_id, dep.dependent_token_id))

    for (c_id, p_idx), edges in parses_map.items():
        adj: Dict[str, List[str]] = {}
        nodes: Set[str] = set()
        for head, dep in edges:
            adj.setdefault(head, []).append(dep)
            nodes.add(head)
            nodes.add(dep)

        # Cycle detection using DFS with 3-color marking
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node: str, path: List[str]) -> None:
            visited[node] = 1
            for nxt in adj.get(node, []):
                if visited.get(nxt, 0) == 1:
                    cycle_str = " -> ".join(path + [nxt])
                    raise SyntaxCycleError(
                        f"Illegal dependency cycle detected in clause '{c_id}' (parse {p_idx}): {cycle_str}"
                    )
                if visited.get(nxt, 0) == 0:
                    dfs(nxt, path + [nxt])
            visited[node] = 2

        for node in nodes:
            if visited.get(node, 0) == 0:
                dfs(node, [node])


# =============================================================================
# SYNTAX MANAGER ENGINE
# =============================================================================

class SyntaxManager:
    """
    Core engine managing source-language syntax parsing, clause segmentation,
    phrase constituency trees, and directed dependency relations.
    """

    def __init__(self, engine: DatabaseEngine):
        self.engine = engine
        self.provenance_tracker = ProvenanceTracker(engine)
        self.version_mgr = VersionManager(engine)
        self.source_text_mgr = SourceTextManager(engine)
        self.token_mgr = TokenizationManager(engine)

    # -------------------------------------------------------------------------
    # 1. CORE SYNTAX REGISTRATION
    # -------------------------------------------------------------------------

    def record_syntax_analysis(
        self,
        source_text_id: str,
        clauses: Sequence[ClauseDefinition],
        dependencies: Sequence[DependencyRelationDefinition],
        constituents: Optional[Sequence[ConstituentDefinition]] = None,
        morphology_run_id: Optional[str] = None,
        config: Optional[SyntaxAnalyzerConfig] = None,
        agent: str = "polya-syntax-engine",
        conn: Optional[sqlite3.Connection] = None,
    ) -> SyntaxResult:
        """
        Record authoritative syntactic observations with strict validation against
        source tokens, cycle prevention, confidence firewall, and provenance tracking.
        """
        config = config or SyntaxAnalyzerConfig()
        constituents = constituents or []
        config_hash = config.compute_config_hash()
        now_iso = datetime.now(timezone.utc).isoformat()

        # Step 1: Resolve source text and authoritative tokens
        try:
            source_rec = self.source_text_mgr.get_source_text(source_text_id)
        except Exception as e:
            raise SyntaxNotFoundError(f"Source text '{source_text_id}' does not exist: {e}") from e

        raw_lang = source_rec.language
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
        if not raw_tokens:
            raise SyntaxOrphanError(f"Source text '{source_text_id}' has no tokens. Ingest tokenization first.")

        token_by_id: Dict[str, TokenRecord] = {t.token_id: t for t in raw_tokens}
        token_order_by_id: Dict[str, int] = {t.token_id: t.token_index for t in raw_tokens}
        tokenization_id = raw_tokens[0].tokenization_id

        # Step 2: Validate morphology run linkage if provided
        if morphology_run_id:
            def _check_morph(c: sqlite3.Connection) -> None:
                cur = c.cursor()
                cur.execute("SELECT source_text_id, language FROM morphology_runs WHERE run_id = ?;", (morphology_run_id,))
                row = cur.fetchone()
                if row is None:
                    raise MorphologyNotFoundError(f"Morphology run '{morphology_run_id}' does not exist.")
                if row[0] != source_text_id:
                    raise SyntaxLanguageMismatchError(
                        f"Morphology run '{morphology_run_id}' source_text_id '{row[0]}' conflicts with '{source_text_id}'."
                    )
            if conn is not None:
                _check_morph(conn)
            else:
                with self.engine.connect() as check_conn:
                    _check_morph(check_conn)

        # Step 3: Validate clauses
        if not clauses:
            raise SyntaxFeatureValidationError("At least one clause definition must be provided.")

        clause_ids_in_batch: Set[str] = set()
        seen_clause_orders: Set[Tuple[int, int]] = set()

        for c_def in clauses:
            c_def.validate_confidence()

            # Token existence
            if c_def.start_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Clause start_token_id '{c_def.start_token_id}' does not exist.")
            if c_def.end_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Clause end_token_id '{c_def.end_token_id}' does not exist.")

            # Span ordering check
            start_idx = token_order_by_id[c_def.start_token_id]
            end_idx = token_order_by_id[c_def.end_token_id]
            if start_idx > end_idx:
                raise SyntaxSpanValidationError(
                    f"Clause '{c_def.clause_id}' has inverted token order: start {start_idx} > end {end_idx}."
                )

            # Lead conjunction token existence
            if c_def.lead_conjunction_token_id and c_def.lead_conjunction_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(
                    f"Clause lead_conjunction_token_id '{c_def.lead_conjunction_token_id}' does not exist."
                )

            # Uniqueness of (clause_order, parse_index)
            order_key = (c_def.clause_order, c_def.parse_index)
            if order_key in seen_clause_orders:
                raise DuplicateSyntaxError(
                    f"Duplicate clause_order {c_def.clause_order} with parse_index {c_def.parse_index} in run."
                )
            seen_clause_orders.add(order_key)
            clause_ids_in_batch.add(c_def.clause_id)

        # Validate parent_clause_ids in batch or DB and prevent circular clause hierarchy
        all_clause_ids = set(clause_ids_in_batch)
        clause_adj: Dict[str, str] = {}
        for c_def in clauses:
            if c_def.parent_clause_id:
                if c_def.parent_clause_id == c_def.clause_id:
                    raise SyntaxCycleError(f"Clause '{c_def.clause_id}' cannot be its own parent.")
                if c_def.parent_clause_id not in all_clause_ids:
                    with self.engine.connect() as chk_conn:
                        chk_cur = chk_conn.cursor()
                        chk_cur.execute("SELECT 1 FROM clauses WHERE clause_id = ?;", (c_def.parent_clause_id,))
                        if chk_cur.fetchone() is None:
                            raise SyntaxClauseNotFoundError(
                                f"Clause '{c_def.clause_id}' references nonexistent parent_clause_id '{c_def.parent_clause_id}'."
                            )
                clause_adj[c_def.clause_id] = c_def.parent_clause_id

        # Detect cycle in clause hierarchy
        for c_id in clause_adj:
            curr = c_id
            visited_path = [curr]
            while curr in clause_adj:
                curr = clause_adj[curr]
                if curr in visited_path:
                    raise SyntaxCycleError(
                        f"Circular clause hierarchy detected: {' -> '.join(visited_path + [curr])}"
                    )
                visited_path.append(curr)

        # Step 4: Validate constituents
        clause_span_map: Dict[str, Tuple[int, int]] = {
            c_def.clause_id: (token_order_by_id[c_def.start_token_id], token_order_by_id[c_def.end_token_id])
            for c_def in clauses
        }
        constituent_ids_in_batch: Set[str] = {cst.constituent_id for cst in constituents}
        seen_const_keys: Set[Tuple[str, str, str, str, int]] = set()
        for cst in constituents:
            cst.validate_confidence()

            if cst.clause_id not in clause_ids_in_batch:
                raise SyntaxClauseNotFoundError(
                    f"Constituent '{cst.constituent_id}' references unknown clause '{cst.clause_id}'."
                )
            if cst.parent_constituent_id and cst.parent_constituent_id not in constituent_ids_in_batch:
                with self.engine.connect() as chk_conn:
                    chk_cur = chk_conn.cursor()
                    chk_cur.execute(
                        "SELECT 1 FROM syntactic_constituents WHERE constituent_id = ?;",
                        (cst.parent_constituent_id,),
                    )
                    if chk_cur.fetchone() is None:
                        raise SyntaxConstituentNotFoundError(
                            f"Constituent '{cst.constituent_id}' references nonexistent parent_constituent_id '{cst.parent_constituent_id}'."
                        )
            if cst.start_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Constituent start_token_id '{cst.start_token_id}' does not exist.")
            if cst.end_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Constituent end_token_id '{cst.end_token_id}' does not exist.")

            start_idx = token_order_by_id[cst.start_token_id]
            end_idx = token_order_by_id[cst.end_token_id]
            if start_idx > end_idx:
                raise SyntaxSpanValidationError(
                    f"Constituent '{cst.constituent_id}' has inverted token order: start {start_idx} > end {end_idx}."
                )

            # Check constituent containment within its clause span
            if cst.clause_id in clause_span_map:
                c_start, c_end = clause_span_map[cst.clause_id]
                if start_idx < c_start or end_idx > c_end:
                    raise SyntaxSpanValidationError(
                        f"Constituent '{cst.constituent_id}' span [{start_idx}, {end_idx}] exceeds clause '{cst.clause_id}' span [{c_start}, {c_end}]."
                    )

            if cst.head_token_id and cst.head_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Constituent head_token_id '{cst.head_token_id}' does not exist.")

            # Permit unary branching if constituent_type differs
            const_key = (cst.clause_id, cst.constituent_type.value, cst.start_token_id, cst.end_token_id, cst.parse_index)
            if const_key in seen_const_keys:
                raise DuplicateSyntaxError(
                    f"Duplicate constituent of type {cst.constituent_type.value} on clause '{cst.clause_id}' for span {cst.start_token_id}-{cst.end_token_id} (parse {cst.parse_index})."
                )
            seen_const_keys.add(const_key)

        # Step 5: Validate dependencies and cycle detection
        seen_dep_keys: Set[Tuple[str, str, int]] = set()
        for dep in dependencies:
            dep.validate_confidence()

            if dep.clause_id not in clause_ids_in_batch:
                raise SyntaxClauseNotFoundError(
                    f"Dependency relation '{dep.dependency_id}' references unknown clause '{dep.clause_id}'."
                )
            if dep.dependent_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Dependent token '{dep.dependent_token_id}' does not exist.")
            if dep.head_token_id and dep.head_token_id not in token_by_id:
                raise SyntaxTokenNotFoundError(f"Head token '{dep.head_token_id}' does not exist.")

            dep_key = (dep.clause_id, dep.dependent_token_id, dep.parse_index)
            if dep_key in seen_dep_keys:
                raise DuplicateSyntaxError(
                    f"Duplicate dependency relation for token '{dep.dependent_token_id}' in clause '{dep.clause_id}' (parse {dep.parse_index})."
                )
            seen_dep_keys.add(dep_key)

        # Enforce graph acyclicity per parse
        detect_dependency_cycles(dependencies)

        # Step 6: Generate deterministic Run ID and Hashes
        input_token_hashes = [hashlib.sha256(t.surface_form.encode("utf-8")).hexdigest()[:16] for t in raw_tokens]
        input_content_hash = hashlib.sha256(":".join(input_token_hashes).encode("utf-8")).hexdigest().lower()
        run_id = f"SRUN-{source_text_id[:16]}-{config_hash[:8]}-{input_content_hash[:8]}"

        output_hash = compute_syntax_output_hash(clauses, dependencies, constituents)

        # Step 7: Atomic Database Persistence
        def _execute_persistence(tx_conn: sqlite3.Connection) -> SyntaxResult:
            cur = tx_conn.cursor()

            # Check duplicate run
            cur.execute("SELECT run_id FROM syntax_runs WHERE run_id = ?;", (run_id,))
            if cur.fetchone() is not None:
                raise DuplicateSyntaxError(f"Syntax run '{run_id}' has already been registered.")

            # Record Provenance
            parent_prov_id = raw_tokens[0].provenance_id if raw_tokens[0].provenance_id else None
            if config.is_deterministic:
                prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id,
                    content=output_hash,
                    parent_provenance_id=parent_prov_id,
                    input_data={
                        "source_text_id": source_text_id,
                        "tokenization_id": tokenization_id,
                        "morphology_run_id": morphology_run_id,
                        "input_content_hash": input_content_hash,
                        "config_hash": config_hash,
                        "clause_count": len(clauses),
                        "dependency_count": len(dependencies),
                        "constituent_count": len(constituents),
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

            # Create Object Version
            ver_rec = self.version_mgr.create_version(
                object_id=run_id,
                object_type="syntax",
                content_hash=output_hash,
                provenance_id=prov_rec.provenance_id,
                created_by=agent,
                change_reason=ChangeReason.INITIAL_CREATION,
                status=VersionStatus.ACTIVE,
                metadata={
                    "source_text_id": source_text_id,
                    "tokenization_id": tokenization_id,
                    "morphology_run_id": morphology_run_id,
                    "configuration_hash": config_hash,
                    "is_deterministic": config.is_deterministic,
                },
                conn=tx_conn,
            )

            # Insert syntax_runs ledger entry
            cur.execute(
                """
                INSERT INTO syntax_runs (
                    run_id, source_text_id, tokenization_id, morphology_run_id,
                    version_id, provenance_id, analyzer_id, analyzer_version,
                    language, representation_type, syntax_model_type,
                    configuration_hash, input_content_hash, output_hash,
                    clause_count, dependency_count, constituent_count,
                    is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (
                    ?, ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?
                );
                """,
                (
                    run_id,
                    source_text_id,
                    tokenization_id,
                    morphology_run_id,
                    ver_rec.version_id,
                    prov_rec.provenance_id,
                    config.analyzer_id,
                    config.analyzer_version,
                    source_lang.value,
                    config.representation_type.value,
                    config.syntax_model_type.value,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    len(clauses),
                    len(dependencies),
                    len(constituents),
                    1 if config.is_deterministic else 0,
                    now_iso,
                    1,
                    json.dumps(config.to_dict()),
                ),
            )

            # Persist Clauses
            persisted_clauses: List[ClauseRecord] = []
            for c in clauses:
                clause_rec = ClauseRecord(
                    clause_id=c.clause_id,
                    run_id=run_id,
                    source_text_id=source_text_id,
                    version_id=ver_rec.version_id,
                    provenance_id=prov_rec.provenance_id,
                    clause_order=c.clause_order,
                    clause_type=c.clause_type,
                    start_token_id=c.start_token_id,
                    end_token_id=c.end_token_id,
                    raw_clause_string=c.raw_clause_string,
                    parent_clause_id=c.parent_clause_id,
                    relation_to_parent=c.relation_to_parent,
                    lead_conjunction_token_id=c.lead_conjunction_token_id,
                    passage_id=c.passage_id,
                    parse_index=c.parse_index,
                    is_preferred=c.is_preferred,
                    confidence_score=c.confidence_score,
                    confidence_level=c.confidence_level.value if c.confidence_level else None,
                    evidence_ref=c.evidence_ref,
                    is_immutable=True,
                    created_at=now_iso,
                    metadata_json=json.dumps(c.metadata) if c.metadata else None,
                )
                persisted_clauses.append(clause_rec)
                cur.execute(
                    """
                    INSERT INTO clauses (
                        clause_id, run_id, source_text_id, version_id, provenance_id, passage_id,
                        parent_clause_id, clause_order, clause_type, relation_to_parent,
                        start_token_id, end_token_id, lead_conjunction_token_id,
                        parse_index, is_preferred, confidence_score, confidence_level,
                        evidence_ref, raw_clause_string, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?, ?
                    );
                    """,
                    (
                        clause_rec.clause_id,
                        clause_rec.run_id,
                        clause_rec.source_text_id,
                        clause_rec.version_id,
                        clause_rec.provenance_id,
                        clause_rec.passage_id,
                        clause_rec.parent_clause_id,
                        clause_rec.clause_order,
                        clause_rec.clause_type.value,
                        clause_rec.relation_to_parent.value if clause_rec.relation_to_parent else None,
                        clause_rec.start_token_id,
                        clause_rec.end_token_id,
                        clause_rec.lead_conjunction_token_id,
                        clause_rec.parse_index,
                        1 if clause_rec.is_preferred else 0,
                        clause_rec.confidence_score,
                        clause_rec.confidence_level,
                        clause_rec.evidence_ref,
                        clause_rec.raw_clause_string,
                        clause_rec.created_at,
                        1,
                        clause_rec.metadata_json,
                    ),
                )

            # Persist Constituents
            persisted_constituents: List[SyntacticConstituentRecord] = []
            for k in constituents:
                cst_rec = SyntacticConstituentRecord(
                    constituent_id=k.constituent_id,
                    run_id=run_id,
                    clause_id=k.clause_id,
                    constituent_type=k.constituent_type,
                    start_token_id=k.start_token_id,
                    end_token_id=k.end_token_id,
                    parent_constituent_id=k.parent_constituent_id,
                    grammatical_role=k.grammatical_role,
                    head_token_id=k.head_token_id,
                    parse_index=k.parse_index,
                    is_preferred=k.is_preferred,
                    confidence_score=k.confidence_score,
                    confidence_level=k.confidence_level.value if k.confidence_level else None,
                    evidence_ref=k.evidence_ref,
                    is_immutable=True,
                    created_at=now_iso,
                    metadata_json=json.dumps(k.metadata) if k.metadata else None,
                )
                persisted_constituents.append(cst_rec)
                cur.execute(
                    """
                    INSERT INTO syntactic_constituents (
                        constituent_id, run_id, clause_id, parent_constituent_id,
                        constituent_type, grammatical_role, head_token_id,
                        start_token_id, end_token_id, parse_index, is_preferred,
                        confidence_score, confidence_level, evidence_ref,
                        created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?
                    );
                    """,
                    (
                        cst_rec.constituent_id,
                        cst_rec.run_id,
                        cst_rec.clause_id,
                        cst_rec.parent_constituent_id,
                        cst_rec.constituent_type.value,
                        cst_rec.grammatical_role.value if cst_rec.grammatical_role else None,
                        cst_rec.head_token_id,
                        cst_rec.start_token_id,
                        cst_rec.end_token_id,
                        cst_rec.parse_index,
                        1 if cst_rec.is_preferred else 0,
                        cst_rec.confidence_score,
                        cst_rec.confidence_level,
                        cst_rec.evidence_ref,
                        cst_rec.created_at,
                        1,
                        cst_rec.metadata_json,
                    ),
                )

            # Persist Dependencies
            persisted_dependencies: List[SyntaxDependencyRecord] = []
            token_dep_map: Dict[str, List[SyntaxDependencyRecord]] = {}
            for d in dependencies:
                dep_rec = SyntaxDependencyRecord(
                    dependency_id=d.dependency_id,
                    run_id=run_id,
                    clause_id=d.clause_id,
                    head_token_id=d.head_token_id,
                    dependent_token_id=d.dependent_token_id,
                    relation_type=d.relation_type,
                    language_specific_tag=d.language_specific_tag,
                    morphology_annotation_id=d.morphology_annotation_id,
                    parse_index=d.parse_index,
                    is_preferred=d.is_preferred,
                    confidence_score=d.confidence_score,
                    confidence_level=d.confidence_level.value if d.confidence_level else None,
                    evidence_ref=d.evidence_ref,
                    is_immutable=True,
                    created_at=now_iso,
                    metadata_json=json.dumps(d.metadata) if d.metadata else None,
                )
                persisted_dependencies.append(dep_rec)
                token_dep_map.setdefault(d.dependent_token_id, []).append(dep_rec)
                cur.execute(
                    """
                    INSERT INTO syntax_dependencies (
                        dependency_id, run_id, clause_id, head_token_id, dependent_token_id,
                        relation_type, language_specific_tag, morphology_annotation_id,
                        parse_index, is_preferred, confidence_score, confidence_level,
                        evidence_ref, created_at, is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, ?
                    );
                    """,
                    (
                        dep_rec.dependency_id,
                        dep_rec.run_id,
                        dep_rec.clause_id,
                        dep_rec.head_token_id,
                        dep_rec.dependent_token_id,
                        dep_rec.relation_type.value,
                        dep_rec.language_specific_tag,
                        dep_rec.morphology_annotation_id,
                        dep_rec.parse_index,
                        1 if dep_rec.is_preferred else 0,
                        dep_rec.confidence_score,
                        dep_rec.confidence_level,
                        dep_rec.evidence_ref,
                        dep_rec.created_at,
                        1,
                        dep_rec.metadata_json,
                    ),
                )

            run_rec = SyntaxRunRecord(
                run_id=run_id,
                source_text_id=source_text_id,
                tokenization_id=tokenization_id,
                morphology_run_id=morphology_run_id,
                version_id=ver_rec.version_id,
                provenance_id=prov_rec.provenance_id,
                analyzer_id=config.analyzer_id,
                analyzer_version=config.analyzer_version,
                language=source_lang,
                representation_type=config.representation_type,
                syntax_model_type=config.syntax_model_type,
                configuration_hash=config_hash,
                input_content_hash=input_content_hash,
                output_hash=output_hash,
                clause_count=len(persisted_clauses),
                dependency_count=len(persisted_dependencies),
                constituent_count=len(persisted_constituents),
                is_exact_reproducible=config.is_deterministic,
                created_at=now_iso,
                is_immutable=True,
                metadata_json=json.dumps(config.to_dict()),
            )

            return SyntaxResult(
                run=run_rec,
                clauses=persisted_clauses,
                dependencies=persisted_dependencies,
                constituents=persisted_constituents,
                token_dependencies_map=token_dep_map,
            )

        try:
            if conn is not None:
                return _execute_persistence(conn)
            with self.engine.transaction() as tx_conn:
                return _execute_persistence(tx_conn)
        except sqlite3.IntegrityError as ie:
            if "UNIQUE constraint failed" in str(ie) or "syntax_" in str(ie) or "clauses" in str(ie):
                raise DuplicateSyntaxError(f"Integrity violation in syntax persistence: {ie}") from ie
            raise

    # -------------------------------------------------------------------------
    # 2. QUERY OPERATIONS
    # -------------------------------------------------------------------------

    def get_syntax_run(
        self,
        run_id: str,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[SyntaxRunRecord]:
        """Fetch syntax run record by primary key."""
        def _get(c: sqlite3.Connection) -> Optional[SyntaxRunRecord]:
            cur = c.cursor()
            cur.execute("SELECT * FROM syntax_runs WHERE run_id = ?;", (run_id,))
            row = cur.fetchone()
            return SyntaxRunRecord.from_row(row) if row else None

        if conn is not None:
            return _get(conn)
        with self.engine.connect() as query_conn:
            return _get(query_conn)

    def get_clauses_for_run(
        self,
        run_id: str,
        is_preferred_only: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[ClauseRecord]:
        """List clause records for a syntax run ordered by clause_order and parse_index."""
        def _list(c: sqlite3.Connection) -> List[ClauseRecord]:
            cur = c.cursor()
            if is_preferred_only:
                cur.execute(
                    "SELECT * FROM clauses WHERE run_id = ? AND is_preferred = 1 ORDER BY clause_order ASC;",
                    (run_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM clauses WHERE run_id = ? ORDER BY clause_order ASC, parse_index ASC;",
                    (run_id,),
                )
            return [ClauseRecord.from_row(row) for row in cur.fetchall()]

        if conn is not None:
            return _list(conn)
        with self.engine.connect() as query_conn:
            return _list(query_conn)

    def get_constituents_for_clause(
        self,
        clause_id: str,
        is_preferred_only: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[SyntacticConstituentRecord]:
        """List constituents for a clause."""
        def _list(c: sqlite3.Connection) -> List[SyntacticConstituentRecord]:
            cur = c.cursor()
            if is_preferred_only:
                cur.execute(
                    "SELECT * FROM syntactic_constituents WHERE clause_id = ? AND is_preferred = 1 ORDER BY constituent_id ASC;",
                    (clause_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM syntactic_constituents WHERE clause_id = ? ORDER BY constituent_id ASC, parse_index ASC;",
                    (clause_id,),
                )
            return [SyntacticConstituentRecord.from_row(row) for row in cur.fetchall()]

        if conn is not None:
            return _list(conn)
        with self.engine.connect() as query_conn:
            return _list(query_conn)

    def get_dependencies_for_clause(
        self,
        clause_id: str,
        is_preferred_only: bool = False,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[SyntaxDependencyRecord]:
        """List dependency relations within a clause."""
        def _list(c: sqlite3.Connection) -> List[SyntaxDependencyRecord]:
            cur = c.cursor()
            if is_preferred_only:
                cur.execute(
                    "SELECT * FROM syntax_dependencies WHERE clause_id = ? AND is_preferred = 1 ORDER BY dependent_token_id ASC;",
                    (clause_id,),
                )
            else:
                cur.execute(
                    "SELECT * FROM syntax_dependencies WHERE clause_id = ? ORDER BY dependent_token_id ASC, parse_index ASC;",
                    (clause_id,),
                )
            return [SyntaxDependencyRecord.from_row(row) for row in cur.fetchall()]

        if conn is not None:
            return _list(conn)
        with self.engine.connect() as query_conn:
            return _list(query_conn)

    def get_dependencies_for_token(
        self,
        token_id: str,
        run_id: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[SyntaxDependencyRecord]:
        """List all dependency parses for a specific token."""
        def _list(c: sqlite3.Connection) -> List[SyntaxDependencyRecord]:
            cur = c.cursor()
            if run_id:
                cur.execute(
                    "SELECT * FROM syntax_dependencies WHERE dependent_token_id = ? AND run_id = ? ORDER BY parse_index ASC;",
                    (token_id, run_id),
                )
            else:
                cur.execute(
                    "SELECT * FROM syntax_dependencies WHERE dependent_token_id = ? ORDER BY created_at DESC, parse_index ASC;",
                    (token_id,),
                )
            return [SyntaxDependencyRecord.from_row(row) for row in cur.fetchall()]

        if conn is not None:
            return _list(conn)
        with self.engine.connect() as query_conn:
            return _list(query_conn)

    # -------------------------------------------------------------------------
    # 3. REANALYSIS & LINEAGE EVOLUTION
    # -------------------------------------------------------------------------

    def reanalyze(
        self,
        source_text_id: str,
        clauses: Sequence[ClauseDefinition],
        dependencies: Sequence[DependencyRelationDefinition],
        constituents: Optional[Sequence[ConstituentDefinition]] = None,
        morphology_run_id: Optional[str] = None,
        new_config: Optional[SyntaxAnalyzerConfig] = None,
        agent: str = "polya-syntax-engine",
    ) -> SyntaxResult:
        """
        Produce a new versioned syntax run that supersedes the prior active syntax run
        for the given source text without modifying historical records.
        """
        new_config = new_config or SyntaxAnalyzerConfig()

        # Identify prior active syntax run
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, version_id FROM syntax_runs
                WHERE source_text_id = ? AND representation_type = ? AND syntax_model_type = ?
                ORDER BY created_at DESC;
                """,
                (source_text_id, new_config.representation_type.value, new_config.syntax_model_type.value),
            )
            rows = cur.fetchall()

        prior_run_id = rows[0][0] if rows else None
        prior_version_id = rows[0][1] if rows else None

        # Execute new syntax analysis
        new_result = self.record_syntax_analysis(
            source_text_id=source_text_id,
            clauses=clauses,
            dependencies=dependencies,
            constituents=constituents,
            morphology_run_id=morphology_run_id,
            config=new_config,
            agent=agent,
        )

        # Supersede prior version if one existed
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
