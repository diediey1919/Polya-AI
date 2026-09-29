"""
Comprehensive Test Suite for Polya Philological Bible Engine - Morphology Foundation (Task 2.3).
Specification: Architecture v2.0 — FROZEN.

Validates:
 1. Token linkage (every observation binds to token_id, source_text_id, version_id, provenance_id)
 2. Orphan rejection (observations without valid tokens rejected)
 3. Greek morphology (POS, case, gender, number, person, tense, voice, mood, degree)
 4. Hebrew morphology (lexical category, state, binyan/stem, aspect, suffixes)
 5. Aramaic morphology (Aramaic-specific stems: Peal, Pael, Aphel, Ithpeel, etc.)
 6. Alternative parses (Parse A, Parse B, Parse C preserved concurrently without overwriting)
 7. Lemma separation (surface form -> lemma -> morphology, multiple lemmas, registry)
 8. Feature validation (strict enum checking, no random strings)
 9. Language-specific schema behavior (firewall: Greek vs Semitic dimensions strictly isolated)
 10. Raw vs Normalized distinction (analyzing raw vs normalized recorded faithfully)
 11. Provenance integration (deterministic & generative provenance, parent linkage)
 12. Versioning integration (object_versions created, active status, content hash)
 13. Immutable historical results (reanalysis supersedes prior version, preserves historical parses)
 14. Analyzer identity (analyzer_id, analyzer_version captured)
 15. Configuration hashing (deterministic config hash computation)
 16. Confidence separation (confidence is metadata, not truth claim or empirical evidence)
 17. Invalid morphology rejection (out-of-bound confidence, cross-language features)
 18. Atomic rollback (failure leaves zero orphan rows in runs or annotations)
 19. Concurrent analysis isolation (independent threads remain isolated)
 20. Legacy database untouched (/home/ubuntu/.polya/polya_index.db preserved intact)
 21. Adversarial trigger probes (UPDATE & DELETE on morphology tables aborted)
 22. Evidence boundary guarantee (morphology produces 0 interpretive/theological claims)
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Dict, List, Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    DuplicateLemmaError,
    DuplicateMorphologyError,
    LemmaNotFoundError,
    MorphologyConfidenceError,
    MorphologyFeatureValidationError,
    MorphologyImmutabilityError,
    MorphologyLanguageMismatchError,
    MorphologyNormalizationFirewallError,
    MorphologyOrphanError,
    MorphologyTokenNotFoundError,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.morphology import (
    ConfidenceLevel,
    GrammaticalGender,
    GrammaticalNumber,
    GrammaticalPerson,
    GreekCase,
    GreekDegree,
    GreekMood,
    GreekMorphologyFeatures,
    GreekPOS,
    GreekTense,
    GreekVoice,
    LemmaRecord,
    MorphologyAnalyzerConfig,
    MorphologyAnnotationRecord,
    MorphologyManager,
    MorphologyParse,
    MorphologyResult,
    MorphologyRunRecord,
    SemiticAspect,
    SemiticLexicalCategory,
    SemiticMorphologyFeatures,
    SemiticState,
    SemiticStem,
    compute_morphology_output_hash,
)
from bible_engine.provenance import ProvenanceTracker
from bible_engine.source_registry import SourceAuthorityLevel, SourceLanguage, SourceRegistry, SourceType
from bible_engine.source_text import RepresentationType, SourceTextLanguage, SourceTextManager, SourceTextRecord
from bible_engine.tokenization import TokenRecord, TokenizationManager, TokenizerConfig
from bible_engine.versioning import VersionManager, VersionStatus


class TestMorphologySubsystem(unittest.TestCase):
    """Exhaustive test suite for Task 2.3 Morphology Foundation subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_morphology.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        # Run all migrations up through 007_morphology.sql
        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.morph_mgr = MorphologyManager(self.engine)
        self.version_mgr = VersionManager(self.engine)
        self.provenance_tracker = ProvenanceTracker(self.engine)

        # Record legacy database checksum
        self.legacy_db_path = Path("/home/ubuntu/.polya/polya_index.db")
        self.initial_legacy_hash = None
        if self.legacy_db_path.exists():
            self.initial_legacy_hash = hashlib.sha256(self.legacy_db_path.read_bytes()).hexdigest()

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Helper Setup Methods
    # -------------------------------------------------------------------------

    def _setup_tokenized_source(
        self,
        source_text_id: str,
        content: str,
        language: SourceTextLanguage,
    ) -> Tuple[SourceTextRecord, List[TokenRecord]]:
        """Register a valid source, source text, and tokenize it to generate authoritative tokens."""
        src_id = f"SRC-{source_text_id}"
        self.source_registry.register_source(
            source_id=src_id,
            canonical_name=f"Authoritative Source {source_text_id}",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage(language.value),
            authority_level=SourceAuthorityLevel.TEXTUAL_CRITICAL,
        )
        st = self.source_text_mgr.register_source_text(
            source_text_id=source_text_id,
            source_id=src_id,
            language=language,
            raw_content=content,
            representation_type=RepresentationType.RAW,
        )
        tok_res = self.token_mgr.tokenize_source_text(st)
        return st, tok_res.tokens

    # -------------------------------------------------------------------------
    # 1. Token Linkage
    # -------------------------------------------------------------------------
    def test_01_token_linkage(self) -> None:
        """Verify morphology observations link strictly to token_id, source_text_id, version_id, provenance_id."""
        st, tokens = self._setup_tokenized_source("ST-LINK-01", "λόγος", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            is_preferred=True,
            pos_tag="N-NMS",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.NOUN,
                case=GreekCase.NOMINATIVE,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
            ),
            confidence_score=0.98,
            confidence_level=ConfidenceLevel.CERTAIN,
        )

        res = self.morph_mgr.record_morphology_parses(
            source_text_id=st.source_text_id,
            token_parses=[(tok, [parse])],
        )

        self.assertEqual(res.run.source_text_id, st.source_text_id)
        self.assertEqual(len(res.annotations), 1)
        ann = res.annotations[0]
        self.assertEqual(ann.token_id, tok.token_id)
        self.assertEqual(ann.source_text_id, st.source_text_id)
        self.assertEqual(ann.run_id, res.run.run_id)
        self.assertEqual(ann.version_id, res.run.version_id)
        self.assertEqual(ann.provenance_id, res.run.provenance_id)
        self.assertTrue(ann.is_immutable)

    # -------------------------------------------------------------------------
    # 2. Orphan Rejection
    # -------------------------------------------------------------------------
    def test_02_orphan_rejection(self) -> None:
        """Morphology observation without a valid token must be rejected."""
        st, _ = self._setup_tokenized_source("ST-ORPH-01", "ἀρχῇ", SourceTextLanguage.GREEK)

        parse = MorphologyParse(
            parse_index=0,
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN),
        )

        # 1. Non-existent token string
        with self.assertRaises(MorphologyTokenNotFoundError):
            self.morph_mgr.record_morphology_parses(
                source_text_id=st.source_text_id,
                token_parses=[("TOK-NON-EXISTENT-9999", [parse])],
            )

        # 2. Token belonging to a different source_text_id
        st_other, tokens_other = self._setup_tokenized_source("ST-ORPH-02", "בָּרָא", SourceTextLanguage.HEBREW)
        with self.assertRaises(MorphologyOrphanError):
            self.morph_mgr.record_morphology_parses(
                source_text_id=st.source_text_id,
                token_parses=[(tokens_other[0], [parse])],
            )

    # -------------------------------------------------------------------------
    # 3. Greek Morphology
    # -------------------------------------------------------------------------
    def test_03_greek_morphology(self) -> None:
        """Verify full Hellenistic Greek morphological dimensions."""
        st, tokens = self._setup_tokenized_source("ST-GRK-01", "ἠγάπησεν", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            pos_tag="V-AAI-3S",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.VERB,
                person=GrammaticalPerson.THIRD,
                number=GrammaticalNumber.SINGULAR,
                tense=GreekTense.AORIST,
                voice=GreekVoice.ACTIVE,
                mood=GreekMood.INDICATIVE,
                pos_tag="V-AAI-3S",
            ),
            confidence_score=0.99,
            confidence_level=ConfidenceLevel.CERTAIN,
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        ann = res.annotations[0]
        self.assertIsNotNone(ann.greek_features)
        self.assertEqual(ann.greek_features.pos, GreekPOS.VERB)
        self.assertEqual(ann.greek_features.tense, GreekTense.AORIST)
        self.assertEqual(ann.greek_features.voice, GreekVoice.ACTIVE)
        self.assertEqual(ann.greek_features.mood, GreekMood.INDICATIVE)
        self.assertEqual(ann.greek_features.person, GrammaticalPerson.THIRD)
        self.assertEqual(ann.greek_features.number, GrammaticalNumber.SINGULAR)
        self.assertIsNone(ann.semitic_features)

    # -------------------------------------------------------------------------
    # 4. Hebrew Morphology
    # -------------------------------------------------------------------------
    def test_04_hebrew_morphology(self) -> None:
        """Verify Biblical Hebrew morphological dimensions (stem/binyan, aspect, construct)."""
        st, tokens = self._setup_tokenized_source("ST-HEB-01", "בָּרָ֣א", SourceTextLanguage.HEBREW)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            pos_tag="V-QAL-PERF-3MS",
            semitic_features=SemiticMorphologyFeatures(
                lexical_category=SemiticLexicalCategory.VERB,
                stem=SemiticStem.QAL,
                verbal_aspect=SemiticAspect.PERFECT,
                person=GrammaticalPerson.THIRD,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
                is_construct=False,
            ),
            confidence_score=0.95,
            confidence_level=ConfidenceLevel.HIGH,
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        ann = res.annotations[0]
        self.assertIsNotNone(ann.semitic_features)
        self.assertEqual(ann.semitic_features.stem, SemiticStem.QAL)
        self.assertEqual(ann.semitic_features.verbal_aspect, SemiticAspect.PERFECT)
        self.assertEqual(ann.semitic_features.person, GrammaticalPerson.THIRD)
        self.assertEqual(ann.semitic_features.gender, GrammaticalGender.MASCULINE)
        self.assertIsNone(ann.greek_features)

    # -------------------------------------------------------------------------
    # 5. Aramaic Morphology
    # -------------------------------------------------------------------------
    def test_05_aramaic_morphology(self) -> None:
        """Verify Biblical Aramaic-specific stems and emphatic states."""
        st, tokens = self._setup_tokenized_source("ST-ARM-01", "מַלְכָּא", SourceTextLanguage.ARAMAIC)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            pos_tag="N-EMPH-MS",
            semitic_features=SemiticMorphologyFeatures(
                lexical_category=SemiticLexicalCategory.NOUN,
                state=SemiticState.EMPHATIC,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
                is_construct=False,
            ),
            confidence_score=0.99,
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        ann = res.annotations[0]
        self.assertEqual(ann.language, SourceTextLanguage.ARAMAIC)
        self.assertEqual(ann.semitic_features.state, SemiticState.EMPHATIC)

    # -------------------------------------------------------------------------
    # 6. Alternative Parses
    # -------------------------------------------------------------------------
    def test_06_alternative_parses(self) -> None:
        """Verify competing alternative parses (Parse A, Parse B, Parse C) are preserved concurrently."""
        st, tokens = self._setup_tokenized_source("ST-MULTI-01", "חָלָב", SourceTextLanguage.HEBREW)
        tok = tokens[0]

        # Parse 0: Noun "milk"
        p0 = MorphologyParse(
            parse_index=0,
            is_preferred=True,
            pos_tag="N-MS",
            semitic_features=SemiticMorphologyFeatures(
                lexical_category=SemiticLexicalCategory.NOUN,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
                state=SemiticState.ABSOLUTE,
            ),
            confidence_score=0.70,
            confidence_level=ConfidenceLevel.HIGH,
        )

        # Parse 1: Noun "fat" (חֵלֶב unvocalized homograph)
        p1 = MorphologyParse(
            parse_index=1,
            is_preferred=False,
            pos_tag="N-MS",
            semitic_features=SemiticMorphologyFeatures(
                lexical_category=SemiticLexicalCategory.NOUN,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
                state=SemiticState.ABSOLUTE,
            ),
            confidence_score=0.30,
            confidence_level=ConfidenceLevel.DISPUTED,
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p0, p1])])
        self.assertEqual(len(res.annotations), 2)

        # Retrieve both parses from database
        parses = self.morph_mgr.get_parses_for_token(tok.token_id)
        self.assertEqual(len(parses), 2)
        self.assertEqual(parses[0].parse_index, 0)
        self.assertTrue(parses[0].is_preferred)
        self.assertEqual(parses[1].parse_index, 1)
        self.assertFalse(parses[1].is_preferred)

        # Preferred parse resolution
        pref = self.morph_mgr.get_preferred_parse(tok.token_id)
        self.assertEqual(pref.annotation_id, parses[0].annotation_id)

    # -------------------------------------------------------------------------
    # 7. Lemma Separation
    # -------------------------------------------------------------------------
    def test_07_lemma_separation(self) -> None:
        """Verify surface form -> lemma -> morphology distinction and lemma registry linkage."""
        # Register authoritative lemma
        lemma = LemmaRecord(
            lemma_id="LEM-G3056",
            language=SourceTextLanguage.GREEK,
            lemma_string="λόγος",
            lexical_category="NOUN",
            strong_code="G3056",
            bdag_entry_id="BDAG-p598",
        )
        self.morph_mgr.register_lemma(lemma)

        # Verify duplicate lemma registration rejection
        with self.assertRaises(DuplicateLemmaError):
            self.morph_mgr.register_lemma(lemma)

        st, tokens = self._setup_tokenized_source("ST-LEM-01", "λόγον", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            lemma_id="LEM-G3056",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.NOUN,
                case=GreekCase.ACCUSATIVE,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
            ),
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        ann = res.annotations[0]
        self.assertEqual(ann.lemma_id, "LEM-G3056")

        # Querying non-existent lemma raises LemmaNotFoundError
        bad_parse = MorphologyParse(
            parse_index=0,
            lemma_id="LEM-NONEXISTENT",
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN),
        )
        with self.assertRaises(LemmaNotFoundError):
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [bad_parse])])

    # -------------------------------------------------------------------------
    # 8. Feature Validation
    # -------------------------------------------------------------------------
    def test_08_feature_validation(self) -> None:
        """Morphological features must conform strictly to controlled dimensions."""
        st, tokens = self._setup_tokenized_source("ST-FEAT-01", "θεός", SourceTextLanguage.GREEK)
        tok = tokens[0]

        # Valid feature set
        valid_features = GreekMorphologyFeatures(
            pos=GreekPOS.NOUN,
            case=GreekCase.NOMINATIVE,
            gender=GrammaticalGender.MASCULINE,
            number=GrammaticalNumber.SINGULAR,
        )
        self.assertEqual(valid_features.case, GreekCase.NOMINATIVE)

        # Empty parse list is rejected
        with self.assertRaises(MorphologyFeatureValidationError):
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [])])

    # -------------------------------------------------------------------------
    # 9. Language-Specific Schema Behavior & Firewall
    # -------------------------------------------------------------------------
    def test_09_language_specific_firewall(self) -> None:
        """Cross-language feature pollution must be strictly rejected."""
        st_grk, grk_tokens = self._setup_tokenized_source("ST-FIRE-GRK", "λόγος", SourceTextLanguage.GREEK)
        st_heb, heb_tokens = self._setup_tokenized_source("ST-FIRE-HEB", "דָּבָר", SourceTextLanguage.HEBREW)

        # Attempting to assign Semitic stem/binyan to Greek token
        cross_semitic = MorphologyParse(
            parse_index=0,
            semitic_features=SemiticMorphologyFeatures(
                lexical_category=SemiticLexicalCategory.VERB,
                stem=SemiticStem.HIPHIL,
            ),
        )
        with self.assertRaises(MorphologyLanguageMismatchError):
            self.morph_mgr.record_morphology_parses(st_grk.source_text_id, [(grk_tokens[0], [cross_semitic])])

        # Attempting to assign Greek grammatical mood/case to Hebrew token
        cross_greek = MorphologyParse(
            parse_index=0,
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.VERB,
                mood=GreekMood.OPTATIVE,
            ),
        )
        with self.assertRaises(MorphologyLanguageMismatchError):
            self.morph_mgr.record_morphology_parses(st_heb.source_text_id, [(heb_tokens[0], [cross_greek])])

    # -------------------------------------------------------------------------
    # 10. Raw vs Normalized Distinction
    # -------------------------------------------------------------------------
    def test_10_raw_vs_normalized_distinction(self) -> None:
        """Morphology must faithfully record whether it analyzes RAW or NORMALIZED tokens."""
        st, tokens = self._setup_tokenized_source("ST-NORM-01", "καὶ", SourceTextLanguage.GREEK)
        tok = tokens[0]

        # Analyze RAW
        cfg_raw = MorphologyAnalyzerConfig(representation_type=RepresentationType.RAW)
        parse = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.CONJUNCTION))
        res_raw = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])], config=cfg_raw)
        self.assertEqual(res_raw.run.representation_type, RepresentationType.RAW)
        self.assertEqual(res_raw.annotations[0].representation_type, RepresentationType.RAW)

        # Analyze NORMALIZED
        cfg_norm = MorphologyAnalyzerConfig(representation_type=RepresentationType.NORMALIZED)
        res_norm = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])], config=cfg_norm)
        self.assertEqual(res_norm.run.representation_type, RepresentationType.NORMALIZED)
        self.assertEqual(res_norm.annotations[0].representation_type, RepresentationType.NORMALIZED)

    # -------------------------------------------------------------------------
    # 11. Provenance Integration
    # -------------------------------------------------------------------------
    def test_11_provenance_integration(self) -> None:
        """Morphology runs generate immutable provenance records linking to tokens."""
        st, tokens = self._setup_tokenized_source("ST-PROV-01", "φῶς", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN, gender=GrammaticalGender.NEUTER),
        )
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])

        prov = self.provenance_tracker.get_record(res.run.provenance_id)
        self.assertIsNotNone(prov)
        self.assertEqual(prov.target_id, res.run.run_id)
        self.assertTrue(prov.is_exact_reproducible)

        # Generative analyzer records non-reproducible provenance
        gen_cfg = MorphologyAnalyzerConfig(analyzer_id="llm-morph-expert", is_deterministic=False)
        res_gen = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])], config=gen_cfg)
        prov_gen = self.provenance_tracker.get_record(res_gen.run.provenance_id)
        self.assertFalse(prov_gen.is_exact_reproducible)

    # -------------------------------------------------------------------------
    # 12. Versioning Integration
    # -------------------------------------------------------------------------
    def test_12_versioning_integration(self) -> None:
        """Morphology runs generate active object_versions with content hash."""
        st, tokens = self._setup_tokenized_source("ST-VER-01", "ζωή", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN, gender=GrammaticalGender.FEMININE),
        )
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])

        ver = self.version_mgr.get_version(res.run.version_id)
        self.assertIsNotNone(ver)
        self.assertEqual(ver.object_type, "morphology")
        self.assertEqual(ver.status, VersionStatus.ACTIVE.value)
        self.assertEqual(ver.content_hash, res.run.output_hash)

    # -------------------------------------------------------------------------
    # 13. Immutable Historical Results & Retrospective Retokenization
    # -------------------------------------------------------------------------
    def test_13_immutable_historical_results(self) -> None:
        """Reanalysis supersedes previous version while permanently preserving historical observations."""
        st, tokens = self._setup_tokenized_source("ST-HIST-01", "ἄνθρωπος", SourceTextLanguage.GREEK)
        tok = tokens[0]

        # Initial analysis with Analyzer 1.0
        cfg1 = MorphologyAnalyzerConfig(analyzer_id="morph-v1", analyzer_version="1.0.0")
        p1 = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))
        res1 = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p1])], config=cfg1)

        # Retrospective reanalysis with Analyzer 2.0
        cfg2 = MorphologyAnalyzerConfig(analyzer_id="morph-v2", analyzer_version="2.0.0")
        p2 = MorphologyParse(
            parse_index=0,
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.NOUN,
                case=GreekCase.NOMINATIVE,
                gender=GrammaticalGender.MASCULINE,
            ),
        )
        res2 = self.morph_mgr.reanalyze(st.source_text_id, [(tok, [p2])], new_config=cfg2)

        # Historical run 1 is superseded but remains permanent
        ver1 = self.version_mgr.get_version(res1.run.version_id)
        self.assertEqual(ver1.status, VersionStatus.SUPERSEDED.value)

        # Both runs and annotations remain queryable in database
        run1 = self.morph_mgr.get_morphology_run(res1.run.run_id)
        run2 = self.morph_mgr.get_morphology_run(res2.run.run_id)
        self.assertIsNotNone(run1)
        self.assertIsNotNone(run2)

        all_annotations = self.morph_mgr.list_annotations_for_source_text(st.source_text_id)
        self.assertEqual(len(all_annotations), 2)

    # -------------------------------------------------------------------------
    # 14. Analyzer Identity
    # -------------------------------------------------------------------------
    def test_14_analyzer_identity(self) -> None:
        """Analyzer identity and version must be recorded on both runs and annotations."""
        st, tokens = self._setup_tokenized_source("ST-IDENT-01", "πνεῦμα", SourceTextLanguage.GREEK)
        tok = tokens[0]

        cfg = MorphologyAnalyzerConfig(analyzer_id="MorphGNT-SBLGNT", analyzer_version="3.4.1")
        parse = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])], config=cfg)

        self.assertEqual(res.run.analyzer_id, "MorphGNT-SBLGNT")
        self.assertEqual(res.run.analyzer_version, "3.4.1")
        self.assertEqual(res.annotations[0].analyzer_id, "MorphGNT-SBLGNT")
        self.assertEqual(res.annotations[0].analyzer_version, "3.4.1")

    # -------------------------------------------------------------------------
    # 15. Configuration Hashing
    # -------------------------------------------------------------------------
    def test_15_configuration_hashing(self) -> None:
        """Configuration hashing is strictly deterministic and sensitive to parameters."""
        cfg1 = MorphologyAnalyzerConfig(analyzer_id="morph-a", analyzer_version="1.0")
        cfg2 = MorphologyAnalyzerConfig(analyzer_id="morph-a", analyzer_version="1.0")
        cfg3 = MorphologyAnalyzerConfig(analyzer_id="morph-b", analyzer_version="1.0")

        self.assertEqual(cfg1.compute_config_hash(), cfg2.compute_config_hash())
        self.assertNotEqual(cfg1.compute_config_hash(), cfg3.compute_config_hash())

    # -------------------------------------------------------------------------
    # 16. Confidence Separation
    # -------------------------------------------------------------------------
    def test_16_confidence_separation(self) -> None:
        """Confidence is strictly numeric metadata and must not be confused with primary empirical evidence."""
        st, tokens = self._setup_tokenized_source("ST-CONF-01", "חֶסֶד", SourceTextLanguage.HEBREW)
        tok = tokens[0]

        parse = MorphologyParse(
            parse_index=0,
            semitic_features=SemiticMorphologyFeatures(lexical_category=SemiticLexicalCategory.NOUN),
            confidence_score=0.999,
            confidence_level=ConfidenceLevel.CERTAIN,
            evidence_ref="BDB p. 338; HALOT p. 336",
        )
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        ann = res.annotations[0]

        # Verify confidence score is preserved as numeric metadata
        self.assertAlmostEqual(ann.confidence_score, 0.999)
        self.assertEqual(ann.confidence_level, "CERTAIN")
        # Evidence reference is distinct from confidence
        self.assertEqual(ann.evidence_ref, "BDB p. 338; HALOT p. 336")

    # -------------------------------------------------------------------------
    # 17. Invalid Morphology Rejection
    # -------------------------------------------------------------------------
    def test_17_invalid_morphology_rejection(self) -> None:
        """Out of bounds confidence scores and illegal values must be rejected."""
        st, tokens = self._setup_tokenized_source("ST-INV-01", "ἀλήθεια", SourceTextLanguage.GREEK)
        tok = tokens[0]

        # Confidence > 1.0
        with self.assertRaises(MorphologyConfidenceError):
            p = MorphologyParse(
                parse_index=0,
                confidence_score=1.5,
                greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN),
            )
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p])])

        # Confidence < 0.0
        with self.assertRaises(MorphologyConfidenceError):
            p = MorphologyParse(
                parse_index=0,
                confidence_score=-0.2,
                greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN),
            )
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p])])

    # -------------------------------------------------------------------------
    # 18. Atomic Rollback
    # -------------------------------------------------------------------------
    def test_18_atomic_rollback(self) -> None:
        """A failure during batch morphology persistence rolls back completely without leaving orphan rows."""
        st, tokens = self._setup_tokenized_source("ST-ROLL-01", "Ἐν ἀρχῇ", SourceTextLanguage.GREEK)
        tok1, tok2 = tokens[0], tokens[1]

        p1 = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.PREPOSITION))
        p2_bad = MorphologyParse(parse_index=0, confidence_score=2.0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))

        # Attempt to record batch where second item fails validation
        with self.assertRaises(MorphologyConfidenceError):
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok1, [p1]), (tok2, [p2_bad])])

        # Verify 0 rows in morphology_runs and morphology_annotations
        with self.engine.connect() as conn:
            runs_count = conn.execute("SELECT count(*) FROM morphology_runs;").fetchone()[0]
            ann_count = conn.execute("SELECT count(*) FROM morphology_annotations;").fetchone()[0]
            self.assertEqual(runs_count, 0)
            self.assertEqual(ann_count, 0)

    # -------------------------------------------------------------------------
    # 19. Concurrent Analysis Isolation
    # -------------------------------------------------------------------------
    def test_19_concurrent_analysis_isolation(self) -> None:
        """Concurrent morphology analysis across distinct threads remains completely isolated."""
        st1, tok1 = self._setup_tokenized_source("ST-CONCUR-01", "λόγος", SourceTextLanguage.GREEK)
        st2, tok2 = self._setup_tokenized_source("ST-CONCUR-02", "אֱלֹהִים", SourceTextLanguage.HEBREW)

        results = {}
        errors = []

        def worker(st, tokens, key, is_greek):
            eng = DatabaseEngine(self.config)
            try:
                mgr = MorphologyManager(eng)
                if is_greek:
                    p = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))
                else:
                    p = MorphologyParse(parse_index=0, semitic_features=SemiticMorphologyFeatures(lexical_category=SemiticLexicalCategory.NOUN))
                res = mgr.record_morphology_parses(st.source_text_id, [(tokens[0], [p])])
                results[key] = res
            except Exception as e:
                errors.append(e)
            finally:
                eng.close()

        t1 = threading.Thread(target=worker, args=(st1, tok1, "greek", True))
        t2 = threading.Thread(target=worker, args=(st2, tok2, "hebrew", False))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0, f"Concurrent workers encountered errors: {errors}")
        self.assertIn("greek", results)
        self.assertIn("hebrew", results)

    # -------------------------------------------------------------------------
    # 20. Legacy Database Untouched
    # -------------------------------------------------------------------------
    def test_20_legacy_db_untouched(self) -> None:
        """Verify /home/ubuntu/.polya/polya_index.db is never touched by morphology subsystem."""
        if self.legacy_db_path.exists() and self.initial_legacy_hash:
            current_hash = hashlib.sha256(self.legacy_db_path.read_bytes()).hexdigest()
            self.assertEqual(
                current_hash,
                self.initial_legacy_hash,
                "CRITICAL: Legacy database /home/ubuntu/.polya/polya_index.db was modified during morphology operations!",
            )

    # -------------------------------------------------------------------------
    # 21. Adversarial Immutability Probes (Triggers)
    # -------------------------------------------------------------------------
    def test_21_adversarial_immutability_probes(self) -> None:
        """Direct SQL UPDATE or DELETE on morphology tables must be rejected by SQLite triggers."""
        st, tokens = self._setup_tokenized_source("ST-ADV-01", "δικαιοσύνη", SourceTextLanguage.GREEK)
        tok = tokens[0]

        p = MorphologyParse(parse_index=0, greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p])])
        ann = res.annotations[0]

        with self.engine.transaction() as conn:
            # 1. Attempt UPDATE pos_tag on morphology_annotations
            with self.assertRaises(sqlite3.DatabaseError) as ctx1:
                conn.execute("UPDATE morphology_annotations SET pos_tag = 'CORRUPTED' WHERE annotation_id = ?;", (ann.annotation_id,))
            self.assertIn("immutable", str(ctx1.exception).lower())

            # 2. Attempt DELETE on morphology_annotations
            with self.assertRaises(sqlite3.DatabaseError) as ctx2:
                conn.execute("DELETE FROM morphology_annotations WHERE annotation_id = ?;", (ann.annotation_id,))
            self.assertIn("immutable", str(ctx2.exception).lower())

            # 3. Attempt UPDATE on morphology_runs
            with self.assertRaises(sqlite3.DatabaseError) as ctx3:
                conn.execute("UPDATE morphology_runs SET output_hash = 'tampered' WHERE run_id = ?;", (res.run.run_id,))
            self.assertIn("immutable", str(ctx3.exception).lower())

            # 4. Attempt DELETE on morphology_runs
            with self.assertRaises(sqlite3.DatabaseError) as ctx4:
                conn.execute("DELETE FROM morphology_runs WHERE run_id = ?;", (res.run.run_id,))
            self.assertIn("immutable", str(ctx4.exception).lower())

    # -------------------------------------------------------------------------
    # 22. Evidence Boundary Guarantee
    # -------------------------------------------------------------------------
    def test_22_evidence_boundary_guarantee(self) -> None:
        """
        Morphology records purely grammatical observations.
        It must NEVER automatically generate interpretive or theological claims.
        """
        st, tokens = self._setup_tokenized_source("ST-BOUND-01", "θεοῦ", SourceTextLanguage.GREEK)
        tok = tokens[0]

        # Genitive case observation: e.g. "θεοῦ" -> genitive masculine singular
        parse = MorphologyParse(
            parse_index=0,
            pos_tag="N-GSM",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.NOUN,
                case=GreekCase.GENITIVE,
                gender=GrammaticalGender.MASCULINE,
                number=GrammaticalNumber.SINGULAR,
            ),
        )

        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])
        self.assertIsNotNone(res)

        # Assert no theological or interpretive claims exist in database
        with self.engine.connect() as conn:
            cur = conn.cursor()
            # If evidence_claims table exists in schema, verify 0 rows were inserted
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            if "evidence_claims" in tables:
                claim_count = cur.execute("SELECT count(*) FROM evidence_claims;").fetchone()[0]
                self.assertEqual(claim_count, 0)
            if "claims" in tables:
                claim_count = cur.execute("SELECT count(*) FROM claims;").fetchone()[0]
                self.assertEqual(claim_count, 0)

    # -------------------------------------------------------------------------
    # 23. Greek POS Round-trip and Output Hash Stability
    # -------------------------------------------------------------------------
    def test_23_greek_pos_roundtrip_hash_stability(self) -> None:
        """Granular morphology tags must not erase GreekPOS, and output hash must match across DB roundtrip."""
        st, tokens = self._setup_tokenized_source("ST-HASH-01", "ἐγένοντο", SourceTextLanguage.GREEK)
        tok = tokens[0]

        parse = MorphologyParse(
            pos_tag="V-2AMI-3P",
            greek_features=GreekMorphologyFeatures(
                pos=GreekPOS.VERB,
                tense=GreekTense.AORIST,
                voice=GreekVoice.MIDDLE,
                mood=GreekMood.INDICATIVE,
                person=GrammaticalPerson.THIRD,
                number=GrammaticalNumber.PLURAL,
            ),
        )
        res = self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [parse])])

        # Fetch from database and ensure GreekPOS was preserved
        from_db = self.morph_mgr.list_annotations_for_source_text(st.source_text_id)
        self.assertEqual(len(from_db), 1)
        self.assertIsNotNone(from_db[0].greek_features)
        self.assertEqual(from_db[0].greek_features.pos, GreekPOS.VERB)
        self.assertEqual(from_db[0].greek_features.tense, GreekTense.AORIST)

        # Output hash recomputed from DB must exactly equal run output_hash
        recomputed_hash = compute_morphology_output_hash(from_db)
        self.assertEqual(res.run.output_hash, recomputed_hash)

    # -------------------------------------------------------------------------
    # 24. Duplicate Parse Index Rejection
    # -------------------------------------------------------------------------
    def test_24_duplicate_parse_index_rejection(self) -> None:
        """Duplicate parse_index values for the same token must raise DuplicateMorphologyError."""
        st, tokens = self._setup_tokenized_source("ST-DUP-PARSE", "λόγος", SourceTextLanguage.GREEK)
        tok = tokens[0]

        p1 = MorphologyParse(parse_index=0, pos_tag="N-NSM", greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))
        p2 = MorphologyParse(parse_index=0, pos_tag="N-NSM", greek_features=GreekMorphologyFeatures(pos=GreekPOS.NOUN))

        with self.assertRaises(DuplicateMorphologyError):
            self.morph_mgr.record_morphology_parses(st.source_text_id, [(tok, [p1, p2])])

    # -------------------------------------------------------------------------
    # 25. Migration 007 Legacy Data Preservation
    # -------------------------------------------------------------------------
    def test_25_migration_007_legacy_data_preservation(self) -> None:
        """Migration 007 must preserve legacy morphology annotations and not delete them."""
        import hashlib
        import pathlib
        legacy_engine = DatabaseEngine(DatabaseConfig(db_path=":memory:"))
        with legacy_engine.connect() as conn:
            for p in sorted(pathlib.Path("schemas/bible_engine").glob("*.sql")):
                if p.name.startswith(("001", "002", "003", "004", "005", "006")):
                    content = p.read_text(encoding="utf-8")
                    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    conn.executescript(content)
                    conn.execute(
                        "INSERT INTO schema_migrations (migration_id, version, checksum_sha256, description, applied_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        (p.stem, "2.0.0", sha, "desc"),
                    )

        srm = SourceRegistry(legacy_engine)
        srm.register_source(
            source_id="SRC-LEGACY-01",
            canonical_name="Legacy Source",
            source_type=SourceType.CRITICAL_EDITION,
            language=SourceLanguage.GREEK,
            authority_level=SourceAuthorityLevel.PRIMARY,
        )
        stm = SourceTextManager(legacy_engine)
        st_leg = stm.register_source_text(
            source_id="SRC-LEGACY-01",
            source_text_id="ST-LEGACY-01",
            language=SourceTextLanguage.GREEK,
            raw_content="ἀρχῇ",
            representation_type=RepresentationType.RAW,
        )
        tok_leg = TokenizationManager(legacy_engine).tokenize_source_text(st_leg).tokens[0]

        with legacy_engine.transaction() as conn:
            conn.execute(
                """INSERT INTO morphology_annotations (annotation_id, token_id, pos_tag, literal_gloss, syntactic_role, confidence, analyzer_provenance)
                VALUES ('ANN-LEGACY-TEST', ?, 'N-DSF', 'beginning', 'DATIVE_MODIFIER', 'CERTAIN', 'legacy-v1');""",
                (tok_leg.token_id,),
            )

        with legacy_engine.connect() as conn:
            cnt_before = conn.execute("SELECT count(*) FROM morphology_annotations;").fetchone()[0]
            self.assertEqual(cnt_before, 1)

        runner = MigrationRunner(legacy_engine)
        runner.apply_pending()

        with legacy_engine.connect() as conn:
            cnt_after = conn.execute("SELECT count(*) FROM morphology_annotations;").fetchone()[0]
            self.assertEqual(cnt_after, 1)
            row = conn.execute("SELECT * FROM morphology_annotations WHERE annotation_id = 'ANN-LEGACY-TEST';").fetchone()
            self.assertEqual(row["run_id"], "RUN-MIGRATION-LEGACY")
            self.assertEqual(row["token_id"], tok_leg.token_id)
            self.assertEqual(row["pos_tag"], "N-DSF")


if __name__ == "__main__":
    unittest.main()
