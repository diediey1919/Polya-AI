"""
Task 1.3 Focused Test Suite: Migration Runner.
Verifies discovery, deterministic ordering, checksum enforcement, transactional DDL rollback,
failure recovery, foreign-key protection, status reporting, and concurrency safety.
"""

import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bible_engine import (
    AmbiguousMigrationOrderError,
    DatabaseConfig,
    DatabaseConfigurationError,
    DatabaseEngine,
    DuplicateMigrationError,
    MalformedMigrationNameError,
    MigrationChecksumMismatchError,
    MigrationError,
    MigrationExecutionError,
    MigrationIntegrityError,
    MissingMigrationFileError,
    create_connection,
)
from bible_engine.migrations import (
    MigrationFile,
    MigrationRecord,
    MigrationRunner,
    MigrationStatus,
    compute_sha256,
    split_sql_statements,
)


class TestMigrationRunner(unittest.TestCase):
    """Focused Task 1.3 Migration Runner Tests."""

    def setUp(self) -> None:
        self.base_tmp = Path(__file__).resolve().parent / "_test_tmp_migrations"
        self.base_tmp.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))

        self.db_path = os.path.join(self.temp_dir.name, "migration_test.db")
        self.migrations_dir = Path(self.temp_dir.name) / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        # Copy authoritative 001_initial_schema.sql as the initial migration
        repo_schema = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
            / "001_initial_schema.sql"
        )
        self.initial_schema_file = self.migrations_dir / "001_initial_schema.sql"
        shutil.copyfile(repo_schema, self.initial_schema_file)

        self.config = DatabaseConfig(
            db_path=self.db_path,
            migrations_dir=str(self.migrations_dir),
            schema_path=str(self.initial_schema_file),
        )
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine, migrations_dir=self.migrations_dir)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()
        if self.base_tmp.exists():
            try:
                self.base_tmp.rmdir()
            except OSError:
                pass

    # -------------------------------------------------------------------------
    # 1. Fresh database initialization
    # -------------------------------------------------------------------------
    def test_01_fresh_database_initialization(self) -> None:
        status = self.runner.get_status()
        self.assertIsNone(status.current_version)
        self.assertIsNone(status.latest_applied_id)
        self.assertEqual(status.applied_count, 0)
        self.assertEqual(status.pending_count, 1)
        self.assertFalse(status.is_clean)
        self.assertEqual(status.pending_migrations[0].migration_id, "001_initial_schema")

    # -------------------------------------------------------------------------
    # 2. Initial schema bootstrap
    # -------------------------------------------------------------------------
    def test_02_initial_schema_bootstrap(self) -> None:
        applied = self.runner.apply_pending()
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0].migration_id, "001_initial_schema")
        self.assertEqual(applied[0].version, "1")

        # Verify all 29 foundation tables are created
        conn = self.engine.get_write_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        self.assertEqual(len(tables), 29)

    # -------------------------------------------------------------------------
    # 3. Migration metadata creation/recording
    # -------------------------------------------------------------------------
    def test_03_migration_metadata_creation_and_recording(self) -> None:
        self.runner.apply_pending()

        conn = self.engine.get_write_connection()
        row = conn.execute(
            "SELECT * FROM schema_migrations WHERE migration_id = '001_initial_schema';"
        ).fetchone()

        self.assertIsNotNone(row)
        self.assertEqual(row["migration_id"], "001_initial_schema")
        self.assertEqual(row["version"], "1")
        self.assertTrue(len(row["checksum_sha256"]) == 64)
        self.assertTrue(len(row["applied_at"]) > 0)
        self.assertIn("BIBLE ENGINE", row["description"].upper())

    # -------------------------------------------------------------------------
    # 4. Current-version detection
    # -------------------------------------------------------------------------
    def test_04_current_version_detection(self) -> None:
        self.assertIsNone(self.runner.get_current_version())
        self.runner.apply_pending()
        self.assertEqual(self.runner.get_current_version(), "1")

    # -------------------------------------------------------------------------
    # 5. Pending migration detection
    # -------------------------------------------------------------------------
    def test_05_pending_migration_detection(self) -> None:
        self.runner.apply_pending()
        self.assertEqual(len(self.runner.get_status().pending_migrations), 0)

        # Create a new second migration
        mig_002 = self.migrations_dir / "002_add_evidence_cache.sql"
        mig_002.write_text(
            "-- Add evidence fast lookup cache\n"
            "CREATE TABLE IF NOT EXISTS evidence_cache (cache_id TEXT PRIMARY KEY);\n",
            encoding="utf-8",
        )

        status = self.runner.get_status()
        self.assertEqual(status.pending_count, 1)
        self.assertEqual(status.pending_migrations[0].migration_id, "002_add_evidence_cache")
        self.assertFalse(status.is_clean)

    # -------------------------------------------------------------------------
    # 6. Deterministic migration ordering
    # -------------------------------------------------------------------------
    def test_06_deterministic_migration_ordering(self) -> None:
        (self.migrations_dir / "003_third.sql").write_text(
            "-- Third\nCREATE TABLE t3 (id INT PRIMARY KEY);\n", encoding="utf-8"
        )
        (self.migrations_dir / "002_second.sql").write_text(
            "-- Second\nCREATE TABLE t2 (id INT PRIMARY KEY);\n", encoding="utf-8"
        )

        discovered = self.runner.discover_migrations()
        sequence = [m.sequence_num for m in discovered]
        self.assertEqual(sequence, [1, 2, 3])

    # -------------------------------------------------------------------------
    # 7. Successful migration application
    # -------------------------------------------------------------------------
    def test_07_successful_migration_application(self) -> None:
        self.runner.apply_pending()

        mig_002 = self.migrations_dir / "002_custom_tag.sql"
        mig_002.write_text(
            "-- Custom tagging table\n"
            "CREATE TABLE tag_registry (tag_id TEXT PRIMARY KEY, label TEXT NOT NULL);\n"
            "INSERT INTO tag_registry VALUES ('T1', 'Hapax Legomenon');\n",
            encoding="utf-8",
        )

        applied = self.runner.apply_pending()
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0].migration_id, "002_custom_tag")

        conn = self.engine.get_write_connection()
        row = conn.execute("SELECT * FROM tag_registry WHERE tag_id = 'T1';").fetchone()
        self.assertEqual(row["label"], "Hapax Legomenon")
        self.assertEqual(self.runner.get_current_version(), "2")

    # -------------------------------------------------------------------------
    # 8. Migration checksum recording
    # -------------------------------------------------------------------------
    def test_08_migration_checksum_recording(self) -> None:
        self.runner.apply_pending()
        expected_hash = compute_sha256(self.initial_schema_file.read_text(encoding="utf-8"))

        conn = self.engine.get_write_connection()
        row = conn.execute("SELECT checksum_sha256 FROM schema_migrations WHERE migration_id = '001_initial_schema';").fetchone()
        self.assertEqual(row["checksum_sha256"], expected_hash)

    # -------------------------------------------------------------------------
    # 9. Modified-applied-migration rejection
    # -------------------------------------------------------------------------
    def test_09_modified_applied_migration_rejection(self) -> None:
        self.runner.apply_pending()

        # Tamper with applied migration file
        with open(self.initial_schema_file, "a", encoding="utf-8") as f:
            f.write("\n-- Tampered comment after application\n")

        with self.assertRaises(MigrationChecksumMismatchError) as ctx:
            self.runner.get_status()

        self.assertIn("Checksum mismatch", str(ctx.exception))
        self.assertIn("001_initial_schema", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 10. Duplicate migration identifier rejection
    # -------------------------------------------------------------------------
    def test_10_duplicate_migration_identifier_rejection(self) -> None:
        # Create duplicate sequence number 001
        (self.migrations_dir / "001_duplicate_init.sql").write_text(
            "-- Duplicate sequence\nCREATE TABLE dup (id INT);\n", encoding="utf-8"
        )
        with self.assertRaises(DuplicateMigrationError):
            self.runner.discover_migrations()

    # -------------------------------------------------------------------------
    # 11. Migration failure rollback
    # -------------------------------------------------------------------------
    def test_11_migration_failure_rollback(self) -> None:
        self.runner.apply_pending()

        # Create migration that succeeds partially then fails with invalid SQL
        mig_002 = self.migrations_dir / "002_partially_failing.sql"
        mig_002.write_text(
            "-- Partial failure test\n"
            "CREATE TABLE should_be_rolled_back (id TEXT PRIMARY KEY);\n"
            "INSERT INTO should_be_rolled_back VALUES ('temp_val');\n"
            "THIS IS INTENTIONALLY INVALID SQL STATEMENT;\n",
            encoding="utf-8",
        )

        with self.assertRaises(MigrationExecutionError) as ctx:
            self.runner.apply_pending()

        self.assertEqual(ctx.exception.migration_id, "002_partially_failing")

        # Verify should_be_rolled_back table was completely reverted
        conn = self.engine.get_write_connection()
        cursor = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='should_be_rolled_back';"
        )
        self.assertEqual(cursor.fetchone()[0], 0, "Table must be rolled back on failure.")

        # Verify schema_migrations does not have record for 002
        cursor = conn.execute(
            "SELECT count(*) FROM schema_migrations WHERE migration_id = '002_partially_failing';"
        )
        self.assertEqual(cursor.fetchone()[0], 0)
        self.assertEqual(self.runner.get_current_version(), "1")

    # -------------------------------------------------------------------------
    # 12. Foreign-key enforcement remains enabled
    # -------------------------------------------------------------------------
    def test_12_foreign_key_enforcement_remains_enabled(self) -> None:
        self.runner.apply_pending()

        # Attempt to create migration disabling foreign keys
        mig_002 = self.migrations_dir / "002_illegal_fk.sql"
        mig_002.write_text(
            "-- Illegal FK disable\n"
            "PRAGMA foreign_keys = OFF;\n"
            "CREATE TABLE t (id INT);\n",
            encoding="utf-8",
        )

        with self.assertRaises(DatabaseConfigurationError):
            self.runner.apply_pending()

        # Verify foreign keys are still 1 (ON)
        conn = self.engine.get_write_connection()
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        self.assertEqual(fk, 1)

    # -------------------------------------------------------------------------
    # 13. Existing schema constraints remain enforced
    # -------------------------------------------------------------------------
    def test_13_existing_schema_constraints_remain_enforced(self) -> None:
        self.runner.apply_pending()

        # Add a migration with foreign key to existing foundation table
        mig_002 = self.migrations_dir / "002_book_notes.sql"
        mig_002.write_text(
            "-- Notes referencing books table\n"
            "CREATE TABLE book_notes ("
            "    note_id TEXT PRIMARY KEY,"
            "    book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE RESTRICT"
            ");\n",
            encoding="utf-8",
        )
        self.runner.apply_pending()

        conn = self.engine.get_write_connection()
        # Inserting invalid book_id must violate foreign key
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO book_notes VALUES ('N1', 'NONEXISTENT_BOOK');")

    # -------------------------------------------------------------------------
    # 14. Re-running already-applied migrations is idempotent
    # -------------------------------------------------------------------------
    def test_14_rerunning_already_applied_migrations_is_idempotent(self) -> None:
        applied_first = self.runner.apply_pending()
        self.assertEqual(len(applied_first), 1)

        # Second call must be no-op
        applied_second = self.runner.apply_pending()
        self.assertEqual(len(applied_second), 0)

        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertEqual(status.pending_count, 0)

    # -------------------------------------------------------------------------
    # 15. Missing migration behavior
    # -------------------------------------------------------------------------
    def test_15_missing_migration_behavior(self) -> None:
        self.runner.apply_pending()

        mig_002 = self.migrations_dir / "002_extra.sql"
        mig_002.write_text("-- Extra\nCREATE TABLE extra (id INT);\n", encoding="utf-8")
        self.runner.apply_pending()

        # Delete 002 from filesystem
        mig_002.unlink()

        with self.assertRaises(MissingMigrationFileError) as ctx:
            self.runner.get_status()

        self.assertIn("002_extra", str(ctx.exception))
        self.assertIn("missing from migrations directory", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 16. Migration status output
    # -------------------------------------------------------------------------
    def test_16_migration_status_output(self) -> None:
        status_before = self.runner.get_status()
        summary_before = status_before.summary()
        self.assertIn("Schema Version: UNINITIALIZED", summary_before)
        self.assertIn("Pending: 1", summary_before)

        dict_before = status_before.to_dict()
        self.assertEqual(dict_before["pending_count"], 1)
        self.assertFalse(dict_before["is_clean"])

        self.runner.apply_pending()

        status_after = self.runner.get_status()
        summary_after = status_after.summary()
        self.assertIn("Schema Version: 1", summary_after)
        self.assertIn("Pending: 0", summary_after)
        self.assertIn("CLEAN", summary_after)
        self.assertTrue(status_after.to_dict()["is_clean"])

    # -------------------------------------------------------------------------
    # 17. Concurrent migration protection
    # -------------------------------------------------------------------------
    def test_17_concurrent_migration_protection(self) -> None:
        # Create second connection that locks the database with write lock
        cfg2 = DatabaseConfig(db_path=self.db_path, busy_timeout_ms=100)
        conn2 = create_connection(cfg2)
        conn2.execute("BEGIN IMMEDIATE;")

        try:
            # Runner configured with short timeout should fail immediately due to lock
            cfg_runner = DatabaseConfig(
                db_path=self.db_path,
                busy_timeout_ms=50,
                migrations_dir=str(self.migrations_dir),
            )
            engine_locked = DatabaseEngine(cfg_runner)
            runner_locked = MigrationRunner(engine_locked, migrations_dir=self.migrations_dir)

            with self.assertRaises(sqlite3.OperationalError) as ctx:
                runner_locked.apply_pending()

            self.assertIn("locked", str(ctx.exception).lower())
            engine_locked.close()
        finally:
            conn2.execute("ROLLBACK;")
            conn2.close()

    # -------------------------------------------------------------------------
    # 18. Gaps in migration numbering rejected
    # -------------------------------------------------------------------------
    def test_18_migration_gaps_rejected(self) -> None:
        # 001 exists, create 003 without 002
        (self.migrations_dir / "003_skipped.sql").write_text(
            "-- Skipped\nCREATE TABLE s (id INT);\n", encoding="utf-8"
        )
        with self.assertRaises(AmbiguousMigrationOrderError) as ctx:
            self.runner.discover_migrations()
        self.assertIn("gap detected", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 19. Malformed filenames rejected
    # -------------------------------------------------------------------------
    def test_19_malformed_migration_filenames_rejected(self) -> None:
        (self.migrations_dir / "invalid_name.sql").write_text(
            "-- Bad name\nSELECT 1;\n", encoding="utf-8"
        )
        with self.assertRaises(MalformedMigrationNameError):
            self.runner.discover_migrations()

    # -------------------------------------------------------------------------
    # 20. Legacy runtime database untouched
    # -------------------------------------------------------------------------
    def test_20_legacy_database_untouched(self) -> None:
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            conn = sqlite3.connect(str(legacy_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
            )
            has_schema_migrations = cursor.fetchone()[0]
            conn.close()
            # polya_index.db must NOT have been contaminated with bible schema_migrations
            self.assertEqual(
                has_schema_migrations,
                0,
                "Legacy polya_index.db must not contain Bible Engine schema_migrations.",
            )


if __name__ == "__main__":
    unittest.main()
