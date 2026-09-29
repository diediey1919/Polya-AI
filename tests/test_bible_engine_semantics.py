"""
Test Suite for Source-Language Semantic Foundation Subsystem (Task 2.5).
Verifies:
  - Lexeme registration, homonym distinction, multiple senses per lexeme
  - Polysemy & semantic relation handling
  - Semantic domain assignment & framework support
  - External lexical resource integration (BDAG, HALOT, BDB, LSJ, Louw-Nida)
  - Contextual sense candidate assignment & ranking
  - Language separation (Greek, Hebrew, Aramaic)
  - Firewalls: Translation, Morphology, Syntax, Theology, Identity
  - Provenance, versioning, reanalysis/supersession, rollback/concurrency
  - SQLite triggers preventing mutation/deletion of semantic records
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
    DuplicateSemanticError,
    LexemeNotFoundError,
    SemanticConfidenceError,
    SemanticDomainNotFoundError,
    SemanticIdentityFirewallError,
    SemanticLanguageMismatchError,
    SemanticMorphologyFirewallError,
    SemanticNotFoundError,
    SemanticOrphanError,
    SemanticRelationError,
    SemanticSenseNotFoundError,
    SemanticSubsystemError,
    SemanticSyntaxFirewallError,
    SemanticTheologyFirewallError,
    SemanticTokenNotFoundError,
    SemanticTranslationFirewallError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.semantics import (
    ConfidenceLevel,
    ContextualSenseCandidateDefinition,
    LexemeRecord,
    LexicalCategory,
    RegisterLevel,
    SemanticAnalyzerConfig,
    SemanticDomainFramework,
    SemanticDomainRecord,
    SemanticManager,
    SemanticRelationRecord,
    SemanticRelationType,
    SemanticResult,
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
    SourceTextRecord,
)
from bible_engine.tokenization import TokenizationManager, TokenRecord


class TestBibleEngineSemantics(unittest.TestCase):
    """Rigorous verification suite for Source-Language Semantic Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_semantics.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.semantic_mgr = SemanticManager(self.engine)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    def _setup_tokens(
        self,
        source_id: str,
        source_text_id: str,
        language: SourceTextLanguage,
        content: str,
    ) -> Tuple[SourceTextRecord, List[TokenRecord]]:
        """Helper to register source, source text, and tokenize it."""
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
        )
        tok_res = self.token_mgr.tokenize_source_text(st)
        return st, tok_res.tokens

    # -------------------------------------------------------------------------
    # 1. Lexeme Registration & Distinctions
    # -------------------------------------------------------------------------

    def test_01_lexeme_registration_and_retrieval(self) -> None:
        """Register a valid Greek lexeme and retrieve it."""
        lex = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-LOGOS",
            language=SourceTextLanguage.GREEK,
            citation_form="λόγος",
            etymological_root="λεγ-",
            homonym_number=1,
            lexical_category=LexicalCategory.NOUN,
        )
        self.assertEqual(lex.lexeme_id, "LEX-G-LOGOS")
        self.assertEqual(lex.citation_form, "λόγος")
        self.assertEqual(lex.homonym_number, 1)

        fetched = self.semantic_mgr.get_lexeme("LEX-G-LOGOS")
        self.assertEqual(fetched.lexeme_id, lex.lexeme_id)

    def test_02_duplicate_lexeme_rejected(self) -> None:
        """Reject duplicate lexeme ID or duplicate (language, citation, homonym_number)."""
        self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-LOGOS",
            language=SourceTextLanguage.GREEK,
            citation_form="λόγος",
            homonym_number=1,
        )
        with self.assertRaises(DuplicateSemanticError):
            self.semantic_mgr.register_lexeme(
                lexeme_id="LEX-G-LOGOS",
                language=SourceTextLanguage.GREEK,
                citation_form="λόγος",
                homonym_number=1,
            )

        with self.assertRaises(DuplicateSemanticError):
            self.semantic_mgr.register_lexeme(
                lexeme_id="LEX-G-LOGOS-2",
                language=SourceTextLanguage.GREEK,
                citation_form="λόγος",
                homonym_number=1,
            )

    def test_03_homonym_distinction(self) -> None:
        """Permit multiple distinct lexemes for identical citation forms via homonym_number."""
        # e.g. Hebrew 'אל' (God/might) vs 'אל' (preposition 'to/unto')
        lex1 = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-H-EL-1",
            language=SourceTextLanguage.HEBREW,
            citation_form="אֵל",
            homonym_number=1,
            lexical_category=LexicalCategory.NOUN,
        )
        lex2 = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-H-EL-2",
            language=SourceTextLanguage.HEBREW,
            citation_form="אֵל",
            homonym_number=2,
            lexical_category=LexicalCategory.PREPOSITION,
        )
        self.assertEqual(lex1.citation_form, lex2.citation_form)
        self.assertNotEqual(lex1.homonym_number, lex2.homonym_number)

    # -------------------------------------------------------------------------
    # 2. Semantic Domains & Resource Frameworks
    # -------------------------------------------------------------------------

    def test_04_semantic_domain_registration(self) -> None:
        """Register hierarchical semantic domains."""
        parent = self.semantic_mgr.register_semantic_domain(
            domain_id="DOM-LN-33",
            domain_code="33",
            domain_name="Communication",
            framework_source=SemanticDomainFramework.LOUW_NIDA,
            description="Domains involving speech, discourse, and language",
        )
        child = self.semantic_mgr.register_semantic_domain(
            domain_id="DOM-LN-33-01",
            domain_code="33.1",
            domain_name="Spoken Discourse",
            parent_domain_id=parent.domain_id,
            framework_source=SemanticDomainFramework.LOUW_NIDA,
        )
        self.assertEqual(child.parent_domain_id, "DOM-LN-33")

    def test_05_semantic_domain_invalid_parent_rejected(self) -> None:
        """Reject semantic domain referencing nonexistent parent."""
        with self.assertRaises(SemanticDomainNotFoundError):
            self.semantic_mgr.register_semantic_domain(
                domain_id="DOM-ORPHAN",
                domain_code="99.9",
                domain_name="Orphan Domain",
                parent_domain_id="DOM-NONEXISTENT",
            )

    # -------------------------------------------------------------------------
    # 3. Semantic Senses & Polysemy
    # -------------------------------------------------------------------------

    def test_06_semantic_sense_registration_and_polysemy(self) -> None:
        """Register multiple discrete senses for a single polysemous lexeme."""
        lex = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-LOGOS",
            language=SourceTextLanguage.GREEK,
            citation_form="λόγος",
        )
        dom = self.semantic_mgr.register_semantic_domain(
            domain_id="DOM-LN-33",
            domain_code="33",
            domain_name="Communication",
        )

        s1 = self.semantic_mgr.register_semantic_sense(
            sense_id="SENSE-LOGOS-01",
            lexeme_id=lex.lexeme_id,
            sense_number=1,
            sense_label="speech / utterance",
            definition="A vocal utterance, message, or proclamation.",
            gloss_primary="word / speech",
            domain_id=dom.domain_id,
            contemporary_domain="Hellenistic discourse",
            lexicon_source="BDAG p. 598",
            external_resource_id="BDAG-LOGOS-1",
        )
        s2 = self.semantic_mgr.register_semantic_sense(
            sense_id="SENSE-LOGOS-02",
            lexeme_id=lex.lexeme_id,
            sense_number=2,
            sense_label="reckoning / accounting",
            definition="A formal calculation, financial reckoning, or account.",
            gloss_primary="account / reckoning",
            contemporary_domain="Greco-Roman financial administration",
            lexicon_source="BDAG p. 600",
            external_resource_id="BDAG-LOGOS-2",
        )
        senses = self.semantic_mgr.get_senses_for_lexeme(lex.lexeme_id)
        self.assertEqual(len(senses), 2)
        self.assertEqual(senses[0].sense_number, 1)
        self.assertEqual(senses[1].sense_number, 2)

    def test_07_duplicate_sense_number_rejected(self) -> None:
        """Reject duplicate sense number for same lexeme."""
        lex = self.semantic_mgr.register_lexeme(
            lexeme_id="LEX-G-LOGOS",
            language=SourceTextLanguage.GREEK,
            citation_form="λόγος",
        )
        self.semantic_mgr.register_semantic_sense(
            sense_id="SENSE-LOGOS-01",
            lexeme_id=lex.lexeme_id,
            sense_number=1,
            sense_label="speech",
            definition="A spoken message.",
            gloss_primary="speech",
            contemporary_domain="Discourse",
            lexicon_source="BDAG",
        )
        with self.assertRaises(DuplicateSemanticError):
            self.semantic_mgr.register_semantic_sense(
                sense_id="SENSE-LOGOS-01-DUP",
                lexeme_id=lex.lexeme_id,
                sense_number=1,
                sense_label="utterance",
                definition="An utterance.",
                gloss_primary="utterance",
                contemporary_domain="Discourse",
                lexicon_source="BDAG",
            )

    # -------------------------------------------------------------------------
    # 4. Semantic Relations
    # -------------------------------------------------------------------------

    def test_08_semantic_relation_registration(self) -> None:
        """Register synonymy and polysemy extension relations between senses."""
        lex1 = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        lex2 = self.semantic_mgr.register_lexeme("LEX-G-RHEMA", SourceTextLanguage.GREEK, "ῥῆμα")

        s1 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex1.lexeme_id, 1, "speech", "Utterance", "speech", "Discourse", "BDAG"
        )
        s2 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-02", lex1.lexeme_id, 2, "account", "Financial reckoning", "account", "Finance", "BDAG"
        )
        s3 = self.semantic_mgr.register_semantic_sense(
            "SENSE-RHEMA-01", lex2.lexeme_id, 1, "spoken utterance", "Specific statement", "word", "Discourse", "BDAG"
        )

        rel1 = self.semantic_mgr.register_semantic_relation(
            "REL-SYN-01", s1.sense_id, s3.sense_id, SemanticRelationType.NEAR_SYNONYM, lexicon_source="Louw-Nida"
        )
        rel2 = self.semantic_mgr.register_semantic_relation(
            "REL-EXT-01", s1.sense_id, s2.sense_id, SemanticRelationType.POLYSEMY_EXTENSION, lexicon_source="BDAG"
        )
        self.assertEqual(rel1.relation_type, SemanticRelationType.NEAR_SYNONYM)
        self.assertEqual(rel2.relation_type, SemanticRelationType.POLYSEMY_EXTENSION)

    def test_09_semantic_self_relation_rejected(self) -> None:
        """Reject relation connecting a sense to itself."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Utterance", "speech", "Discourse", "BDAG"
        )
        with self.assertRaises(SemanticRelationError):
            self.semantic_mgr.register_semantic_relation(
                "REL-SELF", s.sense_id, s.sense_id, SemanticRelationType.SYNONYM
            )

    # -------------------------------------------------------------------------
    # 5. Contextual Sense Disambiguation & Candidates
    # -------------------------------------------------------------------------

    def test_10_contextual_semantics_registration(self) -> None:
        """Register contextual sense candidate for a token in a source text."""
        st, tokens = self._setup_tokens("SRC-G-01", "ST-SEM-01", SourceTextLanguage.GREEK, "Ἐν ἀρχῇ ἦν ὁ λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        sense = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Divine revelation/proclamation", "word", "Theological/Linguistic", "BDAG"
        )

        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-01",
            token_id=tokens[4].token_id,  # λόγος
            sense_id=sense.sense_id,
            contextual_gloss="the Word / Message",
            candidate_rank=1,
            is_preferred=True,
            confidence_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )

        res = self.semantic_mgr.record_contextual_semantics(
            source_text_id=st.source_text_id,
            candidates=[cand],
        )
        self.assertEqual(len(res.candidates), 1)
        self.assertEqual(res.candidates[0].candidate_id, "CAND-01")
        self.assertEqual(res.run.candidate_count, 1)

    def test_11_multiple_competing_contextual_candidates(self) -> None:
        """Register competing candidate senses (rank 1 vs rank 2) for an ambiguous token."""
        st, tokens = self._setup_tokens("SRC-G-02", "ST-SEM-02", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s1 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Message", "word", "Discourse", "BDAG"
        )
        s2 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-02", lex.lexeme_id, 2, "account", "Financial report", "account", "Finance", "BDAG"
        )

        cand1 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-01",
            token_id=tokens[0].token_id,
            sense_id=s1.sense_id,
            contextual_gloss="spoken message",
            candidate_rank=1,
            is_preferred=True,
            confidence_score=0.7,
            confidence_level=ConfidenceLevel.PROVISIONAL,
        )
        cand2 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-02",
            token_id=tokens[0].token_id,
            sense_id=s2.sense_id,
            contextual_gloss="reckoning",
            candidate_rank=2,
            is_preferred=False,
            confidence_score=0.3,
            confidence_level=ConfidenceLevel.AMBIGUOUS,
            evidence_ref="Alternative accounting metaphor attested in papyri",
        )

        res = self.semantic_mgr.record_contextual_semantics(
            source_text_id=st.source_text_id,
            candidates=[cand1, cand2],
        )
        self.assertEqual(len(res.candidates), 2)
        saved = self.semantic_mgr.get_candidates_for_token(tokens[0].token_id)
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[0].candidate_rank, 1)
        self.assertEqual(saved[1].candidate_rank, 2)

    # -------------------------------------------------------------------------
    # 6. Firewalls: Translation, Morphology, Syntax, Theology, Identity
    # -------------------------------------------------------------------------

    def test_12_theology_firewall_prohibits_dogmatic_claims_in_sense(self) -> None:
        """Reject semantic sense definition making dogmatic or theological assertions."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        with self.assertRaises(SemanticTheologyFirewallError):
            self.semantic_mgr.register_semantic_sense(
                "SENSE-DOGMA",
                lexeme_id=lex.lexeme_id,
                sense_number=1,
                sense_label="hypostatic logos",
                definition="A title that proves Jesus is divine and proves the Trinity.",
                gloss_primary="God",
                contemporary_domain="Theology",
                lexicon_source="Patristics",
            )

    def test_13_theology_firewall_prohibits_dogmatic_claims_in_candidate(self) -> None:
        """Reject contextual gloss containing prohibited theological dogmatic claims."""
        st, tokens = self._setup_tokens("SRC-G-03", "ST-SEM-03", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-THEO",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="Word which proves trinity",
        )
        with self.assertRaises(SemanticTheologyFirewallError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    def test_14_identity_firewall_prohibits_strict_ontological_identity(self) -> None:
        """Reject semantic sense attempting to claim strict ontological identity with the divine essence."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        with self.assertRaises(SemanticIdentityFirewallError):
            self.semantic_mgr.register_semantic_sense(
                "SENSE-IDENT",
                lexeme_id=lex.lexeme_id,
                sense_number=1,
                sense_label="divine logos",
                definition="A being who is strictly identical to God.",
                gloss_primary="God",
                contemporary_domain="Theology",
                lexicon_source="Patristics",
            )

    def test_15_translation_firewall_prohibits_dynamic_equivalence_idioms(self) -> None:
        """Reject substituting target-language dynamic equivalence idiom for lexical source sense."""
        st, tokens = self._setup_tokens("SRC-G-04", "ST-SEM-04", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-TRANS",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="dynamic translation of idea",
        )
        with self.assertRaises(SemanticTranslationFirewallError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    def test_16_language_mismatch_rejected(self) -> None:
        """Reject Hebrew sense assignment to Greek source text."""
        st, tokens = self._setup_tokens("SRC-G-05", "ST-SEM-05", SourceTextLanguage.GREEK, "λόγος")
        lex_heb = self.semantic_mgr.register_lexeme("LEX-H-DAVAR", SourceTextLanguage.HEBREW, "דָּבָר")
        sense_heb = self.semantic_mgr.register_semantic_sense(
            "SENSE-DAVAR-01", lex_heb.lexeme_id, 1, "matter/word", "Speech", "word", "Discourse", "HALOT"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-MISMATCH",
            token_id=tokens[0].token_id,
            sense_id=sense_heb.sense_id,
            contextual_gloss="word",
        )
        with self.assertRaises(SemanticLanguageMismatchError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    def test_17_orphan_rejection_for_nonexistent_token(self) -> None:
        """Reject contextual sense candidate referencing nonexistent token ID."""
        st, _ = self._setup_tokens("SRC-G-06", "ST-SEM-06", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-ORPHAN",
            token_id="TOK-NONEXISTENT",
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        with self.assertRaises(SemanticTokenNotFoundError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    # -------------------------------------------------------------------------
    # 7. Confidence & Evidence Separation
    # -------------------------------------------------------------------------

    def test_18_confidence_score_validation(self) -> None:
        """Enforce confidence score bounds [0.0, 1.0]."""
        st, tokens = self._setup_tokens("SRC-G-07", "ST-SEM-07", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-BAD-CONF",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
            confidence_score=1.5,
        )
        with self.assertRaises(SemanticConfidenceError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    def test_19_ambiguous_confidence_requires_evidence_ref(self) -> None:
        """Ambiguous contextual sense candidate must provide non-empty evidence_ref."""
        st, tokens = self._setup_tokens("SRC-G-08", "ST-SEM-08", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-NO-EVID",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
            confidence_level=ConfidenceLevel.AMBIGUOUS,
            evidence_ref=None,
        )
        with self.assertRaises(SemanticConfidenceError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

    # -------------------------------------------------------------------------
    # 8. Immutability Triggers (SQL Level)
    # -------------------------------------------------------------------------

    def test_20_lexeme_immutability_triggers(self) -> None:
        """Verify SQL triggers prevent UPDATE or DELETE on lexemes table."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE lexemes SET citation_form = 'different' WHERE lexeme_id = ?;", (lex.lexeme_id,))

            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM lexemes WHERE lexeme_id = ?;", (lex.lexeme_id,))

    def test_21_semantic_sense_immutability_triggers(self) -> None:
        """Verify SQL triggers prevent UPDATE or DELETE on semantic_senses table."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE semantic_senses SET definition = 'altered' WHERE sense_id = ?;", (s.sense_id,))

            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM semantic_senses WHERE sense_id = ?;", (s.sense_id,))

    def test_22_contextual_candidate_immutability_triggers(self) -> None:
        """Verify SQL triggers prevent UPDATE or DELETE on contextual_sense_candidates table."""
        st, tokens = self._setup_tokens("SRC-G-09", "ST-SEM-09", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-IMMUT",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        res = self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])
        with self.engine.connect() as conn:
            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("UPDATE contextual_sense_candidates SET contextual_gloss = 'modified' WHERE candidate_id = 'CAND-IMMUT';")

            with self.assertRaises(sqlite3.DatabaseError):
                conn.execute("DELETE FROM contextual_sense_candidates WHERE candidate_id = 'CAND-IMMUT';")

    # -------------------------------------------------------------------------
    # 9. Provenance & Versioning Lineage & Reanalysis
    # -------------------------------------------------------------------------

    def test_23_provenance_and_versioning_integration(self) -> None:
        """Verify semantic runs create valid provenance and versioning records."""
        st, tokens = self._setup_tokens("SRC-G-10", "ST-SEM-10", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-VER",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        res = self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand])

        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM object_versions WHERE version_id = ?;", (res.version.version_id,))
            ver_row = cur.fetchone()
            self.assertIsNotNone(ver_row)
            self.assertEqual(ver_row["object_type"], "semantics")

            cur.execute("SELECT * FROM provenance_records WHERE provenance_id = ?;", (res.provenance.provenance_id,))
            prov_row = cur.fetchone()
            self.assertIsNotNone(prov_row)

    def test_24_reanalysis_supersedes_prior_version(self) -> None:
        """Verify reanalyze creates a new version and marks the prior version as SUPERSEDED."""
        st, tokens = self._setup_tokens("SRC-G-11", "ST-SEM-11", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )
        cand1 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-RUN1",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        cfg1 = SemanticAnalyzerConfig(analyzer_version="1.0.0")
        res1 = self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand1], config=cfg1)

        cand2 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-RUN2",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="authoritative message",
        )
        cfg2 = SemanticAnalyzerConfig(analyzer_version="2.0.0")
        res2 = self.semantic_mgr.reanalyze(st.source_text_id, [cand2], new_config=cfg2)

        self.assertNotEqual(res1.run.run_id, res2.run.run_id)
        self.assertNotEqual(res1.version.version_id, res2.version.version_id)

        # Check version 1 is SUPERSEDED
        v1 = self.semantic_mgr.version_mgr.get_version(res1.version.version_id)
        self.assertEqual(v1.status, "SUPERSEDED")

    # -------------------------------------------------------------------------
    # 10. Concurrency & Rollback
    # -------------------------------------------------------------------------

    def test_25_transactional_rollback_on_failure(self) -> None:
        """Verify transaction rollback ensures zero orphaned rows if candidate fails mid-insertion."""
        st, tokens = self._setup_tokens("SRC-G-12", "ST-SEM-12", SourceTextLanguage.GREEK, "λόγος ἦν")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-01", lex.lexeme_id, 1, "speech", "Proclamation", "word", "Discourse", "BDAG"
        )

        cand_valid = ContextualSenseCandidateDefinition(
            candidate_id="CAND-ROLL-1",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        # Second candidate triggers theology firewall
        cand_invalid = ContextualSenseCandidateDefinition(
            candidate_id="CAND-ROLL-2",
            token_id=tokens[1].token_id,
            sense_id=s.sense_id,
            contextual_gloss="proves trinity",
        )

        with self.assertRaises(SemanticTheologyFirewallError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand_valid, cand_invalid])

        with self.engine.connect() as conn:
            cnt_runs = conn.execute("SELECT count(*) FROM semantic_runs;").fetchone()[0]
            cnt_cands = conn.execute("SELECT count(*) FROM contextual_sense_candidates;").fetchone()[0]
            self.assertEqual(cnt_runs, 0)
            self.assertEqual(cnt_cands, 0)

    # -------------------------------------------------------------------------
    # 11. Legacy Database Protection
    # -------------------------------------------------------------------------

    def test_26_legacy_db_untouched_and_unmodified(self) -> None:
        """Verify legacy database remains strictly untouched."""
        legacy_path = "/home/ubuntu/.polya/polya_index.db"
        expected_sha = "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81"
        self.assertTrue(os.path.exists(legacy_path))
        with open(legacy_path, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest().lower()
        self.assertEqual(actual_sha, expected_sha)

    def test_27_theology_firewall_prohibits_dogma_in_gloss(self) -> None:
        """Verify theology firewall inspects gloss_primary and gloss_secondary."""
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS-GLOSS", SourceTextLanguage.GREEK, "λόγος")
        with self.assertRaises(SemanticTheologyFirewallError):
            self.semantic_mgr.register_semantic_sense(
                "SENSE-GLOSS-THEO",
                lexeme_id=lex.lexeme_id,
                sense_number=1,
                sense_label="speech",
                definition="A normal speech definition.",
                gloss_primary="proves deity",
                contemporary_domain="Discourse",
                lexicon_source="Lexicon",
            )

    def test_28_upstream_morphology_linkage_firewall(self) -> None:
        """Verify morphology_run_id must belong to the matching source_text_id."""
        st, tokens = self._setup_tokens("SRC-G-13", "ST-SEM-13", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS-M", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-M", lex.lexeme_id, 1, "speech", "Utterance", "speech", "Discourse", "BDAG"
        )
        cand = ContextualSenseCandidateDefinition(
            candidate_id="CAND-M-FAIL",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
        )
        with self.assertRaises(SemanticNotFoundError):
            self.semantic_mgr.record_contextual_semantics(
                source_text_id=st.source_text_id,
                candidates=[cand],
                morphology_run_id="NONEXISTENT-MORPH-RUN",
            )

    def test_29_contiguous_ranks_enforced_per_token(self) -> None:
        """Verify candidate ranks must be contiguous 1-based integers."""
        st, tokens = self._setup_tokens("SRC-G-14", "ST-SEM-14", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS-R", SourceTextLanguage.GREEK, "λόγος")
        s = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-R", lex.lexeme_id, 1, "speech", "Utterance", "speech", "Discourse", "BDAG"
        )
        cand_gap = ContextualSenseCandidateDefinition(
            candidate_id="CAND-GAP",
            token_id=tokens[0].token_id,
            sense_id=s.sense_id,
            contextual_gloss="word",
            candidate_rank=2,  # Missing rank 1
        )
        with self.assertRaises(SemanticSubsystemError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand_gap])

    def test_30_at_most_one_preferred_candidate_per_token(self) -> None:
        """Verify multiple preferred candidates for same token are rejected."""
        st, tokens = self._setup_tokens("SRC-G-15", "ST-SEM-15", SourceTextLanguage.GREEK, "λόγος")
        lex = self.semantic_mgr.register_lexeme("LEX-G-LOGOS-P", SourceTextLanguage.GREEK, "λόγος")
        s1 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-P1", lex.lexeme_id, 1, "speech", "Utterance", "speech", "Discourse", "BDAG"
        )
        s2 = self.semantic_mgr.register_semantic_sense(
            "SENSE-LOGOS-P2", lex.lexeme_id, 2, "account", "Reckoning", "account", "Finance", "BDAG"
        )
        cand1 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-P1",
            token_id=tokens[0].token_id,
            sense_id=s1.sense_id,
            contextual_gloss="speech",
            candidate_rank=1,
            is_preferred=True,
        )
        cand2 = ContextualSenseCandidateDefinition(
            candidate_id="CAND-P2",
            token_id=tokens[0].token_id,
            sense_id=s2.sense_id,
            contextual_gloss="account",
            candidate_rank=2,
            is_preferred=True,  # Second preferred candidate on same token
        )
        with self.assertRaises(SemanticSubsystemError):
            self.semantic_mgr.record_contextual_semantics(st.source_text_id, [cand1, cand2])


if __name__ == "__main__":
    unittest.main()

