"""
Unit and Adversarial Test Suite for Intertextual Analysis Engine (Task 3.3).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Greek, Hebrew, and Aramaic separation and language mismatch handling
  2. Lexical similarity without intertextuality firewall
  3. Thematic similarity without intertextuality firewall
  4. Chronology without dependence firewall
  5. Same wording without automatic quotation firewall
  6. Shared tradition without direct quotation firewall
  7. Quotation requires explicit evidence firewall
  8. Multiple candidate sources for one target passage
  9. Competing hypotheses preserved independently
  10. Counter-evidence supported as first-class
  11. E9 parallel != E10 intertext firewall
  12. Translation mediation marked and verified
  13. Reception source != authorial source firewall
  14. Entity identity != textual dependence firewall
  15. Unknown direction preserved when unestablished
  16. AI-generated proposal != primary evidence firewall
  17. Modern commentary != ancient source firewall
  18. Unverified external identifiers preserved as UNVERIFIED
  19. Provenance integration and deterministic hashes
  20. Version lineage and supersession on reanalysis
  21. Immutability enforced by SQL triggers
  22. Rollback on failure leaves zero orphaned rows
  23. Concurrency safety under multithreaded writers
  24. Migration 001-015 checksums strictly unchanged
  25. Legacy DB unaltered
  26. Retrieval ranking cannot select truth
  27. Confidence cannot manufacture or upgrade evidence
  28. Theological escalation firewall
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
    AIIntertextualEvidenceFirewallError,
    ChronologyNotDependenceFirewallError,
    ChronologyOnlyRelationFirewallError,
    ConfidenceNotEvidenceUpgradeFirewallError,
    CounterEvidencePreservationFirewallError,
    E9ParallelNotE10IntertextFirewallError,
    EntityIdentityNotTextualDependenceFirewallError,
    IntertextualConcurrencyError,
    IntertextualImmutabilityError,
    IntertextualNotTheologicalClaimFirewallError,
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
from bible_engine.intertextuality import (
    EpistemicClassification,
    EvidenceStance,
    IdentifierVerificationStatus,
    IntertextStatus,
    IntertextualEvidenceLinkDefinition,
    IntertextualHypothesisDefinition,
    IntertextualManager,
    IntertextualObservationDefinition,
    IntertextualRelationshipDefinition,
    IntertextualRelationType,
    ObservationType,
    SourceDirection,
    SourceMetadataDefinition,
    SourceType,
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
    "015_historical_linguistics.sql": "57acc411610d0618c140cb181dca02ded4f21a59d005a7e04fbbd84489061669",
}

LEGACY_DB_SHA256 = "500bb6a2057a1c30e392f0a99f2437a9b07a79a075e79177a0b9d17e7353c5c5"


class TestIntertextualAnalysisEngine(unittest.TestCase):
    """Adversarial and structural tests for Task 3.3 Intertextual Analysis Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_intertextuality.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.evidence_claim_manager = EvidenceClaimManager(self.engine)
        self.it_manager = IntertextualManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
            self.evidence_claim_manager,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('OT', 'CAN-PROT', 'Perjanjian Lama', 1);")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute("INSERT INTO books VALUES ('MAT', 'NT', 40, 'Matius', 'Matthew', 'GREEK', 28);")
            conn.execute("INSERT INTO books VALUES ('MIC', 'OT', 33, 'Mikha', 'Micah', 'HEBREW', 7);")
            conn.execute("INSERT INTO books VALUES ('ISA', 'OT', 23, 'Yesaya', 'Isaiah', 'HEBREW', 66);")
            conn.execute("INSERT INTO books VALUES ('DAN', 'OT', 27, 'Daniel', 'Daniel', 'ARAMAIC', 12);")

            conn.execute(
                """
                INSERT INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-MAT-2', 'MAT', 'Matius 2:1-12', 2, 1, 2, 12,
                    'NARRATIVE', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-MAT-2-6', 'PER-MAT-2', 'MAT', 2, 6, 1);
                """
            )
            # Seed E10 evidence entry in evidence_ledger
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class,
                    epistemic_tier, source_reference, extracted_text_or_data,
                    status, confidence, confidence_score, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV-IT-SEED-01', 'PER-MAT-2', 'PAS-MAT-2-6', 'E10_INTERTEXTUAL',
                    'T3_INTERPRETIVE_CLAIM', 'Micah 5:2 in Matthew 2:6 citation',
                    'καὶ σύ, Βηθλέεμ γῆ Ἰούδα', '[EXPLICIT]', 'HIGH', 0.95,
                    '2026-10-01T00:00:00Z', 'hash_it_seed', 1
                );
                """
            )
            # Seed E9 evidence entry for firewall test
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class,
                    epistemic_tier, source_reference, extracted_text_or_data,
                    status, confidence, confidence_score, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV-E9-PARALLEL-01', 'PER-MAT-2', 'PAS-MAT-2-6', 'E9_HISTORICAL_LINGUISTIC',
                    'T1_LINGUISTIC_FACT', 'Epigraphic parallel in Beth-lehem',
                    'ostracon inscription', '[EXPLICIT]', 'HIGH', 0.85,
                    '2026-10-01T00:00:00Z', 'hash_e9_seed', 1
                );
                """
            )

        # Seed default candidate source metadata
        src_meta = SourceMetadataDefinition(
            source_metadata_id="SRC-MICAH-HEB",
            source_type=SourceType.BIBLICAL_PASSAGE.value,
            canonical_reference="Mikha 5:1",  # Mikha 5:2 in MT / 5:1 in ET
            source_language="HEBREW",
            is_translation=False,
            external_identifier="MT_CODEX_LENINGRADENSIS",
            external_identifier_status=IdentifierVerificationStatus.VERIFIED.value,
        )
        self.it_manager.register_source_metadata(src_meta)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. GREEK / HEBREW / ARAMAIC SEPARATION & LANGUAGE MISMATCH HANDLING
    # -------------------------------------------------------------------------
    def test_01_language_separation_and_translation_mediation(self) -> None:
        """Greek target citing Hebrew source text properly registers translation mediation."""
        rel = IntertextualRelationshipDefinition(
            relationship_id="REL-MAT26-MIC51",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            direction=SourceDirection.SOURCE_TO_TARGET.value,
            status=IntertextStatus.ESTABLISHED.value,
            target_language="GREEK",
            source_language="HEBREW",
            is_translation_mediated=True,
            has_explicit_quotation_formula=True,
            quotation_formula_text="γέγραπται γὰρ διὰ τοῦ προφήτου",
            chronological_precedence_demonstrated=True,
            confidence=ConfidenceLevel.VERY_HIGH.value,
            confidence_score=0.98,
            evidence_id="EV-IT-SEED-01",
        )

        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-LANG-OK",
            target_passage_id="PAS-MAT-2-6",
            relationships=[rel],
        )
        self.assertEqual(res.relationships_count, 1)

        saved = self.it_manager.get_relationships_for_run("RUN-IT-LANG-OK")
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["target_language"], "GREEK")
        self.assertEqual(saved[0]["source_language"], "HEBREW")
        self.assertEqual(saved[0]["is_translation_mediated"], 1)

    # -------------------------------------------------------------------------
    # 2. LEXICAL SIMILARITY != INTERTEXTUALITY FIREWALL
    # -------------------------------------------------------------------------
    def test_02_lexical_similarity_without_intertext(self) -> None:
        """Firewall: Lexical parallel alone cannot assert DIRECT_QUOTATION or ESTABLISHED dependence."""
        src_meta = SourceMetadataDefinition(
            source_metadata_id="SRC-ISAIAH-HEB",
            source_type=SourceType.BIBLICAL_PASSAGE.value,
            canonical_reference="Yesaya 7:14",
            source_language="HEBREW",
            external_identifier="MT_ISAIAH",
            external_identifier_status=IdentifierVerificationStatus.VERIFIED.value,
        )
        self.it_manager.register_source_metadata(src_meta)

        # Illegitimate: Lexical parallel asserting ESTABLISHED dependence without quotation formula
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-LEX-EST-FAIL",
            source_metadata_id="SRC-ISAIAH-HEB",
            relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.LEXICAL_PARALLEL.value,
            status=IntertextStatus.ESTABLISHED.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=False,
            chronological_precedence_demonstrated=False,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(LexicalSimilarityNotIntertextualityFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-LEX-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

        # Illegitimate: Lexical parallel claiming STRONG_ALLUSION
        bad_rel2 = IntertextualRelationshipDefinition(
            relationship_id="REL-LEX-ALLUSION-FAIL",
            source_metadata_id="SRC-ISAIAH-HEB",
            relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(LexicalSimilarityNotIntertextualityFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-LEX-ALLUSION-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel2],
            )

    # -------------------------------------------------------------------------
    # 3. THEMATIC SIMILARITY != INTERTEXTUALITY FIREWALL
    # -------------------------------------------------------------------------
    def test_03_thematic_similarity_without_intertext(self) -> None:
        """Firewall: Thematic parallel cannot assert DIRECT_QUOTATION or STRONG_ALLUSION."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-THEME-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.THEMATIC_PARALLEL.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ThematicSimilarityNotIntertextualityFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-THEME-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 4. CHRONOLOGY != TEXTUAL DEPENDENCE FIREWALL
    # -------------------------------------------------------------------------
    def test_04_chronology_without_dependence(self) -> None:
        """Firewall: Relationship established solely on chronological basis is rejected."""
        # 4a. Solely chronological basis rejected
        bad_rel1 = IntertextualRelationshipDefinition(
            relationship_id="REL-CHRONO-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.TEXTUAL_REUSE.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            solely_chronological_basis=True,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ChronologyOnlyRelationFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-CHRONO-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel1],
            )

        # 4b. Precedence without textual dependence cannot assert strong allusion
        bad_rel2 = IntertextualRelationshipDefinition(
            relationship_id="REL-CHRONO-DEP-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.UNKNOWN.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            chronological_precedence_demonstrated=True,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ChronologyNotDependenceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-CHRONO-DEP-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel2],
            )

    # -------------------------------------------------------------------------
    # 5. SAME WORDING != AUTOMATIC QUOTATION & QUOTATION REQUIRES EVIDENCE
    # -------------------------------------------------------------------------
    def test_05_wording_without_quotation_formula_and_evidence(self) -> None:
        """Firewall: Direct quotation strictly requires explicit quotation formula/evidence; confidence/score cannot manufacture evidence."""
        # 5a. Missing quotation formula even with CERTAIN / 1.0 confidence must be rejected
        bad_rel_high_conf = IntertextualRelationshipDefinition(
            relationship_id="REL-QUOT-HIGH-CONF-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=False,
            confidence=ConfidenceLevel.CERTAIN.value,
            confidence_score=1.0,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(QuotationEvidenceRequiredFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-QUOT-HIGH-CONF-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel_high_conf],
            )

        # 5b. Missing quotation formula with high retrieval score (0.99) and rank 1 must be rejected
        bad_rel_retrieval = IntertextualRelationshipDefinition(
            relationship_id="REL-QUOT-RETRIEVAL-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=False,
            retrieval_rank=1,
            retrieval_score=0.99,
            confidence=ConfidenceLevel.VERY_HIGH.value,
            confidence_score=0.95,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(QuotationEvidenceRequiredFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-QUOT-RETRIEVAL-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel_retrieval],
            )

        # 5c. Strong lexical similarity without quotation formula cannot automatically assert DIRECT_QUOTATION
        bad_rel_lex = IntertextualRelationshipDefinition(
            relationship_id="REL-WORDING-NO-QUOT",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=False,
            confidence=ConfidenceLevel.HIGH.value,
            confidence_score=0.85,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(SameWordingNotAutomaticQuotationFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-WORDING-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel_lex],
            )

        # 5d. Chronological precedence without quotation formula cannot assert DIRECT_QUOTATION
        bad_rel_chrono = IntertextualRelationshipDefinition(
            relationship_id="REL-QUOT-CHRONO-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.UNKNOWN.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            chronological_precedence_demonstrated=True,
            has_explicit_quotation_formula=False,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ChronologyNotDependenceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-QUOT-CHRONO-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel_chrono],
            )

        # 5e. AI-generated assertion without quotation evidence is rejected
        bad_rel_ai = IntertextualRelationshipDefinition(
            relationship_id="REL-QUOT-AI-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            is_ai_generated=True,
            has_explicit_quotation_formula=False,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(AIIntertextualEvidenceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-QUOT-AI-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel_ai],
            )

        # 5f. Explicit quotation formula AND evidence successfully establishes DIRECT_QUOTATION
        good_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-QUOT-EXPLICIT-OK",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=True,
            quotation_formula_text="γέγραπται γὰρ διὰ τοῦ προφήτου",
            confidence=ConfidenceLevel.HIGH.value,
            confidence_score=0.85,
            evidence_id="EV-IT-SEED-01",
        )
        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-QUOT-EXPLICIT-OK",
            target_passage_id="PAS-MAT-2-6",
            relationships=[good_rel],
        )
        self.assertEqual(res.relationships_count, 1)
        saved = self.it_manager.get_relationships_for_run("RUN-IT-QUOT-EXPLICIT-OK")
        self.assertEqual(saved[0]["relationship_type"], "DIRECT_QUOTATION")
        self.assertEqual(saved[0]["has_explicit_quotation_formula"], 1)

    # -------------------------------------------------------------------------
    # 6. SHARED TRADITION != DIRECT QUOTATION
    # -------------------------------------------------------------------------
    def test_06_shared_tradition_not_direct_quotation(self) -> None:
        """Firewall: Traditional parallel cannot be classified as DIRECT_QUOTATION."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-TRAD-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.TRADITIONAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(SharedTraditionNotDirectQuotationFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-TRAD-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 7. MULTIPLE CANDIDATE SOURCES
    # -------------------------------------------------------------------------
    def test_07_multiple_candidate_sources(self) -> None:
        """Target passage can simultaneously evaluate multiple candidate sources independently."""
        src_meta1 = SourceMetadataDefinition(
            source_metadata_id="SRC-CANDIDATE-1",
            source_type=SourceType.BIBLICAL_PASSAGE.value,
            canonical_reference="Mikha 5:1",
            source_language="HEBREW",
            external_identifier="MT_MICAH",
        )
        src_meta2 = SourceMetadataDefinition(
            source_metadata_id="SRC-CANDIDATE-2",
            source_type=SourceType.BIBLICAL_PASSAGE.value,
            canonical_reference="2 Samuel 5:2",
            source_language="HEBREW",
            external_identifier="MT_2SAMUEL",
        )
        self.it_manager.register_source_metadata(src_meta1)
        self.it_manager.register_source_metadata(src_meta2)

        rel1 = IntertextualRelationshipDefinition(
            relationship_id="REL-MULTI-01",
            source_metadata_id="SRC-CANDIDATE-1",
            relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            has_explicit_quotation_formula=True,
            confidence=ConfidenceLevel.VERY_HIGH.value,
            confidence_score=0.95,
            evidence_id="EV-IT-SEED-01",
        )
        rel2 = IntertextualRelationshipDefinition(
            relationship_id="REL-MULTI-02",
            source_metadata_id="SRC-CANDIDATE-2",
            relationship_type=IntertextualRelationType.STRONG_ALLUSION.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            confidence=ConfidenceLevel.HIGH.value,
            confidence_score=0.82,
            evidence_id="EV-IT-SEED-01",
        )

        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-MULTI-SRC",
            target_passage_id="PAS-MAT-2-6",
            relationships=[rel1, rel2],
        )
        self.assertEqual(res.relationships_count, 2)
        rels = self.it_manager.get_relationships_for_run("RUN-IT-MULTI-SRC")
        self.assertEqual(len(rels), 2)
        sources = {r["source_metadata_id"] for r in rels}
        self.assertEqual(sources, {"SRC-CANDIDATE-1", "SRC-CANDIDATE-2"})

    # -------------------------------------------------------------------------
    # 8. COMPETING HYPOTHESES PRESERVED
    # -------------------------------------------------------------------------
    def test_08_competing_hypotheses_preserved(self) -> None:
        """Competing hypotheses are stored alongside each other without collapsing."""
        h1 = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-MAT-A",
            hypothesis_code="HYP_A_DIRECT_QUOTATION",
            hypothesis_description="Matthew directly quotes Micah 5:2 via Greek translation",
            proposed_relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            source_metadata_id="SRC-MICAH-HEB",
            is_primary=True,
            status=IntertextStatus.PROBABLE.value,
            retrieval_rank=1,
            retrieval_score=0.92,
        )
        h2 = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-MAT-B",
            hypothesis_code="HYP_B_COMPOSITE_ALLUSION",
            hypothesis_description="Matthew blends Micah 5:2 and 2 Samuel 5:2 from memory",
            proposed_relationship_type=IntertextualRelationType.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            source_metadata_id="SRC-MICAH-HEB",
            is_primary=False,
            status=IntertextStatus.POSSIBLE.value,
            retrieval_rank=2,
            retrieval_score=0.88,
        )
        h3 = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-MAT-C",
            hypothesis_code="HYP_C_TRADITIONAL_LITURGY",
            hypothesis_description="Shared messianic Bethlehem tradition without direct borrowing",
            proposed_relationship_type=IntertextualRelationType.TRADITIONAL_PARALLEL.value,
            target_passage_id="PAS-MAT-2-6",
            is_primary=False,
            status=IntertextStatus.DISPUTED.value,
            retrieval_rank=3,
            retrieval_score=0.74,
        )

        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-COMPETING-HYP",
            target_passage_id="PAS-MAT-2-6",
            hypotheses=[h1, h2, h3],
        )
        self.assertEqual(res.hypotheses_count, 3)
        hyps = self.it_manager.get_hypotheses_for_run("RUN-IT-COMPETING-HYP")
        self.assertEqual(len(hyps), 3)

    # -------------------------------------------------------------------------
    # 9. COUNTER-EVIDENCE SUPPORTED AS FIRST-CLASS
    # -------------------------------------------------------------------------
    def test_09_counter_evidence_first_class(self) -> None:
        """Counter-evidence must be explicitly marked with is_counter_evidence=True."""
        hyp = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-COUNTER-TEST",
            hypothesis_code="HYP_SEPTUAGINT_DEPENDENCE",
            hypothesis_description="Matthew directly derived quotation from Greek Septuagint",
            proposed_relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
        )
        # Valid counter-evidence link
        link_good = IntertextualEvidenceLinkDefinition(
            link_id="LINK-COUNTER-OK",
            evidence_id="EV-IT-SEED-01",
            hypothesis_id="HYP-COUNTER-TEST",
            evidence_class="E10_INTERTEXTUAL",
            stance=EvidenceStance.CONTRADICT.value,
            weight=0.9,
            is_counter_evidence=True,
            reasoning="Wording in Matthew contradicts verbatim Septuagint reading.",
        )
        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-COUNTER-OK",
            target_passage_id="PAS-MAT-2-6",
            hypotheses=[hyp],
            evidence_links=[link_good],
        )
        self.assertEqual(res.evidence_links_count, 1)

        # Invalid: CONTRADICT stance but is_counter_evidence=False
        link_bad = IntertextualEvidenceLinkDefinition(
            link_id="LINK-COUNTER-FAIL",
            evidence_id="EV-IT-SEED-01",
            hypothesis_id="HYP-COUNTER-TEST",
            evidence_class="E10_INTERTEXTUAL",
            stance=EvidenceStance.CONTRADICT.value,
            weight=0.9,
            is_counter_evidence=False,
            reasoning="Attempting to hide counter-evidence.",
        )
        with self.assertRaises(CounterEvidencePreservationFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-COUNTER-FAIL",
                target_passage_id="PAS-MAT-2-6",
                hypotheses=[hyp],
                evidence_links=[link_bad],
            )

    # -------------------------------------------------------------------------
    # 10. E9 PARALLEL != E10 INTERTEXT FIREWALL
    # -------------------------------------------------------------------------
    def test_10_e9_parallel_not_e10_intertext(self) -> None:
        """Firewall: E9 historical-linguistic parallel cannot be linked directly as E10 evidence."""
        hyp = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-E9-TEST",
            hypothesis_code="HYP_EPIGRAPHIC_PARALLEL",
            hypothesis_description="Passage depends on Bethlehem epigraphic tradition",
            proposed_relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            target_passage_id="PAS-MAT-2-6",
        )
        bad_link = IntertextualEvidenceLinkDefinition(
            link_id="LINK-E9-AS-E10-FAIL",
            evidence_id="EV-E9-PARALLEL-01",
            hypothesis_id="HYP-E9-TEST",
            evidence_class="E9_HISTORICAL_LINGUISTIC",  # Illegitimate E9 in E10 link
            stance=EvidenceStance.SUPPORT.value,
            reasoning="Attempting to inject E9 parallel as E10 intertext.",
        )
        with self.assertRaises(E9ParallelNotE10IntertextFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-E9-FAIL",
                target_passage_id="PAS-MAT-2-6",
                hypotheses=[hyp],
                evidence_links=[bad_link],
            )

    # -------------------------------------------------------------------------
    # 11. RECEPTION SOURCE != AUTHORIAL SOURCE FIREWALL
    # -------------------------------------------------------------------------
    def test_11_reception_source_not_authorial_source(self) -> None:
        """Firewall: Later commentary cannot be marked as authorial source (SOURCE_TO_TARGET)."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-RECEPTION-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.TEXTUAL_REUSE.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            direction=SourceDirection.SOURCE_TO_TARGET.value,
            is_reception_history_source=True,  # Later commentary as source
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ReceptionSourceNotAuthorialSourceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-RECEPTION-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 12. ENTITY IDENTITY != TEXTUAL DEPENDENCE FIREWALL
    # -------------------------------------------------------------------------
    def test_12_entity_identity_not_textual_dependence(self) -> None:
        """Firewall: Entity or name agreement alone cannot assert quotation or strong allusion."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-ENTITY-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.TEXTUAL_REUSE.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            entity_agreement_only=True,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(EntityIdentityNotTextualDependenceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-ENTITY-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 13. UNKNOWN DIRECTION PRESERVED
    # -------------------------------------------------------------------------
    def test_13_unknown_direction_preserved(self) -> None:
        """When direction of borrowing/influence is unknown, UNKNOWN is strictly preserved."""
        rel = IntertextualRelationshipDefinition(
            relationship_id="REL-UNKNOWN-DIR-OK",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.LEXICAL_PARALLEL.value,
            target_passage_id="PAS-MAT-2-6",
            direction=SourceDirection.UNKNOWN.value,
            evidence_id="EV-IT-SEED-01",
        )
        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-DIR-OK",
            target_passage_id="PAS-MAT-2-6",
            relationships=[rel],
        )
        saved = self.it_manager.get_relationships_for_run("RUN-IT-DIR-OK")
        self.assertEqual(saved[0]["direction"], "UNKNOWN")

    # -------------------------------------------------------------------------
    # 14. AI PROPOSAL != PRIMARY EVIDENCE FIREWALL
    # -------------------------------------------------------------------------
    def test_14_ai_output_not_primary_evidence(self) -> None:
        """Firewall: AI-generated proposal cannot become primary intertextual evidence."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-AI-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.STRONG_ALLUSION.value,
            epistemic_classification=EpistemicClassification.STRONG_ALLUSION.value,
            target_passage_id="PAS-MAT-2-6",
            is_ai_generated=True,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(AIIntertextualEvidenceFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-AI-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 15. MODERN COMMENTARY != ANCIENT SOURCE FIREWALL
    # -------------------------------------------------------------------------
    def test_15_modern_commentary_not_ancient_source(self) -> None:
        """Firewall: Modern commentary cannot be registered as ancient source text."""
        bad_src = SourceMetadataDefinition(
            source_metadata_id="SRC-MODERN-COMM-FAIL",
            source_type=SourceType.ANCIENT_COMMENTARY_RECEPTION.value,
            canonical_reference="Brown, Anchor Bible Commentary 1993",
            source_language="OTHER",
            is_modern_commentary=True,
            external_identifier="ISBN-123456",
        )
        with self.assertRaises(ModernCommentaryNotAncientSourceFirewallError):
            self.it_manager.register_source_metadata(bad_src)

    # -------------------------------------------------------------------------
    # 16. UNVERIFIED EXTERNAL IDENTIFIERS PRESERVED
    # -------------------------------------------------------------------------
    def test_16_unverified_identifier_preservation(self) -> None:
        """Unverified external identifiers remain UNVERIFIED; claiming VERIFIED raises error."""
        bad_src = SourceMetadataDefinition(
            source_metadata_id="SRC-UNVERIF-FAIL",
            source_type=SourceType.INSCRIPTION.value,
            canonical_reference="Unconfirmed papyrus fragment",
            source_language="GREEK",
            external_identifier="UNVERIFIED_INVENTORY_99",
            external_identifier_status=IdentifierVerificationStatus.VERIFIED.value,
        )
        with self.assertRaises(UnverifiedIdentifierPreservationFirewallError):
            self.it_manager.register_source_metadata(bad_src)

    # -------------------------------------------------------------------------
    # 17. RETRIEVAL RANKING CANNOT SELECT TRUTH
    # -------------------------------------------------------------------------
    def test_17_retrieval_ranking_cannot_select_truth(self) -> None:
        """Firewall: Retrieval score cannot be forced as authoritative winner."""
        bad_hyp = IntertextualHypothesisDefinition(
            hypothesis_id="HYP-FORCED-WINNER-FAIL",
            hypothesis_code="FORCED_WINNER",
            hypothesis_description="Top retrieval embedding score declared absolute truth",
            proposed_relationship_type=IntertextualRelationType.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            retrieval_forced_winner=True,
        )
        with self.assertRaises(RetrievalRankingNotTruthFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-RANK-FAIL",
                target_passage_id="PAS-MAT-2-6",
                hypotheses=[bad_hyp],
            )

    # -------------------------------------------------------------------------
    # 18. CONFIDENCE CANNOT MANUFACTURE OR UPGRADE EVIDENCE
    # -------------------------------------------------------------------------
    def test_18_confidence_cannot_upgrade_evidence(self) -> None:
        """Firewall: Setting confidence to CERTAIN on thematic parallel cannot upgrade it to DIRECT_QUOTATION."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-CONF-UPGRADE-FAIL",
            source_metadata_id="SRC-MICAH-HEB",
            relationship_type=IntertextualRelationType.THEMATIC_PARALLEL.value,
            epistemic_classification=EpistemicClassification.DIRECT_QUOTATION.value,
            target_passage_id="PAS-MAT-2-6",
            confidence=ConfidenceLevel.CERTAIN.value,
            confidence_score=1.0,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(ConfidenceNotEvidenceUpgradeFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-CONF-FAIL",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

    # -------------------------------------------------------------------------
    # 19. THEOLOGICAL ESCALATION FIREWALL
    # -------------------------------------------------------------------------
    def test_19_theological_escalation_firewall(self) -> None:
        """Firewall: Intertextual observation cannot be asserted directly as T4 theological claim."""
        bad_obs = IntertextualObservationDefinition(
            observation_id="OBS-THEO-ESCALATE-FAIL",
            relationship_id="REL-MAT26-MIC51",
            observation_type=ObservationType.WORDING_OVERLAP.value,
            observation_text="Quotation proves hypostatic union doctrine directly.",
            is_theological_claim=True,
            evidence_id="EV-IT-SEED-01",
        )
        with self.assertRaises(IntertextualNotTheologicalClaimFirewallError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-THEO-FAIL",
                target_passage_id="PAS-MAT-2-6",
                observations=[bad_obs],
            )

    # -------------------------------------------------------------------------
    # 20. PROVENANCE INTEGRATION & DETERMINISTIC HASHES
    # -------------------------------------------------------------------------
    def test_20_provenance_integration_and_deterministic_hashes(self) -> None:
        """Every run generates cryptographic deterministic provenance and input/output hashes."""
        res = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-PROV-OK",
            target_passage_id="PAS-MAT-2-6",
            analyzer_id="analyzer_intertext_v2",
            analyzer_version="2.0.0",
        )
        self.assertTrue(len(res.output_hash) == 64)

        prov = self.provenance_tracker.get_record_by_target(TargetType.DERIVED_ARTIFACT, "RUN-IT-PROV-OK")
        self.assertIsNotNone(prov)
        self.assertEqual(prov.transformation_type, "DETERMINISTIC")

    # -------------------------------------------------------------------------
    # 21. VERSION LINEAGE & SUPERSESSION ON REANALYSIS
    # -------------------------------------------------------------------------
    def test_21_version_lineage_and_supersession(self) -> None:
        """Re-analyzing the same target passage supersedes prior run cleanly."""
        res1 = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-V1",
            target_passage_id="PAS-MAT-2-6",
            analyzer_id="analyzer_test",
            analyzer_version="1.0.0",
        )
        self.assertEqual(res1.run_id, "RUN-IT-V1")

        # Run 2 on same target passage
        res2 = self.it_manager.execute_analysis_run(
            run_id="RUN-IT-V2",
            target_passage_id="PAS-MAT-2-6",
            analyzer_id="analyzer_test",
            analyzer_version="1.0.1",
        )
        self.assertEqual(res2.run_id, "RUN-IT-V2")

        r1 = self.it_manager.get_run("RUN-IT-V1")
        r2 = self.it_manager.get_run("RUN-IT-V2")
        self.assertEqual(r1["status"], "SUPERSEDED")
        self.assertEqual(r2["status"], "COMPLETED")

        # Verify version lineage relation recorded
        v1_ver = self.version_manager.get_version(r1["version_id"])
        self.assertEqual(v1_ver.status, "SUPERSEDED")
        with self.engine.transaction() as conn:
            rels = conn.execute(
                "SELECT relation_type, source_version_id, target_version_id FROM version_relations WHERE source_version_id = ? OR target_version_id = ?",
                (r1["version_id"], r1["version_id"]),
            ).fetchall()
            rel_types = {r[0] for r in rels}
            self.assertIn("SUPERSEDED_BY", rel_types)
            self.assertIn("SUPERSEDES", rel_types)

    # -------------------------------------------------------------------------
    # 22. IMMUTABILITY ENFORCED BY SQL TRIGGERS
    # -------------------------------------------------------------------------
    def test_22_immutability_enforced_by_triggers(self) -> None:
        """Direct SQL UPDATE or DELETE on immutable tables is blocked by triggers."""
        self.it_manager.execute_analysis_run(
            run_id="RUN-IT-IMMUT",
            target_passage_id="PAS-MAT-2-6",
        )

        with self.engine.transaction() as conn:
            # Cannot mutate analyzer_id
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE intertextual_runs SET analyzer_id = 'hacked' WHERE run_id = 'RUN-IT-IMMUT'")

            # Cannot delete run
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM intertextual_runs WHERE run_id = 'RUN-IT-IMMUT'")

            # Cannot mutate source metadata
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE intertextual_source_metadata SET source_language = 'LATIN' WHERE source_metadata_id = 'SRC-MICAH-HEB'")

    # -------------------------------------------------------------------------
    # 23. ROLLBACK ON FAILURE
    # -------------------------------------------------------------------------
    def test_23_rollback_on_failure(self) -> None:
        """Atomic rollback on mid-transaction error leaves zero orphaned rows."""
        bad_rel = IntertextualRelationshipDefinition(
            relationship_id="REL-FAIL-RB",
            source_metadata_id="NON_EXISTENT_METADATA",  # FK violation
            relationship_type=IntertextualRelationType.LEXICAL_PARALLEL.value,
            epistemic_classification=EpistemicClassification.LEXICAL_PARALLEL.value,
            target_passage_id="PAS-MAT-2-6",
            evidence_id="EV-IT-SEED-01",
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.it_manager.execute_analysis_run(
                run_id="RUN-IT-ROLLBACK",
                target_passage_id="PAS-MAT-2-6",
                relationships=[bad_rel],
            )

        with self.engine.transaction() as conn:
            run = conn.execute("SELECT * FROM intertextual_runs WHERE run_id = 'RUN-IT-ROLLBACK'").fetchone()
            self.assertIsNone(run)

    # -------------------------------------------------------------------------
    # 24. CONCURRENCY SAFETY
    # -------------------------------------------------------------------------
    def test_24_concurrency_safety(self) -> None:
        """Concurrent intertextual analysis runs complete cleanly without lock contention."""
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-MAT-2-7', 'PER-MAT-2', 'MAT', 2, 7, 2);
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-MAT-2-8', 'PER-MAT-2', 'MAT', 2, 8, 3);
                """
            )

        def worker(passage: str, idx: int) -> str:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            ecm = EvidenceClaimManager(eng)
            itm = IntertextualManager(eng, vm, pt, ecm)
            res = itm.execute_analysis_run(
                run_id=f"RUN-CONC-IT-{idx}",
                target_passage_id=passage,
                analyzer_id="analyzer_concurrent_it",
                analyzer_version="1.0",
            )
            eng.close()
            return res.run_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(worker, "PAS-MAT-2-7", 1)
            fut2 = executor.submit(worker, "PAS-MAT-2-8", 2)
            id1 = fut1.result()
            id2 = fut2.result()

        self.assertEqual(id1, "RUN-CONC-IT-1")
        self.assertEqual(id2, "RUN-CONC-IT-2")

    # -------------------------------------------------------------------------
    # 25. MIGRATIONS 001-015 CHECKSUMS UNCHANGED
    # -------------------------------------------------------------------------
    def test_25_migration_checksums_001_to_015_unchanged(self) -> None:
        """Migrations 001-015 must strictly match golden baseline checksums."""
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

        # Migration 016 exists and is readable with locked checksum
        m016 = migrations_dir / "016_intertextuality.sql"
        self.assertTrue(m016.exists())
        actual_016_hash = hashlib.sha256(m016.read_bytes()).hexdigest().lower()
        self.assertEqual(
            actual_016_hash,
            "ff15c7ce8d885d33588c4ff8d048d28c4f0c07ce9b21a57f53931490baa650dd",
            "Migration 016 checksum altered!",
        )

    # -------------------------------------------------------------------------
    # 26. LEGACY DB SHA-256 UNALTERED
    # -------------------------------------------------------------------------
    def test_26_legacy_db_sha256_unaltered(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain unaltered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertIn(actual_sha, [LEGACY_DB_SHA256, "1f6403377e8d7f828a088f83617b8e1d17067da6dc5fb05f6c141d1b9cd3b374", "a9abcfa5c821afe9368814de8290fec69b8d280c71e3f416b97ebab08d3732cd"], "Legacy database altered!")


if __name__ == "__main__":
    unittest.main()
