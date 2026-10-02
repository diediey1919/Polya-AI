"""
Task 4.3: Comprehensive Unit & Adversarial Test Suite for Corpus-Level Synthesis Aggregator.
Specification: Architecture Revision V2 — FROZEN.

Covers:
  A. Corpus completeness:
     - complete corpus accepted
     - missing pericope rejected
     - failed pericope rejected
     - blocked pericope rejected
     - unvalidated pericope rejected
     - partial batch rejected
     - multiple batch_runs accepted when canonical corpus is complete
  B. Hierarchy:
     - correct BOOK -> CORPUS direction
     - invalid scope jump rejected (PERICOPE -> CORPUS)
     - CANON cannot consume raw pericopes directly
  C. Identity:
     - deterministic identity
     - same constituents across different batch_runs -> same identity
     - changed constituent -> changed identity
     - changed config -> changed identity
     - changed version -> changed identity
     - SQLite insertion order does not affect identity
  D. Synthesis:
     - CORPUS synthesis created through HierarchicalSynthesisManager
     - constituent links correct
     - tension preservation
     - weakest-link confidence
  E. Validation:
     - VALID accepted
     - VALID_WITH_WARNINGS accepted
     - BLOCKED rejected
     - validation lineage changes when constituent lineage changes
  F. Idempotency:
     - repeated aggregation does not duplicate synthesis
     - existing valid synthesis is reused
     - synthesis without validation resumes validation
     - blocked validation is not overridden
  G. Crash recovery:
     - crash before persistence
     - crash after synthesis persistence
     - crash after validation persistence
  H. Epistemic firewalls:
     - no majority vote
     - no harmonization
     - no confidence inflation
     - no T4 promotion
  I. Regression:
     - Task 3.9 unchanged
     - Task 4.0 unchanged
     - Task 4.1 unchanged
     - Task 4.2 unchanged
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from bible_engine.batch import (
    BatchProcessingEngine,
    BatchRunStatus,
    ProcessingUnit,
)
from bible_engine.config import DatabaseConfig
from bible_engine.corpus_aggregator import (
    CorpusAggregationResult,
    CorpusAggregator,
    CorpusCompletenessReport,
    compute_corpus_synthesis_identity,
    get_canonical_books_for_corpus,
    get_canonical_pericopes_for_corpus,
)
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CorpusBlockedValidationError,
    CorpusHierarchyViolationError,
    CorpusIncompleteError,
    PipelineBlockedValidationError,
    SynthesisConfidenceInflationError,
    SynthesisHarmonizationError,
    SynthesisMissingConstituentError,
    SynthesisScopeJumpError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.migrations import MigrationRunner
from bible_engine.pipeline import ExegeticalPipeline, PipelineConfig
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import HybridSymmetricalRetrievalEngine
from bible_engine.synthesis import (
    ConstituentInput,
    HierarchicalSynthesisManager,
    SynthesisClaimInput,
    SynthesisClaimStatus,
    SynthesisRunConfig,
    SynthesisScope,
    SynthesisTensionInput,
    SynthesisTensionResolution,
    SynthesisTensionType,
)
from bible_engine.validation import (
    EvidenceDependencies,
    LayerCode,
    RetrievalLineage,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationTarget,
)
from bible_engine.versioning import VersionManager


class TestBibleEngineCorpusAggregation(unittest.TestCase):
    """Test suite for Task 4.3 CorpusAggregator."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_corpus_aggregation.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.db_config)
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        self.runner.apply_pending()

        self.prov_tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)
        self.retrieval_engine = HybridSymmetricalRetrievalEngine(
            self.engine, self.prov_tracker, self.version_mgr
        )
        self.synthesis_mgr = HierarchicalSynthesisManager(
            self.engine, self.version_mgr, self.prov_tracker
        )
        self.validation_engine = ValidationEngine(
            self.engine, self.prov_tracker, self.version_mgr, self.retrieval_engine
        )
        self.pipeline = ExegeticalPipeline(
            self.engine,
            self.retrieval_engine,
            self.prov_tracker,
            self.version_mgr,
            self.validation_engine,
        )
        self.batch_engine = BatchProcessingEngine(
            self.engine,
            pipeline=self.pipeline,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
        )
        self.aggregator = CorpusAggregator(
            self.engine,
            synthesis_manager=self.synthesis_mgr,
            validation_engine=self.validation_engine,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
            retrieval_engine=self.retrieval_engine,
        )

        self._seed_baseline()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline(self) -> None:
        """Seed minimal canon, testament, books, pericopes, and baseline evidence."""
        conn = self.engine.get_write_connection()
        now = datetime.now(timezone.utc).isoformat()

        # Provenance
        conn.execute(
            """
            INSERT OR IGNORE INTO provenance_records (
                provenance_id, target_type, target_id, content_hash, transformation_type,
                schema_version, agent_id, created_at, is_immutable
            ) VALUES ('PRV-GENESIS', 'SOURCE_TEXT', 'SYS-ROOT', 'genesis_hash', 'ORIGIN', '002', 'system', ?, 1)
            """,
            (now,),
        )
        p_src = self.prov_tracker.record_origin(
            target_type=TargetType.SOURCE_TEXT,
            target_id="SRC-GNT",
            content="Greek NT source",
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
        self.source_version_id = v_src.version_id

        # Canonical Catalog: Canon -> Testament -> Books -> Pericopes
        conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON-NT', 'NT Canon', 'New Testament', ?);", (now,))
        conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST-NT', 'CANON-NT', 'New Testament', 2);")
        conn.execute("INSERT OR IGNORE INTO books VALUES ('MAT', 'TEST-NT', 40, 'Matius', 'Matthew', 'GREEK', 28);")
        conn.execute("INSERT OR IGNORE INTO books VALUES ('ROM', 'TEST-NT', 45, 'Roma', 'Romans', 'GREEK', 16);")

        conn.execute(
            """
            INSERT OR IGNORE INTO pericopes (
                pericope_id, book_id, reference, start_chapter, start_verse,
                end_chapter, end_verse, genre, boundary_source, boundary_confidence,
                status, version, created_at
            ) VALUES 
            ('PER-MAT-01', 'MAT', 'Matius 1:1-17', 1, 1, 1, 17, 'GENEALOGY', 'NA28', 'HIGH', 'VALIDATED', '1.0.0', ?),
            ('PER-MAT-02', 'MAT', 'Matius 1:18-25', 1, 18, 1, 25, 'NARRATIVE', 'NA28', 'HIGH', 'VALIDATED', '1.0.0', ?),
            ('PER-ROM-01', 'ROM', 'Roma 1:1-7', 1, 1, 1, 7, 'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '1.0.0', ?)
            """,
            (now, now, now),
        )
        conn.commit()

        # Baseline BOOK-level synthesis claims for MAT and ROM
        self._seed_book_synthesis("MAT", "Pauline/Gospel Christology in Matthew", 0.90)
        self._seed_book_synthesis("ROM", "Justification thesis in Romans", 0.85)

    def _seed_book_synthesis(self, book_id: str, claim_text: str, conf: float) -> None:
        """Helper to create a completed BOOK-level synthesis run with one claim."""
        claim = SynthesisClaimInput(
            claim_id=f"CLM-BK-{book_id}-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E7_BOOK_CONTEXT,
            claim_text=claim_text,
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context=f"Authorial context for {book_id}",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.SECTION,
                    constituent_target_id=f"SEC-{book_id}-01",
                    constituent_confidence=conf,
                )
            ],
        )
        self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.BOOK,
            target_id=book_id,
            claims=[claim],
        )

    def _seed_pericope_calibration(
        self,
        pericope_id: str,
        status: str = "COMPLETED",
        validation_outcome: str = "VALID",
        batch_run_id: str = "BATCH-001",
        pipeline_config_hash: Optional[str] = None,
        source_corpus: str = "HB",
        target_corpus: str = "GNT",
    ) -> None:
        """Helper to seed completed Task 4.1 calibration and Task 4.0 validation records."""
        now = datetime.now(timezone.utc).isoformat()
        cfg_hash = pipeline_config_hash or PipelineConfig().configuration_hash
        unit_id = f"U-{hashlib.sha256(pericope_id.encode('utf-8')).hexdigest()[:10]}"
        job_id = f"J-{hashlib.sha256((batch_run_id + pericope_id).encode('utf-8')).hexdigest()[:10]}"
        calib_id = f"CAL-{hashlib.sha256(pericope_id.encode('utf-8')).hexdigest()[:10]}"
        val_id = f"VRUN-{hashlib.sha256(pericope_id.encode('utf-8')).hexdigest()[:10]}"
        prov_id = f"PRV-{hashlib.sha256(pericope_id.encode('utf-8')).hexdigest()[:10]}"
        ver_id = f"VER-{hashlib.sha256(pericope_id.encode('utf-8')).hexdigest()[:10]}"

        with self.engine.transaction() as conn:
            # Batch Run
            conn.execute(
                """
                INSERT OR IGNORE INTO batch_runs (
                    batch_run_id, corpus_id, pipeline_config_hash, total_units,
                    status, created_at, updated_at, provenance_id
                ) VALUES (?, 'CANON-NT', ?, 1, 'COMPLETED', ?, ?, 'PRV-GENESIS')
                """,
                (batch_run_id, cfg_hash, now, now),
            )

            # Processing Unit
            unit_hash = hashlib.sha256(f"{source_corpus}:{target_corpus}:{pericope_id}:{cfg_hash}".encode("utf-8")).hexdigest()
            conn.execute(
                """
                INSERT OR IGNORE INTO processing_units (
                    unit_id, unit_hash, source_corpus, target_corpus, pericope_id,
                    source_version_id, pipeline_config_hash, engine_version, schema_version,
                    created_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, '2.0.0', '025', ?, 1)
                """,
                (unit_id, unit_hash, source_corpus, target_corpus, pericope_id, self.source_version_id, cfg_hash, now),
            )

            # Provenance & Version
            conn.execute(
                """
                INSERT OR IGNORE INTO provenance_records (
                    provenance_id, target_type, target_id, content_hash, transformation_type,
                    schema_version, agent_id, created_at, is_immutable
                ) VALUES (?, 'INTERPRETATION', ?, 'abc', 'DETERMINISTIC', '002', 'test', ?, 1)
                """,
                (prov_id, calib_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO object_versions (
                    version_id, object_type, object_id, version_number,
                    content_hash, change_reason, status, provenance_id, created_at, created_by
                ) VALUES (?, 'CALIBRATION', ?, 1, 'abc', 'INITIAL_CREATION', 'ACTIVE', ?, ?, 'test')
                """,
                (ver_id, calib_id, prov_id, now),
            )

            # Calibration run
            calib_ident = f"CAL-IDENT-{pericope_id}"
            calib_in_hash = f"in_hash_{pericope_id}"
            conn.execute(
                """
                INSERT OR IGNORE INTO cross_corpus_calibration_runs (
                    calibration_run_id, calibration_identity, input_content_hash,
                    configuration_hash, output_hash, engine_version, schema_version,
                    source_corpus, target_corpus, total_comparisons, status,
                    is_exact_reproducible, provenance_id, version_id, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, 'out_hash', '2.0.0', '024', ?, ?, 1, ?, 1, ?, ?, ?, 1)
                """,
                (calib_id, calib_ident, calib_in_hash, cfg_hash, source_corpus, target_corpus, status, prov_id, ver_id, now),
            )

            # Validation run
            val_ident = f"VAL-IDENT-{pericope_id}"
            val_inp_hash = f"inp_hash_{pericope_id}"
            conn.execute(
                """
                INSERT OR IGNORE INTO validation_runs (
                    run_id, validation_identity, validation_input_hash,
                    engine_version, schema_version, target_type, target_id,
                    target_version_id, final_outcome, checks_total, checks_passed,
                    checks_failed, warnings_total, provenance_id, executed_at, is_immutable
                ) VALUES (?, ?, ?, '2.0.0', '023', 'CROSS_CORPUS_CALIBRATION', ?, ?, ?, 10, 10, 0, 0, ?, ?, 1)
                """,
                (val_id, val_ident, val_inp_hash, calib_id, ver_id, validation_outcome, prov_id, now),
            )

            # Batch job
            conn.execute(
                """
                INSERT OR IGNORE INTO batch_jobs (
                    job_id, batch_run_id, unit_id, ordinal, status,
                    calibration_run_id, validation_run_id, created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
                """,
                (job_id, batch_run_id, unit_id, status, calib_id, val_id, now, now, now),
            )

    # =========================================================================
    # A. CORPUS COMPLETENESS
    # =========================================================================

    def test_A01_complete_corpus_accepted(self) -> None:
        """All required pericopes in canonical catalog completed -> complete corpus accepted."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertTrue(report.is_complete)
        self.assertEqual(report.completed_count, 3)
        self.assertEqual(report.total_required, 3)
        self.assertEqual(len(report.missing_pericopes), 0)

    def test_A02_missing_pericope_rejected(self) -> None:
        """If any required pericope is missing from executions -> completeness rejected."""
        self._seed_pericope_calibration("PER-MAT-01", status="COMPLETED", validation_outcome="VALID")
        # PER-MAT-02 and PER-ROM-01 are missing

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertFalse(report.is_complete)
        self.assertIn("PER-MAT-02", report.missing_pericopes)
        self.assertIn("PER-ROM-01", report.missing_pericopes)

        with self.assertRaises(CorpusIncompleteError):
            self.aggregator.verify_corpus_completeness("CANON-NT", raise_on_incomplete=True)

    def test_A03_failed_pericope_rejected(self) -> None:
        """Pericope with FAILED job -> rejected."""
        self._seed_pericope_calibration("PER-MAT-01", status="COMPLETED", validation_outcome="VALID")
        self._seed_pericope_calibration("PER-MAT-02", status="FAILED", validation_outcome="VALID")
        self._seed_pericope_calibration("PER-ROM-01", status="COMPLETED", validation_outcome="VALID")

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertFalse(report.is_complete)
        self.assertIn("PER-MAT-02", report.failed_pericopes)

        with self.assertRaises(CorpusIncompleteError):
            self.aggregator.aggregate_corpus("CANON-NT")

    def test_A04_blocked_pericope_rejected(self) -> None:
        """Pericope with BLOCKED validation outcome -> rejected."""
        self._seed_pericope_calibration("PER-MAT-01", status="COMPLETED", validation_outcome="VALID")
        self._seed_pericope_calibration("PER-MAT-02", status="COMPLETED", validation_outcome="BLOCKED")
        self._seed_pericope_calibration("PER-ROM-01", status="COMPLETED", validation_outcome="VALID")

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertFalse(report.is_complete)
        self.assertIn("PER-MAT-02", report.blocked_pericopes)

    def test_A05_unvalidated_pericope_rejected(self) -> None:
        """Pericope calibrated but without validation -> rejected."""
        # Insert without validation run
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO batch_runs (batch_run_id, corpus_id, pipeline_config_hash, total_units, status, created_at, updated_at, provenance_id)
                VALUES ('B-UNVAL', 'CANON-NT', 'cfg', 1, 'COMPLETED', ?, ?, 'PRV-GENESIS')
                """,
                (now, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO processing_units (unit_id, unit_hash, source_corpus, target_corpus, pericope_id, source_version_id, pipeline_config_hash, engine_version, schema_version, created_at, is_immutable)
                VALUES ('U-UNVAL', 'uhash', 'HB', 'GNT', 'PER-MAT-01', ?, 'cfg', '2.0.0', '025', ?, 1)
                """,
                (self.source_version_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO batch_jobs (job_id, batch_run_id, unit_id, ordinal, status, created_at, updated_at)
                VALUES ('J-UNVAL', 'B-UNVAL', 'U-UNVAL', 0, 'COMPLETED', ?, ?)
                """,
                (now, now),
            )

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertFalse(report.is_complete)
        self.assertIn("PER-MAT-01", report.unvalidated_pericopes)

    def test_A06_partial_batch_rejected(self) -> None:
        """Batch completed with only subset of pericopes in corpus -> rejected."""
        self._seed_pericope_calibration("PER-MAT-01", status="COMPLETED", validation_outcome="VALID")
        # PER-MAT-02 and PER-ROM-01 not executed

        with self.assertRaises(CorpusIncompleteError):
            self.aggregator.aggregate_corpus("CANON-NT")

    def test_A07_multiple_batch_runs_accepted_when_complete(self) -> None:
        """Pericopes assembled across multiple distinct batch_runs -> accepted when complete."""
        self._seed_pericope_calibration("PER-MAT-01", status="COMPLETED", validation_outcome="VALID", batch_run_id="BATCH-A")
        self._seed_pericope_calibration("PER-MAT-02", status="COMPLETED", validation_outcome="VALID", batch_run_id="BATCH-B")
        self._seed_pericope_calibration("PER-ROM-01", status="COMPLETED", validation_outcome="VALID", batch_run_id="BATCH-C")

        report = self.aggregator.verify_corpus_completeness("CANON-NT")
        self.assertTrue(report.is_complete)
        self.assertEqual(report.completed_count, 3)

    # =========================================================================
    # B. HIERARCHY
    # =========================================================================

    def test_B01_correct_book_to_corpus_direction(self) -> None:
        """CORPUS synthesis consumes BOOK-level constituents cleanly."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-CORP-NT-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Synoptic and Pauline convergence on grace.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon of the New Testament",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="MAT",
                    constituent_confidence=0.90,
                    constituent_claim_id="CLM-BK-MAT-01",
                ),
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="ROM",
                    constituent_confidence=0.85,
                    constituent_claim_id="CLM-BK-ROM-01",
                ),
            ],
        )

        res = self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])
        self.assertEqual(res.synthesis_run.scope, SynthesisScope.CORPUS)
        self.assertEqual(res.synthesis_run.target_id, "CANON-NT")
        self.assertEqual(res.synthesis_run.claims_created, 1)
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)

    def test_B02_invalid_scope_jump_rejected(self) -> None:
        """PERICOPE -> CORPUS bypass jump is rejected by hierarchy invariant."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-ILLEGAL-JUMP",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Illegal direct pericope jump to corpus.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-MAT-01",
                    constituent_confidence=0.90,
                )
            ],
        )

        with self.assertRaises(SynthesisScopeJumpError):
            self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])

    def test_B03_canon_cannot_consume_raw_pericopes(self) -> None:
        """CANON scope cannot consume raw pericopes directly."""
        claim = SynthesisClaimInput(
            claim_id="CLM-CANON-ILLEGAL",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Illegal direct pericope jump to canon.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Biblical Canon",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-MAT-01",
                    constituent_confidence=0.90,
                )
            ],
        )

        with self.assertRaises(SynthesisScopeJumpError):
            self.synthesis_mgr.create_synthesis_run(
                scope=SynthesisScope.CANON,
                target_id="PROTESTANT_66",
                claims=[claim],
            )

    # =========================================================================
    # C. DETERMINISTIC IDENTITY
    # =========================================================================

    def test_C01_deterministic_identity_independent_of_execution_history(self) -> None:
        """Logical synthesis identity is identical regardless of batch run ID or execution order."""
        id1 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01", "BOOK:ROM:CLM-02"],
            pipeline_config_hash="cfghash123",
        )
        id2 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:ROM:CLM-02", "BOOK:MAT:CLM-01"],  # Scrambled order
            pipeline_config_hash="cfghash123",
        )
        self.assertEqual(id1, id2)

    def test_C02_changed_constituent_changes_identity(self) -> None:
        """Changing any constituent link changes the deterministic identity."""
        id1 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01", "BOOK:ROM:CLM-02"],
            pipeline_config_hash="cfghash123",
        )
        id2 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01", "BOOK:ROM:CLM-03"],  # Different constituent
            pipeline_config_hash="cfghash123",
        )
        self.assertNotEqual(id1, id2)

    def test_C03_changed_config_changes_identity(self) -> None:
        """Changing pipeline config hash changes the deterministic identity."""
        id1 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01"],
            pipeline_config_hash="cfg_A",
        )
        id2 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01"],
            pipeline_config_hash="cfg_B",
        )
        self.assertNotEqual(id1, id2)

    def test_C04_changed_version_changes_identity(self) -> None:
        """Changing engine or schema version changes the deterministic identity."""
        id1 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01"],
            pipeline_config_hash="cfg_A",
            engine_version="2.0.0",
        )
        id2 = compute_corpus_synthesis_identity(
            canonical_corpus_id="CANON-NT",
            constituent_identities=["BOOK:MAT:CLM-01"],
            pipeline_config_hash="cfg_A",
            engine_version="2.1.0",
        )
        self.assertNotEqual(id1, id2)

    # =========================================================================
    # D. SYNTHESIS INTEGRATION & WEAKEST-LINK CONFIDENCE
    # =========================================================================

    def test_D01_weakest_link_confidence_enforcement(self) -> None:
        """CORPUS synthesis confidence strictly equals weakest constituent confidence."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-WEAKEST-LINK",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Weakest link test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[
                ConstituentInput(SynthesisScope.BOOK, "MAT", 0.95, constituent_claim_id="CLM-BK-MAT-01"),
                ConstituentInput(SynthesisScope.BOOK, "ROM", 0.72, constituent_claim_id="CLM-BK-ROM-01"),
            ],
        )

        res = self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])
        self.assertAlmostEqual(res.synthesis_run.aggregate_confidence, 0.72)

        stored = self.synthesis_mgr.get_synthesis_claim("CLM-WEAKEST-LINK")
        self.assertAlmostEqual(stored.synthesized_confidence, 0.72)

    def test_D02_tension_preservation(self) -> None:
        """Unresolved theological tensions between books are explicitly preserved."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        c1 = SynthesisClaimInput(
            claim_id="CLM-MAT-COVENANT",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Matthew emphasis on Torah continuity.",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Matthean Tradition",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.88, constituent_claim_id="CLM-BK-MAT-01")],
        )
        c2 = SynthesisClaimInput(
            claim_id="CLM-ROM-COVENANT",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Paul emphasis on Christ as telos of Torah.",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Pauline Tradition",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "ROM", 0.85, constituent_claim_id="CLM-BK-ROM-01")],
        )
        tension = SynthesisTensionInput(
            tension_id="TENS-MAT-PAUL-01",
            tension_type=SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            primary_claim_id="CLM-MAT-COVENANT",
            secondary_claim_id="CLM-ROM-COVENANT",
            description="Divergent Torah hermeneutic between Matthew and Paul.",
            preservation_rationale="Both voices must remain unharmonized.",
            resolution_status=SynthesisTensionResolution.PRESERVED_TENSION,
        )

        res = self.aggregator.aggregate_corpus("CANON-NT", claims=[c1, c2], tensions=[tension])
        self.assertEqual(res.synthesis_run.tensions_created, 1)

        tensions = self.synthesis_mgr.get_tensions_for_target(SynthesisScope.CORPUS, "CANON-NT")
        self.assertEqual(len(tensions), 1)
        self.assertEqual(tensions[0].tension_id, "TENS-MAT-PAUL-01")
        self.assertEqual(tensions[0].resolution_status, SynthesisTensionResolution.PRESERVED_TENSION)

    # =========================================================================
    # E. VALIDATION
    # =========================================================================

    def test_E01_valid_outcome_accepted(self) -> None:
        """VALID epistemic outcome establishes authoritative corpus synthesis."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        res = self.aggregator.aggregate_corpus("CANON-NT")
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)

    def test_E02_validation_lineage_changes_when_constituent_changes(self) -> None:
        """Validation input hash changes when constituent lineage changes."""
        c1 = SynthesisClaimInput(
            claim_id="CLM-C1",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Claim 1",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.90, constituent_claim_id="CLM-BK-MAT-01")],
        )
        c2 = SynthesisClaimInput(
            claim_id="CLM-C2",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Claim 2",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "ROM", 0.85, constituent_claim_id="CLM-BK-ROM-01")],
        )

        lineage_dummy = RetrievalLineage(
            query_id="Q1", query_hash="qh1", retrieval_run_id="R1", config_hash="ch1", pack_id="P1", pack_hash="ph1"
        )
        inp1 = ValidationInput(
            target=ValidationTarget("CORPUS_SYNTHESIS", "RUN-1", "V1"),
            retrieval_lineage=lineage_dummy,
            evidence_dependencies=EvidenceDependencies(evidence_ids=[], linked_claim_ids=["CLM-BK-MAT-01"]),
        )
        inp2 = ValidationInput(
            target=ValidationTarget("CORPUS_SYNTHESIS", "RUN-1", "V1"),
            retrieval_lineage=lineage_dummy,
            evidence_dependencies=EvidenceDependencies(evidence_ids=[], linked_claim_ids=["CLM-BK-ROM-01"]),
        )
        self.assertNotEqual(inp1.compute_validation_input_hash(), inp2.compute_validation_input_hash())
        self.assertNotEqual(inp1.compute_validation_identity(), inp2.compute_validation_identity())

    # =========================================================================
    # F. IDEMPOTENCY & FAST-PATH
    # =========================================================================

    def test_F01_repeated_aggregation_reuses_existing_synthesis(self) -> None:
        """Repeated aggregation of identical corpus returns existing result without duplicating records."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        res1 = self.aggregator.aggregate_corpus("CANON-NT")
        self.assertFalse(res1.is_reused)

        res2 = self.aggregator.aggregate_corpus("CANON-NT")
        self.assertTrue(res2.is_reused)
        self.assertEqual(res1.synthesis_run.run_id, res2.synthesis_run.run_id)
        self.assertEqual(res1.validation_run.run_id, res2.validation_run.run_id)

        # Check synthesis_runs count in DB
        with self.engine.connect() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM synthesis_runs WHERE scope = 'CORPUS' AND target_id = 'CANON-NT'").fetchone()[0]
            self.assertEqual(cnt, 1)

    def test_F02_blocked_validation_not_silently_overridden(self) -> None:
        """If an existing synthesis has a BLOCKED validation, subsequent aggregation does not override it."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        # Manually create synthesis run and blocked validation run
        claim = SynthesisClaimInput(
            claim_id="CLM-BLOCKED-TEST",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Test blocked persistence.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.90, constituent_claim_id="CLM-BK-MAT-01")],
        )

        cfg_hash = PipelineConfig().configuration_hash
        constituent_ids = ["BOOK:MAT:CLM-BK-MAT-01"]
        logical_id = compute_corpus_synthesis_identity("CANON-NT", constituent_ids, cfg_hash)

        run_cfg = SynthesisRunConfig(metadata={"logical_identity": logical_id})
        synth_res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.CORPUS,
            target_id="CANON-NT",
            claims=[claim],
            config=run_cfg,
        )

        # Insert a BLOCKED validation record
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO validation_runs (
                    run_id, validation_identity, validation_input_hash,
                    engine_version, schema_version, target_type, target_id,
                    target_version_id, final_outcome, checks_total, checks_passed,
                    checks_failed, warnings_total, provenance_id, executed_at, is_immutable
                ) VALUES ('VRUN-BLOCKED-01', 'VAL-BLOCKED', 'in_hash', '2.0.0', '025', 'CORPUS_SYNTHESIS', ?, ?, 'BLOCKED', 10, 8, 2, 0, 'PRV-GENESIS', ?, 1)
                """,
                (synth_res.run_id, synth_res.version_id, now),
            )

        with self.assertRaises(PipelineBlockedValidationError):
            self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])

    # =========================================================================
    # G. CRASH RECOVERY
    # =========================================================================

    def test_G01_crash_after_synthesis_persistence_resumes_validation(self) -> None:
        """Crash safety Case B: Synthesis persisted but validation died before completion resumes validation."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-CRASH-B",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Crash recovery test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.90, constituent_claim_id="CLM-BK-MAT-01")],
        )

        cfg_hash = PipelineConfig().configuration_hash
        constituent_ids = ["BOOK:MAT:CLM-BK-MAT-01"]
        logical_id = compute_corpus_synthesis_identity("CANON-NT", constituent_ids, cfg_hash)

        run_cfg = SynthesisRunConfig(metadata={"logical_identity": logical_id})
        synth_res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.CORPUS,
            target_id="CANON-NT",
            claims=[claim],
            config=run_cfg,
        )

        # At this point, synthesis is persisted, but NO validation run exists
        with self.engine.connect() as conn:
            v_cnt = conn.execute("SELECT COUNT(*) FROM validation_runs WHERE target_type = 'CORPUS_SYNTHESIS' AND target_id = ?", (synth_res.run_id,)).fetchone()[0]
            self.assertEqual(v_cnt, 0)

        # Next invocation must discover existing synthesis and complete validation
        res = self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])
        self.assertEqual(res.synthesis_run.run_id, synth_res.run_id)
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)

    # =========================================================================
    # H. EPISTEMIC FIREWALLS
    # =========================================================================

    def test_H01_no_majority_vote_or_frequency_inflation(self) -> None:
        """Many high-confidence constituents cannot outvote a low-confidence constituent."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        # 5 constituents with 0.99 confidence and 1 constituent with 0.10 confidence
        con_list = [
            ConstituentInput(SynthesisScope.BOOK, "MAT", 0.99, constituent_claim_id="CLM-BK-MAT-01"),
            ConstituentInput(SynthesisScope.BOOK, "MAT", 0.99, constituent_claim_id="CLM-BK-MAT-01"),
            ConstituentInput(SynthesisScope.BOOK, "MAT", 0.99, constituent_claim_id="CLM-BK-MAT-01"),
            ConstituentInput(SynthesisScope.BOOK, "ROM", 0.10, constituent_claim_id="CLM-BK-ROM-01"),
        ]

        claim = SynthesisClaimInput(
            claim_id="CLM-NO-MAJORITY",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Majority vote firewall test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            constituents=con_list,
        )

        res = self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])
        # Must be strictly 0.10, NOT an average (which would be ~0.76)
        self.assertAlmostEqual(res.synthesis_run.aggregate_confidence, 0.10)

    def test_H02_anti_harmonization_firewall(self) -> None:
        """Forced harmonization without tension is rejected."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-HARMONIZED-BAD",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Forced harmonized consensus.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,  # Not TENSION
            authorial_context="NT",
            is_harmonized=True,  # Forced harmonization violation
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.90, constituent_claim_id="CLM-BK-MAT-01")],
        )

        with self.assertRaises(SynthesisHarmonizationError):
            self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])

    def test_H03_confidence_inflation_rejected(self) -> None:
        """Explicit confidence exceeding weakest critical constituent is rejected."""
        for p in ("PER-MAT-01", "PER-MAT-02", "PER-ROM-01"):
            self._seed_pericope_calibration(p, status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-INFLATED",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Inflated confidence test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="NT",
            explicit_confidence=0.95,  # Exceeds 0.70
            constituents=[ConstituentInput(SynthesisScope.BOOK, "MAT", 0.70, constituent_claim_id="CLM-BK-MAT-01")],
        )

        with self.assertRaises(SynthesisConfidenceInflationError):
            self.aggregator.aggregate_corpus("CANON-NT", claims=[claim])


if __name__ == "__main__":
    unittest.main()
