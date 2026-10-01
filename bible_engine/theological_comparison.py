"""
Theological Comparison & Ilzam al-Khasm Engine (Task 3.8).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principles:
  1. HARD THEOLOGY FIREWALL:
     T0–T3 evidence -> theological audit -> T4 proposition assessment.
     T4 dogmatic claims CANNOT contaminate, rewrite, upgrade, or define T0–T3 facts.
  2. NO SELF-PROVING DOGMA:
     A theological proposition cannot serve as evidence for its own underlying premises.
     Circular dependency chains are strictly forbidden (petitio principii).
  3. ILZAM AL-KHASM (INTERNAL CRITIQUE):
     Evaluates propositions strictly against a framework's own stated premises,
     acknowledged texts, and linguistic constraints without manufacturing contradictions.
  4. SYMMETRICAL FRAMEWORK EVALUATION:
     Every theological framework is evaluated against identical evidence and rules;
     zero majority-vote, popularity, or council consensus ranking.
  5. ANTI-ANACHRONISM FIREWALL:
     Post-biblical reception terminology (E12) cannot be retrojected into early biblical texts
     as original authorial intent without contemporary epigraphic/linguistic warrant.
  6. IDENTITY FIREWALL:
     Metaphorical agency, divine representation, messenger terminology, or title usage
     cannot be automatically equated to ontological identity.
  7. WEAKEST-CRITICAL-DEPENDENCY CONFIDENCE:
     Audit confidence <= min(constituent evidence confidences).
     Zero majority-vote or frequency inflation.
  8. IMMUTABILITY & PROVENANCE:
     Full cryptographic SHA-256 provenance lineage; UPDATE/DELETE blocked by triggers.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AnachronisticRetrojectionError,
    AsymmetricalFrameworkEvaluationError,
    CircularProofStructureError,
    ComparisonRunNotFoundError,
    DogmaticEvidenceContaminationError,
    FrameworkNotFoundError,
    IdentityCollapseError,
    IlzamCritiqueDetectedError,
    PropositionNotFoundError,
    TheologicalComparisonSubsystemError,
    TheologicalConcurrencyError,
    TheologicalConfidenceInflationError,
    TheologicalHarmonizationError,
    TheologicalImmutabilityError,
    TheologicalInvalidProvenanceError,
    TheologicalInvalidVersionError,
    TheologicalValidationError,
    TheologyFirewallError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class FrameworkTradition(str, Enum):
    CHRISTIAN_PATRISTIC = "CHRISTIAN_PATRISTIC"
    CHRISTIAN_HETERODOX = "CHRISTIAN_HETERODOX"
    JUDAISM_SECOND_TEMPLE = "JUDAISM_SECOND_TEMPLE"
    JUDAISM_RABBINIC = "JUDAISM_RABBINIC"
    ISLAMIC_TAWHIDIC = "ISLAMIC_TAWHIDIC"
    ENLIGHTENMENT_SOCINIAN = "ENLIGHTENMENT_SOCINIAN"
    OTHER = "OTHER"


class HistoricalEra(str, Enum):
    BIBLICAL_ERA = "BIBLICAL_ERA"
    APOSTOLIC_FATHERS = "APOSTOLIC_FATHERS"
    EARLY_PATRISTIC = "EARLY_PATRISTIC"
    NICENE_ERA = "NICENE_ERA"
    POST_CHALCEDONIAN = "POST_CHALCEDONIAN"
    MEDIEVAL = "MEDIEVAL"
    REFORMATION = "REFORMATION"
    MODERN = "MODERN"


class AuditVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    IN_TENSION = "IN_TENSION"
    INSUFFICIENTLY_WARRANTED = "INSUFFICIENTLY_WARRANTED"
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"


class AlignmentStatus(str, Enum):
    TEXTUALLY_SUPPORTED = "TEXTUALLY_SUPPORTED"
    LEXICALLY_UNSUPPORTED = "LEXICALLY_UNSUPPORTED"
    ANACHRONISTIC_RETROJECTION = "ANACHRONISTIC_RETROJECTION"
    CATEGORY_MISTAKE_IDENTITY = "CATEGORY_MISTAKE_IDENTITY"
    EXEGETICAL_TENSION = "EXEGETICAL_TENSION"
    CONTRADICTION = "CONTRADICTION"
    UNWARRANTED_EXTRAPOLATION = "UNWARRANTED_EXTRAPOLATION"
    ABSENCE_OF_TEXTUAL_WARRANT = "ABSENCE_OF_TEXTUAL_WARRANT"


class CritiqueType(str, Enum):
    INTERNAL_PREMISE_CONTRADICTION = "INTERNAL_PREMISE_CONTRADICTION"
    UNSUPPORTED_INFERENCE = "UNSUPPORTED_INFERENCE"
    INVALID_EXTRAPOLATION = "INVALID_EXTRAPOLATION"
    CONTRADICTION_WITH_ACKNOWLEDGED_TEXT = "CONTRADICTION_WITH_ACKNOWLEDGED_TEXT"
    ANACHRONISTIC_CATEGORY_LEAKAGE = "ANACHRONISTIC_CATEGORY_LEAKAGE"
    CIRCULAR_PROOF_STRUCTURE = "CIRCULAR_PROOF_STRUCTURE"
    AMBIGUITY_OR_UNRESOLVED_ANTINOMY = "AMBIGUITY_OR_UNRESOLVED_ANTINOMY"


class CritiqueSeverity(str, Enum):
    FATAL_INTERNAL_CONTRADICTION = "FATAL_INTERNAL_CONTRADICTION"
    UNWARRANTED_LEAP = "UNWARRANTED_LEAP"
    FORMAL_AMBIGUITY = "FORMAL_AMBIGUITY"
    INFORMATIONAL_TENSION = "INFORMATIONAL_TENSION"


class ComparisonRunStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


# Known post-biblical philosophical / dogmatic terminology requiring anachronism audit
POST_BIBLICAL_TERMS: Set[str] = {
    "homoousios",
    "homoiousios",
    "hypostasis",
    "ousia",
    "prosopon",
    "communicatio_idiomatum",
    "theotokos",
    "perichoresis",
    "circumincessio",
    "hypostatic_union",
    "trinitas",
    "filioque",
    "eternal_generation",
    "consubstantial",
    "active_spirator",
}


def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash of a serializable object."""
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# =============================================================================
# INPUT & RECORD DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class TheologicalFrameworkDefinition:
    framework_id: str
    framework_name: str
    tradition_family: FrameworkTradition
    historical_period: str
    description: str
    canonical_source_corpus: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DogmaticPropositionDefinition:
    proposition_id: str
    framework_id: str
    formulation_title: str
    proposition_text: str
    formal_creedal_source: str
    historical_era: HistoricalEra
    contains_post_biblical_terminology: bool = False
    post_biblical_terms: Sequence[str] = ()
    claim_tier: ClaimTier = ClaimTier.T4_THEOLOGICAL_CLAIM
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class PropositionAuditInput:
    audit_id: str
    deconstructed_premise_text: str
    target_evidence_tier: ClaimTier
    target_passage_or_pericope_id: str
    alignment_status: AlignmentStatus
    evidence_confidence: float
    audit_confidence: float
    audit_finding_detail: str
    target_claim_id: Optional[str] = None
    target_synthesis_claim_id: Optional[str] = None
    target_evidence_id: Optional[str] = None
    is_anachronism_detected: bool = False
    is_identity_collapse_detected: bool = False
    is_critical_dependency: bool = True
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class IlzamCritiqueInput:
    critique_id: str
    critique_type: CritiqueType
    acknowledged_premise_a: str
    dependency_chain: Sequence[str]
    demonstration_text: str
    critique_severity: CritiqueSeverity
    acknowledged_premise_b: Optional[str] = None
    is_circularity_rejected: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class TheologicalComparisonConfig:
    comparator_id: str = "POLYA-ILZAM-ENGINE-V2"
    comparator_version: str = "2.0.0"
    allow_unwarranted_retrojection: bool = False
    enforce_strict_anachronism_rejection: bool = False
    allow_identity_collapse: bool = False
    enforce_strict_identity_rejection: bool = False
    enforce_strict_circularity_rejection: bool = True
    strict_immutability: bool = True


@dataclass(frozen=True)
class TheologicalComparisonRunResult:
    run_id: str
    proposition_id: str
    audit_verdict: AuditVerdict
    overall_confidence: float
    status: ComparisonRunStatus
    provenance_id: str
    version_id: str
    input_content_hash: str
    configuration_hash: str
    output_hash: str
    audits_count: int
    critiques_count: int
    created_at: str


@dataclass(frozen=True)
class TheologicalFrameworkRecord:
    framework_id: str
    framework_name: str
    tradition_family: str
    historical_period: str
    description: str
    canonical_source_corpus: str
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class DogmaticPropositionRecord:
    proposition_id: str
    framework_id: str
    claim_tier: str
    formulation_title: str
    proposition_text: str
    formal_creedal_source: str
    historical_era: str
    contains_post_biblical_terminology: bool
    post_biblical_terms: List[str]
    provenance_id: str
    version_id: str
    status: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class PropositionEvidenceAuditRecord:
    audit_id: str
    run_id: str
    proposition_id: str
    deconstructed_premise_text: str
    target_evidence_tier: str
    target_claim_id: Optional[str]
    target_synthesis_claim_id: Optional[str]
    target_evidence_id: Optional[str]
    target_passage_or_pericope_id: str
    alignment_status: str
    evidence_confidence: float
    audit_confidence: float
    is_anachronism_detected: bool
    is_identity_collapse_detected: bool
    audit_finding_detail: str
    provenance_id: str
    version_id: str
    status: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class IlzamCritiqueRecord:
    critique_id: str
    run_id: str
    target_framework_id: str
    target_proposition_id: str
    critique_type: str
    acknowledged_premise_a: str
    acknowledged_premise_b: Optional[str]
    dependency_chain: List[str]
    demonstration_text: str
    critique_severity: str
    is_circularity_rejected: bool
    provenance_id: str
    version_id: str
    status: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# THEOLOGICAL COMPARISON & ILZAM AL-KHASM MANAGER
# =============================================================================

class TheologicalComparisonManager:
    """
    Subsystem manager for Theological Comparison & Ilzam al-Khasm Engine (Task 3.8).
    Audits T4 dogmatic propositions against lower-tier evidence (T0-T3).
    Enforces Hard Theology Firewall, anti-circularity, anti-anachronism, identity firewall,
    weakest-critical-dependency confidence propagation, and symmetrical framework evaluation.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: VersionManager,
        provenance_tracker: ProvenanceTracker,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager
        self.provenance_tracker = provenance_tracker

    # -------------------------------------------------------------------------
    # 1. FRAMEWORK & PROPOSITION REGISTRATION
    # -------------------------------------------------------------------------

    def register_framework(
        self,
        framework: TheologicalFrameworkDefinition,
    ) -> TheologicalFrameworkRecord:
        """Register a confessional / theological framework tradition."""
        if not framework.framework_id or not framework.framework_id.strip():
            raise TheologicalValidationError("Framework ID cannot be empty.")
        if not framework.framework_name or not framework.framework_name.strip():
            raise TheologicalValidationError("Framework name cannot be empty.")
        if not isinstance(framework.tradition_family, FrameworkTradition):
            raise TheologicalValidationError(f"Invalid tradition family: {framework.tradition_family}")

        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(framework.metadata or {}) if framework.metadata else None

        # Provenance & Versioning
        prov_record = self.provenance_tracker.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id=framework.framework_id,
            content=f"THEO_FRAMEWORK:{framework.framework_id}:{framework.framework_name}",
        )
        ver_record = self.version_manager.create_version(
            object_type="THEOLOGICAL_FRAMEWORK",
            object_id=framework.framework_id,
            content=json.dumps(asdict(framework), sort_keys=True, default=str),
            change_reason=ChangeReason.INITIAL_CREATION,
            provenance_id=prov_record.provenance_id,
        )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO theological_frameworks (
                    framework_id, framework_name, tradition_family, historical_period,
                    description, canonical_source_corpus, provenance_id, version_id,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    framework.framework_id,
                    framework.framework_name,
                    framework.tradition_family.value,
                    framework.historical_period,
                    framework.description,
                    framework.canonical_source_corpus,
                    prov_record.provenance_id,
                    ver_record.version_id,
                    now,
                    metadata_json,
                ),
            )

        return TheologicalFrameworkRecord(
            framework_id=framework.framework_id,
            framework_name=framework.framework_name,
            tradition_family=framework.tradition_family.value,
            historical_period=framework.historical_period,
            description=framework.description,
            canonical_source_corpus=framework.canonical_source_corpus,
            provenance_id=prov_record.provenance_id,
            version_id=ver_record.version_id,
            created_at=now,
            metadata=framework.metadata,
        )

    def register_proposition(
        self,
        proposition: DogmaticPropositionDefinition,
    ) -> DogmaticPropositionRecord:
        """
        Register a T4 theological/dogmatic proposition.
        Enforces Hard Theology Firewall: claim tier must strictly be T4_THEOLOGICAL_CLAIM.
        """
        if not proposition.proposition_id or not proposition.proposition_id.strip():
            raise TheologicalValidationError("Proposition ID cannot be empty.")
        if not proposition.framework_id or not proposition.framework_id.strip():
            raise TheologicalValidationError("Framework ID cannot be empty.")
        if not proposition.proposition_text or not proposition.proposition_text.strip():
            raise TheologicalValidationError("Proposition text cannot be empty.")

        # Hard Theology Firewall: Tier must strictly be T4
        if proposition.claim_tier != ClaimTier.T4_THEOLOGICAL_CLAIM:
            raise DogmaticEvidenceContaminationError(
                f"Theology Firewall Violation: Dogmatic proposition '{proposition.proposition_id}' "
                f"must have claim_tier T4_THEOLOGICAL_CLAIM, found '{proposition.claim_tier.value}'. "
                "T4 dogmas cannot pose as lower-tier facts."
            )

        # Check framework existence
        fw = self.get_framework(proposition.framework_id)
        if fw is None:
            raise FrameworkNotFoundError(f"Referenced framework '{proposition.framework_id}' not found.")

        # Check post-biblical terms
        text_lower = proposition.proposition_text.lower()
        detected_terms = set(proposition.post_biblical_terms)
        for term in POST_BIBLICAL_TERMS:
            if term in text_lower:
                detected_terms.add(term)

        contains_post_biblical = proposition.contains_post_biblical_terminology or len(detected_terms) > 0
        terms_json = json.dumps(sorted(list(detected_terms))) if detected_terms else None

        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(proposition.metadata or {}) if proposition.metadata else None

        prov_record = self.provenance_tracker.record_origin(
            target_type=TargetType.CLAIM,
            target_id=proposition.proposition_id,
            content=f"DOGMATIC_PROP:{proposition.proposition_id}:{proposition.proposition_text}",
        )
        ver_record = self.version_manager.create_version(
            object_type="DOGMATIC_PROPOSITION",
            object_id=proposition.proposition_id,
            content=json.dumps(asdict(proposition), sort_keys=True, default=str),
            change_reason=ChangeReason.INITIAL_CREATION,
            provenance_id=prov_record.provenance_id,
        )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO dogmatic_propositions (
                    proposition_id, framework_id, claim_tier, formulation_title,
                    proposition_text, formal_creedal_source, historical_era,
                    contains_post_biblical_terminology, post_biblical_terms_json,
                    provenance_id, version_id, status, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, 1, ?)
                """,
                (
                    proposition.proposition_id,
                    proposition.framework_id,
                    proposition.claim_tier.value,
                    proposition.formulation_title,
                    proposition.proposition_text,
                    proposition.formal_creedal_source,
                    proposition.historical_era.value,
                    1 if contains_post_biblical else 0,
                    terms_json,
                    prov_record.provenance_id,
                    ver_record.version_id,
                    now,
                    metadata_json,
                ),
            )

        return DogmaticPropositionRecord(
            proposition_id=proposition.proposition_id,
            framework_id=proposition.framework_id,
            claim_tier=proposition.claim_tier.value,
            formulation_title=proposition.formulation_title,
            proposition_text=proposition.proposition_text,
            formal_creedal_source=proposition.formal_creedal_source,
            historical_era=proposition.historical_era.value,
            contains_post_biblical_terminology=contains_post_biblical,
            post_biblical_terms=sorted(list(detected_terms)),
            provenance_id=prov_record.provenance_id,
            version_id=ver_record.version_id,
            status="ACTIVE",
            created_at=now,
            metadata=proposition.metadata,
        )

    # -------------------------------------------------------------------------
    # 2. THEOLOGICAL COMPARISON EXECUTION
    # -------------------------------------------------------------------------

    def execute_comparison_run(
        self,
        proposition_id: str,
        audits: Sequence[PropositionAuditInput],
        critiques: Sequence[IlzamCritiqueInput] = (),
        run_id: Optional[str] = None,
        config: Optional[TheologicalComparisonConfig] = None,
    ) -> TheologicalComparisonRunResult:
        """
        Execute an atomic theological comparison and Ilzam al-Khasm audit run.
        Enforces:
          - Hard Theology Firewall (T0-T3 -> T4, no T4 pollution).
          - No self-proving dogma (anti-circularity detection).
          - Anti-anachronism firewall (reception != original authorial intent).
          - Identity firewall (agency/representation != ontological identity).
          - Weakest-critical-dependency confidence propagation.
          - Atomic transaction rollback on any validation failure.
        """
        cfg = config or TheologicalComparisonConfig()
        now = datetime.now(timezone.utc).isoformat()
        actual_run_id = run_id or f"THEO-RUN-{hashlib.sha256(now.encode('utf-8')).hexdigest()[:12].upper()}"

        # 1. Structural & invariant validation
        if not proposition_id or not proposition_id.strip():
            raise TheologicalValidationError("Proposition ID cannot be empty.")
        if not audits:
            raise TheologicalValidationError("Theological comparison run must contain at least one evidence audit.")

        prop = self.get_proposition(proposition_id)
        if prop is None:
            raise PropositionNotFoundError(f"Referenced proposition '{proposition_id}' not found.")

        # Check for duplicate audit IDs
        seen_audit_ids: Set[str] = set()
        for a in audits:
            if not a.audit_id or not a.audit_id.strip():
                raise TheologicalValidationError("Audit ID cannot be empty.")
            if a.audit_id in seen_audit_ids:
                raise TheologicalValidationError(f"Duplicate audit ID '{a.audit_id}' within run.")
            seen_audit_ids.add(a.audit_id)

        # Check for duplicate critique IDs
        seen_critique_ids: Set[str] = set()
        for c in critiques:
            if not c.critique_id or not c.critique_id.strip():
                raise TheologicalValidationError("Critique ID cannot be empty.")
            if c.critique_id in seen_critique_ids:
                raise TheologicalValidationError(f"Duplicate critique ID '{c.critique_id}' within run.")
            seen_critique_ids.add(c.critique_id)

        # 2. Hard Theology Firewall & Circularity Verification
        critical_confidences: List[float] = []

        for a in audits:
            # Directionality check: Target evidence tier must be T0, T1, T2, or T3
            if a.target_evidence_tier == ClaimTier.T4_THEOLOGICAL_CLAIM:
                raise DogmaticEvidenceContaminationError(
                    f"Theology Firewall Violation in audit '{a.audit_id}': "
                    "Target evidence tier cannot be T4_THEOLOGICAL_CLAIM. "
                    "Dogmatic claims cannot serve as evidentiary foundation for dogmatic propositions."
                )

            # Circularity check: A proposition cannot cite itself as evidence
            if a.target_claim_id == proposition_id or a.target_synthesis_claim_id == proposition_id:
                raise CircularProofStructureError(
                    f"Circular Proof Detected in audit '{a.audit_id}': "
                    f"Proposition '{proposition_id}' attempts to cite itself as evidence."
                )

            # Check target claim tier in database if referenced
            if a.target_claim_id:
                with self.engine.get_read_connection() as r_conn:
                    cursor = r_conn.cursor()
                    cursor.execute("SELECT claim_tier FROM claims WHERE claim_id = ?", (a.target_claim_id,))
                    row = cursor.fetchone()
                    if row and row[0] in (ClaimTier.T4_THEOLOGICAL_CLAIM.value, ClaimTier.T4_THEOLOGICAL_CLAIM.name, "TIER_4_THEOLOGICAL_CLAIM"):
                        raise DogmaticEvidenceContaminationError(
                            f"Theology Firewall Violation in audit '{a.audit_id}': "
                            f"Target claim '{a.target_claim_id}' in claims table is T4_THEOLOGICAL_CLAIM. "
                            "Dogmatic claims cannot serve as evidentiary foundation for dogmatic propositions."
                        )

            # Audit confidence capping
            if a.audit_confidence > a.evidence_confidence + 0.00001:
                raise TheologicalConfidenceInflationError(
                    f"Confidence Inflation in audit '{a.audit_id}': "
                    f"Audit confidence ({a.audit_confidence}) exceeds evidence confidence ({a.evidence_confidence})."
                )

            if a.is_critical_dependency:
                critical_confidences.append(a.audit_confidence)

            # Anti-Anachronism check
            if a.is_anachronism_detected or a.alignment_status == AlignmentStatus.ANACHRONISTIC_RETROJECTION:
                if cfg.enforce_strict_anachronism_rejection or not cfg.allow_unwarranted_retrojection:
                    raise AnachronisticRetrojectionError(
                        f"Anachronistic Retrojection Violation in audit '{a.audit_id}': "
                        f"Attempting to retroject post-biblical terminology into target passage "
                        f"'{a.target_passage_or_pericope_id}' without contemporary linguistic warrant."
                    )

            # Identity Firewall check
            if a.is_identity_collapse_detected or a.alignment_status == AlignmentStatus.CATEGORY_MISTAKE_IDENTITY:
                if cfg.enforce_strict_identity_rejection or not cfg.allow_identity_collapse:
                    raise IdentityCollapseError(
                        f"Identity Firewall Violation in audit '{a.audit_id}': "
                        f"Metaphorical agency or divine representation illicitly collapsed into "
                        f"ontological identity in target passage '{a.target_passage_or_pericope_id}'."
                    )

        # 3. Ilzam al-Khasm & Dependency Chain Verification
        for c in critiques:
            # Check circularity in critique dependency chains
            if cfg.enforce_strict_circularity_rejection:
                if proposition_id in c.dependency_chain:
                    # Circular chain detected
                    if not (c.critique_type == CritiqueType.CIRCULAR_PROOF_STRUCTURE or c.is_circularity_rejected):
                        raise CircularProofStructureError(
                            f"Circularity Violation in critique '{c.critique_id}': "
                            f"Dependency chain contains target proposition '{proposition_id}' circularly."
                        )
                # Internal loop detection
                if len(c.dependency_chain) != len(set(c.dependency_chain)):
                    if not (c.critique_type == CritiqueType.CIRCULAR_PROOF_STRUCTURE or c.is_circularity_rejected):
                        raise CircularProofStructureError(
                            f"Internal Cycle Detected in critique '{c.critique_id}': "
                            "Dependency chain contains duplicate nodes forming an internal loop."
                        )

        # 4. Weakest-Critical-Dependency Confidence Propagation
        if critical_confidences:
            calculated_max_confidence = min(critical_confidences)
        else:
            calculated_max_confidence = min(a.audit_confidence for a in audits)

        # Determine overall audit verdict based on constituent alignments and critiques
        verdict = self._derive_audit_verdict(audits, critiques)

        # Overall confidence is capped strictly by weakest critical dependency
        overall_confidence = calculated_max_confidence

        # 5. Hashes & Provenance
        input_payload = {
            "proposition_id": proposition_id,
            "audits": [asdict(a) for a in audits],
            "critiques": [asdict(c) for c in critiques],
        }
        config_payload = asdict(cfg)
        output_payload = {
            "run_id": actual_run_id,
            "verdict": verdict.value,
            "overall_confidence": overall_confidence,
            "audits_count": len(audits),
            "critiques_count": len(critiques),
        }

        input_content_hash = compute_canonical_hash(input_payload)
        configuration_hash = compute_canonical_hash(config_payload)
        output_hash = compute_canonical_hash(output_payload)

        # Register Provenance & Version
        prov_record = self.provenance_tracker.record_origin(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id=actual_run_id,
            content=f"THEO_RUN:{actual_run_id}:{proposition_id}:{output_hash}",
        )
        ver_record = self.version_manager.create_version(
            object_type="THEOLOGICAL_COMPARISON_RUN",
            object_id=actual_run_id,
            content=json.dumps(output_payload, sort_keys=True),
            change_reason=ChangeReason.INITIAL_CREATION,
            provenance_id=prov_record.provenance_id,
        )

        # 6. Atomic Transaction Persistence
        with self.engine.transaction() as conn:
            # Insert Run
            conn.execute(
                """
                INSERT INTO theological_comparison_runs (
                    run_id, proposition_id, comparator_id, comparator_version,
                    configuration_hash, input_content_hash, output_hash,
                    audit_verdict, overall_confidence, status, is_exact_reproducible,
                    provenance_id, version_id, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, ?, ?, 1, ?)
                """,
                (
                    actual_run_id,
                    proposition_id,
                    cfg.comparator_id,
                    cfg.comparator_version,
                    configuration_hash,
                    input_content_hash,
                    output_hash,
                    verdict.value,
                    overall_confidence,
                    prov_record.provenance_id,
                    ver_record.version_id,
                    now,
                    json.dumps(output_payload),
                ),
            )

            # Insert Audits
            for a in audits:
                a_prov = self.provenance_tracker.record_origin(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=a.audit_id,
                    content=f"PROP_AUDIT:{a.audit_id}:{a.target_passage_or_pericope_id}",
                )
                a_ver = self.version_manager.create_version(
                    object_type="PROPOSITION_EVIDENCE_AUDIT",
                    object_id=a.audit_id,
                    content=json.dumps(asdict(a), sort_keys=True, default=str),
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=a_prov.provenance_id,
                )

                conn.execute(
                    """
                    INSERT INTO proposition_evidence_audits (
                        audit_id, run_id, proposition_id, deconstructed_premise_text,
                        target_evidence_tier, target_claim_id, target_synthesis_claim_id,
                        target_evidence_id, target_passage_or_pericope_id, alignment_status,
                        evidence_confidence, audit_confidence, is_anachronism_detected,
                        is_identity_collapse_detected, audit_finding_detail,
                        provenance_id, version_id, status, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, 1, ?)
                    """,
                    (
                        a.audit_id,
                        actual_run_id,
                        proposition_id,
                        a.deconstructed_premise_text,
                        a.target_evidence_tier.value,
                        a.target_claim_id,
                        a.target_synthesis_claim_id,
                        a.target_evidence_id,
                        a.target_passage_or_pericope_id,
                        a.alignment_status.value,
                        a.evidence_confidence,
                        a.audit_confidence,
                        1 if a.is_anachronism_detected else 0,
                        1 if a.is_identity_collapse_detected else 0,
                        a.audit_finding_detail,
                        a_prov.provenance_id,
                        a_ver.version_id,
                        now,
                        json.dumps(a.metadata or {}),
                    ),
                )

            # Insert Critiques
            for c in critiques:
                c_prov = self.provenance_tracker.record_origin(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=c.critique_id,
                    content=f"ILZAM_CRITIQUE:{c.critique_id}:{prop.framework_id}",
                )
                c_ver = self.version_manager.create_version(
                    object_type="ILZAM_CRITIQUE_RECORD",
                    object_id=c.critique_id,
                    content=json.dumps(asdict(c), sort_keys=True, default=str),
                    change_reason=ChangeReason.INITIAL_CREATION,
                    provenance_id=c_prov.provenance_id,
                )

                conn.execute(
                    """
                    INSERT INTO ilzam_critique_records (
                        critique_id, run_id, target_framework_id, target_proposition_id,
                        critique_type, acknowledged_premise_a, acknowledged_premise_b,
                        dependency_chain_json, demonstration_text, critique_severity,
                        is_circularity_rejected, provenance_id, version_id, status,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, 1, ?)
                    """,
                    (
                        c.critique_id,
                        actual_run_id,
                        prop.framework_id,
                        proposition_id,
                        c.critique_type.value,
                        c.acknowledged_premise_a,
                        c.acknowledged_premise_b,
                        json.dumps(list(c.dependency_chain)),
                        c.demonstration_text,
                        c.critique_severity.value,
                        1 if c.is_circularity_rejected else 0,
                        c_prov.provenance_id,
                        c_ver.version_id,
                        now,
                        json.dumps(c.metadata or {}),
                    ),
                )

        return TheologicalComparisonRunResult(
            run_id=actual_run_id,
            proposition_id=proposition_id,
            audit_verdict=verdict,
            overall_confidence=overall_confidence,
            status=ComparisonRunStatus.COMPLETED,
            provenance_id=prov_record.provenance_id,
            version_id=ver_record.version_id,
            input_content_hash=input_content_hash,
            configuration_hash=configuration_hash,
            output_hash=output_hash,
            audits_count=len(audits),
            critiques_count=len(critiques),
            created_at=now,
        )

    # -------------------------------------------------------------------------
    # 3. VERDICT DERIVATION ENGINE
    # -------------------------------------------------------------------------

    def _derive_audit_verdict(
        self,
        audits: Sequence[PropositionAuditInput],
        critiques: Sequence[IlzamCritiqueInput],
    ) -> AuditVerdict:
        """
        Derive audit verdict objectively without majority-vote or dogmatic bias.
        """
        has_fatal_critique = any(
            c.critique_severity == CritiqueSeverity.FATAL_INTERNAL_CONTRADICTION
            for c in critiques
        )
        has_contradiction = any(
            a.alignment_status == AlignmentStatus.CONTRADICTION
            for a in audits
        )
        if has_fatal_critique or has_contradiction:
            return AuditVerdict.CONTRADICTED

        has_formal_ambiguity = any(
            c.critique_severity == CritiqueSeverity.FORMAL_AMBIGUITY
            for c in critiques
        )
        if has_formal_ambiguity:
            return AuditVerdict.UNRESOLVED

        has_tension = any(
            a.alignment_status in (
                AlignmentStatus.EXEGETICAL_TENSION,
                AlignmentStatus.ANACHRONISTIC_RETROJECTION,
                AlignmentStatus.CATEGORY_MISTAKE_IDENTITY,
            )
            for a in audits
        ) or any(
            c.critique_severity in (CritiqueSeverity.UNWARRANTED_LEAP, CritiqueSeverity.INFORMATIONAL_TENSION)
            for c in critiques
        )

        has_absence_or_unsupported = any(
            a.alignment_status in (
                AlignmentStatus.ABSENCE_OF_TEXTUAL_WARRANT,
                AlignmentStatus.LEXICALLY_UNSUPPORTED,
                AlignmentStatus.UNWARRANTED_EXTRAPOLATION,
            )
            for a in audits
        )

        all_supported = all(
            a.alignment_status == AlignmentStatus.TEXTUALLY_SUPPORTED
            for a in audits
        )

        if all_supported and not critiques:
            return AuditVerdict.SUPPORTED

        if any(a.alignment_status == AlignmentStatus.TEXTUALLY_SUPPORTED for a in audits):
            if has_tension:
                return AuditVerdict.IN_TENSION
            if has_absence_or_unsupported:
                return AuditVerdict.PARTIALLY_SUPPORTED

        if has_tension:
            return AuditVerdict.IN_TENSION

        if has_absence_or_unsupported:
            return AuditVerdict.INSUFFICIENTLY_WARRANTED

        return AuditVerdict.UNRESOLVED

    # -------------------------------------------------------------------------
    # 4. SUPERSESSION LIFECYCLE
    # -------------------------------------------------------------------------

    def supersede_comparison_run(
        self,
        run_id: str,
        superseding_run_id: str,
        reason: ChangeReason = ChangeReason.REANALYSIS,
    ) -> None:
        """Supersede an existing comparison run and mark its constituents SUPERSEDED."""
        run = self.get_comparison_run(run_id)
        if run is None:
            raise ComparisonRunNotFoundError(f"Run '{run_id}' not found.")

        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                UPDATE theological_comparison_runs
                SET status = 'SUPERSEDED'
                WHERE run_id = ?
                """,
                (run_id,),
            )
            conn.execute(
                """
                UPDATE proposition_evidence_audits
                SET status = 'SUPERSEDED'
                WHERE run_id = ?
                """,
                (run_id,),
            )
            conn.execute(
                """
                UPDATE ilzam_critique_records
                SET status = 'SUPERSEDED'
                WHERE run_id = ?
                """,
                (run_id,),
            )

    # -------------------------------------------------------------------------
    # 5. SYMMETRICAL FRAMEWORK COMPARISON
    # -------------------------------------------------------------------------

    def compare_frameworks_symmetrically(
        self,
        framework_ids: Sequence[str],
        pericope_or_passage_id: str,
    ) -> Dict[str, Any]:
        """
        Evaluate multiple frameworks against a passage under identical evidentiary standards.
        Rejects majority voting, consensus ranking, and popularity bias.
        """
        if len(set(framework_ids)) < 2:
            raise AsymmetricalFrameworkEvaluationError(
                "Symmetrical comparison requires at least two distinct frameworks."
            )

        results: Dict[str, Any] = {}
        for fw_id in framework_ids:
            fw = self.get_framework(fw_id)
            if fw is None:
                raise FrameworkNotFoundError(f"Framework '{fw_id}' not found.")

            # Retrieve propositions for this framework
            props = self.get_propositions_for_framework(fw_id)
            framework_runs = []
            for p in props:
                runs = self.get_runs_for_proposition(p.proposition_id)
                for r in runs:
                    audits = self.get_audits_for_run(r.run_id)
                    matching_audits = [
                        a for a in audits if a.target_passage_or_pericope_id == pericope_or_passage_id
                    ]
                    if matching_audits:
                        critiques = self.get_critiques_for_run(r.run_id)
                        framework_runs.append({
                            "proposition": asdict(p),
                            "run": asdict(r),
                            "audits": [asdict(a) for a in matching_audits],
                            "critiques": [asdict(c) for c in critiques],
                        })

            results[fw_id] = {
                "framework": asdict(fw),
                "evaluations": framework_runs,
                "evaluated_symmetrically": True,
            }

        return {
            "target_passage_or_pericope_id": pericope_or_passage_id,
            "framework_count": len(framework_ids),
            "frameworks": results,
            "consensus_privileging_rejected": True,
            "majority_voting_rejected": True,
        }

    # -------------------------------------------------------------------------
    # 6. QUERY & RETRIEVAL APIS
    # -------------------------------------------------------------------------

    def get_framework(self, framework_id: str) -> Optional[TheologicalFrameworkRecord]:
        """Retrieve a theological framework by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT framework_id, framework_name, tradition_family, historical_period,
                       description, canonical_source_corpus, provenance_id, version_id,
                       created_at, metadata_json
                FROM theological_frameworks
                WHERE framework_id = ?
                """,
                (framework_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return TheologicalFrameworkRecord(
                framework_id=row[0],
                framework_name=row[1],
                tradition_family=row[2],
                historical_period=row[3],
                description=row[4],
                canonical_source_corpus=row[5],
                provenance_id=row[6],
                version_id=row[7],
                created_at=row[8],
                metadata=json.loads(row[9]) if row[9] else None,
            )

    def get_proposition(self, proposition_id: str) -> Optional[DogmaticPropositionRecord]:
        """Retrieve a dogmatic proposition by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT proposition_id, framework_id, claim_tier, formulation_title,
                       proposition_text, formal_creedal_source, historical_era,
                       contains_post_biblical_terminology, post_biblical_terms_json,
                       provenance_id, version_id, status, created_at, metadata_json
                FROM dogmatic_propositions
                WHERE proposition_id = ?
                """,
                (proposition_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return DogmaticPropositionRecord(
                proposition_id=row[0],
                framework_id=row[1],
                claim_tier=row[2],
                formulation_title=row[3],
                proposition_text=row[4],
                formal_creedal_source=row[5],
                historical_era=row[6],
                contains_post_biblical_terminology=bool(row[7]),
                post_biblical_terms=json.loads(row[8]) if row[8] else [],
                provenance_id=row[9],
                version_id=row[10],
                status=row[11],
                created_at=row[12],
                metadata=json.loads(row[13]) if row[13] else None,
            )

    def get_propositions_for_framework(self, framework_id: str) -> List[DogmaticPropositionRecord]:
        """Retrieve all propositions for a given framework."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT proposition_id, framework_id, claim_tier, formulation_title,
                       proposition_text, formal_creedal_source, historical_era,
                       contains_post_biblical_terminology, post_biblical_terms_json,
                       provenance_id, version_id, status, created_at, metadata_json
                FROM dogmatic_propositions
                WHERE framework_id = ? AND status = 'ACTIVE'
                ORDER BY created_at ASC
                """,
                (framework_id,),
            )
            records = []
            for row in cursor.fetchall():
                records.append(
                    DogmaticPropositionRecord(
                        proposition_id=row[0],
                        framework_id=row[1],
                        claim_tier=row[2],
                        formulation_title=row[3],
                        proposition_text=row[4],
                        formal_creedal_source=row[5],
                        historical_era=row[6],
                        contains_post_biblical_terminology=bool(row[7]),
                        post_biblical_terms=json.loads(row[8]) if row[8] else [],
                        provenance_id=row[9],
                        version_id=row[10],
                        status=row[11],
                        created_at=row[12],
                        metadata=json.loads(row[13]) if row[13] else None,
                    )
                )
            return records

    def get_comparison_run(self, run_id: str) -> Optional[TheologicalComparisonRunResult]:
        """Retrieve comparison run result by ID."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT run_id, proposition_id, audit_verdict, overall_confidence,
                       status, provenance_id, version_id, input_content_hash,
                       configuration_hash, output_hash, created_at
                FROM theological_comparison_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute("SELECT COUNT(*) FROM proposition_evidence_audits WHERE run_id = ?", (run_id,))
            a_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ilzam_critique_records WHERE run_id = ?", (run_id,))
            c_count = cursor.fetchone()[0]

            return TheologicalComparisonRunResult(
                run_id=row[0],
                proposition_id=row[1],
                audit_verdict=AuditVerdict(row[2]),
                overall_confidence=row[3],
                status=ComparisonRunStatus(row[4]),
                provenance_id=row[5],
                version_id=row[6],
                input_content_hash=row[7],
                configuration_hash=row[8],
                output_hash=row[9],
                audits_count=a_count,
                critiques_count=c_count,
                created_at=row[10],
            )

    def get_runs_for_proposition(self, proposition_id: str) -> List[TheologicalComparisonRunResult]:
        """Retrieve all completed runs for a proposition."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT run_id, proposition_id, audit_verdict, overall_confidence,
                       status, provenance_id, version_id, input_content_hash,
                       configuration_hash, output_hash, created_at
                FROM theological_comparison_runs
                WHERE proposition_id = ? AND status = 'COMPLETED'
                ORDER BY created_at DESC
                """,
                (proposition_id,),
            )
            records = []
            for row in cursor.fetchall():
                cursor.execute("SELECT COUNT(*) FROM proposition_evidence_audits WHERE run_id = ?", (row[0],))
                a_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM ilzam_critique_records WHERE run_id = ?", (row[0],))
                c_count = cursor.fetchone()[0]

                records.append(
                    TheologicalComparisonRunResult(
                        run_id=row[0],
                        proposition_id=row[1],
                        audit_verdict=AuditVerdict(row[2]),
                        overall_confidence=row[3],
                        status=ComparisonRunStatus(row[4]),
                        provenance_id=row[5],
                        version_id=row[6],
                        input_content_hash=row[7],
                        configuration_hash=row[8],
                        output_hash=row[9],
                        audits_count=a_count,
                        critiques_count=c_count,
                        created_at=row[10],
                    )
                )
            return records

    def get_audits_for_run(self, run_id: str) -> List[PropositionEvidenceAuditRecord]:
        """Retrieve all evidence audits for a run."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT audit_id, run_id, proposition_id, deconstructed_premise_text,
                       target_evidence_tier, target_claim_id, target_synthesis_claim_id,
                       target_evidence_id, target_passage_or_pericope_id, alignment_status,
                       evidence_confidence, audit_confidence, is_anachronism_detected,
                       is_identity_collapse_detected, audit_finding_detail,
                       provenance_id, version_id, status, created_at, metadata_json
                FROM proposition_evidence_audits
                WHERE run_id = ?
                ORDER BY created_at ASC
                """,
                (run_id,),
            )
            records = []
            for row in cursor.fetchall():
                records.append(
                    PropositionEvidenceAuditRecord(
                        audit_id=row[0],
                        run_id=row[1],
                        proposition_id=row[2],
                        deconstructed_premise_text=row[3],
                        target_evidence_tier=row[4],
                        target_claim_id=row[5],
                        target_synthesis_claim_id=row[6],
                        target_evidence_id=row[7],
                        target_passage_or_pericope_id=row[8],
                        alignment_status=row[9],
                        evidence_confidence=row[10],
                        audit_confidence=row[11],
                        is_anachronism_detected=bool(row[12]),
                        is_identity_collapse_detected=bool(row[13]),
                        audit_finding_detail=row[14],
                        provenance_id=row[15],
                        version_id=row[16],
                        status=row[17],
                        created_at=row[18],
                        metadata=json.loads(row[19]) if row[19] else None,
                    )
                )
            return records

    def get_critiques_for_run(self, run_id: str) -> List[IlzamCritiqueRecord]:
        """Retrieve all Ilzam critique records for a run."""
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT critique_id, run_id, target_framework_id, target_proposition_id,
                       critique_type, acknowledged_premise_a, acknowledged_premise_b,
                       dependency_chain_json, demonstration_text, critique_severity,
                       is_circularity_rejected, provenance_id, version_id, status,
                       created_at, metadata_json
                FROM ilzam_critique_records
                WHERE run_id = ?
                ORDER BY created_at ASC
                """,
                (run_id,),
            )
            records = []
            for row in cursor.fetchall():
                records.append(
                    IlzamCritiqueRecord(
                        critique_id=row[0],
                        run_id=row[1],
                        target_framework_id=row[2],
                        target_proposition_id=row[3],
                        critique_type=row[4],
                        acknowledged_premise_a=row[5],
                        acknowledged_premise_b=row[6],
                        dependency_chain=json.loads(row[7]) if row[7] else [],
                        demonstration_text=row[8],
                        critique_severity=row[9],
                        is_circularity_rejected=bool(row[10]),
                        provenance_id=row[11],
                        version_id=row[12],
                        status=row[13],
                        created_at=row[14],
                        metadata=json.loads(row[15]) if row[15] else None,
                    )
                )
            return records
