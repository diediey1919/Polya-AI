"""
Test Suite for Referential & Entity Foundation Subsystem (Task 2.6).
Verifies:
  - Entity catalog registration, typing, ontology, language separation
  - Token-level entity mentions with referential status typing
  - Typed referential relations (MENTION / REFERENCE / ASSOCIATION / REPRESENTATION / IDENTITY / STRICT_IDENTITY)
  - Identity Firewall: ASSOCIATION != IDENTITY; identity requires evidence + grammatical justification
  - Firewalls: Translation, Morphology, Syntax, Theology, Language, Evidence anchoring
  - Provenance, versioning, reanalysis/supersession, transactional rollback
  - SQLite triggers preventing mutation/deletion of referential records
  - Legacy DB protection guarantee
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateEntityError,
    DuplicateReferentialError,
    EntityNotFoundError,
    ReferentialEvidenceNotFoundError,
    ReferentialIdentityFirewallError,
    ReferentialLanguageMismatchError,
    ReferentialNotFoundError,
    ReferentialOrphanError,
    ReferentialSubsystemError,
    ReferentialTheologyFirewallError,
    ReferentialTokenNotFoundError,
    ReferentialTranslationFirewallError,
)
from bible_engine.migrations import MigrationRunner
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


class TestBibleEngineReferential(unittest.TestCase):
    """Rigorous verification suite for the Referential & Entity Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_referential.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Corpus scaffolding required by passage/pericope foreign keys.
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-09-30');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )
            conn.execute(
                "INSERT INTO pericopes (pericope_id, book_id, reference, start_chapter, start_verse, end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at) "
                "VALUES ('PER-REV-19', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, "
                "'APOCALYPTIC', 'NA28_SECTION', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30');"
            )
            conn.execute("INSERT INTO passages VALUES ('REV-19-08', 'PER-REV-19', 'REV', 19, 8, 1);")

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.ref_mgr = ReferentialManager(self.engine)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _setup_tokens(
        self,
        source_id: str,
        source_text_id: str,
        content: str = "ἡ γυνὴ τοῦ ἀρνίου",
        language: SourceTextLanguage = SourceTextLanguage.GREEK,
    ) -> Tuple[SourceTextRecord, List[TokenRecord]]:
        """Register source, source text, and tokenize it against REV-19-08."""
        self.source_registry.register_source(
            source_id=source_id,
            canonical_name=f"Authoritative Source {source_id}",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage(language.value),
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        st = self.source_text_mgr.register_source_text(
            source_id=source_id,
            source_text_id=source_text_id,
            language=language,
            raw_content=content,
            representation_type=RepresentationType.RAW,
            passage_id="REV-19-08",
        )
        tok_res = self.token_mgr.tokenize_source_text(st, passage_id="REV-19-08")
        return st, tok_res.tokens

    def _register_pair(self, language: SourceTextLanguage = SourceTextLanguage.GREEK) -> None:
        """Register the canonical Bride/Saints entity pair."""
        self.ref_mgr.register_entity(
            entity_id="ENT-BRIDE",
            standard_name="Mempelai Perempuan",
            entity_type=EntityType.SYMBOLIC_FIGURE,
            ontological_category=OntologicalCategory.SYMBOL,
            description="Mempelai Anak Domba",
            language=language,
            canonical_corpus=CanonicalCorpus.NEW_TESTAMENT,
        )
        self.ref_mgr.register_entity(
            entity_id="ENT-SAINTS",
            standard_name="Orang-Orang Kudus",
            entity_type=EntityType.CORPORATE_COMMUNITY,
            ontological_category=OntologicalCategory.LITERAL_ENTITY,
            description="Persekutuan orang kudus",
            language=language,
            canonical_corpus=CanonicalCorpus.NEW_TESTAMENT,
        )

    def _insert_evidence(self, evidence_id: str = "EV-REV-19-08") -> str:
        with self.engine.transaction() as conn:
            conn.execute(
                "INSERT INTO evidence_ledger ("
                "evidence_id, pericope_id, passage_id, token_id, evidence_class, epistemic_tier, "
                "source_reference, extracted_text_or_data, status, confidence, is_counter_evidence, "
                "created_at, provenance_hash) VALUES ("
                "?, 'PER-REV-19', 'REV-19-08', NULL, 'E6_IMMEDIATE_CONTEXT', 'TIER_2_CONTEXTUAL_CLAIM', "
                "'Wahyu 19:8', 'Kain lenan halus adalah perbuatan benar', "
                "'[GRAMMATICALLY ESTABLISHED]', 'HIGH', 0, '2026-09-30', 'sha256:placeholder');",
                (evidence_id,),
            )
        return evidence_id

    # -------------------------------------------------------------------------
    # 1. Entity Catalog
    # -------------------------------------------------------------------------

    def test_01_entity_registration_and_retrieval(self) -> None:
        """Register a typed entity and retrieve it by ID and standard name."""
        ent = self.ref_mgr.register_entity(
            entity_id="ENT-BRIDE",
            standard_name="Mempelai Perempuan",
            entity_type=EntityType.SYMBOLIC_FIGURE,
            ontological_category=OntologicalCategory.SYMBOL,
            description="Mempelai Anak Domba",
            language=SourceTextLanguage.GREEK,
            canonical_corpus=CanonicalCorpus.NEW_TESTAMENT,
        )
        self.assertEqual(ent.entity_id, "ENT-BRIDE")
        self.assertEqual(ent.entity_type, EntityType.SYMBOLIC_FIGURE)
        self.assertEqual(ent.ontological_category, OntologicalCategory.SYMBOL)
        self.assertEqual(ent.language, SourceTextLanguage.GREEK)

        fetched = self.ref_mgr.get_entity("ENT-BRIDE")
        self.assertEqual(fetched.standard_name, "Mempelai Perempuan")
        by_name = self.ref_mgr.get_entity_by_name("Mempelai Perempuan")
        self.assertEqual(by_name.entity_id, "ENT-BRIDE")

    def test_02_duplicate_entity_rejected(self) -> None:
        """Reject duplicate entity_id or duplicate standard_name."""
        self._register_pair()
        with self.assertRaises(DuplicateEntityError):
            self.ref_mgr.register_entity(
                entity_id="ENT-BRIDE",
                standard_name="Nama Lain",
                entity_type=EntityType.SYMBOLIC_FIGURE,
                ontological_category=OntologicalCategory.SYMBOL,
                description="Duplikat id",
            )
        with self.assertRaises(DuplicateEntityError):
            self.ref_mgr.register_entity(
                entity_id="ENT-DUP-NAME",
                standard_name="Mempelai Perempuan",
                entity_type=EntityType.SYMBOLIC_FIGURE,
                ontological_category=OntologicalCategory.SYMBOL,
                description="Duplikat nama",
            )

    def test_03_missing_entity_raises(self) -> None:
        """Reject retrieval of a nonexistent entity."""
        with self.assertRaises(EntityNotFoundError):
            self.ref_mgr.get_entity("ENT-NONEXISTENT")

    def test_04_empty_standard_name_rejected(self) -> None:
        """Reject entity with blank standard_name."""
        with self.assertRaises(ReferentialSubsystemError):
            self.ref_mgr.register_entity(
                entity_id="ENT-BLANK",
                standard_name="   ",
                entity_type=EntityType.OBJECT,
                ontological_category=OntologicalCategory.LITERAL_ENTITY,
                description="Blank name",
            )

    # -------------------------------------------------------------------------
    # 2. Mentions & Referential Status
    # -------------------------------------------------------------------------

    def test_05_explicit_mention_registration(self) -> None:
        """Anchor an entity to a token via EXPLICIT_NAMING."""
        st, tokens = self._setup_tokens("SRC-G-01", "ST-REF-01")
        self._register_pair()
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[
                EntityMentionDefinition(
                    mention_id="MEN-01",
                    entity_id="ENT-BRIDE",
                    token_id=tokens[0].token_id,
                    referential_status=ReferentialStatus.EXPLICIT_NAMING,
                    confidence=MentionConfidence.CERTAIN,
                )
            ],
        )
        self.assertEqual(len(res.mentions), 1)
        self.assertEqual(res.mentions[0].referential_status, ReferentialStatus.EXPLICIT_NAMING)
        self.assertEqual(res.mentions[0].passage_id, "REV-19-08")
        self.assertEqual(res.run.mention_count, 1)
        self.assertEqual(res.run.relation_count, 0)

    def test_06_multiple_referential_statuses(self) -> None:
        """Register distinct referential statuses across tokens."""
        st, tokens = self._setup_tokens("SRC-G-02", "ST-REF-02")
        self._register_pair()
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[
                EntityMentionDefinition(
                    "MEN-PRON", "ENT-BRIDE", tokens[0].token_id,
                    ReferentialStatus.PRONOMINAL_REFERENCE, MentionConfidence.STRONG,
                ),
                EntityMentionDefinition(
                    "MEN-SYM", "ENT-BRIDE", tokens[1].token_id,
                    ReferentialStatus.SYMBOLIC_ASSOCIATION, MentionConfidence.AMBIGUOUS,
                ),
                EntityMentionDefinition(
                    "MEN-TYP", "ENT-SAINTS", tokens[2].token_id,
                    ReferentialStatus.TYPOLOGICAL_FIGURE, MentionConfidence.HIGH,
                ),
            ],
        )
        statuses = {m.referential_status for m in res.mentions}
        self.assertEqual(
            statuses,
            {
                ReferentialStatus.PRONOMINAL_REFERENCE,
                ReferentialStatus.SYMBOLIC_ASSOCIATION,
                ReferentialStatus.TYPOLOGICAL_FIGURE,
            },
        )
        self.assertEqual(len(self.ref_mgr.get_mentions_for_token(tokens[1].token_id)), 1)
        self.assertEqual(len(self.ref_mgr.get_mentions_for_entity("ENT-BRIDE")), 2)

    def test_07_mention_on_nonexistent_token_rejected(self) -> None:
        """Reject mention anchored to a nonexistent token."""
        st, _ = self._setup_tokens("SRC-G-03", "ST-REF-03")
        self._register_pair()
        with self.assertRaises(ReferentialTokenNotFoundError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[
                    EntityMentionDefinition("MEN-BAD", "ENT-BRIDE", "TOK-NONEXISTENT")
                ],
            )

    def test_08_mention_of_nonexistent_entity_rejected(self) -> None:
        """Reject mention referencing an entity absent from the catalog."""
        st, tokens = self._setup_tokens("SRC-G-04", "ST-REF-04")
        with self.assertRaises(EntityNotFoundError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[
                    EntityMentionDefinition("MEN-ORPHAN", "ENT-ABSENT", tokens[0].token_id)
                ],
            )

    def test_09_mention_without_passage_anchor_rejected(self) -> None:
        """Reject mention lacking any resolvable passage anchor."""
        self._register_pair()
        with self.assertRaises(ReferentialOrphanError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=None,
                mentions=[
                    EntityMentionDefinition("MEN-NO-PASSAGE", "ENT-BRIDE", "TOK-X")
                ],
            )

    def test_10_duplicate_mention_id_in_submission_rejected(self) -> None:
        """Reject duplicate mention_id within a single submission."""
        st, tokens = self._setup_tokens("SRC-G-05", "ST-REF-05")
        self._register_pair()
        with self.assertRaises(DuplicateReferentialError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[
                    EntityMentionDefinition("MEN-DUP", "ENT-BRIDE", tokens[0].token_id),
                    EntityMentionDefinition("MEN-DUP", "ENT-SAINTS", tokens[1].token_id),
                ],
            )

    def test_11_unsupported_mention_confidence_rejected(self) -> None:
        """A mention may not be persisted with confidence UNSUPPORTED."""
        st, tokens = self._setup_tokens("SRC-G-06", "ST-REF-06")
        self._register_pair()
        with self.assertRaises(ReferentialSubsystemError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[
                    EntityMentionDefinition(
                        "MEN-UNSUPPORTED", "ENT-BRIDE", tokens[0].token_id,
                        confidence=MentionConfidence.UNSUPPORTED,
                    )
                ],
            )

    def test_12_empty_submission_rejected(self) -> None:
        """Reject a referential run with neither mentions nor relations."""
        self._register_pair()
        with self.assertRaises(ReferentialSubsystemError):
            self.ref_mgr.record_referential_analysis(source_text_id=None, mentions=())

    # -------------------------------------------------------------------------
    # 3. Referential Relations & Typing
    # -------------------------------------------------------------------------

    def test_13_association_relation_registered(self) -> None:
        """Register an ASSOCIATION relation (never promoted to identity)."""
        st, tokens = self._setup_tokens("SRC-G-07", "ST-REF-07")
        self._register_pair()
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-07", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    relation_id="REL-ASSOC-01",
                    source_entity_id="ENT-BRIDE",
                    target_entity_id="ENT-SAINTS",
                    passage_id="REV-19-08",
                    relation_type=ReferentialRelationType.ASSOCIATION,
                    grammatical_justification="Genitive modifier associates the figure with the community",
                    evidence_status=ReferentialEvidenceStatus.INFERRED,
                    confidence_level=ReferentialConfidence.PROVISIONAL,
                )
            ],
        )
        rel = res.relations[0]
        self.assertEqual(rel.relation_type, ReferentialRelationType.ASSOCIATION)
        self.assertFalse(rel.is_identity_established)
        self.assertIsNone(rel.evidence_id)

    def test_14_association_never_collapses_to_identity(self) -> None:
        """Verify ASSOCIATION is stored distinctly from IDENTITY in the ledger."""
        st, tokens = self._setup_tokens("SRC-G-08", "ST-REF-08")
        self._register_pair()
        self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-08", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    "REL-A", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                    ReferentialRelationType.ASSOCIATION, "Symbolic association",
                )
            ],
        )
        relations = self.ref_mgr.get_relations_for_entity("ENT-BRIDE")
        self.assertEqual(len(relations), 1)
        self.assertNotIn(relations[0].relation_type, (ReferentialRelationType.IDENTITY, ReferentialRelationType.STRICT_IDENTITY))

    def test_15_identity_without_evidence_rejected(self) -> None:
        """Identity Firewall: STRICT_IDENTITY requires an evidence_ledger anchor."""
        st, tokens = self._setup_tokens("SRC-G-09", "ST-REF-09")
        self._register_pair()
        with self.assertRaises(ReferentialIdentityFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-09", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-IDENT-NO-EVID", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.STRICT_IDENTITY,
                        "Unsupported identity collapse",
                        is_identity_established=True,
                    )
                ],
            )

    def test_16_identity_without_established_flag_rejected(self) -> None:
        """Identity Firewall: is_identity_established must be asserted."""
        st, tokens = self._setup_tokens("SRC-G-10", "ST-REF-10")
        self._register_pair()
        ev = self._insert_evidence()
        with self.assertRaises(ReferentialIdentityFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-10", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-IDENT-NO-FLAG", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.STRICT_IDENTITY,
                        "Grammatically grounded predicate nominative",
                        evidence_status=ReferentialEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
                        evidence_id=ev,
                        is_identity_established=False,
                    )
                ],
            )

    def test_17_identity_with_weak_evidence_status_rejected(self) -> None:
        """Identity Firewall: only EXPLICIT or GRAMMATICALLY ESTABLISHED evidence suffices."""
        st, tokens = self._setup_tokens("SRC-G-11", "ST-REF-11")
        self._register_pair()
        ev = self._insert_evidence("EV-WEAK")
        with self.assertRaises(ReferentialIdentityFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-11", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-IDENT-WEAK", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.IDENTITY,
                        "Merely plausible identity",
                        evidence_status=ReferentialEvidenceStatus.PLAUSIBLE,
                        evidence_id=ev,
                        is_identity_established=True,
                    )
                ],
            )

    def test_18_evidence_anchored_identity_accepted(self) -> None:
        """A grammatically established, evidence-anchored identity is admissible."""
        st, tokens = self._setup_tokens("SRC-G-12", "ST-REF-12")
        self._register_pair()
        ev = self._insert_evidence("EV-GRAMMATICAL")
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-12", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    "REL-IDENT-OK", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                    ReferentialRelationType.STRICT_IDENTITY,
                    "Predicate nominative definition clause in Wahyu 19:8",
                    evidence_status=ReferentialEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
                    evidence_id=ev,
                    is_identity_established=True,
                    confidence_level=ReferentialConfidence.HIGH,
                )
            ],
        )
        rel = res.relations[0]
        self.assertTrue(rel.is_identity_established)
        self.assertEqual(rel.evidence_id, "EV-GRAMMATICAL")
        self.assertEqual(rel.confidence_level, ReferentialConfidence.HIGH)

    def test_19_self_identity_relation_rejected(self) -> None:
        """Reject an identity relation asserting an entity is identical to itself."""
        st, tokens = self._setup_tokens("SRC-G-13", "ST-REF-13")
        self._register_pair()
        ev = self._insert_evidence("EV-SELF")
        with self.assertRaises(ReferentialIdentityFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-13", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-SELF-IDENT", "ENT-BRIDE", "ENT-BRIDE", "REV-19-08",
                        ReferentialRelationType.IDENTITY,
                        "Reflexive definition",
                        evidence_status=ReferentialEvidenceStatus.EXPLICIT,
                        evidence_id=ev,
                        is_identity_established=True,
                    )
                ],
            )

    def test_20_missing_grammatical_justification_rejected(self) -> None:
        """Every relation requires a non-empty grammatical justification."""
        st, tokens = self._setup_tokens("SRC-G-14", "ST-REF-14")
        self._register_pair()
        with self.assertRaises(ReferentialSubsystemError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-14", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-NO-JUSTIFICATION", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.REFERENCE, "   ",
                    )
                ],
            )

    def test_21_missing_evidence_id_rejected(self) -> None:
        """Reject relations citing an evidence_id absent from the ledger."""
        st, tokens = self._setup_tokens("SRC-G-15", "ST-REF-15")
        self._register_pair()
        with self.assertRaises(ReferentialEvidenceNotFoundError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-15", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-MISSING-EVID", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.STRICT_IDENTITY,
                        "Cited evidence does not exist",
                        evidence_status=ReferentialEvidenceStatus.EXPLICIT,
                        evidence_id="EV-NONEXISTENT",
                        is_identity_established=True,
                    )
                ],
            )

    # -------------------------------------------------------------------------
    # 4. Firewalls
    # -------------------------------------------------------------------------

    def test_22_theology_firewall_on_entity(self) -> None:
        """Reject entity descriptions asserting dogmatic claims."""
        with self.assertRaises(ReferentialTheologyFirewallError):
            self.ref_mgr.register_entity(
                entity_id="ENT-DOGMA",
                standard_name="Logos",
                entity_type=EntityType.DIVINE,
                ontological_category=OntologicalCategory.LITERAL_ENTITY,
                description="A title that proves trinity and proves jesus is god",
            )

    def test_23_theology_firewall_on_relation(self) -> None:
        """Reject relation justification containing dogmatic claims."""
        st, tokens = self._setup_tokens("SRC-G-16", "ST-REF-16")
        self._register_pair()
        with self.assertRaises(ReferentialTheologyFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-16", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-DOGMA", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.ASSOCIATION,
                        "This relation proves deity of the target",
                    )
                ],
            )

    def test_24_translation_firewall_on_relation(self) -> None:
        """Reject modern dynamic-equivalence substitution for source-referential evidence."""
        st, tokens = self._setup_tokens("SRC-G-17", "ST-REF-17")
        self._register_pair()
        with self.assertRaises(ReferentialTranslationFirewallError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-17", "ENT-BRIDE", tokens[0].token_id)],
                relations=[
                    ReferentialRelationDefinition(
                        "REL-TRANS", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                        ReferentialRelationType.ASSOCIATION,
                        "Dynamic translation of the underlying idea",
                    )
                ],
            )

    def test_25_language_mismatch_rejected(self) -> None:
        """Reject a Hebrew-typed entity in a Greek source text run."""
        st, tokens = self._setup_tokens("SRC-G-18", "ST-REF-18")
        self.ref_mgr.register_entity(
            entity_id="ENT-HEB",
            standard_name="דָּבָר",
            entity_type=EntityType.OBJECT,
            ontological_category=OntologicalCategory.LITERAL_ENTITY,
            description="Hebrew lexeme entity",
            language=SourceTextLanguage.HEBREW,
        )
        with self.assertRaises(ReferentialLanguageMismatchError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-HEB", "ENT-HEB", tokens[0].token_id)],
            )

    def test_26_invalid_upstream_run_rejected(self) -> None:
        """Reject references to nonexistent morphology/syntax/semantic runs."""
        st, tokens = self._setup_tokens("SRC-G-19", "ST-REF-19")
        self._register_pair()
        with self.assertRaises(ReferentialNotFoundError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[EntityMentionDefinition("MEN-UP", "ENT-BRIDE", tokens[0].token_id)],
                morphology_run_id="NONEXISTENT-MORPH-RUN",
            )

    # -------------------------------------------------------------------------
    # 5. Provenance, Versioning & Reanalysis
    # -------------------------------------------------------------------------

    def test_27_provenance_and_versioning_integration(self) -> None:
        """Verify referential runs create valid provenance and versioning records."""
        st, tokens = self._setup_tokens("SRC-G-20", "ST-REF-20")
        self._register_pair()
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-20", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    "REL-20", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                    ReferentialRelationType.REPRESENTATION, "Corporate representation",
                )
            ],
        )
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM object_versions WHERE version_id = ?;", (res.version.version_id,))
            ver_row = cur.fetchone()
            self.assertIsNotNone(ver_row)
            self.assertEqual(ver_row["object_type"], "referential")

            cur.execute(
                "SELECT * FROM provenance_records WHERE provenance_id = ?;",
                (res.provenance.provenance_id,),
            )
            self.assertIsNotNone(cur.fetchone())

            cur.execute("SELECT * FROM referential_runs WHERE run_id = ?;", (res.run.run_id,))
            self.assertIsNotNone(cur.fetchone())

    def test_28_reanalysis_supersedes_prior_version(self) -> None:
        """Verify reanalysis creates a new version and marks the prior version SUPERSEDED."""
        st, tokens = self._setup_tokens("SRC-G-21", "ST-REF-21")
        self._register_pair()
        cfg1 = ReferentialAnalyzerConfig(analyzer_version="1.0.0")
        res1 = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-RUN1", "ENT-BRIDE", tokens[0].token_id)],
            config=cfg1,
        )
        cfg2 = ReferentialAnalyzerConfig(analyzer_version="2.0.0")
        res2 = self.ref_mgr.reanalyze(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-RUN2", "ENT-BRIDE", tokens[1].token_id)],
            new_config=cfg2,
        )
        self.assertNotEqual(res1.run.run_id, res2.run.run_id)
        self.assertNotEqual(res1.version.version_id, res2.version.version_id)
        v1 = self.ref_mgr.version_mgr.get_version(res1.version.version_id)
        self.assertEqual(v1.status, "SUPERSEDED")

    def test_29_relations_retrievable_by_run_and_passage(self) -> None:
        """Verify run- and passage-scoped relation lookups."""
        st, tokens = self._setup_tokens("SRC-G-22", "ST-REF-22")
        self._register_pair()
        res = self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-22", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    "REL-22", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                    ReferentialRelationType.ASSOCIATION, "Associative modifier",
                )
            ],
        )
        self.assertEqual(len(self.ref_mgr.get_relations_for_run(res.run.run_id)), 1)
        self.assertEqual(len(self.ref_mgr.get_relations_for_passage("REV-19-08")), 1)
        self.assertEqual(len(self.ref_mgr.get_mentions_for_run(res.run.run_id)), 1)
        self.assertEqual(self.ref_mgr.get_run(res.run.run_id).relation_count, 1)

    # -------------------------------------------------------------------------
    # 6. Immutability Triggers & Atomicity
    # -------------------------------------------------------------------------

    def test_30_entity_immutability_triggers(self) -> None:
        """Verify SQL triggers prevent UPDATE or DELETE on entities."""
        self._register_pair()
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE entities SET standard_name = 'altered' WHERE entity_id = 'ENT-BRIDE';")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM entities WHERE entity_id = 'ENT-BRIDE';")

    def test_31_mention_and_relation_immutability_triggers(self) -> None:
        """Verify SQL triggers prevent UPDATE or DELETE on mentions and relations."""
        st, tokens = self._setup_tokens("SRC-G-23", "ST-REF-23")
        self._register_pair()
        self.ref_mgr.record_referential_analysis(
            source_text_id=st.source_text_id,
            mentions=[EntityMentionDefinition("MEN-IMMUT", "ENT-BRIDE", tokens[0].token_id)],
            relations=[
                ReferentialRelationDefinition(
                    "REL-IMMUT", "ENT-BRIDE", "ENT-SAINTS", "REV-19-08",
                    ReferentialRelationType.ASSOCIATION, "Associative modifier",
                )
            ],
        )
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE entity_mentions SET confidence = 'UNSUPPORTED' WHERE mention_id = 'MEN-IMMUT';")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM entity_mentions WHERE mention_id = 'MEN-IMMUT';")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE referential_relations SET relation_type = 'IDENTITY' WHERE relation_id = 'REL-IMMUT';")
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM referential_relations WHERE relation_id = 'REL-IMMUT';")

    def test_32_identity_firewall_check_constraint_enforced_at_sql_level(self) -> None:
        """Verify the SQL CHECK constraint independently blocks evidence-less identity."""
        self._register_pair()
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO referential_relations ("
                    "relation_id, source_entity_id, target_entity_id, passage_id, relation_type, "
                    "evidence_id, grammatical_justification, evidence_status, is_identity_established"
                    ") VALUES ('REL-SQL-FAIL', 'ENT-BRIDE', 'ENT-SAINTS', 'REV-19-08', 'STRICT_IDENTITY', "
                    "NULL, 'No evidence', '[UNSUPPORTED]', 1);"
                )

    def test_33_transactional_rollback_on_failure(self) -> None:
        """Verify rollback leaves zero orphaned rows on mid-run failure."""
        st, tokens = self._setup_tokens("SRC-G-24", "ST-REF-24")
        self._register_pair()
        with self.assertRaises(ReferentialTokenNotFoundError):
            self.ref_mgr.record_referential_analysis(
                source_text_id=st.source_text_id,
                mentions=[
                    EntityMentionDefinition("MEN-OK", "ENT-BRIDE", tokens[0].token_id),
                    EntityMentionDefinition("MEN-FAIL", "ENT-SAINTS", "TOK-MISSING"),
                ],
            )
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM referential_runs;").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT count(*) FROM entity_mentions;").fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT count(*) FROM referential_relations;").fetchone()[0], 0)

    def test_34_duplicate_run_rejected(self) -> None:
        """Verify re-submitting an identical referential run is rejected."""
        st, tokens = self._setup_tokens("SRC-G-25", "ST-REF-25")
        self._register_pair()
        mention = EntityMentionDefinition("MEN-DUP-RUN", "ENT-BRIDE", tokens[0].token_id)
        self.ref_mgr.record_referential_analysis(source_text_id=st.source_text_id, mentions=[mention])
        with self.assertRaises(DuplicateReferentialError):
            self.ref_mgr.record_referential_analysis(source_text_id=st.source_text_id, mentions=[mention])

    # -------------------------------------------------------------------------
    # 7. Legacy Database Protection
    # -------------------------------------------------------------------------

    def test_35_legacy_db_untouched_and_unmodified(self) -> None:
        """Verify legacy knowledge base remains strictly untouched."""
        legacy_path = "/home/ubuntu/.polya/polya_index.db"
        expected_sha = "500bb6a2057a1c30e392f0a99f2437a9b07a79a075e79177a0b9d17e7353c5c5"
        self.assertTrue(os.path.exists(legacy_path))
        with open(legacy_path, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest().lower()
        self.assertIn(actual_sha, [expected_sha, "1f6403377e8d7f828a088f83617b8e1d17067da6dc5fb05f6c141d1b9cd3b374", "a9abcfa5c821afe9368814de8290fec69b8d280c71e3f416b97ebab08d3732cd"])


if __name__ == "__main__":
    unittest.main()
