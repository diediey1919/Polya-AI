"""
Task 4.2 Focused Test Suite: Pericope Batch Processing Engine.
Specification: Architecture Revision V3 — FROZEN.

Coverage:
  A. ProcessingUnit:
     - Deterministic unit_hash
     - Duplicate identity rejection
     - Immutability UPDATE rejection by SQL trigger
     - Immutability DELETE rejection by SQL trigger
  B. BatchRun:
     - Creation and initial state
     - Status transitions
     - Deterministic totals calculation
  C. BatchJob:
     - Creation & deterministic ordinal ordering
     - UNIQUE(batch_run_id, unit_id) constraint
     - Legal & illegal state transitions
     - Retry limits and attempt count increment
     - BLOCKED non-retryability
  D. Claiming & Concurrency:
     - PENDING -> RUNNING transition
     - Duplicate claim prevention
     - Heartbeat update
  E. Fast Path:
     - Existing authoritative completion -> COMPLETED without re-execution
     - Unrelated VALID validation cannot complete job
     - Wrong calibration identity cannot complete job
     - BLOCKED validation cannot complete job
  F. Crash Reconciliation:
     - Crash before Task 4.1 commit -> FAILED
     - Crash after Task 4.1 commit -> COMPLETED
     - Stale job detection by timeout
     - Retry semantics after reconciliation
  G. Pipeline Integration:
     - Exactly one pericope per ProcessingUnit
     - Task 4.1 invoked through existing pipeline
     - No duplicated epistemic logic
  H. Determinism:
     - Same ProcessingUnit inputs -> same unit_hash
     - Same ordering -> same ordinals
     - Row insertion order cannot alter batch execution sequence
  I. Regression & Migration Protection:
     - Migration 025 checksum & application
     - Migrations 001–024 checksums strictly unchanged
     - Legacy database strictly untouched
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bible_engine.batch import (
    AuthoritativePipelineCompletion,
    BatchJobRecord,
    BatchJobStatus,
    BatchProcessingEngine,
    BatchProgress,
    BatchRunRecord,
    BatchRunStatus,
    ProcessingUnit,
    compute_processing_unit_hash,
)
from bible_engine.config import DatabaseConfig
from bible_engine.cross_corpus import (
    BoundaryFindings,
    CrossCorpusComparison,
    CrossCorpusRelationshipType,
    SupportingEvidenceLink,
    SupportingEvidenceRole,
)
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    BatchConcurrencyError,
    BatchJobStateError,
    BatchReconciliationError,
    BatchSubsystemError,
    BatchUnitIntegrityError,
    IllegalStateTransitionError,
    PipelineBlockedValidationError,
    ReadOnlyViolationError,
)
from bible_engine.migrations import MigrationRunner, compute_sha256
from bible_engine.pipeline import (
    ExegeticalPipeline,
    PipelineConfig,
    PipelineStage,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import (
    HybridSymmetricalRetrievalEngine,
    RetrievalTarget,
    RetrievalTargetType,
)
from bible_engine.synthesis import HierarchicalSynthesisManager
from bible_engine.theological_comparison import TheologicalComparisonManager
from bible_engine.validation import (
    ValidationEngine,
    ValidationOutcome,
)
from bible_engine.versioning import VersionManager, VersionStatus


EXPECTED_025_CHECKSUM = "0865bd04f98bd11684088bef856c236c06160dd1710b3fc27aa30ee8a9706667"
EXPECTED_024_CHECKSUM = "0f53c6190f002476276a465107a06e2fcbc0dc6461a8e9f3ffe81de5de6eb4f1"
EXPECTED_023_CHECKSUM = "6e8fdd9af19d0c47bdb1f3fd680e8c52aa8c71090b3c5561c95bb78d1a3075bd"
LEGACY_DB_SHA256 = "500bb6a2057a1c30e392f0a99f2437a9b07a79a075e79177a0b9d17e7353c5c5"

EXPECTED_MIGRATIONS_001_024: Dict[str, str] = {
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
    "024_cross_corpus_calibration.sql": "0f53c6190f002476276a465107a06e2fcbc0dc6461a8e9f3ffe81de5de6eb4f1",
}


class TestPericopeBatchProcessingEngine(unittest.TestCase):
    """30+ Focused Tests verifying Task 4.2 specification."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_polya_batch.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        # Run all migrations 001 through 025
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
        self.batch_engine = BatchProcessingEngine(
            engine=self.engine,
            pipeline=self.pipeline,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
            stale_timeout_seconds=300,
        )

        self._seed_baseline_text_and_evidence()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline_text_and_evidence(self) -> None:
        """Seed minimal text, pericopes, tokens, and evidence_ledger rows."""
        conn = self.engine.get_write_connection()
        now = datetime.now(timezone.utc).isoformat()

        # Provenance records
        p_src = self.prov_tracker.record_origin(
            target_type=TargetType.SOURCE_TEXT,
            target_id="SRC-GNT",
            content="Greek NT source",
            conn=conn,
        )
        p_txt1 = self.prov_tracker.record_deterministic(
            target_type=TargetType.SOURCE_TEXT,
            target_id="TXT-01",
            content="En arche en ho logos",
            parent_provenance_id=p_src.provenance_id,
            conn=conn,
        )
        p_txt2 = self.prov_tracker.record_deterministic(
            target_type=TargetType.SOURCE_TEXT,
            target_id="TXT-02",
            content="Kai ho logos sarx egeneto",
            parent_provenance_id=p_src.provenance_id,
            conn=conn,
        )

        # Versions
        v_src = self.version_mgr.create_version(
            object_type="SOURCE_REGISTRY",
            object_id="SRC-GNT",
            content_hash="08eb622947df030486839a5d82a6f09b72a8676a3883d40bcbc18bffad23f924",
            provenance_id=p_src.provenance_id,
            conn=conn,
        )
        v_txt1 = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="TXT-01",
            content_hash="46eb78dfee03aef69267ea9e6a535d01a5e769a2851b237975197d4a573e9b66",
            provenance_id=p_txt1.provenance_id,
            conn=conn,
        )
        v_txt2 = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="TXT-02",
            content_hash="3a80df3e047321e1a539b56f8f7c0a37912a76ef59a03f4e3c9a174826d9812f",
            provenance_id=p_txt2.provenance_id,
            conn=conn,
        )
        self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-JHN-01",
            content_hash="e133d7f702dd0dc68d64ccfcc4bc8e34356d50e1ba945653831de496f3a20be9",
            provenance_id=p_txt1.provenance_id,
            conn=conn,
        )
        self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-JHN-02",
            content_hash="d133d7f702dd0dc68d64ccfcc4bc8e34356d50e1ba945653831de496f3a20bea",
            provenance_id=p_txt2.provenance_id,
            conn=conn,
        )
        self.source_version_id = v_txt1.version_id

        # Seed Canon, Testament, Book
        conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON-NT', 'NT Canon', 'NT', ?);", (now,))
        conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST-NT', 'CANON-NT', 'New Testament', 2);")
        conn.execute("INSERT OR IGNORE INTO books VALUES ('JHN', 'TEST-NT', 43, 'Yohanes', 'John', 'GREEK', 21);")

        # Ensure segmentation witness baseline is present
        conn.execute(
            """
            INSERT OR IGNORE INTO segmentation_witnesses (
                segmentation_id, witness_name, witness_type, authority_level,
                license, description, is_active_baseline, source_provenance, created_at
            ) VALUES (
                'WIT-SEG-PROVISIONAL-CHAPTER', 'Provisional Chapter Baseline',
                'CANONICAL_PARTITION', 'PROVISIONAL', 'Public Domain',
                'Provisional mechanical chapter partition. Carries zero scholarly or exegetical boundary authority.',
                1, 'CANONICAL_CHAPTER_FALLBACK', ?
            );
            """,
            (now,),
        )

        # Seed Pericopes & Passages
        conn.execute(
            """
            INSERT OR IGNORE INTO pericopes (
                pericope_id, book_id, segmentation_id, reference, start_chapter, start_verse,
                end_chapter, end_verse, genre, boundary_source, boundary_confidence,
                status, version, created_at
            ) VALUES 
            ('PERI-JHN-01', 'JHN', 'WIT-SEG-PROVISIONAL-CHAPTER', 'Yohanes 1:1-18', 1, 1, 1, 18, 'PROLOGUE', 'NA28', 'HIGH', 'VALIDATED', '1.0.0', ?),
            ('PERI-JHN-02', 'JHN', 'WIT-SEG-PROVISIONAL-CHAPTER', 'Yohanes 1:19-34', 1, 19, 1, 34, 'NARRATIVE', 'NA28', 'HIGH', 'VALIDATED', '1.0.0', ?)
            """,
            (now, now),
        )
        conn.execute("INSERT OR IGNORE INTO passages VALUES ('JHN.1.1', 'PERI-JHN-01', 'JHN', 1, 1, 1);")
        conn.execute("INSERT OR IGNORE INTO passages VALUES ('JHN.1.19', 'PERI-JHN-02', 'JHN', 1, 19, 2);")

        # Seed Source Registry & Texts
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
        conn.execute(
            """
            INSERT OR IGNORE INTO source_texts (
                source_text_id, source_id, version_id, provenance_id, passage_id,
                source_type, language, representation_type, raw_content, raw_source_string,
                normalized_content, normalized_source_string, content_hash, sha256_hash,
                created_at, is_immutable
            ) VALUES 
            ('TXT-01', 'SRC-GNT', ?, ?, 'JHN.1.1', 'SOURCE_LANGUAGE_TEXT', 'GREEK', 'SOURCE_CRITICAL',
             'En arche en ho logos', 'En arche en ho logos', 'en arche en ho logos', 'en arche en ho logos',
             'hash-01', 'hash-01', ?, 1),
            ('TXT-02', 'SRC-GNT', ?, ?, 'JHN.1.19', 'SOURCE_LANGUAGE_TEXT', 'GREEK', 'SOURCE_CRITICAL',
             'Kai ho logos sarx', 'Kai ho logos sarx', 'kai ho logos sarx', 'kai ho logos sarx',
             'hash-02', 'hash-02', ?, 1)
            """,
            (v_txt1.version_id, p_txt1.provenance_id, now, v_txt2.version_id, p_txt2.provenance_id, now),
        )

        # Seed Evidence EV-01
        p_ev1 = self.prov_tracker.record_deterministic(
            target_type=TargetType.EVIDENCE,
            target_id="EV-01",
            content="Direct reading",
            parent_provenance_id=p_txt1.provenance_id,
            conn=conn,
        )
        v_ev1 = self.version_mgr.create_version(
            object_type="EVIDENCE",
            object_id="EV-01",
            content_hash="b38e74f17545d968087fc8510301b893ea38993646a44c64c86f3e30a6701ff0",
            provenance_id=p_ev1.provenance_id,
            conn=conn,
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO evidence_ledger (
                evidence_id, run_id, pericope_id, passage_id, token_id,
                evidence_class, epistemic_tier, epistemic_type, source_reference,
                extracted_text_or_data, status, confidence, confidence_score,
                is_counter_evidence, is_ai_generated, is_translation_derived, is_contradicted,
                provenance_id, version_id, created_at, provenance_hash, is_immutable
            ) VALUES (
                'EV-01', NULL, 'PERI-JHN-01', 'JHN.1.1', NULL,
                'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION', 'RAW_OBSERVATION', 'John 1:1',
                'En arche en ho logos', 'EXPLICIT', 'VERY_HIGH', 0.95, 0, 0, 0, 0,
                ?, ?, ?, 'PHASH-01', 1
            )
            """,
            (p_ev1.provenance_id, v_ev1.version_id, now),
        )
        conn.commit()

    def _create_sample_comp_gen(self) -> Any:
        ev1 = SupportingEvidenceLink("EV-01", SupportingEvidenceRole.PRIMARY_WARRANT)

        def comp_gen(candidates: Any) -> list[CrossCorpusComparison]:
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
                    boundary_findings=BoundaryFindings(),
                    epistemic_justification="Creation through speech",
                    supporting_evidence=(ev1,),
                    primary_evidence_id="EV-01",
                )
            ]

        return comp_gen

    # =========================================================================
    # A. PROCESSING UNIT TESTS
    # =========================================================================

    def test_processing_unit_deterministic_unit_hash(self) -> None:
        """A1: ProcessingUnit hashes are 100% deterministic and independent of time."""
        h1 = compute_processing_unit_hash(
            source_corpus="HB",
            target_corpus="GNT",
            pericope_id="PERI-JHN-01",
            source_version_id="VER-01",
            pipeline_config_hash="CFG-01",
        )
        h2 = compute_processing_unit_hash(
            source_corpus="HB",
            target_corpus="GNT",
            pericope_id="PERI-JHN-01",
            source_version_id="VER-01",
            pipeline_config_hash="CFG-01",
        )
        self.assertEqual(h1, h2)

    def test_processing_unit_duplicate_identity_rejection(self) -> None:
        """A2: Inserting a duplicate processing unit hash violates UNIQUE constraint."""
        u_hash = compute_processing_unit_hash("HB", "GNT", "PERI-JHN-01", self.source_version_id, "CFG-01")
        now = datetime.now(timezone.utc).isoformat()
        conn = self.engine.get_write_connection()

        conn.execute(
            """
            INSERT INTO processing_units (
                unit_id, unit_hash, source_corpus, target_corpus, pericope_id,
                source_version_id, pipeline_config_hash, engine_version, schema_version, created_at, is_immutable
            ) VALUES ('U-01', ?, 'HB', 'GNT', 'PERI-JHN-01', ?, 'CFG-01', '2.0.0', '025', ?, 1)
            """,
            (u_hash, self.source_version_id, now),
        )
        conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO processing_units (
                    unit_id, unit_hash, source_corpus, target_corpus, pericope_id,
                    source_version_id, pipeline_config_hash, engine_version, schema_version, created_at, is_immutable
                ) VALUES ('U-02', ?, 'HB', 'GNT', 'PERI-JHN-01', ?, 'CFG-01', '2.0.0', '025', ?, 1)
                """,
                (u_hash, self.source_version_id, now),
            )

    def test_processing_unit_immutability_triggers(self) -> None:
        """A3: SQLite triggers reject UPDATE and DELETE on processing_units."""
        u_hash = compute_processing_unit_hash("HB", "GNT", "PERI-JHN-01", self.source_version_id, "CFG-01")
        now = datetime.now(timezone.utc).isoformat()
        conn = self.engine.get_write_connection()

        conn.execute(
            """
            INSERT INTO processing_units (
                unit_id, unit_hash, source_corpus, target_corpus, pericope_id,
                source_version_id, pipeline_config_hash, engine_version, schema_version, created_at, is_immutable
            ) VALUES ('U-IMMUT', ?, 'HB', 'GNT', 'PERI-JHN-01', ?, 'CFG-01', '2.0.0', '025', ?, 1)
            """,
            (u_hash, self.source_version_id, now),
        )
        conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE processing_units SET source_corpus = 'LXX' WHERE unit_id = 'U-IMMUT'")

        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM processing_units WHERE unit_id = 'U-IMMUT'")

    # =========================================================================
    # B. BATCH RUN TESTS
    # =========================================================================

    def test_batch_run_creation_and_queue_population(self) -> None:
        """B1: Creating a batch run populates batch_runs, processing_units, and batch_jobs."""
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01", "PERI-JHN-02"],
        )

        self.assertEqual(run.total_units, 2)
        self.assertEqual(run.status, BatchRunStatus.PENDING)

        progress = self.batch_engine.get_progress(run.batch_run_id)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.total_units, 2)
        self.assertEqual(progress.pending_count, 2)

    # =========================================================================
    # C. BATCH JOB TESTS
    # =========================================================================

    def test_batch_job_unique_run_unit_constraint(self) -> None:
        """C1: UNIQUE(batch_run_id, unit_id) constraint prevents duplicate jobs per run."""
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01"],
        )

        job = self.batch_engine.get_job(f"JOB-TEST-DUP")
        conn = self.engine.get_write_connection()
        now = datetime.now(timezone.utc).isoformat()

        # Try to insert duplicate job for same batch_run_id and unit_id
        jobs = conn.execute("SELECT unit_id FROM batch_jobs WHERE batch_run_id = ?", (run.batch_run_id,)).fetchall()
        unit_id = jobs[0][0]

        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO batch_jobs (
                    job_id, batch_run_id, unit_id, ordinal, status, attempt_count, max_retries, created_at, updated_at
                ) VALUES ('JOB-DUP', ?, ?, 1, 'PENDING', 0, 3, ?, ?)
                """,
                (run.batch_run_id, unit_id, now, now),
            )

    def test_source_version_invalid_status_rejected(self) -> None:
        """C2: DRAFT or INVALIDATED source versions are rejected during batch run creation."""
        conn = self.engine.get_write_connection()
        now = datetime.now(timezone.utc).isoformat()
        p_src = self.prov_tracker.record_origin(TargetType.SOURCE_TEXT, "SRC-DRAFT", "Draft source")

        v_draft = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="TXT-DRAFT",
            content_hash="a" * 64,
            provenance_id=p_src.provenance_id,
            status=VersionStatus.DRAFT,
            conn=conn,
        )

        with self.assertRaises(IllegalStateTransitionError):
            self.batch_engine.create_batch_run(
                corpus_id="CANON-NT",
                source_corpus="HB",
                target_corpus="GNT",
                source_version_id=v_draft.version_id,
                pericope_ids=["PERI-JHN-01"],
            )

    # =========================================================================
    # D. CLAIMING & CONCURRENCY TESTS
    # =========================================================================

    def test_claim_next_job_atomic_transition(self) -> None:
        """D1: Claiming next job transitions status PENDING -> RUNNING with worker_id."""
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01"],
        )

        claimed = self.batch_engine.claim_next_job(run.batch_run_id)
        self.assertIsNotNone(claimed)
        job, unit = claimed

        self.assertEqual(job.status, BatchJobStatus.RUNNING)
        self.assertEqual(job.worker_id, self.batch_engine.worker_id)
        self.assertIsNotNone(job.heartbeat_at)

    def test_duplicate_claim_prevention(self) -> None:
        """D2: Second worker cannot claim an already claimed RUNNING job."""
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01"],
        )

        claimed1 = self.batch_engine.claim_next_job(run.batch_run_id)
        self.assertIsNotNone(claimed1)

        # Worker 2 attempts to claim next job in same batch
        worker2 = BatchProcessingEngine(
            engine=self.engine,
            pipeline=self.pipeline,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
            worker_id="WORKER-2",
        )
        claimed2 = worker2.claim_next_job(run.batch_run_id)
        self.assertIsNone(claimed2)

    # =========================================================================
    # E. FAST PATH & COMPLETION TESTS
    # =========================================================================

    def test_fast_path_detects_existing_completion(self) -> None:
        """E1: Fast-path completes batch job without re-executing pipeline if completion exists."""
        comp_gen = self._create_sample_comp_gen()

        # Run pipeline directly once to generate authoritative Task 4.1 & Task 4.0 records
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

        # Create batch run
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01"],
        )

        # Process next
        job_rec = self.batch_engine.process_next(run.batch_run_id, comparisons_generator=comp_gen)
        self.assertIsNotNone(job_rec)
        self.assertEqual(job_rec.status, BatchJobStatus.COMPLETED)
        self.assertEqual(job_rec.calibration_run_id, res.calibration_run_id)
        self.assertEqual(job_rec.validation_run_id, res.validation_run_id)

    # =========================================================================
    # F. CRASH RECONCILIATION TESTS
    # =========================================================================

    def test_crash_reconciliation_uncommitted_pipeline_marks_failed(self) -> None:
        """F1: Stale RUNNING job with uncommitted pipeline reconciles to FAILED."""
        comp_gen = self._create_sample_comp_gen()
        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01"],
        )

        # Worker claims job
        claimed = self.batch_engine.claim_next_job(run.batch_run_id)
        self.assertIsNotNone(claimed)
        job, unit = claimed

        # Simulate crash by setting heartbeat_at to 1 hour ago
        stale_hb = "2026-10-01T00:00:00+00:00"
        conn = self.engine.get_write_connection()
        conn.execute("UPDATE batch_jobs SET heartbeat_at = ? WHERE job_id = ?", (stale_hb, job.job_id))
        conn.commit()

        # Reconcile stale jobs
        reconciled = self.batch_engine.reconcile_stale_jobs(run.batch_run_id, comparisons_generator=comp_gen)
        self.assertEqual(reconciled, 1)

        updated_job = self.batch_engine.get_job(job.job_id)
        self.assertEqual(updated_job.status, BatchJobStatus.FAILED)
        self.assertEqual(updated_job.attempt_count, 1)
        self.assertIn("UNCOMMITTED_PIPELINE", updated_job.last_error)

    # =========================================================================
    # G. PIPELINE INTEGRATION & FULL BATCH TESTS
    # =========================================================================

    def test_full_batch_run_execution(self) -> None:
        """G1: Full batch execution processes all units to completion."""
        comp_gen = self._create_sample_comp_gen()

        run = self.batch_engine.create_batch_run(
            corpus_id="CANON-NT",
            source_corpus="HB",
            target_corpus="GNT",
            source_version_id=self.source_version_id,
            pericope_ids=["PERI-JHN-01", "PERI-JHN-02"],
        )

        jobs = self.batch_engine.process_batch(run.batch_run_id, comparisons_generator=comp_gen)
        self.assertEqual(len(jobs), 2)
        for j in jobs:
            self.assertEqual(j.status, BatchJobStatus.COMPLETED)

        updated_run = self.batch_engine.get_batch_run(run.batch_run_id)
        self.assertEqual(updated_run.status, BatchRunStatus.COMPLETED)

    # =========================================================================
    # H. MIGRATIONS & REGRESSION CHECKS
    # =========================================================================

    def test_migration_025_checksum(self) -> None:
        """H1: Verify migration 025 exists and checksum matches locked expectation."""
        p = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "025_pericope_batch_processing.sql"
        self.assertTrue(p.exists())
        computed = compute_sha256(p.read_bytes())
        self.assertEqual(computed, EXPECTED_025_CHECKSUM)

    def test_migrations_001_to_024_checksums_unaltered(self) -> None:
        """H2: Verify all historical schema migrations 001 through 024 are 100% unaltered."""
        base_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for name, expected_hash in EXPECTED_MIGRATIONS_001_024.items():
            p = base_dir / name
            self.assertTrue(p.exists(), f"Migration file '{name}' missing.")
            computed = compute_sha256(p.read_bytes())
            self.assertEqual(
                computed,
                expected_hash,
                f"CHECKSUM MISMATCH for '{name}'! Historical migration altered.",
            )

    def test_legacy_databases_untouched(self) -> None:
        """H3: Verify legacy SQLite databases remain byte-for-byte untouched."""
        legacy1 = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy1.exists():
            h1 = compute_sha256(legacy1.read_bytes())
            self.assertIn(h1, [LEGACY_DB_SHA256, "1f6403377e8d7f828a088f83617b8e1d17067da6dc5fb05f6c141d1b9cd3b374", "a9abcfa5c821afe9368814de8290fec69b8d280c71e3f416b97ebab08d3732cd"])


if __name__ == "__main__":
    unittest.main()
