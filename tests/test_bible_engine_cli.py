"""
Task 4.8: Test Suite for CLI Transport Adapter (bible_engine.cli).
Tests:
- Preservation of status and migrate commands
- query command with all semantic options
- plan command and field preservation
- freshness command and answer_id validation (^ANS-[a-f0-9]{16}$)
- Error envelopes and deterministic CLI exit codes (0, 1, 2, 3, 4, 5, 6)
- Transport projections without mutating canonical payloads
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerConstructor,
    AnswerFreshnessInspector,
    AnswerFreshnessReport,
    compute_answer_content_hash,
    compute_answer_id,
    record_answer_provenance,
    record_answer_version,
)
from bible_engine.provenance import ProvenanceTracker
from bible_engine.cli import main, serialize_answer_transport, serialize_query_plan_transport
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AmbiguousTargetError,
    AnswerEpistemicTierViolationError,
    KnowledgeNotFoundError,
    KnowledgeVersionMismatchError,
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
    AuthoritativeTensionItem,
    ConstituentLineageNode,
    KnowledgePackResult,
    KnowledgeQuery,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.query_planning import QueryPlan, QueryPlanner
from bible_engine.retrieval import CandidateSource, EvidenceRole, SearchBranch
from bible_engine.service import AnswerRequest, AnswerResponse
from bible_engine.synthesis import (
    SynthesisClaimStatus,
    SynthesisScope,
    SynthesisTensionType,
)
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


class TestBibleEngineCLI(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_cli.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.db_config)
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        self.runner.apply_pending()

        self._seed_catalog()

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

    def test_status_command(self) -> None:
        """status command runs cleanly with exit code 0."""
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = main(["status", "--db-path", self.db_path])
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("BIBLE ENGINE MIGRATION STATUS", output)

    def test_migrate_command(self) -> None:
        """migrate command runs cleanly with exit code 0."""
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = main(["migrate", "--db-path", self.db_path])
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertTrue("Database is already up to date" in output or "Successfully applied" in output)

    def test_plan_command_human_readable(self) -> None:
        """plan command executes and prints formatted summary."""
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = main(["plan", "Roma 3:1-5", "--db-path", self.db_path])
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("BIBLE ENGINE QUERY PLAN", output)
        self.assertIn("Plan ID:", output)
        self.assertIn("PLAN-", output)
        self.assertIn("Raw Query:        Roma 3:1-5", output)

    def test_plan_command_json(self) -> None:
        """plan command with --json returns valid JSON matching QueryPlan transport projection."""
        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = main([
                "plan",
                "Roma 3:1-5",
                "--scope", "PERICOPE",
                "--limit", "25",
                "--no-lineage",
                "--no-evidence",
                "--no-tensions",
                "--json",
                "--db-path", self.db_path,
            ])
        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["success"])
        plan_data = data["data"]
        self.assertTrue(plan_data["plan_id"].startswith("PLAN-"))
        self.assertEqual(plan_data["raw_query"], "Roma 3:1-5")
        self.assertEqual(plan_data["normalized_query"], "Roma 3:1-5")
        self.assertEqual(plan_data["canonical_passage_reference"], "Roma 3:1-5")
        self.assertEqual(plan_data["limit"], 25)
        self.assertFalse(plan_data["include_lineage"])
        self.assertFalse(plan_data["include_evidence"])
        self.assertFalse(plan_data["include_tensions"])
        self.assertIn("compiled_query", plan_data)

    def test_plan_syntax_error_exit_code_2(self) -> None:
        """plan command with invalid syntax exits with code 2."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = main(["plan", "", "--db-path", self.db_path])
        self.assertEqual(code, 2)

    def test_plan_json_error_envelope(self) -> None:
        """plan command with --json outputs frozen error envelope on failure."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = main(["plan", "", "--json", "--db-path", self.db_path])
        self.assertEqual(code, 2)
        err_data = json.loads(stderr.getvalue())
        self.assertFalse(err_data["success"])
        self.assertEqual(err_data["error"]["error_code"], "QUERY_SYNTAX_ERROR")
        self.assertEqual(err_data["error"]["error_type"], "QuerySyntaxError")
        self.assertIn("message", err_data["error"])

    def test_query_command_all_semantic_inputs_exposed(self) -> None:
        """query command parses all semantic inputs correctly into AnswerRequest."""
        pack = make_test_pack()
        constructor = AnswerConstructor()
        artifact = constructor.construct_answer(pack, render_markdown=True)
        planner = QueryPlanner(self.engine)
        plan = planner.plan("Roma 3:1-5")
        resp = AnswerResponse(
            artifact=artifact,
            query_plan=plan,
            freshness_report=None,
            provenance_record_id="PRV-ANS-001",
            version_id="VER-ANS-001",
            execution_time_ms=12.34,
        )

        with patch("bible_engine.service.AnswerApplicationService.execute", return_value=resp) as mock_exec:
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                code = main([
                    "query",
                    "Roma 3:1-5",
                    "--scope", "PERICOPE",
                    "--target-id", "PER-ROM-003",
                    "--source-corpus", "CORPUS-NT",
                    "--target-corpus", "CORPUS-OT",
                    "--source-version", "NA28",
                    "--pipeline-config-hash", "conf123",
                    "--limit", "40",
                    "--no-lineage",
                    "--no-evidence",
                    "--no-tensions",
                    "--render-markdown",
                    "--check-freshness",
                    "--record-ledger",
                    "--json",
                    "--db-path", self.db_path,
                ])
            self.assertEqual(code, 0)
            mock_exec.assert_called_once()
            call_req: AnswerRequest = mock_exec.call_args[0][0]
            self.assertEqual(call_req.query_text, "Roma 3:1-5")
            self.assertEqual(call_req.requested_scope, SynthesisScope.PERICOPE)
            self.assertEqual(call_req.explicit_target_id, "PER-ROM-003")
            self.assertEqual(call_req.source_corpus, "CORPUS-NT")
            self.assertEqual(call_req.target_corpus, "CORPUS-OT")
            self.assertEqual(call_req.source_version, "NA28")
            self.assertEqual(call_req.pipeline_configuration_hash, "conf123")
            self.assertEqual(call_req.limit, 40)
            self.assertFalse(call_req.include_lineage)
            self.assertFalse(call_req.include_evidence)
            self.assertFalse(call_req.include_tensions)
            self.assertTrue(call_req.render_markdown)
            self.assertTrue(call_req.check_freshness)
            self.assertTrue(call_req.record_ledger)

            # Validate wire payload structure
            data = json.loads(stdout.getvalue())
            self.assertTrue(data["success"])
            ans_wire = data["data"]["answer"]
            self.assertTrue(ans_wire["identity"]["answer_id"].startswith("ANS-"))
            self.assertIn("canonical_payload", ans_wire)
            self.assertIn("presentation", ans_wire)
            self.assertIsNotNone(ans_wire["presentation"]["formatted_markdown"])

    def test_freshness_command_invalid_id_exit_code_2(self) -> None:
        """freshness command rejects invalid answer_id format with exit code 2."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = main(["freshness", "ans_12345", "--db-path", self.db_path])
        self.assertEqual(code, 2)
        self.assertIn("QUERY_VALIDATION_ERROR", stderr.getvalue())

    def test_freshness_command_not_found_exit_code_3(self) -> None:
        """freshness command on non-existent answer exits with code 3."""
        stderr = io.StringIO()
        with patch("sys.stderr", stderr):
            code = main(["freshness", "ANS-1234567890abcdef", "--db-path", self.db_path])
        self.assertEqual(code, 3)
        self.assertIn("ANSWER_NOT_FOUND", stderr.getvalue())

    def test_freshness_command_success_with_persisted_answer(self) -> None:
        """freshness command verifies live persisted answer in ledger."""
        pack = make_test_pack()
        constructor = AnswerConstructor()
        artifact = constructor.construct_answer(pack)

        # Record answer provenance & version in ledgers
        tracker = ProvenanceTracker(self.engine)
        vm = VersionManager(self.engine)
        with self.engine.transaction() as conn:
            p_rec = record_answer_provenance(tracker, artifact, pack.content_hash, conn=conn)
            record_answer_version(version_manager=vm, artifact=artifact, provenance_id=p_rec.provenance_id, conn=conn)

        stdout = io.StringIO()
        with patch("sys.stdout", stdout):
            code = main(["freshness", artifact.answer_id, "--json", "--db-path", self.db_path])
        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["answer_id"], artifact.answer_id)
        self.assertTrue(data["data"]["is_fresh"])

    def test_exit_codes_mapping(self) -> None:
        """Test exit codes across exception categories."""
        cases = [
            (QuerySyntaxError("bad query"), 2),
            (ScopeResolutionError("target not found"), 3),
            (KnowledgeNotFoundError("pack not found"), 3),
            (AmbiguousTargetError("multiple matches"), 4),
            (KnowledgeVersionMismatchError("version mismatch"), 4),
            (UnvalidatedKnowledgeRetrievalError("blocked validation"), 5),
            (AnswerEpistemicTierViolationError("tier promotion"), 5),
            (ReadOnlyViolationError("cannot write"), 6),
            (ServiceOrchestrationError("orchestration failed"), 1),
        ]
        for exc, expected_code in cases:
            with patch("bible_engine.service.AnswerApplicationService.execute", side_effect=exc):
                stderr = io.StringIO()
                with patch("sys.stderr", stderr):
                    code = main(["query", "Roma 3:1-5", "--db-path", self.db_path])
                self.assertEqual(code, expected_code, f"Failed for {type(exc).__name__}")


if __name__ == "__main__":
    unittest.main()
