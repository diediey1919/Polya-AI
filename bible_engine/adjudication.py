"""
Evidence Adjudication Subsystem (Task 3.5).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principle:
  NO CONCLUSION MAY OUTRUN ITS EVIDENCE.

Epistemic Firewalls:
  1. Majority vote != truth.
  2. Scholarly or ecclesial consensus != truth.
  3. Fewer supporting sources != justifiable elimination of hypothesis.
  4. Counter-evidence cannot be suppressed or silently omitted.
  5. Absence of evidence != evidence of absence.
  6. Later reception != authorial intent.
  7. Increased source volume != claim tier upgrade.
  8. Incompatible evidence cannot be averaged into artificial consensus.
  9. Confidence aggregation cannot exceed weakest critical dependency.
  10. Lower-tier evidence cannot masquerade as higher-tier evidence.
  11. Competing hypotheses must remain preserved when evidence is inconclusive.
  12. Unresolved conflict is a valid, preserved epistemic state.
  13. Fallacy rejection must be auditable, rule-based, and deterministic.
  14. Immutability enforced by SQL triggers; revisions require supersession.
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
    AdjudicationConcurrencyError,
    AdjudicationImmutabilityError,
    AdjudicationInvalidProvenanceError,
    AdjudicationInvalidVersionError,
    AdjudicationNotFoundError,
    AdjudicationValidationError,
    AnachronisticSemanticInjectionError,
    ConfidenceEscalationError,
    ConsensusAsTruthError,
    EvidenceAdjudicationSubsystemError,
    FallacyDetectedError,
    IllegitimateTotalityTransferError,
    MajorityVoteEpistemologyError,
    RootFallacyError,
    SuppressedCounterEvidenceError,
    UnresolvedConflictSuppressionError,
    UnwarrantedGeneralizationError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class AdjudicationState(str, Enum):
    INITIALIZED = "INITIALIZED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUPERSEDED = "SUPERSEDED"


class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    DEFENDED = "DEFENDED"
    UNDETERMINED = "UNDETERMINED"
    CONTESTED = "CONTESTED"
    DEFEATED = "DEFEATED"
    SUPERSEDED = "SUPERSEDED"


class ConflictType(str, Enum):
    MUTUALLY_EXCLUSIVE = "MUTUALLY_EXCLUSIVE"
    PARTIAL_CONTRADICTION = "PARTIAL_CONTRADICTION"
    TENSION = "TENSION"
    EVIDENTIARY_ASYMMETRY = "EVIDENTIARY_ASYMMETRY"
    UNRESOLVED_DISPUTE = "UNRESOLVED_DISPUTE"


class ConflictSeverity(str, Enum):
    IRRECONCILABLE = "IRRECONCILABLE"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class ResolutionMethod(str, Enum):
    PRIMARY_TEXT_OVER_RECEPTION = "PRIMARY_TEXT_OVER_RECEPTION"
    GRAMMATICAL_DEFEAT = "GRAMMATICAL_DEFEAT"
    WITNESS_APPARATUS_SUPERIORITY = "WITNESS_APPARATUS_SUPERIORITY"
    HISTORICAL_PRIORITY = "HISTORICAL_PRIORITY"
    UNRESOLVED_PRESERVED = "UNRESOLVED_PRESERVED"
    NONE = "NONE"


class FallacyType(str, Enum):
    ILLEGITIMATE_TOTALITY_TRANSFER = "ILLEGITIMATE_TOTALITY_TRANSFER"
    ROOT_FALLACY = "ROOT_FALLACY"
    SEMANTIC_ANACHRONISM = "SEMANTIC_ANACHRONISM"
    UNWARRANTED_GENERALIZATION = "UNWARRANTED_GENERALIZATION"
    MAJORITY_CONSENSUS_FALLACY = "MAJORITY_CONSENSUS_FALLACY"
    CONFIDENCE_ESCALATION_FALLACY = "CONFIDENCE_ESCALATION_FALLACY"
    ABSENCE_AS_PROOF_FALLACY = "ABSENCE_AS_PROOF_FALLACY"
    COUNTER_EVIDENCE_SUPPRESSION_FALLACY = "COUNTER_EVIDENCE_SUPPRESSION_FALLACY"
    AI_BLACK_BOX_FALLACY = "AI_BLACK_BOX_FALLACY"
    RECEPTION_AS_AUTHORIAL_FALLACY = "RECEPTION_AS_AUTHORIAL_FALLACY"


class FallacySeverity(str, Enum):
    FATAL_INVALIDATION = "FATAL_INVALIDATION"
    HIGH_RISK = "HIGH_RISK"
    WARNING = "WARNING"


class VerdictStatus(str, Enum):
    ESTABLISHED_FACT = "ESTABLISHED_FACT"
    PROBABLE_CONCLUSION = "PROBABLE_CONCLUSION"
    COMPETING_INTERPRETATION_PRESERVED = "COMPETING_INTERPRETATION_PRESERVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FALSIFIED_BY_PRIMARY_EVIDENCE = "FALSIFIED_BY_PRIMARY_EVIDENCE"
    INVALIDATED_BY_FALLACY = "INVALIDATED_BY_FALLACY"


def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash for audit and provenance."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


# =============================================================================
# DATA STRUCTURES & DEFINITIONS
# =============================================================================

@dataclass(frozen=True)
class AdjudicationEvidenceItem:
    evidence_id: str
    evidence_class: EvidenceClass
    claim_tier: ClaimTier
    confidence: float
    is_counter_evidence: bool = False
    is_critical_dependency: bool = True
    source_reference: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjudicationHypothesisDefinition:
    hypothesis_code: str
    title: str
    description: str
    claim_tier: ClaimTier
    base_confidence: float
    supporting_evidence_ids: List[str] = field(default_factory=list)
    critical_dependency_ids: List[str] = field(default_factory=list)
    passage_id: Optional[str] = None
    pericope_id: Optional[str] = None
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    is_eliminated: bool = False
    elimination_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjudicationConflictDefinition:
    hypothesis_a_code: str
    hypothesis_b_code: str
    conflict_type: ConflictType
    conflict_severity: ConflictSeverity
    is_resolved: bool = False
    resolution_method: ResolutionMethod = ResolutionMethod.UNRESOLVED_PRESERVED
    resolution_reasoning: str = "Conflict unresolved; competing hypotheses preserved."
    is_majority_vote_applied: bool = False
    is_consensus_equated_truth: bool = False
    is_counter_evidence_suppressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)



@dataclass(frozen=True)
class FallacyFinding:
    audit_id: str
    hypothesis_code: str
    fallacy_type: FallacyType
    violating_inference: str
    evidence_used: List[str]
    applicable_rule: str
    enforcing_firewall: str
    severity: FallacySeverity
    is_fatal: bool
    detected_by: str = "POLYA-FALLACY-FILTER-V2"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjudicationRunConfig:
    adjudicator_id: str = "POLYA-ADJUDICATOR-V2"
    adjudicator_version: str = "2.0.0"
    enforce_strict_firewalls: bool = True
    allow_competing_preservation: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjudicatedVerdictResult:
    verdict_id: str
    hypothesis_id: str
    hypothesis_code: str
    verdict_status: VerdictStatus
    epistemic_tier: ClaimTier
    confidence_score: float
    weakest_critical_dependency_id: Optional[str]
    weakest_critical_confidence: Optional[float]
    supporting_evidence_count: int
    contrary_evidence_count: int
    unresolved_conflict_count: int
    fallacy_count: int
    is_competing_preserved: bool
    verdict_rationale: str
    provenance_id: str
    version_id: str


@dataclass(frozen=True)
class AdjudicationRunResult:
    run_id: str
    version_id: str
    provenance_id: str
    hypothesis_ids: List[str]
    conflict_ids: List[str]
    fallacy_audit_ids: List[str]
    verdict_ids: List[str]
    verdicts: List[AdjudicatedVerdictResult]
    fallacies: List[FallacyFinding]
    output_hash: str
    status: str = "COMPLETED"


# =============================================================================
# DETERMINISTIC FALLACY AUDITOR
# =============================================================================

class FallacyAuditor:
    """Deterministic, rule-based detector for hermeneutical and dialectical fallacies."""

    @staticmethod
    def audit_hypothesis(
        hypothesis: AdjudicationHypothesisDefinition,
        evidence_pool: Dict[str, AdjudicationEvidenceItem],
    ) -> List[FallacyFinding]:
        findings: List[FallacyFinding] = []
        meta = hypothesis.metadata or {}

        # 1. Illegitimate Totality Transfer (ITT)
        # Attempting to read all potential semantic senses or the entire semantic range into a single instance
        if meta.get("assert_all_senses", False) or meta.get("transfers_totality", False):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-ITT-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.ILLEGITIMATE_TOTALITY_TRANSFER,
                    violating_inference="Inferred that because a word can mean multiple senses across the canon, it means all of them in this specific passage.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="A word means what it means in context, not everything it could mean elsewhere (Barr 1961).",
                    enforcing_firewall="IllegitimateTotalityTransferFirewall",
                    severity=FallacySeverity.FATAL_INVALIDATION,
                    is_fatal=True,
                )
            )

        # 2. Root Fallacy
        # Inferring contextual meaning solely or determinatively from etymology/radix
        if meta.get("etymological_derivation_only", False) or meta.get("root_determines_meaning", False):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-ROOT-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.ROOT_FALLACY,
                    violating_inference="Asserted contextual definition strictly based on root etymology despite contrary synchronic usage.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="Etymology is not synonymous with synchronic meaning. The historical root does not dictate the contemporary usage.",
                    enforcing_firewall="RootFallacyFirewall",
                    severity=FallacySeverity.FATAL_INVALIDATION,
                    is_fatal=True,
                )
            )

        # 3. Semantic Anachronism
        # Inverting temporal direction or retrofitting later reception/theology into ancient texts
        has_anachronism = meta.get("injects_later_theology", False) or meta.get("anachronistic_reading", False)
        # Also check if supporting evidence contains only E11/E12 but hypothesis claims T1/T2 original authorial intent
        e11_e12_only = (
            len(hypothesis.supporting_evidence_ids) > 0
            and all(
                evidence_pool.get(eid) is not None
                and evidence_pool[eid].evidence_class in (EvidenceClass.E11_EARLY_RECEPTION, EvidenceClass.E12_LATER_INTERPRETATION)
                for eid in hypothesis.supporting_evidence_ids
            )
        )
        if has_anachronism or (e11_e12_only and hypothesis.claim_tier in (ClaimTier.T1_LINGUISTIC_FACT, ClaimTier.T2_CONTEXTUAL_CLAIM) and not meta.get("reception_claim_only", False)):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-ANACHRONISM-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.SEMANTIC_ANACHRONISM,
                    violating_inference="Later theological formulation or reception tradition retrofitted into original authorial text as a verified ancient fact.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="Later interpretation != original authorial intent. Reception history cannot retroactively redefine ancient source text.",
                    enforcing_firewall="ReceptionAuthorialIntentFirewall",
                    severity=FallacySeverity.FATAL_INVALIDATION,
                    is_fatal=True,
                )
            )

        # 4. Unwarranted Generalization
        # Elevating a localized linguistic or contextual observation (T0/T1/T2) to a sweeping theological dogmatic claim (T4) without intermediate evidence
        if meta.get("unwarranted_generalization", False) or (hypothesis.claim_tier == ClaimTier.T4_THEOLOGICAL_CLAIM and all(
            evidence_pool.get(eid) is not None and evidence_pool[eid].claim_tier in (ClaimTier.T0_RAW_OBSERVATION, ClaimTier.T1_LINGUISTIC_FACT)
            for eid in hypothesis.supporting_evidence_ids
        ) and meta.get("skip_contextual_link", False)):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-GENERALIZATION-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.UNWARRANTED_GENERALIZATION,
                    violating_inference="Generalizing a localized grammatical/lexical observation into an unconstrained universal theological claim.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="Morphology/syntax cannot directly create T4 theological claims without contextual and canonical warrant.",
                    enforcing_firewall="LinguisticTheologyFirewall",
                    severity=FallacySeverity.FATAL_INVALIDATION,
                    is_fatal=True,
                )
            )

        # 5. Majority / Consensus Fallacy
        if meta.get("assert_majority_as_truth", False) or meta.get("consensus_equals_fact", False):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-MAJORITY-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.MAJORITY_CONSENSUS_FALLACY,
                    violating_inference="Asserted that an interpretation is verified textual truth because the majority of commentators or consensus holds it.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="Majority vote or scholarly consensus is not a biblical truth mechanism. Evidence alone decides veracity.",
                    enforcing_firewall="MajorityVoteFirewall",
                    severity=FallacySeverity.FATAL_INVALIDATION,
                    is_fatal=True,
                )
            )

        # 6. Absence as Proof Fallacy
        if meta.get("absence_as_proof", False):
            findings.append(
                FallacyFinding(
                    audit_id=f"FALLACY-ABSENCE-{hypothesis.hypothesis_code}",
                    hypothesis_code=hypothesis.hypothesis_code,
                    fallacy_type=FallacyType.ABSENCE_AS_PROOF_FALLACY,
                    violating_inference="Asserted non-existence or defect solely from lack of positive mention in a limited corpus.",
                    evidence_used=hypothesis.supporting_evidence_ids,
                    applicable_rule="Absence of evidence is not evidence of absence without proven exhaustive documentation.",
                    enforcing_firewall="AbsenceAsProofFirewall",
                    severity=FallacySeverity.HIGH_RISK,
                    is_fatal=False,
                )
            )

        return findings


# =============================================================================
# EVIDENCE ADJUDICATION MANAGER (Task 3.5 Core Engine)
# =============================================================================

class EvidenceAdjudicationManager:
    """Core Manager for the Evidence Adjudication Subsystem (Task 3.5)."""

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: VersionManager,
        provenance_tracker: ProvenanceTracker,
        evidence_claim_manager: EvidenceClaimManager,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager
        self.provenance_tracker = provenance_tracker
        self.evidence_claim_manager = evidence_claim_manager

    # -------------------------------------------------------------------------
    # CONFIDENCE & WEAKEST CRITICAL DEPENDENCY PROPAGATION
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_propagated_confidence(
        base_confidence: float,
        critical_evidence_items: Sequence[AdjudicationEvidenceItem],
    ) -> Tuple[float, Optional[str], Optional[float]]:
        """
        Enforce Weakest-Critical-Dependency confidence propagation.
        Compound hypothesis confidence MUST NOT exceed the weakest critical dependency or base confidence.
        """
        if not critical_evidence_items:
            res_conf = round(base_confidence, 4)
            if res_conf > base_confidence:
                res_conf = base_confidence
            return res_conf, None, None

        weakest_item: Optional[AdjudicationEvidenceItem] = None
        min_conf = float("inf")

        for ev in critical_evidence_items:
            if ev.is_critical_dependency:
                if ev.confidence < min_conf:
                    min_conf = ev.confidence
                    weakest_item = ev

        if weakest_item is None:
            res_conf = round(base_confidence, 4)
            if res_conf > base_confidence:
                res_conf = base_confidence
            return res_conf, None, None

        # Propagated confidence is strictly bounded by weakest critical confidence and base confidence
        propagated = min(base_confidence, min_conf)
        res_conf = round(propagated, 4)
        if res_conf > base_confidence:
            res_conf = base_confidence
        if res_conf > min_conf:
            res_conf = min_conf
        return res_conf, weakest_item.evidence_id, round(weakest_item.confidence, 4)

    # -------------------------------------------------------------------------
    # MAIN ADJUDICATION EXECUTION PIPELINE
    # -------------------------------------------------------------------------

    def execute_adjudication_run(
        self,
        target_passage_id: Optional[str],
        target_pericope_id: Optional[str],
        hypotheses: Sequence[AdjudicationHypothesisDefinition],
        conflicts: Sequence[AdjudicationConflictDefinition],
        evidence_pool: Sequence[AdjudicationEvidenceItem],
        config: Optional[AdjudicationRunConfig] = None,
        run_id: Optional[str] = None,
    ) -> AdjudicationRunResult:
        """
        Execute an atomic, immutable evidence adjudication run.
        Evaluates competing hypotheses, cross-examines conflicts, detects fallacies,
        and generates calibrated verdicts without majority vote or evidence suppression.
        """
        if not target_passage_id and not target_pericope_id:
            raise AdjudicationValidationError("Adjudication run must specify target_passage_id or target_pericope_id.")

        if not hypotheses:
            raise AdjudicationValidationError("Adjudication run must contain at least one hypothesis.")

        cfg = config or AdjudicationRunConfig()
        ev_map: Dict[str, AdjudicationEvidenceItem] = {ev.evidence_id: ev for ev in evidence_pool}

        # 1. Epistemic Pre-Flight Validation (Firewalls)
        for conflict in conflicts:
            if conflict.is_majority_vote_applied:
                raise MajorityVoteEpistemologyError(
                    f"Majority vote cannot be applied in conflict resolution: {conflict.hypothesis_a_code} vs {conflict.hypothesis_b_code}"
                )
            if conflict.is_consensus_equated_truth:
                raise ConsensusAsTruthError(
                    f"Consensus cannot be equated to truth in conflict: {conflict.hypothesis_a_code} vs {conflict.hypothesis_b_code}"
                )
            if conflict.is_counter_evidence_suppressed:
                raise SuppressedCounterEvidenceError(
                    f"Counter-evidence suppression detected in conflict: {conflict.hypothesis_a_code} vs {conflict.hypothesis_b_code}"
                )
            if "majority" in (conflict.resolution_reasoning or "").lower() and conflict.resolution_method != ResolutionMethod.UNRESOLVED_PRESERVED:
                raise MajorityVoteEpistemologyError(
                    f"Reasoning relies on majority vote: {conflict.resolution_reasoning}"
                )
            if "consensus" in (conflict.resolution_reasoning or "").lower() and "text" not in (conflict.resolution_reasoning or "").lower() and conflict.resolution_method != ResolutionMethod.UNRESOLVED_PRESERVED:
                raise ConsensusAsTruthError(
                    f"Reasoning relies on consensus as truth: {conflict.resolution_reasoning}"
                )

        # Check for premature elimination or suppression of hypotheses
        hyp_codes = {h.hypothesis_code for h in hypotheses}
        if len(hyp_codes) != len(hypotheses):
            raise AdjudicationValidationError("Duplicate hypothesis_code detected in adjudication run.")

        for hyp in hypotheses:
            if hyp.is_eliminated:
                if not hyp.elimination_reason or len(hyp.elimination_reason.strip()) == 0:
                    raise UnresolvedConflictSuppressionError(
                        f"Hypothesis {hyp.hypothesis_code} was eliminated without documented evidentiary justification."
                    )
                if "fewer sources" in hyp.elimination_reason.lower() or "minority" in hyp.elimination_reason.lower():
                    raise MajorityVoteEpistemologyError(
                        f"Hypothesis {hyp.hypothesis_code} eliminated based on source quantity or minority status: {hyp.elimination_reason}"
                    )

        # 2. Deterministic Fallacy Audit
        all_fallacies: List[FallacyFinding] = []
        for hyp in hypotheses:
            findings = FallacyAuditor.audit_hypothesis(hyp, ev_map)
            for f in findings:
                all_fallacies.append(f)
                if cfg.enforce_strict_firewalls and f.is_fatal:
                    if f.fallacy_type == FallacyType.ILLEGITIMATE_TOTALITY_TRANSFER:
                        raise IllegitimateTotalityTransferError(f.violating_inference)
                    elif f.fallacy_type == FallacyType.ROOT_FALLACY:
                        raise RootFallacyError(f.violating_inference)
                    elif f.fallacy_type == FallacyType.SEMANTIC_ANACHRONISM:
                        raise AnachronisticSemanticInjectionError(f.violating_inference)
                    elif f.fallacy_type == FallacyType.UNWARRANTED_GENERALIZATION:
                        raise UnwarrantedGeneralizationError(f.violating_inference)
                    elif f.fallacy_type == FallacyType.MAJORITY_CONSENSUS_FALLACY:
                        raise MajorityVoteEpistemologyError(f.violating_inference)

        # Map fallacies per hypothesis
        fallacies_by_hyp: Dict[str, List[FallacyFinding]] = {}
        for f in all_fallacies:
            fallacies_by_hyp.setdefault(f.hypothesis_code, []).append(f)

        # 3. Conflict Map & Unresolved Conflict Counts
        conflict_map: Dict[str, List[AdjudicationConflictDefinition]] = {}
        for c in conflicts:
            conflict_map.setdefault(c.hypothesis_a_code, []).append(c)
            conflict_map.setdefault(c.hypothesis_b_code, []).append(c)

        # 4. Generate Identifiers & Provenance Hashes
        now = datetime.now(timezone.utc).isoformat()
        run_id = run_id or f"ADJ-RUN-{compute_canonical_hash({'p': target_passage_id, 'pe': target_pericope_id, 't': now})[:16]}"
        input_hash = compute_canonical_hash({
            "target_passage_id": target_passage_id,
            "target_pericope_id": target_pericope_id,
            "hypotheses": [asdict(h) for h in hypotheses],
            "conflicts": [asdict(c) for c in conflicts],
            "evidence": [asdict(e) for e in evidence_pool],
        })
        cfg_hash = compute_canonical_hash(asdict(cfg))

        run_prov_id = f"PROV-{run_id}"
        run_ver_id = f"VER-{run_id}"

        # 5. Adjudicate Verdicts
        verdict_results: List[AdjudicatedVerdictResult] = []
        db_hyp_records: List[Dict[str, Any]] = []
        db_conf_records: List[Dict[str, Any]] = []
        db_fallacy_records: List[Dict[str, Any]] = []
        db_verdict_records: List[Dict[str, Any]] = []

        hyp_id_map: Dict[str, str] = {}
        hyp_dict: Dict[str, AdjudicationHypothesisDefinition] = {
            h.hypothesis_code: h for h in hypotheses
        }

        for hyp in hypotheses:
            h_id = f"HYP-{run_id}-{hyp.hypothesis_code}"
            hyp_id_map[hyp.hypothesis_code] = h_id

            # Gather critical evidence items
            crit_items: List[AdjudicationEvidenceItem] = []
            for eid in hyp.critical_dependency_ids:
                if eid not in ev_map:
                    raise AdjudicationValidationError(
                        f"Critical dependency evidence ID '{eid}' for hypothesis '{hyp.hypothesis_code}' not found in evidence pool."
                    )
                crit_items.append(ev_map[eid])

            # Gather all supporting items
            supp_items: List[AdjudicationEvidenceItem] = []
            for eid in hyp.supporting_evidence_ids:
                if eid in ev_map:
                    supp_items.append(ev_map[eid])

            # Calculate weakest critical dependency
            prop_conf, weakest_id, weakest_conf = self.calculate_propagated_confidence(
                hyp.base_confidence,
                crit_items if crit_items else supp_items,
            )
            # Ensure propagated confidence never exceeds base confidence
            prop_conf = min(prop_conf, hyp.base_confidence)

            # Epistemic firewall: propagated confidence cannot exceed base confidence or weakest critical
            if weakest_conf is not None and prop_conf > weakest_conf:
                raise ConfidenceEscalationError(
                    f"Propagated confidence {prop_conf} exceeds weakest critical dependency {weakest_conf}"
                )

            # Map confidence level
            if prop_conf >= 0.90:
                conf_level = ConfidenceLevel.CERTAIN.value
            elif prop_conf >= 0.75:
                conf_level = ConfidenceLevel.VERY_HIGH.value
            elif prop_conf >= 0.60:
                conf_level = ConfidenceLevel.HIGH.value
            elif prop_conf >= 0.40:
                conf_level = ConfidenceLevel.MEDIUM.value
            elif prop_conf >= 0.20:
                conf_level = ConfidenceLevel.LOW.value
            else:
                conf_level = ConfidenceLevel.UNSUPPORTED.value

            hyp_prov_id = f"PROV-{h_id}"
            hyp_ver_id = f"VER-{h_id}"

            db_hyp_records.append({
                "hypothesis_id": h_id,
                "run_id": run_id,
                "passage_id": hyp.passage_id or target_passage_id,
                "pericope_id": hyp.pericope_id or target_pericope_id,
                "hypothesis_code": hyp.hypothesis_code,
                "title": hyp.title,
                "description": hyp.description,
                "claim_tier": hyp.claim_tier.value,
                "base_confidence": hyp.base_confidence,
                "propagated_confidence": prop_conf,
                "confidence_level": conf_level,
                "status": hyp.status.value,
                "is_eliminated": 1 if hyp.is_eliminated else 0,
                "elimination_reason": hyp.elimination_reason,
                "provenance_id": hyp_prov_id,
                "version_id": hyp_ver_id,
                "created_at": now,
                "metadata_json": json.dumps(hyp.metadata, sort_keys=True) if hyp.metadata else None,
            })

            # Check contrary evidence:
            # 1. Any counter-evidence in supporting_evidence_ids
            # 2. Any counter-evidence in evidence_pool targeting this hypothesis or general
            # 3. Supporting evidence from conflicting hypotheses with unresolved conflicts
            contrary_items = set()
            for eid in hyp.supporting_evidence_ids:
                if eid in ev_map and ev_map[eid].is_counter_evidence:
                    contrary_items.add(eid)

            for ev in evidence_pool:
                if ev.is_counter_evidence:
                    target_code = ev.metadata.get("target_hypothesis_code") or ev.metadata.get("counter_hypothesis_code")
                    if target_code is None or target_code == hyp.hypothesis_code:
                        contrary_items.add(ev.evidence_id)

            hyp_conflicts = conflict_map.get(hyp.hypothesis_code, [])
            unresolved_conflicts = [
                c for c in hyp_conflicts
                if not c.is_resolved or c.resolution_method == ResolutionMethod.UNRESOLVED_PRESERVED
            ]

            for conf in unresolved_conflicts:
                other_code = conf.hypothesis_b_code if conf.hypothesis_a_code == hyp.hypothesis_code else conf.hypothesis_a_code
                other_hyp = hyp_dict.get(other_code)
                if other_hyp:
                    for s_eid in other_hyp.supporting_evidence_ids:
                        if s_eid in ev_map:
                            contrary_items.add(s_eid)

            contrary_count = len(contrary_items)

            hyp_fallacies = fallacies_by_hyp.get(hyp.hypothesis_code, [])
            has_fatal_fallacy = any(f.is_fatal for f in hyp_fallacies)

            # Determine Verdict Status
            if has_fatal_fallacy:
                v_status = VerdictStatus.INVALIDATED_BY_FALLACY
                v_rationale = f"Hypothesis invalidated by detected hermeneutical fallacy: {[f.fallacy_type.value for f in hyp_fallacies]}."
            elif len(hyp_fallacies) > 0:
                v_status = VerdictStatus.INSUFFICIENT_EVIDENCE
                v_rationale = f"Hypothesis burdened by detected fallacy risk: {[f.fallacy_type.value for f in hyp_fallacies]}; blocked from established/probable status."
            elif hyp.is_eliminated:
                v_status = VerdictStatus.FALSIFIED_BY_PRIMARY_EVIDENCE
                v_rationale = f"Hypothesis eliminated on verified evidentiary grounds: {hyp.elimination_reason}."
            elif contrary_count > 0 or len(unresolved_conflicts) > 0:
                # Epistemic Rule: Competing interpretations must be preserved when contrary evidence or dispute exists
                v_status = VerdictStatus.COMPETING_INTERPRETATION_PRESERVED
                v_rationale = (
                    f"Preserved as competing interpretation. Has {len(unresolved_conflicts)} active unresolved conflicts "
                    f"and {contrary_count} contrary evidence points. No consensus manufactured."
                )
            elif prop_conf >= 0.90 and len(supp_items) > 0:
                # Check that no contrary evidence exists anywhere for this passage
                v_status = VerdictStatus.ESTABLISHED_FACT
                v_rationale = f"Established on conclusive primary linguistic/textual evidence with {len(supp_items)} supporting items."
            elif prop_conf >= 0.60:
                v_status = VerdictStatus.PROBABLE_CONCLUSION
                v_rationale = f"Probable conclusion supported by evidence; uncertainty preserved at confidence {prop_conf}."
            else:
                v_status = VerdictStatus.INSUFFICIENT_EVIDENCE
                v_rationale = f"Insufficient evidence to establish hypothesis (confidence {prop_conf})."

            verdict_id = f"VRD-{run_id}-{hyp.hypothesis_code}"
            v_prov_id = f"PROV-{verdict_id}"
            v_ver_id = f"VER-{verdict_id}"

            db_verdict_records.append({
                "verdict_id": verdict_id,
                "run_id": run_id,
                "hypothesis_id": h_id,
                "hypothesis_code": hyp.hypothesis_code,
                "verdict_status": v_status.value,
                "epistemic_tier": hyp.claim_tier.value,
                "confidence_score": prop_conf,
                "weakest_critical_dependency_id": weakest_id,
                "weakest_critical_confidence": weakest_conf,
                "supporting_evidence_count": len(supp_items),
                "contrary_evidence_count": contrary_count,
                "unresolved_conflict_count": len(unresolved_conflicts),
                "fallacy_count": len(hyp_fallacies),
                "is_consensus_derived": 0,
                "is_majority_vote_derived": 0,
                "is_competing_preserved": 1 if v_status == VerdictStatus.COMPETING_INTERPRETATION_PRESERVED else 0,
                "verdict_rationale": v_rationale,
                "provenance_id": v_prov_id,
                "version_id": v_ver_id,
                "created_at": now,
                "metadata_json": None,
            })

        # Process Conflicts
        for c in conflicts:
            h_a = hyp_id_map.get(c.hypothesis_a_code)
            h_b = hyp_id_map.get(c.hypothesis_b_code)
            if not h_a or not h_b:
                raise AdjudicationValidationError(
                    f"Conflict references unknown hypothesis code: {c.hypothesis_a_code} or {c.hypothesis_b_code}"
                )
            c_id = f"CONF-{run_id}-{c.hypothesis_a_code}-{c.hypothesis_b_code}"
            db_conf_records.append({
                "conflict_id": c_id,
                "run_id": run_id,
                "hypothesis_a_id": h_a,
                "hypothesis_b_id": h_b,
                "conflict_type": c.conflict_type.value,
                "conflict_severity": c.conflict_severity.value,
                "is_resolved": 1 if c.resolution_method not in (ResolutionMethod.UNRESOLVED_PRESERVED, ResolutionMethod.NONE) else 0,
                "resolution_method": c.resolution_method.value,
                "resolution_reasoning": c.resolution_reasoning,
                "is_majority_vote_applied": 0,
                "is_consensus_equated_truth": 0,
                "is_counter_evidence_suppressed": 0,
                "created_at": now,
                "metadata_json": json.dumps(c.metadata, sort_keys=True) if c.metadata else None,
            })

        # Process Fallacy Records
        for f in all_fallacies:
            h_id = hyp_id_map.get(f.hypothesis_code)
            if not h_id:
                continue
            db_fallacy_records.append({
                "audit_id": f.audit_id,
                "run_id": run_id,
                "hypothesis_id": h_id,
                "fallacy_type": f.fallacy_type.value,
                "violating_inference": f.violating_inference,
                "evidence_used_json": json.dumps(f.evidence_used, sort_keys=True),
                "applicable_rule": f.applicable_rule,
                "enforcing_firewall": f.enforcing_firewall,
                "severity": f.severity.value,
                "is_fatal": 1 if f.is_fatal else 0,
                "detected_by": f.detected_by,
                "created_at": now,
                "metadata_json": json.dumps(f.metadata, sort_keys=True) if f.metadata else None,
            })

        output_payload = {
            "run_id": run_id,
            "verdicts": [
                {
                    "verdict_id": vr["verdict_id"],
                    "hypothesis_id": vr["hypothesis_id"],
                    "hypothesis_code": vr["hypothesis_code"],
                    "verdict_status": vr["verdict_status"],
                    "epistemic_tier": vr["epistemic_tier"],
                    "confidence_score": vr["confidence_score"],
                    "weakest_critical_dependency_id": vr["weakest_critical_dependency_id"],
                    "weakest_critical_confidence": vr["weakest_critical_confidence"],
                    "supporting_evidence_count": vr["supporting_evidence_count"],
                    "contrary_evidence_count": vr["contrary_evidence_count"],
                    "unresolved_conflict_count": vr["unresolved_conflict_count"],
                    "fallacy_count": vr["fallacy_count"],
                    "is_competing_preserved": vr["is_competing_preserved"],
                    "verdict_rationale": vr["verdict_rationale"],
                }
                for vr in db_verdict_records
            ],
            "fallacies": [asdict(f) for f in all_fallacies],
        }
        output_hash = compute_canonical_hash(output_payload)

        # 6. Atomic Transaction Commit with Provenance & Versioning
        with self.engine.transaction() as conn:
            # Create Run Version & Provenance
            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=run_id,
                content=f"ADJUDICATION_RUN:{run_id}:{output_hash}",
                input_data=input_hash,
                agent_id=cfg.adjudicator_id,
                agent_version=cfg.adjudicator_version,
                conn=conn,
            )
            run_prov_id = prov_rec.provenance_id

            new_version = self.version_manager.create_version(
                object_type="ADJUDICATION_RUN",
                object_id=run_id,
                content_hash=output_hash,
                provenance_id=run_prov_id,
                change_reason=ChangeReason.INITIAL_CREATION,
                created_by=cfg.adjudicator_id,
                conn=conn,
            )
            run_ver_id = new_version.version_id

            # Insert Run Record
            conn.execute(
                """
                INSERT INTO adjudication_runs (
                    run_id, target_passage_id, target_pericope_id, version_id, provenance_id,
                    adjudicator_id, adjudicator_version, configuration_hash, input_content_hash,
                    output_hash, status, is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?)
                """,
                (
                    run_id,
                    target_passage_id,
                    target_pericope_id,
                    run_ver_id,
                    run_prov_id,
                    cfg.adjudicator_id,
                    cfg.adjudicator_version,
                    cfg_hash,
                    input_hash,
                    output_hash,
                    now,
                    json.dumps(cfg.metadata, sort_keys=True) if cfg.metadata else None,
                ),
            )

            # Insert Hypotheses
            for hr in db_hyp_records:
                hyp_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.CLAIM,
                    target_id=hr["hypothesis_id"],
                    content=f"HYPOTHESIS:{hr['hypothesis_id']}:{hr['hypothesis_code']}",
                    parent_provenance_id=run_prov_id,
                    agent_id=cfg.adjudicator_id,
                    agent_version=cfg.adjudicator_version,
                    conn=conn,
                )
                hyp_ver_id = f"VER-{hr['hypothesis_id']}"
                hr["provenance_id"] = hyp_prov.provenance_id
                hr["version_id"] = hyp_ver_id
                hr["is_immutable"] = 1

                hyp_ver = self.version_manager.create_version(
                    object_type="ADJUDICATION_HYPOTHESIS",
                    object_id=hr["hypothesis_id"],
                    content_hash=compute_canonical_hash(hr),
                    version_id=hyp_ver_id,
                    provenance_id=hyp_prov.provenance_id,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    created_by=cfg.adjudicator_id,
                    conn=conn,
                )

                conn.execute(
                    """
                    INSERT INTO adjudication_hypotheses (
                        hypothesis_id, run_id, passage_id, pericope_id, hypothesis_code,
                        title, description, claim_tier, base_confidence, propagated_confidence,
                        confidence_level, status, is_eliminated, elimination_reason,
                        provenance_id, version_id, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        hr["hypothesis_id"],
                        hr["run_id"],
                        hr["passage_id"],
                        hr["pericope_id"],
                        hr["hypothesis_code"],
                        hr["title"],
                        hr["description"],
                        hr["claim_tier"],
                        hr["base_confidence"],
                        hr["propagated_confidence"],
                        hr["confidence_level"],
                        hr["status"],
                        hr["is_eliminated"],
                        hr["elimination_reason"],
                        hr["provenance_id"],
                        hr["version_id"],
                        hr["created_at"],
                        hr["metadata_json"],
                    ),
                )

            # Insert Conflicts
            for cr in db_conf_records:
                conn.execute(
                    """
                    INSERT INTO adjudication_conflicts (
                        conflict_id, run_id, hypothesis_a_id, hypothesis_b_id,
                        conflict_type, conflict_severity, is_resolved, resolution_method,
                        resolution_reasoning, is_majority_vote_applied, is_consensus_equated_truth,
                        is_counter_evidence_suppressed, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, 1, ?)
                    """,
                    (
                        cr["conflict_id"],
                        cr["run_id"],
                        cr["hypothesis_a_id"],
                        cr["hypothesis_b_id"],
                        cr["conflict_type"],
                        cr["conflict_severity"],
                        cr["is_resolved"],
                        cr["resolution_method"],
                        cr["resolution_reasoning"],
                        cr["created_at"],
                        cr["metadata_json"],
                    ),
                )

            # Insert Fallacy Records
            for fr in db_fallacy_records:
                conn.execute(
                    """
                    INSERT INTO fallacy_audit_records (
                        audit_id, run_id, hypothesis_id, fallacy_type, violating_inference,
                        evidence_used_json, applicable_rule, enforcing_firewall,
                        severity, is_fatal, detected_by, created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        fr["audit_id"],
                        fr["run_id"],
                        fr["hypothesis_id"],
                        fr["fallacy_type"],
                        fr["violating_inference"],
                        fr["evidence_used_json"],
                        fr["applicable_rule"],
                        fr["enforcing_firewall"],
                        fr["severity"],
                        fr["is_fatal"],
                        fr["detected_by"],
                        fr["created_at"],
                        fr["metadata_json"],
                    ),
                )

            # Insert Verdicts
            final_verdicts: List[AdjudicatedVerdictResult] = []
            for vr in db_verdict_records:
                verd_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=vr["verdict_id"],
                    content=f"VERDICT:{vr['verdict_id']}:{vr['verdict_status']}",
                    parent_provenance_id=run_prov_id,
                    agent_id=cfg.adjudicator_id,
                    agent_version=cfg.adjudicator_version,
                    conn=conn,
                )
                verd_ver_id = f"VER-{vr['verdict_id']}"
                vr["provenance_id"] = verd_prov.provenance_id
                vr["version_id"] = verd_ver_id
                vr["is_consensus_derived"] = 0
                vr["is_majority_vote_derived"] = 0
                vr["is_immutable"] = 1

                # Construct record dictionary matching exact DB schema for canonical content hash
                db_vr_record = {
                    "verdict_id": vr["verdict_id"],
                    "run_id": vr["run_id"],
                    "hypothesis_id": vr["hypothesis_id"],
                    "verdict_status": vr["verdict_status"],
                    "epistemic_tier": vr["epistemic_tier"],
                    "confidence_score": vr["confidence_score"],
                    "weakest_critical_dependency_id": vr["weakest_critical_dependency_id"],
                    "weakest_critical_confidence": vr["weakest_critical_confidence"],
                    "supporting_evidence_count": vr["supporting_evidence_count"],
                    "contrary_evidence_count": vr["contrary_evidence_count"],
                    "unresolved_conflict_count": vr["unresolved_conflict_count"],
                    "fallacy_count": vr["fallacy_count"],
                    "is_consensus_derived": 0,
                    "is_majority_vote_derived": 0,
                    "is_competing_preserved": vr["is_competing_preserved"],
                    "verdict_rationale": vr["verdict_rationale"],
                    "provenance_id": vr["provenance_id"],
                    "version_id": vr["version_id"],
                    "created_at": vr["created_at"],
                    "is_immutable": 1,
                    "metadata_json": vr["metadata_json"],
                }

                verd_ver = self.version_manager.create_version(
                    object_type="ADJUDICATED_VERDICT",
                    object_id=vr["verdict_id"],
                    content_hash=compute_canonical_hash(db_vr_record),
                    version_id=verd_ver_id,
                    provenance_id=verd_prov.provenance_id,
                    change_reason=ChangeReason.INITIAL_CREATION,
                    created_by=cfg.adjudicator_id,
                    conn=conn,
                )

                conn.execute(
                    """
                    INSERT INTO adjudicated_verdicts (
                        verdict_id, run_id, hypothesis_id, verdict_status, epistemic_tier,
                        confidence_score, weakest_critical_dependency_id, weakest_critical_confidence,
                        supporting_evidence_count, contrary_evidence_count, unresolved_conflict_count,
                        fallacy_count, is_consensus_derived, is_majority_vote_derived,
                        is_competing_preserved, verdict_rationale, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        vr["verdict_id"],
                        vr["run_id"],
                        vr["hypothesis_id"],
                        vr["verdict_status"],
                        vr["epistemic_tier"],
                        vr["confidence_score"],
                        vr["weakest_critical_dependency_id"],
                        vr["weakest_critical_confidence"],
                        vr["supporting_evidence_count"],
                        vr["contrary_evidence_count"],
                        vr["unresolved_conflict_count"],
                        vr["fallacy_count"],
                        vr["is_competing_preserved"],
                        vr["verdict_rationale"],
                        vr["provenance_id"],
                        vr["version_id"],
                        vr["created_at"],
                        vr["metadata_json"],
                    ),
                )

                final_verdicts.append(
                    AdjudicatedVerdictResult(
                        verdict_id=vr["verdict_id"],
                        hypothesis_id=vr["hypothesis_id"],
                        hypothesis_code=vr["hypothesis_code"],
                        verdict_status=VerdictStatus(vr["verdict_status"]),
                        epistemic_tier=ClaimTier(vr["epistemic_tier"]),
                        confidence_score=vr["confidence_score"],
                        weakest_critical_dependency_id=vr["weakest_critical_dependency_id"],
                        weakest_critical_confidence=vr["weakest_critical_confidence"],
                        supporting_evidence_count=vr["supporting_evidence_count"],
                        contrary_evidence_count=vr["contrary_evidence_count"],
                        unresolved_conflict_count=vr["unresolved_conflict_count"],
                        fallacy_count=vr["fallacy_count"],
                        is_competing_preserved=bool(vr["is_competing_preserved"]),
                        verdict_rationale=vr["verdict_rationale"],
                        provenance_id=vr["provenance_id"],
                        version_id=vr["version_id"],
                    )
                )

        return AdjudicationRunResult(
            run_id=run_id,
            version_id=run_ver_id,
            provenance_id=run_prov_id,
            hypothesis_ids=[hr["hypothesis_id"] for hr in db_hyp_records],
            conflict_ids=[cr["conflict_id"] for cr in db_conf_records],
            fallacy_audit_ids=[fr["audit_id"] for fr in db_fallacy_records],
            verdict_ids=[vr["verdict_id"] for vr in db_verdict_records],
            verdicts=final_verdicts,
            fallacies=all_fallacies,
            output_hash=output_hash,
            status="COMPLETED",
        )

    # -------------------------------------------------------------------------
    # QUERY & INSPECTION APIS
    # -------------------------------------------------------------------------

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve adjudication run by ID."""
        with self.engine.transaction() as conn:
            cursor = conn.execute("SELECT * FROM adjudication_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve adjudication hypothesis by ID."""
        with self.engine.transaction() as conn:
            cursor = conn.execute("SELECT * FROM adjudication_hypotheses WHERE hypothesis_id = ?", (hypothesis_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    def get_hypotheses_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all hypotheses belonging to an adjudication run."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM adjudication_hypotheses WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_conflicts_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all conflicts recorded in an adjudication run."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM adjudication_conflicts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_fallacies_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all detected fallacies in an adjudication run."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM fallacy_audit_records WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_verdicts_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all verdicts produced by an adjudication run."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM adjudicated_verdicts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
