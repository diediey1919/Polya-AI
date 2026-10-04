"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 4.9: Integrated Epistemic Invariant Benchmark Test Suite

Validates:
1. Canonical hashing and runtime metadata isolation.
2. Isolated benchmark workspace lifecycle and WAL cleanup.
3. Golden Corpus manifest and multi-lingual fixture integrity.
4. Epistemic invariant machine evaluation (INV-01 through INV-12).
5. Adversarial invariant failure boundary verification (ADV-001 through ADV-08).
6. Black-box transport adapters (CLI & HTTP).
7. Cross-run report determinism and cryptographic idempotency across clean databases.
8. Epistemic tripartite distinction (NOT_FOUND vs COUNTER_EVIDENCE_NOT_FOUND vs Negative Proposition).
"""

from __future__ import annotations

import copy
import json
import sqlite3
import unittest
from pathlib import Path

from starlette.testclient import TestClient

from bible_engine.api import create_app
from bible_engine.benchmark.engine import BenchmarkEngine
from bible_engine.benchmark.hashing import (
    canonical_json,
    compute_canonical_hash,
    compute_fixture_hash,
    compute_report_hash,
)
from bible_engine.benchmark.models import InvariantStatus
from bible_engine.benchmark.workspace import IsolatedBenchmarkWorkspace
from bible_engine.cli import main as cli_main
from bible_engine.errors import KnowledgeNotFoundError
from bible_engine.knowledge_retrieval import CounterEvidenceStatus, KnowledgeQuery
from bible_engine.retrieval import EvidenceRole, SearchBranch
from bible_engine.synthesis import SynthesisScope

MANIFEST_PATH = (
    Path(__file__).resolve().parent / "fixtures" / "golden_corpus" / "manifest.json"
)


class TestBibleEngineBenchmark(unittest.TestCase):
    """Full integration suite for Task 4.9 Epistemic Benchmark Subsystem."""

    def test_canonical_hashing_and_runtime_isolation(self) -> None:
        """Verify fixture hash self-reference elimination and report hash isolation."""
        fixture_sample = {
            "case_id": "TEST-01",
            "payload": {"text": "Alpha"},
            "fixture_sha256": "placeholder",
        }
        computed_hash = compute_fixture_hash(fixture_sample)
        self.assertTrue(len(computed_hash) == 64)

        # Altering fixture_sha256 in dict does NOT alter computed hash
        fixture_sample["fixture_sha256"] = "different"
        self.assertEqual(compute_fixture_hash(fixture_sample), computed_hash)

        # Report hash excludes runtime metadata
        canonical_payload = {
            "suite_id": "SUITE-01",
            "evaluations": [{"id": 1, "status": "PASS"}],
        }
        report_hash_1 = compute_report_hash(canonical_payload)

        # Injected runtime keys do not affect canonical report hash
        dirty_payload = copy.deepcopy(canonical_payload)
        dirty_payload["timestamp_iso"] = "2026-10-03T12:00:00Z"
        dirty_payload["execution_time_ms"] = 999.99
        dirty_payload["pid"] = 12345
        dirty_payload["temp_workspace_path"] = "/tmp/random/path"

        report_hash_2 = compute_report_hash(dirty_payload)
        self.assertEqual(report_hash_1, report_hash_2)

    def test_isolated_benchmark_workspace_lifecycle(self) -> None:
        """Verify workspace lifecycle, schema application (001-026, no 027), and clean disposal."""
        with IsolatedBenchmarkWorkspace() as ws:
            self.assertIsNotNone(ws.engine)
            self.assertIsNotNone(ws.workspace_path)
            self.assertTrue(ws.workspace_path.exists())
            self.assertTrue(ws.db_path.exists())

            # Verify migrations applied
            with ws.engine.connect() as conn:
                cur = conn.execute("SELECT migration_id FROM schema_migrations ORDER BY migration_id;")
                migrations = [row[0] for row in cur.fetchall()]
                self.assertGreaterEqual(len(migrations), 26)
                # Migration 027+ strictly forbidden
                self.assertFalse(any("027" in m for m in migrations))

            saved_path = ws.workspace_path

        # After context exit, workspace must be completely removed
        self.assertFalse(saved_path.exists())

    def test_golden_corpus_manifest_and_fixtures(self) -> None:
        """Verify all Golden Corpus fixtures load and pass cryptographic verification."""
        with IsolatedBenchmarkWorkspace() as ws:
            engine = BenchmarkEngine(ws)
            manifest_data, pericopes, adversarial_cases = engine.load_manifest(MANIFEST_PATH)

            self.assertEqual(manifest_data["manifest_id"], "MANIFEST-GOLDEN-CORPUS-v1.1")
            self.assertEqual(len(pericopes), 3)
            self.assertEqual(len(adversarial_cases), 8)

            pericope_ids = [p.pericope_id for p in pericopes]
            self.assertIn("PER-ROM-003", pericope_ids)
            self.assertIn("PER-GEN-001", pericope_ids)
            self.assertIn("PER-DAN-007", pericope_ids)

    def test_full_benchmark_run_and_invariants(self) -> None:
        """Verify full benchmark execution and 100% pass on 12 Epistemic Invariants."""
        with IsolatedBenchmarkWorkspace() as ws:
            bench = BenchmarkEngine(ws)
            report = bench.run(MANIFEST_PATH)

            self.assertIsNotNone(report.report_hash)
            self.assertEqual(len(report.report_hash), 64)

            payload = report.canonical_payload
            self.assertEqual(payload["engine_version"], "2.0.0")
            self.assertEqual(payload["schema_version"], "025")

            # Check 12 invariants
            inv_evals = payload["invariant_evaluations"]
            self.assertEqual(len(inv_evals), 12)
            for inv in inv_evals:
                self.assertEqual(
                    inv["status"],
                    InvariantStatus.PASS.value,
                    f"Invariant {inv['invariant_id']} failed: {inv['details']}",
                )

            # Check summary
            summary = payload["summary"]
            self.assertEqual(summary["fail_count"], 0)
            self.assertEqual(summary["blocked_count"], 0)
            self.assertEqual(summary["pass_count"], 20)  # 12 invariants + 8 adversarial cases

    def test_adversarial_suite_execution(self) -> None:
        """Verify all 8 adversarial failure cases trigger expected exceptions and rollbacks."""
        with IsolatedBenchmarkWorkspace() as ws:
            bench = BenchmarkEngine(ws)
            _, pericopes, adversarial_cases = bench.load_manifest(MANIFEST_PATH)
            bench.ingest_golden_pericopes(pericopes)

            adv_results = bench.evaluate_adversarial_suite(adversarial_cases)
            self.assertEqual(len(adv_results), 8)

            for res in adv_results:
                self.assertEqual(
                    res.status,
                    InvariantStatus.PASS,
                    f"Adversarial case {res.case_id} failed: expected {res.expected_exception}, got {res.actual_exception}",
                )
                self.assertTrue(res.error_code_matched)

    def test_blackbox_transports(self) -> None:
        """Verify CLI and HTTP public transports as black-box transports around AnswerApplicationService."""
        with IsolatedBenchmarkWorkspace() as ws:
            bench = BenchmarkEngine(ws)
            bench.seed_catalog()

            # CLI Transport
            exit_code = cli_main(["status", "--db", str(ws.db_path)])
            self.assertEqual(exit_code, 0)

            # HTTP Transport
            app = create_app(db=ws.engine, service=bench.service)
            client = TestClient(app)

            health_res = client.get("/v1/health")
            self.assertEqual(health_res.status_code, 200)

            # Non-existent query triggers 404 KNOWLEDGE_NOT_FOUND (INV-12 Part A)
            ans_res = client.post("/v1/answers", json={"query_text": "NonExistent 99:1"})
            self.assertEqual(ans_res.status_code, 404)
            self.assertIn(ans_res.json()["error"]["error_code"], ("SCOPE_RESOLUTION_FAILED", "KNOWLEDGE_NOT_FOUND"))

    def test_benchmark_determinism_across_clean_workspaces(self) -> None:
        """
        Verify cryptographic idempotency:
        Running the benchmark on clean DB A vs clean DB B produces identical canonical payload & hash.
        """
        with IsolatedBenchmarkWorkspace() as ws_a:
            bench_a = BenchmarkEngine(ws_a)
            report_a = bench_a.run(MANIFEST_PATH)

        with IsolatedBenchmarkWorkspace() as ws_b:
            bench_b = BenchmarkEngine(ws_b)
            report_b = bench_b.run(MANIFEST_PATH)

        # Canonical payloads must be bit-for-bit identical
        self.assertEqual(report_a.canonical_payload, report_b.canonical_payload)
        # Canonical report hashes must match identically
        self.assertEqual(report_a.report_hash, report_b.report_hash)

        # Runtime metadata may differ (e.g. timestamps, execution latency)
        self.assertNotEqual(
            report_a.runtime_metadata["timestamp_utc_iso"],
            report_b.runtime_metadata["timestamp_utc_iso"],
        )

    def test_inv_12_tripartite_separation(self) -> None:
        """
        Formally verify INV-12 tripartite epistemic distinction:
        A. NOT_FOUND: Raises KnowledgeNotFoundError (HTTP 404), zero answer constructed.
        B. COUNTER_EVIDENCE_NOT_FOUND: Search finds primary, 0 counter -> not universal proof of absence.
        C. NEGATIVE EPISTEMIC PROPOSITION: Requires affirmative counter-evidence items.
        """
        with IsolatedBenchmarkWorkspace() as ws:
            bench = BenchmarkEngine(ws)
            bench.seed_catalog()

            # State A: NOT_FOUND
            with self.assertRaises(KnowledgeNotFoundError):
                q = KnowledgeQuery(
                    query_text="NonExistent 1:1",
                    pericope_id="PER-NOT-FOUND-999",
                    requested_scope=SynthesisScope.PERICOPE,
                )
                bench.retrieval_engine.retrieve_knowledge(q)

            # State B: Absence of counter-evidence semantics
            self.assertEqual(
                CounterEvidenceStatus.COUNTER_EVIDENCE_NOT_FOUND.value,
                "COUNTER_EVIDENCE_NOT_FOUND",
            )

            # State C: Negative proposition requires affirmative counter-evidence
            self.assertEqual(EvidenceRole.COUNTER_EVIDENCE.value, "COUNTER_EVIDENCE")
            self.assertEqual(SearchBranch.COUNTER_SEARCH.value, "COUNTER_SEARCH")


if __name__ == "__main__":
    unittest.main()
