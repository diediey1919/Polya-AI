"""
Unit and Adversarial Test Suite for Textual Criticism Engine (Task 3.1).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Translation cannot become manuscript evidence
  2. Secondary translation cannot be registered as manuscript witness
  3. AI output cannot become primary textual evidence
  4. Unknown witness rejected
  5. Unverified external identifier preserved
  6. Competing readings preserved (suppression blocked)
  7. Preferred != Certain original
  8. Model confidence cannot upgrade decision to certain original
  9. Lectio difficilior != automatic priority
  10. Lectio brevior != automatic priority
  11. Witness count != automatic priority
  12. Witness age != automatic priority
  13. Textual family != automatic priority
  14. External/internal evidence criteria separation
  15. Evidence relationship integrity (E1 linked to evidence_ledger)
  16. Rollback on failure
  17. Concurrency safety
  18. Version supersession on reanalysis
  19. Provenance chain integrity verification
  20. Migration checksums 001-013 unchanged
  21. Legacy DB unchanged
  22. Realistic multi-reading variant unit pipeline (Yohanes 1:18)
"""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.config import DatabaseConfig
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
    TextualCriticismSubsystemError,
    TextualFamilyPriorityFirewallError,
    TranslationAsWitnessFirewallError,
    WitnessAgePriorityFirewallError,
    WitnessCountPriorityFirewallError,
    WitnessNotFoundError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceStatus,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.textual_criticism import (
    CriticalSignificance,
    EditorialStatus,
    EvidenceType,
    IdentifierStatus,
    MethodologyCriterion,
    ReadingCategory,
    ReadingConfidence,
    TextualCriticismConfig,
    TextualCriticismManager,
    TextualCriterionObservationDefinition,
    TextualDecisionDefinition,
    TextualDecisionState,
    TextualFamily,
    VariantReadingDefinition,
    VariantUnitDefinition,
    WitnessAttestationDefinition,
    WitnessDefinition,
    WitnessType,
)
from bible_engine.versioning import VersionManager

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
    "013_exegesis.sql": "5289378259eeebd23f057e7a55f447c5cb8277d7861694b288d927080248f720",
}

LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestTextualCriticismEngine(unittest.TestCase):
    """Test suite verifying all Task 3.1 requirements and epistemic firewalls."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_textual_criticism.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.evidence_claim_manager = EvidenceClaimManager(self.engine)
        self.tc_manager = TextualCriticismManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
            self.evidence_claim_manager,
        )

        # Baseline seed data
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute("INSERT INTO books VALUES ('JHN', 'NT', 43, 'Yohanes', 'John', 'GREEK', 21);")
            conn.execute(
                """
                INSERT INTO pericopes VALUES (
                    'PER-JHN-1', 'JHN', 'Yohanes 1:14-18', 1, 14, 1, 18,
                    'PROLOGUE', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-JHN-1-18', 'PER-JHN-1', 'JHN', 1, 18, 1);
                """
            )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. MODERN TRANSLATION AS ATTESTATION FIREWALL
    # -------------------------------------------------------------------------
    def test_01_translation_cannot_become_direct_manuscript_evidence(self) -> None:
        """A modern translation cannot be registered as an ancient witness attestation."""
        w_modern = WitnessDefinition(
            witness_id="MS-NIV-2011",
            siglum="NIV",
            name="New International Version",
            witness_type=WitnessType.EARLY_TRANSLATION,
            language="ENGLISH",
            century_origin="XXI CE",
            is_modern_translation=True,
        )
        with self.assertRaises(ModernTranslationAsAttestationFirewallError):
            self.tc_manager.register_witness(w_modern)

    # -------------------------------------------------------------------------
    # 2. SECONDARY TRANSLATION TYPED AS PRIMARY MANUSCRIPT FIREWALL
    # -------------------------------------------------------------------------
    def test_02_secondary_translation_cannot_be_manuscript_witness(self) -> None:
        """A translation cannot be registered with a primary manuscript type (UNCIAL/PAPYRUS)."""
        w_trans = WitnessDefinition(
            witness_id="MS-VULG-ERR",
            siglum="vg-err",
            name="Vulgate Erroneous",
            witness_type=WitnessType.UNCIAL,
            language="LATIN",
            century_origin="IV CE",
            is_translation=True,
        )
        with self.assertRaises(TranslationAsWitnessFirewallError):
            self.tc_manager.register_witness(w_trans)

    # -------------------------------------------------------------------------
    # 3. AI OUTPUT CANNOT BECOME WITNESS EVIDENCE
    # -------------------------------------------------------------------------
    def test_03_ai_output_cannot_become_primary_textual_evidence(self) -> None:
        """AI-generated content cannot be registered as an ancient textual witness."""
        w_ai = WitnessDefinition(
            witness_id="MS-AI-GEN-01",
            siglum="AI-SYN",
            name="Synthetic AI Manuscript",
            witness_type=WitnessType.PAPYRUS,
            language="GREEK",
            century_origin="II CE",
            is_ai_synthetic=True,
        )
        with self.assertRaises(AITextualEvidenceFirewallError):
            self.tc_manager.register_witness(w_ai)

    # -------------------------------------------------------------------------
    # 4. UNKNOWN WITNESS REJECTED
    # -------------------------------------------------------------------------
    def test_04_unknown_witness_rejected(self) -> None:
        """Citing an unregistered witness in an attestation must be rejected."""
        unit = VariantUnitDefinition(
            variant_unit_id="VAR-JHN-1-18-01",
            passage_id="PAS-JHN-1-18",
            word_position_start=5,
            word_position_end=6,
            base_text_reading="μονογενὴς θεός",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-01-A",
            variant_unit_id="VAR-JHN-1-18-01",
            reading_siglum="A",
            greek_or_hebrew_string="μονογενὴς θεός",
        )
        r2 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-01-B",
            variant_unit_id="VAR-JHN-1-18-01",
            reading_siglum="B",
            greek_or_hebrew_string="ὁ μονογενὴς υἱός",
        )
        att = WitnessAttestationDefinition(
            attestation_id="ATT-01",
            reading_id="READ-JHN-1-18-01-A",
            witness_id="MS-NONEXISTENT-99",
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-01",
            variant_unit_id="VAR-JHN-1-18-01",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="READ-JHN-1-18-01-A",
            confidence_score=0.85,
        )

        with self.assertRaises(WitnessNotFoundError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-01",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 5. UNVERIFIED EXTERNAL IDENTIFIER PRESERVED
    # -------------------------------------------------------------------------
    def test_05_unverified_external_identifier_preserved(self) -> None:
        """External manuscript identifiers that are not certified remain UNVERIFIED."""
        w = WitnessDefinition(
            witness_id="MS-P66",
            siglum="P66",
            name="Papyrus Bodmer II",
            witness_type=WitnessType.PAPYRUS,
            language="GREEK",
            century_origin="II-III CE",
            external_identifier="LDAB 2777",
            identifier_system="LDAB",
            identifier_status=IdentifierStatus.UNVERIFIED,
            textual_family=TextualFamily.ALEXANDRIAN,
        )
        wid = self.tc_manager.register_witness(w)
        self.assertEqual(wid, "MS-P66")

        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT identifier_status, identifier_system FROM witness_metadata_v2 WHERE witness_id = 'MS-P66'"
            )
            row = cursor.fetchone()
            self.assertEqual(row[0], "UNVERIFIED")
            self.assertEqual(row[1], "LDAB")

    # -------------------------------------------------------------------------
    # 6. COMPETING READINGS PRESERVED (NO SUPPRESSION)
    # -------------------------------------------------------------------------
    def test_06_competing_readings_preserved(self) -> None:
        """A variant unit with fewer than 2 competing readings raises suppression firewall error."""
        unit = VariantUnitDefinition(
            variant_unit_id="VAR-JHN-1-18-02",
            passage_id="PAS-JHN-1-18",
            word_position_start=5,
            word_position_end=6,
            base_text_reading="μονογενὴς θεός",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-02-A",
            variant_unit_id="VAR-JHN-1-18-02",
            reading_siglum="A",
            greek_or_hebrew_string="μονογενὴς θεός",
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-02",
            variant_unit_id="VAR-JHN-1-18-02",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="READ-JHN-1-18-02-A",
        )

        with self.assertRaises(SuppressionOfAlternativeReadingsFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-02",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1],
                attestations=[],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 7. PREFERRED != CERTAIN ORIGINAL
    # -------------------------------------------------------------------------
    def test_07_preferred_not_certain_original(self) -> None:
        """Marking a PREFERRED reading as CERTAIN_ORIGINAL is strictly prohibited."""
        w1 = WitnessDefinition(
            witness_id="MS-ALEPH", siglum="א", name="Codex Sinaiticus",
            witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="IV CE"
        )
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(
            variant_unit_id="VAR-JHN-1-18-03",
            passage_id="PAS-JHN-1-18",
            word_position_start=5,
            word_position_end=6,
            base_text_reading="μονογενὴς θεός",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(
            reading_id="READ-03-A", variant_unit_id="VAR-JHN-1-18-03",
            reading_siglum="A", greek_or_hebrew_string="μονογενὴς θεός"
        )
        r2 = VariantReadingDefinition(
            reading_id="READ-03-B", variant_unit_id="VAR-JHN-1-18-03",
            reading_siglum="B", greek_or_hebrew_string="ὁ μονογενὴς υἱός"
        )
        att = WitnessAttestationDefinition(
            attestation_id="ATT-03", reading_id="READ-03-A", witness_id="MS-ALEPH"
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-03",
            variant_unit_id="VAR-JHN-1-18-03",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="READ-03-A",
            is_certain_original=True,
        )

        with self.assertRaises(PreferredAsCertainOriginalFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-03",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 8. CONFIDENCE CANNOT UPGRADE DECISION TO CERTAIN ORIGINAL
    # -------------------------------------------------------------------------
    def test_08_confidence_cannot_upgrade_to_certain_original(self) -> None:
        """High statistical confidence score cannot upgrade decision to certain original."""
        w1 = WitnessDefinition(
            witness_id="MS-B-CONF", siglum="B-conf", name="Codex Vaticanus",
            witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="IV CE"
        )
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(
            variant_unit_id="VAR-CONF-01", passage_id="PAS-JHN-1-18",
            word_position_start=5, word_position_end=6, base_text_reading="word",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(reading_id="R-CONF-A", variant_unit_id="VAR-CONF-01", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-CONF-B", variant_unit_id="VAR-CONF-01", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-CONF", reading_id="R-CONF-A", witness_id="MS-B-CONF")

        dec = TextualDecisionDefinition(
            decision_id="DEC-CONF-01",
            variant_unit_id="VAR-CONF-01",
            decision_state=TextualDecisionState.POSSIBLE,
            preferred_reading_id="R-CONF-A",
            confidence_score=0.99,
            is_certain_original=True,
        )

        with self.assertRaises(ConfidenceTextualUpgradeFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-CONF",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 9. LECTIO DIFFICILIOR NOT AUTOMATIC PRIORITY
    # -------------------------------------------------------------------------
    def test_09_lectio_difficilior_not_automatic_priority(self) -> None:
        """Asserting lectio difficilior as an automatic truth formula raises firewall error."""
        w1 = WitnessDefinition(
            witness_id="MS-B", siglum="B", name="Codex Vaticanus",
            witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="IV CE"
        )
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(
            variant_unit_id="VAR-04", passage_id="PAS-JHN-1-18",
            word_position_start=5, word_position_end=6, base_text_reading="μονογενὴς θεός",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(reading_id="R-04-A", variant_unit_id="VAR-04", reading_siglum="A", greek_or_hebrew_string="θεός")
        r2 = VariantReadingDefinition(reading_id="R-04-B", variant_unit_id="VAR-04", reading_siglum="B", greek_or_hebrew_string="υἱός")
        att = WitnessAttestationDefinition(attestation_id="ATT-04", reading_id="R-04-A", witness_id="MS-B")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-04",
            reading_id="R-04-A",
            evidence_type=EvidenceType.INTERNAL,
            criterion=MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_DIFFICILIOR,
            observation_value="θεός is the more difficult reading",
            is_automatic_priority=True,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-04",
            variant_unit_id="VAR-04",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-04-A",
            observations=[obs],
        )

        with self.assertRaises(LectioDifficiliorPriorityFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-04",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 10. LECTIO BREVIOR NOT AUTOMATIC PRIORITY
    # -------------------------------------------------------------------------
    def test_10_lectio_brevior_not_automatic_priority(self) -> None:
        """Asserting lectio brevior as automatic priority raises firewall error."""
        w1 = WitnessDefinition(
            witness_id="MS-W", siglum="W", name="Codex Washingtonianus",
            witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="IV-V CE"
        )
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(
            variant_unit_id="VAR-05", passage_id="PAS-JHN-1-18",
            word_position_start=5, word_position_end=6, base_text_reading="θεός",
            pericope_id="PER-JHN-1",
        )
        r1 = VariantReadingDefinition(reading_id="R-05-A", variant_unit_id="VAR-05", reading_siglum="A", greek_or_hebrew_string="θεός")
        r2 = VariantReadingDefinition(reading_id="R-05-B", variant_unit_id="VAR-05", reading_siglum="B", greek_or_hebrew_string="ὁ μονογενὴς θεός")
        att = WitnessAttestationDefinition(attestation_id="ATT-05", reading_id="R-05-A", witness_id="MS-W")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-05",
            reading_id="R-05-A",
            evidence_type=EvidenceType.INTERNAL,
            criterion=MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_BREVIOR,
            observation_value="Shorter reading",
            is_automatic_priority=True,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-05",
            variant_unit_id="VAR-05",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-05-A",
            observations=[obs],
        )

        with self.assertRaises(LectioBreviorPriorityFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-05",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

    # -------------------------------------------------------------------------
    # 11. WITNESS COUNT NOT AUTOMATIC PRIORITY
    # -------------------------------------------------------------------------
    def test_11_witness_count_not_automatic_priority(self) -> None:
        """Witness count alone cannot determine textual priority."""
        w1 = WitnessDefinition(witness_id="MS-C", siglum="C", name="Codex Ephraemi", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="V CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-06", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-06-A", variant_unit_id="VAR-06", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-06-B", variant_unit_id="VAR-06", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-06", reading_id="R-06-A", witness_id="MS-C")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-06",
            reading_id="R-06-A",
            evidence_type=EvidenceType.EXTERNAL,
            criterion=MethodologyCriterion.EXTERNAL_WITNESS_ATTESTATION,
            observation_value="Supported by 500 minuscules",
            is_automatic_priority=True,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-06", variant_unit_id="VAR-06", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-06-A", observations=[obs]
        )

        with self.assertRaises(WitnessCountPriorityFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-06", passage_id="PAS-JHN-1-18",
                variant_units=[unit], variant_readings=[r1, r2],
                attestations=[att], decisions=[dec]
            )

    # -------------------------------------------------------------------------
    # 12. WITNESS AGE NOT AUTOMATIC PRIORITY
    # -------------------------------------------------------------------------
    def test_12_witness_age_not_automatic_priority(self) -> None:
        """Witness age alone cannot determine textual priority."""
        w1 = WitnessDefinition(witness_id="MS-P75", siglum="P75", name="Papyrus Bodmer XIV-XV", witness_type=WitnessType.PAPYRUS, language="GREEK", century_origin="III CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-07", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-07-A", variant_unit_id="VAR-07", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-07-B", variant_unit_id="VAR-07", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-07", reading_id="R-07-A", witness_id="MS-P75")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-07",
            reading_id="R-07-A",
            evidence_type=EvidenceType.EXTERNAL,
            criterion=MethodologyCriterion.EXTERNAL_WITNESS_DATE,
            observation_value="Oldest papyrus",
            is_automatic_priority=True,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-07", variant_unit_id="VAR-07", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-07-A", observations=[obs]
        )

        with self.assertRaises(WitnessAgePriorityFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-07", passage_id="PAS-JHN-1-18",
                variant_units=[unit], variant_readings=[r1, r2],
                attestations=[att], decisions=[dec]
            )

    # -------------------------------------------------------------------------
    # 13. TEXTUAL FAMILY NOT AUTOMATIC PRIORITY
    # -------------------------------------------------------------------------
    def test_13_textual_family_not_automatic_priority(self) -> None:
        """Textual family alone cannot determine textual priority."""
        w1 = WitnessDefinition(witness_id="MS-D", siglum="D", name="Codex Bezae", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="V CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-08", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-08-A", variant_unit_id="VAR-08", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-08-B", variant_unit_id="VAR-08", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-08", reading_id="R-08-A", witness_id="MS-D")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-08",
            reading_id="R-08-A",
            evidence_type=EvidenceType.EXTERNAL,
            criterion=MethodologyCriterion.EXTERNAL_TEXTUAL_FAMILY,
            observation_value="Alexandrian family reading",
            is_automatic_priority=True,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-08", variant_unit_id="VAR-08", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-08-A", observations=[obs]
        )

        with self.assertRaises(TextualFamilyPriorityFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-08", passage_id="PAS-JHN-1-18",
                variant_units=[unit], variant_readings=[r1, r2],
                attestations=[att], decisions=[dec]
            )

    # -------------------------------------------------------------------------
    # 14. EXTERNAL/INTERNAL CRITERION MISMATCH REJECTED
    # -------------------------------------------------------------------------
    def test_14_external_internal_criterion_mismatch(self) -> None:
        """Mismatching evidence_type with criterion raises an epistemic error."""
        w1 = WitnessDefinition(witness_id="MS-MIS", siglum="MIS", name="Codex Mismatch", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="V CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-MIS", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-MIS-A", variant_unit_id="VAR-MIS", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-MIS-B", variant_unit_id="VAR-MIS", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-MIS", reading_id="R-MIS-A", witness_id="MS-MIS")

        # Marked EXTERNAL but criterion is internal lectio difficilior
        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-MIS",
            reading_id="R-MIS-A",
            evidence_type=EvidenceType.EXTERNAL,  # MISMATCH
            criterion=MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_DIFFICILIOR,
            observation_value="Mismatched type test",
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-MIS", variant_unit_id="VAR-MIS", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-MIS-A", observations=[obs]
        )

        with self.assertRaises(TextualCriticismSubsystemError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-MIS", passage_id="PAS-JHN-1-18",
                variant_units=[unit], variant_readings=[r1, r2],
                attestations=[att], decisions=[dec]
            )

    # -------------------------------------------------------------------------
    # 15. EVIDENCE INTEGRATION & IMMUTABILITY
    # -------------------------------------------------------------------------
    def test_15_evidence_integration_and_immutability(self) -> None:
        """A valid run registers E1 evidence and triggers block unauthorized mutations."""
        w1 = WitnessDefinition(witness_id="MS-A", siglum="A", name="Codex Alexandrinus", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="V CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-09", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-09-A", variant_unit_id="VAR-09", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-09-B", variant_unit_id="VAR-09", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-09", reading_id="R-09-A", witness_id="MS-A")

        obs = TextualCriterionObservationDefinition(
            observation_id="OBS-09",
            reading_id="R-09-A",
            evidence_type=EvidenceType.EXTERNAL,
            criterion=MethodologyCriterion.EXTERNAL_WITNESS_ATTESTATION,
            observation_value="Attested in Codex Alexandrinus",
            evaluation_score=0.8,
            is_automatic_priority=False,
        )
        dec = TextualDecisionDefinition(
            decision_id="DEC-09",
            variant_unit_id="VAR-09",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-09-A",
            confidence_score=0.75,
            is_certain_original=False,
            reasoning="Balanced external and internal evidence supports reading A.",
            observations=[obs],
        )

        res = self.tc_manager.execute_run(
            run_id="RUN-TC-09",
            passage_id="PAS-JHN-1-18",
            variant_units=[unit],
            variant_readings=[r1, r2],
            attestations=[att],
            decisions=[dec],
        )

        self.assertEqual(res.status, "COMPLETED")
        self.assertTrue(len(res.evidence_ids) > 0)

        # Verify evidence_ledger record
        with self.engine.transaction() as conn:
            cursor = conn.execute(
                "SELECT evidence_class, epistemic_tier, confidence FROM evidence_ledger WHERE evidence_id = ?",
                (res.evidence_ids[0],),
            )
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "E1_TEXTUAL_MANUSCRIPT")
            self.assertEqual(row[1], "T1_LINGUISTIC_FACT")
            self.assertEqual(row[2], "HIGH")

            # Verify variant_unit_executions has populated evidence_id
            cursor_vue = conn.execute(
                "SELECT evidence_id FROM variant_unit_executions WHERE variant_unit_id = 'VAR-09'"
            )
            vue_row = cursor_vue.fetchone()
            self.assertIsNotNone(vue_row)
            self.assertEqual(vue_row[0], res.evidence_ids[0])

            # Verify immutability trigger blocks unauthorized update
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE textual_criticism_runs SET analyzer_id = 'HACKED' WHERE run_id = 'RUN-TC-09'"
                )

            # Verify immutability trigger blocks delete
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "DELETE FROM textual_decisions WHERE decision_id = 'DEC-09'"
                )

    # -------------------------------------------------------------------------
    # 16. ROLLBACK INTEGRITY
    # -------------------------------------------------------------------------
    def test_16_rollback_integrity(self) -> None:
        """Failure during execution leaves zero orphaned records in the database."""
        w1 = WitnessDefinition(witness_id="MS-L", siglum="L", name="Codex Regius", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="VIII CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-10", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="test", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-10-A", variant_unit_id="VAR-10", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-10-B", variant_unit_id="VAR-10", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-10", reading_id="R-10-A", witness_id="MS-L")

        dec = TextualDecisionDefinition(
            decision_id="DEC-10",
            variant_unit_id="VAR-10",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-10-A",
            is_certain_original=True,
        )

        with self.assertRaises(PreferredAsCertainOriginalFirewallError):
            self.tc_manager.execute_run(
                run_id="RUN-TC-10",
                passage_id="PAS-JHN-1-18",
                variant_units=[unit],
                variant_readings=[r1, r2],
                attestations=[att],
                decisions=[dec],
            )

        # Verify nothing was persisted
        with self.engine.transaction() as conn:
            cursor = conn.execute("SELECT 1 FROM textual_criticism_runs WHERE run_id = 'RUN-TC-10'")
            self.assertIsNone(cursor.fetchone())
            cursor = conn.execute("SELECT 1 FROM textual_decisions WHERE decision_id = 'DEC-10'")
            self.assertIsNone(cursor.fetchone())

    # -------------------------------------------------------------------------
    # 17. CONCURRENCY SAFETY
    # -------------------------------------------------------------------------
    def test_17_concurrency_safety(self) -> None:
        """Parallel read/write operations execute safely without database corruption."""
        for i in range(5):
            w = WitnessDefinition(
                witness_id=f"MS-CONC-{i}",
                siglum=f"C{i}",
                name=f"Codex Concurrency {i}",
                witness_type=WitnessType.MINUSCULE,
                language="GREEK",
                century_origin="X CE",
            )
            self.tc_manager.register_witness(w)

        def worker(idx: int) -> str:
            thread_engine = DatabaseEngine(self.config)
            try:
                thread_tc = TextualCriticismManager(thread_engine)
                unit = VariantUnitDefinition(
                    variant_unit_id=f"VAR-CONC-{idx}",
                    passage_id="PAS-JHN-1-18",
                    word_position_start=1,
                    word_position_end=2,
                    base_text_reading="word",
                    pericope_id="PER-JHN-1",
                )
                r1 = VariantReadingDefinition(reading_id=f"R-C-{idx}-A", variant_unit_id=f"VAR-CONC-{idx}", reading_siglum="A", greek_or_hebrew_string="A")
                r2 = VariantReadingDefinition(reading_id=f"R-C-{idx}-B", variant_unit_id=f"VAR-CONC-{idx}", reading_siglum="B", greek_or_hebrew_string="B")
                att = WitnessAttestationDefinition(attestation_id=f"ATT-C-{idx}", reading_id=f"R-C-{idx}-A", witness_id=f"MS-CONC-{idx % 5}")
                dec = TextualDecisionDefinition(
                    decision_id=f"DEC-C-{idx}",
                    variant_unit_id=f"VAR-CONC-{idx}",
                    decision_state=TextualDecisionState.POSSIBLE,
                    preferred_reading_id=f"R-C-{idx}-A",
                    confidence_score=0.6,
                )
                res = thread_tc.execute_run(
                    run_id=f"RUN-C-{idx}",
                    passage_id="PAS-JHN-1-18",
                    variant_units=[unit],
                    variant_readings=[r1, r2],
                    attestations=[att],
                    decisions=[dec],
                )
                return res.run_id
            finally:
                thread_engine.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 10)

    # -------------------------------------------------------------------------
    # 18. VERSION SUPERSESSION
    # -------------------------------------------------------------------------
    def test_18_version_supersession(self) -> None:
        """Re-analyzing a passage marks the previous completed run as SUPERSEDED."""
        w1 = WitnessDefinition(witness_id="MS-SUP", siglum="SUP", name="Codex Supersession", witness_type=WitnessType.UNCIAL, language="GREEK", century_origin="IV CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-SUP", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="A", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-SUP-A", variant_unit_id="VAR-SUP", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-SUP-B", variant_unit_id="VAR-SUP", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-SUP", reading_id="R-SUP-A", witness_id="MS-SUP")

        dec1 = TextualDecisionDefinition(
            decision_id="DEC-SUP-1", variant_unit_id="VAR-SUP", decision_state=TextualDecisionState.POSSIBLE,
            preferred_reading_id="R-SUP-A", confidence_score=0.5
        )
        res1 = self.tc_manager.execute_run(
            run_id="RUN-TC-SUP-1", passage_id="PAS-JHN-1-18",
            variant_units=[unit], variant_readings=[r1, r2], attestations=[att], decisions=[dec1]
        )
        self.assertEqual(res1.status, "COMPLETED")

        # Run 2 on same passage
        dec2 = TextualDecisionDefinition(
            decision_id="DEC-SUP-2", variant_unit_id="VAR-SUP", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-SUP-A", confidence_score=0.8
        )
        res2 = self.tc_manager.execute_run(
            run_id="RUN-TC-SUP-2", passage_id="PAS-JHN-1-18",
            variant_units=[unit], variant_readings=[r1, r2], attestations=[att], decisions=[dec2]
        )
        self.assertEqual(res2.status, "COMPLETED")

        # Verify run 1 is now SUPERSEDED
        run1_data = self.tc_manager.get_run("RUN-TC-SUP-1")
        self.assertIsNotNone(run1_data)
        self.assertEqual(run1_data["status"], "SUPERSEDED")

        run2_data = self.tc_manager.get_run("RUN-TC-SUP-2")
        self.assertIsNotNone(run2_data)
        self.assertEqual(run2_data["status"], "COMPLETED")

    # -------------------------------------------------------------------------
    # 19. PROVENANCE CHAIN INTEGRITY
    # -------------------------------------------------------------------------
    def test_19_provenance_chain_integrity(self) -> None:
        """Every executed run creates valid, cryptographic provenance chain records."""
        w1 = WitnessDefinition(witness_id="MS-PROV", siglum="PRV", name="Codex Provenance", witness_type=WitnessType.PAPYRUS, language="GREEK", century_origin="III CE")
        self.tc_manager.register_witness(w1)

        unit = VariantUnitDefinition(variant_unit_id="VAR-PROV", passage_id="PAS-JHN-1-18", word_position_start=1, word_position_end=2, base_text_reading="A", pericope_id="PER-JHN-1")
        r1 = VariantReadingDefinition(reading_id="R-PROV-A", variant_unit_id="VAR-PROV", reading_siglum="A", greek_or_hebrew_string="A")
        r2 = VariantReadingDefinition(reading_id="R-PROV-B", variant_unit_id="VAR-PROV", reading_siglum="B", greek_or_hebrew_string="B")
        att = WitnessAttestationDefinition(attestation_id="ATT-PROV", reading_id="R-PROV-A", witness_id="MS-PROV")

        dec = TextualDecisionDefinition(
            decision_id="DEC-PROV", variant_unit_id="VAR-PROV", decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="R-PROV-A", confidence_score=0.7
        )
        res = self.tc_manager.execute_run(
            run_id="RUN-TC-PROV", passage_id="PAS-JHN-1-18",
            variant_units=[unit], variant_readings=[r1, r2], attestations=[att], decisions=[dec]
        )

        # Verify provenance record directly
        prov_record = self.provenance_tracker.get_record_by_target(TargetType.DERIVED_ARTIFACT, "RUN-TC-PROV")
        self.assertIsNotNone(prov_record)
        self.assertEqual(prov_record.target_id, "RUN-TC-PROV")
        self.assertTrue(len(prov_record.output_hash) == 64)

        # Verify chain integrity passes
        integrity = self.provenance_tracker.verify_chain_integrity(prov_record.provenance_id)
        self.assertTrue(integrity.is_valid)

    # -------------------------------------------------------------------------
    # 20. MIGRATION INTEGRITY
    # -------------------------------------------------------------------------
    def test_20_migration_checksums_001_to_013_unchanged(self) -> None:
        """Migrations 001-013 must strictly match golden baseline checksums."""
        migrations_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for filename, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            file_path = migrations_dir / filename
            self.assertTrue(file_path.exists(), f"Missing migration file: {filename}")
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Migration altered: {filename}! Expected {expected_hash}, got {actual_hash}",
            )

        # Migration 014 exists and is readable
        m014 = migrations_dir / "014_textual_criticism.sql"
        self.assertTrue(m014.exists())
        self.assertTrue(len(m014.read_bytes()) > 0)

    # -------------------------------------------------------------------------
    # 21. LEGACY DB INTEGRITY
    # -------------------------------------------------------------------------
    def test_21_legacy_db_sha256_unaltered(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain unaltered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_sha, LEGACY_DB_SHA256, "Legacy database altered!")

    # -------------------------------------------------------------------------
    # 22. REALISTIC MULTI-READING VARIANT UNIT PIPELINE (Yohanes 1:18)
    # -------------------------------------------------------------------------
    def test_22_realistic_multi_reading_variant_pipeline(self) -> None:
        """
        Complete realistic textual criticism pipeline for Yohanes 1:18:
          Unit: μονογενὴς θεός vs ὁ μονογενὴς υἱός vs ὁ μονογενὴς θεός
          Witnesses: P66, P75, א, B, C*, L (Alexandrian); A, C3, K, W (Byzantine/Western)
          Criteria: External witness distribution + Transcriptional (lectio difficilior) + Intrinsic (Johannine style)
          Output: Calibrated decision, preferred != certain original, competing readings preserved, E1 evidence linked.
        """
        # 1. Register Primary Witnesses
        witnesses_data = [
            ("MS-P66-REAL", "P66", "Papyrus Bodmer II", WitnessType.PAPYRUS, "II-III CE", TextualFamily.ALEXANDRIAN),
            ("MS-P75-REAL", "P75", "Papyrus Bodmer XIV-XV", WitnessType.PAPYRUS, "III CE", TextualFamily.ALEXANDRIAN),
            ("MS-ALEPH-REAL", "א", "Codex Sinaiticus", WitnessType.UNCIAL, "IV CE", TextualFamily.ALEXANDRIAN),
            ("MS-B-REAL", "B", "Codex Vaticanus", WitnessType.UNCIAL, "IV CE", TextualFamily.ALEXANDRIAN),
            ("MS-A-REAL", "A", "Codex Alexandrinus", WitnessType.UNCIAL, "V CE", TextualFamily.BYZANTINE),
            ("MS-C-REAL", "C", "Codex Ephraemi Rescriptus", WitnessType.UNCIAL, "V CE", TextualFamily.ALEXANDRIAN),
            ("MS-W-REAL", "W", "Codex Washingtonianus", WitnessType.UNCIAL, "IV-V CE", TextualFamily.WESTERN),
        ]
        for wid, sig, name, wtype, cent, fam in witnesses_data:
            self.tc_manager.register_witness(
                WitnessDefinition(
                    witness_id=wid,
                    siglum=sig,
                    name=name,
                    witness_type=wtype,
                    language="GREEK",
                    century_origin=cent,
                    textual_family=fam,
                    identifier_system="GREGORY_ALAND",
                    identifier_status=IdentifierStatus.VERIFIED,
                )
            )

        # 2. Define Variant Unit
        unit = VariantUnitDefinition(
            variant_unit_id="VAR-JHN-1-18-REAL",
            passage_id="PAS-JHN-1-18",
            word_position_start=5,
            word_position_end=6,
            base_text_reading="μονογενὴς θεός",
            critical_significance=CriticalSignificance.HIGH,
            editorial_status=EditorialStatus.PROBABLE,
            notes="Major Christological variant unit in the Prologue of John",
            pericope_id="PER-JHN-1",
        )

        # 3. Define Competing Readings
        r1 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-A",
            variant_unit_id="VAR-JHN-1-18-REAL",
            reading_siglum="Reading 1 (NA28 Preferred)",
            greek_or_hebrew_string="μονογενὴς θεός",
            external_evidence_summary="P66, P75, א*, B, C*, L",
            internal_evidence_evaluation="Lectio difficilior praeferenda est; scribes more likely to harmonize with υἱός",
            reading_category=ReadingCategory.ORIGINAL_PREFERRED,
            reading_confidence=ReadingConfidence.VERY_HIGH,
        )
        r2 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-B",
            variant_unit_id="VAR-JHN-1-18-REAL",
            reading_siglum="Reading 2 (Majority/Byzantine)",
            greek_or_hebrew_string="ὁ μονογενὴς υἱός",
            external_evidence_summary="A, C3, K, W, Byzantine tradition",
            internal_evidence_evaluation="Conforms to standard Johannine terminology (John 3:16, 3:18, 1 John 4:9)",
            reading_category=ReadingCategory.MAJORITY_READING,
            reading_confidence=ReadingConfidence.HIGH,
        )
        r3 = VariantReadingDefinition(
            reading_id="READ-JHN-1-18-C",
            variant_unit_id="VAR-JHN-1-18-REAL",
            reading_siglum="Reading 3 (Composite/Article)",
            greek_or_hebrew_string="ὁ μονογενὴς θεός",
            external_evidence_summary="אc, 33",
            internal_evidence_evaluation="Secondary grammatical smoothing adding the definite article",
            reading_category=ReadingCategory.EARLY_CORRECTION,
            reading_confidence=ReadingConfidence.MEDIUM,
        )

        # 4. Attestations
        attestations = [
            WitnessAttestationDefinition("ATT-REAL-01", "READ-JHN-1-18-A", "MS-P66-REAL"),
            WitnessAttestationDefinition("ATT-REAL-02", "READ-JHN-1-18-A", "MS-P75-REAL"),
            WitnessAttestationDefinition("ATT-REAL-03", "READ-JHN-1-18-A", "MS-ALEPH-REAL"),
            WitnessAttestationDefinition("ATT-REAL-04", "READ-JHN-1-18-A", "MS-B-REAL"),
            WitnessAttestationDefinition("ATT-REAL-05", "READ-JHN-1-18-A", "MS-C-REAL"),
            WitnessAttestationDefinition("ATT-REAL-06", "READ-JHN-1-18-B", "MS-A-REAL"),
            WitnessAttestationDefinition("ATT-REAL-07", "READ-JHN-1-18-B", "MS-W-REAL"),
            WitnessAttestationDefinition("ATT-REAL-08", "READ-JHN-1-18-C", "MS-ALEPH-REAL", is_correction=True),
        ]

        # 5. Methodological Observations
        obs1 = TextualCriterionObservationDefinition(
            observation_id="OBS-REAL-01",
            reading_id="READ-JHN-1-18-A",
            evidence_type=EvidenceType.EXTERNAL,
            criterion=MethodologyCriterion.EXTERNAL_WITNESS_DATE,
            observation_value="Attested by earliest extant papyri (P66, P75) and primary 4th century uncials (א, B)",
            evaluation_score=0.9,
            is_automatic_priority=False,
        )
        obs2 = TextualCriterionObservationDefinition(
            observation_id="OBS-REAL-02",
            reading_id="READ-JHN-1-18-A",
            evidence_type=EvidenceType.INTERNAL,
            criterion=MethodologyCriterion.TRANSCRIPTIONAL_LECTIO_DIFFICILIOR,
            observation_value="θεός is the more difficult reading; scribes naturally harmonized to υἱός based on Johannine usage",
            evaluation_score=0.85,
            is_automatic_priority=False,
        )
        obs3 = TextualCriterionObservationDefinition(
            observation_id="OBS-REAL-03",
            reading_id="READ-JHN-1-18-B",
            evidence_type=EvidenceType.INTERNAL,
            criterion=MethodologyCriterion.INTRINSIC_AUTHORIAL_VOCABULARY,
            observation_value="ὁ μονογενὴς υἱός aligns with authorial terminology elsewhere in Johannine corpus",
            evaluation_score=0.75,
            is_automatic_priority=False,
        )

        # 6. Textual Decision
        dec = TextualDecisionDefinition(
            decision_id="DEC-JHN-1-18-REAL",
            variant_unit_id="VAR-JHN-1-18-REAL",
            decision_state=TextualDecisionState.PREFERRED,
            preferred_reading_id="READ-JHN-1-18-A",
            confidence_score=0.85,
            is_certain_original=False,
            competing_readings_preserved=True,
            external_evidence_summary="P66, P75, א*, B strongly support Reading A (Alexandrian); A, W support Reading B.",
            internal_evidence_summary="Transcriptional probability heavily favors Reading A (harder reading). Intrinsic probability divided.",
            reasoning="Reading 1 (μονογενὴς θεός) is preferred based on weight of earliest witnesses and scribal tendency to smooth difficult phrase.",
            observations=[obs1, obs2, obs3],
        )

        # 7. Execute Run
        res = self.tc_manager.execute_run(
            run_id="RUN-TC-JHN-1-18",
            passage_id="PAS-JHN-1-18",
            variant_units=[unit],
            variant_readings=[r1, r2, r3],
            attestations=attestations,
            decisions=[dec],
            pericope_id="PER-JHN-1",
        )

        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.competing_readings_count, 3)
        self.assertEqual(len(res.decision_ids), 1)
        self.assertEqual(len(res.evidence_ids), 1)

        # Verify DB records
        decisions_db = self.tc_manager.get_decisions_for_variant("VAR-JHN-1-18-REAL")
        self.assertEqual(len(decisions_db), 1)
        self.assertEqual(decisions_db[0]["decision_state"], "PREFERRED")
        self.assertEqual(decisions_db[0]["is_certain_original"], 0)
        self.assertEqual(decisions_db[0]["competing_readings_count"], 3)
        self.assertEqual(decisions_db[0]["competing_readings_preserved"], 1)

        # Verify attestations
        att_db = self.tc_manager.get_attestations_for_reading("READ-JHN-1-18-A")
        self.assertEqual(len(att_db), 5)
        sigla = {a["siglum"] for a in att_db}
        self.assertTrue({"P66", "P75", "א", "B", "C"}.issubset(sigla))


if __name__ == "__main__":
    unittest.main()
