"""
Unit and Adversarial Test Suite for Historical-Linguistic & Diachronic Engine (Task 3.2).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Greek, Hebrew, and Aramaic linguistic strata separation
  2. Uncertain period preserved without forcing categorization
  3. Lexical similarity != borrowing firewall
  4. Shared root != causal relation / same historical source firewall
  5. Chronological proximity != causation firewall
  6. Borrowing requires evidence firewall
  7. Disputed etymology preserved
  8. Rejected etymology preserved
  9. Parallel != intertextuality firewall (E9 parallel cannot become E10)
  10. Translation cannot become historical-linguistic source evidence
  11. AI output cannot become primary historical evidence
  12. Provenance required and verifiable
  13. Version supersession on reanalysis
  14. Immutability enforced by SQL triggers
  15. Rollback on failure leaves zero orphaned rows
  16. Concurrency safety under multithreaded writers
  17. Migration 001-014 checksums unchanged
  18. Legacy DB unchanged
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
    AIHistoricalEvidenceFirewallError,
    BorrowingEvidenceRequiredFirewallError,
    ChronologicalProximityNotCausationFirewallError,
    HistoricalLinguisticImmutabilityError,
    HistoricalLinguisticSubsystemError,
    LaterFormEarlierReadingFirewallError,
    LexicalSimilarityNotBorrowingFirewallError,
    LexicalSimilarityNotCausationFirewallError,
    ModernTerminologyAuthorialIntentFirewallError,
    ParallelNotIntertextualFirewallError,
    SharedRootNotSameSourceFirewallError,
    TranslationHistoricalSourceFirewallError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceDefinition,
    EvidenceStatus,
)
from bible_engine.historical_linguistics import (
    AramaicPeriod,
    BorrowingState,
    BorrowingType,
    DiachronicAnnotationDefinition,
    DiachronicStratumDefinition,
    EpigraphicParallelDefinition,
    EtymologicalRelationDefinition,
    EtymologicalRelationshipType,
    EvidenceScope,
    GreekPeriod,
    HebrewPeriod,
    HistoricalLinguisticManager,
    HistoricalObservationDefinition,
    IdentifierVerificationStatus,
    LanguageCode,
    LoanwordDefinition,
    ObservationScope,
    ParallelCorpusType,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
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
    "014_textual_criticism.sql": "2ceec0c7e59d43998e279d2f7712b961747199b688cbee2c21b0347fe9ac0d41",
}

LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestHistoricalLinguisticEngine(unittest.TestCase):
    """Test suite verifying all Task 3.2 historical-linguistic requirements and firewalls."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_hist_ling.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.evidence_claim_manager = EvidenceClaimManager(self.engine)
        self.hl_manager = HistoricalLinguisticManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
            self.evidence_claim_manager,
        )
        self.hl_manager.seed_canonical_strata()

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('OT', 'CAN-PROT', 'Perjanjian Lama', 1);")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute("INSERT INTO books VALUES ('DAN', 'OT', 27, 'Daniel', 'Daniel', 'ARAMAIC', 12);")
            conn.execute("INSERT INTO books VALUES ('JHN', 'NT', 43, 'Yohanes', 'John', 'GREEK', 21);")
            conn.execute("INSERT INTO books VALUES ('GEN', 'OT', 1, 'Kejadian', 'Genesis', 'HEBREW', 50);")
            conn.execute(
                """
                INSERT INTO pericopes VALUES (
                    'PER-DAN-2', 'DAN', 'Daniel 2:20-23', 2, 20, 2, 23,
                    'DOXOLOGY', 'BHS_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-DAN-2-20', 'PER-DAN-2', 'DAN', 2, 20, 1);
                """
            )
            # Seed evidence entry in evidence_ledger
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class,
                    epistemic_tier, source_reference, extracted_text_or_data,
                    status, confidence, confidence_score, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV-HIST-SEED-01', 'PER-DAN-2', 'PAS-DAN-2-20', 'E9_HISTORICAL_LINGUISTIC',
                    'T1_LINGUISTIC_FACT', 'Official Aramaic in Daniel 2:20', 'שם אלהא מברך',
                    '[EXPLICIT]', 'HIGH', 0.9, '2026-10-01T00:00:00Z', 'hash123', 1
                );
                """
            )

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. GREEK / HEBREW / ARAMAIC SEPARATION
    # -------------------------------------------------------------------------
    def test_01_language_separation_and_canonical_strata(self) -> None:
        """Greek, Hebrew, and Aramaic strata exist independently with strict separation."""
        with self.engine.transaction() as conn:
            greek_count = conn.execute("SELECT COUNT(*) FROM diachronic_strata WHERE language = 'GREEK'").fetchone()[0]
            hebrew_count = conn.execute("SELECT COUNT(*) FROM diachronic_strata WHERE language = 'HEBREW'").fetchone()[0]
            aramaic_count = conn.execute("SELECT COUNT(*) FROM diachronic_strata WHERE language = 'ARAMAIC'").fetchone()[0]

            self.assertGreaterEqual(greek_count, 5)
            self.assertGreaterEqual(hebrew_count, 6)
            self.assertGreaterEqual(aramaic_count, 5)

            # Invalid language must fail DB check constraint
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO diachronic_strata (stratum_id, language, period_code, period_name, description, created_at)
                    VALUES ('STRAT-LAT', 'LATIN', 'CLASSICAL', 'Latin', 'Classical Latin', '2026-10-01T00:00:00Z')
                    """
                )

    # -------------------------------------------------------------------------
    # 2. UNCERTAIN PERIOD PRESERVED
    # -------------------------------------------------------------------------
    def test_02_uncertain_period_preserved(self) -> None:
        """Uncertain period is preserved explicitly without forcing period categorization."""
        ann = DiachronicAnnotationDefinition(
            annotation_id="ANN-UNCERTAIN-01",
            stratum_id="STRAT-ARM-UNKNOWN",
            classification_confidence="UNCERTAIN",
            linguistic_features="Morphological archaism vs later dialectal leveling disputed",
            is_period_uncertain=True,
            notes="Cannot be forced into Official vs Middle Aramaic on current evidence",
        )
        res = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-UNCERTAIN",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
            annotations=[ann],
        )
        self.assertEqual(res.annotations_count, 1)

        saved = self.hl_manager.get_annotations_for_run("RUN-HL-UNCERTAIN")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["classification_confidence"], "UNCERTAIN")
        self.assertEqual(saved[0]["is_period_uncertain"], 1)
        self.assertEqual(saved[0]["stratum_id"], "STRAT-ARM-UNKNOWN")

    # -------------------------------------------------------------------------
    # 3. LEXICAL SIMILARITY != BORROWING
    # -------------------------------------------------------------------------
    def test_03_lexical_similarity_not_borrowing(self) -> None:
        """Firewall: Lexical similarity alone cannot assert borrowing as ESTABLISHED."""
        # Unverified borrowing type asserted as ESTABLISHED based on resemblance
        lw = LoanwordDefinition(
            loanword_id="LW-SIM-01",
            source_language="PERSIAN",
            target_language="ARAMAIC",
            lexeme="פתגם",
            candidate_etymon="patigama",
            borrowing_type="UNVERIFIED",
            chronological_range="VI BCE",
            external_reference="Superficial resemblance to Old Persian",
            state=BorrowingState.ESTABLISHED.value,
            confidence=ConfidenceLevel.HIGH.value,
            confidence_score=0.85,
            evidence_id="EV-HIST-SEED-01",
        )
        with self.assertRaises(LexicalSimilarityNotBorrowingFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-SIM-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                loanwords=[lw],
            )

    # -------------------------------------------------------------------------
    # 4. SHARED ROOT != SAME HISTORICAL SOURCE / CAUSAL RELATION
    # -------------------------------------------------------------------------
    def test_04_shared_root_not_causal_relation_or_same_source(self) -> None:
        """Firewall: Shared root cannot assert same historical source or causal derivation."""
        ety = EtymologicalRelationDefinition(
            relation_id="ETY-FAIL-01",
            lexeme_text="שלם",
            target_language="HEBREW",
            related_lexeme_text="salimu",
            source_language="AKKADIAN",
            relationship_type=EtymologicalRelationshipType.SHARED_ROOT.value,
            state=BorrowingState.ESTABLISHED.value,
            reconstruction_method="Comparative Semitic",
            lexicon_source="HALOT",
            evidence_id="EV-HIST-SEED-01",
            is_same_historical_source=True,  # VIOLATION
        )
        with self.assertRaises(SharedRootNotSameSourceFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-ETY-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                etymologies=[ety],
            )

        # Spurious similarity asserting causal relation must also fail
        ety2 = EtymologicalRelationDefinition(
            relation_id="ETY-FAIL-02",
            lexeme_text="קול",
            target_language="HEBREW",
            related_lexeme_text="call",
            source_language="ENGLISH",
            relationship_type=EtymologicalRelationshipType.SPURIOUS_SIMILARITY.value,
            state=BorrowingState.PROPOSED.value,
            reconstruction_method="Superficial phonetic similarity",
            lexicon_source="Popular blog",
            evidence_id="EV-HIST-SEED-01",
            is_causal_relation=True,  # VIOLATION
        )
        with self.assertRaises(LexicalSimilarityNotCausationFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-ETY-FAIL2",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                etymologies=[ety2],
            )

    # -------------------------------------------------------------------------
    # 5. CHRONOLOGICAL PROXIMITY != CAUSATION
    # -------------------------------------------------------------------------
    def test_05_chronological_proximity_not_causation(self) -> None:
        """Firewall: Chronological proximity must not be asserted as causation."""
        obs = HistoricalObservationDefinition(
            observation_id="OBS-FAIL-01",
            passage_id="PAS-DAN-2-20",
            observation_scope=ObservationScope.PASSAGE.value,
            evidence_scope=EvidenceScope.EXTERNAL_HISTORICAL.value,
            observation_title="Proximity of Achaemenid inscriptions",
            observation_text="Achaemenid edicts occurred closely in time, therefore causing the Danielic syntax",
            evidence_id="EV-HIST-SEED-01",
            chronological_proximity_noted="539 BCE vs 536 BCE",
            asserts_historical_causation=True,  # VIOLATION
        )
        with self.assertRaises(ChronologicalProximityNotCausationFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-OBS-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                observations=[obs],
            )

    # -------------------------------------------------------------------------
    # 6. BORROWING REQUIRES EVIDENCE
    # -------------------------------------------------------------------------
    def test_06_borrowing_requires_evidence(self) -> None:
        """Firewall: Loanword borrowing requires valid evidence_id."""
        lw = LoanwordDefinition(
            loanword_id="LW-NO-EV",
            source_language="PERSIAN",
            target_language="ARAMAIC",
            lexeme="פתגם",
            candidate_etymon="patigama",
            borrowing_type=BorrowingType.DIRECT_LOAN.value,
            chronological_range="VI BCE",
            external_reference="BDB p. 1109",
            state=BorrowingState.PROBABLE.value,
            confidence=ConfidenceLevel.HIGH.value,
            confidence_score=0.8,
            evidence_id="",  # EMPTY VIOLATION
        )
        with self.assertRaises(BorrowingEvidenceRequiredFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-LW-NOEV",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                loanwords=[lw],
            )

    # -------------------------------------------------------------------------
    # 7. DISPUTED ETYMOLOGY PRESERVED
    # -------------------------------------------------------------------------
    def test_07_disputed_etymology_preserved(self) -> None:
        """Disputed etymology can be registered and preserved in DISPUTED state."""
        ety = EtymologicalRelationDefinition(
            relation_id="ETY-DISP-01",
            lexeme_text="דת",
            target_language="ARAMAIC",
            related_lexeme_text="data",
            source_language="OLD_PERSIAN",
            relationship_type=EtymologicalRelationshipType.BORROWING.value,
            state=BorrowingState.DISPUTED.value,
            reconstruction_method="Phonological correspondence",
            lexicon_source="HALOT p. 1856",
            evidence_id="EV-HIST-SEED-01",
            notes="Scholars debate whether loan is direct Persian or mediated through Akkadian",
        )
        res = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-DISP",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
            etymologies=[ety],
        )
        self.assertEqual(res.etymologies_count, 1)

        saved = self.hl_manager.get_etymologies_for_run("RUN-HL-DISP")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["state"], "DISPUTED")

    # -------------------------------------------------------------------------
    # 8. REJECTED ETYMOLOGY PRESERVED
    # -------------------------------------------------------------------------
    def test_08_rejected_etymology_preserved(self) -> None:
        """Rejected etymology is explicitly recorded with its REJECTED state."""
        ety = EtymologicalRelationDefinition(
            relation_id="ETY-REJ-01",
            lexeme_text="אלפא",
            target_language="ARAMAIC",
            related_lexeme_text="alef",
            source_language="SANSKRIT",
            relationship_type=EtymologicalRelationshipType.FOLK_ETYMOLOGY.value,
            state=BorrowingState.REJECTED.value,
            reconstruction_method="Speculative 19th c. comparison",
            lexicon_source="Critique in Gesenius",
            evidence_id="EV-HIST-SEED-01",
            notes="Decisively rejected due to Semitic West-Semitic origin of Aleph",
        )
        res = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-REJ",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
            etymologies=[ety],
        )
        self.assertEqual(res.etymologies_count, 1)

        saved = self.hl_manager.get_etymologies_for_run("RUN-HL-REJ")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["state"], "REJECTED")

    # -------------------------------------------------------------------------
    # 9. PARALLEL != INTERTEXTUALITY
    # -------------------------------------------------------------------------
    def test_09_parallel_not_intertextuality(self) -> None:
        """Firewall: Parallel cannot automatically become E10 intertextual evidence."""
        par = EpigraphicParallelDefinition(
            parallel_id="PAR-FAIL-01",
            parallel_corpus=ParallelCorpusType.DOCUMENTARY_PAPYRUS.value,
            artifact_siglum="P.Elephantine Cowley 30",
            dating_period="407 BCE",
            parallel_text="אלה שמיא ישאל שלמך",
            linguistic_significance="Epistolary formula in Official Aramaic",
            external_identifier="TAD A4.7",
            evidence_id="EV-HIST-SEED-01",
            is_intertextual_dependence=True,  # VIOLATION
        )
        with self.assertRaises(ParallelNotIntertextualFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-PAR-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                parallels=[par],
            )

        # Non-E9 evidence class must also fail
        par2 = EpigraphicParallelDefinition(
            parallel_id="PAR-FAIL-02",
            parallel_corpus=ParallelCorpusType.DOCUMENTARY_PAPYRUS.value,
            artifact_siglum="P.Elephantine Cowley 30",
            dating_period="407 BCE",
            parallel_text="אלה שמיא ישאל שלמך",
            linguistic_significance="Epistolary formula in Official Aramaic",
            external_identifier="TAD A4.7",
            evidence_id="EV-HIST-SEED-01",
            evidence_class="E10_INTERTEXTUAL",  # VIOLATION
        )
        with self.assertRaises(ParallelNotIntertextualFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-PAR-FAIL2",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                parallels=[par2],
            )

    # -------------------------------------------------------------------------
    # 10. TRANSLATION CANNOT BECOME HISTORICAL SOURCE
    # -------------------------------------------------------------------------
    def test_10_translation_cannot_become_historical_source(self) -> None:
        """Firewall: Modern translation cannot be registered as historical source."""
        lw = LoanwordDefinition(
            loanword_id="LW-TRANS-FAIL",
            source_language="LATIN",
            target_language="GREEK",
            lexeme="censere",
            candidate_etymon="censere",
            borrowing_type=BorrowingType.DIRECT_LOAN.value,
            chronological_range="Modern",
            external_reference="English translation",
            state=BorrowingState.PROPOSED.value,
            confidence=ConfidenceLevel.LOW.value,
            confidence_score=0.2,
            evidence_id="EV-HIST-SEED-01",
            is_translation_derived=True,  # VIOLATION
        )
        with self.assertRaises(TranslationHistoricalSourceFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-TRANS-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                loanwords=[lw],
            )

    # -------------------------------------------------------------------------
    # 11. AI OUTPUT CANNOT BECOME PRIMARY HISTORICAL EVIDENCE
    # -------------------------------------------------------------------------
    def test_11_ai_output_cannot_become_primary_historical_evidence(self) -> None:
        """Firewall: AI-generated etymologies cannot become primary historical evidence."""
        ety = EtymologicalRelationDefinition(
            relation_id="ETY-AI-FAIL",
            lexeme_text="אלהא",
            target_language="ARAMAIC",
            related_lexeme_text="elah",
            source_language="HEBREW",
            relationship_type=EtymologicalRelationshipType.COGNATE.value,
            state=BorrowingState.PROBABLE.value,
            reconstruction_method="AI LLM Hallucinated Reconstruction",
            lexicon_source="LLM prompt output",
            evidence_id="EV-HIST-SEED-01",
            is_ai_generated=True,  # VIOLATION
        )
        with self.assertRaises(AIHistoricalEvidenceFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-AI-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                etymologies=[ety],
            )

    # -------------------------------------------------------------------------
    # 12. PROVENANCE REQUIRED & UNVERIFIED IDENTIFIERS PRESERVED
    # -------------------------------------------------------------------------
    def test_12_provenance_and_unverified_identifier_preservation(self) -> None:
        """Unverified external identifiers remain UNVERIFIED; valid provenance is recorded."""
        par = EpigraphicParallelDefinition(
            parallel_id="PAR-UNVERIFIED-01",
            parallel_corpus=ParallelCorpusType.EPIGRAPHIC_INSCRIPTION.value,
            artifact_siglum="Stele of Zakkur",
            dating_period="VIII BCE",
            parallel_text="ואשא ידי אל בעלשמין",
            linguistic_significance="Old Aramaic verbal predicate syntax",
            external_identifier="KAI 202",
            external_identifier_status=IdentifierVerificationStatus.UNVERIFIED.value,
            evidence_id="EV-HIST-SEED-01",
        )
        res = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-PROV-OK",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
            parallels=[par],
        )

        saved = self.hl_manager.get_parallels_for_run("RUN-HL-PROV-OK")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["external_identifier_status"], "UNVERIFIED")

        # Verify provenance record created
        prov = self.provenance_tracker.get_record_by_target(TargetType.DERIVED_ARTIFACT, "RUN-HL-PROV-OK")
        self.assertIsNotNone(prov)
        self.assertEqual(prov.transformation_type, "DETERMINISTIC")
        self.assertTrue(len(prov.output_hash) == 64)

    # -------------------------------------------------------------------------
    # 13. VERSION SUPERSESSION ON REANALYSIS
    # -------------------------------------------------------------------------
    def test_13_version_supersession_on_reanalysis(self) -> None:
        """Re-analyzing the same passage marks prior run as SUPERSEDED and creates new version."""
        res1 = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-V1",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
        )
        self.assertEqual(res1.run_id, "RUN-HL-V1")

        # Run 2 on same passage
        res2 = self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-V2",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.1",
        )
        self.assertEqual(res2.run_id, "RUN-HL-V2")

        run1_data = self.hl_manager.get_run("RUN-HL-V1")
        run2_data = self.hl_manager.get_run("RUN-HL-V2")

        self.assertEqual(run1_data["status"], "SUPERSEDED")
        self.assertEqual(run2_data["status"], "COMPLETED")

    # -------------------------------------------------------------------------
    # 14. IMMUTABILITY ENFORCED BY SQL TRIGGERS
    # -------------------------------------------------------------------------
    def test_14_immutability_enforced_by_triggers(self) -> None:
        """Direct SQL UPDATE or DELETE on historical tables is blocked by triggers."""
        self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-IMMUT",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_polya_diachronic",
            analyzer_version="2.0.0",
        )

        with self.engine.transaction() as conn:
            # Cannot mutate analyzer_id
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE historical_linguistic_runs SET analyzer_id = 'hacked' WHERE run_id = 'RUN-HL-IMMUT'")

            # Cannot delete run
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM historical_linguistic_runs WHERE run_id = 'RUN-HL-IMMUT'")

            # Cannot delete strata
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM diachronic_strata WHERE stratum_id = 'STRAT-GRC-CLASSICAL'")

    # -------------------------------------------------------------------------
    # 15. ROLLBACK ON FAILURE
    # -------------------------------------------------------------------------
    def test_15_rollback_on_failure(self) -> None:
        """Atomic rollback on mid-transaction error leaves zero orphaned rows."""
        bad_ann = DiachronicAnnotationDefinition(
            annotation_id="ANN-FAIL-RB",
            stratum_id="NON_EXISTENT_STRATUM",  # FK violation
            classification_confidence="HIGH",
            linguistic_features="Archaic form",
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-ROLLBACK",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                annotations=[bad_ann],
            )

        with self.engine.transaction() as conn:
            run = conn.execute("SELECT * FROM historical_linguistic_runs WHERE run_id = 'RUN-HL-ROLLBACK'").fetchone()
            self.assertIsNone(run)

    # -------------------------------------------------------------------------
    # 16. CONCURRENCY SAFETY
    # -------------------------------------------------------------------------
    def test_16_concurrency_safety(self) -> None:
        """Concurrent historical analysis runs on distinct passages complete cleanly."""
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-DAN-2-21', 'PER-DAN-2', 'DAN', 2, 21, 2);
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-DAN-2-22', 'PER-DAN-2', 'DAN', 2, 22, 3);
                """
            )

        def run_worker(passage: str, idx: int) -> str:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            ecm = EvidenceClaimManager(eng)
            hl = HistoricalLinguisticManager(eng, vm, pt, ecm)
            res = hl.execute_analysis_run(
                run_id=f"RUN-CONC-{idx}",
                passage_id=passage,
                analyzer_id="analyzer_concurrent",
                analyzer_version="1.0",
            )
            eng.close()
            return res.run_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(run_worker, "PAS-DAN-2-21", 1)
            fut2 = executor.submit(run_worker, "PAS-DAN-2-22", 2)
            id1 = fut1.result()
            id2 = fut2.result()

        self.assertEqual(id1, "RUN-CONC-1")
        self.assertEqual(id2, "RUN-CONC-2")

    # -------------------------------------------------------------------------
    # 17. MIGRATIONS 001-014 CHECKSUMS UNCHANGED
    # -------------------------------------------------------------------------
    def test_17_migration_checksums_001_to_014_unchanged(self) -> None:
        """Migrations 001-014 must strictly match golden baseline checksums."""
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

        # Migration 015 exists and is readable
        m015 = migrations_dir / "015_historical_linguistics.sql"
        self.assertTrue(m015.exists())
        self.assertTrue(len(m015.read_bytes()) > 0)

    # -------------------------------------------------------------------------
    # 18. LEGACY DB INTEGRITY
    # -------------------------------------------------------------------------
    def test_18_legacy_db_sha256_unaltered(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain unaltered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_sha, LEGACY_DB_SHA256, "Legacy database altered!")

    # -------------------------------------------------------------------------
    # 19. LATER FORM NOT EARLIER READING FIREWALL
    # -------------------------------------------------------------------------
    def test_19_later_form_not_earlier_reading_firewall(self) -> None:
        """Asserting later form implies earlier reading is rejected by firewall."""
        bad_ann = DiachronicAnnotationDefinition(
            annotation_id="ANN-LATER-EARLIER",
            stratum_id="STRAT-HEB-LATE_BIBLICAL",
            classification_confidence="HIGH",
            linguistic_features="late form proves early text reading",
        )
        with self.assertRaises(LaterFormEarlierReadingFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-LATER-FORM-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                annotations=[bad_ann],
            )

    # -------------------------------------------------------------------------
    # 20. MODERN TERMINOLOGY AUTHORIAL INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_20_modern_terminology_authorial_intent_firewall(self) -> None:
        """Imposing modern linguistic terminology as authorial intent is rejected."""
        bad_obs = HistoricalObservationDefinition(
            observation_id="OBS-MOD-INTENT-FAIL",
            passage_id="PAS-DAN-2-20",
            observation_scope="LEXEME",
            evidence_scope="INTERNAL_LINGUISTIC",
            observation_title="Modern Concept Anachronism",
            observation_text="Ancient author intended 21st-century syntactic semantics.",
            evidence_id="EV-HIST-SEED-01",
            modern_terminology_imposed=True,
        )
        with self.assertRaises(ModernTerminologyAuthorialIntentFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-MOD-INTENT-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                observations=[bad_obs],
            )

    # -------------------------------------------------------------------------
    # 21. UNCONDITIONAL THEOLOGICAL INFLUENCE REJECTION
    # -------------------------------------------------------------------------
    def test_21_unconditional_theological_influence_rejection(self) -> None:
        """Asserting borrowing/lexical similarity equals theological influence is unconditionally rejected."""
        bad_obs = HistoricalObservationDefinition(
            observation_id="OBS-THEO-INFL-FAIL",
            passage_id="PAS-DAN-2-20",
            observation_scope="LEXEME",
            evidence_scope="EXTERNAL_HISTORICAL",
            observation_title="Illegitimate Theological Jump",
            observation_text="Lexical loanword proves borrowing of Babylonian theology.",
            evidence_id="EV-HIST-SEED-01",
            asserts_theological_influence=True,
        )
        with self.assertRaises(LexicalSimilarityNotCausationFirewallError):
            self.hl_manager.execute_analysis_run(
                run_id="RUN-HL-THEO-INFL-FAIL",
                passage_id="PAS-DAN-2-20",
                analyzer_id="analyzer_test",
                analyzer_version="1.0",
                observations=[bad_obs],
            )

    # -------------------------------------------------------------------------
    # 22. DIRECT SQL TRIGGER REJECTION ON SUPERSEDED RUN MUTATION
    # -------------------------------------------------------------------------
    def test_22_superseded_run_immutability_trigger(self) -> None:
        """Direct SQL UPDATE on a SUPERSEDED run is rejected by trigger."""
        self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-SUP-1",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_test",
            analyzer_version="1.0",
        )
        # Supersede it with run 2
        self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-SUP-2",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_test",
            analyzer_version="2.0",
        )

        with self.engine.transaction() as conn:
            row = conn.execute("SELECT status FROM historical_linguistic_runs WHERE run_id = 'RUN-HL-SUP-1'").fetchone()
            self.assertEqual(row["status"], "SUPERSEDED")

            # Trying to mutate any field on SUPERSEDED run must fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE historical_linguistic_runs SET status = 'COMPLETED' WHERE run_id = 'RUN-HL-SUP-1'")

            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE historical_linguistic_runs SET metadata_json = '{\"hacked\": true}' WHERE run_id = 'RUN-HL-SUP-1'")

    # -------------------------------------------------------------------------
    # 23. DIRECT SQL CHECK CONSTRAINT REJECTION ON UNVERIFIED ESTABLISHED LOANWORD
    # -------------------------------------------------------------------------
    def test_23_loanword_sql_check_unverified_established(self) -> None:
        """SQL CHECK constraint rejects borrowing_type='UNVERIFIED' with state='ESTABLISHED'."""
        prov = self.provenance_tracker.record_deterministic(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id="TEST-TARGET",
            content="test",
            input_data="test",
            agent_id="test",
            agent_version="1.0",
        )
        self.hl_manager.execute_analysis_run(
            run_id="RUN-HL-SQL-CHECK",
            passage_id="PAS-DAN-2-20",
            analyzer_id="analyzer_test",
            analyzer_version="1.0",
        )

        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO loanword_registry (
                        loanword_id, run_id, source_language, target_language,
                        lexeme, lemma_id, candidate_etymon, borrowing_type,
                        chronological_range, external_reference, external_identifier_status,
                        state, confidence, confidence_score, evidence_id, provenance_id,
                        is_ai_generated, is_translation_derived, created_at, is_immutable, notes
                    ) VALUES (
                        'LW-SQL-CHECK-FAIL', 'RUN-HL-SQL-CHECK', 'OLD_PERSIAN', 'ARAMAIC',
                        'pitgama', 'LEM-PITGAMA', 'patigama', 'UNVERIFIED',
                        'c. 5th BCE', 'CAD P', 'UNVERIFIED',
                        'ESTABLISHED', 'HIGH', 0.85, 'EV-HIST-SEED-01', ?,
                        0, 0, '2026-10-01T00:00:00Z', 1, 'Bypassing firewall test'
                    )
                    """,
                    (prov.provenance_id,),
                )


if __name__ == "__main__":
    unittest.main()
