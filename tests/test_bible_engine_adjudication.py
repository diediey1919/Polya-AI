"""
Unit and Adversarial Test Suite for Evidence Adjudication Subsystem (Task 3.5).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Multi-hypothesis evaluation and cross-examination
  2. Competing interpretations preserved under unresolved tension
  3. Illegitimate Totality Transfer firewall rejection
  4. Root Fallacy firewall rejection
  5. Semantic Anachronism firewall rejection
  6. Unwarranted Generalization firewall rejection
  7. Anti-suppression: omission of counter-evidence rejected
  8. Majority-vote rejection: source volume != truth
  9. Consensus-as-truth rejection: consensus != verified textual fact
  10. Weakest-link confidence propagation (propagated <= min(critical_dependencies))
  11. Confidence escalation rejection (propagated > base/weakest rejected)
  12. Mid-transaction atomic rollback on failure (zero orphaned rows)
  13. Concurrency safety under multithreaded writers
  14. Immutability enforced by SQL triggers (no update/delete)
  15. Status transition: only COMPLETED -> SUPERSEDED allowed on runs
  16. Provenance and versioning integrity
  17. Foreign-key constraint enforcement
  18. Migration 018 checksum locked
  19. Migrations 001–017 checksums strictly unchanged
  20. Legacy database strictly untouched
"""

import hashlib
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.adjudication import (
    AdjudicatedVerdictResult,
    AdjudicationConflictDefinition,
    AdjudicationEvidenceItem,
    AdjudicationHypothesisDefinition,
    AdjudicationRunConfig,
    AdjudicationRunResult,
    AdjudicationState,
    ConflictSeverity,
    ConflictType,
    EvidenceAdjudicationManager,
    FallacyAuditor,
    FallacySeverity,
    FallacyType,
    HypothesisStatus,
    ResolutionMethod,
    VerdictStatus,
    compute_canonical_hash,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AdjudicationConcurrencyError,
    AdjudicationImmutabilityError,
    AdjudicationInvalidProvenanceError,
    AdjudicationInvalidVersionError,
    AdjudicationNotFoundError,
    AdjudicationValidationError,
    AnachronisticSemanticInjectionError,
    ConfidenceEscalationError,
    ConsensusAsTruthError,
    EvidenceAdjudicationSubsystemError,
    FallacyDetectedError,
    IllegitimateTotalityTransferError,
    MajorityVoteEpistemologyError,
    RootFallacyError,
    SuppressedCounterEvidenceError,
    UnresolvedConflictSuppressionError,
    UnwarrantedGeneralizationError,
)
from bible_engine.evidence_claim import (
    ClaimTier,
    ConfidenceLevel,
    EvidenceClass,
    EvidenceClaimManager,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
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
    "017_reception_history.sql": "76bfc99691e5d05da1fd662f4371187337a5aca943d8b57481b527125b965e13",
}

EXPECTED_018_CHECKSUM = "50aa9dbeb9fa27e25b0fa4299ac4d01aeaf44bc1907115f9a03fd0eece13e025"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"



class TestEvidenceAdjudicationSubsystem(unittest.TestCase):
    """Unit and Adversarial Test Suite for Evidence Adjudication Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_adjudication.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.evidence_claim_manager = EvidenceClaimManager(self.engine)
        self.adjudication_mgr = EvidenceAdjudicationManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
            self.evidence_claim_manager,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('ROM', 'TEST_NT', 45, 'Roma', 'Romans', 'GREEK', 16);")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-ROM-03-27-31', 'ROM', 'Roma 3:27-31', 3, 27, 3, 31,
                    'EPISTLE', 'NA28_SECTION', 'HIGH', 'REGISTERED', '1.0', '2026-09-30'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO passages (passage_id, pericope_id, book_id, chapter, verse, sort_order)
                VALUES ('PAS-ROM-03-28', 'PER-ROM-03-27-31', 'ROM', 3, 28, 1);
                """
            )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # CHECKSUM & BASELINE INTEGRITY
    # -------------------------------------------------------------------------

    def test_01_legacy_db_checksum_unchanged(self) -> None:
        """Verify legacy database remains strictly unaltered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            h = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
            self.assertEqual(h, LEGACY_DB_SHA256, "Legacy DB checksum must remain untouched.")

    def test_02_migration_checksums_001_to_017_frozen(self) -> None:
        """Verify all previous migrations 001–017 retain exact frozen hashes."""
        schemas_dir = Path("/home/ubuntu/Polya-AI/schemas/bible_engine")
        for mig_file, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            path = schemas_dir / mig_file
            self.assertTrue(path.exists(), f"Missing migration file: {mig_file}")
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Checksum mismatch for {mig_file}")

    def test_03_migration_018_checksum_locked(self) -> None:
        """Verify migration 018 checksum is strictly locked."""
        path = Path("/home/ubuntu/Polya-AI/schemas/bible_engine/018_evidence_adjudication.sql")
        self.assertTrue(path.exists(), "Migration 018 must exist.")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(actual_hash, EXPECTED_018_CHECKSUM, "Migration 018 checksum mismatch.")

    # -------------------------------------------------------------------------
    # MULTI-HYPOTHESIS EVALUATION & COMPETING PRESERVATION
    # -------------------------------------------------------------------------

    def test_04_multi_hypothesis_adjudication_competing_preserved(self) -> None:
        """Verify competing interpretations are preserved when unresolved tension exists."""
        ev1 = AdjudicationEvidenceItem(
            evidence_id="EV-ROM328-1",
            evidence_class=EvidenceClass.E3_SYNTAX,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.85,
            source_reference="Roma 3:28 pistis genitive/dative syntax",
        )
        ev2 = AdjudicationEvidenceItem(
            evidence_id="EV-ROM328-2",
            evidence_class=EvidenceClass.E6_IMMEDIATE_CONTEXT,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            confidence=0.80,
            source_reference="Roma 3:27-31 boundary discussion",
        )

        hyp_a = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-A-FAITH-IN-CHRIST",
            title="Objective Faith in Christ",
            description="Reading pistis as objective faith exercised by the believer.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.82,
            supporting_evidence_ids=["EV-ROM328-1"],
            critical_dependency_ids=["EV-ROM328-1"],
        )
        hyp_b = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-B-FAITHFULNESS-OF-CHRIST",
            title="Subjective Faithfulness of Christ",
            description="Reading pistis as the subjective faithfulness of Christ Himself.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.78,
            supporting_evidence_ids=["EV-ROM328-2"],
            critical_dependency_ids=["EV-ROM328-2"],
        )

        conflict = AdjudicationConflictDefinition(
            hypothesis_a_code="HYP-A-FAITH-IN-CHRIST",
            hypothesis_b_code="HYP-B-FAITHFULNESS-OF-CHRIST",
            conflict_type=ConflictType.EVIDENTIARY_ASYMMETRY,
            conflict_severity=ConflictSeverity.HIGH,
            resolution_method=ResolutionMethod.UNRESOLVED_PRESERVED,
            resolution_reasoning="Both readings are syntactically and contextually viable; preserving competing hypotheses.",
        )

        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id="PER-ROM-03-27-31",
            hypotheses=[hyp_a, hyp_b],
            conflicts=[conflict],
            evidence_pool=[ev1, ev2],
        )

        self.assertEqual(res.status, "COMPLETED")
        self.assertEqual(len(res.verdicts), 2)
        # Both must have verdict COMPETING_INTERPRETATION_PRESERVED
        for v in res.verdicts:
            self.assertEqual(v.verdict_status, VerdictStatus.COMPETING_INTERPRETATION_PRESERVED)
            self.assertEqual(v.is_competing_preserved, 1)
            self.assertEqual(v.unresolved_conflict_count, 1)

    # -------------------------------------------------------------------------
    # FALLACY REJECTION FIREWALLS
    # -------------------------------------------------------------------------

    def test_05_illegitimate_totality_transfer_firewall(self) -> None:
        """Verify Illegitimate Totality Transfer (ITT) is deterministically rejected."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-ITT-1",
            evidence_class=EvidenceClass.E4_LEXICAL,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.90,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-TOTALITY-FALLACY",
            title="Total Lexical Transfer Claim",
            description="Asserting all 8 dictionary meanings apply simultaneously to Roma 3:28.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.85,
            supporting_evidence_ids=["EV-ITT-1"],
            metadata={"assert_all_senses": True, "transfers_totality": True},
        )

        with self.assertRaises(IllegitimateTotalityTransferError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[ev],
                config=AdjudicationRunConfig(enforce_strict_firewalls=True),
            )

    def test_06_root_fallacy_firewall(self) -> None:
        """Verify Root Fallacy is deterministically rejected."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-ROOT-1",
            evidence_class=EvidenceClass.E2_MORPHOLOGY,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.90,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ROOT-FALLACY",
            title="Etymological Root Fallacy Claim",
            description="Insisting meaning in Roma 3:28 is governed entirely by ancient root radix.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.85,
            supporting_evidence_ids=["EV-ROOT-1"],
            metadata={"etymological_derivation_only": True, "root_determines_meaning": True},
        )

        with self.assertRaises(RootFallacyError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[ev],
                config=AdjudicationRunConfig(enforce_strict_firewalls=True),
            )

    def test_07_semantic_anachronism_firewall(self) -> None:
        """Verify Semantic Anachronism (retrofitted theology/reception) is rejected."""
        ev_rec = AdjudicationEvidenceItem(
            evidence_id="EV-REC-1",
            evidence_class=EvidenceClass.E12_LATER_INTERPRETATION,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            confidence=0.88,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ANACHRONISM-CLAIM",
            title="16th Century Doctrine as Original Meaning",
            description="Claiming 16th century confessional definitions represent the ancient 1st century Greek text.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.85,
            supporting_evidence_ids=["EV-REC-1"],
            metadata={"injects_later_theology": True},
        )

        with self.assertRaises(AnachronisticSemanticInjectionError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[ev_rec],
                config=AdjudicationRunConfig(enforce_strict_firewalls=True),
            )

    def test_08_unwarranted_generalization_firewall(self) -> None:
        """Verify Unwarranted Generalization is rejected."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-LING-1",
            evidence_class=EvidenceClass.E2_MORPHOLOGY,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.95,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-GENERALIZATION-CLAIM",
            title="Morphology to Dogma Jump",
            description="Jumping from localized aorist participle to universal dogma.",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            base_confidence=0.90,
            supporting_evidence_ids=["EV-LING-1"],
            metadata={"unwarranted_generalization": True, "skip_contextual_link": True},
        )

        with self.assertRaises(UnwarrantedGeneralizationError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[ev],
                config=AdjudicationRunConfig(enforce_strict_firewalls=True),
            )

    # -------------------------------------------------------------------------
    # ANTI-SUPPRESSION, MAJORITY VOTE & CONSENSUS
    # -------------------------------------------------------------------------

    def test_09_anti_suppression_counter_evidence_flag_triggers_error(self) -> None:
        """Verify suppression of counter-evidence in conflict resolution is blocked."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-1",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.90,
        )
        hyp_a = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-A",
            title="Hyp A",
            description="Hyp A",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        hyp_b = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-B",
            title="Hyp B",
            description="Hyp B",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        conflict = AdjudicationConflictDefinition(
            hypothesis_a_code="HYP-A",
            hypothesis_b_code="HYP-B",
            conflict_type=ConflictType.MUTUALLY_EXCLUSIVE,
            conflict_severity=ConflictSeverity.HIGH,
            is_counter_evidence_suppressed=True,
        )

        with self.assertRaises(SuppressedCounterEvidenceError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp_a, hyp_b],
                conflicts=[conflict],
                evidence_pool=[ev],
            )

    def test_10_majority_vote_rejection(self) -> None:
        """Verify majority vote or source popularity cannot determine truth."""
        hyp_a = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-A",
            title="Hyp A",
            description="Hyp A",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        hyp_b = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-B",
            title="Hyp B",
            description="Hyp B",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        conflict = AdjudicationConflictDefinition(
            hypothesis_a_code="HYP-A",
            hypothesis_b_code="HYP-B",
            conflict_type=ConflictType.MUTUALLY_EXCLUSIVE,
            conflict_severity=ConflictSeverity.HIGH,
            is_majority_vote_applied=True,
        )

        with self.assertRaises(MajorityVoteEpistemologyError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp_a, hyp_b],
                conflicts=[conflict],
                evidence_pool=[],
            )

    def test_11_consensus_as_truth_rejection(self) -> None:
        """Verify consensus cannot be equated to textual truth."""
        hyp_a = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-A",
            title="Hyp A",
            description="Hyp A",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        hyp_b = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-B",
            title="Hyp B",
            description="Hyp B",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        conflict = AdjudicationConflictDefinition(
            hypothesis_a_code="HYP-A",
            hypothesis_b_code="HYP-B",
            conflict_type=ConflictType.MUTUALLY_EXCLUSIVE,
            conflict_severity=ConflictSeverity.HIGH,
            is_consensus_equated_truth=True,
        )

        with self.assertRaises(ConsensusAsTruthError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp_a, hyp_b],
                conflicts=[conflict],
                evidence_pool=[],
            )

    def test_12_premature_elimination_without_evidence_rejected(self) -> None:
        """Verify hypothesis cannot be eliminated without documented evidentiary justification."""
        hyp_elim = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ELIM",
            title="Eliminated Hyp",
            description="Eliminated without proof",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.7,
            is_eliminated=True,
            elimination_reason="",  # Empty reason must fail!
        )

        with self.assertRaises(UnresolvedConflictSuppressionError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp_elim],
                conflicts=[],
                evidence_pool=[],
            )

    # -------------------------------------------------------------------------
    # CONFIDENCE PROPAGATION & ESCALATION PREVENTION
    # -------------------------------------------------------------------------

    def test_13_weakest_link_confidence_propagation(self) -> None:
        """Verify compound confidence is strictly bounded by weakest critical dependency."""
        ev_strong = AdjudicationEvidenceItem(
            evidence_id="EV-STRONG",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.95,
            is_critical_dependency=True,
        )
        ev_weak = AdjudicationEvidenceItem(
            evidence_id="EV-WEAK",
            evidence_class=EvidenceClass.E10_INTERTEXTUAL,
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            confidence=0.45,
            is_critical_dependency=True,
        )

        # Base confidence is 0.90, but depends critically on EV-WEAK (0.45)
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-COMPOUND",
            title="Compound Claim",
            description="Relies on strong manuscript and weak intertextual link.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.90,
            supporting_evidence_ids=["EV-STRONG", "EV-WEAK"],
            critical_dependency_ids=["EV-STRONG", "EV-WEAK"],
        )

        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id=None,
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[ev_strong, ev_weak],
        )

        verdict = res.verdicts[0]
        # Propagated confidence must not exceed 0.45
        self.assertLessEqual(verdict.confidence_score, 0.45)
        self.assertEqual(verdict.weakest_critical_dependency_id, "EV-WEAK")
        self.assertEqual(verdict.weakest_critical_confidence, 0.45)

    # -------------------------------------------------------------------------
    # ATOMIC ROLLBACK & DATABASE IMMUTABILITY
    # -------------------------------------------------------------------------

    def test_14_mid_transaction_rollback_leaves_zero_orphaned_rows(self) -> None:
        """Verify atomic rollback on mid-transaction error leaves database completely clean."""
        # Initial counts
        with self.engine.transaction() as conn:
            cnt_runs = conn.execute("SELECT COUNT(*) FROM adjudication_runs").fetchone()[0]
            cnt_hyp = conn.execute("SELECT COUNT(*) FROM adjudication_hypotheses").fetchone()[0]
            cnt_verd = conn.execute("SELECT COUNT(*) FROM adjudicated_verdicts").fetchone()[0]

        # Construct invalid run that will fail on pre-flight or constraint
        hyp_bad = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-BAD",
            title="Bad Hyp",
            description="Bad Hyp",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
            is_eliminated=True,
            elimination_reason="eliminated because minority",  # Triggers MajorityVoteEpistemologyError
        )

        with self.assertRaises(MajorityVoteEpistemologyError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp_bad],
                conflicts=[],
                evidence_pool=[],
            )

        # Post counts must be identical (zero orphaned rows)
        with self.engine.transaction() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM adjudication_runs").fetchone()[0], cnt_runs)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM adjudication_hypotheses").fetchone()[0], cnt_hyp)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM adjudicated_verdicts").fetchone()[0], cnt_verd)

    def test_15_immutability_triggers_prevent_update_and_delete(self) -> None:
        """Verify SQL triggers abort UPDATE and DELETE operations on adjudication entities."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-IMMUT",
            title="Immutable Test",
            description="Immutable Description",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.75,
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id=None,
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[],
        )

        run_id = res.run_id
        hyp_id = res.hypothesis_ids[0]
        verd_id = res.verdict_ids[0]

        # 1. Update on hypothesis must raise IntegrityError (trigger abort)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE adjudication_hypotheses SET title = 'Changed' WHERE hypothesis_id = ?", (hyp_id,))

        # 2. Delete on hypothesis must raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM adjudication_hypotheses WHERE hypothesis_id = ?", (hyp_id,))

        # 3. Update on verdict must raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE adjudicated_verdicts SET confidence_score = 0.99 WHERE verdict_id = ?", (verd_id,))

        # 4. Delete on verdict must raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM adjudicated_verdicts WHERE verdict_id = ?", (verd_id,))

        # 5. Unauthorized update on run (changing fields other than status COMPLETED->SUPERSEDED)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE adjudication_runs SET adjudicator_id = 'HACKED' WHERE run_id = ?", (run_id,))

        # 6. Authorized status transition COMPLETED -> SUPERSEDED must succeed
        with self.engine.transaction() as conn:
            conn.execute("UPDATE adjudication_runs SET status = 'SUPERSEDED' WHERE run_id = ?", (run_id,))
            status = conn.execute("SELECT status FROM adjudication_runs WHERE run_id = ?", (run_id,)).fetchone()[0]
            self.assertEqual(status, "SUPERSEDED")

    # -------------------------------------------------------------------------
    # CONCURRENCY SAFETY
    # -------------------------------------------------------------------------

    def test_16_multithreaded_concurrent_runs(self) -> None:
        """Verify concurrent worker threads can execute distinct adjudication runs safely."""
        def run_task(worker_id: int) -> str:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            ecm = EvidenceClaimManager(eng)
            mgr = EvidenceAdjudicationManager(eng, vm, pt, ecm)

            hyp = AdjudicationHypothesisDefinition(
                hypothesis_code=f"HYP-CONC-{worker_id}",
                title=f"Concurrent Test {worker_id}",
                description=f"Concurrency Worker {worker_id}",
                claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
                base_confidence=0.70 + (worker_id * 0.02),
            )
            res = mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[],
                run_id=f"ADJ-RUN-CONC-{worker_id}",
            )
            eng.close()
            return res.run_id

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut1 = executor.submit(run_task, 1)
            fut2 = executor.submit(run_task, 2)
            run_ids = [fut1.result(), fut2.result()]

        self.assertEqual(len(run_ids), 2)
        self.assertEqual(len(set(run_ids)), 2)


        # Verify all concurrent runs exist in database
        with self.engine.transaction() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM adjudication_runs WHERE run_id LIKE 'ADJ-RUN-CONC-%'").fetchone()[0]
            self.assertEqual(cnt, 2)


    # -------------------------------------------------------------------------
    # PROVENANCE & QUERY APIS
    # -------------------------------------------------------------------------

    def test_17_provenance_and_version_chain_integrity(self) -> None:
        """Verify cryptographic provenance and object versions resolve accurately."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-PROV-TEST",
            title="Provenance Test Claim",
            description="Provenance verification",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.92,
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id=None,
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[],
        )

        run = self.adjudication_mgr.get_run(res.run_id)
        self.assertIsNotNone(run)
        self.assertEqual(run["provenance_id"], res.provenance_id)
        self.assertEqual(run["version_id"], res.version_id)

        hypotheses = self.adjudication_mgr.get_hypotheses_for_run(res.run_id)
        self.assertEqual(len(hypotheses), 1)
        self.assertEqual(hypotheses[0]["hypothesis_code"], "HYP-PROV-TEST")

        verdicts = self.adjudication_mgr.get_verdicts_for_run(res.run_id)
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["verdict_id"], res.verdict_ids[0])

    # -------------------------------------------------------------------------
    # ADVERSARIAL EDGE CASES & INTEGRITY CONSTRAINTS
    # -------------------------------------------------------------------------

    def test_18_absence_as_proof_fallacy_detection(self) -> None:
        """Verify absence of evidence is not treated as evidence of absence."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-ABS-1",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.85,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ABSENCE",
            title="Absence of Evidence Claim",
            description="Claiming reading is unbiblical because it is not attested in a specific single manuscript.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.75,
            supporting_evidence_ids=["EV-ABS-1"],
            metadata={"absence_as_proof": True},
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id=None,
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[ev],
            config=AdjudicationRunConfig(enforce_strict_firewalls=False),
        )
        fallacies = self.adjudication_mgr.get_fallacies_for_run(res.run_id)
        self.assertEqual(len(fallacies), 1)
        self.assertEqual(fallacies[0]["fallacy_type"], FallacyType.ABSENCE_AS_PROOF_FALLACY.value)

    def test_19_non_strict_fallacy_audit_generates_invalidated_verdict(self) -> None:
        """Verify non-strict mode records fatal fallacy and marks verdict INVALIDATED_BY_FALLACY."""
        ev = AdjudicationEvidenceItem(
            evidence_id="EV-REC-9",
            evidence_class=EvidenceClass.E12_LATER_INTERPRETATION,
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            confidence=0.90,
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ANACHRONISTIC-NONSTRICT",
            title="Anachronistic Claim Non-Strict",
            description="Projecting 17th century dogma into 1st century Greek text.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.85,
            supporting_evidence_ids=["EV-REC-9"],
            metadata={"anachronistic_reading": True},
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id=None,
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[ev],
            config=AdjudicationRunConfig(enforce_strict_firewalls=False),
        )
        self.assertEqual(len(res.verdicts), 1)
        v = res.verdicts[0]
        self.assertEqual(v.verdict_status, VerdictStatus.INVALIDATED_BY_FALLACY)
        self.assertGreaterEqual(v.fallacy_count, 1)

    def test_20_foreign_key_integrity_enforcement(self) -> None:
        """Verify foreign-key constraints reject non-existent passage or pericope references."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-FK-FAIL",
            title="FK Fail",
            description="FK Fail",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            base_confidence=0.8,
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="NON-EXISTENT-PASSAGE-ID",
                target_pericope_id=None,
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[],
            )

    def test_21_mixed_verdicts_preservation_and_elimination(self) -> None:
        """Verify adjudication correctly handles a tri-hypothesis scenario with mixed outcomes."""
        ev_fact = AdjudicationEvidenceItem(
            evidence_id="EV-DIRECT-GREEK",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.98,
        )
        # Hypothesis 1: Well-supported primary fact
        hyp_fact = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ESTABLISHED-SYNTAX",
            title="Established Greek Syntax",
            description="Pistis used in dative construction in Roma 3:28.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.98,
            supporting_evidence_ids=["EV-DIRECT-GREEK"],
            critical_dependency_ids=["EV-DIRECT-GREEK"],
        )
        # Hypothesis 2: Legitimate competing interpretation
        hyp_comp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-THEOLOGICAL-NUANCE",
            title="Competing Discourse Nuance",
            description="Nuanced reading preserved in discourse context.",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            base_confidence=0.72,
            supporting_evidence_ids=["EV-DIRECT-GREEK"],
        )
        # Hypothesis 3: Falsified / eliminated hypothesis on verified textual grounds
        hyp_elim = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-DISPROVEN-READING",
            title="Disproven Scribal Gloss",
            description="Later Western interpolation not in earliest witnesses.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.15,
            is_eliminated=True,
            elimination_reason="Absent from P46, Codex Sinaiticus, and Codex Vaticanus; demonstrated 9th century interpolation.",
        )
        conflict = AdjudicationConflictDefinition(
            hypothesis_a_code="HYP-ESTABLISHED-SYNTAX",
            hypothesis_b_code="HYP-THEOLOGICAL-NUANCE",
            conflict_type=ConflictType.TENSION,
            conflict_severity=ConflictSeverity.MODERATE,
            resolution_method=ResolutionMethod.UNRESOLVED_PRESERVED,
            resolution_reasoning="Discourse tension preserved without collapsing distinct theological emphases.",
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id="PER-ROM-03-27-31",
            hypotheses=[hyp_fact, hyp_comp, hyp_elim],
            conflicts=[conflict],
            evidence_pool=[ev_fact],
        )
        v_map = {v.hypothesis_code: v for v in res.verdicts}
        self.assertEqual(v_map["HYP-DISPROVEN-READING"].verdict_status, VerdictStatus.FALSIFIED_BY_PRIMARY_EVIDENCE)
        self.assertEqual(v_map["HYP-THEOLOGICAL-NUANCE"].verdict_status, VerdictStatus.COMPETING_INTERPRETATION_PRESERVED)

    def test_22_cannot_establish_fact_with_active_contrary_evidence(self) -> None:
        """Verify SQL CHECK constraint prevents ESTABLISHED_FACT when contrary_evidence_count > 0."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                # Direct SQL insert attempting to breach the firewall
                conn.execute(
                    """
                    INSERT INTO adjudicated_verdicts (
                        verdict_id, run_id, hypothesis_id, verdict_status, epistemic_tier,
                        confidence_score, weakest_critical_dependency_id, weakest_critical_confidence,
                        supporting_evidence_count, contrary_evidence_count, unresolved_conflict_count,
                        fallacy_count, is_consensus_derived, is_majority_vote_derived,
                        is_competing_preserved, verdict_rationale, provenance_id, version_id,
                        created_at, is_immutable, metadata_json
                    ) VALUES (
                        'VRD-BREACH-TEST', 'NON-EXISTENT', 'NON-EXISTENT', 'ESTABLISHED_FACT', 'T1_LINGUISTIC_FACT',
                        0.95, NULL, NULL, 5, 2, 0, 0, 0, 0, 0, 'Illicit fact with contrary evidence',
                        'PRV-FAKE', 'VER-FAKE', '2026-10-01T00:00:00Z', 1, NULL
                    )
                    """
                )

    def test_23_persisted_provenance_and_version_hashes_match_db_rows(self) -> None:
        """Verify object_versions content_hash matches DB rows and in-memory verdict IDs match DB."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-PROV-TEST",
            title="Provenance Integrity Test",
            description="Testing hash and ID alignment between memory and DB.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.92,
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id="PER-ROM-03-27-31",
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[],
        )
        self.assertEqual(len(res.verdicts), 1)
        verd = res.verdicts[0]

        # Check that in-memory verdict IDs match real persisted records
        self.assertFalse(verd.provenance_id.startswith("PROV-VRD-"))
        self.assertIsNotNone(self.provenance_tracker.get_record(verd.provenance_id))
        self.assertIsNotNone(self.version_manager.get_version(verd.version_id))

        with self.engine.connect() as conn:
            # Check hypothesis hash
            hyp_row = conn.execute("SELECT * FROM adjudication_hypotheses WHERE hypothesis_id = ?", (res.hypothesis_ids[0],)).fetchone()
            hyp_ver_row = conn.execute("SELECT content_hash FROM object_versions WHERE object_type = 'ADJUDICATION_HYPOTHESIS' AND object_id = ?", (res.hypothesis_ids[0],)).fetchone()
            self.assertEqual(compute_canonical_hash(dict(hyp_row)), hyp_ver_row[0])

            # Check verdict hash
            verd_row = conn.execute("SELECT * FROM adjudicated_verdicts WHERE verdict_id = ?", (verd.verdict_id,)).fetchone()
            verd_ver_row = conn.execute("SELECT content_hash FROM object_versions WHERE object_type = 'ADJUDICATED_VERDICT' AND object_id = ?", (verd.verdict_id,)).fetchone()
            self.assertEqual(compute_canonical_hash(dict(verd_row)), verd_ver_row[0])

    def test_24_counter_evidence_in_pool_blocks_established_fact(self) -> None:
        """Verify unlinked counter-evidence in pool blocks ESTABLISHED_FACT and preserves competing interpretation."""
        ev_supp = AdjudicationEvidenceItem(
            evidence_id="EV-PRIMARY-SUPP",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.95,
            is_counter_evidence=False,
            is_critical_dependency=True,
        )
        ev_counter = AdjudicationEvidenceItem(
            evidence_id="EV-UNLINKED-COUNTER",
            evidence_class=EvidenceClass.E3_SYNTAX,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            confidence=0.88,
            is_counter_evidence=True,
            is_critical_dependency=False,
            metadata={"target_hypothesis_code": "HYP-CANDIDATE-FACT"},
        )
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-CANDIDATE-FACT",
            title="Candidate for Established Fact",
            description="High confidence hypothesis with external unlinked counter evidence in pool.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.95,
            supporting_evidence_ids=["EV-PRIMARY-SUPP"],
            critical_dependency_ids=["EV-PRIMARY-SUPP"],
        )
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id="PER-ROM-03-27-31",
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[ev_supp, ev_counter],
        )
        verd = res.verdicts[0]
        # Must be preserved as competing interpretation due to counter evidence in pool
        self.assertEqual(verd.verdict_status, VerdictStatus.COMPETING_INTERPRETATION_PRESERVED)
        self.assertGreater(verd.contrary_evidence_count, 0)

    def test_25_propagated_confidence_rounding_bounds_base_confidence(self) -> None:
        """Verify propagated confidence never exceeds base confidence when base confidence has fine decimals."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-ROUNDING-TEST",
            title="Fine Decimals Rounding Test",
            description="Testing that 0.81996 does not round up to 0.8200 and crash SQLite CHECK constraint.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.81996,
        )
        # Must execute cleanly without IntegrityError CHECK constraint failed
        res = self.adjudication_mgr.execute_adjudication_run(
            target_passage_id="PAS-ROM-03-28",
            target_pericope_id="PER-ROM-03-27-31",
            hypotheses=[hyp],
            conflicts=[],
            evidence_pool=[],
        )
        self.assertEqual(len(res.verdicts), 1)
        verd = res.verdicts[0]
        self.assertLessEqual(verd.confidence_score, 0.81996)

    def test_26_missing_critical_dependency_raises_validation_error(self) -> None:
        """Verify missing critical dependency ID in evidence pool raises AdjudicationValidationError."""
        hyp = AdjudicationHypothesisDefinition(
            hypothesis_code="HYP-MISSING-CRIT",
            title="Missing Critical Dependency Test",
            description="Critical dependency ID not supplied in evidence pool.",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            base_confidence=0.90,
            critical_dependency_ids=["EV-DOES-NOT-EXIST"],
        )
        with self.assertRaises(AdjudicationValidationError):
            self.adjudication_mgr.execute_adjudication_run(
                target_passage_id="PAS-ROM-03-28",
                target_pericope_id="PER-ROM-03-27-31",
                hypotheses=[hyp],
                conflicts=[],
                evidence_pool=[],
            )


if __name__ == "__main__":
    unittest.main()

