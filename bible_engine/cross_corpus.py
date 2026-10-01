"""
Task 4.1 Pure Domain Logic: Cross-Corpus Calibration Engine.
Specification: Architecture Revision V4 — FROZEN.

Enforces:
  1. Frozen / immutable dataclasses.
  2. Pure deterministic behavior.
  3. No direct DB writes from domain layer.
  4. No certificate issuance (owned exclusively by Task 4.0).
  5. No confidence calculation, multiplication, penalty, boost, or aggregate confidence.
  6. Confidence remains owned exclusively by evidence_ledger via relational FK.
  7. Exact 7 canonical relationship values:
     PARALLEL, ANALOGOUS, DISTINCT, CONTRADICTORY, ORTHOGONAL_TENSION, INCOMMENSURABLE, UNKNOWN.
     Explicitly rejects: CONVERGENT, DIVERGENT, ASYMMETRICAL_TENSION, ORTHOGONAL.
  8. Categorical boundary findings only:
     Temporal boundary, semantic boundary, identity/referential boundary.
     No numerical scoring. No confidence adjustment.
  9. Deterministic canonical comparison hashing & calibration identity calculation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.errors import (
    CrossCorpusBoundaryViolationError,
    CrossCorpusDeterminismError,
    InvalidCrossCorpusOntologyError,
)


# =============================================================================
# CANONICAL ONTOLOGY ENUMS
# =============================================================================

class CrossCorpusRelationshipType(str, Enum):
    """
    Exact 7 canonical cross-corpus relationship types.
    Do NOT introduce CONVERGENT, DIVERGENT, ASYMMETRICAL_TENSION, ORTHOGONAL.
    """
    PARALLEL = "PARALLEL"
    ANALOGOUS = "ANALOGOUS"
    DISTINCT = "DISTINCT"
    CONTRADICTORY = "CONTRADICTORY"
    ORTHOGONAL_TENSION = "ORTHOGONAL_TENSION"
    INCOMMENSURABLE = "INCOMMENSURABLE"
    UNKNOWN = "UNKNOWN"


FORBIDDEN_RELATIONSHIPS: Set[str] = {
    "CONVERGENT",
    "DIVERGENT",
    "ASYMMETRICAL_TENSION",
    "ORTHOGONAL",
}


class TemporalBoundary(str, Enum):
    """Categorical temporal boundaries between source and target text/claim."""
    ANACHRONISTIC = "ANACHRONISTIC"
    CONTEMPORANEOUS = "CONTEMPORANEOUS"
    ANTECEDENT = "ANTECEDENT"
    SUBSEQUENT = "SUBSEQUENT"
    INDETERMINATE = "INDETERMINATE"


class SemanticBoundary(str, Enum):
    """Categorical semantic field boundaries."""
    IDENTICAL_SEMANTIC_FIELD = "IDENTICAL_SEMANTIC_FIELD"
    OVERLAPPING_RANGE = "OVERLAPPING_RANGE"
    DIVERGENT_SENSE = "DIVERGENT_SENSE"
    RADICAL_DISCONTINUITY = "RADICAL_DISCONTINUITY"
    ASYMMETRIC_MAPPING = "ASYMMETRIC_MAPPING"
    INDETERMINATE = "INDETERMINATE"


class IdentityBoundary(str, Enum):
    """Categorical referential/identity boundaries."""
    ONTOLOGICAL_DISTINCTION = "ONTOLOGICAL_DISTINCTION"
    METAPHORICAL_ALIGNMENT = "METAPHORICAL_ALIGNMENT"
    FUNCTIONAL_EQUIVALENCE = "FUNCTIONAL_EQUIVALENCE"
    STRICT_ONTOLOGICAL_IDENTITY = "STRICT_ONTOLOGICAL_IDENTITY"
    CATEGORY_CONFUSION = "CATEGORY_CONFUSION"
    INDETERMINATE = "INDETERMINATE"


class SupportingEvidenceRole(str, Enum):
    """Relevance role of supporting evidence in comparison."""
    PRIMARY_WARRANT = "PRIMARY_WARRANT"
    CORROBORATING = "CORROBORATING"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    CONTEXTUAL_BOUNDARY = "CONTEXTUAL_BOUNDARY"
    HISTORICAL_WITNESS = "HISTORICAL_WITNESS"


# =============================================================================
# PURE IMMUTABLE DOMAIN MODELS
# =============================================================================

@dataclass(frozen=True)
class BoundaryFindings:
    """Categorical boundary findings only. No numerical scores or adjustments."""
    temporal_boundary: TemporalBoundary = TemporalBoundary.INDETERMINATE
    semantic_boundary: SemanticBoundary = SemanticBoundary.INDETERMINATE
    identity_boundary: IdentityBoundary = IdentityBoundary.INDETERMINATE

    def to_canonical_dict(self) -> Dict[str, str]:
        return {
            "identity_boundary": self.identity_boundary.value,
            "semantic_boundary": self.semantic_boundary.value,
            "temporal_boundary": self.temporal_boundary.value,
        }


@dataclass(frozen=True)
class SupportingEvidenceLink:
    """Immutable link to an evidence item in evidence_ledger."""
    evidence_id: str
    relevance_role: SupportingEvidenceRole

    def to_canonical_dict(self) -> Dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "relevance_role": self.relevance_role.value,
        }


@dataclass(frozen=True)
class CrossCorpusComparison:
    """
    Immutable cross-corpus comparison candidate / record.
    Adheres strictly to V4 Contract:
    - No confidence score, calibrated confidence, similarity score, weight, multiplier, penalty, or boost.
    - Confidence remains owned exclusively by evidence_ledger via primary_evidence_id or supporting evidence.
    """
    source_corpus: str
    source_target_type: str
    source_target_id: str
    target_corpus: str
    target_target_type: str
    target_target_id: str
    comparison_dimension: str
    relationship_type: CrossCorpusRelationshipType
    boundary_findings: BoundaryFindings
    epistemic_justification: str
    supporting_evidence: Tuple[SupportingEvidenceLink, ...] = field(default_factory=tuple)
    primary_evidence_id: Optional[str] = None
    provenance_id: Optional[str] = None
    version_id: Optional[str] = None
    comparison_id: Optional[str] = None
    calibration_run_id: Optional[str] = None

    def __post_init__(self) -> None:
        # Validate relationship type is canonical
        val = (
            self.relationship_type.value
            if isinstance(self.relationship_type, CrossCorpusRelationshipType)
            else str(self.relationship_type)
        )
        if val in FORBIDDEN_RELATIONSHIPS:
            raise InvalidCrossCorpusOntologyError(
                f"Forbidden relationship type '{val}' cannot be used. Canonical ontology strictly requires one of "
                f"{[e.value for e in CrossCorpusRelationshipType]}."
            )
        if val not in [e.value for e in CrossCorpusRelationshipType]:
            raise InvalidCrossCorpusOntologyError(
                f"Unknown relationship type '{val}'. Must be one of {[e.value for e in CrossCorpusRelationshipType]}."
            )

    def compute_canonical_hash(
        self,
        configuration_hash: str = "default_config",
        engine_version: str = "4.1.0",
        schema_version: str = "024",
    ) -> str:
        """
        Compute deterministic SHA-256 canonical comparison hash.
        Includes all semantically relevant inputs:
        - source target type & ID
        - target target type & ID
        - comparison dimension
        - relationship type
        - boundary findings
        - sorted supporting evidence IDs and roles
        - primary evidence ID
        - epistemic justification
        - configuration hash
        - engine version
        - schema version
        Does NOT depend on timestamp, created_at, random UUID, or insertion order.
        """
        sorted_ev = sorted(
            [e.to_canonical_dict() for e in self.supporting_evidence],
            key=lambda x: (x["evidence_id"], x["relevance_role"]),
        )

        payload = {
            "boundary_findings": self.boundary_findings.to_canonical_dict(),
            "comparison_dimension": self.comparison_dimension,
            "configuration_hash": configuration_hash,
            "engine_version": engine_version,
            "epistemic_justification": self.epistemic_justification,
            "primary_evidence_id": self.primary_evidence_id or "",
            "relationship_type": self.relationship_type.value,
            "schema_version": schema_version,
            "source_corpus": self.source_corpus,
            "source_target_id": self.source_target_id,
            "source_target_type": self.source_target_type,
            "supporting_evidence": sorted_ev,
            "target_corpus": self.target_corpus,
            "target_target_id": self.target_target_id,
            "target_target_type": self.target_target_type,
        }
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class CrossCorpusCalibrationRun:
    """
    Immutable Cross-Corpus Calibration Run domain record.
    """
    calibration_identity: str
    input_content_hash: str
    configuration_hash: str
    output_hash: str
    engine_version: str
    schema_version: str
    source_corpus: str
    target_corpus: str
    total_comparisons: int
    provenance_id: str
    version_id: str
    calibration_run_id: str
    comparisons: Tuple[CrossCorpusComparison, ...] = field(default_factory=tuple)


# =============================================================================
# DETERMINISTIC DOMAIN FUNCTIONS
# =============================================================================

def compute_calibration_identity(
    input_content_hash: str,
    configuration_hash: str,
    engine_version: str = "4.1.0",
    schema_version: str = "024",
) -> str:
    """
    Deterministic identity for a calibration run:
    SHA-256(input_content_hash:configuration_hash:engine_version:schema_version)
    """
    identity_str = f"{input_content_hash}:{configuration_hash}:{engine_version}:{schema_version}"
    return hashlib.sha256(identity_str.encode("utf-8")).hexdigest().lower()


def compute_run_input_content_hash(
    source_corpus: str,
    target_corpus: str,
    comparisons: Sequence[CrossCorpusComparison],
    configuration_hash: str = "default_config",
    engine_version: str = "4.1.0",
    schema_version: str = "024",
) -> str:
    """
    Deterministic input content hash for calibration run.
    Aggregates sorted comparison canonical hashes.
    """
    comp_hashes = sorted([
        c.compute_canonical_hash(
            configuration_hash=configuration_hash,
            engine_version=engine_version,
            schema_version=schema_version,
        )
        for c in comparisons
    ])

    payload = {
        "comparison_hashes": comp_hashes,
        "source_corpus": source_corpus,
        "target_corpus": target_corpus,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()


def compute_run_output_hash(
    calibration_identity: str,
    comparisons: Sequence[CrossCorpusComparison],
    configuration_hash: str = "default_config",
    engine_version: str = "4.1.0",
    schema_version: str = "024",
) -> str:
    """
    Deterministic output content hash for calibration run.
    """
    comp_hashes = sorted([
        c.compute_canonical_hash(
            configuration_hash=configuration_hash,
            engine_version=engine_version,
            schema_version=schema_version,
        )
        for c in comparisons
    ])
    payload = {
        "calibration_identity": calibration_identity,
        "comparison_hashes": comp_hashes,
        "total": len(comp_hashes),
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()
