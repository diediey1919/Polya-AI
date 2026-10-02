"""
Test Suite for Task 4.7 Deterministic Query Planning Engine.
Specification: TASK 4.7 SPECIFICATION v1.3.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AmbiguousTargetError,
    KnowledgeHierarchyViolationError,
    KnowledgeQueryValidationError,
    QueryPlanningError,
    QuerySyntaxError,
    ScopeResolutionError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.query_planning import (
    COLON_MAPPINGS,
    DASH_MAPPINGS,
    OUTER_DELIMITER_PAIRS,
    QueryPlan,
    QueryPlanner,
    compute_plan_hash,
    normalize_query,
)
from bible_engine.synthesis import SynthesisScope


class TestBibleEngineQueryPlanning(unittest.TestCase):
    """Exhaustive unit and integration test suite for Task 4.7 Query Planning."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_query_planning.db")
        self.migrations_dir = Path(__file__).parent.parent / "schemas" / "bible_engine"

        self.db_config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.db_config)
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        self.runner.apply_pending()

        self._seed_catalog()
        self.planner = QueryPlanner(self.engine)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _seed_catalog(self) -> None:
        """Seed minimal canonical catalog records for testing."""
        with self.engine.transaction() as conn:
            # Canons
            conn.execute(
                """
                INSERT INTO canons (canon_id, name, description, created_at)
                VALUES ('CANON-PROTESTANT-66', 'Protestant Canon', 'Standard 66-book canon', '2026-10-02T00:00:00Z');
                """
            )
            # Testaments / Corpora
            conn.execute(
                """
                INSERT INTO testaments (testament_id, canon_id, name, sort_order)
                VALUES ('TEST-OT', 'CANON-PROTESTANT-66', 'Perjanjian Lama', 1);
                """
            )
            conn.execute(
                """
                INSERT INTO testaments (testament_id, canon_id, name, sort_order)
                VALUES ('TEST-NT', 'CANON-PROTESTANT-66', 'Perjanjian Baru', 2);
                """
            )
            # Books
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('ROM', 'TEST-NT', 45, 'Roma', 'Romans', 'GREEK', 16);
                """
            )
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('1CO', 'TEST-NT', 46, '1 Korintus', '1 Corinthians', 'GREEK', 16);
                """
            )
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('REV', 'TEST-NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);
                """
            )
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('GEN', 'TEST-OT', 1, 'Kejadian', 'Genesis', 'HEBREW', 50);
                """
            )
            # Sections
            conn.execute(
                """
                INSERT INTO sections (section_id, book_id, title, start_chapter, start_verse, end_chapter, end_verse, genre)
                VALUES ('SEC-ROM-001', 'ROM', 'Greeting & Intro', 1, 1, 1, 17, 'EPISTLE');
                """
            )
            conn.execute(
                """
                INSERT INTO sections (section_id, book_id, title, start_chapter, start_verse, end_chapter, end_verse, genre)
                VALUES ('SEC-ROM-003', 'ROM', 'Righteousness by Faith', 3, 1, 3, 31, 'EPISTLE');
                """
            )
            # Pericopes
            conn.execute(
                """
                INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at)
                VALUES ('PER-ROM-003', 'ROM', 'Roma 3:1-5', 3, 1, 3, 5, 'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '1', '2026-10-02T00:00:00Z');
                """
            )
            conn.execute(
                """
                INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at)
                VALUES ('PER-1CO-13', '1CO', '1 Korintus 13:4-8', 13, 4, 13, 8, 'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '1', '2026-10-02T00:00:00Z');
                """
            )

    # =========================================================================
    # 1. NORMALIZATION TESTS
    # =========================================================================

    def test_normalization_nfkc(self) -> None:
        """Test Unicode NFKC compatibility normalization."""
        # Decomposed Latin e + acute accent vs precomposed
        decomposed = "Rom\u0065\u0301 3:1-5"
        normalized = normalize_query(decomposed)
        self.assertEqual(normalized, "Romé 3:1-5")

        # Full-width Latin letters
        full_width = "\uff32\uff4f\uff4d\uff41 3:1-5"  # Ｒｏｍａ
        self.assertEqual(normalize_query(full_width), "Roma 3:1-5")

    def test_normalization_whitespace(self) -> None:
        """Test whitespace stripping and collapsing."""
        # Leading and trailing spaces
        self.assertEqual(normalize_query("   Roma 3:1-5   "), "Roma 3:1-5")
        # Internal tabs, newlines, multiple spaces
        self.assertEqual(normalize_query("Roma\t\n  3:1-5"), "Roma 3:1-5")
        self.assertEqual(normalize_query("1   Korintus    13:4-8"), "1 Korintus 13:4-8")

    def test_normalization_outer_quote_stripping(self) -> None:
        """Test stripping of approved outer quote pairs."""
        # ASCII double quotes
        self.assertEqual(normalize_query('"Roma 3:1-5"'), "Roma 3:1-5")
        # ASCII single quotes
        self.assertEqual(normalize_query("'Roma 3:1-5'"), "Roma 3:1-5")
        # Curly double quotes U+201C ... U+201D
        self.assertEqual(normalize_query("“Roma 3:1-5”"), "Roma 3:1-5")
        # Curly single quotes U+2018 ... U+2019
        self.assertEqual(normalize_query("‘Roma 3:1-5’"), "Roma 3:1-5")
        # Guillemets U+00AB ... U+00BB
        self.assertEqual(normalize_query("«Roma 3:1-5»"), "Roma 3:1-5")

    def test_normalization_outer_bracket_stripping(self) -> None:
        """Test stripping of approved outer bracket and parenthesis pairs."""
        # Square brackets [ ... ]
        self.assertEqual(normalize_query("[Roma 3:1-5]"), "Roma 3:1-5")
        # Parentheses ( ... )
        self.assertEqual(normalize_query("(Roma 3:1-5)"), "Roma 3:1-5")

    def test_normalization_single_outer_pair_non_recursive(self) -> None:
        """Verify non-recursive stripping: only the outermost pair is stripped."""
        nested = '"[Roma 3:1-5]"'
        # Strips outer double quotes, leaves inner square brackets
        self.assertEqual(normalize_query(nested), "[Roma 3:1-5]")

    def test_normalization_unmatched_delimiters(self) -> None:
        """Unmatched delimiters must NOT be stripped and remain intact."""
        # Starts with quote, doesn't end with quote
        self.assertEqual(normalize_query('"Roma 3:1-5'), '"Roma 3:1-5')
        # Ends with quote, doesn't start with quote
        self.assertEqual(normalize_query('Roma 3:1-5"'), 'Roma 3:1-5"')
        # Mismatched pair: starts with [ and ends with )
        self.assertEqual(normalize_query("[Roma 3:1-5)"), "[Roma 3:1-5)")
        # Mismatched quotes: starts with “ and ends with "
        self.assertEqual(normalize_query('“Roma 3:1-5"'), '“Roma 3:1-5"')

    def test_normalization_dash_mappings(self) -> None:
        """Verify all 8 specified Unicode dash code points map to ASCII hyphen-minus U+002D."""
        dash_chars = [
            ("\u2010", "Hyphen"),
            ("\u2011", "Non-breaking hyphen"),
            ("\u2012", "Figure dash"),
            ("\u2013", "En-dash"),
            ("\u2014", "Em-dash"),
            ("\u2015", "Horizontal bar"),
            ("\ufe63", "Small hyphen-minus"),
            ("\uff0d", "Full-width hyphen-minus"),
        ]
        for ch, name in dash_chars:
            raw = f"Roma 3:1{ch}5"
            normalized = normalize_query(raw)
            self.assertEqual(
                normalized,
                "Roma 3:1-5",
                f"Failed mapping for {name} ({hex(ord(ch))})",
            )

    def test_normalization_full_width_colon(self) -> None:
        """Verify full-width colon U+FF1A maps to ASCII colon U+003A."""
        raw = "Roma 3\uff1a1-5"
        self.assertEqual(normalize_query(raw), "Roma 3:1-5")

    # =========================================================================
    # 2. CANONICAL PASSAGE REFERENCE TESTS
    # =========================================================================

    def test_canonical_passage_reference_equivalence(self) -> None:
        """
        Verify that typographical and formatting variants of a reference
        all derive the exact same canonical reference: "Roma 3:1-5".
        """
        variants = [
            "Roma 3:1-5",
            "Roma 3:1–5",       # En-dash
            "Roma   3:1 - 5",   # Spacing
            "roma 3:1-5",       # Lowercase
            "“Roma 3:1-5”",     # Quoted
            "'Roma 3:1-5'",     # Single quoted
            "«Roma 3:1-5»",     # Guillemets
        ]
        for variant in variants:
            plan = self.planner.plan(variant)
            self.assertEqual(
                plan.canonical_passage_reference,
                "Roma 3:1-5",
                f"Variant '{variant}' failed to resolve to 'Roma 3:1-5'",
            )

    def test_canonical_passage_reference_single_verse(self) -> None:
        """Verify single verse formatting: standard_name ch:vs."""
        plan = self.planner.plan("roma 3:1", explicit_target_id="PER-ROM-003")
        self.assertEqual(plan.canonical_passage_reference, "Roma 3:1")

    def test_canonical_passage_reference_multi_chapter(self) -> None:
        """Verify multi-chapter range formatting: standard_name start_ch:start_vs-end_ch:end_vs."""
        plan = self.planner.plan("roma 3:1-4:5", explicit_target_id="PER-ROM-003")
        self.assertEqual(plan.canonical_passage_reference, "Roma 3:1-4:5")

    def test_canonical_passage_reference_non_passage(self) -> None:
        """Verify non-passage queries resolve canonical_passage_reference to None."""
        # Book only
        self.assertIsNone(self.planner.plan("Roma").canonical_passage_reference)
        # Canon ID
        self.assertIsNone(self.planner.plan("CANON-PROTESTANT-66").canonical_passage_reference)
        # Section ID
        self.assertIsNone(self.planner.plan("SEC-ROM-001").canonical_passage_reference)
        # Pericope ID
        self.assertIsNone(self.planner.plan("PER-ROM-003").canonical_passage_reference)

    # =========================================================================
    # 3. CATALOG RESOLUTION TESTS
    # =========================================================================

    def test_catalog_resolve_books(self) -> None:
        """Test resolving books by ID, standard name, and English name."""
        # Standard name
        plan = self.planner.plan("Roma")
        self.assertEqual(plan.resolved_scope, SynthesisScope.BOOK)
        self.assertEqual(plan.resolved_target_id, "ROM")

        # Uppercase book ID
        plan_id = self.planner.plan("ROM")
        self.assertEqual(plan_id.resolved_scope, SynthesisScope.BOOK)
        self.assertEqual(plan_id.resolved_target_id, "ROM")

        # English name
        plan_en = self.planner.plan("Romans")
        self.assertEqual(plan_en.resolved_scope, SynthesisScope.BOOK)
        self.assertEqual(plan_en.resolved_target_id, "ROM")

        # Book with number prefix
        plan_co = self.planner.plan("1 Korintus")
        self.assertEqual(plan_co.resolved_scope, SynthesisScope.BOOK)
        self.assertEqual(plan_co.resolved_target_id, "1CO")

    def test_catalog_resolve_canons(self) -> None:
        """Test resolving canons by ID and name."""
        plan = self.planner.plan("CANON-PROTESTANT-66")
        self.assertEqual(plan.resolved_scope, SynthesisScope.CANON)
        self.assertEqual(plan.resolved_target_id, "CANON-PROTESTANT-66")

        plan_name = self.planner.plan("Protestant Canon")
        self.assertEqual(plan_name.resolved_scope, SynthesisScope.CANON)
        self.assertEqual(plan_name.resolved_target_id, "CANON-PROTESTANT-66")

    def test_catalog_resolve_testaments_corpora(self) -> None:
        """Test resolving testaments/corpora by ID and name."""
        plan = self.planner.plan("TEST-NT")
        self.assertEqual(plan.resolved_scope, SynthesisScope.CORPUS)
        self.assertEqual(plan.resolved_target_id, "TEST-NT")

        plan_name = self.planner.plan("Perjanjian Baru")
        self.assertEqual(plan_name.resolved_scope, SynthesisScope.CORPUS)
        self.assertEqual(plan_name.resolved_target_id, "TEST-NT")

    def test_catalog_resolve_sections(self) -> None:
        """Test resolving section by section_id."""
        plan = self.planner.plan("SEC-ROM-001")
        self.assertEqual(plan.resolved_scope, SynthesisScope.SECTION)
        self.assertEqual(plan.resolved_target_id, "SEC-ROM-001")

    def test_catalog_resolve_pericopes(self) -> None:
        """Test resolving pericope by pericope_id and reference."""
        # By ID
        plan_id = self.planner.plan("PER-ROM-003")
        self.assertEqual(plan_id.resolved_scope, SynthesisScope.PERICOPE)
        self.assertEqual(plan_id.resolved_target_id, "PER-ROM-003")

        # By passage reference
        plan_ref = self.planner.plan("Roma 3:1-5")
        self.assertEqual(plan_ref.resolved_scope, SynthesisScope.PERICOPE)
        self.assertEqual(plan_ref.resolved_target_id, "PER-ROM-003")

    def test_catalog_resolve_chapter_only_success(self) -> None:
        """Whole-chapter query matches registered section."""
        # Section SEC-ROM-003 covers start_chapter=3, end_chapter=3
        plan = self.planner.plan("Roma 3")
        self.assertEqual(plan.resolved_scope, SynthesisScope.SECTION)
        self.assertEqual(plan.resolved_target_id, "SEC-ROM-003")

    def test_catalog_resolve_chapter_only_fail_closed(self) -> None:
        """Whole-chapter query fails closed when no registered section exists."""
        # Chapter 4 of Roma has no registered section
        with self.assertRaises(ScopeResolutionError) as ctx:
            self.planner.plan("Roma 4")
        self.assertIn("No registered section matches chapter query", str(ctx.exception))

    def test_catalog_missing_target_fails_closed(self) -> None:
        """Missing book or entity raises ScopeResolutionError."""
        with self.assertRaises(ScopeResolutionError):
            self.planner.plan("NonexistentBook 1:1")
        with self.assertRaises(ScopeResolutionError):
            self.planner.plan("CANON-UNKNOWN-99")
        with self.assertRaises(ScopeResolutionError):
            self.planner.plan("SEC-UNKNOWN-99")

    def test_catalog_ambiguous_target_fails_closed(self) -> None:
        """Multiple matching catalog targets raise AmbiguousTargetError."""
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count)
                VALUES ('ROM_ALT', 'TEST-NT', 99, 'Roma Alt', 'Roma', 'GREEK', 16);
                """
            )
        try:
            with self.assertRaises(AmbiguousTargetError):
                self.planner.plan("Roma")
        finally:
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM books WHERE book_id = 'ROM_ALT';")

    def test_invalid_syntax_ranges(self) -> None:
        """Test invalid verse or chapter bounds."""
        with self.assertRaises(QuerySyntaxError):
            self.planner.plan("Roma 3:5-1")  # End verse precedes start verse
        with self.assertRaises(QuerySyntaxError):
            self.planner.plan("Roma 4:5-3:1")  # End chapter precedes start chapter
        with self.assertRaises(QuerySyntaxError):
            self.planner.plan("   ")  # Empty query

    # =========================================================================
    # 4. PLANNER & PLAN IDENTITY TESTS
    # =========================================================================

    def test_plan_hash_and_id_determinism(self) -> None:
        """Verify identical inputs yield byte-identical plan_hash and plan_id."""
        plan1 = self.planner.plan("Roma 3:1-5")
        plan2 = self.planner.plan("Roma 3:1-5")

        self.assertEqual(plan1.plan_hash, plan2.plan_hash)
        self.assertEqual(plan1.plan_id, plan2.plan_id)
        self.assertTrue(plan1.plan_id.startswith("PLAN-"))
        self.assertEqual(len(plan1.plan_id), 5 + 16)  # 'PLAN-' + 16 hex chars

    def test_plan_identity_presentation_independence(self) -> None:
        """
        Queries that normalize identically must produce byte-identical
        plan_hash and plan_id despite raw formatting differences.
        """
        plan_clean = self.planner.plan("Roma 3:1-5")
        plan_dash = self.planner.plan("Roma 3:1–5")
        plan_quoted = self.planner.plan("“Roma 3:1-5”")
        plan_spaces = self.planner.plan("Roma   3:1-5")

        self.assertEqual(plan_clean.plan_hash, plan_dash.plan_hash)
        self.assertEqual(plan_clean.plan_hash, plan_quoted.plan_hash)
        self.assertEqual(plan_clean.plan_hash, plan_spaces.plan_hash)

    def test_plan_identity_sensitive_to_semantic_parameters(self) -> None:
        """Plan hash must differ when semantic retrieval parameters change."""
        base_plan = self.planner.plan("Roma 3:1-5", limit=50)

        # Different limit
        plan_limit = self.planner.plan("Roma 3:1-5", limit=20)
        self.assertNotEqual(base_plan.plan_hash, plan_limit.plan_hash)

        # Different evidence flag
        plan_ev = self.planner.plan("Roma 3:1-5", include_evidence=False)
        self.assertNotEqual(base_plan.plan_hash, plan_ev.plan_hash)

        # Different pipeline hash
        plan_pipe = self.planner.plan("Roma 3:1-5", pipeline_configuration_hash="pipe-abc")
        self.assertNotEqual(base_plan.plan_hash, plan_pipe.plan_hash)

    def test_knowledge_query_compilation_all_17_fields(self) -> None:
        """Verify KnowledgeQuery contract is strictly compiled with all 17 fields."""
        plan = self.planner.plan(
            query_text="Roma 3:1-5",
            source_corpus="NA28",
            target_corpus="BYZ",
            source_version="v1.0",
            pipeline_configuration_hash="cfg-123",
            limit=25,
            include_lineage=False,
            include_evidence=True,
            include_tensions=False,
        )
        kq = plan.knowledge_query

        self.assertEqual(kq.query_text, "Roma 3:1-5")
        self.assertEqual(kq.pericope_id, "PER-ROM-003")
        self.assertIsNone(kq.canon_id)
        self.assertIsNone(kq.corpus_id)
        self.assertIsNone(kq.book_id)
        self.assertIsNone(kq.section_id)
        self.assertEqual(kq.requested_scope, SynthesisScope.PERICOPE)
        self.assertEqual(kq.source_corpus, "NA28")
        self.assertEqual(kq.target_corpus, "BYZ")
        self.assertEqual(kq.source_version, "v1.0")
        self.assertEqual(kq.pipeline_configuration_hash, "cfg-123")
        self.assertEqual(kq.engine_version, "2.0.0")
        self.assertEqual(kq.schema_version, "025")
        self.assertEqual(kq.limit, 25)
        self.assertFalse(kq.include_lineage)
        self.assertTrue(kq.include_evidence)
        self.assertFalse(kq.include_tensions)

    def test_knowledge_query_hierarchy_validation_conflict(self) -> None:
        """
        Verify that conflicting requested_scope raises KnowledgeHierarchyViolationError
        per Task 4.5 contract.
        """
        # Query resolves to PERICOPE, but caller forces requested_scope=CANON
        with self.assertRaises(KnowledgeHierarchyViolationError):
            self.planner.plan(
                query_text="Roma 3:1-5",
                requested_scope=SynthesisScope.CANON,
            )


if __name__ == "__main__":
    unittest.main()
