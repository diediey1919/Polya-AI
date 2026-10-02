"""
Test Suite for Task 4.7 Deterministic Answer Application Service.
Specification: TASK 4.7 SPECIFICATION v1.3.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerConstructor,
    AnswerFreshnessInspector,
    AnswerFreshnessReport,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AnswerConstructionSubsystemError,
    KnowledgeHierarchyViolationError,
    KnowledgeNotFoundError,
    KnowledgeRetrievalSubsystemError,
    QueryPlanningError,
    QuerySyntaxError,
    ScopeResolutionError,
    ServiceOrchestrationError,
    VersioningError,
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
from bible_engine.provenance import ProvenanceTracker
from bible_engine.query_planning import QueryPlan, QueryPlanner
from bible_engine.service import (
    AnswerApplicationService,
    AnswerRequest,
    AnswerResponse,
)
from bible_engine.synthesis import (
    SynthesisClaimStatus,
    SynthesisScope,
    SynthesisTensionType,
)
from bible_engine.validation import ValidationCertificate
from bible_engine.versioning import VersionManager


from bible_engine.retrieval import CandidateSource, EvidenceRole, SearchBranch


def make_test_pack(
    query_text: str = "Roma 3:1-5",
    target_id: str = "PER-ROM-003",
    resolved_scope: SynthesisScope = SynthesisScope.PERICOPE,
    aggregate_confidence: float = 0.88,
    schema_version: str = "025",
) -> KnowledgePackResult:
    """Helper to build a cryptographically valid KnowledgePackResult."""
    claims = (
        AuthoritativeClaimItem(
            claim_id="CLM-001",
            run_id="SYN-RUN-001",
            scope=resolved_scope,
            target_id=target_id,
            claim_tier=ClaimTier.T0_RAW_OBSERVATION,
            primary_evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_text="P46 witnesses Romans 3 reading.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            synthesized_confidence=0.95,
            weakest_constituent_confidence=0.90,
            authorial_context="Pauline epistle context",
            is_harmonized=False,
            provenance_id="PRV-CLM-001",
            version_id="VER-CLM-001",
            validation_certificate_id="CERT-001",
            created_at="2026-10-02T00:00:00Z",
        ),
    )
    evidence = (
        AuthoritativeEvidenceItem(
            item_id="ITM-EV-001",
            evidence_id="EV-001",
            search_branch=SearchBranch.PRIMARY_SEARCH,
            evidence_role=EvidenceRole.SUPPORTING,
            candidate_source=CandidateSource.DIRECT_LOOKUP,
            item_confidence=0.95,
            item_rank=1,
            linked_claim_id="CLM-001",
            extracted_text="Text of Romans 3 in P46",
        ),
    )
    tensions: tuple[AuthoritativeTensionItem, ...] = ()
    counter_ev: tuple[AuthoritativeEvidenceItem, ...] = ()
    certs = (
        ValidationCertificate(
            certificate_id="CERT-001",
            run_id="VAL-RUN-001",
            validation_identity="VAL-ID-001",
            validation_input_hash="HASH-VAL-001",
            engine_version="2.0.0",
            schema_version=schema_version,
            target_type="PERICOPE",
            target_id=target_id,
            target_version_id="VER-PER-001",
            validation_status="VALID",
            layer_summary_json="{}",
            provenance_id="PRV-CERT-001",
            validated_at="2026-10-02T00:00:00Z",
        ),
    )
    lineage = (
        ConstituentLineageNode(
            constituent_link_id="LNK-001",
            parent_claim_id="CLM-001",
            constituent_scope=SynthesisScope.PERICOPE,
            constituent_target_id=target_id,
            constituent_claim_id="CLM-001",
            constituent_evidence_id="EV-001",
            constituent_confidence=0.95,
            is_critical_dependency=True,
            run_id="SYN-RUN-001",
            provenance_id="PRV-LNK-001",
            validation_certificate_id="CERT-001",
            children=(),
        ),
    )

    prov_ids = ("PRV-ROOT",)
    ver_ids = ("VER-CLM-001",)

    payload = {
        "resolved_scope": resolved_scope.value,
        "target_id": target_id,
        "synthesis_run_id": "SYN-RUN-001",
        "aggregate_confidence": round(aggregate_confidence, 6),
        "claims": [c.claim_id for c in sorted(claims, key=lambda x: x.claim_id)],
        "tensions": [t.tension_id for t in sorted(tensions, key=lambda x: x.tension_id)],
        "competing_claims": [],
        "evidence": [e.evidence_id for e in sorted(evidence, key=lambda x: x.evidence_id)],
        "counter_evidence": [e.evidence_id for e in sorted(counter_ev, key=lambda x: x.evidence_id)],
        "certificates": [c.certificate_id for c in sorted(certs, key=lambda x: x.certificate_id)],
        "provenance_ids": list(sorted(prov_ids)),
        "version_ids": list(sorted(ver_ids)),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    query = KnowledgeQuery(
        query_text=query_text,
        pericope_id=target_id,
        requested_scope=resolved_scope,
        engine_version="2.0.0",
        schema_version=schema_version,
    )

    return KnowledgePackResult(
        query=query,
        requested_scope=resolved_scope,
        resolved_scope=resolved_scope,
        target_id=target_id,
        synthesis_run_id="SYN-RUN-001",
        aggregate_confidence=aggregate_confidence,
        claims=claims,
        tensions=tensions,
        competing_claims=(),
        evidence=evidence,
        counter_evidence=counter_ev,
        lineage=lineage,
        validation_certificates=certs,
        provenance_ids=prov_ids,
        version_ids=ver_ids,
        warnings=(),
        content_hash=content_hash,
    )


class TestBibleEngineService(unittest.TestCase):
    """Integration and invariant test suite for Task 4.7 AnswerApplicationService."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_service.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.db_config)
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        self.runner.apply_pending()

        self._seed_catalog()

        # Wire subsystems
        self.planner = QueryPlanner(self.engine)
        self.retrieval_engine = AuthoritativeKnowledgeRetrievalEngine(self.engine)
        self.constructor = AnswerConstructor()
        self.prov_tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)

        self.service = AnswerApplicationService(
            db=self.engine,
            planner=self.planner,
            retrieval_engine=self.retrieval_engine,
            constructor=self.constructor,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_catalog(self) -> None:
        """Seed minimal catalog data."""
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO canons (canon_id, name, description, created_at)
                VALUES ('CANON-PROTESTANT-66', 'Protestant Canon', 'Standard 66-book canon', '2026-10-02T00:00:00Z');
                """
            )
            conn.execute(
                """
                INSERT INTO testaments (testament_id, canon_id, name, sort_order)
                VALUES ('TEST-NT', 'CANON-PROTESTANT-66', 'Perjanjian Baru', 2);
                """
            )
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('ROM', 'TEST-NT', 45, 'Roma', 'Romans', 'GREEK', 16);
                """
            )
            conn.execute(
                """
                INSERT INTO sections (section_id, book_id, title, start_chapter, start_verse, end_chapter, end_verse, genre)
                VALUES ('SEC-ROM-003', 'ROM', 'Righteousness by Faith', 3, 1, 3, 31, 'EPISTLE');
                """
            )
            conn.execute(
                """
                INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at)
                VALUES ('PER-ROM-003', 'ROM', 'Roma 3:1-5', 3, 1, 3, 5, 'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '1', '2026-10-02T00:00:00Z');
                """
            )
            # Provenance root
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, content_hash, transformation_type, schema_version, agent_id, created_at, is_immutable)
                VALUES ('PRV-ROOT', 'SOURCE_TEXT', 'SYS-ROOT', 'root_hash', 'ORIGIN', '025', 'system', '2026-10-02T00:00:00Z', 1);
                """
            )
            # Object Versions
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, provenance_id, status, change_reason, created_at, created_by)
                VALUES ('VER-PER-001', 'PERICOPE', 'PER-ROM-003', 1, 'h1', 'PRV-ROOT', 'ACTIVE', 'INITIAL_CREATION', '2026-10-02T00:00:00Z', 'SYSTEM');
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, provenance_id, status, change_reason, created_at, created_by)
                VALUES ('VER-CLM-001', 'CLAIM', 'CLM-001', 1, 'h2', 'PRV-ROOT', 'ACTIVE', 'INITIAL_CREATION', '2026-10-02T00:00:00Z', 'SYSTEM');
                """
            )
            # Synthesis Run
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN-RUN-001', 'PERICOPE', 'PER-ROM-003', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.88, 'COMPLETED', 'PRV-ROOT', 'VER-PER-001', '2026-10-02T00:00:00Z');
                """
            )
            # Validation Run and Certificate
            conn.execute(
                """
                INSERT INTO validation_runs (run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, final_outcome, checks_total, checks_passed, checks_failed, warnings_total, provenance_id, executed_at, is_immutable)
                VALUES ('VAL-RUN-001', 'VAL-ID-001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER-ROM-003', 'VER-PER-001', 'VALID', 10, 10, 0, 0, 'PRV-ROOT', '2026-10-02T00:00:00Z', 1);
                """
            )
            conn.execute(
                """
                INSERT INTO validation_certificates (certificate_id, run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, validation_status, layer_summary_json, provenance_id, validated_at, is_immutable)
                VALUES ('CERT-001', 'VAL-RUN-001', 'VAL-ID-001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER-ROM-003', 'VER-PER-001', 'VALID', '{}', 'PRV-ROOT', '2026-10-02T00:00:00Z', 1);
                """
            )

    # =========================================================================
    # 1. END-TO-END EXECUTION & INVARIANTS
    # =========================================================================

    def test_service_end_to_end_mocked_pack(self) -> None:
        """Verify full AnswerApplicationService pipeline with valid KnowledgePackResult."""
        mock_pack = make_test_pack(query_text="Roma 3:1-5", target_id="PER-ROM-003")

        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            req = AnswerRequest(
                query_text="Roma 3:1-5",
                check_freshness=False,
                record_ledger=False,
            )
            response = self.service.execute(req)

            self.assertIsInstance(response, AnswerResponse)
            self.assertEqual(response.artifact.query_text, "Roma 3:1-5")
            self.assertEqual(response.query_plan.canonical_passage_reference, "Roma 3:1-5")
            self.assertIsNone(response.freshness_report)
            self.assertIsNone(response.provenance_record_id)
            self.assertIsNone(response.version_id)
            self.assertGreater(response.execution_time_ms, 0.0)

            # Invariant: input_knowledge_pack_hash matches pack.content_hash
            self.assertEqual(
                response.artifact.input_knowledge_pack_hash,
                mock_pack.content_hash,
            )

            # Independent answer hash invariant
            self.assertNotEqual(
                response.artifact.content_hash,
                mock_pack.content_hash,
            )

    # =========================================================================
    # 2. FRESHNESS INSPECTION INTEGRATION
    # =========================================================================

    def test_service_freshness_disabled(self) -> None:
        """When check_freshness=False, freshness report must be None."""
        mock_pack = make_test_pack()
        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            req = AnswerRequest(query_text="Roma 3:1-5", check_freshness=False)
            resp = self.service.execute(req)
            self.assertIsNone(resp.freshness_report)

    def test_service_freshness_enabled_live_schema_authority(self) -> None:
        """
        When check_freshness=True, live schema version is queried from
        MigrationRunner(self.db).get_current_version(conn), NEVER artifact.schema_version.
        """
        mock_pack = make_test_pack(schema_version="025")
        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            req = AnswerRequest(query_text="Roma 3:1-5", check_freshness=True)

            with patch.object(
                AnswerFreshnessInspector,
                "inspect_freshness",
                wraps=AnswerFreshnessInspector.inspect_freshness,
            ) as spy_inspect:
                resp = self.service.execute(req)
                self.assertIsNotNone(resp.freshness_report)
                self.assertFalse(resp.freshness_report.is_stale)
                self.assertEqual(len(resp.freshness_report.stale_reasons), 0)

                # Verify current_schema_version passed to inspect_freshness was "025" from MigrationRunner
                spy_inspect.assert_called_once()
                call_args = spy_inspect.call_args[1]
                self.assertEqual(call_args["current_schema_version"], "025")

    def test_service_freshness_detects_stale_schema_boundary(self) -> None:
        """
        Verify that schema version mismatch between artifact ('024') and live schema ('025')
        is accurately detected and marked stale.
        """
        mock_pack = make_test_pack(schema_version="024")
        with patch.object(self.constructor, "schema_version", "024"):
            with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
                req = AnswerRequest(query_text="Roma 3:1-5", check_freshness=True)
                resp = self.service.execute(req)

                self.assertIsNotNone(resp.freshness_report)
                self.assertTrue(resp.freshness_report.is_stale)
                reasons = " ".join(resp.freshness_report.stale_reasons)
                self.assertIn("Schema boundary mismatch", reasons)

    # =========================================================================
    # 3. LEDGER PERSISTENCE & ATOMIC ROLLBACK
    # =========================================================================

    def test_service_record_ledger_success(self) -> None:
        """When record_ledger=True, provenance and version records are persisted atomically."""
        mock_pack = make_test_pack()
        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            req = AnswerRequest(query_text="Roma 3:1-5", record_ledger=True)
            resp = self.service.execute(req)

            self.assertIsNotNone(resp.provenance_record_id)
            self.assertIsNotNone(resp.version_id)

            # Verify rows exist in DB
            with self.engine.connect(read_only=True) as conn:
                prov_row = conn.execute(
                    "SELECT target_id, content_hash FROM provenance_records WHERE provenance_id = ?",
                    (resp.provenance_record_id,),
                ).fetchone()
                self.assertIsNotNone(prov_row)
                self.assertEqual(prov_row[0], resp.artifact.answer_id)

                ver_row = conn.execute(
                    "SELECT object_id, provenance_id FROM object_versions WHERE version_id = ?",
                    (resp.version_id,),
                ).fetchone()
                self.assertIsNotNone(ver_row)
                self.assertEqual(ver_row[0], resp.artifact.answer_id)
                self.assertEqual(ver_row[1], resp.provenance_record_id)

    def test_service_record_ledger_atomic_rollback_on_version_failure(self) -> None:
        """
        When version persistence fails, transaction rolls back completely:
        provenance record is rolled back, leaving zero orphaned rows.
        """
        mock_pack = make_test_pack()

        # Count provenance records before
        with self.engine.connect(read_only=True) as conn:
            initial_prov_count = conn.execute("SELECT count(*) FROM provenance_records;").fetchone()[0]

        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            with patch.object(
                self.version_mgr,
                "create_version",
                side_effect=sqlite3.OperationalError("Simulated disk error during version insertion"),
            ):
                req = AnswerRequest(query_text="Roma 3:1-5", record_ledger=True)
                with self.assertRaises(ServiceOrchestrationError) as ctx:
                    self.service.execute(req)

                self.assertIsInstance(ctx.exception.__cause__, sqlite3.OperationalError)
                self.assertIn("Ledger persistence failed due to database error.", str(ctx.exception))

        # Verify zero orphaned provenance rows
        with self.engine.connect(read_only=True) as conn:
            post_prov_count = conn.execute("SELECT count(*) FROM provenance_records;").fetchone()[0]
            self.assertEqual(post_prov_count, initial_prov_count)

    def test_service_nested_transaction_savepoint(self) -> None:
        """
        Verify that calling service.execute with record_ledger=True within an
        active outer transaction executes correctly using savepoints.
        """
        mock_pack = make_test_pack()
        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            req = AnswerRequest(query_text="Roma 3:1-5", record_ledger=True)

            with self.engine.transaction() as outer_conn:
                resp = self.service.execute(req, conn=outer_conn)
                self.assertIsNotNone(resp.provenance_record_id)
                self.assertIsNotNone(resp.version_id)

            # After outer transaction commit, verify records persisted
            with self.engine.connect(read_only=True) as conn:
                row = conn.execute(
                    "SELECT count(*) FROM provenance_records WHERE provenance_id = ?",
                    (resp.provenance_record_id,),
                ).fetchone()
                self.assertEqual(row[0], 1)

    # =========================================================================
    # 4. ERROR PROPAGATION & WRAPPING
    # =========================================================================

    def test_service_propagates_query_planning_errors_unchanged(self) -> None:
        """QuerySyntaxError and ScopeResolutionError propagate without wrapping."""
        with self.assertRaises(QuerySyntaxError):
            self.service.execute(AnswerRequest(query_text="   "))

        with self.assertRaises(ScopeResolutionError):
            self.service.execute(AnswerRequest(query_text="NonexistentBook 1:1"))

    def test_service_propagates_knowledge_hierarchy_errors_unchanged(self) -> None:
        """KnowledgeHierarchyViolationError propagates without wrapping."""
        req = AnswerRequest(
            query_text="Roma 3:1-5",
            requested_scope=SynthesisScope.CANON,  # Conflicts with PERICOPE resolved target
        )
        with self.assertRaises(KnowledgeHierarchyViolationError):
            self.service.execute(req)

    def test_service_wraps_persistence_infrastructure_error_preserving_cause(self) -> None:
        """Infrastructure exceptions during persistence wrap in ServiceOrchestrationError with __cause__."""
        mock_pack = make_test_pack()
        with patch.object(self.retrieval_engine, "retrieve_knowledge", return_value=mock_pack):
            with patch.object(
                self.prov_tracker,
                "record_deterministic",
                side_effect=sqlite3.DatabaseError("DB corrupted"),
            ):
                req = AnswerRequest(query_text="Roma 3:1-5", record_ledger=True)
                with self.assertRaises(ServiceOrchestrationError) as ctx:
                    self.service.execute(req)
                self.assertIsInstance(ctx.exception.__cause__, sqlite3.DatabaseError)


if __name__ == "__main__":
    unittest.main()
