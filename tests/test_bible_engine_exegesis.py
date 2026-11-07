"""
Rigorous Adversarial Test Suite for Exegesis Foundation Subsystem (Task 2.9).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Interpretation without evidence rejected
  2. Unsupported conclusion rejected
  3. Counter-evidence cannot be silently removed
  4. Competing interpretations preserved
  5. Model majority cannot establish truth
  6. Confidence cannot upgrade evidence
  7. Translation cannot become source evidence
  8. Morphology cannot become theology automatically
  9. Syntax cannot become theology automatically
  10. Semantic sense cannot become theology automatically
  11. Discourse cannot become theology automatically
  12. Entity association cannot become identity
  13. Strict identity requires independent evidence
  14. Ambiguity preserved
  15. Pericope remains primary exegesis unit
  16. Verse cannot replace pericope provenance
  17. Source immutability
  18. Lower-level evidence immutability
  19. Provenance required
  20. Version supersession
  21. Rollback
  22. Concurrency safety
  23. Migration checksums 001-012 verification
  24. Legacy DB SHA-256 verification
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.config import DatabaseConfig
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
from bible_engine.evidence_claim import (
    ClaimDefinition,
    ClaimEvidenceLinkDefinition,
    ClaimTier,
    EpistemicType,
    EvidenceClaimConfig,
    EvidenceClaimManager,
    EvidenceClass,
    EvidenceDefinition,
    EvidenceRelationship,
)
from bible_engine.exegesis import (
    AuditRelationship,
    CalibratedConclusionDefinition,
    CalibratedConclusionRecord,
    CompetingInterpretationDefinition,
    CompetingInterpretationRecord,
    ContextualFindingDefinition,
    EvidenceAuditDefinition,
    ExegesisConfig,
    ExegesisManager,
    ExegesisObservationDefinition,
    InterpretiveHypothesisDefinition,
    LinguisticFindingDefinition,
    TensionType,
    UnresolvedIssueDefinition,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker
from bible_engine.source_registry import (
    SourceAuthorityLevel,
    SourceLanguage,
    SourceRegistry,
    SourceType,
)
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
)
from bible_engine.versioning import ChangeReason, VersionManager


EXPECTED_MIGRATION_CHECKSUMS: Dict[str, str] = {
    "001_initial_schema.sql": "dca5e56fa1ab2ce5472e47aa5d61b1630fe9533d028df60a93506420516ce201",
    "002_provenance.sql": "f2932bfda7beb792d0993880d43ed7326965630f77526d756a235606b7793267",
    "003_versioning.sql": "83bf6b0a6a72156791cf6c701ad4501e3349b1ff602f01ab17df956a8cea8381",
    "004_source_registry.sql": "0613e2b35e957fed65ce9e75ac1b1dde00258860dfac219f3750472601fab33e",
    "005_source_text.sql": "e6d9663b5e94ea7610daa07979130fa00790e7157a1e86b421a6915192683a77",
    "006_tokenization.sql": "08782cf1aca1ac351419130c9d1d22cac034679154f75b5bada0819c8588bf3b",
    "007_morphology.sql": "dff8781a7c65828b5bdd542a321c4c81f499836cb38e96025154aee3a03eb145",
    "008_syntax.sql": "2daf0ebfd0022e480ea079ab02ec4d37f37eefa733281458327b19d20c3a649b",
    "009_semantics.sql": "93f606e376f80cef7e60f194961d4d163257a4dfb6444f35eb57974865183113",
    "010_referential_entity.sql": "1ec09317ceb1c21bbe4c451b0400538a7ad821ea615d423bc72b0141f4e6b055",
    "011_discourse_context.sql": "e09595cfc19c43d2e42b2f04925bd20fa7e6fb5bd0aa31937926d9afd3732c98",
    "012_evidence_claim.sql": "3c9bfd78943189caa1a56411f8aad0d1c1f5c37075618624513fe2ad37f31944",
}

LEGACY_DB_SHA256 = "500bb6a2057a1c30e392f0a99f2437a9b07a79a075e79177a0b9d17e7353c5c5"


class TestBibleEngineExegesis(unittest.TestCase):
    """Rigorous adversarial test suite for Exegesis Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_exegesis.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Scaffolding required by foreign keys
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )
            conn.execute(
                """
                INSERT INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                    'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-07', 'PER-REV-19', 'REV', 19, 7, 1);")
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 2);")
            conn.execute("INSERT INTO passages VALUES ('REV-19-09', 'PER-REV-19', 'REV', 19, 9, 3);")

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.source_registry.register_source(
            source_id="SRC-NA28-REV",
            canonical_name="Novum Testamentum Graece 28 - Revelation",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        st = self.source_text_mgr.register_source_text(
            source_id="SRC-NA28-REV",
            source_text_id="ST-NA28-REV-19-08",
            language=SourceTextLanguage.GREEK,
            raw_content="ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον λαμπρὸν καθαρόν",
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )
        self.source_text_id = st.source_text_id
        self.ev_mgr = EvidenceClaimManager(self.engine)
        self.ex_mgr = ExegesisManager(self.engine)

        # Create basic foundational evidence & claims
        ev1 = EvidenceDefinition(
            evidence_id="EV-BASE-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28 Wahyu 19:8",
            extracted_text_or_data="βύσσινον λαμπρὸν καθαρόν",
        )
        ev2 = EvidenceDefinition(
            evidence_id="EV-BASE-02",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E2_MORPHOLOGY,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Verb parse",
            extracted_text_or_data="ἐδόθη: Aorist Passive Indicative 3S",
        )
        ev_contra = EvidenceDefinition(
            evidence_id="EV-CONTRA-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Codex Sinaiticus variant",
            extracted_text_or_data="καθαρὸν καὶ λαμπρόν",
            is_counter_evidence=True,
        )

        cl1 = ClaimDefinition(
            claim_id="CLM-BASE-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="Textual grammar indicates divine passive.",
            claimed_by="NA28_ANALYSER",
        )
        link1 = ClaimEvidenceLinkDefinition(
            link_id="LNK-BASE-01",
            claim_id="CLM-BASE-01",
            evidence_id="EV-BASE-02",
            relationship=EvidenceRelationship.SUPPORT,
            is_critical_dependency=True,
            reasoning="Passive voice morphology confirms passive grant.",
        )

        self.ev_run = self.ev_mgr.record_evidence_and_claims(
            source_text_id=self.source_text_id,
            evidence_defs=[ev1, ev2, ev_contra],
            claim_defs=[cl1],
            link_defs=[link1],
            run_id="EV-RUN-BASE-01",
        )

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. PERICOPE AS PRIMARY EXEGESIS UNIT
    # -------------------------------------------------------------------------

    def test_pericope_remains_primary_exegesis_unit(self) -> None:
        """Valid pericope allows successful exegesis record."""
        obs = ExegesisObservationDefinition(
            observation_id="OBS-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            observation_type="RAW_OBSERVATION",
            source_reference="NA28",
            observed_text_or_data="βύσσινον",
        )
        run = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            evidence_run_id=self.ev_run.run.run_id,
            observations=[obs],
            run_id="EXEG-VALID-01",
        )
        self.assertEqual(run.pericope_id, "PER-REV-19")
        self.assertEqual(run.status, "COMPLETED")

    def test_verse_cannot_replace_pericope_primary_unit(self) -> None:
        """Supplying a verse address instead of pericope ID is rejected."""
        with self.assertRaises(PericopePrimaryUnitFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="REV-19-08",  # Verse address, not pericope
                source_text_id=self.source_text_id,
            )

    # -------------------------------------------------------------------------
    # 2. INTERPRETATION & CONCLUSION EVIDENCE AUDIT FIREWALLS
    # -------------------------------------------------------------------------

    def test_interpretation_without_evidence_rejected(self) -> None:
        """Hypothesis marked SUPPORTED with zero evidence audits is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-NO-EV-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Fine linen represents allegorical dogma.",
            hypothesis_state="SUPPORTED",
            claim_tier="T3_INTERPRETIVE_CLAIM",
        )
        with self.assertRaises(InterpretationWithoutEvidenceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
                evidence_audits=[],  # Zero supporting audits
            )

    def test_unsupported_conclusion_rejected(self) -> None:
        """Conclusion marked SUPPORTED with 0 supporting evidence count is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-UNSUP-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Linguistic observation on fine linen.",
            hypothesis_state="PROPOSED",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-UNSUP-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-UNSUP-01",
            conclusion_text="Linen is verified dogma.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.8,
            supporting_evidence_count=0,  # Zero supporting evidence
        )
        with self.assertRaises(UnsupportedConclusionFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
                calibrated_conclusions=[conc],
            )

    # -------------------------------------------------------------------------
    # 3. COUNTER-EVIDENCE & AMBIGUITY PRESERVATION
    # -------------------------------------------------------------------------

    def test_counter_evidence_cannot_be_silently_removed(self) -> None:
        """Conclusion reporting 0 counter-evidence when counter-audits exist is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-COUNTER-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Original word order is strictly καθαρόν then λαμπρόν.",
            hypothesis_state="PROPOSED",
        )
        audit_contra = EvidenceAuditDefinition(
            audit_id="AUD-CONTRA-01",
            hypothesis_id="HYP-COUNTER-01",
            evidence_id="EV-CONTRA-01",
            relationship="CONTRADICT",
            is_counter_evidence=True,
            audit_notes="Codex Sinaiticus transposes adjectives.",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-COUNTER-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-COUNTER-01",
            conclusion_text="Word order is established without contradiction.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.7,
            supporting_evidence_count=1,
            counter_evidence_count=0,  # Suppressed counter-evidence!
        )
        with self.assertRaises(SuppressionOfCounterEvidenceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
                evidence_audits=[audit_contra],
                calibrated_conclusions=[conc],
            )

    def test_unresolved_contradiction_cannot_be_supported(self) -> None:
        """Conclusion with unresolved contradiction cannot be marked SUPPORTED."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-CONTRADICTION-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Contradicted reading.",
            hypothesis_state="PROPOSED",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-CONTRADICTION-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-CONTRADICTION-01",
            conclusion_text="Reading established despite contradiction.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.5,
            supporting_evidence_count=1,
            counter_evidence_count=1,
            has_unresolved_contradiction=True,
        )
        with self.assertRaises(UnresolvedContradictionFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
                calibrated_conclusions=[conc],
            )

    def test_ambiguity_preserved_and_cannot_be_silently_resolved(self) -> None:
        """Silently resolving an ambiguity without justification is rejected."""
        issue = UnresolvedIssueDefinition(
            issue_id="ISSUE-AMBIG-01",
            pericope_id="PER-REV-19",
            issue_type="AMBIGUITY",
            description="Ambiguity in genitive relation.",
            is_silently_resolved=True,  # Silent resolution attempted
        )
        with self.assertRaises(SilentAmbiguityResolutionFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                unresolved_issues=[issue],
            )

    # -------------------------------------------------------------------------
    # 4. COMPETING INTERPRETATIONS & MODEL CONSENSUS
    # -------------------------------------------------------------------------

    def test_competing_interpretations_preserved_and_cannot_be_suppressed(self) -> None:
        """Setting is_suppressed=True on a competing interpretation is rejected."""
        hyp_a = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-A-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Reading A: Literal bride clothing.",
        )
        hyp_b = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-B-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Reading B: Collective community symbol.",
        )
        comp = CompetingInterpretationDefinition(
            competing_id="COMP-01",
            pericope_id="PER-REV-19",
            hypothesis_a_id="HYP-A-01",
            hypothesis_b_id="HYP-B-01",
            tension_type="ALTERNATIVE_READING",
            description="Literal vs figurative tension.",
            is_suppressed=True,  # Suppression attempted
        )
        with self.assertRaises(SuppressionOfCompetingInterpretationFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp_a, hyp_b],
                competing_interpretations=[comp],
            )

    def test_model_majority_cannot_establish_truth(self) -> None:
        """Hypothesis relying on model majority consensus is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-MAJ-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Interpretation accepted because 4/5 models agree.",
            is_majority_vote_derived=True,
        )
        with self.assertRaises(ModelMajorityTruthFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    # -------------------------------------------------------------------------
    # 5. CONFIDENCE & TRANSLATION FIREWALLS
    # -------------------------------------------------------------------------

    def test_confidence_cannot_upgrade_evidence(self) -> None:
        """Calibrated conclusion confidence cannot exceed weakest critical dependency."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-CONF-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Hypothesis with weak critical dependency.",
        )
        audit_crit = EvidenceAuditDefinition(
            audit_id="AUD-CRIT-01",
            hypothesis_id="HYP-CONF-01",
            evidence_id="EV-BASE-02",
            relationship="SUPPORT",
            is_critical=True,
            evidence_confidence=0.6,
            audit_notes="Critical dependency with 0.6 confidence",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-CONF-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-CONF-01",
            conclusion_text="Conclusion trying to upgrade confidence to 0.95",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.95,  # Exceeds 0.6!
            weakest_critical_dependency="EV-BASE-02",
            weakest_critical_confidence=0.6,
            supporting_evidence_count=1,
        )
        with self.assertRaises(ConfidenceUpgradeFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
                evidence_audits=[audit_crit],
                calibrated_conclusions=[conc],
            )

    def test_translation_cannot_become_source_evidence(self) -> None:
        """Translation-derived observation is rejected from becoming source evidence."""
        obs = ExegesisObservationDefinition(
            observation_id="OBS-TRANS-01",
            pericope_id="PER-REV-19",
            observation_type="RAW_OBSERVATION",
            source_reference="LAI TB Wahyu 19:8",
            observed_text_or_data="lenan halus yang berkilau-kilau",
            is_translation_derived=True,
        )
        with self.assertRaises(TranslationAsSourceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                observations=[obs],
            )

    # -------------------------------------------------------------------------
    # 6. DIRECT THEOLOGY & STRICT IDENTITY FIREWALLS
    # -------------------------------------------------------------------------

    def test_morphology_cannot_become_theology_automatically(self) -> None:
        """Directly manufacturing theology from morphology alone is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-THEO-MORPH-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Passive verb proves divine election dogma directly.",
            claim_tier="T4_THEOLOGICAL_CLAIM",
            direct_theology_source="MORPHOLOGY",
        )
        with self.assertRaises(ExegesisMorphologyTheologyFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_syntax_cannot_become_theology_automatically(self) -> None:
        """Directly manufacturing theology from syntax alone is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-THEO-SYNTAX-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Subordinate clause proves predestinarian dogma directly.",
            claim_tier="T4_THEOLOGICAL_CLAIM",
            direct_theology_source="SYNTAX",
        )
        with self.assertRaises(ExegesisSyntaxTheologyFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_semantic_sense_cannot_become_theology_automatically(self) -> None:
        """Directly manufacturing theology from lexical sense alone is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-THEO-SEM-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Lexeme βύσσινον proves imputed righteousness dogma directly.",
            claim_tier="T4_THEOLOGICAL_CLAIM",
            direct_theology_source="SEMANTICS",
        )
        with self.assertRaises(ExegesisSemanticTheologyFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_discourse_cannot_become_theology_automatically(self) -> None:
        """Directly manufacturing theology from discourse relation alone is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-THEO-DISC-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Discourse elaboration proves ecclesiological dogma directly.",
            claim_tier="T4_THEOLOGICAL_CLAIM",
            direct_theology_source="DISCOURSE",
        )
        with self.assertRaises(ExegesisDiscourseTheologyFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_entity_theology_source_rejected(self) -> None:
        """Directly manufacturing theology from entity association alone is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-THEO-ENT-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Entity mention directly proves hypostatic union dogma.",
            claim_tier="T4_THEOLOGICAL_CLAIM",
            direct_theology_source="ENTITY",
        )
        with self.assertRaises(ExegesisEntityIdentityFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_hypothesis_state_coercion_case_insensitive(self) -> None:
        """Hypothesis state coercion handles lowercase 'supported' and requires evidence."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-LOWER-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Lowercase state requiring audit.",
            hypothesis_state="supported",  # lowercase
        )
        with self.assertRaises(InterpretationWithoutEvidenceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_entity_association_cannot_become_identity_without_evidence(self) -> None:
        """Entity association asserting STRICT_IDENTITY without independent evidence is rejected."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-IDENTITY-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Bride is ontologically identical to historical institution.",
            asserts_strict_identity=True,
            independent_identity_evidence_id=None,  # No independent evidence
        )
        with self.assertRaises(StrictIdentityEvidenceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                hypotheses=[hyp],
            )

    def test_strict_identity_requires_independent_evidence(self) -> None:
        """Strict identity with independent evidence succeeds."""
        audit = EvidenceAuditDefinition(
            audit_id="AUD-ID-01",
            hypothesis_id="HYP-IDENTITY-OK",
            evidence_id="EV-BASE-01",
            relationship="SUPPORT",
            audit_notes="Direct textual naming verifies entity identity.",
        )
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-IDENTITY-OK",
            pericope_id="PER-REV-19",
            hypothesis_text="Bride is identified as saints' community.",
            hypothesis_state="SUPPORTED",
            asserts_strict_identity=True,
            independent_identity_evidence_id="EV-BASE-01",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-ID-OK",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-IDENTITY-OK",
            conclusion_text="Identity supported by explicit textual gloss.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.85,
            supporting_evidence_count=1,
        )
        run = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            hypotheses=[hyp],
            evidence_audits=[audit],
            calibrated_conclusions=[conc],
            run_id="EXEG-ID-OK",
        )
        self.assertEqual(run.status, "COMPLETED")

    # -------------------------------------------------------------------------
    # 7. IMMUTABILITY, PROVENANCE & VERSIONING
    # -------------------------------------------------------------------------

    def test_source_and_lower_level_evidence_immutability(self) -> None:
        """Database triggers prevent UPDATE or DELETE on exegesis and evidence tables."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE evidence_runs SET analyzer_id = 'HACKED' WHERE run_id = 'EV-RUN-BASE-01'")

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM evidence_ledger WHERE evidence_id = 'EV-BASE-01'")

    def test_exegesis_immutability_triggers(self) -> None:
        """Database triggers prevent UPDATE or DELETE on exegesis records."""
        run = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            run_id="EXEG-IMMUT-01",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE exegesis_runs SET analyzer_id = 'HACKED' WHERE run_id = 'EXEG-IMMUT-01'")

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM exegesis_runs WHERE run_id = 'EXEG-IMMUT-01'")

    def test_provenance_required_and_verified(self) -> None:
        """Exegesis runs must have valid provenance linkage."""
        run = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            run_id="EXEG-PROV-01",
        )
        self.assertTrue(bool(run.provenance_id))
        prov_record = self.ex_mgr.provenance_tracker.get_record(run.provenance_id)
        self.assertIsNotNone(prov_record)
        self.assertEqual(prov_record.target_id, "EXEG-PROV-01")

    def test_version_supersession(self) -> None:
        """Exegesis runs support structured versioning and supersession."""
        vm = VersionManager(self.engine)
        run1 = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            run_id="EXEG-V1",
        )
        run2 = self.ex_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=self.source_text_id,
            parent_version_id=run1.version_id,
            run_id="EXEG-V2",
        )
        self.assertNotEqual(run1.version_id, run2.version_id)
        v2_record = vm.get_version(run2.version_id)
        self.assertEqual(v2_record.parent_version_id, run1.version_id)

    def test_transactional_rollback(self) -> None:
        """Failure during exegesis persistence rolls back all tables cleanly."""
        obs = ExegesisObservationDefinition(
            observation_id="OBS-ROLLBACK-01",
            pericope_id="PER-REV-19",
            observation_type="RAW_OBSERVATION",
            source_reference="NA28",
            observed_text_or_data="βύσσινον",
        )
        # Invalid hypothesis with no evidence but marked SUPPORTED triggers rollback
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-ROLLBACK-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Will fail",
            hypothesis_state="SUPPORTED",
        )
        with self.assertRaises(InterpretationWithoutEvidenceFirewallError):
            self.ex_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id=self.source_text_id,
                observations=[obs],
                hypotheses=[hyp],
                run_id="EXEG-ROLLBACK-01",
            )

        with self.assertRaises(ExegesisRunNotFoundError):
            self.ex_mgr.get_exegesis_run("EXEG-ROLLBACK-01")

    def test_concurrency_safety(self) -> None:
        """Parallel insertions of exegesis runs on separate connections succeed cleanly."""
        def insert_exegesis(index: int) -> str:
            engine = DatabaseEngine(self.config)
            try:
                mgr = ExegesisManager(engine)
                obs = ExegesisObservationDefinition(
                    observation_id=f"OBS-CONC-{index}",
                    pericope_id="PER-REV-19",
                    observation_type="RAW_OBSERVATION",
                    source_reference=f"Source {index}",
                    observed_text_or_data=f"Text {index}",
                )
                run = mgr.record_exegesis(
                    pericope_id="PER-REV-19",
                    source_text_id=self.source_text_id,
                    observations=[obs],
                    run_id=f"EXEG-CONC-{index}",
                )
                return run.run_id
            finally:
                engine.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(insert_exegesis, range(5)))

        self.assertEqual(len(results), 5)
        for i in range(5):
            rec = self.ex_mgr.get_exegesis_run(f"EXEG-CONC-{i}")
            self.assertEqual(rec.run_id, f"EXEG-CONC-{i}")

    # -------------------------------------------------------------------------
    # 8. MIGRATION CHECKSUMS & LEGACY DB INTEGRITY
    # -------------------------------------------------------------------------

    def test_migration_checksums_001_to_012_unchanged(self) -> None:
        """Verify migrations 001-012 checksums match expected golden values."""
        migrations_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for filename, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            file_path = migrations_dir / filename
            self.assertTrue(file_path.exists(), f"Missing migration file: {filename}")
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Checksum mismatch for {filename}! Expected {expected_hash}, got {actual_hash}",
            )

    def test_legacy_db_sha256_unchanged(self) -> None:
        """Verify legacy database polya_index.db has not been altered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_sha,
                LEGACY_DB_SHA256,
                f"Legacy DB altered! Expected {LEGACY_DB_SHA256}, got {actual_sha}",
            )


if __name__ == "__main__":
    unittest.main()
