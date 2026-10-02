"""
Polya Philological Bible Engine — Canon-Level Synthesis Aggregator (Task 4.4)
=============================================================================
Architecture Revision V1 — FROZEN SPECIFICATION

The CanonAggregator orchestrates bottom-up synthesis from CORPUS to CANON:
    PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON

Core Responsibilities:
1. CANON BOUNDARY DISCOVERY:
   Resolves authoritative constituent corpora belonging to a canon from the
   canonical catalog (canons -> testaments).

2. COMPLETENESS ENFORCEMENT:
   Verifies that every required constituent corpus within the canonical catalog
   has an authoritative completed Task 4.3 CORPUS synthesis with an authoritative
   Task 4.0 validation result (VALID or VALID_WITH_WARNINGS) matching boundaries.
   Zero partial canon aggregation. Zero tolerance for unvalidated/blocked corpora.

3. HIERARCHICAL DIRECTIONALITY:
   CANON synthesis consumes ONLY lower-level CORPUS constituents. Direct skips
   from PERICOPE, SECTION, or BOOK to CANON are strictly prohibited.

4. DETERMINISTIC LOGICAL IDENTITY:
   Generates a reproducible logical synthesis identity independent of execution
   history, worker IDs, timestamps, batch IDs, or SQLite insertion ordering.

5. WEAKEST-LINK CONFIDENCE PROPAGATION:
   Delegates synthesis strictly to HierarchicalSynthesisManager. The aggregate
   confidence is bounded by the minimum of critical constituent confidences.
   No averaging, no frequency weighting, no majority voting.

6. EPISTEMIC VALIDATION INTEGRATION:
   Binds full corpus constituent lineage into ValidationInput and validates
   against Task 4.0 ValidationEngine (target_type='CANON_SYNTHESIS').

7. FAST-PATH IDEMPOTENCY & CRASH SAFETY:
   Reuses existing validated syntheses without duplication. Safely resumes
   validation if a previous run crashed after synthesis persistence. Refuses
   to silently override blocked validations.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CanonBlockedValidationError,
    CanonHierarchyViolationError,
    CanonIncompleteError,
    CanonSubsystemError,
    CorpusSubsystemError,
    PipelineBlockedValidationError,
    SynthesisConfidenceInflationError,
    SynthesisMissingConstituentError,
    SynthesisNotFoundError,
    SynthesisScopeJumpError,
    SynthesisValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.pipeline import PipelineConfig
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import (
    HybridSymmetricalRetrievalEngine,
    RetrievalTarget,
    RetrievalTargetType,
)
from bible_engine.synthesis import (
    ConstituentInput,
    HierarchicalSynthesisManager,
    SCOPE_ORDER,
    SynthesisClaimInput,
    SynthesisClaimRecord,
    SynthesisClaimStatus,
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
from bible_engine.validation import (
    EvidenceDependencies,
    LayerCode,
    RetrievalLineage,
    ValidationEngine,
    ValidationEnvironment,
    ValidationInput,
    ValidationOutcome,
    ValidationRun,
    ValidationTarget,
)
from bible_engine.versioning import VersionManager


# =============================================================================
# DETERMINISTIC CANONICAL IDENTITY & CATALOG RESOLUTION
# =============================================================================

def compute_canon_synthesis_identity(
    canonical_canon_id: str,
    constituent_corpus_identities: Sequence[str],
    pipeline_config_hash: str,
    engine_version: str = "2.0.0",
    schema_version: str = "025",
) -> str:
    """
    Compute deterministic logical synthesis identity independent of execution history.
    Strictly independent of batch_run_id, worker_ids, timestamps, and SQLite insertion order.
    """
    payload = {
        "canonical_canon_id": canonical_canon_id,
        "constituent_corpus_identities": sorted(list(set(constituent_corpus_identities))),
        "engine_version": engine_version,
        "pipeline_config_hash": pipeline_config_hash,
        "schema_version": schema_version,
        "scope": "CANON",
    }
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"SYNTH-CANON-{hashlib.sha256(dumped.encode('utf-8')).hexdigest()}"


def get_canonical_corpora_for_canon(conn: sqlite3.Connection, canon_id: str) -> List[str]:
    """
    Derive the authoritative constituent corpus membership of a canon from the canonical catalog.
    Traverses canons -> testaments.
    Each testament (e.g. 'TEST-OT', 'TEST-NT' or 'HB', 'GNT') acts as a canonical corpus constituent.
    Sorted deterministically by sort_order and testament_id.
    """
    # Match against canons -> testaments
    cur = conn.execute(
        """
        SELECT t.testament_id
        FROM testaments t
        JOIN canons c ON t.canon_id = c.canon_id
        WHERE c.canon_id = ?
        ORDER BY t.sort_order, t.testament_id
        """,
        (canon_id,),
    )
    testaments = [row[0] for row in cur.fetchall()]
    if testaments:
        return testaments

    # Fallback: direct testaments where canon_id = ?
    cur = conn.execute(
        """
        SELECT testament_id
        FROM testaments
        WHERE canon_id = ?
        ORDER BY sort_order, testament_id
        """,
        (canon_id,),
    )
    testaments = [row[0] for row in cur.fetchall()]
    if testaments:
        return testaments

    # If the canon_id itself exists in canons without testaments, return empty list
    return []


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class CorpusCompletenessStatus:
    """Status summary of a single constituent corpus within a canon."""
    corpus_id: str
    synthesis_run_id: Optional[str] = None
    synthesis_status: Optional[str] = None
    validation_run_id: Optional[str] = None
    validation_outcome: Optional[str] = None
    logical_identity: Optional[str] = None
    is_authoritative: bool = False
    failure_reason: Optional[str] = None


@dataclass(frozen=True)
class CanonCompletenessReport:
    """Authoritative completeness audit report for a canon boundary."""
    canon_id: str
    is_complete: bool
    total_required: int
    completed_count: int
    corpora: Dict[str, CorpusCompletenessStatus]
    missing_corpora: List[str]
    pending_corpora: List[str]
    running_corpora: List[str]
    failed_corpora: List[str]
    blocked_corpora: List[str]
    unvalidated_corpora: List[str]
    mismatched_corpora: List[str]


@dataclass(frozen=True)
class CanonAggregationResult:
    """Result of an authoritative CANON synthesis aggregation run."""
    synthesis_run: SynthesisRunResult
    validation_run: ValidationRun
    logical_identity: str
    validation_identity: str
    is_reused: bool = False


# =============================================================================
# CANON AGGREGATOR
# =============================================================================

class CanonAggregator:
    """
    Canon-Level Synthesis Aggregator orchestrating Task 4.4 inductive synthesis:
        CORPUS -> CANON
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        synthesis_manager: Optional[HierarchicalSynthesisManager] = None,
        validation_engine: Optional[ValidationEngine] = None,
        provenance_tracker: Optional[ProvenanceTracker] = None,
        version_manager: Optional[VersionManager] = None,
        retrieval_engine: Optional[HybridSymmetricalRetrievalEngine] = None,
        engine_version: str = "2.0.0",
        schema_version: str = "025",
    ) -> None:
        self.engine = engine
        self.provenance_tracker = provenance_tracker or ProvenanceTracker(engine)
        self.version_manager = version_manager or VersionManager(engine)
        self.retrieval_engine = retrieval_engine or HybridSymmetricalRetrievalEngine(
            self.engine, self.provenance_tracker, self.version_manager
        )
        self.synthesis_manager = synthesis_manager or HierarchicalSynthesisManager(
            self.engine, self.version_manager, self.provenance_tracker
        )
        self.validation_engine = validation_engine or ValidationEngine(
            self.engine, self.provenance_tracker, self.version_manager, self.retrieval_engine
        )
        self.engine_version = engine_version
        self.schema_version = schema_version

    # -------------------------------------------------------------------------
    # 1. CANON COMPLETENESS VERIFICATION
    # -------------------------------------------------------------------------

    def verify_canon_completeness(
        self,
        canon_id: str,
        source_corpus: Optional[str] = None,
        target_corpus: Optional[str] = None,
        pipeline_config_hash: Optional[str] = None,
        raise_on_incomplete: bool = False,
    ) -> CanonCompletenessReport:
        """
        Verify that all required constituent corpora in the canonical catalog have
        authoritative, completed, and epistemically validated Task 4.3 CORPUS results.
        """
        with self.engine.connect() as conn:
            required_corpora = get_canonical_corpora_for_canon(conn, canon_id)

            if not required_corpora:
                report = CanonCompletenessReport(
                    canon_id=canon_id,
                    is_complete=False,
                    total_required=0,
                    completed_count=0,
                    corpora={},
                    missing_corpora=[],
                    pending_corpora=[],
                    running_corpora=[],
                    failed_corpora=[],
                    blocked_corpora=[],
                    unvalidated_corpora=[],
                    mismatched_corpora=[],
                )
                if raise_on_incomplete:
                    raise CanonIncompleteError(
                        f"Canon '{canon_id}' has no constituent corpora defined in the canonical catalog."
                    )
                return report

            corpora_status: Dict[str, CorpusCompletenessStatus] = {}
            missing: List[str] = []
            pending: List[str] = []
            running: List[str] = []
            failed: List[str] = []
            blocked: List[str] = []
            unvalidated: List[str] = []
            mismatched: List[str] = []

            for c_id in required_corpora:
                # Query completed CORPUS-level synthesis runs
                cur = conn.execute(
                    """
                    SELECT r.run_id, r.scope, r.target_id, r.status, r.aggregate_confidence,
                           r.version_id, r.input_content_hash, r.configuration_hash, r.output_hash,
                           r.created_at, r.metadata_json,
                           v.run_id AS validation_run_id, v.final_outcome AS validation_outcome,
                           v.validation_identity
                    FROM synthesis_runs r
                    LEFT JOIN validation_runs v ON v.target_type = 'CORPUS_SYNTHESIS' AND v.target_id = r.run_id
                    WHERE r.scope = 'CORPUS' AND r.target_id = ?
                    ORDER BY r.created_at DESC
                    """,
                    (c_id,),
                )
                rows = cur.fetchall()

                if not rows:
                    missing.append(c_id)
                    corpora_status[c_id] = CorpusCompletenessStatus(
                        corpus_id=c_id,
                        failure_reason="No synthesis run found for required corpus.",
                    )
                    continue

                # Inspect candidates
                authoritative_completed = False
                config_mismatch_candidate = None
                blocked_candidate = None
                failed_candidate = None
                running_candidate = None
                unvalidated_candidate = None

                for r in rows:
                    s_status = r["status"]
                    v_outcome = r["validation_outcome"]
                    v_id = r["validation_run_id"]
                    r_id = r["run_id"]
                    meta_raw = r["metadata_json"]
                    meta = {}
                    if meta_raw:
                        try:
                            meta = json.loads(meta_raw)
                        except Exception:
                            pass
                    logical_id = meta.get("logical_identity")

                    # Check config match
                    config_matches = True
                    if pipeline_config_hash:
                        config_matches = (
                            r["configuration_hash"] == pipeline_config_hash
                            or meta.get("pipeline_config_hash") == pipeline_config_hash
                        )

                    if s_status == "COMPLETED" and v_id and v_outcome in ("VALID", "VALID_WITH_WARNINGS"):
                        if config_matches:
                            authoritative_completed = True
                            corpora_status[c_id] = CorpusCompletenessStatus(
                                corpus_id=c_id,
                                synthesis_run_id=r_id,
                                synthesis_status=s_status,
                                validation_run_id=v_id,
                                validation_outcome=v_outcome,
                                logical_identity=logical_id,
                                is_authoritative=True,
                            )
                            break
                        else:
                            config_mismatch_candidate = (r_id, s_status, v_id, v_outcome, logical_id, r["configuration_hash"])
                    elif v_outcome == "BLOCKED":
                        blocked_candidate = (r_id, s_status, v_id, v_outcome, logical_id)
                    elif s_status in ("FAILED", "SUPERSEDED"):
                        failed_candidate = (r_id, s_status, v_id, v_outcome, logical_id)
                    elif s_status in ("INITIALIZED", "PROCESSING"):
                        running_candidate = (r_id, s_status, v_id, v_outcome, logical_id)
                    elif s_status == "COMPLETED" and (not v_id or v_outcome not in ("VALID", "VALID_WITH_WARNINGS")):
                        unvalidated_candidate = (r_id, s_status, v_id, v_outcome, logical_id)

                if not authoritative_completed:
                    if blocked_candidate:
                        r_id, s_status, v_id, v_outcome, logical_id = blocked_candidate
                        blocked.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=r_id,
                            synthesis_status=s_status,
                            validation_run_id=v_id,
                            validation_outcome=v_outcome,
                            logical_identity=logical_id,
                            failure_reason="Validation outcome is BLOCKED.",
                        )
                    elif failed_candidate:
                        r_id, s_status, v_id, v_outcome, logical_id = failed_candidate
                        failed.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=r_id,
                            synthesis_status=s_status,
                            validation_run_id=v_id,
                            validation_outcome=v_outcome,
                            logical_identity=logical_id,
                            failure_reason=f"Synthesis run status is '{s_status}'.",
                        )
                    elif running_candidate:
                        r_id, s_status, v_id, v_outcome, logical_id = running_candidate
                        running.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=r_id,
                            synthesis_status=s_status,
                            validation_run_id=v_id,
                            validation_outcome=v_outcome,
                            logical_identity=logical_id,
                            failure_reason=f"Synthesis run status is '{s_status}'.",
                        )
                    elif config_mismatch_candidate:
                        r_id, s_status, v_id, v_outcome, logical_id, cfg_h = config_mismatch_candidate
                        mismatched.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=r_id,
                            synthesis_status=s_status,
                            validation_run_id=v_id,
                            validation_outcome=v_outcome,
                            logical_identity=logical_id,
                            failure_reason=f"Pipeline config hash mismatch ({cfg_h} != {pipeline_config_hash}).",
                        )
                    elif unvalidated_candidate:
                        r_id, s_status, v_id, v_outcome, logical_id = unvalidated_candidate
                        unvalidated.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=r_id,
                            synthesis_status=s_status,
                            validation_run_id=v_id,
                            validation_outcome=v_outcome,
                            logical_identity=logical_id,
                            failure_reason=f"Validation outcome '{v_outcome}' not acceptable or missing.",
                        )
                    else:
                        missing.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            failure_reason="No eligible synthesis run found.",
                        )

            # Check cross-corpus configuration consistency if pipeline_config_hash not specified
            if not pipeline_config_hash:
                authoritative_cfgs = {}
                for c_id, st in corpora_status.items():
                    if st.is_authoritative and st.synthesis_run_id:
                        with self.engine.connect() as conn:
                            cur = conn.execute("SELECT configuration_hash, metadata_json FROM synthesis_runs WHERE run_id = ?", (st.synthesis_run_id,))
                            crow = cur.fetchone()
                            if crow:
                                cmeta = json.loads(crow["metadata_json"]) if crow["metadata_json"] else {}
                                eff_cfg = cmeta.get("pipeline_config_hash") or crow["configuration_hash"]
                                authoritative_cfgs[c_id] = eff_cfg
                if len(set(authoritative_cfgs.values())) > 1:
                    for c_id in authoritative_cfgs:
                        if c_id not in mismatched:
                            mismatched.append(c_id)
                        corpora_status[c_id] = CorpusCompletenessStatus(
                            corpus_id=c_id,
                            synthesis_run_id=corpora_status[c_id].synthesis_run_id,
                            synthesis_status=corpora_status[c_id].synthesis_status,
                            validation_run_id=corpora_status[c_id].validation_run_id,
                            validation_outcome=corpora_status[c_id].validation_outcome,
                            logical_identity=corpora_status[c_id].logical_identity,
                            failure_reason="Mixed pipeline configuration across constituent corpora.",
                        )

            completed_count = sum(1 for s in corpora_status.values() if s.is_authoritative)
            is_complete = (
                completed_count == len(required_corpora)
                and len(missing) == 0
                and len(pending) == 0
                and len(running) == 0
                and len(failed) == 0
                and len(blocked) == 0
                and len(unvalidated) == 0
                and len(mismatched) == 0
            )

            report = CanonCompletenessReport(
                canon_id=canon_id,
                is_complete=is_complete,
                total_required=len(required_corpora),
                completed_count=completed_count,
                corpora=corpora_status,
                missing_corpora=sorted(missing),
                pending_corpora=sorted(pending),
                running_corpora=sorted(running),
                failed_corpora=sorted(failed),
                blocked_corpora=sorted(blocked),
                unvalidated_corpora=sorted(unvalidated),
                mismatched_corpora=sorted(mismatched),
            )

            if raise_on_incomplete and not is_complete:
                reasons = []
                if missing:
                    reasons.append(f"missing={len(missing)} {missing}")
                if blocked:
                    reasons.append(f"blocked={len(blocked)} {blocked}")
                if failed:
                    reasons.append(f"failed={len(failed)} {failed}")
                if unvalidated:
                    reasons.append(f"unvalidated={len(unvalidated)} {unvalidated}")
                if mismatched:
                    reasons.append(f"mismatched={len(mismatched)} {mismatched}")
                raise CanonIncompleteError(
                    f"Canon '{canon_id}' is incomplete ({completed_count}/{len(required_corpora)} completed): {'; '.join(reasons)}"
                )

            return report

    # -------------------------------------------------------------------------
    # 2. CANON SYNTHESIS AGGREGATION
    # -------------------------------------------------------------------------

    def aggregate_canon(
        self,
        canon_id: str,
        claims: Optional[Sequence[SynthesisClaimInput]] = None,
        tensions: Optional[Sequence[SynthesisTensionInput]] = None,
        config: Optional[SynthesisRunConfig] = None,
        retrieval_lineage: Optional[RetrievalLineage] = None,
        run_id: Optional[str] = None,
        pipeline_config_hash: Optional[str] = None,
    ) -> CanonAggregationResult:
        """
        Aggregate validated constituent CORPUS syntheses into an authoritative CANON synthesis.
        Enforces bottom-up directionality, weakest-link confidence, anti-harmonization,
        epistemic validation, fast-path idempotency, and crash safety.
        """
        cfg = config or SynthesisRunConfig()
        pipe_cfg_hash = pipeline_config_hash or PipelineConfig().configuration_hash

        # Step 1: Enforce Canon Completeness
        completeness = self.verify_canon_completeness(
            canon_id=canon_id,
            pipeline_config_hash=pipeline_config_hash,
            raise_on_incomplete=True,
        )

        with self.engine.connect() as conn:
            corpora_in_canon = get_canonical_corpora_for_canon(conn, canon_id)

        # Step 2: Prepare Claims and Constituents
        actual_claims: List[SynthesisClaimInput] = []
        if claims is not None:
            # Validate directionality of supplied claims
            for c in claims:
                for con in c.constituents:
                    if con.constituent_scope != SynthesisScope.CORPUS:
                        raise CanonHierarchyViolationError(
                            f"Hierarchy Violation: CANON synthesis cannot consume '{con.constituent_scope.value}' "
                            f"constituent '{con.constituent_target_id}'. CANON consumes ONLY CORPUS constituents."
                        )
            actual_claims = list(claims)
        else:
            # Reconstruct claims from completed CORPUS-level synthesis runs
            with self.engine.connect() as conn:
                for c_id in corpora_in_canon:
                    c_cur = conn.execute(
                        """
                        SELECT c.claim_id, c.claim_tier, c.primary_evidence_class,
                               c.claim_text, c.epistemic_status, c.synthesized_confidence,
                               c.authorial_context
                        FROM synthesis_claims c
                        JOIN synthesis_runs r ON c.run_id = r.run_id
                        WHERE c.scope = 'CORPUS' AND c.target_id = ? AND r.status = 'COMPLETED'
                        ORDER BY c.claim_id
                        """,
                        (c_id,),
                    )
                    c_rows = c_cur.fetchall()
                    for row in c_rows:
                        actual_claims.append(
                            SynthesisClaimInput(
                                claim_id=f"CLM-CANON-{canon_id}-{c_id}-{row['claim_id']}",
                                claim_tier=ClaimTier(row["claim_tier"]),
                                primary_evidence_class=EvidenceClass(row["primary_evidence_class"]),
                                claim_text=row["claim_text"],
                                epistemic_status=SynthesisClaimStatus(row["epistemic_status"]),
                                authorial_context=row["authorial_context"],
                                constituents=[
                                    ConstituentInput(
                                        constituent_scope=SynthesisScope.CORPUS,
                                        constituent_target_id=c_id,
                                        constituent_confidence=float(row["synthesized_confidence"]),
                                        constituent_claim_id=row["claim_id"],
                                        is_critical_dependency=True,
                                    )
                                ],
                            )
                        )

            if not actual_claims:
                raise SynthesisMissingConstituentError(
                    f"No authoritative completed CORPUS-level constituents found for canon '{canon_id}'."
                )

        actual_tensions = list(tensions or ())

        # Step 3: Extract Constituent Identities & Lineage
        constituent_corpus_identities: List[str] = []
        linked_claim_ids: List[str] = []
        evidence_ids: List[str] = []

        for c_id in corpora_in_canon:
            st = completeness.corpora.get(c_id)
            if st and st.logical_identity:
                constituent_corpus_identities.append(st.logical_identity)
            else:
                constituent_corpus_identities.append(f"CORPUS-{c_id}")

        for clm in actual_claims:
            for con in clm.constituents:
                if con.constituent_claim_id:
                    linked_claim_ids.append(con.constituent_claim_id)
                if con.constituent_evidence_id:
                    evidence_ids.append(con.constituent_evidence_id)

        linked_claim_ids = sorted(list(set(linked_claim_ids)))
        evidence_ids = sorted(list(set(evidence_ids)))

        # Step 4: Compute Logical CANON Identity
        logical_identity = compute_canon_synthesis_identity(
            canonical_canon_id=canon_id,
            constituent_corpus_identities=constituent_corpus_identities,
            pipeline_config_hash=pipe_cfg_hash,
            engine_version=self.engine_version,
            schema_version=self.schema_version,
        )

        # Step 5: Fast-Path / Idempotency / Crash Recovery Check
        existing_run: Optional[SynthesisRunRecord] = None
        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT run_id, scope, target_id, status, aggregate_confidence,
                       version_id, input_content_hash, configuration_hash, output_hash,
                       created_at, metadata_json
                FROM synthesis_runs
                WHERE scope = 'CANON' AND target_id = ?
                ORDER BY created_at DESC
                """,
                (canon_id,),
            )
            rows = cur.fetchall()
            for row in rows:
                meta_raw = row["metadata_json"]
                if meta_raw:
                    try:
                        meta = json.loads(meta_raw)
                        if meta.get("logical_identity") == logical_identity:
                            existing_run = self.synthesis_manager.get_synthesis_run(row["run_id"])
                            break
                    except Exception:
                        pass

        if existing_run:
            # Synthesis already exists; inspect validation ledger
            with self.engine.connect() as conn:
                v_cur = conn.execute(
                    """
                    SELECT run_id, final_outcome, validation_identity
                    FROM validation_runs
                    WHERE target_type = 'CANON_SYNTHESIS' AND target_id = ?
                    ORDER BY executed_at DESC
                    """,
                    (existing_run.run_id,),
                )
                v_row = v_cur.fetchone()

            if v_row:
                out = ValidationOutcome(v_row["final_outcome"])
                if out == ValidationOutcome.BLOCKED:
                    # Do not override blocked validation
                    raise CanonBlockedValidationError(
                        f"Authoritative validation is BLOCKED for existing canon synthesis '{existing_run.run_id}'."
                    )
                # Valid existing result: fast-path return
                val_run = self.validation_engine.get_validation_run(v_row["run_id"])
                return CanonAggregationResult(
                    synthesis_run=SynthesisRunResult(
                        run_id=existing_run.run_id,
                        scope=existing_run.scope,
                        target_id=existing_run.target_id,
                        status=existing_run.status,
                        aggregate_confidence=existing_run.aggregate_confidence,
                        claims_created=len(actual_claims),
                        tensions_created=len(actual_tensions),
                        constituents_linked=len(constituent_corpus_identities),
                        provenance_id=existing_run.provenance_id,
                        version_id=existing_run.version_id,
                        input_content_hash=existing_run.input_content_hash,
                        configuration_hash=existing_run.configuration_hash,
                        output_hash=existing_run.output_hash,
                        created_at=existing_run.created_at,
                    ),
                    validation_run=val_run,
                    logical_identity=logical_identity,
                    validation_identity=v_row["validation_identity"],
                    is_reused=True,
                )
            else:
                # Crash Safety Case B: synthesis persisted, validation absent -> resume validation
                synth_target_id = existing_run.run_id
                synth_version_id = existing_run.version_id
                synth_input_hash = existing_run.input_content_hash
                aggregate_conf = existing_run.aggregate_confidence
                synth_result = SynthesisRunResult(
                    run_id=existing_run.run_id,
                    scope=existing_run.scope,
                    target_id=existing_run.target_id,
                    status=existing_run.status,
                    aggregate_confidence=existing_run.aggregate_confidence,
                    claims_created=len(actual_claims),
                    tensions_created=len(actual_tensions),
                    constituents_linked=len(constituent_corpus_identities),
                    provenance_id=existing_run.provenance_id,
                    version_id=existing_run.version_id,
                    input_content_hash=existing_run.input_content_hash,
                    configuration_hash=existing_run.configuration_hash,
                    output_hash=existing_run.output_hash,
                    created_at=existing_run.created_at,
                )
        else:
            # Step 6: Create New CANON Synthesis Run through HierarchicalSynthesisManager
            augmented_metadata = dict(cfg.metadata or {})
            augmented_metadata.update({
                "logical_identity": logical_identity,
                "canonical_canon_id": canon_id,
                "constituent_corpus_identities": constituent_corpus_identities,
            })
            run_cfg = SynthesisRunConfig(
                synthesizer_id=cfg.synthesizer_id,
                synthesizer_version=cfg.synthesizer_version,
                enforce_strict_scope_hierarchy=cfg.enforce_strict_scope_hierarchy,
                enforce_anti_harmonization=cfg.enforce_anti_harmonization,
                enforce_authorial_distinctives=cfg.enforce_authorial_distinctives,
                enforce_reception_firewall=cfg.enforce_reception_firewall,
                allow_direct_pericope_to_book=cfg.allow_direct_pericope_to_book,
                metadata=augmented_metadata,
            )

            synth_result = self.synthesis_manager.create_synthesis_run(
                scope=SynthesisScope.CANON,
                target_id=canon_id,
                claims=actual_claims,
                tensions=actual_tensions,
                config=run_cfg,
                run_id=run_id,
            )
            synth_target_id = synth_result.run_id
            synth_version_id = synth_result.version_id
            synth_input_hash = synth_result.input_content_hash
            aggregate_conf = synth_result.aggregate_confidence

        # Step 7: Epistemic Validation via ValidationEngine (Task 4.0)
        ret_lineage = retrieval_lineage or self._ensure_retrieval_lineage(
            canon_id=canon_id,
            constituent_corpus_identities=constituent_corpus_identities,
            input_content_hash=synth_input_hash,
            config_hash=pipe_cfg_hash,
        )

        val_input = ValidationInput(
            target=ValidationTarget(
                target_type="CANON_SYNTHESIS",
                target_id=synth_target_id,
                target_version_id=synth_version_id,
            ),
            retrieval_lineage=ret_lineage,
            evidence_dependencies=EvidenceDependencies(
                evidence_ids=evidence_ids,
                linked_claim_ids=linked_claim_ids,
            ),
            environment=ValidationEnvironment(
                engine_version=self.engine_version,
                schema_version=self.schema_version,
            ),
            candidate_payload={
                "canonical_canon_id": canon_id,
                "scope": "CANON",
                "constituent_corpus_identities": constituent_corpus_identities,
                "constituent_claim_ids": linked_claim_ids,
                "evidence_ids": evidence_ids,
                "input_content_hash": synth_input_hash,
                "configuration_hash": pipe_cfg_hash,
                "candidate_confidence": aggregate_conf,
            },
        )

        val_run = self.validation_engine.validate(val_input)

        # Step 8: Validate Outcome
        if val_run.final_outcome == ValidationOutcome.BLOCKED:
            raise CanonBlockedValidationError(
                f"Epistemic Validation BLOCKED for canon synthesis '{synth_target_id}'. "
                f"Checks failed: {val_run.checks_failed}, violations: {len(val_run.violations)}."
            )

        return CanonAggregationResult(
            synthesis_run=synth_result,
            validation_run=val_run,
            logical_identity=logical_identity,
            validation_identity=val_run.validation_identity,
            is_reused=False,
        )

    # -------------------------------------------------------------------------
    # 3. INTERNAL HELPERS
    # -------------------------------------------------------------------------

    def _ensure_retrieval_lineage(
        self,
        canon_id: str,
        constituent_corpus_identities: List[str],
        input_content_hash: str,
        config_hash: str,
    ) -> RetrievalLineage:
        """
        Produce an authoritative retrieval lineage anchored to a Task 3.9 retrieval context pack.
        """
        # 1. Check if an existing pack exists in DB
        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT p.pack_id, p.pack_hash, p.run_id, p.query_id, q.query_hash, r.config_hash
                FROM retrieval_context_packs p
                JOIN retrieval_runs r ON p.run_id = r.run_id
                JOIN retrieval_queries q ON p.query_id = q.query_id
                ORDER BY p.created_at DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if row:
                return RetrievalLineage(
                    query_id=row["query_id"],
                    query_hash=row["query_hash"],
                    retrieval_run_id=row["run_id"],
                    config_hash=row["config_hash"],
                    pack_id=row["pack_id"],
                    pack_hash=row["pack_hash"],
                )

        # 2. Execute retrieval via authoritative HybridSymmetricalRetrievalEngine
        pack = self.retrieval_engine.execute_retrieval(f"Canon {canon_id}")
        with self.engine.connect() as conn:
            q_row = conn.execute(
                "SELECT query_hash FROM retrieval_queries WHERE query_id = ?",
                (pack.query_id,),
            ).fetchone()
            r_row = conn.execute(
                "SELECT config_hash FROM retrieval_runs WHERE run_id = ?",
                (pack.run_id,),
            ).fetchone()

        return RetrievalLineage(
            query_id=pack.query_id,
            query_hash=q_row["query_hash"] if q_row else "",
            retrieval_run_id=pack.run_id,
            config_hash=r_row["config_hash"] if r_row else config_hash,
            pack_id=pack.pack_id,
            pack_hash=pack.pack_hash,
        )
