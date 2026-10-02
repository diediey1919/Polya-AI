"""
Authoritative Knowledge Retrieval Engine (Task 4.5).
Specification: Architecture v2.0 — Post-CANON Consumption Boundary.

Epistemic Invariants:
  1. AUTHORITY GATE:
     A synthesis artifact is retrievable as authoritative knowledge ONLY IF:
     - synthesis_run exists, status == COMPLETED, status != SUPERSEDED
     - associated ValidationEngine result exists
     - validation outcome is VALID or VALID_WITH_WARNINGS
     - validation certificate is not superseded
     - requested scope/version/config boundaries match exactly.
     Unvalidated, pending, running, failed, or blocked synthesis is strictly rejected.
  2. HIERARCHY PRESERVATION:
     Supports scopes: PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON.
     Downward lineage traversal is supported (CANON -> CORPUS -> BOOK -> SECTION -> PERICOPE -> EVIDENCE).
     Upward/downward scope confusion and scope jumping are strictly prohibited.
  3. NO CONFIDENCE INVENTIONS:
     Returns authoritative confidence established by validated synthesis.
     Never calculates, averages, weights, or inflates confidence.
     Ranking and agreement cannot inflate epistemic confidence.
  4. EPISTEMIC TIER INTEGRITY:
     Preserves original claim tiers (T0-T4).
     T4 dogmatic claims remain strictly quarantined from lower-tier evidentiary roles.
  5. MANDATORY SYMMETRICAL RETRIEVAL:
     Preserves Task 3.9 symmetry (PRIMARY + COUNTER evidence).
     Counter-search cannot be suppressed. NOT_FOUND != no counter-evidence.
  6. TENSION PRESERVATION:
     Returns existing synthesis_tensions without resolving or harmonizing them.
  7. IMMUTABLE DERIVED RESULT:
     KnowledgePackResult is an immutable in-memory transport artifact.
     Deterministic canonical sorting and SHA-256 content hash independent of SQLite row order.
     No new database migration (Migration 026 is forbidden).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CounterSearchSuppressionError,
    KnowledgeConfidenceInflationError,
    KnowledgeHierarchyViolationError,
    KnowledgeNotFoundError,
    KnowledgeQueryValidationError,
    KnowledgeRetrievalSubsystemError,
    KnowledgeTheologicalContaminationError,
    KnowledgeVersionMismatchError,
    MissingValidationCertificateError,
    SupersededKnowledgeRetrievalError,
    UnvalidatedKnowledgeRetrievalError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.provenance import ProvenanceTracker
from bible_engine.retrieval import (
    CandidateSource,
    CounterEvidenceStatus,
    CoverageRecord,
    CoverageStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalConfig,
    RetrievalPackItem,
    RetrievalPackResult,
    RetrievalTarget,
    RetrievalTargetType,
    SearchBranch,
)
from bible_engine.synthesis import (
    SCOPE_ORDER,
    HierarchicalSynthesisManager,
    SynthesisClaimStatus,
    SynthesisRunRecord,
    SynthesisRunStatus,
    SynthesisScope,
    SynthesisTensionRecord,
    SynthesisTensionResolution,
    SynthesisTensionType,
)
from bible_engine.validation import (
    ValidationCertificate,
    ValidationEngine,
    ValidationOutcome,
)
from bible_engine.versioning import VersionManager


# =============================================================================
# QUERY CONTRACT
# =============================================================================

@dataclass(frozen=True)
class KnowledgeQuery:
    """
    Deterministic Knowledge Query contract for authoritative knowledge retrieval.
    Raw query semantics; no speculative NLP intent classifier.
    """
    query_text: str
    canon_id: Optional[str] = None
    corpus_id: Optional[str] = None
    book_id: Optional[str] = None
    section_id: Optional[str] = None
    pericope_id: Optional[str] = None
    requested_scope: Optional[SynthesisScope] = None
    source_corpus: Optional[str] = None
    target_corpus: Optional[str] = None
    source_version: Optional[str] = None
    pipeline_configuration_hash: Optional[str] = None
    engine_version: Optional[str] = None
    schema_version: Optional[str] = None
    limit: int = 50
    include_lineage: bool = True
    include_evidence: bool = True
    include_tensions: bool = True

    def __post_init__(self) -> None:
        if not self.query_text or not self.query_text.strip():
            raise KnowledgeQueryValidationError("Query text cannot be empty.")
        if self.limit <= 0:
            raise KnowledgeQueryValidationError("Query limit must be positive.")

        # Validate scope consistency if both requested_scope and target IDs are provided
        if self.requested_scope is not None:
            if self.requested_scope == SynthesisScope.CANON and (self.corpus_id or self.book_id or self.section_id or self.pericope_id):
                raise KnowledgeHierarchyViolationError(
                    "Scope Mismatch: requested_scope CANON cannot be combined with lower-scope IDs."
                )
            if self.requested_scope != SynthesisScope.CANON and self.canon_id is not None:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Mismatch: canon_id provided with non-CANON requested_scope '{self.requested_scope.value}'."
                )
            if self.requested_scope != SynthesisScope.CORPUS and self.corpus_id is not None:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Mismatch: corpus_id provided with non-CORPUS requested_scope '{self.requested_scope.value}'."
                )
            if self.requested_scope != SynthesisScope.BOOK and self.book_id is not None:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Mismatch: book_id provided with non-BOOK requested_scope '{self.requested_scope.value}'."
                )
            if self.requested_scope != SynthesisScope.SECTION and self.section_id is not None:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Mismatch: section_id provided with non-SECTION requested_scope '{self.requested_scope.value}'."
                )
            if self.requested_scope != SynthesisScope.PERICOPE and self.pericope_id is not None:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Mismatch: pericope_id provided with non-PERICOPE requested_scope '{self.requested_scope.value}'."
                )


# =============================================================================
# AUTHORITATIVE TRANSPORT DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class AuthoritativeClaimItem:
    """Immutable representation of an authoritatively validated synthesis claim."""
    claim_id: str
    run_id: str
    scope: SynthesisScope
    target_id: str
    claim_tier: ClaimTier
    primary_evidence_class: EvidenceClass
    claim_text: str
    epistemic_status: SynthesisClaimStatus
    synthesized_confidence: float
    weakest_constituent_confidence: float
    authorial_context: str
    is_harmonized: bool
    provenance_id: str
    version_id: str
    validation_certificate_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class AuthoritativeTensionItem:
    """Immutable representation of a preserved dialectical/exegetical tension."""
    tension_id: str
    run_id: str
    scope: SynthesisScope
    target_id: str
    tension_type: SynthesisTensionType
    primary_claim_id: str
    secondary_claim_id: str
    description: str
    preservation_rationale: str
    resolution_status: SynthesisTensionResolution
    provenance_id: str
    version_id: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class AuthoritativeEvidenceItem:
    """Immutable representation of an evidence item retrieved via symmetrical search."""
    item_id: str
    evidence_id: str
    search_branch: SearchBranch
    evidence_role: EvidenceRole
    candidate_source: CandidateSource
    item_confidence: float
    item_rank: int
    linked_claim_id: Optional[str]
    extracted_text: Optional[str] = None


@dataclass(frozen=True)
class ConstituentLineageNode:
    """Node in the downward constituent hierarchy tree (CANON -> CORPUS -> BOOK -> SECTION -> PERICOPE -> EVIDENCE)."""
    constituent_link_id: str
    parent_claim_id: str
    constituent_scope: SynthesisScope
    constituent_target_id: str
    constituent_claim_id: Optional[str]
    constituent_evidence_id: Optional[str]
    constituent_confidence: float
    is_critical_dependency: bool
    run_id: str
    provenance_id: Optional[str] = None
    validation_certificate_id: Optional[str] = None
    children: Tuple[ConstituentLineageNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class KnowledgePackResult:
    """
    Deterministic transport artifact returned by AuthoritativeKnowledgeRetrievalEngine.
    Immutable, in-memory derived representation. Zero DB mutations during retrieval.
    """
    query: KnowledgeQuery
    requested_scope: Optional[SynthesisScope]
    resolved_scope: SynthesisScope
    target_id: str
    synthesis_run_id: str
    aggregate_confidence: float
    claims: Tuple[AuthoritativeClaimItem, ...]
    tensions: Tuple[AuthoritativeTensionItem, ...]
    competing_claims: Tuple[AuthoritativeClaimItem, ...]
    evidence: Tuple[AuthoritativeEvidenceItem, ...]
    counter_evidence: Tuple[AuthoritativeEvidenceItem, ...]
    lineage: Tuple[ConstituentLineageNode, ...]
    validation_certificates: Tuple[ValidationCertificate, ...]
    provenance_ids: Tuple[str, ...]
    version_ids: Tuple[str, ...]
    warnings: Tuple[str, ...]
    content_hash: str


# =============================================================================
# KNOWLEDGE RETRIEVAL ENGINE
# =============================================================================

class AuthoritativeKnowledgeRetrievalEngine:
    """
    Authoritative Knowledge Retrieval Engine (Task 4.5).
    Retrieves existing validated synthesis, downward constituent lineage,
    preserved tensions, and symmetrical evidence without inventing knowledge.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        retrieval_engine: Optional[HybridSymmetricalRetrievalEngine] = None,
        synthesis_manager: Optional[HierarchicalSynthesisManager] = None,
        validation_engine: Optional[ValidationEngine] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
        default_engine_version: str = "2.0.0",
        default_schema_version: str = "025",
    ) -> None:
        self.engine = engine
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.version_manager = version_manager or VersionManager(engine)
        self.retrieval_engine = retrieval_engine or HybridSymmetricalRetrievalEngine(
            engine, self.provenance_tracker, self.version_manager
        )
        self.synthesis_manager = synthesis_manager or HierarchicalSynthesisManager(
            engine, self.version_manager, self.provenance_tracker
        )
        self.validation_engine = validation_engine or ValidationEngine(
            engine, self.provenance_tracker, self.version_manager, self.retrieval_engine
        )
        self.default_engine_version = default_engine_version
        self.default_schema_version = default_schema_version

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    def retrieve_knowledge(
        self,
        query: KnowledgeQuery,
        **kwargs: Any,
    ) -> KnowledgePackResult:
        """
        Execute authoritative knowledge retrieval adhering to all epistemic invariants:
        - Authority Gate: ONLY COMPLETED, non-superseded, certified synthesis runs.
        - Symmetry Invariant: Counter-search cannot be suppressed.
        - Confidence Invariant: Authoritative weakest-link confidence preserved; no averaging.
        - Tension Preservation: Dialectical tensions returned without harmonization.
        - Lineage: Downward constituent traversal without fabrication.
        """
        # 1. Check for counter-search suppression attempts
        if "enable_counter_search" in kwargs or "disable_counter_search" in kwargs or "skip_counter_search" in kwargs:
            raise CounterSearchSuppressionError(
                "Counter-search is an architectural invariant and cannot be disabled or suppressed."
            )
        for k, v in kwargs.items():
            if "counter" in k.lower() and v is False:
                raise CounterSearchSuppressionError(
                    f"Attempted to suppress counter-search via '{k}=False'. Counter-search is mandatory."
                )

        # 2. Resolve Target Scope & ID
        resolved_scope, target_id = self._resolve_target(query)

        # 3. Enforce Authority Gate
        with self.engine.connect() as conn:
            run_row, cert_rows = self._verify_authority_gate(conn, resolved_scope, target_id, query)
            run_id = run_row["run_id"]
            primary_cert = cert_rows[0]

            # 4. Fetch Claims (Certified & Epistemically Classified)
            claims, competing_claims = self._fetch_claims(conn, run_id, primary_cert["certificate_id"])

            # 5. Fetch Preserved Tensions
            tensions: List[AuthoritativeTensionItem] = []
            if query.include_tensions:
                tensions = self._fetch_tensions(conn, run_id, resolved_scope, target_id)

            # 6. Resolve Downward Lineage
            lineage: Tuple[ConstituentLineageNode, ...] = ()
            if query.include_lineage:
                lineage = self._resolve_downward_lineage(conn, run_id, resolved_scope, query)

        # 7. Symmetrical Evidence Retrieval (Task 3.9 Composition)
        primary_evidence: List[AuthoritativeEvidenceItem] = []
        counter_evidence: List[AuthoritativeEvidenceItem] = []
        warnings: List[str] = []

        if query.include_evidence:
            primary_evidence, counter_evidence, ev_warnings = self._fetch_symmetrical_evidence(
                query=query,
                target_scope=resolved_scope,
                target_id=target_id,
            )
            warnings.extend(ev_warnings)

        # 8. Weakest-Link Confidence
        if claims:
            aggregate_confidence = min(c.synthesized_confidence for c in claims)
        else:
            aggregate_confidence = float(run_row["aggregate_confidence"])

        # 9. Collect Provenance & Version IDs
        prov_set: Set[str] = {run_row["provenance_id"]}
        ver_set: Set[str] = {run_row["version_id"]}

        for c in cert_rows:
            prov_set.add(c["provenance_id"])
        for cl in claims:
            prov_set.add(cl.provenance_id)
            ver_set.add(cl.version_id)
        for t in tensions:
            prov_set.add(t.provenance_id)
            ver_set.add(t.version_id)

        sorted_prov_ids = tuple(sorted(prov_set))
        sorted_ver_ids = tuple(sorted(ver_set))
        sorted_claims = tuple(sorted(claims, key=lambda x: x.claim_id))
        sorted_tensions = tuple(sorted(tensions, key=lambda x: x.tension_id))
        sorted_competing = tuple(sorted(competing_claims, key=lambda x: x.claim_id))
        sorted_evidence = tuple(sorted(primary_evidence, key=lambda x: x.evidence_id))
        sorted_counter_evidence = tuple(sorted(counter_evidence, key=lambda x: x.evidence_id))
        sorted_warnings = tuple(sorted(set(warnings)))

        certificates = tuple(
            self.validation_engine._row_to_certificate(r) for r in sorted(cert_rows, key=lambda x: x["certificate_id"])
        )

        # 10. Compute Deterministic Content Hash
        content_hash = self._compute_canonical_hash(
            resolved_scope=resolved_scope,
            target_id=target_id,
            run_id=run_id,
            aggregate_conf=aggregate_confidence,
            claims=sorted_claims,
            tensions=sorted_tensions,
            competing_claims=sorted_competing,
            evidence=sorted_evidence,
            counter_evidence=sorted_counter_evidence,
            lineage=lineage,
            certificates=certificates,
            provenance_ids=sorted_prov_ids,
            version_ids=sorted_ver_ids,
        )

        return KnowledgePackResult(
            query=query,
            requested_scope=query.requested_scope,
            resolved_scope=resolved_scope,
            target_id=target_id,
            synthesis_run_id=run_id,
            aggregate_confidence=aggregate_confidence,
            claims=sorted_claims,
            tensions=sorted_tensions,
            competing_claims=sorted_competing,
            evidence=sorted_evidence,
            counter_evidence=sorted_counter_evidence,
            lineage=lineage,
            validation_certificates=certificates,
            provenance_ids=sorted_prov_ids,
            version_ids=sorted_ver_ids,
            warnings=sorted_warnings,
            content_hash=content_hash,
        )

    # -------------------------------------------------------------------------
    # INTERNAL HELPERS
    # -------------------------------------------------------------------------

    def _resolve_target(self, query: KnowledgeQuery) -> Tuple[SynthesisScope, str]:
        """Resolve authoritative scope and target_id from the query contract."""
        if query.canon_id:
            if query.requested_scope and query.requested_scope != SynthesisScope.CANON:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Conflict: canon_id provided with non-CANON requested_scope '{query.requested_scope.value}'."
                )
            return SynthesisScope.CANON, query.canon_id
        if query.corpus_id:
            if query.requested_scope and query.requested_scope != SynthesisScope.CORPUS:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Conflict: corpus_id provided with non-CORPUS requested_scope '{query.requested_scope.value}'."
                )
            return SynthesisScope.CORPUS, query.corpus_id
        if query.book_id:
            if query.requested_scope and query.requested_scope != SynthesisScope.BOOK:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Conflict: book_id provided with non-BOOK requested_scope '{query.requested_scope.value}'."
                )
            return SynthesisScope.BOOK, query.book_id
        if query.section_id:
            if query.requested_scope and query.requested_scope != SynthesisScope.SECTION:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Conflict: section_id provided with non-SECTION requested_scope '{query.requested_scope.value}'."
                )
            return SynthesisScope.SECTION, query.section_id
        if query.pericope_id:
            if query.requested_scope and query.requested_scope != SynthesisScope.PERICOPE:
                raise KnowledgeHierarchyViolationError(
                    f"Scope Conflict: pericope_id provided with non-PERICOPE requested_scope '{query.requested_scope.value}'."
                )
            return SynthesisScope.PERICOPE, query.pericope_id

        # If only requested_scope is provided without a target ID
        if query.requested_scope:
            raise KnowledgeQueryValidationError(
                f"Scope '{query.requested_scope.value}' requested without specifying target identifier."
            )

        raise KnowledgeQueryValidationError(
            "Knowledge query requires at least one target scope identifier (canon_id, corpus_id, book_id, section_id, or pericope_id)."
        )

    def _verify_authority_gate(
        self,
        conn: sqlite3.Connection,
        scope: SynthesisScope,
        target_id: str,
        query: KnowledgeQuery,
    ) -> Tuple[sqlite3.Row, List[sqlite3.Row]]:
        """
        Enforce the 7-Point Authority Gate Invariant:
        1. synthesis_run exists
        2. synthesis status is COMPLETED
        3. synthesis is not SUPERSEDED
        4. associated ValidationEngine result exists
        5. validation outcome is VALID or VALID_WITH_WARNINGS
        6. validation certificate is not superseded
        7. requested scope/version/config boundaries match
        """
        cur = conn.execute(
            """
            SELECT run_id, scope, target_id, parent_scope, parent_target_id,
                   synthesizer_id, synthesizer_version, configuration_hash,
                   input_content_hash, output_hash, aggregate_confidence,
                   status, provenance_id, version_id, created_at, metadata_json
            FROM synthesis_runs
            WHERE scope = ? AND target_id = ?
            ORDER BY created_at DESC
            """,
            (scope.value, target_id),
        )
        run_rows = cur.fetchall()
        if not run_rows:
            raise KnowledgeNotFoundError(
                f"Authority Gate Failure: No synthesis run exists for scope '{scope.value}' and target '{target_id}'."
            )

        run_row = run_rows[0]
        run_id = run_row["run_id"]
        run_status = run_row["status"]

        # Check synthesis run status
        if run_status == SynthesisRunStatus.SUPERSEDED.value:
            raise SupersededKnowledgeRetrievalError(
                f"Authority Gate Failure: Synthesis run '{run_id}' for target '{target_id}' is SUPERSEDED."
            )
        if run_status in (SynthesisRunStatus.INITIALIZED.value, SynthesisRunStatus.PROCESSING.value, "PENDING", "RUNNING"):
            raise UnvalidatedKnowledgeRetrievalError(
                f"Authority Gate Failure: Synthesis run '{run_id}' is in non-completed status '{run_status}'."
            )
        if run_status in (SynthesisRunStatus.FAILED.value, "BLOCKED"):
            raise UnvalidatedKnowledgeRetrievalError(
                f"Authority Gate Failure: Synthesis run '{run_id}' terminated in status '{run_status}'."
            )
        if run_status != SynthesisRunStatus.COMPLETED.value:
            raise UnvalidatedKnowledgeRetrievalError(
                f"Authority Gate Failure: Synthesis run '{run_id}' status is '{run_status}', expected COMPLETED."
            )

        # Check associated ValidationEngine result and certificates
        val_cur = conn.execute(
            """
            SELECT final_outcome, checks_passed, checks_failed, warnings_total
            FROM validation_runs
            WHERE target_id = ? OR target_id = ?
            ORDER BY executed_at DESC
            """,
            (run_id, target_id),
        )
        val_runs = val_cur.fetchall()
        if val_runs:
            latest_val = val_runs[0]
            if latest_val["final_outcome"] == "BLOCKED" or latest_val["final_outcome"] == "FAILED":
                raise UnvalidatedKnowledgeRetrievalError(
                    f"Authority Gate Failure: Validation for synthesis run '{run_id}' outcome is '{latest_val['final_outcome']}'."
                )

        cert_cur = conn.execute(
            """
            SELECT c.*, v.final_outcome
            FROM validation_certificates c
            JOIN validation_runs v ON c.run_id = v.run_id
            WHERE (c.target_id = ? OR c.target_id = ?)
            ORDER BY c.validated_at DESC
            """,
            (run_id, target_id),
        )
        cert_rows = cert_cur.fetchall()
        if not cert_rows:
            raise MissingValidationCertificateError(
                f"Authority Gate Failure: Synthesis run '{run_id}' for '{target_id}' lacks an authoritative validation certificate."
            )

        valid_certs = []
        for c in cert_rows:
            val_status = c["validation_status"]
            outcome = c["final_outcome"]
            if val_status in ("VALID", "VALID_WITH_WARNINGS") and outcome in ("VALID", "VALID_WITH_WARNINGS"):
                valid_certs.append(c)
            elif val_status == "BLOCKED" or outcome == "BLOCKED":
                raise UnvalidatedKnowledgeRetrievalError(
                    f"Authority Gate Failure: Validation certificate '{c['certificate_id']}' has outcome BLOCKED."
                )

        if not valid_certs:
            raise MissingValidationCertificateError(
                f"Authority Gate Failure: No non-blocked validation certificate found for synthesis run '{run_id}'."
            )

        # Check if version is superseded in object_versions
        v_cur = conn.execute(
            "SELECT status FROM object_versions WHERE version_id = ?",
            (run_row["version_id"],),
        )
        v_row = v_cur.fetchone()
        if v_row and v_row["status"] == "SUPERSEDED":
            raise SupersededKnowledgeRetrievalError(
                f"Authority Gate Failure: Synthesis version '{run_row['version_id']}' is SUPERSEDED."
            )

        primary_cert = valid_certs[0]

        # Check version and configuration boundaries
        if query.engine_version and primary_cert["engine_version"] != query.engine_version:
            raise KnowledgeVersionMismatchError(
                f"Version Boundary Mismatch: Certificate engine_version '{primary_cert['engine_version']}' does not match requested '{query.engine_version}'."
            )
        if query.schema_version and primary_cert["schema_version"] != query.schema_version:
            raise KnowledgeVersionMismatchError(
                f"Schema Boundary Mismatch: Certificate schema_version '{primary_cert['schema_version']}' does not match requested '{query.schema_version}'."
            )
        if query.pipeline_configuration_hash and run_row["configuration_hash"] != query.pipeline_configuration_hash:
            raise KnowledgeVersionMismatchError(
                f"Configuration Boundary Mismatch: Synthesis configuration_hash '{run_row['configuration_hash']}' does not match requested '{query.pipeline_configuration_hash}'."
            )
        if query.source_version and run_row["version_id"] != query.source_version:
            raise KnowledgeVersionMismatchError(
                f"Version Boundary Mismatch: Synthesis version_id '{run_row['version_id']}' does not match requested '{query.source_version}'."
            )

        return run_row, valid_certs

    def _fetch_claims(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        cert_id: str,
    ) -> Tuple[List[AuthoritativeClaimItem], List[AuthoritativeClaimItem]]:
        """Fetch and categorize authoritative claims from synthesis_claims."""
        cur = conn.execute(
            """
            SELECT claim_id, run_id, scope, target_id, claim_tier,
                   primary_evidence_class, claim_text, epistemic_status,
                   synthesized_confidence, weakest_constituent_confidence,
                   authorial_context, is_harmonized, provenance_id, version_id,
                   created_at, metadata_json
            FROM synthesis_claims
            WHERE run_id = ? AND epistemic_status != 'SUPERSEDED'
            ORDER BY claim_id ASC
            """,
            (run_id,),
        )
        claims: List[AuthoritativeClaimItem] = []
        competing: List[AuthoritativeClaimItem] = []

        for row in cur.fetchall():
            tier = ClaimTier(row["claim_tier"])
            ev_class = EvidenceClass(row["primary_evidence_class"])
            status = SynthesisClaimStatus(row["epistemic_status"])
            item = AuthoritativeClaimItem(
                claim_id=row["claim_id"],
                run_id=row["run_id"],
                scope=SynthesisScope(row["scope"]),
                target_id=row["target_id"],
                claim_tier=tier,
                primary_evidence_class=ev_class,
                claim_text=row["claim_text"],
                epistemic_status=status,
                synthesized_confidence=float(row["synthesized_confidence"]),
                weakest_constituent_confidence=float(row["weakest_constituent_confidence"]),
                authorial_context=row["authorial_context"],
                is_harmonized=bool(row["is_harmonized"]),
                provenance_id=row["provenance_id"],
                version_id=row["version_id"],
                validation_certificate_id=cert_id,
                created_at=row["created_at"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
            )
            claims.append(item)
            if status in (SynthesisClaimStatus.COMPETING, SynthesisClaimStatus.TENSION, SynthesisClaimStatus.UNRESOLVED):
                competing.append(item)

        return claims, competing

    def _fetch_tensions(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        scope: SynthesisScope,
        target_id: str,
    ) -> List[AuthoritativeTensionItem]:
        """Fetch preserved tensions from synthesis_tensions."""
        cur = conn.execute(
            """
            SELECT tension_id, run_id, scope, target_id, tension_type,
                   primary_claim_id, secondary_claim_id, description,
                   preservation_rationale, resolution_status, provenance_id,
                   version_id, created_at, metadata_json
            FROM synthesis_tensions
            WHERE run_id = ? AND resolution_status != 'SUPERSEDED'
            ORDER BY tension_id ASC
            """,
            (run_id,),
        )
        tensions: List[AuthoritativeTensionItem] = []
        for row in cur.fetchall():
            tensions.append(
                AuthoritativeTensionItem(
                    tension_id=row["tension_id"],
                    run_id=row["run_id"],
                    scope=SynthesisScope(row["scope"]),
                    target_id=row["target_id"],
                    tension_type=SynthesisTensionType(row["tension_type"]),
                    primary_claim_id=row["primary_claim_id"],
                    secondary_claim_id=row["secondary_claim_id"],
                    description=row["description"],
                    preservation_rationale=row["preservation_rationale"],
                    resolution_status=SynthesisTensionResolution(row["resolution_status"]),
                    provenance_id=row["provenance_id"],
                    version_id=row["version_id"],
                    created_at=row["created_at"],
                    metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
                )
            )
        return tensions

    def _resolve_downward_lineage(
        self,
        conn: sqlite3.Connection,
        run_id: str,
        parent_scope: SynthesisScope,
        query: KnowledgeQuery,
        depth: int = 0,
    ) -> Tuple[ConstituentLineageNode, ...]:
        """
        Recursively traverse downward constituent links from synthesis_constituents:
        CANON -> CORPUS -> BOOK -> SECTION -> PERICOPE -> EVIDENCE
        Enforces strict downward directionality.
        """
        if depth > 6:
            return ()

        cur = conn.execute(
            """
            SELECT constituent_link_id, run_id, claim_id, constituent_scope,
                   constituent_target_id, constituent_claim_id, constituent_evidence_id,
                   constituent_confidence, is_critical_dependency, created_at
            FROM synthesis_constituents
            WHERE run_id = ?
            ORDER BY constituent_link_id ASC
            """,
            (run_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return ()

        nodes: List[ConstituentLineageNode] = []
        parent_rank = SCOPE_ORDER[parent_scope]

        for r in rows:
            c_scope = SynthesisScope(r["constituent_scope"])
            c_rank = SCOPE_ORDER[c_scope]

            # Invariant: Downward directionality
            if c_rank >= parent_rank:
                raise KnowledgeHierarchyViolationError(
                    f"Hierarchy Violation: Parent scope '{parent_scope.value}' (rank {parent_rank}) "
                    f"has non-downward constituent scope '{c_scope.value}' (rank {c_rank})."
                )

            # Look up constituent child run if it's a synthesis claim
            child_run_id: Optional[str] = None
            cert_id: Optional[str] = None
            prov_id: Optional[str] = None

            if r["constituent_claim_id"]:
                cl_cur = conn.execute(
                    "SELECT run_id, provenance_id FROM synthesis_claims WHERE claim_id = ?",
                    (r["constituent_claim_id"],),
                )
                cl_row = cl_cur.fetchone()
                if cl_row:
                    child_run_id = cl_row["run_id"]
                    prov_id = cl_row["provenance_id"]

                    # Fetch certificate of child run
                    cert_cur = conn.execute(
                        "SELECT certificate_id FROM validation_certificates WHERE target_id = ? ORDER BY validated_at DESC LIMIT 1",
                        (child_run_id,),
                    )
                    cert_row = cert_cur.fetchone()
                    if cert_row:
                        cert_id = cert_row["certificate_id"]

            # Recurse downward if child run exists
            children: Tuple[ConstituentLineageNode, ...] = ()
            if child_run_id and child_run_id != run_id:
                children = self._resolve_downward_lineage(
                    conn=conn,
                    run_id=child_run_id,
                    parent_scope=c_scope,
                    query=query,
                    depth=depth + 1,
                )

            nodes.append(
                ConstituentLineageNode(
                    constituent_link_id=r["constituent_link_id"],
                    parent_claim_id=r["claim_id"],
                    constituent_scope=c_scope,
                    constituent_target_id=r["constituent_target_id"],
                    constituent_claim_id=r["constituent_claim_id"],
                    constituent_evidence_id=r["constituent_evidence_id"],
                    constituent_confidence=float(r["constituent_confidence"]),
                    is_critical_dependency=bool(r["is_critical_dependency"]),
                    run_id=run_id,
                    provenance_id=prov_id,
                    validation_certificate_id=cert_id,
                    children=children,
                )
            )

        return tuple(nodes)

    def _fetch_symmetrical_evidence(
        self,
        query: KnowledgeQuery,
        target_scope: SynthesisScope,
        target_id: str,
    ) -> Tuple[List[AuthoritativeEvidenceItem], List[AuthoritativeEvidenceItem], List[str]]:
        """
        Execute symmetrical evidence retrieval using HybridSymmetricalRetrievalEngine.
        Enforces T4 quarantine and preserves Task 3.9 absence-of-evidence semantics.
        """
        warnings: List[str] = []
        cfg = RetrievalConfig(
            limit_primary=min(query.limit, 20),
            limit_counter=min(query.limit, 20),
        )
        target = RetrievalTarget(
            target_type=RetrievalTargetType.FREE_TEXT,
            target_id=target_id,
        )

        pack_result = self.retrieval_engine.execute_retrieval(
            query=query.query_text,
            target=target,
            config=cfg,
        )

        # Absence of evidence check
        if pack_result.counter_evidence_status == CounterEvidenceStatus.COUNTER_EVIDENCE_NOT_FOUND:
            warnings.append(
                "COUNTER_EVIDENCE_NOT_FOUND: Negative search result does not imply absence of counter-evidence in the canon."
            )

        primary_items: List[AuthoritativeEvidenceItem] = []
        counter_items: List[AuthoritativeEvidenceItem] = []

        with self.engine.connect() as conn:
            for item in pack_result.items:
                # T4 Theology Quarantine Check: Ensure T4 claim is NEVER supporting evidence for lower-tier scopes
                if item.linked_claim_id:
                    c_cur = conn.execute(
                        "SELECT claim_tier FROM claims WHERE claim_id = ?",
                        (item.linked_claim_id,),
                    )
                    c_row = c_cur.fetchone()
                    if c_row and c_row["claim_tier"] in ("T4", "T4_THEOLOGICAL_CLAIM", "TIER_4_THEOLOGICAL_CLAIM"):
                        if item.evidence_role == EvidenceRole.SUPPORTING:
                            raise KnowledgeTheologicalContaminationError(
                                f"Theology Firewall Violation: T4 dogmatic claim '{item.linked_claim_id}' "
                                f"cannot serve as supporting evidence in knowledge retrieval."
                            )

                # Check if this evidence is linked to any T4 claim in a supporting relationship
                t4_cur = conn.execute(
                    """
                    SELECT l.claim_id, c.claim_tier
                    FROM claim_evidence_links l
                    JOIN claims c ON l.claim_id = c.claim_id
                    WHERE l.evidence_id = ? AND l.relationship IN ('SUPPORT', 'SUPPORTS')
                      AND c.claim_tier IN ('T4', 'T4_THEOLOGICAL_CLAIM', 'TIER_4_THEOLOGICAL_CLAIM')
                    """,
                    (item.evidence_id,),
                )
                t4_row = t4_cur.fetchone()
                if t4_row and item.evidence_role == EvidenceRole.SUPPORTING:
                    raise KnowledgeTheologicalContaminationError(
                        f"Theology Firewall Violation: Evidence '{item.evidence_id}' is linked to T4 dogmatic claim "
                        f"'{t4_row['claim_id']}' in a supporting role."
                    )

                # Fetch extracted text from evidence_ledger
                ev_cur = conn.execute(
                    "SELECT extracted_text_or_data FROM evidence_ledger WHERE evidence_id = ?",
                    (item.evidence_id,),
                )
                ev_row = ev_cur.fetchone()
                extracted_text = ev_row["extracted_text_or_data"] if ev_row else None

                auth_item = AuthoritativeEvidenceItem(
                    item_id=item.item_id,
                    evidence_id=item.evidence_id,
                    search_branch=item.search_branch,
                    evidence_role=item.evidence_role,
                    candidate_source=item.candidate_source,
                    item_confidence=item.item_confidence,
                    item_rank=item.item_rank,
                    linked_claim_id=item.linked_claim_id,
                    extracted_text=extracted_text,
                )

                if item.evidence_role == EvidenceRole.COUNTER_EVIDENCE:
                    counter_items.append(auth_item)
                else:
                    primary_items.append(auth_item)

        return primary_items, counter_items, warnings

    def _compute_canonical_hash(
        self,
        resolved_scope: SynthesisScope,
        target_id: str,
        run_id: str,
        aggregate_conf: float,
        claims: Tuple[AuthoritativeClaimItem, ...],
        tensions: Tuple[AuthoritativeTensionItem, ...],
        competing_claims: Tuple[AuthoritativeClaimItem, ...],
        evidence: Tuple[AuthoritativeEvidenceItem, ...],
        counter_evidence: Tuple[AuthoritativeEvidenceItem, ...],
        lineage: Tuple[ConstituentLineageNode, ...],
        certificates: Tuple[ValidationCertificate, ...],
        provenance_ids: Tuple[str, ...],
        version_ids: Tuple[str, ...],
    ) -> str:
        """Compute canonical deterministic SHA-256 hash of the knowledge pack."""
        payload = {
            "resolved_scope": resolved_scope.value,
            "target_id": target_id,
            "synthesis_run_id": run_id,
            "aggregate_confidence": round(aggregate_conf, 6),
            "claims": [c.claim_id for c in claims],
            "tensions": [t.tension_id for t in tensions],
            "competing_claims": [c.claim_id for c in competing_claims],
            "evidence": [e.evidence_id for e in evidence],
            "counter_evidence": [e.evidence_id for e in counter_evidence],
            "certificates": [c.certificate_id for c in certificates],
            "provenance_ids": list(provenance_ids),
            "version_ids": list(version_ids),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
