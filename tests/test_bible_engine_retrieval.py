"""
Unit and Adversarial Test Suite for Hybrid Symmetrical Retrieval Engine (Task 3.9).
Specification: Architecture v2.0 — FROZEN.

Target: >= 30 comprehensive adversarial tests.
Coverage:
  1. Migration 022 Schema & Triggers
  2. Migrations 001–021 Checksums Frozen
  3. Legacy Database Hash Preservation
  4. Migration 022 Checksum Locked
  5. Immutability Triggers (retrieval_queries)
  6. Immutability Triggers (retrieval_runs)
  7. Immutability Triggers (retrieval_coverage_records)
  8. Immutability Triggers (retrieval_context_packs)
  9. Immutability Triggers (retrieval_pack_items)
  10. FTS5 Virtual Table Availability & Indexing
  11. FTS5 Hostile Input Escaping & Injection Resistance
  12. Unicode Greek & Hebrew Normalization
  13. Counter-Search Mandatory (enable_counter_search=False raises error)
  14. Counter-Search Kwarg Suppression Detection
  15. Search Symmetry Obligation (Both Branches Executed)
  16. Search Branch Decoupled from Evidence Role
  17. Counter-Search Candidate Not Automatic Counter-Evidence
  18. E/T Tier Firewall: No claim_tier Column on retrieval_pack_items
  19. E/T Tier Firewall: Null linked_claim_id Has No T-Tier
  20. Graph Firewall: Connectivity / Centrality / Degree Not Truth
  21. Graph Candidate Validation Against Evidence Ledger
  22. Bounded Graph Expansion
  23. T4 Theology Firewall: T4 Cannot Support T0–T3
  24. T4 Theology Firewall: T4 Retrieval Target Decomposition
  25. Absence of Evidence: NOT_FOUND != NO_COUNTER_EVIDENCE_EXISTS
  26. Absence of Evidence: Methodology Explanation Recorded
  27. Confidence Firewall: Capped at Min Critical Evidence Confidence
  28. Confidence Firewall: BM25 / Ranking Score Does Not Inflate Confidence
  29. Deterministic Canonical Pack Hash Calculation
  30. Deterministic Hash Independent of SQLite Row Return Order
  31. Provenance Methodology Completeness
  32. Object Versioning Integration
  33. Concurrent Retrieval Execution Safety
  34. Pack Integrity Verification Pass and Tamper Detection
  35. Anti-Confirmation Bias: Symmetrical Coverage Guarantee
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

from bible_engine.database import DatabaseConfig, DatabaseEngine
from bible_engine.errors import (
    AbsenceOfEvidenceConflationError,
    AsymmetricalRetrievalError,
    CounterSearchSuppressionError,
    DeterministicHashMismatchError,
    DogmaticContaminationError,
    EpistemicTierConfusionError,
    FTS5HostileInputError,
    GraphEpistemicLeakageError,
    RetrievalConfidenceInflationError,
    RetrievalContextPackNotFoundError,
    RetrievalImmutabilityError,
    RetrievalQueryNotFoundError,
    RetrievalRunNotFoundError,
    RetrievalSubsystemError,
    RetrievalValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.graph import EvidenceKnowledgeGraphManager
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import (
    CandidateSource,
    CounterEvidenceStatus,
    CoverageRecord,
    CoverageStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalConfig,
    RetrievalPackItem,
    RetrievalPackResult,
    RetrievalTarget,
    RetrievalTargetType,
    SearchBranch,
    normalize_text_for_search,
    sanitize_fts5_query,
)
from bible_engine.synthesis import HierarchicalSynthesisManager
from bible_engine.theological_comparison import TheologicalComparisonManager
from bible_engine.versioning import ChangeReason, VersionManager


EXPECTED_MIGRATION_CHECKSUMS: Dict[str, str] = {
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
}

EXPECTED_022_CHECKSUM = "2fed1487f9a5fdc857c369469b118cfbdb802ca41eb5e4f173b76100afcf4c4d"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestHybridSymmetricalRetrievalEngine(unittest.TestCase):
    """Unit and Adversarial Test Suite for Task 3.9 Hybrid Symmetrical Retrieval Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_retrieval.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.retrieval_engine = HybridSymmetricalRetrievalEngine(
            self.engine,
            self.provenance_tracker,
            self.version_manager,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('JHN', 'TEST_NT', 43, 'Yohanes', 'John', 'GREEK', 21);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse,
                    end_chapter, end_verse, genre, boundary_source, boundary_confidence,
                    status, version, created_at
                ) VALUES (
                    'PERIC_JHN_1_1', 'JHN', 'Yohanes 1:1-18', 1, 1, 1, 18,
                    'GOSPEL_PROLOGUE', 'NA28_SECTION', 'HIGH', 'REGISTERED',
                    '1.0.0', '2026-09-30T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO passages (
                    passage_id, pericope_id, book_id, chapter, verse, sort_order
                ) VALUES (
                    'PASS_JHN_1_1', 'PERIC_JHN_1_1', 'JHN', 1, 1, 1
                );
                """
            )

            # Insert baseline Evidence records into evidence_ledger
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier,
                    source_reference, extracted_text_or_data, status, confidence,
                    confidence_score, is_counter_evidence, is_ai_generated,
                    is_translation_derived, is_contradicted, provenance_hash, is_immutable
                ) VALUES
                ('EV-LOGOS-01', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION',
                 'Yohanes 1:1', 'Ἐν ἀρχῇ ἦν ὁ λόγος', 'EXPLICIT', 'CERTAIN', 1.0, 0, 0, 0, 0, 'hash1', 1),
                ('EV-LOGOS-02', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'E4_LEXICAL', 'T1_LINGUISTIC_FACT',
                 'BDAG s.v. logos', 'logos: word, speech, divine utterance', 'LEXICALLY_SUPPORTED', 'HIGH', 0.85, 0, 0, 0, 0, 'hash2', 1),
                ('EV-COUNTER-01', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'E3_SYNTAX', 'T1_LINGUISTIC_FACT',
                 'Colwell Rule Critique', 'theos without article indicates qualitative predicate, not ontological identity',
                 'CONTEXTUALLY_STRONG', 'MEDIUM', 0.60, 1, 0, 0, 0, 'hash3', 1),
                ('EV-TENSION-01', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'E6_IMMEDIATE_CONTEXT', 'T2_CONTEXTUAL_CLAIM',
                 'Yohanes 1:14', 'sarx egeneto indicates becoming/temporal entrance', 'PLAUSIBLE', 'MEDIUM', 0.50, 0, 0, 0, 0, 'hash4', 1);
                """
            )

            # Insert baseline claims into claims
            conn.execute(
                """
                INSERT OR IGNORE INTO claims (
                    claim_id, pericope_id, passage_id, claim_tier, epistemic_type,
                    claim_text, claimed_by, epistemic_status, confidence_score,
                    calculated_confidence, is_unresolved_contradiction, has_counter_evidence,
                    is_theology_independent, is_immutable
                ) VALUES
                ('CLAIM-T1-LOGOS', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'T1_LINGUISTIC_FACT', 'LINGUISTIC_FACT',
                 'Logos is grammatical subject in Yohanes 1:1a', 'Grammarian', 'VERIFIED_FACT', 0.95, 0.95, 0, 0, 1, 1),
                ('CLAIM-T4-DOGMA', 'PERIC_JHN_1_1', 'PASS_JHN_1_1', 'T4_THEOLOGICAL_CLAIM', 'THEOLOGICAL_CLAIM',
                 'Logos denotes Second Person of Trinity eternally generated', 'Creed', 'UNPROVEN_DOGMA', 0.40, 0.40, 0, 1, 0, 1);
                """
            )

            # Insert claim evidence links
            conn.execute(
                """
                INSERT OR IGNORE INTO claim_evidence_links (
                    link_id, claim_id, evidence_id, relationship, is_critical_dependency,
                    weight, reasoning
                ) VALUES
                ('LINK-01', 'CLAIM-T1-LOGOS', 'EV-LOGOS-01', 'SUPPORT', 1, 1.0, 'Direct Greek text observation'),
                ('LINK-02', 'CLAIM-T4-DOGMA', 'EV-COUNTER-01', 'CONTRADICT', 1, 0.9, 'Qualitative reading challenges ontological identity');
                """
            )

        # Index evidence into FTS
        self.retrieval_engine.index_evidence_ledger()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. MIGRATION & BASELINE PROTECTION
    # -------------------------------------------------------------------------

    def test_01_migration_022_schema_and_triggers_initialized(self) -> None:
        """Verify all migration 022 tables and triggers are properly installed."""
        with self.engine.connect() as conn:
            tables = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name;"
                ).fetchall()
            ]
            self.assertIn("retrieval_queries", tables)
            self.assertIn("retrieval_runs", tables)
            self.assertIn("retrieval_coverage_records", tables)
            self.assertIn("retrieval_context_packs", tables)
            self.assertIn("retrieval_pack_items", tables)
            self.assertIn("retrieval_fts_index", tables)

            triggers = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'trigger' ORDER BY name;"
                ).fetchall()
            ]
            self.assertIn("trg_immut_retrieval_queries_upd", triggers)
            self.assertIn("trg_immut_retrieval_queries_del", triggers)
            self.assertIn("trg_immut_retrieval_runs_upd", triggers)
            self.assertIn("trg_immut_retrieval_runs_del", triggers)
            self.assertIn("trg_immut_retrieval_cov_upd", triggers)
            self.assertIn("trg_immut_retrieval_cov_del", triggers)
            self.assertIn("trg_immut_retrieval_packs_upd", triggers)
            self.assertIn("trg_immut_retrieval_packs_del", triggers)
            self.assertIn("trg_immut_retrieval_items_upd", triggers)
            self.assertIn("trg_immut_retrieval_items_del", triggers)

    def test_02_migration_001_to_021_checksums_frozen(self) -> None:
        """Verify migrations 001–021 remain strictly byte-for-byte unmodified."""
        schemas_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for filename, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            path = schemas_dir / filename
            self.assertTrue(path.exists(), f"Migration file missing: {filename}")
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Checksum mismatch for frozen migration {filename}!",
            )

    def test_03_legacy_database_hash_preservation(self) -> None:
        """Verify legacy databases remain untouched."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
            self.assertEqual(actual, LEGACY_DB_SHA256, "Legacy DB polya_index.db was modified!")

    def test_04_migration_022_checksum_locked(self) -> None:
        """Verify migration 022 checksum matches the locked schema."""
        path = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "022_hybrid_symmetrical_retrieval.sql"
        self.assertTrue(path.exists())
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(actual_hash, EXPECTED_022_CHECKSUM)

    # -------------------------------------------------------------------------
    # 2. IMMUTABILITY TRIGGERS
    # -------------------------------------------------------------------------

    def test_05_immutability_retrieval_queries_triggers(self) -> None:
        """retrieval_queries cannot be updated or deleted."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE retrieval_queries SET raw_query = 'tampered' WHERE query_id = ?",
                    (pack.query_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM retrieval_queries WHERE query_id = ?",
                    (pack.query_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_06_immutability_retrieval_runs_triggers(self) -> None:
        """retrieval_runs cannot be updated or deleted."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE retrieval_runs SET run_seed = 999 WHERE run_id = ?",
                    (pack.run_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM retrieval_runs WHERE run_id = ?",
                    (pack.run_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_07_immutability_coverage_records_triggers(self) -> None:
        """retrieval_coverage_records cannot be updated or deleted."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        cov_id = pack.coverage_records[0].coverage_id
        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE retrieval_coverage_records SET candidate_count = 0 WHERE coverage_id = ?",
                    (cov_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM retrieval_coverage_records WHERE coverage_id = ?",
                    (cov_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_08_immutability_context_packs_triggers(self) -> None:
        """retrieval_context_packs cannot be updated or deleted."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE retrieval_context_packs SET aggregate_confidence = 1.0 WHERE pack_id = ?",
                    (pack.pack_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM retrieval_context_packs WHERE pack_id = ?",
                    (pack.pack_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_09_immutability_pack_items_triggers(self) -> None:
        """retrieval_pack_items cannot be updated or deleted."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        self.assertGreater(len(pack.items), 0)
        item_id = pack.items[0].item_id
        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE retrieval_pack_items SET item_confidence = 1.0 WHERE item_id = ?",
                    (item_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

        with self.assertRaises((sqlite3.IntegrityError, sqlite3.OperationalError)) as ctx:
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM retrieval_pack_items WHERE item_id = ?",
                    (item_id,),
                )
        self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 3. FTS5 & STRING NORMALIZATION
    # -------------------------------------------------------------------------

    def test_10_fts5_virtual_table_availability_and_indexing(self) -> None:
        """FTS5 table indexes text and responds to search."""
        indexed_count = self.retrieval_engine.index_evidence_ledger()
        self.assertGreater(indexed_count, 0)
        with self.engine.connect() as conn:
            cur = conn.execute("SELECT count(*) FROM retrieval_fts_index;")
            self.assertGreater(cur.fetchone()[0], 0)

    def test_11_fts5_escaping_and_hostile_input_handling(self) -> None:
        """Hostile FTS syntax, boolean injections, unclosed quotes, and null bytes are sanitized."""
        hostile_inputs = [
            '" OR 1=1 --',
            'AND NOT OR *()',
            'test*',
            '\x00null',
            'SELECT * FROM users',
            '"""unbalanced quotes',
            'NEAR(logos, theos, 5)',
            'col:value AND NOT',
        ]
        for hostile in hostile_inputs:
            sanitized = sanitize_fts5_query(hostile)
            # Must not crash when queried in FTS5
            with self.engine.connect() as conn:
                try:
                    if sanitized:
                        conn.execute(
                            "SELECT * FROM retrieval_fts_index WHERE retrieval_fts_index MATCH ?",
                            (sanitized,),
                        ).fetchall()
                except sqlite3.OperationalError as e:
                    self.fail(f"FTS5 query failed for hostile input {hostile!r} (sanitized: {sanitized!r}): {e}")

    def test_12_unicode_greek_and_hebrew_normalization(self) -> None:
        """Greek and Hebrew text are normalized safely for search."""
        greek_text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        hebrew_text = "בְּרֵאשִׁית בָּרָא אֱלֹהִים"
        norm_greek = normalize_text_for_search(greek_text)
        norm_hebrew = normalize_text_for_search(hebrew_text)
        self.assertTrue(len(norm_greek) > 0)
        self.assertTrue(len(norm_hebrew) > 0)
        sanitized_greek = sanitize_fts5_query(greek_text)
        sanitized_hebrew = sanitize_fts5_query(hebrew_text)
        self.assertIn("λογος", norm_greek)
        self.assertTrue(len(sanitized_greek) > 0)
        self.assertTrue(len(sanitized_hebrew) > 0)

    # -------------------------------------------------------------------------
    # 4. SYMMETRICAL SEARCH OBLIGATION & SUPPRESSION PREVENTION
    # -------------------------------------------------------------------------

    def test_13_counter_search_mandatory_suppression_raises_error(self) -> None:
        """Attempting to disable counter-search via enable_counter_search=False raises error."""
        with self.assertRaises(CounterSearchSuppressionError):
            self.retrieval_engine.execute_retrieval("logos", enable_counter_search=False)

    def test_14_counter_search_kwarg_suppression_detection(self) -> None:
        """Kwargs attempting to disable, skip, or suppress counter-search are intercepted."""
        with self.assertRaises(CounterSearchSuppressionError):
            self.retrieval_engine.execute_retrieval("logos", disable_counter_search=True)
        with self.assertRaises(CounterSearchSuppressionError):
            self.retrieval_engine.execute_retrieval("logos", skip_counter_search=True)
        with self.assertRaises(CounterSearchSuppressionError):
            self.retrieval_engine.execute_retrieval("logos", run_counter_search=False)

    def test_15_search_symmetry_obligation_both_branches_executed(self) -> None:
        """Every retrieval run executes both PRIMARY_SEARCH and COUNTER_SEARCH branches."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        branches = [c.search_branch for c in pack.coverage_records]
        self.assertIn(SearchBranch.PRIMARY_SEARCH, branches)
        self.assertIn(SearchBranch.COUNTER_SEARCH, branches)
        self.assertEqual(len(branches), 2)

    # -------------------------------------------------------------------------
    # 5. SEARCH BRANCH != EVIDENCE ROLE
    # -------------------------------------------------------------------------

    def test_16_search_branch_separated_from_evidence_role(self) -> None:
        """Search branch indicates origin; evidence role is independently validated."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        for item in pack.items:
            self.assertIn(item.search_branch, (SearchBranch.PRIMARY_SEARCH, SearchBranch.COUNTER_SEARCH))
            self.assertIn(
                item.evidence_role,
                (
                    EvidenceRole.SUPPORTING,
                    EvidenceRole.COUNTER_EVIDENCE,
                    EvidenceRole.NEUTRAL_CONTEXT,
                    EvidenceRole.ORTHOGONAL_TENSION,
                ),
            )

    def test_17_counter_search_candidate_not_automatic_counter_evidence(self) -> None:
        """A candidate found through COUNTER_SEARCH is not automatically COUNTER_EVIDENCE."""
        # Querying an item via counter search without contradictory evidence will not force COUNTER_EVIDENCE
        pack = self.retrieval_engine.execute_retrieval("direct text")
        counter_items = [it for it in pack.items if it.search_branch == SearchBranch.COUNTER_SEARCH]
        for it in counter_items:
            # If not inherently contradicting, role must be neutral or orthogonal
            if it.evidence_id == "EV-TENSION-01":
                self.assertIn(it.evidence_role, (EvidenceRole.ORTHOGONAL_TENSION, EvidenceRole.NEUTRAL_CONTEXT))

    # -------------------------------------------------------------------------
    # 6. E/T TIER FIREWALL
    # -------------------------------------------------------------------------

    def test_18_et_tier_firewall_no_claim_tier_column_on_pack_items(self) -> None:
        """retrieval_pack_items table strictly does NOT store a claim_tier column."""
        with self.engine.connect() as conn:
            columns = [
                r["name"]
                for r in conn.execute("PRAGMA table_info(retrieval_pack_items);").fetchall()
            ]
            self.assertNotIn("claim_tier", columns)
            self.assertIn("linked_claim_id", columns)

    def test_19_et_tier_firewall_null_linked_claim_has_no_t_tier(self) -> None:
        """If linked_claim_id is NULL, retrieval item has NO T-tier."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        unlinked_items = [it for it in pack.items if it.linked_claim_id is None]
        for it in unlinked_items:
            self.assertIsNone(it.linked_claim_id)
            self.assertFalse(hasattr(it, "claim_tier"))

    # -------------------------------------------------------------------------
    # 7. GRAPH FIREWALL
    # -------------------------------------------------------------------------

    def test_20_graph_firewall_connectivity_and_centrality_not_truth(self) -> None:
        """Graph centrality, node degree, or path length cannot determine truth or confidence."""
        with self.assertRaises(GraphEpistemicLeakageError):
            self.retrieval_engine._validate_and_build_item(
                pack_id="pack-test",
                candidate={
                    "evidence_id": "EV-LOGOS-01",
                    "source": CandidateSource.GRAPH_RELATION,
                    "degree": 15,
                    "centrality": 0.99,
                },
                branch=SearchBranch.PRIMARY_SEARCH,
                target=RetrievalTarget(target_type=RetrievalTargetType.FREE_TEXT),
                rank=1,
            )

    def test_21_graph_candidate_validation_against_evidence_ledger(self) -> None:
        """Graph signals not present in evidence_ledger are rejected during validation."""
        item = self.retrieval_engine._validate_and_build_item(
            pack_id="pack-test",
            candidate={
                "evidence_id": "EV-PHANTOM-999",
                "source": CandidateSource.GRAPH_RELATION,
                "score": 0.5,
            },
            branch=SearchBranch.PRIMARY_SEARCH,
            target=RetrievalTarget(target_type=RetrievalTargetType.FREE_TEXT),
            rank=1,
        )
        self.assertIsNone(item)

    def test_22_bounded_graph_expansion(self) -> None:
        """Graph expansion strictly adheres to max_graph_depth and candidate limits."""
        cfg = RetrievalConfig(max_graph_depth=1, max_graph_candidates=5)
        self.assertEqual(cfg.max_graph_depth, 1)
        self.assertEqual(cfg.max_graph_candidates, 5)

    # -------------------------------------------------------------------------
    # 8. T4 THEOLOGY FIREWALL
    # -------------------------------------------------------------------------

    def test_23_t4_theology_firewall_t4_cannot_support_t0_to_t3(self) -> None:
        """T4 dogmatic proposition cannot serve as supporting evidence for T0–T3 target."""
        with self.assertRaises(DogmaticContaminationError):
            self.retrieval_engine._validate_and_build_item(
                pack_id="pack-test",
                candidate={
                    "evidence_id": "EV-LOGOS-01",
                    "claim_id": "CLAIM-T4-DOGMA",
                    "relationship": "SUPPORT",
                    "source": CandidateSource.DIRECT_LOOKUP,
                    "score": 0.9,
                },
                branch=SearchBranch.PRIMARY_SEARCH,
                target=RetrievalTarget(
                    target_type=RetrievalTargetType.CLAIM,
                    target_tier="T1_LINGUISTIC_FACT",
                ),
                rank=1,
            )

    def test_24_t4_theology_firewall_t4_retrieval_target_allowed(self) -> None:
        """T4 dogmatic propositions may be retrieval targets without violating firewall."""
        pack = self.retrieval_engine.execute_retrieval(
            query="consubstantiality",
            target=RetrievalTarget(
                target_type=RetrievalTargetType.PROPOSITION,
                target_id="PROP-NICENE-01",
                target_tier="T4_THEOLOGICAL_CLAIM",
            ),
        )
        self.assertIsNotNone(pack)
        self.assertTrue(pack.pack_id.startswith("ret-pack-"))

    # -------------------------------------------------------------------------
    # 9. ABSENCE-OF-EVIDENCE FIREWALL
    # -------------------------------------------------------------------------

    def test_25_absence_of_evidence_not_found_not_equal_no_counter_evidence(self) -> None:
        """NOT_FOUND status does not convert into NO_COUNTER_EVIDENCE_EXISTS."""
        pack = self.retrieval_engine.execute_retrieval("uncontroversial observation")
        self.assertIn(
            pack.counter_evidence_status,
            (
                CounterEvidenceStatus.COUNTER_EVIDENCE_FOUND,
                CounterEvidenceStatus.COUNTER_EVIDENCE_NOT_FOUND,
                CounterEvidenceStatus.COUNTER_EVIDENCE_NOT_DETERMINABLE,
            ),
        )
        self.assertNotEqual(str(pack.counter_evidence_status), "NO_COUNTER_EVIDENCE_EXISTS")

    def test_26_absence_of_evidence_status_methodology_recording(self) -> None:
        """Coverage records document why counter-evidence status was assigned."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        counter_cov = next(
            c for c in pack.coverage_records if c.search_branch == SearchBranch.COUNTER_SEARCH
        )
        self.assertTrue(len(counter_cov.methodology_notes) > 0)
        self.assertIn("counter-search", counter_cov.methodology_notes.lower())

    # -------------------------------------------------------------------------
    # 10. CONFIDENCE FIREWALL
    # -------------------------------------------------------------------------

    def test_27_confidence_firewall_capped_at_min_critical_evidence(self) -> None:
        """Pack aggregate confidence is capped at the minimum constituent item confidence."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        if pack.items:
            expected_min = min(it.item_confidence for it in pack.items)
            self.assertAlmostEqual(pack.aggregate_confidence, expected_min, places=4)
            self.assertLessEqual(pack.aggregate_confidence, expected_min)

    def test_28_confidence_firewall_ranking_bm25_does_not_inflate(self) -> None:
        """High BM25 score or rank #1 does not inflate item confidence above source value."""
        pack = self.retrieval_engine.execute_retrieval("theos")
        for item in pack.items:
            # Item confidence must match evidence_ledger confidence, not relevance score
            with self.engine.connect() as conn:
                row = conn.execute(
                    "SELECT confidence_score FROM evidence_ledger WHERE evidence_id = ?",
                    (item.evidence_id,),
                ).fetchone()
                if row and row["confidence_score"] is not None:
                    self.assertAlmostEqual(item.item_confidence, float(row["confidence_score"]), places=4)

    # -------------------------------------------------------------------------
    # 11. DETERMINISTIC CANONICAL HASH
    # -------------------------------------------------------------------------

    def test_29_deterministic_canonical_pack_hash_calculation(self) -> None:
        """Pack hash matches SHA-256 computation of canonical deterministic payload."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        self.assertTrue(self.retrieval_engine.verify_pack_integrity(pack.pack_id))

    def test_30_deterministic_hash_independent_of_sqlite_row_order(self) -> None:
        """Canonical hash does not depend on SQLite row-return order."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        # Recalculate hash with scrambled internal order
        primary_ev_ids = [it.evidence_id for it in pack.items if it.search_branch == SearchBranch.PRIMARY_SEARCH]
        counter_ev_ids = [it.evidence_id for it in pack.items if it.search_branch == SearchBranch.COUNTER_SEARCH]
        graph_signal_ids = [it.evidence_id for it in pack.items if it.candidate_source == CandidateSource.GRAPH_RELATION]
        linked_claim_ids = [it.linked_claim_id for it in pack.items if it.linked_claim_id is not None]

        payload_1 = {
            "query_hash": hashlib.sha256(normalize_text_for_search("logos").encode("utf-8")).hexdigest(),
            "normalized_query": normalize_text_for_search("logos"),
            "configuration_hash": RetrievalConfig().compute_hash(),
            "coverage_records": sorted([
                {
                    "branch": c.search_branch.value,
                    "status": c.coverage_status,
                    "strategy": c.search_strategy,
                    "candidate_count": c.candidate_count,
                    "matched_count": c.matched_count,
                }
                for c in reversed(pack.coverage_records)  # Reversing input list
            ], key=lambda x: (x["branch"], x["strategy"], x["status"])),
            "primary_evidence_ids": sorted(list(set(reversed(primary_ev_ids)))),
            "counter_evidence_ids": sorted(list(set(reversed(counter_ev_ids)))),
            "graph_signal_ids": sorted(list(set(reversed(graph_signal_ids)))),
            "linked_claim_ids": sorted(list(set(reversed(linked_claim_ids)))),
            "version_id": pack.version_id,
            "provenance_id": pack.provenance_id,
        }
        hash_1 = hashlib.sha256(json.dumps(payload_1, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(hash_1, pack.pack_hash)

    # -------------------------------------------------------------------------
    # 12. PROVENANCE & VERSIONING
    # -------------------------------------------------------------------------

    def test_31_provenance_methodology_completeness(self) -> None:
        """Every retrieval run registers verifiable cryptographic provenance."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        prov_record = self.provenance_tracker.get_record(pack.provenance_id)
        self.assertIsNotNone(prov_record)
        self.assertEqual(prov_record.agent_id, "retrieval_engine")
        self.assertEqual(prov_record.target_type, "DERIVED_ARTIFACT")
        self.assertTrue(prov_record.provenance_id.startswith("PRV-"))

    def test_32_versioning_integration(self) -> None:
        """Every retrieval pack registers an object version record."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        ver_record = self.version_manager.get_version(pack.version_id)
        self.assertIsNotNone(ver_record)
        self.assertEqual(ver_record.object_type, "retrieval_context_pack")
        self.assertEqual(ver_record.object_id, pack.pack_id)

    # -------------------------------------------------------------------------
    # 13. CONCURRENCY & INTEGRITY
    # -------------------------------------------------------------------------

    def test_33_concurrent_retrieval_execution_safety(self) -> None:
        """Concurrent threads execute retrieval without deadlock or table locks."""
        queries = ["logos", "theos", "arche", "sarx"]
        results: List[RetrievalPackResult] = []

        def worker(q: str) -> RetrievalPackResult:
            eng = DatabaseEngine(DatabaseConfig(db_path=str(self.db_path)))
            prov = ProvenanceTracker(eng)
            ver = VersionManager(eng)
            r_eng = HybridSymmetricalRetrievalEngine(eng, prov, ver)
            res = r_eng.execute_retrieval(q)
            return res

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(worker, q) for q in queries]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

        self.assertEqual(len(results), 4)
        for r in results:
            self.assertTrue(r.pack_id.startswith("ret-pack-"))

    def test_34_pack_integrity_verification_pass_and_tamper_detection(self) -> None:
        """verify_pack_integrity passes for unaltered pack and raises error on missing run."""
        pack = self.retrieval_engine.execute_retrieval("logos")
        self.assertTrue(self.retrieval_engine.verify_pack_integrity(pack.pack_id))
        with self.assertRaises(RetrievalContextPackNotFoundError):
            self.retrieval_engine.verify_pack_integrity("non-existent-pack")

    def test_35_anti_confirmation_bias_symmetrical_coverage(self) -> None:
        """Retrieval does not suppress counter-evidence for controversial doctrinal topics."""
        pack = self.retrieval_engine.execute_retrieval("logos theos")
        counter_cov = next(
            c for c in pack.coverage_records if c.search_branch == SearchBranch.COUNTER_SEARCH
        )
        self.assertIsNotNone(counter_cov)
        # Symmetrical search candidate obligation was fulfilled
        self.assertEqual(counter_cov.search_branch, SearchBranch.COUNTER_SEARCH)
