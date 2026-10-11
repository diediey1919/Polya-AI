"""
Unit and Adversarial Test Suite for Reception History Engine (Task 3.4).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Later interpretation != original authorial intent firewall
  2. Early reception != proof of original meaning firewall
  3. Patristic interpretation != automatic apostolic interpretation firewall
  4. Rabbinic interpretation != automatic Second Temple interpretation firewall
  5. Medieval interpretation != automatic biblical interpretation firewall
  6. Modern scholarly consensus != textual evidence firewall
  7. Denominational doctrine != ancient authorial intent firewall
  8. Chronology != influence firewall
  9. Citation != interpretation firewall
  10. Allusion != quotation firewall
  11. Translation != original source firewall
  12. Lexical similarity != reception firewall
  13. Thematic parallel != reception firewall
  14. Doctrinal formulation != textual reading firewall
  15. Reception source != authorial source firewall
  16. Reception history != canonical authority firewall
  17. Reception history != theological truth firewall
  18. Majority interpretation != verified fact firewall
  19. AI-generated summary != primary source firewall
  20. Modern commentary != historical witness firewall
  21. External identifier != verified identity firewall
  22. Confidence score != evidence upgrade firewall
  23. Temporal direction must not be reversed without evidence
  24. Counter-evidence cannot be suppressed
  25. Epistemic relevance differentiation (E11 primary for reception vs secondary for authorial)
  26. Actor date precision and identity status (uncertain/anonymous/disputed)
  27. Version lineage and supersession on reanalysis
  28. Immutability enforced by SQL triggers
  29. Rollback on failure leaves zero orphaned rows
  30. Concurrency safety under multithreaded writers
  31. Migrations 001-016 checksums strictly unchanged
  32. Legacy DB unaltered
"""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    ReceptionAISummaryNotPrimarySourceFirewallError,
    ReceptionActorNotFoundError,
    ReceptionAllusionNotQuotationFirewallError,
    ReceptionAuthorialIntentFirewallError,
    ReceptionChronologyNotInfluenceFirewallError,
    ReceptionCitationNotInterpretationFirewallError,
    ReceptionClaimNotFoundError,
    ReceptionConfidenceNotUpgradeFirewallError,
    ReceptionCounterEvidencePreservationFirewallError,
    ReceptionDenominationalNotAuthorialFirewallError,
    ReceptionDoctrinalNotTextualReadingFirewallError,
    ReceptionEarlyNotApostolicFirewallError,
    ReceptionHistorySubsystemError,
    ReceptionImmutabilityError,
    ReceptionLexicalNotReceptionFirewallError,
    ReceptionMajorityNotFactFirewallError,
    ReceptionMedievalNotBiblicalFirewallError,
    ReceptionModernCommentaryNotWitnessFirewallError,
    ReceptionNotCanonicalAuthorityFirewallError,
    ReceptionRabbinicNotSecondTempleFirewallError,
    ReceptionRecordNotFoundError,
    ReceptionRelationNotFoundError,
    ReceptionScholarlyNotTextualFirewallError,
    ReceptionSourceNotAuthorialSourceFirewallError,
    ReceptionSourceNotFoundError,
    ReceptionTemporalDirectionFirewallError,
    ReceptionThematicNotReceptionFirewallError,
    ReceptionTheologicalTruthFirewallError,
    ReceptionTranslationNotOriginalFirewallError,
    ReceptionUnverifiedIdentifierFirewallError,
    ReceptionValidationError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
    EvidenceDefinition,
    EvidenceRelationship,
    EvidenceStatus,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.reception_history import (
    ActorIdentityStatus,
    ActorType,
    ClaimRelevance,
    DatePrecision,
    EvidenceStance,
    ExegeticalMethod,
    ExternalIdentifierStatus,
    HistoricalEra,
    ReceptionActorDefinition,
    ReceptionClaimDefinition,
    ReceptionClaimType,
    ReceptionEra,
    ReceptionEvidenceLinkDefinition,
    ReceptionHistoryManager,
    ReceptionRecordDefinition,
    ReceptionRelationDefinition,
    ReceptionRelationType,
    ReceptionSourceDefinition,
    ReceptionSourceType,
    TemporalDirection,
)
from bible_engine.versioning import VersionManager

EXPECTED_MIGRATION_CHECKSUMS: Dict[str, str] = {
    "001_initial_schema.sql": "dca5e56fa1ab2ce5472e47aa5d61b1630fe9533d028df60a93506420516ce201",
    "002_provenance.sql": "f2932bfda7beb792d0993880d43ed7326965630f77526d756a235606b7793267",
    "003_versioning.sql": "83bf6b0a6a72156791cf6c701ad4501e3349b1ff602f01ab17df956a8cea8381",
    "004_source_registry.sql": "0613e2b35e957fed65ce9e75ac1b1dde00258860dfac219f3750472601fab33e",
    "005_source_text.sql": "e6d9663b5e94ea7610daa07979130fa00790e7157a1e86b421a6915192683a77",
    "006_tokenization.sql": "08782cf1aca1ac351419130c9d1d22cac034679154f75b5bada0819c8588bf3b",
    "007_morphology.sql": "dff8781a7c65828b5bdd542a321c4c81f499836cb38e96025154aee3a03eb145",
    "008_syntax.sql": "2daf0ebfd0022e480ea079ab02ec4d37f37eefa733281458327b19d20c3a649b",
    "009_semantics.sql": "93f606e376f80cef7e60f194961d4d163257a4dfb6444f35eb57974865183113",
    "010_referential_entity.sql": "1ec09317ceb1c21bbe4c451b0400538a7ad821ea615d423bc72b0141f4e6b055",
    "011_discourse_context.sql": "e09595cfc19c43d2e42b2f04925bd20fa7e6fb5bd0aa31937926d9afd3732c98",
    "012_evidence_claim.sql": "3c9bfd78943189caa1a56411f8aad0d1c1f5c37075618624513fe2ad37f31944",
    "013_exegesis.sql": "5289378259eeebd23f057e7a55f447c5cb8277d7861694b288d927080248f720",
    "014_textual_criticism.sql": "2ceec0c7e59d43998e279d2f7712b961747199b688cbee2c21b0347fe9ac0d41",
    "015_historical_linguistics.sql": "57acc411610d0618c140cb181dca02ded4f21a59d005a7e04fbbd84489061669",
    "016_intertextuality.sql": "ff15c7ce8d885d33588c4ff8d048d28c4f0c07ce9b21a57f53931490baa650dd",
}

EXPECTED_017_CHECKSUM = "76bfc99691e5d05da1fd662f4371187337a5aca943d8b57481b527125b965e13"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestReceptionHistoryEngine(unittest.TestCase):
    """Unit and Adversarial Test Suite for Reception History Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_reception.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.evidence_claim_manager = EvidenceClaimManager(self.engine)
        self.reception_mgr = ReceptionHistoryManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
            self.evidence_claim_manager,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('REV', 'TEST_NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-REV-19-07-09', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                    'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'REGISTERED', '1.0', '2026-09-30'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-REV-19-8', 'PER-REV-19-07-09', 'REV', 19, 8, 1);
                """
            )

        # Register seed version, provenance, and claim for evidence ledger
        self.seed_prov = self.provenance_tracker.record_origin(
            target_type=TargetType.EVIDENCE,
            target_id="SEED-REC-EVID",
            content="seed_content_str",
            agent_id="test_runner",
        )
        self.seed_ver = self.version_manager.create_version(
            object_type="HISTORICAL_SOURCE",
            object_id="SRC-PAT-OR-01",
            content="seed_content",
            provenance_id=self.seed_prov.provenance_id,
        )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO evidence_ledger (
                    evidence_id, pericope_id, passage_id, evidence_class,
                    epistemic_tier, source_reference, extracted_text_or_data,
                    status, confidence, confidence_score, created_at, provenance_hash, is_immutable
                ) VALUES (
                    'EV-REC-SEED-01', 'PER-REV-19-07-09', 'PAS-REV-19-8', 'E11_EARLY_RECEPTION',
                    'T2_CONTEXTUAL_CLAIM', 'Origen, Comm. in Joann. II.2', 'βύσσινον',
                    '[EXPLICIT]', 'HIGH', 0.85, '2026-10-01T00:00:00Z', 'hash_rec_seed', 1
                );
                """
            )
            conn.execute(
                """
                INSERT INTO claims (
                    claim_id, pericope_id, passage_id, claim_tier, epistemic_type, claim_text,
                    claimed_by, confidence_score, calculated_confidence, epistemic_status,
                    version_id, provenance_id, created_at, is_immutable
                ) VALUES (
                    'CLM-REC-SEED-01', 'PER-REV-19-07-09', 'PAS-REV-19-8', 'T2_CONTEXTUAL_CLAIM', 'CONTEXTUAL_FACT',
                    'Origen understood fine linen allegorically as the virtues of saints.',
                    'test_runner', 0.90, 0.90, 'VERIFIED_FACT',
                    ?, ?, '2026-10-01T00:00:00Z', 1
                );
                """,
                (self.seed_ver.version_id, self.seed_prov.provenance_id),
            )

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. LATER INTERPRETATION != ORIGINAL AUTHORIAL INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_01_later_interpretation_not_authorial_intent_firewall(self) -> None:
        """Later reception cannot equate itself to ancient authorial intent."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-INTENT",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM.value,
            claim_statement="Author of Revelation meant Origen's exact allegorical schema.",
            temporal_direction=TemporalDirection.RECEPTION_TO_INTERPRETATION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_authorial_intent_equated=True,  # VIOLATION
        )
        with self.assertRaises(ReceptionAuthorialIntentFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-01",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 2. RECEPTION HISTORY != THEOLOGICAL TRUTH FIREWALL
    # -------------------------------------------------------------------------
    def test_02_reception_history_not_theological_truth_firewall(self) -> None:
        """Reception history record cannot assert absolute theological dogma."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-THEOL",
            record_id="REC-001",
            claim_type=ReceptionClaimType.DOCTRINAL_DEVELOPMENT.value,
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM.value,
            claim_statement="The fine linen is dogmatically defined as infused grace.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.THEOLOGICAL_TRADITION_RELEVANT.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_theological_truth_equated=True,  # VIOLATION
        )
        with self.assertRaises(ReceptionTheologicalTruthFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-02",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 3. DOCTRINAL FORMULATION != T1 LINGUISTIC FACT FIREWALL
    # -------------------------------------------------------------------------
    def test_03_doctrinal_development_cannot_create_t1_linguistic_fact(self) -> None:
        """Reception doctrine/reading cannot masquerade as T1 linguistic fact."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-T1-DOCTRINE",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT.value,  # VIOLATION
            claim_statement="The Greek noun bussinon grammatically means sacramental grace.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionDoctrinalNotTextualReadingFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-03",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 4. CHRONOLOGY != CAUSAL INFLUENCE FIREWALL
    # -------------------------------------------------------------------------
    def test_04_chronology_not_influence_firewall(self) -> None:
        """Asserting causal influence requires verified chronological sequence."""
        rel = ReceptionRelationDefinition(
            relation_id="REL-ERR-INFL",
            source_record_id="REC-001",
            target_record_id="REC-002",
            relation_type=ReceptionRelationType.DIRECT_DEPENDENCE.value,
            temporal_direction=TemporalDirection.RECEPTION_TO_LATER_RECEPTION.value,
            hypothesis_id="HYP-01",
            is_influence_asserted=True,
            chronological_order_verified=False,  # VIOLATION
        )
        with self.assertRaises(ReceptionChronologyNotInfluenceFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-04",
                target_passage_id="PAS-REV-19-8",
                relations=[rel],
            )

    # -------------------------------------------------------------------------
    # 5. TRANSLATION MEDIATION FIREWALL
    # -------------------------------------------------------------------------
    def test_05_translation_mediation_firewall(self) -> None:
        """Translation-mediated reception records must specify target language."""
        rec = ReceptionRecordDefinition(
            record_id="REC-ERR-TRANS",
            source_id="SRC-PAT-01",
            witness_passage_reference="Comm. in Matt. Tomus XIV",
            citation_text="Latine verbum...",
            citation_language="LATIN",
            exegetical_method=ExegeticalMethod.ALLEGORICAL_TYPOLOGICAL.value,
            hermeneutical_summary="Latin translation of lost Greek Origenic text.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
            is_translation_mediated=True,
            translation_language=None,  # VIOLATION
        )
        with self.assertRaises(ReceptionTranslationNotOriginalFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-05",
                target_passage_id="PAS-REV-19-8",
                records=[rec],
            )

    # -------------------------------------------------------------------------
    # 6. MODERN COMMENTARY != ANCIENT HISTORICAL WITNESS FIREWALL
    # -------------------------------------------------------------------------
    def test_06_modern_commentary_not_ancient_witness_firewall(self) -> None:
        """Modern commentary cannot claim to be primary ancient witness."""
        src = ReceptionSourceDefinition(
            source_id="SRC-MOD-01",
            canonical_work_title="Modern Commentary on Patristics",
            source_type=ReceptionSourceType.PATRISTIC_COMMENTARY.value,
            source_language="ENGLISH",
            is_modern_commentary=True,
            is_primary_historical_witness=True,  # VIOLATION
        )
        with self.assertRaises(ReceptionModernCommentaryNotWitnessFirewallError):
            self.reception_mgr.register_source(src)

    # -------------------------------------------------------------------------
    # 7. AI-GENERATED SUMMARY != PRIMARY SOURCE FIREWALL
    # -------------------------------------------------------------------------
    def test_07_ai_summary_not_primary_evidence_firewall(self) -> None:
        """AI generated synthesis cannot serve as primary E11/E12 reception evidence."""
        lnk = ReceptionEvidenceLinkDefinition(
            link_id="LNK-ERR-AI",
            record_id="REC-001",
            evidence_id="EV-REC-SEED-01",
            evidence_class=EvidenceClass.E11_EARLY_RECEPTION.value,
            claim_id="CLM-REC-SEED-01",
            stance=EvidenceStance.SUPPORT.value,
            is_ai_generated=True,  # VIOLATION
        )
        with self.assertRaises(ReceptionAISummaryNotPrimarySourceFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-07",
                target_passage_id="PAS-REV-19-8",
                evidence_links=[lnk],
            )

    # -------------------------------------------------------------------------
    # 8. COUNTER-EVIDENCE PRESERVATION FIREWALL
    # -------------------------------------------------------------------------
    def test_08_counter_evidence_preservation_firewall(self) -> None:
        """Counter-evidence and competing hypotheses cannot be suppressed."""
        rel = ReceptionRelationDefinition(
            relation_id="REL-ERR-SUPPRESS",
            source_record_id="REC-001",
            target_record_id="REC-002",
            relation_type=ReceptionRelationType.COMPETING_INTERPRETATION.value,
            temporal_direction=TemporalDirection.RECEPTION_TO_LATER_RECEPTION.value,
            hypothesis_id="HYP-02",
            counter_evidence_preserved=False,  # VIOLATION
        )
        with self.assertRaises(ReceptionCounterEvidencePreservationFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-08",
                target_passage_id="PAS-REV-19-8",
                relations=[rel],
            )

    # -------------------------------------------------------------------------
    # 9. SUCCESSFUL RECEPTION HISTORY PIPELINE & EPISTEMIC RELEVANCE
    # -------------------------------------------------------------------------
    def test_09_successful_reception_run_and_epistemic_relevance(self) -> None:
        """Full execution of reception pipeline preserving provenance, actors, and relevance."""
        # 1. Register Actor
        actor = ReceptionActorDefinition(
            actor_id="ACT-ORIGEN",
            canonical_name="Origen of Alexandria",
            actor_type=ActorType.CHURCH_FATHER.value,
            historical_era=HistoricalEra.PATRISTIC_ANTE_NICENE.value,
            identity_status=ActorIdentityStatus.DEFINITE.value,
            approximate_start_bce_ce=185,
            approximate_end_bce_ce=253,
            date_precision=DatePrecision.EXACT.value,
            tradition_affiliation="Alexandrian School",
            external_identifier="TLG-2042",
            external_identifier_status=ExternalIdentifierStatus.VERIFIED.value,
        )
        self.reception_mgr.register_actor(actor)

        # 2. Register Source
        source = ReceptionSourceDefinition(
            source_id="SRC-ORIGEN-JOANN",
            canonical_work_title="Commentarii in Evangelium Joannis",
            source_type=ReceptionSourceType.PATRISTIC_COMMENTARY.value,
            source_language="GREEK",
            primary_actor_id="ACT-ORIGEN",
            approximate_date_bce_ce=231,
            is_modern_commentary=False,
            is_primary_historical_witness=True,
        )
        self.reception_mgr.register_source(source)

        # 3. Create Record
        record = ReceptionRecordDefinition(
            record_id="REC-ORIGEN-01",
            source_id="SRC-ORIGEN-JOANN",
            actor_id="ACT-ORIGEN",
            target_passage_id="PAS-REV-19-8",
            witness_passage_reference="Comm. Joann. II.2.14",
            citation_text="καὶ ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον λαμπρὸν καθαρόν...",
            citation_language="GREEK",
            exegetical_method=ExegeticalMethod.ALLEGORICAL_TYPOLOGICAL.value,
            hermeneutical_summary="Linen represents purity of virtuous deeds of the saints.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
        )

        # 4. Create Claim with Reception Relevance
        claim = ReceptionClaimDefinition(
            claim_id="CLM-ORIGEN-01",
            record_id="REC-ORIGEN-01",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="Origen witnessed an early 3rd-century Alexandrian reading of Rev 19:8.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.VERY_HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )

        # 5. Create Evidence Link
        link = ReceptionEvidenceLinkDefinition(
            link_id="LNK-ORIGEN-01",
            record_id="REC-ORIGEN-01",
            evidence_id="EV-REC-SEED-01",
            evidence_class=EvidenceClass.E11_EARLY_RECEPTION.value,
            claim_id="CLM-REC-SEED-01",
            stance=EvidenceStance.SUPPORT.value,
        )

        res = self.reception_mgr.execute_analysis_run(
            run_id="RUN-REC-SUCCESS-01",
            target_passage_id="PAS-REV-19-8",
            records=[record],
            claims=[claim],
            evidence_links=[link],
        )

        self.assertEqual(res.run_id, "RUN-REC-SUCCESS-01")
        self.assertEqual(res.records_count, 1)
        self.assertEqual(res.claims_count, 1)
        self.assertEqual(res.links_count, 1)

        # Verify query retrieval
        records = self.reception_mgr.get_records_for_passage("PAS-REV-19-8")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["actor_id"], "ACT-ORIGEN")

        claims = self.reception_mgr.get_claims_for_record("REC-ORIGEN-01")
        self.assertEqual(len(claims), 1)
        self.assertEqual(claims[0]["claim_relevance"], "RECEPTION_HISTORY_PRIMARY")

    # -------------------------------------------------------------------------
    # 10. REANALYSIS & VERSION SUPERSESSION
    # -------------------------------------------------------------------------
    def test_10_version_lineage_and_supersession(self) -> None:
        """Re-analyzing same passage supersedes prior run cleanly."""
        res1 = self.reception_mgr.execute_analysis_run(
            run_id="RUN-REC-V1",
            target_passage_id="PAS-REV-19-8",
            analyzer_version="1.0.0",
        )
        self.assertEqual(res1.run_id, "RUN-REC-V1")

        # Run 2 on same passage
        res2 = self.reception_mgr.execute_analysis_run(
            run_id="RUN-REC-V2",
            target_passage_id="PAS-REV-19-8",
            analyzer_version="1.0.1",
        )
        self.assertEqual(res2.run_id, "RUN-REC-V2")

        r1 = self.reception_mgr.get_run("RUN-REC-V1")
        r2 = self.reception_mgr.get_run("RUN-REC-V2")
        self.assertEqual(r1["status"], "SUPERSEDED")
        self.assertEqual(r2["status"], "COMPLETED")

    # -------------------------------------------------------------------------
    # 11. IMMUTABILITY ENFORCED BY TRIGGERS
    # -------------------------------------------------------------------------
    def test_11_immutability_enforced_by_triggers(self) -> None:
        """Direct SQL UPDATE or DELETE on reception tables is blocked by triggers."""
        self.reception_mgr.execute_analysis_run(
            run_id="RUN-REC-IMMUT",
            target_passage_id="PAS-REV-19-8",
        )

        with self.engine.transaction() as conn:
            # Cannot mutate analyzer_id
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute("UPDATE reception_runs SET analyzer_id = 'hacked' WHERE run_id = 'RUN-REC-IMMUT';")
            self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

            # Cannot delete run
            with self.assertRaises(sqlite3.IntegrityError) as ctx:
                conn.execute("DELETE FROM reception_runs WHERE run_id = 'RUN-REC-IMMUT';")
            self.assertIn("IMMUTABILITY_VIOLATION", str(ctx.exception))

    # -------------------------------------------------------------------------
    # 12. CONCURRENCY SAFETY UNDER MULTIPLE THREADS
    # -------------------------------------------------------------------------
    def test_12_concurrency_safety(self) -> None:
        """Concurrent reception analysis runs complete cleanly without lock contention."""
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-REV-19-9', 'PER-REV-19-07-09', 'REV', 19, 9, 2);
                """
            )
            conn.execute(
                """
                INSERT INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-REV-19-10', 'PER-REV-19-07-09', 'REV', 19, 10, 3);
                """
            )

        def worker(passage: str, idx: int) -> str:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            ecm = EvidenceClaimManager(eng)
            rm = ReceptionHistoryManager(eng, vm, pt, ecm)
            res = rm.execute_analysis_run(
                run_id=f"RUN-CONC-REC-{idx}",
                target_passage_id=passage,
                analyzer_id="analyzer_concurrent_rec",
                analyzer_version="1.0",
            )
            eng.close()
            return res.run_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(worker, "PAS-REV-19-9", 1)
            fut2 = executor.submit(worker, "PAS-REV-19-10", 2)
            id1 = fut1.result()
            id2 = fut2.result()

        self.assertEqual(id1, "RUN-CONC-REC-1")
        self.assertEqual(id2, "RUN-CONC-REC-2")

    # -------------------------------------------------------------------------
    # 15. EARLY RECEPTION != APOSTOLIC INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_15_early_reception_not_apostolic_intent(self) -> None:
        """Patristic or subapostolic reception cannot claim to be apostolic intent."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-APOSTOLIC",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM.value,
            claim_statement="Clement of Rome represents the apostolic meaning directly.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_authorial_intent_equated=True,
        )
        with self.assertRaises(ReceptionEarlyNotApostolicFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-15",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 16. RABBINIC RECEPTION != SECOND TEMPLE INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_16_rabbinic_reception_not_second_temple(self) -> None:
        """Rabbinic/Talmudic reception cannot claim Second Temple authorial intent."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-RABBINIC",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM.value,
            claim_statement="The Amoraic Gemara records the original Second Temple authorial view.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_authorial_intent_equated=True,
        )
        with self.assertRaises(ReceptionRabbinicNotSecondTempleFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-16",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 17. MEDIEVAL RECEPTION != ANCIENT BIBLICAL INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_17_medieval_reception_not_ancient_biblical(self) -> None:
        """Medieval interpretation cannot be equated to ancient biblical intent."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-MEDIEVAL",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM.value,
            claim_statement="Thomas Aquinas Glossa ordinaria is the biblical intent.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_authorial_intent_equated=True,
        )
        with self.assertRaises(ReceptionMedievalNotBiblicalFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-17",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 18. SCHOLARLY CONSENSUS != TEXTUAL EVIDENCE FIREWALL
    # -------------------------------------------------------------------------
    def test_18_scholarly_consensus_not_textual_evidence(self) -> None:
        """Modern academic consensus cannot masquerade as T1 linguistic fact."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-SCHOLAR",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT.value,
            claim_statement="The scholarly consensus establishes the grammatical sense.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionScholarlyNotTextualFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-18",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 19. DENOMINATIONAL DOCTRINE != ANCIENT AUTHORIAL INTENT FIREWALL
    # -------------------------------------------------------------------------
    def test_19_denominational_doctrine_not_authorial_intent(self) -> None:
        """Denominational confession cannot be equated to ancient authorial intent."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-DENOM",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM.value,
            claim_statement="The denominational catechism defines the original intent.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.THEOLOGICAL_TRADITION_RELEVANT.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_authorial_intent_equated=True,
        )
        with self.assertRaises(ReceptionDenominationalNotAuthorialFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-19",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 20. CITATION != INTERPRETATION FIREWALL
    # -------------------------------------------------------------------------
    def test_20_citation_not_interpretation_firewall(self) -> None:
        """Quoting a passage does not automatically establish interpretive agreement."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-CITE-INTERP",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="The author citation equals interpretation without qualification.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionCitationNotInterpretationFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-20",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 21. ALLUSION != DIRECT QUOTATION FIREWALL
    # -------------------------------------------------------------------------
    def test_21_allusion_not_quotation_firewall(self) -> None:
        """Allusion cannot be asserted as direct quotation without textual quotation formula."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-ALLUS-QUOTE",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="The author allusion is quotation verbatim.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionAllusionNotQuotationFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-21",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 22. LEXICAL SIMILARITY != RECEPTION FIREWALL
    # -------------------------------------------------------------------------
    def test_22_lexical_similarity_not_reception_firewall(self) -> None:
        """Lexical similarity alone does not establish reception history connection."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-LEX-REC",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="The shared lexical parallel alone establishes reception dependence.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionLexicalNotReceptionFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-22",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 23. THEMATIC PARALLEL != RECEPTION FIREWALL
    # -------------------------------------------------------------------------
    def test_23_thematic_parallel_not_reception_firewall(self) -> None:
        """Thematic parallel alone does not establish reception history connection."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-THEME-REC",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="The thematic parallel alone establishes reception lineage.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionThematicNotReceptionFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-23",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 24. RECEPTION SOURCE != AUTHORIAL SOURCE FIREWALL
    # -------------------------------------------------------------------------
    def test_24_reception_source_not_authorial_source(self) -> None:
        """A reception commentary cannot be asserted as authorial source of the ancient text."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-SRC-AUTH",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="The reception source is authorial of Revelation.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionSourceNotAuthorialSourceFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-24",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 25. RECEPTION HISTORY != CANONICAL AUTHORITY FIREWALL
    # -------------------------------------------------------------------------
    def test_25_reception_not_canonical_authority(self) -> None:
        """Reception history cannot be endowed with canonical authority."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-CANON-AUTH",
            record_id="REC-001",
            claim_type=ReceptionClaimType.DOCTRINAL_DEVELOPMENT.value,
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM.value,
            claim_statement="This reading holds canonical authority over the text.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.THEOLOGICAL_TRADITION_RELEVANT.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionNotCanonicalAuthorityFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-25",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 26. MAJORITY INTERPRETATION != VERIFIED FACT FIREWALL
    # -------------------------------------------------------------------------
    def test_26_majority_interpretation_not_verified_fact(self) -> None:
        """Majority reception cannot be asserted as verified fact."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-MAJ-FACT",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT.value,
            claim_statement="The majority of patristic writers verify the textual fact.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionMajorityNotFactFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-26",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 27. EXTERNAL IDENTIFIER != VERIFIED IDENTITY FIREWALL
    # -------------------------------------------------------------------------
    def test_27_external_identifier_not_verified_identity(self) -> None:
        """An unverified external identifier cannot be marked VERIFIED."""
        actor = ReceptionActorDefinition(
            actor_id="ACT-ERR-ID",
            canonical_name="Anonymous Commentator",
            actor_type=ActorType.ANONYMOUS_TRADITION.value,
            historical_era=HistoricalEra.UNKNOWN.value,
            external_identifier="LOCAL",
            external_identifier_status=ExternalIdentifierStatus.VERIFIED.value,  # VIOLATION
        )
        with self.assertRaises(ReceptionUnverifiedIdentifierFirewallError):
            self.reception_mgr.register_actor(actor)

    # -------------------------------------------------------------------------
    # 28. CONFIDENCE SCORE != EVIDENCE UPGRADE FIREWALL
    # -------------------------------------------------------------------------
    def test_28_confidence_score_not_evidence_upgrade(self) -> None:
        """High confidence score cannot upgrade reception into absolute theological truth."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-CONF-UPGRADE",
            record_id="REC-001",
            claim_type=ReceptionClaimType.DOCTRINAL_DEVELOPMENT.value,
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM.value,
            claim_statement="High confidence dogma of the linen.",
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            claim_relevance=ClaimRelevance.THEOLOGICAL_TRADITION_RELEVANT.value,
            confidence_level=ConfidenceLevel.CERTAIN.value,
            ledger_claim_id="CLM-REC-SEED-01",
            is_theological_truth_equated=True,  # VIOLATION
        )
        with self.assertRaises(ReceptionConfidenceNotUpgradeFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-28",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 29. TEMPORAL DIRECTION PRESERVATION
    # -------------------------------------------------------------------------
    def test_29_temporal_direction_preservation(self) -> None:
        """Temporal direction must be explicitly specified and preserved."""
        clm = ReceptionClaimDefinition(
            claim_id="CLM-ERR-NO-TEMP",
            record_id="REC-001",
            claim_type=ReceptionClaimType.HERMENEUTICAL_READING.value,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM.value,
            claim_statement="Claim lacking temporal direction.",
            temporal_direction="",  # VIOLATION
            claim_relevance=ClaimRelevance.RECEPTION_HISTORY_PRIMARY.value,
            confidence_level=ConfidenceLevel.HIGH.value,
            ledger_claim_id="CLM-REC-SEED-01",
        )
        with self.assertRaises(ReceptionTemporalDirectionFirewallError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-TEST-29",
                target_passage_id="PAS-REV-19-8",
                claims=[clm],
            )

    # -------------------------------------------------------------------------
    # 30. ACTOR UNCERTAINTY AND DATING RANGES
    # -------------------------------------------------------------------------
    def test_30_actor_uncertainty_and_dating_ranges(self) -> None:
        """Actor identity status (DISPUTED, ANONYMOUS) and broad dating ranges persist cleanly."""
        actor = ReceptionActorDefinition(
            actor_id="ACT-DISPUTED-01",
            canonical_name="Pseudo-Dionysius the Areopagite",
            actor_type=ActorType.INDIVIDUAL_AUTHOR.value,
            historical_era=HistoricalEra.PATRISTIC_POST_NICENE.value,
            identity_status=ActorIdentityStatus.DISPUTED.value,
            approximate_start_bce_ce=485,
            approximate_end_bce_ce=528,
            date_precision=DatePrecision.CENTURY.value,
            tradition_affiliation="Neoplatonic Christian Mysticism",
            external_identifier="TLG-4099",
            external_identifier_status=ExternalIdentifierStatus.VERIFIED.value,
        )
        act_id = self.reception_mgr.register_actor(actor)
        self.assertEqual(act_id, "ACT-DISPUTED-01")

        with self.engine.transaction() as conn:
            row = conn.execute("SELECT * FROM reception_actors WHERE actor_id = 'ACT-DISPUTED-01'").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["identity_status"], "DISPUTED")
            self.assertEqual(row["date_precision"], "CENTURY")

    # -------------------------------------------------------------------------
    # 31. COMPETING RECEPTION INTERPRETATIONS PRESERVED INDEPENDENTLY
    # -------------------------------------------------------------------------
    def test_31_competing_reception_interpretations_preserved(self) -> None:
        """Diverging reception traditions (Alexandrian allegorical vs Antiochene literal) preserved as competing."""
        # 1. Register Source for Theodore of Mopsuestia
        src_theo = ReceptionSourceDefinition(
            source_id="SRC-THEO-MOP",
            canonical_work_title="In Epistolas Pauli Commentarii",
            source_type=ReceptionSourceType.PATRISTIC_COMMENTARY.value,
            source_language="GREEK",
            approximate_date_bce_ce=410,
            is_primary_historical_witness=True,
        )
        self.reception_mgr.register_source(src_theo)

        rec_allegorical = ReceptionRecordDefinition(
            record_id="REC-COMP-ALLEGORICAL",
            source_id="SRC-THEO-MOP",
            witness_passage_reference="Comm. in Paul. IV.1",
            citation_text="Allegorical reading...",
            citation_language="GREEK",
            exegetical_method=ExegeticalMethod.ALLEGORICAL_TYPOLOGICAL.value,
            hermeneutical_summary="Allegorical interpretation of fine linen as divine virtues.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
        )

        rec_literal = ReceptionRecordDefinition(
            record_id="REC-COMP-LITERAL",
            source_id="SRC-THEO-MOP",
            witness_passage_reference="Comm. in Paul. IV.2",
            citation_text="Literal reading...",
            citation_language="GREEK",
            exegetical_method=ExegeticalMethod.LITERAL_HISTORICAL.value,
            hermeneutical_summary="Literal-historical interpretation of physical linen in bride garment.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
        )

        rel = ReceptionRelationDefinition(
            relation_id="REL-COMP-01",
            source_record_id="REC-COMP-ALLEGORICAL",
            target_record_id="REC-COMP-LITERAL",
            relation_type=ReceptionRelationType.COMPETING_INTERPRETATION.value,
            temporal_direction=TemporalDirection.RECEPTION_TO_INTERPRETATION.value,
            hypothesis_id="HYP-ALEXANDRIA-VS-ANTIOCH",
            counter_evidence_preserved=True,
        )

        res = self.reception_mgr.execute_analysis_run(
            run_id="RUN-REC-COMPETING",
            target_passage_id="PAS-REV-19-8",
            records=[rec_allegorical, rec_literal],
            relations=[rel],
        )

        self.assertEqual(res.records_count, 2)
        self.assertEqual(res.relations_count, 1)

        rels = self.reception_mgr.get_relations_for_record("REC-COMP-ALLEGORICAL")
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0]["relation_type"], "COMPETING_INTERPRETATION")

    # -------------------------------------------------------------------------
    # 32. MIGRATIONS 001-016 CHECKSUMS UNCHANGED & 017 VERIFIED
    # -------------------------------------------------------------------------
    def test_32_migration_checksums_001_to_016_unchanged(self) -> None:
        """Migrations 001-016 must strictly match golden baseline checksums."""
        migrations_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for filename, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            file_path = migrations_dir / filename
            self.assertTrue(file_path.exists(), f"Missing migration file: {filename}")
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Migration altered: {filename}! Expected {expected_hash}, got {actual_hash}",
            )

        # Migration 017 exists and is readable with locked checksum
        m017 = migrations_dir / "017_reception_history.sql"
        self.assertTrue(m017.exists())
        actual_017_hash = hashlib.sha256(m017.read_bytes()).hexdigest().lower()
        self.assertEqual(
            actual_017_hash,
            EXPECTED_017_CHECKSUM,
            "Migration 017 checksum altered!",
        )

    # -------------------------------------------------------------------------
    # 33. LEGACY DB SHA-256 UNALTERED
    # -------------------------------------------------------------------------
    def test_33_legacy_db_sha256_unaltered(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain unaltered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(actual_sha, LEGACY_DB_SHA256, "Legacy database altered!")

    # -------------------------------------------------------------------------
    # 34. ROLLBACK ON FAILURE LEAVES ZERO ORPHANED ROWS
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # 34. ROLLBACK ON FAILURE LEAVES ZERO ORPHANED ROWS
    # -------------------------------------------------------------------------
    def test_34_rollback_on_failure_leaves_no_orphans(self) -> None:
        """When analysis run encounters mid-transaction error, transaction rolls back cleanly without orphans."""
        with self.engine.connect() as conn:
            initial_runs = conn.execute("SELECT count(*) FROM reception_runs").fetchone()[0]
            initial_records = conn.execute("SELECT count(*) FROM reception_records").fetchone()[0]
            initial_claims = conn.execute("SELECT count(*) FROM reception_claims").fetchone()[0]
            initial_versions = conn.execute("SELECT count(*) FROM object_versions WHERE object_type = 'RECEPTION_ANALYSIS'").fetchone()[0]

        rec1 = ReceptionRecordDefinition(
            record_id="REC-ROLLBACK-DUP",
            source_id="SRC-PAT-01",
            witness_passage_reference="Comm. in Joh. II.1",
            citation_text="KAI TO BYSSINON...",
            citation_language="GREEK",
            exegetical_method=ExegeticalMethod.ALLEGORICAL_TYPOLOGICAL.value,
            hermeneutical_summary="Allegorical interpretation.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
            target_passage_id="PAS-REV-19-8",
        )
        rec2 = ReceptionRecordDefinition(
            record_id="REC-ROLLBACK-DUP",  # Mid-transaction duplicate PK triggers rollback!
            source_id="SRC-PAT-01",
            witness_passage_reference="Comm. in Joh. II.2",
            citation_text="KAI TO BYSSINON 2...",
            citation_language="GREEK",
            exegetical_method=ExegeticalMethod.ALLEGORICAL_TYPOLOGICAL.value,
            hermeneutical_summary="Allegorical interpretation 2.",
            reception_era=ReceptionEra.PATRISTIC.value,
            evidence_id="EV-REC-SEED-01",
            target_passage_id="PAS-REV-19-8",
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-ROLLBACK-FAIL",
                target_passage_id="PAS-REV-19-8",
                records=[rec1, rec2],
            )

        with self.engine.connect() as conn:
            final_runs = conn.execute("SELECT count(*) FROM reception_runs").fetchone()[0]
            final_records = conn.execute("SELECT count(*) FROM reception_records").fetchone()[0]
            final_claims = conn.execute("SELECT count(*) FROM reception_claims").fetchone()[0]
            final_versions = conn.execute("SELECT count(*) FROM object_versions WHERE object_type = 'RECEPTION_ANALYSIS'").fetchone()[0]

        self.assertEqual(final_runs, initial_runs, "Orphaned reception_run row remained after rollback!")
        self.assertEqual(final_records, initial_records, "Orphaned reception_record row remained after rollback!")
        self.assertEqual(final_claims, initial_claims, "Orphaned reception_claim row remained after rollback!")
        self.assertEqual(final_versions, initial_versions, "Orphaned version row remained after rollback!")

    # -------------------------------------------------------------------------
    # 35. ENTITY GETTERS AND NOT-FOUND ERRORS
    # -------------------------------------------------------------------------
    def test_35_entity_getters_and_not_found(self) -> None:
        """Getter methods return correct dictionaries or raise specific domain NotFound errors."""
        actor_def = ReceptionActorDefinition(
            actor_id="ACT-ORIGEN-TEST",
            canonical_name="Origen of Alexandria",
            actor_type=ActorType.CHURCH_FATHER.value,
            identity_status=ActorIdentityStatus.DEFINITE.value,
            historical_era=HistoricalEra.PATRISTIC_ANTE_NICENE.value,
        )
        self.reception_mgr.register_actor(actor_def)

        source_def = ReceptionSourceDefinition(
            source_id="SRC-PAT-01-TEST",
            canonical_work_title="Commentarii in Evangelium Joannis",
            source_type=ReceptionSourceType.PATRISTIC_COMMENTARY.value,
            source_language="GREEK",
            primary_actor_id="ACT-ORIGEN-TEST",
            dating_period="3rd century CE",
            approximate_date_bce_ce=230,
        )
        self.reception_mgr.register_source(source_def)

        actor = self.reception_mgr.get_actor("ACT-ORIGEN-TEST")
        self.assertEqual(actor["canonical_name"], "Origen of Alexandria")

        source = self.reception_mgr.get_source("SRC-PAT-01-TEST")
        self.assertEqual(source["canonical_work_title"], "Commentarii in Evangelium Joannis")

        with self.assertRaises(ReceptionActorNotFoundError):
            self.reception_mgr.get_actor("ACT-NONEXISTENT")

        with self.assertRaises(ReceptionSourceNotFoundError):
            self.reception_mgr.get_source("SRC-NONEXISTENT")

        with self.assertRaises(ReceptionRecordNotFoundError):
            self.reception_mgr.get_record("REC-NONEXISTENT")

        with self.assertRaises(ReceptionClaimNotFoundError):
            self.reception_mgr.get_claim("CLM-NONEXISTENT")

        with self.assertRaises(ReceptionRelationNotFoundError):
            self.reception_mgr.get_relation("REL-NONEXISTENT")

    # -------------------------------------------------------------------------
    # 36. SELF-RELATION VALIDATION ERROR
    # -------------------------------------------------------------------------
    def test_36_self_relation_validation_error(self) -> None:
        """Connecting a reception record to itself raises ReceptionValidationError."""
        rel = ReceptionRelationDefinition(
            relation_id="REL-SELF-ERR",
            source_record_id="REC-001",
            target_record_id="REC-001",
            relation_type=ReceptionRelationType.DIRECT_DEPENDENCE.value,
            temporal_direction=TemporalDirection.TEXT_TO_RECEPTION.value,
            hypothesis_id="HYP-SELF",
        )
        with self.assertRaises(ReceptionValidationError):
            self.reception_mgr.execute_analysis_run(
                run_id="RUN-SELF-ERR",
                target_passage_id="PAS-REV-19-8",
                relations=[rel],
            )


if __name__ == "__main__":
    unittest.main()


