"""
POLYA PHILOLOGICAL BIBLE ENGINE
Integration & Verification Suite for Source Text Foundation (Task 2.1)

Covers all 26 mandatory requirements:
  1. source-text registration
  2. source existence requirement
  3. source retrieval
  4. language validation
  5. representation validation
  6. deterministic SHA-256
  7. malformed hash rejection
  8. hash mismatch detection
  9. raw content immutability
  10. hash immutability
  11. DELETE protection
  12. source linkage immutability
  13. provenance integration
  14. version integration
  15. Unicode Greek (polytonic)
  16. Unicode Hebrew (niqqud and cantillation)
  17. Unicode Aramaic
  18. combining marks & NFC/NFD integrity
  19. raw vs normalized separation
  20. translation firewall
  21. ancient translation distinction
  22. witness distinction
  23. critical edition distinction
  24. transaction rollback
  25. concurrent registration
  26. legacy database untouched
"""

import hashlib
import os
import sqlite3
import tempfile
import threading
import unicodedata
import unittest
from pathlib import Path
from typing import List, Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSourceTextError,
    InvalidRepresentationTypeError,
    InvalidSourceTextLanguageError,
    MalformedContentHashError,
    SourceNotFoundError,
    SourceTextHashMismatchError,
    SourceTextImmutabilityError,
    SourceTextNotFoundError,
    SourceTextOrphanError,
    SourceTextTranslationFirewallError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import (
    ProvenanceTracker,
    TargetType,
    TransformationType,
)
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
    compute_content_hash,
    generate_source_text_id,
    normalize_unicode_text,
    validate_content_hash,
)
from bible_engine.versioning import (
    ChangeReason,
    VersionManager,
    VersionStatus,
)


class TestSourceTextSubsystem(unittest.TestCase):
    """Complete verification of Source Text Foundation subsystem (Task 2.1)."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_source_text.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)

        # Bootstrap all migrations (001-005)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.source_registry = SourceRegistry(self.engine)
        self.source_text_manager = SourceTextManager(
            self.engine,
            version_manager=self.version_manager,
            provenance_tracker=self.provenance_tracker,
            source_registry=self.source_registry,
        )

        # Seed baseline scholarly sources
        self.na28_source = self.source_registry.register_source(
            canonical_name="Nestle-Aland 28th Edition",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
            source_id="SRC-ED-NA28",
            description="Novum Testamentum Graece 28th Rev",
        )
        self.sinaiticus_source = self.source_registry.register_source(
            canonical_name="Codex Sinaiticus (01, א)",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            source_id="SRC-WIT-SINAITICUS",
            description="4th century uncial manuscript witness",
        )
        self.vulgate_source = self.source_registry.register_source(
            canonical_name="Biblia Sacra Vulgata (Stuttgart)",
            source_type=SourceType.ANCIENT_TRANSLATION,
            language=SourceLanguage.LATIN,
            authority_level=SourceAuthorityLevel.HISTORICAL,
            source_id="SRC-VULGATE-STUTT",
            description="Jerome Latin Vulgate translation",
        )
        self.niv_source = self.source_registry.register_source(
            canonical_name="New International Version (2011)",
            source_type=SourceType.MODERN_TRANSLATION,
            language=SourceLanguage.OTHER,
            authority_level=SourceAuthorityLevel.TRANSLATION,
            source_id="SRC-NIV-2011",
            description="Modern English dynamic equivalence translation",
        )

        # Record legacy database checksum before testing
        self.legacy_db_path = "/home/ubuntu/.polya/polya_index.db"
        self.legacy_db_hash = self._compute_file_sha256(self.legacy_db_path)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _compute_file_sha256(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    # -------------------------------------------------------------------------
    # 1. Source-text registration
    # -------------------------------------------------------------------------
    def test_01_source_text_registration(self) -> None:
        """Verify successful registration of authoritative source text with complete fields."""
        raw_greek = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content=raw_greek,
            language=SourceTextLanguage.GREEK,
            representation_type=RepresentationType.RAW,
            metadata={"chapter": 1, "verse": 1, "book": "JOHN"},
        )
        self.assertIsNotNone(rec.source_text_id)
        self.assertEqual(rec.source_id, "SRC-ED-NA28")
        self.assertEqual(rec.raw_content, raw_greek)
        self.assertEqual(rec.raw_source_string, raw_greek)
        self.assertEqual(rec.language, "GREEK")
        self.assertEqual(rec.representation_type, "RAW")
        self.assertEqual(rec.is_immutable, 1)
        self.assertIsNotNone(rec.provenance_id)
        self.assertIsNotNone(rec.version_id)
        self.assertEqual(rec.content_hash, compute_content_hash(raw_greek))
        self.assertEqual(rec.metadata.get("book"), "JOHN")

    # -------------------------------------------------------------------------
    # 2. Source existence requirement
    # -------------------------------------------------------------------------
    def test_02_source_existence_requirement(self) -> None:
        """Attempting to register source text with a non-existent or orphan source_id must fail."""
        with self.assertRaises((SourceNotFoundError, SourceTextOrphanError)):
            self.source_text_manager.register_source_text(
                source_id="SRC-DOES-NOT-EXIST",
                raw_content="Some text",
                language=SourceTextLanguage.GREEK,
            )

        with self.assertRaises(SourceTextOrphanError):
            self.source_text_manager.register_source_text(
                source_id="",
                raw_content="Some text",
                language=SourceTextLanguage.GREEK,
            )

    # -------------------------------------------------------------------------
    # 3. Source retrieval
    # -------------------------------------------------------------------------
    def test_03_source_retrieval(self) -> None:
        """Verify retrieval by ID and filtered listing; non-existent ID raises SourceTextNotFoundError."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="καὶ ὁ λόγος ἦν πρὸς τὸν θεόν",
            language=SourceTextLanguage.GREEK,
        )
        fetched = self.source_text_manager.get_source_text(rec.source_text_id)
        self.assertEqual(fetched.source_text_id, rec.source_text_id)
        self.assertEqual(fetched.raw_content, rec.raw_content)

        # Listing by source_id
        results = self.source_text_manager.list_source_texts(source_id="SRC-ED-NA28")
        self.assertTrue(any(r.source_text_id == rec.source_text_id for r in results))

        with self.assertRaises(SourceTextNotFoundError):
            self.source_text_manager.get_source_text("ST-NON-EXISTENT")

    # -------------------------------------------------------------------------
    # 4. Language validation
    # -------------------------------------------------------------------------
    def test_04_language_validation(self) -> None:
        """All 8 controlled languages must be accepted; invalid languages must be rejected."""
        valid_langs = [
            SourceTextLanguage.GREEK,
            SourceTextLanguage.HEBREW,
            SourceTextLanguage.ARAMAIC,
            SourceTextLanguage.LATIN,
            SourceTextLanguage.SYRIAC,
            SourceTextLanguage.COPTIC,
            SourceTextLanguage.OTHER,
            SourceTextLanguage.MULTILINGUAL,
        ]
        # Register a multilingual source to test all languages
        multi_src = self.source_registry.register_source(
            canonical_name="Polyglot Reference",
            source_type=SourceType.SOURCE_LANGUAGE_TEXT,
            language=SourceLanguage.MULTILINGUAL,
            authority_level=SourceAuthorityLevel.PRIMARY,
            source_id="SRC-MULTI-REF",
        )
        for lang in valid_langs:
            rec = self.source_text_manager.register_source_text(
                source_id="SRC-MULTI-REF",
                raw_content=f"Content for {lang.value}",
                language=lang,
            )
            self.assertEqual(rec.language, lang.value)

        with self.assertRaises(InvalidSourceTextLanguageError):
            self.source_text_manager.register_source_text(
                source_id="SRC-MULTI-REF",
                raw_content="Invalid language test",
                language="ESPERANTO",
            )

    # -------------------------------------------------------------------------
    # 5. Representation validation
    # -------------------------------------------------------------------------
    def test_05_representation_validation(self) -> None:
        """Controlled representations (RAW, NORMALIZED, TRANSLITERATED, TRANSFORMED) accepted; invalid rejected."""
        valid_reps = [
            RepresentationType.RAW,
            RepresentationType.NORMALIZED,
            RepresentationType.TRANSLITERATED,
            RepresentationType.TRANSFORMED,
        ]
        for rep in valid_reps:
            rec = self.source_text_manager.register_source_text(
                source_id="SRC-ED-NA28",
                raw_content=f"Sample text for {rep.value}",
                language=SourceTextLanguage.GREEK,
                representation_type=rep,
            )
            self.assertEqual(rec.representation_type, rep.value)

        with self.assertRaises(InvalidRepresentationTypeError):
            self.source_text_manager.register_source_text(
                source_id="SRC-ED-NA28",
                raw_content="Sample text",
                language=SourceTextLanguage.GREEK,
                representation_type="HALLUCINATED",
            )

    # -------------------------------------------------------------------------
    # 6. Deterministic SHA-256
    # -------------------------------------------------------------------------
    def test_06_deterministic_sha256(self) -> None:
        """SHA-256 content hash must be completely deterministic across repeated evaluations."""
        text = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים"
        hash1 = compute_content_hash(text)
        hash2 = compute_content_hash(text)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash1))

    # -------------------------------------------------------------------------
    # 7. Malformed hash rejection
    # -------------------------------------------------------------------------
    def test_07_malformed_hash_rejection(self) -> None:
        """Malformed, non-hex, uppercase, or incorrect length hashes must be rejected."""
        invalid_hashes = [
            "not-a-hash",
            "12345",
            "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",  # Uppercase
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85g",  # 'g' not hex
            " " * 64,
        ]
        for bad_hash in invalid_hashes:
            with self.assertRaises(MalformedContentHashError):
                self.source_text_manager.register_source_text(
                    source_id="SRC-ED-NA28",
                    raw_content="Some content",
                    language=SourceTextLanguage.GREEK,
                    content_hash=bad_hash,
                )

    # -------------------------------------------------------------------------
    # 8. Hash mismatch detection
    # -------------------------------------------------------------------------
    def test_08_hash_mismatch_detection(self) -> None:
        """Supplying a valid hash that does not match computed SHA-256 must be rejected."""
        content = "Authentic raw content"
        wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        with self.assertRaises(SourceTextHashMismatchError):
            self.source_text_manager.register_source_text(
                source_id="SRC-ED-NA28",
                raw_content=content,
                language=SourceTextLanguage.GREEK,
                content_hash=wrong_hash,
            )

    # -------------------------------------------------------------------------
    # 9. Raw content immutability
    # -------------------------------------------------------------------------
    def test_09_raw_content_immutability(self) -> None:
        """Attempting to mutate raw content via API or direct SQL must be rejected."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Immutable original string",
            language=SourceTextLanguage.GREEK,
        )
        # API level check
        with self.assertRaises(SourceTextImmutabilityError):
            self.source_text_manager.update_raw_content(rec.source_text_id, "Corrupted string")

        # Database trigger level check (H-002)
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE source_texts SET raw_content = 'Hacked' WHERE source_text_id = ?;",
                    (rec.source_text_id,),
                )

    # -------------------------------------------------------------------------
    # 10. Hash immutability
    # -------------------------------------------------------------------------
    def test_10_hash_immutability(self) -> None:
        """Direct SQL attempt to alter stored SHA-256 content hash must be rejected by trigger."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Text with protected hash",
            language=SourceTextLanguage.GREEK,
        )
        fake_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE source_texts SET sha256_hash = ? WHERE source_text_id = ?;",
                    (fake_hash, rec.source_text_id),
                )

    # -------------------------------------------------------------------------
    # 11. DELETE protection
    # -------------------------------------------------------------------------
    def test_11_delete_protection(self) -> None:
        """Deleting source text records via API or direct SQL must be strictly prohibited."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Text to protect from deletion",
            language=SourceTextLanguage.GREEK,
        )
        with self.assertRaises(SourceTextImmutabilityError):
            self.source_text_manager.delete_source_text(rec.source_text_id)

        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "DELETE FROM source_texts WHERE source_text_id = ?;",
                    (rec.source_text_id,),
                )

    # -------------------------------------------------------------------------
    # 12. Source linkage immutability
    # -------------------------------------------------------------------------
    def test_12_source_linkage_immutability(self) -> None:
        """Mutating the source_id foreign key linkage must be rejected at API and SQL level."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Text with immutable source linkage",
            language=SourceTextLanguage.GREEK,
        )
        with self.assertRaises(SourceTextImmutabilityError):
            self.source_text_manager.update_source_linkage(rec.source_text_id, "SRC-WIT-SINAITICUS")

        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "UPDATE source_texts SET source_id = 'SRC-WIT-SINAITICUS' WHERE source_text_id = ?;",
                    (rec.source_text_id,),
                )

    # -------------------------------------------------------------------------
    # 13. Provenance integration
    # -------------------------------------------------------------------------
    def test_13_provenance_integration(self) -> None:
        """Registered source text must create a verifiable provenance record in provenance_records."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Text with provenance record",
            language=SourceTextLanguage.GREEK,
        )
        self.assertIsNotNone(rec.provenance_id)
        prov_record = self.provenance_tracker.get_record(rec.provenance_id)
        self.assertIsNotNone(prov_record)
        self.assertEqual(prov_record.target_id, rec.source_text_id)
        self.assertEqual(prov_record.target_type, TargetType.SOURCE_TEXT.value)
        self.assertEqual(prov_record.content_hash, rec.content_hash)
        self.assertEqual(prov_record.is_immutable, 1)

    # -------------------------------------------------------------------------
    # 14. Version integration
    # -------------------------------------------------------------------------
    def test_14_version_integration(self) -> None:
        """Source text must link to object_versions; lifecycle transitions must follow versioning rules."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Versioned source text",
            language=SourceTextLanguage.GREEK,
        )
        self.assertIsNotNone(rec.version_id)
        version_record = self.version_manager.get_version(rec.version_id)
        self.assertEqual(version_record.object_id, rec.source_text_id)
        self.assertEqual(version_record.object_type, "SOURCE_TEXT")
        self.assertEqual(version_record.version_number, 1)
        self.assertEqual(version_record.status, VersionStatus.ACTIVE.value)

        # Transition ACTIVE -> SUPERSEDED via VersionManager
        new_ver = self.version_manager.create_version(
            object_id=rec.source_text_id,
            object_type="SOURCE_TEXT",
            content_hash=compute_content_hash("Updated reading in new edition"),
            parent_version_id=rec.version_id,
            status=VersionStatus.ACTIVE,
            change_reason=ChangeReason.CORRECTION,
        )
        # Previous version is now superseded
        old_ver_updated = self.version_manager.get_version(rec.version_id)
        self.assertEqual(old_ver_updated.status, VersionStatus.SUPERSEDED.value)
        self.assertEqual(new_ver.version_number, 2)

    # -------------------------------------------------------------------------
    # 15. Unicode Greek (polytonic)
    # -------------------------------------------------------------------------
    def test_15_unicode_greek(self) -> None:
        """Polytonic Greek with rough breathing, circumflex, and iota subscript must be preserved byte-exact."""
        greek_polytonic = "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος."
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-WIT-SINAITICUS",
            raw_content=greek_polytonic,
            language=SourceTextLanguage.GREEK,
        )
        fetched = self.source_text_manager.get_source_text(rec.source_text_id)
        self.assertEqual(fetched.raw_content, greek_polytonic)
        # Verify SHA-256 calculation on polytonic Greek
        expected_hash = hashlib.sha256(greek_polytonic.encode("utf-8")).hexdigest()
        self.assertEqual(fetched.content_hash, expected_hash)

    # -------------------------------------------------------------------------
    # 16. Unicode Hebrew (niqqud and cantillation)
    # -------------------------------------------------------------------------
    def test_16_unicode_hebrew(self) -> None:
        """Biblical Hebrew with niqqud vowel points and cantillation marks must remain uncorrupted."""
        bhs_source = self.source_registry.register_source(
            canonical_name="Biblia Hebraica Stuttgartensia",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.HEBREW,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
            source_id="SRC-ED-BHS",
        )
        hebrew_verse = "בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃"
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-BHS",
            raw_content=hebrew_verse,
            language=SourceTextLanguage.HEBREW,
        )
        fetched = self.source_text_manager.get_source_text(rec.source_text_id)
        self.assertEqual(fetched.raw_content, hebrew_verse)
        self.assertEqual(fetched.raw_source_string, hebrew_verse)

    # -------------------------------------------------------------------------
    # 17. Unicode Aramaic
    # -------------------------------------------------------------------------
    def test_17_unicode_aramaic(self) -> None:
        """Biblical Aramaic text must be preserved with exact character encoding."""
        aramaic_source = self.source_registry.register_source(
            canonical_name="Biblical Aramaic Corpus (Daniel)",
            source_type=SourceType.SOURCE_LANGUAGE_TEXT,
            language=SourceLanguage.ARAMAIC,
            authority_level=SourceAuthorityLevel.PRIMARY,
            source_id="SRC-ARAMAIC-DAN",
        )
        aramaic_text = "עֲנֵה מַלְכָּא וְאָמַר לְדָנִיֵּאל"
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ARAMAIC-DAN",
            raw_content=aramaic_text,
            language=SourceTextLanguage.ARAMAIC,
        )
        fetched = self.source_text_manager.get_source_text(rec.source_text_id)
        self.assertEqual(fetched.raw_content, aramaic_text)
        self.assertEqual(fetched.language, "ARAMAIC")

    # -------------------------------------------------------------------------
    # 18. Combining marks & NFC/NFD integrity
    # -------------------------------------------------------------------------
    def test_18_combining_marks(self) -> None:
        """Decomposed characters (NFD) must NOT be silently rewritten to composed (NFC) in raw_content."""
        # Decomposed Greek 'alpha' with rough breathing and acute accent (3 codepoints)
        decomposed = "\u03B1\u0314\u0301"  # NFD
        composed = unicodedata.normalize("NFC", decomposed)  # 1 codepoint: ἄ

        self.assertNotEqual(len(decomposed), len(composed))

        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content=decomposed,
            language=SourceTextLanguage.GREEK,
        )
        fetched = self.source_text_manager.get_source_text(rec.source_text_id)
        # raw_content MUST preserve the exact NFD sequence without collapsing to NFC
        self.assertEqual(fetched.raw_content, decomposed)
        self.assertNotEqual(fetched.raw_content, composed)
        # However, normalized_content has the NFC form
        self.assertEqual(fetched.normalized_content, composed)

    # -------------------------------------------------------------------------
    # 19. Raw vs normalized separation
    # -------------------------------------------------------------------------
    def test_19_raw_vs_normalized_separation(self) -> None:
        """Creating a derived normalized representation must leave parent raw content 100% intact."""
        raw_text = "ἐν  ἀρχῇ   ἦν"
        parent = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content=raw_text,
            language=SourceTextLanguage.GREEK,
        )

        normalized_str = "ἐν ἀρχῇ ἦν"
        derived = self.source_text_manager.create_derived_representation(
            parent_source_text_id=parent.source_text_id,
            derived_content=normalized_str,
            representation_type=RepresentationType.NORMALIZED,
        )

        # Parent remains intact
        refetched_parent = self.source_text_manager.get_source_text(parent.source_text_id)
        self.assertEqual(refetched_parent.raw_content, raw_text)

        # Derived artifact points back to parent provenance
        derived_prov = self.provenance_tracker.get_record(derived.provenance_id)
        self.assertIsNotNone(derived_prov)
        self.assertEqual(derived_prov.parent_provenance_id, parent.provenance_id)
        self.assertEqual(derived.representation_type, "NORMALIZED")

    # -------------------------------------------------------------------------
    # 20. Translation firewall
    # -------------------------------------------------------------------------
    def test_20_translation_firewall(self) -> None:
        """MODERN_TRANSLATION source cannot be registered as PRIMARY_WITNESS, CRITICAL_EDITION, or SOURCE_LANGUAGE_TEXT."""
        # API Level checks
        with self.assertRaises(SourceTextTranslationFirewallError):
            self.source_text_manager.register_source_text(
                source_id="SRC-NIV-2011",
                raw_content="In the beginning",
                language=SourceTextLanguage.OTHER,
                source_type=SourceType.PRIMARY_WITNESS,
            )

        with self.assertRaises(SourceTextTranslationFirewallError):
            self.source_text_manager.register_source_text(
                source_id="SRC-NIV-2011",
                raw_content="In the beginning",
                language=SourceTextLanguage.OTHER,
                source_type=SourceType.CRITICAL_EDITION,
            )

        with self.assertRaises(SourceTextTranslationFirewallError):
            self.source_text_manager.register_source_text(
                source_id="SRC-NIV-2011",
                raw_content="In the beginning",
                language=SourceTextLanguage.GREEK,  # Language promotion attempt
            )

        # Direct SQL trigger check
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, source_type, language,
                        raw_source_string, normalized_source_string, sha256_hash,
                        created_at, is_immutable
                    ) VALUES (
                        'ST-BYPASS-FIREWALL', 'SRC-NIV-2011', 'PRIMARY_WITNESS', 'OTHER',
                        'In the beginning', 'In the beginning', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                        'now', 1
                    );
                    """
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 21. Ancient translation distinction
    # -------------------------------------------------------------------------
    def test_21_ancient_translation_distinction(self) -> None:
        """Ancient translations (Vulgate) remain ANCIENT_TRANSLATION and cannot masquerade as Greek/Hebrew primary originals."""
        # Valid registration as ancient translation
        vulgate_text = "In principio creavit Deus caelum et terram."
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-VULGATE-STUTT",
            raw_content=vulgate_text,
            language=SourceTextLanguage.LATIN,
            source_type=SourceType.ANCIENT_TRANSLATION,
        )
        self.assertEqual(rec.source_type, "ANCIENT_TRANSLATION")
        self.assertEqual(rec.language, "LATIN")

        # Attempt to convert to PRIMARY_WITNESS or CRITICAL_EDITION must fail
        with self.assertRaises(SourceTextTranslationFirewallError):
            self.source_text_manager.register_source_text(
                source_id="SRC-VULGATE-STUTT",
                raw_content=vulgate_text,
                language=SourceTextLanguage.LATIN,
                source_type=SourceType.PRIMARY_WITNESS,
            )

    # -------------------------------------------------------------------------
    # 22. Witness distinction
    # -------------------------------------------------------------------------
    def test_22_witness_distinction(self) -> None:
        """Primary manuscript witness correctly records source_type='PRIMARY_WITNESS' and preserves witness identity."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-WIT-SINAITICUS",
            raw_content="ΕΝΑΡΧΗΗΝΟΛΟΓΟΣ",
            language=SourceTextLanguage.GREEK,
            source_type=SourceType.PRIMARY_WITNESS,
        )
        self.assertEqual(rec.source_type, "PRIMARY_WITNESS")
        self.assertEqual(rec.source_id, "SRC-WIT-SINAITICUS")

    # -------------------------------------------------------------------------
    # 23. Critical edition distinction
    # -------------------------------------------------------------------------
    def test_23_critical_edition_distinction(self) -> None:
        """Critical edition correctly records source_type='CRITICAL_EDITION' and distinguishes from manuscript witness."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Ἐν ἀρχῇ ἦν ὁ λόγος",
            language=SourceTextLanguage.GREEK,
            source_type=SourceType.CRITICAL_EDITION,
        )
        self.assertEqual(rec.source_type, "CRITICAL_EDITION")
        self.assertEqual(rec.source_id, "SRC-ED-NA28")

    # -------------------------------------------------------------------------
    # 24. Transaction rollback
    # -------------------------------------------------------------------------
    def test_24_rollback(self) -> None:
        """Constraint failure inside a transactional block leaves zero partial state."""
        count_before = len(self.source_text_manager.list_source_texts())

        # Attempt transaction with a duplicate ID or trigger violation
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, source_type, language,
                        raw_source_string, normalized_source_string, sha256_hash,
                        created_at, is_immutable
                    ) VALUES (
                        'ST-RB-1', 'SRC-ED-NA28', 'CRITICAL_EDITION', 'GREEK',
                        'Valid line', 'Valid line', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                        'now', 1
                    );
                    """
                )
                # Intentionally trigger Translation Firewall violation on second insert
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, source_type, language,
                        raw_source_string, normalized_source_string, sha256_hash,
                        created_at, is_immutable
                    ) VALUES (
                        'ST-RB-2', 'SRC-NIV-2011', 'PRIMARY_WITNESS', 'OTHER',
                        'Boom', 'Boom', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
                        'now', 1
                    );
                    """
                )
        except sqlite3.IntegrityError:
            pass

        count_after = len(self.source_text_manager.list_source_texts())
        self.assertEqual(count_after, count_before, "Failed transaction must roll back cleanly.")
        with self.assertRaises(SourceTextNotFoundError):
            self.source_text_manager.get_source_text("ST-RB-1")

    # -------------------------------------------------------------------------
    # 25. Concurrent registration
    # -------------------------------------------------------------------------
    def test_25_concurrent_registration(self) -> None:
        """Multi-threaded concurrent registrations must safely serialize without corrupting state."""
        errors: List[Exception] = []

        def worker(thread_idx: int) -> None:
            eng = DatabaseEngine(self.config)
            try:
                mgr = SourceTextManager(eng)
                for i in range(5):
                    content = f"Concurrent text from thread {thread_idx} item {i}"
                    mgr.register_source_text(
                        source_id="SRC-ED-NA28",
                        raw_content=content,
                        language=SourceTextLanguage.GREEK,
                        source_text_id=f"ST-CONCUR-{thread_idx}-{i}",
                    )
            except Exception as e:
                errors.append(e)
            finally:
                eng.close()

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent workers encountered errors: {errors}")
        records = self.source_text_manager.list_source_texts(source_id="SRC-ED-NA28")
        concur_records = [r for r in records if r.source_text_id.startswith("ST-CONCUR-")]
        self.assertEqual(len(concur_records), 20)

    # -------------------------------------------------------------------------
    # 26. Legacy database untouched
    # -------------------------------------------------------------------------
    def test_26_legacy_db_untouched(self) -> None:
        """Legacy knowledge base database at /home/ubuntu/.polya/polya_index.db must remain untouched."""
        post_hash = self._compute_file_sha256(self.legacy_db_path)
        self.assertEqual(
            self.legacy_db_hash,
            post_hash,
            "Legacy database /home/ubuntu/.polya/polya_index.db was modified during Source Text testing!",
        )

    # -------------------------------------------------------------------------
    # 27. Atomic registration leaves ZERO orphaned provenance or version rows (D6)
    # -------------------------------------------------------------------------
    def test_27_atomic_rollback_leaves_no_orphaned_provenance_or_version(self) -> None:
        """When source_texts insertion fails (e.g. invalid FK), provenance and version records must roll back."""
        with self.engine.connect() as conn:
            prov_count_before = conn.execute("SELECT count(*) FROM provenance_records;").fetchone()[0]
            ver_count_before = conn.execute("SELECT count(*) FROM object_versions;").fetchone()[0]

        # Attempt to register with a non-existent passage_id to trigger FK failure on insert
        with self.assertRaises(SourceTextOrphanError):
            self.source_text_manager.register_source_text(
                source_id="SRC-ED-NA28",
                raw_content="Text with bogus passage FK",
                language=SourceTextLanguage.GREEK,
                passage_id="PASS-NON-EXISTENT",
            )

        with self.engine.connect() as conn:
            prov_count_after = conn.execute("SELECT count(*) FROM provenance_records;").fetchone()[0]
            ver_count_after = conn.execute("SELECT count(*) FROM object_versions;").fetchone()[0]

        self.assertEqual(prov_count_after, prov_count_before, "Failed registration must not leak provenance records.")
        self.assertEqual(ver_count_after, ver_count_before, "Failed registration must not leak object_versions records.")

    # -------------------------------------------------------------------------
    # 28. Adversarial immutability probes on all columns (D1, D10)
    # -------------------------------------------------------------------------
    def test_28_adversarial_immutability_probes(self) -> None:
        """Verify that every single column in source_texts is rejected if mutated via SQL."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Adversarial probe content",
            language=SourceTextLanguage.GREEK,
        )

        columns_to_probe = [
            ("source_id", "'SRC-WIT-SINAITICUS'"),
            ("version_id", "'VER-FORGED'"),
            ("provenance_id", "'PROV-FORGED'"),
            ("source_type", "'PRIMARY_WITNESS'"),
            ("language", "'LATIN'"),
            ("representation_type", "'TRANSFORMED'"),
            ("encoding", "'ASCII'"),
            ("metadata_json", "'{\"hacked\": true}'"),
            ("is_immutable", "0"),
        ]

        for col, new_val in columns_to_probe:
            with self.engine.transaction() as conn:
                with self.assertRaises(sqlite3.IntegrityError, msg=f"Column {col} mutation should be blocked"):
                    conn.execute(f"UPDATE source_texts SET {col} = {new_val} WHERE source_text_id = '{rec.source_text_id}';")

    # -------------------------------------------------------------------------
    # 29. Translation firewall probes & hash uniqueness (D3, D5)
    # -------------------------------------------------------------------------
    def test_29_translation_firewall_probes_and_hash_uniqueness(self) -> None:
        """Verify duplicate SHA-256 is rejected and modern translation cannot masquerade as Greek."""
        rec = self.source_text_manager.register_source_text(
            source_id="SRC-ED-NA28",
            raw_content="Unique content for hash test",
            language=SourceTextLanguage.GREEK,
        )

        # Duplicate SHA-256 insert attempt via direct SQL must fail UNIQUE constraint
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, source_type, language,
                        raw_source_string, normalized_source_string, sha256_hash,
                        created_at, is_immutable
                    ) VALUES (
                        'ST-DUP-HASH', 'SRC-ED-NA28', 'CRITICAL_EDITION', 'GREEK',
                        'Different string', 'Different string', ?,
                        'now', 1
                    );
                    """,
                    (rec.sha256_hash,),
                )

        # Direct SQL attempt to insert modern translation with Greek language must fail Translation Firewall
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    """
                    INSERT INTO source_texts (
                        source_text_id, source_id, source_type, language,
                        raw_source_string, normalized_source_string, sha256_hash,
                        created_at, is_immutable
                    ) VALUES (
                        'ST-MODERN-GREEK', 'SRC-NIV-2011', 'MODERN_TRANSLATION', 'GREEK',
                        'Greek NIV text', 'Greek NIV text', '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
                        'now', 1
                    );
                    """
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
