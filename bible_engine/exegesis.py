"""
Exegesis Foundation Subsystem (Task 2.9).
Specification: Architecture v2.0 — FROZEN.

Core principle: NO CONCLUSION MAY OUTRUN ITS EVIDENCE.

Epistemic Pipeline:
  OBSERVATION
  → LINGUISTIC_FACT
  → CONTEXTUAL_FACT
  → CLAIM
  → HYPOTHESIS
  → COMPETING_INTERPRETATIONS
  → EVIDENCE_AUDIT
  → CALIBRATED_CONCLUSION

Critical rules:
  1. EXEGESIS MUST NOT:
     - rewrite source text
     - rewrite morphology
     - rewrite syntax
     - rewrite semantic senses
     - rewrite entity identity
     - promote translation into source evidence
     - convert confidence into evidence
     - convert model agreement into truth
     - suppress competing interpretations
     - suppress counter-evidence
     - silently resolve ambiguity
     - create STRICT_IDENTITY without independent evidence
     - directly manufacture unsupported T4 theology
  2. Pericope is the primary exegesis unit. Verse remains reference unit.
  3. Competing interpretations must coexist; no majority vote.
  4. Final calibrated conclusion preserves: supporting evidence, counter-evidence,
     unresolved ambiguity, weakest critical dependency, confidence, and provenance.
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
    CalibratedConclusionNotFoundError,
    CompetingInterpretationNotFoundError,
    ConfidenceAsEvidenceFirewallError,
    ConfidenceUpgradeFirewallError,
    DuplicateExegesisError,
    EvidenceAuditNotFoundError,
    EvidenceConfidenceError,
    EvidenceNotFoundError,
    ExegesisDiscourseTheologyFirewallError,
    ExegesisEntityIdentityFirewallError,
    ExegesisImmutabilityError,
    ExegesisInvalidProvenanceError,
    ExegesisInvalidVersionError,
    ExegesisMorphologyTheologyFirewallError,
    ExegesisOrphanError,
    ExegesisRunNotFoundError,
    ExegesisSemanticTheologyFirewallError,
    ExegesisSubsystemError,
    ExegesisSyntaxTheologyFirewallError,
    HypothesisNotFoundError,
    InterpretationWithoutEvidenceFirewallError,
    InvalidClaimTierError,
    InvalidEvidenceRelationshipError,
    MissingProvenanceError,
    ModelMajorityTruthFirewallError,
    ObservationNotFoundError,
    PericopePrimaryUnitFirewallError,
    SilentAmbiguityResolutionFirewallError,
    SourceTextNotFoundError,
    StrictIdentityEvidenceFirewallError,
    SuppressionOfCompetingInterpretationFirewallError,
    SuppressionOfCounterEvidenceFirewallError,
    TranslationAsSourceFirewallError,
    UnresolvedContradictionFirewallError,
    UnresolvedIssueNotFoundError,
    UnsupportedConclusionFirewallError,
)
from bible_engine.evidence_claim import ClaimTier, coerce_claim_tier
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class InterpretationState(str, Enum):
    """Explicit interpretation lifecycle states."""
    PROPOSED = "PROPOSED"
    SUPPORTED = "SUPPORTED"
    QUALIFIED = "QUALIFIED"
    CONTESTED = "CONTESTED"
    REJECTED = "REJECTED"
    UNRESOLVED = "UNRESOLVED"


class AuditRelationship(str, Enum):
    """Audit evidence evaluation relationship."""
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    QUALIFY = "QUALIFY"
    LIMIT = "LIMIT"
    REFINE = "REFINE"


class TensionType(str, Enum):
    """Taxonomy of tensions between competing interpretations."""
    MUTUALLY_EXCLUSIVE = "MUTUALLY_EXCLUSIVE"
    ALTERNATIVE_READING = "ALTERNATIVE_READING"
    SEMANTIC_AMBIGUITY = "SEMANTIC_AMBIGUITY"
    SYNTACTIC_AMBIGUITY = "SYNTACTIC_AMBIGUITY"
    REFERENTIAL_AMBIGUITY = "REFERENTIAL_AMBIGUITY"
    DIALECTICAL_TENSION = "DIALECTICAL_TENSION"


class IssueType(str, Enum):
    """Controlled taxonomy of unresolved exegesis issues."""
    AMBIGUITY = "AMBIGUITY"
    TEXTUAL_VARIANT = "TEXTUAL_VARIANT"
    UNRESOLVED_CONTRADICTION = "UNRESOLVED_CONTRADICTION"
    UNRESOLVED_COUNTER_EVIDENCE = "UNRESOLVED_COUNTER_EVIDENCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNSUPPORTED_LEAP = "UNSUPPORTED_LEAP"


class ObservationType(str, Enum):
    """Types of exegesis observations."""
    RAW_OBSERVATION = "RAW_OBSERVATION"
    TEXTUAL_VARIANT = "TEXTUAL_VARIANT"
    GRAMMATICAL_FEATURE = "GRAMMATICAL_FEATURE"
    LEXICAL_OCCURRENCE = "LEXICAL_OCCURRENCE"
    DISCOURSE_FEATURE = "DISCOURSE_FEATURE"
    REFERENTIAL_OCCURRENCE = "REFERENTIAL_OCCURRENCE"


class LinguisticFindingCategory(str, Enum):
    """Categories of linguistic findings."""
    MORPHOLOGY = "MORPHOLOGY"
    SYNTAX = "SYNTAX"
    LEXICAL_SEMANTICS = "LEXICAL_SEMANTICS"


class ContextualFindingCategory(str, Enum):
    """Categories of contextual findings."""
    IMMEDIATE_CONTEXT = "IMMEDIATE_CONTEXT"
    DISCOURSE_STRUCTURE = "DISCOURSE_STRUCTURE"
    REFERENTIAL_COGNITION = "REFERENTIAL_COGNITION"
    BOOK_CONTEXT = "BOOK_CONTEXT"
    CORPUS_CONTEXT = "CORPUS_CONTEXT"
    HISTORICAL_LINGUISTIC = "HISTORICAL_LINGUISTIC"


_INTERPRETATION_STATE_MAP = {
    "PROPOSED": InterpretationState.PROPOSED,
    "SUPPORTED": InterpretationState.SUPPORTED,
    "QUALIFIED": InterpretationState.QUALIFIED,
    "CONTESTED": InterpretationState.CONTESTED,
    "REJECTED": InterpretationState.REJECTED,
    "UNRESOLVED": InterpretationState.UNRESOLVED,
}

_AUDIT_RELATIONSHIP_MAP = {
    "SUPPORT": AuditRelationship.SUPPORT,
    "SUPPORTS": AuditRelationship.SUPPORT,
    "CONTRADICT": AuditRelationship.CONTRADICT,
    "CONTRADICTS": AuditRelationship.CONTRADICT,
    "QUALIFY": AuditRelationship.QUALIFY,
    "QUALIFIES": AuditRelationship.QUALIFY,
    "LIMIT": AuditRelationship.LIMIT,
    "LIMITS": AuditRelationship.LIMIT,
    "REFINE": AuditRelationship.REFINE,
    "REFINES": AuditRelationship.REFINE,
}


def coerce_interpretation_state(value: Any) -> InterpretationState:
    if isinstance(value, InterpretationState):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _INTERPRETATION_STATE_MAP:
            return _INTERPRETATION_STATE_MAP[key]
    raise ExegesisSubsystemError(
        f"Invalid interpretation state: '{value}'. Expected one of: "
        f"{[s.value for s in InterpretationState]}"
    )


def coerce_audit_relationship(value: Any) -> AuditRelationship:
    if isinstance(value, AuditRelationship):
        return value
    if isinstance(value, str):
        key = value.strip().upper()
        if key in _AUDIT_RELATIONSHIP_MAP:
            return _AUDIT_RELATIONSHIP_MAP[key]
    raise InvalidEvidenceRelationshipError(
        f"Invalid audit relationship: '{value}'. Expected SUPPORT, CONTRADICT, QUALIFY, LIMIT, REFINE."
    )


# =============================================================================
# DATA DEFINITIONS (INPUT CONTRACTS)
# =============================================================================

@dataclass(frozen=True)
class ExegesisObservationDefinition:
    observation_id: str
    pericope_id: str
    observation_type: str
    source_reference: str
    observed_text_or_data: str
    passage_id: Optional[str] = None
    token_id: Optional[str] = None
    is_translation_derived: bool = False
    is_ai_generated: bool = False


@dataclass(frozen=True)
class LinguisticFindingDefinition:
    finding_id: str
    pericope_id: str
    category: str
    finding_text: str
    passage_id: Optional[str] = None
    evidence_id: Optional[str] = None
    confidence_score: float = 1.0


@dataclass(frozen=True)
class ContextualFindingDefinition:
    context_finding_id: str
    pericope_id: str
    category: str
    finding_text: str
    evidence_id: Optional[str] = None
    confidence_score: float = 1.0


@dataclass(frozen=True)
class InterpretiveHypothesisDefinition:
    hypothesis_id: str
    pericope_id: str
    hypothesis_text: str
    hypothesis_state: str = "PROPOSED"
    claim_tier: str = "T3_INTERPRETIVE_CLAIM"
    claim_id: Optional[str] = None
    is_theology_independent: bool = False
    confidence_score: float = 0.0
    direct_theology_source: Optional[str] = None
    asserts_strict_identity: bool = False
    independent_identity_evidence_id: Optional[str] = None
    is_majority_vote_derived: bool = False


@dataclass(frozen=True)
class CompetingInterpretationDefinition:
    competing_id: str
    pericope_id: str
    hypothesis_a_id: str
    hypothesis_b_id: str
    tension_type: str
    description: str
    status: str = "COEXISTING"
    is_suppressed: bool = False


@dataclass(frozen=True)
class EvidenceAuditDefinition:
    audit_id: str
    hypothesis_id: str
    evidence_id: str
    relationship: str
    audit_notes: str
    is_counter_evidence: bool = False
    is_critical: bool = False
    evidence_confidence: float = 1.0


@dataclass(frozen=True)
class UnresolvedIssueDefinition:
    issue_id: str
    pericope_id: str
    issue_type: str
    description: str
    hypothesis_id: Optional[str] = None
    is_silently_resolved: bool = False
    is_resolved: bool = False


@dataclass(frozen=True)
class CalibratedConclusionDefinition:
    conclusion_id: str
    pericope_id: str
    hypothesis_id: str
    conclusion_text: str
    epistemic_status: str
    calibrated_confidence: float
    claim_tier: str = "T3_INTERPRETIVE_CLAIM"
    weakest_critical_dependency: Optional[str] = None
    weakest_critical_confidence: Optional[float] = None
    supporting_evidence_count: int = 0
    counter_evidence_count: int = 0
    unresolved_ambiguity_count: int = 0
    has_unresolved_contradiction: bool = False
    model_name: Optional[str] = None
    analyzer_id: str = "POLYA-EXEGESIS-ENGINE"


# =============================================================================
# RECORD MODELS (DATABASE MAPPINGS)
# =============================================================================

@dataclass(frozen=True)
class ExegesisObservationRecord:
    observation_id: str
    run_id: str
    pericope_id: str
    passage_id: Optional[str]
    token_id: Optional[str]
    observation_type: str
    source_reference: str
    observed_text_or_data: str
    is_translation_derived: int
    is_ai_generated: int
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class LinguisticFindingRecord:
    finding_id: str
    run_id: str
    pericope_id: str
    passage_id: Optional[str]
    category: str
    finding_text: str
    evidence_id: Optional[str]
    confidence_score: float
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class ContextualFindingRecord:
    context_finding_id: str
    run_id: str
    pericope_id: str
    category: str
    finding_text: str
    evidence_id: Optional[str]
    confidence_score: float
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class InterpretiveHypothesisRecord:
    hypothesis_id: str
    run_id: str
    pericope_id: str
    claim_id: Optional[str]
    hypothesis_text: str
    hypothesis_state: str
    claim_tier: str
    is_theology_independent: int
    confidence_score: float
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class CompetingInterpretationRecord:
    competing_id: str
    run_id: str
    pericope_id: str
    hypothesis_a_id: str
    hypothesis_b_id: str
    tension_type: str
    description: str
    status: str
    is_suppressed: int
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class EvidenceAuditRecord:
    audit_id: str
    run_id: str
    hypothesis_id: str
    evidence_id: str
    relationship: str
    is_counter_evidence: int
    is_critical: int
    audit_notes: str
    evidence_confidence: float
    audited_at: str
    is_immutable: int


@dataclass(frozen=True)
class UnresolvedIssueRecord:
    issue_id: str
    run_id: str
    pericope_id: str
    hypothesis_id: Optional[str]
    issue_type: str
    description: str
    is_silently_resolved: int
    is_resolved: int
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class CalibratedConclusionRecord:
    conclusion_id: str
    run_id: str
    pericope_id: str
    hypothesis_id: str
    claim_tier: str
    conclusion_text: str
    epistemic_status: str
    calibrated_confidence: float
    weakest_critical_dependency: Optional[str]
    weakest_critical_confidence: Optional[float]
    supporting_evidence_count: int
    counter_evidence_count: int
    unresolved_ambiguity_count: int
    has_unresolved_contradiction: int
    model_name: Optional[str]
    analyzer_id: str
    input_hash: str
    output_hash: str
    provenance_hash: str
    created_at: str
    is_immutable: int


@dataclass(frozen=True)
class ExegesisRunRecord:
    run_id: str
    pericope_id: str
    source_text_id: str
    morphology_run_id: Optional[str]
    syntax_run_id: Optional[str]
    semantic_run_id: Optional[str]
    discourse_run_id: Optional[str]
    referential_run_id: Optional[str]
    evidence_run_id: Optional[str]
    version_id: str
    provenance_id: str
    analyzer_id: str
    analyzer_version: str
    model_name: Optional[str]
    relevant_clauses_json: str
    relevant_tokens_json: str
    configuration_hash: str
    input_content_hash: str
    output_hash: str
    status: str
    is_exact_reproducible: int
    created_at: str
    is_immutable: int
    metadata_json: Optional[str]


@dataclass
class ExegesisConfig:
    analyzer_id: str = "POLYA-EXEGESIS-ENGINE"
    analyzer_version: str = "2.0.0"
    model_name: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        payload = {
            "analyzer_id": self.analyzer_id,
            "analyzer_version": self.analyzer_version,
            "model_name": self.model_name,
            "parameters": self.parameters,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# =============================================================================
# EXEGESIS MANAGER
# =============================================================================

class ExegesisManager:
    """Core Manager for Exegesis Foundation Subsystem (Task 2.9)."""

    def __init__(
        self,
        engine: DatabaseEngine,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
    ) -> None:
        self.engine = engine
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.version_manager = version_manager or VersionManager(engine)

    def record_exegesis(
        self,
        pericope_id: str,
        source_text_id: str,
        morphology_run_id: Optional[str] = None,
        syntax_run_id: Optional[str] = None,
        semantic_run_id: Optional[str] = None,
        discourse_run_id: Optional[str] = None,
        referential_run_id: Optional[str] = None,
        evidence_run_id: Optional[str] = None,
        relevant_clauses: Sequence[str] = (),
        relevant_tokens: Sequence[str] = (),
        observations: Sequence[ExegesisObservationDefinition] = (),
        linguistic_findings: Sequence[LinguisticFindingDefinition] = (),
        contextual_findings: Sequence[ContextualFindingDefinition] = (),
        hypotheses: Sequence[InterpretiveHypothesisDefinition] = (),
        competing_interpretations: Sequence[CompetingInterpretationDefinition] = (),
        evidence_audits: Sequence[EvidenceAuditDefinition] = (),
        unresolved_issues: Sequence[UnresolvedIssueDefinition] = (),
        calibrated_conclusions: Sequence[CalibratedConclusionDefinition] = (),
        config: Optional[ExegesisConfig] = None,
        run_id: Optional[str] = None,
        parent_version_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> ExegesisRunRecord:
        """
        Record and calibrate an exegesis run with strict epistemic firewalls.
        """
        config = config or ExegesisConfig()
        created_at_str = created_at or datetime.now(timezone.utc).isoformat()
        run_id_val = run_id or f"EXEG-{hashlib.sha256(f'{pericope_id}-{created_at_str}'.encode()).hexdigest()[:12]}"

        # ---------------------------------------------------------------------
        # 1. VERIFY PERICOPE AS PRIMARY EXEGESIS UNIT
        # ---------------------------------------------------------------------
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT pericope_id FROM pericopes WHERE pericope_id = ?", (pericope_id,))
            row = cur.fetchone()
            if not row:
                raise PericopePrimaryUnitFirewallError(
                    f"Pericope '{pericope_id}' not found in canonical pericopes registry. "
                    "Pericope is the primary unit of exegesis; verse cannot substitute for pericope."
                )

            # Verify source text exists
            cur.execute("SELECT source_text_id FROM source_texts WHERE source_text_id = ?", (source_text_id,))
            if not cur.fetchone():
                raise SourceTextNotFoundError(f"Source text '{source_text_id}' not found.")

            # Verify lower-level runs if specified
            if morphology_run_id:
                cur.execute("SELECT run_id FROM morphology_runs WHERE run_id = ?", (morphology_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Morphology run '{morphology_run_id}' not found.")
            if syntax_run_id:
                cur.execute("SELECT run_id FROM syntax_runs WHERE run_id = ?", (syntax_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Syntax run '{syntax_run_id}' not found.")
            if semantic_run_id:
                cur.execute("SELECT run_id FROM semantic_runs WHERE run_id = ?", (semantic_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Semantic run '{semantic_run_id}' not found.")
            if discourse_run_id:
                cur.execute("SELECT run_id FROM discourse_runs WHERE run_id = ?", (discourse_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Discourse run '{discourse_run_id}' not found.")
            if referential_run_id:
                cur.execute("SELECT run_id FROM referential_runs WHERE run_id = ?", (referential_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Referential run '{referential_run_id}' not found.")
            if evidence_run_id:
                cur.execute("SELECT run_id FROM evidence_runs WHERE run_id = ?", (evidence_run_id,))
                if not cur.fetchone():
                    raise ExegesisOrphanError(f"Evidence run '{evidence_run_id}' not found.")

        # ---------------------------------------------------------------------
        # 2. EPISTEMIC FIREWALL CHECKS
        # ---------------------------------------------------------------------
        self._enforce_epistemic_firewalls(
            observations=observations,
            hypotheses=hypotheses,
            competing_interpretations=competing_interpretations,
            evidence_audits=evidence_audits,
            unresolved_issues=unresolved_issues,
            calibrated_conclusions=calibrated_conclusions,
        )

        # ---------------------------------------------------------------------
        # 3. COMPUTE HASHES & PROVENANCE
        # ---------------------------------------------------------------------
        configuration_hash = config.compute_hash()

        input_payload = {
            "pericope_id": pericope_id,
            "source_text_id": source_text_id,
            "morphology_run_id": morphology_run_id,
            "syntax_run_id": syntax_run_id,
            "semantic_run_id": semantic_run_id,
            "discourse_run_id": discourse_run_id,
            "referential_run_id": referential_run_id,
            "evidence_run_id": evidence_run_id,
            "relevant_clauses": sorted(list(relevant_clauses)),
            "relevant_tokens": sorted(list(relevant_tokens)),
        }
        input_content_hash = hashlib.sha256(
            json.dumps(input_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        output_payload = {
            "observations": [asdict(o) for o in observations],
            "linguistic_findings": [asdict(lf) for lf in linguistic_findings],
            "contextual_findings": [asdict(cf) for cf in contextual_findings],
            "hypotheses": [asdict(h) for h in hypotheses],
            "competing_interpretations": [asdict(c) for c in competing_interpretations],
            "evidence_audits": [asdict(a) for a in evidence_audits],
            "unresolved_issues": [asdict(u) for u in unresolved_issues],
            "calibrated_conclusions": [asdict(cc) for cc in calibrated_conclusions],
        }
        output_hash = hashlib.sha256(
            json.dumps(output_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        # ---------------------------------------------------------------------
        # 4. PERSIST IN ATOMIC TRANSACTION
        # ---------------------------------------------------------------------
        try:
            with self.engine.transaction() as conn:
                cur = conn.cursor()

                provenance_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=run_id_val,
                    content=f"EXEGESIS_RUN:{run_id_val}:{output_hash}",
                    input_data=input_payload,
                    agent_id=config.analyzer_id,
                    agent_version=config.analyzer_version,
                    config=config.parameters,
                    conn=conn,
                )

                if parent_version_id:
                    parent_ver = self.version_manager.get_version(parent_version_id, conn=conn)
                    object_type_val = parent_ver.object_type
                    object_id_val = parent_ver.object_id
                    change_reason_val = ChangeReason.REANALYSIS
                else:
                    object_type_val = "EXEGESIS_RUN"
                    object_id_val = run_id_val
                    change_reason_val = ChangeReason.INITIAL_CREATION

                version_rec = self.version_manager.create_version(
                    object_type=object_type_val,
                    object_id=object_id_val,
                    content=json.dumps(output_payload, sort_keys=True),
                    version_number=None,
                    change_reason=change_reason_val,
                    created_by=config.analyzer_id,
                    parent_version_id=parent_version_id,
                    provenance_id=provenance_rec.provenance_id,
                    conn=conn,
                )

                # Insert Exegesis Run
                cur.execute(
                    """
                    INSERT INTO exegesis_runs (
                        run_id, pericope_id, source_text_id, morphology_run_id,
                        syntax_run_id, semantic_run_id, discourse_run_id,
                        referential_run_id, evidence_run_id, version_id,
                        provenance_id, analyzer_id, analyzer_version, model_name,
                        relevant_clauses_json, relevant_tokens_json,
                        configuration_hash, input_content_hash, output_hash,
                        status, is_exact_reproducible, created_at, is_immutable,
                        metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, 1, ?)
                    """,
                    (
                        run_id_val,
                        pericope_id,
                        source_text_id,
                        morphology_run_id,
                        syntax_run_id,
                        semantic_run_id,
                        discourse_run_id,
                        referential_run_id,
                        evidence_run_id,
                        version_rec.version_id,
                        provenance_rec.provenance_id,
                        config.analyzer_id,
                        config.analyzer_version,
                        config.model_name,
                        json.dumps(list(relevant_clauses)),
                        json.dumps(list(relevant_tokens)),
                        configuration_hash,
                        input_content_hash,
                        output_hash,
                        "COMPLETED",
                        created_at_str,
                        json.dumps(config.parameters) if config.parameters else None,
                    ),
                )

                # Insert Observations
                for obs in observations:
                    obs_prov_hash = hashlib.sha256(
                        f"{obs.observation_id}:{obs.source_reference}:{obs.observed_text_or_data}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO exegesis_observations (
                            observation_id, run_id, pericope_id, passage_id, token_id,
                            observation_type, source_reference, observed_text_or_data,
                            is_translation_derived, is_ai_generated, provenance_hash,
                            created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            obs.observation_id,
                            run_id_val,
                            obs.pericope_id,
                            obs.passage_id,
                            obs.token_id,
                            obs.observation_type,
                            obs.source_reference,
                            obs.observed_text_or_data,
                            1 if obs.is_translation_derived else 0,
                            1 if obs.is_ai_generated else 0,
                            obs_prov_hash,
                            created_at_str,
                        ),
                    )

                # Insert Linguistic Findings
                for lf in linguistic_findings:
                    lf_hash = hashlib.sha256(
                        f"{lf.finding_id}:{lf.category}:{lf.finding_text}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO exegesis_linguistic_findings (
                            finding_id, run_id, pericope_id, passage_id, category,
                            finding_text, evidence_id, confidence_score,
                            provenance_hash, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            lf.finding_id,
                            run_id_val,
                            lf.pericope_id,
                            lf.passage_id,
                            lf.category,
                            lf.finding_text,
                            lf.evidence_id,
                            lf.confidence_score,
                            lf_hash,
                            created_at_str,
                        ),
                    )

                # Insert Contextual Findings
                for cf in contextual_findings:
                    cf_hash = hashlib.sha256(
                        f"{cf.context_finding_id}:{cf.category}:{cf.finding_text}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO exegesis_contextual_findings (
                            context_finding_id, run_id, pericope_id, category,
                            finding_text, evidence_id, confidence_score,
                            provenance_hash, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            cf.context_finding_id,
                            run_id_val,
                            cf.pericope_id,
                            cf.category,
                            cf.finding_text,
                            cf.evidence_id,
                            cf.confidence_score,
                            cf_hash,
                            created_at_str,
                        ),
                    )

                # Insert Interpretive Hypotheses
                for hyp in hypotheses:
                    hyp_hash = hashlib.sha256(
                        f"{hyp.hypothesis_id}:{hyp.hypothesis_text}:{hyp.hypothesis_state}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO interpretive_hypotheses (
                            hypothesis_id, run_id, pericope_id, claim_id,
                            hypothesis_text, hypothesis_state, claim_tier,
                            is_theology_independent, confidence_score,
                            provenance_hash, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            hyp.hypothesis_id,
                            run_id_val,
                            hyp.pericope_id,
                            hyp.claim_id,
                            hyp.hypothesis_text,
                            coerce_interpretation_state(hyp.hypothesis_state).value,
                            coerce_claim_tier(hyp.claim_tier).value,
                            1 if hyp.is_theology_independent else 0,
                            hyp.confidence_score,
                            hyp_hash,
                            created_at_str,
                        ),
                    )

                # Insert Competing Interpretations
                for comp in competing_interpretations:
                    comp_hash = hashlib.sha256(
                        f"{comp.competing_id}:{comp.hypothesis_a_id}:{comp.hypothesis_b_id}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO competing_interpretations (
                            competing_id, run_id, pericope_id, hypothesis_a_id,
                            hypothesis_b_id, tension_type, description, status,
                            is_suppressed, provenance_hash, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            comp.competing_id,
                            run_id_val,
                            comp.pericope_id,
                            comp.hypothesis_a_id,
                            comp.hypothesis_b_id,
                            comp.tension_type,
                            comp.description,
                            comp.status,
                            1 if comp.is_suppressed else 0,
                            comp_hash,
                            created_at_str,
                        ),
                    )

                # Insert Evidence Audits
                for audit in evidence_audits:
                    cur.execute(
                        """
                        INSERT INTO evidence_audits (
                            audit_id, run_id, hypothesis_id, evidence_id,
                            relationship, is_counter_evidence, is_critical,
                            audit_notes, evidence_confidence, audited_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            audit.audit_id,
                            run_id_val,
                            audit.hypothesis_id,
                            audit.evidence_id,
                            coerce_audit_relationship(audit.relationship).value,
                            1 if audit.is_counter_evidence else 0,
                            1 if audit.is_critical else 0,
                            audit.audit_notes,
                            audit.evidence_confidence,
                            created_at_str,
                        ),
                    )

                # Insert Unresolved Issues
                for issue in unresolved_issues:
                    issue_hash = hashlib.sha256(
                        f"{issue.issue_id}:{issue.issue_type}:{issue.description}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO unresolved_issues (
                            issue_id, run_id, pericope_id, hypothesis_id,
                            issue_type, description, is_silently_resolved,
                            is_resolved, provenance_hash, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            issue.issue_id,
                            run_id_val,
                            issue.pericope_id,
                            issue.hypothesis_id,
                            issue.issue_type,
                            issue.description,
                            1 if issue.is_silently_resolved else 0,
                            1 if issue.is_resolved else 0,
                            issue_hash,
                            created_at_str,
                        ),
                    )

                # Insert Calibrated Conclusions
                for conc in calibrated_conclusions:
                    conc_hash = hashlib.sha256(
                        f"{conc.conclusion_id}:{conc.conclusion_text}:{conc.epistemic_status}".encode()
                    ).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO calibrated_conclusions (
                            conclusion_id, run_id, pericope_id, hypothesis_id,
                            claim_tier, conclusion_text, epistemic_status,
                            calibrated_confidence, weakest_critical_dependency,
                            weakest_critical_confidence, supporting_evidence_count,
                            counter_evidence_count, unresolved_ambiguity_count,
                            has_unresolved_contradiction, model_name, analyzer_id,
                            input_hash, output_hash, provenance_hash, created_at,
                            is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            conc.conclusion_id,
                            run_id_val,
                            conc.pericope_id,
                            conc.hypothesis_id,
                            coerce_claim_tier(conc.claim_tier).value,
                            conc.conclusion_text,
                            conc.epistemic_status,
                            conc.calibrated_confidence,
                            conc.weakest_critical_dependency,
                            conc.weakest_critical_confidence,
                            conc.supporting_evidence_count,
                            conc.counter_evidence_count,
                            conc.unresolved_ambiguity_count,
                            1 if conc.has_unresolved_contradiction else 0,
                            conc.model_name or config.model_name,
                            conc.analyzer_id,
                            input_content_hash,
                            output_hash,
                            conc_hash,
                            created_at_str,
                        ),
                    )
        except Exception as e:
            # Map sqlite3 trigger aborts to domain errors
            msg = str(e).lower()
            if "immutable" in msg or "strictly prohibited" in msg:
                raise ExegesisImmutabilityError(str(e)) from e
            if "unique constraint failed" in msg:
                raise DuplicateExegesisError(str(e)) from e
            if "foreign key constraint failed" in msg:
                raise ExegesisOrphanError(str(e)) from e
            raise

        return self.get_exegesis_run(run_id_val)

    def _enforce_epistemic_firewalls(
        self,
        observations: Sequence[ExegesisObservationDefinition],
        hypotheses: Sequence[InterpretiveHypothesisDefinition],
        competing_interpretations: Sequence[CompetingInterpretationDefinition],
        evidence_audits: Sequence[EvidenceAuditDefinition],
        unresolved_issues: Sequence[UnresolvedIssueDefinition],
        calibrated_conclusions: Sequence[CalibratedConclusionDefinition],
    ) -> None:
        """Enforce strict epistemic firewalls before persistence."""

        # 1. Observation firewalls: Translation and AI output
        for obs in observations:
            if obs.is_translation_derived:
                raise TranslationAsSourceFirewallError(
                    f"Observation '{obs.observation_id}' is translation-derived. "
                    "Translation output cannot become source evidence."
                )
            if obs.is_ai_generated:
                raise ConfidenceAsEvidenceFirewallError(
                    f"Observation '{obs.observation_id}' is AI-generated. "
                    "AI synthetic output cannot become raw primary observation."
                )

        # 2. Hypothesis firewalls
        for hyp in hypotheses:
            # Model majority consensus firewall
            if hyp.is_majority_vote_derived:
                raise ModelMajorityTruthFirewallError(
                    f"Hypothesis '{hyp.hypothesis_id}' is derived from model majority or consensus. "
                    "Model agreement is not evidence and cannot establish truth."
                )

            # Theology direct derivation firewalls
            if hyp.direct_theology_source:
                src = hyp.direct_theology_source.upper()
                if src == "MORPHOLOGY":
                    raise ExegesisMorphologyTheologyFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' directly manufactures theological claim from morphology alone."
                    )
                if src == "SYNTAX":
                    raise ExegesisSyntaxTheologyFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' directly manufactures theological claim from syntax alone."
                    )
                if src in ("SEMANTICS", "SEMANTIC_SENSE", "LEXICAL"):
                    raise ExegesisSemanticTheologyFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' directly manufactures theological claim from semantic sense alone."
                    )
                if src == "DISCOURSE":
                    raise ExegesisDiscourseTheologyFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' directly manufactures theological claim from discourse relation alone."
                    )
                if src in ("ENTITY", "REFERENTIAL"):
                    raise ExegesisEntityIdentityFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' directly manufactures theological claim from entity association alone."
                    )

            # Entity association to strict identity firewall
            if hyp.asserts_strict_identity and not hyp.independent_identity_evidence_id:
                raise StrictIdentityEvidenceFirewallError(
                    f"Hypothesis '{hyp.hypothesis_id}' asserts STRICT_IDENTITY without independent evidence. "
                    "Entity association cannot directly create strict identity."
                )

            # Interpretation without evidence firewall
            state = coerce_interpretation_state(hyp.hypothesis_state)
            if state == InterpretationState.SUPPORTED:
                supporting_audits = [
                    a for a in evidence_audits
                    if a.hypothesis_id == hyp.hypothesis_id and coerce_audit_relationship(a.relationship) == AuditRelationship.SUPPORT
                ]
                if not supporting_audits:
                    raise InterpretationWithoutEvidenceFirewallError(
                        f"Hypothesis '{hyp.hypothesis_id}' is marked SUPPORTED without supporting evidence audits."
                    )

        # 3. Competing interpretations anti-suppression firewall
        for comp in competing_interpretations:
            if comp.is_suppressed:
                raise SuppressionOfCompetingInterpretationFirewallError(
                    f"Competing interpretation '{comp.competing_id}' has is_suppressed=True. "
                    "Competing interpretations must coexist and cannot be suppressed."
                )

        # 4. Unresolved issues firewall
        for issue in unresolved_issues:
            if issue.is_silently_resolved:
                raise SilentAmbiguityResolutionFirewallError(
                    f"Issue '{issue.issue_id}' was marked as silently resolved. "
                    "Ambiguity and contradictions must not be silently resolved."
                )

        # 5. Conclusion firewalls & weakest critical dependency calibration
        for conc in calibrated_conclusions:
            # Unsupported conclusion
            if conc.epistemic_status == "SUPPORTED" and conc.supporting_evidence_count == 0:
                raise UnsupportedConclusionFirewallError(
                    f"Conclusion '{conc.conclusion_id}' is marked SUPPORTED but has zero supporting evidence."
                )

            # Suppressed counter-evidence scoped to hypothesis
            counter_audits_for_hyp = [
                a for a in evidence_audits
                if a.hypothesis_id == conc.hypothesis_id and (a.is_counter_evidence or a.relationship == "CONTRADICT")
            ]
            if counter_audits_for_hyp and conc.counter_evidence_count == 0:
                raise SuppressionOfCounterEvidenceFirewallError(
                    f"Conclusion '{conc.conclusion_id}' reports 0 counter-evidence despite existing counter-evidence audits for hypothesis '{conc.hypothesis_id}'. "
                    "Counter-evidence cannot be silently removed."
                )

            # Unresolved contradiction
            if conc.has_unresolved_contradiction and conc.epistemic_status == "SUPPORTED":
                raise UnresolvedContradictionFirewallError(
                    f"Conclusion '{conc.conclusion_id}' has unresolved contradiction and cannot be marked SUPPORTED."
                )

            # Ambiguity preservation scoped to hypothesis or pericope
            ambiguity_issues = [
                u for u in unresolved_issues
                if u.issue_type == "AMBIGUITY" and not u.is_resolved and (u.hypothesis_id is None or u.hypothesis_id == conc.hypothesis_id)
            ]
            if ambiguity_issues and conc.unresolved_ambiguity_count == 0:
                raise SilentAmbiguityResolutionFirewallError(
                    f"Conclusion '{conc.conclusion_id}' reports 0 unresolved ambiguity despite active ambiguity issues. "
                    "Ambiguity must be explicitly preserved."
                )

            # Weakest critical dependency propagation
            critical_audits = [
                a for a in evidence_audits
                if a.hypothesis_id == conc.hypothesis_id and a.is_critical
            ]
            if critical_audits:
                min_critical_conf = min(a.evidence_confidence for a in critical_audits)
                if conc.calibrated_confidence > min_critical_conf + 0.0001:
                    raise ConfidenceUpgradeFirewallError(
                        f"Conclusion confidence ({conc.calibrated_confidence}) exceeds weakest critical "
                        f"evidence dependency ({min_critical_conf})."
                    )

    # -------------------------------------------------------------------------
    # RETRIEVAL METHODS
    # -------------------------------------------------------------------------

    def get_exegesis_run(self, run_id: str) -> ExegesisRunRecord:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, pericope_id, source_text_id, morphology_run_id,
                       syntax_run_id, semantic_run_id, discourse_run_id,
                       referential_run_id, evidence_run_id, version_id,
                       provenance_id, analyzer_id, analyzer_version, model_name,
                       relevant_clauses_json, relevant_tokens_json,
                       configuration_hash, input_content_hash, output_hash,
                       status, is_exact_reproducible, created_at, is_immutable,
                       metadata_json
                FROM exegesis_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                raise ExegesisRunNotFoundError(f"Exegesis run '{run_id}' not found.")
            return ExegesisRunRecord(*row)

    def get_observations(self, run_id: str) -> List[ExegesisObservationRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT observation_id, run_id, pericope_id, passage_id, token_id,
                       observation_type, source_reference, observed_text_or_data,
                       is_translation_derived, is_ai_generated, provenance_hash,
                       created_at, is_immutable
                FROM exegesis_observations
                WHERE run_id = ?
                ORDER BY observation_id
                """,
                (run_id,),
            )
            return [ExegesisObservationRecord(*row) for row in cur.fetchall()]

    def get_linguistic_findings(self, run_id: str) -> List[LinguisticFindingRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT finding_id, run_id, pericope_id, passage_id, category,
                       finding_text, evidence_id, confidence_score,
                       provenance_hash, created_at, is_immutable
                FROM exegesis_linguistic_findings
                WHERE run_id = ?
                ORDER BY finding_id
                """,
                (run_id,),
            )
            return [LinguisticFindingRecord(*row) for row in cur.fetchall()]

    def get_contextual_findings(self, run_id: str) -> List[ContextualFindingRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT context_finding_id, run_id, pericope_id, category,
                       finding_text, evidence_id, confidence_score,
                       provenance_hash, created_at, is_immutable
                FROM exegesis_contextual_findings
                WHERE run_id = ?
                ORDER BY context_finding_id
                """,
                (run_id,),
            )
            return [ContextualFindingRecord(*row) for row in cur.fetchall()]

    def get_hypotheses(self, run_id: str) -> List[InterpretiveHypothesisRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT hypothesis_id, run_id, pericope_id, claim_id,
                       hypothesis_text, hypothesis_state, claim_tier,
                       is_theology_independent, confidence_score,
                       provenance_hash, created_at, is_immutable
                FROM interpretive_hypotheses
                WHERE run_id = ?
                ORDER BY hypothesis_id
                """,
                (run_id,),
            )
            return [InterpretiveHypothesisRecord(*row) for row in cur.fetchall()]

    def get_competing_interpretations(self, run_id: str) -> List[CompetingInterpretationRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT competing_id, run_id, pericope_id, hypothesis_a_id,
                       hypothesis_b_id, tension_type, description, status,
                       is_suppressed, provenance_hash, created_at, is_immutable
                FROM competing_interpretations
                WHERE run_id = ?
                ORDER BY competing_id
                """,
                (run_id,),
            )
            return [CompetingInterpretationRecord(*row) for row in cur.fetchall()]

    def get_evidence_audits(self, run_id: str) -> List[EvidenceAuditRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT audit_id, run_id, hypothesis_id, evidence_id,
                       relationship, is_counter_evidence, is_critical,
                       audit_notes, evidence_confidence, audited_at, is_immutable
                FROM evidence_audits
                WHERE run_id = ?
                ORDER BY audit_id
                """,
                (run_id,),
            )
            return [EvidenceAuditRecord(*row) for row in cur.fetchall()]

    def get_unresolved_issues(self, run_id: str) -> List[UnresolvedIssueRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT issue_id, run_id, pericope_id, hypothesis_id,
                       issue_type, description, is_silently_resolved,
                       is_resolved, provenance_hash, created_at, is_immutable
                FROM unresolved_issues
                WHERE run_id = ?
                ORDER BY issue_id
                """,
                (run_id,),
            )
            return [UnresolvedIssueRecord(*row) for row in cur.fetchall()]

    def get_calibrated_conclusions(self, run_id: str) -> List[CalibratedConclusionRecord]:
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT conclusion_id, run_id, pericope_id, hypothesis_id,
                       claim_tier, conclusion_text, epistemic_status,
                       calibrated_confidence, weakest_critical_dependency,
                       weakest_critical_confidence, supporting_evidence_count,
                       counter_evidence_count, unresolved_ambiguity_count,
                       has_unresolved_contradiction, model_name, analyzer_id,
                       input_hash, output_hash, provenance_hash, created_at,
                       is_immutable
                FROM calibrated_conclusions
                WHERE run_id = ?
                ORDER BY conclusion_id
                """,
                (run_id,),
            )
            return [CalibratedConclusionRecord(*row) for row in cur.fetchall()]
