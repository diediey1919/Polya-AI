"""
Unit and Adversarial Test Suite for Hierarchical Synthesis Engine (Task 3.7).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  1. Scope hierarchy: PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON
  2. Scope progression: Invalid scope jump rejected
  3. Scope progression: Permitted PERICOPE -> BOOK jump under explicit config
  4. Directionality: Higher scope cannot become constituent of lower scope (reverse scope rejected)
  5. Directionality: Circular synthesis (target using itself as constituent) rejected
  6. Bottom-up derivation: Claim without constituents rejected
  7. Anti-harmonization: Forced harmonization without tension rejected
  8. Anti-harmonization: Competing interpretations and tensions preserved
  9. Anti-harmonization: Unresolved divergence persisted as explicit tension
  10. Authorial distinctives: Authorial divergence tension requires distinct authors
  11. Reception firewall: E11/E12 cannot be synthesized as authorial book/corpus theology
  12. Reception firewall: E11/E12 accepted when authorial_context indicates reception history
  13. Weakest-link confidence: Synthesis claim confidence strictly bounded by weakest constituent
  14. Weakest-link confidence: Out-of-bounds explicit confidence rejected
  15. Weakest-link confidence: Explicit confidence inflation above constituent rejected
  16. Evidence tiers: E0-E12 and T0-T4 classifications preserved across scopes
  17. Provenance & versioning: Complete cryptographic audit chain for runs, claims, tensions
  18. Missing constituent references: Nonexistent verdict/node/evidence rejected
  19. Immutability: Direct SQL UPDATE and DELETE on synthesis tables blocked by triggers
  20. Supersession: Valid status transition to SUPERSEDED allowed
  21. Atomic transactions: Mid-synthesis failure rolls back all records cleanly
  22. Concurrency: Multithreaded concurrent synthesis runs serialize without collision
  23. Knowledge graph integration: Graph nodes referenced as constituents resolve cleanly
  24. Adjudication integration: Adjudication verdicts referenced as constituents resolve cleanly
  25. Migration 020 checksum locked
  26. Migrations 001–019 checksums strictly unchanged
  27. Legacy database strictly untouched
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
    SynthesisAuthorialDistinctiveViolationError,
    SynthesisCircularDependencyError,
    SynthesisConcurrencyError,
    SynthesisConfidenceInflationError,
    SynthesisEvidenceTierViolationError,
    SynthesisHarmonizationError,
    SynthesisImmutabilityError,
    SynthesisInvalidProvenanceError,
    SynthesisInvalidVersionError,
    SynthesisMissingConstituentError,
    SynthesisNotFoundError,
    SynthesisReceptionAuthorialFirewallError,
    SynthesisReverseScopeError,
    SynthesisScopeJumpError,
    SynthesisSubsystemError,
    SynthesisValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.synthesis import (
    ConstituentInput,
    HierarchicalSynthesisManager,
    SynthesisClaimInput,
    SynthesisClaimRecord,
    SynthesisClaimStatus,
    SynthesisConstituentRecord,
    SynthesisRunConfig,
    SynthesisRunRecord,
    SynthesisRunResult,
    SynthesisRunStatus,
    SynthesisScope,
    SynthesisTensionInput,
    SynthesisTensionRecord,
    SynthesisTensionResolution,
    SynthesisTensionType,
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
}

EXPECTED_020_CHECKSUM = "3f80d67d9567ea0775c593f663458d4a8892dd719a75d01d3bd39ac0c9fe1216"
LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"




class TestHierarchicalSynthesisEngine(unittest.TestCase):
    """Unit and Adversarial Test Suite for Hierarchical Synthesis Engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_synthesis.db"

        config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(config)
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.version_manager = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)
        self.synth_mgr = HierarchicalSynthesisManager(
            self.engine,
            self.version_manager,
            self.provenance_tracker,
        )

        # Baseline seed data for testing
        with self.engine.transaction() as conn:
            conn.execute("INSERT OR IGNORE INTO canons VALUES ('CANON_TEST', 'Test Canon', 'Desc', '2026-09-30');")
            conn.execute("INSERT OR IGNORE INTO testaments VALUES ('TEST_NT', 'CANON_TEST', 'New Testament', 1);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('ROM', 'TEST_NT', 45, 'Roma', 'Romans', 'GREEK', 16);")
            conn.execute("INSERT OR IGNORE INTO books VALUES ('JAS', 'TEST_NT', 59, 'Yakobus', 'James', 'GREEK', 5);")
            conn.execute("INSERT OR IGNORE INTO sections VALUES ('SEC-ROM-03', 'ROM', 'Righteousness by Faith', 3, 21, 3, 31, 'EPISTLE');")
            conn.execute("INSERT OR IGNORE INTO sections VALUES ('SEC-JAS-02', 'JAS', 'Faith and Works', 2, 14, 2, 26, 'EPISTLE');")
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-ROM-03-21-26', 'ROM', 'Roma 3:21-26', 3, 21, 3, 26,
                    'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO pericopes (
                    pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse,
                    genre, boundary_source, boundary_confidence, status, version, created_at
                ) VALUES (
                    'PER-JAS-02-14-26', 'JAS', 'Yakobus 2:14-26', 2, 14, 2, 26,
                    'EPISTLE', 'NA28', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30'
                );
                """
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO passages VALUES (
                    'ROM-03-24', 'PER-ROM-03-21-26', 'ROM', 3, 24, 100
                );
                """
            )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. SCOPE PROGRESSION & DIRECTIONALITY
    # -------------------------------------------------------------------------

    def test_01_valid_scope_hierarchy_pericope_to_section(self) -> None:
        """Valid scope progression: PERICOPE -> SECTION succeeds."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-SEC-ROM-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Justification by grace through faith in Christ.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.92,
                    is_critical_dependency=True,
                )
            ],
        )

        result = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        self.assertEqual(result.scope, SynthesisScope.SECTION)
        self.assertEqual(result.claims_created, 1)
        self.assertAlmostEqual(result.aggregate_confidence, 0.92)

        stored_claim = self.synth_mgr.get_synthesis_claim("CLM-SEC-ROM-01")
        self.assertEqual(stored_claim.scope, SynthesisScope.SECTION)
        self.assertAlmostEqual(stored_claim.synthesized_confidence, 0.92)

    def test_02_invalid_scope_jump_rejected(self) -> None:
        """Invalid scope jump: PERICOPE -> BOOK without intermediate SECTION is rejected."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-BK-ROM-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Justification thesis across Romans.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.90,
                )
            ],
        )

        with self.assertRaises(SynthesisScopeJumpError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.BOOK,
                target_id="ROM",
                claims=[claim_input],
                config=SynthesisRunConfig(enforce_strict_scope_hierarchy=True),
            )

    def test_03_permitted_pericope_to_book_under_explicit_config(self) -> None:
        """PERICOPE -> BOOK is permitted when allow_direct_pericope_to_book=True."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-BK-ROM-DIRECT",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Direct pericope to book synthesis.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.88,
                )
            ],
        )

        result = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.BOOK,
            target_id="ROM",
            claims=[claim_input],
            config=SynthesisRunConfig(
                enforce_strict_scope_hierarchy=True,
                allow_direct_pericope_to_book=True,
            ),
        )
        self.assertEqual(result.scope, SynthesisScope.BOOK)
        self.assertEqual(result.claims_created, 1)

    def test_04_reverse_scope_dependency_rejected(self) -> None:
        """Directionality Invariant: Higher scope cannot be constituent of lower scope."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-PER-REV-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Constituent from canon used to prove pericope.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.CANON,
                    constituent_target_id="CANON_TEST",
                    constituent_confidence=0.95,
                )
            ],
        )

        with self.assertRaises(SynthesisReverseScopeError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.PERICOPE,
                target_id="PER-ROM-03-21-26",
                claims=[claim_input],
            )

    def test_05_circular_synthesis_rejected(self) -> None:
        """Target attempting to consume itself as constituent is rejected as circular."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-CIRCULAR-01",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Self-feeding circular synthesis.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="ROM",
                    constituent_confidence=0.90,
                )
            ],
        )

        with self.assertRaises(SynthesisCircularDependencyError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.BOOK,
                target_id="ROM",
                claims=[claim_input],
            )

    def test_06_bottom_up_missing_constituent_rejected(self) -> None:
        """Claim with zero constituents is rejected as unsupported bottom-up derivation."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-UNSUPPORTED",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Claim fabricated without constituent evidence.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[],
        )

        with self.assertRaises(SynthesisMissingConstituentError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[claim_input],
            )

    # -------------------------------------------------------------------------
    # 2. ANTI-HARMONIZATION FIREWALL & AUTHORIAL DISTINCTIVES
    # -------------------------------------------------------------------------

    def test_07_forced_harmonization_without_tension_rejected(self) -> None:
        """Anti-Harmonization: Claim marked is_harmonized=True without TENSION status is rejected."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-FORCED-HARM",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Paul and James harmonized into single theological dogma.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Combined NT",
            is_harmonized=True,
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.90,
                )
            ],
        )

        with self.assertRaises(SynthesisHarmonizationError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[claim_input],
                config=SynthesisRunConfig(enforce_anti_harmonization=True),
            )

    def test_08_competing_claims_and_tensions_preserved(self) -> None:
        """Anti-Harmonization: Conflicting theological claims persist with explicit tension record."""
        claim_paul = SynthesisClaimInput(
            claim_id="CLM-PAUL-JUST",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Justification by faith apart from works of the Law (Roma 3:28).",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Pauline Corpus",
            is_harmonized=False,
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="ROM",
                    constituent_confidence=0.95,
                )
            ],
        )

        claim_james = SynthesisClaimInput(
            claim_id="CLM-JAMES-JUST",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="A person is justified by works and not by faith alone (Yakobus 2:24).",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Jamesian Corpus",
            is_harmonized=False,
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="JAS",
                    constituent_confidence=0.93,
                )
            ],
        )

        tension = SynthesisTensionInput(
            tension_id="TENS-PAUL-JAMES-01",
            tension_type=SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            primary_claim_id="CLM-PAUL-JUST",
            secondary_claim_id="CLM-JAMES-JUST",
            description="Linguistic and thematic disparity on 'faith' and 'works' terminology.",
            preservation_rationale="Paul uses 'works of the law' while James uses 'works of charity'; both voices must remain unharmonized.",
            resolution_status=SynthesisTensionResolution.PRESERVED_TENSION,
        )

        result = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.CORPUS,
            target_id="APOSTOLIC_EPISTLES",
            claims=[claim_paul, claim_james],
            tensions=[tension],
        )

        self.assertEqual(result.claims_created, 2)
        self.assertEqual(result.tensions_created, 1)

        tensions = self.synth_mgr.get_tensions_for_target(SynthesisScope.CORPUS, "APOSTOLIC_EPISTLES")
        self.assertEqual(len(tensions), 1)
        self.assertEqual(tensions[0].tension_id, "TENS-PAUL-JAMES-01")
        self.assertEqual(tensions[0].resolution_status, SynthesisTensionResolution.PRESERVED_TENSION)

    def test_09_authorial_divergence_requires_distinct_authors(self) -> None:
        """Authorial divergence tension connecting claims with identical author is rejected."""
        c1 = SynthesisClaimInput(
            claim_id="CLM-P1",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Paul claim 1",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.SECTION, "SEC-ROM-03", 0.9)],
        )
        c2 = SynthesisClaimInput(
            claim_id="CLM-P2",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Paul claim 2",
            epistemic_status=SynthesisClaimStatus.TENSION,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.SECTION, "SEC-ROM-03", 0.9)],
        )
        t = SynthesisTensionInput(
            tension_id="TENS-BAD-AUTH",
            tension_type=SynthesisTensionType.AUTHORIAL_DIVERGENCE,
            primary_claim_id="CLM-P1",
            secondary_claim_id="CLM-P2",
            description="Invalid authorial divergence within same author",
            preservation_rationale="test",
        )

        with self.assertRaises(SynthesisAuthorialDistinctiveViolationError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.BOOK,
                target_id="ROM",
                claims=[c1, c2],
                tensions=[t],
                config=SynthesisRunConfig(enforce_authorial_distinctives=True),
            )

    # -------------------------------------------------------------------------
    # 3. RECEPTION FIREWALL
    # -------------------------------------------------------------------------

    def test_10_reception_firewall_blocks_e11_e12_as_authorial_intent(self) -> None:
        """Reception Firewall: E11/E12 reception cannot be asserted as original authorial book/corpus theology."""
        claim_reception = SynthesisClaimInput(
            claim_id="CLM-PATRISTIC-INTENT",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            primary_evidence_class=EvidenceClass.E11_EARLY_RECEPTION,
            claim_text="Fourth-century Nicene consensus asserted as author's intent.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",  # Omits 'RECEPTION'
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="ROM",
                    constituent_confidence=0.85,
                )
            ],
        )

        with self.assertRaises(SynthesisReceptionAuthorialFirewallError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.CORPUS,
                target_id="PAULINE",
                claims=[claim_reception],
                config=SynthesisRunConfig(enforce_reception_firewall=True),
            )

    def test_11_reception_accepted_when_tagged_as_reception_history(self) -> None:
        """Reception Firewall: E11/E12 accepted when authorial_context indicates reception history."""
        claim_reception = SynthesisClaimInput(
            claim_id="CLM-PATRISTIC-VALID",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E11_EARLY_RECEPTION,
            claim_text="Augustinian reception of grace in Romans 3.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Patristic Reception History",  # Explicitly declares RECEPTION
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="ROM",
                    constituent_confidence=0.85,
                )
            ],
        )

        result = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.CORPUS,
            target_id="PAULINE",
            claims=[claim_reception],
            config=SynthesisRunConfig(enforce_reception_firewall=True),
        )
        self.assertEqual(result.claims_created, 1)

    # -------------------------------------------------------------------------
    # 4. WEAKEST-LINK CONFIDENCE PROPAGATION
    # -------------------------------------------------------------------------

    def test_12_weakest_link_confidence_propagation(self) -> None:
        """Confidence propagation: Synthesis claim confidence equals weakest critical constituent."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-WEAK-PROP",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Multi-constituent lexical synthesis.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.95, is_critical_dependency=True),
                ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.65, is_critical_dependency=True),
                ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.90, is_critical_dependency=False),
            ],
        )

        result = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        stored_claim = self.synth_mgr.get_synthesis_claim("CLM-WEAK-PROP")
        self.assertAlmostEqual(stored_claim.synthesized_confidence, 0.65)
        self.assertAlmostEqual(stored_claim.weakest_constituent_confidence, 0.65)
        self.assertAlmostEqual(result.aggregate_confidence, 0.65)

    def test_13_confidence_inflation_above_weakest_link_rejected(self) -> None:
        """Confidence Inflation: Explicit confidence higher than weakest critical constituent is rejected."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-INFLATED",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Inflated confidence claim.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            explicit_confidence=0.85,
            constituents=[
                ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.60, is_critical_dependency=True),
            ],
        )

        with self.assertRaises(SynthesisConfidenceInflationError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[claim_input],
            )

    def test_14_out_of_bounds_confidence_rejected(self) -> None:
        """Constituent confidence outside [0.0, 1.0] is rejected."""
        with self.assertRaises(SynthesisConfidenceInflationError):
            claim_input = SynthesisClaimInput(
                claim_id="CLM-OOB",
                claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
                primary_evidence_class=EvidenceClass.E3_SYNTAX,
                claim_text="OOB confidence",
                epistemic_status=SynthesisClaimStatus.CONVERGENT,
                authorial_context="Pauline Corpus",
                constituents=[
                    ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 1.25),
                ],
            )
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[claim_input],
            )

    # -------------------------------------------------------------------------
    # 5. EVIDENCE TIERS & IMMUTABILITY
    # -------------------------------------------------------------------------

    def test_15_evidence_tiers_preserved_across_scopes(self) -> None:
        """Evidence classes and claim tiers are preserved verbatim across scope rollup."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-TIER-PRESERVE",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            primary_evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            claim_text="Autograph textual reading at Section scope.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.98),
            ],
        )

        self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        claim = self.synth_mgr.get_synthesis_claim("CLM-TIER-PRESERVE")
        self.assertEqual(claim.claim_tier, ClaimTier.T1_LINGUISTIC_FACT)
        self.assertEqual(claim.primary_evidence_class, EvidenceClass.E0_DIRECT_TEXT)

    def test_16_immutability_triggers_block_update_and_delete(self) -> None:
        """Immutability: Direct SQL UPDATE and DELETE on synthesis tables are blocked by triggers."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-IMMUT-01",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Immutable claim.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.9)],
        )

        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        with self.engine.transaction() as conn:
            # Direct UPDATE on synthesis_runs blocked
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE synthesis_runs SET aggregate_confidence = 1.0 WHERE run_id = ?", (res.run_id,))

            # Direct DELETE on synthesis_runs blocked
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM synthesis_runs WHERE run_id = ?", (res.run_id,))

            # Direct UPDATE on synthesis_claims blocked
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE synthesis_claims SET claim_text = 'Tampered' WHERE claim_id = ?", ("CLM-IMMUT-01",))

            # Direct DELETE on synthesis_claims blocked
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM synthesis_claims WHERE claim_id = ?", ("CLM-IMMUT-01",))

            # Direct UPDATE on synthesis_constituents blocked
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE synthesis_constituents SET constituent_confidence = 1.0 WHERE claim_id = ?", ("CLM-IMMUT-01",))

    def test_17_valid_supersession(self) -> None:
        """Valid status transition to SUPERSEDED is permitted by immutability triggers."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-SUPERSEDE-01",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Supersession test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.85)],
        )

        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        self.synth_mgr.supersede_synthesis_run(res.run_id, "New evidence available")
        run = self.synth_mgr.get_synthesis_run(res.run_id)
        self.assertEqual(run.status, SynthesisRunStatus.SUPERSEDED)

        self.synth_mgr.supersede_synthesis_claim("CLM-SUPERSEDE-01", "Updated exegesis")
        claim = self.synth_mgr.get_synthesis_claim("CLM-SUPERSEDE-01")
        self.assertEqual(claim.epistemic_status, SynthesisClaimStatus.SUPERSEDED)

    # -------------------------------------------------------------------------
    # 6. TRANSACTIONS, PROVENANCE, & CONCURRENCY
    # -------------------------------------------------------------------------

    def test_18_atomic_transaction_rollback_on_failure(self) -> None:
        """Transaction Safety: Failure during constituent/tension insertion rolls back entire run."""
        c1 = SynthesisClaimInput(
            claim_id="CLM-ATOMIC-OK",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="OK claim",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.9)],
        )
        # Tension referencing non-existent claim to trigger failure
        bad_tension = SynthesisTensionInput(
            tension_id="TENS-FAIL",
            tension_type=SynthesisTensionType.GENRE_DISPARITY,
            primary_claim_id="CLM-ATOMIC-OK",
            secondary_claim_id="CLM-NONEXISTENT",
            description="Fail",
            preservation_rationale="Fail",
        )

        with self.assertRaises(SynthesisNotFoundError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[c1],
                tensions=[bad_tension],
                run_id="SYNTH-ATOMIC-FAIL",
            )

        with self.assertRaises(SynthesisNotFoundError):
            self.synth_mgr.get_synthesis_run("SYNTH-ATOMIC-FAIL")

        claims = self.synth_mgr.get_claims_for_target(SynthesisScope.SECTION, "SEC-ROM-03")
        self.assertEqual(len(claims), 0)

    def test_19_provenance_and_versioning_integration(self) -> None:
        """Complete provenance and version records trace every synthesis run, claim, tension."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-PROV-01",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Provenance traceability test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.91)],
        )

        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )

        run = self.synth_mgr.get_synthesis_run(res.run_id)
        prov = self.provenance_tracker.get_record(run.provenance_id)
        self.assertIsNotNone(prov)
        self.assertEqual(prov.target_id, res.run_id)

        ver = self.version_manager.get_version(run.version_id)
        self.assertIsNotNone(ver)
        self.assertEqual(ver.object_id, res.run_id)

    def test_20_multithreaded_concurrency_safety(self) -> None:
        """Concurrency: Multiple threads synthesizing distinct targets complete cleanly."""
        def synthesize_section(sec_idx: int) -> SynthesisRunResult:
            cfg = DatabaseConfig(db_path=str(self.db_path))
            eng = DatabaseEngine(cfg)
            vm = VersionManager(eng)
            pt = ProvenanceTracker(eng)
            mgr = HierarchicalSynthesisManager(eng, vm, pt)

            sec_id = f"SEC-TEST-{sec_idx}"
            c = SynthesisClaimInput(
                claim_id=f"CLM-CONCUR-{sec_idx}",
                claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
                primary_evidence_class=EvidenceClass.E3_SYNTAX,
                claim_text=f"Concurrent claim {sec_idx}",
                epistemic_status=SynthesisClaimStatus.CONVERGENT,
                authorial_context="Test Author",
                constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.85)],
            )
            res = mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id=sec_id,
                claims=[c],
            )
            eng.close()
            return res

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(synthesize_section, i) for i in range(4)]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), 4)
        for r in results:
            self.assertEqual(r.status, SynthesisRunStatus.COMPLETED)

    # -------------------------------------------------------------------------
    # 7. REGRESSION, CHECKSUMS, & LEGACY DATABASE
    # -------------------------------------------------------------------------

    def test_21_migration_020_checksum_locked(self) -> None:
        """Migration 020 checksum is locked and deterministic."""
        m_file = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine" / "020_hierarchical_synthesis.sql"
        self.assertTrue(m_file.exists())
        content = m_file.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        self.assertEqual(actual, EXPECTED_020_CHECKSUM)

    def test_22_migrations_001_to_019_strictly_unchanged(self) -> None:
        """Migrations 001–019 checksums remain strictly unchanged."""
        base_dir = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"
        for fname, exp_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            fpath = base_dir / fname
            self.assertTrue(fpath.exists(), f"Missing migration file: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, exp_hash, f"Checksum mismatch in frozen migration: {fname}")

    def test_23_legacy_database_strictly_untouched(self) -> None:
        """Legacy knowledge base at /home/ubuntu/.polya/polya_index.db remains strictly untouched."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_hash = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, LEGACY_DB_SHA256)

    def test_24_graph_node_constituent_integration(self) -> None:
        """Graph Integration: Constituent referencing graph node persists and resolves cleanly."""
        p_rec = self.provenance_tracker.record_origin(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id="GR-TEST-01",
            content="graph test content",
        )
        v_rec = self.version_manager.create_version(
            object_type="GRAPH",
            object_id="GR-TEST-01",
            content="graph test content",
            change_reason=ChangeReason.INITIAL_CREATION,
        )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO graph_runs (
                    run_id, version_id, provenance_id, graph_builder_id,
                    graph_builder_version, configuration_hash, input_content_hash,
                    output_hash, status, is_exact_reproducible, created_at,
                    is_immutable, metadata_json
                ) VALUES (
                    'GR-TEST-01', ?, ?, 'BUILDER-01',
                    '2.0.0', 'CFG-HASH', 'INP-HASH', 'OUT-HASH', 'COMPLETED',
                    1, '2026-10-01T00:00:00Z', 1, NULL
                );
                """,
                (v_rec.version_id, p_rec.provenance_id),
            )
            conn.execute(
                """
                INSERT INTO graph_nodes (
                    node_id, run_id, node_type, reference_id, label,
                    base_confidence, status, provenance_id, version_id,
                    created_at, is_immutable, metadata_json
                ) VALUES (
                    'GNOD-TEST-01', 'GR-TEST-01', 'CLAIM', 'REF-01', 'Graph Claim Node',
                    0.92, 'ACTIVE', ?, ?,
                    '2026-10-01T00:00:00Z', 1, NULL
                );
                """,
                (p_rec.provenance_id, v_rec.version_id),
            )

        claim_input = SynthesisClaimInput(
            claim_id="CLM-GRAPH-INTEG",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Claim backed by graph node.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.92,
                    constituent_graph_node_id="GNOD-TEST-01",
                )
            ],
        )

        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )
        self.assertEqual(res.status, SynthesisRunStatus.COMPLETED)
        constituents = self.synth_mgr.get_constituents_for_claim("CLM-GRAPH-INTEG")
        self.assertEqual(len(constituents), 1)
        self.assertEqual(constituents[0].constituent_graph_node_id, "GNOD-TEST-01")

    def test_25_adjudication_verdict_constituent_integration(self) -> None:
        """Adjudication Integration: Constituent referencing adjudication verdict persists cleanly."""
        p_rec = self.provenance_tracker.record_origin(
            target_type=TargetType.DERIVED_ARTIFACT,
            target_id="ADJ-TEST-01",
            content="adjudication test content",
        )
        v_rec = self.version_manager.create_version(
            object_type="ADJUDICATION",
            object_id="ADJ-TEST-01",
            content="adjudication test content",
            change_reason=ChangeReason.INITIAL_CREATION,
        )

        with self.engine.transaction() as conn:
            conn.execute(
                """
                INSERT INTO adjudication_runs (
                    run_id, target_pericope_id, version_id, provenance_id,
                    adjudicator_id, adjudicator_version, configuration_hash,
                    input_content_hash, output_hash, status, is_exact_reproducible,
                    created_at, is_immutable, metadata_json
                ) VALUES (
                    'ADJ-TEST-01', 'PER-ROM-03-21-26', ?, ?,
                    'ADJ-01', '2.0.0', 'CFG-HASH', 'INP-HASH', 'OUT-HASH',
                    'COMPLETED', 1, '2026-10-01T00:00:00Z', 1, NULL
                );
                """,
                (v_rec.version_id, p_rec.provenance_id),
            )
            conn.execute(
                """
                INSERT INTO adjudication_hypotheses (
                    hypothesis_id, run_id, pericope_id, hypothesis_code, title,
                    description, claim_tier, base_confidence, propagated_confidence,
                    confidence_level, status, provenance_id, version_id,
                    created_at, is_immutable, metadata_json
                ) VALUES (
                    'HYP-TEST-01', 'ADJ-TEST-01', 'PER-ROM-03-21-26', 'H-01', 'Hypothesis 1',
                    'Desc', 'T2_CONTEXTUAL_CLAIM', 0.88, 0.88,
                    'HIGH', 'ACTIVE', ?, ?,
                    '2026-10-01T00:00:00Z', 1, NULL
                );
                """,
                (p_rec.provenance_id, v_rec.version_id),
            )
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
                    'VRD-TEST-01', 'ADJ-TEST-01', 'HYP-TEST-01', 'PROBABLE_CONCLUSION',
                    'T2_CONTEXTUAL_CLAIM', 0.88, NULL, 0.88,
                    1, 0, 0, 0, 0, 0, 1, 'Well supported', ?, ?,
                    '2026-10-01T00:00:00Z', 1, NULL
                );
                """,
                (p_rec.provenance_id, v_rec.version_id),
            )

        claim_input = SynthesisClaimInput(
            claim_id="CLM-ADJ-INTEG",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Claim backed by adjudication verdict.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.88,
                    constituent_adjudication_verdict_id="VRD-TEST-01",
                )
            ],
        )

        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )
        self.assertEqual(res.status, SynthesisRunStatus.COMPLETED)
        constituents = self.synth_mgr.get_constituents_for_claim("CLM-ADJ-INTEG")
        self.assertEqual(len(constituents), 1)
        self.assertEqual(constituents[0].constituent_adjudication_verdict_id, "VRD-TEST-01")

    def test_26_duplicate_claim_id_in_batch_rejected(self) -> None:
        """Batch validation: Duplicate claim_id in synthesis batch is rejected before DB insert."""
        c1 = SynthesisClaimInput(
            claim_id="CLM-DUP-ID",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Claim A",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.88)],
        )
        c2 = SynthesisClaimInput(
            claim_id="CLM-DUP-ID",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Claim B (duplicate ID)",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.88)],
        )
        with self.assertRaises(SynthesisValidationError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[c1, c2],
            )

    def test_27_supersession_non_completed_run_rejected(self) -> None:
        """Immutability: Attempting to supersede non-COMPLETED run raises SynthesisImmutabilityError."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-SUP-FAIL",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Supersession non-completed run test.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.85)],
        )
        res = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-03",
            claims=[claim_input],
        )
        # Supersede once to make status SUPERSEDED
        self.synth_mgr.supersede_synthesis_run(res.run_id, "First supersession")
        # Attempting second supersession on non-COMPLETED run must raise SynthesisImmutabilityError
        with self.assertRaises(SynthesisImmutabilityError):
            self.synth_mgr.supersede_synthesis_run(res.run_id, "Second supersession attempt")

    def test_28_non_critical_constituents_bound_confidence(self) -> None:
        """Confidence propagation: When no constituents are marked critical, confidence is bounded by min(all_confidences)."""
        claim_input = SynthesisClaimInput(
            claim_id="CLM-NON-CRITICAL",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="Non-critical constituent confidence check.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.65,
                    is_critical_dependency=False,
                ),
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-27-31",
                    constituent_confidence=0.85,
                    is_critical_dependency=False,
                ),
            ],
            explicit_confidence=0.90,  # Exceeds 0.65 min
        )
        with self.assertRaises(SynthesisConfidenceInflationError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[claim_input],
            )

    def test_29_target_queries_exclude_superseded_runs(self) -> None:
        """Target queries: get_claims_for_target excludes claims from superseded runs when include_superseded=False."""
        c1 = SynthesisClaimInput(
            claim_id="CLM-QUERY-SUP-1",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Run 1 claim",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.85)],
        )
        run1 = self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-QUERY-TEST",
            claims=[c1],
        )
        self.synth_mgr.supersede_synthesis_run(run1.run_id, "Superseded by run 2")

        c2 = SynthesisClaimInput(
            claim_id="CLM-QUERY-SUP-2",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Run 2 claim",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[ConstituentInput(SynthesisScope.PERICOPE, "PER-ROM-03-21-26", 0.90)],
        )
        self.synth_mgr.create_synthesis_run(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-QUERY-TEST",
            claims=[c2],
        )

        active_claims = self.synth_mgr.get_claims_for_target(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-QUERY-TEST",
            include_superseded=False,
        )
        self.assertEqual(len(active_claims), 1)
        self.assertEqual(active_claims[0].claim_id, "CLM-QUERY-SUP-2")

        all_claims = self.synth_mgr.get_claims_for_target(
            scope=SynthesisScope.SECTION,
            target_id="SEC-ROM-QUERY-TEST",
            include_superseded=True,
        )
        self.assertEqual(len(all_claims), 2)

    def test_30_equal_scope_constituent_rejected(self) -> None:
        """Directionality Invariant: Constituent at equal scope is rejected with SynthesisReverseScopeError."""
        c = SynthesisClaimInput(
            claim_id="CLM-EQUAL-SCOPE",
            claim_tier=ClaimTier.T3_INTERPRETIVE_CLAIM,
            primary_evidence_class=EvidenceClass.E7_BOOK_CONTEXT,
            claim_text="Book depending horizontally on Book.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.BOOK,
                    constituent_target_id="GAL",
                    constituent_confidence=0.88,
                )
            ],
        )
        with self.assertRaises(SynthesisReverseScopeError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.BOOK,
                target_id="ROM",
                claims=[c],
                config=SynthesisRunConfig(enforce_strict_scope_hierarchy=False),
            )

    def test_31_nonexistent_constituent_claim_rejected(self) -> None:
        """Missing constituent: Nonexistent constituent_claim_id raises SynthesisNotFoundError."""
        c = SynthesisClaimInput(
            claim_id="CLM-MISSING-CLAIM-ID",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            primary_evidence_class=EvidenceClass.E4_LEXICAL,
            claim_text="Claim referencing fake constituent claim.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            authorial_context="Pauline Corpus",
            constituents=[
                ConstituentInput(
                    constituent_scope=SynthesisScope.PERICOPE,
                    constituent_target_id="PER-ROM-03-21-26",
                    constituent_confidence=0.85,
                    constituent_claim_id="NONEXISTENT-CLAIM-XYZ",
                )
            ],
        )
        with self.assertRaises(SynthesisNotFoundError):
            self.synth_mgr.create_synthesis_run(
                scope=SynthesisScope.SECTION,
                target_id="SEC-ROM-03",
                claims=[c],
            )


if __name__ == "__main__":
    unittest.main()
