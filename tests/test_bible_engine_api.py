"""
Task 4.8: Test Suite for Public HTTP Adapter (bible_engine.api).
Tests:
- POST /v1/answers (with render_markdown, check_freshness, record_ledger)
- POST /v1/plans (QueryPlan fields, raw_query preservation)
- GET  /v1/answers/{answer_id}/freshness (validation, ledger lookup, freshness report)
- GET  /v1/health
- Exact Error Envelope & Deterministic HTTP Status Mappings (400, 403, 404, 409, 422, 500, 503)
- Canonical identity immutability and wire projection segregation
- FastAPI import isolation
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerConstructor,
    compute_answer_content_hash,
    compute_answer_id,
    record_answer_provenance,
    record_answer_version,
)
from bible_engine.api import create_app
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AmbiguousTargetError,
    AnswerEpistemicTierViolationError,
    DatabaseConnectionError,
    KnowledgeConfidenceInflationError,
    KnowledgeNotFoundError,
    KnowledgeQueryValidationError,
    MissingValidationCertificateError,
    QuerySyntaxError,
    ReadOnlyViolationError,
    ScopeResolutionError,
    ServiceOrchestrationError,
    UnvalidatedKnowledgeRetrievalError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.knowledge_retrieval import (
    AuthoritativeClaimItem,
    AuthoritativeEvidenceItem,
    ConstituentLineageNode,
    KnowledgePackResult,
    KnowledgeQuery,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker
from bible_engine.query_planning import QueryPlan, QueryPlanner
from bible_engine.retrieval import CandidateSource, EvidenceRole, SearchBranch
from bible_engine.service import AnswerApplicationService, AnswerRequest, AnswerResponse
from bible_engine.synthesis import SynthesisClaimStatus, SynthesisScope
from bible_engine.validation import ValidationCertificate
from bible_engine.versioning import VersionManager


def make_test_pack(
    query_text: str = "Roma 3:1-5",
    target_id: str = "PER-ROM-003",
    resolved_scope: SynthesisScope = SynthesisScope.PERICOPE,
    aggregate_confidence: float = 0.88,
    schema_version: str = "025",
) -> KnowledgePackResult:
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
        "tensions": [],
        "competing_claims": [],
        "evidence": [e.evidence_id for e in sorted(evidence, key=lambda x: x.evidence_id)],
        "counter_evidence": [],
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
        tensions=(),
        competing_claims=(),
        evidence=evidence,
        counter_evidence=(),
        lineage=lineage,
        validation_certificates=certs,
        provenance_ids=prov_ids,
        version_ids=ver_ids,
        warnings=(),
        content_hash=content_hash,
    )


class TestBibleEngineAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_api.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.db_config)
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        self.runner.apply_pending()

        self._seed_catalog()

        self.planner = QueryPlanner(self.engine)
        self.constructor = AnswerConstructor()
        self.prov_tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)

        self.mock_retrieval = MagicMock()
        self.pack = make_test_pack()
        self.mock_retrieval.retrieve_knowledge.return_value = self.pack

        self.service = AnswerApplicationService(
            db=self.engine,
            planner=self.planner,
            retrieval_engine=self.mock_retrieval,
            constructor=self.constructor,
            provenance_tracker=self.prov_tracker,
            version_manager=self.version_mgr,
        )

        self.app = create_app(db=self.engine, service=self.service)
        self.client = TestClient(self.app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_catalog(self) -> None:
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
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, content_hash, transformation_type, schema_version, agent_id, created_at, is_immutable)
                VALUES ('PRV-ROOT', 'SOURCE_TEXT', 'SYS-ROOT', 'root_hash', 'ORIGIN', '025', 'system', '2026-10-02T00:00:00Z', 1);
                """
            )
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
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN-RUN-001', 'PERICOPE', 'PER-ROM-003', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.88, 'COMPLETED', 'PRV-ROOT', 'VER-PER-001', '2026-10-02T00:00:00Z');
                """
            )
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

    # 1. GET /v1/health
    def test_health_endpoint(self) -> None:
        """GET /v1/health returns 200 with engine health metadata."""
        resp = self.client.get("/v1/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["engine_version"], "2.0.0")
        self.assertEqual(data["schema_version"], "025")
        self.assertEqual(data["database"], "connected")

    # 2. POST /v1/plans
    def test_post_plans_endpoint(self) -> None:
        """POST /v1/plans generates deterministic QueryPlan transport wire representation."""
        payload = {
            "query_text": "Roma 3:1-5",
            "requested_scope": "PERICOPE",
            "limit": 30,
            "include_lineage": True,
            "include_evidence": True,
            "include_tensions": True,
        }
        resp = self.client.post("/v1/plans", json=payload)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertTrue(data["plan_id"].startswith("PLAN-"))
        self.assertEqual(data["raw_query"], "Roma 3:1-5")
        self.assertEqual(data["normalized_query"], "Roma 3:1-5")
        self.assertEqual(data["canonical_passage_reference"], "Roma 3:1-5")
        self.assertEqual(data["resolved_scope"], "PERICOPE")
        self.assertEqual(data["resolved_target_id"], "PER-ROM-003")
        self.assertEqual(data["limit"], 30)
        self.assertIn("compiled_query", data)
        self.assertEqual(data["compiled_query"]["query_text"], "Roma 3:1-5")

    # 3. POST /v1/answers (Base, Render Markdown, Freshness, Ledger)
    def test_post_answers_base(self) -> None:
        """POST /v1/answers returns valid AnswerResponse with ANS- answer ID."""
        payload = {
            "query_text": "Roma 3:1-5",
            "render_markdown": False,
            "check_freshness": False,
            "record_ledger": False,
        }
        resp = self.client.post("/v1/answers", json=payload)
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        data = body["data"]
        ans = data["answer"]

        # 1. Answer ID uses ANS- prefix
        ans_id = ans["identity"]["answer_id"]
        self.assertTrue(ans_id.startswith("ANS-"))
        self.assertTrue(re.match(r"^ANS-[a-f0-9]{16}$", ans_id))
        self.assertFalse(ans_id.startswith("ans_"))

        # 2. Canonical payload matches AnswerArtifact.to_canonical_dict()
        canon = ans["canonical_payload"]
        self.assertEqual(canon["query_text"], "Roma 3:1-5")
        self.assertEqual(canon["target_id"], "PER-ROM-003")
        self.assertNotIn("answer_id", canon)
        self.assertNotIn("content_hash", canon)
        self.assertNotIn("formatted_markdown", canon)

        # 3. Presentation markdown is null when render_markdown=False
        self.assertIsNone(ans["presentation"]["formatted_markdown"])

        # 4. Hash preservation
        self.assertEqual(canon["input_knowledge_pack_hash"], self.pack.content_hash)
        self.assertIsNone(data["provenance_record_id"])
        self.assertIsNone(data["version_id"])

    def test_post_answers_render_markdown(self) -> None:
        """POST /v1/answers with render_markdown=True populates presentation.formatted_markdown."""
        payload = {
            "query_text": "Roma 3:1-5",
            "render_markdown": True,
        }
        resp = self.client.post("/v1/answers", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        md = data["answer"]["presentation"]["formatted_markdown"]
        self.assertIsNotNone(md)
        self.assertIn("# Authoritative Exegesis & Synthesis", md)

    def test_post_answers_check_freshness_and_record_ledger(self) -> None:
        """POST /v1/answers with check_freshness and record_ledger populates ledger IDs."""
        payload = {
            "query_text": "Roma 3:1-5",
            "check_freshness": True,
            "record_ledger": True,
        }
        resp = self.client.post("/v1/answers", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertIsNotNone(data["freshness_report"])
        self.assertFalse(data["freshness_report"]["is_stale"])
        self.assertIsNotNone(data["provenance_record_id"])
        self.assertIsNotNone(data["version_id"])

    # 4. GET /v1/answers/{answer_id}/freshness
    def test_freshness_invalid_id_format(self) -> None:
        """GET /v1/answers/{answer_id}/freshness rejects legacy ans_ prefix with 400."""
        resp = self.client.get("/v1/answers/ans_1234567890abcdef/freshness")
        self.assertEqual(resp.status_code, 400)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["error_code"], "QUERY_VALIDATION_ERROR")
        self.assertEqual(body["error"]["error_type"], "KnowledgeQueryValidationError")

    def test_freshness_not_found(self) -> None:
        """GET /v1/answers/{answer_id}/freshness on unpersisted answer returns 404."""
        resp = self.client.get("/v1/answers/ANS-1234567890abcdef/freshness")
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertFalse(body["success"])
        self.assertEqual(body["error"]["error_code"], "ANSWER_NOT_FOUND")

    def test_freshness_success_persisted(self) -> None:
        """GET /v1/answers/{answer_id}/freshness succeeds on persisted answer in ledger."""
        artifact = self.constructor.construct_answer(self.pack)
        with self.engine.transaction() as conn:
            p_rec = record_answer_provenance(self.prov_tracker, artifact, self.pack.content_hash, conn=conn)
            record_answer_version(self.version_mgr, artifact, provenance_id=p_rec.provenance_id, conn=conn)

        resp = self.client.get(f"/v1/answers/{artifact.answer_id}/freshness")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["answer_id"], artifact.answer_id)
        self.assertTrue(body["data"]["is_fresh"])
        self.assertEqual(body["data"]["current_schema_version"], "025")
        self.assertEqual(body["data"]["artifact_schema_version"], "025")

    # 5. Error Envelope and Status Mappings
    def test_error_envelope_structure_and_mappings(self) -> None:
        """Verify exact error envelope structure and HTTP status mappings."""
        test_cases = [
            (QuerySyntaxError("Invalid grammar"), 400, "QUERY_SYNTAX_ERROR"),
            (KnowledgeQueryValidationError("Invalid limit"), 400, "QUERY_VALIDATION_ERROR"),
            (ReadOnlyViolationError("Database is read only"), 403, "READ_ONLY_VIOLATION"),
            (ScopeResolutionError("Book not found"), 404, "SCOPE_RESOLUTION_FAILED"),
            (KnowledgeNotFoundError("Pack not found"), 404, "KNOWLEDGE_NOT_FOUND"),
            (AmbiguousTargetError("Multiple candidates"), 409, "AMBIGUOUS_TARGET"),
            (UnvalidatedKnowledgeRetrievalError("Synthesis not validated"), 422, "UNVALIDATED_KNOWLEDGE"),
            (MissingValidationCertificateError("No certificate"), 422, "MISSING_CERTIFICATE"),
            (AnswerEpistemicTierViolationError("Tier promotion"), 422, "TIER_VIOLATION"),
            (KnowledgeConfidenceInflationError("Confidence inflation"), 422, "CONFIDENCE_INFLATION"),
            (DatabaseConnectionError("Connection lost"), 503, "DATABASE_CONNECTION_ERROR"),
            (ServiceOrchestrationError("Pipeline aborted"), 500, "ORCHESTRATION_ERROR"),
        ]

        for exc, expected_status, expected_code in test_cases:
            with patch("bible_engine.service.AnswerApplicationService.execute", side_effect=exc):
                payload = {"query_text": "Roma 3:1-5"}
                resp = self.client.post("/v1/answers", json=payload)
                self.assertEqual(resp.status_code, expected_status, f"Failed status for {type(exc).__name__}")
                body = resp.json()
                self.assertFalse(body["success"])
                self.assertIn("error", body)
                err = body["error"]
                self.assertEqual(err["error_code"], expected_code)
                self.assertEqual(err["error_type"], type(exc).__name__)
                self.assertIn("message", err)
                self.assertIn("details", err)
                self.assertIn("target_id", err)
                # HTTP status MUST NOT be inside the error object
                self.assertNotIn("http_status", err)
                self.assertNotIn("status", err)


if __name__ == "__main__":
    unittest.main()
