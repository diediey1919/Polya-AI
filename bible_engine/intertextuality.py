"""
Intertextual Analysis Engine (Task 3.3).
Evidence Class: E10_INTERTEXTUAL.
Specification: Architecture v2.0 — FROZEN.

Provides provenance-first, immutable evaluation of relationships between biblical
passages and other textual witnesses without allowing conclusions to outrun evidence.

Epistemic Firewalls:
  1. Lexical similarity != intertextuality
  2. Thematic similarity != intertextuality
  3. Chronology != textual dependence
  4. Same wording != automatic quotation
  5. Shared tradition != direct quotation
  6. E9 historical-linguistic parallel != E10 intertextual relationship
  7. Translation != original-source identity
  8. Reception source != authorial source
  9. Entity identity != textual dependence
  10. Unknown direction must remain UNKNOWN
  11. AI-generated proposal != primary intertextual evidence
  12. Modern commentary != ancient source
  13. Confidence cannot upgrade evidence
  14. Retrieval ranking cannot select truth
  15. Competing hypotheses must remain preserved
  16. Counter-evidence cannot be silently discarded
  17. Direct quotation requires explicit evidence
  18. Intertextual relation cannot be established solely by chronology
  19. Intertextual claim cannot silently become theological claim
  20. Unverified external identifier cannot be treated as verified
"""

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AIIntertextualEvidenceFirewallError,
    ChronologyNotDependenceFirewallError,
    ChronologyOnlyRelationFirewallError,
    ConfidenceNotEvidenceUpgradeFirewallError,
    CounterEvidencePreservationFirewallError,
    E9ParallelNotE10IntertextFirewallError,
    EntityIdentityNotTextualDependenceFirewallError,
    IntertextualConcurrencyError,
    IntertextualImmutabilityError,
    IntertextualInvalidProvenanceError,
    IntertextualInvalidVersionError,
    IntertextualNotTheologicalClaimFirewallError,
    IntertextualRelationshipNotFoundError,
    IntertextualSourceNotFoundError,
    IntertextualSubsystemError,
    LexicalSimilarityNotIntertextualityFirewallError,
    ModernCommentaryNotAncientSourceFirewallError,
    QuotationEvidenceRequiredFirewallError,
    ReceptionSourceNotAuthorialSourceFirewallError,
    RetrievalRankingNotTruthFirewallError,
    SameWordingNotAutomaticQuotationFirewallError,
    SharedTraditionNotDirectQuotationFirewallError,
    ThematicSimilarityNotIntertextualityFirewallError,
    TranslationNotOriginalSourceFirewallError,
    UnknownDirectionPreservationFirewallError,
    UnverifiedIdentifierPreservationFirewallError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceDefinition,
    EvidenceStatus,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, VersionManager


# =============================================================================
# TAXONOMIES AND ENUMS
# =============================================================================

class IntertextualRelationType(str, Enum):
    """Controlled relationship types for intertextual analysis."""
    TEXTUAL_REUSE = "TEXTUAL_REUSE"
    DIRECT_QUOTATION = "DIRECT_QUOTATION"
    STRONG_ALLUSION = "STRONG_ALLUSION"
    PROBABLE_ALLUSION = "PROBABLE_ALLUSION"
    POSSIBLE_ALLUSION = "POSSIBLE_ALLUSION"
    LEXICAL_PARALLEL = "LEXICAL_PARALLEL"
    THEMATIC_PARALLEL = "THEMATIC_PARALLEL"
    TRADITIONAL_PARALLEL = "TRADITIONAL_PARALLEL"
    UNKNOWN = "UNKNOWN"


class EpistemicClassification(str, Enum):
    """Controlled epistemic classifications for intertextuality."""
    DIRECT_QUOTATION = "DIRECT_QUOTATION"
    STRONG_ALLUSION = "STRONG_ALLUSION"
    PROBABLE_ALLUSION = "PROBABLE_ALLUSION"
    POSSIBLE_ALLUSION = "POSSIBLE_ALLUSION"
    LEXICAL_PARALLEL = "LEXICAL_PARALLEL"
    THEMATIC_PARALLEL = "THEMATIC_PARALLEL"
    NO_ESTABLISHED_RELATION = "NO_ESTABLISHED_RELATION"


class SourceType(str, Enum):
    """Controlled categories of candidate intertextual sources."""
    BIBLICAL_PASSAGE = "BIBLICAL_PASSAGE"
    BIBLICAL_PERICOPE = "BIBLICAL_PERICOPE"
    CLAUSE = "CLAUSE"
    NON_BIBLICAL_ANCIENT_TEXT = "NON_BIBLICAL_ANCIENT_TEXT"
    INSCRIPTION = "INSCRIPTION"
    PAPYRUS = "PAPYRUS"
    MANUSCRIPT_WITNESS = "MANUSCRIPT_WITNESS"
    ANCIENT_TRANSLATION = "ANCIENT_TRANSLATION"
    ANCIENT_COMMENTARY_RECEPTION = "ANCIENT_COMMENTARY_RECEPTION"


class SourceDirection(str, Enum):
    """Direction of intertextual flow."""
    SOURCE_TO_TARGET = "SOURCE_TO_TARGET"
    TARGET_TO_SOURCE = "TARGET_TO_SOURCE"
    BIDIRECTIONAL = "BIDIRECTIONAL"
    UNKNOWN = "UNKNOWN"


class IntertextStatus(str, Enum):
    """Controlled consensus status of intertextual relation."""
    PROPOSED = "PROPOSED"
    POSSIBLE = "POSSIBLE"
    PROBABLE = "PROBABLE"
    ESTABLISHED = "ESTABLISHED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class ObservationType(str, Enum):
    """Raw intertextual observation types separated from conclusions."""
    WORDING_OVERLAP = "WORDING_OVERLAP"
    PHRASE_OVERLAP = "PHRASE_OVERLAP"
    RARE_LEXICAL_SEQUENCE = "RARE_LEXICAL_SEQUENCE"
    SYNTACTIC_CORRESPONDENCE = "SYNTACTIC_CORRESPONDENCE"
    STRUCTURAL_CORRESPONDENCE = "STRUCTURAL_CORRESPONDENCE"
    THEMATIC_CORRESPONDENCE = "THEMATIC_CORRESPONDENCE"
    DISTINCTIVE_MOTIF = "DISTINCTIVE_MOTIF"
    NARRATIVE_CORRESPONDENCE = "NARRATIVE_CORRESPONDENCE"
    QUOTATION_FORMULA = "QUOTATION_FORMULA"
    CITATION_FORMULA = "CITATION_FORMULA"
    CONTEXTUAL_CORRESPONDENCE = "CONTEXTUAL_CORRESPONDENCE"
    CANONICAL_PLACEMENT = "CANONICAL_PLACEMENT"
    SOURCE_AVAILABILITY = "SOURCE_AVAILABILITY"
    HISTORICAL_PLAUSIBILITY = "HISTORICAL_PLAUSIBILITY"


class EvidenceStance(str, Enum):
    """Stance of evidence linking to relationship or hypothesis."""
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    QUALIFY = "QUALIFY"
    LIMIT = "LIMIT"
    REFINE = "REFINE"


class IdentifierVerificationStatus(str, Enum):
    """External scholarly identifier verification status."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash of JSON-serializable payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest().lower()


# =============================================================================
# DATA DEFINITIONS (DTOs)
# =============================================================================

@dataclass(frozen=True)
class SourceMetadataDefinition:
    """Definition for candidate intertextual source metadata."""
    source_metadata_id: str
    source_type: str
    canonical_reference: str
    source_language: str
    is_translation: bool = False
    original_language: Optional[str] = None
    dating_period: Optional[str] = None
    approximate_date_bce_ce: Optional[int] = None
    is_modern_commentary: bool = False
    external_identifier: str = ""
    external_identifier_status: str = "UNVERIFIED"
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class IntertextualRelationshipDefinition:
    """Definition for an evaluated intertextual relationship."""
    relationship_id: str
    source_metadata_id: str
    relationship_type: str
    epistemic_classification: str
    target_passage_id: Optional[str] = None
    target_pericope_id: Optional[str] = None
    direction: str = "UNKNOWN"
    status: str = "PROPOSED"
    target_language: str = "GREEK"
    source_language: str = "GREEK"
    is_translation_mediated: bool = False
    has_explicit_quotation_formula: bool = False
    quotation_formula_text: Optional[str] = None
    chronological_precedence_demonstrated: bool = False
    solely_chronological_basis: bool = False
    is_ai_generated: bool = False
    is_reception_history_source: bool = False
    entity_agreement_only: bool = False
    confidence: str = "HIGH"
    confidence_score: float = 0.8
    retrieval_rank: Optional[int] = None
    retrieval_score: Optional[float] = None
    evidence_id: str = ""
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class IntertextualObservationDefinition:
    """Definition for raw intertextual observation."""
    observation_id: str
    relationship_id: str
    observation_type: str
    observation_text: str
    shared_elements: Optional[str] = None
    is_theological_claim: bool = False
    evidence_id: str = ""
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class IntertextualHypothesisDefinition:
    """Definition for competing intertextual hypothesis."""
    hypothesis_id: str
    hypothesis_code: str
    hypothesis_description: str
    proposed_relationship_type: str
    target_passage_id: Optional[str] = None
    source_metadata_id: Optional[str] = None
    is_primary: bool = False
    status: str = "PROPOSED"
    retrieval_rank: Optional[int] = None
    retrieval_score: Optional[float] = None
    retrieval_forced_winner: bool = False
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class IntertextualEvidenceLinkDefinition:
    """Definition for linking supporting/counter evidence to relationship or hypothesis."""
    link_id: str
    evidence_id: str
    relationship_id: Optional[str] = None
    hypothesis_id: Optional[str] = None
    evidence_class: str = "E10_INTERTEXTUAL"
    stance: str = "SUPPORT"
    weight: float = 1.0
    is_counter_evidence: bool = False
    reasoning: str = ""
    notes: Optional[str] = None


@dataclass(frozen=True)
class IntertextualRunResult:
    """Summary result of an intertextual analysis run."""
    run_id: str
    version_id: str
    provenance_id: str
    relationships_count: int
    observations_count: int
    hypotheses_count: int
    evidence_links_count: int
    output_hash: str
    created_at: str


# =============================================================================
# INTERTEXTUAL MANAGER ENGINE
# =============================================================================

class IntertextualManager:
    """
    Manager for Intertextual Analysis Engine (Task 3.3).
    Enforces provenance, immutability, versioning, and strict epistemic firewalls.
    """

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
    # SOURCE METADATA REGISTRATION
    # -------------------------------------------------------------------------

    def register_source_metadata(
        self,
        source: SourceMetadataDefinition,
        created_at: Optional[str] = None,
    ) -> str:
        """Register candidate intertextual source metadata."""
        timestamp = created_at or datetime.now(timezone.utc).isoformat()
        src_lang = source.source_language.upper()
        src_type = source.source_type.upper()
        ext_status = source.external_identifier_status.upper()

        # Firewall 12: Modern commentary != ancient source
        if source.is_modern_commentary or "MODERN" in src_type or "COMMENTARY_RECEPTION" in src_type and "ANCIENT" not in src_type:
            raise ModernCommentaryNotAncientSourceFirewallError(
                f"Source '{source.source_metadata_id}': Modern commentary cannot be registered as ancient source text."
            )

        # Firewall 7: Translation cannot masquerade as original language
        if source.is_translation:
            if not source.original_language or source.original_language.upper() == src_lang:
                raise TranslationNotOriginalSourceFirewallError(
                    f"Source '{source.source_metadata_id}': Translation must specify distinct original_language."
                )

        # Firewall 20: Unverified external identifier cannot be treated as verified
        if ext_status == "VERIFIED" and (not source.external_identifier or source.external_identifier.startswith("UNVERIFIED")):
            raise UnverifiedIdentifierPreservationFirewallError(
                f"Source '{source.source_metadata_id}': Unverified identifier cannot be asserted as VERIFIED."
            )

        prov_id = source.provenance_id
        with self.engine.transaction() as conn:
            if not prov_id:
                content_hash = compute_canonical_hash(asdict(source))
                prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=source.source_metadata_id,
                    content=f"SOURCE_METADATA:{source.source_metadata_id}:{content_hash}",
                    input_data=source.canonical_reference,
                    agent_id="intertextual_source_registry",
                    agent_version="1.0.0",
                    conn=conn,
                )
                prov_id = prov_rec.provenance_id

            conn.execute(
                """
                INSERT INTO intertextual_source_metadata (
                    source_metadata_id, source_type, canonical_reference,
                    source_language, is_translation, original_language,
                    dating_period, approximate_date_bce_ce, is_modern_commentary,
                    external_identifier, external_identifier_status, provenance_id,
                    created_at, is_immutable, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    source.source_metadata_id,
                    src_type,
                    source.canonical_reference,
                    src_lang,
                    1 if source.is_translation else 0,
                    source.original_language.upper() if source.original_language else None,
                    source.dating_period,
                    source.approximate_date_bce_ce,
                    1 if source.is_modern_commentary else 0,
                    source.external_identifier,
                    ext_status,
                    prov_id,
                    timestamp,
                    source.notes,
                ),
            )
        return source.source_metadata_id

    # -------------------------------------------------------------------------
    # EPISTEMIC FIREWALL ENFORCEMENT
    # -------------------------------------------------------------------------

    def validate_intertextual_firewalls(
        self,
        relationships: Sequence[IntertextualRelationshipDefinition],
        observations: Sequence[IntertextualObservationDefinition],
        hypotheses: Sequence[IntertextualHypothesisDefinition],
        evidence_links: Sequence[IntertextualEvidenceLinkDefinition],
    ) -> None:
        """
        Validate all 20 epistemic firewalls before atomic commit.
        """
        # 1. Relationship Firewalls
        for r in relationships:
            rel_type = r.relationship_type.upper()
            epist_class = r.epistemic_classification.upper()
            direction = r.direction.upper()
            conf = r.confidence.upper()

            if not r.evidence_id or not str(r.evidence_id).strip():
                raise IntertextualSubsystemError(
                    f"Relationship '{r.relationship_id}': evidence_id cannot be empty."
                )

            # Firewall 11: AI-generated proposal != primary evidence
            if r.is_ai_generated:
                raise AIIntertextualEvidenceFirewallError(
                    f"Relationship '{r.relationship_id}': AI-generated proposal cannot become primary intertextual evidence."
                )

            # Firewall 1 & 4: Lexical similarity != intertextuality / Same wording != automatic quotation
            if rel_type == IntertextualRelationType.LEXICAL_PARALLEL.value:
                if epist_class == EpistemicClassification.DIRECT_QUOTATION.value and not r.has_explicit_quotation_formula:
                    raise SameWordingNotAutomaticQuotationFirewallError(
                        f"Relationship '{r.relationship_id}': Same wording or lexical overlap cannot automatically assert DIRECT_QUOTATION without explicit quotation formula."
                    )
                if epist_class in (
                    EpistemicClassification.DIRECT_QUOTATION.value,
                    EpistemicClassification.STRONG_ALLUSION.value,
                ):
                    raise LexicalSimilarityNotIntertextualityFirewallError(
                        f"Relationship '{r.relationship_id}': Lexical parallel cannot be classified as {epist_class}."
                    )
                if r.status.upper() == IntertextStatus.ESTABLISHED.value and not r.has_explicit_quotation_formula and not r.chronological_precedence_demonstrated:
                    raise LexicalSimilarityNotIntertextualityFirewallError(
                        f"Relationship '{r.relationship_id}': Lexical parallel alone cannot assert intertextual dependence as ESTABLISHED."
                    )

            # Firewall 13: Confidence cannot upgrade evidence
            if rel_type == IntertextualRelationType.THEMATIC_PARALLEL.value and conf in ("CERTAIN", "VERY_HIGH"):
                if epist_class == EpistemicClassification.DIRECT_QUOTATION.value:
                    raise ConfidenceNotEvidenceUpgradeFirewallError(
                        f"Relationship '{r.relationship_id}': High confidence cannot upgrade thematic parallel into DIRECT_QUOTATION."
                    )

            # Firewall 2: Thematic similarity != intertextuality
            if rel_type == IntertextualRelationType.THEMATIC_PARALLEL.value:
                if epist_class in (
                    EpistemicClassification.DIRECT_QUOTATION.value,
                    EpistemicClassification.STRONG_ALLUSION.value,
                    EpistemicClassification.PROBABLE_ALLUSION.value,
                ):
                    raise ThematicSimilarityNotIntertextualityFirewallError(
                        f"Relationship '{r.relationship_id}': Thematic similarity cannot assert direct quotation or strong/probable allusion."
                    )

            # Firewall 3 & 18: Chronology != textual dependence / Chronology only relation
            if r.solely_chronological_basis:
                raise ChronologyOnlyRelationFirewallError(
                    f"Relationship '{r.relationship_id}': Intertextual relation cannot be established solely by chronology."
                )
            if r.chronological_precedence_demonstrated and not r.has_explicit_quotation_formula and rel_type not in (
                IntertextualRelationType.DIRECT_QUOTATION.value,
                IntertextualRelationType.STRONG_ALLUSION.value,
                IntertextualRelationType.PROBABLE_ALLUSION.value,
                IntertextualRelationType.POSSIBLE_ALLUSION.value,
                IntertextualRelationType.TEXTUAL_REUSE.value,
            ) and epist_class in (EpistemicClassification.DIRECT_QUOTATION.value, EpistemicClassification.STRONG_ALLUSION.value):
                raise ChronologyNotDependenceFirewallError(
                    f"Relationship '{r.relationship_id}': Chronological precedence alone cannot assert textual dependence."
                )

            # Firewall 5: Shared tradition != direct quotation
            if rel_type == IntertextualRelationType.TRADITIONAL_PARALLEL.value and epist_class == EpistemicClassification.DIRECT_QUOTATION.value:
                raise SharedTraditionNotDirectQuotationFirewallError(
                    f"Relationship '{r.relationship_id}': Shared tradition cannot be classified as DIRECT_QUOTATION."
                )

            # Firewall 4 & 17: Same wording != automatic quotation / Quotation requires explicit evidence
            if rel_type == IntertextualRelationType.DIRECT_QUOTATION.value or epist_class == EpistemicClassification.DIRECT_QUOTATION.value:
                if not r.has_explicit_quotation_formula:
                    if rel_type == IntertextualRelationType.LEXICAL_PARALLEL.value:
                        raise SameWordingNotAutomaticQuotationFirewallError(
                            f"Relationship '{r.relationship_id}': Same wording or lexical overlap cannot automatically assert DIRECT_QUOTATION without explicit quotation formula."
                        )
                    raise QuotationEvidenceRequiredFirewallError(
                        f"Relationship '{r.relationship_id}': DIRECT_QUOTATION strictly requires explicit quotation formula or evidence; confidence cannot create evidence."
                    )

            # Firewall 8: Reception source != authorial source
            if r.is_reception_history_source and direction == SourceDirection.SOURCE_TO_TARGET.value:
                raise ReceptionSourceNotAuthorialSourceFirewallError(
                    f"Relationship '{r.relationship_id}': Later reception/commentary source cannot be authorial source (SOURCE_TO_TARGET) of earlier biblical text."
                )

            # Firewall 9: Entity identity != textual dependence
            if r.entity_agreement_only:
                if epist_class in (
                    EpistemicClassification.DIRECT_QUOTATION.value,
                    EpistemicClassification.STRONG_ALLUSION.value,
                    EpistemicClassification.PROBABLE_ALLUSION.value,
                ):
                    raise EntityIdentityNotTextualDependenceFirewallError(
                        f"Relationship '{r.relationship_id}': Entity/name agreement alone cannot establish quotation or allusion dependence."
                    )

            # Firewall 10: Unknown direction must remain UNKNOWN
            if direction not in [d.value for d in SourceDirection]:
                raise UnknownDirectionPreservationFirewallError(
                    f"Relationship '{r.relationship_id}': Invalid direction '{direction}'."
                )

        # 2. Observation Firewalls
        for obs in observations:
            # Firewall 19: Intertextual claim cannot become theological claim
            if obs.is_theological_claim:
                raise IntertextualNotTheologicalClaimFirewallError(
                    f"Observation '{obs.observation_id}': Intertextual observation cannot be asserted directly as T4 theological claim."
                )

        # 3. Hypothesis Firewalls
        for hyp in hypotheses:
            # Firewall 14: Retrieval ranking cannot select truth
            if hyp.retrieval_forced_winner:
                raise RetrievalRankingNotTruthFirewallError(
                    f"Hypothesis '{hyp.hypothesis_id}': Retrieval score or rank cannot be forced as authoritative winner."
                )

        # 4. Evidence Link Firewalls
        for link in evidence_links:
            link_class = link.evidence_class.upper()
            link_stance = link.stance.upper()

            # Firewall 6: E9 parallel != E10 intertext
            if link_class != EvidenceClass.E10_INTERTEXTUAL.value:
                raise E9ParallelNotE10IntertextFirewallError(
                    f"Link '{link.link_id}': Intertextual link must use E10_INTERTEXTUAL evidence, got '{link_class}'."
                )

            # Firewall 16: Counter-evidence cannot be silently discarded
            if link_stance in (EvidenceStance.CONTRADICT.value, EvidenceStance.LIMIT.value):
                if not link.is_counter_evidence:
                    raise CounterEvidencePreservationFirewallError(
                        f"Link '{link.link_id}': Stance '{link_stance}' must be explicitly marked as counter-evidence (is_counter_evidence=True)."
                    )

    # -------------------------------------------------------------------------
    # ATOMIC ANALYSIS EXECUTION RUN
    # -------------------------------------------------------------------------

    def execute_analysis_run(
        self,
        run_id: str,
        target_passage_id: Optional[str] = None,
        analyzer_id: str = "analyzer_polya_intertextual",
        analyzer_version: str = "1.0.0",
        target_pericope_id: Optional[str] = None,
        target_source_text_id: Optional[str] = None,
        relationships: Sequence[IntertextualRelationshipDefinition] = (),
        observations: Sequence[IntertextualObservationDefinition] = (),
        hypotheses: Sequence[IntertextualHypothesisDefinition] = (),
        evidence_links: Sequence[IntertextualEvidenceLinkDefinition] = (),
        created_at: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> IntertextualRunResult:
        """
        Execute an immutable intertextual analysis run.
        Integrates with VersionManager, ProvenanceTracker, and EvidenceClaimManager.
        Supports rollback on error and version supersession on reanalysis.
        """
        timestamp = created_at or datetime.now(timezone.utc).isoformat()

        if not target_passage_id and not target_pericope_id and not target_source_text_id:
            raise IntertextualSubsystemError(
                "Intertextual analysis run requires at least one target scope: target_passage_id, target_pericope_id, or target_source_text_id."
            )

        # 1. Enforce Firewalls
        self.validate_intertextual_firewalls(
            relationships=relationships,
            observations=observations,
            hypotheses=hypotheses,
            evidence_links=evidence_links,
        )

        # 2. Compute Deterministic Hashes
        config_dict = {
            "analyzer_id": analyzer_id,
            "analyzer_version": analyzer_version,
            "target_passage_id": target_passage_id,
            "target_pericope_id": target_pericope_id,
        }
        config_hash = compute_canonical_hash(config_dict)

        input_dict = {
            "target_passage_id": target_passage_id,
            "target_pericope_id": target_pericope_id,
            "target_source_text_id": target_source_text_id,
            "relationships_len": len(relationships),
            "observations_len": len(observations),
            "hypotheses_len": len(hypotheses),
            "evidence_links_len": len(evidence_links),
        }
        input_content_hash = compute_canonical_hash(input_dict)

        output_dict = {
            "run_id": run_id,
            "relationships": [asdict(r) for r in relationships],
            "observations": [asdict(o) for o in observations],
            "hypotheses": [asdict(h) for h in hypotheses],
            "evidence_links": [asdict(l) for l in evidence_links],
        }
        output_hash = compute_canonical_hash(output_dict)

        prov_id = f"PROV-IT-{run_id}"
        version_id = f"VER-IT-{run_id}"

        # 3. Transaction Execution
        with self.engine.transaction() as conn:
            # Query prior completed runs matching target scope
            prior_runs = []
            if target_passage_id:
                prior_runs = conn.execute(
                    "SELECT run_id, version_id FROM intertextual_runs WHERE target_passage_id = ? AND status = 'COMPLETED'",
                    (target_passage_id,),
                ).fetchall()
            elif target_pericope_id:
                prior_runs = conn.execute(
                    "SELECT run_id, version_id FROM intertextual_runs WHERE target_pericope_id = ? AND status = 'COMPLETED'",
                    (target_pericope_id,),
                ).fetchall()
            elif target_source_text_id:
                prior_runs = conn.execute(
                    "SELECT run_id, version_id FROM intertextual_runs WHERE target_source_text_id = ? AND status = 'COMPLETED'",
                    (target_source_text_id,),
                ).fetchall()

            # Record Provenance for Run
            provenance_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=run_id,
                content=f"INTERTEXTUAL_RUN:{run_id}:{output_hash}",
                input_data=input_content_hash,
                agent_id=analyzer_id,
                agent_version=analyzer_version,
                conn=conn,
            )
            prov_id = provenance_rec.provenance_id

            # Record Version
            version_rec = self.version_manager.create_version(
                object_type="INTERTEXTUAL_RUN",
                object_id=run_id,
                content_hash=output_hash,
                change_reason=ChangeReason.INITIAL_CREATION,
                created_by=analyzer_id,
                provenance_id=prov_id,
                version_id=version_id,
                conn=conn,
            )
            version_id = version_rec.version_id

            # Supersede prior completed runs on this target scope and link version lineage
            for old_run_id, old_ver_id in prior_runs:
                conn.execute(
                    "UPDATE intertextual_runs SET status = 'SUPERSEDED' WHERE run_id = ?",
                    (old_run_id,),
                )
                if old_ver_id:
                    self.version_manager.supersede_version(
                        version_id=old_ver_id,
                        superseded_by_version_id=version_id,
                        conn=conn,
                    )

            # 4. Insert Run Record
            conn.execute(
                """
                INSERT INTO intertextual_runs (
                    run_id, target_passage_id, target_pericope_id, target_source_text_id,
                    version_id, provenance_id, analyzer_id, analyzer_version,
                    configuration_hash, input_content_hash, output_hash,
                    status, is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?)
                """,
                (
                    run_id,
                    target_passage_id,
                    target_pericope_id,
                    target_source_text_id,
                    version_id,
                    prov_id,
                    analyzer_id,
                    analyzer_version,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    timestamp,
                    metadata_json,
                ),
            )

            # 5. Insert Relationships
            for r in relationships:
                r_prov_id = r.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO intertextual_relationships (
                        relationship_id, run_id, target_passage_id, target_pericope_id,
                        source_metadata_id, relationship_type, epistemic_classification,
                        direction, status, target_language, source_language,
                        is_translation_mediated, has_explicit_quotation_formula,
                        quotation_formula_text, chronological_precedence_demonstrated,
                        solely_chronological_basis, is_ai_generated, is_reception_history_source,
                        entity_agreement_only, confidence, confidence_score,
                        retrieval_rank, retrieval_score, evidence_id, provenance_id,
                        created_at, is_immutable, notes
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, 1, ?
                    )
                    """,
                    (
                        r.relationship_id,
                        run_id,
                        r.target_passage_id or target_passage_id,
                        r.target_pericope_id or target_pericope_id,
                        r.source_metadata_id,
                        r.relationship_type.upper(),
                        r.epistemic_classification.upper(),
                        r.direction.upper(),
                        r.status.upper(),
                        r.target_language.upper(),
                        r.source_language.upper(),
                        1 if r.is_translation_mediated else 0,
                        1 if r.has_explicit_quotation_formula else 0,
                        r.quotation_formula_text,
                        1 if r.chronological_precedence_demonstrated else 0,
                        1 if r.solely_chronological_basis else 0,
                        1 if r.is_ai_generated else 0,
                        1 if r.is_reception_history_source else 0,
                        1 if r.entity_agreement_only else 0,
                        r.confidence.upper(),
                        r.confidence_score,
                        r.retrieval_rank,
                        r.retrieval_score,
                        r.evidence_id,
                        r_prov_id,
                        timestamp,
                        r.notes,
                    ),
                )

            # 6. Insert Observations
            for obs in observations:
                obs_prov_id = obs.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO intertextual_observations (
                        observation_id, run_id, relationship_id, observation_type,
                        observation_text, shared_elements, is_theological_claim,
                        evidence_id, provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        obs.observation_id,
                        run_id,
                        obs.relationship_id,
                        obs.observation_type.upper(),
                        obs.observation_text,
                        obs.shared_elements,
                        1 if obs.is_theological_claim else 0,
                        obs.evidence_id,
                        obs_prov_id,
                        timestamp,
                        obs.notes,
                    ),
                )

            # 7. Insert Hypotheses
            for hyp in hypotheses:
                hyp_prov_id = hyp.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO intertextual_hypotheses (
                        hypothesis_id, run_id, target_passage_id, hypothesis_code,
                        hypothesis_description, proposed_relationship_type, source_metadata_id,
                        is_primary, status, retrieval_rank, retrieval_score,
                        retrieval_forced_winner, provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        hyp.hypothesis_id,
                        run_id,
                        hyp.target_passage_id or target_passage_id,
                        hyp.hypothesis_code,
                        hyp.hypothesis_description,
                        hyp.proposed_relationship_type.upper(),
                        hyp.source_metadata_id,
                        1 if hyp.is_primary else 0,
                        hyp.status.upper(),
                        hyp.retrieval_rank,
                        hyp.retrieval_score,
                        1 if hyp.retrieval_forced_winner else 0,
                        hyp_prov_id,
                        timestamp,
                        hyp.notes,
                    ),
                )

            # 8. Insert Evidence Links
            for link in evidence_links:
                conn.execute(
                    """
                    INSERT INTO intertextual_evidence_links (
                        link_id, run_id, relationship_id, hypothesis_id,
                        evidence_id, evidence_class, stance, weight,
                        is_counter_evidence, reasoning, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        link.link_id,
                        run_id,
                        link.relationship_id,
                        link.hypothesis_id,
                        link.evidence_id,
                        link.evidence_class.upper(),
                        link.stance.upper(),
                        link.weight,
                        1 if link.is_counter_evidence else 0,
                        link.reasoning,
                        timestamp,
                        link.notes,
                    ),
                )

        return IntertextualRunResult(
            run_id=run_id,
            version_id=version_id,
            provenance_id=prov_id,
            relationships_count=len(relationships),
            observations_count=len(observations),
            hypotheses_count=len(hypotheses),
            evidence_links_count=len(evidence_links),
            output_hash=output_hash,
            created_at=timestamp,
        )

    # -------------------------------------------------------------------------
    # INSPECTION ACCESSORS
    # -------------------------------------------------------------------------

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run record by ID."""
        with self.engine.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM intertextual_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_relationships_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all relationships for a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM intertextual_relationships WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_observations_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all observations for a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM intertextual_observations WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_hypotheses_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all hypotheses for a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM intertextual_hypotheses WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_evidence_links_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all evidence links for a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM intertextual_evidence_links WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]
