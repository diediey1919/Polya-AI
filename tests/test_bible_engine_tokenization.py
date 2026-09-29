"""
POLYA PHILOLOGICAL BIBLE ENGINE
Test Suite: Tokenization Subsystem (Task 2.2)

Authoritative verification of the deterministic, immutable Level 1 tokenization layer.
Validates all 24 required capabilities plus adversarial security probes:
  1. deterministic tokenization
  2. source linkage
  3. token ordering
  4. repeated-token distinction
  5. source offsets
  6. source reconstruction
  7. Unicode Greek
  8. Unicode Hebrew
  9. Unicode Aramaic
  10. combining marks
  11. punctuation preservation
  12. whitespace behavior
  13. normalization-source declaration
  14. language validation
  15. no morphology leakage
  16. no semantic leakage
  17. source hash unchanged
  18. token immutability
  19. version lineage
  20. provenance
  21. deterministic reproducibility
  22. failed-tokenization rollback
  23. concurrent tokenization isolation
  24. legacy DB untouched
  25. adversarial immutability probes (direct SQL update/delete/null-escape)
  26. offset boundary and reconstruction failure probes
  27. retokenization version supersession
"""

import hashlib
import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateTokenError,
    TokenError,
    TokenImmutabilityError,
    TokenNormalizationFirewallError,
    TokenNotFoundError,
    TokenOffsetError,
    TokenReconstructionError,
    TokenSourceNotFoundError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker
from bible_engine.source_registry import SourceLanguage, SourceRegistry, SourceType
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
    SourceTextRecord,
    compute_content_hash,
)
from bible_engine.tokenization import (
    TokenOffsetUnit,
    TokenRecord,
    TokenType,
    TokenizationManager,
    TokenizationResult,
    TokenizationRunRecord,
    TokenizerConfig,
    compute_tokens_output_hash,
    reconstruct_source_span,
    reconstruct_text_from_tokens,
    tokenize_text,
)
from bible_engine.versioning import VersionManager, VersionStatus


class TestTokenizationSubsystem(unittest.TestCase):
    """Exhaustive test suite for Task 2.2 Tokenization Foundation."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "token_test.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)

        # Run all migrations including 006_tokenization.sql
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.version_mgr = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)

        # Record legacy database checksum
        self.legacy_db_path = Path("/home/ubuntu/.polya/polya_index.db")
        self.initial_legacy_hash = None
        if self.legacy_db_path.exists():
            self.initial_legacy_hash = hashlib.sha256(self.legacy_db_path.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _create_sample_source(self, source_id: str, stype: SourceType = SourceType.CRITICAL_EDITION, lang: SourceLanguage = SourceLanguage.GREEK) -> str:
        """Helper to register a valid source in source_registry."""
        src = self.source_registry.register_source(
            source_id=source_id,
            canonical_name=f"Canonical Source {source_id}",
            source_type=stype,
            language=lang,
            authority_level="TEXTUAL_CRITICAL",
        )
        return src.source_id

    def _create_sample_source_text(
        self,
        source_text_id: str,
        content: str,
        language: SourceTextLanguage = SourceTextLanguage.GREEK,
        source_id: Optional[str] = None,
    ) -> SourceTextRecord:
        """Helper to register an immutable source text."""
        sid = source_id or self._create_sample_source(f"SRC-{source_text_id}", SourceType.CRITICAL_EDITION, SourceLanguage(language.value))
        return self.source_text_mgr.register_source_text(
            source_text_id=source_text_id,
            source_id=sid,
            language=language,
            raw_content=content,
            representation_type=RepresentationType.RAW,
        )

    # -------------------------------------------------------------------------
    # 1. Deterministic Tokenization
    # -------------------------------------------------------------------------
    def test_01_deterministic_tokenization(self) -> None:
        """Verify tokenization produces deterministic results across multiple runs."""
        text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        st = self._create_sample_source_text("ST-DET-01", text, SourceTextLanguage.GREEK)

        cfg = TokenizerConfig(include_whitespace=False)
        res1 = self.token_mgr.tokenize_source_text(st, config=cfg)
        
        # Verify run record properties
        self.assertTrue(res1.run.is_exact_reproducible)
        self.assertEqual(res1.run.token_count, 5)
        self.assertEqual(len(res1.tokens), 5)

        # Tokens list matches expected surface forms
        expected = ["Ἐν", "ἀρχῇ", "ἦν", "ὁ", "λόγος"]
        self.assertEqual([t.surface_form for t in res1.tokens], expected)

        # Offsets are monotonically non-decreasing and accurate
        for t in res1.tokens:
            self.assertEqual(text[t.start_offset : t.end_offset], t.surface_form)

    # -------------------------------------------------------------------------
    # 2. Source Linkage
    # -------------------------------------------------------------------------
    def test_02_source_linkage(self) -> None:
        """Verify every token is explicitly linked to source_text_id, object_version, and provenance."""
        text = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים"
        st = self._create_sample_source_text("ST-LINK-01", text, SourceTextLanguage.HEBREW)

        res = self.token_mgr.tokenize_source_text(st)
        self.assertEqual(res.run.source_text_id, st.source_text_id)

        for t in res.tokens:
            self.assertEqual(t.source_text_id, st.source_text_id)
            self.assertEqual(t.tokenization_id, res.run.tokenization_id)
            self.assertEqual(t.version_id, res.run.version_id)
            self.assertEqual(t.provenance_id, res.run.provenance_id)
            self.assertIsNotNone(t.created_at)

        # Attempting to tokenize a non-existent source text raises TokenSourceNotFoundError
        with self.assertRaises(TokenSourceNotFoundError):
            self.token_mgr.tokenize_source_text("NON-EXISTENT-ST-999")

    # -------------------------------------------------------------------------
    # 3. Token Ordering
    # -------------------------------------------------------------------------
    def test_03_token_ordering(self) -> None:
        """Verify token_index is deterministic, 0-indexed, and ordered 0, 1, 2, 3..."""
        text = "καὶ τὸ φῶς ἐν τῇ σκοτίᾳ φαίνει"
        st = self._create_sample_source_text("ST-ORD-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        for i, t in enumerate(res.tokens):
            self.assertEqual(t.token_index, i)
            self.assertEqual(t.position, i + 1)

        # Ensure database retrieval preserves exact index ordering
        fetched_tokens = self.token_mgr.get_tokens_for_run(res.run.tokenization_id)
        self.assertEqual([t.token_index for t in fetched_tokens], list(range(len(fetched_tokens))))

    # -------------------------------------------------------------------------
    # 4. Repeated-Token Distinction
    # -------------------------------------------------------------------------
    def test_04_repeated_token_distinction(self) -> None:
        """Verify identical surface forms at different positions produce distinct token instances."""
        text = "καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος."
        st = self._create_sample_source_text("ST-REP-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        logos_tokens = [t for t in res.tokens if t.surface_form == "λόγος"]
        
        # λόγος appears exactly twice
        self.assertEqual(len(logos_tokens), 2)
        tok_a, tok_b = logos_tokens[0], logos_tokens[1]

        # Different token_id
        self.assertNotEqual(tok_a.token_id, tok_b.token_id)
        # Different token_index
        self.assertNotEqual(tok_a.token_index, tok_b.token_index)
        # Different offsets
        self.assertNotEqual(tok_a.start_offset, tok_b.start_offset)
        self.assertNotEqual(tok_a.end_offset, tok_b.end_offset)
        # Slices from text match accurately
        self.assertEqual(text[tok_a.start_offset : tok_a.end_offset], "λόγος")
        self.assertEqual(text[tok_b.start_offset : tok_b.end_offset], "λόγος")

    # -------------------------------------------------------------------------
    # 5. Source Offsets
    # -------------------------------------------------------------------------
    def test_05_source_offsets(self) -> None:
        """Verify code-point and UTF-8 byte offsets are exact and non-overlapping."""
        text = "Ἐν ἀρχῇ ἦν"
        st = self._create_sample_source_text("ST-OFF-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        self.assertEqual(len(res.tokens), 3)

        t0, t1, t2 = res.tokens
        self.assertEqual((t0.start_offset, t0.end_offset), (0, 2))
        self.assertEqual((t1.start_offset, t1.end_offset), (3, 7))
        self.assertEqual((t2.start_offset, t2.end_offset), (8, 10))

        # Check UTF-8 byte offsets
        raw_bytes = text.encode("utf-8")
        self.assertEqual(raw_bytes[t0.start_byte : t0.end_byte].decode("utf-8"), "Ἐν")
        self.assertEqual(raw_bytes[t1.start_byte : t1.end_byte].decode("utf-8"), "ἀρχῇ")
        self.assertEqual(raw_bytes[t2.start_byte : t2.end_byte].decode("utf-8"), "ἦν")

    # -------------------------------------------------------------------------
    # 6. Source Reconstruction
    # -------------------------------------------------------------------------
    def test_06_source_reconstruction(self) -> None:
        """Verify token positions reconstruct the complete original source span without character drift."""
        text = "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος."
        st = self._create_sample_source_text("ST-REC-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        
        # Test reconstruct_source_span on each token
        for t in res.tokens:
            span = reconstruct_source_span(text, t)
            self.assertEqual(span, t.surface_form)

        # Test full reconstruction
        reconstructed = reconstruct_text_from_tokens(res.tokens, text)
        self.assertEqual(reconstructed, text)

    # -------------------------------------------------------------------------
    # 7. Unicode Greek
    # -------------------------------------------------------------------------
    def test_07_unicode_greek(self) -> None:
        """Verify polytonic Greek with accents, breathing marks, and punctuation is safely tokenized."""
        greek_text = "Οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον, ὥστε τὸν υἱὸν τὸν μονογενῆ ἔδωκεν·"
        st = self._create_sample_source_text("ST-GRK-01", greek_text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        self.assertGreater(len(res.tokens), 10)
        
        # Last token is punctuation ano teleia (·)
        last_tok = res.tokens[-1]
        self.assertEqual(last_tok.token_type, TokenType.PUNCTUATION)
        self.assertEqual(last_tok.surface_form, "·")

        # Full reconstruction
        self.assertEqual(reconstruct_text_from_tokens(res.tokens, greek_text), greek_text)

    # -------------------------------------------------------------------------
    # 8. Unicode Hebrew
    # -------------------------------------------------------------------------
    def test_08_unicode_hebrew(self) -> None:
        """Verify Hebrew with niqqud, cantillation, maqaf, and sof pasuq is preserved accurately."""
        hebrew_text = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
        st = self._create_sample_source_text("ST-HEB-01", hebrew_text, SourceTextLanguage.HEBREW)

        res = self.token_mgr.tokenize_source_text(st)
        words = [t for t in res.tokens if t.token_type == TokenType.WORD]
        puncts = [t for t in res.tokens if t.token_type == TokenType.PUNCTUATION]

        self.assertEqual(len(words), 7)
        self.assertEqual(len(puncts), 1)
        self.assertEqual(puncts[0].surface_form, "׃")

        # Full reconstruction
        self.assertEqual(reconstruct_text_from_tokens(res.tokens, hebrew_text), hebrew_text)

    # -------------------------------------------------------------------------
    # 9. Unicode Aramaic
    # -------------------------------------------------------------------------
    def test_09_unicode_aramaic(self) -> None:
        """Verify Biblical Aramaic passage (Daniel 2:20) with maqaf is tokenized properly."""
        aramaic_text = "מִן־עָלְמָא וְעַד־עָלְמָא"
        st = self._create_sample_source_text("ST-ARM-01", aramaic_text, SourceTextLanguage.ARAMAIC)

        res = self.token_mgr.tokenize_source_text(st)
        # Expected tokens: מִן, ־, עָלְמָא, וְעַד, ־, עָלְמָא
        self.assertEqual(len(res.tokens), 6)
        self.assertEqual(res.tokens[0].surface_form, "מִן")
        self.assertEqual(res.tokens[1].surface_form, "־")
        self.assertEqual(res.tokens[1].token_type, TokenType.PUNCTUATION)
        self.assertEqual(res.tokens[2].surface_form, "עָלְמָא")
        self.assertEqual(res.tokens[3].surface_form, "וְעַד")
        self.assertEqual(res.tokens[4].surface_form, "־")
        self.assertEqual(res.tokens[5].surface_form, "עָלְמָא")

        # Full reconstruction
        self.assertEqual(reconstruct_text_from_tokens(res.tokens, aramaic_text), aramaic_text)

    # -------------------------------------------------------------------------
    # 10. Combining Marks
    # -------------------------------------------------------------------------
    def test_10_combining_marks(self) -> None:
        """Verify combining marks attach to preceding base characters without offset drift."""
        # Decomposed: 'e' + combining acute (\u0301) + ' ' + 'a' + combining grave (\u0300)
        decomp_text = "e\u0301 a\u0300"
        st = self._create_sample_source_text("ST-CMB-01", decomp_text, SourceTextLanguage.OTHER)

        res = self.token_mgr.tokenize_source_text(st)
        self.assertEqual(len(res.tokens), 2)
        self.assertEqual(res.tokens[0].surface_form, "e\u0301")
        self.assertEqual(res.tokens[0].start_offset, 0)
        self.assertEqual(res.tokens[0].end_offset, 2)
        self.assertEqual(res.tokens[1].surface_form, "a\u0300")
        self.assertEqual(res.tokens[1].start_offset, 3)
        self.assertEqual(res.tokens[1].end_offset, 5)

        self.assertEqual(reconstruct_text_from_tokens(res.tokens, decomp_text), decomp_text)

    # -------------------------------------------------------------------------
    # 11. Punctuation Preservation
    # -------------------------------------------------------------------------
    def test_11_punctuation_preservation(self) -> None:
        """Verify Greek and Hebrew punctuation marks are strictly preserved as distinct tokens."""
        punct_text = "«λόγος»· (θεός); ׃ ׀ ־"
        st = self._create_sample_source_text("ST-PUNCT-01", punct_text, SourceTextLanguage.MULTILINGUAL)

        res = self.token_mgr.tokenize_source_text(st)
        puncts = [t for t in res.tokens if t.token_type == TokenType.PUNCTUATION]
        punct_surfaces = [t.surface_form for t in puncts]

        expected_puncts = ["«", "»", "·", "(", ")", ";", "׃", "׀", "־"]
        self.assertEqual(punct_surfaces, expected_puncts)
        self.assertEqual(reconstruct_text_from_tokens(res.tokens, punct_text), punct_text)

    # -------------------------------------------------------------------------
    # 12. Whitespace Behavior
    # -------------------------------------------------------------------------
    def test_12_whitespace_behavior(self) -> None:
        """Verify whitespace can be represented as positional gaps or explicit tokens."""
        ws_text = "  Ἐν   ἀρχῇ \t\n ἦν  "
        st = self._create_sample_source_text("ST-WS-01", ws_text, SourceTextLanguage.GREEK)

        # Mode A: Positional gaps (default include_whitespace=False)
        res_gaps = self.token_mgr.tokenize_source_text(st, config=TokenizerConfig(include_whitespace=False))
        self.assertEqual(len(res_gaps.tokens), 3)
        self.assertEqual([t.surface_form for t in res_gaps.tokens], ["Ἐν", "ἀρχῇ", "ἦν"])
        self.assertEqual(reconstruct_text_from_tokens(res_gaps.tokens, ws_text), ws_text)

        # Mode B: Explicit tokens (include_whitespace=True)
        res_explicit = self.token_mgr.tokenize_source_text(
            st, config=TokenizerConfig(tokenizer_version="1.1.0", include_whitespace=True)
        )
        ws_tokens = [t for t in res_explicit.tokens if t.token_type == TokenType.WHITESPACE]
        self.assertGreater(len(ws_tokens), 0)
        # Direct concatenation of all surface forms reproduces original string
        concatenated = "".join([t.surface_form for t in res_explicit.tokens])
        self.assertEqual(concatenated, ws_text)

    # -------------------------------------------------------------------------
    # 13. Normalization-Source Declaration
    # -------------------------------------------------------------------------
    def test_13_normalization_source_declaration(self) -> None:
        """Verify tokenization declares whether it uses RAW or NORMALIZED representation."""
        raw_text = "e\u0301"  # Decomposed
        norm_text = "\u00e9"   # NFC precomposed
        
        # Register source text with distinct raw and normalized representations
        src_id = self._create_sample_source("SRC-NORM-DECL")
        st = self.source_text_mgr.register_source_text(
            source_text_id="ST-NORM-DECL-01",
            source_id=src_id,
            language=SourceTextLanguage.OTHER,
            raw_content=raw_text,
            normalized_content=norm_text,
            representation_type=RepresentationType.RAW,
        )

        # Tokenize RAW
        res_raw = self.token_mgr.tokenize_source_text(st, config=TokenizerConfig(representation_type=RepresentationType.RAW))
        self.assertEqual(res_raw.run.representation_type, RepresentationType.RAW)
        self.assertEqual(res_raw.tokens[0].surface_form, raw_text)
        self.assertEqual(res_raw.tokens[0].end_offset, 2)

        # Tokenize NORMALIZED
        res_norm = self.token_mgr.tokenize_source_text(st, config=TokenizerConfig(representation_type=RepresentationType.NORMALIZED))
        self.assertEqual(res_norm.run.representation_type, RepresentationType.NORMALIZED)
        self.assertEqual(res_norm.tokens[0].surface_form, norm_text)
        self.assertEqual(res_norm.tokens[0].end_offset, 1)

    # -------------------------------------------------------------------------
    # 14. Language Validation
    # -------------------------------------------------------------------------
    def test_14_language_validation(self) -> None:
        """Verify tokens inherit valid controlled language classification from source text."""
        for lang in [SourceTextLanguage.GREEK, SourceTextLanguage.HEBREW, SourceTextLanguage.ARAMAIC, SourceTextLanguage.LATIN]:
            st = self._create_sample_source_text(f"ST-LANG-{lang.value}", f"Veritas {lang.value}", lang)
            res = self.token_mgr.tokenize_source_text(st)
            self.assertEqual(res.run.language, lang)
            for t in res.tokens:
                self.assertEqual(t.language, lang)

    # -------------------------------------------------------------------------
    # 15. No Morphology Leakage
    # -------------------------------------------------------------------------
    def test_15_no_morphology_leakage(self) -> None:
        """Verify tokenizer produces zero morphological inferences (no lemma, POS, case, tense)."""
        text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        st = self._create_sample_source_text("ST-MORPH-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        for t in res.tokens:
            self.assertIsNone(t.lemma_id)
            # Ensure no hidden morphological attributes exist
            self.assertFalse(hasattr(t, "pos_tag"))
            self.assertFalse(hasattr(t, "grammatical_case"))
            self.assertFalse(hasattr(t, "tense_form"))
            self.assertFalse(hasattr(t, "voice"))
            self.assertFalse(hasattr(t, "mood"))

    # -------------------------------------------------------------------------
    # 16. No Semantic Leakage
    # -------------------------------------------------------------------------
    def test_16_no_semantic_leakage(self) -> None:
        """Verify tokenizer produces zero semantic glosses or theological definitions."""
        text = "בְּרֵאשִׁ֖ית"
        st = self._create_sample_source_text("ST-SEM-01", text, SourceTextLanguage.HEBREW)

        res = self.token_mgr.tokenize_source_text(st)
        for t in res.tokens:
            self.assertFalse(hasattr(t, "literal_gloss"))
            self.assertFalse(hasattr(t, "semantic_sense"))
            self.assertFalse(hasattr(t, "strong_code"))

    # -------------------------------------------------------------------------
    # 17. Source Hash Unchanged
    # -------------------------------------------------------------------------
    def test_17_source_hash_unchanged(self) -> None:
        """Verify tokenization does not mutate or alter source text content or content hash."""
        text = "καὶ θεὸς ἦν ὁ λόγος."
        st = self._create_sample_source_text("ST-UNCHANGED-01", text, SourceTextLanguage.GREEK)

        hash_before = st.content_hash
        raw_before = st.raw_content

        res = self.token_mgr.tokenize_source_text(st)

        st_after = self.source_text_mgr.get_source_text(st.source_text_id)
        self.assertIsNotNone(st_after)
        self.assertEqual(st_after.content_hash, hash_before)
        self.assertEqual(st_after.raw_content, raw_before)

    # -------------------------------------------------------------------------
    # 18. Token Immutability
    # -------------------------------------------------------------------------
    def test_18_token_immutability(self) -> None:
        """Verify direct SQL UPDATE and DELETE on tokens table are blocked by triggers."""
        text = "Ἐν ἀρχῇ"
        st = self._create_sample_source_text("ST-IMMUT-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        tok_id = res.tokens[0].token_id

        # Attempting UPDATE surface_form
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE tokens SET surface_form = 'Tampered' WHERE token_id = ?;", (tok_id,))

        # Attempting UPDATE offsets
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE tokens SET start_offset = 99 WHERE token_id = ?;", (tok_id,))

        # Attempting DELETE
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM tokens WHERE token_id = ?;", (tok_id,))

    # -------------------------------------------------------------------------
    # 19. Version Lineage
    # -------------------------------------------------------------------------
    def test_19_version_lineage(self) -> None:
        """Verify tokenization run integrates cleanly with VersionManager object_versions."""
        text = "Ἐν ἀρχῇ ἦν"
        st = self._create_sample_source_text("ST-VER-01", text, SourceTextLanguage.GREEK)

        res = self.token_mgr.tokenize_source_text(st)
        ver = self.version_mgr.get_version(res.run.version_id)
        
        self.assertIsNotNone(ver)
        self.assertEqual(ver.object_id, res.run.tokenization_id)
        self.assertEqual(ver.object_type, "tokenization")
        self.assertEqual(ver.status, VersionStatus.ACTIVE)
        self.assertEqual(ver.content_hash, res.run.output_hash)

    # -------------------------------------------------------------------------
    # 20. Provenance Integration
    # -------------------------------------------------------------------------
    def test_20_provenance(self) -> None:
        """Verify tokenization records cryptographic provenance linking to source text."""
        text = "בָּרָ֣א אֱלֹהִ֑ים"
        st = self._create_sample_source_text("ST-PROV-01", text, SourceTextLanguage.HEBREW)

        res = self.token_mgr.tokenize_source_text(st)
        prov = self.provenance_tracker.get_record(res.run.provenance_id)

        self.assertIsNotNone(prov)
        self.assertEqual(prov.target_id, res.run.tokenization_id)
        self.assertEqual(prov.output_hash, hashlib.sha256(res.run.output_hash.encode("utf-8")).hexdigest())
        self.assertTrue(self.provenance_tracker.verify_record_content(prov.provenance_id, res.run.output_hash).is_valid)
        self.assertIsNotNone(prov.input_hash)
        self.assertEqual(prov.parent_provenance_id, st.provenance_id)
        self.assertTrue(prov.is_exact_reproducible)

    # -------------------------------------------------------------------------
    # 21. Deterministic Reproducibility
    # -------------------------------------------------------------------------
    def test_21_deterministic_reproducibility(self) -> None:
        """Verify tokenize_text output hash is 100% deterministic across repeated independent calls."""
        text = "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν"
        st = self._create_sample_source_text("ST-REPRO-01", text, SourceTextLanguage.GREEK)

        tokens1 = tokenize_text(text, SourceTextLanguage.GREEK)
        tokens2 = tokenize_text(text, SourceTextLanguage.GREEK)

        self.assertEqual(tokens1, tokens2)

    # -------------------------------------------------------------------------
    # 22. Failed Tokenization Rollback
    # -------------------------------------------------------------------------
    def test_22_failed_tokenization_rollback(self) -> None:
        """Verify failure during tokenization leaves no orphaned tokens, provenance, or version."""
        text = "Valid text"
        st = self._create_sample_source_text("ST-ROLLBACK-01", text, SourceTextLanguage.GREEK)

        # Count records before failure
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM tokenization_runs;")
            runs_before = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM tokens;")
            tokens_before = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM object_versions WHERE object_type = 'tokenization';")
            vers_before = cur.fetchone()[0]

        # Trigger failure by forcing invalid representation_type
        bad_config = TokenizerConfig(representation_type="INVALID_REP")  # type: ignore
        with self.assertRaises(TokenNormalizationFirewallError):
            self.token_mgr.tokenize_source_text(st, config=bad_config)

        # Verify zero state change in database
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM tokenization_runs;")
            self.assertEqual(cur.fetchone()[0], runs_before)
            cur.execute("SELECT count(*) FROM tokens;")
            self.assertEqual(cur.fetchone()[0], tokens_before)
            cur.execute("SELECT count(*) FROM object_versions WHERE object_type = 'tokenization';")
            self.assertEqual(cur.fetchone()[0], vers_before)

    # -------------------------------------------------------------------------
    # 23. Concurrent Tokenization Isolation
    # -------------------------------------------------------------------------
    def test_23_concurrent_tokenization_isolation(self) -> None:
        """Verify concurrent tokenization requests across separate source texts remain isolated."""
        st1 = self._create_sample_source_text("ST-CONC-01", "Ἐν ἀρχῇ ἦν", SourceTextLanguage.GREEK)
        st2 = self._create_sample_source_text("ST-CONC-02", "בְּרֵאשִׁ֖ית בָּרָ֣א", SourceTextLanguage.HEBREW)

        results = {}
        errors = []

        def worker(st, key):
            eng = DatabaseEngine(self.config)
            try:
                tm = TokenizationManager(eng)
                res = tm.tokenize_source_text(st.source_text_id)
                results[key] = res
            except Exception as e:
                errors.append(e)
            finally:
                eng.close()

        t1 = threading.Thread(target=worker, args=(st1, "greek"))
        t2 = threading.Thread(target=worker, args=(st2, "hebrew"))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Concurrent workers encountered errors: {errors}")
        self.assertIn("greek", results)
        self.assertIn("hebrew", results)
        self.assertEqual(results["greek"].run.source_text_id, st1.source_text_id)
        self.assertEqual(results["hebrew"].run.source_text_id, st2.source_text_id)

    # -------------------------------------------------------------------------
    # 24. Legacy DB Untouched
    # -------------------------------------------------------------------------
    def test_24_legacy_db_untouched(self) -> None:
        """Verify /home/ubuntu/.polya/polya_index.db remains completely untouched."""
        if self.legacy_db_path.exists() and self.initial_legacy_hash:
            current_hash = hashlib.sha256(self.legacy_db_path.read_bytes()).hexdigest()
            self.assertEqual(
                current_hash,
                self.initial_legacy_hash,
                "Legacy database /home/ubuntu/.polya/polya_index.db was modified during token tests!",
            )

    # -------------------------------------------------------------------------
    # 25. Adversarial Immutability Probes
    # -------------------------------------------------------------------------
    def test_25_adversarial_immutability_probes(self) -> None:
        """Adversarial security probe: test NULL-escape and column updates on tokens and runs."""
        text = "λόγος"
        st = self._create_sample_source_text("ST-ADV-01", text, SourceTextLanguage.GREEK)
        res = self.token_mgr.tokenize_source_text(st)

        tok = res.tokens[0]
        run_id = res.run.tokenization_id

        # Probe 1: Updating tokenization_runs fields
        forbidden_run_updates = [
            ("source_text_id", "'ST-FAKE'"),
            ("version_id", "'VER-FAKE'"),
            ("tokenizer_id", "'tampered'"),
            ("input_content_hash", "'0' * 64"),
            ("token_count", "999"),
        ]
        for col, val in forbidden_run_updates:
            with self.subTest(run_col=col):
                with self.assertRaises(sqlite3.IntegrityError):
                    with self.engine.transaction() as conn:
                        conn.execute(f"UPDATE tokenization_runs SET {col} = {val} WHERE tokenization_id = ?;", (run_id,))

        # Probe 2: Updating tokens fields
        forbidden_tok_updates = [
            ("surface_form", "'hacked'"),
            ("start_offset", "99"),
            ("end_offset", "100"),
            ("token_type", "'PUNCTUATION'"),
            ("language", "'LATIN'"),
            ("version_id", "'VER-HACK'"),
        ]
        for col, val in forbidden_tok_updates:
            with self.subTest(tok_col=col):
                with self.assertRaises(sqlite3.IntegrityError):
                    with self.engine.transaction() as conn:
                        conn.execute(f"UPDATE tokens SET {col} = {val} WHERE token_id = ?;", (tok.token_id,))

        # Probe 3: Deleting tokenization run
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM tokenization_runs WHERE tokenization_id = ?;", (run_id,))

    # -------------------------------------------------------------------------
    # 26. Offset Boundary and Reconstruction Failure Probes
    # -------------------------------------------------------------------------
    def test_26_offset_boundary_and_reconstruction_failure_probes(self) -> None:
        """Verify invalid offsets or mismatched surfaces are caught by reconstruction guards."""
        text = "Ἐν ἀρχῇ"
        tok_valid = TokenRecord(
            token_id="T1",
            source_text_id="S1",
            version_id="V1",
            provenance_id="P1",
            surface_form="Ἐν",
            start_offset=0,
            end_offset=2,
        )
        # Valid span
        self.assertEqual(reconstruct_source_span(text, tok_valid), "Ἐν")

        # Out of bounds offset
        tok_oob = TokenRecord(
            token_id="T2",
            source_text_id="S1",
            version_id="V1",
            provenance_id="P1",
            surface_form="Ἐν",
            start_offset=0,
            end_offset=999,
        )
        with self.assertRaises(TokenOffsetError):
            reconstruct_source_span(text, tok_oob)

        # Inverted offset
        tok_inv = TokenRecord(
            token_id="T3",
            source_text_id="S1",
            version_id="V1",
            provenance_id="P1",
            surface_form="Ἐν",
            start_offset=5,
            end_offset=2,
        )
        with self.assertRaises(TokenOffsetError):
            reconstruct_source_span(text, tok_inv)

        # Mismatched surface form
        tok_mismatch = TokenRecord(
            token_id="T4",
            source_text_id="S1",
            version_id="V1",
            provenance_id="P1",
            surface_form="Mismatch",
            start_offset=0,
            end_offset=2,
        )
        with self.assertRaises(TokenReconstructionError):
            reconstruct_source_span(text, tok_mismatch)

    # -------------------------------------------------------------------------
    # 27. Retokenization Version Supersession
    # -------------------------------------------------------------------------
    def test_27_retokenization_version_supersession(self) -> None:
        """Verify retokenise creates a new version lineage without mutating historical tokens."""
        text = "Ἐν ἀρχῇ ἦν"
        st = self._create_sample_source_text("ST-RETOK-01", text, SourceTextLanguage.GREEK)

        cfg1 = TokenizerConfig(tokenizer_version="1.0.0", include_whitespace=False)
        res1 = self.token_mgr.tokenize_source_text(st, config=cfg1)
        self.assertEqual(len(res1.tokens), 3)

        # Retokenize with include_whitespace=True
        cfg2 = TokenizerConfig(tokenizer_version="1.1.0", include_whitespace=True)
        res2 = self.token_mgr.retokenise(st.source_text_id, new_config=cfg2, reason="Whitespace addition")
        self.assertEqual(len(res2.tokens), 5)  # 3 words + 2 whitespace tokens

        # Historical run and tokens remain intact in database
        tokens_run1 = self.token_mgr.get_tokens_for_run(res1.run.tokenization_id)
        tokens_run2 = self.token_mgr.get_tokens_for_run(res2.run.tokenization_id)
        self.assertEqual(len(tokens_run1), 3)
        self.assertEqual(len(tokens_run2), 5)

        # Version 1 superseded by Version 2
        ver1 = self.version_mgr.get_version(res1.run.version_id)
        ver2 = self.version_mgr.get_version(res2.run.version_id)
        self.assertEqual(ver1.status, VersionStatus.SUPERSEDED)
        self.assertEqual(ver2.status, VersionStatus.ACTIVE)


if __name__ == "__main__":
    unittest.main()
