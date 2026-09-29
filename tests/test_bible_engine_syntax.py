"""
Comprehensive Test Suite for Source-Language Syntax Foundation Subsystem.
Task 2.4 — Architecture v2.0 — FROZEN.

Validates:
  1. Syntax registration
  2. Token linkage
  3. Orphan rejection
  4. Clause linkage
  5. Clause boundary validation
  6. Dependency relation validation
  7. Constituent span validation
  8. Multiple competing parses
  9. Preferred parse separation
  10. Greek syntax
  11. Hebrew syntax
  12. Aramaic syntax
  13. Morphology firewall
  14. Semantic firewall
  15. Theology firewall
  16. Identity firewall
  17. Ambiguity preservation
  18. Provenance integration (deterministic)
  19. Provenance integration (generative)
  20. Versioning & superseding
  21. Immutability triggers
  22. Atomic rollback
  23. Concurrent syntax runs
  24. Cycle validation (self-loops, 2-node, 3-node cycles)
  25. Source reconstruction integrity
  26. Legacy database untouched
  27. Adversarial: out-of-bounds confidence scores
  28. Adversarial: duplicate parse index rejection
  29. Adversarial: cross-language / mismatched morphology run rejection
  30. Migration 008: legacy clause data preservation
"""

import hashlib
import os
import pathlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSyntaxError,
    MorphologyNotFoundError,
    SyntaxClauseNotFoundError,
    SyntaxConfidenceError,
    SyntaxConstituentNotFoundError,
    SyntaxCycleError,
    SyntaxFeatureValidationError,
    SyntaxIdentityFirewallError,
    SyntaxImmutabilityError,
    SyntaxLanguageMismatchError,
    SyntaxMorphologyFirewallError,
    SyntaxNotFoundError,
    SyntaxOrphanError,
    SyntaxSemanticsFirewallError,
    SyntaxSpanValidationError,
    SyntaxSubsystemError,
    SyntaxTheologyFirewallError,
    SyntaxTokenNotFoundError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.morphology import (
    GreekMorphologyFeatures,
    GreekPOS,
    GreekTense,
    MorphologyManager,
    MorphologyParse,
)
from bible_engine.provenance import TargetType
from bible_engine.source_registry import (
    SourceAuthorityLevel,
    SourceLanguage,
    SourceRegistry,
    SourceType,
)
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
    SourceTextRecord,
)
from bible_engine.syntax import (
    ClauseDefinition,
    ClauseRecord,
    ClauseRelationToParent,
    ClauseType,
    ConfidenceLevel,
    ConstituentDefinition,
    ConstituentType,
    DependencyRelationDefinition,
    SyntacticConstituentRecord,
    SyntaxAnalyzerConfig,
    SyntaxDependencyRecord,
    SyntaxManager,
    SyntaxModelType,
    SyntaxRelationType,
    SyntaxResult,
    SyntaxRunRecord,
    compute_syntax_output_hash,
    detect_dependency_cycles,
)
from bible_engine.tokenization import TokenizationManager, TokenRecord


class TestBibleEngineSyntax(unittest.TestCase):
    """Rigorous verification suite for Source-Language Syntax Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_syntax.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.morph_mgr = MorphologyManager(self.engine)
        self.syntax_mgr = SyntaxManager(self.engine)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _setup_tokens(
        self,
        source_id: str,
        source_text_id: str,
        language: SourceTextLanguage,
        content: str,
    ) -> Tuple[SourceTextRecord, List[TokenRecord]]:
        """Helper to register source, source text, and tokenize it."""
        self.source_registry.register_source(
            source_id=source_id,
            canonical_name=f"Authoritative Source {source_id}",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage(language.value),
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        st = self.source_text_mgr.register_source_text(
            source_id=source_id,
            source_text_id=source_text_id,
            language=language,
            raw_content=content,
            representation_type=RepresentationType.RAW,
        )
        tok_res = self.token_mgr.tokenize_source_text(st)
        return st, tok_res.tokens

    # -------------------------------------------------------------------------
    # 1. Syntax Registration
    # -------------------------------------------------------------------------
    def test_01_syntax_registration(self) -> None:
        """Register basic syntax run with clause, constituent, and dependency relation."""
        st, tokens = self._setup_tokens("SRC-GNT-01", "ST-SYN-01", SourceTextLanguage.GREEK, "λόγος ἦν")
        tok0, tok1 = tokens[0], tokens[1]

        c = ClauseDefinition(
            clause_id="CLS-01",
            clause_order=0,
            clause_type=ClauseType.INDEPENDENT,
            start_token_id=tok0.token_id,
            end_token_id=tok1.token_id,
            raw_clause_string="λόγος ἦν",
        )
        deps = [
            DependencyRelationDefinition("DEP-01", "CLS-01", dependent_token_id=tok1.token_id, head_token_id=None, relation_type=SyntaxRelationType.ROOT),
            DependencyRelationDefinition("DEP-02", "CLS-01", dependent_token_id=tok0.token_id, head_token_id=tok1.token_id, relation_type=SyntaxRelationType.SUBJECT),
        ]
        consts = [
            ConstituentDefinition("CST-01", "CLS-01", ConstituentType.NOUN_PHRASE, start_token_id=tok0.token_id, end_token_id=tok0.token_id, grammatical_role=SyntaxRelationType.SUBJECT),
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps, consts)
        self.assertIsNotNone(res)
        self.assertEqual(res.run.clause_count, 1)
        self.assertEqual(res.run.dependency_count, 2)
        self.assertEqual(res.run.constituent_count, 1)
        self.assertEqual(len(res.clauses), 1)
        self.assertEqual(len(res.dependencies), 2)
        self.assertEqual(len(res.constituents), 1)

    # -------------------------------------------------------------------------
    # 2. Token Linkage & Nonexistent Token Rejection
    # -------------------------------------------------------------------------
    def test_02_token_linkage_and_nonexistent_token_rejection(self) -> None:
        """Every syntactic relation must resolve to source tokens; referencing unknown token fails."""
        st, tokens = self._setup_tokens("SRC-GNT-02", "ST-SYN-02", SourceTextLanguage.GREEK, "ὁ λόγος")
        tok0 = tokens[0]

        # Nonexistent end_token_id in clause
        with self.assertRaises(SyntaxTokenNotFoundError):
            c_bad = ClauseDefinition(
                clause_id="CLS-BAD",
                clause_order=0,
                clause_type=ClauseType.INDEPENDENT,
                start_token_id=tok0.token_id,
                end_token_id="NONEXISTENT-TOKEN-ID",
                raw_clause_string="ὁ λόγος",
            )
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c_bad], [])

        # Nonexistent dependent_token_id in dependency
        with self.assertRaises(SyntaxTokenNotFoundError):
            c_good = ClauseDefinition(
                clause_id="CLS-GOOD",
                clause_order=0,
                clause_type=ClauseType.INDEPENDENT,
                start_token_id=tok0.token_id,
                end_token_id=tok0.token_id,
                raw_clause_string="ὁ",
            )
            dep_bad = DependencyRelationDefinition(
                "DEP-BAD", "CLS-GOOD",
                dependent_token_id="NONEXISTENT-TOKEN",
                head_token_id=None,
                relation_type=SyntaxRelationType.ROOT,
            )
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c_good], [dep_bad])

    # -------------------------------------------------------------------------
    # 3. Orphan Syntax Rejection
    # -------------------------------------------------------------------------
    def test_03_orphan_syntax_rejection(self) -> None:
        """Attempting to record syntax for nonexistent source text or text without tokens raises error."""
        with self.assertRaises(SyntaxNotFoundError):
            self.syntax_mgr.record_syntax_analysis("NONEXISTENT-SOURCE-TEXT", [], [])

    # -------------------------------------------------------------------------
    # 4. Clause Linkage
    # -------------------------------------------------------------------------
    def test_04_clause_linkage(self) -> None:
        """Constituents and dependencies must reference a valid clause in the run."""
        st, tokens = self._setup_tokens("SRC-GNT-04", "ST-SYN-04", SourceTextLanguage.GREEK, "ἐν ἀρχῇ")
        tok0, tok1 = tokens[0], tokens[1]

        c = ClauseDefinition("CLS-VALID", 0, ClauseType.INDEPENDENT, tok0.token_id, tok1.token_id, "ἐν ἀρχῇ")
        # Dependency references unknown clause
        bad_dep = DependencyRelationDefinition("DEP-ORPHAN", "UNKNOWN-CLAUSE", tok0.token_id, None, SyntaxRelationType.ROOT)
        with self.assertRaises(SyntaxClauseNotFoundError):
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [bad_dep])

        # Constituent references unknown clause
        bad_const = ConstituentDefinition("CST-ORPHAN", "UNKNOWN-CLAUSE", ConstituentType.PREPOSITIONAL_PHRASE, tok0.token_id, tok1.token_id)
        with self.assertRaises(SyntaxClauseNotFoundError):
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [], [bad_const])

    # -------------------------------------------------------------------------
    # 5. Clause Boundary Validation
    # -------------------------------------------------------------------------
    def test_05_clause_boundary_validation(self) -> None:
        """Clause token span boundaries must follow token ordering (start <= end)."""
        st, tokens = self._setup_tokens("SRC-GNT-05", "ST-SYN-05", SourceTextLanguage.GREEK, "πρῶτον δεύτερον")
        tok0, tok1 = tokens[0], tokens[1]

        # Inverted clause boundaries: start is token 1, end is token 0
        with self.assertRaises(SyntaxSpanValidationError):
            inverted_c = ClauseDefinition("CLS-INV", 0, ClauseType.INDEPENDENT, tok1.token_id, tok0.token_id, "inverted")
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [inverted_c], [])

    # -------------------------------------------------------------------------
    # 6. Dependency Relation Validation
    # -------------------------------------------------------------------------
    def test_06_dependency_relation_validation(self) -> None:
        """Supports explicit relation types required by specification."""
        st, tokens = self._setup_tokens("SRC-GNT-06", "ST-SYN-06", SourceTextLanguage.GREEK, "ὁ πατὴρ φιλεῖ τὸν υἱόν")
        # tokens: [ὁ, πατὴρ, φιλεῖ, τὸν, υἱόν]
        c = ClauseDefinition("CLS-REL-01", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[4].token_id, "ὁ πατὴρ φιλεῖ τὸν υἱόν")

        deps = [
            DependencyRelationDefinition("D1", "CLS-REL-01", tokens[2].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("D2", "CLS-REL-01", tokens[1].token_id, tokens[2].token_id, SyntaxRelationType.SUBJECT),
            DependencyRelationDefinition("D3", "CLS-REL-01", tokens[0].token_id, tokens[1].token_id, SyntaxRelationType.DETERMINER),
            DependencyRelationDefinition("D4", "CLS-REL-01", tokens[4].token_id, tokens[2].token_id, SyntaxRelationType.OBJECT),
            DependencyRelationDefinition("D5", "CLS-REL-01", tokens[3].token_id, tokens[4].token_id, SyntaxRelationType.DETERMINER),
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps)
        dep_types = {d.relation_type for d in res.dependencies}
        self.assertIn(SyntaxRelationType.ROOT, dep_types)
        self.assertIn(SyntaxRelationType.SUBJECT, dep_types)
        self.assertIn(SyntaxRelationType.OBJECT, dep_types)
        self.assertIn(SyntaxRelationType.DETERMINER, dep_types)

    # -------------------------------------------------------------------------
    # 7. Constituent Span Validation
    # -------------------------------------------------------------------------
    def test_07_constituent_span_validation(self) -> None:
        """Constituent spans must adhere to token order and can represent hierarchical phrases."""
        st, tokens = self._setup_tokens("SRC-GNT-07", "ST-SYN-07", SourceTextLanguage.GREEK, "ἐν τῇ ἀρχῇ")
        c = ClauseDefinition("CLS-CST-01", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[2].token_id, "ἐν τῇ ἀρχῇ")

        # Inverted span should fail
        with self.assertRaises(SyntaxSpanValidationError):
            bad_cst = ConstituentDefinition("CST-BAD", "CLS-CST-01", ConstituentType.PREPOSITIONAL_PHRASE, tokens[2].token_id, tokens[0].token_id)
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [], [bad_cst])

        # Valid hierarchical constituents: PP containing NP
        pp = ConstituentDefinition("CST-PP", "CLS-CST-01", ConstituentType.PREPOSITIONAL_PHRASE, tokens[0].token_id, tokens[2].token_id, grammatical_role=SyntaxRelationType.ADJUNCT)
        np = ConstituentDefinition("CST-NP", "CLS-CST-01", ConstituentType.NOUN_PHRASE, tokens[1].token_id, tokens[2].token_id, parent_constituent_id="CST-PP", grammatical_role=SyntaxRelationType.PREPOSITIONAL_COMPLEMENT)

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [], [pp, np])
        self.assertEqual(len(res.constituents), 2)
        consts_from_db = self.syntax_mgr.get_constituents_for_clause("CLS-CST-01")
        self.assertEqual(len(consts_from_db), 2)

    # -------------------------------------------------------------------------
    # 8. Multiple Competing Parses
    # -------------------------------------------------------------------------
    def test_08_multiple_competing_parses(self) -> None:
        """Syntax supports competing analyses without overwriting (parse_index 0 vs 1)."""
        st, tokens = self._setup_tokens("SRC-GNT-08", "ST-SYN-08", SourceTextLanguage.GREEK, "λόγος σὰρξ ἐγένετο")
        c = ClauseDefinition("CLS-ALT", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[2].token_id, "λόγος σὰρξ ἐγένετο")

        # Competing parses for σὰρξ (tokens[1]):
        # Parse 0: PREDICATE (preferred)
        # Parse 1: SUBJECT (alternative)
        p0 = DependencyRelationDefinition("DEP-P0", "CLS-ALT", tokens[1].token_id, tokens[2].token_id, SyntaxRelationType.PREDICATE, parse_index=0, is_preferred=True)
        p1 = DependencyRelationDefinition("DEP-P1", "CLS-ALT", tokens[1].token_id, tokens[2].token_id, SyntaxRelationType.SUBJECT, parse_index=1, is_preferred=False)

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [p0, p1])
        self.assertEqual(len(res.dependencies), 2)

        # Retrieve both parses
        all_deps = self.syntax_mgr.get_dependencies_for_token(tokens[1].token_id, run_id=res.run.run_id)
        self.assertEqual(len(all_deps), 2)
        self.assertEqual(all_deps[0].parse_index, 0)
        self.assertEqual(all_deps[0].relation_type, SyntaxRelationType.PREDICATE)
        self.assertEqual(all_deps[1].parse_index, 1)
        self.assertEqual(all_deps[1].relation_type, SyntaxRelationType.SUBJECT)

    # -------------------------------------------------------------------------
    # 9. Preferred Parse Separation
    # -------------------------------------------------------------------------
    def test_09_preferred_parse_separation(self) -> None:
        """Preferred parse is distinguishable and queryable separately from alternative parses."""
        st, tokens = self._setup_tokens("SRC-GNT-09", "ST-SYN-09", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-PREF", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")

        p0 = DependencyRelationDefinition("DEP-PREF-0", "CLS-PREF", tokens[0].token_id, None, SyntaxRelationType.ROOT, parse_index=0, is_preferred=True)
        p1 = DependencyRelationDefinition("DEP-PREF-1", "CLS-PREF", tokens[0].token_id, None, SyntaxRelationType.VOCATIVE, parse_index=1, is_preferred=False)

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [p0, p1])

        # Fetch only preferred
        pref_deps = self.syntax_mgr.get_dependencies_for_clause("CLS-PREF", is_preferred_only=True)
        self.assertEqual(len(pref_deps), 1)
        self.assertEqual(pref_deps[0].relation_type, SyntaxRelationType.ROOT)
        self.assertTrue(pref_deps[0].is_preferred)

        # Fetch all
        all_deps = self.syntax_mgr.get_dependencies_for_clause("CLS-PREF", is_preferred_only=False)
        self.assertEqual(len(all_deps), 2)

    # -------------------------------------------------------------------------
    # 10. Greek Syntax
    # -------------------------------------------------------------------------
    def test_10_greek_syntax(self) -> None:
        """Hellenistic Greek syntax parsing with copula and modifier."""
        st, tokens = self._setup_tokens("SRC-GNT-10", "ST-SYN-10", SourceTextLanguage.GREEK, "καὶ θεὸς ἦν ὁ λόγος")
        c = ClauseDefinition("CLS-GNT-10", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[4].token_id, "καὶ θεὸς ἦν ὁ λόγος")

        deps = [
            DependencyRelationDefinition("D-10-1", "CLS-GNT-10", tokens[2].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("D-10-2", "CLS-GNT-10", tokens[0].token_id, tokens[2].token_id, SyntaxRelationType.CONJUNCT),
            DependencyRelationDefinition("D-10-3", "CLS-GNT-10", tokens[1].token_id, tokens[2].token_id, SyntaxRelationType.PREDICATE),
            DependencyRelationDefinition("D-10-4", "CLS-GNT-10", tokens[4].token_id, tokens[2].token_id, SyntaxRelationType.SUBJECT),
            DependencyRelationDefinition("D-10-5", "CLS-GNT-10", tokens[3].token_id, tokens[4].token_id, SyntaxRelationType.DETERMINER),
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps)
        self.assertEqual(res.run.language, SourceTextLanguage.GREEK)
        self.assertEqual(res.run.dependency_count, 5)

    # -------------------------------------------------------------------------
    # 11. Hebrew Syntax
    # -------------------------------------------------------------------------
    def test_11_hebrew_syntax(self) -> None:
        """Biblical Hebrew syntax parsing with construct chains and verbal predicates."""
        st, tokens = self._setup_tokens("SRC-WLC-11", "ST-SYN-11", SourceTextLanguage.HEBREW, "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם")
        c = ClauseDefinition("CLS-HEB-11", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[-1].token_id, "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם")

        deps = [
            DependencyRelationDefinition("DH-1", "CLS-HEB-11", tokens[1].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("DH-2", "CLS-HEB-11", tokens[0].token_id, tokens[1].token_id, SyntaxRelationType.ADJUNCT),
            DependencyRelationDefinition("DH-3", "CLS-HEB-11", tokens[2].token_id, tokens[1].token_id, SyntaxRelationType.SUBJECT),
            DependencyRelationDefinition("DH-4", "CLS-HEB-11", tokens[4].token_id, tokens[1].token_id, SyntaxRelationType.OBJECT),
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps)
        self.assertEqual(res.run.language, SourceTextLanguage.HEBREW)
        self.assertEqual(res.run.dependency_count, 4)

    # -------------------------------------------------------------------------
    # 12. Aramaic Syntax
    # -------------------------------------------------------------------------
    def test_12_aramaic_syntax(self) -> None:
        """Biblical Aramaic syntax parsing."""
        st, tokens = self._setup_tokens("SRC-ARM-12", "ST-SYN-12", SourceTextLanguage.ARAMAIC, "לֶהֱוֵא שְׁמֵהּ דִּי אֱלָהָא מְבָרַךְ")
        c = ClauseDefinition("CLS-ARM-12", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[-1].token_id, "לֶהֱוֵא שְׁמֵהּ דִּי אֱלָהָא מְבָרַךְ")

        deps = [
            DependencyRelationDefinition("DA-1", "CLS-ARM-12", tokens[0].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("DA-2", "CLS-ARM-12", tokens[1].token_id, tokens[0].token_id, SyntaxRelationType.SUBJECT),
            DependencyRelationDefinition("DA-3", "CLS-ARM-12", tokens[4].token_id, tokens[0].token_id, SyntaxRelationType.PREDICATE),
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps)
        self.assertEqual(res.run.language, SourceTextLanguage.ARAMAIC)

    # -------------------------------------------------------------------------
    # 13. Morphology Firewall
    # -------------------------------------------------------------------------
    def test_13_morphology_firewall(self) -> None:
        """Syntax operations MUST NOT mutate or overwrite morphology records."""
        st, tokens = self._setup_tokens("SRC-GNT-13", "ST-SYN-13", SourceTextLanguage.GREEK, "λόγος")
        tok = tokens[0]

        # Ingest morphology parse first
        m_parse = MorphologyParse(
            parse_index=0,
            pos_tag="N-NSM",
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN, tense=None),
        )
        m_res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [m_parse])])
        orig_morph = self.morph_mgr.get_parses_for_token(tok.token_id)[0]

        # Record syntax referencing morphology run
        c = ClauseDefinition("CLS-MFIRE", 0, ClauseType.INDEPENDENT, tok.token_id, tok.token_id, "λόγος")
        dep = DependencyRelationDefinition(
            "DEP-MFIRE", "CLS-MFIRE",
            dependent_token_id=tok.token_id,
            head_token_id=None,
            relation_type=SyntaxRelationType.ROOT,
            morphology_annotation_id=orig_morph.annotation_id,
        )
        self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep], morphology_run_id=m_res.run.run_id)

        # Assert morphology was NOT altered in any column
        post_morph = self.morph_mgr.get_parses_for_token(tok.token_id)[0]
        self.assertEqual(orig_morph.to_dict(), post_morph.to_dict())

    # -------------------------------------------------------------------------
    # 14. Semantic Firewall
    # -------------------------------------------------------------------------
    def test_14_semantic_firewall(self) -> None:
        """Syntax must NOT automatically infer semantic roles (e.g. OBJECT != thing possessed)."""
        st, tokens = self._setup_tokens("SRC-GNT-14", "ST-SYN-14", SourceTextLanguage.GREEK, "ἔχει βιβλίον")
        c = ClauseDefinition("CLS-SEM", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[1].token_id, "ἔχει βιβλίον")
        dep = DependencyRelationDefinition("DEP-SEM", "CLS-SEM", tokens[1].token_id, tokens[0].token_id, SyntaxRelationType.OBJECT)

        self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep])

        # Verify semantic_senses table has 0 rows inserted
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cnt = cur.execute("SELECT count(*) FROM semantic_senses;").fetchone()[0]
            self.assertEqual(cnt, 0)

    # -------------------------------------------------------------------------
    # 15. Theology Firewall
    # -------------------------------------------------------------------------
    def test_15_theology_firewall(self) -> None:
        """Syntax analysis must NEVER directly generate T3 or T4 theological claims."""
        st, tokens = self._setup_tokens("SRC-GNT-15", "ST-SYN-15", SourceTextLanguage.GREEK, "θεὸς ἦν ὁ λόγος")
        c = ClauseDefinition("CLS-THEO", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[-1].token_id, "θεὸς ἦν ὁ λόγος")
        deps = [
            DependencyRelationDefinition("DT-1", "CLS-THEO", tokens[1].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("DT-2", "CLS-THEO", tokens[0].token_id, tokens[1].token_id, SyntaxRelationType.PREDICATE),
            DependencyRelationDefinition("DT-3", "CLS-THEO", tokens[3].token_id, tokens[1].token_id, SyntaxRelationType.SUBJECT),
        ]
        self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps)

        with self.engine.connect() as conn:
            cur = conn.cursor()
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            if "evidence_claims" in tables:
                cnt = cur.execute("SELECT count(*) FROM evidence_claims;").fetchone()[0]
                self.assertEqual(cnt, 0)

    # -------------------------------------------------------------------------
    # 16. Identity Firewall
    # -------------------------------------------------------------------------
    def test_16_identity_firewall(self) -> None:
        """Syntax must NOT automatically establish identity (APPOSITION != STRICT_IDENTITY)."""
        st, tokens = self._setup_tokens("SRC-GNT-16", "ST-SYN-16", SourceTextLanguage.GREEK, "Ἰησοῦς Χριστός")
        c = ClauseDefinition("CLS-ID-16", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[1].token_id, "Ἰησοῦς Χριστός")
        dep = DependencyRelationDefinition("DEP-ID-16", "CLS-ID-16", tokens[1].token_id, tokens[0].token_id, SyntaxRelationType.APPOSITION)

        self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep])

        # Assert no STRICT_IDENTITY was inserted in referential_relations
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cnt = cur.execute("SELECT count(*) FROM referential_relations WHERE relation_type = 'STRICT_IDENTITY';").fetchone()[0]
            self.assertEqual(cnt, 0)

    # -------------------------------------------------------------------------
    # 17. Ambiguity Preservation
    # -------------------------------------------------------------------------
    def test_17_ambiguity_preservation(self) -> None:
        """Preserve syntactic ambiguity: candidate, preferred, confidence, and evidence remain distinct."""
        st, tokens = self._setup_tokens("SRC-GNT-17", "ST-SYN-17", SourceTextLanguage.GREEK, "λόγῳ")
        c = ClauseDefinition("CLS-AMB", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγῳ")

        d0 = DependencyRelationDefinition("DEP-AMB-0", "CLS-AMB", tokens[0].token_id, None, SyntaxRelationType.ROOT, parse_index=0, is_preferred=True, confidence_score=0.6, confidence_level=ConfidenceLevel.HIGH, evidence_ref="Grammar §101")
        d1 = DependencyRelationDefinition("DEP-AMB-1", "CLS-AMB", tokens[0].token_id, None, SyntaxRelationType.ADJUNCT, parse_index=1, is_preferred=False, confidence_score=0.4, confidence_level=ConfidenceLevel.AMBIGUOUS, evidence_ref="Grammar §102")

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [d0, d1])
        self.assertEqual(len(res.dependencies), 2)
        self.assertEqual(res.dependencies[0].confidence_score, 0.6)
        self.assertEqual(res.dependencies[1].confidence_score, 0.4)
        self.assertEqual(res.dependencies[0].evidence_ref, "Grammar §101")
        self.assertEqual(res.dependencies[1].evidence_ref, "Grammar §102")

    # -------------------------------------------------------------------------
    # 18. Provenance Integration (Deterministic)
    # -------------------------------------------------------------------------
    def test_18_provenance_integration_deterministic(self) -> None:
        """Deterministic syntax analysis produces SHA-256 cryptographic provenance."""
        st, tokens = self._setup_tokens("SRC-GNT-18", "ST-SYN-18", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-DET", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        dep = DependencyRelationDefinition("DEP-DET", "CLS-DET", tokens[0].token_id, None, SyntaxRelationType.ROOT)

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep])
        prov = self.syntax_mgr.provenance_tracker.get_record(res.run.provenance_id)
        self.assertIsNotNone(prov)
        self.assertTrue(res.run.is_exact_reproducible)

    # -------------------------------------------------------------------------
    # 19. Provenance Integration (Generative)
    # -------------------------------------------------------------------------
    def test_19_provenance_integration_generative(self) -> None:
        """Generative / LLM parser marked non-exactly reproducible in provenance."""
        st, tokens = self._setup_tokens("SRC-GNT-19", "ST-SYN-19", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-GEN", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        dep = DependencyRelationDefinition("DEP-GEN", "CLS-GEN", tokens[0].token_id, None, SyntaxRelationType.ROOT)

        cfg = SyntaxAnalyzerConfig(analyzer_id="claude-3-5-sonnet", is_deterministic=False)
        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep], config=cfg)
        self.assertFalse(res.run.is_exact_reproducible)

    # -------------------------------------------------------------------------
    # 20. Versioning & Superseding
    # -------------------------------------------------------------------------
    def test_20_versioning_and_superseding(self) -> None:
        """Reanalysis produces new version and supersedes prior version without data loss."""
        st, tokens = self._setup_tokens("SRC-GNT-20", "ST-SYN-20", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-V1", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        dep1 = DependencyRelationDefinition("DEP-V1", "CLS-V1", tokens[0].token_id, None, SyntaxRelationType.ROOT)

        cfg1 = SyntaxAnalyzerConfig(analyzer_version="1.0.0")
        res1 = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep1], config=cfg1)

        # Reanalyze with v2.0.0
        cfg2 = SyntaxAnalyzerConfig(analyzer_version="2.0.0")
        c2 = ClauseDefinition("CLS-V2", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        dep2 = DependencyRelationDefinition("DEP-V2", "CLS-V2", tokens[0].token_id, None, SyntaxRelationType.ROOT)
        res2 = self.syntax_mgr.reanalyze(st.source_text_id, [c2], [dep2], new_config=cfg2)

        self.assertNotEqual(res1.run.run_id, res2.run.run_id)
        # Verify both runs are retrievable
        self.assertIsNotNone(self.syntax_mgr.get_syntax_run(res1.run.run_id))
        self.assertIsNotNone(self.syntax_mgr.get_syntax_run(res2.run.run_id))

    # -------------------------------------------------------------------------
    # 21. Immutability Triggers
    # -------------------------------------------------------------------------
    def test_21_immutability_triggers(self) -> None:
        """Database triggers prevent UPDATE or DELETE on syntax runs, clauses, constituents, dependencies."""
        st, tokens = self._setup_tokens("SRC-GNT-21", "ST-SYN-21", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-IMM", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        dep = DependencyRelationDefinition("DEP-IMM", "CLS-IMM", tokens[0].token_id, None, SyntaxRelationType.ROOT)
        const = ConstituentDefinition("CST-IMM", "CLS-IMM", ConstituentType.NOUN_PHRASE, tokens[0].token_id, tokens[0].token_id)

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [dep], [const])

        with self.engine.transaction() as conn:
            # Attempt to delete syntax run
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM syntax_runs WHERE run_id = ?;", (res.run.run_id,))

            # Attempt to update clause
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE clauses SET clause_type = 'OTHER' WHERE clause_id = 'CLS-IMM';")

            # Attempt to delete constituent
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM syntactic_constituents WHERE constituent_id = 'CST-IMM';")

            # Attempt to delete dependency
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM syntax_dependencies WHERE dependency_id = 'DEP-IMM';")

    # -------------------------------------------------------------------------
    # 22. Atomic Rollback
    # -------------------------------------------------------------------------
    def test_22_atomic_rollback(self) -> None:
        """Transactions roll back cleanly on error with zero orphaned rows."""
        st, tokens = self._setup_tokens("SRC-GNT-22", "ST-SYN-22", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-RB", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        # Self-loop cycle causes failure
        bad_dep = DependencyRelationDefinition("DEP-CYCLE", "CLS-RB", tokens[0].token_id, tokens[0].token_id, SyntaxRelationType.ROOT)

        with self.assertRaises(SyntaxCycleError):
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [bad_dep])

        with self.engine.connect() as conn:
            cur = conn.cursor()
            cnt_runs = cur.execute("SELECT count(*) FROM syntax_runs;").fetchone()[0]
            cnt_clauses = cur.execute("SELECT count(*) FROM clauses;").fetchone()[0]
            self.assertEqual(cnt_runs, 0)
            self.assertEqual(cnt_clauses, 0)

    # -------------------------------------------------------------------------
    # 23. Concurrent Syntax Runs
    # -------------------------------------------------------------------------
    def test_23_concurrent_syntax_runs(self) -> None:
        """Two independent runs with different configurations coexist without collision."""
        st, tokens = self._setup_tokens("SRC-GNT-23", "ST-SYN-23", SourceTextLanguage.GREEK, "λόγος")
        c1 = ClauseDefinition("CLS-A", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        d1 = DependencyRelationDefinition("DEP-A", "CLS-A", tokens[0].token_id, None, SyntaxRelationType.ROOT)

        c2 = ClauseDefinition("CLS-B", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")
        d2 = DependencyRelationDefinition("DEP-B", "CLS-B", tokens[0].token_id, None, SyntaxRelationType.ROOT)

        cfg1 = SyntaxAnalyzerConfig(analyzer_id="parser-A")
        cfg2 = SyntaxAnalyzerConfig(analyzer_id="parser-B")

        res1 = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c1], [d1], config=cfg1)
        res2 = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c2], [d2], config=cfg2)

        self.assertNotEqual(res1.run.run_id, res2.run.run_id)

    # -------------------------------------------------------------------------
    # 24. Cycle Validation
    # -------------------------------------------------------------------------
    def test_24_cycle_validation(self) -> None:
        """Rejects illegal cycles (self-loop, 2-node cycle, 3-node cycle)."""
        st, tokens = self._setup_tokens("SRC-GNT-24", "ST-SYN-24", SourceTextLanguage.GREEK, "α β γ")
        t0, t1, t2 = tokens[0], tokens[1], tokens[2]
        c = ClauseDefinition("CLS-CYC", 0, ClauseType.INDEPENDENT, t0.token_id, t2.token_id, "α β γ")

        # 24a. Self-loop: A -> A
        with self.assertRaises(SyntaxCycleError):
            self.syntax_mgr.record_syntax_analysis(
                st.source_text_id, [c],
                [DependencyRelationDefinition("D-LOOP", "CLS-CYC", t0.token_id, t0.token_id, SyntaxRelationType.MODIFIER)],
            )

        # 24b. 2-node cycle: A -> B and B -> A
        with self.assertRaises(SyntaxCycleError):
            self.syntax_mgr.record_syntax_analysis(
                st.source_text_id, [c],
                [
                    DependencyRelationDefinition("D-2A", "CLS-CYC", t0.token_id, t1.token_id, SyntaxRelationType.MODIFIER),
                    DependencyRelationDefinition("D-2B", "CLS-CYC", t1.token_id, t0.token_id, SyntaxRelationType.MODIFIER),
                ],
            )

        # 24c. 3-node cycle: A -> B -> C -> A
        with self.assertRaises(SyntaxCycleError):
            self.syntax_mgr.record_syntax_analysis(
                st.source_text_id, [c],
                [
                    DependencyRelationDefinition("D-3A", "CLS-CYC", t1.token_id, t0.token_id, SyntaxRelationType.MODIFIER),
                    DependencyRelationDefinition("D-3B", "CLS-CYC", t2.token_id, t1.token_id, SyntaxRelationType.MODIFIER),
                    DependencyRelationDefinition("D-3C", "CLS-CYC", t0.token_id, t2.token_id, SyntaxRelationType.MODIFIER),
                ],
            )

    # -------------------------------------------------------------------------
    # 25. Source Reconstruction Integrity
    # -------------------------------------------------------------------------
    def test_25_source_reconstruction_integrity(self) -> None:
        """Recomputing hash from database rows yields exact match with run output_hash."""
        st, tokens = self._setup_tokens("SRC-GNT-25", "ST-SYN-25", SourceTextLanguage.GREEK, "λόγος ἦν")
        c = ClauseDefinition("CLS-25", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[1].token_id, "λόγος ἦν")
        deps = [
            DependencyRelationDefinition("D-25-1", "CLS-25", tokens[1].token_id, None, SyntaxRelationType.ROOT),
            DependencyRelationDefinition("D-25-2", "CLS-25", tokens[0].token_id, tokens[1].token_id, SyntaxRelationType.SUBJECT),
        ]
        consts = [
            ConstituentDefinition("C-25-1", "CLS-25", ConstituentType.NOUN_PHRASE, tokens[0].token_id, tokens[0].token_id, grammatical_role=SyntaxRelationType.SUBJECT)
        ]

        res = self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], deps, consts)

        from_db_c = self.syntax_mgr.get_clauses_for_run(res.run.run_id)
        from_db_d = self.syntax_mgr.get_dependencies_for_clause("CLS-25")
        from_db_k = self.syntax_mgr.get_constituents_for_clause("CLS-25")

        db_hash = compute_syntax_output_hash(from_db_c, from_db_d, from_db_k)
        self.assertEqual(res.run.output_hash, db_hash)

    # -------------------------------------------------------------------------
    # 26. Legacy Database Untouched
    # -------------------------------------------------------------------------
    def test_26_legacy_db_untouched(self) -> None:
        """Verifies legacy database /home/ubuntu/.polya/polya_index.db is untouched."""
        path = "/home/ubuntu/.polya/polya_index.db"
        if os.path.exists(path):
            stat = os.stat(path)
            self.assertEqual(stat.st_size, 12365824)

    # -------------------------------------------------------------------------
    # 27. Adversarial: Out-of-bounds Confidence Scores
    # -------------------------------------------------------------------------
    def test_27_adversarial_invalid_confidence(self) -> None:
        """Confidence score outside [0.0, 1.0] must be rejected."""
        st, tokens = self._setup_tokens("SRC-GNT-27", "ST-SYN-27", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-ADV", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")

        # Confidence > 1.0
        with self.assertRaises(SyntaxConfidenceError):
            bad_dep1 = DependencyRelationDefinition("DEP-C1", "CLS-ADV", tokens[0].token_id, None, SyntaxRelationType.ROOT, confidence_score=1.5)
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [bad_dep1])

        # Confidence < 0.0
        with self.assertRaises(SyntaxConfidenceError):
            bad_dep2 = DependencyRelationDefinition("DEP-C2", "CLS-ADV", tokens[0].token_id, None, SyntaxRelationType.ROOT, confidence_score=-0.1)
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [bad_dep2])

    # -------------------------------------------------------------------------
    # 28. Adversarial: Duplicate Parse Index Rejection
    # -------------------------------------------------------------------------
    def test_28_adversarial_duplicate_parse_index(self) -> None:
        """Submitting duplicate parse_index for same token/clause raises DuplicateSyntaxError."""
        st, tokens = self._setup_tokens("SRC-GNT-28", "ST-SYN-28", SourceTextLanguage.GREEK, "λόγος")
        c = ClauseDefinition("CLS-DUP", 0, ClauseType.INDEPENDENT, tokens[0].token_id, tokens[0].token_id, "λόγος")

        d1 = DependencyRelationDefinition("D1", "CLS-DUP", tokens[0].token_id, None, SyntaxRelationType.ROOT, parse_index=0)
        d2 = DependencyRelationDefinition("D2", "CLS-DUP", tokens[0].token_id, None, SyntaxRelationType.SUBJECT, parse_index=0)

        with self.assertRaises(DuplicateSyntaxError):
            self.syntax_mgr.record_syntax_analysis(st.source_text_id, [c], [d1, d2])

    # -------------------------------------------------------------------------
    # 29. Adversarial: Cross-Language / Mismatched Morphology Run Rejection
    # -------------------------------------------------------------------------
    def test_29_adversarial_cross_language_morphology_link(self) -> None:
        """Linking a morphology run from a different source text raises SyntaxLanguageMismatchError."""
        st_greek, tok_g = self._setup_tokens("SRC-GNT-29", "ST-G-29", SourceTextLanguage.GREEK, "λόγος")
        st_heb, tok_h = self._setup_tokens("SRC-WLC-29", "ST-H-29", SourceTextLanguage.HEBREW, "שָׁלוֹם")

        # Ingest Greek morphology
        m_parse = MorphologyParse(parse_index=0, pos_tag="N-NSM")
        m_res = self.morph_mgr.record_morphology_parses(st_greek.source_text_id, [(tok_g[0], [m_parse])])

        # Attempt to link Greek morphology to Hebrew syntax run
        c_heb = ClauseDefinition("CLS-HEB-29", 0, ClauseType.INDEPENDENT, tok_h[0].token_id, tok_h[0].token_id, "שָׁלוֹם")
        dep_heb = DependencyRelationDefinition("D-H-29", "CLS-HEB-29", tok_h[0].token_id, None, SyntaxRelationType.ROOT)

        with self.assertRaises(SyntaxLanguageMismatchError):
            self.syntax_mgr.record_syntax_analysis(
                st_heb.source_text_id, [c_heb], [dep_heb], morphology_run_id=m_res.run.run_id
            )

    # -------------------------------------------------------------------------
    # 30. Migration 008 Legacy Clause Data Preservation
    # -------------------------------------------------------------------------
    def test_30_migration_008_legacy_clause_preservation(self) -> None:
        """Migration 008 preserves legacy clause records and does not delete them."""
        legacy_engine = DatabaseEngine(DatabaseConfig(db_path=":memory:"))
        with legacy_engine.connect() as conn:
            for p in sorted(pathlib.Path("schemas/bible_engine").glob("*.sql")):
                if p.name.startswith(("001", "002", "003", "004", "005", "006", "007")):
                    content = p.read_text(encoding="utf-8")
                    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    conn.executescript(content)
                    conn.execute(
                        "INSERT INTO schema_migrations (migration_id, version, checksum_sha256, description, applied_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        (p.stem, "2.0.0", sha, "desc"),
                    )

        srm = SourceRegistry(legacy_engine)
        srm.register_source(
            source_id="SRC-LEG-SYN",
            canonical_name="Legacy Source",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        stm = SourceTextManager(legacy_engine)
        st_leg = stm.register_source_text(
            source_id="SRC-LEG-SYN",
            source_text_id="ST-LEG-SYN",
            language=SourceTextLanguage.GREEK,
            raw_content="ἀρχὴ λόγου",
            representation_type=RepresentationType.RAW,
        )
        tokens_leg = TokenizationManager(legacy_engine).tokenize_source_text(st_leg).tokens

        # Insert legacy clause into 001 clauses table with complete foreign-key lineage
        with legacy_engine.transaction() as conn:
            conn.execute(
                "INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-TEST', 'Test Canon', CURRENT_TIMESTAMP);"
            )
            conn.execute(
                "INSERT INTO testaments (testament_id, canon_id, name, sort_order) VALUES ('TEST-NT', 'CANON-TEST', 'NT', 1);"
            )
            conn.execute(
                "INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count) VALUES ('REV', 'TEST-NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) VALUES ('PER-TEST', 'REV', 'Wahyu 19:8', 19, 8, 19, 8, 'APOCALYPTIC', 'NA28', 'HIGH', 'REGISTERED', '1.0', CURRENT_TIMESTAMP);"
            )
            conn.execute(
                "INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) VALUES ('REV.19.8', 'PER-TEST', 'REV', 19, 8, 1);"
            )
            conn.execute(
                """INSERT INTO clauses (clause_id, passage_id, clause_order, clause_type, raw_clause_string)
                VALUES ('CLS-LEGACY-TEST', 'REV.19.8', 1, 'INDEPENDENT', 'ἀρχὴ λόγου');"""
            )
            # Link token to passage_id for migration join
            conn.execute("UPDATE tokens SET passage_id = 'REV.19.8' WHERE token_id = ?;", (tokens_leg[0].token_id,))

        with legacy_engine.connect() as conn:
            cnt_before = conn.execute("SELECT count(*) FROM clauses;").fetchone()[0]
            self.assertEqual(cnt_before, 1)

        runner = MigrationRunner(legacy_engine)
        runner.apply_pending()

        with legacy_engine.connect() as conn:
            cnt_after = conn.execute("SELECT count(*) FROM clauses;").fetchone()[0]
            self.assertEqual(cnt_after, 1)
            row = conn.execute("SELECT * FROM clauses WHERE clause_id = 'CLS-LEGACY-TEST';").fetchone()
            self.assertEqual(row["run_id"], "RUN-MIGRATION-LEGACY-SYNTAX")
            self.assertEqual(row["raw_clause_string"], "ἀρχὴ λόγου")

    def test_31_forward_referencing_parent_child_hierarchy(self) -> None:
        """Verify subordinate clause appearing before parent clause succeeds with deferred foreign keys."""
        st, tokens = self._setup_tokens("SRC-FWD", "ST-FWD", SourceTextLanguage.GREEK, "ἐὰν ᾖ ὁ λόγος ἦν")
        c_sub = ClauseDefinition(
            clause_id="CLS-SUB-PROTASIS",
            clause_order=0,
            clause_type=ClauseType.CONDITIONAL_PROTASIS,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[1].token_id,
            raw_clause_string="ἐὰν ᾖ",
            parent_clause_id="CLS-MAIN-APODOSIS",
            relation_to_parent=ClauseRelationToParent.SUBORDINATION,
        )
        c_main = ClauseDefinition(
            clause_id="CLS-MAIN-APODOSIS",
            clause_order=1,
            clause_type=ClauseType.CONDITIONAL_APODOSIS,
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[4].token_id,
            raw_clause_string="ὁ λόγος ἦν",
        )
        d_sub = DependencyRelationDefinition(
            dependency_id="DEP-SUB-ROOT",
            clause_id="CLS-SUB-PROTASIS",
            dependent_token_id=tokens[0].token_id,
            head_token_id=None,
            relation_type=SyntaxRelationType.ROOT,
        )
        d_main = DependencyRelationDefinition(
            dependency_id="DEP-MAIN-ROOT",
            clause_id="CLS-MAIN-APODOSIS",
            dependent_token_id=tokens[4].token_id,
            head_token_id=None,
            relation_type=SyntaxRelationType.ROOT,
        )
        res = self.syntax_mgr.record_syntax_analysis(
            source_text_id=st.source_text_id,
            clauses=[c_sub, c_main],
            dependencies=[d_sub, d_main],
        )
        self.assertEqual(len(res.clauses), 2)
        saved_sub = [c for c in res.clauses if c.clause_id == "CLS-SUB-PROTASIS"][0]
        self.assertEqual(saved_sub.parent_clause_id, "CLS-MAIN-APODOSIS")

    def test_32_parent_validation_raises_expected_errors(self) -> None:
        """Verify invalid parent_clause_id or parent_constituent_id raises specific NotFoundError."""
        st, tokens = self._setup_tokens("SRC-PVAL", "ST-PVAL", SourceTextLanguage.GREEK, "λόγος ἦν")
        c_invalid = ClauseDefinition(
            clause_id="CLS-ORPHAN-CHILD",
            clause_order=0,
            clause_type=ClauseType.SUBORDINATE_CAUSAL,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[1].token_id,
            raw_clause_string="test",
            parent_clause_id="CLS-DOES-NOT-EXIST",
        )
        with self.assertRaises(SyntaxClauseNotFoundError):
            self.syntax_mgr.record_syntax_analysis(
                source_text_id=st.source_text_id,
                clauses=[c_invalid],
                dependencies=[],
            )

        c_valid = ClauseDefinition(
            clause_id="CLS-VALID-PARENT",
            clause_order=0,
            clause_type=ClauseType.INDEPENDENT,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[1].token_id,
            raw_clause_string="test",
        )
        k_invalid = ConstituentDefinition(
            constituent_id="CST-INVALID-CHILD",
            clause_id="CLS-VALID-PARENT",
            constituent_type=ConstituentType.NOUN_PHRASE,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[1].token_id,
            parent_constituent_id="CST-DOES-NOT-EXIST",
        )
        with self.assertRaises(SyntaxConstituentNotFoundError):
            self.syntax_mgr.record_syntax_analysis(
                source_text_id=st.source_text_id,
                clauses=[c_valid],
                dependencies=[],
                constituents=[k_invalid],
            )

    def test_33_constituent_grammatical_role_all_extended_values(self) -> None:
        """Verify all extended SyntaxRelationType values can be stored as constituent grammatical roles."""
        st, tokens = self._setup_tokens("SRC-EXT", "ST-EXT", SourceTextLanguage.GREEK, "Ἐν ἀρχῇ ἦν ὁ λόγος")
        c = ClauseDefinition(
            clause_id="CLS-ROLE-TEST",
            clause_order=0,
            clause_type=ClauseType.INDEPENDENT,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[4].token_id,
            raw_clause_string="Ἐν ἀρχῇ ἦν ὁ λόγος",
        )
        extended_roles = [
            SyntaxRelationType.SPECIFIER,
            SyntaxRelationType.CONJUNCT,
            SyntaxRelationType.COPULA,
            SyntaxRelationType.DETERMINER,
            SyntaxRelationType.ADVERBIAL,
        ]
        constituents = [
            ConstituentDefinition(
                constituent_id=f"CST-EXT-{idx}",
                clause_id="CLS-ROLE-TEST",
                constituent_type=ConstituentType.NOUN_PHRASE,
                start_token_id=tokens[idx].token_id,
                end_token_id=tokens[idx].token_id,
                grammatical_role=role,
            )
            for idx, role in enumerate(extended_roles)
        ]
        res = self.syntax_mgr.record_syntax_analysis(
            source_text_id=st.source_text_id,
            clauses=[c],
            dependencies=[],
            constituents=constituents,
        )
        self.assertEqual(len(res.constituents), 5)


if __name__ == "__main__":
    unittest.main()

