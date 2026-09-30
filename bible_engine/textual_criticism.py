"""
Polya Philological Bible Engine - Textual Criticism Engine Subsystem (Task 3.1).
Specification: Architecture v2.0 — FROZEN.

Core Epistemic Principles:
  1. Evidence class is not a universal truth ranking.
  2. E11/E12 must never overwrite primary textual evidence (E1), but provide
     evidence of reception and interpretation history.
  3. Methodological criteria (lectio difficilior, lectio brevior, witness count,
     witness age, textual family) are analytical considerations, NOT automatic
     truth-selection formulas.
  4. PREFERRED reading is never automatically CERTAIN_ORIGINAL.
  5. All competing readings are preserved without suppression or deletion.
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
    AITextualEvidenceFirewallError,
    AutomaticPriorityCriterionFirewallError,
    ConfidenceTextualUpgradeFirewallError,
    LectioBreviorPriorityFirewallError,
    LectioDifficiliorPriorityFirewallError,
    ModernTranslationAsAttestationFirewallError,
    PreferredAsCertainOriginalFirewallError,
    SuppressionOfAlternativeReadingsFirewallError,
    TextualCriticismConcurrencyError,
    TextualCriticismImmutabilityError,
    TextualCriticismInvalidProvenanceError,
    TextualCriticismInvalidVersionError,
    TextualCriticismSubsystemError,
    TextualFamilyPriorityFirewallError,
    TranslationAsWitnessFirewallError,
    VariantReadingNotFoundError,
    VariantUnitNotFoundError,
    WitnessAgePriorityFirewallError,
    WitnessCountPriorityFirewallError,
    WitnessNotFoundError,
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
# TAXONOMIES & ENUMS
# =============================================================================

class TextualDecisionState(str, Enum):
    """Explicit epistemic states for a textual-critical assessment."""
    UNDECIDED = "UNDECIDED"
    PREFERRED = "PREFERRED"
    POSSIBLE = "POSSIBLE"
    UNCERTAIN = "UNCERTAIN"
    DISPUTED = "DISPUTED"
    REJECTED = "REJECTED"


class CriticalSignificance(str, Enum):
    """Significance level of the textual variation."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ORTHOGRAPHIC_ONLY = "ORTHOGRAPHIC_ONLY"


class EditorialStatus(str, Enum):
    """Editorial status assigned in the critical apparatus."""
    CERTAIN = "CERTAIN"
    PROBABLE = "PROBABLE"
    UNCERTAIN = "UNCERTAIN"
    DISPUTED = "DISPUTED"


class ReadingCategory(str, Enum):
    """Classification of the reading within the tradition."""
    ORIGINAL_PREFERRED = "ORIGINAL_PREFERRED"
    MAJORITY_READING = "MAJORITY_READING"
    EARLY_CORRECTION = "EARLY_CORRECTION"
    SCRIBAL_HARMONIZATION = "SCRIBAL_HARMONIZATION"
    ORTHOGRAPHIC_VARIANT = "ORTHOGRAPHIC_VARIANT"


class ReadingConfidence(str, Enum):
    """Confidence grade of a textual reading."""
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    AMBIGUOUS = "AMBIGUOUS"


class EvidenceType(str, Enum):
    """Strict separation of External and Internal Evidence."""
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"


class MethodologyCriterion(str, Enum):
    """Controlled vocabulary of textual-critical criteria."""
    # External Evidence criteria
    EXTERNAL_WITNESS_ATTESTATION = "EXTERNAL_WITNESS_ATTESTATION"
    EXTERNAL_WITNESS_DATE = "EXTERNAL_WITNESS_DATE"
    EXTERNAL_GEOGRAPHIC_DISTRIBUTION = "EXTERNAL_GEOGRAPHIC_DISTRIBUTION"
    EXTERNAL_TEXTUAL_FAMILY = "EXTERNAL_TEXTUAL_FAMILY"
    EXTERNAL_INDEPENDENT_STEMMA = "EXTERNAL_INDEPENDENT_STEMMA"

    # Internal Transcriptional Probability criteria
    TRANSCRIPTIONAL_LECTIO_DIFFICILIOR = "TRANSCRIPTIONAL_LECTIO_DIFFICILIOR"
    TRANSCRIPTIONAL_LECTIO_BREVIOR = "TRANSCRIPTIONAL_LECTIO_BREVIOR"
    TRANSCRIPTIONAL_HARMONIZATION_TENDENCY = "TRANSCRIPTIONAL_HARMONIZATION_TENDENCY"
    TRANSCRIPTIONAL_PALEOGRAPHIC_CONFUSION = "TRANSCRIPTIONAL_PALEOGRAPHIC_CONFUSION"
    TRANSCRIPTIONAL_HOMOIOTELEUTON = "TRANSCRIPTIONAL_HOMOIOTELEUTON"
    TRANSCRIPTIONAL_LITURGICAL_EXPANSION = "TRANSCRIPTIONAL_LITURGICAL_EXPANSION"
    TRANSCRIPTIONAL_DOCTRINAL_ALTERATION = "TRANSCRIPTIONAL_DOCTRINAL_ALTERATION"

    # Internal Intrinsic Probability criteria
    INTRINSIC_AUTHORIAL_STYLE = "INTRINSIC_AUTHORIAL_STYLE"
    INTRINSIC_AUTHORIAL_VOCABULARY = "INTRINSIC_AUTHORIAL_VOCABULARY"
    INTRINSIC_IMMEDIATE_CONTEXT = "INTRINSIC_IMMEDIATE_CONTEXT"
    INTRINSIC_THEMATIC_COHERENCE = "INTRINSIC_THEMATIC_COHERENCE"


class TextualFamily(str, Enum):
    """Recognized manuscript family or textual tradition."""
    ALEXANDRIAN = "ALEXANDRIAN"
    WESTERN = "WESTERN"
    CAESAREAN = "CAESAREAN"
    BYZANTINE = "BYZANTINE"
    PROTO_MASORETIC = "PROTO_MASORETIC"
    PRE_SAMARITAN = "PRE_SAMARITAN"
    MIXED = "MIXED"
    INDEPENDENT = "INDEPENDENT"


class WitnessType(str, Enum):
    """Physical and scholarly categorization of the witness."""
    PAPYRUS = "PAPYRUS"
    UNCIAL = "UNCIAL"
    MINUSCULE = "MINUSCULE"
    LECTIONARY = "LECTIONARY"
    DEAD_SEA_SCROLL = "DEAD_SEA_SCROLL"
    MASORETIC_CODEX = "MASORETIC_CODEX"
    INSCRIPTION = "INSCRIPTION"
    EARLY_TRANSLATION = "EARLY_TRANSLATION"


class IdentifierStatus(str, Enum):
    """Verification status of external catalog identifiers."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    DISPUTED = "DISPUTED"


# =============================================================================
# INPUT & DATA DEFINITIONS
# =============================================================================

@dataclass(frozen=True)
class WitnessDefinition:
    witness_id: str
    siglum: str
    name: str
    witness_type: WitnessType | str
    language: str
    century_origin: str
    dating_estimate_start: Optional[int] = None
    dating_estimate_end: Optional[int] = None
    repository: Optional[str] = None
    external_identifier: Optional[str] = None
    identifier_system: str = "UNVERIFIED"
    identifier_status: IdentifierStatus | str = IdentifierStatus.UNVERIFIED
    textual_family: Optional[TextualFamily | str] = None
    geographic_origin: Optional[str] = None
    is_translation: bool = False
    is_modern_translation: bool = False
    is_ai_synthetic: bool = False
    provenance_id: Optional[str] = None
    metadata_json: Optional[str] = None


@dataclass(frozen=True)
class VariantUnitDefinition:
    variant_unit_id: str
    passage_id: str
    word_position_start: int
    word_position_end: int
    base_text_reading: str
    critical_significance: CriticalSignificance | str = CriticalSignificance.MEDIUM
    editorial_status: EditorialStatus | str = EditorialStatus.PROBABLE
    notes: Optional[str] = None
    pericope_id: Optional[str] = None
    token_start_id: Optional[str] = None
    token_end_id: Optional[str] = None


@dataclass(frozen=True)
class VariantReadingDefinition:
    reading_id: str
    variant_unit_id: str
    reading_siglum: str
    greek_or_hebrew_string: str
    external_evidence_summary: str = ""
    internal_evidence_evaluation: str = ""
    reading_category: ReadingCategory | str = ReadingCategory.MAJORITY_READING
    reading_confidence: ReadingConfidence | str = ReadingConfidence.HIGH


@dataclass(frozen=True)
class WitnessAttestationDefinition:
    attestation_id: str
    reading_id: str
    witness_id: str
    folio_or_page: Optional[str] = None
    is_correction: bool = False
    transcription_text: Optional[str] = None


@dataclass(frozen=True)
class TextualCriterionObservationDefinition:
    observation_id: str
    reading_id: str
    evidence_type: EvidenceType | str
    criterion: MethodologyCriterion | str
    observation_value: str
    evaluation_score: float = 0.0
    is_automatic_priority: bool = False
    notes: Optional[str] = None


@dataclass(frozen=True)
class TextualDecisionDefinition:
    decision_id: str
    variant_unit_id: str
    decision_state: TextualDecisionState | str
    preferred_reading_id: Optional[str] = None
    confidence_score: float = 0.0
    is_certain_original: bool = False
    competing_readings_preserved: bool = True
    external_evidence_summary: str = ""
    internal_evidence_summary: str = ""
    reasoning: str = ""
    claim_id: Optional[str] = None
    observations: Sequence[TextualCriterionObservationDefinition] = ()
    metadata_json: Optional[str] = None


@dataclass(frozen=True)
class TextualCriticismConfig:
    analyzer_id: str = "POLYA-TEXTUAL-CRITIC-1.0"
    analyzer_version: str = "1.0.0"
    model_name: Optional[str] = None
    strict_firewalls: bool = True


@dataclass(frozen=True)
class TextualCriticismRunResult:
    run_id: str
    version_id: str
    provenance_id: str
    variant_unit_ids: List[str]
    decision_ids: List[str]
    evidence_ids: List[str]
    competing_readings_count: int
    output_hash: str
    status: str


# =============================================================================
# TEXTUAL CRITICISM MANAGER
# =============================================================================

class TextualCriticismManager:
    """
    Core execution manager for Textual Criticism in Polya Bible Engine.
    Coordinates runs, witness metadata, variant units, readings, attestations,
    observations, decisions, provenance, versioning, and evidence links.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        version_manager: Optional[VersionManager] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        evidence_claim_manager: Optional[EvidenceClaimManager] = None,
    ) -> None:
        self.engine = engine
        self.version_manager = version_manager or VersionManager(engine)
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.evidence_claim_manager = evidence_claim_manager or EvidenceClaimManager(engine)

    def register_witness(self, witness: WitnessDefinition) -> str:
        """
        Register a primary manuscript or version witness with metadata and firewalls.
        """
        # Epistemic Firewalls
        if witness.is_ai_synthetic:
            raise AITextualEvidenceFirewallError(
                f"Witness '{witness.witness_id}' is AI-synthetic: cannot be registered as an ancient textual witness."
            )
        if witness.is_modern_translation:
            raise ModernTranslationAsAttestationFirewallError(
                f"Witness '{witness.witness_id}' is a modern translation: cannot be registered as ancient witness attestation."
            )

        witness_type_val = witness.witness_type.value if isinstance(witness.witness_type, WitnessType) else str(witness.witness_type).upper()

        if witness.is_translation and witness_type_val != WitnessType.EARLY_TRANSLATION.value:
            raise TranslationAsWitnessFirewallError(
                f"Witness '{witness.witness_id}' is marked as a translation but typed as '{witness_type_val}'. "
                "Secondary translations cannot be registered as primary manuscript witnesses."
            )
        if witness.is_translation and witness.language.upper() in ("GREEK", "HEBREW", "ARAMAIC"):
            raise TranslationAsWitnessFirewallError(
                f"Witness '{witness.witness_id}' is marked as translation in original language '{witness.language}'. "
                "Translations cannot be cited as direct primary source language witnesses."
            )
        ident_status_val = witness.identifier_status.value if isinstance(witness.identifier_status, IdentifierStatus) else str(witness.identifier_status).upper()
        family_val = witness.textual_family.value if isinstance(witness.textual_family, TextualFamily) else (str(witness.textual_family).upper() if witness.textual_family else None)

        now = datetime.now(timezone.utc).isoformat()
        prov_hash = compute_canonical_hash({
            "witness_id": witness.witness_id,
            "siglum": witness.siglum,
            "name": witness.name,
            "witness_type": witness_type_val,
            "language": witness.language.upper(),
            "century_origin": witness.century_origin,
        })

        with self.engine.transaction() as conn:
            # 1. Insert into migration 001 witnesses table if not already present
            conn.execute(
                """
                INSERT OR IGNORE INTO witnesses (
                    witness_id, siglum, name, witness_type, language,
                    century_origin, dating_estimate_start, dating_estimate_end,
                    repository, provenance_hash, is_source_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    witness.witness_id,
                    witness.siglum,
                    witness.name,
                    witness_type_val,
                    witness.language.upper(),
                    witness.century_origin,
                    witness.dating_estimate_start,
                    witness.dating_estimate_end,
                    witness.repository,
                    prov_hash,
                ),
            )

            # 2. Insert into witness_metadata_v2
            conn.execute(
                """
                INSERT OR REPLACE INTO witness_metadata_v2 (
                    witness_id, external_identifier, identifier_system, identifier_status,
                    textual_family, geographic_origin, is_translation, is_modern_translation,
                    is_ai_synthetic, provenance_id, created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    witness.witness_id,
                    witness.external_identifier,
                    witness.identifier_system,
                    ident_status_val,
                    family_val,
                    witness.geographic_origin,
                    1 if witness.is_translation else 0,
                    1 if witness.is_modern_translation else 0,
                    1 if witness.is_ai_synthetic else 0,
                    witness.provenance_id,
                    now,
                    witness.metadata_json,
                ),
            )

        return witness.witness_id

    def execute_run(
        self,
        run_id: str,
        passage_id: str,
        variant_units: Sequence[VariantUnitDefinition],
        variant_readings: Sequence[VariantReadingDefinition],
        attestations: Sequence[WitnessAttestationDefinition],
        decisions: Sequence[TextualDecisionDefinition],
        config: Optional[TextualCriticismConfig] = None,
        source_text_id: Optional[str] = None,
        edition_id: Optional[str] = None,
        pericope_id: Optional[str] = None,
        token_start_id: Optional[str] = None,
        token_end_id: Optional[str] = None,
        version_id: Optional[str] = None,
        provenance_id: Optional[str] = None,
    ) -> TextualCriticismRunResult:
        """
        Execute an end-to-end versioned textual-critical run with rigorous epistemic firewalls.
        """
        cfg = config or TextualCriticismConfig()
        now = datetime.now(timezone.utc).isoformat()

        # Build maps for validation
        units_map = {u.variant_unit_id: u for u in variant_units}
        readings_map = {r.reading_id: r for r in variant_readings}
        readings_by_unit: Dict[str, List[VariantReadingDefinition]] = {}
        for r in variant_readings:
            readings_by_unit.setdefault(r.variant_unit_id, []).append(r)

        # ---------------------------------------------------------------------
        # FIREWALL 1: Validate Passage & Witness Existence & Constraints
        # ---------------------------------------------------------------------
        with self.engine.transaction() as conn:
            # Check passage exists
            cursor = conn.execute("SELECT 1 FROM passages WHERE passage_id = ?", (passage_id,))
            if not cursor.fetchone():
                cursor_p = conn.execute("SELECT 1 FROM pericopes WHERE pericope_id = ?", (passage_id,))
                if not cursor_p.fetchone():
                    raise VariantUnitNotFoundError(f"Passage or Pericope '{passage_id}' does not exist.")

            # Check witnesses exist in database
            known_witnesses: Dict[str, Dict[str, Any]] = {}
            for att in attestations:
                cursor = conn.execute(
                    """
                    SELECT w.witness_id, w.language, w.witness_type,
                           m.is_translation, m.is_modern_translation, m.is_ai_synthetic
                    FROM witnesses w
                    LEFT JOIN witness_metadata_v2 m ON w.witness_id = m.witness_id
                    WHERE w.witness_id = ?
                    """,
                    (att.witness_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise WitnessNotFoundError(
                        f"Witness '{att.witness_id}' cited in attestation '{att.attestation_id}' is not registered."
                    )
                w_id, lang, w_type, is_trans, is_mod_trans, is_ai = row
                known_witnesses[w_id] = {
                    "language": lang,
                    "witness_type": w_type,
                    "is_translation": bool(is_trans),
                    "is_modern_translation": bool(is_mod_trans),
                    "is_ai": bool(is_ai),
                }

        for att in attestations:
            w_info = known_witnesses.get(att.witness_id, {})
            if w_info.get("is_ai"):
                raise AITextualEvidenceFirewallError(
                    f"Attestation '{att.attestation_id}' links to AI synthetic witness '{att.witness_id}'."
                )
            if w_info.get("is_modern_translation"):
                raise ModernTranslationAsAttestationFirewallError(
                    f"Attestation '{att.attestation_id}' links to modern translation '{att.witness_id}'."
                )

        # ---------------------------------------------------------------------
        # FIREWALL 2: Competing Readings Preservation
        # ---------------------------------------------------------------------
        for u_id, u_readings in readings_by_unit.items():
            if len(u_readings) < 2:
                raise SuppressionOfAlternativeReadingsFirewallError(
                    f"Variant unit '{u_id}' has only {len(u_readings)} reading(s). "
                    "A textual variant unit must represent and preserve all competing readings (minimum 2)."
                )

        # ---------------------------------------------------------------------
        # FIREWALL 3: Textual Decision States & Preferred Reading Checks
        # ---------------------------------------------------------------------
        for dec in decisions:
            if dec.variant_unit_id not in units_map:
                raise VariantUnitNotFoundError(f"Decision references unknown variant unit '{dec.variant_unit_id}'.")

            state_val = dec.decision_state.value if isinstance(dec.decision_state, TextualDecisionState) else str(dec.decision_state).upper()

            # Rule: Preferred reading is never automatically certain original
            if state_val == TextualDecisionState.PREFERRED.value and dec.is_certain_original:
                raise PreferredAsCertainOriginalFirewallError(
                    f"Decision '{dec.decision_id}': A PREFERRED reading cannot be marked as CERTAIN_ORIGINAL."
                )

            # Rule: Decision state must be valid
            if state_val not in [s.value for s in TextualDecisionState]:
                raise TextualCriticismSubsystemError(f"Invalid decision state: {state_val}")

            # Rule: Confidence cannot upgrade decision to certain original
            if dec.confidence_score >= 0.95 and dec.is_certain_original:
                raise ConfidenceTextualUpgradeFirewallError(
                    f"Decision '{dec.decision_id}': Model confidence score {dec.confidence_score} cannot upgrade textual decision to certain original."
                )

            # Check preferred reading exists if specified
            if dec.preferred_reading_id and dec.preferred_reading_id not in readings_map:
                raise VariantReadingNotFoundError(
                    f"Preferred reading '{dec.preferred_reading_id}' in decision '{dec.decision_id}' is not in readings."
                )

            # -----------------------------------------------------------------
            # FIREWALL 4: Methodological Criteria Priority Firewalls
            # -----------------------------------------------------------------
            for obs in dec.observations:
                if obs.reading_id not in readings_map:
                    raise VariantReadingNotFoundError(f"Observation references unknown reading '{obs.reading_id}'.")

                obs_type = obs.evidence_type.value if isinstance(obs.evidence_type, EvidenceType) else str(obs.evidence_type).upper()
                crit_val = obs.criterion.value if isinstance(obs.criterion, MethodologyCriterion) else str(obs.criterion).upper()

                # Boundary constraint: external vs internal criteria
                if obs_type == "EXTERNAL" and not crit_val.startswith("EXTERNAL_"):
                    raise TextualCriticismSubsystemError(
                        f"Criterion '{crit_val}' is not external, but was typed as EXTERNAL in observation '{obs.observation_id}'."
                    )
                if obs_type == "INTERNAL" and crit_val.startswith("EXTERNAL_"):
                    raise TextualCriticismSubsystemError(
                        f"Criterion '{crit_val}' is an external criterion, but was typed as INTERNAL in observation '{obs.observation_id}'."
                    )

                if obs.is_automatic_priority:
                    if crit_val == MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_DIFFICILIOR.value:
                        raise LectioDifficiliorPriorityFirewallError(
                            f"Decision '{dec.decision_id}': lectio difficilior cannot be an automatic truth-selection formula."
                        )
                    elif crit_val == MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_BREVIOR.value:
                        raise LectioBreviorPriorityFirewallError(
                            f"Decision '{dec.decision_id}': lectio brevior cannot be an automatic truth-selection formula."
                        )
                    elif crit_val == MethodologyCriterion.EXTERNAL_WITNESS_DATE.value:
                        raise WitnessAgePriorityFirewallError(
                            f"Decision '{dec.decision_id}': witness date/age alone cannot determine textual priority."
                        )
                    elif crit_val == MethodologyCriterion.EXTERNAL_WITNESS_ATTESTATION.value:
                        raise WitnessCountPriorityFirewallError(
                            f"Decision '{dec.decision_id}': number of witnesses alone cannot determine textual priority."
                        )
                    elif crit_val == MethodologyCriterion.EXTERNAL_TEXTUAL_FAMILY.value:
                        raise TextualFamilyPriorityFirewallError(
                            f"Decision '{dec.decision_id}': textual family alone cannot determine textual priority."
                        )
                    else:
                        raise AutomaticPriorityCriterionFirewallError(
                            f"Decision '{dec.decision_id}': criterion '{crit_val}' cannot be an automatic priority formula."
                        )

        # ---------------------------------------------------------------------
        # PROVENANCE & VERSIONING INTEGRATION
        # ---------------------------------------------------------------------
        config_hash = compute_canonical_hash(asdict(cfg))
        input_hash = compute_canonical_hash({
            "passage_id": passage_id,
            "units": [asdict(u) for u in variant_units],
            "readings": [asdict(r) for r in variant_readings],
            "attestations": [asdict(a) for a in attestations],
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "variant_unit_id": d.variant_unit_id,
                    "state": str(d.decision_state),
                    "score": d.confidence_score,
                    "certain": d.is_certain_original,
                }
                for d in decisions
            ],
        })

        output_hash = compute_canonical_hash({
            "run_id": run_id,
            "input_hash": input_hash,
            "config_hash": config_hash,
            "decision_count": len(decisions),
        })

        decision_ids: List[str] = []
        evidence_ids: List[str] = []

        with self.engine.transaction() as conn:
            # Register Provenance for Run
            provenance_rec = self.provenance_tracker.record_deterministic(
                target_type=TargetType.DERIVED_ARTIFACT,
                target_id=run_id,
                content=f"TEXTUAL_CRITICISM_RUN:{run_id}:{output_hash}",
                input_data=input_hash,
                agent_id=cfg.analyzer_id,
                agent_version=cfg.analyzer_version,
                conn=conn,
            )
            effective_prov_id = provenance_id or provenance_rec.provenance_id

            # Register Version for Run
            version_rec = self.version_manager.create_version(
                object_type="TEXTUAL_CRITICISM_RUN",
                object_id=run_id,
                content_hash=output_hash,
                change_reason=ChangeReason.INITIAL_CREATION,
                created_by=cfg.analyzer_id,
                provenance_id=effective_prov_id,
                version_id=version_id,
                conn=conn,
            )
            effective_version_id = version_rec.version_id

            # 1. Insert Textual Criticism Run
            conn.execute(
                """
                INSERT INTO textual_criticism_runs (
                    run_id, source_text_id, edition_id, passage_id, pericope_id,
                    token_start_id, token_end_id, version_id, provenance_id,
                    analyzer_id, analyzer_version, model_name, configuration_hash,
                    input_content_hash, output_hash, status, is_exact_reproducible,
                    created_at, is_immutable, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED', 1, ?, 1, ?)
                """,
                (
                    run_id,
                    source_text_id,
                    edition_id,
                    passage_id,
                    pericope_id,
                    token_start_id,
                    token_end_id,
                    effective_version_id,
                    effective_prov_id,
                    cfg.analyzer_id,
                    cfg.analyzer_version,
                    cfg.model_name,
                    config_hash,
                    input_hash,
                    output_hash,
                    now,
                    json.dumps({"variant_units_count": len(variant_units)}),
                ),
            )

            # Mark previous completed runs for this passage as SUPERSEDED
            conn.execute(
                "UPDATE textual_criticism_runs SET status = 'SUPERSEDED' WHERE passage_id = ? AND run_id != ? AND status = 'COMPLETED'",
                (passage_id, run_id),
            )

            # Map unit to decision ev_id
            decisions_by_unit = {d.variant_unit_id: f"EV-TC-{d.decision_id}" for d in decisions}

            # 2. Insert Variant Units (into 001 variant_units table if absent)
            for u in variant_units:
                sig_val = u.critical_significance.value if isinstance(u.critical_significance, CriticalSignificance) else str(u.critical_significance).upper()
                ed_val = u.editorial_status.value if isinstance(u.editorial_status, EditorialStatus) else str(u.editorial_status).upper()

                conn.execute(
                    """
                    INSERT OR IGNORE INTO variant_units (
                        variant_unit_id, passage_id, word_position_start,
                        word_position_end, base_text_reading, critical_significance,
                        editorial_status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        u.variant_unit_id,
                        u.passage_id,
                        u.word_position_start,
                        u.word_position_end,
                        u.base_text_reading,
                        sig_val,
                        ed_val,
                        u.notes,
                    ),
                )


            # 3. Insert Variant Readings (into 001 variant_readings table if absent)
            for r in variant_readings:
                cat_val = r.reading_category.value if isinstance(r.reading_category, ReadingCategory) else str(r.reading_category).upper()
                conf_val = r.reading_confidence.value if isinstance(r.reading_confidence, ReadingConfidence) else str(r.reading_confidence).upper()

                conn.execute(
                    """
                    INSERT OR IGNORE INTO variant_readings (
                        reading_id, variant_unit_id, reading_siglum,
                        greek_or_hebrew_string, external_evidence_summary,
                        internal_evidence_evaluation, reading_category, reading_confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r.reading_id,
                        r.variant_unit_id,
                        r.reading_siglum,
                        r.greek_or_hebrew_string,
                        r.external_evidence_summary,
                        r.internal_evidence_evaluation,
                        cat_val,
                        conf_val,
                    ),
                )

            # 4. Insert Witness Attestations (into 001 variant_witness_attestations table)
            for att in attestations:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO variant_witness_attestations (
                        attestation_id, reading_id, witness_id, folio_or_page,
                        is_correction, transcription_text
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        att.attestation_id,
                        att.reading_id,
                        att.witness_id,
                        att.folio_or_page,
                        1 if att.is_correction else 0,
                        att.transcription_text,
                    ),
                )

            # 5. Insert Decisions & Link to Evidence Claim Subsystem
            for dec in decisions:
                state_val = dec.decision_state.value if isinstance(dec.decision_state, TextualDecisionState) else str(dec.decision_state).upper()
                ev_id = f"EV-TC-{dec.decision_id}"
                dec_prov_id = f"PROV-DEC-{dec.decision_id}"
                dec_ver_id = f"VER-DEC-{dec.decision_id}"
                unit = units_map[dec.variant_unit_id]

                # Record Evidence in Evidence Claim Subsystem (E1_TEXTUAL_MANUSCRIPT)
                # Maps directly to existing evidence_ledger table from Migration 012!
                ev_def = EvidenceDefinition(
                    evidence_id=ev_id,
                    pericope_id=unit.pericope_id or pericope_id or "PER-CANONICAL",
                    passage_id=unit.passage_id,
                    evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
                    epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
                    source_reference=f"{unit.passage_id} variant {dec.variant_unit_id}",
                    extracted_text_or_data=json.dumps({
                        "variant_unit_id": dec.variant_unit_id,
                        "preferred_reading_id": dec.preferred_reading_id,
                        "decision_state": state_val,
                        "confidence_score": dec.confidence_score,
                        "competing_readings_preserved": True,
                    }),
                    status=EvidenceStatus.EXPLICIT,
                    confidence=ConfidenceLevel.HIGH if dec.confidence_score >= 0.7 else ConfidenceLevel.MEDIUM,
                    confidence_score=dec.confidence_score,
                    is_counter_evidence=False,
                    is_ai_generated=False,
                    is_translation_derived=False,
                    provenance_id=effective_prov_id,
                    version_id=effective_version_id,
                )

                ev_conf_str = ev_def.confidence.value if isinstance(ev_def.confidence, ConfidenceLevel) else str(ev_def.confidence).upper()
                ev_tier_str = "T1_LINGUISTIC_FACT" if state_val in (TextualDecisionState.PREFERRED.value, TextualDecisionState.POSSIBLE.value) else "T0_RAW_OBSERVATION"

                prov_hasher = hashlib.sha256()
                prov_hasher.update(
                    f"{ev_id}:{ev_def.pericope_id}:{ev_def.passage_id}:{ev_def.source_reference}:{ev_def.extracted_text_or_data}".encode(
                        "utf-8"
                    )
                )
                ev_prov_hash = prov_hasher.hexdigest()

                conn.execute(
                    """
                    INSERT OR REPLACE INTO evidence_ledger (
                        evidence_id, run_id, pericope_id, passage_id, token_id,
                        evidence_class, epistemic_tier, epistemic_type,
                        source_reference, extracted_text_or_data, status,
                        confidence, confidence_score, is_counter_evidence,
                        is_ai_generated, is_translation_derived, is_contradicted,
                        provenance_id, version_id, created_at, provenance_hash,
                        is_immutable, metadata_json
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, 'LINGUISTIC_FACT',
                        ?, ?, '[EXPLICIT]', ?, ?, 0, 0, 0, 0,
                        ?, ?, ?, ?, 1, ?
                    )
                    """,
                    (
                        ev_id,
                        None,
                        ev_def.pericope_id,
                        ev_def.passage_id,
                        unit.token_start_id or token_start_id,
                        "E1_TEXTUAL_MANUSCRIPT",
                        ev_tier_str,
                        ev_def.source_reference,
                        ev_def.extracted_text_or_data,
                        ev_conf_str,
                        dec.confidence_score,
                        effective_prov_id,
                        effective_version_id,
                        now,
                        ev_prov_hash,
                        dec.metadata_json,
                    ),
                )
                evidence_ids.append(ev_id)

                # Register Provenance for Decision
                dec_prov_rec = self.provenance_tracker.record_deterministic(
                    target_type=TargetType.DERIVED_ARTIFACT,
                    target_id=dec.decision_id,
                    content=f"TEXTUAL_DECISION:{dec.decision_id}:{state_val}",
                    input_data={"decision_id": dec.decision_id, "state": state_val},
                    agent_id=cfg.analyzer_id,
                    agent_version=cfg.analyzer_version,
                    conn=conn,
                )
                effective_dec_prov_id = dec_prov_rec.provenance_id

                # Register Version for Decision
                dec_ver_rec = self.version_manager.create_version(
                    object_type="TEXTUAL_DECISION",
                    object_id=dec.decision_id,
                    content_hash=compute_canonical_hash({"decision_id": dec.decision_id, "state": state_val}),
                    change_reason=ChangeReason.INITIAL_CREATION,
                    created_by=cfg.analyzer_id,
                    provenance_id=effective_dec_prov_id,
                    conn=conn,
                )
                effective_dec_ver_id = dec_ver_rec.version_id

                # Insert Textual Decision
                u_readings = readings_by_unit.get(dec.variant_unit_id, [])
                conn.execute(
                    """
                    INSERT INTO textual_decisions (
                        decision_id, run_id, variant_unit_id, preferred_reading_id,
                        decision_state, confidence_score, is_certain_original,
                        competing_readings_count, competing_readings_preserved,
                        external_evidence_summary, internal_evidence_summary,
                        reasoning, evidence_id, claim_id, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        dec.decision_id,
                        run_id,
                        dec.variant_unit_id,
                        dec.preferred_reading_id,
                        state_val,
                        dec.confidence_score,
                        1 if dec.is_certain_original else 0,
                        len(u_readings),
                        dec.external_evidence_summary,
                        dec.internal_evidence_summary,
                        dec.reasoning,
                        ev_id,
                        dec.claim_id,
                        effective_dec_prov_id,
                        effective_dec_ver_id,
                        now,
                        dec.metadata_json,
                    ),
                )
                decision_ids.append(dec.decision_id)

                # Insert Observations
                for obs in dec.observations:
                    obs_type = obs.evidence_type.value if isinstance(obs.evidence_type, EvidenceType) else str(obs.evidence_type).upper()
                    obs_crit = obs.criterion.value if isinstance(obs.criterion, MethodologyCriterion) else str(obs.criterion).upper()
                    obs_hash = compute_canonical_hash(asdict(obs))

                    conn.execute(
                        """
                        INSERT INTO textual_criterion_observations (
                            observation_id, decision_id, reading_id, evidence_type,
                            criterion, observation_value, evaluation_score,
                            is_automatic_priority, notes, provenance_hash,
                            created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, 1)
                        """,
                        (
                            obs.observation_id,
                            dec.decision_id,
                            obs.reading_id,
                            obs_type,
                            obs_crit,
                            obs.observation_value,
                            obs.evaluation_score,
                            obs.notes,
                            obs_hash,
                            now,
                        ),
                    )

            # 6. Insert Variant Unit Executions (now that evidence_ledger is populated)
            for u in variant_units:
                vue_id = f"VUE-{run_id}-{u.variant_unit_id}"
                ev_id_for_unit = decisions_by_unit.get(u.variant_unit_id)
                conn.execute(
                    """
                    INSERT INTO variant_unit_executions (
                        execution_id, run_id, variant_unit_id, pericope_id,
                        token_start_id, token_end_id, evidence_id, provenance_id,
                        created_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        vue_id,
                        run_id,
                        u.variant_unit_id,
                        u.pericope_id or pericope_id,
                        u.token_start_id or token_start_id,
                        u.token_end_id or token_end_id,
                        ev_id_for_unit,
                        effective_prov_id,
                        now,
                    ),
                )

        return TextualCriticismRunResult(
            run_id=run_id,
            version_id=effective_version_id,
            provenance_id=effective_prov_id,
            variant_unit_ids=list(units_map.keys()),
            decision_ids=decision_ids,
            evidence_ids=evidence_ids,
            competing_readings_count=len(variant_readings),
            output_hash=output_hash,
            status="COMPLETED",
        )

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve textual criticism run record by run_id."""
        with self.engine.transaction() as conn:
            cursor = conn.execute("SELECT * FROM textual_criticism_runs WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    def get_variant_unit(self, variant_unit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve variant unit from migration 001 table."""
        with self.engine.transaction() as conn:
            cursor = conn.execute("SELECT * FROM variant_units WHERE variant_unit_id = ?", (variant_unit_id,))
            row = cursor.fetchone()
            if not row:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    def get_decisions_for_variant(self, variant_unit_id: str) -> List[Dict[str, Any]]:
        """Retrieve decisions for a variant unit."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT * FROM textual_decisions WHERE variant_unit_id = ? ORDER BY created_at ASC",
                (variant_unit_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_attestations_for_reading(self, reading_id: str) -> List[Dict[str, Any]]:
        """Retrieve witness attestations for a reading."""
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                """
                SELECT a.*, w.siglum, w.name as witness_name, w.witness_type, w.century_origin
                FROM variant_witness_attestations a
                JOIN witnesses w ON a.witness_id = w.witness_id
                WHERE a.reading_id = ?
                """,
                (reading_id,),
            )
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
