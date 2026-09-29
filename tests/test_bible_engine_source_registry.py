"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 1.6 Source Registry Subsystem Test Suite.

Verifies:
1. Source registration.
2. Source retrieval.
3. Source filtering/search.
4. Stable source identity.
5. Source type validation.
6. Language validation.
7. Provenance integration.
8. Versioning integration.
9. External identifier storage.
10. Verification status transitions.
11. Duplicate source rejection.
12. Invalid provenance rejection.
13. Invalid version rejection.
14. Hash validation.
15. Source immutability.
16. Translation cannot become primary witness.
17. Witness/edition distinction.
18. Historical metadata preservation.
19. Migration checksum integrity.
20. Legacy /home/ubuntu/.polya/polya_index.db remains untouched.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
import hashlib

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateSourceError,
    IllegalSourceStateTransitionError,
    InvalidSourceAuthorityError,
    InvalidSourceLanguageError,
    InvalidSourceTypeError,
    InvalidVerificationStatusError,
    SourceHashMismatchError,
    SourceImmutabilityError,
    SourceInvalidProvenanceError,
    SourceInvalidVersionError,
    SourceNotFoundError,
    SourceRegistryError,
    SourceTranslationFirewallError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker as ProvenanceManager, TargetType, TransformationType
from bible_engine.source_registry import (
    ExternalIdentifierType,
    SourceAuthorityLevel,
    SourceLanguage,
    SourceRecord,
    SourceRegistry,
    SourceType,
    SourceVerificationStatus,
    generate_source_id,
)
from bible_engine.versioning import ChangeReason, VersionManager, VersionStatus

LEGACY_DB_PATH = "/home/ubuntu/.polya/polya_index.db"


class TestSourceRegistrySubsystem(unittest.TestCase):
    """Authoritative test suite for Task 1.6 Source Registry."""

    def setUp(self) -> None:
        """Create fresh file-backed database with all migrations (001-004) applied."""
        try:
            self.temp_dir = tempfile.mkdtemp(dir="/dev/shm")
        except (OSError, FileNotFoundError):
            self.temp_dir = tempfile.mkdtemp()

        self.db_path = os.path.join(self.temp_dir, "test_source_registry.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.registry = SourceRegistry(self.engine)
        self.prov_mgr = ProvenanceManager(self.engine)
        self.ver_mgr = VersionManager(self.engine)

        self.legacy_exists = os.path.exists(LEGACY_DB_PATH)
        if self.legacy_exists:
            self.legacy_mtime_before = os.path.getmtime(LEGACY_DB_PATH)
            self.legacy_size_before = os.path.getsize(LEGACY_DB_PATH)

    def tearDown(self) -> None:
        """Clean up test resources."""
        self.engine.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # 1. Source registration
    # -------------------------------------------------------------------------
    def test_01_source_registration(self) -> None:
        """Verify successful registration of multiple representative source types."""
        # 1. Primary witness
        src_aleph = self.registry.register_source(
            canonical_name="Codex Sinaiticus",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            description="Fourth-century uncial manuscript of the Greek Bible",
            creator="Scribes A, B1, B2, D",
            date_or_period="IV CE",
            repository="British Library",
            external_identifier="01",
            external_identifier_type=ExternalIdentifierType.GREGORY_ALAND,
            external_identifier_verified=True,
        )
        self.assertIsNotNone(src_aleph.source_id)
        self.assertEqual(src_aleph.canonical_name, "Codex Sinaiticus")
        self.assertEqual(src_aleph.source_type, SourceType.PRIMARY_WITNESS)
        self.assertEqual(src_aleph.authority_level, SourceAuthorityLevel.PRIMARY)
        self.assertEqual(src_aleph.verification_status, SourceVerificationStatus.REGISTERED)

        # 2. Critical edition
        src_na28 = self.registry.register_source(
            canonical_name="Novum Testamentum Graece (NA28)",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
            creator="Institut für Neutestamentliche Textforschung",
            date_or_period="2012",
        )
        self.assertEqual(src_na28.source_type, SourceType.CRITICAL_EDITION)

        # 3. Lexicon
        src_bdag = self.registry.register_source(
            canonical_name="Bauer-Danker Greek-English Lexicon (BDAG)",
            source_type=SourceType.LEXICON,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
            creator="Frederick William Danker",
            date_or_period="2000",
        )
        self.assertEqual(src_bdag.source_type, SourceType.LEXICON)

        # 4. Modern translation (safely registered under TRANSLATION authority)
        src_tb = self.registry.register_source(
            canonical_name="Terjemahan Baru LAI (TB1)",
            source_type=SourceType.MODERN_TRANSLATION,
            language=SourceLanguage.OTHER,
            authority_level=SourceAuthorityLevel.TRANSLATION,
            creator="Lembaga Alkitab Indonesia",
            date_or_period="1974",
        )
        self.assertEqual(src_tb.source_type, SourceType.MODERN_TRANSLATION)
        self.assertEqual(src_tb.authority_level, SourceAuthorityLevel.TRANSLATION)

    # -------------------------------------------------------------------------
    # 2. Source retrieval
    # -------------------------------------------------------------------------
    def test_02_source_retrieval(self) -> None:
        """Verify retrieval by ID and rejection of non-existent identifiers."""
        created = self.registry.register_source(
            canonical_name="Codex Vaticanus",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            external_identifier="B/03",
        )
        retrieved = self.registry.get_source(created.source_id)
        self.assertEqual(created.source_id, retrieved.source_id)
        self.assertEqual(created.canonical_name, retrieved.canonical_name)

        with self.assertRaises(SourceNotFoundError):
            self.registry.get_source("SRC-NON-EXISTENT-999")

    # -------------------------------------------------------------------------
    # 3. Source filtering/search
    # -------------------------------------------------------------------------
    def test_03_source_filtering_and_search(self) -> None:
        """Verify filtering by type, language, status, and canonical name search."""
        self.registry.register_source(
            canonical_name="Codex Ephraemi Rescriptus",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        self.registry.register_source(
            canonical_name="Biblia Hebraica Stuttgartensia (BHS)",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.HEBREW,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
        )
        self.registry.register_source(
            canonical_name="Targum Onkelos",
            source_type=SourceType.ANCIENT_TRANSLATION,
            language=SourceLanguage.ARAMAIC,
            authority_level=SourceAuthorityLevel.RECEPTION,
        )

        # Filter by language
        hebrew_sources = self.registry.find_sources(language=SourceLanguage.HEBREW)
        self.assertEqual(len(hebrew_sources), 1)
        self.assertEqual(hebrew_sources[0].canonical_name, "Biblia Hebraica Stuttgartensia (BHS)")

        # Filter by source_type
        witnesses = self.registry.find_sources(source_type=SourceType.PRIMARY_WITNESS)
        self.assertEqual(len(witnesses), 1)
        self.assertEqual(witnesses[0].canonical_name, "Codex Ephraemi Rescriptus")

        # Substring search on canonical name
        search_res = self.registry.find_sources(canonical_name="Targum")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].canonical_name, "Targum Onkelos")

    # -------------------------------------------------------------------------
    # 4. Stable source identity
    # -------------------------------------------------------------------------
    def test_04_stable_source_identity(self) -> None:
        """Verify deterministic generation of source IDs and preservation of custom IDs."""
        id1 = generate_source_id(SourceType.PRIMARY_WITNESS, "Codex Sinaiticus")
        id2 = generate_source_id(SourceType.PRIMARY_WITNESS, "Codex Sinaiticus")
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("SRC-WIT-CODEX-SINAITICUS-"))

        # Explicit source_id provided
        custom_src = self.registry.register_source(
            source_id="SRC-CUSTOM-P46",
            canonical_name="Papyrus 46 (Chester Beatty II)",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        self.assertEqual(custom_src.source_id, "SRC-CUSTOM-P46")

    # -------------------------------------------------------------------------
    # 5. Source type validation
    # -------------------------------------------------------------------------
    def test_05_source_type_validation(self) -> None:
        """Verify rejection of invalid source classifications."""
        with self.assertRaises(InvalidSourceTypeError):
            self.registry.register_source(
                canonical_name="Invalid Resource",
                source_type="SUPER_SOURCE",  # Not in taxonomy
                language=SourceLanguage.GREEK,
                authority_level=SourceAuthorityLevel.PRIMARY,
            )

    # -------------------------------------------------------------------------
    # 6. Language validation
    # -------------------------------------------------------------------------
    def test_06_language_validation(self) -> None:
        """Verify rejection of invalid source languages."""
        with self.assertRaises(InvalidSourceLanguageError):
            self.registry.register_source(
                canonical_name="Invalid Language Resource",
                source_type=SourceType.LEXICON,
                language="ESPERANTO_UNKNOWN",
                authority_level=SourceAuthorityLevel.LINGUISTIC,
            )

    # -------------------------------------------------------------------------
    # 7. Provenance integration
    # -------------------------------------------------------------------------
    def test_07_provenance_integration(self) -> None:
        """Verify foreign key linking and resolution with Task 1.4 Provenance records."""
        prov = self.prov_mgr.record_origin(
            target_type=TargetType.PRIMARY_SOURCE,
            target_id="DOC-SINAITICUS-DIGITAL",
            content="Codex Sinaiticus John 1:1 transcription",
            schema_version="2.0.0",
        )
        # Register source with valid provenance_id
        src = self.registry.register_source(
            canonical_name="Digital Sinaiticus Transcription",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            provenance_id=prov.provenance_id,
        )
        self.assertEqual(src.provenance_id, prov.provenance_id)

        # Retrieve through registry API
        resolved_prov = self.registry.get_source_provenance(src.source_id)
        self.assertIsNotNone(resolved_prov)
        self.assertEqual(resolved_prov.provenance_id, prov.provenance_id)
        self.assertEqual(resolved_prov.target_id, "DOC-SINAITICUS-DIGITAL")

    # -------------------------------------------------------------------------
    # 8. Versioning integration
    # -------------------------------------------------------------------------
    def test_08_versioning_integration(self) -> None:
        """Verify foreign key linking and resolution with Task 1.5 Object Version records."""
        src = self.registry.register_source(
            canonical_name="Nestle-Aland Digital Collation",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
        )

        ver1 = self.ver_mgr.create_version(
            object_type="biblical_source",
            object_id=src.source_id,
            content={"edition": "NA28", "release": "1.0"},
            created_by="editor_agent",
            change_reason=ChangeReason.INITIAL_CREATION,
            status=VersionStatus.ACTIVE,
        )

        self.registry.attach_version(src.source_id, ver1.version_id)
        updated = self.registry.get_source(src.source_id)
        self.assertEqual(updated.current_version_id, ver1.version_id)

        # Retrieve versions for this source
        versions = self.registry.get_source_versions(src.source_id)
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0].version_id, ver1.version_id)

    # -------------------------------------------------------------------------
    # 9. External identifier storage
    # -------------------------------------------------------------------------
    def test_09_external_identifier_storage(self) -> None:
        """Verify storage of Gregory-Aland, Rahlfs, and Dead Sea Scroll identifiers."""
        src_dss = self.registry.register_source(
            canonical_name="Great Isaiah Scroll (1QIsa-a)",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.HEBREW,
            authority_level=SourceAuthorityLevel.PRIMARY,
            external_identifier="1QIsa-a",
            external_identifier_type=ExternalIdentifierType.DEAD_SEA_SCROLL,
            external_identifier_verified=True,
        )
        self.assertEqual(src_dss.external_identifier, "1QIsa-a")
        self.assertEqual(src_dss.external_identifier_type, ExternalIdentifierType.DEAD_SEA_SCROLL)
        self.assertTrue(src_dss.external_identifier_verified)

    # -------------------------------------------------------------------------
    # 10. Verification status transitions
    # -------------------------------------------------------------------------
    def test_10_verification_status_transitions(self) -> None:
        """Verify controlled status transitions and rejection of illegal transitions out of DEPRECATED."""
        src = self.registry.register_source(
            canonical_name="Unchecked Minuscule 1739",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            verification_status=SourceVerificationStatus.UNVERIFIED,
        )
        # UNVERIFIED -> PARTIALLY_VERIFIED
        v1 = self.registry.verify_source(src.source_id, SourceVerificationStatus.PARTIALLY_VERIFIED)
        self.assertEqual(v1.verification_status, SourceVerificationStatus.PARTIALLY_VERIFIED)

        # PARTIALLY_VERIFIED -> VERIFIED
        v2 = self.registry.verify_source(src.source_id, SourceVerificationStatus.VERIFIED)
        self.assertEqual(v2.verification_status, SourceVerificationStatus.VERIFIED)

        # VERIFIED -> DEPRECATED (terminal)
        v3 = self.registry.deprecate_source(src.source_id, reason="Superseded by high-resolution multi-spectral autopsy")
        self.assertEqual(v3.verification_status, SourceVerificationStatus.DEPRECATED)

        # DEPRECATED -> VERIFIED must fail
        with self.assertRaises(IllegalSourceStateTransitionError):
            self.registry.verify_source(src.source_id, SourceVerificationStatus.VERIFIED)

    # -------------------------------------------------------------------------
    # 11. Duplicate source rejection
    # -------------------------------------------------------------------------
    def test_11_duplicate_source_rejection(self) -> None:
        """Verify rejection of duplicate canonical names and duplicate IDs."""
        self.registry.register_source(
            source_id="SRC-TEST-DUP-01",
            canonical_name="Unique Canonical Name Alpha",
            source_type=SourceType.LEXICON,
            language=SourceLanguage.HEBREW,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
        )

        # Duplicate ID
        with self.assertRaises(DuplicateSourceError):
            self.registry.register_source(
                source_id="SRC-TEST-DUP-01",
                canonical_name="Different Name Beta",
                source_type=SourceType.LEXICON,
                language=SourceLanguage.HEBREW,
                authority_level=SourceAuthorityLevel.LINGUISTIC,
            )

        # Duplicate canonical name
        with self.assertRaises(DuplicateSourceError):
            self.registry.register_source(
                source_id="SRC-TEST-DUP-02",
                canonical_name="Unique Canonical Name Alpha",
                source_type=SourceType.LEXICON,
                language=SourceLanguage.HEBREW,
                authority_level=SourceAuthorityLevel.LINGUISTIC,
            )

    # -------------------------------------------------------------------------
    # 12. Invalid provenance rejection
    # -------------------------------------------------------------------------
    def test_12_invalid_provenance_rejection(self) -> None:
        """Verify rejection when registering or attaching a non-existent provenance ID."""
        with self.assertRaises(SourceInvalidProvenanceError):
            self.registry.register_source(
                canonical_name="Source Bad Provenance",
                source_type=SourceType.PRIMARY_WITNESS,
                language=SourceLanguage.GREEK,
                authority_level=SourceAuthorityLevel.PRIMARY,
                provenance_id="prov_non_existent_999",
            )

    # -------------------------------------------------------------------------
    # 13. Invalid version rejection
    # -------------------------------------------------------------------------
    def test_13_invalid_version_rejection(self) -> None:
        """Verify rejection when registering or attaching a non-existent version ID."""
        with self.assertRaises(SourceInvalidVersionError):
            self.registry.register_source(
                canonical_name="Source Bad Version",
                source_type=SourceType.PRIMARY_WITNESS,
                language=SourceLanguage.GREEK,
                authority_level=SourceAuthorityLevel.PRIMARY,
                current_version_id="ver_non_existent_999",
            )

    # -------------------------------------------------------------------------
    # 14. Hash validation
    # -------------------------------------------------------------------------
    def test_14_hash_validation(self) -> None:
        """Verify content hash validation and cryptographic integrity verification."""
        content = "Exact raw witness text"
        valid_hash = hashlib.sha256(content.encode("utf-8")).hexdigest().lower()

        # Malformed hash string (not 64 chars)
        with self.assertRaises(SourceHashMismatchError):
            self.registry.register_source(
                canonical_name="Malformed Hash Source",
                source_type=SourceType.PRIMARY_WITNESS,
                language=SourceLanguage.GREEK,
                authority_level=SourceAuthorityLevel.PRIMARY,
                content_hash="not_a_valid_sha256",
            )

        # Valid hash registered
        src = self.registry.register_source(
            canonical_name="Valid Hash Source",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            content_hash=valid_hash,
        )
        self.assertTrue(self.registry.verify_source_integrity(src.source_id, content))

        # Tampered content fails
        with self.assertRaises(SourceHashMismatchError):
            self.registry.verify_source_integrity(src.source_id, "Tampered text")

    # -------------------------------------------------------------------------
    # 15. Source immutability
    # -------------------------------------------------------------------------
    def test_15_source_immutability(self) -> None:
        """Verify database triggers block source deletion and core identity mutation."""
        src = self.registry.register_source(
            canonical_name="Immutable Source Test",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )

        # 1. DELETE is blocked
        with self.assertRaises(SourceImmutabilityError):
            try:
                with self.engine.transaction() as conn:
                    conn.execute("DELETE FROM source_registry WHERE source_id = ?", (src.source_id,))
            except Exception as e:
                self.registry._handle_sqlite_error(e)

        # 2. UPDATE on canonical_name is blocked
        with self.assertRaises(SourceImmutabilityError):
            try:
                with self.engine.transaction() as conn:
                    conn.execute(
                        "UPDATE source_registry SET canonical_name = 'Changed Name' WHERE source_id = ?",
                        (src.source_id,),
                    )
            except Exception as e:
                self.registry._handle_sqlite_error(e)

    # -------------------------------------------------------------------------
    # 16. Translation cannot become primary witness
    # -------------------------------------------------------------------------
    def test_16_translation_cannot_become_primary_witness(self) -> None:
        """Verify strict Translation Firewall invariants preventing translation elevation."""
        # 1. Modern translation cannot be registered with authority_level = PRIMARY
        with self.assertRaises(SourceTranslationFirewallError):
            self.registry.register_source(
                canonical_name="Modern English Version Violating Firewall",
                source_type=SourceType.MODERN_TRANSLATION,
                language=SourceLanguage.OTHER,
                authority_level=SourceAuthorityLevel.PRIMARY,
            )

        # 2. Modern translation cannot have witness_id
        with self.assertRaises(SourceTranslationFirewallError):
            self.registry.register_source(
                canonical_name="Modern Translation Posing As Witness",
                source_type=SourceType.MODERN_TRANSLATION,
                language=SourceLanguage.OTHER,
                authority_level=SourceAuthorityLevel.TRANSLATION,
                witness_id="MS-ALEPH-01",
            )

        # 3. Legitimate translation registered
        trn = self.registry.register_source(
            canonical_name="Authorized Version (KJV 1611)",
            source_type=SourceType.MODERN_TRANSLATION,
            language=SourceLanguage.OTHER,
            authority_level=SourceAuthorityLevel.TRANSLATION,
        )

        # 4. Trigger blocks updating source_type to PRIMARY_WITNESS
        with self.assertRaises(SourceTranslationFirewallError):
            try:
                with self.engine.transaction() as conn:
                    conn.execute(
                        "UPDATE source_registry SET source_type = 'PRIMARY_WITNESS' WHERE source_id = ?",
                        (trn.source_id,),
                    )
            except Exception as e:
                self.registry._handle_sqlite_error(e)

    # -------------------------------------------------------------------------
    # 17. Witness/edition distinction
    # -------------------------------------------------------------------------
    def test_17_witness_edition_distinction(self) -> None:
        """Verify distinct foreign key targets and types for witnesses vs critical editions."""
        # Insert a raw manuscript witness into witnesses table
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO witnesses (
                    witness_id, siglum, name, witness_type, language,
                    century_origin, provenance_hash, is_source_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                ("MS-B-03", "B", "Codex Vaticanus", "UNCIAL", "GREEK", "IV CE", "0" * 64),
            )
            # Insert a critical edition into critical_editions table
            conn.execute(
                """
                INSERT INTO critical_editions (
                    edition_id, name, scholarly_apparatus, publication_year,
                    publisher, source_language, provenance_hash, is_source_immutable
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                ("ED-UBS5", "UBS 5th Edition", "United Bible Societies", 2014, "German Bible Society", "GREEK", "0" * 64),
            )

        # Register witness catalog entry
        reg_witness = self.registry.register_source(
            canonical_name="Codex Vaticanus Catalog Entry",
            source_type=SourceType.PRIMARY_WITNESS,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
            witness_id="MS-B-03",
        )
        self.assertEqual(reg_witness.witness_id, "MS-B-03")
        self.assertIsNone(reg_witness.edition_id)

        # Register critical edition catalog entry
        reg_edition = self.registry.register_source(
            canonical_name="UBS5 Critical Edition Catalog Entry",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
            edition_id="ED-UBS5",
        )
        self.assertEqual(reg_edition.edition_id, "ED-UBS5")
        self.assertIsNone(reg_edition.witness_id)

    # -------------------------------------------------------------------------
    # 18. Historical metadata preservation
    # -------------------------------------------------------------------------
    def test_18_historical_metadata_preservation(self) -> None:
        """Verify auditable tracking of metadata updates and immutability of audit records."""
        src = self.registry.register_source(
            canonical_name="Audit Trail Test Source",
            source_type=SourceType.LEXICON,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.LINGUISTIC,
            description="Initial description",
        )

        self.registry.update_metadata(
            source_id=src.source_id,
            description="Updated scholarly description",
            creator="Scholarly Committee",
            changed_by="analyst_agent_01",
            change_reason="Corrected editorial attribution",
        )

        history = self.registry.get_source_audit_history(src.source_id)
        # Should have REGISTER and UPDATE_METADATA entries
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].action, "REGISTER")
        self.assertEqual(history[1].action, "UPDATE_METADATA")
        self.assertEqual(history[1].changed_by, "analyst_agent_01")
        self.assertEqual(history[1].change_reason, "Corrected editorial attribution")

        # Deleting from audit table is blocked
        with self.assertRaises(SourceImmutabilityError):
            try:
                with self.engine.transaction() as conn:
                    conn.execute("DELETE FROM source_registry_audit WHERE source_id = ?", (src.source_id,))
            except Exception as e:
                self.registry._handle_sqlite_error(e)

    # -------------------------------------------------------------------------
    # 19. Migration checksum integrity
    # -------------------------------------------------------------------------
    def test_19_migration_checksum_integrity_remains_intact(self) -> None:
        """Verify all migrations (001-004) report clean, verified checksums."""
        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertEqual(status.applied_count, 4)
        self.assertEqual(status.pending_count, 0)
        self.assertEqual(status.latest_applied_id, "004_source_registry")

        applied_ids = [m.migration_id for m in status.applied_migrations]
        self.assertEqual(
            applied_ids,
            ["001_initial_schema", "002_provenance", "003_versioning", "004_source_registry"],
        )

    # -------------------------------------------------------------------------
    # 20. Legacy database untouched
    # -------------------------------------------------------------------------
    def test_20_legacy_database_untouched(self) -> None:
        """Verify legacy knowledge base at /home/ubuntu/.polya/polya_index.db remains completely untouched."""
        if self.legacy_exists:
            mtime_after = os.path.getmtime(LEGACY_DB_PATH)
            size_after = os.path.getsize(LEGACY_DB_PATH)
            self.assertEqual(
                self.legacy_mtime_before,
                mtime_after,
                "Legacy database mtime was modified during test run!",
            )
            self.assertEqual(
                self.legacy_size_before,
                size_after,
                "Legacy database file size changed during test run!",
            )


if __name__ == "__main__":
    unittest.main()
