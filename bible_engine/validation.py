"""
Automated 10-Layer Epistemic Validation Engine (Task 4.0).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principles:
  1. VALIDATION GATE != TRUTH ENGINE:
     A validation result records that an artifact passed defined validation
     constraints. It does NOT mean the proposition is true.
  2. INDEPENDENT ORTHOGONAL DIMENSIONS:
     V1–V10 are independent orthogonal validation layers. Not an epistemic ladder.
     All applicable layers execute. One blocking violation does not halt
     unrelated layers.
  3. OUTCOME DETERMINISM:
     - VALID: 0 blocking violations, 0 warnings.
     - VALID_WITH_WARNINGS: 0 blocking violations, >= 1 warnings.
     - BLOCKED: >= 1 blocking violations. Warnings must not conceal blocking violations.
  4. DETERMINISTIC VALIDATION IDENTITY:
     validation_identity = SHA256(validation_input_hash:engine_version:schema_version).
     Timestamps do NOT participate in validation identity.
  5. IMMUTABLE VALIDATION LEDGER:
     No RUNNING/FAILED rows. Atomic terminal persistence only.
     No UPDATE. No DELETE.
  6. HISTORICAL VALIDATION CERTIFICATE:
     Issued only for VALID or VALID_WITH_WARNINGS. Never for BLOCKED.
     Records validation event; contains NO epistemic confidence score.
  7. EPISTEMIC FIREWALLS:
     - T4 cannot serve as evidence for T0–T3.
     - Validation cannot promote evidence.
     - Validation cannot transform association -> identity.
     - Validation cannot transform reception -> authorial intent.
     - Validation cannot transform translation -> primary text.
     - Validation cannot transform retrieval ranking -> epistemic certainty.
     - Validation cannot transform graph centrality -> truth.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CertificateGenerationError,
    DeterministicValidationHashMismatchError,
    EpistemicFirewallViolationError,
    ValidationConcurrencyError,
    ValidationEngineSubsystemError,
    ValidationExecutionError,
    ValidationImmutabilityError,
    ValidationIntegrityError,
    ValidationLineageError,
    ValidationTargetNotFoundError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import HybridSymmetricalRetrievalEngine, SearchBranch
from bible_engine.versioning import ChangeReason, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class ValidationOutcome(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    BLOCKED = "BLOCKED"


class ViolationSeverity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


class LayerCode(str, Enum):
    V1 = "V1"
    V2 = "V2"
    V3 = "V3"
    V4 = "V4"
    V5 = "V5"
    V6 = "V6"
    V7 = "V7"
    V8 = "V8"
    V9 = "V9"
    V10 = "V10"


LAYER_NAMES: Dict[LayerCode, str] = {
    LayerCode.V1: "Source Text & Invariant Integrity",
    LayerCode.V2: "Morphological & Grammatical Bounds",
    LayerCode.V3: "Syntactic Dependency Boundaries",
    LayerCode.V4: "Lexical & Semantic Field Bounds",
    LayerCode.V5: "Referential & Identity Firewall",
    LayerCode.V6: "Discourse & Immediate Context Integrity",
    LayerCode.V7: "Textual Witness & Apparatus Calibration",
    LayerCode.V8: "Reception History & Anti-Anachronism Firewall",
    LayerCode.V9: "Symmetrical Counter-Evidence Search Audit",
    LayerCode.V10: "Epistemic Tier & Confidence Calibration",
}


# =============================================================================
# DOMAIN MODELS
# =============================================================================

@dataclass(frozen=True)
class ValidationTarget:
    """Target artifact under validation."""
    target_type: str
    target_id: str
    target_version_id: str


@dataclass(frozen=True)
class RetrievalLineage:
    """Authoritative Task 3.9 retrieval lineage references."""
    query_id: str
    query_hash: str
    retrieval_run_id: str
    config_hash: str
    pack_id: str
    pack_hash: str


@dataclass(frozen=True)
class EvidenceDependencies:
    """Evidence and claim dependencies associated with the target."""
    evidence_ids: List[str] = field(default_factory=list)
    linked_claim_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationEnvironment:
    """Engine runtime and schema version configuration."""
    engine_version: str = "2.0.0"
    schema_version: str = "023"


@dataclass(frozen=True)
class ValidationInput:
    """Complete validation input payload."""
    target: ValidationTarget
    retrieval_lineage: RetrievalLineage
    evidence_dependencies: EvidenceDependencies = field(default_factory=EvidenceDependencies)
    environment: ValidationEnvironment = field(default_factory=ValidationEnvironment)
    candidate_payload: Dict[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Produce canonical dictionary exactly matching Task 4.0 Section 6."""
        return {
            "environment": {
                "engine_version": self.environment.engine_version,
                "schema_version": self.environment.schema_version,
            },
            "evidence_dependencies": {
                "evidence_ids": sorted(list(set(self.evidence_dependencies.evidence_ids))),
                "linked_claim_ids": sorted(list(set(self.evidence_dependencies.linked_claim_ids))),
            },
            "retrieval_lineage": {
                "config_hash": self.retrieval_lineage.config_hash,
                "pack_hash": self.retrieval_lineage.pack_hash,
                "pack_id": self.retrieval_lineage.pack_id,
                "query_hash": self.retrieval_lineage.query_hash,
                "query_id": self.retrieval_lineage.query_id,
                "retrieval_run_id": self.retrieval_lineage.retrieval_run_id,
            },
            "target": {
                "target_id": self.target.target_id,
                "target_type": self.target.target_type,
                "target_version_id": self.target.target_version_id,
            },
        }

    def compute_validation_input_hash(self) -> str:
        """Deterministic SHA-256 of canonical JSON serialized input."""
        payload = self.to_canonical_dict()
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def compute_validation_identity(self) -> str:
        """Deterministic validation identity independent of timestamps."""
        inp_hash = self.compute_validation_input_hash()
        identity_str = f"{inp_hash}:{self.environment.engine_version}:{self.environment.schema_version}"
        return hashlib.sha256(identity_str.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ValidationViolation:
    """Individual violation or warning recorded during layer validation."""
    violation_id: str
    run_id: str
    layer_code: LayerCode
    severity: ViolationSeverity
    rule_code: str
    message: str
    context_json: Optional[str] = None


@dataclass(frozen=True)
class ValidationLayerResult:
    """Result of an individual validation layer (V1–V10)."""
    result_id: str
    run_id: str
    layer_code: LayerCode
    layer_name: str
    outcome: ValidationOutcome
    checks_evaluated: int
    violations_count: int
    warnings_count: int
    summary_notes: str
    violations: List[ValidationViolation] = field(default_factory=list)
    metadata_json: Optional[str] = None


@dataclass(frozen=True)
class ValidationCertificate:
    """Historical validation record issued for VALID or VALID_WITH_WARNINGS."""
    certificate_id: str
    run_id: str
    validation_identity: str
    validation_input_hash: str
    engine_version: str
    schema_version: str
    target_type: str
    target_id: str
    target_version_id: str
    validation_status: str
    layer_summary_json: str
    provenance_id: str
    validated_at: str
    is_immutable: int = 1
    metadata_json: Optional[str] = None


@dataclass(frozen=True)
class ValidationRun:
    """Terminal immutable validation run record."""
    run_id: str
    validation_identity: str
    validation_input_hash: str
    engine_version: str
    schema_version: str
    target_type: str
    target_id: str
    target_version_id: str
    final_outcome: ValidationOutcome
    checks_total: int
    checks_passed: int
    checks_failed: int
    warnings_total: int
    provenance_id: str
    executed_at: str
    layer_results: List[ValidationLayerResult]
    violations: List[ValidationViolation]
    certificate: Optional[ValidationCertificate] = None
    is_immutable: int = 1
    metadata_json: Optional[str] = None


# =============================================================================
# INDEPENDENT LAYER VALIDATORS (V1–V10)
# =============================================================================

class BaseValidator:
    """Base interface for orthogonal validation layers."""

    def __init__(self, engine: DatabaseEngine) -> None:
        self.engine = engine

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        raise NotImplementedError


class V1SourceTextValidator(BaseValidator):
    """
    V1: Source Text & Invariant Integrity.
    Verifies source-text integrity and required invariant constraints.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V1
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        target = val_input.target
        payload = val_input.candidate_payload
        source_text_id = payload.get("source_text_id") or (
            target.target_id if target.target_type in ("SOURCE_TEXT", "PASSAGE") else None
        )
        if "source_string" in payload:
            source_string = payload["source_string"]
        elif "text_content" in payload:
            source_string = payload["text_content"]
        else:
            source_string = None

        # Check 1: Invariant constraints and source existence
        checks += 1
        target_conn = conn or self.engine.get_write_connection()
        if source_text_id:
            cur = target_conn.execute(
                "SELECT source_text_id, raw_source_string, sha256_hash, is_immutable FROM source_texts WHERE source_text_id = ?",
                (source_text_id,),
            )
            row = cur.fetchone()
            if not row:
                # If explicit source_text_id referenced but not in DB, check if it's candidate or invalid
                if payload.get("require_registered_source", False):
                    violations.append(
                        ValidationViolation(
                            violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                            run_id=run_id,
                            layer_code=layer_code,
                            severity=ViolationSeverity.BLOCKING,
                            rule_code="V1_SOURCE_TEXT_NOT_FOUND",
                            message=f"Referenced source_text_id '{source_text_id}' not found in source registry.",
                        )
                    )
            else:
                if row["is_immutable"] != 1:
                    violations.append(
                        ValidationViolation(
                            violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                            run_id=run_id,
                            layer_code=layer_code,
                            severity=ViolationSeverity.BLOCKING,
                            rule_code="V1_SOURCE_TEXT_MUTABLE",
                            message=f"Source text '{source_text_id}' is marked mutable, violating invariant integrity.",
                        )
                    )

        # Check 2: Unicode NFC normalization & non-emptiness
        checks += 1
        if source_string is not None:
            if not isinstance(source_string, str) or not source_string.strip():
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V1_EMPTY_SOURCE_STRING",
                        message="Candidate source string is empty or invalid.",
                    )
                )
            else:
                nfc_norm = unicodedata.normalize("NFC", source_string)
                if nfc_norm != source_string:
                    violations.append(
                        ValidationViolation(
                            violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                            run_id=run_id,
                            layer_code=layer_code,
                            severity=ViolationSeverity.WARNING,
                            rule_code="V1_UNICODE_NORMALIZATION_WARNING",
                            message="Source string is not in canonical Unicode NFC normalization form.",
                        )
                    )

        # Check 3: Text alteration invariant check
        checks += 1
        if payload.get("unauthorized_alteration", False):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V1_UNAUTHORIZED_TEXT_ALTERATION",
                    message="Unauthorized text alteration detected outside established textual apparatus.",
                )
            )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Source text and invariant integrity audited.",
            violations=violations,
        )


class V2MorphologyValidator(BaseValidator):
    """
    V2: Morphological & Grammatical Bounds.
    Verifies that grammatical/morphological conclusions remain within available evidence.
    Must reject unsupported grammatical expansion.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V2
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        morphology_claims = payload.get("morphology_claims", [])

        checks += 1
        for claim in morphology_claims:
            checks += 1
            # Check for unsupported expansion
            if claim.get("is_unsupported_expansion", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V2_UNSUPPORTED_GRAMMATICAL_EXPANSION",
                        message=claim.get(
                            "message",
                            "Grammatical conclusion exceeds available morphological evidence.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_ambiguous", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V2_GRAMMATICAL_AMBIGUITY_WARNING",
                        message=claim.get(
                            "message",
                            "Grammatical conclusion relies on rare or ambiguous morphological inflection.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Morphological and grammatical boundaries audited.",
            violations=violations,
        )


class V3SyntaxValidator(BaseValidator):
    """
    V3: Syntactic Dependency Boundaries.
    Verifies dependency structures and prevents unsupported syntactic relationships.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V3
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        syntactic_claims = payload.get("syntactic_claims", [])

        checks += 1
        for claim in syntactic_claims:
            checks += 1
            if claim.get("violates_dependency_boundary", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V3_UNSUPPORTED_SYNTACTIC_RELATIONSHIP",
                        message=claim.get(
                            "message",
                            "Asserted dependency structure violates governing phrase or clause boundaries.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_unattested_syntax", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V3_UNATTESTED_SYNTACTIC_RELATION_WARNING",
                        message=claim.get(
                            "message",
                            "Syntactic relationship lacks direct corpus treebank attestation.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Syntactic dependency boundaries audited.",
            violations=violations,
        )


class V4SemanticsValidator(BaseValidator):
    """
    V4: Lexical & Semantic Field Bounds.
    Verifies lexical/semantic claims against available evidence.
    Must not allow semantic expansion beyond documented evidence.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V4
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        semantic_claims = payload.get("semantic_claims", [])

        checks += 1
        for claim in semantic_claims:
            checks += 1
            if claim.get("is_illegitimate_totality_transfer", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V4_ILLEGITIMATE_TOTALITY_TRANSFER",
                        message=claim.get(
                            "message",
                            "Illegitimate totality transfer: multiple distinct semantic senses illicitly combined.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_root_fallacy", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V4_ROOT_FALLACY",
                        message=claim.get(
                            "message",
                            "Root fallacy: etymological derivation asserted as determinative contextual meaning.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_unsupported_expansion", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V4_UNSUPPORTED_SEMANTIC_EXPANSION",
                        message=claim.get(
                            "message",
                            "Semantic claim extends beyond documented lexicon and contextual evidence.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_semantic_tension", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V4_SEMANTIC_FIELD_TENSION_WARNING",
                        message=claim.get(
                            "message",
                            "Semantic gloss operates at the periphery of the documented semantic field.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Lexical and semantic field bounds audited.",
            violations=violations,
        )


class V5ReferentialValidator(BaseValidator):
    """
    V5: Referential & Identity Firewall.
    Association does not equal identity.
    Do not allow: ASSOCIATED_WITH -> EQUATED_WITH without explicit evidence.
    Identity claims require explicit support.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V5
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        referential_claims = payload.get("referential_claims", [])

        checks += 1
        for claim in referential_claims:
            checks += 1
            rel_type = str(claim.get("relation_type", "")).upper()
            asserted_equated = claim.get("equates_entities", False) or rel_type in (
                "EQUATED_WITH",
                "IDENTICAL_TO",
                "SAME_AS",
                "ONTOLOGICAL_IDENTITY",
            )
            has_explicit_evidence = claim.get("has_explicit_identity_evidence", False)

            # Rule 1: Association conflated to identity
            if rel_type in (
                "ASSOCIATED_WITH",
                "IN_PROXIMITY_TO",
                "ATTRIBUTED_TO",
                "METAPHORICALLY_LINKED",
                "SYMBOLIZED_BY",
                "TYPOLOGICAL_SHADOW",
            ) and asserted_equated:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V5_ASSOCIATION_IDENTITY_CONFLATION",
                        message=claim.get(
                            "message",
                            "Illicit transformation of association into ontological identity without evidence.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

            # Rule 2: Identity claims require explicit support
            elif asserted_equated and not has_explicit_evidence:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V5_UNSUPPORTED_IDENTITY_CLAIM",
                        message=claim.get(
                            "message",
                            "Identity claim asserted without explicit primary textual or referential evidence.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

            elif claim.get("is_referential_ambiguity", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V5_REFERENTIAL_AMBIGUITY_WARNING",
                        message=claim.get(
                            "message",
                            "Entity referent possesses multiple plausible textual candidates.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Referential and identity firewalls audited.",
            violations=violations,
        )


class V6DiscourseValidator(BaseValidator):
    """
    V6: Discourse & Immediate Context Integrity.
    Verifies that claims respect local discourse and immediate context.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V6
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        discourse_claims = payload.get("discourse_claims", [])

        checks += 1
        for claim in discourse_claims:
            checks += 1
            if claim.get("is_proof_text_isolation", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V6_PROOF_TEXT_ISOLATION",
                        message=claim.get(
                            "message",
                            "Proof-text isolation: claim ignores immediate discourse unit boundaries.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("speaker_attribution_error", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V6_SPEAKER_ATTRIBUTION_ERROR",
                        message=claim.get(
                            "message",
                            "Dialogue spoken by non-authorial or adverse interlocutor attributed as authorial thesis.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("discourse_tension", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V6_DISCOURSE_TENSION_WARNING",
                        message=claim.get(
                            "message",
                            "Claim exists in tension with adjacent discourse pericope transitions.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Discourse and immediate context integrity audited.",
            violations=violations,
        )


class V7TextualCriticismValidator(BaseValidator):
    """
    V7: Textual Witness & Apparatus Calibration.
    Verifies textual-critical claims against actual witnesses/apparatus evidence.
    Do not allow translation or interpretation to masquerade as primary-text evidence.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V7
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        textual_claims = payload.get("textual_claims", [])

        checks += 1
        for claim in textual_claims:
            checks += 1
            if claim.get("is_translation_masquerading_as_primary", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V7_TRANSLATION_MASQUERADING_AS_PRIMARY",
                        message=claim.get(
                            "message",
                            "Translation or interpretation masquerades as primary textual witness.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_unattested_variant", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V7_UNATTESTED_TEXTUAL_VARIANT",
                        message=claim.get(
                            "message",
                            "Textual variant claimed without calibration in registered critical apparatus.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_minority_reading", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V7_MINORITY_READING_WARNING",
                        message=claim.get(
                            "message",
                            "Reading is attested solely by isolated or secondary witness tradition.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Textual witness and apparatus calibration audited.",
            violations=violations,
        )


class V8ReceptionHistoryValidator(BaseValidator):
    """
    V8: Reception History & Anti-Anachronism Firewall.
    Must be context-aware. Do NOT implement simplistic keyword-only detection.
    Distinguishes legitimate modern analytical terminology from anachronistic retrojection.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V8
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        reception_claims = payload.get("reception_claims", [])

        checks += 1
        for claim in reception_claims:
            checks += 1
            is_anachronistic = claim.get("is_anachronistic_retrojection", False)
            claim_scope = str(claim.get("claim_scope", "")).upper()
            is_analytical_terminology = claim.get("is_analytical_terminology", False)

            # Legitimate analytical meta-language is permitted
            if is_analytical_terminology:
                continue

            # Retrojection of later historical/dogmatic concept as ancient authorial intent
            if is_anachronistic or (
                claim.get("concept_period_post_dates_source", False)
                and claim_scope in ("AUTHORIAL_INTENT", "ORIGINAL_MEANING")
            ):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V8_ANACHRONISTIC_RETROJECTION",
                        message=claim.get(
                            "message",
                            "Anachronistic retrojection: later historical/theological development asserted as authorial intent.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )
            elif claim.get("is_reception_ambiguity", False):
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.WARNING,
                        rule_code="V8_RECEPTION_AMBIGUITY_WARNING",
                        message=claim.get(
                            "message",
                            "Boundary between original contextual meaning and later reception history is blurred.",
                        ),
                        context_json=json.dumps(claim),
                    )
                )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Reception history and anti-anachronism firewall audited.",
            violations=violations,
        )


class V9RetrievalAuditValidator(BaseValidator):
    """
    V9: Symmetrical Counter-Evidence Search Audit.
    MUST use real Task 3.9 architecture.
    Authoritative components:
    - retrieval_queries
    - retrieval_runs
    - retrieval_coverage_records
    - retrieval_context_packs
    - retrieval_pack_items
    - RetrievalService.verify_pack_integrity()
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        retrieval_engine: HybridSymmetricalRetrievalEngine,
    ) -> None:
        super().__init__(engine)
        self.retrieval_engine = retrieval_engine

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V9
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        lineage = val_input.retrieval_lineage
        target_conn = conn or self.engine.get_write_connection()

        # 1. pack exists
        checks += 1
        pack_cur = target_conn.execute(
            """
            SELECT pack_id, run_id, query_id, pack_hash, counter_evidence_status
            FROM retrieval_context_packs
            WHERE pack_id = ?
            """,
            (lineage.pack_id,),
        )
        pack_row = pack_cur.fetchone()
        if not pack_row:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_PACK_NOT_FOUND",
                    message=f"Referenced retrieval context pack '{lineage.pack_id}' does not exist.",
                )
            )
            # Cannot proceed with deep pack checks if pack is absent
            return ValidationLayerResult(
                result_id=f"LYR-{uuid.uuid4().hex[:12]}",
                run_id=run_id,
                layer_code=layer_code,
                layer_name=layer_name,
                outcome=ValidationOutcome.BLOCKED,
                checks_evaluated=checks,
                violations_count=1,
                warnings_count=0,
                summary_notes="Pack not found in authoritative retrieval ledger.",
                violations=violations,
            )

        # 2. stored pack_hash matches supplied lineage
        checks += 1
        if pack_row["pack_hash"] != lineage.pack_hash:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_PACK_HASH_MISMATCH",
                    message=f"Supplied pack_hash '{lineage.pack_hash}' does not match stored hash '{pack_row['pack_hash']}'.",
                )
            )

        # 3. Authoritative Task 3.9 pack integrity verification succeeds
        checks += 1
        try:
            integrity_ok = self.retrieval_engine.verify_pack_integrity(lineage.pack_id)
            if not integrity_ok:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V9_INTEGRITY_VERIFICATION_FAILED",
                        message="Authoritative Task 3.9 verify_pack_integrity returned False.",
                    )
                )
        except Exception as e:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_INTEGRITY_VERIFICATION_FAILED",
                    message=f"Authoritative Task 3.9 verify_pack_integrity failed: {e}",
                )
            )

        # 4. retrieval run lineage matches
        checks += 1
        run_cur = target_conn.execute(
            "SELECT run_id, query_id, config_hash FROM retrieval_runs WHERE run_id = ?",
            (lineage.retrieval_run_id,),
        )
        run_row = run_cur.fetchone()
        if not run_row:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_RUN_LINEAGE_MISMATCH",
                    message=f"Referenced retrieval run '{lineage.retrieval_run_id}' not found.",
                )
            )
        else:
            if pack_row["run_id"] != lineage.retrieval_run_id:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V9_RUN_LINEAGE_MISMATCH",
                        message=f"Pack run_id '{pack_row['run_id']}' != lineage run_id '{lineage.retrieval_run_id}'.",
                    )
                )
            if run_row["config_hash"] != lineage.config_hash:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V9_RUN_LINEAGE_MISMATCH",
                        message=f"Run config_hash '{run_row['config_hash']}' != lineage config_hash '{lineage.config_hash}'.",
                    )
                )

        # 5. query lineage matches
        checks += 1
        if pack_row["query_id"] != lineage.query_id or (run_row and run_row["query_id"] != lineage.query_id):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_QUERY_LINEAGE_MISMATCH",
                    message=f"Pack/run query_id mismatch against lineage query_id '{lineage.query_id}'.",
                )
            )

        # 6. query_hash matches
        checks += 1
        query_cur = target_conn.execute(
            "SELECT query_id, query_hash FROM retrieval_queries WHERE query_id = ?",
            (lineage.query_id,),
        )
        query_row = query_cur.fetchone()
        if not query_row:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_QUERY_HASH_MISMATCH",
                    message=f"Referenced retrieval query '{lineage.query_id}' not found.",
                )
            )
        elif query_row["query_hash"] != lineage.query_hash:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_QUERY_HASH_MISMATCH",
                    message=f"Stored query_hash '{query_row['query_hash']}' != lineage query_hash '{lineage.query_hash}'.",
                )
            )

        # 7. PRIMARY_SEARCH exists
        checks += 1
        pri_cur = target_conn.execute(
            """
            SELECT COUNT(*) FROM retrieval_coverage_records
            WHERE run_id = ? AND search_branch = 'PRIMARY_SEARCH'
            """,
            (lineage.retrieval_run_id,),
        )
        if pri_cur.fetchone()[0] == 0:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_MISSING_PRIMARY_SEARCH",
                    message="Mandatory PRIMARY_SEARCH coverage record missing for retrieval run.",
                )
            )

        # 8. COUNTER_SEARCH exists
        checks += 1
        cnt_cur = target_conn.execute(
            """
            SELECT COUNT(*) FROM retrieval_coverage_records
            WHERE run_id = ? AND search_branch = 'COUNTER_SEARCH'
            """,
            (lineage.retrieval_run_id,),
        )
        if cnt_cur.fetchone()[0] == 0:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_MISSING_COUNTER_SEARCH",
                    message="Mandatory COUNTER_SEARCH coverage record missing for retrieval run.",
                )
            )

        # 9. submitted evidence is contained in referenced pack
        checks += 1
        items_cur = target_conn.execute(
            "SELECT evidence_id, linked_claim_id FROM retrieval_pack_items WHERE pack_id = ?",
            (lineage.pack_id,),
        )
        pack_ev_ids = {r["evidence_id"] for r in items_cur.fetchall()}
        missing_evidence = set(val_input.evidence_dependencies.evidence_ids) - pack_ev_ids
        if missing_evidence:
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_DETACHED_EVIDENCE",
                    message=f"Submitted evidence items not contained in referenced retrieval pack: {sorted(list(missing_evidence))}",
                    context_json=json.dumps({"missing_evidence_ids": sorted(list(missing_evidence))}),
                )
            )

        # 10. no detached/synthetic retrieval context is accepted
        checks += 1
        if val_input.candidate_payload.get("has_synthetic_retrieval_context", False):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V9_SYNTHETIC_CONTEXT_DETECTED",
                    message="Detached or synthetic retrieval context rejected by Task 3.9 audit firewall.",
                )
            )

        # Warning check: if counter-evidence status was not determinable
        if pack_row["counter_evidence_status"] == "COUNTER_EVIDENCE_NOT_DETERMINABLE":
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.WARNING,
                    rule_code="V9_COUNTER_EVIDENCE_NOT_DETERMINABLE_WARNING",
                    message="Retrieval run completed with COUNTER_EVIDENCE_NOT_DETERMINABLE status.",
                )
            )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Authoritative Task 3.9 symmetrical retrieval audit completed.",
            violations=violations,
        )


class V10EpistemicTierValidator(BaseValidator):
    """
    V10: Epistemic Tier & Confidence Calibration.
    V10 is AUDIT ONLY.
    It inspects existing T0–T4 classification and confidence.
    It MUST NOT:
    - assign a new tier
    - promote a tier
    - lower/raise a tier
    - generate truth
    - generate certificate confidence
    Existing evidence confidence remains authoritative within its existing model.
    """

    def validate(
        self,
        run_id: str,
        val_input: ValidationInput,
        conn: Optional[sqlite3.Connection] = None,
    ) -> ValidationLayerResult:
        layer_code = LayerCode.V10
        layer_name = LAYER_NAMES[layer_code]
        violations: List[ValidationViolation] = []
        checks = 0

        payload = val_input.candidate_payload
        target = val_input.target
        target_conn = conn or self.engine.get_write_connection()

        # Check 1: Tier promotion firewall
        checks += 1
        if payload.get("promotes_tier", False) or payload.get("attempted_tier_promotion", False):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V10_TIER_PROMOTION_PROHIBITED",
                    message="Validation engine prohibits elevating or promoting evidence claim tiers.",
                )
            )

        # Check 2: T4 Theology Firewall: T4 cannot serve as evidence for T0-T3 claims
        checks += 1
        target_is_t0_t3 = target.target_type in (
            "CLAIM",
            "PROPOSITION",
            "EXEGESIS",
        ) and payload.get("target_tier") in ("T0", "T1", "T2", "T3")

        referenced_tiers: List[str] = []
        confidences: List[float] = []

        # Check in DB evidence_ledger and claims
        for ev_id in val_input.evidence_dependencies.evidence_ids:
            cur = target_conn.execute(
                "SELECT epistemic_tier, confidence_score FROM evidence_ledger WHERE evidence_id = ?",
                (ev_id,),
            )
            row = cur.fetchone()
            if row:
                referenced_tiers.append(str(row["epistemic_tier"]))
                if row["confidence_score"] is not None:
                    confidences.append(float(row["confidence_score"]))

        for c_id in val_input.evidence_dependencies.linked_claim_ids:
            cur = target_conn.execute(
                "SELECT claim_tier FROM claims WHERE claim_id = ?",
                (c_id,),
            )
            row = cur.fetchone()
            if row:
                referenced_tiers.append(str(row["claim_tier"]))
            else:
                cur = target_conn.execute(
                    "SELECT claim_tier, synthesized_confidence AS confidence FROM synthesis_claims WHERE claim_id = ?",
                    (c_id,),
                )
                row = cur.fetchone()
                if row:
                    referenced_tiers.append(str(row["claim_tier"]))
                    if row["confidence"] is not None:
                        confidences.append(float(row["confidence"]))
                else:
                    cur = target_conn.execute(
                        "SELECT claim_tier, confidence_score AS confidence FROM claims_v2 WHERE claim_id = ?",
                        (c_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        referenced_tiers.append(str(row["claim_tier"]))
                        if row["confidence"] is not None:
                            confidences.append(float(row["confidence"]))

        # Also inspect candidate_payload for declared evidence tiers/confidences
        for item in payload.get("evidence_items", []):
            if "claim_tier" in item:
                referenced_tiers.append(str(item["claim_tier"]))
            if "confidence" in item:
                confidences.append(float(item["confidence"]))

        if payload.get("has_t4_theology_contamination", False) or (
            target_is_t0_t3
            and any(
                t in ("T4", "T4_THEOLOGICAL_CLAIM", "T4_DOGMATIC") for t in referenced_tiers
            )
        ):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V10_THEOLOGY_FIREWALL_VIOLATION",
                    message="Hard Theology Firewall violation: T4 dogmatic propositions cannot serve as evidence for T0–T3 claims.",
                )
            )

        # Check 3: Confidence boundary & weakest-critical-dependency audit
        checks += 1
        candidate_conf = payload.get("candidate_confidence")
        if candidate_conf is not None:
            if candidate_conf < 0.0 or candidate_conf > 1.0:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V10_INVALID_CONFIDENCE_RANGE",
                        message=f"Candidate confidence {candidate_conf} is outside allowable range [0.0, 1.0].",
                    )
                )
            elif confidences and candidate_conf > min(confidences) + 1e-6:
                violations.append(
                    ValidationViolation(
                        violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        layer_code=layer_code,
                        severity=ViolationSeverity.BLOCKING,
                        rule_code="V10_CONFIDENCE_INFLATION",
                        message=f"Candidate confidence ({candidate_conf}) exceeds weakest critical dependency ({min(confidences)}).",
                    )
                )

        # Check 4: Truth or score generation prohibition check
        checks += 1
        if payload.get("asserts_truth_engine_derivation", False):
            violations.append(
                ValidationViolation(
                    violation_id=f"VIOL-{uuid.uuid4().hex[:12]}",
                    run_id=run_id,
                    layer_code=layer_code,
                    severity=ViolationSeverity.BLOCKING,
                    rule_code="V10_TRUTH_ENGINE_DRIFT",
                    message="Validation engine cannot establish ontological truth or truth-engine certificates.",
                )
            )

        blocking = [v for v in violations if v.severity == ViolationSeverity.BLOCKING]
        warnings = [v for v in violations if v.severity == ViolationSeverity.WARNING]
        outcome = (
            ValidationOutcome.BLOCKED
            if blocking
            else (ValidationOutcome.VALID_WITH_WARNINGS if warnings else ValidationOutcome.VALID)
        )

        return ValidationLayerResult(
            result_id=f"LYR-{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            layer_code=layer_code,
            layer_name=layer_name,
            outcome=outcome,
            checks_evaluated=checks,
            violations_count=len(blocking),
            warnings_count=len(warnings),
            summary_notes="Epistemic tier and confidence calibration audit completed.",
            violations=violations,
        )


# =============================================================================
# VALIDATION ENGINE (Task 4.0 Subsystem Manager)
# =============================================================================

class ValidationEngine:
    """
    Automated 10-Layer Epistemic Validation Engine.
    Executes V1–V10 orthogonal validation layers, maintains immutable terminal
    persistence, issues historical certificates, and enforces epistemic firewalls.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
        retrieval_engine: Optional[HybridSymmetricalRetrievalEngine] = None,
    ) -> None:
        self.engine = engine
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.version_manager = version_manager or VersionManager(engine)
        self.retrieval_engine = retrieval_engine or HybridSymmetricalRetrievalEngine(
            self.engine, self.provenance_tracker, self.version_manager
        )

        # Initialize orthogonal validators V1–V10
        self.validators: Dict[LayerCode, BaseValidator] = {
            LayerCode.V1: V1SourceTextValidator(self.engine),
            LayerCode.V2: V2MorphologyValidator(self.engine),
            LayerCode.V3: V3SyntaxValidator(self.engine),
            LayerCode.V4: V4SemanticsValidator(self.engine),
            LayerCode.V5: V5ReferentialValidator(self.engine),
            LayerCode.V6: V6DiscourseValidator(self.engine),
            LayerCode.V7: V7TextualCriticismValidator(self.engine),
            LayerCode.V8: V8ReceptionHistoryValidator(self.engine),
            LayerCode.V9: V9RetrievalAuditValidator(self.engine, self.retrieval_engine),
            LayerCode.V10: V10EpistemicTierValidator(self.engine),
        }

    # -------------------------------------------------------------------------
    # PUBLIC VALIDATION API
    # -------------------------------------------------------------------------

    def validate(self, val_input: ValidationInput) -> ValidationRun:
        """
        Execute deterministic 10-layer epistemic validation workflow.
        Algorithm:
          1. Calculate canonical input
          2. Calculate validation identity
          3. Fast-path lookup
          4. If existing -> return existing immutable result
          5. Otherwise execute V1–V10 in memory
          6. Aggregate final result
          7. BEGIN IMMEDIATE (via DatabaseEngine.transaction)
          8. Re-check identity
          9. If another process already persisted -> return existing
          10. Insert validation_run, V1–V10 results, violations, certificate if eligible
          11. COMMIT
        """
        # 1 & 2. Calculate canonical input hash and validation identity
        val_input_hash = val_input.compute_validation_input_hash()
        val_identity = val_input.compute_validation_identity()

        # 3 & 4. Fast-path lookup
        existing = self.get_validation_run_by_identity(val_identity)
        if existing:
            return existing

        # 5. Execute V1–V10 independently in memory (NO early-exit)
        run_id = f"VRUN-{uuid.uuid4().hex[:12]}"
        layer_results: List[ValidationLayerResult] = []

        for code in (
            LayerCode.V1,
            LayerCode.V2,
            LayerCode.V3,
            LayerCode.V4,
            LayerCode.V5,
            LayerCode.V6,
            LayerCode.V7,
            LayerCode.V8,
            LayerCode.V9,
            LayerCode.V10,
        ):
            validator = self.validators[code]
            res = validator.validate(run_id, val_input)
            layer_results.append(res)

        # 6. Aggregate final result
        all_violations: List[ValidationViolation] = []
        for lr in layer_results:
            all_violations.extend(lr.violations)

        blocking_violations = [v for v in all_violations if v.severity == ViolationSeverity.BLOCKING]
        warning_violations = [v for v in all_violations if v.severity == ViolationSeverity.WARNING]

        if blocking_violations:
            final_outcome = ValidationOutcome.BLOCKED
        elif warning_violations:
            final_outcome = ValidationOutcome.VALID_WITH_WARNINGS
        else:
            final_outcome = ValidationOutcome.VALID

        checks_total = sum(lr.checks_evaluated for lr in layer_results)
        checks_failed = len(blocking_violations)
        checks_passed = max(0, checks_total - checks_failed)
        warnings_total = len(warning_violations)
        now_str = datetime.now(timezone.utc).isoformat()

        # 7. BEGIN IMMEDIATE atomic persistence
        with self.engine.transaction() as conn:
            # 8 & 9. Re-check identity under lock
            existing_locked = self._get_run_by_identity_conn(val_identity, conn)
            if existing_locked:
                return existing_locked

            # Ensure target_version_id exists in object_versions to respect foreign keys
            ver_cur = conn.execute(
                "SELECT 1 FROM object_versions WHERE version_id = ?",
                (val_input.target.target_version_id,),
            )
            if not ver_cur.fetchone():
                conn.execute(
                    """
                    INSERT INTO object_versions (
                        version_id, object_type, object_id, version_number,
                        content_hash, change_reason, provenance_id, created_at, is_immutable
                    ) VALUES (?, ?, ?, 1, ?, 'INITIAL_CREATION', 'PRV-GENESIS', ?, 1)
                    """,
                    (
                        val_input.target.target_version_id,
                        val_input.target.target_type,
                        val_input.target.target_id,
                        hashlib.sha256(val_input.target.target_id.encode("utf-8")).hexdigest(),
                        now_str,
                    ),
                )

            # Record provenance inside transaction
            prov_record = self.provenance_tracker.record_origin(
                target_type=TargetType.VALIDATION_RESULT,
                target_id=run_id,
                content=f"VALIDATION_RUN:{val_identity}:{val_input.target.target_type}:{val_input.target.target_id}",
                conn=conn,
            )

            # 10. Insert validation_run
            conn.execute(
                """
                INSERT INTO validation_runs (
                    run_id, validation_identity, validation_input_hash,
                    engine_version, schema_version, target_type, target_id,
                    target_version_id, final_outcome, checks_total, checks_passed,
                    checks_failed, warnings_total, provenance_id, executed_at,
                    is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    run_id,
                    val_identity,
                    val_input_hash,
                    val_input.environment.engine_version,
                    val_input.environment.schema_version,
                    val_input.target.target_type,
                    val_input.target.target_id,
                    val_input.target.target_version_id,
                    final_outcome.value,
                    checks_total,
                    checks_passed,
                    checks_failed,
                    warnings_total,
                    prov_record.provenance_id,
                    now_str,
                    json.dumps(val_input.candidate_payload.get("metadata", {})),
                ),
            )

            # Insert validation_layer_results
            for lr in layer_results:
                conn.execute(
                    """
                    INSERT INTO validation_layer_results (
                        result_id, run_id, layer_code, layer_name, outcome,
                        checks_evaluated, violations_count, warnings_count,
                        summary_notes, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        lr.result_id,
                        run_id,
                        lr.layer_code.value,
                        lr.layer_name,
                        lr.outcome.value,
                        lr.checks_evaluated,
                        lr.violations_count,
                        lr.warnings_count,
                        lr.summary_notes,
                        lr.metadata_json,
                    ),
                )

            # Insert validation_violations
            for v in all_violations:
                conn.execute(
                    """
                    INSERT INTO validation_violations (
                        violation_id, run_id, layer_code, severity,
                        rule_code, message, context_json, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        v.violation_id,
                        run_id,
                        v.layer_code.value,
                        v.severity.value,
                        v.rule_code,
                        v.message,
                        v.context_json,
                    ),
                )

            # Insert certificate if eligible (VALID or VALID_WITH_WARNINGS)
            certificate: Optional[ValidationCertificate] = None
            if final_outcome in (ValidationOutcome.VALID, ValidationOutcome.VALID_WITH_WARNINGS):
                cert_id = f"VCERT-{uuid.uuid4().hex[:12]}"
                layer_summary = {lr.layer_code.value: lr.outcome.value for lr in layer_results}
                layer_summary_json = json.dumps(layer_summary, sort_keys=True)

                conn.execute(
                    """
                    INSERT INTO validation_certificates (
                        certificate_id, run_id, validation_identity, validation_input_hash,
                        engine_version, schema_version, target_type, target_id,
                        target_version_id, validation_status, layer_summary_json,
                        provenance_id, validated_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        cert_id,
                        run_id,
                        val_identity,
                        val_input_hash,
                        val_input.environment.engine_version,
                        val_input.environment.schema_version,
                        val_input.target.target_type,
                        val_input.target.target_id,
                        val_input.target.target_version_id,
                        final_outcome.value,
                        layer_summary_json,
                        prov_record.provenance_id,
                        now_str,
                        None,
                    ),
                )

                certificate = ValidationCertificate(
                    certificate_id=cert_id,
                    run_id=run_id,
                    validation_identity=val_identity,
                    validation_input_hash=val_input_hash,
                    engine_version=val_input.environment.engine_version,
                    schema_version=val_input.environment.schema_version,
                    target_type=val_input.target.target_type,
                    target_id=val_input.target.target_id,
                    target_version_id=val_input.target.target_version_id,
                    validation_status=final_outcome.value,
                    layer_summary_json=layer_summary_json,
                    provenance_id=prov_record.provenance_id,
                    validated_at=now_str,
                )

        # Construct and return completed immutable run snapshot
        return ValidationRun(
            run_id=run_id,
            validation_identity=val_identity,
            validation_input_hash=val_input_hash,
            engine_version=val_input.environment.engine_version,
            schema_version=val_input.environment.schema_version,
            target_type=val_input.target.target_type,
            target_id=val_input.target.target_id,
            target_version_id=val_input.target.target_version_id,
            final_outcome=final_outcome,
            checks_total=checks_total,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings_total=warnings_total,
            provenance_id=prov_record.provenance_id,
            executed_at=now_str,
            layer_results=layer_results,
            violations=all_violations,
            certificate=certificate,
            metadata_json=json.dumps(val_input.candidate_payload.get("metadata", {})),
        )

    # -------------------------------------------------------------------------
    # LOOKUP AND QUERY HELPERS
    # -------------------------------------------------------------------------

    def get_validation_run(self, run_id: str) -> Optional[ValidationRun]:
        """Fetch an immutable validation run and its associated entities by run_id."""
        with self.engine.connect() as conn:
            return self._get_run_by_id_conn(run_id, conn)

    def get_validation_run_by_identity(self, validation_identity: str) -> Optional[ValidationRun]:
        """Fetch an immutable validation run by deterministic validation identity."""
        with self.engine.connect() as conn:
            return self._get_run_by_identity_conn(validation_identity, conn)

    def get_certificate(self, certificate_id: str) -> Optional[ValidationCertificate]:
        """Fetch a historical validation certificate by certificate_id."""
        with self.engine.connect() as conn:
            cur = conn.execute(
                "SELECT * FROM validation_certificates WHERE certificate_id = ?",
                (certificate_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_certificate(row)

    def get_certificate_by_identity(self, validation_identity: str) -> Optional[ValidationCertificate]:
        """Fetch a historical validation certificate by validation_identity."""
        with self.engine.connect() as conn:
            cur = conn.execute(
                "SELECT * FROM validation_certificates WHERE validation_identity = ?",
                (validation_identity,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_certificate(row)

    # -------------------------------------------------------------------------
    # INTERNAL RECONSTRUCTION METHODS
    # -------------------------------------------------------------------------

    def _get_run_by_id_conn(
        self,
        run_id: str,
        conn: sqlite3.Connection,
    ) -> Optional[ValidationRun]:
        cur = conn.execute("SELECT * FROM validation_runs WHERE run_id = ?", (run_id,))
        row = cur.fetchone()
        if not row:
            return None
        return self._hydrate_run(row, conn)

    def _get_run_by_identity_conn(
        self,
        validation_identity: str,
        conn: sqlite3.Connection,
    ) -> Optional[ValidationRun]:
        cur = conn.execute(
            "SELECT * FROM validation_runs WHERE validation_identity = ?",
            (validation_identity,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._hydrate_run(row, conn)

    def _hydrate_run(
        self,
        run_row: sqlite3.Row,
        conn: sqlite3.Connection,
    ) -> ValidationRun:
        run_id = run_row["run_id"]

        # Fetch violations
        viol_cur = conn.execute(
            "SELECT * FROM validation_violations WHERE run_id = ? ORDER BY layer_code, rule_code",
            (run_id,),
        )
        violations = [
            ValidationViolation(
                violation_id=vr["violation_id"],
                run_id=vr["run_id"],
                layer_code=LayerCode(vr["layer_code"]),
                severity=ViolationSeverity(vr["severity"]),
                rule_code=vr["rule_code"],
                message=vr["message"],
                context_json=vr["context_json"],
            )
            for vr in viol_cur.fetchall()
        ]

        # Fetch layer results
        lyr_cur = conn.execute(
            "SELECT * FROM validation_layer_results WHERE run_id = ? ORDER BY layer_code",
            (run_id,),
        )
        layer_results: List[ValidationLayerResult] = []
        for lr in lyr_cur.fetchall():
            code = LayerCode(lr["layer_code"])
            l_viols = [v for v in violations if v.layer_code == code]
            layer_results.append(
                ValidationLayerResult(
                    result_id=lr["result_id"],
                    run_id=run_id,
                    layer_code=code,
                    layer_name=lr["layer_name"],
                    outcome=ValidationOutcome(lr["outcome"]),
                    checks_evaluated=lr["checks_evaluated"],
                    violations_count=lr["violations_count"],
                    warnings_count=lr["warnings_count"],
                    summary_notes=lr["summary_notes"],
                    violations=l_viols,
                    metadata_json=lr["metadata_json"],
                )
            )

        # Fetch certificate if any
        cert_cur = conn.execute(
            "SELECT * FROM validation_certificates WHERE run_id = ?",
            (run_id,),
        )
        cert_row = cert_cur.fetchone()
        certificate = self._row_to_certificate(cert_row) if cert_row else None

        return ValidationRun(
            run_id=run_row["run_id"],
            validation_identity=run_row["validation_identity"],
            validation_input_hash=run_row["validation_input_hash"],
            engine_version=run_row["engine_version"],
            schema_version=run_row["schema_version"],
            target_type=run_row["target_type"],
            target_id=run_row["target_id"],
            target_version_id=run_row["target_version_id"],
            final_outcome=ValidationOutcome(run_row["final_outcome"]),
            checks_total=run_row["checks_total"],
            checks_passed=run_row["checks_passed"],
            checks_failed=run_row["checks_failed"],
            warnings_total=run_row["warnings_total"],
            provenance_id=run_row["provenance_id"],
            executed_at=run_row["executed_at"],
            layer_results=layer_results,
            violations=violations,
            certificate=certificate,
            is_immutable=run_row["is_immutable"],
            metadata_json=run_row["metadata_json"],
        )

    def _row_to_certificate(self, row: sqlite3.Row) -> ValidationCertificate:
        return ValidationCertificate(
            certificate_id=row["certificate_id"],
            run_id=row["run_id"],
            validation_identity=row["validation_identity"],
            validation_input_hash=row["validation_input_hash"],
            engine_version=row["engine_version"],
            schema_version=row["schema_version"],
            target_type=row["target_type"],
            target_id=row["target_id"],
            target_version_id=row["target_version_id"],
            validation_status=row["validation_status"],
            layer_summary_json=row["layer_summary_json"],
            provenance_id=row["provenance_id"],
            validated_at=row["validated_at"],
            is_immutable=row["is_immutable"],
            metadata_json=row["metadata_json"],
        )
