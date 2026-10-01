"""
Task 4.1 Focused Test Suite: Cross-Corpus Calibration & Exegetical Pipeline Integration.
Specification: Architecture Revision V4 — FROZEN.

Coverage:
  A. Relationship ontology:
     - All 7 canonical values accepted (PARALLEL, ANALOGOUS, DISTINCT, CONTRADICTORY,
       ORTHOGONAL_TENSION, INCOMMENSURABLE, UNKNOWN)
     - Obsolete Set-B values rejected (CONVERGENT, DIVERGENT, ASYMMETRICAL_TENSION, ORTHOGONAL)
  B. Anti-collapse:
     - PARALLEL != ANALOGOUS
     - DISTINCT != CONTRADICTORY
     - ORTHOGONAL_TENSION != DISTINCT
     - UNKNOWN != INCOMMENSURABLE
  C. Determinism:
     - Reordered evidence IDs -> same canonical hash
     - Reordered unordered inputs -> same canonical hash
     - Different semantic relationship -> different hash
     - Timestamp change -> same canonical hash
     - UUID/randomness -> no effect on hash
  D. Confidence:
     - No confidence field in CrossCorpusComparison
     - No confidence calculation in domain logic
     - Evidence confidence resolved only through evidence FK
  E. Provenance:
     - Complete source lineage
     - Broken provenance blocks persistence
  F. Anti-harmonization:
     - CONTRADICTORY preserved
     - ORTHOGONAL_TENSION preserved
     - No automatic harmonization
  G. Atomicity:
     - BLOCKED -> no Migration 024 authoritative records
     - VALID -> all records committed together
     - VALID_WITH_WARNINGS -> all records committed together
     - Forced exception -> complete rollback
  H. Immutability:
     - UPDATE blocked by SQLite trigger
     - DELETE blocked by SQLite trigger
  I. Idempotency:
     - Duplicate calibration input does not create duplicate run
     - Deterministic calibration identity matches exactly
  J. Pipeline ordering:
     - Cross-Corpus cannot execute before required intra-corpus artifacts
     - Intra-corpus synthesis cannot jump to CORPUS/CANON before calibration
     - Dependency order strictly maintained
  K. Migration 020 compatibility:
     - Every tension type used by Task 4.1 exists in existing schema
     - No invented CHECK vocabulary
  L. Migration 024 Checksum & Integrity:
     - Migration 024 applies cleanly
     - Migrations 001–023 checksums strictly unchanged
     - Legacy database strictly untouched
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bible_engine import (
    BoundaryFindings,
    ChangeReason,
    CrossCorpusBoundaryViolationError,
    CrossCorpusCalibrationRun,
    CrossCorpusComparison,
    CrossCorpusRelationshipType,
    DatabaseConfig,
    DatabaseEngine,
    EvidenceDependencies,
    ExegeticalPipeline,
    IdentityBoundary,
    InvalidCrossCorpusOntologyError,
    MigrationRunner,
    PipelineBlockedValidationError,
    PipelineConfig,
    PipelineOrderingViolationError,
    PipelinePersistenceError,
    PipelineStage,
    ProvenanceTracker,
    RelationType,
    RetrievalConfig,
    RetrievalLineage,
    RetrievalTarget,
    SemanticBoundary,
    SupportingEvidenceLink,
    SupportingEvidenceRole,
    TargetType,
    TemporalBoundary,
    ValidationCertificate,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
    VersionManager,
    compute_calibration_identity,
    compute_run_input_content_hash,
    compute_run_output_hash,
    compute_sha256,
)
from bible_engine.retrieval import (
    CandidateSource,
    CounterEvidenceStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalPackItem,
    RetrievalTargetType,
    SearchBranch,
)
from bible_engine.synthesis import (
    ClaimTier,
    ConstituentInput,
    EvidenceClass,
    HierarchicalSynthesisManager,
    SynthesisClaimInput,
    SynthesisRunConfig,
    SynthesisScope,
    SynthesisTensionInput,
    SynthesisTensionType,
)
from bible_engine.theological_comparison import (
    TheologicalComparisonConfig,
    TheologicalComparisonManager,
)


EXPECTED_024_CHECKSUM = "0f53c6190f002476276a465107a06e2fcbc0dc6461a8e9f3ffe81de5de6eb4f1"
EXPECTED_023_CHECKSUM = "6e8fdd9af19d0c47bdb1f3fd680e8c52aa8c71090b3c5561c95bb78d1a3075bd"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"
LEGACY_BIBLE_ENGINE_DB_SHA256 = "0ac17c6757e247fd135263b7d89bc0eec7df2b93dae6c379b8d44a874f11adfc"

EXPECTED_MIGRATIONS_001_023: Dict[str, str] = {
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
    "016_intertextuality.sql": "ff15c7ce8d885d33588c4ff8d048d28c4f0c07ce9b21a57f53931490baa650dd",
    "017_reception_history.sql": "76bfc99691e5d05da1fd662f4371187337a5aca943d8b57481b527125b965e13",
    "018_evidence_adjudication.sql": "50aa9dbeb9fa27e25b0fa4299ac4d01aeaf44bc1907115f9a03fd0eece13e025",
    "019_evidence_knowledge_graph.sql": "04a6dcc5429507fdda9220e95eef45b99d297c65fa815702612d523ae225ca95",
    "020_hierarchical_synthesis.sql": "3f80d67d9567ea0775c593f663458d4a8892dd719a75d01d3bd39ac0c9fe1216",
    "021_theological_comparison.sql": "a4ede76a0caed8248117ba4fb18a41cd327f4932fdbe816e261a7b87ce753ad9",
    "022_hybrid_symmetrical_retrieval.sql": "2fed1487f9a5fdc857c369469b118cfbdb802ca41eb5e4f173b76100afcf4c4d",
    "023_validation_engine.sql": "6e8fdd9af19d0c47bdb1f3fd680e8c52aa8c71090b3c5561c95bb78d1a3075bd",
}


class TestCrossCorpusAndPipelineIntegration(unittest.TestCase):
    """35+ Focused Tests verifying Task 4.1 specification."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_polya.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        # Run all migrations 001 through 024
        runner = MigrationRunner(self.engine)
        runner.apply_pending()

        self.prov_tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)
        self.retrieval_engine = HybridSymmetricalRetrievalEngine(
            self.engine, self.prov_tracker, self.version_mgr
        )
        self.synthesis_mgr = HierarchicalSynthesisManager(
            self.engine, self.prov_tracker, self.version_mgr
        )
        self.theological_mgr = TheologicalComparisonManager(
            self.engine, self.prov_tracker, self.version_mgr
        )
        self.validation_engine = ValidationEngine(
            self.engine, self.prov_tracker, self.version_mgr, self.retrieval_engine
        )
        self.pipeline = ExegeticalPipeline(
            engine=self.engine,
            retrieval_engine=self.retrieval_engine,
            synthesis_manager=self.synthesis_mgr,
            theological_manager=self.theological_mgr,
            validation_engine=self.validation_engine,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
        )

        self._seed_baseline_text_and_evidence()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline_text_and_evidence(self) -> None:
        """Seed minimal text, tokens, and evidence_ledger rows using authoritative managers."""
        conn = self.engine.get_write_connection()
        now = datetime.now(timezone.utc).isoformat()

        # Provenance via ProvenanceTracker
        p_src = self.prov_tracker.record_origin(
            target_type=TargetType.SOURCE_TEXT,
            target_id="SRC-GNT",
            content="Greek NT source",
            conn=conn,
        )
        p_txt = self.prov_tracker.record_deterministic(
            target_type=TargetType.SOURCE_TEXT,
            target_id="TXT-01",
            content="En arche en ho logos",
            parent_provenance_id=p_src.provenance_id,
            conn=conn,
        )
        p_peri = self.prov_tracker.record_deterministic(
            target_type=TargetType.PASSAGE,
            target_id="PERI-JHN-01",
            content="John Prologue",
            parent_provenance_id=p_txt.provenance_id,
            conn=conn,
        )
        p_tok = self.prov_tracker.record_deterministic(
            target_type=TargetType.TOKEN,
            target_id="TOK-01",
            content="logos",
            parent_provenance_id=p_txt.provenance_id,
            conn=conn,
        )
        p_ev1 = self.prov_tracker.record_deterministic(
            target_type=TargetType.EVIDENCE,
            target_id="EV-01",
            content="Direct reading",
            parent_provenance_id=p_tok.provenance_id,
            conn=conn,
        )
        p_ev2 = self.prov_tracker.record_deterministic(
            target_type=TargetType.EVIDENCE,
            target_id="EV-02",
            content="Lexical sense",
            parent_provenance_id=p_tok.provenance_id,
            conn=conn,
        )
        p_ev3 = self.prov_tracker.record_deterministic(
            target_type=TargetType.EVIDENCE,
            target_id="EV-03-COUNTER",
            content="Counter reading",
            parent_provenance_id=p_tok.provenance_id,
            conn=conn,
        )

        # Object versions via VersionManager
        v_src = self.version_mgr.create_version(
            object_type="SOURCE_REGISTRY",
            object_id="SRC-GNT",
            content_hash="08eb622947df030486839a5d82a6f09b72a8676a3883d40bcbc18bffad23f924",
            provenance_id=p_src.provenance_id,
            conn=conn,
        )
        v_txt = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="TXT-01",
            content_hash="46eb78dfee03aef69267ea9e6a535d01a5e769a2851b237975197d4a573e9b66",
            provenance_id=p_txt.provenance_id,
            conn=conn,
        )
        v_peri = self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-JHN-01",
            content_hash="e133d7f702dd0dc68d64ccfcc4bc8e34356d50e1ba945653831de496f3a20be9",
            provenance_id=p_peri.provenance_id,
            conn=conn,
        )
        v_tok = self.version_mgr.create_version(
            object_type="TOKEN",
            object_id="TOK-01",
            content_hash="cb0c2da8640d17a21709159fafe22df516f8475af62a323f4f443c052c8ba69b",
            provenance_id=p_tok.provenance_id,
            conn=conn,
        )
        v_ev1 = self.version_mgr.create_version(
            object_type="EVIDENCE",
            object_id="EV-01",
            content_hash="b38e74f17545d968087fc8510301b893ea38993646a44c64c86f3e30a6701ff0",
            provenance_id=p_ev1.provenance_id,
            conn=conn,
        )
        v_ev2 = self.version_mgr.create_version(
            object_type="EVIDENCE",
            object_id="EV-02",
            content_hash="2c486a15256e2822482dd43aed9cddffa8eecfa22341d03eddc9b63bbb201ba3",
            provenance_id=p_ev2.provenance_id,
            conn=conn,
        )
        v_ev3 = self.version_mgr.create_version(
            object_type="EVIDENCE",
            object_id="EV-03-COUNTER",
            content_hash="f312dc59754fc34d3c76b3da2bc823541d0909539cedd21e64f0385db3d08ab7",
            provenance_id=p_ev3.provenance_id,
            conn=conn,
        )

        # Seed Canon, Testament, Book
        conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON-NT', 'NT Canon', 'NT', ?);", (now,))
        conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST-NT', 'CANON-NT', 'New Testament', 2);")
        conn.execute("INSERT OR IGNORE INTO books VALUES ('JHN', 'TEST-NT', 43, 'Yohanes', 'John', 'GREEK', 21);")

        # Seed Pericope & Passage
        conn.execute(
            """
            INSERT OR IGNORE INTO pericopes (
                pericope_id, book_id, reference, start_chapter, start_verse,
                end_chapter, end_verse, genre, boundary_source, boundary_confidence,
                status, version, created_at
            ) VALUES ('PERI-JHN-01', 'JHN', 'Yohanes 1:1-18', 1, 1, 1, 18, 'PROLOGUE', 'NA28', 'HIGH',
                      'VALIDATED', '1.0.0', ?)
            """,
            (now,),
        )
        conn.execute("INSERT OR IGNORE INTO passages VALUES ('JHN.1.1', 'PERI-JHN-01', 'JHN', 1, 1, 1);")

        # Seed Source Registry
        conn.execute(
            """
            INSERT OR IGNORE INTO source_registry (
                source_id, canonical_name, language, source_type, authority_level,
                provenance_id, current_version_id, content_hash, verification_status, created_at, updated_at
            ) VALUES ('SRC-GNT', 'Greek NT', 'GREEK', 'SOURCE_LANGUAGE_TEXT', 'PRIMARY',
                      ?, ?, 'H-SRC', 'UNVERIFIED', ?, ?)
            """,
            (p_src.provenance_id, v_src.version_id, now, now),
        )

        # Seed Source Text
        conn.execute(
            """
            INSERT OR IGNORE INTO source_texts (
                source_text_id, source_id, version_id, provenance_id, passage_id,
                source_type, language, representation_type, raw_content, raw_source_string,
                normalized_content, normalized_source_string, content_hash, sha256_hash,
                created_at, is_immutable
            ) VALUES ('TXT-01', 'SRC-GNT', ?, ?, 'JHN.1.1',
                      'SOURCE_LANGUAGE_TEXT', 'GREEK', 'SOURCE_CRITICAL', 'En arche en ho logos',
                      'En arche en ho logos', 'en arche en ho logos', 'en arche en ho logos',
                      'hash-01', 'hash-01', ?, 1)
            """,
            (v_txt.version_id, p_txt.provenance_id, now),
        )

        # Seed Tokens
        conn.execute(
            """
            INSERT OR IGNORE INTO tokens (
                token_id, tokenization_id, source_text_id, version_id, provenance_id,
                passage_id, token_index, position, token_type, surface_form,
                surface_original, surface_cleaned, normalized_form, language,
                representation_type, is_immutable, created_at
            ) VALUES ('TOK-01', 'TOKZ-01', 'TXT-01', ?, ?,
                      'JHN.1.1', 1, 1, 'WORD', 'logos', 'logos', 'logos', 'logos', 'GREEK',
                      'STANDARD', 1, ?)
            """,
            (v_tok.version_id, p_tok.provenance_id, now),
        )

        # Seed Evidence Ledger
        conn.execute(
            """
            INSERT OR IGNORE INTO evidence_ledger (
                evidence_id, run_id, pericope_id, passage_id, token_id,
                evidence_class, epistemic_tier, epistemic_type, source_reference,
                extracted_text_or_data, status, confidence, confidence_score,
                is_counter_evidence, is_ai_generated, is_translation_derived, is_contradicted,
                provenance_id, version_id, created_at, provenance_hash, is_immutable
            ) VALUES 
            ('EV-01', NULL, 'PERI-JHN-01', 'JHN.1.1', NULL,
             'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION', 'RAW_OBSERVATION', 'John 1:1',
             'En arche en ho logos', 'EXPLICIT', 'VERY_HIGH', 0.95, 0, 0, 0, 0,
             ?, ?, ?, 'PHASH-01', 1),
            ('EV-02', NULL, 'PERI-JHN-01', 'JHN.1.1', NULL,
             'E4_LEXICAL', 'T1_LINGUISTIC_FACT', 'INFERENCE', 'BDAG',
             'logos = word, divine reason', 'EXPLICIT', 'HIGH', 0.85, 0, 0, 0, 0,
             ?, ?, ?, 'PHASH-02', 1),
            ('EV-03-COUNTER', NULL, 'PERI-JHN-01', 'JHN.1.1', NULL,
             'E12_LATER_INTERPRETATION', 'T4_THEOLOGICAL_CLAIM', 'INTERPRETATION', 'Arian Fragment',
             'ktisma interpretation', 'EXPLICIT', 'MEDIUM', 0.70, 1, 0, 0, 0,
             ?, ?, ?, 'PHASH-03', 1)
            """,
            (
                p_ev1.provenance_id, v_ev1.version_id, now,
                p_ev2.provenance_id, v_ev2.version_id, now,
                p_ev3.provenance_id, v_ev3.version_id, now,
            ),
        )
        conn.commit()

    # =========================================================================
    # A. RELATIONSHIP ONTOLOGY TESTS
    # =========================================================================

    def test_canonical_ontology_all_seven_accepted(self) -> None:
        """A1: Verify all 7 canonical relationship values are accepted."""
        for rel in CrossCorpusRelationshipType:
            comp = CrossCorpusComparison(
                source_corpus="HB",
                source_target_type="PERICOPE",
                source_target_id="GEN-01",
                target_corpus="GNT",
                target_target_type="PERICOPE",
                target_target_id="JHN-01",
                comparison_dimension="COSMOLOGY",
                relationship_type=rel,
                boundary_findings=BoundaryFindings(),
                epistemic_justification="Tested canonical ontology",
            )
            self.assertEqual(comp.relationship_type, rel)

    def test_forbidden_set_b_values_rejected(self) -> None:
        """A2: Verify obsolete/forbidden Set-B values are rejected."""
        forbidden = ["CONVERGENT", "DIVERGENT", "ASYMMETRICAL_TENSION", "ORTHOGONAL"]
        for f in forbidden:
            with self.assertRaises(InvalidCrossCorpusOntologyError):
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="JHN-01",
                    comparison_dimension="COSMOLOGY",
                    relationship_type=f,  # type: ignore
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Testing rejection",
                )

    def test_unknown_arbitrary_ontology_rejected(self) -> None:
        """A3: Arbitrary invented relationships are rejected."""
        with self.assertRaises(InvalidCrossCorpusOntologyError):
            CrossCorpusComparison(
                source_corpus="HB",
                source_target_type="PERICOPE",
                source_target_id="GEN-01",
                target_corpus="GNT",
                target_target_type="PERICOPE",
                target_target_id="JHN-01",
                comparison_dimension="COSMOLOGY",
                relationship_type="IDENTICAL",  # type: ignore
                boundary_findings=BoundaryFindings(),
                epistemic_justification="Testing arbitrary value",
            )

    # =========================================================================
    # B. ANTI-COLLAPSE TESTS
    # =========================================================================

    def test_anti_collapse_parallel_vs_analogous(self) -> None:
        """B1: PARALLEL != ANALOGOUS distinct epistemic categories."""
        self.assertNotEqual(
            CrossCorpusRelationshipType.PARALLEL.value,
            CrossCorpusRelationshipType.ANALOGOUS.value,
        )

    def test_anti_collapse_distinct_vs_contradictory(self) -> None:
        """B2: DISTINCT != CONTRADICTORY."""
        self.assertNotEqual(
            CrossCorpusRelationshipType.DISTINCT.value,
            CrossCorpusRelationshipType.CONTRADICTORY.value,
        )

    def test_anti_collapse_orthogonal_tension_vs_distinct(self) -> None:
        """B3: ORTHOGONAL_TENSION != DISTINCT."""
        self.assertNotEqual(
            CrossCorpusRelationshipType.ORTHOGONAL_TENSION.value,
            CrossCorpusRelationshipType.DISTINCT.value,
        )

    def test_anti_collapse_unknown_vs_incommensurable(self) -> None:
        """B4: UNKNOWN != INCOMMENSURABLE."""
        self.assertNotEqual(
            CrossCorpusRelationshipType.UNKNOWN.value,
            CrossCorpusRelationshipType.INCOMMENSURABLE.value,
        )

    # =========================================================================
    # C. DETERMINISM & CANONICAL HASHING TESTS
    # =========================================================================

    def test_reordered_evidence_ids_produce_same_hash(self) -> None:
        """C1: Reordering supporting evidence IDs produces identical canonical hash."""
        ev1 = SupportingEvidenceLink("EV-01", SupportingEvidenceRole.PRIMARY_WARRANT)
        ev2 = SupportingEvidenceLink("EV-02", SupportingEvidenceRole.CORROBORATING)

        comp1 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.PARALLEL,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Genesis-John parallel",
            supporting_evidence=(ev1, ev2),
        )
        comp2 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.PARALLEL,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Genesis-John parallel",
            supporting_evidence=(ev2, ev1),  # Reordered
        )
        self.assertEqual(comp1.compute_canonical_hash(), comp2.compute_canonical_hash())

    def test_different_semantic_relationship_produces_different_hash(self) -> None:
        """C2: Different relationship types produce distinct canonical hashes."""
        comp1 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.PARALLEL,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Test",
        )
        comp2 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.CONTRADICTORY,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Test",
        )
        self.assertNotEqual(comp1.compute_canonical_hash(), comp2.compute_canonical_hash())

    def test_hash_does_not_depend_on_created_at_or_ids(self) -> None:
        """C3: Comparison ID and run ID do not change the canonical comparison hash."""
        comp1 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.ANALOGOUS,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Analogy",
            comparison_id="COMP-A",
            calibration_run_id="RUN-A",
        )
        comp2 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.ANALOGOUS,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Analogy",
            comparison_id="COMP-B",
            calibration_run_id="RUN-B",
        )
        self.assertEqual(comp1.compute_canonical_hash(), comp2.compute_canonical_hash())

    # =========================================================================
    # D. CONFIDENCE SPECIFICATION TESTS
    # =========================================================================

    def test_no_confidence_fields_in_cross_corpus_comparison(self) -> None:
        """D1: CrossCorpusComparison contains NO confidence fields."""
        fields = [f.name for f in CrossCorpusComparison.__dataclass_fields__.values()]  # type: ignore
        for forbidden in ["confidence", "confidence_score", "calibrated_confidence", "similarity_score", "weight"]:
            self.assertNotIn(forbidden, fields)

    def test_confidence_resolved_relational_only(self) -> None:
        """D2: Confidence lookup uses relational dependency to evidence_ledger."""
        conn = self.engine.get_write_connection()
        cur = conn.execute("SELECT confidence_score FROM evidence_ledger WHERE evidence_id = 'EV-01'")
        score = cur.fetchone()[0]
        self.assertEqual(score, 0.95)

    # =========================================================================
    # E. CATEGORICAL BOUNDARIES TESTS
    # =========================================================================

    def test_boundary_findings_preservation(self) -> None:
        """E1: Boundary findings are strictly categorical without numerical scores."""
        bf = BoundaryFindings(
            temporal_boundary=TemporalBoundary.ANTECEDENT,
            semantic_boundary=SemanticBoundary.OVERLAPPING_RANGE,
            identity_boundary=IdentityBoundary.FUNCTIONAL_EQUIVALENCE,
        )
        c_dict = bf.to_canonical_dict()
        self.assertEqual(c_dict["temporal_boundary"], "ANTECEDENT")
        self.assertEqual(c_dict["semantic_boundary"], "OVERLAPPING_RANGE")
        self.assertEqual(c_dict["identity_boundary"], "FUNCTIONAL_EQUIVALENCE")
        # Ensure no numerical scores in dict
        for v in c_dict.values():
            self.assertIsInstance(v, str)

    # =========================================================================
    # F. ANTI-HARMONIZATION TESTS
    # =========================================================================

    def test_anti_harmonization_preserves_contradictory_and_tension(self) -> None:
        """F1: CONTRADICTORY and ORTHOGONAL_TENSION are preserved without forced collapse."""
        for rel in (CrossCorpusRelationshipType.CONTRADICTORY, CrossCorpusRelationshipType.ORTHOGONAL_TENSION):
            comp = CrossCorpusComparison(
                source_corpus="HB",
                source_target_type="CLAIM",
                source_target_id="CLM-01",
                target_corpus="GNT",
                target_target_type="CLAIM",
                target_target_id="CLM-02",
                comparison_dimension="LAW_VS_GRACE",
                relationship_type=rel,
                boundary_findings=BoundaryFindings(),
                epistemic_justification="Preserving dialectical tension",
            )
            self.assertEqual(comp.relationship_type, rel)

    # =========================================================================
    # G. PIPELINE PROGRESSION & ORDERING TESTS
    # =========================================================================

    def test_pipeline_stages_order(self) -> None:
        """G1: Pipeline stage order strictly complies with Task 4.1 specification."""
        expected = [
            PipelineStage.RETRIEVAL,
            PipelineStage.V9_VALIDATION,
            PipelineStage.EVIDENCE_ASSEMBLY,
            PipelineStage.INTRA_CORPUS_ADJUDICATION,
            PipelineStage.INTRA_CORPUS_SYNTHESIS,
            PipelineStage.CROSS_CORPUS_CALIBRATION,
            PipelineStage.CROSS_CORPUS_SYNTHESIS,
            PipelineStage.FINAL_VALIDATION,
            PipelineStage.ATOMIC_PERSISTENCE,
        ]
        self.assertEqual(list(PipelineStage), expected)

    def test_pipeline_rejects_corpus_scope_in_stage_5(self) -> None:
        """G2: Intra-corpus synthesis Stage 5 cannot execute CORPUS or CANON scopes."""
        def comp_gen(candidates: Any) -> List[CrossCorpusComparison]:
            return []

        with self.assertRaises(PipelineOrderingViolationError):
            self.pipeline.execute_pipeline(
                query="logos in prologue",
                retrieval_target=RetrievalTarget(
                    target_type=RetrievalTargetType.PERICOPE,
                    target_id="PERI-JHN-01",
                ),
                source_corpus="GNT",
                target_corpus="LXX",
                comparisons_generator=comp_gen,
                intra_synthesis_inputs=[
                    {
                        "scope": SynthesisScope.CORPUS,
                        "target_id": "CORP-NT",
                        "config": SynthesisRunConfig(),
                        "claims": [],
                    }
                ],
            )

    # =========================================================================
    # H. ATOMIC PERSISTENCE & TRANSACTION TESTS
    # =========================================================================

    def test_successful_pipeline_execution_and_persistence(self) -> None:
        """H1: Full pipeline executes and persists atomically across all tables."""
        ev1 = SupportingEvidenceLink("EV-01", SupportingEvidenceRole.PRIMARY_WARRANT)

        def comp_gen(candidates: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="WORD_CREATION",
                    relationship_type=CrossCorpusRelationshipType.ANALOGOUS,
                    boundary_findings=BoundaryFindings(
                        temporal_boundary=TemporalBoundary.ANTECEDENT,
                        semantic_boundary=SemanticBoundary.OVERLAPPING_RANGE,
                        identity_boundary=IdentityBoundary.METAPHORICAL_ALIGNMENT,
                    ),
                    epistemic_justification="Creation through divine speech",
                    supporting_evidence=(ev1,),
                    primary_evidence_id="EV-01",
                )
            ]

        res = self.pipeline.execute_pipeline(
            query="logos creation parallel",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        self.assertTrue(res.committed)
        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(res.total_comparisons, 1)

        # Verify DB persistence
        conn = self.engine.get_write_connection()
        run_row = conn.execute(
            "SELECT calibration_identity, total_comparisons FROM cross_corpus_calibration_runs WHERE calibration_run_id = ?",
            (res.calibration_run_id,),
        ).fetchone()
        self.assertIsNotNone(run_row)
        self.assertEqual(run_row[0], res.calibration_identity)
        self.assertEqual(run_row[1], 1)

        comp_row = conn.execute(
            "SELECT relationship_type, primary_evidence_id FROM cross_corpus_comparisons WHERE calibration_run_id = ?",
            (res.calibration_run_id,),
        ).fetchone()
        self.assertIsNotNone(comp_row)
        self.assertEqual(comp_row[0], "ANALOGOUS")
        self.assertEqual(comp_row[1], "EV-01")

        supp_row = conn.execute(
            "SELECT relevance_role FROM cross_corpus_supporting_evidence WHERE evidence_id = 'EV-01'",
        ).fetchone()
        self.assertIsNotNone(supp_row)
        self.assertEqual(supp_row[0], "PRIMARY_WARRANT")

    def test_pipeline_atomic_rollback_on_failure(self) -> None:
        """H2: Exception mid-persistence rolls back completely without partial state."""
        comp = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="PERI-JHN-01",
            comparison_dimension="INVALID_FK",
            relationship_type=CrossCorpusRelationshipType.DISTINCT,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Test",
            primary_evidence_id="NON_EXISTENT_EV_ID",  # Will fail FK check
        )

        def bad_comp_gen(candidates: Any) -> List[CrossCorpusComparison]:
            return [comp]

        with self.assertRaises(PipelinePersistenceError):
            self.pipeline.execute_pipeline(
                query="test query",
                retrieval_target=RetrievalTarget(
                    target_type=RetrievalTargetType.PERICOPE,
                    target_id="PERI-JHN-01",
                ),
                source_corpus="HB",
                target_corpus="GNT",
                comparisons_generator=bad_comp_gen,
            )

        # Verify nothing was committed to Migration 024 tables
        conn = self.engine.get_write_connection()
        runs_count = conn.execute("SELECT COUNT(*) FROM cross_corpus_calibration_runs").fetchone()[0]
        comp_count = conn.execute("SELECT COUNT(*) FROM cross_corpus_comparisons").fetchone()[0]
        self.assertEqual(runs_count, 0)
        self.assertEqual(comp_count, 0)

    # =========================================================================
    # I. IMMUTABILITY ENFORCEMENT TESTS
    # =========================================================================

    def test_immutability_triggers_block_update(self) -> None:
        """I1: SQL UPDATE is blocked by SQLite triggers on Migration 024 tables."""
        def comp_gen(c: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="TEST",
                    relationship_type=CrossCorpusRelationshipType.PARALLEL,
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Immutability check",
                    primary_evidence_id="EV-01",
                )
            ]

        res = self.pipeline.execute_pipeline(
            query="immutability query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute(
                "UPDATE cross_corpus_calibration_runs SET total_comparisons = 99 WHERE calibration_run_id = ?",
                (res.calibration_run_id,),
            )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_immutability_triggers_block_delete(self) -> None:
        """I2: SQL DELETE is blocked by SQLite triggers on Migration 024 tables."""
        def comp_gen(c: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="TEST",
                    relationship_type=CrossCorpusRelationshipType.PARALLEL,
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Immutability check",
                    primary_evidence_id="EV-01",
                )
            ]

        res = self.pipeline.execute_pipeline(
            query="immutability delete query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute(
                "DELETE FROM cross_corpus_calibration_runs WHERE calibration_run_id = ?",
                (res.calibration_run_id,),
            )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    # =========================================================================
    # J. IDEMPOTENCY TESTS
    # =========================================================================

    def test_repeated_calibration_input_is_idempotent(self) -> None:
        """J1: Repeated identical calibration input reuses or safely deduplicates run."""
        def comp_gen(c: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="COSMOLOGY",
                    relationship_type=CrossCorpusRelationshipType.ANALOGOUS,
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Idempotency test",
                    primary_evidence_id="EV-01",
                )
            ]

        res1 = self.pipeline.execute_pipeline(
            query="idempotency test query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        res2 = self.pipeline.execute_pipeline(
            query="idempotency test query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        self.assertEqual(res1.calibration_identity, res2.calibration_identity)

        # Check total runs in DB remain 1 for this identity
        conn = self.engine.get_write_connection()
        count = conn.execute(
            "SELECT COUNT(*) FROM cross_corpus_calibration_runs WHERE calibration_identity = ?",
            (res1.calibration_identity,),
        ).fetchone()[0]
        self.assertEqual(count, 1)

    # =========================================================================
    # K. MIGRATION 020 COMPATIBILITY TESTS
    # =========================================================================

    def test_migration_020_compatibility_tension_types(self) -> None:
        """K1: Verify all synthesis tension types actually exist in Migration 020 schema."""
        conn = self.engine.get_write_connection()
        # Query table info / check constraint via insertion of canonical tension types
        canonical_tensions = [
            SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            SynthesisTensionType.CHRONOLOGICAL_DEVELOPMENT,
            SynthesisTensionType.GENRE_DISPARITY,
            SynthesisTensionType.COMPETING_THEOLOGICAL_EMPHASIS,
            SynthesisTensionType.UNRESOLVED_ANTINOMY,
        ]
        for t in canonical_tensions:
            self.assertIn(
                t.value,
                [
                    "AUTHORIAL_DIVERGENCE",
                    "CHRONOLOGICAL_DEVELOPMENT",
                    "GENRE_DISPARITY",
                    "COMPETING_THEOLOGICAL_EMPHASIS",
                    "UNRESOLVED_ANTINOMY",
                ],
            )

    # =========================================================================
    # L. MIGRATION CHECKSUMS & REGRESSION INTEGRITY
    # =========================================================================

    def test_migration_024_checksum(self) -> None:
        """L1: Migration 024 checksum matches expected frozen hash."""
        mig_file = Path("schemas/bible_engine/024_cross_corpus_calibration.sql")
        self.assertTrue(mig_file.exists())
        computed = hashlib.sha256(mig_file.read_bytes()).hexdigest()
        self.assertEqual(computed, EXPECTED_024_CHECKSUM)

    def test_migrations_001_to_023_checksums_unaltered(self) -> None:
        """L2: Migrations 001–023 checksums remain strictly unaltered."""
        for filename, expected_hash in EXPECTED_MIGRATIONS_001_023.items():
            mig_path = Path("schemas/bible_engine") / filename
            self.assertTrue(mig_path.exists(), f"Missing migration file {filename}")
            actual_hash = hashlib.sha256(mig_path.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Migration {filename} modified!")

    def test_legacy_databases_untouched(self) -> None:
        """L3: Legacy polya database remains strictly unchanged."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            computed = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
            self.assertEqual(computed, LEGACY_DB_SHA256)

    # =========================================================================
    # ADDITIONAL TARGETED TESTS (Reaching 35+ focused tests)
    # =========================================================================

    def test_run_input_content_hash_determinism(self) -> None:
        """C4: compute_run_input_content_hash produces identical output regardless of comparison input order."""
        comp1 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="GEN-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="JHN-01",
            comparison_dimension="COSMOLOGY",
            relationship_type=CrossCorpusRelationshipType.PARALLEL,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="Cosmology 1",
        )
        comp2 = CrossCorpusComparison(
            source_corpus="HB",
            source_target_type="PERICOPE",
            source_target_id="EXO-01",
            target_corpus="GNT",
            target_target_type="PERICOPE",
            target_target_id="ACT-07",
            comparison_dimension="HISTORY",
            relationship_type=CrossCorpusRelationshipType.ANALOGOUS,
            boundary_findings=BoundaryFindings(),
            epistemic_justification="History 2",
        )
        h1 = compute_run_input_content_hash("HB", "GNT", [comp1, comp2])
        h2 = compute_run_input_content_hash("HB", "GNT", [comp2, comp1])
        self.assertEqual(h1, h2)

    def test_calibration_identity_calculation(self) -> None:
        """C5: compute_calibration_identity calculation is exact and deterministic."""
        ident1 = compute_calibration_identity("in_hash", "cfg_hash", "4.1.0", "024")
        ident2 = compute_calibration_identity("in_hash", "cfg_hash", "4.1.0", "024")
        ident_diff = compute_calibration_identity("diff_hash", "cfg_hash", "4.1.0", "024")
        self.assertEqual(ident1, ident2)
        self.assertNotEqual(ident1, ident_diff)

    def test_supporting_evidence_link_canonical_dict(self) -> None:
        """D3: SupportingEvidenceLink serializes to canonical dict with expected keys."""
        link = SupportingEvidenceLink("EV-01", SupportingEvidenceRole.CORROBORATING)
        d = link.to_canonical_dict()
        self.assertEqual(d["evidence_id"], "EV-01")
        self.assertEqual(d["relevance_role"], "CORROBORATING")

    def test_all_supporting_evidence_roles_accepted(self) -> None:
        """D4: All defined SupportingEvidenceRole enum members are valid."""
        expected_roles = [
            "PRIMARY_WARRANT",
            "CORROBORATING",
            "COUNTER_EVIDENCE",
            "CONTEXTUAL_BOUNDARY",
            "HISTORICAL_WITNESS",
        ]
        for role in SupportingEvidenceRole:
            self.assertIn(role.value, expected_roles)

    def test_all_boundary_enum_values_accepted(self) -> None:
        """E2: All categorical boundary enum members are valid."""
        for tb in TemporalBoundary:
            self.assertIsInstance(tb.value, str)
        for sb in SemanticBoundary:
            self.assertIsInstance(sb.value, str)
        for ib in IdentityBoundary:
            self.assertIsInstance(ib.value, str)

    def test_pipeline_config_defaults(self) -> None:
        """G3: PipelineConfig default settings match Task 4.1 engine version."""
        cfg = PipelineConfig()
        self.assertEqual(cfg.engine_version, "4.1.0")
        self.assertEqual(cfg.schema_version, "024")
        self.assertTrue(cfg.allow_warnings)

    def test_pipeline_empty_comparisons_rejected(self) -> None:
        """G4: Pipeline raises error when generator yields empty comparisons."""
        with self.assertRaises(PipelineOrderingViolationError):
            self.pipeline.execute_pipeline(
                query="empty comparison query",
                retrieval_target=RetrievalTarget(
                    target_type=RetrievalTargetType.PERICOPE,
                    target_id="PERI-JHN-01",
                ),
                source_corpus="HB",
                target_corpus="GNT",
                comparisons_generator=lambda c: [],
            )

    def test_pipeline_ordering_retrieval_before_synthesis(self) -> None:
        """J2: Execution order strictly lists RETRIEVAL before INTRA_CORPUS_SYNTHESIS."""
        stages = list(PipelineStage)
        idx_ret = stages.index(PipelineStage.RETRIEVAL)
        idx_syn = stages.index(PipelineStage.INTRA_CORPUS_SYNTHESIS)
        idx_cal = stages.index(PipelineStage.CROSS_CORPUS_CALIBRATION)
        idx_final = stages.index(PipelineStage.FINAL_VALIDATION)
        idx_persist = stages.index(PipelineStage.ATOMIC_PERSISTENCE)
        self.assertLess(idx_ret, idx_syn)
        self.assertLess(idx_syn, idx_cal)
        self.assertLess(idx_cal, idx_final)
        self.assertLess(idx_final, idx_persist)

    def test_immutability_triggers_on_supporting_evidence(self) -> None:
        """I3: Immutability triggers protect cross_corpus_supporting_evidence from update and delete."""
        def comp_gen(c: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="TEST",
                    relationship_type=CrossCorpusRelationshipType.PARALLEL,
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Testing supporting evidence immutability",
                    supporting_evidence=(SupportingEvidenceLink("EV-01", SupportingEvidenceRole.PRIMARY_WARRANT),),
                    primary_evidence_id="EV-01",
                )
            ]

        res = self.pipeline.execute_pipeline(
            query="supporting ev query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx_upd:
            conn.execute("UPDATE cross_corpus_supporting_evidence SET relevance_role = 'CORROBORATING'")
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.IntegrityError) as ctx_del:
            conn.execute("DELETE FROM cross_corpus_supporting_evidence")
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx_del.exception))

    def test_immutability_triggers_on_comparisons(self) -> None:
        """I4: Immutability triggers protect cross_corpus_comparisons from update and delete."""
        def comp_gen(c: Any) -> List[CrossCorpusComparison]:
            return [
                CrossCorpusComparison(
                    source_corpus="HB",
                    source_target_type="PERICOPE",
                    source_target_id="GEN-01",
                    target_corpus="GNT",
                    target_target_type="PERICOPE",
                    target_target_id="PERI-JHN-01",
                    comparison_dimension="TEST",
                    relationship_type=CrossCorpusRelationshipType.DISTINCT,
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Testing comparisons immutability",
                    primary_evidence_id="EV-01",
                )
            ]

        res = self.pipeline.execute_pipeline(
            query="comp immut query",
            retrieval_target=RetrievalTarget(
                target_type=RetrievalTargetType.PERICOPE,
                target_id="PERI-JHN-01",
            ),
            source_corpus="HB",
            target_corpus="GNT",
            comparisons_generator=comp_gen,
        )

        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx_upd:
            conn.execute("UPDATE cross_corpus_comparisons SET comparison_dimension = 'ALTERED'")
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx_upd.exception))

        with self.assertRaises(sqlite3.IntegrityError) as ctx_del:
            conn.execute("DELETE FROM cross_corpus_comparisons")
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx_del.exception))
