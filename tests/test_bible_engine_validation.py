"""
Task 4.0 Focused Test Suite: Automated 10-Layer Epistemic Validation Engine.
Verifies V1–V10 orthogonal validators, deterministic input hashing, identity calculation,
concurrency safety, atomic immutable persistence, certificate generation, and epistemic firewalls.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import sqlite3
import tempfile
import unicodedata
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bible_engine import (
    DatabaseConfig,
    DatabaseEngine,
    EvidenceDependencies,
    LayerCode,
    MigrationRunner,
    ProvenanceTracker,
    RetrievalLineage,
    TargetType,
    ValidationCertificate,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
    ViolationSeverity,
    compute_sha256,
)
from bible_engine.retrieval import (
    CandidateSource,
    CounterEvidenceStatus,
    CoverageRecord,
    CoverageStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalConfig,
    RetrievalPackItem,
    RetrievalTargetType,
    SearchBranch,
)
from bible_engine.versioning import ChangeReason, VersionManager


EXPECTED_023_CHECKSUM = "6e8fdd9af19d0c47bdb1f3fd680e8c52aa8c71090b3c5561c95bb78d1a3075bd"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"
LEGACY_BIBLE_ENGINE_DB_SHA256 = "0ac17c6757e247fd135263b7d89bc0eec7df2b93dae6c379b8d44a874f11adfc"


class TestValidationEngineSuite(unittest.TestCase):
    """Complete 40+ Targeted Tests for Task 4.0 Epistemic Validation Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_validation.db"

        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.retrieval_engine = HybridSymmetricalRetrievalEngine(
            self.engine,
            self.provenance_tracker,
            self.version_manager,
        )
        self.validation_engine = ValidationEngine(
            self.engine,
            self.provenance_tracker,
            self.version_manager,
            self.retrieval_engine,
        )

        self._seed_baseline_retrieval_context()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline_retrieval_context(self) -> None:
        """Seed valid Task 3.9 retrieval objects and evidence dependencies."""
        now = datetime.now(timezone.utc).isoformat()

        # Create valid seed provenance and version records
        prov = self.provenance_tracker.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="SRC_GEN_1_1",
            content="בְּרֵאשִׁית בָּרָא אֱלֹהִים",
        )
        self.prov_id = prov.provenance_id

        ver = self.version_manager.create_version(
            object_type="SOURCE_TEXT",
            object_id="SRC_GEN_1_1",
            content="בְּרֵאשִׁית בָּרָא אֱלֹהִים",
            change_reason=ChangeReason.INITIAL_CREATION,
            provenance_id=self.prov_id,
        )
        self.ver_id = ver.version_id

        with self.engine.transaction() as conn:
            # Baseline canon and source
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('TEST_CANON', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_OT', 'TEST_CANON', 'Old Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('GEN', 'TEST_OT', 1, 'Kejadian', 'Genesis', 'HEBREW', 50);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes VALUES (
                    'PER_GEN_1_1', 'GEN', 'Kejadian 1:1-3', 1, 1, 1, 3,
                    'NARRATIVE', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0.0', ?
                )
                """,
                (now,),
            )
            conn.execute("INSERT OR IGNORE INTO passages VALUES ('GEN_1_1', 'PER_GEN_1_1', 'GEN', 1, 1, 1);")

            # Source text
            conn.execute(
                """
                INSERT OR IGNORE INTO source_texts (
                    source_text_id, source_id, passage_id, source_type, language,
                    representation_type, raw_source_string, normalized_source_string,
                    sha256_hash, encoding, created_at, is_immutable
                ) VALUES (
                    'SRC_GEN_1_1', 'SRC-CANONICAL-ROOT', 'GEN_1_1', 'SOURCE_LANGUAGE_TEXT', 'HEBREW',
                    'RAW', 'בְּרֵאשִׁית בָּרָא אֱלֹהִים', 'בְּרֵאשִׁית בָּרָא אֱלֹהִים',
                    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'UTF-8', ?, 1
                )
                """,
                (now,),
            )

            # Evidence ledger items
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier,
                    source_reference, extracted_text_or_data, status, confidence,
                    confidence_score, provenance_id, version_id, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV_PRIMARY_01', 'PER_GEN_1_1', 'GEN_1_1', 'E0_DIRECT_TEXT', 'T1_LINGUISTIC_FACT',
                    'GEN 1:1', 'Primary text excerpt', 'EXPLICIT', 'VERY_HIGH',
                    0.95, ?, ?, ?, 'hash-ev1', 1
                )
                """,
                (self.prov_id, self.ver_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier,
                    source_reference, extracted_text_or_data, status, confidence,
                    confidence_score, is_counter_evidence, provenance_id, version_id, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV_COUNTER_01', 'PER_GEN_1_1', 'GEN_1_1', 'E6_IMMEDIATE_CONTEXT', 'T1_LINGUISTIC_FACT',
                    'GEN 1:1', 'Counter context excerpt', 'EXPLICIT', 'HIGH',
                    0.85, 1, ?, ?, ?, 'hash-ev2', 1
                )
                """,
                (self.prov_id, self.ver_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier,
                    source_reference, extracted_text_or_data, status, confidence,
                    confidence_score, provenance_id, version_id, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV_T4_DOGMATIC', 'PER_GEN_1_1', 'GEN_1_1', 'E12_LATER_INTERPRETATION', 'T4_THEOLOGICAL_CLAIM',
                    'Dogmatic tradition', 'Dogmatic confession', 'EXPLICIT', 'MEDIUM',
                    0.50, ?, ?, ?, 'hash-ev3', 1
                )
                """,
                (self.prov_id, self.ver_id, now),
            )

            # Retrieval Query
            self.query_id = "QRY_TEST_01"
            self.raw_query = "in the beginning"
            self.normalized_query = "in the beginning"
            self.query_hash = compute_sha256(self.normalized_query)
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_queries (
                    query_id, raw_query, normalized_query, query_hash, target_type,
                    target_id, provenance_id, created_at, is_immutable
                ) VALUES (?, ?, ?, ?, 'PASSAGE', 'GEN_1_1', ?, ?, 1)
                """,
                (self.query_id, self.raw_query, self.normalized_query, self.query_hash, self.prov_id, now),
            )

            # Retrieval Run
            self.run_id = "RUN_TEST_01"
            self.config_hash = compute_sha256('{"limit":20}')
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_runs (
                    run_id, query_id, run_seed, config_hash, config_json,
                    provenance_id, version_id, created_at, is_immutable
                ) VALUES (?, ?, 42, ?, '{"limit":20}', ?, ?, ?, 1)
                """,
                (self.run_id, self.query_id, self.config_hash, self.prov_id, self.ver_id, now),
            )

            # Coverage records: PRIMARY_SEARCH & COUNTER_SEARCH
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_coverage_records (
                    coverage_id, run_id, search_branch, search_strategy, query_formulation,
                    target_scope, candidate_count, matched_count, coverage_status,
                    methodology_notes, provenance_id, created_at, is_immutable
                ) VALUES (
                    'COV_PRI_01', ?, 'PRIMARY_SEARCH', 'LEXICAL', 'in beginning',
                    'GEN', 5, 2, 'PRIMARY_EVIDENCE_FOUND', 'Standard search',
                    ?, ?, 1
                )
                """,
                (self.run_id, self.prov_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_coverage_records (
                    coverage_id, run_id, search_branch, search_strategy, query_formulation,
                    target_scope, candidate_count, matched_count, coverage_status,
                    methodology_notes, provenance_id, created_at, is_immutable
                ) VALUES (
                    'COV_CNT_01', ?, 'COUNTER_SEARCH', 'OPPOSING', 'not in beginning',
                    'GEN', 3, 1, 'COUNTER_EVIDENCE_FOUND', 'Counter search',
                    ?, ?, 1
                )
                """,
                (self.run_id, self.prov_id, now),
            )

            # Context pack canonical payload recalculation
            self.pack_id = "PACK_TEST_01"
            canonical_payload = {
                "configuration_hash": self.config_hash,
                "counter_evidence_ids": ["EV_COUNTER_01"],
                "coverage_records": [
                    {
                        "branch": "COUNTER_SEARCH",
                        "candidate_count": 3,
                        "matched_count": 1,
                        "status": "COUNTER_EVIDENCE_FOUND",
                        "strategy": "OPPOSING",
                    },
                    {
                        "branch": "PRIMARY_SEARCH",
                        "candidate_count": 5,
                        "matched_count": 2,
                        "status": "PRIMARY_EVIDENCE_FOUND",
                        "strategy": "LEXICAL",
                    },
                ],
                "graph_signal_ids": [],
                "linked_claim_ids": [],
                "normalized_query": self.normalized_query,
                "primary_evidence_ids": ["EV_PRIMARY_01"],
                "provenance_id": self.prov_id,
                "query_hash": self.query_hash,
                "version_id": self.ver_id,
            }
            serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
            self.pack_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_context_packs (
                    pack_id, run_id, query_id, pack_hash, aggregate_confidence,
                    primary_count, counter_count, total_item_count, counter_evidence_status,
                    provenance_id, version_id, created_at, is_immutable
                ) VALUES (
                    ?, ?, ?, ?, 0.85, 1, 1, 2, 'COUNTER_EVIDENCE_FOUND',
                    ?, ?, ?, 1
                )
                """,
                (self.pack_id, self.run_id, self.query_id, self.pack_hash, self.prov_id, self.ver_id, now),
            )

            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_pack_items (
                    item_id, pack_id, search_branch, evidence_role, evidence_id,
                    candidate_source, item_confidence, item_rank, relevance_score,
                    created_at, is_immutable
                ) VALUES (
                    'ITEM_01', ?, 'PRIMARY_SEARCH', 'SUPPORTING', 'EV_PRIMARY_01',
                    'DIRECT_LOOKUP', 0.95, 1, 1.0, ?, 1
                )
                """,
                (self.pack_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_pack_items (
                    item_id, pack_id, search_branch, evidence_role, evidence_id,
                    candidate_source, item_confidence, item_rank, relevance_score,
                    created_at, is_immutable
                ) VALUES (
                    'ITEM_02', ?, 'COUNTER_SEARCH', 'COUNTER_EVIDENCE', 'EV_COUNTER_01',
                    'DIRECT_LOOKUP', 0.85, 2, 0.9, ?, 1
                )
                """,
                (self.pack_id, now),
            )

        self.retrieval_lineage = RetrievalLineage(
            query_id=self.query_id,
            query_hash=self.query_hash,
            retrieval_run_id=self.run_id,
            config_hash=self.config_hash,
            pack_id=self.pack_id,
            pack_hash=self.pack_hash,
        )

    def _create_valid_input(
        self,
        target_id: str = "TGT_PROP_01",
        target_type: str = "PROPOSITION",
        version_id: Optional[str] = None,
        candidate_payload: Optional[Dict[str, Any]] = None,
        evidence_ids: Optional[List[str]] = None,
    ) -> ValidationInput:
        if version_id is None:
            version_id = self.ver_id
        if evidence_ids is None:
            evidence_ids = ["EV_PRIMARY_01"]
        payload = {
            "source_string": "בְּרֵאשִׁית בָּרָא אֱלֹהִים",
            "source_text_id": "SRC_GEN_1_1",
            "candidate_confidence": 0.85,
        }
        if candidate_payload:
            payload.update(candidate_payload)

        return ValidationInput(
            target=ValidationTarget(
                target_type=target_type,
                target_id=target_id,
                target_version_id=version_id,
            ),
            retrieval_lineage=self.retrieval_lineage,
            evidence_dependencies=EvidenceDependencies(evidence_ids=evidence_ids),
            environment=ValidationEnvironment(engine_version="2.0.0", schema_version="023"),
            candidate_payload=payload,
        )

    # -------------------------------------------------------------------------
    # 1. Migration Checks & Checksums
    # -------------------------------------------------------------------------
    def test_01_migration_023_creation_and_checksum(self) -> None:
        p = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "023_validation_engine.sql"
        self.assertTrue(p.exists())
        computed = compute_sha256(p.read_bytes())
        self.assertEqual(computed, EXPECTED_023_CHECKSUM)

    def test_02_migration_status_clean(self) -> None:
        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertEqual(status.current_version, "24")

    def test_03_legacy_database_hashes_unchanged(self) -> None:
        legacy1 = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy1.exists():
            h1 = compute_sha256(legacy1.read_bytes())
            self.assertEqual(h1, LEGACY_DB_SHA256)

        legacy2 = Path("/home/ubuntu/.polya/bible_engine.db")
        if legacy2.exists():
            h2 = compute_sha256(legacy2.read_bytes())
            self.assertEqual(h2, LEGACY_BIBLE_ENGINE_DB_SHA256)

    # -------------------------------------------------------------------------
    # 2. Canonical Hashing & Deterministic Identity
    # -------------------------------------------------------------------------
    def test_04_canonical_hashing_structure_and_order_independence(self) -> None:
        inp1 = self._create_valid_input(evidence_ids=["EV_PRIMARY_01", "EV_COUNTER_01"])
        inp2 = self._create_valid_input(evidence_ids=["EV_COUNTER_01", "EV_PRIMARY_01"])
        h1 = inp1.compute_validation_input_hash()
        h2 = inp2.compute_validation_input_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_05_validation_identity_determinism_no_timestamps(self) -> None:
        inp = self._create_valid_input()
        id1 = inp.compute_validation_identity()
        id2 = inp.compute_validation_identity()
        self.assertEqual(id1, id2)
        expected = hashlib.sha256(
            f"{inp.compute_validation_input_hash()}:2.0.0:023".encode("utf-8")
        ).hexdigest()
        self.assertEqual(id1, expected)

    # -------------------------------------------------------------------------
    # 3. Layer V1: Source Text & Invariant Integrity
    # -------------------------------------------------------------------------
    def test_06_v1_empty_source_string_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V1_01",
            candidate_payload={"source_string": "   "},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v1_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V1)
        self.assertEqual(v1_res.outcome, ValidationOutcome.BLOCKED)
        self.assertTrue(any(v.rule_code == "V1_EMPTY_SOURCE_STRING" for v in v1_res.violations))

    def test_07_v1_unauthorized_alteration_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V1_02",
            candidate_payload={"unauthorized_alteration": True},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v1_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V1)
        self.assertTrue(any(v.rule_code == "V1_UNAUTHORIZED_TEXT_ALTERATION" for v in v1_res.violations))

    def test_08_v1_unicode_normalization_warning(self) -> None:
        decomposed = unicodedata.normalize("NFD", "Ἐν ἀρχῇ")
        inp = self._create_valid_input(
            target_id="TGT_V1_03",
            candidate_payload={"source_string": decomposed},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        v1_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V1)
        self.assertTrue(any(v.rule_code == "V1_UNICODE_NORMALIZATION_WARNING" for v in v1_res.violations))

    # -------------------------------------------------------------------------
    # 4. Layer V2: Morphological & Grammatical Bounds
    # -------------------------------------------------------------------------
    def test_09_v2_unsupported_grammatical_expansion_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V2_01",
            candidate_payload={
                "morphology_claims": [
                    {"token_id": "T1", "is_unsupported_expansion": True, "message": "Singular claimed as plural"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v2_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V2)
        self.assertEqual(v2_res.outcome, ValidationOutcome.BLOCKED)
        self.assertTrue(any(v.rule_code == "V2_UNSUPPORTED_GRAMMATICAL_EXPANSION" for v in v2_res.violations))

    def test_10_v2_grammatical_ambiguity_warning(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V2_02",
            candidate_payload={
                "morphology_claims": [
                    {"token_id": "T1", "is_ambiguous": True, "message": "Rare inflectional form"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        v2_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V2)
        self.assertEqual(v2_res.outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        self.assertTrue(any(v.rule_code == "V2_GRAMMATICAL_AMBIGUITY_WARNING" for v in v2_res.violations))

    # -------------------------------------------------------------------------
    # 5. Layer V3: Syntactic Dependency Boundaries
    # -------------------------------------------------------------------------
    def test_11_v3_unsupported_syntactic_relationship_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V3_01",
            candidate_payload={
                "syntactic_claims": [
                    {"violates_dependency_boundary": True, "message": "Illicit cross-clausal attachment"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v3_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V3)
        self.assertEqual(v3_res.outcome, ValidationOutcome.BLOCKED)
        self.assertTrue(any(v.rule_code == "V3_UNSUPPORTED_SYNTACTIC_RELATIONSHIP" for v in v3_res.violations))

    def test_12_v3_unattested_syntax_warning(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V3_02",
            candidate_payload={
                "syntactic_claims": [
                    {"is_unattested_syntax": True, "message": "Peripheral syntactic pattern"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        v3_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V3)
        self.assertTrue(any(v.rule_code == "V3_UNATTESTED_SYNTACTIC_RELATION_WARNING" for v in v3_res.violations))

    # -------------------------------------------------------------------------
    # 6. Layer V4: Lexical & Semantic Field Bounds
    # -------------------------------------------------------------------------
    def test_13_v4_illegitimate_totality_transfer_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V4_01",
            candidate_payload={
                "semantic_claims": [
                    {"is_illegitimate_totality_transfer": True, "message": "All lexical glosses combined"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v4_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V4)
        self.assertTrue(any(v.rule_code == "V4_ILLEGITIMATE_TOTALITY_TRANSFER" for v in v4_res.violations))

    def test_14_v4_root_fallacy_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V4_02",
            candidate_payload={
                "semantic_claims": [
                    {"is_root_fallacy": True, "message": "Etymological determinism asserted"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v4_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V4)
        self.assertTrue(any(v.rule_code == "V4_ROOT_FALLACY" for v in v4_res.violations))

    def test_15_v4_semantic_field_tension_warning(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V4_03",
            candidate_payload={
                "semantic_claims": [
                    {"is_semantic_tension": True, "message": "Peripheral semantic field"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        v4_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V4)
        self.assertTrue(any(v.rule_code == "V4_SEMANTIC_FIELD_TENSION_WARNING" for v in v4_res.violations))

    # -------------------------------------------------------------------------
    # 7. Layer V5: Referential & Identity Firewall
    # -------------------------------------------------------------------------
    def test_16_v5_association_identity_conflation_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V5_01",
            candidate_payload={
                "referential_claims": [
                    {
                        "relation_type": "ASSOCIATED_WITH",
                        "equates_entities": True,
                        "has_explicit_identity_evidence": False,
                    }
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v5_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V5)
        self.assertTrue(any(v.rule_code == "V5_ASSOCIATION_IDENTITY_CONFLATION" for v in v5_res.violations))

    def test_17_v5_unsupported_identity_claim_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V5_02",
            candidate_payload={
                "referential_claims": [
                    {
                        "relation_type": "EQUATED_WITH",
                        "equates_entities": True,
                        "has_explicit_identity_evidence": False,
                    }
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v5_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V5)
        self.assertTrue(any(v.rule_code == "V5_UNSUPPORTED_IDENTITY_CLAIM" for v in v5_res.violations))

    def test_18_v5_supported_identity_claim_valid(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V5_03",
            candidate_payload={
                "referential_claims": [
                    {
                        "relation_type": "EQUATED_WITH",
                        "equates_entities": True,
                        "has_explicit_identity_evidence": True,
                    }
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        v5_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V5)
        self.assertEqual(v5_res.outcome, ValidationOutcome.VALID)

    # -------------------------------------------------------------------------
    # 8. Layer V6: Discourse & Immediate Context Integrity
    # -------------------------------------------------------------------------
    def test_19_v6_proof_text_isolation_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V6_01",
            candidate_payload={
                "discourse_claims": [
                    {"is_proof_text_isolation": True, "message": "Isolated clause ignores pericope argument"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v6_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V6)
        self.assertTrue(any(v.rule_code == "V6_PROOF_TEXT_ISOLATION" for v in v6_res.violations))

    def test_20_v6_speaker_attribution_error_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V6_02",
            candidate_payload={
                "discourse_claims": [
                    {"speaker_attribution_error": True, "message": "Adversary dialogue treated as authorial thesis"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v6_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V6)
        self.assertTrue(any(v.rule_code == "V6_SPEAKER_ATTRIBUTION_ERROR" for v in v6_res.violations))

    # -------------------------------------------------------------------------
    # 9. Layer V7: Textual Witness & Apparatus Calibration
    # -------------------------------------------------------------------------
    def test_21_v7_translation_masquerading_as_primary_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V7_01",
            candidate_payload={
                "textual_claims": [
                    {"is_translation_masquerading_as_primary": True, "message": "Vulgate cited as Hebrew original"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v7_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V7)
        self.assertTrue(any(v.rule_code == "V7_TRANSLATION_MASQUERADING_AS_PRIMARY" for v in v7_res.violations))

    def test_22_v7_unattested_variant_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V7_02",
            candidate_payload={
                "textual_claims": [
                    {"is_unattested_variant": True, "message": "Hypothetical reading without witness"}
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v7_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V7)
        self.assertTrue(any(v.rule_code == "V7_UNATTESTED_TEXTUAL_VARIANT" for v in v7_res.violations))

    # -------------------------------------------------------------------------
    # 10. Layer V8: Reception History & Anti-Anachronism Firewall
    # -------------------------------------------------------------------------
    def test_23_v8_anachronistic_concept_retrojection_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V8_01",
            candidate_payload={
                "reception_claims": [
                    {
                        "is_anachronistic_retrojection": True,
                        "claim_scope": "AUTHORIAL_INTENT",
                        "message": "Nicene homoousios retrojected to ancient author",
                    }
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v8_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V8)
        self.assertTrue(any(v.rule_code == "V8_ANACHRONISTIC_RETROJECTION" for v in v8_res.violations))

    def test_24_v8_analytical_terminology_permitted(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V8_02",
            candidate_payload={
                "reception_claims": [
                    {
                        "is_analytical_terminology": True,
                        "term": "chiastic structure",
                        "message": "Modern linguistic classification",
                    }
                ]
            },
        )
        res = self.validation_engine.validate(inp)
        v8_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V8)
        self.assertEqual(v8_res.outcome, ValidationOutcome.VALID)

    # -------------------------------------------------------------------------
    # 11. Layer V9: Symmetrical Counter-Evidence Search Audit (Task 3.9)
    # -------------------------------------------------------------------------
    def test_25_v9_missing_pack_blocking(self) -> None:
        bogus_lineage = RetrievalLineage(
            query_id=self.query_id,
            query_hash=self.query_hash,
            retrieval_run_id=self.run_id,
            config_hash=self.config_hash,
            pack_id="PACK_NONEXISTENT",
            pack_hash="abc",
        )
        inp = ValidationInput(
            target=ValidationTarget("PROPOSITION", "TGT_V9_01", self.ver_id),
            retrieval_lineage=bogus_lineage,
            evidence_dependencies=EvidenceDependencies(["EV_PRIMARY_01"]),
            environment=ValidationEnvironment("2.0.0", "023"),
            candidate_payload={"source_string": "text"},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v9_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V9)
        self.assertTrue(any(v.rule_code == "V9_PACK_NOT_FOUND" for v in v9_res.violations))

    def test_26_v9_pack_hash_mismatch_blocking(self) -> None:
        bogus_lineage = RetrievalLineage(
            query_id=self.query_id,
            query_hash=self.query_hash,
            retrieval_run_id=self.run_id,
            config_hash=self.config_hash,
            pack_id=self.pack_id,
            pack_hash="bogus_pack_hash_00000000000000000000000000000000000000000000000000",
        )
        inp = ValidationInput(
            target=ValidationTarget("PROPOSITION", "TGT_V9_02", self.ver_id),
            retrieval_lineage=bogus_lineage,
            evidence_dependencies=EvidenceDependencies(["EV_PRIMARY_01"]),
            environment=ValidationEnvironment("2.0.0", "023"),
            candidate_payload={"source_string": "text"},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v9_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V9)
        self.assertTrue(any(v.rule_code == "V9_PACK_HASH_MISMATCH" for v in v9_res.violations))

    def test_27_v9_missing_counter_search_blocking(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        no_cnt_run_id = "RUN_NO_CNT_01"
        no_cnt_pack_id = "PACK_NO_CNT_01"
        cfg_hash = compute_sha256('{"limit":10}')
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_runs (
                    run_id, query_id, run_seed, config_hash, config_json,
                    provenance_id, version_id, created_at, is_immutable
                ) VALUES (?, ?, 42, ?, '{"limit":10}', ?, ?, ?, 1)
                """,
                (no_cnt_run_id, self.query_id, cfg_hash, self.prov_id, self.ver_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_coverage_records (
                    coverage_id, run_id, search_branch, search_strategy, query_formulation,
                    target_scope, candidate_count, matched_count, coverage_status,
                    methodology_notes, provenance_id, created_at, is_immutable
                ) VALUES (
                    'COV_NO_CNT_01', ?, 'PRIMARY_SEARCH', 'LEXICAL', 'in beginning',
                    'GEN', 5, 2, 'PRIMARY_EVIDENCE_FOUND', 'Standard search',
                    ?, ?, 1
                )
                """,
                (no_cnt_run_id, self.prov_id, now),
            )
            canonical_payload = {
                "configuration_hash": cfg_hash,
                "counter_evidence_ids": [],
                "coverage_records": [
                    {
                        "branch": "PRIMARY_SEARCH",
                        "candidate_count": 5,
                        "matched_count": 2,
                        "status": "PRIMARY_EVIDENCE_FOUND",
                        "strategy": "LEXICAL",
                    },
                ],
                "graph_signal_ids": [],
                "linked_claim_ids": [],
                "normalized_query": self.normalized_query,
                "primary_evidence_ids": ["EV_PRIMARY_01"],
                "provenance_id": self.prov_id,
                "query_hash": self.query_hash,
                "version_id": self.ver_id,
            }
            serialized = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
            pack_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_context_packs (
                    pack_id, run_id, query_id, pack_hash, aggregate_confidence,
                    primary_count, counter_count, total_item_count, counter_evidence_status,
                    provenance_id, version_id, created_at, is_immutable
                ) VALUES (
                    ?, ?, ?, ?, 0.85, 1, 0, 1, 'COUNTER_EVIDENCE_NOT_FOUND',
                    ?, ?, ?, 1
                )
                """,
                (no_cnt_pack_id, no_cnt_run_id, self.query_id, pack_hash, self.prov_id, self.ver_id, now),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO retrieval_pack_items (
                    item_id, pack_id, search_branch, evidence_role, evidence_id,
                    candidate_source, item_confidence, item_rank, relevance_score,
                    created_at, is_immutable
                ) VALUES (
                    'ITEM_NO_CNT_01', ?, 'PRIMARY_SEARCH', 'SUPPORTING', 'EV_PRIMARY_01',
                    'DIRECT_LOOKUP', 0.95, 1, 1.0, ?, 1
                )
                """,
                (no_cnt_pack_id, now),
            )

        lineage = RetrievalLineage(
            query_id=self.query_id,
            query_hash=self.query_hash,
            retrieval_run_id=no_cnt_run_id,
            config_hash=cfg_hash,
            pack_id=no_cnt_pack_id,
            pack_hash=pack_hash,
        )
        inp = ValidationInput(
            target=ValidationTarget("PROPOSITION", "TGT_V9_03", self.ver_id),
            retrieval_lineage=lineage,
            evidence_dependencies=EvidenceDependencies(["EV_PRIMARY_01"]),
            environment=ValidationEnvironment("2.0.0", "023"),
            candidate_payload={"source_string": "text"},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v9_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V9)
        self.assertTrue(any(v.rule_code == "V9_MISSING_COUNTER_SEARCH" for v in v9_res.violations))

    def test_28_v9_detached_evidence_rejection(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V9_04",
            evidence_ids=["EV_PRIMARY_01", "EV_DETACHED_UNREFERENCED"],
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v9_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V9)
        self.assertTrue(any(v.rule_code == "V9_DETACHED_EVIDENCE" for v in v9_res.violations))

    def test_29_v9_synthetic_context_rejection(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V9_05",
            candidate_payload={"has_synthetic_retrieval_context": True},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v9_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V9)
        self.assertTrue(any(v.rule_code == "V9_SYNTHETIC_CONTEXT_DETECTED" for v in v9_res.violations))

    # -------------------------------------------------------------------------
    # 12. Layer V10: Epistemic Tier & Confidence Calibration (Audit Only)
    # -------------------------------------------------------------------------
    def test_30_v10_tier_promotion_prohibited_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V10_01",
            candidate_payload={"promotes_tier": True},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v10_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V10)
        self.assertTrue(any(v.rule_code == "V10_TIER_PROMOTION_PROHIBITED" for v in v10_res.violations))

    def test_31_v10_t4_theology_firewall_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V10_02",
            candidate_payload={"target_tier": "T1", "has_t4_theology_contamination": True},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v10_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V10)
        self.assertTrue(any(v.rule_code == "V10_THEOLOGY_FIREWALL_VIOLATION" for v in v10_res.violations))

    def test_32_v10_confidence_inflation_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V10_03",
            evidence_ids=["EV_PRIMARY_01"],  # confidence = 0.95
            candidate_payload={"candidate_confidence": 0.99},  # exceeds 0.95
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v10_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V10)
        self.assertTrue(any(v.rule_code == "V10_CONFIDENCE_INFLATION" for v in v10_res.violations))

    def test_33_v10_truth_engine_drift_blocking(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_V10_04",
            candidate_payload={"asserts_truth_engine_derivation": True},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        v10_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V10)
        self.assertTrue(any(v.rule_code == "V10_TRUTH_ENGINE_DRIFT" for v in v10_res.violations))

    # -------------------------------------------------------------------------
    # 13. Integration, Independence, and No Early Exit
    # -------------------------------------------------------------------------
    def test_34_no_early_exit_between_layers(self) -> None:
        # V1 fails AND V4 fails. Both must be evaluated.
        inp = self._create_valid_input(
            target_id="TGT_INT_01",
            candidate_payload={
                "source_string": "",  # V1 failure
                "semantic_claims": [{"is_root_fallacy": True}],  # V4 failure
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        self.assertEqual(len(res.layer_results), 10)
        v1_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V1)
        v4_res = next(lr for lr in res.layer_results if lr.layer_code == LayerCode.V4)
        self.assertEqual(v1_res.outcome, ValidationOutcome.BLOCKED)
        self.assertEqual(v4_res.outcome, ValidationOutcome.BLOCKED)

    def test_35_warning_does_not_conceal_blocking_violation(self) -> None:
        # V1 has warning, V5 has blocking violation -> outcome MUST be BLOCKED
        inp = self._create_valid_input(
            target_id="TGT_INT_02",
            candidate_payload={
                "source_string": unicodedata.normalize("NFD", "Ἐν ἀρχῇ"),  # V1 warning
                "referential_claims": [
                    {
                        "relation_type": "ASSOCIATED_WITH",
                        "equates_entities": True,
                        "has_explicit_identity_evidence": False,
                    }
                ],  # V5 blocking
            },
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        self.assertGreaterEqual(res.warnings_total, 1)
        self.assertGreaterEqual(res.checks_failed, 1)

    def test_36_valid_outcome_all_layers_pass(self) -> None:
        inp = self._create_valid_input(target_id="TGT_INT_03")
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID)
        self.assertEqual(res.checks_failed, 0)
        self.assertEqual(res.warnings_total, 0)
        self.assertEqual(len(res.layer_results), 10)

    # -------------------------------------------------------------------------
    # 14. Certificate Generation & Semantics
    # -------------------------------------------------------------------------
    def test_37_certificate_generated_for_valid(self) -> None:
        inp = self._create_valid_input(target_id="TGT_CERT_01")
        res = self.validation_engine.validate(inp)
        self.assertIsNotNone(res.certificate)
        self.assertEqual(res.certificate.validation_status, "VALID")
        # Verify NO confidence score on certificate
        self.assertFalse(hasattr(res.certificate, "certificate_confidence"))
        self.assertFalse(hasattr(res.certificate, "confidence"))
        self.assertFalse(hasattr(res.certificate, "score"))

    def test_38_certificate_generated_for_valid_with_warnings(self) -> None:
        decomposed = unicodedata.normalize("NFD", "Ἐν ἀρχῇ")
        inp = self._create_valid_input(
            target_id="TGT_CERT_02",
            candidate_payload={"source_string": decomposed},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.VALID_WITH_WARNINGS)
        self.assertIsNotNone(res.certificate)
        self.assertEqual(res.certificate.validation_status, "VALID_WITH_WARNINGS")

    def test_39_no_certificate_for_blocked(self) -> None:
        inp = self._create_valid_input(
            target_id="TGT_CERT_03",
            candidate_payload={"source_string": ""},
        )
        res = self.validation_engine.validate(inp)
        self.assertEqual(res.final_outcome, ValidationOutcome.BLOCKED)
        self.assertIsNone(res.certificate)

    # -------------------------------------------------------------------------
    # 15. Immutability, Provenance & Rollback
    # -------------------------------------------------------------------------
    def test_40_validation_runs_immutability_trigger(self) -> None:
        inp = self._create_valid_input(target_id="TGT_IMMUT_01")
        res = self.validation_engine.validate(inp)
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE validation_runs SET checks_total = 999 WHERE run_id = ?",
                    (res.run_id,),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "DELETE FROM validation_runs WHERE run_id = ?",
                    (res.run_id,),
                )

    def test_41_validation_certificates_immutability_trigger(self) -> None:
        inp = self._create_valid_input(target_id="TGT_IMMUT_02")
        res = self.validation_engine.validate(inp)
        self.assertIsNotNone(res.certificate)
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE validation_certificates SET validation_status = 'INVALID' WHERE certificate_id = ?",
                    (res.certificate.certificate_id,),
                )
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "DELETE FROM validation_certificates WHERE certificate_id = ?",
                    (res.certificate.certificate_id,),
                )

    def test_42_provenance_registered_as_validation_result(self) -> None:
        inp = self._create_valid_input(target_id="TGT_PROV_01")
        res = self.validation_engine.validate(inp)
        with self.engine.connect() as conn:
            cur = conn.execute(
                "SELECT target_type FROM provenance_records WHERE provenance_id = ?",
                (res.provenance_id,),
            )
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["target_type"], TargetType.VALIDATION_RESULT.value)

    # -------------------------------------------------------------------------
    # 16. Idempotency & Concurrency
    # -------------------------------------------------------------------------
    def test_43_idempotency_returns_exact_persisted_instance(self) -> None:
        inp = self._create_valid_input(target_id="TGT_IDEMP_01")
        res1 = self.validation_engine.validate(inp)
        res2 = self.validation_engine.validate(inp)
        self.assertEqual(res1.run_id, res2.run_id)
        self.assertEqual(res1.validation_identity, res2.validation_identity)
        if res1.certificate:
            self.assertEqual(res1.certificate.certificate_id, res2.certificate.certificate_id)

    def test_44_concurrent_identical_validation_safety(self) -> None:
        inp = self._create_valid_input(target_id="TGT_CONC_01")

        def run_val() -> str:
            eng = DatabaseEngine(DatabaseConfig(db_path=str(self.db_path)))
            try:
                val_eng = ValidationEngine(eng)
                res = val_eng.validate(inp)
                return res.run_id
            finally:
                eng.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_val) for _ in range(5)]
            run_ids = [f.result() for f in futures]

        # All concurrent workers must converge on the exact same persisted run_id
        self.assertEqual(len(set(run_ids)), 1)

        # Database must contain exactly 1 run and <= 1 certificate
        with self.engine.connect() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM validation_runs WHERE validation_identity = ?",
                (inp.compute_validation_identity(),),
            )
            self.assertEqual(cur.fetchone()[0], 1)

            cert_cur = conn.execute(
                "SELECT COUNT(*) FROM validation_certificates WHERE validation_identity = ?",
                (inp.compute_validation_identity(),),
            )
            self.assertEqual(cert_cur.fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
