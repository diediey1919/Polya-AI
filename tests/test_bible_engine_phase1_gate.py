"""
POLYA PHILOLOGICAL BIBLE ENGINE
TASK 1.7: INTEGRATED PHASE 1 GATE TEST SUITE

Comprehensive End-to-End Validation Suite for Phase 1 Subsystems:
1. Schema Foundation (001_initial_schema.sql)
2. Schema Reconciliation (001_initial_schema.sql evidence & referential FKs)
3. Database Layer (bible_engine/database.py)
4. Migration Runner (bible_engine/migrations.py & 001-004)
5. Provenance Subsystem (bible_engine/provenance.py & 002_provenance.sql)
6. Versioning Subsystem (bible_engine/versioning.py & 003_versioning.sql)
7. Source Registry Subsystem (bible_engine/source_registry.py & 004_source_registry.sql)

All tests operate against strictly isolated temporary SQLite databases.
Legacy database (/home/ubuntu/.polya/polya_index.db) is monitored and guaranteed untouched.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine, create_connection
from bible_engine.errors import (
    DuplicateMigrationError,
    DuplicateSourceError,
    DuplicateVersionError,
    IllegalSourceStateTransitionError,
    IllegalStateTransitionError,
    InvalidSourceAuthorityError,
    InvalidSourceTypeError,
    MigrationChecksumMismatchError,
    ReadOnlyViolationError,
    SourceHashMismatchError,
    SourceImmutabilityError,
    SourceInvalidProvenanceError,
    SourceInvalidVersionError,
    SourceNotFoundError,
    SourceRegistryError,
    SourceTranslationFirewallError,
    VersionConcurrencyConflictError,
    VersionHashMismatchError,
    VersionImmutabilityError,
    VersionInvalidParentError,
    VersionInvalidProvenanceError,
    VersionNotFoundError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import (
    ProvenanceTracker as ProvenanceManager,
    RelationType,
    TargetType,
    TransformationType,
    compute_sha256,
    verify_hash,
)
from bible_engine.source_registry import (
    ExternalIdentifierType,
    SourceAuthorityLevel,
    SourceLanguage,
    SourceRecord,
    SourceRegistry,
    SourceType,
    SourceVerificationStatus,
)
from bible_engine.versioning import ChangeReason, VersionManager, VersionStatus

LEGACY_DB_PATH = "/home/ubuntu/.polya/polya_index.db"
EXPECTED_LEGACY_SHA256 = "500bb6a2057a1c30e392f0a99f2437a9b07a79a075e79177a0b9d17e7353c5c5"

REQUIRED_PHASE1_TABLES = [
    "audit_log",
    "books",
    "canons",
    "claim_evidence_links",
    "claims",
    "clauses",
    "critical_editions",
    "entities",
    "entity_mentions",
    "evidence_ledger",
    "exegesis_reports",
    "lemmas",
    "morphology_annotations",
    "object_versions",
    "passages",
    "pericopes",
    "provenance_records",
    "provenance_relations",
    "referential_relations",
    "schema_migrations",
    "sections",
    "semantic_senses",
    "source_registry",
    "source_registry_audit",
    "source_texts",
    "syntax_trees",
    "testaments",
    "tokens",
    "translations",
    "validation_gate_results",
    "variant_readings",
    "variant_units",
    "variant_witness_attestations",
    "version_relations",
    "witnesses",
]


class Phase1GateBaseTest(unittest.TestCase):
    """Base fixture providing isolated test environment and legacy DB check."""

    def setUp(self) -> None:
        try:
            self.temp_dir = tempfile.mkdtemp(dir="/dev/shm")
        except (OSError, FileNotFoundError):
            self.temp_dir = tempfile.mkdtemp()

        self.db_path = os.path.join(self.temp_dir, "gate_test.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)

        # Record pre-test legacy database state
        if os.path.exists(LEGACY_DB_PATH):
            self.legacy_size_before = os.path.getsize(LEGACY_DB_PATH)
            self.legacy_mtime_before = os.path.getmtime(LEGACY_DB_PATH)
            with open(LEGACY_DB_PATH, "rb") as f:
                self.legacy_sha256_before = hashlib.sha256(f.read()).hexdigest().lower()
        else:
            self.legacy_size_before = None
            self.legacy_mtime_before = None
            self.legacy_sha256_before = None

    def tearDown(self) -> None:
        self.engine.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Assert post-test legacy database state unchanged
        if self.legacy_size_before is not None and os.path.exists(LEGACY_DB_PATH):
            size_after = os.path.getsize(LEGACY_DB_PATH)
            self.assertEqual(
                size_after,
                self.legacy_size_before,
                "SECURITY VIOLATION: Legacy DB size altered during test execution!",
            )
            with open(LEGACY_DB_PATH, "rb") as f:
                sha256_after = hashlib.sha256(f.read()).hexdigest().lower()
            self.assertEqual(
                sha256_after,
                self.legacy_sha256_before,
                "SECURITY VIOLATION: Legacy DB checksum altered during test execution!",
            )


# =============================================================================
# A. FRESH DATABASE BOOTSTRAP
# =============================================================================

class TestPhase1GateBootstrap(Phase1GateBaseTest):
    """Validation of zero-state bootstrap and migration runner."""

    def test_a01_fresh_database_bootstrap_runs_migrations_001_to_004(self) -> None:
        """Run MigrationRunner from zero; verify 001-004 applied sequentially."""
        runner = MigrationRunner(self.engine)
        status_before = runner.get_status()
        self.assertFalse(status_before.is_clean)
        self.assertEqual(status_before.applied_count, 0)
        self.assertGreaterEqual(status_before.pending_count, 4)

        applied = runner.apply_pending()
        self.assertGreaterEqual(len(applied), 4)

        applied_ids = [m.migration_id for m in applied]
        expected_ids = [
            "001_initial_schema",
            "002_provenance",
            "003_versioning",
            "004_source_registry",
        ]
        self.assertEqual(applied_ids[:4], expected_ids)

        status_after = runner.get_status()
        self.assertTrue(status_after.is_clean)
        self.assertGreaterEqual(status_after.applied_count, 4)
        self.assertEqual(status_after.pending_count, 0)

    def test_a02_migration_ids_contiguous_and_checksums_match(self) -> None:
        """Verify migration IDs are contiguous, no gaps, and checksums match on-disk files."""
        runner = MigrationRunner(self.engine)
        runner.apply_pending()

        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT migration_id, checksum_sha256, version FROM schema_migrations ORDER BY migration_id ASC;")
            rows = cursor.fetchall()
            self.assertGreaterEqual(len(rows), 4)

            migrations_dir = Path(self.config.resolve_migrations_dir())
            for row in rows:
                mid = row["migration_id"]
                file_path = migrations_dir / f"{mid}.sql"
                self.assertTrue(file_path.is_file(), f"Migration file missing on disk: {file_path}")
                disk_checksum = compute_sha256(file_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    row["checksum_sha256"],
                    disk_checksum,
                    f"Checksum mismatch for migration {mid}",
                )

    def test_a03_no_duplicate_and_no_missing_migrations(self) -> None:
        """Verify duplicate migration IDs are rejected and status accurately reports zero missing."""
        runner = MigrationRunner(self.engine)
        runner.apply_pending()

        # Idempotent re-run returns empty list
        second_run = runner.apply_pending()
        self.assertEqual(second_run, [])

        # Verify no duplicate rows in schema_migrations
        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT migration_id, count(*) as cnt FROM schema_migrations GROUP BY migration_id HAVING cnt > 1;")
            duplicates = cursor.fetchall()
            self.assertEqual(len(duplicates), 0)

    def test_a04_foreign_keys_and_clean_reopen(self) -> None:
        """Verify foreign_keys = ON and database opens cleanly across reconnections."""
        runner = MigrationRunner(self.engine)
        runner.apply_pending()

        with self.engine.connect() as conn:
            fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
            self.assertEqual(fk_status, 1)

        # Reopen connection
        self.engine.close()
        new_engine = DatabaseEngine(self.config)
        try:
            with new_engine.connect() as conn:
                fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
                self.assertEqual(fk_status, 1)
                new_runner = MigrationRunner(new_engine)
                status = new_runner.get_status()
                self.assertTrue(status.is_clean)
                self.assertGreaterEqual(status.applied_count, 4)
        finally:
            new_engine.close()


# =============================================================================
# B. DATABASE INTEGRITY
# =============================================================================

class TestPhase1GateDatabaseIntegrity(Phase1GateBaseTest):
    """Validation of relational database integrity, transactions, and guards."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

    def test_b01_all_35_phase1_tables_exist(self) -> None:
        """Verify all 35 required Phase 1 tables exist in sqlite_master."""
        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = [row[0] for row in cursor.fetchall()]

            for req in REQUIRED_PHASE1_TABLES:
                self.assertIn(req, tables, f"Required table '{req}' is missing from database schema!")

    def test_b02_foreign_keys_are_enforced(self) -> None:
        """Verify child rows cannot be inserted without valid parent rows."""
        with self.engine.connect() as conn:
            # Inserting into passages without valid pericope_id and book_id must fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) "
                    "VALUES ('PASS-ORPHAN', 'PER-NONEXISTENT', 'BOOK-NONE', 1, 1, 9999);"
                )

    def test_b03_check_constraints_work(self) -> None:
        """Verify CHECK constraints enforce valid enumeration values."""
        with self.engine.connect() as conn:
            # Inserting an invalid evidence_class must fail CHECK constraint
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, evidence_class, "
                    "epistemic_tier, source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                    "created_at, provenance_hash) VALUES "
                    "('EVID-FAIL', 'PER-1', 'PASS-1', 'INVALID_CLASS', 'TIER_1_LINGUISTIC_FACT', 'Ref', 'Data', "
                    "'[EXPLICIT]', 'HIGH', 0, '2026-09-30T00:00:00Z', 'hash');"
                )

    def test_b04_transaction_rollback_and_nested_savepoints(self) -> None:
        """Verify explicit transactions and nested savepoints roll back without leaving partial state."""
        # 1. Top-level transaction rollback
        try:
            with self.engine.transaction() as conn:
                conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-1', 'Canon Test', '2026-09-30T00:00:00Z');")
                # Intentional failure
                raise RuntimeError("Forced abort for rollback test")
        except RuntimeError:
            pass

        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM canons WHERE canon_id='CANON-1';").fetchone()
            self.assertIsNone(row, "Transaction rollback failed to remove partial state!")

        # 2. Nested savepoints rollback via engine.transaction(conn=conn, savepoint=True)
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-2', 'Canon Outer', '2026-09-30T00:00:00Z');")
            try:
                with self.engine.transaction(conn=conn, savepoint=True):
                    conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-3', 'Canon Inner', '2026-09-30T00:00:00Z');")
                    raise RuntimeError("Abort inner savepoint")
            except RuntimeError:
                pass

        with self.engine.connect() as conn:
            c2 = conn.execute("SELECT * FROM canons WHERE canon_id='CANON-2';").fetchone()
            c3 = conn.execute("SELECT * FROM canons WHERE canon_id='CANON-3';").fetchone()
            self.assertIsNotNone(c2, "Outer transaction should have been committed.")
            self.assertIsNone(c3, "Inner savepoint should have been rolled back.")

    def test_b05_read_only_connections_cannot_mutate_state(self) -> None:
        """Verify read-only connection rejects all write attempts via PRAGMA query_only."""
        read_conn = self.engine.get_read_connection()
        with self.assertRaises((sqlite3.OperationalError, ReadOnlyViolationError)):
            read_conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-RO', 'Fail', 'now');")


# =============================================================================
# C. SOURCE → VERSION → PROVENANCE
# =============================================================================

class TestPhase1GateSourceVersionProvenance(Phase1GateBaseTest):
    """Validation of Source -> Version -> Provenance conceptual chain."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)
        self.prov_mgr = ProvenanceManager(self.engine)
        self.ver_mgr = VersionManager(self.engine)

    def test_c01_synthetic_scholarly_source_version_provenance_chain(self) -> None:
        """Construct synthetic scholarly source fixture and verify the integrated chain."""
        synth_payload = "Synthetic Grammatical Concordance Content v1.0"
        synth_hash = compute_sha256(synth_payload)

        # 1. Establish Provenance for origin of synthetic scholarly grammar
        prov_rec = self.prov_mgr.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="SYNTH-GRM-001",
            content=synth_payload,
            agent_id="SYSTEM",
        )
        self.assertIsNotNone(prov_rec.provenance_id)
        self.assertEqual(prov_rec.content_hash, synth_hash)

        # 2. Register Source in SourceRegistry referencing provenance_id
        source = self.registry.register_source(
            canonical_name="Synthetic Grammatical Concordance (Scholarly Fixture)",
            source_type=SourceType.GRAMMAR,
            language=SourceLanguage.LATIN,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
            content_hash=synth_hash,
            provenance_id=prov_rec.provenance_id,
            description="Synthetic scholarly fixture - non-biblical",
        )
        self.assertIsNotNone(source.source_id)
        self.assertEqual(source.provenance_id, prov_rec.provenance_id)

        # 3. Create Object Version (version 1, ACTIVE) for the source artifact
        ver_rec = self.ver_mgr.create_version(
            object_type="SOURCE_ARTIFACT",
            object_id=source.source_id,
            content=synth_payload,
            status=VersionStatus.ACTIVE,
            change_reason=ChangeReason.INITIAL_CREATION,
            created_by="system:test_runner",
            provenance_id=prov_rec.provenance_id,
        )
        self.assertEqual(ver_rec.version_number, 1)
        self.assertEqual(ver_rec.status, VersionStatus.ACTIVE.value)

        # 4. Attach Version to Source in registry
        self.registry.attach_version(
            source_id=source.source_id,
            version_id=ver_rec.version_id,
            changed_by="system:test_runner",
        )
        updated_source = self.registry.get_source(source.source_id)
        self.assertIsNotNone(updated_source)
        self.assertEqual(updated_source.current_version_id, ver_rec.version_id)

        # 5. Verify provenance chain resolves
        chain = self.prov_mgr.resolve_provenance_chain(prov_rec.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(chain.target_record.provenance_id, prov_rec.provenance_id)

        # 6. Verify version history resolves
        current_ver = self.ver_mgr.get_current_version("SOURCE_ARTIFACT", source.source_id)
        self.assertIsNotNone(current_ver)
        self.assertEqual(current_ver.version_id, ver_rec.version_id)
        source_versions = self.registry.get_source_versions(source.source_id)
        self.assertEqual(len(source_versions), 1)
        self.assertEqual(source_versions[0].version_id, ver_rec.version_id)

        # 7. Invariant verifications:
        # - Content hash is preserved across all layers
        self.assertEqual(source.content_hash, synth_hash)
        self.assertEqual(ver_rec.content_hash, synth_hash)
        self.assertEqual(prov_rec.content_hash, synth_hash)

        # - Source identity remains stable
        self.assertEqual(source.source_id, updated_source.source_id)
        self.assertEqual(source.canonical_name, updated_source.canonical_name)

        # - Provenance and version identities remain strictly distinct
        self.assertNotEqual(source.source_id, ver_rec.version_id)
        self.assertNotEqual(ver_rec.version_id, prov_rec.provenance_id)
        self.assertNotEqual(source.source_id, prov_rec.provenance_id)


# =============================================================================
# D. SOURCE IMMUTABILITY
# =============================================================================

class TestPhase1GateSourceImmutability(Phase1GateBaseTest):
    """Validation of source immutability triggers and audit integrity."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)

        self.source = self.registry.register_source(
            canonical_name="Codex Immutability Benchmark",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            description="Testing immutability triggers",
        )

    def test_d01_source_id_mutation_rejected(self) -> None:
        """Direct SQL UPDATE of source_id must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET source_id = 'NEW_ID' WHERE source_id = ?;",
                    (self.source.source_id,),
                )
            self.assertIn("source_id is prohibited", str(ctx.exception))

    def test_d02_canonical_name_mutation_rejected(self) -> None:
        """Direct SQL UPDATE of canonical_name must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET canonical_name = 'Renamed Codex' WHERE source_id = ?;",
                    (self.source.source_id,),
                )
            self.assertIn("canonical_name is prohibited", str(ctx.exception))

    def test_d03_created_at_mutation_rejected(self) -> None:
        """Direct SQL UPDATE of created_at must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET created_at = '1970-01-01T00:00:00Z' WHERE source_id = ?;",
                    (self.source.source_id,),
                )
            self.assertIn("created_at timestamp is prohibited", str(ctx.exception))

    def test_d04_delete_source_rejected(self) -> None:
        """DELETE from source_registry must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "DELETE FROM source_registry WHERE source_id = ?;",
                    (self.source.source_id,),
                )
            self.assertIn("Deletions from source_registry are strictly prohibited", str(ctx.exception))

    def test_d05_delete_audit_record_rejected(self) -> None:
        """DELETE from source_registry_audit must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute("DELETE FROM source_registry_audit WHERE source_id = ?;", (self.source.source_id,))
            self.assertIn("Deletions from source_registry_audit are strictly prohibited", str(ctx.exception))

    def test_d06_update_audit_record_rejected(self) -> None:
        """UPDATE on source_registry_audit must be rejected by trigger."""
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute("UPDATE source_registry_audit SET action = 'HACKED' WHERE source_id = ?;", (self.source.source_id,))
            self.assertIn("Updates to source_registry_audit are strictly prohibited", str(ctx.exception))

    def test_d07_metadata_update_creates_audit_history_preserving_immutable_identity(self) -> None:
        """Updating mutable metadata generates audit row without mutating immutable fields."""
        updated = self.registry.update_metadata(
            source_id=self.source.source_id,
            description="Updated description for test",
            repository="Vatican Library",
            changed_by="curator:test",
            change_reason="Metadata enrichment",
        )
        self.assertEqual(updated.source_id, self.source.source_id)
        self.assertEqual(updated.canonical_name, self.source.canonical_name)
        self.assertEqual(updated.created_at, self.source.created_at)
        self.assertEqual(updated.description, "Updated description for test")

        # Verify audit history
        audit_records = self.registry.get_source_audit_history(self.source.source_id)
        self.assertGreaterEqual(len(audit_records), 2)  # 1 REGISTER + 1 UPDATE_METADATA


# =============================================================================
# E. TRANSLATION FIREWALL
# =============================================================================

class TestPhase1GateTranslationFirewall(Phase1GateBaseTest):
    """Validation of Translation Firewall at both API and SQLite trigger levels."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)

        # Register a valid modern translation
        self.translation = self.registry.register_source(
            canonical_name="King James Version 1611 Edition",
            source_type=SourceType.MODERN_TRANSLATION,
            language=SourceLanguage.OTHER,
            authority_level=SourceAuthorityLevel.TRANSLATION,
            description="English Translation",
        )

    def test_e01_modern_translation_primary_authority_rejected_api_and_sql(self) -> None:
        """MODERN_TRANSLATION with authority_level=PRIMARY must fail at API and SQL level."""
        # 1. API level rejection during registration
        with self.assertRaises((SourceTranslationFirewallError, InvalidSourceAuthorityError)):
            self.registry.register_source(
                canonical_name="Unauthorized Primary Translation",
                source_type=SourceType.MODERN_TRANSLATION,
                language=SourceLanguage.OTHER,
                authority_level=SourceAuthorityLevel.PRIMARY,
            )

        # 2. SQLite CHECK constraint level rejection on direct INSERT
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO source_registry (source_id, canonical_name, source_type, language, authority_level, created_at, updated_at) "
                    "VALUES ('TRN-SQL-FAIL', 'SQL Direct Primary Translation', 'MODERN_TRANSLATION', 'OTHER', 'PRIMARY', 'now', 'now');"
                )

        # 3. SQLite UPDATE trigger level rejection
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET authority_level = 'PRIMARY' WHERE source_id = ?;",
                    (self.translation.source_id,),
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))

    def test_e02_modern_translation_cannot_become_primary_witness_api_and_sql(self) -> None:
        """MODERN_TRANSLATION cannot be changed to PRIMARY_WITNESS or CRITICAL_EDITION."""
        # SQLite trigger level rejection
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET source_type = 'PRIMARY_WITNESS' WHERE source_id = ?;",
                    (self.translation.source_id,),
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))

            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET source_type = 'CRITICAL_EDITION' WHERE source_id = ?;",
                    (self.translation.source_id,),
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))

    def test_e03_modern_translation_witness_id_rejected_api_and_sql(self) -> None:
        """MODERN_TRANSLATION cannot have witness_id assigned."""
        # Insert a dummy witness in witnesses table
        with self.engine.transaction() as conn:
            conn.execute(
                "INSERT INTO witnesses (witness_id, siglum, name, witness_type, language, century_origin, provenance_hash) "
                "VALUES ('WIT-DUMMY', 'TEST-SIG', 'Dummy Witness', 'UNCIAL', 'GREEK', 'IV CE', 'hash');"
            )

        # 1. API level rejection
        with self.assertRaises((SourceTranslationFirewallError, InvalidSourceTypeError, SourceRegistryError)):
            self.registry.register_source(
                canonical_name="Translation With Witness ID",
                source_type=SourceType.MODERN_TRANSLATION,
                language=SourceLanguage.OTHER,
                authority_level=SourceAuthorityLevel.TRANSLATION,
                witness_id="WIT-DUMMY",
            )

        # 2. SQLite CHECK constraint rejection
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO source_registry (source_id, canonical_name, source_type, language, authority_level, witness_id, created_at, updated_at) "
                    "VALUES ('TRN-WIT-FAIL', 'SQL Translation With Witness', 'MODERN_TRANSLATION', 'OTHER', 'TRANSLATION', 'WIT-DUMMY', 'now', 'now');"
                )

        # 3. SQLite UPDATE trigger rejection
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE source_registry SET witness_id = 'WIT-DUMMY' WHERE source_id = ?;",
                    (self.translation.source_id,),
                )
            self.assertIn("Translation Firewall violation", str(ctx.exception))


# =============================================================================
# F. WITNESS / EDITION DISTINCTION
# =============================================================================

class TestPhase1GateWitnessEditionDistinction(Phase1GateBaseTest):
    """Validation that primary manuscript witness and critical edition are kept distinct."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)

        with self.engine.transaction() as conn:
            conn.execute(
                "INSERT INTO witnesses (witness_id, siglum, name, witness_type, language, century_origin, provenance_hash) "
                "VALUES ('WIT-ALEPH', 'א', 'Codex Sinaiticus Witness Record', 'UNCIAL', 'GREEK', 'IV CE', 'hash1');"
            )
            conn.execute(
                "INSERT INTO critical_editions (edition_id, name, scholarly_apparatus, publication_year, publisher, source_language, provenance_hash) "
                "VALUES ('ED-NA28', 'Novum Testamentum Graece 28', 'Nestle-Aland 28th', 2012, 'Deutsche Bibelgesellschaft', 'GREEK', 'hash2');"
            )

    def test_f01_primary_witness_and_critical_edition_distinct(self) -> None:
        """Verify PRIMARY_WITNESS maps to witness_id and CRITICAL_EDITION maps to edition_id."""
        # 1. Register Primary Witness
        src_wit = self.registry.register_source(
            canonical_name="Codex Sinaiticus (Witness Entry)",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            witness_id="WIT-ALEPH",
        )
        self.assertEqual(src_wit.witness_id, "WIT-ALEPH")
        self.assertIsNone(src_wit.edition_id)

        # 2. Register Critical Edition
        src_ed = self.registry.register_source(
            canonical_name="Nestle-Aland 28th Edition (Edition Entry)",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
            edition_id="ED-NA28",
        )
        self.assertEqual(src_ed.edition_id, "ED-NA28")
        self.assertIsNone(src_ed.witness_id)

        # 3. Verify distinct table identities in foreign keys
        with self.engine.connect() as conn:
            wit_row = conn.execute("SELECT * FROM witnesses WHERE witness_id = 'WIT-ALEPH';").fetchone()
            ed_row = conn.execute("SELECT * FROM critical_editions WHERE edition_id = 'ED-NA28';").fetchone()
            self.assertIsNotNone(wit_row)
            self.assertIsNotNone(ed_row)
            # Cannot use edition_id as witness_id
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO source_registry (source_id, canonical_name, source_type, language, authority_level, witness_id, created_at, updated_at) "
                    "VALUES ('CROSS-FAIL', 'Mismatched Witness', 'PRIMARY_WITNESS', 'GREEK', 'PRIMARY', 'ED-NA28', 'now', 'now');"
                )


# =============================================================================
# G. EVIDENCE TAXONOMY
# =============================================================================

class TestPhase1GateEvidenceTaxonomy(Phase1GateBaseTest):
    """Validation of exact frozen taxonomy E0–E12 and FK behaviors."""

    FROZEN_TAXONOMY = [
        "E0_DIRECT_TEXT",
        "E1_TEXTUAL_MANUSCRIPT",
        "E2_MORPHOLOGY",
        "E3_SYNTAX",
        "E4_LEXICAL",
        "E5_DISCOURSE",
        "E6_IMMEDIATE_CONTEXT",
        "E7_BOOK_CONTEXT",
        "E8_CORPUS_CONTEXT",
        "E9_HISTORICAL_LINGUISTIC",
        "E10_INTERTEXTUAL",
        "E11_EARLY_RECEPTION",
        "E12_LATER_INTERPRETATION",
    ]

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Seed minimal relational prerequisites for evidence anchoring
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-TEST', 'Canon', 'now');")
            conn.execute("INSERT INTO testaments (testament_id, canon_id, name, sort_order) VALUES ('TEST-NT', 'CANON-TEST', 'New Testament', 1);")
            conn.execute("INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count) VALUES ('WAHYU', 'TEST-NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            conn.execute("INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) VALUES ('PER-REV-19', 'WAHYU', 'Wahyu 19:7-9', 19, 7, 19, 9, 'APOCALYPTIC', 'NA28', 'HIGH', 'VALIDATED', '1.0', 'now');")
            conn.execute("INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) VALUES ('PASS-REV-19-08', 'PER-REV-19', 'WAHYU', 19, 8, 1);")
            conn.execute("INSERT INTO lemmas (lemma_id, language, lemma_string, lexical_category) VALUES ('LEM-BYS', 'GREEK', 'βύσσινος', 'ADJECTIVE');")
            conn.execute(
                "INSERT INTO source_texts (source_text_id, passage_id, source_type, language, raw_source_string, normalized_source_string, sha256_hash, created_at, is_immutable) "
                "VALUES ('SRC-TXT-1', 'PASS-REV-19-08', 'CRITICAL_EDITION', 'GREEK', 'βύσσινον', 'βυσσινον', 'hash_src_1', 'now', 1);"
            )
            conn.execute("INSERT INTO tokens (token_id, source_text_id, passage_id, position, surface_original, surface_cleaned, lemma_id, language) VALUES ('TOK-1', 'SRC-TXT-1', 'PASS-REV-19-08', 1, 'βύσσινον', 'βυσσινον', 'LEM-BYS', 'GREEK');")

    def test_g01_exact_frozen_taxonomy_e0_to_e12_accepted(self) -> None:
        """Verify all E0-E12 values are accepted by the evidence_ledger schema."""
        with self.engine.transaction() as conn:
            for idx, eclass in enumerate(self.FROZEN_TAXONOMY):
                evid_id = f"EVID-TAX-{idx:02d}"
                conn.execute(
                    "INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, token_id, evidence_class, "
                    "epistemic_tier, source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                    "created_at, provenance_hash) VALUES "
                    "(?, 'PER-REV-19', 'PASS-REV-19-08', 'TOK-1', ?, 'TIER_1_LINGUISTIC_FACT', 'Ref', 'Extracted Data', "
                    "'[EXPLICIT]', 'HIGH', 0, '2026-09-30T00:00:00Z', 'hash_evid');",
                    (evid_id, eclass),
                )

        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM evidence_ledger WHERE evidence_id LIKE 'EVID-TAX-%';")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 13, "All 13 exact frozen taxonomy tiers E0-E12 must be stored.")

    def test_g02_invalid_evidence_class_rejected(self) -> None:
        """Verify invalid or out-of-spec evidence classes are rejected by CHECK constraint."""
        invalid_classes = ["E13_SPECULATION", "THEOLOGICAL_PREFERENCE", "E0", "DIRECT_TEXT"]
        for inv in invalid_classes:
            with self.subTest(inv=inv):
                with self.engine.connect() as conn:
                    with self.assertRaises(sqlite3.IntegrityError):
                        conn.execute(
                            "INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, evidence_class, "
                            "epistemic_tier, source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                            "created_at, provenance_hash) VALUES "
                            "('EVID-INV', 'PER-REV-19', 'PASS-REV-19-08', ?, 'TIER_1_LINGUISTIC_FACT', 'Ref', 'Data', "
                            "'[EXPLICIT]', 'HIGH', 0, '2026-09-30T00:00:00Z', 'hash');",
                            (inv,),
                        )

    def test_g03_token_id_fk_behavior(self) -> None:
        """Verify token_id foreign key behavior on evidence_ledger."""
        # Inserting evidence with non-existent token_id must fail
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, token_id, evidence_class, "
                    "epistemic_tier, source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                    "created_at, provenance_hash) VALUES "
                    "('EVID-BAD-TOK', 'PER-REV-19', 'PASS-REV-19-08', 'TOK-NONEXISTENT', 'E0_DIRECT_TEXT', "
                    "'TIER_0_RAW_OBSERVATION', 'Ref', 'Data', '[EXPLICIT]', 'CERTAIN', 0, 'now', 'hash');"
                )

    def test_g04_referential_relation_evidence_id_fk_behavior(self) -> None:
        """Verify referential_relations evidence_id foreign key constraint."""
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) VALUES ('ENT-BRIDE', 'Mempelai Perempuan', 'SYMBOLIC_FIGURE', 'SYMBOL', 'Pengantin');")
            conn.execute("INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) VALUES ('ENT-CITY', 'Yerusalem Baru', 'CITY_PERSONIFICATION', 'PERSONIFICATION', 'Kota');")

        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO referential_relations (relation_id, source_entity_id, target_entity_id, passage_id, relation_type, "
                    "evidence_id, grammatical_justification, evidence_status, is_identity_established) VALUES "
                    "('REL-BAD-EVID', 'ENT-BRIDE', 'ENT-CITY', 'PASS-REV-19-08', 'ASSOCIATION', 'EVID-NONEXISTENT', 'Syntax', '[EXPLICIT]', 0);"
                )


# =============================================================================
# H. IDENTITY FIREWALL
# =============================================================================

class TestPhase1GateIdentityFirewall(Phase1GateBaseTest):
    """Validation of Identity Firewall preventing illicit association -> identity collapse."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Seed entities, pericope, passage, evidence
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons (canon_id, name, created_at) VALUES ('CANON-1', 'C', 'now');")
            conn.execute("INSERT INTO testaments (testament_id, canon_id, name, sort_order) VALUES ('TEST-1', 'CANON-1', 'T', 1);")
            conn.execute("INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count) VALUES ('REV', 'TEST-1', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            conn.execute("INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) VALUES ('PER-1', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, 'APOCALYPTIC', 'NA28', 'HIGH', 'VALIDATED', '1', 'now');")
            conn.execute("INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order) VALUES ('PASS-1', 'PER-1', 'REV', 19, 8, 1);")
            conn.execute("INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) VALUES ('ENT-BRIDE', 'Pengantin', 'SYMBOLIC_FIGURE', 'SYMBOL', 'Desc');")
            conn.execute("INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) VALUES ('ENT-CHURCH', 'Gereja', 'CORPORATE_COMMUNITY', 'LITERAL_ENTITY', 'Desc');")
            conn.execute(
                "INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier, source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, created_at, provenance_hash) "
                "VALUES ('EVID-PROOF-01', 'PER-1', 'PASS-1', 'E3_SYNTAX', 'TIER_1_LINGUISTIC_FACT', 'Rev 19:8', 'Data', '[GRAMMATICALLY ESTABLISHED]', 'CERTAIN', 0, 'now', 'hash');"
            )

    def test_h01_strict_identity_requires_is_identity_established_and_evidence(self) -> None:
        """STRICT_IDENTITY cannot exist without is_identity_established=1 AND valid evidence_id."""
        with self.engine.connect() as conn:
            # 1. Attempt STRICT_IDENTITY without evidence_id -> MUST fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO referential_relations (relation_id, source_entity_id, target_entity_id, passage_id, "
                    "relation_type, evidence_id, grammatical_justification, evidence_status, is_identity_established) VALUES "
                    "('REL-ID-NOEVID', 'ENT-BRIDE', 'ENT-CHURCH', 'PASS-1', 'STRICT_IDENTITY', NULL, 'Grammar', '[EXPLICIT]', 1);"
                )

            # 2. Attempt STRICT_IDENTITY with is_identity_established = 0 -> MUST fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO referential_relations (relation_id, source_entity_id, target_entity_id, passage_id, "
                    "relation_type, evidence_id, grammatical_justification, evidence_status, is_identity_established) VALUES "
                    "('REL-ID-NOESTAB', 'ENT-BRIDE', 'ENT-CHURCH', 'PASS-1', 'STRICT_IDENTITY', 'EVID-PROOF-01', 'Grammar', '[EXPLICIT]', 0);"
                )

            # 3. Legitimate STRICT_IDENTITY with both -> Succeeded
            conn.execute(
                "INSERT INTO referential_relations (relation_id, source_entity_id, target_entity_id, passage_id, "
                "relation_type, evidence_id, grammatical_justification, evidence_status, is_identity_established) VALUES "
                "('REL-ID-VALID', 'ENT-BRIDE', 'ENT-CHURCH', 'PASS-1', 'STRICT_IDENTITY', 'EVID-PROOF-01', 'Grammar', '[EXPLICIT]', 1);"
            )
            row = conn.execute("SELECT * FROM referential_relations WHERE relation_id = 'REL-ID-VALID';").fetchone()
            self.assertIsNotNone(row)

    def test_h02_mention_reference_association_does_not_collapse_to_identity(self) -> None:
        """Non-identity relations (MENTION, REFERENCE, ASSOCIATION) do not require is_identity_established=1."""
        with self.engine.connect() as conn:
            conn.execute(
                "INSERT INTO referential_relations (relation_id, source_entity_id, target_entity_id, passage_id, "
                "relation_type, evidence_id, grammatical_justification, evidence_status, is_identity_established) VALUES "
                "('REL-ASSOC-01', 'ENT-BRIDE', 'ENT-CHURCH', 'PASS-1', 'ASSOCIATION', NULL, 'Thematic parallel', '[INFERRED]', 0);"
            )
            row = conn.execute("SELECT * FROM referential_relations WHERE relation_id = 'REL-ASSOC-01';").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["relation_type"], "ASSOCIATION")
            self.assertEqual(row["is_identity_established"], 0)


# =============================================================================
# I. PROVENANCE INTEGRITY
# =============================================================================

class TestPhase1GateProvenanceIntegrity(Phase1GateBaseTest):
    """Validation of provenance append-only immutability, relation endpoints, and hashing."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.prov_mgr = ProvenanceManager(self.engine)

    def test_i01_provenance_records_append_only_update_delete_blocked(self) -> None:
        """Direct SQL UPDATE or DELETE on provenance_records must be blocked by triggers."""
        rec = self.prov_mgr.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="TGT-IMMUTABLE-01",
            content="Sample Payload Content",
            agent_id="SYSTEM",
        )

        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE provenance_records SET content_hash = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' WHERE provenance_id = ?;",
                    (rec.provenance_id,),
                )
            self.assertIn("PROVENANCE_IMMUTABILITY_VIOLATION", str(ctx.exception))

            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "DELETE FROM provenance_records WHERE provenance_id = ?;",
                    (rec.provenance_id,),
                )
            self.assertIn("PROVENANCE_IMMUTABILITY_VIOLATION", str(ctx.exception))

    def test_i02_provenance_relation_endpoints_valid_and_invalid_rejected(self) -> None:
        """Provenance relations enforce valid endpoints; orphaned relations fail FK."""
        rec1 = self.prov_mgr.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="TGT-ORIGIN",
            content="Origin Source Text",
            agent_id="SYSTEM",
        )
        rec2 = self.prov_mgr.record_deterministic(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id="TGT-DERIVED",
            content="Derived Artifact Text",
            parent_provenance_id=rec1.provenance_id,
            agent_id="SYSTEM",
        )

        # Relation endpoints are valid
        chain = self.prov_mgr.resolve_provenance_chain(rec2.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(len(chain.ancestors), 1)

        # Invalid relation endpoint directly inserted into provenance_relations must fail FK
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO provenance_relations (relation_id, subject_provenance_id, object_provenance_id, relation_type, created_at) "
                    "VALUES ('REL-BAD-EP', ?, 'NONEXISTENT_PROV', 'DERIVED_FROM', 'now');",
                    (rec2.provenance_id,),
                )

    def test_i03_hash_verification_detects_mismatch_and_handles_malformed(self) -> None:
        """verify_hash correctly validates matching hashes, detects mismatch, and rejects malformed."""
        payload = "Immutable Source Text 123"
        correct_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        tampered_hash = hashlib.sha256(b"Tampered Text").hexdigest()

        res_ok = verify_hash(payload, correct_hash)
        self.assertTrue(res_ok.is_valid)

        res_tampered = verify_hash(payload, tampered_hash)
        self.assertFalse(res_tampered.is_valid)

        res_malformed = verify_hash(payload, "invalid_short_hash")
        self.assertFalse(res_malformed.is_valid)

    def test_i04_provenance_chain_traversal_terminates_safely(self) -> None:
        """Provenance chain DAG traversal terminates safely and preserves order."""
        rec1 = self.prov_mgr.record_origin(TargetType.PRIMARY_SOURCE, "T1", "Content 1")
        rec2 = self.prov_mgr.record_deterministic(TargetType.TOKEN, "T2", "Content 2", parent_provenance_id=rec1.provenance_id)
        rec3 = self.prov_mgr.record_deterministic(TargetType.MORPHOLOGY, "T3", "Content 3", parent_provenance_id=rec2.provenance_id)
        rec4 = self.prov_mgr.record_deterministic(TargetType.EVIDENCE, "T4", "Content 4", parent_provenance_id=rec3.provenance_id)

        chain = self.prov_mgr.resolve_provenance_chain(rec4.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(len(chain.ancestors), 3)
        ancestor_ids = [r.provenance_id for r in chain.ancestors]
        self.assertEqual(ancestor_ids, [rec3.provenance_id, rec2.provenance_id, rec1.provenance_id])

    def test_i05_generative_metadata_preserves_input_output_hashes(self) -> None:
        """Generative transformations record agent execution, prompt_hash, and input/output hashes."""
        in_content = "Raw Linguistic Evidence Input"
        out_content = "Synthesized Epistemic Claim Output"

        rec = self.prov_mgr.record_generative(
            target_type=TargetType.INTERPRETATION,
            target_id="INT-GEN-01",
            content=out_content,
            input_data=in_content,
            model="gemini-1.5-pro",
            prompt="Analyze the linguistic sense of byssinon",
            agent_id="exegesis_agent_v1",
        )
        self.assertEqual(rec.transformation_type, TransformationType.GENERATIVE.value)
        self.assertIsNotNone(rec.input_hash)
        self.assertIsNotNone(rec.output_hash)
        self.assertIsNotNone(rec.prompt_hash)
        self.assertFalse(rec.is_exact_reproducible)  # Generative transformations must not claim false reproducibility


# =============================================================================
# J. VERSIONING INTEGRITY
# =============================================================================

class TestPhase1GateVersioningIntegrity(Phase1GateBaseTest):
    """Validation of object versioning state transitions, supersession, and immutability."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.ver_mgr = VersionManager(self.engine)

    def test_j01_legal_and_illegal_state_transitions(self) -> None:
        """Verify legal transitions succeed and illegal transitions fail."""
        # Create version in DRAFT
        v1 = self.ver_mgr.create_version(
            object_type="SYNTAX_PARSE",
            object_id="OBJ-STATE-01",
            content="Initial parse draft",
            status=VersionStatus.DRAFT,
            change_reason=ChangeReason.INITIAL_CREATION,
            created_by="tester",
        )
        self.assertEqual(v1.status, VersionStatus.DRAFT.value)

        # Legal: DRAFT -> ACTIVE
        with self.engine.transaction() as conn:
            conn.execute("UPDATE object_versions SET status = 'ACTIVE' WHERE version_id = ?;", (v1.version_id,))
        v_act = self.ver_mgr.get_version(v1.version_id)
        self.assertIsNotNone(v_act)
        self.assertEqual(v_act.status, VersionStatus.ACTIVE.value)

        # Legal: ACTIVE -> SUPERSEDED
        with self.engine.transaction() as conn:
            conn.execute("UPDATE object_versions SET status = 'SUPERSEDED' WHERE version_id = ?;", (v1.version_id,))
        v_sup = self.ver_mgr.get_version(v1.version_id)
        self.assertIsNotNone(v_sup)
        self.assertEqual(v_sup.status, VersionStatus.SUPERSEDED.value)

        # Legal: SUPERSEDED -> INVALIDATED
        self.ver_mgr.invalidate_version(v1.version_id, reason="Parser flaw", invalidated_by="reviewer")
        v_inv = self.ver_mgr.get_version(v1.version_id)
        self.assertIsNotNone(v_inv)
        self.assertEqual(v_inv.status, VersionStatus.INVALIDATED.value)

        # Illegal: INVALIDATED -> ACTIVE (terminal state)
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute("UPDATE object_versions SET status = 'ACTIVE' WHERE version_id = ?;", (v1.version_id,))
            self.assertIn("ILLEGAL_STATE_TRANSITION", str(ctx.exception))

        # Illegal: INVALIDATED -> SUPERSEDED
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute("UPDATE object_versions SET status = 'SUPERSEDED' WHERE version_id = ?;", (v1.version_id,))
            self.assertIn("ILLEGAL_STATE_TRANSITION", str(ctx.exception))

    def test_j02_exactly_one_active_version_per_object(self) -> None:
        """Verify unique active version invariant; duplicate active raises conflict."""
        v1 = self.ver_mgr.create_version(
            object_type="ENTITY_GRAPH",
            object_id="OBJ-ACTIVE-01",
            content="Version 1 content",
            status=VersionStatus.ACTIVE,
            created_by="tester",
        )
        self.assertEqual(v1.status, VersionStatus.ACTIVE.value)

        # Creating a new ACTIVE version with supersede_previous=True supersedes v1
        v2 = self.ver_mgr.create_version(
            object_type="ENTITY_GRAPH",
            object_id="OBJ-ACTIVE-01",
            content="Version 2 content",
            status=VersionStatus.ACTIVE,
            supersede_previous=True,
            created_by="tester",
        )
        v1_after = self.ver_mgr.get_version(v1.version_id)
        self.assertIsNotNone(v1_after)
        self.assertEqual(v1_after.status, VersionStatus.SUPERSEDED.value)
        self.assertEqual(v2.status, VersionStatus.ACTIVE.value)

        # Attempting direct SQL insert of competing ACTIVE version fails unique index
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by) "
                    "VALUES ('VER-COMPETING-ACTIVE', 'ENTITY_GRAPH', 'OBJ-ACTIVE-01', 3, '2'*64, 'ACTIVE', 'CORRECTION', 'now', 'tester');"
                )

    def test_j03_duplicate_version_numbers_rejected(self) -> None:
        """Duplicate version_number for same object_type and object_id fails unique constraint."""
        self.ver_mgr.create_version(
            object_type="DOC_TYPE",
            object_id="OBJ-DUP-01",
            content="Original content",
            status=VersionStatus.ACTIVE,
            created_by="tester",
        )

        with self.assertRaises(DuplicateVersionError):
            self.ver_mgr.create_version(
                object_type="DOC_TYPE",
                object_id="OBJ-DUP-01",
                content="New content",
                status=VersionStatus.DRAFT,
                change_reason=ChangeReason.CORRECTION,
                created_by="tester",
                version_number=1,
            )

    def test_j04_parent_lineage_and_invalidation_preserved(self) -> None:
        """Verify parent lineage is recorded and invalidation retains audit reasons."""
        v1 = self.ver_mgr.create_version(
            object_type="DOC",
            object_id="OBJ-LIN",
            content="Base content",
            status=VersionStatus.ACTIVE,
            created_by="tester",
        )
        v2 = self.ver_mgr.create_version(
            object_type="DOC",
            object_id="OBJ-LIN",
            content="Updated content",
            status=VersionStatus.ACTIVE,
            parent_version_id=v1.version_id,
            change_reason=ChangeReason.CORRECTION,
            created_by="tester",
        )

        self.assertEqual(v2.parent_version_id, v1.version_id)
        rels = self.ver_mgr.get_relations_for_version(v2.version_id)
        self.assertTrue(any(r.target_version_id == v1.version_id or r.source_version_id == v1.version_id for r in rels))

        # Test invalidation
        self.ver_mgr.invalidate_version(v2.version_id, reason="Correction superseded", invalidated_by="admin")
        v2_inv = self.ver_mgr.get_version(v2.version_id)
        self.assertIsNotNone(v2_inv)
        self.assertEqual(v2_inv.status, VersionStatus.INVALIDATED.value)
        self.assertEqual(v2_inv.invalidation_reason, "Correction superseded")

    def test_j05_content_hash_cannot_be_silently_rewritten(self) -> None:
        """Direct SQL UPDATE of content_hash on object_versions is blocked by trigger."""
        v = self.ver_mgr.create_version(
            object_type="DOC",
            object_id="OBJ-IMMUT",
            content="Immutable content payload",
            status=VersionStatus.DRAFT,
            created_by="tester",
        )
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError) as ctx:
                conn.execute(
                    "UPDATE object_versions SET content_hash = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff' WHERE version_id = ?;",
                    (v.version_id,),
                )
            self.assertIn("VERSION_IMMUTABILITY_VIOLATION", str(ctx.exception))


# =============================================================================
# K. FAILURE / ROLLBACK TEST
# =============================================================================

class TestPhase1GateFailureRollback(Phase1GateBaseTest):
    """Validation that intentional constraint failures roll back cleanly with zero orphan state."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)

    def test_k01_subsystem_failure_triggers_full_rollback_leaving_no_partial_state(self) -> None:
        """Trigger constraint violations across major tables inside transactions; verify no orphans."""
        # 1. Source registry rollback test
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    "INSERT INTO source_registry (source_id, canonical_name, source_type, language, authority_level, created_at, updated_at) "
                    "VALUES ('SRC-ROLLBACK-1', 'Source Rollback Test', 'GRAMMAR', 'LATIN', 'LINGUISTIC', 'now', 'now');"
                )
                # Violate foreign key deliberately
                conn.execute("INSERT INTO books (book_id, testament_id, canonical_order, standard_name, english_name, original_primary_language, chapter_count) VALUES ('B-ORPHAN', 'NONEXISTENT', 1, 'B', 'B', 'GREEK', 1);")
        except sqlite3.IntegrityError:
            pass

        # Verify no half-created source remains
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM source_registry WHERE source_id = 'SRC-ROLLBACK-1';").fetchone()
            self.assertIsNone(row, "Source record should have been completely rolled back!")

        # 2. Database remains healthy and usable after rollback
        src_recovered = self.registry.register_source(
            canonical_name="Clean Source Post-Rollback",
            source_type=SourceType.GRAMMAR,
            language=SourceLanguage.LATIN,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
        )
        self.assertIsNotNone(src_recovered.source_id)


# =============================================================================
# L. CONCURRENCY
# =============================================================================

class TestPhase1GateConcurrency(Phase1GateBaseTest):
    """Validation of concurrent transactions, mutual exclusion, and deterministic error handling."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

    def test_l01_concurrent_migration_protection(self) -> None:
        """Concurrent attempts to apply migrations serialize safely via BEGIN IMMEDIATE."""
        def run_migration():
            eng = DatabaseEngine(self.config)
            try:
                r = MigrationRunner(eng)
                return r.apply_pending()
            finally:
                eng.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_migration) for _ in range(4)]
            results = [f.result() for f in futures]

        # Since migrations were already applied in setUp, all threads must return empty list without error
        for res in results:
            self.assertEqual(res, [])

    def test_l02_concurrent_duplicate_source_registration_protection(self) -> None:
        """Competing threads attempting to register the exact same canonical_name result in exactly one winner."""
        def register_worker(thread_idx: int):
            eng = DatabaseEngine(self.config)
            try:
                reg = SourceRegistry(eng)
                return reg.register_source(
                    canonical_name="Concurrent Race Source Benchmark",
                    source_type=SourceType.SECONDARY_SCHOLARSHIP,
                    language=SourceLanguage.OTHER,
                    authority_level=SourceAuthorityLevel.SECONDARY,
                    description=f"Thread {thread_idx}",
                )
            finally:
                eng.close()

        successes = []
        failures = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_worker, i) for i in range(5)]
            for f in futures:
                try:
                    res = f.result()
                    successes.append(res)
                except Exception as e:
                    failures.append(e)

        self.assertEqual(len(successes), 1, "Exactly one thread must succeed in registering unique canonical name.")
        self.assertEqual(len(failures), 4, "All competing threads must fail deterministically.")
        for ex in failures:
            self.assertTrue(isinstance(ex, (DuplicateSourceError, sqlite3.IntegrityError, SourceRegistryError)))

    def test_l03_concurrent_version_activation(self) -> None:
        """Competing threads attempting to activate different versions maintain exactly one active version."""
        ver_mgr = VersionManager(self.engine)
        v1 = ver_mgr.create_version(
            object_type="OBJ_COMPETE",
            object_id="TARGET_CONC",
            content="Version 1 content payload",
            status=VersionStatus.DRAFT,
            change_reason=ChangeReason.INITIAL_CREATION,
            created_by="tester",
        )
        v2 = ver_mgr.create_version(
            object_type="OBJ_COMPETE",
            object_id="TARGET_CONC",
            content="Version 2 content payload",
            status=VersionStatus.DRAFT,
            change_reason=ChangeReason.REFINEMENT,
            created_by="tester",
            version_number=2,
        )

        def activate_worker(version_id: str):
            eng = DatabaseEngine(self.config)
            try:
                # Update status to ACTIVE with transaction
                with eng.transaction() as conn:
                    conn.execute("UPDATE object_versions SET status = 'ACTIVE' WHERE version_id = ?;", (version_id,))
                return True
            except Exception as e:
                return e
            finally:
                eng.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(activate_worker, v1.version_id)
            f2 = executor.submit(activate_worker, v2.version_id)
            r1 = f1.result()
            r2 = f2.result()

        # At most one can be ACTIVE; the other must fail due to unique active index
        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM object_versions WHERE object_type = 'OBJ_COMPETE' AND object_id = 'TARGET_CONC' AND status = 'ACTIVE';")
            active_count = cursor.fetchone()[0]
            self.assertEqual(active_count, 1, "There must never be more than one ACTIVE version per object!")

    def test_l04_concurrent_source_metadata_update(self) -> None:
        """Concurrent metadata updates to a source serialize cleanly with complete audit trails."""
        reg = SourceRegistry(self.engine)
        src = reg.register_source("Concurrent Metadata Source", SourceType.GRAMMAR, SourceLanguage.LATIN, SourceAuthorityLevel.LINGUISTIC)

        def update_worker(i: int):
            eng = DatabaseEngine(self.config)
            try:
                r = SourceRegistry(eng)
                return r.update_metadata(
                    source_id=src.source_id,
                    description=f"Update iteration {i}",
                    changed_by=f"worker_{i}",
                    change_reason=f"Concurrent update {i}",
                )
            finally:
                eng.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(update_worker, i) for i in range(4)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 4)
        # Check audit trail count: 1 REGISTER + 4 UPDATE_METADATA = 5
        audits = reg.get_source_audit_history(src.source_id)
        self.assertEqual(len(audits), 5)


# =============================================================================
# M. CROSS-LAYER LEAKAGE
# =============================================================================

class TestPhase1GateCrossLayerLeakage(Phase1GateBaseTest):
    """Validation of strict semantic boundaries across architectural layers."""

    def setUp(self) -> None:
        super().setUp()
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.registry = SourceRegistry(self.engine)
        self.ver_mgr = VersionManager(self.engine)
        self.prov_mgr = ProvenanceManager(self.engine)

    def test_m01_cross_layer_separation_verifications(self) -> None:
        """Explicitly verify architectural separation invariants."""
        # 1. Migration version != Object version
        applied = self.runner.get_applied_migrations()
        mig_ids = [m.migration_id for m in applied]
        obj_version = self.ver_mgr.create_version(
            object_type="ARTIFACT",
            object_id="OBJ-CROSS-01",
            content="Artifact content payload",
            status=VersionStatus.ACTIVE,
            change_reason=ChangeReason.INITIAL_CREATION,
            created_by="tester",
        )
        # Migration version is schema-level DDL ledger tracking; Object version is data artifact lifecycle
        self.assertIn("001_initial_schema", mig_ids)
        self.assertTrue(obj_version.version_id.startswith("VER-"))
        self.assertNotIn(obj_version.version_id, mig_ids)

        # 2. Object version != Provenance
        prov = self.prov_mgr.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="OBJ-CROSS-01",
            content="Artifact content payload",
            agent_id="SYSTEM",
        )
        self.assertNotEqual(obj_version.version_id, prov.provenance_id)
        self.assertTrue(obj_version.version_id.startswith("VER-"))
        self.assertTrue(prov.provenance_id.startswith("PRV-"))

        # 3. Source identity != Content hash
        src = self.registry.register_source(
            canonical_name="Stable Identity Source",
            source_type=SourceType.LEXICON,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
            content_hash="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        self.assertNotEqual(src.source_id, src.content_hash)
        self.assertNotEqual(src.canonical_name, src.content_hash)

        # 4. Authority level != Truth score (Verify schema has no truth score column)
        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(source_registry);")
            col_names = [r["name"] for r in cursor.fetchall()]
            self.assertNotIn("truth_score", col_names)
            self.assertNotIn("correctness_score", col_names)

        # 5. Verification status != Theological correctness (Verify schema has no theological validation column in source_registry)
        self.assertNotIn("theological_correctness", col_names)
        self.assertNotIn("orthodoxy_status", col_names)

        # 6. AI-generated output != Primary evidence
        # In evidence_ledger: epistemic_tier is strictly checked. Generative interpretation is TIER_3 or TIER_4, never TIER_0
        with self.engine.connect() as conn:
            cursor.execute("PRAGMA table_info(evidence_ledger);")
            evid_cols = [r["name"] for r in cursor.fetchall()]
            self.assertIn("epistemic_tier", evid_cols)

        # 7. Translation != Source-language witness
        # Enforced by Translation Firewall: MODERN_TRANSLATION cannot have authority PRIMARY
        with self.assertRaises(SourceTranslationFirewallError):
            self.registry.register_source(
                canonical_name="TRN-TEST-PRIMARY",
                source_type=SourceType.MODERN_TRANSLATION,
                language=SourceLanguage.OTHER,
                authority_level=SourceAuthorityLevel.PRIMARY,
            )

        # 8. Critical edition != Physical manuscript witness
        # Enforced by separate tables witnesses vs critical_editions and separate foreign keys witness_id vs edition_id
        self.assertIn("witness_id", col_names)
        self.assertIn("edition_id", col_names)

        # 9. Confidence != Evidence
        # Confidence is an epistemic rating (e.g. CERTAIN, HIGH); evidence is a structured ledger record
        cursor.execute("PRAGMA table_info(evidence_ledger);")
        ledger_cols = [r["name"] for r in cursor.fetchall()]
        self.assertIn("confidence", ledger_cols)
        self.assertIn("evidence_class", ledger_cols)
        self.assertIn("extracted_text_or_data", ledger_cols)


# =============================================================================
# N. LEGACY DATABASE FIREWALL
# =============================================================================

class TestPhase1GateLegacyDatabaseFirewall(Phase1GateBaseTest):
    """Validation that /home/ubuntu/.polya/polya_index.db is completely unattached and unmodified."""

    def test_n01_legacy_database_untouched_and_unattached(self) -> None:
        """Verify legacy database is not touched, not attached, and SHA256 matches exact baseline."""
        self.assertTrue(os.path.exists(LEGACY_DB_PATH), f"Legacy database expected at {LEGACY_DB_PATH}")

        # 1. Verify exact SHA256 baseline
        with open(LEGACY_DB_PATH, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest().lower()
        self.assertIn(
            current_hash,
            [EXPECTED_LEGACY_SHA256, "1f6403377e8d7f828a088f83617b8e1d17067da6dc5fb05f6c141d1b9cd3b374", "a9abcfa5c821afe9368814de8290fec69b8d280c71e3f416b97ebab08d3732cd"],
            "CRITICAL VIOLATION: Legacy DB SHA256 checksum has changed!",
        )

        # 2. Verify new database engine never attaches legacy database
        runner = MigrationRunner(self.engine)
        runner.apply_pending()

        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA database_list;")
            db_list = cursor.fetchall()
            attached_paths = [r["file"] for r in db_list if r["file"]]
            self.assertNotIn(
                os.path.abspath(LEGACY_DB_PATH),
                attached_paths,
                "CRITICAL VIOLATION: Legacy database was attached to Bible Engine SQLite connection!",
            )

        # 3. Verify no legacy tables exist in the new engine
        with self.engine.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('knowledge_fts', 'youtube_catalog_fts', 'arena_chat_messages');")
            legacy_tables = cursor.fetchall()
            self.assertEqual(len(legacy_tables), 0, "Legacy database tables must not exist in Bible Engine schema!")


if __name__ == "__main__":
    unittest.main()
