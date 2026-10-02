"""
Test Suite for Task 4.6 Deterministic Answer & Exegesis Construction Engine.
Verifies Spec v1.2 compliance:
- Pure in-memory projection with zero database dependencies.
- Cryptographic upstream pack hash verification reproducing Task 4.5.
- Confidence, epistemic tier, and tension preservation invariants.
- Presentation-only markdown exclusion from artifact identity.
- Freshness inspection against live ledgers using verified schema (001-025).
- Zero migrations; provenance and versioning integration.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import tempfile
import unicodedata
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bible_engine.answer_construction import (
    AnswerArtifact,
    AnswerClaimBlock,
    AnswerConstructor,
    AnswerEvidenceBlock,
    AnswerFreshnessInspector,
    AnswerFreshnessReport,
    AnswerLineageSummary,
    AnswerTensionBlock,
    _verify_pack_hash,
    compute_answer_content_hash,
    compute_answer_id,
    record_answer_provenance,
    record_answer_version,
)
from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    AnswerConfidenceMutationError,
    AnswerConstructionSubsystemError,
    AnswerEpistemicTierViolationError,
    AnswerFreshnessInspectionError,
    AnswerSerializationError,
    InvalidKnowledgePackError,
    KnowledgeConfidenceRangeError,
    KnowledgeIntegrityViolationError,
    MissingValidationCertificateError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.knowledge_retrieval import (
    AuthoritativeClaimItem,
    AuthoritativeEvidenceItem,
    AuthoritativeKnowledgeRetrievalEngine,
    AuthoritativeTensionItem,
    ConstituentLineageNode,
    KnowledgePackResult,
    KnowledgeQuery,
)
from bible_engine.migrations import MigrationRunner
from bible_engine.provenance import ProvenanceTracker, TargetType, TransformationType
from bible_engine.retrieval import CandidateSource, EvidenceRole, SearchBranch
from bible_engine.synthesis import (
    SynthesisClaimStatus,
    SynthesisScope,
    SynthesisTensionResolution,
    SynthesisTensionType,
)
from bible_engine.validation import ValidationCertificate
from bible_engine.versioning import VersionManager, VersionStatus


def create_dummy_pack(
    query_text: str = "Who is the word in John 1:1?",
    aggregate_confidence: float = 0.85,
    resolved_scope: SynthesisScope = SynthesisScope.PERICOPE,
    target_id: str = "PER_JHN_001_001_005",
    synthesis_run_id: str = "SYN_RUN_001",
    include_counter_evidence: bool = True,
    pipeline_configuration_hash: Optional[str] = "CFG_HASH_TEST_001",
    requested_scope: Optional[SynthesisScope] = SynthesisScope.PERICOPE,
) -> KnowledgePackResult:
    """Helper to build a valid, self-consistent KnowledgePackResult with valid content_hash."""
    query = KnowledgeQuery(
        query_text=query_text,
        pericope_id=target_id,
        requested_scope=requested_scope,
        pipeline_configuration_hash=pipeline_configuration_hash,
    )

    claims = (
        AuthoritativeClaimItem(
            claim_id="CLM_001",
            run_id=synthesis_run_id,
            scope=resolved_scope,
            target_id=target_id,
            claim_tier=ClaimTier.T0_RAW_OBSERVATION,  # T0
            primary_evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_text="Codex Sinaiticus witnesses 'en arche en ho logos'.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            synthesized_confidence=0.98,
            weakest_constituent_confidence=0.95,
            authorial_context="Gospel of John Prologue",
            is_harmonized=False,
            provenance_id="PROV_CLM_001",
            version_id="VER_CLM_001",
            validation_certificate_id="CERT_001",
            created_at="2026-10-01T00:00:00Z",
        ),
        AuthoritativeClaimItem(
            claim_id="CLM_002",
            run_id=synthesis_run_id,
            scope=resolved_scope,
            target_id=target_id,
            claim_tier=ClaimTier.T1_LINGUISTIC_FACT,  # T1
            primary_evidence_class=EvidenceClass.E3_SYNTAX,
            claim_text="'Logos' functions as pre-verbal grammatical subject.",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            synthesized_confidence=0.92,
            weakest_constituent_confidence=0.90,
            authorial_context="Gospel of John Prologue",
            is_harmonized=False,
            provenance_id="PROV_CLM_002",
            version_id="VER_CLM_002",
            validation_certificate_id="CERT_001",
            created_at="2026-10-01T00:00:00Z",
        ),
        AuthoritativeClaimItem(
            claim_id="CLM_003",
            run_id=synthesis_run_id,
            scope=resolved_scope,
            target_id=target_id,
            claim_tier=ClaimTier.T4_THEOLOGICAL_CLAIM,  # T4
            primary_evidence_class=EvidenceClass.E12_LATER_INTERPRETATION,
            claim_text="Logos implies eternal hypostatic pre-existence.",
            epistemic_status=SynthesisClaimStatus.UNRESOLVED,
            synthesized_confidence=0.75,
            weakest_constituent_confidence=0.70,
            authorial_context="Nicene Patristic exegesis",
            is_harmonized=True,
            provenance_id="PROV_CLM_003",
            version_id="VER_CLM_003",
            validation_certificate_id="CERT_001",
            created_at="2026-10-01T00:00:00Z",
        ),
    )

    tensions = (
        AuthoritativeTensionItem(
            tension_id="TEN_001",
            run_id=synthesis_run_id,
            scope=resolved_scope,
            target_id=target_id,
            tension_type=SynthesisTensionType.UNRESOLVED_ANTINOMY,
            primary_claim_id="CLM_001",
            secondary_claim_id="CLM_003",
            description="Grammatical predication vs dogmatic hypostasis.",
            preservation_rationale="Retain distinction between textual grammar and post-Nicene theology.",
            resolution_status=SynthesisTensionResolution.PRESERVED_TENSION,
            provenance_id="PROV_TEN_001",
            version_id="VER_TEN_001",
            created_at="2026-10-01T00:00:00Z",
        ),
    )

    evidence = (
        AuthoritativeEvidenceItem(
            item_id="ITM_EV_001",
            evidence_id="EV_001",
            search_branch=SearchBranch.PRIMARY_SEARCH,
            evidence_role=EvidenceRole.SUPPORTING,
            candidate_source=CandidateSource.DIRECT_LOOKUP,
            item_confidence=0.95,
            item_rank=1,
            linked_claim_id="CLM_001",
            extracted_text="P66 f. 1r: en arche en ho logos",
        ),
    )

    counter_ev: Tuple[AuthoritativeEvidenceItem, ...] = ()
    if include_counter_evidence:
        counter_ev = (
            AuthoritativeEvidenceItem(
                item_id="ITM_EV_002",
                evidence_id="EV_002",
                search_branch=SearchBranch.COUNTER_SEARCH,
                evidence_role=EvidenceRole.COUNTER_EVIDENCE,
                candidate_source=CandidateSource.SYNTHESIS_GROUNDING,
                item_confidence=0.88,
                item_rank=1,
                linked_claim_id="CLM_003",
                extracted_text="Alternative Hellenistic Jewish wisdom motif interpretation.",
            ),
        )

    lineage = (
        ConstituentLineageNode(
            constituent_link_id="LNK_001",
            parent_claim_id="CLM_001",
            constituent_scope=SynthesisScope.PERICOPE,
            constituent_target_id=target_id,
            constituent_claim_id="CLM_001",
            constituent_evidence_id="EV_001",
            constituent_confidence=0.95,
            is_critical_dependency=True,
            run_id=synthesis_run_id,
            provenance_id="PROV_LNK_001",
            validation_certificate_id="CERT_001",
            children=(),
        ),
    )

    certs = (
        ValidationCertificate(
            certificate_id="CERT_001",
            run_id="VAL_RUN_001",
            validation_identity="VAL_ID_001",
            validation_input_hash="HASH_INPUT_001",
            engine_version="2.0.0",
            schema_version="025",
            target_type="PERICOPE",
            target_id=target_id,
            target_version_id="VER_TARGET_001",
            validation_status="VALID",
            layer_summary_json="{}",
            provenance_id="PROV_CERT_001",
            validated_at="2026-10-01T00:00:00Z",
        ),
    )

    prov_ids = ("PROV_CLM_001", "PROV_CLM_002", "PROV_CLM_003", "PROV_TEN_001", "PROV_CERT_001")
    ver_ids = ("VER_CLM_001", "VER_CLM_002", "VER_CLM_003", "VER_TEN_001", "VER_TARGET_001")
    warnings = ("TEST_NOTICE_01",)

    # Compute upstream pack content_hash using Task 4.5 12-key payload
    payload = {
        "resolved_scope": resolved_scope.value,
        "target_id": target_id,
        "synthesis_run_id": synthesis_run_id,
        "aggregate_confidence": round(aggregate_confidence, 6),
        "claims": [c.claim_id for c in sorted(claims, key=lambda x: x.claim_id)],
        "tensions": [t.tension_id for t in sorted(tensions, key=lambda x: x.tension_id)],
        "competing_claims": [],
        "evidence": [e.evidence_id for e in sorted(evidence, key=lambda x: x.evidence_id)],
        "counter_evidence": [e.evidence_id for e in sorted(counter_ev, key=lambda x: x.evidence_id)],
        "certificates": [c.certificate_id for c in sorted(certs, key=lambda x: x.certificate_id)],
        "provenance_ids": list(sorted(prov_ids)),
        "version_ids": list(sorted(ver_ids)),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    return KnowledgePackResult(
        query=query,
        requested_scope=requested_scope,
        resolved_scope=resolved_scope,
        target_id=target_id,
        synthesis_run_id=synthesis_run_id,
        aggregate_confidence=aggregate_confidence,
        claims=claims,
        tensions=tensions,
        competing_claims=(),
        evidence=evidence,
        counter_evidence=counter_ev,
        lineage=lineage,
        validation_certificates=certs,
        provenance_ids=prov_ids,
        version_ids=ver_ids,
        warnings=warnings,
        content_hash=content_hash,
    )


class TestBibleEngineAnswerConstruction(unittest.TestCase):
    """35 Comprehensive Tests for Task 4.6 Deterministic Answer Construction & Freshness."""

    def setUp(self) -> None:
        self.constructor = AnswerConstructor(engine_version="2.0.0", schema_version="025")

    # -------------------------------------------------------------------------
    # UNIT TESTS: PURE PROJECTION & CONTRACT INTEGRITY (TESTS 01-14)
    # -------------------------------------------------------------------------

    def test_01_successful_pure_answer_construction(self) -> None:
        """Test valid pack projection into an immutable AnswerArtifact."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack, render_markdown=False)

        self.assertIsInstance(artifact, AnswerArtifact)
        self.assertEqual(artifact.query_text, pack.query.query_text)
        self.assertEqual(artifact.resolved_scope, pack.resolved_scope)
        self.assertEqual(artifact.target_id, pack.target_id)
        self.assertEqual(artifact.synthesis_run_id, pack.synthesis_run_id)
        self.assertEqual(artifact.aggregate_confidence, pack.aggregate_confidence)
        self.assertTrue(artifact.answer_id.startswith("ANS-"))
        self.assertIsNotNone(artifact.content_hash)
        self.assertIsNone(artifact.formatted_markdown)

    def test_02_zero_db_operations_during_construction(self) -> None:
        """Confirm AnswerConstructor takes no database connection and executes purely in memory."""
        pack = create_dummy_pack()
        # Verify constructor accepts no db parameter
        constructor = AnswerConstructor()
        self.assertFalse(hasattr(constructor, "conn"))
        self.assertFalse(hasattr(constructor, "engine"))
        # Execute without error
        artifact = constructor.construct_answer(pack)
        self.assertIsNotNone(artifact.answer_id)

    def test_03_reject_none_or_invalid_knowledge_pack(self) -> None:
        """Reject None or invalid objects with InvalidKnowledgePackError."""
        with self.assertRaises(InvalidKnowledgePackError):
            self.constructor.construct_answer(None)  # type: ignore

        with self.assertRaises(InvalidKnowledgePackError):
            self.constructor.construct_answer("not a pack")  # type: ignore

    def test_04_reject_empty_validation_certificates(self) -> None:
        """Reject pack with empty validation certificates."""
        pack = create_dummy_pack()
        # Create pack with empty certs
        tampered_pack = KnowledgePackResult(
            query=pack.query,
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            aggregate_confidence=pack.aggregate_confidence,
            claims=pack.claims,
            tensions=pack.tensions,
            competing_claims=pack.competing_claims,
            evidence=pack.evidence,
            counter_evidence=pack.counter_evidence,
            lineage=pack.lineage,
            validation_certificates=(),  # EMPTY
            provenance_ids=pack.provenance_ids,
            version_ids=pack.version_ids,
            warnings=pack.warnings,
            content_hash=pack.content_hash,
        )
        with self.assertRaises(MissingValidationCertificateError):
            self.constructor.construct_answer(tampered_pack)

    def test_05_reject_tampered_pack_hash(self) -> None:
        """Reject pack where content_hash fails canonical re-verification."""
        pack = create_dummy_pack()
        tampered_pack = KnowledgePackResult(
            query=pack.query,
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            aggregate_confidence=pack.aggregate_confidence,
            claims=pack.claims,
            tensions=pack.tensions,
            competing_claims=pack.competing_claims,
            evidence=pack.evidence,
            counter_evidence=pack.counter_evidence,
            lineage=pack.lineage,
            validation_certificates=pack.validation_certificates,
            provenance_ids=pack.provenance_ids,
            version_ids=pack.version_ids,
            warnings=pack.warnings,
            content_hash="tampered_hash_000000000000000000000000000000000000000000000000000",
        )
        with self.assertRaises(KnowledgeIntegrityViolationError):
            self.constructor.construct_answer(tampered_pack)

    def test_06_reject_out_of_bounds_pack_confidence(self) -> None:
        """Reject pack with aggregate_confidence out of [0.0, 1.0]."""
        pack = create_dummy_pack(aggregate_confidence=1.2)
        # Note: _verify_pack_hash will check hash first, or confidence range
        with self.assertRaises((KnowledgeConfidenceRangeError, KnowledgeIntegrityViolationError)):
            self.constructor.construct_answer(pack)

        pack_neg = create_dummy_pack(aggregate_confidence=-0.1)
        with self.assertRaises((KnowledgeConfidenceRangeError, KnowledgeIntegrityViolationError)):
            self.constructor.construct_answer(pack_neg)

    def test_07_reject_out_of_bounds_claim_confidence(self) -> None:
        """Reject claim with confidence outside [0.0, 1.0]."""
        pack = create_dummy_pack()
        bad_claim = AuthoritativeClaimItem(
            claim_id="CLM_BAD",
            run_id=pack.synthesis_run_id,
            scope=pack.resolved_scope,
            target_id=pack.target_id,
            claim_tier=ClaimTier.T0_RAW_OBSERVATION,
            primary_evidence_class=EvidenceClass.E1_TEXTUAL_MANUSCRIPT,
            claim_text="Bad confidence claim",
            epistemic_status=SynthesisClaimStatus.CONVERGENT,
            synthesized_confidence=1.5,  # OUT OF BOUNDS
            weakest_constituent_confidence=0.9,
            authorial_context="context",
            is_harmonized=False,
            provenance_id="P_BAD",
            version_id="V_BAD",
            validation_certificate_id="CERT_001",
            created_at="2026-10-01T00:00:00Z",
        )
        # Recalculate pack hash for bad claim
        claims = (bad_claim,)
        payload = {
            "resolved_scope": pack.resolved_scope.value,
            "target_id": pack.target_id,
            "synthesis_run_id": pack.synthesis_run_id,
            "aggregate_confidence": round(pack.aggregate_confidence, 6),
            "claims": ["CLM_BAD"],
            "tensions": [t.tension_id for t in pack.tensions],
            "competing_claims": [],
            "evidence": [e.evidence_id for e in pack.evidence],
            "counter_evidence": [e.evidence_id for e in pack.counter_evidence],
            "certificates": [c.certificate_id for c in pack.validation_certificates],
            "provenance_ids": list(sorted(pack.provenance_ids)),
            "version_ids": list(sorted(pack.version_ids)),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        chash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        tampered = KnowledgePackResult(
            query=pack.query,
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            aggregate_confidence=pack.aggregate_confidence,
            claims=claims,
            tensions=pack.tensions,
            competing_claims=(),
            evidence=pack.evidence,
            counter_evidence=pack.counter_evidence,
            lineage=pack.lineage,
            validation_certificates=pack.validation_certificates,
            provenance_ids=pack.provenance_ids,
            version_ids=pack.version_ids,
            warnings=pack.warnings,
            content_hash=chash,
        )
        with self.assertRaises(KnowledgeConfidenceRangeError):
            self.constructor.construct_answer(tampered)

    def test_08_aggregate_confidence_exact_preservation(self) -> None:
        """Confirm AnswerArtifact.aggregate_confidence == pack.aggregate_confidence exactly."""
        pack = create_dummy_pack(aggregate_confidence=0.742819)
        artifact = self.constructor.construct_answer(pack)
        self.assertEqual(artifact.aggregate_confidence, 0.742819)

    def test_09_claim_confidence_exact_preservation(self) -> None:
        """Confirm claim confidence exactly preserves synthesized_confidence."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)
        for tier, claims in artifact.claims_by_tier.items():
            for c in claims:
                upstream = next(up for up in pack.claims if up.claim_id == c.claim_id)
                self.assertEqual(c.confidence, upstream.synthesized_confidence)

    def test_10_tier_segregation_t0_to_t4(self) -> None:
        """Verify claims are strictly partitioned across T0, T1, T2, T3, T4."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        self.assertIn("T0", artifact.claims_by_tier)
        self.assertIn("T1", artifact.claims_by_tier)
        self.assertIn("T2", artifact.claims_by_tier)
        self.assertIn("T3", artifact.claims_by_tier)
        self.assertIn("T4", artifact.claims_by_tier)

        self.assertEqual(len(artifact.claims_by_tier["T0"]), 1)
        self.assertEqual(artifact.claims_by_tier["T0"][0].claim_id, "CLM_001")
        self.assertEqual(len(artifact.claims_by_tier["T1"]), 1)
        self.assertEqual(artifact.claims_by_tier["T1"][0].claim_id, "CLM_002")
        self.assertEqual(len(artifact.claims_by_tier["T4"]), 1)
        self.assertEqual(artifact.claims_by_tier["T4"][0].claim_id, "CLM_003")

    def test_11_t4_theological_claim_isolation(self) -> None:
        """Ensure T4 dogmatic propositions are strictly segregated into T4 and absent from T0/T1."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        t4_claim_ids = {c.claim_id for c in artifact.claims_by_tier["T4"]}
        t0_claim_ids = {c.claim_id for c in artifact.claims_by_tier["T0"]}
        t1_claim_ids = {c.claim_id for c in artifact.claims_by_tier["T1"]}

        self.assertIn("CLM_003", t4_claim_ids)
        self.assertNotIn("CLM_003", t0_claim_ids)
        self.assertNotIn("CLM_003", t1_claim_ids)

    def test_12_symmetrical_evidence_projection(self) -> None:
        """Verify supporting and counter-evidence are symmetrically projected without loss."""
        pack = create_dummy_pack(include_counter_evidence=True)
        artifact = self.constructor.construct_answer(pack)

        self.assertEqual(len(artifact.supporting_evidence), 1)
        self.assertEqual(artifact.supporting_evidence[0].evidence_id, "EV_001")
        self.assertEqual(artifact.supporting_evidence[0].search_branch, SearchBranch.PRIMARY_SEARCH)

        self.assertEqual(len(artifact.counter_evidence), 1)
        self.assertEqual(artifact.counter_evidence[0].evidence_id, "EV_002")
        self.assertEqual(artifact.counter_evidence[0].search_branch, SearchBranch.COUNTER_SEARCH)

    def test_13_counter_evidence_cannot_be_suppressed(self) -> None:
        """Confirm counter-evidence cannot be suppressed or filtered out during construction."""
        pack = create_dummy_pack(include_counter_evidence=True)
        artifact = self.constructor.construct_answer(pack)
        self.assertTrue(len(artifact.counter_evidence) > 0)
        self.assertEqual(artifact.counter_evidence[0].confidence, 0.88)
        self.assertEqual(artifact.counter_evidence[0].evidence_role, EvidenceRole.COUNTER_EVIDENCE)

    def test_14_counter_evidence_not_found_warning_propagated(self) -> None:
        """Confirm warnings propagate intact into AnswerArtifact.warnings."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)
        self.assertIn("TEST_NOTICE_01", artifact.warnings)

    # -------------------------------------------------------------------------
    # UNIT TESTS: DIALECTICAL TENSIONS & PROVENANCE (TESTS 15-20)
    # -------------------------------------------------------------------------

    def test_15_preserved_dialectical_tensions(self) -> None:
        """Confirm dialectical tensions are preserved side-by-side without harmonization."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        self.assertEqual(len(artifact.preserved_tensions), 1)
        tension = artifact.preserved_tensions[0]
        self.assertEqual(tension.tension_id, "TEN_001")
        self.assertEqual(tension.tension_type, SynthesisTensionType.UNRESOLVED_ANTINOMY)
        self.assertEqual(tension.resolution_status, SynthesisTensionResolution.PRESERVED_TENSION)

    def test_16_is_harmonized_pass_through_mirror(self) -> None:
        """Confirm is_harmonized is strictly a pass-through mirror without re-adjudication."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        clm_001 = next(c for c in artifact.claims_by_tier["T0"] if c.claim_id == "CLM_001")
        clm_003 = next(c for c in artifact.claims_by_tier["T4"] if c.claim_id == "CLM_003")

        self.assertFalse(clm_001.is_harmonized)
        self.assertTrue(clm_003.is_harmonized)

    def test_17_tension_provenance_and_version_preservation(self) -> None:
        """Confirm AnswerTensionBlock preserves both source_provenance_id and source_version_id."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        tension = artifact.preserved_tensions[0]
        self.assertEqual(tension.source_provenance_id, "PROV_TEN_001")
        self.assertEqual(tension.source_version_id, "VER_TEN_001")

    def test_18_claim_provenance_and_version_preservation(self) -> None:
        """Confirm AnswerClaimBlock preserves source_provenance_id, source_version_id, and validation_certificate_id."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        claim = artifact.claims_by_tier["T0"][0]
        self.assertEqual(claim.source_provenance_id, "PROV_CLM_001")
        self.assertEqual(claim.source_version_id, "VER_CLM_001")
        self.assertEqual(claim.validation_certificate_id, "CERT_001")

    def test_19_identity_context_preservation(self) -> None:
        """Confirm AnswerArtifact preserves requested_scope and pipeline_configuration_hash."""
        pack = create_dummy_pack(
            pipeline_configuration_hash="CFG_CANONICAL_999",
            requested_scope=SynthesisScope.PERICOPE,
        )
        artifact = self.constructor.construct_answer(pack)

        self.assertEqual(artifact.requested_scope, SynthesisScope.PERICOPE)
        self.assertEqual(artifact.pipeline_configuration_hash, "CFG_CANONICAL_999")

    def test_20_lineage_summary_hierarchy_computation(self) -> None:
        """Confirm lineage summary correctly captures count, deepest scope, and critical dependencies."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        lineage = artifact.lineage_summary
        self.assertEqual(lineage.total_constituents, 1)
        self.assertEqual(lineage.critical_dependency_count, 1)
        self.assertEqual(lineage.deepest_scope, SynthesisScope.PERICOPE)
        self.assertIn("CLM_001", lineage.root_claim_ids)

    # -------------------------------------------------------------------------
    # UNIT TESTS: CANONICAL SERIALIZATION & HASHING (TESTS 21-27)
    # -------------------------------------------------------------------------

    def test_21_canonical_float_serialization(self) -> None:
        """Verify floats are formatted as fixed-point 6-decimal strings in to_canonical_dict()."""
        pack = create_dummy_pack(aggregate_confidence=0.85)
        artifact = self.constructor.construct_answer(pack)

        canonical = artifact.to_canonical_dict()
        self.assertEqual(canonical["aggregate_confidence"], "0.850000")
        self.assertEqual(canonical["claims_by_tier"]["T0"][0]["confidence"], "0.980000")
        self.assertEqual(canonical["supporting_evidence"][0]["confidence"], "0.950000")

    def test_22_unicode_nfc_normalization(self) -> None:
        """Confirm decomposed Unicode text (NFD) is normalized to NFC in canonical dict."""
        # 'e' + combining acute accent -> decomposed NFD
        nfd_text = "e\u0301n arche\u0301"
        pack = create_dummy_pack(query_text=nfd_text)
        artifact = self.constructor.construct_answer(pack)

        canonical = artifact.to_canonical_dict()
        self.assertEqual(canonical["query_text"], unicodedata.normalize("NFC", nfd_text))

    def test_23_collision_resistant_content_hash(self) -> None:
        """Verify SHA-256 content hash determinism and collision-resistant semantics."""
        pack1 = create_dummy_pack()
        pack2 = create_dummy_pack()

        art1 = self.constructor.construct_answer(pack1)
        art2 = self.constructor.construct_answer(pack2)

        self.assertEqual(art1.content_hash, art2.content_hash)
        self.assertEqual(len(art1.content_hash), 64)

    def test_24_deterministic_answer_id_format(self) -> None:
        """Verify answer_id format is ANS-{16_hex_chars}."""
        pack = create_dummy_pack()
        artifact = self.constructor.construct_answer(pack)

        self.assertTrue(artifact.answer_id.startswith("ANS-"))
        self.assertEqual(len(artifact.answer_id), 20)  # "ANS-" (4) + 16 hex chars
        self.assertEqual(artifact.answer_id, f"ANS-{artifact.content_hash[:16]}")

    def test_25_row_order_independence(self) -> None:
        """Confirm content hash is completely invariant to insertion/row order of collections."""
        pack = create_dummy_pack()
        art1 = self.constructor.construct_answer(pack)

        # Shuffle provenance_ids and version_ids
        shuffled_pack = KnowledgePackResult(
            query=pack.query,
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            aggregate_confidence=pack.aggregate_confidence,
            claims=tuple(reversed(pack.claims)),
            tensions=pack.tensions,
            competing_claims=pack.competing_claims,
            evidence=pack.evidence,
            counter_evidence=pack.counter_evidence,
            lineage=pack.lineage,
            validation_certificates=pack.validation_certificates,
            provenance_ids=tuple(reversed(pack.provenance_ids)),
            version_ids=tuple(reversed(pack.version_ids)),
            warnings=pack.warnings,
            content_hash=pack.content_hash,
        )

        art2 = self.constructor.construct_answer(shuffled_pack)
        self.assertEqual(art1.content_hash, art2.content_hash)
        self.assertEqual(art1.answer_id, art2.answer_id)

    def test_26_markdown_presentation_only_exclusion(self) -> None:
        """Confirm formatted_markdown is excluded from canonical dict, canonical json, content_hash, and answer_id."""
        pack = create_dummy_pack()
        art_without_md = self.constructor.construct_answer(pack, render_markdown=False)
        art_with_md = self.constructor.construct_answer(pack, render_markdown=True)

        self.assertIsNone(art_without_md.formatted_markdown)
        self.assertIsNotNone(art_with_md.formatted_markdown)

        # Crucial invariant: hashes and answer_id must be 100% byte-identical
        self.assertEqual(art_without_md.content_hash, art_with_md.content_hash)
        self.assertEqual(art_without_md.answer_id, art_with_md.answer_id)
        self.assertEqual(art_without_md.to_canonical_dict(), art_with_md.to_canonical_dict())
        self.assertEqual(art_without_md.to_canonical_json(), art_with_md.to_canonical_json())

    def test_27_markdown_content_attested_assertions(self) -> None:
        """Confirm rendered markdown includes verbatim claims, tensions, evidence, and answer ID."""
        pack = create_dummy_pack(include_counter_evidence=True)
        artifact = self.constructor.construct_answer(pack, render_markdown=True)
        md = artifact.formatted_markdown
        self.assertIsNotNone(md)

        self.assertIn(artifact.answer_id, md)
        self.assertIn("Codex Sinaiticus witnesses 'en arche en ho logos'", md)
        self.assertIn("Logos implies eternal hypostatic pre-existence", md)
        self.assertIn("Grammatical predication vs dogmatic hypostasis", md)
        self.assertIn("P66 f. 1r: en arche en ho logos", md)
        self.assertIn("Alternative Hellenistic Jewish wisdom motif interpretation", md)

    # -------------------------------------------------------------------------
    # INTEGRATION TESTS: FRESHNESS INSPECTOR & LEDGERS (TESTS 28-35)
    # -------------------------------------------------------------------------

    def test_28_freshness_clean_completed_run(self) -> None:
        """Freshness inspection returns is_stale=False on active, non-superseded live records."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            # Seed live tables matching pack
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            for vid in artifact.source_version_ids:
                if vid != "VER_TARGET_001":
                    conn.execute(
                        f"""
                        INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                        VALUES ('{vid}', 'CLAIM', '{vid}', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                        """
                    )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'COMPLETED', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.execute(
                """
                INSERT INTO validation_runs (run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, final_outcome, checks_total, checks_passed, checks_failed, warnings_total, provenance_id, executed_at, is_immutable)
                VALUES ('VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', 10, 10, 0, 0, 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO validation_certificates (certificate_id, run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, validation_status, layer_summary_json, provenance_id, validated_at, is_immutable)
                VALUES ('CERT_001', 'VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', '{}', 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertFalse(report.is_stale)
            self.assertEqual(len(report.stale_reasons), 0)
            engine.close()

    def test_29_freshness_stale_on_superseded_synthesis(self) -> None:
        """Freshness inspection flags stale when synthesis_runs.status == 'SUPERSEDED'."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            # Synthesis marked SUPERSEDED
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'SUPERSEDED', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertTrue(report.is_stale)
            self.assertTrue(any("SUPERSEDED" in r for r in report.stale_reasons))
            engine.close()

    def test_30_freshness_stale_on_non_completed_synthesis(self) -> None:
        """Freshness inspection flags stale when synthesis_runs has non-completed status (e.g. PROCESSING)."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'PROCESSING', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertTrue(report.is_stale)
            self.assertTrue(any("non-completed" in r for r in report.stale_reasons))
            engine.close()

    def test_31_freshness_stale_on_invalid_certificate_status(self) -> None:
        """Freshness inspection flags stale when certificate is missing or invalid."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            # Synthesis COMPLETED, but certificate missing from DB
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'COMPLETED', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertTrue(report.is_stale)
            self.assertTrue(any("Validation certificate" in r for r in report.stale_reasons))
            engine.close()

    def test_32_freshness_stale_on_superseded_certificate_target_version(self) -> None:
        """Freshness inspection flags stale when certificate's target version is SUPERSEDED."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            # Target version SUPERSEDED
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'SUPERSEDED', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'COMPLETED', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.execute(
                """
                INSERT INTO validation_runs (run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, final_outcome, checks_total, checks_passed, checks_failed, warnings_total, provenance_id, executed_at, is_immutable)
                VALUES ('VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', 10, 10, 0, 0, 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO validation_certificates (certificate_id, run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, validation_status, layer_summary_json, provenance_id, validated_at, is_immutable)
                VALUES ('CERT_001', 'VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', '{}', 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertTrue(report.is_stale)
            self.assertTrue(any("target version is SUPERSEDED" in r for r in report.stale_reasons))
            engine.close()

    def test_33_freshness_stale_on_superseded_constituent_version(self) -> None:
        """Freshness inspection flags stale when any source_version_id is INVALIDATED."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_SYN_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_TARGET_001', 'PERICOPE', 'PER_001', 1, 'HASH', 'ACTIVE', 'INITIAL_CREATION', '2026-10-01', 'SYSTEM')
                """
            )
            # VER_CLM_001 INVALIDATED
            conn.execute(
                """
                INSERT INTO object_versions (version_id, object_type, object_id, version_number, content_hash, status, change_reason, created_at, created_by)
                VALUES ('VER_CLM_001', 'CLAIM', 'CLM_001', 1, 'HASH', 'INVALIDATED', 'CORRECTION', '2026-10-01', 'SYSTEM')
                """
            )
            conn.execute(
                """
                INSERT INTO synthesis_runs (run_id, scope, target_id, synthesizer_id, synthesizer_version, configuration_hash, input_content_hash, output_hash, aggregate_confidence, status, provenance_id, version_id, created_at)
                VALUES ('SYN_RUN_001', 'PERICOPE', 'PER_JHN_001_001_005', 'SYNTH', '1.0', 'CFG', 'IN', 'OUT', 0.85, 'COMPLETED', 'PROV_SYN_001', 'VER_TARGET_001', '2026-10-01')
                """
            )
            conn.execute(
                """
                INSERT INTO validation_runs (run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, final_outcome, checks_total, checks_passed, checks_failed, warnings_total, provenance_id, executed_at, is_immutable)
                VALUES ('VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', 10, 10, 0, 0, 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO validation_certificates (certificate_id, run_id, validation_identity, validation_input_hash, engine_version, schema_version, target_type, target_id, target_version_id, validation_status, layer_summary_json, provenance_id, validated_at, is_immutable)
                VALUES ('CERT_001', 'VAL_RUN_001', 'VAL_ID_001', 'IN_HASH', '2.0.0', '025', 'PERICOPE', 'PER_001', 'VER_TARGET_001', 'VALID', '{}', 'PROV_SYN_001', '2026-10-01', 1)
                """
            )
            conn.commit()

            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact)
            self.assertTrue(report.is_stale)
            self.assertTrue(any("VER_CLM_001" in r and "INVALIDATED" in r for r in report.stale_reasons))
            engine.close()

    def test_34_freshness_stale_on_schema_drift(self) -> None:
        """Freshness inspection flags stale when runtime schema does not match artifact."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            conn = engine.get_write_connection()
            report = AnswerFreshnessInspector.inspect_freshness(conn, artifact, current_schema_version="026_DRIFT")
            self.assertTrue(report.is_stale)
            self.assertTrue(any("Schema boundary mismatch" in r for r in report.stale_reasons))
            engine.close()

    def test_35_provenance_and_version_recording(self) -> None:
        """Verify provenance and version records are created without schema alterations."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "freshness.db")
            engine = DatabaseEngine(DatabaseConfig(db_path=db_path))
            runner = MigrationRunner(engine, Path(__file__).parent.parent / "schemas" / "bible_engine")
            runner.apply_pending()

            tracker = ProvenanceTracker(engine)
            ver_mgr = VersionManager(engine)

            conn = engine.get_write_connection()
            conn.execute(
                """
                INSERT INTO provenance_records (provenance_id, target_type, target_id, transformation_type, content_hash, schema_version, created_at, is_immutable)
                VALUES ('PROV_CERT_001', 'PASSAGE', 'PER_001', 'DETERMINISTIC', 'HASH', '2.0.0', '2026-10-01', 1)
                """
            )
            conn.commit()

            pack = create_dummy_pack()
            artifact = self.constructor.construct_answer(pack)

            # Record provenance
            prov_rec = record_answer_provenance(tracker, artifact, pack.content_hash, conn=conn)
            self.assertIsNotNone(prov_rec.provenance_id)
            self.assertEqual(prov_rec.target_type, TargetType.DERIVED_ARTIFACT)
            self.assertEqual(prov_rec.transformation_type, TransformationType.DETERMINISTIC)

            # Record version
            ver_rec = record_answer_version(ver_mgr, artifact, prov_rec.provenance_id)
            self.assertIsNotNone(ver_rec.version_id)
            self.assertEqual(ver_rec.object_type, "ANSWER_ARTIFACT")
            self.assertEqual(ver_rec.status, VersionStatus.ACTIVE)

            engine.close()


if __name__ == "__main__":
    unittest.main()
