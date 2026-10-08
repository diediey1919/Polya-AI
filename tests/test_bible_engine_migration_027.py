"""
Hermetic Test Suite for Migration 027: Corpus Import Identity & Mapping Subsystem.
Verifies DDL, constraints, triggers, composite FKs, partial unique index,
lease fencing, immutability, and idempotency.
"""

import hashlib
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bible_engine import (
    DatabaseConfig,
    DatabaseEngine,
    create_connection,
)
from bible_engine.migrations import (
    MigrationRunner,
    compute_sha256,
)


def compute_unit_id(
    source_id: str,
    source_version_id: str,
    book_id: str,
    chapter: int,
    sub_partition: str,
    config_hash: str,
) -> str:
    raw = f"{source_id}:{source_version_id}:{book_id}:{chapter}:{sub_partition}:{config_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().lower()


def compute_checkpoint_id(run_id: str, unit_id: str) -> str:
    raw = f"{run_id}:{unit_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().lower()


def compute_verse_record_id(source_version_id: str, source_coordinate: str, raw_sha256: str) -> str:
    raw = f"{source_version_id}:{source_coordinate}:{raw_sha256}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().lower()


def compute_mapping_id(verse_record_id: str, canonical_passage_id: str, sub_verse: str, rule_hash: str) -> str:
    raw = f"{verse_record_id}:{canonical_passage_id}:{sub_verse}:{rule_hash}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest().lower()


class TestBibleEngineMigration027(unittest.TestCase):
    """Focused Unit and Integration Test Suite for Migration 027."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.base_tmp = Path(__file__).resolve().parent / "_test_tmp_migration_027"
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
        self.db_path = os.path.join(self.temp_dir.name, "mig027_test.db")
        self.migrations_dir = Path(self.temp_dir.name) / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)

        repo_schemas = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for sql_file in sorted(repo_schemas.glob("*.sql")):
            shutil.copyfile(sql_file, self.migrations_dir / sql_file.name)

        self.config = DatabaseConfig(
            db_path=self.db_path,
            migrations_dir=str(self.migrations_dir),
            schema_path=str(self.migrations_dir / "001_initial_schema.sql"),
        )
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine, migrations_dir=self.migrations_dir)

        # Apply all migrations up to 027
        self.runner.apply_pending()

        # Seed essential baseline data in isolated test db
        self._seed_baseline()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _seed_baseline(self) -> None:
        conn = self.engine.get_write_connection()
        # Seed canon, testament, book, pericope, passage
        conn.execute(
            "INSERT OR IGNORE INTO canons (canon_id, name, created_at) "
            "VALUES ('CANON-PROT', 'Protestant Canon', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT OR IGNORE INTO testaments (testament_id, canon_id, name, sort_order) "
            "VALUES ('OT', 'CANON-PROT', 'Old Testament', 1);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count) "
            "VALUES ('DAN', 'OT', 27, 'Daniel', 'Daniel', 'HEBREW', 12);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO pericopes (pericope_id, book_id, segmentation_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
            "VALUES ('PER-DAN-2', 'DAN', 'WIT-SEG-PROVISIONAL-CHAPTER', 'Dan 2', 2, 1, 2, 49, 'APOCALYPTIC', 'CANONICAL_CHAPTER_FALLBACK', 'HIGH', 'REGISTERED', '1.0', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT OR IGNORE INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) "
            "VALUES ('PAS-DAN-2-4', 'PER-DAN-2', 'DAN', 2, 4, 27002004);"
        )
        # Seed provenance
        conn.execute(
            "INSERT OR IGNORE INTO provenance_records (provenance_id, target_type, target_id, content_hash, transformation_type, schema_version, created_at, is_immutable) "
            "VALUES ('PROV-ROOT', 'PRIMARY_SOURCE', 'SRC-WLC', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'ORIGIN', '1.0.0', '2026-10-05 00:00:00', 1);"
        )
        conn.execute(
            "INSERT OR IGNORE INTO provenance_records (provenance_id, target_type, target_id, content_hash, transformation_type, schema_version, created_at, is_immutable) "
            "VALUES ('PROV-MAP', 'DERIVED_ARTIFACT', 'MAP-DAN-2-4', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'DETERMINISTIC', '1.0.0', '2026-10-05 00:00:00', 1);"
        )
        # Seed source_registry
        conn.execute(
            "INSERT OR IGNORE INTO source_registry (source_id, canonical_name, source_type, language, authority_level, provenance_id, created_at, updated_at) "
            "VALUES ('SRC-WLC', 'Westminster Leningrad Codex', 'PRIMARY_WITNESS', 'HEBREW', 'PRIMARY', 'PROV-ROOT', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT OR IGNORE INTO source_registry (source_id, canonical_name, source_type, language, authority_level, provenance_id, created_at, updated_at) "
            "VALUES ('SRC-NA28', 'Novum Testamentum Graece NA28', 'CRITICAL_EDITION', 'GREEK', 'TEXTUAL_CRITICAL', 'PROV-ROOT', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        # Seed object_versions: valid SOURCE version for SRC-WLC
        conn.execute(
            "INSERT OR IGNORE INTO object_versions (version_id, object_type, object_id, version_number, content_hash, provenance_id, status, change_reason, created_at, created_by) "
            "VALUES ('VER-WLC-1', 'SOURCE', 'SRC-WLC', 1, 'hash_wlc_v1', 'PROV-ROOT', 'ACTIVE', 'INITIAL_CREATION', '2026-10-05 00:00:00', 'admin');"
        )
        # Seed object_versions: valid SOURCE version for SRC-NA28
        conn.execute(
            "INSERT OR IGNORE INTO object_versions (version_id, object_type, object_id, version_number, content_hash, provenance_id, status, change_reason, created_at, created_by) "
            "VALUES ('VER-NA28-1', 'SOURCE', 'SRC-NA28', 1, 'hash_na28_v1', 'PROV-ROOT', 'ACTIVE', 'INITIAL_CREATION', '2026-10-05 00:00:00', 'admin');"
        )
        # Seed object_versions: invalid object_type (CLAIM instead of SOURCE)
        conn.execute(
            "INSERT OR IGNORE INTO object_versions (version_id, object_type, object_id, version_number, content_hash, provenance_id, status, change_reason, created_at, created_by) "
            "VALUES ('VER-CLAIM-1', 'CLAIM', 'SRC-WLC', 2, 'hash_claim_v1', 'PROV-ROOT', 'ACTIVE', 'INITIAL_CREATION', '2026-10-05 00:00:00', 'admin');"
        )

    # 1. schema existence
    def test_01_schema_existence(self) -> None:
        conn = self.engine.get_write_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [r[0] for r in cur.fetchall()]
        expected = [
            "corpus_import_artifacts",
            "corpus_import_checkpoints",
            "corpus_import_runs",
            "corpus_source_verse_mappings",
            "corpus_source_verses",
        ]
        for t in expected:
            self.assertIn(t, tables, f"Expected table '{t}' was not created.")

    # 2. parent lineage valid
    def test_02_parent_lineage_valid(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        cur = conn.execute("SELECT run_id FROM corpus_import_runs WHERE run_id = 'RUN-1';")
        self.assertIsNotNone(cur.fetchone())

    # 3. wrong source rejected
    def test_03_wrong_source_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute(
                "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
                "VALUES ('RUN-BAD-SRC', 'SRC-NA28', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
            )
        self.assertIn("Parent lineage mismatch", str(ctx.exception))

    # 4. wrong object_type rejected
    def test_04_wrong_object_type_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute(
                "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
                "VALUES ('RUN-BAD-TYPE', 'SRC-WLC', 'VER-CLAIM-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
            )
        self.assertIn("Parent lineage mismatch", str(ctx.exception))

    # 5. missing version rejected
    def test_05_missing_version_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
                "VALUES ('RUN-MISS-VER', 'SRC-WLC', 'VER-GHOST-999', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
            )

    # 6. artifact valid
    def test_06_artifact_valid(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-ART-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_artifacts (artifact_id, run_id, source_id, uri, sha256_hash, size_bytes, mime_type, created_at) "
            "VALUES ('ART-1', 'RUN-ART-1', 'SRC-WLC', 'file:///tmp/wlc.zip', 'hash_wlc_zip', 1024, 'application/zip', '2026-10-05 00:00:00');"
        )
        cur = conn.execute("SELECT artifact_id FROM corpus_import_artifacts WHERE artifact_id = 'ART-1';")
        self.assertIsNotNone(cur.fetchone())

    # 7. artifact cross-lineage rejected
    def test_07_artifact_cross_lineage_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-ART-2', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO corpus_import_artifacts (artifact_id, run_id, source_id, uri, sha256_hash, size_bytes, mime_type, created_at) "
                "VALUES ('ART-BAD', 'RUN-ART-2', 'SRC-NA28', 'file:///tmp/na28.zip', 'hash_na28_zip', 1024, 'application/zip', '2026-10-05 00:00:00');"
            )

    # 8. checkpoint lineage rejected
    def test_08_checkpoint_lineage_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-CHK-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        # Checkpoint with mismatched source_id vs run
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
                "VALUES ('CHK-BAD-SRC', 'RUN-CHK-1', 'UNIT-1', 'SRC-NA28', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
            )

    # 9. verse lineage rejected
    def test_09_verse_lineage_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-VRS-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-VRS-1', 'RUN-VRS-1', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        # Verse claims wrong run_id or wrong source_id relative to checkpoint
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
                "VALUES ('V-BAD', 'CHK-VRS-1', 'RUN-OTHER', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
            )

    # 10. verse UPDATE rejected
    def test_10_verse_update_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-IMM-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-IMM-1', 'RUN-IMM-1', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-IMM-1', 'CHK-IMM-1', 'RUN-IMM-1', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("UPDATE corpus_source_verses SET raw_content = 'mutated' WHERE verse_record_id = 'V-IMM-1';")
        self.assertIn("strictly immutable", str(ctx.exception))

    # 11. verse DELETE rejected
    def test_11_verse_delete_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-IMM-2', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-IMM-2', 'RUN-IMM-2', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-IMM-2', 'CHK-IMM-2', 'RUN-IMM-2', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("DELETE FROM corpus_source_verses WHERE verse_record_id = 'V-IMM-2';")
        self.assertIn("strictly immutable", str(ctx.exception))

    # 12. mapping immutable fields rejected
    def test_12_mapping_immutable_fields_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-MAP-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-MAP-1', 'RUN-MAP-1', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-MAP-1', 'CHK-MAP-1', 'RUN-MAP-1', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-1', 'V-MAP-1', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-1', 1, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("UPDATE corpus_source_verse_mappings SET rule_hash = 'mutated' WHERE mapping_id = 'M-1';")
        self.assertIn("Immutable field mutation prohibited", str(ctx.exception))

    # 13. ACTIVE -> SUPERSEDED accepted
    def test_13_active_to_superseded_accepted(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-MAP-2', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-MAP-2', 'RUN-MAP-2', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-MAP-2', 'CHK-MAP-2', 'RUN-MAP-2', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-2', 'V-MAP-2', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-1', 1, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        conn.execute("UPDATE corpus_source_verse_mappings SET status = 'SUPERSEDED' WHERE mapping_id = 'M-2';")
        st = conn.execute("SELECT status FROM corpus_source_verse_mappings WHERE mapping_id = 'M-2';").fetchone()[0]
        self.assertEqual(st, "SUPERSEDED")

    # 14. SUPERSEDED -> ACTIVE rejected
    def test_14_superseded_to_active_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-MAP-3', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-MAP-3', 'RUN-MAP-3', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-MAP-3', 'CHK-MAP-3', 'RUN-MAP-3', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-3', 'V-MAP-3', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-1', 1, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        conn.execute("UPDATE corpus_source_verse_mappings SET status = 'SUPERSEDED' WHERE mapping_id = 'M-3';")
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            conn.execute("UPDATE corpus_source_verse_mappings SET status = 'ACTIVE' WHERE mapping_id = 'M-3';")
        self.assertIn("Invalid status transition", str(ctx.exception))

    # 15. duplicate ACTIVE mapping rejected
    def test_15_duplicate_active_mapping_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-MAP-4', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-MAP-4', 'RUN-MAP-4', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-MAP-4', 'CHK-MAP-4', 'RUN-MAP-4', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-4A', 'V-MAP-4', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-1', 1, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
                "VALUES ('M-4B', 'V-MAP-4', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-2', 2, 'ACTIVE', '2026-10-05 00:00:00');"
            )

    # 16. historical SUPERSEDED accepted
    def test_16_historical_superseded_accepted(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-MAP-5', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints (checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, status, created_at, updated_at) "
            "VALUES ('CHK-MAP-5', 'RUN-MAP-5', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', 'PENDING', '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verses (verse_record_id, checkpoint_id, run_id, source_id, source_version_id, source_coordinate, language_code, raw_content, raw_sha256, created_at) "
            "VALUES ('V-MAP-5', 'CHK-MAP-5', 'RUN-MAP-5', 'SRC-WLC', 'VER-WLC-1', 'DAN 2:4', 'HEBREW', 'content', 'hash', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-5A', 'V-MAP-5', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-1', 1, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        conn.execute("UPDATE corpus_source_verse_mappings SET status = 'SUPERSEDED' WHERE mapping_id = 'M-5A';")
        # Now insert new ACTIVE mapping
        conn.execute(
            "INSERT INTO corpus_source_verse_mappings (mapping_id, verse_record_id, canonical_passage_id, mapping_provenance_id, mapping_type, sub_verse, rule_hash, mapping_version, status, created_at) "
            "VALUES ('M-5B', 'V-MAP-5', 'PAS-DAN-2-4', 'PROV-MAP', 'EXACT_ONE_TO_ONE', '', 'rule-hash-2', 2, 'ACTIVE', '2026-10-05 00:00:00');"
        )
        cur = conn.execute("SELECT count(*) FROM corpus_source_verse_mappings WHERE verse_record_id = 'V-MAP-5';")
        self.assertEqual(cur.fetchone()[0], 2)

    # 17. lease fencing valid
    def test_17_lease_fencing_valid(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-LSE-1', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints ("
            "checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, "
            "status, worker_id, lease_expires_at, fence_token, created_at, updated_at"
            ") VALUES ('CHK-LSE-1', 'RUN-LSE-1', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', "
            "'LEASED', 'worker-1', datetime('now', '+300 seconds'), 42, '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )

        # Fenced commit update
        cur = conn.execute(
            "UPDATE corpus_import_checkpoints SET status = 'COMPLETED', updated_at = datetime('now') "
            "WHERE checkpoint_id = 'CHK-LSE-1' AND status = 'LEASED' AND worker_id = 'worker-1' "
            "AND fence_token = 42 AND lease_expires_at > datetime('now');"
        )
        self.assertEqual(cur.rowcount, 1)

    # 18. expired lease rejected
    def test_18_expired_lease_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-LSE-2', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        # Lease expired 10 seconds ago
        conn.execute(
            "INSERT INTO corpus_import_checkpoints ("
            "checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, "
            "status, worker_id, lease_expires_at, fence_token, created_at, updated_at"
            ") VALUES ('CHK-LSE-2', 'RUN-LSE-2', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', "
            "'LEASED', 'worker-1', datetime('now', '-10 seconds'), 42, '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )

        cur = conn.execute(
            "UPDATE corpus_import_checkpoints SET status = 'COMPLETED', updated_at = datetime('now') "
            "WHERE checkpoint_id = 'CHK-LSE-2' AND status = 'LEASED' AND worker_id = 'worker-1' "
            "AND fence_token = 42 AND lease_expires_at > datetime('now');"
        )
        self.assertEqual(cur.rowcount, 0)

    # 19. wrong worker rejected
    def test_19_wrong_worker_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-LSE-3', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints ("
            "checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, "
            "status, worker_id, lease_expires_at, fence_token, created_at, updated_at"
            ") VALUES ('CHK-LSE-3', 'RUN-LSE-3', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', "
            "'LEASED', 'worker-1', datetime('now', '+300 seconds'), 42, '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )

        cur = conn.execute(
            "UPDATE corpus_import_checkpoints SET status = 'COMPLETED', updated_at = datetime('now') "
            "WHERE checkpoint_id = 'CHK-LSE-3' AND status = 'LEASED' AND worker_id = 'worker-GHOST' "
            "AND fence_token = 42 AND lease_expires_at > datetime('now');"
        )
        self.assertEqual(cur.rowcount, 0)

    # 20. wrong fence token rejected
    def test_20_wrong_fence_token_rejected(self) -> None:
        conn = self.engine.get_write_connection()
        conn.execute(
            "INSERT INTO corpus_import_runs (run_id, source_id, source_version_id, provenance_id, runner_id, status, config_hash, started_at) "
            "VALUES ('RUN-LSE-4', 'SRC-WLC', 'VER-WLC-1', 'PROV-ROOT', 'runner-01', 'INITIALIZED', 'cfg-01', '2026-10-05 00:00:00');"
        )
        conn.execute(
            "INSERT INTO corpus_import_checkpoints ("
            "checkpoint_id, run_id, unit_id, source_id, source_version_id, book_id, chapter, config_hash, "
            "status, worker_id, lease_expires_at, fence_token, created_at, updated_at"
            ") VALUES ('CHK-LSE-4', 'RUN-LSE-4', 'UNIT-1', 'SRC-WLC', 'VER-WLC-1', 'DAN', 2, 'cfg-01', "
            "'LEASED', 'worker-1', datetime('now', '+300 seconds'), 42, '2026-10-05 00:00:00', '2026-10-05 00:00:00');"
        )

        cur = conn.execute(
            "UPDATE corpus_import_checkpoints SET status = 'COMPLETED', updated_at = datetime('now') "
            "WHERE checkpoint_id = 'CHK-LSE-4' AND status = 'LEASED' AND worker_id = 'worker-1' "
            "AND fence_token = 999 AND lease_expires_at > datetime('now');"
        )
        self.assertEqual(cur.rowcount, 0)

    # 21. migration idempotency
    def test_21_migration_idempotency(self) -> None:
        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertEqual(status.pending_count, 0)
        re_applied = self.runner.apply_pending()
        self.assertEqual(len(re_applied), 0)

    # 22. PRAGMA foreign_key_check
    def test_22_pragma_foreign_key_check(self) -> None:
        conn = self.engine.get_write_connection()
        violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
        self.assertEqual(len(violations), 0, f"Foreign key violations found: {violations}")

    # 23. PRAGMA integrity_check
    def test_23_pragma_integrity_check(self) -> None:
        conn = self.engine.get_write_connection()
        res = [tuple(r) for r in conn.execute("PRAGMA integrity_check;").fetchall()]
        self.assertEqual(res, [("ok",)])

    # 24. PRAGMA foreign_keys = 1
    def test_24_pragma_foreign_keys_enabled(self) -> None:
        conn = self.engine.get_write_connection()
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        self.assertEqual(fk, 1)

    # 25. Identity formulas test
    def test_25_identity_formulas(self) -> None:
        u_id = compute_unit_id("SRC-WLC", "VER-WLC-1", "DAN", 2, "a", "cfg-hash-01")
        self.assertEqual(len(u_id), 64)
        self.assertEqual(u_id, u_id.lower())

        chk_id = compute_checkpoint_id("RUN-01", u_id)
        self.assertEqual(len(chk_id), 64)

        v_id = compute_verse_record_id("VER-WLC-1", "DAN 2:4a", "raw_hash_01")
        self.assertEqual(len(v_id), 64)

        m_id = compute_mapping_id(v_id, "PAS-DAN-2-4", "a", "rule_hash_01")
        self.assertEqual(len(m_id), 64)


if __name__ == "__main__":
    unittest.main()
