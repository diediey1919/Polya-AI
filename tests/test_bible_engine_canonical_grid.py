"""
Isolated Test Suite for Canonical Passages Grid Generator & Versification Mapping (Task 5E-A).

Verifies manifest validation, atomic generation, conflict detection, deterministic IDs/sort_order,
idempotency, transaction rollback, FK integrity, and structural versification mapping.
Zero access to production DB.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from bible_engine.canonical_grid import (
    CanonicalGridConflictError,
    CanonicalGridError,
    CanonicalGridGenerator,
    CanonicalGridValidator,
    ManifestChecksumMismatchError,
    ManifestDuplicateCoordinateError,
    ManifestIncompleteError,
    ManifestInvalidOrderError,
    ManifestValidationError,
    compute_manifest_checksum,
    compute_passage_id,
    compute_provisional_pericope_id,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.migrations import MigrationRunner, compute_association_id
from bible_engine.versification_mapping import (
    InvalidMappingCoordinateError,
    InvalidMappingStructureError,
    VersificationMapper,
    VersificationMappingType,
    compute_mapping_id,
    compute_rule_hash,
)


def make_synthetic_test_manifest(
    book_specs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Construct an explicitly labeled synthetic test fixture.
    NOT PRODUCTION CANONICAL DATA.
    """
    books_copy = copy.deepcopy(book_specs)
    checksum = compute_manifest_checksum(books_copy)
    return {
        "manifest_id": "MANIFEST-SYNTHETIC-TEST-GRID-v1.0",
        "canon_id": "CANON-TEST-SYNTHETIC",
        "edition": "SYNTHETIC_TEST_FIXTURE_DO_NOT_USE_IN_PRODUCTION",
        "checksum_sha256": checksum,
        "books": books_copy,
    }


CANONICAL_66_BOOKS_FIXTURE = [
    ("GEN", "TEST-OT", 1, "Kejadian", "Genesis", "HEBREW", 50),
    ("EXO", "TEST-OT", 2, "Keluaran", "Exodus", "HEBREW", 40),
    ("LEV", "TEST-OT", 3, "Imamat", "Leviticus", "HEBREW", 27),
    ("NUM", "TEST-OT", 4, "Bilangan", "Numbers", "HEBREW", 36),
    ("DEU", "TEST-OT", 5, "Ulangan", "Deuteronomy", "HEBREW", 34),
    ("JOS", "TEST-OT", 6, "Yosua", "Joshua", "HEBREW", 24),
    ("JDG", "TEST-OT", 7, "Hakim-hakim", "Judges", "HEBREW", 21),
    ("RUT", "TEST-OT", 8, "Rut", "Ruth", "HEBREW", 4),
    ("1SA", "TEST-OT", 9, "1 Samuel", "I Samuel", "HEBREW", 31),
    ("2SA", "TEST-OT", 10, "2 Samuel", "II Samuel", "HEBREW", 24),
    ("1KI", "TEST-OT", 11, "1 Raja-raja", "I Kings", "HEBREW", 22),
    ("2KI", "TEST-OT", 12, "2 Raja-raja", "II Kings", "HEBREW", 25),
    ("1CH", "TEST-OT", 13, "1 Tawarikh", "I Chronicles", "HEBREW", 29),
    ("2CH", "TEST-OT", 14, "2 Tawarikh", "II Chronicles", "HEBREW", 36),
    ("EZR", "TEST-OT", 15, "Ezra", "Ezra", "HEBREW", 10),
    ("NEH", "TEST-OT", 16, "Nehemia", "Nehemiah", "HEBREW", 13),
    ("EST", "TEST-OT", 17, "Ester", "Esther", "HEBREW", 10),
    ("JOB", "TEST-OT", 18, "Ayub", "Job", "HEBREW", 42),
    ("PSA", "TEST-OT", 19, "Mazmur", "Psalms", "HEBREW", 150),
    ("PRO", "TEST-OT", 20, "Amsal", "Proverbs", "HEBREW", 31),
    ("ECC", "TEST-OT", 21, "Pengkhotbah", "Ecclesiastes", "HEBREW", 12),
    ("SNG", "TEST-OT", 22, "Kidung Agung", "Song of Solomon", "HEBREW", 8),
    ("ISA", "TEST-OT", 23, "Yesaya", "Isaiah", "HEBREW", 66),
    ("JER", "TEST-OT", 24, "Yeremia", "Jeremiah", "HEBREW", 52),
    ("LAM", "TEST-OT", 25, "Ratapan", "Lamentations", "HEBREW", 5),
    ("EZK", "TEST-OT", 26, "Yehezkiel", "Ezekiel", "HEBREW", 48),
    ("DAN", "TEST-OT", 27, "Daniel", "Daniel", "HEBREW", 12),
    ("HOS", "TEST-OT", 28, "Hosea", "Hosea", "HEBREW", 14),
    ("JOL", "TEST-OT", 29, "Yoel", "Joel", "HEBREW", 3),
    ("AMO", "TEST-OT", 30, "Amos", "Amos", "HEBREW", 9),
    ("OBA", "TEST-OT", 31, "Obaja", "Obadiah", "HEBREW", 1),
    ("JON", "TEST-OT", 32, "Yunus", "Jonah", "HEBREW", 4),
    ("MIC", "TEST-OT", 33, "Mikha", "Micah", "HEBREW", 7),
    ("NAM", "TEST-OT", 34, "Nahum", "Nahum", "HEBREW", 3),
    ("HAB", "TEST-OT", 35, "Habakuk", "Habakkuk", "HEBREW", 3),
    ("ZEP", "TEST-OT", 36, "Zefanya", "Zephaniah", "HEBREW", 3),
    ("HAG", "TEST-OT", 37, "Hagai", "Haggai", "HEBREW", 2),
    ("ZEC", "TEST-OT", 38, "Zakharia", "Zechariah", "HEBREW", 14),
    ("MAL", "TEST-OT", 39, "Maleakhi", "Malachi", "HEBREW", 4),
    ("MAT", "TEST-NT", 40, "Matius", "Matthew", "GREEK", 28),
    ("MRK", "TEST-NT", 41, "Markus", "Mark", "GREEK", 16),
    ("LUK", "TEST-NT", 42, "Lukas", "Luke", "GREEK", 24),
    ("JOH", "TEST-NT", 43, "Yohanes", "John", "GREEK", 21),
    ("ACT", "TEST-NT", 44, "Kisah Para Rasul", "Acts", "GREEK", 28),
    ("ROM", "TEST-NT", 45, "Roma", "Romans", "GREEK", 16),
    ("1CO", "TEST-NT", 46, "1 Korintus", "I Corinthians", "GREEK", 16),
    ("2CO", "TEST-NT", 47, "2 Korintus", "II Corinthians", "GREEK", 13),
    ("GAL", "TEST-NT", 48, "Galatia", "Galatians", "GREEK", 6),
    ("EPH", "TEST-NT", 49, "Efesus", "Ephesians", "GREEK", 6),
    ("PHP", "TEST-NT", 50, "Filipi", "Philippians", "GREEK", 4),
    ("COL", "TEST-NT", 51, "Kolose", "Colossians", "GREEK", 4),
    ("1TH", "TEST-NT", 52, "1 Tesalonika", "I Thessalonians", "GREEK", 5),
    ("2TH", "TEST-NT", 53, "2 Tesalonika", "II Thessalonians", "GREEK", 3),
    ("1TI", "TEST-NT", 54, "1 Timotius", "I Timothy", "GREEK", 6),
    ("2TI", "TEST-NT", 55, "2 Timotius", "II Timothy", "GREEK", 4),
    ("TIT", "TEST-NT", 56, "Titus", "Titus", "GREEK", 3),
    ("PHM", "TEST-NT", 57, "Filemon", "Philemon", "GREEK", 1),
    ("HEB", "TEST-NT", 58, "Ibrani", "Hebrews", "GREEK", 13),
    ("JAS", "TEST-NT", 59, "Yakobus", "James", "GREEK", 5),
    ("1PE", "TEST-NT", 60, "1 Petrus", "I Peter", "GREEK", 5),
    ("2PE", "TEST-NT", 61, "2 Petrus", "II Peter", "GREEK", 3),
    ("1JN", "TEST-NT", 62, "1 Yohanes", "I John", "GREEK", 5),
    ("2JN", "TEST-NT", 63, "2 Yohanes", "II John", "GREEK", 1),
    ("3JN", "TEST-NT", 64, "3 Yohanes", "III John", "GREEK", 1),
    ("JUD", "TEST-NT", 65, "Yudas", "Jude", "GREEK", 1),
    ("REV", "TEST-NT", 66, "Wahyu", "Revelation of John", "GREEK", 22),
]


class TestCanonicalGridAndVersification(unittest.TestCase):
    """Hermetic unit and integration tests for canonical grid generation and versification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_tmp = Path(__file__).resolve().parent / "_test_tmp_grid_5e"
        cls.base_tmp.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.base_tmp.exists():
            try:
                shutil.rmtree(cls.base_tmp)
            except OSError:
                pass

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))
        self.db_path = os.path.join(self.temp_dir.name, "test_grid.db")
        self.migrations_dir = Path(self.temp_dir.name) / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        repo_schemas = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        # Copy migrations up to 026
        for sql_file in sorted(repo_schemas.glob("*.sql")):
            shutil.copyfile(sql_file, self.migrations_dir / sql_file.name)

        self.config = DatabaseConfig(
            db_path=self.db_path,
            migrations_dir=str(self.migrations_dir),
            schema_path=str(self.migrations_dir / "001_initial_schema.sql"),
        )
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine, migrations_dir=self.migrations_dir)
        self.runner.apply_pending()

        # Seed essential baseline structures
        self._seed_baseline()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            "INSERT OR IGNORE INTO canons (canon_id, name, created_at) "
            "VALUES ('CANON-PROT', 'Protestant Canon', '2026-10-01T00:00:00Z');"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments (testament_id, canon_id, name, sort_order) "
            "VALUES ('TEST-OT', 'CANON-PROT', 'Old Testament', 1);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments (testament_id, canon_id, name, sort_order) "
            "VALUES ('TEST-NT', 'CANON-PROT', 'New Testament', 2);"
        )
        # Seed 3 controlled test books
        books_data = [
            ("GEN", "TEST-OT", 1, "Kejadian", "Genesis", "HEBREW", 2),
            ("EXO", "TEST-OT", 2, "Keluaran", "Exodus", "HEBREW", 1),
            ("MAT", "TEST-NT", 40, "Matius", "Matthew", "GREEK", 2),
        ]
        for b_id, t_id, c_order, std_name, en_name, lang, ch_count in books_data:
            conn.execute(
                """
                INSERT OR IGNORE INTO books (
                    book_id, testament_id, canonical_order, standard_name, english_name,
                    original_primary_language, chapter_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (b_id, t_id, c_order, std_name, en_name, lang, ch_count),
            )
        # Ensure segmentation witness exists
        conn.execute(
            """
            INSERT OR IGNORE INTO segmentation_witnesses (
                segmentation_id, witness_name, witness_type, authority_level,
                license, description, is_active_baseline, source_provenance, created_at
            ) VALUES (
                'WIT-SEG-PROVISIONAL-CHAPTER', 'Provisional Chapter Baseline',
                'CANONICAL_PARTITION', 'PROVISIONAL', 'Public Domain',
                'Provisional baseline', 1, 'CANONICAL_CHAPTER_FALLBACK', '2026-10-01T00:00:00Z'
            );
            """
        )
        conn.commit()

    def _create_isolated_66_books_db(self):
        temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))
        db_path = os.path.join(temp_dir.name, "canon66_test.db")
        migrations_dir = Path(temp_dir.name) / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        repo_schemas = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for sql_file in sorted(repo_schemas.glob("*.sql")):
            shutil.copyfile(sql_file, migrations_dir / sql_file.name)

        config = DatabaseConfig(
            db_path=db_path,
            migrations_dir=str(migrations_dir),
            schema_path=str(migrations_dir / "001_initial_schema.sql"),
        )
        engine = DatabaseEngine(config)
        runner = MigrationRunner(engine, migrations_dir=migrations_dir)
        runner.apply_pending()

        conn = engine.get_write_connection()
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            "INSERT OR IGNORE INTO canons (canon_id, name, created_at) "
            "VALUES ('CANON-PROTESTANT-66', 'Protestant Canon (66 Books)', '2026-10-01T00:00:00Z');"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments (testament_id, canon_id, name, sort_order) "
            "VALUES ('TEST-OT', 'CANON-PROTESTANT-66', 'Perjanjian Lama', 1);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments (testament_id, canon_id, name, sort_order) "
            "VALUES ('TEST-NT', 'CANON-PROTESTANT-66', 'Perjanjian Baru', 2);"
        )
        for row in CANONICAL_66_BOOKS_FIXTURE:
            conn.execute(
                """
                INSERT OR IGNORE INTO books (
                    book_id, testament_id, canonical_order, standard_name, english_name,
                    original_primary_language, chapter_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                row,
            )
        conn.execute(
            """
            INSERT OR IGNORE INTO segmentation_witnesses (
                segmentation_id, witness_name, witness_type, authority_level,
                license, description, is_active_baseline, source_provenance, created_at
            ) VALUES (
                'WIT-SEG-PROVISIONAL-CHAPTER', 'Provisional Chapter Baseline',
                'CANONICAL_PARTITION', 'PROVISIONAL', 'Public Domain',
                'Provisional baseline', 1, 'CANONICAL_CHAPTER_FALLBACK', '2026-10-01T00:00:00Z'
            );
            """
        )
        conn.commit()
        return engine, temp_dir

    def _sample_valid_manifest_books(self) -> List[Dict[str, Any]]:
        return [
            {
                "book_id": "GEN",
                "canonical_order": 1,
                "chapter_count": 2,
                "chapters": [
                    {"chapter": 1, "verse_count": 3},
                    {"chapter": 2, "verse_count": 2},
                ],
            },
            {
                "book_id": "EXO",
                "canonical_order": 2,
                "chapter_count": 1,
                "chapters": [
                    {"chapter": 1, "verse_count": 4},
                ],
            },
            {
                "book_id": "MAT",
                "canonical_order": 40,
                "chapter_count": 2,
                "chapters": [
                    {"chapter": 1, "verse_count": 2},
                    {"chapter": 2, "verse_count": 3},
                ],
            },
        ]

    # -------------------------------------------------------------------------
    # 1. MANIFEST VALIDATION TESTS
    # -------------------------------------------------------------------------
    def test_validate_manifest_success(self) -> None:
        conn = self.engine.get_read_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

        self.assertEqual(validated.total_books, 3)
        self.assertEqual(validated.total_chapters, 5)
        self.assertEqual(validated.total_verses, 14)
        self.assertEqual(validated.books[0].book_id, "GEN")
        self.assertEqual(validated.books[0].chapters[0].verse_count, 3)

    def test_reject_checksum_mismatch(self) -> None:
        conn = self.engine.get_read_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        manifest_data["checksum_sha256"] = "deadbeef" * 8

        with self.assertRaises(ManifestChecksumMismatchError):
            CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

    def test_reject_incomplete_books(self) -> None:
        conn = self.engine.get_read_connection()
        # Drop MAT
        books = self._sample_valid_manifest_books()[:2]
        manifest_data = make_synthetic_test_manifest(books)

        with self.assertRaises(ManifestIncompleteError):
            CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

    def test_reject_incomplete_chapters(self) -> None:
        conn = self.engine.get_read_connection()
        books = self._sample_valid_manifest_books()
        # GEN has 2 chapters, give only 1
        books[0]["chapters"] = [{"chapter": 1, "verse_count": 3}]
        manifest_data = make_synthetic_test_manifest(books)

        with self.assertRaises(ManifestIncompleteError):
            CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

    def test_reject_invalid_book_order(self) -> None:
        conn = self.engine.get_read_connection()
        books = self._sample_valid_manifest_books()
        # Invert GEN and EXO
        books[0], books[1] = books[1], books[0]
        manifest_data = make_synthetic_test_manifest(books)

        with self.assertRaises(ManifestInvalidOrderError):
            CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

    def test_reject_duplicate_coordinates(self) -> None:
        conn = self.engine.get_read_connection()
        books = self._sample_valid_manifest_books()
        # Duplicate chapter number in GEN
        books[0]["chapters"] = [
            {"chapter": 1, "verse_count": 2},
            {"chapter": 1, "verse_count": 2},
        ]
        manifest_data = make_synthetic_test_manifest(books)

        with self.assertRaises(ManifestInvalidOrderError):
            CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

    # -------------------------------------------------------------------------
    # 2. GENERATION EXECUTION, IDEMPOTENCY, & INTEGRITY TESTS
    # -------------------------------------------------------------------------
    def test_generation_execution_and_schema_integrity(self) -> None:
        conn = self.engine.get_write_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

        generator = CanonicalGridGenerator(conn)
        summary = generator.generate(validated)

        self.assertEqual(summary.books_processed, 3)
        self.assertEqual(summary.pericopes_inserted, 5)
        self.assertEqual(summary.passages_inserted, 14)
        self.assertEqual(summary.associations_inserted, 14)
        self.assertEqual(summary.total_verses, 14)

        # Integrity Checks
        int_check = [r[0] for r in conn.execute("PRAGMA integrity_check;").fetchall()]
        self.assertEqual(int_check, ["ok"])

        fk_check = conn.execute("PRAGMA foreign_key_check;").fetchall()
        self.assertEqual(len(fk_check), 0)

        # Verify deterministic IDs
        first_pas = conn.execute(
            "SELECT passage_id, pericope_id, book_id, chapter, verse, sort_order FROM passages WHERE sort_order = 1;"
        ).fetchone()
        self.assertEqual(first_pas[0], "PAS-GEN.1.1")
        self.assertEqual(first_pas[1], "PER-PROV-GEN-CH001")
        self.assertEqual(first_pas[2], "GEN")
        self.assertEqual(first_pas[3], 1)
        self.assertEqual(first_pas[4], 1)
        self.assertEqual(first_pas[5], 1)

        last_pas = conn.execute(
            "SELECT passage_id, pericope_id, sort_order FROM passages ORDER BY sort_order DESC LIMIT 1;"
        ).fetchone()
        self.assertEqual(last_pas[0], "PAS-MAT.2.3")
        self.assertEqual(last_pas[1], "PER-PROV-MAT-CH002")
        self.assertEqual(last_pas[2], 14)

        # Verify boundary positions in pericope_passages
        p_bound = conn.execute(
            "SELECT boundary_position FROM pericope_passages WHERE passage_id = 'PAS-GEN.1.1';"
        ).fetchone()[0]
        self.assertEqual(p_bound, "START_BOUNDARY")

        p_end = conn.execute(
            "SELECT boundary_position FROM pericope_passages WHERE passage_id = 'PAS-GEN.1.3';"
        ).fetchone()[0]
        self.assertEqual(p_end, "END_BOUNDARY")

    def test_idempotent_replay_preserves_state(self) -> None:
        conn = self.engine.get_write_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

        generator = CanonicalGridGenerator(conn)
        # First execution
        summary1 = generator.generate(validated)
        self.assertEqual(summary1.passages_inserted, 14)

        # Second identical execution
        summary2 = generator.generate(validated)
        self.assertEqual(summary2.passages_inserted, 0)
        self.assertEqual(summary2.pericopes_inserted, 0)
        self.assertEqual(summary2.associations_inserted, 0)
        self.assertEqual(summary2.passages_replayed, 14)
        self.assertEqual(summary2.pericopes_replayed, 5)
        self.assertEqual(summary2.associations_replayed, 14)

        # Verify total rows remained constant
        total_p = conn.execute("SELECT count(*) FROM passages;").fetchone()[0]
        self.assertEqual(total_p, 14)

    def test_conflict_detection_aborts_without_insert_or_ignore(self) -> None:
        conn = self.engine.get_write_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

        generator = CanonicalGridGenerator(conn)
        generator.generate(validated)

        # Mutate one pericope in db to simulate conflicting preexisting data
        conn.execute(
            "UPDATE pericopes SET end_verse = 999 WHERE pericope_id = 'PER-PROV-GEN-CH001';"
        )
        conn.commit()

        # Re-running generator must raise CanonicalGridConflictError and NOT silently overwrite/ignore
        with self.assertRaises(CanonicalGridConflictError):
            generator.generate(validated)

    def test_transaction_atomic_rollback_on_failure(self) -> None:
        conn = self.engine.get_write_connection()
        manifest_data = make_synthetic_test_manifest(self._sample_valid_manifest_books())
        validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

        # Remove segmentation witness to induce guaranteed failure during execution
        conn.execute("DELETE FROM segmentation_witnesses WHERE segmentation_id = 'WIT-SEG-PROVISIONAL-CHAPTER';")
        conn.commit()

        generator = CanonicalGridGenerator(conn)
        with self.assertRaises(CanonicalGridError):
            generator.generate(validated)

        # Assert zero rows entered passages or pericopes
        p_count = conn.execute("SELECT count(*) FROM passages;").fetchone()[0]
        per_count = conn.execute("SELECT count(*) FROM pericopes;").fetchone()[0]
        self.assertEqual(p_count, 0)
        self.assertEqual(per_count, 0)

    # -------------------------------------------------------------------------
    # 3. VERSIFICATION MAPPING STRUCTURAL TESTS (ISOLATED MODULE)
    # -------------------------------------------------------------------------
    def test_versification_mapping_one_to_one(self) -> None:
        rule = {"source": "WLC", "rule": "exact_identity_alignment"}
        entry = VersificationMapper.build_one_to_one(
            verse_record_id="REC-WLC-GEN-1-1",
            canonical_passage_id="PAS-GEN.1.1",
            mapping_provenance_id="PROV-TEST-001",
            rule_payload=rule,
        )
        self.assertEqual(entry.mapping_type, VersificationMappingType.EXACT_ONE_TO_ONE)
        self.assertEqual(entry.sub_verse, "")
        self.assertEqual(len(entry.mapping_id), 64)

    def test_versification_mapping_split(self) -> None:
        rule = {"source": "LXX", "rule": "split_verse_boundary"}
        targets = [("PAS-GEN.1.1", "a"), ("PAS-GEN.1.2", "b")]
        entries = VersificationMapper.build_split(
            verse_record_id="REC-LXX-GEN-1-1",
            targets=targets,
            mapping_provenance_id="PROV-TEST-002",
            rule_payload=rule,
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].mapping_type, VersificationMappingType.ONE_TO_MANY_SPLIT)
        self.assertEqual(entries[0].sub_verse, "a")
        self.assertEqual(entries[1].sub_verse, "b")

    def test_versification_mapping_merge(self) -> None:
        rule = {"source": "MT", "rule": "merge_inscriptional_verses"}
        sources = ["REC-MT-PSA-51-1", "REC-MT-PSA-51-2"]
        entries = VersificationMapper.build_merge(
            source_verse_record_ids=sources,
            canonical_passage_id="PAS-PSA.51.1",
            mapping_provenance_id="PROV-TEST-003",
            rule_payload=rule,
        )
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].mapping_type, VersificationMappingType.MANY_TO_ONE_MERGE)
        self.assertEqual(entries[0].sub_verse, "src_1")
        self.assertEqual(entries[1].sub_verse, "src_2")

    def test_versification_mapping_rejects_invalid_inputs(self) -> None:
        rule = {"rule": "test"}
        # Invalid passage prefix
        with self.assertRaises(InvalidMappingCoordinateError):
            VersificationMapper.build_one_to_one(
                verse_record_id="REC-001",
                canonical_passage_id="INVALID-PREFIX.1.1",
                mapping_provenance_id="PROV-001",
                rule_payload=rule,
            )

        # Split with less than 2 targets
        with self.assertRaises(InvalidMappingStructureError):
            VersificationMapper.build_split(
                verse_record_id="REC-001",
                targets=[("PAS-GEN.1.1", "a")],
                mapping_provenance_id="PROV-001",
                rule_payload=rule,
            )

        # Merge with less than 2 sources
        with self.assertRaises(InvalidMappingStructureError):
            VersificationMapper.build_merge(
                source_verse_record_ids=["REC-001"],
                canonical_passage_id="PAS-GEN.1.1",
                mapping_provenance_id="PROV-001",
                rule_payload=rule,
            )

    def test_production_canonical_manifest_validation(self) -> None:
        """Validate production 66-book manifest against schema, invariants, and DB books."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        schema_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_manifest.schema.json"
        )
        self.assertTrue(manifest_path.exists(), f"Manifest missing at {manifest_path}")
        self.assertTrue(schema_path.exists(), f"Schema missing at {schema_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_data = json.load(f)

        # 1. JSON Schema validation
        import jsonschema
        jsonschema.validate(instance=manifest_data, schema=schema_data)

        # 2. CanonicalGridValidator against isolated 66 books database
        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

            self.assertEqual(validated.total_books, 66)
            self.assertEqual(validated.total_chapters, 1189)
            self.assertEqual(validated.total_verses, 31102)
            self.assertEqual(manifest_data["versification_system"], "PROTESTANT_KJV_STANDARD")
            self.assertEqual(manifest_data["license"], "GPL-2.0")

            # Verify all verse counts are strictly positive and chapters match DB
            cursor = conn.cursor()
            db_books = {r[0]: r[1] for r in cursor.execute("SELECT book_id, chapter_count FROM books").fetchall()}
            for b in validated.books:
                self.assertEqual(len(b.chapters), db_books[b.book_id])
                for ch in b.chapters:
                    self.assertGreater(ch.verse_count, 0)
        finally:
            engine.close()
            tmp.cleanup()

    def test_production_manifest_tamper_fails_checksum(self) -> None:
        """Verify that altering a single verse count breaks manifest checksum validation."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        # Tamper: change Genesis 1:1 verse count by +1
        tampered_data = json.loads(json.dumps(manifest_data))
        tampered_data["books"][0]["chapters"][0]["verse_count"] += 1

        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            with self.assertRaises(ManifestChecksumMismatchError):
                CanonicalGridValidator.validate(tampered_data, conn, require_full_canon=True)
        finally:
            engine.close()
            tmp.cleanup()

    def test_production_manifest_missing_book_rejected(self) -> None:
        """Verify that dropping a book from the 66-book manifest raises ManifestIncompleteError."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        from bible_engine.canonical_grid import compute_manifest_payload_checksum

        tampered_data = json.loads(json.dumps(manifest_data))
        tampered_data["books"] = tampered_data["books"][:-1]  # remove Revelation
        tampered_data["total_books"] = 65
        tampered_data["manifest_checksum_sha256"] = compute_manifest_payload_checksum(tampered_data)

        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            with self.assertRaises(ManifestIncompleteError):
                CanonicalGridValidator.validate(tampered_data, conn, require_full_canon=True)
        finally:
            engine.close()
            tmp.cleanup()

    def test_production_manifest_missing_chapter_rejected(self) -> None:
        """Verify that missing a chapter in a book raises ManifestValidationError."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        from bible_engine.canonical_grid import compute_manifest_payload_checksum

        tampered_data = json.loads(json.dumps(manifest_data))
        # Remove Genesis chapter 50
        tampered_data["books"][0]["chapters"] = tampered_data["books"][0]["chapters"][:-1]
        tampered_data["manifest_checksum_sha256"] = compute_manifest_payload_checksum(tampered_data)

        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            with self.assertRaises(ManifestValidationError):
                CanonicalGridValidator.validate(tampered_data, conn, require_full_canon=True)
        finally:
            engine.close()
            tmp.cleanup()

    def test_production_manifest_invalid_order_rejected(self) -> None:
        """Verify that out-of-order books raise ManifestInvalidOrderError."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        from bible_engine.canonical_grid import compute_manifest_payload_checksum

        tampered_data = json.loads(json.dumps(manifest_data))
        # Swap Genesis (index 0) and Exodus (index 1)
        tampered_data["books"][0], tampered_data["books"][1] = (
            tampered_data["books"][1],
            tampered_data["books"][0],
        )
        tampered_data["manifest_checksum_sha256"] = compute_manifest_payload_checksum(tampered_data)

        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            with self.assertRaises(ManifestInvalidOrderError):
                CanonicalGridValidator.validate(tampered_data, conn, require_full_canon=True)
        finally:
            engine.close()
            tmp.cleanup()

    def test_production_manifest_duplicate_coordinate_rejected(self) -> None:
        """Verify that duplicate chapter coordinates raise ManifestDuplicateCoordinateError."""
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        from bible_engine.canonical_grid import compute_manifest_payload_checksum

        tampered_data = json.loads(json.dumps(manifest_data))
        # Duplicate Genesis chapter 1
        tampered_data["books"][0]["chapters"].append({"chapter": 1, "verse_count": 31})
        tampered_data["manifest_checksum_sha256"] = compute_manifest_payload_checksum(tampered_data)

        engine, tmp = self._create_isolated_66_books_db()
        try:
            conn = engine.get_write_connection()
            with self.assertRaises((ManifestDuplicateCoordinateError, ManifestValidationError)):
                CanonicalGridValidator.validate(tampered_data, conn, require_full_canon=True)
        finally:
            engine.close()
            tmp.cleanup()

    def test_stepbible_tvtms_artifact_license_separation(self) -> None:
        """Verify STEPBible TVTMS artifact exists with CC-BY-4.0 license, separate from GPL-2.0."""
        tvtms_path = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "canonical"
            / "stepbible_tvtms_mappings.json"
        )
        self.assertTrue(tvtms_path.exists(), f"TVTMS artifact missing at {tvtms_path}")

        with open(tvtms_path, "r", encoding="utf-8") as f:
            tvtms_data = json.load(f)

        self.assertEqual(tvtms_data["license"], "CC-BY-4.0")
        self.assertIn("Tyndale House Cambridge", tvtms_data["attribution"])
        self.assertGreater(tvtms_data["extracted_rules_count"], 0)
        self.assertIn("artifact_checksum_sha256", tvtms_data)


if __name__ == "__main__":
    unittest.main()
