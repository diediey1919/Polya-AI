"""
Test Suite for Evidence & Claim Foundation Subsystem (Task 2.8).
Specification: Architecture v2.0 — FROZEN.

Verifies:
  - Evidence records, claim records, evidence-to-claim links
  - Required evidence classes: E0 through E12
  - Required claim tiers: T0 through T4
  - Required epistemic types: RAW_OBSERVATION through THEOLOGICAL_CLAIM
  - Required relationships: SUPPORT, CONTRADICT, QUALIFY, LIMIT, REFINE
  - Epistemic Firewalls:
      * Invalid E-level / T-level / Epistemic type rejected
      * Translation cannot become E0 DIRECT_TEXT
      * AI output cannot become primary evidence (E0-E1)
      * Confidence cannot create evidence / upgrade claim tier / establish theology / historical fact
      * Morphology cannot directly create theological claim
      * Syntax cannot directly create theological claim
      * Semantic sense cannot directly create theological claim
      * Discourse cannot directly create theological claim
      * Entity association cannot directly create STRICT_IDENTITY
      * Unsupported claim rejected
      * Missing provenance rejected
      * Counter-evidence & contradictory evidence preserved
      * Unresolved contradiction preserved / cannot be marked VERIFIED_FACT
      * Weakest-critical-dependency confidence propagation
  - Immutability triggers on evidence, claims, links, and runs
  - Transactional rollback and concurrency safety
  - Migration checksum 001-011 verification
  - Legacy DB SHA-256 integrity verification
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AIPrimaryEvidenceFirewallError,
    ClaimEvidenceLinkNotFoundError,
    ClaimNotFoundError,
    ConfidenceUpgradeFirewallError,
    DiscourseTheologyFirewallError,
    DuplicateClaimError,
    DuplicateClaimEvidenceLinkError,
    DuplicateEvidenceError,
    EvidenceClaimImmutabilityError,
    EvidenceClaimInvalidProvenanceError,
    EvidenceClaimInvalidVersionError,
    EvidenceClaimOrphanError,
    EvidenceConfidenceError,
    EvidenceNotFoundError,
    IdentityFirewallError,
    InvalidClaimTierError,
    InvalidEpistemicTypeError,
    InvalidEvidenceClassError,
    InvalidEvidenceRelationshipError,
    MorphologyTheologyFirewallError,
    SemanticTheologyFirewallError,
    SyntaxTheologyFirewallError,
    TranslationToE0FirewallError,
    UnresolvedContradictionFirewallError,
    UnsupportedClaimError,
)
from bible_engine.evidence_claim import (
    ClaimDefinition,
    ClaimEvidenceLinkDefinition,
    ClaimTier,
    ConfidenceLevel,
    EpistemicStatus,
    EpistemicType,
    EvidenceClaimConfig,
    EvidenceClaimManager,
    EvidenceClass,
    EvidenceDefinition,
    EvidenceRelationship,
    EvidenceStatus,
    coerce_claim_tier,
    coerce_confidence_level,
    coerce_epistemic_type,
    coerce_evidence_class,
    coerce_evidence_relationship,
    compute_evidence_claim_output_hash,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker
from bible_engine.source_registry import (
    SourceAuthorityLevel,
    SourceLanguage,
    SourceRegistry,
    SourceType,
)
from bible_engine.source_text import (
    RepresentationType,
    SourceTextLanguage,
    SourceTextManager,
    SourceTextRecord,
)
from bible_engine.tokenization import TokenizationManager, TokenRecord
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
}

LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestBibleEngineEvidenceClaim(unittest.TestCase):
    """Rigorous adversarial test suite for the Evidence & Claim Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_evidence_claim.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Scaffolding required by foreign keys
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
                "VALUES ('PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, "
                "'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'VALIDATED', '2.0.0', '2026-10-01');"
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.ev_mgr = EvidenceClaimManager(self.engine)

        # Register source text and tokens
        self.source_registry.register_source(
            source_id="SRC-NA28-REV",
            canonical_name="Novum Testamentum Graece 28 - Revelation",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )

        st = self.source_text_mgr.register_source_text(
            source_id="SRC-NA28-REV",
            source_text_id="ST-NA28-REV-19-08",
            language=SourceTextLanguage.GREEK,
            raw_content="ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον λαμπρὸν καθαρόν",
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )
        self.source_text_id = st.source_text_id

        tok_res = self.token_mgr.tokenize_source_text(st, passage_id="REV-19-08")
        self.tokens = tok_res.tokens
        self.tokenization_id = tok_res.run.tokenization_id

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. TAXONOMY & ENUM ADVERSARIAL VALIDATIONS
    # -------------------------------------------------------------------------

    def test_invalid_evidence_class_rejected(self) -> None:
        """Invalid E-level string must be rejected."""
        with self.assertRaises(InvalidEvidenceClassError):
            coerce_evidence_class("E99_NONEXISTENT")
        with self.assertRaises(InvalidEvidenceClassError):
            coerce_evidence_class("INVALID_CLASS")

        ev = EvidenceDefinition(
            evidence_id="EV-INV-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class="E99_INVALID",
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
        )
        with self.assertRaises(InvalidEvidenceClassError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[],
                link_defs=[],
            )

    def test_invalid_claim_tier_rejected(self) -> None:
        """Invalid T-level string must be rejected."""
        with self.assertRaises(InvalidClaimTierError):
            coerce_claim_tier("T9_ULTIMATE_TRUTH")
        with self.assertRaises(InvalidClaimTierError):
            coerce_claim_tier("DOGMATIC_TIER")

        cl = ClaimDefinition(
            claim_id="CLM-INV-01",
            pericope_id="PER-REV-19",
            claim_tier="T9_INVALID",
            epistemic_type=EpistemicType.RAW_OBSERVATION,
            claim_text="Invalid tier claim",
            claimed_by="TEST",
        )
        with self.assertRaises(InvalidClaimTierError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[],
                claim_defs=[cl],
                link_defs=[],
            )

    def test_invalid_epistemic_type_rejected(self) -> None:
        """Invalid epistemic type must be rejected."""
        with self.assertRaises(InvalidEpistemicTypeError):
            coerce_epistemic_type("INFALLIBLE_REVELATION")
        with self.assertRaises(InvalidEpistemicTypeError):
            coerce_epistemic_type("SPECULATION")

        cl = ClaimDefinition(
            claim_id="CLM-INV-02",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type="UNKNOWN_EPISTEMIC",
            claim_text="Invalid type claim",
            claimed_by="TEST",
        )
        with self.assertRaises(InvalidEpistemicTypeError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[],
                claim_defs=[cl],
                link_defs=[],
            )

    # -------------------------------------------------------------------------
    # 2. EPISTEMIC FIREWALLS
    # -------------------------------------------------------------------------

    def test_translation_cannot_become_e0(self) -> None:
        """Translation output cannot become E0 DIRECT_TEXT."""
        ev = EvidenceDefinition(
            evidence_id="EV-TRANS-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="LAI-TB",
            extracted_text_or_data="kepadanya dikaruniakan",
            is_translation_derived=True,
        )
        with self.assertRaises(TranslationToE0FirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[],
                link_defs=[],
            )

    def test_ai_output_cannot_become_primary_evidence(self) -> None:
        """AI output is never automatically E0-E12 primary evidence (E0-E1)."""
        ev_e0 = EvidenceDefinition(
            evidence_id="EV-AI-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="LLM_GENERATED",
            extracted_text_or_data="hypothetical text",
            is_ai_generated=True,
        )
        with self.assertRaises(AIPrimaryEvidenceFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev_e0],
                claim_defs=[],
                link_defs=[],
            )

        ev_e1 = EvidenceDefinition(
            evidence_id="EV-AI-02",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="LLM_MSS_GUESS",
            extracted_text_or_data="conjectural reading",
            is_ai_generated=True,
        )
        with self.assertRaises(AIPrimaryEvidenceFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev_e1],
                claim_defs=[],
                link_defs=[],
            )

    def test_confidence_cannot_create_evidence_or_upgrade_tier(self) -> None:
        """Model confidence score cannot upgrade claim tier or establish theology."""
        # 1. High confidence cannot make a T4 claim VERIFIED_FACT
        ev = EvidenceDefinition(
            evidence_id="EV-E0-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="ἐδόθη",
        )
        cl = ClaimDefinition(
            claim_id="CLM-UPGRADE-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            epistemic_type=EpistemicType.THEOLOGICAL_CLAIM,
            claim_text="Absolute theological dogma established as verified fact",
            claimed_by="DOGMATIC_USER",
            epistemic_status=EpistemicStatus.VERIFIED_FACT,
            confidence_score=0.99,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-01",
            claim_id="CLM-UPGRADE-01",
            evidence_id="EV-E0-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Attempting to establish theology as fact by confidence",
        )
        with self.assertRaises(ConfidenceUpgradeFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_morphology_cannot_create_theological_claim(self) -> None:
        """Morphology alone cannot directly create T3/T4 claims."""
        ev = EvidenceDefinition(
            evidence_id="EV-MORPH-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E2_MORPHOLOGY,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="NA28 Morph",
            extracted_text_or_data="Aorist Passive 3S",
        )
        cl = ClaimDefinition(
            claim_id="CLM-THEO-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            epistemic_type=EpistemicType.THEOLOGICAL_CLAIM,
            claim_text="The passive verb proves divine monergism doctrine",
            claimed_by="SYSTEMATICIAN",
            epistemic_status=EpistemicStatus.POSSIBLE_INTERPRETATION,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-THEO-01",
            claim_id="CLM-THEO-01",
            evidence_id="EV-MORPH-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Deriving dogma directly from verbal voice alone",
        )
        with self.assertRaises(MorphologyTheologyFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_syntax_cannot_create_theological_claim(self) -> None:
        """Syntax alone cannot directly create T3/T4 claims."""
        ev = EvidenceDefinition(
            evidence_id="EV-SYN-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E3_SYNTAX,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Clause Dep Tree",
            extracted_text_or_data="Subject-Verb Agreement",
        )
        cl = ClaimDefinition(
            claim_id="CLM-THEO-SYN-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            epistemic_type=EpistemicType.THEOLOGICAL_CLAIM,
            claim_text="Syntactic dependency proves ontological hierarchy",
            claimed_by="SYSTEMATICIAN",
            epistemic_status=EpistemicStatus.POSSIBLE_INTERPRETATION,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-SYN-01",
            claim_id="CLM-THEO-SYN-01",
            evidence_id="EV-SYN-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Deriving dogma directly from syntax alone",
        )
        with self.assertRaises(SyntaxTheologyFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_semantic_sense_cannot_create_theological_claim(self) -> None:
        """Semantic sense alone cannot directly create T3/T4 claims."""
        ev = EvidenceDefinition(
            evidence_id="EV-SEM-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E4_LEXICAL,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="BDAG sense 1",
            extracted_text_or_data="fine linen = righteous deeds",
        )
        cl = ClaimDefinition(
            claim_id="CLM-THEO-SEM-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            epistemic_type=EpistemicType.THEOLOGICAL_CLAIM,
            claim_text="Lexical gloss establishes sacramental justification doctrine",
            claimed_by="SYSTEMATICIAN",
            epistemic_status=EpistemicStatus.POSSIBLE_INTERPRETATION,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-SEM-01",
            claim_id="CLM-THEO-SEM-01",
            evidence_id="EV-SEM-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Deriving dogma directly from lexical sense alone",
        )
        with self.assertRaises(SemanticTheologyFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_discourse_cannot_create_theological_claim(self) -> None:
        """Discourse relation cannot directly create T3/T4 claims."""
        ev = EvidenceDefinition(
            evidence_id="EV-DISC-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E5_DISCOURSE,
            epistemic_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            source_reference="Discourse Segment 1",
            extracted_text_or_data="Elaboration relation",
        )
        cl = ClaimDefinition(
            claim_id="CLM-THEO-DISC-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,
            epistemic_type=EpistemicType.THEOLOGICAL_CLAIM,
            claim_text="Discourse elaboration establishes eschatological timing",
            claimed_by="SYSTEMATICIAN",
            epistemic_status=EpistemicStatus.POSSIBLE_INTERPRETATION,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-DISC-01",
            claim_id="CLM-THEO-DISC-01",
            evidence_id="EV-DISC-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Deriving dogma directly from discourse alone",
        )
        with self.assertRaises(DiscourseTheologyFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_entity_association_cannot_directly_create_strict_identity(self) -> None:
        """Entity association cannot directly create STRICT_IDENTITY."""
        ev = EvidenceDefinition(
            evidence_id="EV-ASSOC-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E4_LEXICAL,
            epistemic_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            source_reference="Metaphorical link",
            extracted_text_or_data="fine linen symbol",
        )
        cl = ClaimDefinition(
            claim_id="CLM-IDENT-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            epistemic_type=EpistemicType.INFERENCE,
            claim_text="Symbolic linen is in STRICT_IDENTITY with believers",
            claimed_by="INTERPRETER",
            epistemic_status=EpistemicStatus.POSSIBLE_INTERPRETATION,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-IDENT-01",
            claim_id="CLM-IDENT-01",
            evidence_id="EV-ASSOC-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Promoting association to strict identity",
        )
        with self.assertRaises(IdentityFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl],
                link_defs=[lk],
            )

    def test_unsupported_claim_rejected(self) -> None:
        """A claim asserting verified fact or strong inference without supporting evidence is rejected."""
        cl = ClaimDefinition(
            claim_id="CLM-UNSUPP-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="Unsubstantiated grammatical claim",
            claimed_by="ANONYMOUS",
            epistemic_status=EpistemicStatus.VERIFIED_FACT,
        )
        with self.assertRaises(UnsupportedClaimError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[],
                claim_defs=[cl],
                link_defs=[],
            )

    def test_missing_provenance_rejected(self) -> None:
        """Missing or invalid provenance id must be rejected."""
        ev = EvidenceDefinition(
            evidence_id="EV-PROV-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
        )
        with self.assertRaises(EvidenceClaimInvalidProvenanceError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[],
                link_defs=[],
                provenance_id="NONEXISTENT-PROVENANCE",
            )

    # -------------------------------------------------------------------------
    # 3. COUNTER-EVIDENCE & UNCERTAINTY PRESERVATION
    # -------------------------------------------------------------------------

    def test_counter_evidence_and_contradiction_preserved(self) -> None:
        """Counter-evidence must be representable independently and linked."""
        ev_supp = EvidenceDefinition(
            evidence_id="EV-READING-A",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Codex Sinaiticus",
            extracted_text_or_data="dikaiomata",
        )
        ev_contra = EvidenceDefinition(
            evidence_id="EV-READING-B",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Minuscule 2053",
            extracted_text_or_data="dikaioma (singular)",
            is_counter_evidence=True,
        )
        cl = ClaimDefinition(
            claim_id="CLM-VAR-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="The plural form dikaiomata is original",
            claimed_by="SCHOLAR",
            epistemic_status=EpistemicStatus.PROVISIONAL,
            is_unresolved_contradiction=True,
        )
        lk_supp = ClaimEvidenceLinkDefinition(
            link_id="LK-VAR-01",
            claim_id="CLM-VAR-01",
            evidence_id="EV-READING-A",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Major uncial support",
        )
        lk_contra = ClaimEvidenceLinkDefinition(
            link_id="LK-VAR-02",
            claim_id="CLM-VAR-01",
            evidence_id="EV-READING-B",
            relationship=EvidenceRelationship.CONTRADICT,
            reasoning="Variant singular reading",
        )

        res = self.ev_mgr.record_evidence_and_claims(
            source_text_id=self.source_text_id,
            evidence_defs=[ev_supp, ev_contra],
            claim_defs=[cl],
            link_defs=[lk_supp, lk_contra],
        )

        self.assertEqual(len(res.evidence_records), 2)
        self.assertTrue(res.claim_records[0].has_counter_evidence)
        self.assertTrue(res.claim_records[0].is_unresolved_contradiction)

        counter_evs = self.ev_mgr.get_counter_evidence_for_claim("CLM-VAR-01")
        self.assertEqual(len(counter_evs), 1)
        self.assertEqual(counter_evs[0][1].evidence_id, "EV-READING-B")

    def test_unresolved_contradiction_cannot_be_marked_verified_fact(self) -> None:
        """A claim with unresolved contradiction must not be marked established/VERIFIED_FACT."""
        ev_supp = EvidenceDefinition(
            evidence_id="EV-S-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="βύσσινον",
        )
        ev_contra = EvidenceDefinition(
            evidence_id="EV-C-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="Codex Alexandrinus",
            extracted_text_or_data="omits βύσσινον",
            is_counter_evidence=True,
        )
        cl = ClaimDefinition(
            claim_id="CLM-CONTRADICTED-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="The word is indisputably genuine without doubt",
            claimed_by="SCHOLAR",
            epistemic_status=EpistemicStatus.VERIFIED_FACT,
            is_unresolved_contradiction=True,
        )
        lk_supp = ClaimEvidenceLinkDefinition(
            link_id="LK-S-01",
            claim_id="CLM-CONTRADICTED-01",
            evidence_id="EV-S-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="NA28 text",
        )
        lk_contra = ClaimEvidenceLinkDefinition(
            link_id="LK-C-01",
            claim_id="CLM-CONTRADICTED-01",
            evidence_id="EV-C-01",
            relationship=EvidenceRelationship.CONTRADICT,
            reasoning="Manuscript omission",
        )

        with self.assertRaises(UnresolvedContradictionFirewallError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev_supp, ev_contra],
                claim_defs=[cl],
                link_defs=[lk_supp, lk_contra],
            )

    # -------------------------------------------------------------------------
    # 4. WEAKEST-CRITICAL-DEPENDENCY CONFIDENCE PROPAGATION
    # -------------------------------------------------------------------------

    def test_weakest_critical_dependency_propagation(self) -> None:
        """Final confidence must not exceed the weakest critical evidence dependency."""
        ev_strong = EvidenceDefinition(
            evidence_id="EV-STRONG",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
            confidence_score=0.95,
        )
        ev_weak = EvidenceDefinition(
            evidence_id="EV-WEAK",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E9_HISTORICAL_LINGUISTIC,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Fragmentary papyrus",
            extracted_text_or_data="damaged reading",
            confidence_score=0.40,
        )
        cl = ClaimDefinition(
            claim_id="CLM-PROP-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            epistemic_type=EpistemicType.CONTEXTUAL_FACT,
            claim_text="Claim dependent on damaged reading",
            claimed_by="SCHOLAR",
            epistemic_status=EpistemicStatus.PROVISIONAL,
            confidence_score=0.90,  # User gave 0.90, but critical dependency is 0.40
        )
        lk1 = ClaimEvidenceLinkDefinition(
            link_id="LK-P1",
            claim_id="CLM-PROP-01",
            evidence_id="EV-STRONG",
            relationship=EvidenceRelationship.SUPPORT,
            is_critical_dependency=False,
            reasoning="Supporting context",
        )
        lk2 = ClaimEvidenceLinkDefinition(
            link_id="LK-P2",
            claim_id="CLM-PROP-01",
            evidence_id="EV-WEAK",
            relationship=EvidenceRelationship.SUPPORT,
            is_critical_dependency=True,
            reasoning="Critical foundation",
        )

        res = self.ev_mgr.record_evidence_and_claims(
            source_text_id=self.source_text_id,
            evidence_defs=[ev_strong, ev_weak],
            claim_defs=[cl],
            link_defs=[lk1, lk2],
        )

        # Calculated confidence capped to weakest critical dependency (0.40)
        self.assertAlmostEqual(res.claim_records[0].calculated_confidence, 0.40, places=2)

    # -------------------------------------------------------------------------
    # 5. RELATIONSHIPS, IMMUTABILITY, ROLLBACK & CONCURRENCY
    # -------------------------------------------------------------------------

    def test_evidence_relationship_integrity(self) -> None:
        """All supported relationships work and invalid relationships are rejected."""
        for rel_str in ["SUPPORT", "CONTRADICT", "QUALIFY", "LIMIT", "REFINE"]:
            rel = coerce_evidence_relationship(rel_str)
            self.assertIsInstance(rel, EvidenceRelationship)

        with self.assertRaises(InvalidEvidenceRelationshipError):
            coerce_evidence_relationship("PROVES_ABSOLUTELY")

    def test_immutable_evidence_triggers(self) -> None:
        """SQLite triggers prevent UPDATE and DELETE on evidence_ledger."""
        ev = EvidenceDefinition(
            evidence_id="EV-IMMUT-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
        )
        self.ev_mgr.record_evidence_and_claims(
            source_text_id=self.source_text_id,
            evidence_defs=[ev],
            claim_defs=[],
            link_defs=[],
        )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE evidence_ledger SET extracted_text_or_data = 'altered' WHERE evidence_id = 'EV-IMMUT-01';"
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM evidence_ledger WHERE evidence_id = 'EV-IMMUT-01';"
                )

    def test_immutable_claim_triggers(self) -> None:
        """SQLite triggers prevent UPDATE and DELETE on claims."""
        ev = EvidenceDefinition(
            evidence_id="EV-CL-IMMUT-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
        )
        cl = ClaimDefinition(
            claim_id="CLM-IMMUT-01",
            pericope_id="PER-REV-19",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="Immutable claim",
            claimed_by="TEST",
            epistemic_status=EpistemicStatus.PROVISIONAL,
        )
        lk = ClaimEvidenceLinkDefinition(
            link_id="LK-IMMUT-01",
            claim_id="CLM-IMMUT-01",
            evidence_id="EV-CL-IMMUT-01",
            relationship=EvidenceRelationship.SUPPORT,
            reasoning="Valid link",
        )
        self.ev_mgr.record_evidence_and_claims(
            source_text_id=self.source_text_id,
            evidence_defs=[ev],
            claim_defs=[cl],
            link_defs=[lk],
        )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "UPDATE claims SET claim_text = 'tampered' WHERE claim_id = 'CLM-IMMUT-01';"
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute(
                    "DELETE FROM claims WHERE claim_id = 'CLM-IMMUT-01';"
                )

    def test_transactional_rollback(self) -> None:
        """Failure during persistence rolls back all inserted records cleanly."""
        ev = EvidenceDefinition(
            evidence_id="EV-ROLLBACK-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="text",
        )
        # Invalid claim referencing nonexistent pericope will fail during foreign check
        cl_invalid = ClaimDefinition(
            claim_id="CLM-FAIL-01",
            pericope_id="NONEXISTENT_PERICOPE",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="Will fail",
            claimed_by="TEST",
        )

        with self.assertRaises(EvidenceClaimOrphanError):
            self.ev_mgr.record_evidence_and_claims(
                source_text_id=self.source_text_id,
                evidence_defs=[ev],
                claim_defs=[cl_invalid],
                link_defs=[],
            )

        # Verify ev was not inserted
        with self.assertRaises(EvidenceNotFoundError):
            self.ev_mgr.get_evidence("EV-ROLLBACK-01")

    def test_concurrency_safety(self) -> None:
        """Concurrent reads and writes do not corrupt state."""
        def insert_evidence(index: int):
            engine = DatabaseEngine(self.config)
            mgr = EvidenceClaimManager(engine)
            try:
                ev = EvidenceDefinition(
                    evidence_id=f"EV-CONC-{index}",
                    pericope_id="PER-REV-19",
                    passage_id="REV-19-08",
                    evidence_class=EvidenceClass.E0_DIRECT_TEXT,
                    epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
                    source_reference=f"Ref {index}",
                    extracted_text_or_data=f"Data {index}",
                )
                return mgr.record_evidence_and_claims(
                    source_text_id=self.source_text_id,
                    evidence_defs=[ev],
                    claim_defs=[],
                    link_defs=[],
                    run_id=f"RUN-CONC-{index}",
                )
            finally:
                engine.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(insert_evidence, range(5)))

        self.assertEqual(len(results), 5)
        for i in range(5):
            ev_rec = self.ev_mgr.get_evidence(f"EV-CONC-{i}")
            self.assertEqual(ev_rec.evidence_id, f"EV-CONC-{i}")

    # -------------------------------------------------------------------------
    # 6. MIGRATION CHECKSUMS & LEGACY DB INTEGRITY
    # -------------------------------------------------------------------------

    def test_migration_checksums_001_to_011_unchanged(self) -> None:
        """Verify migrations 001-011 checksums match expected golden values."""
        migrations_dir = (
            Path(__file__).resolve().parent.parent
            / "schemas"
            / "bible_engine"
        )
        for filename, expected_hash in EXPECTED_MIGRATION_CHECKSUMS.items():
            file_path = migrations_dir / filename
            self.assertTrue(file_path.exists(), f"Missing migration file: {filename}")
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"Checksum mismatch for {filename}! Expected {expected_hash}, got {actual_hash}",
            )

    def test_legacy_db_sha256_unchanged(self) -> None:
        """Verify legacy database polya_index.db has not been altered."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_sha,
                LEGACY_DB_SHA256,
                f"Legacy DB altered! Expected {LEGACY_DB_SHA256}, got {actual_sha}",
            )


if __name__ == "__main__":
    unittest.main()
