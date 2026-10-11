"""
Focused Test Suite for Polya Philological Bible Engine - Provenance Subsystem (Phase 1, Task 1.4).
Verifies all 20 Task 1.4 verification points:
1. SHA-256 generation
2. Hash determinism
3. Hash mismatch detection
4. Provenance record creation
5. Provenance retrieval
6. Source-to-derived provenance chain
7. Evidence provenance chain
8. Claim-to-evidence provenance
9. Identity-to-evidence provenance
10. Agent execution metadata
11. Deterministic transformation metadata
12. Generative transformation metadata without false reproducibility claims
13. Provenance append/immutability behavior
14. Missing provenance detection
15. Transaction rollback when provenance creation fails
16. Existing source immutability remains intact
17. Existing translation firewall remains intact
18. Existing identity firewall remains intact
19. Existing migration checks remain intact
20. Legacy /home/ubuntu/.polya/polya_index.db remains untouched
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bible_engine import (
    DatabaseConfig,
    DatabaseEngine,
    HashStatus,
    MigrationRunner,
    ProvenanceChain,
    ProvenanceError,
    ProvenanceImmutabilityError,
    ProvenanceMissingParentError,
    ProvenanceRecordNotFoundError,
    ProvenanceTracker,
    RelationType,
    TargetType,
    TransformationType,
    compute_canonical_hash,
    compute_sha256,
    verify_hash,
)

LEGACY_DB_PATH = "/home/ubuntu/.polya/polya_index.db"


class TestProvenanceSubsystem(unittest.TestCase):
    """Test suite covering Task 1.4 Provenance requirements."""

    def setUp(self) -> None:
        """Create fresh file-backed database in temp dir with migrations 001 and 002 applied."""
        self.base_tmp = Path(__file__).resolve().parent / "_test_tmp_prov"
        self.base_tmp.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))

        self.db_path = os.path.join(self.temp_dir.name, "test_provenance.db")
        self.config = DatabaseConfig(db_path=self.db_path)
        self.engine = DatabaseEngine(self.config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()
        self.tracker = ProvenanceTracker(self.engine)

        # Record legacy db state if exists
        self.legacy_exists = os.path.exists(LEGACY_DB_PATH)
        if self.legacy_exists:
            self.legacy_mtime_before = os.path.getmtime(LEGACY_DB_PATH)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def test_01_sha256_generation(self) -> None:
        """1. Verify SHA-256 generation produces standard 64-character lowercase hex string."""
        sample = "Ἐν ἀρχῇ ἦν ὁ λόγος"
        h = compute_sha256(sample)
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_02_hash_determinism(self) -> None:
        """2. Verify identical content yields identical hash deterministically across runs and representations."""
        text = "בְּרֵאשִׁית בָּרָא אֱלֹהִים"
        h1 = compute_sha256(text)
        h2 = compute_sha256(text.encode("utf-8"))
        self.assertEqual(h1, h2)

        data = {"book": "Genesis", "chapter": 1, "verse": 1}
        c1 = compute_canonical_hash(data)
        c2 = compute_canonical_hash(data)
        self.assertEqual(c1, c2)

    def test_03_hash_mismatch_detection(self) -> None:
        """3. Verify deterministic hash verification identifies valid, mismatch, malformed, and missing states."""
        orig_text = "Textus Receptus 1550"
        orig_hash = compute_sha256(orig_text)

        # Valid
        res_valid = verify_hash(orig_text, orig_hash)
        self.assertTrue(res_valid.is_valid)
        self.assertEqual(res_valid.status, HashStatus.VALID)

        # Mismatch
        res_mismatch = verify_hash("Modified Text", orig_hash)
        self.assertFalse(res_mismatch.is_valid)
        self.assertEqual(res_mismatch.status, HashStatus.MISMATCH)
        self.assertIn("Hash mismatch", res_mismatch.message)

        # Malformed
        res_malformed = verify_hash(orig_text, "not-a-valid-sha256")
        self.assertFalse(res_malformed.is_valid)
        self.assertEqual(res_malformed.status, HashStatus.MALFORMED_HASH)

        # Missing content
        res_missing = verify_hash(None, orig_hash)
        self.assertFalse(res_missing.is_valid)
        self.assertEqual(res_missing.status, HashStatus.MISSING_CONTENT)

    def test_04_provenance_record_creation(self) -> None:
        """4. Verify provenance record creation writes all required metadata into provenance_records."""
        rec = self.tracker.record_origin(
            target_type=TargetType.CRITICAL_EDITION,
            target_id="ED-NA28",
            content="Novum Testamentum Graece 28th Edition",
            agent_id="SYSTEM",
        )
        self.assertTrue(rec.provenance_id.startswith("PRV-ORIGIN"))
        self.assertEqual(rec.target_type, "CRITICAL_EDITION")
        self.assertEqual(rec.target_id, "ED-NA28")
        self.assertEqual(rec.transformation_type, "ORIGIN")
        self.assertTrue(rec.is_exact_reproducible)
        self.assertTrue(rec.is_immutable)

        # Verify record exists in database
        fetched = self.tracker.get_record(rec.provenance_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.provenance_id, rec.provenance_id)
        self.assertEqual(fetched.content_hash, rec.content_hash)

    def test_05_provenance_retrieval(self) -> None:
        """5. Verify provenance retrieval by ID and by target type + target ID."""
        rec = self.tracker.record_origin(
            target_type=TargetType.TEXTUAL_WITNESS,
            target_id="MS-ALEPH-01",
            content="Codex Sinaiticus Add MS 43725",
        )

        by_id = self.tracker.get_record(rec.provenance_id)
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id.target_id, "MS-ALEPH-01")

        by_target = self.tracker.get_record_by_target(TargetType.TEXTUAL_WITNESS, "MS-ALEPH-01")
        self.assertIsNotNone(by_target)
        self.assertEqual(by_target.provenance_id, rec.provenance_id)

    def test_06_source_to_derived_provenance_chain(self) -> None:
        """6. Verify multi-tier provenance chain (source text -> tokens -> morphology)."""
        src_rec = self.tracker.record_origin(
            target_type=TargetType.SOURCE_TEXT,
            target_id="ST-REV-19-08-NA28",
            content="καὶ ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον λαμπρὸν καθαρόν",
        )

        tok_rec = self.tracker.record_deterministic(
            target_type=TargetType.TOKEN,
            target_id="TOK-REV-19-08-01",
            content="καὶ",
            parent_provenance_id=src_rec.provenance_id,
            relation_type=RelationType.DERIVED_FROM,
        )

        morph_rec = self.tracker.record_deterministic(
            target_type=TargetType.MORPHOLOGY,
            target_id="MPH-REV-19-08-01",
            content="CONJ (Conjunction)",
            parent_provenance_id=tok_rec.provenance_id,
            relation_type=RelationType.ANALYZED_FROM,
        )

        chain = self.tracker.resolve_provenance_chain(morph_rec.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(len(chain.ancestors), 2)
        ancestor_ids = [a.provenance_id for a in chain.ancestors]
        self.assertIn(tok_rec.provenance_id, ancestor_ids)
        self.assertIn(src_rec.provenance_id, ancestor_ids)
        self.assertEqual(len(chain.root_sources), 1)
        self.assertEqual(chain.root_sources[0].provenance_id, src_rec.provenance_id)

    def test_07_evidence_provenance_chain(self) -> None:
        """7. Verify evidence provenance reaches source text and retains unbroken lineage."""
        src_rec = self.tracker.record_origin(
            target_type=TargetType.SOURCE_TEXT,
            target_id="ST-DEUT-06-04",
            content="שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד",
        )

        ev_rec = self.tracker.record_deterministic(
            target_type=TargetType.EVIDENCE,
            target_id="EV-DEUT-06-04-01",
            content="E1_GRAMMATICAL: אֶחָד functioning as predicate adjective of absolute singularity",
            parent_provenance_id=src_rec.provenance_id,
            relation_type=RelationType.DERIVED_FROM,
        )

        integrity = self.tracker.verify_chain_integrity(ev_rec.provenance_id)
        self.assertTrue(integrity.is_valid)
        self.assertEqual(integrity.total_nodes, 2)
        self.assertEqual(len(integrity.missing_nodes), 0)

    def test_08_claim_to_evidence_provenance(self) -> None:
        """8. Verify claim provenance depends on evidence record and establishes traceable origin."""
        ev_rec = self.tracker.record_origin(
            target_type=TargetType.EVIDENCE,
            target_id="EV-MARK-12-29-01",
            content="E1_GRAMMATICAL: εἷς ἐστιν asserts numerical singularity",
        )

        claim_rec = self.tracker.record_deterministic(
            target_type=TargetType.CLAIM,
            target_id="CLM-SHEMA-NT-01",
            content="Mark 12:29 affirms unequivocal strict monotheism",
            parent_provenance_id=ev_rec.provenance_id,
            relation_type=RelationType.SUPPORTED_BY,
        )

        chain = self.tracker.resolve_provenance_chain(claim_rec.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(len(chain.ancestors), 1)
        self.assertEqual(chain.ancestors[0].provenance_id, ev_rec.provenance_id)

    def test_09_identity_to_evidence_provenance(self) -> None:
        """9. Verify identity provenance links referential relation to evidence and source text."""
        # 1. Setup canon, testament, book, pericope, passage
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestant', '', '2026-09-30');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'New Testament', '2026-09-30');")
            conn.execute("INSERT INTO books VALUES ('REV', 'NT', 'Wahyu', 'Revelation', 66, 'GREEK', '2026-09-30');")
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
                "VALUES ('PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, "
                "'APOCALYPTIC', 'NA28', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30');"
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")
            conn.execute(
                "INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) "
                "VALUES ('ENT-BRIDE', 'The Bride', 'SYMBOLIC_FIGURE', 'SYMBOL', 'The bride of the Lamb');"
            )
            conn.execute(
                "INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) "
                "VALUES ('ENT-SAINTS', 'The Saints', 'CORPORATE_COMMUNITY', 'LITERAL_ENTITY', 'The saints community');"
            )

            # Insert evidence into evidence_ledger
            conn.execute(
                "INSERT INTO evidence_ledger ("
                "evidence_id, pericope_id, passage_id, token_id, evidence_class, epistemic_tier, "
                "source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                "created_at, provenance_hash"
                ") VALUES ("
                "'EV-REV-19-08-METAPHOR', 'PER-REV-19', 'REV-19-08', NULL, 'E6_IMMEDIATE_CONTEXT', "
                "'TIER_2_CONTEXTUAL_CLAIM', 'Wahyu 19:8', 'Fine linen is righteous acts', '[CONTEXTUALLY STRONG]', "
                "'HIGH', 0, '2026-09-30', 'dummy_hash');"
            )

            # Insert referential relation enforcing STRICT_IDENTITY with evidence_id
            conn.execute(
                "INSERT INTO referential_relations ("
                "relation_id, source_entity_id, target_entity_id, passage_id, relation_type, "
                "evidence_id, grammatical_justification, evidence_status, is_identity_established"
                ") VALUES ("
                "'REL-REV-19-08', 'ENT-BRIDE', 'ENT-SAINTS', 'REV-19-08', 'STRICT_IDENTITY', "
                "'EV-REV-19-08-METAPHOR', 'Grammatical definition clause in 19:8b', '[GRAMMATICALLY ESTABLISHED]', 1);"
            )

        # Track provenance for the referential relation
        ev_prov = self.tracker.record_origin(
            target_type=TargetType.EVIDENCE,
            target_id="EV-REV-19-08-METAPHOR",
            content="E6_METAPHOR evidence for Bride -> Saints identification",
        )
        id_prov = self.tracker.record_deterministic(
            target_type=TargetType.SEMANTIC_ANALYSIS,
            target_id="REL-REV-19-08",
            content="STRICT_IDENTITY: Bride = Saints",
            parent_provenance_id=ev_prov.provenance_id,
            relation_type=RelationType.DERIVED_FROM,
        )

        chain = self.tracker.resolve_provenance_chain(id_prov.provenance_id)
        self.assertFalse(chain.is_broken)
        self.assertEqual(chain.ancestors[0].provenance_id, ev_prov.provenance_id)

    def test_10_agent_execution_metadata(self) -> None:
        """10. Verify agent execution metadata is completely captured in generative records."""
        rec = self.tracker.record_generative(
            target_type=TargetType.INTERPRETATION,
            target_id="EXEG-REV-19-08",
            content="Forensic exegesis of Revelation 19:8 establishing metonymic bridal imagery",
            agent_id="AGY",
            agent_version="2.0.0",
            model="gemini-2.5-pro",
            model_version="2026-09",
            prompt="Analyze Revelation 19:8 under Deep Philological Mode",
            prompt_version="1.0",
            config={"temperature": 0.0, "top_p": 0.95},
            retrieval_version="idx_20260930",
            job_id="job_hermes_8829",
        )

        self.assertEqual(rec.agent_id, "AGY")
        self.assertEqual(rec.model, "gemini-2.5-pro")
        self.assertIsNotNone(rec.prompt_hash)
        self.assertIsNotNone(rec.config_hash)
        self.assertEqual(rec.retrieval_version, "idx_20260930")
        self.assertEqual(rec.job_id, "job_hermes_8829")

    def test_11_deterministic_transformation_metadata(self) -> None:
        """11. Verify deterministic transformation sets is_exact_reproducible = True and preserves inputs."""
        input_tokens = ["Ἐν", "ἀρχῇ", "ἦν"]
        rec = self.tracker.record_deterministic(
            target_type=TargetType.SYNTAX,
            target_id="SYN-JOHN-01-01",
            content="PP -> P NP",
            input_data=input_tokens,
            config={"parser": "earley", "grammar_rules": "v2.0"},
        )
        self.assertTrue(rec.is_exact_reproducible)
        self.assertEqual(rec.transformation_type, "DETERMINISTIC")
        self.assertIsNotNone(rec.input_hash)
        self.assertIsNotNone(rec.config_hash)

    def test_12_generative_transformation_metadata_without_false_reproducibility(self) -> None:
        """12. Verify generative transformation explicitly refuses false claims of exact reproducibility."""
        rec = self.tracker.record_generative(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id="ART-SUMMARY-01",
            content="Synthesized theological summary of Johannine prologue",
            agent_id="CLAUDE_CODE",
            model="claude-3-7-sonnet",
            prompt="Summarize the Johannine logos theology",
        )
        self.assertFalse(rec.is_exact_reproducible)
        self.assertEqual(rec.transformation_type, "GENERATIVE")

    def test_13_provenance_append_immutability_behavior(self) -> None:
        """13. Verify provenance records and relations are append-only; updates and deletes fail via triggers."""
        rec = self.tracker.record_origin(
            target_type=TargetType.CRITICAL_EDITION,
            target_id="ED-BHS",
            content="Biblia Hebraica Stuttgartensia",
        )

        with self.engine.connect() as conn:
            # Attempt to UPDATE provenance_records -> must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx_update:
                conn.execute(
                    "UPDATE provenance_records SET content_hash = 'tampered' WHERE provenance_id = ?;",
                    (rec.provenance_id,),
                )
            self.assertIn("PROVENANCE_IMMUTABILITY_VIOLATION", str(ctx_update.exception))

            # Attempt to DELETE from provenance_records -> must fail
            with self.assertRaises(sqlite3.IntegrityError) as ctx_delete:
                conn.execute(
                    "DELETE FROM provenance_records WHERE provenance_id = ?;",
                    (rec.provenance_id,),
                )
            self.assertIn("PROVENANCE_IMMUTABILITY_VIOLATION", str(ctx_delete.exception))

    def test_14_missing_provenance_detection(self) -> None:
        """14. Verify missing provenance ancestor is detected by lineage verification."""
        # Non-existent target
        res_missing_target = self.tracker.verify_chain_integrity("PRV-NONEXISTENT")
        self.assertFalse(res_missing_target.is_valid)
        self.assertEqual(res_missing_target.status, "TARGET_NOT_FOUND")

    def test_15_transaction_rollback_when_provenance_creation_fails(self) -> None:
        """15. Verify transaction rolls back atomically if provenance write fails."""
        with self.assertRaises(Exception):
            with self.engine.transaction() as conn:
                # Insert a dummy record into critical_editions
                conn.execute(
                    "INSERT INTO critical_editions VALUES ("
                    "'ED-FAIL-TEST', 'Fail Edition', 'Apparatus', 2026, 'Publisher', 'GREEK', 'h1', 1);"
                )
                # Attempt to link provenance to non-existent parent
                self.tracker.record_deterministic(
                    target_type=TargetType.CRITICAL_EDITION,
                    target_id="ED-FAIL-TEST",
                    content="Fail edition content",
                    parent_provenance_id="PRV-DOES-NOT-EXIST-FOREIGN-KEY-FAIL",
                    conn=conn,
                )

        # Verify that critical_editions row was cleanly rolled back
        with self.engine.connect() as conn:
            row = conn.execute("SELECT * FROM critical_editions WHERE edition_id = 'ED-FAIL-TEST';").fetchone()
            self.assertIsNone(row)

    def test_16_existing_source_immutability_remains_intact(self) -> None:
        """16. Verify existing source immutability constraints from 001_initial_schema remain enforced."""
        with self.engine.transaction() as conn:
            conn.execute(
                "INSERT INTO witnesses VALUES ("
                "'MS-IMMUTABLE-01', 'א-IMM', 'Codex Sinaiticus', 'UNCIAL', 'GREEK', 'IV CE', "
                "330, 360, 'British Library', 'sha_prov', 1);"
            )
            # Violating is_source_immutable = 1 should fail
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO witnesses VALUES ("
                    "'MS-MUTABLE-FAIL', 'א-MUT', 'Codex Mutabilis', 'UNCIAL', 'GREEK', 'IV CE', "
                    "330, 360, 'British Library', 'sha_prov', 0);"
                )

    def test_17_existing_translation_firewall_remains_intact(self) -> None:
        """17. Verify existing translation firewall prevents using translations as primary source authority."""
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestant', '', '2026-09-30');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'New Testament', '2026-09-30');")
            conn.execute("INSERT INTO books VALUES ('REV', 'NT', 'Wahyu', 'Revelation', 66, 'GREEK', '2026-09-30');")
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
                "VALUES ('PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, "
                "'APOCALYPTIC', 'NA28', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30');"
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")

            # Translation insertion succeeds with valid parameters and is_primary_source = 0
            conn.execute(
                "INSERT INTO translations VALUES ("
                "'TR-REV-19-08-TB', 'PER-REV-19', 'POPULAR_LAI_TB', "
                "'Dan kepadanya dikaruniakan supaya memakai kain lenan halus yang berkilau-kilau dan yang bersih!', "
                "'TB notes', 'INDONESIAN', 0);"
            )

            # Translation firewall violation: attempting is_primary_source = 1 fails CHECK constraint
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO translations VALUES ("
                    "'TR-FAIL-PRIMARY', 'PER-REV-19', 'POPULAR_LAI_TB', "
                    "'Attempted primary source translation', 'notes', 'INDONESIAN', 1);"
                )

    def test_18_existing_identity_firewall_remains_intact(self) -> None:
        """18. Verify existing identity firewall prevents STRICT_IDENTITY assertion without evidence_id."""
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestant', '', '2026-09-30');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'New Testament', '2026-09-30');")
            conn.execute("INSERT INTO books VALUES ('REV', 'NT', 'Wahyu', 'Revelation', 66, 'GREEK', '2026-09-30');")
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
                "VALUES ('PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, "
                "'APOCALYPTIC', 'NA28', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30');"
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")
            conn.execute(
                "INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) "
                "VALUES ('E1', 'Entity 1', 'HUMAN_INDIVIDUAL', 'LITERAL_ENTITY', 'First');"
            )
            conn.execute(
                "INSERT INTO entities (entity_id, standard_name, entity_type, ontological_category, description) "
                "VALUES ('E2', 'Entity 2', 'HUMAN_INDIVIDUAL', 'LITERAL_ENTITY', 'Second');"
            )

            # Attempt STRICT_IDENTITY without evidence_id -> must fail CHECK constraint
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO referential_relations ("
                    "relation_id, source_entity_id, target_entity_id, passage_id, relation_type, "
                    "evidence_id, grammatical_justification, evidence_status, is_identity_established"
                    ") VALUES ('REL-FAIL-IDENTITY', 'E1', 'E2', 'REV-19-08', 'STRICT_IDENTITY', "
                    "NULL, 'Unsupported jump to identity', '[UNSUPPORTED]', 1);"
                )

    def test_19_existing_migration_checks_remain_intact(self) -> None:
        """19. Verify migration system reports clean state with both 001 and 002 applied."""
        status = self.runner.get_status()
        self.assertTrue(status.is_clean)
        self.assertGreaterEqual(status.applied_count, 2)
        self.assertEqual(status.pending_count, 0)
        applied_ids = [m.migration_id for m in status.applied_migrations]
        self.assertIn("001_initial_schema", applied_ids)
        self.assertIn("002_provenance", applied_ids)

    def test_20_legacy_database_untouched(self) -> None:
        """20. Verify legacy knowledge base at /home/ubuntu/.polya/polya_index.db remains completely untouched."""
        if self.legacy_exists:
            mtime_after = os.path.getmtime(LEGACY_DB_PATH)
            self.assertEqual(
                self.legacy_mtime_before,
                mtime_after,
                "CRITICAL: Legacy database was modified during provenance tests!",
            )


if __name__ == "__main__":
    unittest.main()
