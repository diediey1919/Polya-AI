"""
Deterministic Answer & Exegesis Construction Subsystem (Task 4.6).
Pure in-memory projection engine downstream of Task 4.5 Authoritative Knowledge Retrieval.

Invariants:
- Task 4.5 remains the sole Authority Gate.
- AnswerConstructor executes ZERO database queries, ZERO mutations, and ZERO epistemic adjudication.
- Symmetrical evidence and theological tensions/antinomies are preserved intact.
- Epistemic tiers (T0-T4) are strictly segregated; no promotion or conflation.
- formatted_markdown is presentation-only and completely excluded from canonical dict/JSON,
  content_hash, and answer_id.
- AnswerFreshnessInspector is fully decoupled from construction and queries verified schema (001-025).
- Zero new migrations (Migration 026 is strictly forbidden).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple
import unicodedata

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
    AuthoritativeTensionItem,
    ConstituentLineageNode,
    KnowledgePackResult,
)
from bible_engine.provenance import (
    ProvenanceRecord,
    ProvenanceTracker,
    RelationType,
    TargetType,
    TransformationType,
)
from bible_engine.retrieval import CandidateSource, EvidenceRole, SearchBranch
from bible_engine.synthesis import (
    SCOPE_ORDER,
    SynthesisClaimStatus,
    SynthesisScope,
    SynthesisTensionResolution,
    SynthesisTensionType,
)
from bible_engine.validation import ValidationCertificate
from bible_engine.versioning import ChangeReason, ObjectVersion, VersionManager, VersionStatus


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class AnswerClaimBlock:
    """
    Immutable representation of an individual answer claim.
    is_harmonized is strictly a pass-through mirror of upstream AuthoritativeClaimItem.
    """
    claim_id: str
    claim_tier: ClaimTier
    primary_evidence_class: EvidenceClass
    claim_text: str
    epistemic_status: SynthesisClaimStatus
    confidence: float
    authorial_context: str
    is_harmonized: bool
    source_provenance_id: str
    source_version_id: str
    validation_certificate_id: str


@dataclass(frozen=True)
class AnswerEvidenceBlock:
    """Immutable representation of an evidence citation in the answer."""
    evidence_id: str
    search_branch: SearchBranch
    evidence_role: EvidenceRole
    candidate_source: CandidateSource
    confidence: float
    rank: int
    linked_claim_id: Optional[str]
    extracted_text: Optional[str] = None


@dataclass(frozen=True)
class AnswerTensionBlock:
    """
    Immutable representation of a preserved dialectical tension.
    Preserves both source_provenance_id and source_version_id from AuthoritativeTensionItem.
    """
    tension_id: str
    tension_type: SynthesisTensionType
    primary_claim_id: str
    secondary_claim_id: str
    description: str
    preservation_rationale: str
    resolution_status: SynthesisTensionResolution
    source_provenance_id: str
    source_version_id: str


@dataclass(frozen=True)
class AnswerLineageSummary:
    """Downward constituent hierarchy summary."""
    total_constituents: int
    deepest_scope: SynthesisScope
    root_claim_ids: Tuple[str, ...]
    critical_dependency_count: int


@dataclass(frozen=True)
class AnswerArtifact:
    """
    Deterministic, immutable derived artifact representing an authoritative answer.
    Preserves complete provenance, weakest-link confidence, symmetrical evidence, and antinomies.
    """
    answer_id: str
    query_text: str
    requested_scope: Optional[SynthesisScope]
    resolved_scope: SynthesisScope
    target_id: str
    synthesis_run_id: str
    pipeline_configuration_hash: Optional[str]
    aggregate_confidence: float
    claims_by_tier: Dict[str, Tuple[AnswerClaimBlock, ...]]
    supporting_evidence: Tuple[AnswerEvidenceBlock, ...]
    counter_evidence: Tuple[AnswerEvidenceBlock, ...]
    preserved_tensions: Tuple[AnswerTensionBlock, ...]
    lineage_summary: AnswerLineageSummary
    primary_validation_certificate_id: str
    validation_identities: Tuple[str, ...]
    input_knowledge_pack_hash: str
    source_provenance_ids: Tuple[str, ...]
    source_version_ids: Tuple[str, ...]
    warnings: Tuple[str, ...]
    engine_version: str
    schema_version: str
    content_hash: str
    formatted_markdown: Optional[str] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Produce canonical dictionary representation for deterministic hashing.
        EXCLUDES answer_id, content_hash, and formatted_markdown.
        Encodes all floats as fixed-point canonical strings (f"{val:.6f}").
        Normalizes all strings to Unicode NFC.
        """
        # 1. Normalize claims by tier
        canonical_claims: Dict[str, List[Dict[str, Any]]] = {}
        for tier in ("T0", "T1", "T2", "T3", "T4"):
            blocks = self.claims_by_tier.get(tier, ())
            sorted_blocks = sorted(blocks, key=lambda c: c.claim_id)
            canonical_claims[tier] = [
                {
                    "claim_id": c.claim_id,
                    "claim_tier": c.claim_tier.value,
                    "primary_evidence_class": c.primary_evidence_class.value,
                    "claim_text": unicodedata.normalize("NFC", c.claim_text),
                    "epistemic_status": c.epistemic_status.value,
                    "confidence": f"{float(c.confidence):.6f}",
                    "authorial_context": unicodedata.normalize("NFC", c.authorial_context),
                    "is_harmonized": c.is_harmonized,
                    "source_provenance_id": c.source_provenance_id,
                    "source_version_id": c.source_version_id,
                    "validation_certificate_id": c.validation_certificate_id,
                }
                for c in sorted_blocks
            ]

        # 2. Supporting evidence (sorted by evidence_role, rank, evidence_id)
        sorted_supporting = sorted(
            self.supporting_evidence,
            key=lambda e: (e.evidence_role.value, e.rank, e.evidence_id),
        )
        canonical_supporting = [
            {
                "evidence_id": e.evidence_id,
                "search_branch": e.search_branch.value,
                "evidence_role": e.evidence_role.value,
                "candidate_source": e.candidate_source.value,
                "confidence": f"{float(e.confidence):.6f}",
                "rank": e.rank,
                "linked_claim_id": e.linked_claim_id,
                "extracted_text": unicodedata.normalize("NFC", e.extracted_text) if e.extracted_text else None,
            }
            for e in sorted_supporting
        ]

        # 3. Counter evidence (sorted by evidence_role, rank, evidence_id)
        sorted_counter = sorted(
            self.counter_evidence,
            key=lambda e: (e.evidence_role.value, e.rank, e.evidence_id),
        )
        canonical_counter = [
            {
                "evidence_id": e.evidence_id,
                "search_branch": e.search_branch.value,
                "evidence_role": e.evidence_role.value,
                "candidate_source": e.candidate_source.value,
                "confidence": f"{float(e.confidence):.6f}",
                "rank": e.rank,
                "linked_claim_id": e.linked_claim_id,
                "extracted_text": unicodedata.normalize("NFC", e.extracted_text) if e.extracted_text else None,
            }
            for e in sorted_counter
        ]

        # 4. Preserved tensions (sorted by tension_id)
        sorted_tensions = sorted(self.preserved_tensions, key=lambda t: t.tension_id)
        canonical_tensions = [
            {
                "tension_id": t.tension_id,
                "tension_type": t.tension_type.value,
                "primary_claim_id": t.primary_claim_id,
                "secondary_claim_id": t.secondary_claim_id,
                "description": unicodedata.normalize("NFC", t.description),
                "preservation_rationale": unicodedata.normalize("NFC", t.preservation_rationale),
                "resolution_status": t.resolution_status.value,
                "source_provenance_id": t.source_provenance_id,
                "source_version_id": t.source_version_id,
            }
            for t in sorted_tensions
        ]

        # 5. Lineage summary
        canonical_lineage = {
            "total_constituents": self.lineage_summary.total_constituents,
            "deepest_scope": self.lineage_summary.deepest_scope.value,
            "root_claim_ids": list(sorted(self.lineage_summary.root_claim_ids)),
            "critical_dependency_count": self.lineage_summary.critical_dependency_count,
        }

        return {
            "query_text": unicodedata.normalize("NFC", self.query_text),
            "requested_scope": self.requested_scope.value if self.requested_scope else None,
            "resolved_scope": self.resolved_scope.value,
            "target_id": self.target_id,
            "synthesis_run_id": self.synthesis_run_id,
            "pipeline_configuration_hash": self.pipeline_configuration_hash,
            "aggregate_confidence": f"{float(self.aggregate_confidence):.6f}",
            "claims_by_tier": canonical_claims,
            "supporting_evidence": canonical_supporting,
            "counter_evidence": canonical_counter,
            "preserved_tensions": canonical_tensions,
            "lineage_summary": canonical_lineage,
            "primary_validation_certificate_id": self.primary_validation_certificate_id,
            "validation_identities": list(sorted(set(self.validation_identities))),
            "input_knowledge_pack_hash": self.input_knowledge_pack_hash,
            "source_provenance_ids": list(sorted(set(self.source_provenance_ids))),
            "source_version_ids": list(sorted(set(self.source_version_ids))),
            "warnings": list(sorted(set(self.warnings))),
            "engine_version": self.engine_version,
            "schema_version": self.schema_version,
        }

    def to_canonical_json(self) -> str:
        """Produce compact canonical JSON string (sort_keys=True, separators=(',', ':'), ensure_ascii=True)."""
        try:
            return json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        except Exception as e:
            raise AnswerSerializationError(f"Failed to serialize AnswerArtifact to canonical JSON: {e}") from e


# =============================================================================
# HASHING & INTEGRITY HELPERS
# =============================================================================

def _verify_pack_hash(pack: KnowledgePackResult) -> str:
    """
    Exact cryptographic verification of upstream KnowledgePackResult content_hash.
    Replicates the exact 12 logical keys, sorting rules, and numeric float rounding of Task 4.5.
    DO NOT include lineage, warnings, query, requested_scope, or pipeline_configuration_hash.
    """
    payload = {
        "resolved_scope": pack.resolved_scope.value,
        "target_id": pack.target_id,
        "synthesis_run_id": pack.synthesis_run_id,
        "aggregate_confidence": round(pack.aggregate_confidence, 6),
        "claims": [c.claim_id for c in sorted(pack.claims, key=lambda x: x.claim_id)],
        "tensions": [t.tension_id for t in sorted(pack.tensions, key=lambda x: x.tension_id)],
        "competing_claims": [c.claim_id for c in sorted(pack.competing_claims, key=lambda x: x.claim_id)],
        "evidence": [e.evidence_id for e in sorted(pack.evidence, key=lambda x: x.evidence_id)],
        "counter_evidence": [e.evidence_id for e in sorted(pack.counter_evidence, key=lambda x: x.evidence_id)],
        "certificates": [c.certificate_id for c in sorted(pack.validation_certificates, key=lambda x: x.certificate_id)],
        "provenance_ids": list(sorted(pack.provenance_ids)),
        "version_ids": list(sorted(pack.version_ids)),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_answer_content_hash(canonical_dict: Dict[str, Any]) -> str:
    """
    Computes SHA-256 digest over canonical dictionary payload.
    EXCLUDES answer_id, content_hash, and formatted_markdown.
    """
    try:
        raw = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception as e:
        raise AnswerSerializationError(f"Failed to compute answer content hash: {e}") from e


def compute_answer_id(content_hash: str) -> str:
    """Compute collision-resistant deterministic answer identifier."""
    return f"ANS-{content_hash[:16]}"


# =============================================================================
# ANSWER CONSTRUCTOR (PURE PROJECTION)
# =============================================================================

class AnswerConstructor:
    """
    Deterministic Answer & Exegesis Construction Engine (Task 4.6).
    Projects validated KnowledgePackResult into an immutable, provenance-preserving AnswerArtifact.
    Executes ZERO database queries, ZERO mutations, and ZERO epistemic adjudication.
    """

    def __init__(
        self,
        engine_version: str = "2.0.0",
        schema_version: str = "025",
    ) -> None:
        self.engine_version = engine_version
        self.schema_version = schema_version

    def construct_answer(
        self,
        pack: KnowledgePackResult,
        render_markdown: bool = False,
    ) -> AnswerArtifact:
        """
        Pure in-memory projection from KnowledgePackResult to AnswerArtifact.

        Preconditions (Input Contract Integrity):
          1. pack is not None and isinstance(pack, KnowledgePackResult).
          2. pack.validation_certificates is non-empty.
          3. 0.0 <= pack.aggregate_confidence <= 1.0.
          4. Canonical hash recomputation of pack matches pack.content_hash via _verify_pack_hash(pack).

        Returns:
          AnswerArtifact: Deterministic, byte-identical derived projection.
        """
        # Precondition 1: Pack validity
        if pack is None or not isinstance(pack, KnowledgePackResult):
            raise InvalidKnowledgePackError("Input must be a valid non-None KnowledgePackResult instance.")

        # Precondition 2: Authority validation certificate presence
        if not pack.validation_certificates or len(pack.validation_certificates) == 0:
            raise MissingValidationCertificateError("Knowledge pack contains no validation certificates.")

        # Precondition 3: Aggregate confidence bounds
        if not (0.0 <= pack.aggregate_confidence <= 1.0):
            raise KnowledgeConfidenceRangeError(
                f"Aggregate confidence out of bounds [0.0, 1.0]: {pack.aggregate_confidence}"
            )

        # Precondition 4: Upstream content hash integrity verification
        recomputed_pack_hash = _verify_pack_hash(pack)
        if recomputed_pack_hash != pack.content_hash:
            raise KnowledgeIntegrityViolationError(
                f"KnowledgePackResult content_hash tampering detected: expected '{pack.content_hash}', computed '{recomputed_pack_hash}'."
            )

        # 1. Project claims by tier
        tier_claims_map: Dict[str, List[AnswerClaimBlock]] = {
            "T0": [],
            "T1": [],
            "T2": [],
            "T3": [],
            "T4": [],
        }

        sorted_claims = sorted(pack.claims, key=lambda c: c.claim_id)
        for c in sorted_claims:
            if not (0.0 <= c.synthesized_confidence <= 1.0):
                raise KnowledgeConfidenceRangeError(
                    f"Claim confidence out of bounds [0.0, 1.0]: {c.synthesized_confidence}"
                )

            tier_key = c.claim_tier.value[:2] if c.claim_tier.value.startswith("T") else c.claim_tier.value
            if tier_key not in tier_claims_map:
                raise AnswerEpistemicTierViolationError(f"Unrecognized claim tier: {tier_key}")

            block = AnswerClaimBlock(
                claim_id=c.claim_id,
                claim_tier=c.claim_tier,
                primary_evidence_class=c.primary_evidence_class,
                claim_text=unicodedata.normalize("NFC", c.claim_text),
                epistemic_status=c.epistemic_status,
                confidence=c.synthesized_confidence,
                authorial_context=unicodedata.normalize("NFC", c.authorial_context),
                is_harmonized=c.is_harmonized,
                source_provenance_id=c.provenance_id,
                source_version_id=c.version_id,
                validation_certificate_id=c.validation_certificate_id,
            )
            tier_claims_map[tier_key].append(block)

        frozen_claims_by_tier: Dict[str, Tuple[AnswerClaimBlock, ...]] = {
            tier: tuple(blocks) for tier, blocks in tier_claims_map.items()
        }

        # 2. Project symmetrical evidence
        sorted_evidence = sorted(
            pack.evidence,
            key=lambda e: (e.evidence_role.value, e.item_rank, e.evidence_id),
        )
        supporting_evidence: Tuple[AnswerEvidenceBlock, ...] = tuple(
            AnswerEvidenceBlock(
                evidence_id=e.evidence_id,
                search_branch=e.search_branch,
                evidence_role=e.evidence_role,
                candidate_source=e.candidate_source,
                confidence=e.item_confidence,
                rank=e.item_rank,
                linked_claim_id=e.linked_claim_id,
                extracted_text=unicodedata.normalize("NFC", e.extracted_text) if e.extracted_text else None,
            )
            for e in sorted_evidence
        )

        sorted_counter = sorted(
            pack.counter_evidence,
            key=lambda e: (e.evidence_role.value, e.item_rank, e.evidence_id),
        )
        counter_evidence: Tuple[AnswerEvidenceBlock, ...] = tuple(
            AnswerEvidenceBlock(
                evidence_id=e.evidence_id,
                search_branch=e.search_branch,
                evidence_role=e.evidence_role,
                candidate_source=e.candidate_source,
                confidence=e.item_confidence,
                rank=e.item_rank,
                linked_claim_id=e.linked_claim_id,
                extracted_text=unicodedata.normalize("NFC", e.extracted_text) if e.extracted_text else None,
            )
            for e in sorted_counter
        )

        # 3. Project preserved dialectical tensions
        sorted_tensions = sorted(pack.tensions, key=lambda t: t.tension_id)
        preserved_tensions: Tuple[AnswerTensionBlock, ...] = tuple(
            AnswerTensionBlock(
                tension_id=t.tension_id,
                tension_type=t.tension_type,
                primary_claim_id=t.primary_claim_id,
                secondary_claim_id=t.secondary_claim_id,
                description=unicodedata.normalize("NFC", t.description),
                preservation_rationale=unicodedata.normalize("NFC", t.preservation_rationale),
                resolution_status=t.resolution_status,
                source_provenance_id=t.provenance_id,
                source_version_id=t.version_id,
            )
            for t in sorted_tensions
        )

        # 4. Compute lineage summary
        lineage_summary = self._summarize_lineage(pack.lineage, pack.resolved_scope)

        # 5. Extract certificates and identities
        sorted_certs = sorted(pack.validation_certificates, key=lambda c: c.certificate_id)
        primary_cert_id = sorted_certs[0].certificate_id
        validation_identities = tuple(sorted(set(c.validation_identity for c in sorted_certs)))

        # 6. Provenance & version identifiers
        source_prov_ids = tuple(sorted(set(pack.provenance_ids)))
        source_ver_ids = tuple(sorted(set(pack.version_ids)))
        warnings = tuple(sorted(set(pack.warnings)))

        # 7. Construct temporary canonical dictionary for content hash calculation
        temp_artifact = AnswerArtifact(
            answer_id="",
            query_text=unicodedata.normalize("NFC", pack.query.query_text),
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            pipeline_configuration_hash=pack.query.pipeline_configuration_hash,
            aggregate_confidence=pack.aggregate_confidence,
            claims_by_tier=frozen_claims_by_tier,
            supporting_evidence=supporting_evidence,
            counter_evidence=counter_evidence,
            preserved_tensions=preserved_tensions,
            lineage_summary=lineage_summary,
            primary_validation_certificate_id=primary_cert_id,
            validation_identities=validation_identities,
            input_knowledge_pack_hash=pack.content_hash,
            source_provenance_ids=source_prov_ids,
            source_version_ids=source_ver_ids,
            warnings=warnings,
            engine_version=self.engine_version,
            schema_version=self.schema_version,
            content_hash="",
            formatted_markdown=None,
        )

        canonical_dict = temp_artifact.to_canonical_dict()
        content_hash = compute_answer_content_hash(canonical_dict)
        answer_id = compute_answer_id(content_hash)

        # 8. Render optional presentation markdown
        markdown_str: Optional[str] = None
        if render_markdown:
            markdown_str = self._render_presentation_markdown(
                query_text=pack.query.query_text,
                resolved_scope=pack.resolved_scope,
                target_id=pack.target_id,
                aggregate_confidence=pack.aggregate_confidence,
                claims_by_tier=frozen_claims_by_tier,
                supporting_evidence=supporting_evidence,
                counter_evidence=counter_evidence,
                tensions=preserved_tensions,
                lineage_summary=lineage_summary,
                answer_id=answer_id,
            )

        # 9. Return final immutable AnswerArtifact
        return AnswerArtifact(
            answer_id=answer_id,
            query_text=unicodedata.normalize("NFC", pack.query.query_text),
            requested_scope=pack.requested_scope,
            resolved_scope=pack.resolved_scope,
            target_id=pack.target_id,
            synthesis_run_id=pack.synthesis_run_id,
            pipeline_configuration_hash=pack.query.pipeline_configuration_hash,
            aggregate_confidence=pack.aggregate_confidence,
            claims_by_tier=frozen_claims_by_tier,
            supporting_evidence=supporting_evidence,
            counter_evidence=counter_evidence,
            preserved_tensions=preserved_tensions,
            lineage_summary=lineage_summary,
            primary_validation_certificate_id=primary_cert_id,
            validation_identities=validation_identities,
            input_knowledge_pack_hash=pack.content_hash,
            source_provenance_ids=source_prov_ids,
            source_version_ids=source_ver_ids,
            warnings=warnings,
            engine_version=self.engine_version,
            schema_version=self.schema_version,
            content_hash=content_hash,
            formatted_markdown=markdown_str,
        )

    def _summarize_lineage(
        self,
        lineage: Tuple[ConstituentLineageNode, ...],
        resolved_scope: SynthesisScope,
    ) -> AnswerLineageSummary:
        """Compute constituent lineage hierarchy summary."""
        total_count = 0
        critical_count = 0
        root_claims: List[str] = []
        deepest_scope = resolved_scope

        scope_ranks = {
            SynthesisScope.CANON: 0,
            SynthesisScope.CORPUS: 1,
            SynthesisScope.BOOK: 2,
            SynthesisScope.SECTION: 3,
            SynthesisScope.PERICOPE: 4,
        }

        def traverse(node: ConstituentLineageNode) -> None:
            nonlocal total_count, critical_count, deepest_scope
            total_count += 1
            if node.is_critical_dependency:
                critical_count += 1
            if scope_ranks.get(node.constituent_scope, -1) > scope_ranks.get(deepest_scope, -1):
                deepest_scope = node.constituent_scope
            if node.constituent_claim_id and node.constituent_claim_id not in root_claims:
                root_claims.append(node.constituent_claim_id)
            for child in node.children:
                traverse(child)

        for n in lineage:
            if n.parent_claim_id and n.parent_claim_id not in root_claims:
                root_claims.append(n.parent_claim_id)
            traverse(n)

        return AnswerLineageSummary(
            total_constituents=total_count,
            deepest_scope=deepest_scope,
            root_claim_ids=tuple(sorted(root_claims)),
            critical_dependency_count=critical_count,
        )

    def _render_presentation_markdown(
        self,
        query_text: str,
        resolved_scope: SynthesisScope,
        target_id: str,
        aggregate_confidence: float,
        claims_by_tier: Dict[str, Tuple[AnswerClaimBlock, ...]],
        supporting_evidence: Tuple[AnswerEvidenceBlock, ...],
        counter_evidence: Tuple[AnswerEvidenceBlock, ...],
        tensions: Tuple[AnswerTensionBlock, ...],
        lineage_summary: AnswerLineageSummary,
        answer_id: str,
    ) -> str:
        """Deterministic presentation markdown renderer mapping claims verbatim."""
        lines: List[str] = [
            f"# Authoritative Exegesis & Synthesis: {target_id}",
            f"**Answer ID:** `{answer_id}`",
            f"**Query:** {query_text}",
            f"**Scope:** {resolved_scope.value} | **Aggregate Confidence:** {aggregate_confidence:.6f}",
            "",
            "## Epistemic Tier Claims",
        ]

        tier_labels = {
            "T0": "T0: Empirical & Textual Witness Claims",
            "T1": "T1: Morphosyntactic & Grammatical Claims",
            "T2": "T2: Discourse & Semantic Context Claims",
            "T3": "T3: Hierarchical Synthesis Claims",
            "T4": "T4: Dogmatic & Theological Propositions",
        }

        for tier in ("T0", "T1", "T2", "T3", "T4"):
            blocks = claims_by_tier.get(tier, ())
            lines.append(f"### {tier_labels[tier]}")
            if not blocks:
                lines.append("*No claims attested at this tier.*")
            else:
                for b in blocks:
                    harmonized_tag = " [Harmonized]" if b.is_harmonized else ""
                    lines.append(
                        f"- **[{b.claim_id}]** (Conf: {b.confidence:.4f}){harmonized_tag} {b.claim_text}"
                    )
            lines.append("")

        lines.append("## Preserved Dialectical & Theological Tensions")
        if not tensions:
            lines.append("*No dialectical tensions preserved; synthesis is consistent.*")
        else:
            for t in tensions:
                lines.append(
                    f"- **[{t.tension_id} - {t.tension_type.value}]** Primary: `{t.primary_claim_id}` vs Secondary: `{t.secondary_claim_id}`"
                )
                lines.append(f"  - *Description:* {t.description}")
                lines.append(f"  - *Preservation Rationale:* {t.preservation_rationale}")
        lines.append("")

        lines.append("## Evidence Citations")
        lines.append("### Supporting Evidence")
        if not supporting_evidence:
            lines.append("*No primary supporting evidence citations.*")
        else:
            for e in supporting_evidence:
                text_snippet = f" - \"{e.extracted_text}\"" if e.extracted_text else ""
                lines.append(
                    f"- **[{e.evidence_id}]** (Rank: {e.rank}, Role: {e.evidence_role.value}, Conf: {e.confidence:.4f}){text_snippet}"
                )
        lines.append("")

        lines.append("### Symmetrical Counter-Evidence")
        if not counter_evidence:
            lines.append("*No counter-evidence attested.*")
        else:
            for e in counter_evidence:
                text_snippet = f" - \"{e.extracted_text}\"" if e.extracted_text else ""
                lines.append(
                    f"- **[{e.evidence_id}]** (Rank: {e.rank}, Role: {e.evidence_role.value}, Conf: {e.confidence:.4f}){text_snippet}"
                )
        lines.append("")

        lines.append("## Constituent Lineage Summary")
        lines.append(f"- **Total Downward Constituents:** {lineage_summary.total_constituents}")
        lines.append(f"- **Deepest Traversed Scope:** {lineage_summary.deepest_scope.value}")
        lines.append(f"- **Critical Dependency Nodes:** {lineage_summary.critical_dependency_count}")

        return "\n".join(lines)


# =============================================================================
# FRESHNESS INSPECTION (DECOUPLED OPERATIONAL SERVICE)
# =============================================================================

@dataclass(frozen=True)
class AnswerFreshnessReport:
    """Report detailing freshness of an AnswerArtifact against live ledgers."""
    is_stale: bool
    stale_reasons: Tuple[str, ...]
    checked_synthesis_run_id: str
    checked_certificate_ids: Tuple[str, ...]
    checked_version_ids: Tuple[str, ...]


class AnswerFreshnessInspector:
    """
    Standalone operational inspector for AnswerArtifact freshness.
    Requires database connection. Operates completely outside AnswerConstructor.
    Queries verified schema (001-025) without invented tables or columns.
    """

    @staticmethod
    def inspect_freshness(
        conn: sqlite3.Connection,
        artifact: AnswerArtifact,
        current_schema_version: str = "025",
    ) -> AnswerFreshnessReport:
        """
        Verify if the underlying synthesis run, certificates, or constituent
        object versions have been superseded or invalidated in live database ledgers.
        Uses ONLY verified columns from migrations 003, 020, and 023.
        """
        reasons: List[str] = []
        checked_certs = (artifact.primary_validation_certificate_id,)
        checked_versions = artifact.source_version_ids

        # 1. Synthesis run status (020_hierarchical_synthesis.sql)
        try:
            cur = conn.execute(
                "SELECT status FROM synthesis_runs WHERE run_id = ?",
                (artifact.synthesis_run_id,),
            )
            row = cur.fetchone()
            if not row:
                reasons.append(f"Synthesis run '{artifact.synthesis_run_id}' not found in live ledger.")
            else:
                status = row["status"] if isinstance(row, sqlite3.Row) else row[0]
                if status == "SUPERSEDED":
                    reasons.append(f"Synthesis run '{artifact.synthesis_run_id}' is SUPERSEDED.")
                elif status != "COMPLETED":
                    reasons.append(f"Synthesis run '{artifact.synthesis_run_id}' has non-completed status '{status}'.")
        except sqlite3.Error as e:
            raise AnswerFreshnessInspectionError(f"Database error querying synthesis_runs: {e}") from e

        # 2. Validation certificate status and target version status (023_validation_engine.sql & 003_versioning.sql)
        try:
            for cert_id in checked_certs:
                cur = conn.execute(
                    """
                    SELECT vc.certificate_id, vc.validation_status, ov.status AS version_status
                    FROM validation_certificates vc
                    JOIN object_versions ov ON vc.target_version_id = ov.version_id
                    WHERE vc.certificate_id = ?
                    """,
                    (cert_id,),
                )
                row = cur.fetchone()
                if not row:
                    reasons.append(f"Validation certificate '{cert_id}' not found or target version missing.")
                else:
                    v_status = row["validation_status"] if isinstance(row, sqlite3.Row) else row[1]
                    ver_status = row["version_status"] if isinstance(row, sqlite3.Row) else row[2]
                    if v_status not in ("VALID", "VALID_WITH_WARNINGS"):
                        reasons.append(f"Validation certificate '{cert_id}' has invalid validation_status '{v_status}'.")
                    if ver_status in ("SUPERSEDED", "INVALIDATED"):
                        reasons.append(f"Validation certificate '{cert_id}' target version is {ver_status}.")
        except sqlite3.Error as e:
            raise AnswerFreshnessInspectionError(f"Database error querying validation_certificates: {e}") from e

        # 3. Direct inspection of all artifact source_version_ids (003_versioning.sql)
        try:
            for ver_id in checked_versions:
                cur = conn.execute(
                    "SELECT status FROM object_versions WHERE version_id = ?",
                    (ver_id,),
                )
                row = cur.fetchone()
                if not row:
                    reasons.append(f"Source version '{ver_id}' not found in object_versions ledger.")
                else:
                    status = row["status"] if isinstance(row, sqlite3.Row) else row[0]
                    if status in ("SUPERSEDED", "INVALIDATED"):
                        reasons.append(f"Source version '{ver_id}' has status '{status}'.")
        except sqlite3.Error as e:
            raise AnswerFreshnessInspectionError(f"Database error querying object_versions: {e}") from e

        # 4. Schema boundary drift
        if current_schema_version != artifact.schema_version:
            reasons.append(
                f"Schema boundary mismatch: artifact schema '{artifact.schema_version}' vs system '{current_schema_version}'."
            )

        return AnswerFreshnessReport(
            is_stale=len(reasons) > 0,
            stale_reasons=tuple(reasons),
            checked_synthesis_run_id=artifact.synthesis_run_id,
            checked_certificate_ids=checked_certs,
            checked_version_ids=checked_versions,
        )


# =============================================================================
# PROVENANCE & VERSIONING INTEGRATION HELPERS
# =============================================================================

def record_answer_provenance(
    tracker: ProvenanceTracker,
    artifact: AnswerArtifact,
    pack_hash: str,
    conn: Optional[sqlite3.Connection] = None,
) -> ProvenanceRecord:
    """
    Record deterministic provenance for an AnswerArtifact using existing ProvenanceTracker.
    TargetType.DERIVED_ARTIFACT, TransformationType.DETERMINISTIC.
    """
    return tracker.record_deterministic(
        target_type=TargetType.DERIVED_ARTIFACT,
        target_id=artifact.answer_id,
        content=artifact.to_canonical_json(),
        parent_provenance_id=artifact.source_provenance_ids[0] if artifact.source_provenance_ids else None,
        input_data={"input_knowledge_pack_hash": pack_hash, "query_text": artifact.query_text},
        config={"engine_version": artifact.engine_version, "schema_version": artifact.schema_version},
        schema_version=artifact.schema_version,
        relation_type=RelationType.DERIVED_FROM,
        conn=conn,
    )


def record_answer_version(
    version_manager: VersionManager,
    artifact: AnswerArtifact,
    provenance_id: Optional[str] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> ObjectVersion:
    """
    Record version for an AnswerArtifact in object_versions using existing VersionManager.
    """
    return version_manager.create_version(
        object_type="ANSWER_ARTIFACT",
        object_id=artifact.answer_id,
        content=artifact.to_canonical_json(),
        content_hash=artifact.content_hash,
        provenance_id=provenance_id,
        status=VersionStatus.ACTIVE,
        change_reason=ChangeReason.INITIAL_CREATION,
        conn=conn,
    )
