"""
Task 1.5 Focused Test Suite: Versioning Subsystem.
Strictly adheres to Architecture v2.0 FROZEN specification.

Verifies:
1. Version creation.
2. Version retrieval.
3. Current-version resolution.
4. Multiple versions for one object.
5. Historical version preservation.
6. Parent-version relationship.
7. Provenance integration.
8. Content-hash integrity.
9. Immutable version protection.
10. Supersession behavior.
11. Invalid-state transition rejection.
12. Invalidation behavior.
13. Duplicate version rejection.
14. Invalid parent rejection.
15. Invalid provenance rejection.
16. Concurrent version creation protection.
17. Source immutability remains intact.
18. Identity firewall remains intact.
19. Translation firewall remains intact.
20. Migration checksum integrity remains intact.
21. Legacy "/home/ubuntu/.polya/polya_index.db" remains untouched.
"""

from __future__ import annotations

import concurrent.futures
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from bible_engine import (
    ChangeReason,
    DatabaseConfig,
    DatabaseEngine,
    DuplicateVersionError,
    HashStatus,
    IllegalStateTransitionError,
    MigrationChecksumMismatchError,
    MigrationRunner,
    ObjectVersion,
    ProvenanceTracker,
    TargetType,
    TransformationType,
    VersionComparisonResult,
    VersionConcurrencyConflictError,
    VersionHashMismatchError,
    VersionImmutabilityError,
    VersionIntegrityError,
    VersionIntegrityResult,
    VersionInvalidParentError,
    VersionInvalidProvenanceError,
    VersionManager,
    VersionNotFoundError,
    VersionRelationType,
    VersionStatus,
    compute_canonical_hash,
    compute_sha256,
)

LEGACY_DB_PATH = "/home/ubuntu/.polya/polya_index.db"


class TestVersioningSubsystem(unittest.TestCase):
    """Focused Task 1.5 Versioning Tests."""

    def setUp(self) -> None:
        """Create fresh file-backed database in temp dir with all migrations applied."""
        try:
            self.base_tmp = Path(__file__).resolve().parent / "_test_tmp_ver"
            self.base_tmp.mkdir(parents=True, exist_ok=True)
            self.temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))
        except OSError:
            self.base_tmp = None
            self.temp_dir = tempfile.TemporaryDirectory()

        self.db_path = os.path.join(self.temp_dir.name, "test_versioning.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)

        # Record legacy db state if exists
        self.legacy_exists = os.path.exists(LEGACY_DB_PATH)
        if self.legacy_exists:
            self.legacy_mtime_before = os.path.getmtime(LEGACY_DB_PATH)
            self.legacy_size_before = os.path.getsize(LEGACY_DB_PATH)

    def tearDown(self) -> None:
        """Clean up database connections and temp files."""
        self.engine.close()
        self.temp_dir.cleanup()
        if self.base_tmp and self.base_tmp.exists():
            try:
                self.base_tmp.rmdir()
            except OSError:
                pass

    # -------------------------------------------------------------------------
    # 1. Version creation
    # -------------------------------------------------------------------------
    def test_01_version_creation(self) -> None:
        raw_text = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        ver = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="ST-JOH-01-01-NA28",
            content=raw_text,
            created_by="TEST_RUNNER",
            metadata={"edition": "NA28", "language": "GREEK"},
        )

        self.assertIsNotNone(ver)
        self.assertEqual(ver.object_type, "SOURCE_TEXT")
        self.assertEqual(ver.object_id, "ST-JOH-01-01-NA28")
        self.assertEqual(ver.version_number, 1)
        self.assertEqual(ver.status, VersionStatus.ACTIVE.value)
        self.assertEqual(ver.change_reason, ChangeReason.INITIAL_CREATION.value)
        self.assertEqual(ver.content_hash, compute_sha256(raw_text))
        self.assertEqual(ver.created_by, "TEST_RUNNER")
        self.assertIsNone(ver.parent_version_id)
        self.assertIsNone(ver.provenance_id)
        self.assertEqual(ver.metadata, {"edition": "NA28", "language": "GREEK"})

        # Verify in database directly
        with self.engine.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM object_versions WHERE version_id = ?;", (ver.version_id,)
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["content_hash"], ver.content_hash)
            self.assertEqual(row["version_number"], 1)

    # -------------------------------------------------------------------------
    # 2. Version retrieval
    # -------------------------------------------------------------------------
    def test_02_version_retrieval(self) -> None:
        content = "Test retrieval content"
        created = self.version_mgr.create_version(
            object_type="DERIVED_ARTIFACT",
            object_id="ART-001",
            content=content,
        )

        fetched = self.version_mgr.get_version(created.version_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.version_id, created.version_id)
        self.assertEqual(fetched.content_hash, created.content_hash)
        self.assertEqual(fetched.object_id, "ART-001")

        # Missing version returns None
        self.assertIsNone(self.version_mgr.get_version("NON-EXISTENT-ID"))

        # Missing version raises when raise_if_missing=True
        with self.assertRaises(VersionNotFoundError):
            self.version_mgr.get_version("NON-EXISTENT-ID", raise_if_missing=True)

    # -------------------------------------------------------------------------
    # 3. Current-version resolution
    # -------------------------------------------------------------------------
    def test_03_current_version_resolution(self) -> None:
        # Non-existent object returns None
        self.assertIsNone(self.version_mgr.get_current_version("CLAIM", "CLM-NONE"))

        # Create version 1 (ACTIVE)
        v1 = self.version_mgr.create_version(
            object_type="CLAIM",
            object_id="CLM-001",
            content="Initial claim content",
        )
        current = self.version_mgr.get_current_version("CLAIM", "CLM-001")
        self.assertIsNotNone(current)
        self.assertEqual(current.version_id, v1.version_id)
        self.assertEqual(current.version_number, 1)

        # Create version 2 (supersedes version 1, becomes ACTIVE)
        v2 = self.version_mgr.create_version(
            object_type="CLAIM",
            object_id="CLM-001",
            content="Refined claim content",
            change_reason=ChangeReason.REFINEMENT,
        )
        current_v2 = self.version_mgr.get_current_version("CLAIM", "CLM-001")
        self.assertIsNotNone(current_v2)
        self.assertEqual(current_v2.version_id, v2.version_id)
        self.assertEqual(current_v2.version_number, 2)

    # -------------------------------------------------------------------------
    # 4. Multiple versions for one object
    # -------------------------------------------------------------------------
    def test_04_multiple_versions_for_one_object(self) -> None:
        v1 = self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-REV-19-01",
            content="Pericope text v1",
        )
        v2 = self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-REV-19-01",
            content="Pericope text v2 (corrections)",
            change_reason=ChangeReason.CORRECTION,
        )
        v3 = self.version_mgr.create_version(
            object_type="PERICOPE",
            object_id="PERI-REV-19-01",
            content="Pericope text v3 (final apparatus collation)",
            change_reason=ChangeReason.REANALYSIS,
        )

        all_versions = self.version_mgr.list_versions("PERICOPE", "PERI-REV-19-01")
        self.assertEqual(len(all_versions), 3)
        self.assertEqual([v.version_number for v in all_versions], [1, 2, 3])
        self.assertEqual(all_versions[0].version_id, v1.version_id)
        self.assertEqual(all_versions[1].version_id, v2.version_id)
        self.assertEqual(all_versions[2].version_id, v3.version_id)

    # -------------------------------------------------------------------------
    # 5. Historical version preservation
    # -------------------------------------------------------------------------
    def test_05_historical_version_preservation(self) -> None:
        v1_content = "Ancient Manuscript Transcription Line 1"
        v1_hash = compute_sha256(v1_content)
        v1 = self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="ST-P46-01",
            content=v1_content,
        )

        # Create v2 and v3
        self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="ST-P46-01",
            content="Ancient Manuscript Transcription Line 1 (Re-collated)",
            change_reason=ChangeReason.SOURCE_CHANGE,
        )
        self.version_mgr.create_version(
            object_type="SOURCE_TEXT",
            object_id="ST-P46-01",
            content="Ancient Manuscript Transcription Line 1 (Multi-spectral imaging)",
            change_reason=ChangeReason.EVIDENCE_CHANGE,
        )

        # Re-fetch v1 and verify content hash, creation timestamp, and data are strictly preserved
        v1_rechecked = self.version_mgr.get_version(v1.version_id)
        self.assertIsNotNone(v1_rechecked)
        self.assertEqual(v1_rechecked.content_hash, v1_hash)
        self.assertEqual(v1_rechecked.created_at, v1.created_at)
        self.assertEqual(v1_rechecked.created_by, v1.created_by)
        self.assertEqual(v1_rechecked.version_number, 1)
        self.assertEqual(v1_rechecked.status, VersionStatus.SUPERSEDED.value)

    # -------------------------------------------------------------------------
    # 6. Parent-version relationship
    # -------------------------------------------------------------------------
    def test_06_parent_version_relationship(self) -> None:
        v1 = self.version_mgr.create_version(
            object_type="EXEGESIS_REPORT",
            object_id="RPT-001",
            content="Report Draft v1",
        )
        v2 = self.version_mgr.create_version(
            object_type="EXEGESIS_REPORT",
            object_id="RPT-001",
            content="Report Draft v2 (model upgrade)",
            parent_version_id=v1.version_id,
            change_reason=ChangeReason.MODEL_CHANGE,
            relation_type=VersionRelationType.REANALYSIS_OF,
        )

        self.assertEqual(v2.parent_version_id, v1.version_id)

        # Verify comparison lineage resolution
        comp = self.version_mgr.compare_versions(v1.version_id, v2.version_id)
        self.assertEqual(comp.lineage_relationship, "DIRECT_DESCENDANT")
        self.assertEqual(comp.version_delta, 1)
        self.assertFalse(comp.is_identical_content)

        # Check recorded relations
        rels = self.version_mgr.get_relations_for_version(v2.version_id)
        rel_types = {r.relation_type for r in rels}
        self.assertIn(VersionRelationType.SUPERSEDES.value, rel_types)
        self.assertIn(VersionRelationType.DERIVED_FROM.value, rel_types)
        self.assertIn(VersionRelationType.REANALYSIS_OF.value, rel_types)

    # -------------------------------------------------------------------------
    # 7. Provenance integration
    # -------------------------------------------------------------------------
    def test_07_provenance_integration(self) -> None:
        source_data = "Codex Sinaiticus John 1:1 raw folio"
        prov = self.tracker.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="MS-ALEPH-01-JOH1",
            content=source_data,
            agent_id="ARCHIVIST",
        )

        ver = self.version_mgr.create_version(
            object_type="PRIMARY_SOURCE",
            object_id="MS-ALEPH-01-JOH1",
            content=source_data,
            provenance_id=prov.provenance_id,
            change_reason=ChangeReason.INITIAL_CREATION,
        )

        self.assertEqual(ver.provenance_id, prov.provenance_id)

        # Verify integrity of version with provenance
        integrity = self.version_mgr.verify_version_integrity(ver.version_id, expected_content=source_data)
        self.assertTrue(integrity.is_valid)
        self.assertTrue(integrity.provenance_valid)
        self.assertTrue(integrity.hash_valid)

    # -------------------------------------------------------------------------
    # 8. Content-hash integrity
    # -------------------------------------------------------------------------
    def test_08_content_hash_integrity(self) -> None:
        content = "Syntactic parsing of Philippians 2:6"
        expected_hash = compute_sha256(content)

        # Success when content and matching hash provided
        ver = self.version_mgr.create_version(
            object_type="SYNTAX",
            object_id="SYN-PHP-02-06",
            content=content,
            content_hash=expected_hash,
        )
        self.assertEqual(ver.content_hash, expected_hash)

        # Failure when mismatched hash provided
        with self.assertRaises(VersionHashMismatchError):
            self.version_mgr.create_version(
                object_type="SYNTAX",
                object_id="SYN-PHP-02-06",
                content=content,
                content_hash="0000000000000000000000000000000000000000000000000000000000000000",
            )

    # -------------------------------------------------------------------------
    # 9. Immutable version protection
    # -------------------------------------------------------------------------
    def test_09_immutable_version_protection(self) -> None:
        ver = self.version_mgr.create_version(
            object_type="EVIDENCE",
            object_id="EVD-001",
            content="Evidence description",
            metadata={"source": "manuscript_p46"},
        )

        with self.engine.transaction() as conn:
            # 1. Direct update to content_hash must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    "UPDATE object_versions SET content_hash = 'tampered' WHERE version_id = ?;",
                    (ver.version_id,),
                )
            self.assertIn("VERSION_IMMUTABILITY_VIOLATION", str(ctx.exception))

            # 2. Direct update to version_number must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    "UPDATE object_versions SET version_number = 999 WHERE version_id = ?;",
                    (ver.version_id,),
                )
            self.assertIn("VERSION_IMMUTABILITY_VIOLATION", str(ctx.exception))

            # 3. Direct update to metadata must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    "UPDATE object_versions SET metadata = '{\"tampered\": true}' WHERE version_id = ?;",
                    (ver.version_id,),
                )
            self.assertIn("VERSION_IMMUTABILITY_VIOLATION", str(ctx.exception))

            # 4. Direct DELETE of historical version must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    "DELETE FROM object_versions WHERE version_id = ?;",
                    (ver.version_id,),
                )
            self.assertIn("VERSION_IMMUTABILITY_VIOLATION", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 10. Supersession behavior
    # -------------------------------------------------------------------------
    def test_10_supersession_behavior(self) -> None:
        v1 = self.version_mgr.create_version(
            object_type="INTERPRETATION",
            object_id="INT-001",
            content="Initial interpretation",
        )
        self.assertEqual(v1.status, VersionStatus.ACTIVE.value)

        # Supersede via API
        v2 = self.version_mgr.create_version(
            object_type="INTERPRETATION",
            object_id="INT-001",
            content="Refined interpretation",
            supersede_previous=False,
            status=VersionStatus.DRAFT,
        )
        self.assertEqual(v2.status, VersionStatus.DRAFT.value)

        # Supersede v1 explicitly pointing to v2
        superseded_v1 = self.version_mgr.supersede_version(v1.version_id, superseded_by_version_id=v2.version_id)
        self.assertEqual(superseded_v1.status, VersionStatus.SUPERSEDED.value)

        rels = self.version_mgr.get_relations_for_version(v1.version_id)
        rel_types = {r.relation_type for r in rels}
        self.assertIn(VersionRelationType.SUPERSEDED_BY.value, rel_types)

    # -------------------------------------------------------------------------
    # 11. Invalid-state transition rejection
    # -------------------------------------------------------------------------
    def test_11_invalid_state_transition_rejection(self) -> None:
        v1 = self.version_mgr.create_version(
            object_type="MORPHOLOGY",
            object_id="MORPH-001",
            content="Morphological parse",
        )
        v2 = self.version_mgr.create_version(
            object_type="MORPHOLOGY",
            object_id="MORPH-001",
            content="Corrected parse",
        )
        # v1 is now SUPERSEDED
        v1_current = self.version_mgr.get_version(v1.version_id)
        assert v1_current is not None
        self.assertEqual(v1_current.status, VersionStatus.SUPERSEDED.value)

        # 1. Attempt SUPERSEDED -> ACTIVE is illegal!
        with self.assertRaises(IllegalStateTransitionError):
            with self.engine.transaction() as conn:
                try:
                    conn.execute(
                        "UPDATE object_versions SET status = 'ACTIVE' WHERE version_id = ?;",
                        (v1.version_id,),
                    )
                except sqlite3.Error as e:
                    self.version_mgr._handle_sqlite_error(e)

        # 2. Invalidate v2
        self.version_mgr.invalidate_version(v2.version_id, reason="Parser bug")
        # 3. Attempt INVALIDATED -> ACTIVE is illegal!
        with self.assertRaises(IllegalStateTransitionError):
            with self.engine.transaction() as conn:
                try:
                    conn.execute(
                        "UPDATE object_versions SET status = 'ACTIVE' WHERE version_id = ?;",
                        (v2.version_id,),
                    )
                except sqlite3.Error as e:
                    self.version_mgr._handle_sqlite_error(e)

    # -------------------------------------------------------------------------
    # 12. Invalidation behavior
    # -------------------------------------------------------------------------
    def test_12_invalidation_behavior(self) -> None:
        ver = self.version_mgr.create_version(
            object_type="SEMANTIC_ANALYSIS",
            object_id="SEM-001",
            content="Semantic parse with erroneous lexical root",
        )
        invalidated = self.version_mgr.invalidate_version(
            ver.version_id,
            reason="Root extraction fallacy identified during philological cross-examination",
            invalidated_by="POLYA_EXEGESIS_AGENT",
        )

        self.assertEqual(invalidated.status, VersionStatus.INVALIDATED.value)
        self.assertIn("Root extraction fallacy", str(invalidated.invalidation_reason))
        self.assertEqual(invalidated.invalidated_by, "POLYA_EXEGESIS_AGENT")
        self.assertIsNotNone(invalidated.invalidated_at)

        # Current version query should now return None (since no active version exists)
        self.assertIsNone(self.version_mgr.get_current_version("SEMANTIC_ANALYSIS", "SEM-001"))

        # Re-invalidation is rejected
        with self.assertRaises(IllegalStateTransitionError):
            self.version_mgr.invalidate_version(ver.version_id, reason="Second invalidation")

    # -------------------------------------------------------------------------
    # 13. Duplicate version rejection
    # -------------------------------------------------------------------------
    def test_13_duplicate_version_rejection(self) -> None:
        v1 = self.version_mgr.create_version(
            object_type="TOKEN",
            object_id="TOK-001",
            content="Token text",
            version_number=1,
        )

        # Attempt to insert version with explicit duplicate version number
        with self.assertRaises(DuplicateVersionError):
            self.version_mgr.create_version(
                object_type="TOKEN",
                object_id="TOK-001",
                content="Token text modified",
                version_number=1,
            )

        # Attempt to insert with duplicate version_id
        with self.assertRaises(DuplicateVersionError):
            self.version_mgr.create_version(
                object_type="TOKEN",
                object_id="TOK-002",
                content="Different token",
                version_id=v1.version_id,
            )

    # -------------------------------------------------------------------------
    # 14. Invalid parent rejection
    # -------------------------------------------------------------------------
    def test_14_invalid_parent_rejection(self) -> None:
        # Non-existent parent ID
        with self.assertRaises(VersionInvalidParentError):
            self.version_mgr.create_version(
                object_type="CLAIM",
                object_id="CLM-PARENT-TEST",
                content="Claim text",
                parent_version_id="VER-NON-EXISTENT-PARENT",
            )

        # Parent from different object
        other_ver = self.version_mgr.create_version(
            object_type="CLAIM",
            object_id="CLM-OTHER",
            content="Other claim",
        )
        with self.assertRaises(VersionInvalidParentError):
            self.version_mgr.create_version(
                object_type="CLAIM",
                object_id="CLM-PARENT-TEST",
                content="Claim text",
                parent_version_id=other_ver.version_id,
            )

    # -------------------------------------------------------------------------
    # 15. Invalid provenance rejection
    # -------------------------------------------------------------------------
    def test_15_invalid_provenance_rejection(self) -> None:
        with self.assertRaises(VersionInvalidProvenanceError):
            self.version_mgr.create_version(
                object_type="PASSAGE",
                object_id="PAS-JOH-01-01",
                content="Passage content",
                provenance_id="PRV-NON-EXISTENT-RECORD",
            )

    # -------------------------------------------------------------------------
    # 16. Concurrent version creation protection
    # -------------------------------------------------------------------------
    def test_16_concurrent_version_creation_protection(self) -> None:
        """
        Verify atomic concurrency protection under multithreaded writers.
        Ensures monotonic version numbering and eliminates conflicting ACTIVE states.
        """
        object_type = "CONCURRENT_TEST"
        object_id = "OBJ-CONC-01"
        num_workers = 6

        # Helper worker function
        def _worker(worker_id: int) -> Optional[str]:
            # Create a separate connection engine for each thread against file DB
            thread_config = DatabaseConfig(db_path=self.db_path)
            thread_engine = DatabaseEngine(thread_config)
            mgr = VersionManager(thread_engine)
            try:
                ver = mgr.create_version(
                    object_type=object_type,
                    object_id=object_id,
                    content=f"Worker {worker_id} payload content at {datetime.now(timezone.utc)}",
                    created_by=f"WORKER_{worker_id}",
                    change_reason=ChangeReason.REANALYSIS,
                )
                return ver.version_id
            finally:
                thread_engine.close()

        created_ids = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_worker, i) for i in range(num_workers)]
            for f in concurrent.futures.as_completed(futures):
                created_ids.append(f.result())

        # Verify all versions were created with strictly unique version numbers
        all_vers = self.version_mgr.list_versions(object_type, object_id)
        self.assertEqual(len(all_vers), num_workers)
        version_nums = [v.version_number for v in all_vers]
        self.assertEqual(version_nums, list(range(1, num_workers + 1)))

        # Exactly ONE version must be ACTIVE
        active_vers = [v for v in all_vers if v.status == VersionStatus.ACTIVE.value]
        self.assertEqual(len(active_vers), 1)
        self.assertEqual(active_vers[0].version_number, num_workers)

    # -------------------------------------------------------------------------
    # 17. Source immutability remains intact
    # -------------------------------------------------------------------------
    def test_17_source_immutability_remains_intact(self) -> None:
        with self.engine.transaction() as conn:
            # Insert valid canon, testament, book, pericope, passage, edition, and source_text
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('REV', 'TEST_NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes VALUES (
                    'PER-REV-19-07-09', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                    'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'REGISTERED', '1.0', '2026-09-30'
                );
                """
            )
            conn.execute("INSERT OR IGNORE INTO passages VALUES ('REV-19-08', 'PER-REV-19-07-09', 'REV', 19, 8, 1);")
            conn.execute(
                "INSERT OR IGNORE INTO critical_editions VALUES ('ED-NA28', 'NA28', 'Apparatus', 2012, 'DBS', 'GREEK', 'prov_na28', 1);"
            )
            raw = "καὶ ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον λαμπρὸν καθαρόν"
            h = compute_sha256(raw)
            conn.execute(
                """
                INSERT OR IGNORE INTO source_texts (
                    source_text_id, passage_id, edition_id, witness_id, source_type,
                    language, raw_source_string, normalized_source_string, sha256_hash,
                    created_at, is_immutable
                ) VALUES ('ST-REV-19-08', 'REV-19-08', 'ED-NA28', NULL, 'CRITICAL_EDITION', 'GREEK', ?, ?, ?, '2026-09-30', 1);
                """,
                (raw, raw, h),
            )

            # Direct update on is_immutable=1 source text cannot alter sha256_hash without check
            # Verify source version creation does not touch source_texts table
            self.version_mgr.create_version(
                object_type="SOURCE_TEXT",
                object_id="ST-REV-19-08",
                content=raw,
            )

            # Verify row in source_texts still has exact hash
            row = conn.execute("SELECT sha256_hash, raw_source_string FROM source_texts WHERE source_text_id = 'ST-REV-19-08';").fetchone()
            self.assertEqual(row["sha256_hash"], h)
            self.assertEqual(row["raw_source_string"], raw)

    # -------------------------------------------------------------------------
    # 18. Identity firewall remains intact
    # -------------------------------------------------------------------------
    def test_18_identity_firewall_remains_intact(self) -> None:
        """Verify strict book standard name and referential identity constraints remain intact."""
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('REV', 'TEST_NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            # Verify canonical order uniqueness
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO books VALUES ('REV2', 'TEST_NT', 66, 'Wahyu Baru', 'Revelation 2', 'GREEK', 22);"
                )

    # -------------------------------------------------------------------------
    # 19. Translation firewall remains intact
    # -------------------------------------------------------------------------
    def test_19_translation_firewall_remains_intact(self) -> None:
        """Verify translation firewall (translations can NEVER be primary source)."""
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('REV', 'TEST_NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes VALUES (
                    'PER-REV-19-07-09', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                    'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'REGISTERED', '1.0', '2026-09-30'
                );
                """
            )
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute(
                    """
                    INSERT INTO translations (
                        translation_id, pericope_id, translation_type, translated_text,
                        translation_notes, language_target, is_primary_source
                    ) VALUES ('TR-001', 'PER-REV-19-07-09', 'POPULAR_LAI_TB', 'Teks terjemahan', NULL, 'id', 1);
                    """
                )
            self.assertIn("CHECK constraint failed", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 20. Migration checksum integrity remains intact
    # -------------------------------------------------------------------------
    def test_20_migration_checksum_integrity_remains_intact(self) -> None:
        """Verify all migrations (001, 002, 003) report clean and tamper-free checksums."""
        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertGreaterEqual(status.applied_count, 3)
        self.assertEqual(status.pending_count, 0)
        # Verify applied IDs list contains 001, 002, 003
        applied_ids = [m.migration_id for m in status.applied_migrations]
        self.assertIn("001_initial_schema", applied_ids)
        self.assertIn("002_provenance", applied_ids)
        self.assertIn("003_versioning", applied_ids)

    # -------------------------------------------------------------------------
    # 21. Legacy /home/ubuntu/.polya/polya_index.db remains untouched
    # -------------------------------------------------------------------------
    def test_21_legacy_database_untouched(self) -> None:
        """Verify legacy knowledge base at /home/ubuntu/.polya/polya_index.db remains completely untouched."""
        if self.legacy_exists:
            mtime_after = os.path.getmtime(LEGACY_DB_PATH)
            size_after = os.path.getsize(LEGACY_DB_PATH)
            self.assertEqual(
                self.legacy_mtime_before,
                mtime_after,
                "CRITICAL: Legacy database /home/ubuntu/.polya/polya_index.db was modified during versioning test execution!",
            )
            self.assertEqual(
                self.legacy_size_before,
                size_after,
                "CRITICAL: Legacy database /home/ubuntu/.polya/polya_index.db changed size!",
            )


if __name__ == "__main__":
    unittest.main()
