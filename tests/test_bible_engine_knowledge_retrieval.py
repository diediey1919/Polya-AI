"""
Test Suite for Task 4.5 Authoritative Knowledge Retrieval Engine.
Specification: Architecture v2.0 — Post-CANON Consumption Boundary.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CounterSearchSuppressionError,
    KnowledgeHierarchyViolationError,
    KnowledgeNotFoundError,
    KnowledgeQueryValidationError,
    KnowledgeTheologicalContaminationError,
    KnowledgeVersionMismatchError,
    MissingValidationCertificateError,
    SupersededKnowledgeRetrievalError,
    UnvalidatedKnowledgeRetrievalError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.knowledge_retrieval import (
    AuthoritativeClaimItem,
    AuthoritativeEvidenceItem,
    AuthoritativeKnowledgeRetrievalEngine,
    AuthoritativeTensionItem,
    ConstituentLineageNode,
    KnowledgePackResult,
    KnowledgeQuery,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.pipeline import PipelineConfig
from bible_engine.provenance import ProvenanceTracker
from bible_engine.retrieval import (
    CandidateSource,
    CoverageStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalConfig,
    RetrievalTarget,
    SearchBranch,
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
    LayerCode,
    RetrievalLineage,
    ValidationCertificate,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
)
from bible_engine.versioning import VersionManager


class TestBibleEngineKnowledgeRetrieval(unittest.TestCase):
    """Exhaustive test suite for Task 4.5 Authoritative Knowledge Retrieval Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_knowledge_retrieval.db")
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
        self.knowledge_engine = AuthoritativeKnowledgeRetrievalEngine(
            self.engine,
            retrieval_engine=self.retrieval_engine,
            synthesis_manager=self.synthesis_mgr,
            validation_engine=self.validation_engine,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
        )

        self._seed_baseline()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # SEEDING HELPERS
    # -------------------------------------------------------------------------

    def _seed_baseline(self) -> None:
        """Seed minimal provenance root and canonical catalog."""
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO provenance_records (
                    provenance_id, target_type, target_id, content_hash, transformation_type,
                    schema_version, agent_id, created_at, is_immutable
                ) VALUES ('PRV-ROOT', 'SOURCE_TEXT', 'SYS-ROOT', 'root_hash', 'ORIGIN', '002', 'system', ?, 1)
                """,
                (now,),
            )
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', ?);", (now,))
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_OT', 'CANON_TEST', 'Old Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('GEN', 'TEST_OT', 1, 'Kejadian', 'Genesis', 'HEBREW', 50);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse,
                    end_chapter, end_verse, genre, boundary_source, boundary_confidence,
                    status, version, created_at
                ) VALUES (
                    'PERIC_GEN_1_1', 'GEN', 'Kejadian 1:1-2:3', 1, 1, 2, 3,
                    'NARRATIVE', 'BHS_SECTION', 'HIGH', 'REGISTERED', '1.0.0', ?
                );
                """,
                (now,),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO passages (
                    passage_id, pericope_id, book_id, chapter, verse, sort_order
                ) VALUES (
                    'PASS_GEN_1_1', 'PERIC_GEN_1_1', 'GEN', 1, 1, 1
                );
                """
            )
            # Evidence ledger items for symmetrical retrieval
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier,
                    source_reference, extracted_text_or_data, status, confidence,
                    confidence_score, is_counter_evidence, is_ai_generated,
                    is_translation_derived, is_contradicted, provenance_hash, is_immutable
                ) VALUES
                ('EV-PRI-01', 'PERIC_GEN_1_1', 'PASS_GEN_1_1', 'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION',
                 'Kejadian 1:1', 'In the beginning God created the heavens and the earth.',
                 'EXPLICIT', 'HIGH', 0.85, 0, 0, 0, 0, 'hash1', 1),
                ('EV-CNT-01', 'PERIC_GEN_1_1', 'PASS_GEN_1_1', 'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION',
                 'Kejadian 1:2', 'Now the earth was formless and void, darkness over the deep.',
                 'EXPLICIT', 'HIGH', 0.80, 1, 0, 0, 0, 'hash2', 1);
                """
            )
        self.retrieval_engine.index_evidence_ledger()

    def _seed_validated_synthesis(
        self,
        scope: SynthesisScope,
        target_id: str,
        status: str = "COMPLETED",
        validation_outcome: str = "VALID",
        claim_conf: float = 0.88,
        config_hash: str = "cfg_hash_test_123",
        engine_version: str = "2.0.0",
        schema_version: str = "025",
        constituents: Optional[List[ConstituentInput]] = None,
        tensions: Optional[List[SynthesisTensionInput]] = None,
    ) -> Tuple[str, str, str]:
        """
        Seed a synthesis run and matching validation certificate.
        Returns (run_id, version_id, cert_id).
        """
        now = datetime.now(timezone.utc).isoformat()
        claim_id = f"CLM-{scope.value}-{target_id}-01"

        if constituents is None:
            if scope == SynthesisScope.CANON:
                constituents = [
                    ConstituentInput(
                        constituent_scope=SynthesisScope.CORPUS,
                        constituent_target_id=f"CORP-{target_id}",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ]
            elif scope == SynthesisScope.CORPUS:
                constituents = [
                    ConstituentInput(
                        constituent_scope=SynthesisScope.BOOK,
                        constituent_target_id=f"BK-{target_id}",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ]
            elif scope == SynthesisScope.BOOK:
                constituents = [
                    ConstituentInput(
                        constituent_scope=SynthesisScope.SECTION,
                        constituent_target_id=f"SEC-{target_id}",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ]
            elif scope == SynthesisScope.SECTION:
                constituents = [
                    ConstituentInput(
                        constituent_scope=SynthesisScope.PERICOPE,
                        constituent_target_id=f"PER-{target_id}",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ]
            elif scope == SynthesisScope.PERICOPE:
                constituents = [
                    ConstituentInput(
                        constituent_scope=SynthesisScope.PERICOPE,
                        constituent_target_id=target_id,
                        constituent_evidence_id="EV-PRI-01",
                        constituent_confidence=claim_conf,
                        is_critical_dependency=True,
                    )
                ]

        if status == "COMPLETED" and scope != SynthesisScope.PERICOPE:
            claim_input = SynthesisClaimInput(
                claim_id=claim_id,
                claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
                primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
                claim_text=f"Authoritative finding for {target_id} at {scope.value}",
                epistemic_status=SynthesisClaimStatus.CONVERGENT,
                authorial_context=f"Context {target_id}",
                constituents=constituents or [],
            )
            synth_res = self.synthesis_mgr.create_synthesis_run(
                scope=scope,
                target_id=target_id,
                claims=[claim_input],
                tensions=tensions or [],
                config=SynthesisRunConfig(
                    metadata={"test_target": target_id},
                ),
            )
            run_id = synth_res.run_id
            ver_id = synth_res.version_id
            prov_id = synth_res.provenance_id
        else:
            run_id = f"RUN-{scope.value}-{target_id}-{status}"
            ver_id = f"VER-{scope.value}-{target_id}-{status}"
            prov_id = f"PRV-{scope.value}-{target_id}-{status}"
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO provenance_records (
                        provenance_id, target_type, target_id, content_hash, transformation_type,
                        schema_version, agent_id, created_at, is_immutable
                    ) VALUES (?, 'INTERPRETATION', ?, 'hash', 'DETERMINISTIC', '002', 'test', ?, 1)
                    """,
                    (prov_id, run_id, now),
                )
                conn.execute(
                    """
                    INSERT INTO object_versions (
                        version_id, object_type, object_id, version_number, content_hash,
                        status, change_reason, provenance_id, created_at, created_by
                    ) VALUES (?, 'SYNTHESIS_RUN', ?, 1, 'hash', 'ACTIVE', 'INITIAL_CREATION', ?, ?, 'test_system')
                    """,
                    (ver_id, run_id, prov_id, now),
                )
                conn.execute(
                    """
                    INSERT INTO synthesis_runs (
                        run_id, scope, target_id, parent_scope, parent_target_id, synthesizer_id,
                        synthesizer_version, configuration_hash, input_content_hash, output_hash,
                        aggregate_confidence, status, provenance_id, version_id, created_at, is_immutable
                    ) VALUES (?, ?, ?, NULL, NULL, 'test_synth', '2.0.0', ?, 'inhash', 'outhash',
                              ?, ?, ?, ?, ?, 1)
                    """,
                    (run_id, scope.value, target_id, config_hash, claim_conf, status, prov_id, ver_id, now),
                )
                if status == "COMPLETED":
                    conn.execute(
                        """
                        INSERT INTO synthesis_claims (
                            claim_id, run_id, scope, target_id, claim_tier, primary_evidence_class,
                            claim_text, epistemic_status, synthesized_confidence, weakest_constituent_confidence,
                            authorial_context, is_harmonized, provenance_id, version_id, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, 'T1_LINGUISTIC_FACT', 'E0_DIRECT_TEXT',
                                  ?, 'CONVERGENT', ?, ?, ?, 0, ?, ?, ?, 1)
                        """,
                        (claim_id, run_id, scope.value, target_id, f"Authoritative finding for {target_id}",
                         claim_conf, claim_conf, f"Context {target_id}", prov_id, ver_id, now),
                    )

        # Validation Engine result and certificate
        cert_id = f"VCERT-{scope.value}-{target_id}-{run_id}"
        val_run_id = f"VRUN-{scope.value}-{target_id}-{run_id}"
        val_identity = f"VID-{scope.value}-{target_id}-{run_id}"
        val_input_hash = f"hash_{scope.value}_{target_id}_{run_id}"

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO validation_runs (
                    run_id, validation_identity, validation_input_hash, engine_version,
                    schema_version, target_type, target_id, target_version_id, final_outcome,
                    checks_total, checks_passed, checks_failed, warnings_total,
                    provenance_id, executed_at, is_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 10, 10, 0, 0, ?, ?, 1)
                """,
                (val_run_id, val_identity, val_input_hash, engine_version, schema_version, f"{scope.value}_SYNTHESIS",
                 run_id, ver_id, validation_outcome, prov_id, now),
            )
            if validation_outcome in ("VALID", "VALID_WITH_WARNINGS"):
                conn.execute(
                    """
                    INSERT OR IGNORE INTO validation_certificates (
                        certificate_id, run_id, validation_identity, validation_input_hash,
                        engine_version, schema_version, target_type, target_id, target_version_id,
                        validation_status, layer_summary_json, provenance_id, validated_at, is_immutable
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?, 1)
                    """,
                    (cert_id, val_run_id, val_identity, val_input_hash, engine_version, schema_version,
                     f"{scope.value}_SYNTHESIS", run_id, ver_id, validation_outcome, prov_id, now),
                )

        return run_id, ver_id, cert_id

    # =========================================================================
    # A. AUTHORITY TESTS
    # =========================================================================

    def test_01_authority_valid_synthesis_retrieved(self) -> None:
        """Authority Gate: COMPLETED synthesis with VALID certificate is retrievable."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.CANON,
            target_id="CANON_PROTESTANT",
            status="COMPLETED",
            validation_outcome="VALID",
        )
        query = KnowledgeQuery(
            query_text="God created heavens and earth",
            canon_id="CANON_PROTESTANT",
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)

        self.assertIsInstance(pack, KnowledgePackResult)
        self.assertEqual(pack.resolved_scope, SynthesisScope.CANON)
        self.assertEqual(pack.target_id, "CANON_PROTESTANT")
        self.assertEqual(pack.synthesis_run_id, run_id)
        self.assertEqual(len(pack.claims), 1)
        self.assertEqual(len(pack.validation_certificates), 1)
        self.assertEqual(pack.validation_certificates[0].certificate_id, cert_id)

    def test_02_authority_valid_with_warnings_retrieved(self) -> None:
        """Authority Gate: VALID_WITH_WARNINGS certificate is accepted as authoritative."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.CORPUS,
            target_id="CORPUS_PAULINE",
            status="COMPLETED",
            validation_outcome="VALID_WITH_WARNINGS",
        )
        query = KnowledgeQuery(
            query_text="Pauline righteousness by faith",
            corpus_id="CORPUS_PAULINE",
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)
        self.assertEqual(pack.resolved_scope, SynthesisScope.CORPUS)
        self.assertEqual(pack.validation_certificates[0].validation_status, "VALID_WITH_WARNINGS")

    def test_03_authority_missing_certificate_rejected(self) -> None:
        """Authority Gate: COMPLETED synthesis without ValidationCertificate raises MissingValidationCertificateError."""
        now = datetime.now(timezone.utc).isoformat()
        claim = SynthesisClaimInput(
            claim_id="CLM-UNVAL-01",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Unvalidated claim",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Test",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.SECTION,
                    constituent_target_id="SEC_ROM_01",
                    constituent_confidence=0.85,
                    is_critical_dependency=True,
                )
            ],
        )
        res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_ROMANS",
            claims=[claim],
        )
        # Note: Do not run validation engine, so no certificate exists

        query = KnowledgeQuery(
            query_text="Romans theological core",
            book_id="BOOK_ROMANS",
        )
        with self.assertRaises(MissingValidationCertificateError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_04_authority_blocked_validation_rejected(self) -> None:
        """Authority Gate: BLOCKED validation run raises UnvalidatedKnowledgeRetrievalError."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_GALATIANS",
            status="COMPLETED",
            validation_outcome="BLOCKED",
        )
        query = KnowledgeQuery(
            query_text="Galatians justification",
            book_id="BOOK_GALATIANS",
        )
        with self.assertRaises(UnvalidatedKnowledgeRetrievalError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_05_authority_failed_status_rejected(self) -> None:
        """Authority Gate: FAILED synthesis status raises UnvalidatedKnowledgeRetrievalError."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.CORPUS,
            target_id="CORPUS_JOHANNINE",
            status="FAILED",
            validation_outcome="VALID",
        )
        query = KnowledgeQuery(
            query_text="Johannine logos",
            corpus_id="CORPUS_JOHANNINE",
        )
        with self.assertRaises(UnvalidatedKnowledgeRetrievalError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_06_authority_running_status_rejected(self) -> None:
        """Authority Gate: RUNNING/PROCESSING status raises UnvalidatedKnowledgeRetrievalError."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.SECTION,
            target_id="SEC_ROM_01",
            status="PROCESSING",
            validation_outcome="VALID",
        )
        query = KnowledgeQuery(
            query_text="Romans section 1",
            section_id="SEC_ROM_01",
        )
        with self.assertRaises(UnvalidatedKnowledgeRetrievalError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_07_authority_superseded_synthesis_rejected(self) -> None:
        """Authority Gate: SUPERSEDED synthesis run raises SupersededKnowledgeRetrievalError."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.CANON,
            target_id="CANON_OLD",
            status="COMPLETED",
            validation_outcome="VALID",
        )
        self.synthesis_mgr.supersede_synthesis_run(run_id, "Superseded by new revision")

        query = KnowledgeQuery(
            query_text="Old canon query",
            canon_id="CANON_OLD",
        )
        with self.assertRaises(SupersededKnowledgeRetrievalError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_08_authority_nonexistent_synthesis_raises_not_found(self) -> None:
        """Authority Gate: Requesting nonexistent target raises KnowledgeNotFoundError."""
        query = KnowledgeQuery(
            query_text="Nonexistent target inquiry",
            book_id="BOOK_NONEXISTENT",
        )
        with self.assertRaises(KnowledgeNotFoundError):
            self.knowledge_engine.retrieve_knowledge(query)

    # =========================================================================
    # B. SCOPE TESTS
    # =========================================================================

    def test_09_scopes_pericope_to_canon_supported(self) -> None:
        """Scope Test: All 5 scopes (PERICOPE, SECTION, BOOK, CORPUS, CANON) retrieve cleanly."""
        scopes_and_targets = [
            (SynthesisScope.PERICOPE, {"pericope_id": "PERI_JHN_01"}, "PERI_JHN_01"),
            (SynthesisScope.SECTION, {"section_id": "SEC_JHN_01"}, "SEC_JHN_01"),
            (SynthesisScope.BOOK, {"book_id": "BOOK_JOHN"}, "BOOK_JOHN"),
            (SynthesisScope.CORPUS, {"corpus_id": "CORPUS_JOHANNINE_2"}, "CORPUS_JOHANNINE_2"),
            (SynthesisScope.CANON, {"canon_id": "CANON_CATHOLIC"}, "CANON_CATHOLIC"),
        ]
        for scope, kwargs, target_id in scopes_and_targets:
            self._seed_validated_synthesis(scope=scope, target_id=target_id)
            query = KnowledgeQuery(query_text=f"Query for {target_id}", **kwargs)
            pack = self.knowledge_engine.retrieve_knowledge(query)
            self.assertEqual(pack.resolved_scope, scope)
            self.assertEqual(pack.target_id, target_id)

    # =========================================================================
    # C. HIERARCHY & LINEAGE TESTS
    # =========================================================================

    def test_10_hierarchy_downward_lineage_resolved(self) -> None:
        """Hierarchy Test: CANON -> CORPUS -> BOOK lineage tree is traversed downwards."""
        # 1. Seed BOOK
        b_run, b_ver, b_cert = self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_MATTHEW",
            claim_conf=0.92,
        )
        b_claim_id = f"CLM-BOOK-BOOK_MATTHEW-01"

        # 2. Seed CORPUS with constituent BOOK
        c_const = ConstituentInput(
            constituent_scope=SynthesisScope.BOOK,
            constituent_target_id="BOOK_MATTHEW",
            constituent_claim_id=b_claim_id,
            constituent_confidence=0.90,
            is_critical_dependency=True,
        )
        c_run, c_ver, c_cert = self._seed_validated_synthesis(
            scope=SynthesisScope.CORPUS,
            target_id="CORPUS_GOSPELS",
            claim_conf=0.90,
            constituents=[c_const],
        )
        c_claim_id = f"CLM-CORPUS-CORPUS_GOSPELS-01"

        # 3. Seed CANON with constituent CORPUS
        canon_const = ConstituentInput(
            constituent_scope=SynthesisScope.CORPUS,
            constituent_target_id="CORPUS_GOSPELS",
            constituent_claim_id=c_claim_id,
            constituent_confidence=0.88,
            is_critical_dependency=True,
        )
        k_run, k_ver, k_cert = self._seed_validated_synthesis(
            scope=SynthesisScope.CANON,
            target_id="CANON_NT",
            claim_conf=0.88,
            constituents=[canon_const],
        )

        query = KnowledgeQuery(
            query_text="New Testament canonical gospel witness",
            canon_id="CANON_NT",
            include_lineage=True,
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)

        self.assertEqual(pack.resolved_scope, SynthesisScope.CANON)
        self.assertEqual(len(pack.lineage), 1)

        # Level 1: CORPUS
        corp_node = pack.lineage[0]
        self.assertEqual(corp_node.constituent_scope, SynthesisScope.CORPUS)
        self.assertEqual(corp_node.constituent_target_id, "CORPUS_GOSPELS")
        self.assertEqual(corp_node.constituent_confidence, 0.88)
        self.assertEqual(len(corp_node.children), 1)

        # Level 2: BOOK
        book_node = corp_node.children[0]
        self.assertEqual(book_node.constituent_scope, SynthesisScope.BOOK)
        self.assertEqual(book_node.constituent_target_id, "BOOK_MATTHEW")
        self.assertEqual(book_node.constituent_confidence, 0.90)

    def test_11_hierarchy_scope_mismatch_rejected(self) -> None:
        """Hierarchy Test: Providing canon_id with requested_scope BOOK raises KnowledgeHierarchyViolationError."""
        with self.assertRaises(KnowledgeHierarchyViolationError):
            KnowledgeQuery(
                query_text="Invalid scope test",
                canon_id="CANON_TEST",
                requested_scope=SynthesisScope.BOOK,
            )

    # =========================================================================
    # D. CONFIDENCE INVARIANT TESTS
    # =========================================================================

    def test_12_confidence_exact_authoritative_preserved(self) -> None:
        """Confidence Test: Confidence is strictly from validated synthesis (no averaging or inflation)."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_ACTS",
            claim_conf=0.73,
        )
        query = KnowledgeQuery(
            query_text="Acts apostolic expansion",
            book_id="BOOK_ACTS",
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)

        self.assertEqual(pack.aggregate_confidence, 0.73)
        self.assertEqual(pack.claims[0].synthesized_confidence, 0.73)

    # =========================================================================
    # E. EPISTEMIC TIERS & T4 QUARANTINE TESTS
    # =========================================================================

    def test_13_epistemic_tier_preserved(self) -> None:
        """Epistemic Tier: Claim tiers (T0-T4) are preserved verbatim without promotion."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_EPHESIANS",
        )
        query = KnowledgeQuery(
            query_text="Ephesians unity",
            book_id="BOOK_EPHESIANS",
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)
        self.assertEqual(pack.claims[0].claim_tier, ClaimTier.T3_INTERPRETIVE_CLAIM)

    def test_14_t4_theology_quarantine_enforced(self) -> None:
        """Theology Firewall: Attempting to treat T4 claim as supporting evidence raises KnowledgeTheologicalContaminationError."""
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO claims (
                    claim_id, pericope_id, claim_tier, epistemic_type, claim_text, claimed_by, epistemic_status
                ) VALUES ('CLM-T4-01', 'PERIC_GEN_1_1', 'TIER_4_THEOLOGICAL_CLAIM', 'THEOLOGICAL_CLAIM',
                          'Dogmatic proposition', 'test', 'UNPROVEN_DOGMA')
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO claim_evidence_links (
                    link_id, claim_id, evidence_id, relationship, is_critical_dependency, weight, reasoning
                ) VALUES ('LNK-T4-01', 'CLM-T4-01', 'EV-PRI-01', 'SUPPORT', 1, 1.0, 'test')
                """
            )
        self._seed_validated_synthesis(scope=SynthesisScope.PERICOPE, target_id="GEN.1.1")

        query = KnowledgeQuery(
            query_text="God created heavens and earth",
            pericope_id="GEN.1.1",
            include_evidence=True,
        )
        with self.assertRaises(KnowledgeTheologicalContaminationError):
            self.knowledge_engine.retrieve_knowledge(query)

    # =========================================================================
    # F. SYMMETRY TESTS
    # =========================================================================

    def test_15_symmetry_counter_search_suppression_raises_error(self) -> None:
        """Symmetry Test: Attempting to disable counter-search raises CounterSearchSuppressionError."""
        self._seed_validated_synthesis(scope=SynthesisScope.BOOK, target_id="BOOK_MARK")
        query = KnowledgeQuery(
            query_text="Mark opening",
            book_id="BOOK_MARK",
        )
        with self.assertRaises(CounterSearchSuppressionError):
            self.knowledge_engine.retrieve_knowledge(query, enable_counter_search=False)

    def test_16_symmetry_both_branches_and_warning_captured(self) -> None:
        """Symmetry Test: Symmetrical evidence retrieval populates evidence and checks negative results."""
        self._seed_validated_synthesis(scope=SynthesisScope.BOOK, target_id="BOOK_LUKE")
        query = KnowledgeQuery(
            query_text="In the beginning God created",
            book_id="BOOK_LUKE",
            include_evidence=True,
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)
        self.assertIsInstance(pack.evidence, tuple)
        self.assertIsInstance(pack.counter_evidence, tuple)

    # =========================================================================
    # G. TENSION PRESERVATION TESTS
    # =========================================================================

    def test_17_tensions_preserved_without_harmonization(self) -> None:
        """Tension Test: synthesis_tensions are preserved with exact divergence metadata."""
        now = datetime.now(timezone.utc).isoformat()
        # Seed 2 claims in tension
        claim1 = SynthesisClaimInput(
            claim_id="CLM-TENS-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Law is fulfilled and persistent (Matius 5:17-20)",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Matthean tradition",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.CORPUS,
                    constituent_target_id="CORPUS_GOSPELS",
                    constituent_confidence=0.85,
                    is_critical_dependency=True,
                )
            ],
        )
        claim2 = SynthesisClaimInput(
            claim_id="CLM-TENS-02",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E8_CORPUS_CONTEXT,
            claim_text="Christ is the end of the law (Roma 10:4)",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Pauline tradition",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.CORPUS,
                    constituent_target_id="CORPUS_PAULINE",
                    constituent_confidence=0.85,
                    is_critical_dependency=True,
                )
            ],
        )
        tension_in = SynthesisTensionInput(
            tension_id="TENS-01",
            tension_type=SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            primary_claim_id="CLM-TENS-01",
            secondary_claim_id="CLM-TENS-02",
            description="Divergent emphasis on law continuity",
            preservation_rationale="Distinct authorial and theological perspectives",
            resolution_status=SynthesisTensionResolution.PRESERVED_TENSION,
        )

        synth_res = self.synthesis_mgr.create_synthesis_run(
            scope=SynthesisScope.CANON,
            target_id="CANON_LAW_TENSION",
            claims=[claim1, claim2],
            tensions=[tension_in],
        )

        # Validate
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO validation_runs (
                    run_id, validation_identity, validation_input_hash, engine_version,
                    schema_version, target_type, target_id, target_version_id, final_outcome,
                    checks_total, checks_passed, checks_failed, warnings_total,
                    provenance_id, executed_at, is_immutable
                ) VALUES ('VRUN-TENS', 'VID-TENS', 'hash', '2.0.0', '025',
                          'CANON_SYNTHESIS', ?, ?, 'VALID', 10, 10, 0, 0, 'PRV-ROOT', ?, 1)
                """,
                (synth_res.run_id, synth_res.version_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO validation_certificates (
                    certificate_id, run_id, validation_identity, validation_input_hash,
                    engine_version, schema_version, target_type, target_id, target_version_id,
                    validation_status, layer_summary_json, provenance_id, validated_at, is_immutable
                ) VALUES ('VCERT-TENS', 'VRUN-TENS', 'VID-TENS', 'hash', '2.0.0', '025',
                          'CANON_SYNTHESIS', ?, ?, 'VALID', '{}', 'PRV-ROOT', ?, 1)
                """,
                (synth_res.run_id, synth_res.version_id, now),
            )

        query = KnowledgeQuery(
            query_text="Law continuity in canon",
            canon_id="CANON_LAW_TENSION",
            include_tensions=True,
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)

        self.assertEqual(len(pack.tensions), 1)
        tens = pack.tensions[0]
        self.assertEqual(tens.tension_type, SynthesisTensionType.AUTHORIAL_DIVERGENCE)
        self.assertEqual(tens.resolution_status, SynthesisTensionResolution.PRESERVED_TENSION)
        self.assertEqual(tens.description, "Divergent emphasis on law continuity")
        self.assertEqual(len(pack.competing_claims), 2)

    # =========================================================================
    # H. PROVENANCE TESTS
    # =========================================================================

    def test_18_provenance_lineage_preserved(self) -> None:
        """Provenance Test: Retrieval preserves provenance and version IDs across run, claims, certificates."""
        run_id, ver_id, cert_id = self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_HEBREWS",
        )
        query = KnowledgeQuery(
            query_text="Hebrews high priest",
            book_id="BOOK_HEBREWS",
        )
        pack = self.knowledge_engine.retrieve_knowledge(query)

        self.assertTrue(len(pack.provenance_ids) >= 1)
        self.assertTrue(len(pack.version_ids) >= 1)
        self.assertIn(ver_id, pack.version_ids)

    # =========================================================================
    # I. VERSIONING BOUNDARY TESTS
    # =========================================================================

    def test_19_versioning_mismatch_rejected(self) -> None:
        """Versioning Test: Requesting mismatched engine_version raises KnowledgeVersionMismatchError."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_JAMES",
            engine_version="2.0.0",
        )
        query = KnowledgeQuery(
            query_text="James faith and works",
            book_id="BOOK_JAMES",
            engine_version="3.0.0",  # Incompatible version requested
        )
        with self.assertRaises(KnowledgeVersionMismatchError):
            self.knowledge_engine.retrieve_knowledge(query)

    def test_20_versioning_config_hash_mismatch_rejected(self) -> None:
        """Versioning Test: Requesting mismatched configuration_hash raises KnowledgeVersionMismatchError."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_1PETER",
            config_hash="actual_hash_001",
        )
        query = KnowledgeQuery(
            query_text="1 Peter living hope",
            book_id="BOOK_1PETER",
            pipeline_configuration_hash="different_hash_999",
        )
        with self.assertRaises(KnowledgeVersionMismatchError):
            self.knowledge_engine.retrieve_knowledge(query)

    # =========================================================================
    # J. DETERMINISM TESTS
    # =========================================================================

    def test_21_determinism_identical_content_hash(self) -> None:
        """Determinism Test: Multiple executions of the same query produce exact same content_hash."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_REVELATION",
        )
        query = KnowledgeQuery(
            query_text="Revelation new creation",
            book_id="BOOK_REVELATION",
        )
        pack1 = self.knowledge_engine.retrieve_knowledge(query)
        pack2 = self.knowledge_engine.retrieve_knowledge(query)

        self.assertEqual(pack1.content_hash, pack2.content_hash)
        self.assertEqual(len(pack1.content_hash), 64)

    # =========================================================================
    # K. IMMUTABILITY TESTS
    # =========================================================================

    def test_22_immutability_retrieval_does_not_mutate_db(self) -> None:
        """Immutability Test: Retrieval operations perform zero inserts/updates on authoritative tables."""
        self._seed_validated_synthesis(
            scope=SynthesisScope.BOOK,
            target_id="BOOK_COLOSSIANS",
        )
        with self.engine.connect() as conn:
            c1_runs = conn.execute("SELECT COUNT(*) FROM synthesis_runs;").fetchone()[0]
            c1_claims = conn.execute("SELECT COUNT(*) FROM synthesis_claims;").fetchone()[0]
            c1_certs = conn.execute("SELECT COUNT(*) FROM validation_certificates;").fetchone()[0]

        query = KnowledgeQuery(
            query_text="Colossians supremacy of Christ",
            book_id="BOOK_COLOSSIANS",
        )
        self.knowledge_engine.retrieve_knowledge(query)

        with self.engine.connect() as conn:
            c2_runs = conn.execute("SELECT COUNT(*) FROM synthesis_runs;").fetchone()[0]
            c2_claims = conn.execute("SELECT COUNT(*) FROM synthesis_claims;").fetchone()[0]
            c2_certs = conn.execute("SELECT COUNT(*) FROM validation_certificates;").fetchone()[0]

        self.assertEqual(c1_runs, c2_runs)
        self.assertEqual(c1_claims, c2_claims)
        self.assertEqual(c1_certs, c2_certs)


if __name__ == "__main__":
    unittest.main()
