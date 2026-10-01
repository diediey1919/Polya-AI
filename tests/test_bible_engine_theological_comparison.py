"""
Unit and Adversarial Test Suite for Theological Comparison & Ilzam al-Khasm Engine (Task 3.8).
Specification: Architecture v2.0 — FROZEN.

Coverage:
  1. Framework registration & validation
  2. Dogmatic proposition registration (T4 validation)
  3. Theology Firewall: T4 cannot modify or pose as T0–T3 evidence
  4. Theology Firewall: T4 cannot serve as target evidence tier in audits
  5. Anti-Circularity: Proposition cannot cite itself as evidence
  6. Anti-Circularity: Circular dependency chains in Ilzam rejected
  7. Ilzam al-Khasm: Internal premise contradiction detected
  8. Ilzam al-Khasm: Unsupported inference detected
  9. Ilzam al-Khasm: Invalid extrapolation detected
  10. Ilzam al-Khasm: Contradiction with acknowledged text detected
  11. Ilzam al-Khasm: Unresolved ambiguity preserved without forced consensus
  12. Anti-Anachronism: Post-biblical terminology detected and flagged
  13. Anti-Anachronism: Unsupported retrojection into ancient text rejected
  14. Identity Firewall: Metaphorical agency not equated with ontological identity
  15. Identity Firewall: Unsupported ontological identity assertion rejected
  16. Confidence: Weakest-critical-dependency capping enforced
  17. Confidence: Inflation exceeding constituent evidence rejected
  18. Symmetrical Framework Evaluation: Independent multi-framework analysis
  19. Symmetrical Framework Evaluation: Rejection of popularity / majority vote
  20. Symmetrical Framework Evaluation: Preservation of competing frameworks
  21. Audit Verdict Derivation: SUPPORTED when all premises textually grounded
  22. Audit Verdict Derivation: PARTIALLY_SUPPORTED with mixed evidence
  23. Audit Verdict Derivation: IN_TENSION with exegetical tension
  24. Audit Verdict Derivation: INSUFFICIENTLY_WARRANTED with absence of warrant
  25. Audit Verdict Derivation: CONTRADICTED on fatal critique or textual clash
  26. Immutability: Framework UPDATE and DELETE rejected by SQLite triggers
  27. Immutability: Proposition UPDATE and DELETE rejected by SQLite triggers
  28. Immutability: Run UPDATE and DELETE rejected by SQLite triggers
  29. Immutability: Audit and Critique UPDATE and DELETE rejected by SQLite triggers
  30. Lifecycle & Supersession: Valid run status transition to SUPERSEDED
  31. Transaction Atomicity: Mid-run failure rolls back all partial records
  32. Concurrency Safety: Multi-threaded writers execute safely without corruption
  33. Cryptographic Provenance: Real provenance IDs and deterministic SHA-256 hashes
  34. Migration 021 Checksum Locked
  35. Migrations 001–020 strictly unchanged
  36. Legacy database at /home/ubuntu/.polya/polya_index.db strictly untouched
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

from bible_engine.database import DatabaseConfig, DatabaseEngine
from bible_engine.errors import (
    AnachronisticRetrojectionError,
    AsymmetricalFrameworkEvaluationError,
    CircularProofStructureError,
    ComparisonRunNotFoundError,
    DogmaticEvidenceContaminationError,
    FrameworkNotFoundError,
    IdentityCollapseError,
    PropositionNotFoundError,
    TheologicalComparisonSubsystemError,
    TheologicalConfidenceInflationError,
    TheologicalValidationError,
    TheologyFirewallError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.theological_comparison import (
    AlignmentStatus,
    AuditVerdict,
    ComparisonRunStatus,
    CritiqueSeverity,
    CritiqueType,
    DogmaticPropositionDefinition,
    DogmaticPropositionRecord,
    FrameworkTradition,
    HistoricalEra,
    IlzamCritiqueInput,
    IlzamCritiqueRecord,
    PropositionAuditInput,
    PropositionEvidenceAuditRecord,
    TheologicalComparisonConfig,
    TheologicalComparisonManager,
    TheologicalComparisonRunResult,
    TheologicalFrameworkDefinition,
    TheologicalFrameworkRecord,
    compute_canonical_hash,
)
from bible_engine.versioning import ChangeReason, VersionManager

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
    "017_reception_history.sql": "76bfc99691e5d05da1fd662f4371187337a5aca943d8b57481b527125b965e13",
    "018_evidence_adjudication.sql": "50aa9dbeb9fa27e25b0fa4299ac4d01aeaf44bc1907115f9a03fd0eece13e025",
    "019_evidence_knowledge_graph.sql": "04a6dcc5429507fdda9220e95eef45b99d297c65fa815702612d523ae225ca95",
    "020_hierarchical_synthesis.sql": "3f80d67d9567ea0775c593f663458d4a8892dd719a75d01d3bd39ac0c9fe1216",
}

EXPECTED_021_CHECKSUM = "a4ede76a0caed8248117ba4fb18a41cd327f4932fdbe816e261a7b87ce753ad9"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestTheologicalComparisonEngine(unittest.TestCase):
    """Unit and Adversarial Test Suite for Task 3.8 Theological Comparison & Ilzam al-Khasm Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_theological_comparison.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.theo_mgr = TheologicalComparisonManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('JHN', 'TEST_NT', 43, 'Yohanes', 'John', 'GREEK', 21);")
            conn.execute("INSERT OR IGNORE INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) VALUES ('PERIC_JHN_1_1', 'JHN', 'Yohanes 1:1-18', 1, 1, 1, 18, 'GOSPEL_PROLOGUE', 'NA28_SECTION', 'HIGH', 'REGISTERED', '1.0.0', '2026-09-30T00:00:00Z');")

        # Register baseline test frameworks
        self.fw_nicene = self.theo_mgr.register_framework(
            TheologicalFrameworkDefinition(
                framework_id="FW-NICENE",
                framework_name="Nicene Pro-Nicene Orthodoxy",
                tradition_family=FrameworkTradition.CHRISTIAN_PATRISTIC,
                historical_period="4th Century (325–381 CE)",
                description="Nicene Trinitarian framework asserting consubstantiality (homoousios).",
                canonical_source_corpus="Creed of Nicaea 325, Creed of Constantinople 381",
            )
        )
        self.fw_arian = self.theo_mgr.register_framework(
            TheologicalFrameworkDefinition(
                framework_id="FW-ARIAN",
                framework_name="Subordinationist Arianism",
                tradition_family=FrameworkTradition.CHRISTIAN_HETERODOX,
                historical_period="4th Century (318–381 CE)",
                description="Subordinationist framework asserting temporal origination of the Logos.",
                canonical_source_corpus="Thalia of Arius, Letter to Eusebius of Nicomedia",
            )
        )
        self.fw_socinian = self.theo_mgr.register_framework(
            TheologicalFrameworkDefinition(
                framework_id="FW-SOCINIAN",
                framework_name="Biblical Unitarianism / Socinianism",
                tradition_family=FrameworkTradition.ENLIGHTENMENT_SOCINIAN,
                historical_period="16th–17th Century",
                description="Strict Unitarian framework holding Jesus to be a prophet elevated by God.",
                canonical_source_corpus="Racovian Catechism (1605)",
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. FRAMEWORK & PROPOSITION REGISTRATION
    # -------------------------------------------------------------------------

    def test_01_framework_registration_and_retrieval(self) -> None:
        """Register framework and verify persistence and retrieval."""
        fw = self.theo_mgr.get_framework("FW-NICENE")
        self.assertIsNotNone(fw)
        self.assertEqual(fw.framework_id, "FW-NICENE")
        self.assertEqual(fw.tradition_family, "CHRISTIAN_PATRISTIC")
        self.assertTrue(fw.provenance_id.startswith("PRV-"))

    def test_02_dogmatic_proposition_registration(self) -> None:
        """Register dogmatic proposition with T4 claim tier."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-NICENE-01",
                framework_id="FW-NICENE",
                formulation_title="Consubstantiality of the Son",
                proposition_text="The Son is homoousios (consubstantial) with the Father.",
                formal_creedal_source="Symbolum Nicaenum 325",
                historical_era=HistoricalEra.NICENE_ERA,
                contains_post_biblical_terminology=True,
                post_biblical_terms=["homoousios"],
                claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            )
        )
        self.assertIsNotNone(prop)
        self.assertEqual(prop.claim_tier, "T4_THEOLOGICAL_CLAIM")
        self.assertTrue(prop.contains_post_biblical_terminology)
        self.assertIn("homoousios", prop.post_biblical_terms)

    # -------------------------------------------------------------------------
    # 2. HARD THEOLOGY FIREWALL (T4 cannot modify or pose as T0–T3)
    # -------------------------------------------------------------------------

    def test_03_theology_firewall_rejects_non_t4_proposition(self) -> None:
        """Hard Theology Firewall: Dogmatic proposition cannot claim to be T0-T3 evidence."""
        with self.assertRaises(DogmaticEvidenceContaminationError):
            self.theo_mgr.register_proposition(
                DogmaticPropositionDefinition(
                    proposition_id="PROP-ILLICIT-01",
                    framework_id="FW-NICENE",
                    formulation_title="Illicit Tier Claim",
                    proposition_text="Dogma posing as raw linguistic fact.",
                    formal_creedal_source="Council",
                    historical_era=HistoricalEra.NICENE_ERA,
                    claim_tier=ClaimTier.T1_LINGUISTIC_FACT,  # VIOLATION!
                )
            )

    def test_04_theology_firewall_rejects_t4_in_audit_target_tier(self) -> None:
        """Hard Theology Firewall: Audit target evidence tier cannot be T4 dogma."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-TEST-AUDIT-01",
                framework_id="FW-NICENE",
                formulation_title="Test Title",
                proposition_text="Test dogmatic statement.",
                formal_creedal_source="Creed",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit_illicit = PropositionAuditInput(
            audit_id="AUDIT-ILLICIT-01",
            deconstructed_premise_text="Premise trying to cite another dogma as evidence",
            target_evidence_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,  # VIOLATION!
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Dogma citing dogma as proof.",
        )
        with self.assertRaises(DogmaticEvidenceContaminationError):
            self.theo_mgr.execute_comparison_run(
                proposition_id=prop.proposition_id,
                audits=[audit_illicit],
            )

    # -------------------------------------------------------------------------
    # 3. ANTI-CIRCULARITY (No self-proving dogma)
    # -------------------------------------------------------------------------

    def test_05_circularity_rejected_when_proposition_cites_itself(self) -> None:
        """Anti-Circularity: Proposition cannot cite itself as evidence in audit."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-CIRCULAR-01",
                framework_id="FW-NICENE",
                formulation_title="Circular Prop",
                proposition_text="Self-proving dogma.",
                formal_creedal_source="Creed",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        circular_audit = PropositionAuditInput(
            audit_id="AUDIT-CIRC-01",
            deconstructed_premise_text="Premise citing the same proposition",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_claim_id="PROP-CIRCULAR-01",  # Self-citation!
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.8,
            audit_confidence=0.8,
            audit_finding_detail="Self-referential evidence cycle.",
        )
        with self.assertRaises(CircularProofStructureError):
            self.theo_mgr.execute_comparison_run(
                proposition_id="PROP-CIRCULAR-01",
                audits=[circular_audit],
            )

    def test_06_circularity_in_critique_dependency_chain_rejected(self) -> None:
        """Anti-Circularity: Circular dependency chain in Ilzam critique rejected if not marked as circular."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-CIRCULAR-CHAIN-01",
                framework_id="FW-NICENE",
                formulation_title="Circular Chain",
                proposition_text="Chain depending on itself.",
                formal_creedal_source="Creed",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        valid_audit = PropositionAuditInput(
            audit_id="AUDIT-OK-01",
            deconstructed_premise_text="Premise 1",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.85,
            audit_confidence=0.85,
            audit_finding_detail="Textual observation.",
        )
        circular_critique = IlzamCritiqueInput(
            critique_id="CRIT-CIRC-01",
            critique_type=CritiqueType.INTERNAL_PREMISE_CONTRADICTION,
            acknowledged_premise_a="Premise A",
            dependency_chain=["CLAIM-01", "PROP-CIRCULAR-CHAIN-01", "CLAIM-02"],  # Contains self!
            demonstration_text="Dependency cycle.",
            critique_severity=CritiqueSeverity.FATAL_INTERNAL_CONTRADICTION,
            is_circularity_rejected=False,  # Unacknowledged circularity!
        )
        with self.assertRaises(CircularProofStructureError):
            self.theo_mgr.execute_comparison_run(
                proposition_id="PROP-CIRCULAR-CHAIN-01",
                audits=[valid_audit],
                critiques=[circular_critique],
            )

    # -------------------------------------------------------------------------
    # 4. ILZAM AL-KHASM (Internal Critique Engine)
    # -------------------------------------------------------------------------

    def test_07_ilzam_internal_premise_contradiction_detected(self) -> None:
        """Ilzam al-Khasm: Internal contradiction within opponent's own premises detected."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-ILZAM-01",
                framework_id="FW-NICENE",
                formulation_title="Athanasian Premise Clash",
                proposition_text="The Son is co-equal and co-eternal, yet sent and subordinate in operation.",
                formal_creedal_source="Creed",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-ILZAM-01",
            deconstructed_premise_text="Yohanes 14:28 'The Father is greater than I'",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_14_28",
            alignment_status=AlignmentStatus.EXEGETICAL_TENSION,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Comparative adjective meizon denotes relational inequality.",
        )
        critique = IlzamCritiqueInput(
            critique_id="CRIT-ILZAM-01",
            critique_type=CritiqueType.INTERNAL_PREMISE_CONTRADICTION,
            acknowledged_premise_a="Premise: Son is co-equal in power and being.",
            acknowledged_premise_b="Premise: Father is ontological source and greater.",
            dependency_chain=["CLAIM-EQUAL", "CLAIM-GREATER"],
            demonstration_text="Internal reduction: Claiming absolute equality while asserting ontological origin yields contradiction.",
            critique_severity=CritiqueSeverity.FATAL_INTERNAL_CONTRADICTION,
        )
        res = self.theo_mgr.execute_comparison_run(
            proposition_id="PROP-ILZAM-01",
            audits=[audit],
            critiques=[critique],
        )
        self.assertEqual(res.audit_verdict, AuditVerdict.CONTRADICTED)
        self.assertEqual(res.critiques_count, 1)

    def test_08_ilzam_unsupported_inference_detected(self) -> None:
        """Ilzam al-Khasm: Unsupported inference detected and classified."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-ILZAM-02",
                framework_id="FW-NICENE",
                formulation_title="Inference from Agency to Essence",
                proposition_text="Jesus creating all things implies Jesus is uncreated YHWH.",
                formal_creedal_source="Theological treatise",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-ILZAM-02",
            deconstructed_premise_text="Colossians 1:16 'in him all things were created'",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_passage_or_pericope_id="PERIC_COL_1_15",
            alignment_status=AlignmentStatus.UNWARRANTED_EXTRAPOLATION,
            evidence_confidence=0.8,
            audit_confidence=0.75,
            audit_finding_detail="Preposition 'dia' denotes intermediate agency, not ultimate source.",
        )
        critique = IlzamCritiqueInput(
            critique_id="CRIT-ILZAM-02",
            critique_type=CritiqueType.UNSUPPORTED_INFERENCE,
            acknowledged_premise_a="Textual premise: All things created through (dia) the Son.",
            demonstration_text="Illegitimate leap: Intermediate agency does not entail identity as ultimate uncreated source.",
            dependency_chain=["COL-1-16-AGENCY"],
            critique_severity=CritiqueSeverity.UNWARRANTED_LEAP,
        )
        res = self.theo_mgr.execute_comparison_run(
            proposition_id="PROP-ILZAM-02",
            audits=[audit],
            critiques=[critique],
        )
        self.assertEqual(res.audit_verdict, AuditVerdict.IN_TENSION)

    def test_09_ilzam_unresolved_ambiguity_preserved(self) -> None:
        """Ilzam al-Khasm: Unresolved ambiguity preserved without forced consensus."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-ILZAM-03",
                framework_id="FW-NICENE",
                formulation_title="The Word in John 1:1",
                proposition_text="The Logos is a distinct hypostasis alongside God.",
                formal_creedal_source="Patristic Commentary",
                historical_era=HistoricalEra.EARLY_PATRISTIC,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-ILZAM-03",
            deconstructed_premise_text="Yohanes 1:1c 'theos en ho logos'",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.EXEGETICAL_TENSION,
            evidence_confidence=0.88,
            audit_confidence=0.85,
            audit_finding_detail="Anarthrous theos permits qualitative or predicate-nominal interpretation; hypostatic distinction unresolved.",
        )
        res = self.theo_mgr.execute_comparison_run(
            proposition_id="PROP-ILZAM-03",
            audits=[audit],
        )
        self.assertEqual(res.audit_verdict, AuditVerdict.IN_TENSION)

    # -------------------------------------------------------------------------
    # 5. ANTI-ANACHRONISM FIREWALL
    # -------------------------------------------------------------------------

    def test_10_anti_anachronism_detects_post_biblical_terminology(self) -> None:
        """Anti-Anachronism: Registration detects post-biblical philosophical terms."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-ANACHRON-01",
                framework_id="FW-NICENE",
                formulation_title="Hypostatic Union Formulation",
                proposition_text="Christ has two natures in one hypostasis with communicatio_idiomatum.",
                formal_creedal_source="Council of Chalcedon 451",
                historical_era=HistoricalEra.POST_CHALCEDONIAN,
            )
        )
        self.assertTrue(prop.contains_post_biblical_terminology)
        self.assertIn("hypostasis", prop.post_biblical_terms)
        self.assertIn("communicatio_idiomatum", prop.post_biblical_terms)

    def test_11_anti_anachronism_rejects_unwarranted_retrojection(self) -> None:
        """Anti-Anachronism: Rejects retrojecting later terminology into biblical text as original intent."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-RETROJECT-01",
                framework_id="FW-NICENE",
                formulation_title="Original Intent Retrojection",
                proposition_text="Paul explicitly taught the Trinity using homoousios.",
                formal_creedal_source="Late Polemic",
                historical_era=HistoricalEra.BIBLICAL_ERA,  # Claiming it's Biblical era!
                contains_post_biblical_terminology=False,
            )
        )
        retroject_audit = PropositionAuditInput(
            audit_id="AUDIT-RETRO-01",
            deconstructed_premise_text="Paul meant homoousios in 1 Corinthians 8:6",
            target_evidence_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            target_passage_or_pericope_id="PERIC_1COR_8_6",
            alignment_status=AlignmentStatus.ANACHRONISTIC_RETROJECTION,
            evidence_confidence=0.8,
            audit_confidence=0.7,
            is_anachronism_detected=True,
            audit_finding_detail="Homoousios is absent from NT Koine corpus; 4th-century retrojection.",
        )
        with self.assertRaises(AnachronisticRetrojectionError):
            self.theo_mgr.execute_comparison_run(
                proposition_id="PROP-RETROJECT-01",
                audits=[retroject_audit],
                config=TheologicalComparisonConfig(allow_unwarranted_retrojection=False),
            )

    # -------------------------------------------------------------------------
    # 6. IDENTITY FIREWALL (Metaphorical agency != Ontological identity)
    # -------------------------------------------------------------------------

    def test_12_identity_firewall_rejects_agency_to_ontology_collapse(self) -> None:
        """Identity Firewall: Rejects collapsing divine agency / representation into ontological identity."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-IDENTITY-01",
                framework_id="FW-NICENE",
                formulation_title="Angel of YHWH Identity",
                proposition_text="The Angel of YHWH is ontologically identical to YHWH.",
                formal_creedal_source="Treatise",
                historical_era=HistoricalEra.EARLY_PATRISTIC,
            )
        )
        collapse_audit = PropositionAuditInput(
            audit_id="AUDIT-COLLAPSE-01",
            deconstructed_premise_text="Exodus 23:20-21 'My name is in him'",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_passage_or_pericope_id="PERIC_EXO_23_20",
            alignment_status=AlignmentStatus.CATEGORY_MISTAKE_IDENTITY,
            evidence_confidence=0.85,
            audit_confidence=0.8,
            is_identity_collapse_detected=True,
            audit_finding_detail="Agency principle (sheliah) confers authority/name, not ontological essence.",
        )
        with self.assertRaises(IdentityCollapseError):
            self.theo_mgr.execute_comparison_run(
                proposition_id="PROP-IDENTITY-01",
                audits=[collapse_audit],
                config=TheologicalComparisonConfig(allow_identity_collapse=False),
            )

    # -------------------------------------------------------------------------
    # 7. CONFIDENCE PROPAGATION (Weakest critical dependency)
    # -------------------------------------------------------------------------

    def test_13_confidence_capped_by_weakest_critical_dependency(self) -> None:
        """Confidence: Overall confidence strictly capped by weakest critical dependency."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-CONF-01",
                framework_id="FW-SOCINIAN",
                formulation_title="Christological Subordination",
                proposition_text="Jesus is a distinct human being created by God.",
                formal_creedal_source="Catechism",
                historical_era=HistoricalEra.REFORMATION,
            )
        )
        audits = [
            PropositionAuditInput(
                audit_id="AUDIT-CONF-A",
                deconstructed_premise_text="1 Timotius 2:5 'one mediator, the man Christ Jesus'",
                target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
                target_passage_or_pericope_id="PERIC_1TIM_2_5",
                alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
                evidence_confidence=0.95,
                audit_confidence=0.92,
                audit_finding_detail="Anthropos denotes human nature.",
                is_critical_dependency=True,
            ),
            PropositionAuditInput(
                audit_id="AUDIT-CONF-B",
                deconstructed_premise_text="Kisah Para Rasul 2:22 'a man accredited by God'",
                target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
                target_passage_or_pericope_id="PERIC_ACT_2_22",
                alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
                evidence_confidence=0.72,
                audit_confidence=0.68,
                audit_finding_detail="Historical speech context.",
                is_critical_dependency=True,
            ),
        ]
        res = self.theo_mgr.execute_comparison_run(
            proposition_id="PROP-CONF-01",
            audits=audits,
        )
        self.assertAlmostEqual(res.overall_confidence, 0.68, places=4)

    def test_14_confidence_inflation_exceeding_evidence_rejected(self) -> None:
        """Confidence: Reject audit confidence exceeding evidence confidence."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-CONF-02",
                framework_id="FW-SOCINIAN",
                formulation_title="Test Conf",
                proposition_text="Test statement.",
                formal_creedal_source="Catechism",
                historical_era=HistoricalEra.REFORMATION,
            )
        )
        audit_inflated = PropositionAuditInput(
            audit_id="AUDIT-INFLATE-01",
            deconstructed_premise_text="Inflated audit",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_1TIM_2_5",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.60,
            audit_confidence=0.85,  # 0.85 > 0.60 VIOLATION!
            audit_finding_detail="Confidence arbitrarily elevated.",
        )
        with self.assertRaises(TheologicalConfidenceInflationError):
            self.theo_mgr.execute_comparison_run(
                proposition_id="PROP-CONF-02",
                audits=[audit_inflated],
            )

    # -------------------------------------------------------------------------
    # 8. SYMMETRICAL FRAMEWORK EVALUATION
    # -------------------------------------------------------------------------

    def test_15_symmetrical_framework_evaluation_independent_and_unbiased(self) -> None:
        """Symmetrical Evaluation: Multiple frameworks evaluated independently without majority voting."""
        prop_nicene = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-COMP-NICENE",
                framework_id="FW-NICENE",
                formulation_title="Nicene Reading",
                proposition_text="Yohanes 1:1 implies co-equal deity.",
                formal_creedal_source="Nicene Exegesis",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        prop_socinian = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-COMP-SOCINIAN",
                framework_id="FW-SOCINIAN",
                formulation_title="Socinian Reading",
                proposition_text="Yohanes 1:1 implies divine plan/wisdom embodied in Christ.",
                formal_creedal_source="Socinian Exegesis",
                historical_era=HistoricalEra.REFORMATION,
            )
        )

        audit_nicene = PropositionAuditInput(
            audit_id="AUDIT-NICENE-JHN1",
            deconstructed_premise_text="Word was God predicate",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.EXEGETICAL_TENSION,
            evidence_confidence=0.85,
            audit_confidence=0.80,
            audit_finding_detail="Anarthrous theos is qualitative or predicate.",
        )
        audit_socinian = PropositionAuditInput(
            audit_id="AUDIT-SOCINIAN-JHN1",
            deconstructed_premise_text="Word as divine wisdom in Jewish Targumic Memra",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.85,
            audit_confidence=0.82,
            audit_finding_detail="Targumic personification fits Jewish monotheistic context.",
        )

        self.theo_mgr.execute_comparison_run(prop_nicene.proposition_id, [audit_nicene])
        self.theo_mgr.execute_comparison_run(prop_socinian.proposition_id, [audit_socinian])

        matrix = self.theo_mgr.compare_frameworks_symmetrically(
            framework_ids=["FW-NICENE", "FW-SOCINIAN"],
            pericope_or_passage_id="PERIC_JHN_1_1",
        )
        self.assertTrue(matrix["consensus_privileging_rejected"])
        self.assertTrue(matrix["majority_voting_rejected"])
        self.assertIn("FW-NICENE", matrix["frameworks"])
        self.assertIn("FW-SOCINIAN", matrix["frameworks"])

    def test_16_symmetrical_comparison_requires_multiple_frameworks(self) -> None:
        """Symmetrical Evaluation: Fails if fewer than two frameworks supplied."""
        with self.assertRaises(AsymmetricalFrameworkEvaluationError):
            self.theo_mgr.compare_frameworks_symmetrically(
                framework_ids=["FW-NICENE"],
                pericope_or_passage_id="PERIC_JHN_1_1",
            )

    # -------------------------------------------------------------------------
    # 9. AUDIT VERDICT DERIVATION SUITE
    # -------------------------------------------------------------------------

    def test_17_verdict_supported_when_fully_grounded(self) -> None:
        """Verdict: SUPPORTED when all premises are textually supported with zero critiques."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-VERD-SUP",
                framework_id="FW-SOCINIAN",
                formulation_title="Jesus as Prophet",
                proposition_text="Jesus was a prophet mighty in deed and word before God and all the people.",
                formal_creedal_source="Biblical Confession",
                historical_era=HistoricalEra.BIBLICAL_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-VERD-SUP-01",
            deconstructed_premise_text="Lukas 24:19 'a prophet mighty in deed and word'",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_LUK_24_19",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.95,
            audit_confidence=0.95,
            audit_finding_detail="Exact textual affirmation.",
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])
        self.assertEqual(res.audit_verdict, AuditVerdict.SUPPORTED)

    def test_18_verdict_insufficiently_warranted_when_evidence_absent(self) -> None:
        """Verdict: INSUFFICIENTLY_WARRANTED when premises lack textual warrant."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-VERD-INSUFF",
                framework_id="FW-NICENE",
                formulation_title="Specific Scholastic Theory",
                proposition_text="Christ possessed two distinct wills operating in absolute perichoretic harmony.",
                formal_creedal_source="Constantinople III 680",
                historical_era=HistoricalEra.POST_CHALCEDONIAN,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-VERD-INSUFF-01",
            deconstructed_premise_text="Dual will faculties",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.ABSENCE_OF_TEXTUAL_WARRANT,
            evidence_confidence=0.8,
            audit_confidence=0.8,
            audit_finding_detail="Biblical text contains no faculty psychology of dual wills.",
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])
        self.assertEqual(res.audit_verdict, AuditVerdict.INSUFFICIENTLY_WARRANTED)

    def test_19_verdict_contradicted_when_direct_textual_clash(self) -> None:
        """Verdict: CONTRADICTED when direct contradiction exists."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-VERD-CONTRA",
                framework_id="FW-NICENE",
                formulation_title="Omniscience Assertion",
                proposition_text="The earthly Jesus possessed absolute divine omniscience at all times.",
                formal_creedal_source="Scholastic Dogma",
                historical_era=HistoricalEra.MEDIEVAL,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-VERD-CONTRA-01",
            deconstructed_premise_text="Markus 13:32 'nor the Son, but only the Father'",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_MRK_13_32",
            alignment_status=AlignmentStatus.CONTRADICTION,
            evidence_confidence=0.96,
            audit_confidence=0.95,
            audit_finding_detail="Text explicitly excludes the Son from knowing the day and hour.",
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])
        self.assertEqual(res.audit_verdict, AuditVerdict.CONTRADICTED)

    # -------------------------------------------------------------------------
    # 10. DATABASE IMMUTABILITY TRIGGERS & SUPERSESSION
    # -------------------------------------------------------------------------

    def test_20_framework_immutability_trigger_blocks_update_and_delete(self) -> None:
        """Immutability: SQLite triggers block UPDATE and DELETE on theological_frameworks."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE theological_frameworks SET framework_name = 'Modified' WHERE framework_id = 'FW-NICENE'"
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM theological_frameworks WHERE framework_id = 'FW-NICENE'"
                )

    def test_21_proposition_immutability_trigger_blocks_arbitrary_update_and_delete(self) -> None:
        """Immutability: SQLite triggers block arbitrary UPDATE and DELETE on dogmatic_propositions."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-IMMUT-01",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE dogmatic_propositions SET proposition_text = 'Tampered' WHERE proposition_id = ?",
                    (prop.proposition_id,),
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM dogmatic_propositions WHERE proposition_id = ?",
                    (prop.proposition_id,),
                )

    def test_22_run_immutability_trigger_blocks_arbitrary_update_and_delete(self) -> None:
        """Immutability: SQLite triggers block UPDATE and DELETE on theological_comparison_runs."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-IMMUT-RUN-01",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-IMMUT-01",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Detail",
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE theological_comparison_runs SET overall_confidence = 0.99 WHERE run_id = ?",
                    (res.run_id,),
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM theological_comparison_runs WHERE run_id = ?",
                    (res.run_id,),
                )

    def test_23_supersession_transition_succeeds(self) -> None:
        """Lifecycle: Valid transition of run and audits to SUPERSEDED succeeds."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-SUPERSEDE-01",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-SUP-01",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Detail",
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])

        # Supersede
        self.theo_mgr.supersede_comparison_run(
            run_id=res.run_id,
            superseding_run_id="NEW-RUN-01",
            reason=ChangeReason.REANALYSIS,
        )
        updated_run = self.theo_mgr.get_comparison_run(res.run_id)
        self.assertEqual(updated_run.status, ComparisonRunStatus.SUPERSEDED)

    # -------------------------------------------------------------------------
    # 11. TRANSACTION ATOMICITY & CONCURRENCY
    # -------------------------------------------------------------------------

    def test_24_transaction_atomicity_rolls_back_on_failure(self) -> None:
        """Transaction Safety: If audit validation fails mid-run, no partial records remain."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-ATOMIC-01",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        valid_audit = PropositionAuditInput(
            audit_id="AUDIT-ATOM-01",
            deconstructed_premise_text="Valid premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Valid detail",
        )
        invalid_audit = PropositionAuditInput(
            audit_id="AUDIT-ATOM-02",
            deconstructed_premise_text="Invalid premise",
            target_evidence_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,  # Will fail!
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Violates tier",
        )

        with self.assertRaises(DogmaticEvidenceContaminationError):
            self.theo_mgr.execute_comparison_run(
                prop.proposition_id,
                [valid_audit, invalid_audit],
                run_id="RUN-SHOULD-ROLLBACK",
            )

        # Verify nothing was committed
        with self.engine.get_read_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM theological_comparison_runs WHERE run_id = 'RUN-SHOULD-ROLLBACK'")
            self.assertEqual(cursor.fetchone()[0], 0)
            cursor.execute("SELECT COUNT(*) FROM proposition_evidence_audits WHERE audit_id = 'AUDIT-ATOM-01'")
            self.assertEqual(cursor.fetchone()[0], 0)

    def test_25_concurrency_safety_under_multithreaded_execution(self) -> None:
        """Concurrency: Multi-threaded execution performs runs without deadlock or corruption."""
        def worker(idx: int) -> str:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            mgr = TheologicalComparisonManager(eng, vm, pt)

            prop_id = f"PROP-CONC-{idx}"
            mgr.register_proposition(
                DogmaticPropositionDefinition(
                    proposition_id=prop_id,
                    framework_id="FW-NICENE",
                    formulation_title=f"Concurrent Prop {idx}",
                    proposition_text=f"Proposition {idx}",
                    formal_creedal_source="Creed",
                    historical_era=HistoricalEra.NICENE_ERA,
                )
            )
            audit = PropositionAuditInput(
                audit_id=f"AUDIT-CONC-{idx}",
                deconstructed_premise_text=f"Premise {idx}",
                target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
                target_passage_or_pericope_id="PERIC_JHN_1_1",
                alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
                evidence_confidence=0.85,
                audit_confidence=0.85,
                audit_finding_detail="Detail",
            )
            res = mgr.execute_comparison_run(prop_id, [audit], run_id=f"RUN-CONC-{idx}")
            eng.close()
            return res.run_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(worker, i) for i in range(4)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 4)

    # -------------------------------------------------------------------------
    # 12. CRYPTOGRAPHIC PROVENANCE & RECORD RETRIEVAL
    # -------------------------------------------------------------------------

    def test_26_cryptographic_provenance_and_full_retrieval(self) -> None:
        """Provenance: Provenance records and deterministic hashes generated properly."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-PROV-01",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-PROV-01",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Detail",
        )
        critique = IlzamCritiqueInput(
            critique_id="CRIT-PROV-01",
            critique_type=CritiqueType.AMBIGUITY_OR_UNRESOLVED_ANTINOMY,
            acknowledged_premise_a="Premise A",
            dependency_chain=["C1"],
            demonstration_text="Demo",
            critique_severity=CritiqueSeverity.FORMAL_AMBIGUITY,
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit], [critique])

        self.assertTrue(res.provenance_id.startswith("PRV-"))
        self.assertTrue(res.version_id.startswith("VER-"))
        self.assertEqual(len(res.input_content_hash), 64)
        self.assertEqual(len(res.output_hash), 64)

        audits = self.theo_mgr.get_audits_for_run(res.run_id)
        critiques = self.theo_mgr.get_critiques_for_run(res.run_id)
        self.assertEqual(len(audits), 1)
        self.assertEqual(len(critiques), 1)

    # -------------------------------------------------------------------------
    # 13. MIGRATION & REPOSITORY INTEGRITY
    # -------------------------------------------------------------------------

    def test_27_migration_021_checksum_locked(self) -> None:
        """Migration 021 checksum is locked and deterministic."""
        m_file = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "021_theological_comparison.sql"
        self.assertTrue(m_file.exists())
        content = m_file.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        self.assertEqual(actual, EXPECTED_021_CHECKSUM)

    def test_28_migrations_001_to_020_strictly_unchanged(self) -> None:
        """Migrations 001–020 checksums remain strictly unchanged."""
        base_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for fname, exp_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            fpath = base_dir / fname
            self.assertTrue(fpath.exists(), f"Missing migration file: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, exp_hash, f"Checksum mismatch in frozen migration: {fname}")

    def test_29_legacy_database_strictly_untouched(self) -> None:
        """Legacy knowledge base at /home/ubuntu/.polya/polya_index.db remains strictly untouched."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_hash = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, LEGACY_DB_SHA256)

    def test_30_missing_framework_lookup_returns_none(self) -> None:
        """Validation: Looking up non-existent framework returns None."""
        fw = self.theo_mgr.get_framework("NON_EXISTENT_FW")
        self.assertIsNone(fw)

    def test_31_missing_proposition_lookup_returns_none(self) -> None:
        """Validation: Looking up non-existent proposition returns None."""
        prop = self.theo_mgr.get_proposition("NON_EXISTENT_PROP")
        self.assertIsNone(prop)

    def test_32_missing_run_lookup_returns_none(self) -> None:
        """Validation: Looking up non-existent run returns None."""
        run = self.theo_mgr.get_comparison_run("NON_EXISTENT_RUN")
        self.assertIsNone(run)

    def test_33_audit_and_critique_immutability_triggers_block_update_and_delete(self) -> None:
        """Immutability: SQLite triggers block UPDATE and DELETE on audits and critiques."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-IMMUT-AUDIT",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-IMMUT-ROW",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Detail",
        )
        critique = IlzamCritiqueInput(
            critique_id="CRIT-IMMUT-ROW",
            critique_type=CritiqueType.UNSUPPORTED_INFERENCE,
            acknowledged_premise_a="Premise A",
            dependency_chain=["C1"],
            demonstration_text="Demo",
            critique_severity=CritiqueSeverity.UNWARRANTED_LEAP,
        )
        self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit], [critique])

        # Attempt to mutate audit
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE proposition_evidence_audits SET audit_finding_detail = 'Tampered' WHERE audit_id = 'AUDIT-IMMUT-ROW'"
                )

        # Attempt to delete audit
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM proposition_evidence_audits WHERE audit_id = 'AUDIT-IMMUT-ROW'"
                )

        # Attempt to mutate critique
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE ilzam_critique_records SET demonstration_text = 'Tampered' WHERE critique_id = 'CRIT-IMMUT-ROW'"
                )

        # Attempt to delete critique
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM ilzam_critique_records WHERE critique_id = 'CRIT-IMMUT-ROW'"
                )

    def test_34_verdict_partially_supported(self) -> None:
        """Verdict: PARTIALLY_SUPPORTED when mixed supported and unsupported premises occur."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-PARTIAL-01",
                framework_id="FW-NICENE",
                formulation_title="Partial Support Title",
                proposition_text="Partial premise statement.",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audits = [
            PropositionAuditInput(
                audit_id="AUDIT-PART-1",
                deconstructed_premise_text="Supported Premise",
                target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
                target_passage_or_pericope_id="PERIC_JHN_1_1",
                alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
                evidence_confidence=0.9,
                audit_confidence=0.9,
                audit_finding_detail="Textual",
            ),
            PropositionAuditInput(
                audit_id="AUDIT-PART-2",
                deconstructed_premise_text="Unsupported Premise",
                target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
                target_passage_or_pericope_id="PERIC_JHN_1_1",
                alignment_status=AlignmentStatus.ABSENCE_OF_TEXTUAL_WARRANT,
                evidence_confidence=0.8,
                audit_confidence=0.8,
                audit_finding_detail="Absent",
            ),
        ]
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, audits)
        self.assertEqual(res.audit_verdict, AuditVerdict.PARTIALLY_SUPPORTED)

    def test_35_verdict_unresolved_on_formal_ambiguity(self) -> None:
        """Verdict: UNRESOLVED when formal ambiguity critique is present."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-UNRESOLVED-01",
                framework_id="FW-NICENE",
                formulation_title="Ambiguous Formulation",
                proposition_text="Ambiguous statement.",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-UNRES-01",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Textual",
        )
        critique = IlzamCritiqueInput(
            critique_id="CRIT-UNRES-01",
            critique_type=CritiqueType.AMBIGUITY_OR_UNRESOLVED_ANTINOMY,
            acknowledged_premise_a="Premise A",
            dependency_chain=["C1"],
            demonstration_text="Formal ambiguity present.",
            critique_severity=CritiqueSeverity.FORMAL_AMBIGUITY,
        )
        res = self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit], [critique])
        self.assertEqual(res.audit_verdict, AuditVerdict.UNRESOLVED)

    def test_36_internal_cycle_in_dependency_chain_rejected(self) -> None:
        """Anti-Circularity: Internal loop in critique dependency chain rejected."""
        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-LOOP-01",
                framework_id="FW-NICENE",
                formulation_title="Loop Title",
                proposition_text="Loop statement.",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-LOOP-01",
            deconstructed_premise_text="Premise",
            target_evidence_tier=ClaimTier.T1_LINGUISTIC_FACT,
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Detail",
        )
        critique_with_cycle = IlzamCritiqueInput(
            critique_id="CRIT-LOOP-01",
            critique_type=CritiqueType.INTERNAL_PREMISE_CONTRADICTION,
            acknowledged_premise_a="Premise A",
            dependency_chain=["CLAIM_A", "CLAIM_B", "CLAIM_A"],  # Loop!
            demonstration_text="Internal cycle.",
            critique_severity=CritiqueSeverity.FATAL_INTERNAL_CONTRADICTION,
        )
        with self.assertRaises(CircularProofStructureError):
            self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit], [critique_with_cycle])

    def test_37_database_target_claim_tier_t4_rejected(self) -> None:
        """Theology Firewall: Audit referencing existing T4 claim in claims table rejected."""
        # Insert a T4 claim into claims table
        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO claims (
                    claim_id, pericope_id, claim_tier, epistemic_type,
                    claim_text, claimed_by, epistemic_status,
                    doctrinal_system, is_theology_independent
                ) VALUES (
                    'CLM-EXISTING-T4', 'PERIC_JHN_1_1', 'T4_THEOLOGICAL_CLAIM', 'THEOLOGICAL_CLAIM',
                    'Existing dogma in DB', 'SYSTEM', 'UNPROVEN_DOGMA',
                    'NICENE', 0
                )
                """
            )

        prop = self.theo_mgr.register_proposition(
            DogmaticPropositionDefinition(
                proposition_id="PROP-DB-T4-CHECK",
                framework_id="FW-NICENE",
                formulation_title="Title",
                proposition_text="Text",
                formal_creedal_source="Source",
                historical_era=HistoricalEra.NICENE_ERA,
            )
        )
        audit = PropositionAuditInput(
            audit_id="AUDIT-DB-T4",
            deconstructed_premise_text="Premise claiming to be T2 but referencing T4 claim in DB",
            target_evidence_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,  # claims to be T2
            target_claim_id="CLM-EXISTING-T4",  # actually T4 in DB!
            target_passage_or_pericope_id="PERIC_JHN_1_1",
            alignment_status=AlignmentStatus.TEXTUALLY_SUPPORTED,
            evidence_confidence=0.9,
            audit_confidence=0.9,
            audit_finding_detail="Contaminated by DB claim tier.",
        )
        with self.assertRaises(DogmaticEvidenceContaminationError):
            self.theo_mgr.execute_comparison_run(prop.proposition_id, [audit])

    def test_38_symmetrical_comparison_rejects_duplicate_framework_ids(self) -> None:
        """Symmetrical Comparison: Fails if duplicate framework IDs passed."""
        with self.assertRaises(AsymmetricalFrameworkEvaluationError):
            self.theo_mgr.compare_frameworks_symmetrically(
                framework_ids=["FW-NICENE", "FW-NICENE"],
                pericope_or_passage_id="PERIC_JHN_1_1",
            )


if __name__ == "__main__":
    unittest.main()
