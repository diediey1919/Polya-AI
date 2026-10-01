"""
Reception History Engine (Task 3.4).
Evidence Classes: E11_EARLY_RECEPTION, E12_LATER_INTERPRETATION.
Specification: Architecture v2.0 — FROZEN.

Provides provenance-first, immutable evaluation of historical reception and
later interpretation of biblical texts without allowing conclusions to outrun evidence.

Epistemic Firewalls:
  1. Later interpretation != original authorial intent
  2. Early reception != proof of original meaning
  3. Patristic interpretation != automatic apostolic interpretation
  4. Rabbinic interpretation != automatic Second Temple interpretation
  5. Medieval interpretation != automatic biblical interpretation
  6. Modern scholarly consensus != textual evidence
  7. Denominational doctrine != ancient authorial intent
  8. Chronology != influence
  9. Citation != interpretation
  10. Allusion != quotation
  11. Translation != original source
  12. Lexical similarity != reception
  13. Thematic parallel != reception
  14. Doctrinal formulation != textual reading
  15. Reception source != authorial source
  16. Reception history != canonical authority
  17. Reception history != theological truth
  18. Majority interpretation != verified fact
  19. AI-generated summary != primary source
  20. Modern commentary != historical witness
  21. External identifier != verified identity
  22. Confidence score != evidence upgrade
  23. Temporal direction must not be reversed without evidence
  24. Counter-evidence cannot be suppressed
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
    ReceptionAISummaryNotPrimarySourceFirewallError,
    ReceptionActorNotFoundError,
    ReceptionAllusionNotQuotationFirewallError,
    ReceptionAuthorialIntentFirewallError,
    ReceptionChronologyNotInfluenceFirewallError,
    ReceptionCitationNotInterpretationFirewallError,
    ReceptionClaimNotFoundError,
    ReceptionConcurrencyError,
    ReceptionConfidenceNotUpgradeFirewallError,
    ReceptionCounterEvidencePreservationFirewallError,
    ReceptionDenominationalNotAuthorialFirewallError,
    ReceptionDoctrinalNotTextualReadingFirewallError,
    ReceptionEarlyNotApostolicFirewallError,
    ReceptionHistorySubsystemError,
    ReceptionImmutabilityError,
    ReceptionInvalidProvenanceError,
    ReceptionInvalidVersionError,
    ReceptionLexicalNotReceptionFirewallError,
    ReceptionMajorityNotFactFirewallError,
    ReceptionMedievalNotBiblicalFirewallError,
    ReceptionModernCommentaryNotWitnessFirewallError,
    ReceptionNotCanonicalAuthorityFirewallError,
    ReceptionRabbinicNotSecondTempleFirewallError,
    ReceptionRecordNotFoundError,
    ReceptionRelationNotFoundError,
    ReceptionScholarlyNotTextualFirewallError,
    ReceptionSourceNotAuthorialSourceFirewallError,
    ReceptionSourceNotFoundError,
    ReceptionTemporalDirectionFirewallError,
    ReceptionThematicNotReceptionFirewallError,
    ReceptionTheologicalTruthFirewallError,
    ReceptionTranslationNotOriginalFirewallError,
    ReceptionUnverifiedIdentifierFirewallError,
    ReceptionValidationError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceDefinition,
    EvidenceRelationship,
    EvidenceStatus,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.versioning import ChangeReason, VersionManager


# =============================================================================
# TAXONOMIES AND ENUMS
# =============================================================================

class ReceptionEra(str, Enum):
    """Controlled reception eras distinguishing historical strata."""
    EARLY_RECEPTION = "EARLY_RECEPTION"
    PATRISTIC = "PATRISTIC"
    RABBINIC = "RABBINIC"
    MEDIEVAL = "MEDIEVAL"
    REFORMATION_EARLY_MODERN = "REFORMATION_EARLY_MODERN"
    MODERN = "MODERN"
    DENOMINATIONAL = "DENOMINATIONAL"
    SCHOLARLY = "SCHOLARLY"
    THEOLOGICAL = "THEOLOGICAL"


class ActorType(str, Enum):
    """Controlled types for reception actors."""
    INDIVIDUAL_AUTHOR = "INDIVIDUAL_AUTHOR"
    CHURCH_FATHER = "CHURCH_FATHER"
    RABBINIC_SAGE = "RABBINIC_SAGE"
    MEDIEVAL_SCHOLAR = "MEDIEVAL_SCHOLAR"
    REFORMER = "REFORMER"
    COMMUNITY = "COMMUNITY"
    COUNCIL_SYNOD = "COUNCIL_SYNOD"
    DENOMINATION = "DENOMINATION"
    MODERN_SCHOLAR = "MODERN_SCHOLAR"
    ANONYMOUS_TRADITION = "ANONYMOUS_TRADITION"


class ActorIdentityStatus(str, Enum):
    """Identity status for historical actors."""
    DEFINITE = "DEFINITE"
    UNCERTAIN = "UNCERTAIN"
    ANONYMOUS = "ANONYMOUS"
    DISPUTED = "DISPUTED"


class HistoricalEra(str, Enum):
    """Historical eras for dating reception actors."""
    APOSTOLIC_SUBAPOSTOLIC = "APOSTOLIC_SUBAPOSTOLIC"
    PATRISTIC_ANTE_NICENE = "PATRISTIC_ANTE_NICENE"
    PATRISTIC_POST_NICENE = "PATRISTIC_POST_NICENE"
    RABBINIC_TANNAITIC = "RABBINIC_TANNAITIC"
    RABBINIC_AMORAIC = "RABBINIC_AMORAIC"
    MEDIEVAL_BYZANTINE = "MEDIEVAL_BYZANTINE"
    MEDIEVAL_WESTERN = "MEDIEVAL_WESTERN"
    MEDIEVAL_ISLAMIC_ERA_JUDAISM = "MEDIEVAL_ISLAMIC_ERA_JUDAISM"
    REFORMATION_EARLY_MODERN = "REFORMATION_EARLY_MODERN"
    MODERN_CRITICAL = "MODERN_CRITICAL"
    MODERN_DENOMINATIONAL = "MODERN_DENOMINATIONAL"
    UNKNOWN = "UNKNOWN"


class DatePrecision(str, Enum):
    """Date precision levels for reception actors and sources."""
    EXACT = "EXACT"
    DECADE = "DECADE"
    CENTURY = "CENTURY"
    CIRCA = "CIRCA"
    UNKNOWN = "UNKNOWN"


class ReceptionSourceType(str, Enum):
    """Controlled types for reception sources."""
    PATRISTIC_HOMILY = "PATRISTIC_HOMILY"
    PATRISTIC_COMMENTARY = "PATRISTIC_COMMENTARY"
    PATRISTIC_TREATISE = "PATRISTIC_TREATISE"
    PATRISTIC_EPISTLE = "PATRISTIC_EPISTLE"
    RABBINIC_MISHNAH = "RABBINIC_MISHNAH"
    RABBINIC_TALMUD = "RABBINIC_TALMUD"
    RABBINIC_MIDRASH = "RABBINIC_MIDRASH"
    RABBINIC_TARGUM = "RABBINIC_TARGUM"
    MEDIEVAL_GLOSS_COMMENTARY = "MEDIEVAL_GLOSS_COMMENTARY"
    MEDIEVAL_SCHOLASTIC_SUMMA = "MEDIEVAL_SCHOLASTIC_SUMMA"
    REFORMATION_COMMENTARY = "REFORMATION_COMMENTARY"
    REFORMATION_CONFESSION = "REFORMATION_CONFESSION"
    CREED_COUNCIL_DECREE = "CREED_COUNCIL_DECREE"
    LITURGICAL_HYMN_TEXT = "LITURGICAL_HYMN_TEXT"
    MODERN_ACADEMIC_COMMENTARY = "MODERN_ACADEMIC_COMMENTARY"
    MODERN_CRITICAL_MONOGRAPH = "MODERN_CRITICAL_MONOGRAPH"
    DENOMINATIONAL_CATECHISM = "DENOMINATIONAL_CATECHISM"
    ANCIENT_TRANSLATION_SOURCE = "ANCIENT_TRANSLATION_SOURCE"


class ExegeticalMethod(str, Enum):
    """Controlled hermeneutical/exegetical methods."""
    LITERAL_HISTORICAL = "LITERAL_HISTORICAL"
    ALLEGORICAL_TYPOLOGICAL = "ALLEGORICAL_TYPOLOGICAL"
    MORAL_TROPOLOGICAL = "MORAL_TROPOLOGICAL"
    ANAGOGICAL_ESCHATOLOGICAL = "ANAGOGICAL_ESCHATOLOGICAL"
    MIDRASHIC_PESHER = "MIDRASHIC_PESHER"
    POLEMICAL_APOLOGETIC = "POLEMICAL_APOLOGETIC"
    DOGMATIC_SYSTEMATIC = "DOGMATIC_SYSTEMATIC"
    HISTORICAL_CRITICAL = "HISTORICAL_CRITICAL"
    LITERARY_CANONICAL = "LITERARY_CANONICAL"
    UNKNOWN = "UNKNOWN"


class ReceptionClaimType(str, Enum):
    """Epistemic types of reception claims."""
    RECEPTION_OCCURRENCE = "RECEPTION_OCCURRENCE"
    HERMENEUTICAL_READING = "HERMENEUTICAL_READING"
    INFLUENCE_HYPOTHESIS = "INFLUENCE_HYPOTHESIS"
    TRADITION_CONTINUITY = "TRADITION_CONTINUITY"
    DOCTRINAL_DEVELOPMENT = "DOCTRINAL_DEVELOPMENT"
    RECEPTION_DIVERGENCE = "RECEPTION_DIVERGENCE"
    AUTHORIAL_INTENT_PROPOSAL = "AUTHORIAL_INTENT_PROPOSAL"


class TemporalDirection(str, Enum):
    """Temporal direction connecting source and reception."""
    TEXT_TO_RECEPTION = "TEXT_TO_RECEPTION"
    RECEPTION_TO_LATER_RECEPTION = "RECEPTION_TO_LATER_RECEPTION"
    RECEPTION_TO_INTERPRETATION = "RECEPTION_TO_INTERPRETATION"
    UNKNOWN = "UNKNOWN"


class ClaimRelevance(str, Enum):
    """Epistemic relevance scope for reception claims."""
    RECEPTION_HISTORY_PRIMARY = "RECEPTION_HISTORY_PRIMARY"
    AUTHORIAL_INTENT_SECONDARY = "AUTHORIAL_INTENT_SECONDARY"
    THEOLOGICAL_TRADITION_RELEVANT = "THEOLOGICAL_TRADITION_RELEVANT"
    IRRELEVANT_TO_ORIGINAL_MEANING = "IRRELEVANT_TO_ORIGINAL_MEANING"


class ReceptionRelationType(str, Enum):
    """Controlled relation types between reception records."""
    DIRECT_DEPENDENCE = "DIRECT_DEPENDENCE"
    TRADITION_DEVELOPMENT = "TRADITION_DEVELOPMENT"
    HERMENEUTICAL_POLEMIC = "HERMENEUTICAL_POLEMIC"
    COMPETING_INTERPRETATION = "COMPETING_INTERPRETATION"
    HARMONIZING_READING = "HARMONIZING_READING"
    INDEPENDENT_PARALLEL = "INDEPENDENT_PARALLEL"
    UNKNOWN_RELATION = "UNKNOWN_RELATION"


class ExternalIdentifierStatus(str, Enum):
    """Verification status of external authority identifiers."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"


class EvidenceStance(str, Enum):
    """Stance of evidence toward a claim."""
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    QUALIFY = "QUALIFY"
    LIMIT = "LIMIT"
    REFINE = "REFINE"


# =============================================================================
# DATA STRUCTURES / DEFINITIONS
# =============================================================================

@dataclass(frozen=True)
class ReceptionActorDefinition:
    """Immutable definition of a historical reception actor."""
    actor_id: str
    canonical_name: str
    actor_type: str
    historical_era: str
    identity_status: str = ActorIdentityStatus.DEFINITE.value
    approximate_start_bce_ce: Optional[int] = None
    approximate_end_bce_ce: Optional[int] = None
    date_precision: str = DatePrecision.EXACT.value
    tradition_affiliation: Optional[str] = None
    external_identifier: str = "LOCAL"
    external_identifier_status: str = ExternalIdentifierStatus.UNVERIFIED.value
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceptionSourceDefinition:
    """Immutable definition of a reception source document."""
    source_id: str
    canonical_work_title: str
    source_type: str
    source_language: str
    primary_actor_id: Optional[str] = None
    is_translation: bool = False
    original_language: Optional[str] = None
    dating_period: Optional[str] = None
    approximate_date_bce_ce: Optional[int] = None
    date_precision: str = DatePrecision.EXACT.value
    is_modern_commentary: bool = False
    is_primary_historical_witness: bool = True
    external_identifier: str = "LOCAL"
    external_identifier_status: str = ExternalIdentifierStatus.UNVERIFIED.value
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceptionRecordDefinition:
    """Immutable definition of a discrete reception witness on a passage."""
    record_id: str
    source_id: str
    witness_passage_reference: str
    citation_text: str
    citation_language: str
    exegetical_method: str
    hermeneutical_summary: str
    reception_era: str
    evidence_id: str
    actor_id: Optional[str] = None
    target_passage_id: Optional[str] = None
    target_pericope_id: Optional[str] = None
    is_translation_mediated: bool = False
    translation_language: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceptionClaimDefinition:
    """Immutable definition of an epistemic claim derived from reception analysis."""
    claim_id: str
    record_id: str
    claim_type: str
    claim_tier: str
    claim_statement: str
    temporal_direction: str
    claim_relevance: str
    confidence_level: str
    ledger_claim_id: str
    is_authorial_intent_equated: bool = False
    is_theological_truth_equated: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceptionRelationDefinition:
    """Immutable definition of a cross-record relation or competing hypothesis."""
    relation_id: str
    source_record_id: str
    target_record_id: str
    relation_type: str
    temporal_direction: str
    hypothesis_id: str
    chronological_order_verified: bool = False
    is_influence_asserted: bool = False
    counter_evidence_preserved: bool = True
    notes: Optional[str] = None


@dataclass(frozen=True)
class ReceptionEvidenceLinkDefinition:
    """Immutable link between reception record, claim, and evidence ledger."""
    link_id: str
    record_id: str
    evidence_id: str
    evidence_class: str
    claim_id: str
    stance: str
    is_ai_generated: bool = False
    is_synthetic_evaluation: bool = False


@dataclass(frozen=True)
class ReceptionRunResult:
    """Immutable result metadata for a reception analysis run."""
    run_id: str
    target_passage_id: Optional[str]
    target_pericope_id: Optional[str]
    target_source_text_id: Optional[str]
    version_id: str
    provenance_id: str
    output_hash: str
    records_count: int
    claims_count: int
    relations_count: int
    links_count: int
    created_at: str


# =============================================================================
# RECEPTION HISTORY MANAGER
# =============================================================================

class ReceptionHistoryManager:
    """
    Subsystem manager for Task 3.4 Reception History Engine.
    Coordinates immutable registration of actors, sources, records, claims,
    cross-record relations, and ledger associations under strict epistemic firewalls.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: VersionManager,
        provenance_tracker: ProvenanceTracker,
        evidence_claim_manager: EvidenceClaimManager,
    ):
        self.engine = engine
        self.version_manager = version_manager
        self.provenance_tracker = provenance_tracker
        self.evidence_claim_manager = evidence_claim_manager

    # -------------------------------------------------------------------------
    # ACTOR REGISTRATION
    # -------------------------------------------------------------------------
    def register_actor(self, actor: ReceptionActorDefinition) -> str:
        """Register a historical actor under strict validation."""
        # Validation checks
        if actor.approximate_start_bce_ce is not None and actor.approximate_end_bce_ce is not None:
            if actor.approximate_start_bce_ce > actor.approximate_end_bce_ce:
                raise ReceptionTemporalDirectionFirewallError(
                    f"Actor start date ({actor.approximate_start_bce_ce}) cannot be after end date ({actor.approximate_end_bce_ce})."
                )

        # Firewall 21: External identifier != verified identity
        if actor.external_identifier_status == ExternalIdentifierStatus.VERIFIED.value:
            if not actor.external_identifier or actor.external_identifier in ("LOCAL", "UNVERIFIED"):
                raise ReceptionUnverifiedIdentifierFirewallError(
                    "Actor external identifier must be a valid external reference to be marked VERIFIED."
                )

        now_utc = datetime.now(timezone.utc).isoformat()
        content_str = f"{actor.actor_id}|{actor.canonical_name}|{actor.actor_type}|{actor.historical_era}"

        with self.engine.transaction() as conn:
            prov = self.provenance_tracker.record_origin(
                target_type=TargetType.TEXTUAL_WITNESS,
                target_id=actor.actor_id,
                content=content_str,
                agent_id="reception_actor_registrar",
                conn=conn,
            )
            conn.execute(
                """
                INSERT INTO reception_actors (
                    actor_id, canonical_name, actor_type, identity_status, historical_era,
                    approximate_start_bce_ce, approximate_end_bce_ce, date_precision,
                    tradition_affiliation, external_identifier, external_identifier_status,
                    provenance_id, created_at, is_immutable, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    actor.actor_id,
                    actor.canonical_name,
                    actor.actor_type,
                    actor.identity_status,
                    actor.historical_era,
                    actor.approximate_start_bce_ce,
                    actor.approximate_end_bce_ce,
                    actor.date_precision,
                    actor.tradition_affiliation,
                    actor.external_identifier,
                    actor.external_identifier_status,
                    prov.provenance_id,
                    now_utc,
                    actor.notes,
                ),
            )
        return actor.actor_id

    # -------------------------------------------------------------------------
    # SOURCE REGISTRATION
    # -------------------------------------------------------------------------
    def register_source(self, source: ReceptionSourceDefinition) -> str:
        """Register a reception source document under epistemic firewalls."""
        # Firewall 11: Translation != original source text
        if source.is_translation:
            if not source.original_language or source.original_language == source.source_language:
                raise ReceptionTranslationNotOriginalFirewallError(
                    "Translation must specify original language distinct from translation source language."
                )

        # Firewall 20: Modern commentary != ancient historical witness
        if source.is_modern_commentary and source.is_primary_historical_witness:
            raise ReceptionModernCommentaryNotWitnessFirewallError(
                f"Modern commentary '{source.source_id}' cannot masquerade as primary historical witness."
            )

        # Firewall 21: External identifier != verified identity
        if source.external_identifier_status == ExternalIdentifierStatus.VERIFIED.value:
            if not source.external_identifier or source.external_identifier in ("LOCAL", "UNVERIFIED"):
                raise ReceptionUnverifiedIdentifierFirewallError(
                    "Source external identifier must be a valid external reference to be marked VERIFIED."
                )

        now_utc = datetime.now(timezone.utc).isoformat()
        content_str = f"{source.source_id}|{source.canonical_work_title}|{source.source_type}|{source.source_language}"

        with self.engine.transaction() as conn:
            prov = self.provenance_tracker.record_origin(
                target_type=TargetType.TEXTUAL_WITNESS,
                target_id=source.source_id,
                content=content_str,
                agent_id="reception_source_registrar",
                conn=conn,
            )
            conn.execute(
                """
                INSERT INTO reception_sources (
                    source_id, canonical_work_title, source_type, primary_actor_id,
                    source_language, is_translation, original_language, dating_period,
                    approximate_date_bce_ce, date_precision, is_modern_commentary,
                    is_primary_historical_witness, external_identifier, external_identifier_status,
                    provenance_id, created_at, is_immutable, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                """,
                (
                    source.source_id,
                    source.canonical_work_title,
                    source.source_type,
                    source.primary_actor_id,
                    source.source_language,
                    1 if source.is_translation else 0,
                    source.original_language,
                    source.dating_period,
                    source.approximate_date_bce_ce,
                    source.date_precision,
                    1 if source.is_modern_commentary else 0,
                    1 if source.is_primary_historical_witness else 0,
                    source.external_identifier,
                    source.external_identifier_status,
                    prov.provenance_id,
                    now_utc,
                    source.notes,
                ),
            )
        return source.source_id

    # -------------------------------------------------------------------------
    # ANALYSIS RUN EXECUTION (Full Pipeline)
    # -------------------------------------------------------------------------
    def execute_analysis_run(
        self,
        run_id: str,
        target_passage_id: Optional[str] = None,
        target_pericope_id: Optional[str] = None,
        target_source_text_id: Optional[str] = None,
        analyzer_id: str = "reception_engine_standard",
        analyzer_version: str = "1.0.0",
        records: Sequence[ReceptionRecordDefinition] = (),
        claims: Sequence[ReceptionClaimDefinition] = (),
        relations: Sequence[ReceptionRelationDefinition] = (),
        evidence_links: Sequence[ReceptionEvidenceLinkDefinition] = (),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReceptionRunResult:
        """
        Executes a complete Reception History analysis run in a single atomic transaction.
        Enforces all 24 epistemic firewalls before persisting.
        """
        if not target_passage_id and not target_pericope_id and not target_source_text_id:
            raise ReceptionHistorySubsystemError(
                "Reception analysis run must target at least one passage, pericope, or source text."
            )

        # 1. Epistemic Firewall Validations
        self._validate_firewalls(
            records=records,
            claims=claims,
            relations=relations,
            evidence_links=evidence_links,
        )

        now_utc = datetime.now(timezone.utc).isoformat()

        # Deterministic Input Content Hash
        input_payload = {
            "target_passage_id": target_passage_id,
            "target_pericope_id": target_pericope_id,
            "target_source_text_id": target_source_text_id,
            "analyzer_id": analyzer_id,
            "analyzer_version": analyzer_version,
            "records": [asdict(r) for r in records],
            "claims": [asdict(c) for c in claims],
            "relations": [asdict(rel) for rel in relations],
            "evidence_links": [asdict(lnk) for lnk in evidence_links],
        }
        input_content_hash = hashlib.sha256(
            json.dumps(input_payload, sort_keys=True).encode("utf-8")
        ).hexdigest()

        config_hash = hashlib.sha256(
            f"{analyzer_id}:{analyzer_version}".encode("utf-8")
        ).hexdigest()

        output_hash = hashlib.sha256(
            f"{input_content_hash}:{len(records)}:{len(claims)}:{len(relations)}:{len(evidence_links)}".encode("utf-8")
        ).hexdigest()

        with self.engine.transaction() as conn:
            # Handle versioning & supersession for re-runs
            target_obj_id = target_passage_id or target_pericope_id or target_source_text_id or run_id
            current_version = self.version_manager.get_current_version("RECEPTION_ANALYSIS", target_obj_id, conn=conn)

            parent_version_id = current_version.version_id if current_version else None
            supersede = parent_version_id is not None

            prov_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=run_id,
                content=f"RECEPTION_RUN:{run_id}:{output_hash}",
                input_data=input_content_hash,
                agent_id=analyzer_id,
                agent_version=analyzer_version,
                conn=conn,
            )

            new_version = self.version_manager.create_version(
                object_type="RECEPTION_ANALYSIS",
                object_id=target_obj_id,
                content_hash=output_hash,
                parent_version_id=parent_version_id,
                provenance_id=prov_rec.provenance_id,
                change_reason=ChangeReason.REANALYSIS if supersede else ChangeReason.INITIAL_CREATION,
                supersede_previous=supersede,
                conn=conn,
            )

            # Check for existing runs targeting same passage/pericope/source_text and mark SUPERSEDED
            if target_passage_id:
                conn.execute(
                    """
                    UPDATE reception_runs
                    SET status = 'SUPERSEDED'
                    WHERE target_passage_id = ? AND status = 'COMPLETED';
                    """,
                    (target_passage_id,),
                )
            if target_pericope_id:
                conn.execute(
                    """
                    UPDATE reception_runs
                    SET status = 'SUPERSEDED'
                    WHERE target_pericope_id = ? AND status = 'COMPLETED';
                    """,
                    (target_pericope_id,),
                )
            if target_source_text_id:
                conn.execute(
                    """
                    UPDATE reception_runs
                    SET status = 'SUPERSEDED'
                    WHERE target_source_text_id = ? AND status = 'COMPLETED';
                    """,
                    (target_source_text_id,),
                )

            # Insert reception run
            conn.execute(
                """
                INSERT INTO reception_runs (
                    run_id, target_passage_id, target_pericope_id, target_source_text_id,
                    version_id, provenance_id, analyzer_id, analyzer_version,
                    configuration_hash, input_content_hash, output_hash, status,
                    is_exact_reproducible, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?);
                """,
                (
                    run_id,
                    target_passage_id,
                    target_pericope_id,
                    target_source_text_id,
                    new_version.version_id,
                    prov_rec.provenance_id,
                    analyzer_id,
                    analyzer_version,
                    config_hash,
                    input_content_hash,
                    output_hash,
                    now_utc,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            # Insert reception records
            for rec in records:
                rec_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=rec.record_id,
                    content=rec.citation_text,
                    agent_id=analyzer_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO reception_records (
                        record_id, run_id, source_id, actor_id, target_passage_id,
                        target_pericope_id, witness_passage_reference, citation_text,
                        citation_language, exegetical_method, hermeneutical_summary,
                        reception_era, is_translation_mediated, translation_language,
                        evidence_id, version_id, provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                    """,
                    (
                        rec.record_id,
                        run_id,
                        rec.source_id,
                        rec.actor_id,
                        rec.target_passage_id or target_passage_id,
                        rec.target_pericope_id or target_pericope_id,
                        rec.witness_passage_reference,
                        rec.citation_text,
                        rec.citation_language,
                        rec.exegetical_method,
                        rec.hermeneutical_summary,
                        rec.reception_era,
                        1 if rec.is_translation_mediated else 0,
                        rec.translation_language,
                        rec.evidence_id,
                        new_version.version_id,
                        rec_prov.provenance_id,
                        now_utc,
                        rec.notes,
                    ),
                )

            # Insert reception claims
            for clm in claims:
                clm_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.CLAIM,
                    target_id=clm.claim_id,
                    content=clm.claim_statement,
                    agent_id=analyzer_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO reception_claims (
                        claim_id, run_id, record_id, claim_type, claim_tier,
                        claim_statement, temporal_direction, claim_relevance,
                        is_authorial_intent_equated, is_theological_truth_equated,
                        confidence_level, ledger_claim_id, provenance_id, created_at,
                        is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?, 1, ?);
                    """,
                    (
                        clm.claim_id,
                        run_id,
                        clm.record_id,
                        clm.claim_type,
                        clm.claim_tier,
                        clm.claim_statement,
                        clm.temporal_direction,
                        clm.claim_relevance,
                        clm.confidence_level,
                        clm.ledger_claim_id,
                        clm_prov.provenance_id,
                        now_utc,
                        clm.notes,
                    ),
                )

            # Insert reception relations
            for rel in relations:
                rel_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.INTERPRETATION,
                    target_id=rel.relation_id,
                    content=f"{rel.source_record_id}:{rel.target_record_id}:{rel.relation_type}",
                    agent_id=analyzer_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO reception_relations (
                        relation_id, run_id, source_record_id, target_record_id,
                        relation_type, temporal_direction, chronological_order_verified,
                        is_influence_asserted, hypothesis_id, counter_evidence_preserved,
                        provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
                    """,
                    (
                        rel.relation_id,
                        run_id,
                        rel.source_record_id,
                        rel.target_record_id,
                        rel.relation_type,
                        rel.temporal_direction,
                        1 if rel.chronological_order_verified else 0,
                        1 if rel.is_influence_asserted else 0,
                        rel.hypothesis_id,
                        1 if rel.counter_evidence_preserved else 0,
                        rel_prov.provenance_id,
                        now_utc,
                        rel.notes,
                    ),
                )

            # Insert reception evidence links
            for lnk in evidence_links:
                lnk_prov = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.EVIDENCE,
                    target_id=lnk.link_id,
                    content=f"{lnk.record_id}:{lnk.evidence_id}:{lnk.claim_id}",
                    agent_id=analyzer_id,
                    conn=conn,
                )
                conn.execute(
                    """
                    INSERT INTO reception_evidence_links (
                        link_id, run_id, record_id, evidence_id, evidence_class,
                        claim_id, stance, is_ai_generated, is_synthetic_evaluation,
                        provenance_id, created_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 1);
                    """,
                    (
                        lnk.link_id,
                        run_id,
                        lnk.record_id,
                        lnk.evidence_id,
                        lnk.evidence_class,
                        lnk.claim_id,
                        lnk.stance,
                        lnk_prov.provenance_id,
                        now_utc,
                    ),
                )

        return ReceptionRunResult(
            run_id=run_id,
            target_passage_id=target_passage_id,
            target_pericope_id=target_pericope_id,
            target_source_text_id=target_source_text_id,
            version_id=new_version.version_id,
            provenance_id=prov_rec.provenance_id,
            output_hash=output_hash,
            records_count=len(records),
            claims_count=len(claims),
            relations_count=len(relations),
            links_count=len(evidence_links),
            created_at=now_utc,
        )

    # -------------------------------------------------------------------------
    # FIREWALL VALIDATION LOGIC
    # -------------------------------------------------------------------------
    def _validate_firewalls(
        self,
        records: Sequence[ReceptionRecordDefinition],
        claims: Sequence[ReceptionClaimDefinition],
        relations: Sequence[ReceptionRelationDefinition],
        evidence_links: Sequence[ReceptionEvidenceLinkDefinition],
    ) -> None:
        """Validates all epistemic firewalls across records, claims, relations, and links."""

        record_map = {r.record_id: r for r in records}

        # Validate Claims
        for clm in claims:
            stmt_lower = clm.claim_statement.lower()

            # Firewall 1, 3, 4, 5, 7: Authorial intent conflations
            if clm.is_authorial_intent_equated:
                rec_era = record_map[clm.record_id].reception_era if clm.record_id in record_map else None
                if not rec_era:
                    with self.engine.connect() as q_conn:
                        row = q_conn.execute("SELECT reception_era FROM reception_records WHERE record_id = ?", (clm.record_id,)).fetchone()
                        if row:
                            rec_era = row[0]

                if rec_era in (ReceptionEra.EARLY_RECEPTION.value, ReceptionEra.PATRISTIC.value) or "apostolic" in stmt_lower:
                    raise ReceptionEarlyNotApostolicFirewallError(
                        f"Reception claim '{clm.claim_id}' illicitly equates patristic/early reception with apostolic intent."
                    )
                if rec_era == ReceptionEra.RABBINIC.value or "second temple" in stmt_lower or "rabbinic" in stmt_lower:
                    raise ReceptionRabbinicNotSecondTempleFirewallError(
                        f"Reception claim '{clm.claim_id}' illicitly equates rabbinic reception with Second Temple intent."
                    )
                if rec_era == ReceptionEra.MEDIEVAL.value or "biblical intent" in stmt_lower or "medieval" in stmt_lower:
                    raise ReceptionMedievalNotBiblicalFirewallError(
                        f"Reception claim '{clm.claim_id}' illicitly equates medieval reception with ancient biblical intent."
                    )
                if rec_era in (ReceptionEra.REFORMATION_EARLY_MODERN.value, ReceptionEra.DENOMINATIONAL.value) or "denominational" in stmt_lower or "reformation" in stmt_lower:
                    raise ReceptionDenominationalNotAuthorialFirewallError(
                        f"Reception claim '{clm.claim_id}' illicitly equates denominational doctrine with ancient authorial intent."
                    )
                raise ReceptionAuthorialIntentFirewallError(
                    f"Reception claim '{clm.claim_id}' illicitly equates reception with original authorial intent."
                )

            # Firewall 17 & 22: Theological truth & confidence upgrade
            if clm.is_theological_truth_equated:
                if "high confidence" in stmt_lower or "confidence score" in stmt_lower:
                    raise ReceptionConfidenceNotUpgradeFirewallError(
                        f"Reception claim '{clm.claim_id}': High confidence cannot upgrade reception into T4 theological truth."
                    )
                raise ReceptionTheologicalTruthFirewallError(
                    f"Reception claim '{clm.claim_id}' illicitly equates reception history with absolute theological truth."
                )
            # Firewall 6: Modern scholarly consensus != textual evidence
            if "scholarly consensus" in stmt_lower and clm.claim_tier in (ClaimTier.T1_LINGUISTIC_FACT.value, ClaimTier.T0_RAW_OBSERVATION.value):
                raise ReceptionScholarlyNotTextualFirewallError(
                    f"Reception claim '{clm.claim_id}': Modern scholarly consensus cannot masquerade as primary textual evidence."
                )

            # Firewall 18: Majority interpretation != verified fact
            if "majority" in stmt_lower and clm.claim_tier in (ClaimTier.T1_LINGUISTIC_FACT.value, ClaimTier.T0_RAW_OBSERVATION.value):
                raise ReceptionMajorityNotFactFirewallError(
                    f"Reception claim '{clm.claim_id}': Majority reception cannot be asserted as verified fact."
                )

            # Firewall 9: Citation != interpretation
            if "citation equals interpretation" in stmt_lower:
                raise ReceptionCitationNotInterpretationFirewallError(
                    f"Reception claim '{clm.claim_id}': Mere citation does not establish interpretive agreement."
                )

            # Firewall 10: Allusion != quotation
            if "allusion is quotation" in stmt_lower:
                raise ReceptionAllusionNotQuotationFirewallError(
                    f"Reception claim '{clm.claim_id}': Allusion cannot be asserted as direct quotation without textual formula."
                )

            # Firewall 15: Reception source != authorial source
            if "reception source is authorial" in stmt_lower:
                raise ReceptionSourceNotAuthorialSourceFirewallError(
                    f"Reception claim '{clm.claim_id}': Reception source cannot be asserted as authorial source."
                )

            # Firewall 16: Reception history != canonical authority
            if "canonical authority" in stmt_lower and clm.claim_tier == ClaimTier.T4_THEOLOGICAL_CLAIM.value:
                raise ReceptionNotCanonicalAuthorityFirewallError(
                    f"Reception claim '{clm.claim_id}': Reception history cannot be endowed with canonical authority."
                )

            # Firewall 12: Lexical similarity != reception
            if "lexical parallel alone" in stmt_lower and clm.claim_tier == ClaimTier.T2_CONTEXTUAL_CLAIM.value:
                raise ReceptionLexicalNotReceptionFirewallError(
                    f"Reception claim '{clm.claim_id}': Lexical similarity alone does not establish reception history."
                )

            # Firewall 13: Thematic parallel != reception
            if "thematic parallel alone" in stmt_lower and clm.claim_tier == ClaimTier.T2_CONTEXTUAL_CLAIM.value:
                raise ReceptionThematicNotReceptionFirewallError(
                    f"Reception claim '{clm.claim_id}': Thematic parallel alone does not establish reception history."
                )

            # Firewall 3 & 4 & 5 & 14: Doctrinal development or hermeneutical reading cannot directly become T1 linguistic fact
            if clm.claim_tier == ClaimTier.T1_LINGUISTIC_FACT.value:
                if clm.claim_type in (
                    ReceptionClaimType.HERMENEUTICAL_READING.value,
                    ReceptionClaimType.DOCTRINAL_DEVELOPMENT.value,
                    ReceptionClaimType.TRADITION_CONTINUITY.value,
                ):
                    raise ReceptionDoctrinalNotTextualReadingFirewallError(
                        f"Reception claim '{clm.claim_id}' cannot assert T1 linguistic fact from {clm.claim_type}."
                    )

            # Firewall 23: Temporal direction cannot be unestablished
            if not clm.temporal_direction:
                raise ReceptionTemporalDirectionFirewallError(
                    f"Reception claim '{clm.claim_id}' must specify temporal direction."
                )

        # Validate Records
        for rec in records:
            # Firewall 11: Translation mediation must declare translation language
            if rec.is_translation_mediated and not rec.translation_language:
                raise ReceptionTranslationNotOriginalFirewallError(
                    f"Reception record '{rec.record_id}' is translation-mediated but lacks translation_language."
                )

        # Validate Relations
        for rel in relations:
            # Self-relation forbidden
            if rel.source_record_id == rel.target_record_id:
                raise ReceptionValidationError(
                    f"Reception relation '{rel.relation_id}' cannot connect a record to itself."
                )

            # Firewall 8: Chronology != influence
            if rel.is_influence_asserted and not rel.chronological_order_verified:
                raise ReceptionChronologyNotInfluenceFirewallError(
                    f"Reception relation '{rel.relation_id}' asserts causal influence without verified chronological sequence."
                )

            # Firewall 24: Counter-evidence preservation
            if not rel.counter_evidence_preserved:
                raise ReceptionCounterEvidencePreservationFirewallError(
                    f"Reception relation '{rel.relation_id}' attempts to suppress counter-evidence."
                )

        # Validate Evidence Links
        for lnk in evidence_links:
            # Firewall 19: AI-generated summary != primary source
            if lnk.is_ai_generated:
                raise ReceptionAISummaryNotPrimarySourceFirewallError(
                    f"Evidence link '{lnk.link_id}' contains AI-generated content which cannot serve as primary reception evidence."
                )

            if lnk.is_synthetic_evaluation:
                raise ReceptionAISummaryNotPrimarySourceFirewallError(
                    f"Evidence link '{lnk.link_id}' is a synthetic evaluation which cannot serve as primary reception evidence."
                )

            # Evidence class validation
            if lnk.evidence_class not in (EvidenceClass.E11_EARLY_RECEPTION.value, EvidenceClass.E12_LATER_INTERPRETATION.value):
                raise ReceptionHistorySubsystemError(
                    f"Evidence link '{lnk.link_id}' specifies invalid reception evidence class: {lnk.evidence_class}"
                )

    # -------------------------------------------------------------------------
    # RETRIEVAL AND QUERY METHODS
    # -------------------------------------------------------------------------
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run details by ID."""
        with self.engine.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM reception_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def get_records_for_passage(self, passage_id: str) -> List[Dict[str, Any]]:
        """Retrieve all active reception records for a passage."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                """
                SELECT r.* FROM reception_records r
                JOIN reception_runs run ON r.run_id = run.run_id
                WHERE r.target_passage_id = ? AND run.status = 'COMPLETED'
                ORDER BY r.created_at ASC;
                """,
                (passage_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_claims_for_record(self, record_id: str) -> List[Dict[str, Any]]:
        """Retrieve all reception claims linked to a reception record."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM reception_claims WHERE record_id = ? ORDER BY created_at ASC;",
                (record_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_relations_for_record(self, record_id: str) -> List[Dict[str, Any]]:
        """Retrieve all cross-record relations involving a record."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                """
                SELECT * FROM reception_relations
                WHERE source_record_id = ? OR target_record_id = ?
                ORDER BY created_at ASC;
                """,
                (record_id, record_id),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_actor(self, actor_id: str) -> Dict[str, Any]:
        """Retrieve an actor by ID, raising ReceptionActorNotFoundError if missing."""
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM reception_actors WHERE actor_id = ?", (actor_id,)).fetchone()
            if not row:
                raise ReceptionActorNotFoundError(f"Reception actor '{actor_id}' not found.")
            return dict(row)

    def get_source(self, source_id: str) -> Dict[str, Any]:
        """Retrieve a reception source by ID, raising ReceptionSourceNotFoundError if missing."""
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM reception_sources WHERE source_id = ?", (source_id,)).fetchone()
            if not row:
                raise ReceptionSourceNotFoundError(f"Reception source '{source_id}' not found.")
            return dict(row)

    def get_record(self, record_id: str) -> Dict[str, Any]:
        """Retrieve a reception record by ID, raising ReceptionRecordNotFoundError if missing."""
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM reception_records WHERE record_id = ?", (record_id,)).fetchone()
            if not row:
                raise ReceptionRecordNotFoundError(f"Reception record '{record_id}' not found.")
            return dict(row)

    def get_claim(self, claim_id: str) -> Dict[str, Any]:
        """Retrieve a reception claim by ID, raising ReceptionClaimNotFoundError if missing."""
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM reception_claims WHERE claim_id = ?", (claim_id,)).fetchone()
            if not row:
                raise ReceptionClaimNotFoundError(f"Reception claim '{claim_id}' not found.")
            return dict(row)

    def get_relation(self, relation_id: str) -> Dict[str, Any]:
        """Retrieve a reception relation by ID, raising ReceptionRelationNotFoundError if missing."""
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM reception_relations WHERE relation_id = ?", (relation_id,)).fetchone()
            if not row:
                raise ReceptionRelationNotFoundError(f"Reception relation '{relation_id}' not found.")
            return dict(row)

