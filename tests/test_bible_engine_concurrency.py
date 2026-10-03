"""
Task 4.9.1 Concurrency Regression Test Suite:
1. BLOCKER 1: FastAPI Non-blocking Event Loop Execution
   - Event loop must not be blocked by AnswerApplicationService.execute()
   - Parallel threadpool execution of concurrent requests
2. BLOCKER 2: DatabaseEngine Connection and Transaction Isolation
   - A. concurrent writers
   - B. concurrent rollback
   - C. concurrent commit
   - D. nested savepoint
   - E. rollback of nested savepoint
   - F. concurrent provenance/version persistence
   - G. concurrent AnswerApplicationService execution
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock

import httpx

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
from bible_engine.query_planning import QueryPlanner
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


class TestFastAPIConcurrency(unittest.TestCase):
    """BLOCKER 1: Regression tests proving FastAPI event loop is not blocked."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_api_concur.db")
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

    def test_blocker1_event_loop_not_blocked_by_service_execute(self) -> None:
        """
        Verify that a long-running service.execute() call does NOT block the async event loop.
        A concurrent /v1/health request must respond immediately while /v1/answers is still processing.
        """
        original_execute = self.service.execute

        def slow_execute(req: AnswerRequest) -> AnswerResponse:
            time.sleep(0.3)
            return original_execute(req)

        self.service.execute = slow_execute  # type: ignore[assignment]

        async def run_scenario() -> None:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                # Launch slow answers request in background task
                post_task = asyncio.create_task(
                    client.post("/v1/answers", json={"query_text": "Roma 3:1-5"})
                )

                # Let event loop schedule the request into worker threadpool
                await asyncio.sleep(0.05)

                # Event loop must remain active and responsive to other requests
                start_health = time.perf_counter()
                health_resp = await client.get("/v1/health")
                health_latency = time.perf_counter() - start_health

                self.assertEqual(health_resp.status_code, 200)
                # Health request must complete quickly while post_task is still in-flight
                self.assertLess(health_latency, 0.20)
                self.assertFalse(post_task.done(), "post_answers must still be executing in worker thread")

                # Wait for post_answers to finish
                post_resp = await post_task
                self.assertEqual(post_resp.status_code, 200)
                self.assertTrue(post_resp.json()["success"])

        asyncio.run(run_scenario())

    def test_blocker1_concurrent_answers_execute_in_parallel_threads(self) -> None:
        """
        Verify that concurrent POST /v1/answers requests execute in parallel worker threads,
        and are not serialized on the event loop.
        """
        original_execute = self.service.execute

        def slow_execute(req: AnswerRequest) -> AnswerResponse:
            time.sleep(0.2)
            return original_execute(req)

        self.service.execute = slow_execute  # type: ignore[assignment]

        async def run_scenario() -> None:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                t0 = time.perf_counter()
                res1, res2 = await asyncio.gather(
                    client.post("/v1/answers", json={"query_text": "Roma 3:1-5"}),
                    client.post("/v1/answers", json={"query_text": "Roma 3:1-5"}),
                )
                elapsed = time.perf_counter() - t0

                self.assertEqual(res1.status_code, 200)
                self.assertEqual(res2.status_code, 200)
                # If serialized, elapsed would be >= 0.4s. Parallel execution must be < 0.35s.
                self.assertLess(elapsed, 0.35, f"Execution was serialized: took {elapsed:.3f}s")

        asyncio.run(run_scenario())


class TestDatabaseConnectionIsolation(unittest.TestCase):
    """
    BLOCKER 2: Concurrency regression test matrix for DatabaseEngine connection isolation.
    A. concurrent writers
    B. concurrent rollback
    C. concurrent commit
    D. nested savepoint
    E. rollback of nested savepoint
    F. concurrent provenance/version persistence
    G. concurrent AnswerApplicationService execution
    """

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_db_concur.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path, busy_timeout_ms=5000)
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
                CREATE TABLE IF NOT EXISTS concur_test (
                    id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    val TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )

    # -------------------------------------------------------------------------
    # A. Concurrent Writers
    # -------------------------------------------------------------------------
    def test_A_concurrent_writers(self) -> None:
        """
        Verify multiple threads concurrently executing transactions via DatabaseEngine.transaction().
        Assert each thread operates on a distinct connection and all rows commit cleanly.
        """
        num_threads = 5
        conn_ids: set[int] = set()
        lock = threading.Lock()
        errors: list[Exception] = []

        def worker(thread_idx: int) -> None:
            try:
                with self.engine.transaction() as conn:
                    with lock:
                        conn_ids.add(id(conn))
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        (f"writer_{thread_idx}", f"thread_{thread_idx}", f"payload_{thread_idx}", time.time()),
                    )
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent writers had errors: {errors}")
        self.assertEqual(len(conn_ids), num_threads, "Each thread must use its own distinct Connection instance")

        rows = self.engine.fetch_all("SELECT id FROM concur_test WHERE id LIKE 'writer_%';")
        self.assertEqual(len(rows), num_threads, f"Expected {num_threads} rows committed, found {len(rows)}")

    # -------------------------------------------------------------------------
    # B. Concurrent Rollback
    # -------------------------------------------------------------------------
    def test_B_concurrent_rollback(self) -> None:
        """
        Verify that a rollback in Thread 1 does NOT roll back or leak into Thread 2's transaction.
        """
        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def worker_failing() -> None:
            try:
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        ("row_failing", "t1", "fail_val", time.time()),
                    )
                    barrier.wait(timeout=5.0)
                    raise RuntimeError("Forced abort in Thread 1")
            except RuntimeError:
                pass
            except Exception as exc:
                errors.append(exc)

        def worker_committing() -> None:
            try:
                barrier.wait(timeout=5.0)
                # Wait slightly for Thread 1 to be inside its transaction or rolling back
                time.sleep(0.05)
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        ("row_committing", "t2", "commit_val", time.time()),
                    )
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=worker_failing)
        t2 = threading.Thread(target=worker_committing)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")

        # Assert database state: row_failing was rolled back, row_committing was committed
        row_fail = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 'row_failing';")
        self.assertIsNone(row_fail, "Rolled-back transaction in Thread 1 must not be present in database")

        row_ok = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 'row_committing';")
        self.assertIsNotNone(row_ok, "Committed transaction in Thread 2 must be present in database")
        self.assertEqual(row_ok["val"], "commit_val")

    # -------------------------------------------------------------------------
    # C. Concurrent Commit
    # -------------------------------------------------------------------------
    def test_C_concurrent_commit(self) -> None:
        """
        Verify two threads concurrently performing independent commits.
        Both must commit their respective changes without interference.
        """
        num_threads = 4
        barrier = threading.Barrier(num_threads)
        errors: list[Exception] = []

        def worker(idx: int) -> None:
            try:
                barrier.wait(timeout=5.0)
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        (f"commit_test_{idx}", f"t_{idx}", f"data_{idx}", time.time()),
                    )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors during concurrent commit: {errors}")
        for i in range(num_threads):
            row = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = ?;", (f"commit_test_{i}",))
            self.assertIsNotNone(row)
            self.assertEqual(row["val"], f"data_{i}")

    # -------------------------------------------------------------------------
    # D. Nested Savepoint
    # -------------------------------------------------------------------------
    def test_D_nested_savepoint(self) -> None:
        """
        Verify nested transactions using SAVEPOINT in concurrent threads.
        Both outer and inner blocks commit successfully in each thread.
        """
        num_threads = 3
        errors: list[Exception] = []

        def worker(idx: int) -> None:
            try:
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        (f"sp_outer_{idx}", f"t_{idx}", "outer_data", time.time()),
                    )
                    # Nested savepoint transaction
                    with self.engine.transaction(conn=conn, savepoint=True):
                        conn.execute(
                            "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                            (f"sp_inner_{idx}", f"t_{idx}", "inner_data", time.time()),
                        )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors: {errors}")
        for i in range(num_threads):
            row_outer = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = ?;", (f"sp_outer_{i}",))
            row_inner = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = ?;", (f"sp_inner_{i}",))
            self.assertIsNotNone(row_outer)
            self.assertIsNotNone(row_inner)

    # -------------------------------------------------------------------------
    # E. Rollback of Nested Savepoint
    # -------------------------------------------------------------------------
    def test_E_rollback_of_nested_savepoint(self) -> None:
        """
        Verify that rolling back an inner savepoint in Thread 1:
        1. Rolls back only the inner block's changes in Thread 1.
        2. Allows Thread 1's outer transaction to commit cleanly.
        3. Has zero impact on Thread 2's concurrent transaction.
        """
        barrier = threading.Barrier(2)
        errors: list[Exception] = []

        def worker_savepoint_rollback() -> None:
            try:
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        ("t1_outer", "t1", "outer_success", time.time()),
                    )
                    # Inner savepoint that fails
                    try:
                        with self.engine.transaction(conn=conn, savepoint=True):
                            conn.execute(
                                "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                                ("t1_inner_fail", "t1", "should_rollback", time.time()),
                            )
                            barrier.wait(timeout=5.0)
                            raise ValueError("Inner savepoint failure")
                    except ValueError:
                        pass  # Recovered from inner savepoint failure

                    # Outer transaction continues and commits
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        ("t1_outer_after", "t1", "outer_after_success", time.time()),
                    )
            except Exception as exc:
                errors.append(exc)

        def worker_independent() -> None:
            try:
                barrier.wait(timeout=5.0)
                with self.engine.transaction() as conn:
                    conn.execute(
                        "INSERT INTO concur_test VALUES (?, ?, ?, ?);",
                        ("t2_normal", "t2", "normal_success", time.time()),
                    )
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=worker_savepoint_rollback)
        t2 = threading.Thread(target=worker_independent)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Errors: {errors}")

        # Assert Thread 1 outer rows committed
        row_o1 = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 't1_outer';")
        self.assertIsNotNone(row_o1)
        row_o2 = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 't1_outer_after';")
        self.assertIsNotNone(row_o2)

        # Assert Thread 1 inner savepoint row was rolled back
        row_inner = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 't1_inner_fail';")
        self.assertIsNone(row_inner, "Inner savepoint failure must roll back its own row")

        # Assert Thread 2 normal commit succeeded
        row_t2 = self.engine.fetch_one("SELECT * FROM concur_test WHERE id = 't2_normal';")
        self.assertIsNotNone(row_t2)

    # -------------------------------------------------------------------------
    # F. Concurrent Provenance and Version Persistence
    # -------------------------------------------------------------------------
    def test_F_concurrent_provenance_version_persistence(self) -> None:
        """
        Verify concurrent persistence of answer provenance and version ledger records
        using a shared DatabaseEngine. Assert all records are written with no collisions.
        """
        prov_tracker = ProvenanceTracker(self.engine)
        version_mgr = VersionManager(self.engine)
        constructor = AnswerConstructor()
        num_items = 4
        errors: list[Exception] = []

        artifacts = [
            constructor.construct_answer(
                pack=make_test_pack(query_text=f"Roma 3:1-{i+1}"),
                render_markdown=True,
            )
            for i in range(num_items)
        ]

        def persist_worker(idx: int) -> None:
            try:
                artifact = artifacts[idx]
                with self.engine.transaction() as conn:
                    prov = record_answer_provenance(
                        tracker=prov_tracker,
                        artifact=artifact,
                        pack_hash=artifact.input_knowledge_pack_hash,
                        conn=conn,
                    )
                    ver = record_answer_version(
                        version_manager=version_mgr,
                        artifact=artifact,
                        provenance_id=prov.provenance_id,
                        conn=conn,
                    )
                    self.assertIsNotNone(prov.provenance_id)
                    self.assertIsNotNone(ver.version_id)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=persist_worker, args=(i,)) for i in range(num_items)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Persistence errors: {errors}")

        for i in range(num_items):
            aid = artifacts[i].answer_id
            v_row = self.engine.fetch_one(
                "SELECT * FROM object_versions WHERE object_id = ? AND object_type = 'ANSWER_ARTIFACT';",
                (aid,),
            )
            self.assertIsNotNone(v_row, f"Version record for {aid} must exist")
            self.assertEqual(v_row["status"], "ACTIVE")

            p_row = self.engine.fetch_one(
                "SELECT * FROM provenance_records WHERE target_id = ?;",
                (aid,),
            )
            self.assertIsNotNone(p_row, f"Provenance record for {aid} must exist")

    # -------------------------------------------------------------------------
    # G. Concurrent AnswerApplicationService Execution
    # -------------------------------------------------------------------------
    def test_G_concurrent_answer_application_service_execution(self) -> None:
        """
        Verify concurrent invocation of AnswerApplicationService.execute() with record_ledger=True.
        Proves:
        - No transaction leakage between concurrent requests.
        - Shared DatabaseEngine handles ledger persistence across worker threads cleanly.
        - All AnswerResponse instances are valid and distinct.
        """
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve_knowledge.return_value = make_test_pack()

        service = AnswerApplicationService(
            db=self.engine,
            planner=QueryPlanner(self.engine),
            retrieval_engine=mock_retrieval,
            constructor=AnswerConstructor(),
            provenance_tracker=ProvenanceTracker(self.engine),
            version_manager=VersionManager(self.engine),
        )

        num_requests = 4
        responses: dict[int, AnswerResponse] = {}
        errors: list[Exception] = []
        lock = threading.Lock()

        def request_worker(idx: int) -> None:
            try:
                req = AnswerRequest(
                    query_text="Roma 3:1-5",
                    requested_scope=SynthesisScope.PERICOPE,
                    record_ledger=True,
                    check_freshness=True,
                )
                resp = service.execute(req)
                with lock:
                    responses[idx] = resp
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=request_worker, args=(i,)) for i in range(num_requests)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Service execution errors: {errors}")
        self.assertEqual(len(responses), num_requests)

        seen_provenance_ids: set[str] = set()
        seen_version_ids: set[str] = set()

        for idx, resp in responses.items():
            self.assertIsNotNone(resp.provenance_record_id)
            self.assertIsNotNone(resp.version_id)
            seen_provenance_ids.add(resp.provenance_record_id)
            seen_version_ids.add(resp.version_id)

            # Assert database state for this response
            p_row = self.engine.fetch_one(
                "SELECT * FROM provenance_records WHERE provenance_id = ?;",
                (resp.provenance_record_id,),
            )
            self.assertIsNotNone(p_row)
            self.assertEqual(p_row["target_id"], resp.artifact.answer_id)

            v_row = self.engine.fetch_one(
                "SELECT * FROM object_versions WHERE version_id = ?;",
                (resp.version_id,),
            )
            self.assertIsNotNone(v_row)
            self.assertIn(v_row["status"], ("ACTIVE", "SUPERSEDED"))
            self.assertEqual(v_row["object_id"], resp.artifact.answer_id)

        # Invariant: Each execution must create a distinct provenance record
        self.assertEqual(
            len(seen_provenance_ids),
            num_requests,
            "Each execution must have a distinct provenance_record_id",
        )
        self.assertEqual(
            len(seen_version_ids),
            num_requests,
            "Each execution must have a distinct version_id",
        )


if __name__ == "__main__":
    unittest.main()
