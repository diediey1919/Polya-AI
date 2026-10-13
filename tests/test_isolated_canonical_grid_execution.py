"""
Isolated Canonical Grid Generation & End-to-End Verification Test (Task 5G-A).

Executes full 66-book canonical grid generation using the validated KJV manifest
against an isolated temporary database with schema migrations 001-027.
Verifies exact counts (66 books, 1,189 pericopes, 31,102 passages),
deterministic sort_order, idempotency, conflict detection, transaction rollback,
PRAGMA integrity_check, and PRAGMA foreign_key_check.
Zero access to production DB.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bible_engine.canonical_grid import (
    CanonicalGridConflictError,
    CanonicalGridError,
    CanonicalGridGenerator,
    CanonicalGridValidator,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.migrations import MigrationRunner
from tests.test_bible_engine_canonical_grid import CANONICAL_66_BOOKS_FIXTURE


class TestIsolatedCanonicalGridExecution(unittest.TestCase):
    """End-to-end isolated generation test suite for 66 canonical books."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_tmp = Path(__file__).resolve().parent / "_test_tmp_grid_exec"
        cls.base_tmp.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.base_tmp.exists():
            try:
                shutil.rmtree(cls.base_tmp)
            except OSError:
                pass

    def _setup_isolated_db(self):
        """Build isolated temporary database with migrations 001-027 and 66 baseline books."""
        temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))
        db_path = os.path.join(temp_dir.name, "isolated_grid.db")
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

    def _load_production_manifest(self) -> dict:
        manifest_path = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "canonical_versification_manifest.json"
        )
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_full_66_book_grid_generation_and_integrity(self) -> None:
        """Execute full isolated generation of 66 books, 1,189 chapters, 31,102 verses."""
        engine, tmp = self._setup_isolated_db()
        try:
            conn = engine.get_write_connection()
            manifest_data = self._load_production_manifest()

            # 1. Pre-execution verification
            pre_passages = conn.execute("SELECT count(*) FROM passages;").fetchone()[0]
            pre_pericopes = conn.execute("SELECT count(*) FROM pericopes;").fetchone()[0]
            pre_assoc = conn.execute("SELECT count(*) FROM pericope_passages;").fetchone()[0]
            pre_books = conn.execute("SELECT count(*) FROM books;").fetchone()[0]

            self.assertEqual(pre_passages, 0)
            self.assertEqual(pre_pericopes, 0)
            self.assertEqual(pre_assoc, 0)
            self.assertEqual(pre_books, 66)

            # 2. Manifest validation
            validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)
            self.assertEqual(validated.total_books, 66)
            self.assertEqual(validated.total_chapters, 1189)
            self.assertEqual(validated.total_verses, 31102)

            # 3. Execution
            generator = CanonicalGridGenerator(conn)
            summary = generator.generate(validated)

            self.assertEqual(summary.books_processed, 66)
            self.assertEqual(summary.pericopes_inserted, 1189)
            self.assertEqual(summary.passages_inserted, 31102)
            self.assertEqual(summary.pericopes_replayed, 0)
            self.assertEqual(summary.passages_replayed, 0)

            # 4. Post-execution row counts
            post_passages = conn.execute("SELECT count(*) FROM passages;").fetchone()[0]
            post_pericopes = conn.execute("SELECT count(*) FROM pericopes;").fetchone()[0]
            post_assoc = conn.execute("SELECT count(*) FROM pericope_passages;").fetchone()[0]

            self.assertEqual(post_passages, 31102)
            self.assertEqual(post_pericopes, 1189)
            self.assertEqual(post_assoc, 31102)

            # 5. Book-by-book chapter and verse breakdown check
            book_stats = conn.execute(
                """
                SELECT b.book_id, b.chapter_count,
                       (SELECT count(*) FROM pericopes p WHERE p.book_id = b.book_id) AS pericope_cnt,
                       (SELECT count(*) FROM passages pas WHERE pas.book_id = b.book_id) AS verse_cnt
                FROM books b
                ORDER BY b.canonical_order ASC;
                """
            ).fetchall()

            self.assertEqual(len(book_stats), 66)
            total_v_sum = 0
            for row in book_stats:
                b_id, ch_count, per_cnt, v_cnt = row[0], row[1], row[2], row[3]
                self.assertEqual(
                    ch_count, per_cnt,
                    f"Book '{b_id}' pericope count {per_cnt} does not match chapter_count {ch_count}"
                )
                self.assertGreater(v_cnt, 0, f"Book '{b_id}' has 0 verses")
                total_v_sum += v_cnt
            self.assertEqual(total_v_sum, 31102)

            # 6. Sort order continuity check
            sort_order_stats = conn.execute(
                """
                SELECT min(sort_order), max(sort_order), count(DISTINCT sort_order)
                FROM passages;
                """
            ).fetchone()
            self.assertEqual(sort_order_stats[0], 1)
            self.assertEqual(sort_order_stats[1], 31102)
            self.assertEqual(sort_order_stats[2], 31102)

            # 7. Boundary IDs verification
            first_pas = conn.execute(
                "SELECT passage_id, pericope_id, book_id, chapter, verse FROM passages WHERE sort_order = 1;"
            ).fetchone()
            self.assertEqual(first_pas[0], "PAS-GEN.1.1")
            self.assertEqual(first_pas[1], "PER-PROV-GEN-CH001")
            self.assertEqual(first_pas[2], "GEN")
            self.assertEqual(first_pas[3], 1)
            self.assertEqual(first_pas[4], 1)

            last_pas = conn.execute(
                "SELECT passage_id, pericope_id, book_id, chapter, verse FROM passages WHERE sort_order = 31102;"
            ).fetchone()
            self.assertEqual(last_pas[0], "PAS-REV.22.21")
            self.assertEqual(last_pas[1], "PER-PROV-REV-CH022")
            self.assertEqual(last_pas[2], "REV")
            self.assertEqual(last_pas[3], 22)
            self.assertEqual(last_pas[4], 21)

            # 8. Pragmas
            int_check = [r[0] for r in conn.execute("PRAGMA integrity_check;").fetchall()]
            self.assertEqual(int_check, ["ok"])

            fk_check = conn.execute("PRAGMA foreign_key_check;").fetchall()
            self.assertEqual(len(fk_check), 0)

            # 9. Idempotency test (second identical execution)
            summary_rerun = generator.generate(validated)
            self.assertEqual(summary_rerun.books_processed, 66)
            self.assertEqual(summary_rerun.pericopes_inserted, 0)
            self.assertEqual(summary_rerun.passages_inserted, 0)
            self.assertEqual(summary_rerun.pericopes_replayed, 1189)
            self.assertEqual(summary_rerun.passages_replayed, 31102)

            # Assert counts are completely identical post-rerun
            self.assertEqual(conn.execute("SELECT count(*) FROM passages;").fetchone()[0], 31102)
            self.assertEqual(conn.execute("SELECT count(*) FROM pericopes;").fetchone()[0], 1189)
            self.assertEqual(conn.execute("SELECT count(*) FROM pericope_passages;").fetchone()[0], 31102)

            # 10. Explicit conflict detection
            conn.execute("UPDATE passages SET chapter = 99 WHERE passage_id = 'PAS-GEN.1.1';")
            with self.assertRaises(CanonicalGridConflictError):
                generator.generate(validated)

        finally:
            engine.close()
            tmp.cleanup()

    def test_atomic_transaction_full_rollback_on_failure(self) -> None:
        """Verify that any exception during generation triggers a full atomic rollback."""
        engine, tmp = self._setup_isolated_db()
        try:
            conn = engine.get_write_connection()
            manifest_data = self._load_production_manifest()
            validated = CanonicalGridValidator.validate(manifest_data, conn, require_full_canon=True)

            generator = CanonicalGridGenerator(conn)

            # Corrupt database by inserting an invalid sort_order collision
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, segmentation_id, reference, "
                "start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, "
                "boundary_confidence, status, version, created_at) "
                "VALUES ('PER-COLLISION', 'GEN', 'WIT-SEG-PROVISIONAL-CHAPTER', 'Ref', 1, 1, 1, 1, "
                "'PROVISIONAL_PARTITION', 'CANONICAL_CHAPTER_FALLBACK', 'HIGH', 'REGISTERED', '1.0', '2026-10-01T00:00:00Z');"
            )
            # Insert a conflicting passage with sort_order = 100
            conn.execute(
                "INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) "
                "VALUES ('PAS-CONFLICT', 'PER-COLLISION', 'GEN', 1, 1, 100);"
            )
            conn.commit()

            # Attempting to generate should fail when sort_order or coordinate collides
            with self.assertRaises(Exception):
                generator.generate(validated)

            # Verify that pericopes generated during the failed run were rolled back
            remaining_pericopes = conn.execute("SELECT count(*) FROM pericopes;").fetchone()[0]
            remaining_passages = conn.execute("SELECT count(*) FROM passages;").fetchone()[0]

            # Only the pre-existing collision rows remain; 0 generated rows leaked
            self.assertEqual(remaining_pericopes, 1)
            self.assertEqual(remaining_passages, 1)

        finally:
            engine.close()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
