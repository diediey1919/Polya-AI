"""
Test Suite for Discourse & Context Foundation Subsystem (Task 2.7).
Verifies:
  - Discourse units anchored to token spans with clause linkage
  - Discourse segments spanning units, with hierarchy
  - Typed discourse relations with justification basis and connector-token anchor
  - Context layers at IMMEDIATE / PERICOPE / BOOK / CORPUS scope; CONTEXT IS NOT EVIDENCE
  - Discourse participants; roles never assert identity
  - Anaphoric / cataphoric / deictic continuity candidate sets with preserved multiplicity
  - Information-structure foundation (topic / focus / markedness / marking device)
  - Ambiguity preservation (unresolved ambiguity is a first-class immutable record)
  - Firewalls: context, morphology-alone, translation, syntax, theology, identity, frequency, language
  - Provenance, versioning, reanalysis/supersession, transactional rollback
  - SQLite triggers preventing mutation/deletion of discourse records
  - Migration 011 applied and checksums 001-010 unchanged
  - Legacy runtime DB untouched
"""

from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.discourse import (
    compute_discourse_output_hash,
    ContextLayerDefinition,
    ContextLayerScope,
    ContextObservationKind,
    ContinuityCandidateDefinition,
    ContinuityResolutionStatus,
    ContinuityType,
    DiscourseAmbiguityDefinition,
    DiscourseAmbiguityResolution,
    DiscourseAmbiguityType,
    DiscourseAnalyzerConfig,
    DiscourseConfidence,
    DiscourseEvidenceStatus,
    DiscourseManager,
    DiscourseRelationDefinition,
    DiscourseRelationType,
    DiscourseSegmentDefinition,
    DiscourseSegmentType,
    DiscourseUnitDefinition,
    DiscourseUnitType,
    GrammaticalNumber,
    GrammaticalPerson,
    InformationRole,
    InformationStructureDefinition,
    JustificationBasis,
    Markedness,
    MarkingDevice,
    ParticipantDefinition,
    ParticipantRole,
    ParticipantRoleStatus,
    RelationDirectionality,
)
from bible_engine.errors import (
    DiscourseAmbiguityFirewallError,
    DiscourseContextFirewallError,
    DiscourseFrequencyFirewallError,
    DiscourseIdentityFirewallError,
    DiscourseMorphologyFirewallError,
    DiscourseNotFoundError,
    DiscourseOrphanError,
    DiscourseSpanValidationError,
    DiscourseSubsystemError,
    DiscourseTheologyFirewallError,
    DiscourseTokenNotFoundError,
    DiscourseTranslationFirewallError,
    DuplicateDiscourseError,
)
from bible_engine.migrations import MigrationRunner, compute_sha256
from bible_engine.referential import (
    CanonicalCorpus,
    EntityType,
    OntologicalCategory,
    ReferentialManager,
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
from bible_engine.errors import SourceTextNotFoundError
from bible_engine.tokenization import TokenizationManager, TokenRecord

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "bible_engine"

# Genesis-style Greek clause, four tokens:
# 0 ἐν  1 ἀρχῇ  2 ἦν  3 ὁ
CLAUSE_TEXT = "ἐν ἀρχῇ ἦν ὁ"


class TestBibleEngineDiscourse(unittest.TestCase):
    """Rigorous verification suite for the Discourse & Context Foundation Subsystem."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_discourse.db"
        self.config = DatabaseConfig(db_path=str(self.db_path))
        self.engine = DatabaseEngine(self.config)

        self.runner = MigrationRunner(self.engine)
        self.runner.apply_pending()

        # Corpus scaffolding required by passage/pericope/book foreign keys.
        with self.engine.transaction() as conn:
            conn.execute("INSERT INTO canons VALUES ('CAN-PROT', 'Protestan', '', '2026-09-30');")
            conn.execute("INSERT INTO testaments VALUES ('NT', 'CAN-PROT', 'Perjanjian Baru', 2);")
            conn.execute(
                "INSERT INTO books VALUES ('JOH', 'NT', 43, 'Yohanes', 'John', 'GREEK', 21);"
            )
            conn.execute(
                "INSERT INTO pericopes VALUES ('PER-JOH-01', 'JOH', 'Yohanes 1:1-3', 1, 1, 1, 3, "
                "'NARRATIVE', 'NA28_SECTION', 'HIGH', 'VALIDATED', '2.0.0', '2026-09-30');"
            )
            conn.execute("INSERT INTO passages VALUES ('JOH-01-01', 'PER-JOH-01', 'JOH', 1, 1, 1);")

        self.source_registry = SourceRegistry(self.engine)
        self.source_text_mgr = SourceTextManager(self.engine)
        self.token_mgr = TokenizationManager(self.engine)
        self.ref_mgr = ReferentialManager(self.engine)
        self.disc_mgr = DiscourseManager(self.engine)

    def tearDown(self) -> None:
        self.engine.close()
        self.temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _setup_tokens(
        self,
        source_id: str = "SRC-NA28",
        source_text_id: str = "ST-JOH-01",
        content: str = CLAUSE_TEXT,
        language: SourceTextLanguage = SourceTextLanguage.GREEK,
    ) -> Tuple[SourceTextRecord, List[TokenRecord]]:
        """Register source, source text, and tokenize it against JOH-01-01."""
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
            passage_id="JOH-01-01",
        )
        tok_res = self.token_mgr.tokenize_source_text(st, passage_id="JOH-01-01")
        return st, tok_res.tokens

    def _register_entities(self) -> None:
        """Register the Logos entity used by participant and continuity tests."""
        self.ref_mgr.register_entity(
            entity_id="ENT-LOGOS",
            standard_name="Firman",
            entity_type=EntityType.DIVINE,
            ontological_category=OntologicalCategory.LITERAL_ENTITY,
            description="Firman yang kekal",
            language=SourceTextLanguage.GREEK,
            canonical_corpus=CanonicalCorpus.NEW_TESTAMENT,
        )

    def _baseline_unit(
        self,
        tokens: List[TokenRecord],
        unit_id: str = "DU-01",
        unit_order: int = 0,
        evidence_status: DiscourseEvidenceStatus = DiscourseEvidenceStatus.INFERRED,
    ) -> DiscourseUnitDefinition:
        return DiscourseUnitDefinition(
            unit_id=unit_id,
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[-1].token_id,
            unit_type=DiscourseUnitType.CLAUSE_UNIT,
            unit_order=unit_order,
            evidence_status=evidence_status,
            raw_unit_surface=CLAUSE_TEXT,
        )

    # -------------------------------------------------------------------------
    # 1-2. Discourse units & segments
    # -------------------------------------------------------------------------

    def test_01_discourse_unit_registration(self) -> None:
        """A discourse unit persists with token span, ordering, and provenance."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit])

        self.assertEqual(res.run.unit_count, 1)
        self.assertEqual(len(res.units), 1)
        self.assertEqual(res.units[0].unit_id, "DU-01")
        self.assertEqual(res.units[0].source_text_id, st.source_text_id)
        self.assertTrue(res.units[0].is_immutable)
        self.assertIsNotNone(res.units[0].passage_id)
        self.assertTrue(res.run.provenance_id.startswith("PRV-"))
        self.assertTrue(res.run.version_id.startswith("VER-discourse-"))

    def test_02_discourse_segment_spanning_units(self) -> None:
        """A segment may span multiple units and reference them as boundaries."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[1].token_id,
            end_token_id=tokens[2].token_id,
            unit_type=DiscourseUnitType.CLAUSE_UNIT,
            unit_order=1,
            raw_unit_surface="ἀρχῇ ἦν",
        )
        seg = DiscourseSegmentDefinition(
            segment_id="DS-01",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[3].token_id,
            segment_type=DiscourseSegmentType.NARRATIVE,
            segment_order=0,
            start_unit_id="DU-01",
            end_unit_id="DU-02",
            raw_segment_surface=CLAUSE_TEXT,
        )

        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2], [seg])
        self.assertEqual(res.run.unit_count, 2)
        self.assertEqual(res.run.segment_count, 1)
        self.assertEqual(res.segments[0].start_unit_id, "DU-01")
        self.assertEqual(res.segments[0].end_unit_id, "DU-02")

    # -------------------------------------------------------------------------
    # 3. Span validation & orphan rejection
    # -------------------------------------------------------------------------

    def test_03_reversed_span_rejected(self) -> None:
        """A unit whose start token follows its end token is rejected."""
        st, tokens = self._setup_tokens()
        bad = DiscourseUnitDefinition(
            unit_id="DU-REV",
            start_token_id=tokens[3].token_id,
            end_token_id=tokens[0].token_id,
            raw_unit_surface="reversed",
        )
        with self.assertRaises(DiscourseSpanValidationError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [bad])

    def test_04_orphan_unit_token_rejected(self) -> None:
        """A unit anchored to a token outside the source text is rejected."""
        st, tokens = self._setup_tokens()
        bad = DiscourseUnitDefinition(
            unit_id="DU-ORPHAN",
            start_token_id="TOK-NONEXISTENT",
            end_token_id=tokens[0].token_id,
            raw_unit_surface="orphan",
        )
        with self.assertRaises(DiscourseTokenNotFoundError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [bad])

    def test_05_orphan_segment_unit_rejected(self) -> None:
        """A segment referencing a unit absent from the run is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        seg = DiscourseSegmentDefinition(
            segment_id="DS-ORPHAN",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[1].token_id,
            start_unit_id="DU-ABSENT",
            raw_segment_surface="x",
        )
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], [seg])

    def test_06_nonexistent_source_text_rejected(self) -> None:
        """Discourse analysis against an unknown source text is rejected."""
        with self.assertRaises(SourceTextNotFoundError):
            self.disc_mgr.record_discourse_analysis(
                "ST-DOES-NOT-EXIST",
                [
                    DiscourseUnitDefinition(
                        unit_id="DU-01",
                        start_token_id="T1",
                        end_token_id="T2",
                        raw_unit_surface="x",
                    )
                ],
            )

    def test_07_missing_source_text_id_rejected(self) -> None:
        """Discourse artifacts cannot be persisted without a source text anchor."""
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(
                None,
                [
                    DiscourseUnitDefinition(
                        unit_id="DU-01",
                        start_token_id="T1",
                        end_token_id="T2",
                        raw_unit_surface="x",
                    )
                ],
            )

    # -------------------------------------------------------------------------
    # 8-10. Discourse relations
    # -------------------------------------------------------------------------

    def test_08_discourse_relation_registration(self) -> None:
        """A discourse relation persists with its justification basis and anchors."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-01",
            source_ref_id="DU-01",
            target_ref_id="DU-02",
            relation_type=DiscourseRelationType.ELABORATION,
            grammatical_justification="Observable continuation of the same narrative clause chain.",
            justification_basis=JustificationBasis.SYNTACTIC_STRUCTURE,
            directionality=RelationDirectionality.FORWARD,
            confidence_level=DiscourseConfidence.HIGH,
        )
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2], relations=[rel])
        self.assertEqual(res.run.relation_count, 1)
        self.assertEqual(res.relations[0].relation_type, DiscourseRelationType.ELABORATION)
        self.assertEqual(res.relations[0].justification_basis, JustificationBasis.SYNTACTIC_STRUCTURE)

    def test_09_relation_to_absent_unit_rejected(self) -> None:
        """A discourse relation referencing an absent unit is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        rel = DiscourseRelationDefinition(
            relation_id="DR-ORPHAN",
            source_ref_id="DU-01",
            target_ref_id="DU-ABSENT",
            relation_type=DiscourseRelationType.CONTRAST,
            grammatical_justification="contrast",
        )
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], relations=[rel])

    def test_10_self_referential_relation_rejected(self) -> None:
        """A discourse relation may not relate a unit to itself."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        rel = DiscourseRelationDefinition(
            relation_id="DR-SELF",
            source_ref_id="DU-01",
            target_ref_id="DU-01",
            relation_type=DiscourseRelationType.PARALLEL,
            grammatical_justification="parallel",
        )
        with self.assertRaises(DiscourseSubsystemError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], relations=[rel])

    # -------------------------------------------------------------------------
    # 11-12. Morphology-alone firewall
    # -------------------------------------------------------------------------

    def test_11_conjunction_justification_requires_connector_token(self) -> None:
        """A relation justified by a conjunction must cite the connector token."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-CONJ",
            source_ref_id="DU-01",
            target_ref_id="DU-02",
            relation_type=DiscourseRelationType.RESULT,
            grammatical_justification="Conjunction marks a result relation.",
            justification_basis=JustificationBasis.EXPLICIT_CONJUNCTION,
        )
        with self.assertRaises(DiscourseMorphologyFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2], relations=[rel])

    def test_12_conjunction_justification_with_connector_accepted(self) -> None:
        """The same relation is accepted once the actual connector token is cited."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-CONJ-OK",
            source_ref_id="DU-01",
            target_ref_id="DU-02",
            relation_type=DiscourseRelationType.RESULT,
            grammatical_justification="Conjunction token marks a result relation.",
            justification_basis=JustificationBasis.EXPLICIT_CONJUNCTION,
            connector_token_id=tokens[2].token_id,
        )
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2], relations=[rel])
        self.assertEqual(res.relations[0].connector_token_id, tokens[2].token_id)

    def test_13_morphology_alone_pattern_rejected(self) -> None:
        """A relation whose justification states a morphological derivation alone is rejected."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-MORPH",
            source_ref_id="DU-01",
            target_ref_id="DU-02",
            relation_type=DiscourseRelationType.PURPOSE,
            grammatical_justification="Gender proves the relation.",
            justification_basis=JustificationBasis.GRAMMATICAL_MARKER,
            connector_token_id=tokens[2].token_id,
        )
        with self.assertRaises(DiscourseMorphologyFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2], relations=[rel])

    def test_14_morphology_alone_pattern_rejected_at_schema_level(self) -> None:
        """The schema CHECK independently blocks marker/schema justification without a connector."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO discourse_relations (
                        relation_id, run_id, source_text_id, version_id, provenance_id,
                        source_kind, source_ref_id, target_kind, target_ref_id,
                        relation_type, directionality, grammatical_justification,
                        justification_basis, evidence_status, created_at, is_immutable
                    ) VALUES (
                        'DR-SCHEMA', ?, ?, ?, ?,
                        'UNIT', 'DU-01', 'UNIT', 'DU-01',
                        'CONTRAST', 'FORWARD', 'schema-level attempt',
                        'EXPLICIT_CONJUNCTION', '[INFERRED]', '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                    ),
                )

    def test_15_relation_connector_token_outside_source_rejected(self) -> None:
        """A connector token must belong to the analyzed source text."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        seg = DiscourseSegmentDefinition(
            segment_id="DS-01",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[3].token_id,
            segment_type=DiscourseSegmentType.PROPOSITIONAL,
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-BAD-CONN",
            source_ref_id="DU-01",
            target_ref_id="DS-01",
            source_kind="UNIT",
            target_kind="SEGMENT",
            relation_type=DiscourseRelationType.ELABORATION,
            grammatical_justification="marker",
            justification_basis=JustificationBasis.GRAMMATICAL_MARKER,
            connector_token_id="TOK-ABSENT",
        )
        with self.assertRaises(DiscourseTokenNotFoundError):
            self.disc_mgr.record_discourse_analysis(
                st.source_text_id, [unit], [seg], [rel]
            )

    # -------------------------------------------------------------------------
    # 16-19. Context layers: CONTEXT IS NOT EVIDENCE
    # -------------------------------------------------------------------------

    def test_16_context_layer_registration(self) -> None:
        """Context layers persist with scope and observation kind; is_evidence stays 0."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-01",
            layer_scope=ContextLayerScope.IMMEDIATE,
            observation_kind=ContextObservationKind.PARTICIPANT_CONTINUITY,
            observation="Same participant remains subject across the following clause.",
            anchor_unit_id="DU-01",
        )
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])
        self.assertFalse(res.context_layers[0].is_evidence)
        self.assertEqual(res.context_layers[0].layer_scope, ContextLayerScope.IMMEDIATE)

    def test_17_context_layer_cannot_claim_grammatical_status(self) -> None:
        """A context observation may not claim [GRAMMATICALLY ESTABLISHED]: context is not evidence."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-CLAIM",
            layer_scope=ContextLayerScope.PERICOPE,
            observation_kind=ContextObservationKind.TOPIC_CONTINUITY,
            observation="Pericope topic continues.",
            evidence_status=DiscourseEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
        )
        with self.assertRaises(DiscourseContextFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_18_context_layer_explicit_requires_evidence_anchor(self) -> None:
        """A context observation claiming [EXPLICIT] without an evidence anchor is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-EXPLICIT",
            layer_scope=ContextLayerScope.BOOK,
            observation_kind=ContextObservationKind.GENRE_FRAME,
            observation="Gospel narrative frame.",
            evidence_status=DiscourseEvidenceStatus.EXPLICIT,
        )
        with self.assertRaises(DiscourseContextFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_19_context_layer_schema_pins_is_evidence_to_zero(self) -> None:
        """The schema itself refuses to store a context layer as evidence."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO discourse_context_layers (
                        context_layer_id, run_id, source_text_id, version_id, provenance_id,
                        layer_scope, observation_kind, observation, evidence_status,
                        is_evidence, created_at, is_immutable
                    ) VALUES (
                        'CL-BAD', ?, ?, ?, ?,
                        'BOOK', 'OTHER', 'attempt to store as evidence', '[EXPLICIT]',
                        1, '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                    ),
                )

    def test_20_context_layer_anchor_absent_unit_rejected(self) -> None:
        """A context layer anchored to a unit absent from the run is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-ORPHAN",
            layer_scope=ContextLayerScope.IMMEDIATE,
            observation_kind=ContextObservationKind.OTHER,
            observation="orphan anchor",
            anchor_unit_id="DU-ABSENT",
        )
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_21_unresolved_context_scope_cannot_cite_evidence(self) -> None:
        """An unresolved context scope must not be converted into evidence."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-UNRES",
            layer_scope=ContextLayerScope.UNRESOLVED,
            observation_kind=ContextObservationKind.BOUNDARY_OBSERVATION,
            observation="Boundary scope cannot be determined from the available observations.",
            evidence_id="EVID-ABSENT",
        )
        with self.assertRaises(DiscourseContextFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    # -------------------------------------------------------------------------
    # 22-24. Participants
    # -------------------------------------------------------------------------

    def test_22_participant_registration(self) -> None:
        """Participants persist with role, grammatical features, and identity pinned to 0."""
        st, tokens = self._setup_tokens()
        self._register_entities()
        unit = self._baseline_unit(tokens)
        part = ParticipantDefinition(
            participant_id="PT-01",
            participant_role=ParticipantRole.SPEAKER,
            role_status=ParticipantRoleStatus.OBSERVED,
            unit_id="DU-01",
            entity_id="ENT-LOGOS",
            grammatical_person=GrammaticalPerson.THIRD,
            grammatical_number=GrammaticalNumber.SINGULAR,
            anchor_token_id=tokens[2].token_id,
            evidence_status=DiscourseEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
        )
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], participants=[part])
        self.assertEqual(res.participants[0].participant_role, ParticipantRole.SPEAKER)
        self.assertFalse(res.participants[0].identity_asserted)

    def test_23_participant_schema_pins_identity_asserted_to_zero(self) -> None:
        """The schema refuses a participant record that asserts identity."""
        st, tokens = self._setup_tokens()
        self._register_entities()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO discourse_participants (
                        participant_id, run_id, source_text_id, version_id, provenance_id,
                        participant_role, role_status, evidence_status, identity_asserted,
                        created_at, is_immutable
                    ) VALUES (
                        'PT-BAD', ?, ?, ?, ?,
                        'SPEAKER', 'OBSERVED', '[INFERRED]', 1,
                        '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                    ),
                )

    def test_24_participant_absent_entity_rejected(self) -> None:
        """A participant referencing an unknown entity is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        part = ParticipantDefinition(
            participant_id="PT-ORPHAN",
            participant_role=ParticipantRole.SPEAKER,
            unit_id="DU-01",
            entity_id="ENT-ABSENT",
        )
        with self.assertRaises(DiscourseNotFoundError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], participants=[part])

    # -------------------------------------------------------------------------
    # 25-29. Continuity candidates (ambiguity preservation)
    # -------------------------------------------------------------------------

    def test_25_continuity_candidate_set_preserved(self) -> None:
        """Two competing antecedents for one referring token are both stored, none collapsed."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        c1 = ContinuityCandidateDefinition(
            candidate_id="CC-01",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            resolution_status=ContinuityResolutionStatus.UNRESOLVED_AMBIGUOUS,
            candidate_rank=1,
            candidate_antecedent_token_id=tokens[0].token_id,
            antecedent_distance_tokens=3,
            resolution_rationale="Nearest preceding substantive candidate.",
        )
        c2 = ContinuityCandidateDefinition(
            candidate_id="CC-02",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            resolution_status=ContinuityResolutionStatus.UNRESOLVED_AMBIGUOUS,
            candidate_rank=2,
            candidate_antecedent_token_id=tokens[1].token_id,
            antecedent_distance_tokens=2,
            resolution_rationale="Alternative candidate within the same clause chain.",
        )
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [unit], continuity_candidates=[c1, c2]
        )
        self.assertEqual(res.run.continuity_candidate_count, 2)
        self.assertEqual(len(res.continuity_candidates), 2)
        for rec in res.continuity_candidates:
            self.assertFalse(rec.is_resolved)
            self.assertFalse(rec.identity_asserted)

    def test_26_resolved_candidate_requires_antecedent(self) -> None:
        """A candidate marked resolved without any antecedent anchor is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        bad = ContinuityCandidateDefinition(
            candidate_id="CC-BAD",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            resolution_status=ContinuityResolutionStatus.PREFERRED_CANDIDATE,
            is_resolved=True,
        )
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], continuity_candidates=[bad])

    def test_27_resolved_candidate_schema_requires_anchor(self) -> None:
        """The schema independently blocks a resolved candidate with no antecedent anchor."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO referential_continuity_candidates (
                        candidate_id, run_id, source_text_id, version_id, provenance_id,
                        referring_token_id, continuity_type, candidate_rank, is_resolved,
                        resolution_status, multiplicity_preserved, evidence_status,
                        identity_asserted, created_at, is_immutable
                    ) VALUES (
                        'CC-SCHEMA', ?, ?, ?, ?,
                        ?, 'ANAPHORIC', 1, 1,
                        'PREFERRED_CANDIDATE', 1, '[INFERRED]',
                        0, '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                        tokens[0].token_id,
                    ),
                )

    def test_28_continuity_schema_pins_multiplicity_preserved(self) -> None:
        """Multiplicity preservation is pinned to 1: candidate sets cannot be collapsed in storage."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO referential_continuity_candidates (
                        candidate_id, run_id, source_text_id, version_id, provenance_id,
                        referring_token_id, continuity_type, candidate_rank, is_resolved,
                        resolution_status, multiplicity_preserved, evidence_status,
                        identity_asserted, created_at, is_immutable
                    ) VALUES (
                        'CC-COLLAPSE', ?, ?, ?, ?,
                        ?, 'ANAPHORIC', 1, 0,
                        'CANDIDATE_SET', 0, '[INFERRED]',
                        0, '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                        tokens[0].token_id,
                    ),
                )

    def test_29_deictic_and_cataphoric_types_supported(self) -> None:
        """Deictic and cataphoric candidate types are representable alongside anaphoric."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        candidates = [
            ContinuityCandidateDefinition(
                candidate_id="CC-ANA",
                referring_token_id=tokens[3].token_id,
                continuity_type=ContinuityType.ANAPHORIC,
                candidate_antecedent_token_id=tokens[0].token_id,
            ),
            ContinuityCandidateDefinition(
                candidate_id="CC-CATA",
                referring_token_id=tokens[3].token_id,
                continuity_type=ContinuityType.CATAPHORIC,
                candidate_rank=2,
                candidate_antecedent_token_id=tokens[1].token_id,
            ),
            ContinuityCandidateDefinition(
                candidate_id="CC-DEIC",
                referring_token_id=tokens[1].token_id,
                continuity_type=ContinuityType.DEICTIC,
                resolution_status=ContinuityResolutionStatus.NO_CANDIDATE,
                candidate_rank=1,
            ),
        ]
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [unit], continuity_candidates=candidates
        )
        types = {c.continuity_type for c in res.continuity_candidates}
        self.assertEqual(
            types,
            {ContinuityType.ANAPHORIC, ContinuityType.CATAPHORIC, ContinuityType.DEICTIC},
        )

    # -------------------------------------------------------------------------
    # 30-32. Information structure
    # -------------------------------------------------------------------------

    def test_30_information_structure_registration(self) -> None:
        """Information structure persists with role, markedness, and marking device."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        info = InformationStructureDefinition(
            info_structure_id="IS-01",
            unit_id="DU-01",
            information_role=InformationRole.TOPIC,
            markedness=Markedness.MARKED,
            marking_device=MarkingDevice.WORD_ORDER,
            token_id=tokens[0].token_id,
            evidence_status=DiscourseEvidenceStatus.GRAMMATICALLY_ESTABLISHED,
        )
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [unit], information_structure=[info]
        )
        self.assertEqual(res.information_structure[0].information_role, InformationRole.TOPIC)
        self.assertEqual(res.information_structure[0].markedness, Markedness.MARKED)

    def test_31_information_structure_undetermined_is_representable(self) -> None:
        """An undetermined information role remains representable without forcing a reading."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        info = InformationStructureDefinition(
            info_structure_id="IS-UNDET",
            unit_id="DU-01",
            information_role=InformationRole.UNDETERMINED,
            markedness=Markedness.UNDETERMINED,
            marking_device=MarkingDevice.NONE_OBSERVED,
        )
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [unit], information_structure=[info]
        )
        self.assertEqual(res.information_structure[0].information_role, InformationRole.UNDETERMINED)

    def test_32_information_structure_absent_unit_rejected(self) -> None:
        """Information structure anchored to an absent unit is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        info = InformationStructureDefinition(
            info_structure_id="IS-ORPHAN",
            unit_id="DU-ABSENT",
            information_role=InformationRole.FOCUS,
        )
        with self.assertRaises(DiscourseOrphanError):
            self.disc_mgr.record_discourse_analysis(
                st.source_text_id, [unit], information_structure=[info]
            )

    # -------------------------------------------------------------------------
    # 33-35. Ambiguity preservation
    # -------------------------------------------------------------------------

    def test_33_ambiguity_preserved_with_competing_readings(self) -> None:
        """An unresolved ambiguity persists with all competing readings intact."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        amb = DiscourseAmbiguityDefinition(
            ambiguity_id="AMB-01",
            ambiguity_type=DiscourseAmbiguityType.RELATION_TYPE,
            subject_ref_id="DU-01",
            description="Elaboration and ground are both compatible with the available markers.",
            competing_interpretations=["ELABORATION", "GROUND"],
            resolution_status=DiscourseAmbiguityResolution.UNRESOLVED,
        )
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], ambiguities=[amb])
        self.assertEqual(res.run.ambiguity_count, 1)
        rec = res.ambiguities[0]
        self.assertTrue(rec.preservation_required)
        self.assertTrue(rec.collapse_prohibited)
        self.assertEqual(rec.competing_interpretation_count, 2)
        self.assertEqual(rec.resolution_status, DiscourseAmbiguityResolution.UNRESOLVED)

    def test_34_ambiguity_requires_competing_interpretations(self) -> None:
        """An ambiguity stating no competing reading is rejected: it would collapse the ambiguity."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        amb = DiscourseAmbiguityDefinition(
            ambiguity_id="AMB-EMPTY",
            ambiguity_type=DiscourseAmbiguityType.UNIT_BOUNDARY,
            subject_ref_id="DU-01",
            description="Boundary undecidable.",
            competing_interpretations=[],
        )
        with self.assertRaises(DiscourseAmbiguityFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], ambiguities=[amb])

    def test_35_ambiguity_schema_pins_collapse_prohibited(self) -> None:
        """The schema refuses an ambiguity record that permits collapse."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.engine.transaction() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO discourse_ambiguities (
                        ambiguity_id, run_id, source_text_id, version_id, provenance_id,
                        ambiguity_type, subject_ref_id, competing_interpretations_json,
                        competing_interpretation_count, resolution_status,
                        preservation_required, collapse_prohibited, description,
                        evidence_status, created_at, is_immutable
                    ) VALUES (
                        'AMB-BAD', ?, ?, ?, ?,
                        'OTHER', 'DU-01', '["A","B"]',
                        2, 'UNRESOLVED',
                        1, 0, 'attempt to permit collapse',
                        '[AMBIGUOUS]', '2026-09-30', 1
                    );
                    """,
                    (
                        res.run.run_id,
                        res.run.source_text_id,
                        res.run.version_id,
                        res.run.provenance_id,
                    ),
                )

    def test_36_ambiguity_resolution_requires_evidence(self) -> None:
        """Claiming an ambiguity resolved without an evidence anchor is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        amb = DiscourseAmbiguityDefinition(
            ambiguity_id="AMB-RESOLVED",
            ambiguity_type=DiscourseAmbiguityType.RELATION_TYPE,
            subject_ref_id="DU-01",
            description="Claims resolution without evidence.",
            competing_interpretations=["RESULT", "PURPOSE"],
            resolution_status=DiscourseAmbiguityResolution.RESOLVED,
        )
        with self.assertRaises(DiscourseAmbiguityFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], ambiguities=[amb])

    # -------------------------------------------------------------------------
    # 37-42. Firewalls
    # -------------------------------------------------------------------------

    def test_37_theology_firewall(self) -> None:
        """A discourse justification asserting a doctrinal claim is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-THEO",
            layer_scope=ContextLayerScope.CORPUS,
            observation_kind=ContextObservationKind.OTHER,
            observation="This context proves the trinity.",
        )
        with self.assertRaises(DiscourseTheologyFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_38_translation_firewall(self) -> None:
        """Discourse meaning derived from a translation is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-TRANS",
            layer_scope=ContextLayerScope.IMMEDIATE,
            observation_kind=ContextObservationKind.OTHER,
            observation="Dynamic equivalence requires this reading.",
        )
        with self.assertRaises(DiscourseTranslationFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_39_identity_firewall(self) -> None:
        """A discourse observation asserting ontological identity is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-ID",
            layer_scope=ContextLayerScope.IMMEDIATE,
            observation_kind=ContextObservationKind.OTHER,
            observation="The two figures are ontologically identical to one another.",
        )
        with self.assertRaises(DiscourseIdentityFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_40_frequency_firewall(self) -> None:
        """Truth derived from contextual frequency is rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        layer = ContextLayerDefinition(
            context_layer_id="CL-FREQ",
            layer_scope=ContextLayerScope.CORPUS,
            observation_kind=ContextObservationKind.LEXICAL_REPETITION,
            observation="Most common usage therefore the claim holds.",
        )
        with self.assertRaises(DiscourseFrequencyFirewallError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], context_layers=[layer])

    def test_41_language_firewall(self) -> None:
        """An entity whose language conflicts with the source text language is rejected."""
        st, tokens = self._setup_tokens(language=SourceTextLanguage.GREEK)
        self.ref_mgr.register_entity(
            entity_id="ENT-HEB",
            standard_name="Firman Ibrani",
            entity_type=EntityType.DIVINE,
            ontological_category=OntologicalCategory.LITERAL_ENTITY,
            description="Entitas berbahasa Ibrani",
            language=SourceTextLanguage.HEBREW,
            canonical_corpus=CanonicalCorpus.OLD_TESTAMENT,
        )
        unit = self._baseline_unit(tokens)
        part = ParticipantDefinition(
            participant_id="PT-LANG",
            participant_role=ParticipantRole.SPEAKER,
            unit_id="DU-01",
            entity_id="ENT-HEB",
        )
        with self.assertRaises(Exception) as ctx:
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit], participants=[part])
        self.assertIn("language", str(ctx.exception).lower())

    def test_42_unsupported_evidence_status_never_persisted(self) -> None:
        """A discourse artifact claiming [UNSUPPORTED] is rejected before persistence."""
        st, tokens = self._setup_tokens()
        unit = DiscourseUnitDefinition(
            unit_id="DU-UNSUP",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[-1].token_id,
            evidence_status=DiscourseEvidenceStatus.UNSUPPORTED,
            raw_unit_surface=CLAUSE_TEXT,
        )
        with self.assertRaises(DiscourseSubsystemError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit])

    # -------------------------------------------------------------------------
    # 43-45. Determinism, provenance, versioning
    # -------------------------------------------------------------------------

    def test_43_deterministic_output_hash_ignores_submission_order(self) -> None:
        """Two units submitted in either order yield the same discourse output hash."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-RUN1-01", 0)
        u2 = DiscourseUnitDefinition(
            unit_id="DU-RUN1-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        first_hash = compute_discourse_output_hash([u1, u2])
        second_hash = compute_discourse_output_hash([u2, u1])
        self.assertEqual(first_hash, second_hash)
        first = self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1, u2])
        self.assertEqual(first.run.output_hash, first_hash)

    def test_44_provenance_integration(self) -> None:
        """A discourse run records a provenance chain entry and is reproducible deterministically."""
        st, tokens = self._setup_tokens()
        res = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        self.assertTrue(res.run.is_exact_reproducible)
        self.assertIsNotNone(res.provenance.provenance_id)
        self.assertEqual(res.provenance.target_id, res.run.run_id)

    def test_45_reanalysis_supersedes_without_mutation(self) -> None:
        """Reanalysis creates a new version and supersedes the prior one without mutating history."""
        st, tokens = self._setup_tokens()
        first = self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        unit2 = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        u1_v2 = self._baseline_unit(tokens, "DU-01-V2", 0)
        second = self.disc_mgr.reanalyze(st.source_text_id, [u1_v2, unit2])

        self.assertNotEqual(first.run.run_id, second.run.run_id)
        self.assertEqual(self.disc_mgr.get_run(first.run.run_id).run_id, first.run.run_id)
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT status FROM object_versions WHERE version_id = ?;", (first.run.version_id,)
            )
            self.assertEqual(cur.fetchone()[0], "SUPERSEDED")

    def test_46_legacy_language_mismatch_rejected(self) -> None:
        """A Hebrew discourse run against a Greek source text is rejected by the language firewall."""
        st, tokens = self._setup_tokens(language=SourceTextLanguage.GREEK)
        self.ref_mgr.register_entity(
            entity_id="ENT-LANG-2",
            standard_name="Firman X",
            entity_type=EntityType.DIVINE,
            ontological_category=OntologicalCategory.LITERAL_ENTITY,
            description="Entitas",
            language=SourceTextLanguage.HEBREW,
        )
        unit = self._baseline_unit(tokens)
        cand = ContinuityCandidateDefinition(
            candidate_id="CC-LANG",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            candidate_antecedent_entity_id="ENT-LANG-2",
        )
        with self.assertRaises(Exception) as ctx:
            self.disc_mgr.record_discourse_analysis(
                st.source_text_id, [unit], continuity_candidates=[cand]
            )
        self.assertIn("language", str(ctx.exception).lower())

    # -------------------------------------------------------------------------
    # 47-49. Immutability & rollback
    # -------------------------------------------------------------------------

    def test_47_immutability_triggers_block_update_and_delete(self) -> None:
        """SQLite triggers prevent UPDATE and DELETE on every discourse table."""
        st, tokens = self._setup_tokens()
        self._register_entities()
        unit = self._baseline_unit(tokens)
        seg = DiscourseSegmentDefinition(
            segment_id="DS-01",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[3].token_id,
            segment_type=DiscourseSegmentType.NARRATIVE,
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-01",
            source_ref_id="DU-01",
            target_ref_id="DS-01",
            source_kind="UNIT",
            target_kind="SEGMENT",
            relation_type=DiscourseRelationType.ELABORATION,
            grammatical_justification="Observable continuation.",
            justification_basis=JustificationBasis.SYNTACTIC_STRUCTURE,
        )
        layer = ContextLayerDefinition(
            context_layer_id="CL-01",
            layer_scope=ContextLayerScope.IMMEDIATE,
            observation_kind=ContextObservationKind.OTHER,
            observation="Immediate context observation.",
        )
        part = ParticipantDefinition(
            participant_id="PT-01",
            participant_role=ParticipantRole.SPEAKER,
            unit_id="DU-01",
        )
        cand = ContinuityCandidateDefinition(
            candidate_id="CC-01",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            candidate_antecedent_token_id=tokens[0].token_id,
        )
        info = InformationStructureDefinition(
            info_structure_id="IS-01",
            unit_id="DU-01",
            information_role=InformationRole.TOPIC,
        )
        amb = DiscourseAmbiguityDefinition(
            ambiguity_id="AMB-01",
            ambiguity_type=DiscourseAmbiguityType.OTHER,
            subject_ref_id="DU-01",
            description="Preserved.",
            competing_interpretations=["A", "B"],
        )
        self.disc_mgr.record_discourse_analysis(
            st.source_text_id,
            [unit],
            [seg],
            [rel],
            [layer],
            [part],
            [cand],
            [info],
            [amb],
        )

        targets = [
            "discourse_runs",
            "discourse_units",
            "discourse_segments",
            "discourse_relations",
            "discourse_context_layers",
            "discourse_participants",
            "referential_continuity_candidates",
            "information_structure",
            "discourse_ambiguities",
        ]
        for table in targets:
            with self.engine.transaction() as conn:
                with self.assertRaises(sqlite3.IntegrityError, msg=f"UPDATE allowed on {table}"):
                    conn.execute(f"UPDATE {table} SET created_at = '1999-01-01';")
            with self.engine.transaction() as conn:
                with self.assertRaises(sqlite3.IntegrityError, msg=f"DELETE allowed on {table}"):
                    conn.execute(f"DELETE FROM {table};")

    def test_48_rollback_on_failure_leaves_no_partial_run(self) -> None:
        """A failure mid-persistence leaves no partial discourse records behind."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        # Second unit duplicates the first run_id constraint order -> duplicate submission is caught
        # pre-persistence; instead force a post-validation failure via a repeated unit_order+parse.
        dup_order = DiscourseUnitDefinition(
            unit_id="DU-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=0,
            parse_index=0,
            raw_unit_surface="dup order",
        )
        with self.assertRaises(Exception):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit, dup_order])

        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM discourse_runs;")
            self.assertEqual(cur.fetchone()[0], 0)
            cur.execute("SELECT count(*) FROM discourse_units;")
            self.assertEqual(cur.fetchone()[0], 0)

    def test_49_concurrent_runs_both_persist(self) -> None:
        """Two distinct discourse runs for the same source text coexist as immutable history."""
        st, tokens = self._setup_tokens()
        u1 = self._baseline_unit(tokens, "DU-RUN1-01")
        first = self.disc_mgr.record_discourse_analysis(st.source_text_id, [u1])
        u2_1 = self._baseline_unit(tokens, "DU-RUN2-01")
        u2_2 = DiscourseUnitDefinition(
            unit_id="DU-RUN2-02",
            start_token_id=tokens[2].token_id,
            end_token_id=tokens[3].token_id,
            unit_order=1,
            raw_unit_surface="ἦν ὁ",
        )
        second = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [u2_1, u2_2]
        )
        self.assertNotEqual(first.run.run_id, second.run.run_id)
        self.assertEqual(self.disc_mgr.get_run(first.run.run_id).run_id, first.run.run_id)
        self.assertEqual(self.disc_mgr.get_run(second.run.run_id).run_id, second.run.run_id)

    def test_50_duplicate_run_rejected(self) -> None:
        """Submitting the identical discourse payload twice is rejected as a duplicate run."""
        st, tokens = self._setup_tokens()
        self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])
        with self.assertRaises(DuplicateDiscourseError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [self._baseline_unit(tokens)])

    def test_51_duplicate_artifact_ids_rejected(self) -> None:
        """Duplicate unit ids or relation ids within one submission are rejected."""
        st, tokens = self._setup_tokens()
        unit = self._baseline_unit(tokens)
        with self.assertRaises(DuplicateDiscourseError):
            self.disc_mgr.record_discourse_analysis(st.source_text_id, [unit, unit])

    # -------------------------------------------------------------------------
    # 52. Read accessors
    # -------------------------------------------------------------------------

    def test_52_read_accessors(self) -> None:
        """Unit, segment, relation, context, participant, info, and ambiguity accessors round-trip."""
        st, tokens = self._setup_tokens()
        self._register_entities()
        unit = self._baseline_unit(tokens)
        seg = DiscourseSegmentDefinition(
            segment_id="DS-01",
            start_token_id=tokens[0].token_id,
            end_token_id=tokens[3].token_id,
        )
        rel = DiscourseRelationDefinition(
            relation_id="DR-01",
            source_ref_id="DU-01",
            target_ref_id="DS-01",
            source_kind="UNIT",
            target_kind="SEGMENT",
            relation_type=DiscourseRelationType.SUMMARY,
            grammatical_justification="Summary observation.",
            justification_basis=JustificationBasis.LEXICAL_COHESION,
        )
        layer = ContextLayerDefinition(
            context_layer_id="CL-01",
            layer_scope=ContextLayerScope.PERICOPE,
            observation_kind=ContextObservationKind.TOPIC_CONTINUITY,
            observation="Topic continues into the next pericope.",
        )
        part = ParticipantDefinition(
            participant_id="PT-01",
            participant_role=ParticipantRole.NARRATOR,
            unit_id="DU-01",
            entity_id="ENT-LOGOS",
        )
        cand = ContinuityCandidateDefinition(
            candidate_id="CC-01",
            referring_token_id=tokens[3].token_id,
            continuity_type=ContinuityType.ANAPHORIC,
            candidate_antecedent_token_id=tokens[0].token_id,
        )
        info = InformationStructureDefinition(
            info_structure_id="IS-01",
            unit_id="DU-01",
            information_role=InformationRole.SETTING,
        )
        amb = DiscourseAmbiguityDefinition(
            ambiguity_id="AMB-01",
            ambiguity_type=DiscourseAmbiguityType.INFORMATION_ROLE,
            subject_ref_id="DU-01",
            description="Topic and setting both plausible.",
            competing_interpretations=["TOPIC", "SETTING"],
        )
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id,
            [unit],
            [seg],
            [rel],
            [layer],
            [part],
            [cand],
            [info],
            [amb],
        )
        run_id = res.run.run_id
        self.assertEqual(len(self.disc_mgr.get_units_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_segments_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_relations_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_context_layers_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_participants_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_continuity_candidates_for_run(run_id)), 1)
        self.assertEqual(
            len(self.disc_mgr.get_continuity_candidates_for_token(tokens[3].token_id)), 1
        )
        self.assertEqual(len(self.disc_mgr.get_information_structure_for_run(run_id)), 1)
        self.assertEqual(len(self.disc_mgr.get_ambiguities_for_run(run_id)), 1)
        for record in (
            res.units + res.segments + res.relations + res.context_layers
            + res.participants + res.continuity_candidates + res.information_structure
            + res.ambiguities
        ):
            self.assertIsInstance(record.to_dict(), dict)

    def test_53_unknown_run_rejected(self) -> None:
        """Fetching an unknown discourse run raises a not-found error."""
        with self.assertRaises(DiscourseNotFoundError):
            self.disc_mgr.get_run("DSCRUN-DOES-NOT-EXIST")

    def test_54_generative_provenance_path(self) -> None:
        """A non-deterministic discourse configuration records generative provenance."""
        st, tokens = self._setup_tokens()
        config = DiscourseAnalyzerConfig(is_deterministic=False)
        res = self.disc_mgr.record_discourse_analysis(
            st.source_text_id, [self._baseline_unit(tokens)], config=config
        )
        self.assertFalse(res.run.is_exact_reproducible)
        self.assertEqual(res.run.is_exact_reproducible, False)

    # -------------------------------------------------------------------------
    # 55-58. Migration integrity
    # -------------------------------------------------------------------------

    def test_55_migration_011_applied(self) -> None:
        """Migration 011 is discovered, applied, and recorded with its checksum."""
        status = self.runner.get_status()
        applied_ids = [m.migration_id for m in status.applied_migrations]
        self.assertIn("011_discourse_context", applied_ids)
        self.assertEqual(status.pending_count, 0)

        disk = (MIGRATIONS_DIR / "011_discourse_context.sql").read_text(encoding="utf-8")
        expected = compute_sha256(disk)
        recorded = {m.migration_id: m.checksum_sha256 for m in status.applied_migrations}
        self.assertEqual(recorded["011_discourse_context"], expected)

    def test_56_migration_checksums_001_to_010_unchanged(self) -> None:
        """Migrations 001-010 are byte-stable: recorded checksums match the on-disk files."""
        status = self.runner.get_status()
        recorded = {m.migration_id: m.checksum_sha256 for m in status.applied_migrations}
        for name in sorted(p.name for p in MIGRATIONS_DIR.glob("0[01][0-9]_*.sql")):
            if name.startswith("011"):
                continue
            migration_id = name[:-4]
            disk = (MIGRATIONS_DIR / name).read_text(encoding="utf-8")
            self.assertIn(migration_id, recorded, f"{migration_id} not recorded")
            self.assertEqual(
                recorded[migration_id],
                compute_sha256(disk),
                f"checksum drift detected in {migration_id}",
            )

    def test_57_all_discourse_tables_present(self) -> None:
        """Every table required by Task 2.7 exists after migration."""
        expected = {
            "discourse_runs",
            "discourse_units",
            "discourse_segments",
            "discourse_relations",
            "discourse_context_layers",
            "discourse_participants",
            "referential_continuity_candidates",
            "information_structure",
            "discourse_ambiguities",
        }
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            present = {r[0] for r in cur.fetchall()}
        self.assertTrue(expected.issubset(present), f"missing: {expected - present}")

    def test_58_discourse_tables_reference_prior_layers(self) -> None:
        """Discourse tables integrate with syntax, semantics, and referential layers via FKs."""
        with self.engine.connect() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_key_list(discourse_runs);")
            parents = {r[2] for r in cur.fetchall()}
            cur.execute("PRAGMA foreign_key_list(discourse_units);")
            parents |= {r[2] for r in cur.fetchall()}
            cur.execute("PRAGMA foreign_key_list(information_structure);")
            parents |= {r[2] for r in cur.fetchall()}
            cur.execute("PRAGMA foreign_key_list(discourse_participants);")
            parents |= {r[2] for r in cur.fetchall()}
        for required in (
            "syntax_runs",
            "semantic_runs",
            "referential_runs",
            "source_texts",
            "provenance_records",
            "object_versions",
            "tokens",
            "clauses",
            "syntactic_constituents",
            "entities",
            "evidence_ledger",
        ):
            self.assertIn(required, parents, f"missing FK to {required}")

    def test_59_legacy_database_untouched(self) -> None:
        """The legacy runtime database is never contaminated with Bible Engine migrations."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if not legacy_path.exists():
            self.skipTest("legacy runtime database not present on this host")
        conn = sqlite3.connect(str(legacy_path))
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
            )
            self.assertEqual(
                cur.fetchone()[0],
                0,
                "Legacy polya_index.db must not contain Bible Engine schema_migrations.",
            )
            cur.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name LIKE 'discourse_%';"
            )
            self.assertEqual(
                cur.fetchone()[0],
                0,
                "Legacy polya_index.db must not contain discourse tables.",
            )
        finally:
            conn.close()

    def test_60_legacy_checksum_digest_unchanged(self) -> None:
        """The legacy runtime DB SHA-256 digest is unchanged from the Task 2.6 baseline."""
        legacy_path = Path("/home/ubuntu/.polya/polya_index.db")
        if not legacy_path.exists():
            self.skipTest("legacy runtime database not present on this host")
        digest = hashlib.sha256(legacy_path.read_bytes()).hexdigest()
        self.assertEqual(
            digest,
            "c10b6d38c649624d708939b6bce3109c2bdc931b821987f54eeacd6b431f1f81",
            "legacy polya_index.db digest changed: Bible Engine wrote to the runtime database",
        )

    def test_61_discourse_foreign_keys_enforced(self) -> None:
        """Foreign keys remain enforced inside a discourse write transaction."""
        with self.engine.transaction() as conn:
            self.assertEqual(conn.execute("PRAGMA foreign_keys;").fetchone()[0], 1)

    def test_62_no_deferred_fk_bypass_in_migration(self) -> None:
        """Migration 011 never disables foreign keys."""
        sql = (MIGRATIONS_DIR / "011_discourse_context.sql").read_text(encoding="utf-8").lower()
        self.assertNotIn("foreign_keys = off", sql)
        self.assertNotIn("foreign_keys=off", sql)


if __name__ == "__main__":
    unittest.main()
