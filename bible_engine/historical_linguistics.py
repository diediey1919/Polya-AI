"""
Polya Philological Bible Engine - Historical-Linguistic & Diachronic Engine (Task 3.2).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principles:
  HISTORICAL/LINGUISTIC PARALLEL != INTERTEXTUAL DEPENDENCE
  LEXICAL SIMILARITY != BORROWING
  BORROWING != THEOLOGICAL INFLUENCE
  CHRONOLOGICAL PROXIMITY != CAUSATION
  SHARED ROOT != SAME HISTORICAL SOURCE
  LATER LINGUISTIC FORM != AUTOMATIC EARLIER READING
  MODERN LINGUISTIC TERMINOLOGY != ANCIENT AUTHORIAL INTENT
  AI-GENERATED ETYMOLOGY != PRIMARY EVIDENCE
  TRANSLATION != HISTORICAL-LINGUISTIC SOURCE EVIDENCE
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
    AIHistoricalEvidenceFirewallError,
    BorrowingEvidenceRequiredFirewallError,
    ChronologicalProximityNotCausationFirewallError,
    HistoricalLinguisticConcurrencyError,
    HistoricalLinguisticImmutabilityError,
    HistoricalLinguisticInvalidProvenanceError,
    HistoricalLinguisticInvalidVersionError,
    HistoricalLinguisticSubsystemError,
    HistoricalObservationNotFoundError,
    LaterFormEarlierReadingFirewallError,
    LexicalSimilarityNotBorrowingFirewallError,
    LexicalSimilarityNotCausationFirewallError,
    ModernTerminologyAuthorialIntentFirewallError,
    ParallelNotIntertextualFirewallError,
    SharedRootNotSameSourceFirewallError,
    StratumNotFoundError,
    TranslationHistoricalSourceFirewallError,
)
from bible_engine.evidence_claim import (
    ClaimDefinition,
    ClaimEvidenceLinkDefinition,
    ClaimTier,
    ConfidenceLevel,
    EpistemicStatus,
    EpistemicType,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceDefinition,
    EvidenceRelationship,
    EvidenceStatus,
)
from bible_engine.provenance import (
    ProvenanceRecord,
    ProvenanceTracker,
    TargetType,
    compute_canonical_hash,
)
from bible_engine.versioning import (
    ChangeReason,
    ObjectVersion,
    VersionManager,
    VersionStatus,
)


# =============================================================================
# TAXONOMIES & CONTROLLED VOCABULARIES
# =============================================================================

class LanguageCode(str, Enum):
    """Controlled primary ancient languages."""
    GREEK = "GREEK"
    HEBREW = "HEBREW"
    ARAMAIC = "ARAMAIC"


class GreekPeriod(str, Enum):
    """Controlled historical-linguistic strata for Greek."""
    CLASSICAL = "CLASSICAL"
    HELLENISTIC_KOINE = "HELLENISTIC_KOINE"
    EARLY_ROMAN = "EARLY_ROMAN"
    IMPERIAL = "IMPERIAL"
    LATE_ANTIQUE = "LATE_ANTIQUE"
    UNKNOWN = "UNKNOWN"


class HebrewPeriod(str, Enum):
    """Controlled historical-linguistic strata for Hebrew."""
    ARCHAIC = "ARCHAIC"
    CLASSICAL_BIBLICAL = "CLASSICAL_BIBLICAL"
    LATE_BIBLICAL = "LATE_BIBLICAL"
    SECOND_TEMPLE = "SECOND_TEMPLE"
    QUMRAN = "QUMRAN"
    POST_BIBLICAL = "POST_BIBLICAL"
    UNKNOWN = "UNKNOWN"


class AramaicPeriod(str, Enum):
    """Controlled historical-linguistic strata for Aramaic."""
    OLD_ARAMAIC = "OLD_ARAMAIC"
    OFFICIAL_IMPERIAL = "OFFICIAL_IMPERIAL"
    BIBLICAL_ARAMAIC = "BIBLICAL_ARAMAIC"
    MIDDLE_ARAMAIC = "MIDDLE_ARAMAIC"
    LATE_ARAMAIC = "LATE_ARAMAIC"
    UNKNOWN = "UNKNOWN"


class BorrowingState(str, Enum):
    """Epistemic states for loanword borrowing hypotheses."""
    PROPOSED = "PROPOSED"
    POSSIBLE = "POSSIBLE"
    PROBABLE = "PROBABLE"
    ESTABLISHED = "ESTABLISHED"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class BorrowingType(str, Enum):
    """Classifications of lexical borrowing."""
    DIRECT_LOAN = "DIRECT_LOAN"
    CALQUE_LOAN_TRANSLATION = "CALQUE_LOAN_TRANSLATION"
    SEMANTIC_LOAN = "SEMANTIC_LOAN"
    MORPHOLOGICAL_ADAPTATION = "MORPHOLOGICAL_ADAPTATION"
    PHONOLOGICAL_BORROWING = "PHONOLOGICAL_BORROWING"
    UNVERIFIED = "UNVERIFIED"


class EtymologicalRelationshipType(str, Enum):
    """Types of etymological connections."""
    COGNATE = "COGNATE"
    DIRECT_DERIVATION = "DIRECT_DERIVATION"
    SHARED_ROOT = "SHARED_ROOT"
    BORROWING = "BORROWING"
    CALQUE = "CALQUE"
    INDEPENDENT_PARALLEL = "INDEPENDENT_PARALLEL"
    FOLK_ETYMOLOGY = "FOLK_ETYMOLOGY"
    SPURIOUS_SIMILARITY = "SPURIOUS_SIMILARITY"
    UNKNOWN = "UNKNOWN"


class ParallelCorpusType(str, Enum):
    """Controlled corpora for external parallel evidence."""
    EPIGRAPHIC_INSCRIPTION = "EPIGRAPHIC_INSCRIPTION"
    DOCUMENTARY_PAPYRUS = "DOCUMENTARY_PAPYRUS"
    OSTRACON = "OSTRACON"
    COIN_LEGEND = "COIN_LEGEND"
    CLASSICAL_LITERATURE = "CLASSICAL_LITERATURE"
    RABBINIC_CORPUS = "RABBINIC_CORPUS"
    DEAD_SEA_SCROLL = "DEAD_SEA_SCROLL"
    TARGUM = "TARGUM"
    SEPTUAGINT_PAPYRUS = "SEPTUAGINT_PAPYRUS"


class ObservationScope(str, Enum):
    """Scope of historical-linguistic observation."""
    TOKEN = "TOKEN"
    LEXEME = "LEXEME"
    SYNTACTIC_CONSTRUCTION = "SYNTACTIC_CONSTRUCTION"
    PASSAGE = "PASSAGE"
    PERICOPE = "PERICOPE"


class EvidenceScope(str, Enum):
    """Strict separation of internal linguistic vs external historical evidence."""
    INTERNAL_LINGUISTIC = "INTERNAL_LINGUISTIC"
    EXTERNAL_HISTORICAL = "EXTERNAL_HISTORICAL"


class IdentifierVerificationStatus(str, Enum):
    """Scholarly verification status of external identifiers."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"


# =============================================================================
# DATA DEFINITIONS & TRANSFER OBJECTS
# =============================================================================

@dataclass(frozen=True)
class DiachronicStratumDefinition:
    """Definition of a historical-linguistic period stratum."""
    stratum_id: str
    language: str
    period_code: str
    period_name: str
    approximate_start_bce_ce: Optional[int]
    approximate_end_bce_ce: Optional[int]
    description: str
    is_controlled: bool = True


@dataclass(frozen=True)
class DiachronicAnnotationDefinition:
    """Token or lexeme diachronic classification annotation."""
    annotation_id: str
    stratum_id: str
    classification_confidence: str  # CERTAIN, HIGH, PROVISIONAL, DISPUTED, UNCERTAIN
    linguistic_features: str
    token_id: Optional[str] = None
    lemma_id: Optional[str] = None
    is_period_uncertain: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class LoanwordDefinition:
    """Loanword / borrowing registry entry."""
    loanword_id: str
    source_language: str
    target_language: str
    lexeme: str
    candidate_etymon: str
    borrowing_type: str
    chronological_range: str
    external_reference: str
    state: str
    confidence: str
    confidence_score: float
    evidence_id: str
    provenance_id: Optional[str] = None
    lemma_id: Optional[str] = None
    external_identifier_status: str = "UNVERIFIED"
    is_ai_generated: bool = False
    is_translation_derived: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class EtymologicalRelationDefinition:
    """Etymological relationship record between forms."""
    relation_id: str
    lexeme_text: str
    target_language: str
    related_lexeme_text: str
    source_language: str
    relationship_type: str
    state: str
    reconstruction_method: str
    lexicon_source: str
    evidence_id: str
    is_causal_relation: bool = False
    is_same_historical_source: bool = False
    lexeme_id: Optional[str] = None
    provenance_id: Optional[str] = None
    is_ai_generated: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class EpigraphicParallelDefinition:
    """Independent epigraphic or papyrological parallel record."""
    parallel_id: str
    parallel_corpus: str
    artifact_siglum: str
    dating_period: str
    parallel_text: str
    linguistic_significance: str
    external_identifier: str
    evidence_id: str
    token_id: Optional[str] = None
    passage_id: Optional[str] = None
    geographic_provenance: Optional[str] = None
    external_identifier_status: str = "UNVERIFIED"
    is_intertextual_dependence: bool = False
    evidence_class: str = "E9_HISTORICAL_LINGUISTIC"
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class HistoricalObservationDefinition:
    """Historical-linguistic observation record."""
    observation_id: str
    passage_id: str
    observation_scope: str
    evidence_scope: str
    observation_title: str
    observation_text: str
    evidence_id: str
    chronological_proximity_noted: Optional[str] = None
    asserts_historical_causation: bool = False
    asserts_theological_influence: bool = False
    modern_terminology_imposed: bool = False
    claim_id: Optional[str] = None
    provenance_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class HistoricalLinguisticRunResult:
    """Result of an executed historical-linguistic analysis run."""
    run_id: str
    version_id: str
    provenance_id: str
    strata_count: int
    annotations_count: int
    loanwords_count: int
    etymologies_count: int
    parallels_count: int
    observations_count: int
    evidence_count: int
    output_hash: str
    created_at: str


# =============================================================================
# HISTORICAL-LINGUISTIC MANAGER
# =============================================================================

class HistoricalLinguisticManager:
    """
    Subsystem manager for Historical-Linguistic & Diachronic Analysis.
    Enforces all epistemic firewalls, immutability, provenance, and versioning.
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
    # STRATA MANAGEMENT
    # -------------------------------------------------------------------------

    def register_stratum(self, stratum: DiachronicStratumDefinition) -> None:
        """Register a controlled diachronic stratum."""
        lang_val = stratum.language.upper()
        if lang_val not in ("GREEK", "HEBREW", "ARAMAIC"):
            raise HistoricalLinguisticSubsystemError(
                f"Unsupported language '{stratum.language}'. Must be GREEK, HEBREW, or ARAMAIC."
            )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO diachronic_strata (
                    stratum_id, language, period_code, period_name,
                    approximate_start_bce_ce, approximate_end_bce_ce,
                    description, is_controlled, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    stratum.stratum_id,
                    lang_val,
                    stratum.period_code.upper(),
                    stratum.period_name,
                    stratum.approximate_start_bce_ce,
                    stratum.approximate_end_bce_ce,
                    stratum.description,
                    1 if stratum.is_controlled else 0,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def seed_canonical_strata(self) -> None:
        """Populate standard controlled strata for Greek, Hebrew, and Aramaic."""
        greek_strata = [
            ("STRAT-GRC-CLASSICAL", "GREEK", "CLASSICAL", "Classical Greek", -800, -323, "Homeric, Archaic, and Classical Attic/Ionic Greek"),
            ("STRAT-GRC-KOINE", "GREEK", "HELLENISTIC_KOINE", "Hellenistic Koine", -323, 30, "Post-Alexandrian Hellenistic Common Greek (LXX, Polybius)"),
            ("STRAT-GRC-EARLY-ROMAN", "GREEK", "EARLY_ROMAN", "Early Roman Koine", 30, 150, "First-century CE Roman period Koine (New Testament, Josephus, Philo)"),
            ("STRAT-GRC-IMPERIAL", "GREEK", "IMPERIAL", "Imperial Greek", 150, 330, "High Imperial Greek, Second Sophistic, Early Patristics"),
            ("STRAT-GRC-LATE-ANTIQUE", "GREEK", "LATE_ANTIQUE", "Late Antique Greek", 330, 600, "Byzantine and Late Antique ecclesiastical Greek"),
            ("STRAT-GRC-UNKNOWN", "GREEK", "UNKNOWN", "Uncertain Greek Period", None, None, "Uncertain or disputed Greek diachronic stratum"),
        ]

        hebrew_strata = [
            ("STRAT-HEB-ARCHAIC", "HEBREW", "ARCHAIC", "Archaic Biblical Hebrew", -1200, -1000, "Earliest biblical poetry (Song of Deborah, Blessing of Jacob)"),
            ("STRAT-HEB-CBH", "HEBREW", "CLASSICAL_BIBLICAL", "Classical Biblical Hebrew", -1000, -586, "Standard pre-exilic First Temple prose and prophetic poetry"),
            ("STRAT-HEB-LBH", "HEBREW", "LATE_BIBLICAL", "Late Biblical Hebrew", -586, -332, "Post-exilic biblical texts (Chronicles, Ezra, Nehemiah, Daniel)"),
            ("STRAT-HEB-SECOND-TEMPLE", "HEBREW", "SECOND_TEMPLE", "Second Temple Hebrew", -332, 70, "Hellenistic and Roman era Jewish literature"),
            ("STRAT-HEB-QUMRAN", "HEBREW", "QUMRAN", "Qumran / Dead Sea Hebrew", -250, 68, "Sectarian and non-biblical manuscripts from the Dead Sea Caves"),
            ("STRAT-HEB-POST-BIBLICAL", "HEBREW", "POST_BIBLICAL", "Post-Biblical / Mishnaic Hebrew", 70, 200, "Tannaitic rabbinic Hebrew (Mishnah, Tosefta)"),
            ("STRAT-HEB-UNKNOWN", "HEBREW", "UNKNOWN", "Uncertain Hebrew Period", None, None, "Uncertain or disputed Hebrew diachronic stratum"),
        ]

        aramaic_strata = [
            ("STRAT-ARM-OLD", "ARAMAIC", "OLD_ARAMAIC", "Old Aramaic", -1000, -700, "Early ancient inscriptions (Tel Dan, Zakkur, Sefire)"),
            ("STRAT-ARM-OFFICIAL", "ARAMAIC", "OFFICIAL_IMPERIAL", "Imperial / Official Aramaic", -700, -200, "Achaemenid Empire lingua franca, Elephantine papyri"),
            ("STRAT-ARM-BIBLICAL", "ARAMAIC", "BIBLICAL_ARAMAIC", "Biblical Aramaic", -600, -165, "Portions of Ezra and Daniel"),
            ("STRAT-ARM-MIDDLE", "ARAMAIC", "MIDDLE_ARAMAIC", "Middle Aramaic", -200, 200, "Qumran Aramaic, Palmyrene, Nabataean, early Targumic"),
            ("STRAT-ARM-LATE", "ARAMAIC", "LATE_ARAMAIC", "Late Aramaic", 200, 700, "Syriac, Jewish Babylonian Aramaic, Christian Palestinian Aramaic"),
            ("STRAT-ARM-UNKNOWN", "ARAMAIC", "UNKNOWN", "Uncertain Aramaic Period", None, None, "Uncertain or disputed Aramaic diachronic stratum"),
        ]

        for s_id, lang, p_code, p_name, start_yr, end_yr, desc in greek_strata + hebrew_strata + aramaic_strata:
            self.register_stratum(
                DiachronicStratumDefinition(
                    stratum_id=s_id,
                    language=lang,
                    period_code=p_code,
                    period_name=p_name,
                    approximate_start_bce_ce=start_yr,
                    approximate_end_bce_ce=end_yr,
                    description=desc,
                )
            )

    # -------------------------------------------------------------------------
    # EPISTEMIC FIREWALL ENFORCEMENT
    # -------------------------------------------------------------------------

    def validate_historical_firewalls(
        self,
        annotations: Sequence[DiachronicAnnotationDefinition] = (),
        loanwords: Sequence[LoanwordDefinition] = (),
        etymologies: Sequence[EtymologicalRelationDefinition] = (),
        parallels: Sequence[EpigraphicParallelDefinition] = (),
        observations: Sequence[HistoricalObservationDefinition] = (),
    ) -> None:
        """
        Enforce all required historical-linguistic firewalls:
        - Lexical similarity != borrowing
        - Lexical similarity != historical causation
        - Chronological proximity != causation
        - Shared root != same historical source
        - Later linguistic form != automatic earlier reading
        - Modern linguistic terminology != ancient authorial intent
        - AI-generated etymology != primary evidence
        - Translation != historical-linguistic source evidence
        - Parallel != intertextual dependence
        - Borrowing requires evidence
        """
        # 1. Loanword & Borrowing Firewalls
        for lw in loanwords:
            # Firewall: AI output cannot become primary historical evidence
            if lw.is_ai_generated:
                raise AIHistoricalEvidenceFirewallError(
                    f"Loanword '{lw.loanword_id}': AI-generated etymology cannot become primary historical evidence."
                )

            # Firewall: Translation cannot become historical-linguistic source evidence
            if lw.is_translation_derived:
                raise TranslationHistoricalSourceFirewallError(
                    f"Loanword '{lw.loanword_id}': Translation output cannot become historical-linguistic source evidence."
                )

            # Firewall: Borrowing requires evidence
            if not lw.evidence_id or not lw.evidence_id.strip():
                raise BorrowingEvidenceRequiredFirewallError(
                    f"Loanword '{lw.loanword_id}': Borrowing cannot be registered without supporting evidence."
                )

            # Firewall: Lexical similarity != borrowing (Merely resembling each other is not borrowing)
            if lw.borrowing_type.upper() == "UNVERIFIED" and lw.state.upper() == BorrowingState.ESTABLISHED.value:
                raise LexicalSimilarityNotBorrowingFirewallError(
                    f"Loanword '{lw.loanword_id}': Cannot assert borrowing as ESTABLISHED merely because two forms resemble each other."
                )

        # 2. Etymological Relation Firewalls
        for ety in etymologies:
            if ety.is_ai_generated:
                raise AIHistoricalEvidenceFirewallError(
                    f"Etymology '{ety.relation_id}': AI-generated etymology cannot become primary historical evidence."
                )

            rel_type = ety.relationship_type.upper()
            ety_state = ety.state.upper()

            # Firewall: Shared root != same historical source
            if rel_type == EtymologicalRelationshipType.SHARED_ROOT.value and ety.is_same_historical_source:
                raise SharedRootNotSameSourceFirewallError(
                    f"Etymology '{ety.relation_id}': Shared root cannot be asserted to demonstrate the same historical source."
                )

            # Firewall: Lexical similarity != borrowing / causation
            if rel_type in (EtymologicalRelationshipType.SPURIOUS_SIMILARITY.value, EtymologicalRelationshipType.FOLK_ETYMOLOGY.value):
                if ety.is_causal_relation:
                    raise LexicalSimilarityNotCausationFirewallError(
                        f"Etymology '{ety.relation_id}': Superficial lexical similarity cannot be asserted as causal relation."
                    )
                if ety_state == BorrowingState.ESTABLISHED.value:
                    raise LexicalSimilarityNotBorrowingFirewallError(
                        f"Etymology '{ety.relation_id}': Superficial similarity cannot be established as valid borrowing."
                    )

        # 3. Epigraphic / Papyrological Parallels Firewalls
        for p in parallels:
            # Firewall: Parallel != intertextuality (A parallel must not automatically become E10 intertextual evidence)
            if p.is_intertextual_dependence:
                raise ParallelNotIntertextualFirewallError(
                    f"Parallel '{p.parallel_id}': A historical-linguistic parallel must NOT automatically become E10 INTERTEXTUAL evidence."
                )
            if p.evidence_class.upper() != EvidenceClass.E9_HISTORICAL_LINGUISTIC.value:
                raise ParallelNotIntertextualFirewallError(
                    f"Parallel '{p.parallel_id}': Must remain E9_HISTORICAL_LINGUISTIC evidence, got '{p.evidence_class}'."
                )

        # 4. Historical Observations Firewalls
        for obs in observations:
            # Firewall: Chronological proximity != causation & Lexical similarity != historical causation
            if obs.asserts_historical_causation:
                if obs.chronological_proximity_noted:
                    raise ChronologicalProximityNotCausationFirewallError(
                        f"Observation '{obs.observation_id}': Chronological proximity must NOT be asserted as historical causation."
                    )
                else:
                    raise LexicalSimilarityNotCausationFirewallError(
                        f"Observation '{obs.observation_id}': Historical-linguistic observation cannot assert historical causation."
                    )

            # Firewall: Borrowing != theological influence
            if obs.asserts_theological_influence:
                raise LexicalSimilarityNotCausationFirewallError(
                    f"Observation '{obs.observation_id}': Linguistic borrowing does NOT equal theological influence."
                )

            # Firewall: Modern linguistic terminology != ancient authorial intent
            if obs.modern_terminology_imposed:
                raise ModernTerminologyAuthorialIntentFirewallError(
                    f"Observation '{obs.observation_id}': Modern linguistic terminology must not be retrofitted as ancient authorial intent."
                )

        # 5. Diachronic Annotation Firewalls
        for ann in annotations:
            # Check for later form earlier reading dogmatic assertions
            feat_lower = ann.linguistic_features.lower()
            if "later form implies earlier reading" in feat_lower or "late form proves early text" in feat_lower:
                raise LaterFormEarlierReadingFirewallError(
                    f"Annotation '{ann.annotation_id}': Later linguistic form cannot be treated as automatic earlier reading."
                )

    # -------------------------------------------------------------------------
    # ATOMIC ANALYSIS EXECUTION RUN
    # -------------------------------------------------------------------------

    def execute_analysis_run(
        self,
        run_id: str,
        passage_id: str,
        analyzer_id: str,
        analyzer_version: str,
        source_text_id: Optional[str] = None,
        pericope_id: Optional[str] = None,
        token_start_id: Optional[str] = None,
        token_end_id: Optional[str] = None,
        annotations: Sequence[DiachronicAnnotationDefinition] = (),
        loanwords: Sequence[LoanwordDefinition] = (),
        etymologies: Sequence[EtymologicalRelationDefinition] = (),
        parallels: Sequence[EpigraphicParallelDefinition] = (),
        observations: Sequence[HistoricalObservationDefinition] = (),
        created_at: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> HistoricalLinguisticRunResult:
        """
        Execute an immutable historical-linguistic analysis run.
        Integrates with VersionManager, ProvenanceTracker, and EvidenceClaimManager.
        Supports rollback on error and version supersession on reanalysis.
        """
        timestamp = created_at or datetime.now(timezone.utc).isoformat()

        # 1. Enforce Firewalls
        self.validate_historical_firewalls(
            annotations=annotations,
            loanwords=loanwords,
            etymologies=etymologies,
            parallels=parallels,
            observations=observations,
        )

        # 2. Compute Hashes
        config_dict = {
            "analyzer_id": analyzer_id,
            "analyzer_version": analyzer_version,
            "passage_id": passage_id,
            "pericope_id": pericope_id,
        }
        config_hash = compute_canonical_hash(config_dict)

        input_dict = {
            "passage_id": passage_id,
            "source_text_id": source_text_id,
            "token_start_id": token_start_id,
            "token_end_id": token_end_id,
            "annotations_len": len(annotations),
            "loanwords_len": len(loanwords),
            "etymologies_len": len(etymologies),
            "parallels_len": len(parallels),
            "observations_len": len(observations),
        }
        input_content_hash = compute_canonical_hash(input_dict)

        output_dict = {
            "run_id": run_id,
            "annotations": [asdict(a) for a in annotations],
            "loanwords": [asdict(lw) for lw in loanwords],
            "etymologies": [asdict(e) for e in etymologies],
            "parallels": [asdict(p) for p in parallels],
            "observations": [asdict(o) for o in observations],
        }
        output_hash = compute_canonical_hash(output_dict)

        # 3. Provenance and Versioning Lifecycle
        prov_id = f"PROV-HL-{run_id}"
        version_id = f"VER-HL-{run_id}"

        # Supersede any prior run on this passage
        with self.engine.transaction() as conn:
            # Check for existing run
            existing_runs = conn.execute(
                "SELECT run_id, version_id FROM historical_linguistic_runs WHERE passage_id = ? AND status = 'COMPLETED'",
                (passage_id,),
            ).fetchall()

            for old_run_id, old_ver_id in existing_runs:
                conn.execute(
                    "UPDATE historical_linguistic_runs SET status = 'SUPERSEDED' WHERE run_id = ?",
                    (old_run_id,),
                )
                if old_ver_id:
                    self.version_manager.supersede_version(
                        version_id=old_ver_id,
                        conn=conn,
                    )

            # Record Provenance for Run
            provenance_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=run_id,
                content=f"HISTORICAL_LINGUISTIC_RUN:{run_id}:{output_hash}",
                input_data=input_content_hash,
                agent_id=analyzer_id,
                agent_version=analyzer_version,
                conn=conn,
            )
            prov_id = provenance_rec.provenance_id

            # Record Version
            version_rec = self.version_manager.create_version(
                object_type="HISTORICAL_LINGUISTIC_RUN",
                object_id=run_id,
                content_hash=output_hash,
                change_reason=ChangeReason.INITIAL_CREATION,
                created_by=analyzer_id,
                provenance_id=prov_id,
                version_id=version_id,
                conn=conn,
            )
            version_id = version_rec.version_id

            # 4. Insert Run Record
            conn.execute(
                """
                INSERT INTO historical_linguistic_runs (
                    run_id, source_text_id, passage_id, pericope_id,
                    token_start_id, token_end_id, version_id, provenance_id,
                    analyzer_id, analyzer_version, configuration_hash,
                    input_content_hash, output_hash, status, is_exact_reproducible,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?)
                """,
                (
                    run_id,
                    source_text_id,
                    passage_id,
                    pericope_id,
                    token_start_id,
                    token_end_id,
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

            # 5. Insert Diachronic Annotations
            for ann in annotations:
                ann_prov_id = f"PROV-ANN-{ann.annotation_id}"
                conn.execute(
                    """
                    INSERT INTO diachronic_annotations (
                        annotation_id, run_id, token_id, lemma_id, stratum_id,
                        classification_confidence, is_period_uncertain,
                        linguistic_features, notes, evidence_id, provenance_id,
                        created_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        ann.annotation_id,
                        run_id,
                        ann.token_id,
                        ann.lemma_id,
                        ann.stratum_id,
                        ann.classification_confidence.upper(),
                        1 if ann.is_period_uncertain else 0,
                        ann.linguistic_features,
                        ann.notes,
                        None,
                        prov_id,
                        timestamp,
                    ),
                )

            # 6. Insert Loanwords
            for lw in loanwords:
                lw_prov_id = lw.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO loanword_registry (
                        loanword_id, run_id, source_language, target_language,
                        lexeme, lemma_id, candidate_etymon, borrowing_type,
                        chronological_range, external_reference, external_identifier_status,
                        state, confidence, confidence_score, evidence_id, provenance_id,
                        is_ai_generated, is_translation_derived, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        lw.loanword_id,
                        run_id,
                        lw.source_language.upper(),
                        lw.target_language.upper(),
                        lw.lexeme,
                        lw.lemma_id,
                        lw.candidate_etymon,
                        lw.borrowing_type.upper(),
                        lw.chronological_range,
                        lw.external_reference,
                        lw.external_identifier_status.upper(),
                        lw.state.upper(),
                        lw.confidence.upper(),
                        lw.confidence_score,
                        lw.evidence_id,
                        lw_prov_id,
                        1 if lw.is_ai_generated else 0,
                        1 if lw.is_translation_derived else 0,
                        timestamp,
                        lw.notes,
                    ),
                )

            # 7. Insert Etymologies
            for ety in etymologies:
                ety_prov_id = ety.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO etymological_relations (
                        relation_id, run_id, lexeme_id, lexeme_text, target_language,
                        related_lexeme_text, source_language, relationship_type, state,
                        is_causal_relation, is_same_historical_source, reconstruction_method,
                        lexicon_source, evidence_id, provenance_id, is_ai_generated,
                        created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        ety.relation_id,
                        run_id,
                        ety.lexeme_id,
                        ety.lexeme_text,
                        ety.target_language.upper(),
                        ety.related_lexeme_text,
                        ety.source_language.upper(),
                        ety.relationship_type.upper(),
                        ety.state.upper(),
                        1 if ety.is_causal_relation else 0,
                        1 if ety.is_same_historical_source else 0,
                        ety.reconstruction_method,
                        ety.lexicon_source,
                        ety.evidence_id,
                        ety_prov_id,
                        1 if ety.is_ai_generated else 0,
                        timestamp,
                        ety.notes,
                    ),
                )

            # 8. Insert Epigraphic / Papyrological Parallels
            for p in parallels:
                p_prov_id = p.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO epigraphic_papyrological_parallels (
                        parallel_id, run_id, token_id, passage_id, parallel_corpus,
                        artifact_siglum, geographic_provenance, dating_period,
                        parallel_text, linguistic_significance, is_intertextual_dependence,
                        evidence_class, external_identifier, external_identifier_status,
                        evidence_id, provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        p.parallel_id,
                        run_id,
                        p.token_id,
                        p.passage_id or passage_id,
                        p.parallel_corpus.upper(),
                        p.artifact_siglum,
                        p.geographic_provenance,
                        p.dating_period,
                        p.parallel_text,
                        p.linguistic_significance,
                        1 if p.is_intertextual_dependence else 0,
                        p.evidence_class.upper(),
                        p.external_identifier,
                        p.external_identifier_status.upper(),
                        p.evidence_id,
                        p_prov_id,
                        timestamp,
                        p.notes,
                    ),
                )

            # 9. Insert Historical Observations
            for obs in observations:
                obs_prov_id = obs.provenance_id or prov_id
                conn.execute(
                    """
                    INSERT INTO historical_linguistic_observations (
                        observation_id, run_id, passage_id, observation_scope,
                        evidence_scope, observation_title, observation_text,
                        chronological_proximity_noted, asserts_historical_causation,
                        asserts_theological_influence, modern_terminology_imposed,
                        evidence_id, claim_id, provenance_id, created_at, is_immutable, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        obs.observation_id,
                        run_id,
                        obs.passage_id,
                        obs.observation_scope.upper(),
                        obs.evidence_scope.upper(),
                        obs.observation_title,
                        obs.observation_text,
                        obs.chronological_proximity_noted,
                        1 if obs.asserts_historical_causation else 0,
                        1 if obs.asserts_theological_influence else 0,
                        1 if obs.modern_terminology_imposed else 0,
                        obs.evidence_id,
                        obs.claim_id,
                        obs_prov_id,
                        timestamp,
                        obs.notes,
                    ),
                )

        return HistoricalLinguisticRunResult(
            run_id=run_id,
            version_id=version_id,
            provenance_id=prov_id,
            strata_count=len({a.stratum_id for a in annotations if a.stratum_id}),
            annotations_count=len(annotations),
            loanwords_count=len(loanwords),
            etymologies_count=len(etymologies),
            parallels_count=len(parallels),
            observations_count=len(observations),
            evidence_count=len(loanwords) + len(etymologies) + len(parallels) + len(observations),
            output_hash=output_hash,
            created_at=timestamp,
        )

    # -------------------------------------------------------------------------
    # RETRIEVAL & INSPECTION ACCESSORS
    # -------------------------------------------------------------------------

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve run summary by ID."""
        with self.engine.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM historical_linguistic_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def get_annotations_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve all diachronic annotations for a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM diachronic_annotations WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_loanwords_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve loanwords registered in a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM loanword_registry WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_etymologies_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve etymological relations registered in a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM etymological_relations WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_parallels_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve parallels registered in a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM epigraphic_papyrological_parallels WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_observations_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieve observations registered in a run."""
        with self.engine.transaction() as conn:
            rows = conn.execute(
                "SELECT * FROM historical_linguistic_observations WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            return [dict(r) for r in rows]
