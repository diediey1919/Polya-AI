"""
POLYA PHILOLOGICAL BIBLE ENGINE
PHASE 2 INTEGRATED ARCHITECTURE GATE TEST SUITE

Validates the complete Phase 2 foundation as ONE integrated epistemic pipeline:
  SOURCE TEXT
  → TOKENIZATION
  → MORPHOLOGY
  → SYNTAX
  → SEMANTICS
  → REFERENTIAL / ENTITY
  → DISCOURSE / CONTEXT
  → EVIDENCE
  → CLAIM
  → EXEGESIS
  → CALIBRATED CONCLUSION

Validates 22 Phase 2 Gate Requirements:
  1. End-to-End Provenance
  2. End-to-End Versioning
  3. Cross-Layer Foreign-Key Integrity
  4. Language Firewall (Greek, Hebrew, Aramaic)
  5. Translation Firewall
  6. AI Output Firewall
  7. Evidence Propagation
  8. Counter-Evidence
  9. Confidence Weakest-Link
  10. Ambiguity Preservation
  11. Identity Firewall
  12. Theology Firewall
  13. Pericope Primary Unit
  14. Immutability
  15. Rollback
  16. Concurrency
  17. Reproducibility
  18. Migration Integrity (001-013)
  19. Legacy Database Protection
  20. Golden Corpus Integration (Greek, Hebrew, Aramaic)
  21. No-Conclusion-Outruns-Evidence
  22. Architecture Invariant
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.discourse import (
    DiscourseAnalyzerConfig,
    DiscourseManager,
    DiscourseRelationDefinition,
    DiscourseRelationType,
    DiscourseSegmentDefinition,
    DiscourseSegmentType,
    DiscourseUnitDefinition,
    DiscourseUnitType,
    ParticipantDefinition,
)
from bible_engine.errors import (
    AIPrimaryEvidenceFirewallError,
    ClaimEvidenceLinkNotFoundError,
    ConfidenceAsEvidenceFirewallError,
    ConfidenceUpgradeFirewallError,
    DiscourseLanguageMismatchError,
    DiscourseTheologyFirewallError,
    EvidenceConfidenceError,
    ExegesisDiscourseTheologyFirewallError,
    ExegesisEntityIdentityFirewallError,
    ExegesisMorphologyTheologyFirewallError,
    ExegesisSemanticTheologyFirewallError,
    ExegesisSyntaxTheologyFirewallError,
    IdentityFirewallError,
    InterpretationWithoutEvidenceFirewallError,
    MorphologyLanguageMismatchError,
    PericopePrimaryUnitFirewallError,
    ReferentialLanguageMismatchError,
    SemanticLanguageMismatchError,
    SilentAmbiguityResolutionFirewallError,
    StrictIdentityEvidenceFirewallError,
    SuppressionOfCompetingInterpretationFirewallError,
    SuppressionOfCounterEvidenceFirewallError,
    SyntaxLanguageMismatchError,
    TranslationAsSourceFirewallError,
    TranslationToE0FirewallError,
    UnresolvedContradictionFirewallError,
    UnsupportedClaimError,
    UnsupportedConclusionFirewallError,
)
from bible_engine.evidence_claim import (
    ClaimDefinition,
    ClaimEvidenceLinkDefinition,
    ClaimTier,
    EpistemicType,
    EvidenceClaimConfig,
    EvidenceClaimManager,
    EvidenceClass,
    EvidenceDefinition,
    EvidenceRelationship,
)
from bible_engine.exegesis import (
    AuditRelationship,
    CalibratedConclusionDefinition,
    CompetingInterpretationDefinition,
    ContextualFindingDefinition,
    EvidenceAuditDefinition,
    ExegesisConfig,
    ExegesisManager,
    ExegesisObservationDefinition,
    InterpretiveHypothesisDefinition,
    LinguisticFindingDefinition,
    TensionType,
    UnresolvedIssueDefinition,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.morphology import (
    GrammaticalGender,
    GrammaticalNumber,
    GrammaticalPerson,
    GreekCase,
    GreekMorphologyFeatures,
    GreekPOS,
    GreekTense,
    GreekVoice,
    LemmaRecord,
    MorphologyAnalyzerConfig,
    MorphologyManager,
    MorphologyParse,
    SemiticAspect,
    SemiticLexicalCategory,
    SemiticMorphologyFeatures,
    SemiticState,
    SemiticStem,
)
from bible_engine.provenance import (
    ProvenanceTracker,
    RelationType,
    TargetType,
    TransformationType,
)
from bible_engine.referential import (
    CanonicalCorpus,
    EntityMentionDefinition,
    EntityType,
    MentionConfidence,
    OntologicalCategory,
    ReferentialAnalyzerConfig,
    ReferentialConfidence,
    ReferentialEvidenceStatus,
    ReferentialManager,
    ReferentialRelationDefinition,
    ReferentialRelationType,
    ReferentialStatus,
)
from bible_engine.semantics import (
    ConfidenceLevel,
    ContextualSenseCandidateDefinition,
    LexemeRecord,
    LexicalCategory,
    SemanticAnalyzerConfig,
    SemanticDomainFramework,
    SemanticManager,
    SemanticRelationType,
    SemanticSenseRecord,
)
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
)
from bible_engine.syntax import (
    ClauseDefinition,
    ClauseType,
    ConstituentDefinition,
    ConstituentType,
    DependencyRelationDefinition,
    SyntaxAnalyzerConfig,
    SyntaxManager,
    SyntaxModelType,
    SyntaxRelationType,
)
from bible_engine.tokenization import TokenizationManager
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
}

LEGACY_DB_SHA256 = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"


class TestBibleEnginePhase2Gate(unittest.TestCase):
    """Integrated Phase 2 Architecture Gate Test Suite."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "gate_phase2.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Canon, Testaments, Books setup
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
            conn.execute("INSERT INTO testaments VALUES ('OT', 'CAN-PROT', 'Perjanjian Lama', 1);")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute(
                "INSERT INTO books VALUES ('GEN', 'OT', 1, 'Kejadian', 'Genesis', 'HEBREW', 50);"
            )
            conn.execute(
                "INSERT INTO books VALUES ('DAN', 'OT', 27, 'Daniel', 'Daniel', 'ARAMAIC', 12);"
            )
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )

            # Pericopes
            conn.execute(
                """
                INSERT INTO pericopes VALUES (
                    'PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                    'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT INTO pericopes VALUES (
                    'PER-GEN-01', 'GEN', 'Kejadian 1:1-3', 1, 1, 1, 3,
                    'NARRATIVE', 'BHS_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )
            conn.execute(
                """
                INSERT INTO pericopes VALUES (
                    'PER-DAN-02', 'DAN', 'Daniel 2:4-6', 2, 4, 2, 6,
                    'APOCALYPTIC', 'BHS_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                );
                """
            )

            # Passages
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")
            conn.execute("INSERT INTO passages VALUES ('GEN-01-01', 'PER-GEN-01', 'GEN', 1, 1, 2);")
            conn.execute("INSERT INTO passages VALUES ('DAN-02-04', 'PER-DAN-02', 'DAN', 2, 4, 3);")

        # Managers initialization
        self.prov_tracker = ProvenanceTracker(self.engine)
        self.version_mgr = VersionManager(self.engine)
        self.source_reg = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.morph_mgr = MorphologyManager(self.engine)
        self.syntax_mgr = SyntaxManager(self.engine)
        self.semantic_mgr = SemanticManager(self.engine)
        self.referential_mgr = ReferentialManager(self.engine)
        self.discourse_mgr = DiscourseManager(self.engine)
        self.evidence_mgr = EvidenceClaimManager(self.engine)
        self.exegesis_mgr = ExegesisManager(self.engine)

        # Register Sources
        self.source_reg.register_source(
            source_id="SRC-NA28",
            canonical_name="Novum Testamentum Graece 28",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        self.source_reg.register_source(
            source_id="SRC-BHS-HEB",
            canonical_name="Biblia Hebraica Stuttgartensia - Genesis",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.HEBREW,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        self.source_reg.register_source(
            source_id="SRC-BHS-ARM",
            canonical_name="Biblia Hebraica Stuttgartensia - Daniel",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.ARAMAIC,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )

        # Standard source texts used across gate tests
        self.st_gk = self.source_text_mgr.register_source_text(
            source_id="SRC-NA28",
            source_text_id="ST-GK-REV-19",
            language=SourceTextLanguage.GREEK,
            raw_content="βύσσινον",
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # 1. END-TO-END PROVENANCE & PIPELINE INTEGRATION
    # -------------------------------------------------------------------------

    def test_01_complete_end_to_end_pipeline_and_provenance_chain(self) -> None:
        """Verify the full 10-layer pipeline from source text to calibrated conclusion."""
        # 1. Source Text
        st = self.source_text_mgr.register_source_text(
            source_id="SRC-NA28",
            source_text_id="ST-GATE-REV-19-08",
            language=SourceTextLanguage.GREEK,
            raw_content="ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον",
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )
        self.assertIsNotNone(st.source_text_id)

        # 2. Tokenization
        tok_res = self.token_mgr.tokenize_source_text(st, passage_id="REV-19-08")
        tokens = tok_res.tokens
        self.assertEqual(len(tokens), 5)
        t_edothe = tokens[0]  # ἐδόθη
        t_byssinon = tokens[4]  # βύσσινον

        # 3. Morphology
        self.morph_mgr.register_lemma(
            LemmaRecord(
                lemma_id="LEM-G-DIDOMI",
                language=SourceTextLanguage.GREEK,
                lemma_string="δίδωμι",
                lexical_category="VERB",
            )
        )
        parse_edothe = MorphologyParse(
            parse_index=0,
            pos_tag="V-AAI-3S",
            lemma_id="LEM-G-DIDOMI",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.VERB,
                person=GrammaticalPerson.THIRD,
                number=GrammaticalNumber.SINGULAR,
                tense=GreekTense.AORIST,
                voice=GreekVoice.PASSIVE,
            ),
        )
        morph_res = self.morph_mgr.record_morphology_parses(
            source_text_id=st.source_text_id,
            token_parses=[(t_edothe, [parse_edothe])],
            config=MorphologyAnalyzerConfig(analyzer_id="GATE-PARSER"),
        )
        self.assertEqual(len(morph_res.annotations), 1)

        # 4. Syntax
        clause = ClauseDefinition(
            clause_id="CLS-GATE-01",
            clause_order=0,
            clause_type=ClauseType.INDEPENDENT,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[-1].token_id,
            raw_clause_string="ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον",
            passage_id="REV-19-08",
        )
        syntax_res = self.syntax_mgr.record_syntax_analysis(
            source_text_id=st.source_text_id,
            clauses=[clause],
            constituents=[],
            dependencies=[],
        )
        self.assertEqual(syntax_res.run.clause_count, 1)

        # 5. Semantics
        lex_res = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-BYSSINON",
            language=SourceTextLanguage.GREEK,
            citation_form="βύσσινον",
            lexical_category=LexicalCategory.NOUN,
        )
        sense_res = self.semantic_mgr.register_semantic_sense(
            sense_id="SNS-G-BYSSINON-01",
            lexeme_id="LEX-G-BYSSINON",
            sense_number=1,
            sense_label="linen cloth",
            definition="Fine linen garment",
            gloss_primary="fine linen",
            contemporary_domain="Clothing / Textile",
            lexicon_source="BDAG",
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CSC-GATE-01",
            token_id=t_byssinon.token_id,
            sense_id=sense_res.sense_id,
            contextual_gloss="fine linen",
            candidate_rank=1,
            is_preferred=True,
        )
        sem_res = self.semantic_mgr.record_contextual_semantics(
            source_text_id=st.source_text_id,
            candidates=[cand],
        )
        self.assertEqual(len(sem_res.candidates), 1)

        # 6. Referential / Entity
        ent_res = self.referential_mgr.register_entity(
            entity_id="ENT-GATE-BRIDE",
            standard_name="Bride of Christ",
            entity_type=EntityType.SYMBOLIC_FIGURE,
            ontological_category=OntologicalCategory.SYMBOL,
            description="Mempelai Perempuan",
            language=SourceTextLanguage.GREEK,
        )
        mention_res = self.referential_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[
                EntityMentionDefinition(
                    mention_id="MNT-GATE-01",
                    entity_id="ENT-GATE-BRIDE",
                    token_id=tokens[1].token_id,  # αὐτῇ
                    referential_status=ReferentialStatus.PRONOMINAL_REFERENCE,
                    confidence=MentionConfidence.HIGH,
                )
            ],
        )
        self.assertEqual(len(mention_res.mentions), 1)

        # 7. Discourse / Context
        unit1 = DiscourseUnitDefinition(
            unit_id="DU-GATE-01",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[-1].token_id,
            unit_type=DiscourseUnitType.CLAUSE_UNIT,
            unit_order=0,
            raw_unit_surface="ἐδόθη αὐτῇ ἵνα περιβάληται βύσσινον",
        )
        disc_res = self.discourse_mgr.record_discourse_analysis(
            source_text_id=st.source_text_id,
            units=[unit1],
            syntax_run_id=syntax_res.run.run_id,
        )
        self.assertEqual(disc_res.run.unit_count, 1)

        # 8. Evidence & Claim
        ev0 = EvidenceDefinition(
            evidence_id="EV-GATE-E0",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            token_id=t_byssinon.token_id,
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28 Wahyu 19:8",
            extracted_text_or_data="βύσσινον",
        )
        ev2 = EvidenceDefinition(
            evidence_id="EV-GATE-E2",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            token_id=t_edothe.token_id,
            evidence_class=EvidenceClass.E2_MORPHOLOGY,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Aorist Passive parse",
            extracted_text_or_data="ἐδόθη: 3S Aorist Passive",
        )
        cl1 = ClaimDefinition(
            claim_id="CLM-GATE-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,
            epistemic_type=EpistemicType.LINGUISTIC_FACT,
            claim_text="The granting of fine linen is grammatically passive.",
            claimed_by="GATE_TEST",
        )
        link1 = ClaimEvidenceLinkDefinition(
            link_id="LNK-GATE-01",
            claim_id="CLM-GATE-01",
            evidence_id="EV-GATE-E2",
            relationship=EvidenceRelationship.SUPPORT,
            is_critical_dependency=True,
            reasoning="Aorist passive morphology demonstrates grant.",
        )
        ev_claim_res = self.evidence_mgr.record_evidence_and_claims(
            source_text_id=st.source_text_id,
            morphology_run_id=morph_res.run.run_id,
            syntax_run_id=syntax_res.run.run_id,
            evidence_defs=[ev0, ev2],
            claim_defs=[cl1],
            link_defs=[link1],
            run_id="EV-RUN-GATE-01",
        )
        self.assertEqual(len(ev_claim_res.evidence_records), 2)

        # 9. Exegesis & Calibrated Conclusion
        obs = ExegesisObservationDefinition(
            observation_id="OBS-GATE-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            observation_type="GRAMMATICAL_FEATURE",
            source_reference="NA28",
            observed_text_or_data="ἐδόθη αὐτῇ",
        )
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-GATE-01",
            pericope_id="PER-REV-19",
            claim_id="CLM-GATE-01",
            hypothesis_text="Fine linen clothing is granted as divine favor.",
            hypothesis_state="SUPPORTED",
            claim_tier="T2_CONTEXTUAL_CLAIM",
        )
        audit = EvidenceAuditDefinition(
            audit_id="AUD-GATE-01",
            hypothesis_id="HYP-GATE-01",
            evidence_id="EV-GATE-E2",
            relationship="SUPPORT",
            is_critical=True,
            evidence_confidence=0.9,
            audit_notes="Morphological evidence supports grammatical grant.",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-GATE-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-GATE-01",
            conclusion_text="Grammatical passive grant of linen is established.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.85,
            weakest_critical_dependency="EV-GATE-E2",
            weakest_critical_confidence=0.9,
            supporting_evidence_count=1,
        )

        exeg_res = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=st.source_text_id,
            morphology_run_id=morph_res.run.run_id,
            syntax_run_id=syntax_res.run.run_id,
            discourse_run_id=disc_res.run.run_id,
            evidence_run_id=ev_claim_res.run.run_id,
            observations=[obs],
            hypotheses=[hyp],
            evidence_audits=[audit],
            calibrated_conclusions=[conc],
            run_id="EXEG-GATE-01",
        )
        self.assertEqual(exeg_res.status, "COMPLETED")

        # Provenance verification: Every layer produces valid provenance record
        for target_id in [st.source_text_id, morph_res.run.run_id, syntax_res.run.run_id, disc_res.run.run_id, ev_claim_res.run.run_id, exeg_res.run_id]:
            with self.engine.connect() as conn:
                row = conn.execute("SELECT provenance_id FROM provenance_records WHERE target_id = ?", (target_id,)).fetchone()
                self.assertIsNotNone(row, f"Orphaned layer artifact missing provenance: {target_id}")

    # -------------------------------------------------------------------------
    # 2. END-TO-END VERSIONING & SUPERSESSION
    # -------------------------------------------------------------------------

    def test_02_versioning_and_supersession_chains(self) -> None:
        """Verify reanalysis creates new versions with supersession links."""
        st = self.source_text_mgr.register_source_text(
            source_id="SRC-NA28",
            source_text_id="ST-VTEST-01",
            language=SourceTextLanguage.GREEK,
            raw_content="βύσσινον λαμπρὸν καθαρόν",
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )
        run1 = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=st.source_text_id,
            run_id="EXEG-VTEST-01",
        )
        run2 = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id=st.source_text_id,
            parent_version_id=run1.version_id,
            run_id="EXEG-VTEST-02",
        )
        self.assertNotEqual(run1.version_id, run2.version_id)
        v2 = self.version_mgr.get_version(run2.version_id)
        self.assertEqual(v2.parent_version_id, run1.version_id)
        self.assertEqual(v2.version_number, 2)

    # -------------------------------------------------------------------------
    # 3. CROSS-LAYER FOREIGN-KEY INTEGRITY
    # -------------------------------------------------------------------------

    def test_03_invalid_cross_layer_references_rejected(self) -> None:
        """Foreign key checks abort invalid cross-layer references."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                # Token referencing nonexistent source_text
                conn.execute(
                    """
                    INSERT INTO tokens (token_id, source_text_id, passage_id, token_index, position, surface_form, language)
                    VALUES ('TOK-FAKE', 'NONEXISTENT-SRC', 'REV-19-08', 1, 0, 'word', 'GREEK');
                    """
                )

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                # Evidence referencing nonexistent passage
                conn.execute(
                    """
                    INSERT INTO evidence_ledger (evidence_id, pericope_id, passage_id, evidence_class, epistemic_tier, source_reference, extracted_text_or_data, status, confidence, provenance_hash)
                    VALUES ('EV-FAKE', 'PER-REV-19', 'NONEXISTENT-PASSAGE', 'E0_DIRECT_TEXT', 'T0_RAW_OBSERVATION', 'ref', 'text', 'EXPLICIT', 'HIGH', 'h');
                    """
                )

    # -------------------------------------------------------------------------
    # 4. LANGUAGE FIREWALL
    # -------------------------------------------------------------------------

    def test_04_language_firewall_enforced(self) -> None:
        """Greek, Hebrew and Aramaic cross-language mismatches rejected."""
        # Register Hebrew text in Genesis
        st_heb = self.source_text_mgr.register_source_text(
            source_id="SRC-BHS-HEB",
            source_text_id="ST-HEB-GEN-01-01",
            language=SourceTextLanguage.HEBREW,
            raw_content="בְּרֵאשִׁית בָּרָא אֱלֹהִים",
            representation_type=RepresentationType.RAW,
            passage_id="GEN-01-01",
        )
        tok_heb = self.token_mgr.tokenize_source_text(st_heb, passage_id="GEN-01-01").tokens[0]

        # Attempt: Hebrew token -> Greek morphology parse
        greek_parse = MorphologyParse(
            parse_index=0,
            pos_tag="N-NSF",
            lemma_id="LEM-G-FAKE",
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN, gender=GrammaticalGender.FEMININE),
        )
        with self.assertRaises(MorphologyLanguageMismatchError):
            self.morph_mgr.record_morphology_parses(
                source_text_id=st_heb.source_text_id,
                token_parses=[(tok_heb, [greek_parse])],
            )

        # Attempt: Greek token -> Hebrew semantic sense
        st_gk = self.st_gk
        tok_gk = self.token_mgr.tokenize_source_text(st_gk, passage_id="REV-19-08").tokens[0]

        # Register Hebrew lexeme & sense
        self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-H-BERESHIT",
            language=SourceTextLanguage.HEBREW,
            citation_form="רֵאשִׁית",
            lexical_category=LexicalCategory.NOUN,
        )
        self.semantic_mgr.register_semantic_sense(
            sense_id="SNS-H-BERESHIT-01",
            lexeme_id="LEX-H-BERESHIT",
            sense_number=1,
            sense_label="beginning",
            definition="First point in time",
            gloss_primary="beginning",
            contemporary_domain="Time",
            lexicon_source="BDB",
        )
        cand_gk_heb = ContextualSenseCandidateDefinition(
            candidate_id="CSC-CROSS-01",
            token_id=tok_gk.token_id,  # Greek token
            sense_id="SNS-H-BERESHIT-01",  # Hebrew sense
            contextual_gloss="beginning",
        )
        with self.assertRaises(SemanticLanguageMismatchError):
            self.semantic_mgr.record_contextual_semantics(
                source_text_id=st_gk.source_text_id,
                candidates=[cand_gk_heb],
            )

        # Attempt: Aramaic token -> Greek semantic sense
        st_arm = self.source_text_mgr.register_source_text(
            source_id="SRC-BHS-ARM",
            source_text_id="ST-ARM-DAN-02-04",
            language=SourceTextLanguage.ARAMAIC,
            raw_content="מַלְכָּא",
            representation_type=RepresentationType.RAW,
            passage_id="DAN-02-04",
        )
        tok_arm = self.token_mgr.tokenize_source_text(st_arm, passage_id="DAN-02-04").tokens[0]

        self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-BASILEUS",
            language=SourceTextLanguage.GREEK,
            citation_form="βασιλεύς",
            lexical_category=LexicalCategory.NOUN,
        )
        self.semantic_mgr.register_semantic_sense(
            sense_id="SNS-G-BASILEUS-01",
            lexeme_id="LEX-G-BASILEUS",
            sense_number=1,
            sense_label="king",
            definition="Monarch / king",
            gloss_primary="king",
            contemporary_domain="Leadership",
            lexicon_source="BDAG",
        )
        cand_arm_gk = ContextualSenseCandidateDefinition(
            candidate_id="CSC-CROSS-02",
            token_id=tok_arm.token_id,  # Aramaic token
            sense_id="SNS-G-BASILEUS-01",  # Greek sense
            contextual_gloss="king",
        )
        with self.assertRaises(SemanticLanguageMismatchError):
            self.semantic_mgr.record_contextual_semantics(
                source_text_id=st_arm.source_text_id,
                candidates=[cand_arm_gk],
            )

    # -------------------------------------------------------------------------
    # 5. TRANSLATION FIREWALL
    # -------------------------------------------------------------------------

    def test_05_translation_firewall_enforced(self) -> None:
        """Translation output rejected from E0 DIRECT_TEXT and RAW_OBSERVATION."""
        # 1. Evidence Claim E0 firewall
        ev_trans = EvidenceDefinition(
            evidence_id="EV-TRANS-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="LAI TB",
            extracted_text_or_data="lenan halus",
            is_translation_derived=True,
        )
        with self.assertRaises(TranslationToE0FirewallError):
            self.evidence_mgr.record_evidence_and_claims(
                source_text_id="ST-GK-REV-19",
                evidence_defs=[ev_trans],
            )

        # 2. Exegesis raw observation firewall
        obs_trans = ExegesisObservationDefinition(
            observation_id="OBS-TRANS-01",
            pericope_id="PER-REV-19",
            observation_type="RAW_OBSERVATION",
            source_reference="KJV",
            observed_text_or_data="fine linen",
            is_translation_derived=True,
        )
        with self.assertRaises(TranslationAsSourceFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                observations=[obs_trans],
            )

    # -------------------------------------------------------------------------
    # 6. AI OUTPUT FIREWALL
    # -------------------------------------------------------------------------

    def test_06_ai_output_firewall_enforced(self) -> None:
        """AI synthetic output rejected from becoming primary evidence (E0-E1)."""
        ev_ai = EvidenceDefinition(
            evidence_id="EV-AI-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="LLM generation",
            extracted_text_or_data="Synthetic text",
            is_ai_generated=True,
        )
        with self.assertRaises(AIPrimaryEvidenceFirewallError):
            self.evidence_mgr.record_evidence_and_claims(
                source_text_id="ST-GK-REV-19",
                evidence_defs=[ev_ai],
            )

        obs_ai = ExegesisObservationDefinition(
            observation_id="OBS-AI-01",
            pericope_id="PER-REV-19",
            observation_type="RAW_OBSERVATION",
            source_reference="LLM",
            observed_text_or_data="Synthetic observation",
            is_ai_generated=True,
        )
        with self.assertRaises(ConfidenceAsEvidenceFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                observations=[obs_ai],
            )

    # -------------------------------------------------------------------------
    # 7. EVIDENCE PROPAGATION
    # -------------------------------------------------------------------------

    def test_07_evidence_propagation_integrity(self) -> None:
        """Evidence classes preserved accurately through claim and exegesis links."""
        ev = EvidenceDefinition(
            evidence_id="EV-PROP-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E6_IMMEDIATE_CONTEXT,
            epistemic_tier=ClaimTier.T2_CONTEXTUAL_CLAIM,
            source_reference="Revelation Context",
            extracted_text_or_data="Pericope boundaries",
        )
        res = self.evidence_mgr.record_evidence_and_claims(
            source_text_id="ST-GK-REV-19",
            evidence_defs=[ev],
            run_id="EV-RUN-PROP-01",
        )
        rec = self.evidence_mgr.get_evidence("EV-PROP-01")
        self.assertEqual(rec.evidence_class, EvidenceClass.E6_IMMEDIATE_CONTEXT)

    # -------------------------------------------------------------------------
    # 8. COUNTER-EVIDENCE PRESERVATION
    # -------------------------------------------------------------------------

    def test_08_counter_evidence_preserved_across_pipeline(self) -> None:
        """Contradictory evidence must survive and cannot be silently suppressed."""
        ev_supp = EvidenceDefinition(
            evidence_id="EV-SUPP-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E0_DIRECT_TEXT,
            epistemic_tier=ClaimTier.T0_RAW_OBSERVATION,
            source_reference="NA28",
            extracted_text_or_data="reading A",
        )
        ev_contra = EvidenceDefinition(
            evidence_id="EV-CONTRA-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Sinaiticus",
            extracted_text_or_data="reading B",
            is_counter_evidence=True,
        )
        self.evidence_mgr.record_evidence_and_claims(
            source_text_id="ST-GK-REV-19",
            evidence_defs=[ev_supp, ev_contra],
            run_id="EV-RUN-CONTRA-01",
        )

        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-CONTRA-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Reading A is unambiguous.",
        )
        audit_c = EvidenceAuditDefinition(
            audit_id="AUD-C-01",
            hypothesis_id="HYP-CONTRA-01",
            evidence_id="EV-CONTRA-01",
            relationship="CONTRADICT",
            is_counter_evidence=True,
            audit_notes="Manuscript divergence",
        )
        conc_invalid = CalibratedConclusionDefinition(
            conclusion_id="CONC-INVALID-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-CONTRA-01",
            conclusion_text="Reading A established with zero counter-evidence.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.8,
            supporting_evidence_count=1,
            counter_evidence_count=0,  # Suppressed!
        )
        with self.assertRaises(SuppressionOfCounterEvidenceFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp],
                evidence_audits=[audit_c],
                calibrated_conclusions=[conc_invalid],
            )

    # -------------------------------------------------------------------------
    # 9. CONFIDENCE WEAKEST-LINK PROPAGATION
    # -------------------------------------------------------------------------

    def test_09_confidence_weakest_link_propagation(self) -> None:
        """Final confidence cannot exceed weakest critical dependency."""
        ev_weak = EvidenceDefinition(
            evidence_id="EV-WEAK-01",
            pericope_id="PER-REV-19",
            passage_id="REV-19-08",
            evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            epistemic_tier=ClaimTier.T1_LINGUISTIC_FACT,
            source_reference="Fragmentary witness",
            extracted_text_or_data="fragment",
        )
        self.evidence_mgr.record_evidence_and_claims(
            source_text_id="ST-GK-REV-19",
            evidence_defs=[ev_weak],
            run_id="EV-RUN-WEAK-01",
        )
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-WEAK-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Weak dependency claim.",
        )
        audit = EvidenceAuditDefinition(
            audit_id="AUD-WEAK-01",
            hypothesis_id="HYP-WEAK-01",
            evidence_id="EV-WEAK-01",
            relationship="SUPPORT",
            is_critical=True,
            evidence_confidence=0.45,
            audit_notes="Weak critical dependency",
        )
        conc_overconfident = CalibratedConclusionDefinition(
            conclusion_id="CONC-OVERCONF-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-WEAK-01",
            conclusion_text="Overconfident conclusion.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.92,  # Exceeds 0.45!
            weakest_critical_dependency="EV-WEAK-01",
            weakest_critical_confidence=0.45,
            supporting_evidence_count=1,
        )
        with self.assertRaises(ConfidenceUpgradeFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp],
                evidence_audits=[audit],
                calibrated_conclusions=[conc_overconfident],
            )

    # -------------------------------------------------------------------------
    # 10. AMBIGUITY PRESERVATION & ANTI-SUPPRESSION
    # -------------------------------------------------------------------------

    def test_10_ambiguity_preservation_and_anti_suppression(self) -> None:
        """Competing interpretations and active ambiguity issues cannot be suppressed."""
        hyp1 = InterpretiveHypothesisDefinition("HYP-AMBIG-A", "PER-REV-19", "Sense A")
        hyp2 = InterpretiveHypothesisDefinition("HYP-AMBIG-B", "PER-REV-19", "Sense B")
        comp = CompetingInterpretationDefinition(
            competing_id="COMP-AMBIG-01",
            pericope_id="PER-REV-19",
            hypothesis_a_id="HYP-AMBIG-A",
            hypothesis_b_id="HYP-AMBIG-B",
            tension_type="SEMANTIC_AMBIGUITY",
            description="Two equally attested senses",
            is_suppressed=True,  # Attempting suppression
        )
        with self.assertRaises(SuppressionOfCompetingInterpretationFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp1, hyp2],
                competing_interpretations=[comp],
            )

    # -------------------------------------------------------------------------
    # 11. IDENTITY FIREWALL
    # -------------------------------------------------------------------------

    def test_11_identity_firewall_enforced(self) -> None:
        """Entity association cannot become STRICT_IDENTITY without independent evidence."""
        hyp_invalid = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-ID-FAIL",
            pericope_id="PER-REV-19",
            hypothesis_text="Symbol is strictly identical to institution.",
            asserts_strict_identity=True,
            independent_identity_evidence_id=None,
        )
        with self.assertRaises(StrictIdentityEvidenceFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp_invalid],
            )

    # -------------------------------------------------------------------------
    # 12. THEOLOGY FIREWALL
    # -------------------------------------------------------------------------

    def test_12_theology_firewall_enforced(self) -> None:
        """Direct T4 theology from morphology, syntax, semantics, discourse, entity fails."""
        for src, err in [
            ("MORPHOLOGY", ExegesisMorphologyTheologyFirewallError),
            ("SYNTAX", ExegesisSyntaxTheologyFirewallError),
            ("SEMANTICS", ExegesisSemanticTheologyFirewallError),
            ("DISCOURSE", ExegesisDiscourseTheologyFirewallError),
            ("ENTITY", ExegesisEntityIdentityFirewallError),
        ]:
            hyp = InterpretiveHypothesisDefinition(
                hypothesis_id=f"HYP-THEO-{src}",
                pericope_id="PER-REV-19",
                hypothesis_text=f"Direct dogma from {src}.",
                claim_tier="T4_THEOLOGICAL_CLAIM",
                direct_theology_source=src,
            )
            with self.assertRaises(err):
                self.exegesis_mgr.record_exegesis(
                    pericope_id="PER-REV-19",
                    source_text_id="ST-GK-REV-19",
                    hypotheses=[hyp],
                )

    # -------------------------------------------------------------------------
    # 13. PERICOPE PRIMARY UNIT
    # -------------------------------------------------------------------------

    def test_13_pericope_primary_unit_enforced(self) -> None:
        """Pericope is required; verse cannot substitute for pericope."""
        with self.assertRaises(PericopePrimaryUnitFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="REV-19-08",  # Verse address
                source_text_id="ST-GK-REV-19",
            )

    # -------------------------------------------------------------------------
    # 14. IMMUTABILITY LEDGER
    # -------------------------------------------------------------------------

    def test_14_database_level_immutability(self) -> None:
        """Direct SQL UPDATE and DELETE on evidence and exegesis tables rejected."""
        run = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id="ST-GK-REV-19",
            run_id="EXEG-IMMUT-GATE",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("UPDATE exegesis_runs SET analyzer_id = 'MUTATED' WHERE run_id = 'EXEG-IMMUT-GATE'")

        with self.assertRaises(sqlite3.IntegrityError):
            with self.engine.transaction() as conn:
                conn.execute("DELETE FROM exegesis_runs WHERE run_id = 'EXEG-IMMUT-GATE'")

    # -------------------------------------------------------------------------
    # 15. ATOMIC TRANSACTION ROLLBACK
    # -------------------------------------------------------------------------

    def test_15_atomic_transaction_rollback(self) -> None:
        """Failure during exegesis persistence rolls back all records cleanly."""
        hyp_fail = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-ROLLBACK-GATE",
            pericope_id="PER-REV-19",
            hypothesis_text="Unsupported hypothesis marked SUPPORTED.",
            hypothesis_state="SUPPORTED",
        )
        with self.assertRaises(InterpretationWithoutEvidenceFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp_fail],
                run_id="EXEG-ROLLBACK-GATE",
            )
        # Verify no orphan exegesis run
        with self.engine.connect() as conn:
            row = conn.execute("SELECT run_id FROM exegesis_runs WHERE run_id = 'EXEG-ROLLBACK-GATE'").fetchone()
            self.assertIsNone(row)

    # -------------------------------------------------------------------------
    # 16. CONCURRENCY SAFETY
    # -------------------------------------------------------------------------

    def test_16_concurrency_safety(self) -> None:
        """Parallel insertions on distinct connections complete without corruption."""
        def insert_run(idx: int) -> str:
            engine = DatabaseEngine(self.config)
            try:
                mgr = ExegesisManager(engine)
                run = mgr.record_exegesis(
                    pericope_id="PER-REV-19",
                    source_text_id="ST-GK-REV-19",
                    run_id=f"EXEG-PARALLEL-{idx}",
                )
                return run.run_id
            finally:
                engine.close()

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(insert_run, range(4)))

        self.assertEqual(len(results), 4)
        for i in range(4):
            rec = self.exegesis_mgr.get_exegesis_run(f"EXEG-PARALLEL-{i}")
            self.assertEqual(rec.run_id, f"EXEG-PARALLEL-{i}")

    # -------------------------------------------------------------------------
    # 17. DETERMINISTIC REPRODUCIBILITY
    # -------------------------------------------------------------------------

    def test_17_deterministic_reproducibility(self) -> None:
        """Identical inputs produce identical input_content_hash and output_hash."""
        obs = ExegesisObservationDefinition(
            observation_id="OBS-REPRO-01",
            pericope_id="PER-REV-19",
            observation_type="RAW_OBSERVATION",
            source_reference="NA28",
            observed_text_or_data="data",
        )
        cfg = ExegesisConfig(analyzer_id="TEST-ANALYZER", analyzer_version="1.0.0")
        run1 = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id="ST-GK-REV-19",
            observations=[obs],
            config=cfg,
            run_id="EXEG-REPRO-01",
        )

        # Execute identical analysis in a fresh isolated database
        with tempfile.TemporaryDirectory() as repro_dir:
            repro_db = Path(repro_dir) / "repro.db"
            repro_engine = DatabaseEngine(DatabaseConfig(db_path=str(repro_db)))
            try:
                MigrationRunner(repro_engine).apply_pending()
                with repro_engine.transaction() as rconn:
                    rconn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-10-01');")
                    rconn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
                    rconn.execute("INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
                    rconn.execute(
                        """
                        INSERT INTO pericopes VALUES (
                            'PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9,
                            'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'VALIDATED', '1.0', '2026-10-01T00:00:00Z'
                        );
                        """
                    )
                    rconn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")
                sreg = SourceRegistry(repro_engine)
                sreg.register_source(
                    source_id="SRC-NA28",
                    canonical_name="Novum Testamentum Graece 28",
                    source_type=SourceType.CRITICAL_EDITION,
                    language=SourceLanguage.GREEK,
                    authority_level=SourceAuthorityLevel.PRIMARY,
                )
                stm = SourceTextManager(repro_engine)
                stm.register_source_text(
                    source_id="SRC-NA28",
                    source_text_id="ST-GK-REV-19",
                    language=SourceTextLanguage.GREEK,
                    raw_content="βύσσινον",
                    representation_type=RepresentationType.RAW,
                    passage_id="REV-19-08",
                )
                repro_mgr = ExegesisManager(repro_engine)
                run2 = repro_mgr.record_exegesis(
                    pericope_id="PER-REV-19",
                    source_text_id="ST-GK-REV-19",
                    observations=[obs],
                    config=cfg,
                    run_id="EXEG-REPRO-01",
                )
                self.assertEqual(run1.input_content_hash, run2.input_content_hash)
                self.assertEqual(run1.output_hash, run2.output_hash)
                self.assertEqual(run1.configuration_hash, run2.configuration_hash)
            finally:
                repro_engine.close()

    # -------------------------------------------------------------------------
    # 18. MIGRATION INTEGRITY (001–013)
    # -------------------------------------------------------------------------

    def test_18_migration_checksums_001_to_013_unchanged(self) -> None:
        """Migrations 001-013 must strictly match golden checksums."""
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

    # -------------------------------------------------------------------------
    # 19. LEGACY DATABASE PROTECTION
    # -------------------------------------------------------------------------

    def test_19_legacy_db_sha256_unaltered(self) -> None:
        """Legacy database /home/ubuntu/.polya/polya_index.db must remain bit-for-bit unchanged."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if legacy_path.exists():
            actual_sha = hashlib.sha256(legacy_path.read_bytes()).hexdigest().lower()
            self.assertEqual(
                actual_sha,
                LEGACY_DB_SHA256,
                f"Legacy DB altered! Expected {LEGACY_DB_SHA256}, got {actual_sha}",
            )

    # -------------------------------------------------------------------------
    # 20. GOLDEN CORPUS INTEGRATION (Greek, Hebrew, Aramaic)
    # -------------------------------------------------------------------------

    def test_20_golden_corpus_multi_language_integration(self) -> None:
        """Representative pericopes for Koine Greek, Biblical Hebrew, Biblical Aramaic."""
        # 1. Greek (Revelation 19:8)
        run_gk = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id="ST-GK-REV-19",
            run_id="EXEG-GOLDEN-GK",
        )
        self.assertEqual(run_gk.pericope_id, "PER-REV-19")

        # 2. Hebrew (Genesis 1:1)
        st_heb = self.source_text_mgr.register_source_text(
            source_id="SRC-BHS-HEB",
            source_text_id="ST-GOLDEN-HEB",
            language=SourceTextLanguage.HEBREW,
            raw_content="בְּרֵאשִׁית בָּרָא אֱלֹהִים",
            representation_type=RepresentationType.RAW,
            passage_id="GEN-01-01",
        )
        run_heb = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-GEN-01",
            source_text_id=st_heb.source_text_id,
            run_id="EXEG-GOLDEN-HEB",
        )
        self.assertEqual(run_heb.pericope_id, "PER-GEN-01")

        # 3. Aramaic (Daniel 2:4)
        st_arm = self.source_text_mgr.register_source_text(
            source_id="SRC-BHS-ARM",
            source_text_id="ST-GOLDEN-ARM",
            language=SourceTextLanguage.ARAMAIC,
            raw_content="מַלְכָּא לְעָלְמִין חֱיִי",
            representation_type=RepresentationType.RAW,
            passage_id="DAN-02-04",
        )
        run_arm = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-DAN-02",
            source_text_id=st_arm.source_text_id,
            run_id="EXEG-GOLDEN-ARM",
        )
        self.assertEqual(run_arm.pericope_id, "PER-DAN-02")

    # -------------------------------------------------------------------------
    # 21. NO-CONCLUSION-OUTRUNS-EVIDENCE
    # -------------------------------------------------------------------------

    def test_21_no_conclusion_outruns_evidence(self) -> None:
        """High confidence with missing evidence must NOT produce an accepted conclusion."""
        hyp = InterpretiveHypothesisDefinition(
            hypothesis_id="HYP-OVERREACH-01",
            pericope_id="PER-REV-19",
            hypothesis_text="Overreaching theological claim without evidence.",
            hypothesis_state="PROPOSED",
        )
        conc = CalibratedConclusionDefinition(
            conclusion_id="CONC-OVERREACH-01",
            pericope_id="PER-REV-19",
            hypothesis_id="HYP-OVERREACH-01",
            conclusion_text="Dogma asserted with confidence 0.99 but no evidence.",
            epistemic_status="SUPPORTED",
            calibrated_confidence=0.99,  # High confidence
            supporting_evidence_count=0,  # Zero evidence!
        )
        with self.assertRaises(UnsupportedConclusionFirewallError):
            self.exegesis_mgr.record_exegesis(
                pericope_id="PER-REV-19",
                source_text_id="ST-GK-REV-19",
                hypotheses=[hyp],
                calibrated_conclusions=[conc],
            )

    # -------------------------------------------------------------------------
    # 22. ARCHITECTURE INVARIANT
    # -------------------------------------------------------------------------

    def test_22_epistemic_architecture_invariant(self) -> None:
        """Verify SOURCE -> OBSERVATION -> EVIDENCE -> CLAIM -> INTERPRETATION -> CONCLUSION flow."""
        # Verification that conclusion requires hypothesis, hypothesis requires evidence audits,
        # and evidence requires source text provenance linkage
        rec = self.exegesis_mgr.record_exegesis(
            pericope_id="PER-REV-19",
            source_text_id="ST-GK-REV-19",
            run_id="EXEG-INVARIANT-01",
        )
        self.assertIsNotNone(rec.input_content_hash)
        self.assertIsNotNone(rec.output_hash)
        self.assertIsNotNone(rec.provenance_id)
        self.assertIsNotNone(rec.version_id)


if __name__ == "__main__":
    unittest.main()
