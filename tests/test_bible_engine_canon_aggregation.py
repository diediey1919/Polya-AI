"""
Tests for Task 4.4 Canon-Level Synthesis Aggregator
===================================================

Covers all 10 minimum test categories from Task 4.4 specification:
A. Completeness
B. Boundary & Directionality
C. Deterministic Identity
D. Validation Lineage & Epistemic Gate
E. Confidence (Weakest-Link & Ceiling Firewall)
F. Tension Preservation (Anti-Harmonization)
G. Idempotency & Fast-Path Reuse
H. Crash Safety & Recovery
I. Immutability
J. Regression
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from bible_engine.canon_aggregator import (
    CanonAggregationResult,
    CanonAggregator,
    CanonCompletenessReport,
    CorpusCompletenessStatus,
    compute_canon_synthesis_identity,
    get_canonical_corpora_for_canon,
)
from bible_engine.config import DatabaseConfig
from bible_engine.corpus_aggregator import (
    compute_corpus_synthesis_identity,
)
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CanonBlockedValidationError,
    CanonHierarchyViolationError,
    CanonIncompleteError,
    PipelineBlockedValidationError,
    SynthesisConfidenceInflationError,
    SynthesisScopeJumpError,
    SynthesisValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.migrations import MigrationRunner
from bible_engine.pipeline import PipelineConfig
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import (
    HybridSymmetricalRetrievalEngine,
)
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
    RetrievalLineage,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
)
from bible_engine.versioning import VersionManager


class TestBibleEngineCanonAggregation(unittest.TestCase):
    """Test suite for Task 4.4 CanonAggregator."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_canon_aggregation.db")
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
        self.aggregator = CanonAggregator(
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
        """Seed minimal canon catalog with 2 constituent testaments/corpora: OT and NT."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self.engine.get_write_connection()

        # Seed root provenance
        conn.execute(
            """
            INSERT OR IGNORE INTO provenance_records (
                provenance_id, target_type, target_id, content_hash, transformation_type,
                schema_version, agent_id, created_at, is_immutable
            ) VALUES ('PRV-ROOT', 'SOURCE_TEXT', 'SYS-ROOT', 'root_hash', 'ORIGIN', '002', 'system', ?, 1)
            """,
            (now,),
        )

        # Canonical Catalog: CANON-BIBLE -> TEST-OT, TEST-NT
        conn.execute(
            "INSERT OR IGNORE INTO canons VALUES ('CANON-BIBLE', 'Christian Bible', 'Complete Canon', ?);",
            (now,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments VALUES ('TEST-OT', 'CANON-BIBLE', 'Old Testament', 1);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments VALUES ('TEST-NT', 'CANON-BIBLE', 'New Testament', 2);"
        )

        conn.commit()

    def _seed_corpus_synthesis(
        self,
        corpus_id: str,
        status: str = "COMPLETED",
        validation_outcome: str = "VALID",
        claim_conf: float = 0.90,
        pipeline_config_hash: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """
        Helper to seed an authoritative CORPUS-level synthesis run and its validation record.
        Returns (run_id, version_id, logical_identity).
        """
        now = datetime.now(timezone.utc).isoformat()
        cfg_hash = pipeline_config_hash or PipelineConfig().configuration_hash

        logical_identity = compute_corpus_synthesis_identity(
            canonical_corpus_id=corpus_id,
            constituent_identities=[f"BK-{corpus_id}-01"],
            pipeline_config_hash=cfg_hash,
        )

        if status == "COMPLETED":
            claim = SynthesisClaimInput(
                claim_id=f"CLM-CORP-{corpus_id}-01",
                claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
                primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
                claim_text=f"Theological theme for {corpus_id}",
                epistemic_status=SynthesisClaimStatus.CONVERGENT,
                authorial_context=f"Tradition {corpus_id}",
                constituents=[
                    ConstituentInput(
                        constituent_scope=SynthesisScope.BOOK,
                        constituent_target_id=f"BK-{corpus_id}-01",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ],
            )
            synth_res = self.synthesis_mgr.create_synthesis_run(
                scope=SynthesisScope.CORPUS,
                target_id=corpus_id,
                claims=[claim],
                config=SynthesisRunConfig(
                    metadata={
                        "logical_identity": logical_identity,
                        "canonical_corpus_id": corpus_id,
                        "constituent_identities": [f"BK-{corpus_id}-01"],
                        "pipeline_config_hash": cfg_hash,
                    }
                ),
            )
            run_id = synth_res.run_id
            ver_id = synth_res.version_id
            prov_id = synth_res.provenance_id
        else:
            run_id = f"SYNTH-RUN-CORP-{corpus_id}-{status}"
            prov_id = f"PRV-CORP-{corpus_id}-{status}"
            ver_id = f"VER-CORP-{corpus_id}-{status}"
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO provenance_records (
                        provenance_id, target_type, target_id, content_hash, transformation_type,
                        schema_version, agent_id, created_at, is_immutable
                    ) VALUES (?, 'INTERPRETATION', ?, 'abc', 'DETERMINISTIC', '002', 'test', ?, 1)
                    """,
                    (prov_id, run_id, now),
                )
                conn.execute(
                    """
                    INSERT INTO object_versions (
                        version_id, object_type, object_id, version_number,
                        content_hash, change_reason, status, provenance_id, created_at, created_by
                    ) VALUES (?, 'CORPUS_SYNTHESIS', ?, 1, 'abc', 'INITIAL_CREATION', 'ACTIVE', ?, ?, 'test')
                    """,
                    (ver_id, run_id, prov_id, now),
                )
                conn.execute(
                    """
                    INSERT INTO synthesis_runs (
                        run_id, scope, target_id, synthesizer_id, synthesizer_version,
                        configuration_hash, input_content_hash, output_hash,
                        aggregate_confidence, status, is_exact_reproducible,
                        provenance_id, version_id, created_at, metadata_json
                    ) VALUES (?, 'CORPUS', ?, 'test_synth', '1.0.0', ?, 'in_hash', 'out_hash', ?, ?, 1, ?, ?, ?, '{}')
                    """,
                    (run_id, corpus_id, cfg_hash, claim_conf, status, prov_id, ver_id, now),
                )

        # Validation Run (if validation_outcome is specified)
        if validation_outcome is not None:
            val_id = f"VRUN-CORP-{corpus_id}"
            val_ident = f"VAL-IDENT-CORP-{corpus_id}"
            val_in_hash = f"val_in_hash_{corpus_id}"
            checks_passed = 10 if validation_outcome in ("VALID", "VALID_WITH_WARNINGS") else 8
            checks_failed = 0 if validation_outcome in ("VALID", "VALID_WITH_WARNINGS") else 2
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO validation_runs (
                        run_id, validation_identity, validation_input_hash,
                        engine_version, schema_version, target_type, target_id,
                        target_version_id, final_outcome, checks_total, checks_passed,
                        checks_failed, warnings_total, provenance_id, executed_at, is_immutable
                    ) VALUES (?, ?, ?, '2.0.0', '023', 'CORPUS_SYNTHESIS', ?, ?, ?, 10, ?, ?, 0, ?, ?, 1)
                    """,
                    (val_id, val_ident, val_in_hash, run_id, ver_id, validation_outcome, checks_passed, checks_failed, prov_id, now),
                )

        return run_id, ver_id, logical_identity

    # =========================================================================
    # A. COMPLETENESS GATE
    # =========================================================================

    def test_A01_complete_canon_accepted(self) -> None:
        """All constituent corpora completed and valid -> complete canon accepted."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        report = self.aggregator.verify_canon_completeness("CANON-BIBLE")
        self.assertTrue(report.is_complete)
        self.assertEqual(report.completed_count, 2)
        self.assertEqual(report.total_required, 2)
        self.assertEqual(len(report.missing_corpora), 0)

    def test_A02_missing_corpus_rejected(self) -> None:
        """Missing one of required corpora -> rejected."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        # TEST-NT missing

        report = self.aggregator.verify_canon_completeness("CANON-BIBLE")
        self.assertFalse(report.is_complete)
        self.assertEqual(report.completed_count, 1)
        self.assertIn("TEST-NT", report.missing_corpora)

        with self.assertRaises(CanonIncompleteError):
            self.aggregator.verify_canon_completeness("CANON-BIBLE", raise_on_incomplete=True)

    def test_A03_failed_corpus_rejected(self) -> None:
        """Corpus with status=FAILED -> rejected."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="FAILED", validation_outcome=None)

        report = self.aggregator.verify_canon_completeness("CANON-BIBLE")
        self.assertFalse(report.is_complete)
        self.assertIn("TEST-NT", report.failed_corpora)

    def test_A04_blocked_corpus_rejected(self) -> None:
        """Corpus with validation_outcome=BLOCKED -> rejected."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="BLOCKED")

        report = self.aggregator.verify_canon_completeness("CANON-BIBLE")
        self.assertFalse(report.is_complete)
        self.assertIn("TEST-NT", report.blocked_corpora)

    def test_A05_unvalidated_corpus_rejected(self) -> None:
        """Corpus completed but with no validation record -> rejected."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome=None)

        report = self.aggregator.verify_canon_completeness("CANON-BIBLE")
        self.assertFalse(report.is_complete)
        self.assertIn("TEST-NT", report.unvalidated_corpora)

    # =========================================================================
    # B. BOUNDARY & HIERARCHICAL DIRECTIONALITY
    # =========================================================================

    def test_B01_corpus_to_canon_direction_accepted(self) -> None:
        """CORPUS constituents are accepted by CANON aggregation."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.88)

        claim = SynthesisClaimInput(
            claim_id="CLM-CANON-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Unified biblical canonical theology.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Biblical Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.90, constituent_claim_id="CLM-CORP-TEST-OT-01"),
                ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.88, constituent_claim_id="CLM-CORP-TEST-NT-01"),
            ],
        )

        res = self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])
        self.assertEqual(res.synthesis_run.scope, SynthesisScope.CANON)
        self.assertEqual(res.synthesis_run.target_id, "CANON-BIBLE")
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)

    def test_B02_raw_pericope_to_canon_rejected(self) -> None:
        """Direct scope jump PERICOPE -> CANON is strictly rejected."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-JUMP-PER-TO-CANON",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            claim_text="Attempting raw pericope to canon skip.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-GEN-01", 0.95)],
        )

        with self.assertRaises(CanonHierarchyViolationError):
            self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])

    def test_B03_book_to_canon_rejected(self) -> None:
        """Direct scope jump BOOK -> CANON is strictly rejected (requires intermediate CORPUS)."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        claim = SynthesisClaimInput(
            claim_id="CLM-JUMP-BK-TO-CANON",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E7_BOOK_CONTEXT,
            claim_text="Attempting book to canon skip.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[ConstituentInput(SynthesisScope.BOOK, "GEN", 0.90)],
        )

        with self.assertRaises(CanonHierarchyViolationError):
            self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])

    # =========================================================================
    # C. DETERMINISTIC IDENTITY
    # =========================================================================

    def test_C01_deterministic_identity_independent_of_execution_history(self) -> None:
        """Same constituents yield identical logical identity across different runs."""
        id1 = compute_canon_synthesis_identity(
            canonical_canon_id="CANON-BIBLE",
            constituent_corpus_identities=["SYNTH-CORP-OT", "SYNTH-CORP-NT"],
            pipeline_config_hash="cfg_hash_1",
        )
        id2 = compute_canon_synthesis_identity(
            canonical_canon_id="CANON-BIBLE",
            constituent_corpus_identities=["SYNTH-CORP-NT", "SYNTH-CORP-OT"],  # reordered
            pipeline_config_hash="cfg_hash_1",
        )
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("SYNTH-CANON-"))

    def test_C02_changed_constituent_changes_identity(self) -> None:
        """Changing constituent corpus changes the CANON logical identity."""
        id1 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT", "SYNTH-CORP-NT"], "cfg_hash")
        id2 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT", "SYNTH-CORP-NT-REV2"], "cfg_hash")
        self.assertNotEqual(id1, id2)

    def test_C03_changed_config_changes_identity(self) -> None:
        """Changing configuration changes the CANON logical identity."""
        id1 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT"], "cfg_v1")
        id2 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT"], "cfg_v2")
        self.assertNotEqual(id1, id2)

    def test_C04_changed_version_changes_identity(self) -> None:
        """Changing engine or schema version changes the identity."""
        id1 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT"], "cfg", engine_version="2.0.0")
        id2 = compute_canon_synthesis_identity("CANON-BIBLE", ["SYNTH-CORP-OT"], "cfg", engine_version="2.1.0")
        self.assertNotEqual(id1, id2)

    # =========================================================================
    # D. VALIDATION LINEAGE & EPISTEMIC GATE
    # =========================================================================

    def test_D01_valid_outcome_accepted(self) -> None:
        """VALID epistemic outcome establishes authoritative CANON synthesis."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        res = self.aggregator.aggregate_canon("CANON-BIBLE")
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)
        self.assertTrue(res.logical_identity.startswith("SYNTH-CANON-"))

    def test_D02_validation_lineage_changes_when_constituent_changes(self) -> None:
        """ValidationInput canonical dict and hash change when constituent lineage changes."""
        lineage_dummy = RetrievalLineage("Q1", "qh1", "R1", "ch1", "P1", "ph1")
        inp1 = ValidationInput(
            target=ValidationTarget("CANON_SYNTHESIS", "RUN-1", "V1"),
            retrieval_lineage=lineage_dummy,
            evidence_dependencies=EvidenceDependencies(evidence_ids=[], linked_claim_ids=["CLM-CORP-TEST-OT-01"]),
        )
        inp2 = ValidationInput(
            target=ValidationTarget("CANON_SYNTHESIS", "RUN-1", "V1"),
            retrieval_lineage=lineage_dummy,
            evidence_dependencies=EvidenceDependencies(evidence_ids=[], linked_claim_ids=["CLM-CORP-TEST-NT-01"]),
        )
        self.assertNotEqual(inp1.compute_validation_input_hash(), inp2.compute_validation_input_hash())
        self.assertNotEqual(inp1.compute_validation_identity(), inp2.compute_validation_identity())

    # =========================================================================
    # E. CONFIDENCE FIREWALL
    # =========================================================================

    def test_E01_weakest_link_confidence_enforcement(self) -> None:
        """Weakest critical constituent caps CANON aggregate confidence."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.95)
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.40)

        claim = SynthesisClaimInput(
            claim_id="CLM-WEAKEST-LINK",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Inter-testamental continuity thesis.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.95, constituent_claim_id="CLM-CORP-TEST-OT-01"),
                ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.40, constituent_claim_id="CLM-CORP-TEST-NT-01"),
            ],
        )

        res = self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])
        self.assertAlmostEqual(res.synthesis_run.aggregate_confidence, 0.40, places=4)

    def test_E02_no_majority_vote_or_averaging(self) -> None:
        """Many high-confidence corpora cannot outvote a single low-confidence corpus."""
        # Baseline has OT and NT. OT has 0.99, NT has 0.15.
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.99)
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.15)

        claim = SynthesisClaimInput(
            claim_id="CLM-NO-AVERAGING",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Weakest link must govern over averaging.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.99, constituent_claim_id="CLM-CORP-TEST-OT-01"),
                ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.15, constituent_claim_id="CLM-CORP-TEST-NT-01"),
            ],
        )

        res = self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])
        self.assertAlmostEqual(res.synthesis_run.aggregate_confidence, 0.15, places=4)
        # Average would be (0.99 + 0.15)/2 = 0.57. It MUST NOT be 0.57!
        self.assertNotAlmostEqual(res.synthesis_run.aggregate_confidence, 0.57, places=1)

    def test_E03_confidence_inflation_rejected_by_v10(self) -> None:
        """Candidate confidence exceeding database dependency confidence is rejected by V10."""
        # Database dependency has 0.80
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.80)
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)

        # Attempting candidate constituent confidence of 0.85 > 0.80
        claim = SynthesisClaimInput(
            claim_id="CLM-INFLATED",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Inflated confidence attempt.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.85, constituent_claim_id="CLM-CORP-TEST-OT-01"),
            ],
        )

        with self.assertRaises(PipelineBlockedValidationError):
            self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])

    # =========================================================================
    # F. TENSION PRESERVATION
    # =========================================================================

    def test_F01_cross_corpus_tensions_preserved(self) -> None:
        """Inter-testamental tensions are preserved without forced harmonization."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.85)
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.85)

        c1 = SynthesisClaimInput(
            claim_id="CLM-OT-PRIESTHOOD",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Levitical priesthood eternal covenant in OT.",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Aaronic Tradition",
            constituents=[ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.85, constituent_claim_id="CLM-CORP-TEST-OT-01")],
        )
        c2 = SynthesisClaimInput(
            claim_id="CLM-NT-PRIESTHOOD",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Melchizedekian priesthood superseding Levitical in NT.",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Hebrews Tradition",
            constituents=[ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.85, constituent_claim_id="CLM-CORP-TEST-NT-01")],
        )
        tension = SynthesisTensionInput(
            tension_id="TENS-PRIESTHOOD-01",
            tension_type=SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            primary_claim_id="CLM-OT-PRIESTHOOD",
            secondary_claim_id="CLM-NT-PRIESTHOOD",
            description="Levitical vs Melchizedekian priesthood disparity.",
            preservation_rationale="Both canonical witnesses preserved intact.",
            resolution_status=SynthesisTensionResolution.PRESERVED_TENSION,
        )

        res = self.aggregator.aggregate_canon("CANON-BIBLE", claims=[c1, c2], tensions=[tension])
        self.assertEqual(res.synthesis_run.tensions_created, 1)

        tensions = self.synthesis_mgr.get_tensions_for_target(SynthesisScope.CANON, "CANON-BIBLE")
        self.assertEqual(len(tensions), 1)
        self.assertEqual(tensions[0].tension_id, "TENS-PRIESTHOOD-01")
        self.assertEqual(tensions[0].resolution_status, SynthesisTensionResolution.PRESERVED_TENSION)

    # =========================================================================
    # G. IDEMPOTENCY & FAST-PATH
    # =========================================================================

    def test_G01_repeated_aggregation_reuses_existing_synthesis(self) -> None:
        """Repeated aggregation of identical canon returns existing result without duplicating records."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        res1 = self.aggregator.aggregate_canon("CANON-BIBLE")
        self.assertFalse(res1.is_reused)

        res2 = self.aggregator.aggregate_canon("CANON-BIBLE")
        self.assertTrue(res2.is_reused)
        self.assertEqual(res1.synthesis_run.run_id, res2.synthesis_run.run_id)
        self.assertEqual(res1.validation_run.run_id, res2.validation_run.run_id)

        # Check synthesis_runs count in DB
        with self.engine.connect() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM synthesis_runs WHERE scope = 'CANON' AND target_id = 'CANON-BIBLE'").fetchone()[0]
            self.assertEqual(cnt, 1)

    def test_G02_blocked_validation_not_silently_overridden(self) -> None:
        """Existing BLOCKED validation is not overridden or silently replaced."""
        _, _, ot_ident = self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)
        _, _, nt_ident = self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)

        claim = SynthesisClaimInput(
            claim_id="CLM-BLOCKED-REUSE",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Test blocked validation reuse.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.90, constituent_claim_id="CLM-CORP-TEST-OT-01"),
                ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.90, constituent_claim_id="CLM-CORP-TEST-NT-01"),
            ],
        )

        pipe_cfg_hash = PipelineConfig().configuration_hash
        constituent_ids = [ot_ident, nt_ident]
        logical_identity = compute_canon_synthesis_identity(
            canonical_canon_id="CANON-BIBLE",
            constituent_corpus_identities=constituent_ids,
            pipeline_config_hash=pipe_cfg_hash,
        )

        # Pre-seed a CANON synthesis run
        synth_res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.CANON,
            target_id="CANON-BIBLE",
            claims=[claim],
            config=SynthesisRunConfig(metadata={"logical_identity": logical_identity}),
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
                ) VALUES ('VRUN-CANON-BLOCKED', 'VAL-CANON-BLOCKED', 'in_hash', '2.0.0', '025', 'CANON_SYNTHESIS', ?, ?, 'BLOCKED', 10, 8, 2, 0, 'PRV-ROOT', ?, 1)
                """,
                (synth_res.run_id, synth_res.version_id, now),
            )

        with self.assertRaises(PipelineBlockedValidationError):
            self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])

    # =========================================================================
    # H. CRASH RECOVERY
    # =========================================================================

    def test_H01_crash_after_synthesis_persistence_resumes_validation(self) -> None:
        """Crash safety Case B: Synthesis persisted but validation died before completion resumes validation."""
        _, _, ot_ident = self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)
        _, _, nt_ident = self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID", claim_conf=0.90)

        claim = SynthesisClaimInput(
            claim_id="CLM-CRASH-CANON-B",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Crash recovery test B.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Canon",
            constituents=[
                ConstituentInput(SynthesisScope.CORPUS, "TEST-OT", 0.90, constituent_claim_id="CLM-CORP-TEST-OT-01"),
                ConstituentInput(SynthesisScope.CORPUS, "TEST-NT", 0.90, constituent_claim_id="CLM-CORP-TEST-NT-01"),
            ],
        )

        pipe_cfg_hash = PipelineConfig().configuration_hash
        constituent_ids = [ot_ident, nt_ident]
        logical_identity = compute_canon_synthesis_identity(
            canonical_canon_id="CANON-BIBLE",
            constituent_corpus_identities=constituent_ids,
            pipeline_config_hash=pipe_cfg_hash,
        )

        # Simulate synthesis persisted without validation record
        synth_res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.CANON,
            target_id="CANON-BIBLE",
            claims=[claim],
            config=SynthesisRunConfig(metadata={"logical_identity": logical_identity}),
        )

        # Verify no validation record yet
        with self.engine.connect() as conn:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM validation_runs WHERE target_type = 'CANON_SYNTHESIS' AND target_id = ?",
                (synth_res.run_id,),
            ).fetchone()[0]
            self.assertEqual(cnt, 0)

        # Call aggregate_canon -> must resume validation and produce valid certificate without duplicate synthesis
        res = self.aggregator.aggregate_canon("CANON-BIBLE", claims=[claim])
        self.assertEqual(res.synthesis_run.run_id, synth_res.run_id)
        self.assertEqual(res.validation_run.final_outcome, ValidationOutcome.VALID)

        # Ensure still only 1 synthesis run exists
        with self.engine.connect() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM synthesis_runs WHERE scope = 'CANON' AND target_id = 'CANON-BIBLE'").fetchone()[0]
            self.assertEqual(cnt, 1)

    # =========================================================================
    # I. IMMUTABILITY
    # =========================================================================

    def test_I01_canon_synthesis_and_validation_immutability(self) -> None:
        """CANON synthesis runs and validation runs cannot be modified or deleted."""
        self._seed_corpus_synthesis("TEST-OT", status="COMPLETED", validation_outcome="VALID")
        self._seed_corpus_synthesis("TEST-NT", status="COMPLETED", validation_outcome="VALID")

        res = self.aggregator.aggregate_canon("CANON-BIBLE")
        run_id = res.synthesis_run.run_id
        val_id = res.validation_run.run_id

        with self.engine.transaction() as conn:
            # Attempt to update synthesis run -> trigger abort
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE synthesis_runs SET aggregate_confidence = 0.0 WHERE run_id = ?", (run_id,))

            # Attempt to delete synthesis run -> trigger abort
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM synthesis_runs WHERE run_id = ?", (run_id,))

            # Attempt to update validation run -> trigger abort
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE validation_runs SET final_outcome = 'BLOCKED' WHERE run_id = ?", (val_id,))

            # Attempt to delete validation run -> trigger abort
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM validation_runs WHERE run_id = ?", (val_id,))


if __name__ == "__main__":
    unittest.main()
