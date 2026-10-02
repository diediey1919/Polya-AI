"""
Task 4.3: Corpus-Level Synthesis Aggregator for Polya Philological Bible Engine.
Specification: Architecture Revision V2 — FROZEN.

Provides:
- CorpusAggregator (Corpus completeness verification, hierarchical aggregation, fast-path idempotency, crash safety)
- compute_corpus_synthesis_identity (Deterministic logical identity independent of batch_run_id / execution history)
- get_canonical_pericopes_for_corpus (Authoritative canonical catalog pericope boundary resolution)
- get_canonical_books_for_corpus (Authoritative canonical catalog book boundary resolution)
- CorpusCompletenessReport & PericopeCompletenessStatus
- CorpusAggregationResult
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union
import uuid

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    CorpusBlockedValidationError,
    CorpusHierarchyViolationError,
    CorpusIncompleteError,
    CorpusSubsystemError,
    PipelineBlockedValidationError,
    SynthesisConfidenceInflationError,
    SynthesisHarmonizationError,
    SynthesisMissingConstituentError,
    SynthesisReverseScopeError,
    SynthesisScopeJumpError,
    SynthesisValidationError,
)
from bible_engine.evidence_claim import ClaimTier, EvidenceClass
from bible_engine.pipeline import PipelineConfig
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import (
    CounterEvidenceStatus,
    CoverageStatus,
    EvidenceRole,
    HybridSymmetricalRetrievalEngine,
    RetrievalTarget,
    RetrievalTargetType,
    SearchBranch,
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

def compute_corpus_synthesis_identity(
    canonical_corpus_id: str,
    constituent_identities: Sequence[str],
    pipeline_config_hash: str,
    engine_version: str = "2.0.0",
    schema_version: str = "025",
) -> str:
    """
    Compute deterministic logical synthesis identity independent of execution history.
    Strictly independent of batch_run_id, worker_ids, timestamps, and SQLite insertion order.
    """
    payload = {
        "canonical_corpus_id": canonical_corpus_id,
        "constituent_identities": sorted(list(set(constituent_identities))),
        "engine_version": engine_version,
        "pipeline_config_hash": pipeline_config_hash,
        "schema_version": schema_version,
        "scope": "CORPUS",
    }
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def get_canonical_pericopes_for_corpus(conn: sqlite3.Connection, corpus_id: str) -> List[str]:
    """
    Derive the authoritative pericope membership of a corpus from the canonical catalog.
    Traverses canons -> testaments -> books -> pericopes or testaments -> books -> pericopes.
    Sorted deterministically by canonical book order and verse sequence.
    """
    # 1. Match against canons table
    cur = conn.execute("SELECT 1 FROM canons WHERE canon_id = ?", (corpus_id,))
    if cur.fetchone():
        cur = conn.execute(
            """
            SELECT p.pericope_id
            FROM pericopes p
            JOIN books b ON p.book_id = b.book_id
            JOIN testaments t ON b.testament_id = t.testament_id
            WHERE t.canon_id = ?
            ORDER BY b.canonical_order, p.start_chapter, p.start_verse, p.pericope_id
            """,
            (corpus_id,),
        )
        return [row[0] for row in cur.fetchall()]

    # 2. Match against testaments table
    cur = conn.execute("SELECT 1 FROM testaments WHERE testament_id = ?", (corpus_id,))
    if cur.fetchone():
        cur = conn.execute(
            """
            SELECT p.pericope_id
            FROM pericopes p
            JOIN books b ON p.book_id = b.book_id
            WHERE b.testament_id = ?
            ORDER BY b.canonical_order, p.start_chapter, p.start_verse, p.pericope_id
            """,
            (corpus_id,),
        )
        return [row[0] for row in cur.fetchall()]

    # 3. Match against books table (if single book treated as corpus boundary)
    cur = conn.execute("SELECT 1 FROM books WHERE book_id = ?", (corpus_id,))
    if cur.fetchone():
        cur = conn.execute(
            """
            SELECT p.pericope_id
            FROM pericopes p
            WHERE p.book_id = ?
            ORDER BY p.start_chapter, p.start_verse, p.pericope_id
            """,
            (corpus_id,),
        )
        return [row[0] for row in cur.fetchall()]

    return []


def get_canonical_books_for_corpus(conn: sqlite3.Connection, corpus_id: str) -> List[str]:
    """
    Derive the authoritative book membership of a corpus from the canonical catalog.
    Sorted deterministically by canonical book order.
    """
    # 1. From canons
    cur = conn.execute("SELECT 1 FROM canons WHERE canon_id = ?", (corpus_id,))
    if cur.fetchone():
        cur = conn.execute(
            """
            SELECT b.book_id
            FROM books b
            JOIN testaments t ON b.testament_id = t.testament_id
            WHERE t.canon_id = ?
            ORDER BY b.canonical_order, b.book_id
            """,
            (corpus_id,),
        )
        return [row[0] for row in cur.fetchall()]

    # 2. From testaments
    cur = conn.execute("SELECT 1 FROM testaments WHERE testament_id = ?", (corpus_id,))
    if cur.fetchone():
        cur = conn.execute(
            """
            SELECT b.book_id
            FROM books b
            WHERE b.testament_id = ?
            ORDER BY b.canonical_order, b.book_id
            """,
            (corpus_id,),
        )
        return [row[0] for row in cur.fetchall()]

    # 3. Direct book
    cur = conn.execute("SELECT 1 FROM books WHERE book_id = ?", (corpus_id,))
    if cur.fetchone():
        return [corpus_id]

    return []


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class PericopeCompletenessStatus:
    """Audit status of a single required pericope inside a corpus."""
    pericope_id: str
    status: str  # 'COMPLETED', 'MISSING', 'PENDING', 'RUNNING', 'FAILED', 'BLOCKED', 'UNVALIDATED', 'BOUNDARY_MISMATCH'
    calibration_run_id: Optional[str] = None
    validation_run_id: Optional[str] = None
    validation_outcome: Optional[ValidationOutcome] = None
    details: Optional[str] = None


@dataclass(frozen=True)
class CorpusCompletenessReport:
    """Comprehensive completeness audit report for a canonical corpus."""
    corpus_id: str
    is_complete: bool
    total_required: int
    completed_count: int
    pericopes: Dict[str, PericopeCompletenessStatus]
    missing_pericopes: List[str]
    pending_pericopes: List[str]
    running_pericopes: List[str]
    failed_pericopes: List[str]
    blocked_pericopes: List[str]
    unvalidated_pericopes: List[str]
    mismatched_pericopes: List[str]

    def __bool__(self) -> bool:
        return self.is_complete


@dataclass(frozen=True)
class CorpusAggregationResult:
    """Authoritative result of a completed or reused corpus-level synthesis."""
    synthesis_run: SynthesisRunResult
    validation_run: ValidationRun
    logical_identity: str
    validation_identity: str
    is_reused: bool = False


# =============================================================================
# CORPUS SYNTHESIS AGGREGATOR
# =============================================================================

class CorpusAggregator:
    """
    Task 4.3: Corpus-Level Synthesis Aggregator.
    Orchestrates corpus completeness verification, bottom-up synthesis integration,
    idempotent fast-path resolution, crash recovery, and epistemic validation.
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
    # 1. CORPUS COMPLETENESS VERIFICATION
    # -------------------------------------------------------------------------

    def verify_corpus_completeness(
        self,
        corpus_id: str,
        source_corpus: Optional[str] = None,
        target_corpus: Optional[str] = None,
        source_version_id: Optional[str] = None,
        pipeline_config_hash: Optional[str] = None,
        raise_on_incomplete: bool = False,
    ) -> CorpusCompletenessReport:
        """
        Verify that all required pericopes in the canonical catalog have authoritative,
        completed, and epistemically validated Task 4.1 results matching the boundary.
        """
        with self.engine.connect() as conn:
            required_pericopes = get_canonical_pericopes_for_corpus(conn, corpus_id)

            if not required_pericopes:
                report = CorpusCompletenessReport(
                    corpus_id=corpus_id,
                    is_complete=False,
                    total_required=0,
                    completed_count=0,
                    pericopes={},
                    missing_pericopes=[],
                    pending_pericopes=[],
                    running_pericopes=[],
                    failed_pericopes=[],
                    blocked_pericopes=[],
                    unvalidated_pericopes=[],
                    mismatched_pericopes=[],
                )
                if raise_on_incomplete:
                    raise CorpusIncompleteError(
                        f"Corpus '{corpus_id}' has no pericopes defined in the canonical catalog."
                    )
                return report

            pericopes_status: Dict[str, PericopeCompletenessStatus] = {}
            missing: List[str] = []
            pending: List[str] = []
            running: List[str] = []
            failed: List[str] = []
            blocked: List[str] = []
            unvalidated: List[str] = []
            mismatched: List[str] = []

            for p_id in required_pericopes:
                # Query candidate jobs across all batch runs
                job_cur = conn.execute(
                    """
                    SELECT j.job_id, j.batch_run_id, j.status AS job_status,
                           j.calibration_run_id, j.validation_run_id,
                           c.status AS calibration_status, c.calibration_identity,
                           c.source_corpus, c.target_corpus,
                           c.configuration_hash,
                           u.source_version_id, u.pipeline_config_hash,
                           v.final_outcome AS validation_outcome
                    FROM processing_units u
                    JOIN batch_jobs j ON j.unit_id = u.unit_id
                    LEFT JOIN cross_corpus_calibration_runs c ON j.calibration_run_id = c.calibration_run_id
                    LEFT JOIN validation_runs v ON j.validation_run_id = v.run_id
                    WHERE u.pericope_id = ?
                    ORDER BY j.completed_at DESC, j.created_at DESC
                    """,
                    (p_id,),
                )
                job_rows = job_cur.fetchall()

                # Also query direct cross_corpus_comparisons if no batch job row found
                comp_rows = []
                if not job_rows:
                    comp_cur = conn.execute(
                        """
                        SELECT c.calibration_run_id, c.status AS calibration_status,
                               c.calibration_identity, c.source_corpus, c.target_corpus,
                               c.configuration_hash,
                               v.run_id AS validation_run_id, v.final_outcome AS validation_outcome
                        FROM cross_corpus_comparisons comp
                        JOIN cross_corpus_calibration_runs c ON comp.calibration_run_id = c.calibration_run_id
                        LEFT JOIN validation_runs v ON v.target_type = 'CROSS_CORPUS_CALIBRATION' AND v.target_id = c.calibration_run_id
                        WHERE comp.target_target_id = ? OR comp.source_target_id = ?
                        ORDER BY c.created_at DESC
                        """,
                        (p_id, p_id),
                    )
                    comp_rows = comp_cur.fetchall()

                # Determine pericope authoritative status
                authoritative_completed = False
                p_status = "MISSING"
                p_calib_id: Optional[str] = None
                p_val_id: Optional[str] = None
                p_outcome: Optional[ValidationOutcome] = None
                p_details: Optional[str] = None

                # Check job rows
                if job_rows:
                    # Look for any row that is COMPLETED and VALID
                    for r in job_rows:
                        cal_stat = r["calibration_status"]
                        val_out = r["validation_outcome"]
                        job_stat = r["job_status"]

                        # Check boundary filters
                        boundary_ok = True
                        if source_corpus and r["source_corpus"] != source_corpus:
                            boundary_ok = False
                        if target_corpus and r["target_corpus"] != target_corpus:
                            boundary_ok = False
                        if source_version_id and r["source_version_id"] != source_version_id:
                            boundary_ok = False
                        if pipeline_config_hash:
                            if r["configuration_hash"] != pipeline_config_hash and r["pipeline_config_hash"] != pipeline_config_hash:
                                boundary_ok = False

                        if job_stat == "COMPLETED" and cal_stat == "COMPLETED" and val_out in ("VALID", "VALID_WITH_WARNINGS"):
                            if boundary_ok:
                                authoritative_completed = True
                                p_status = "COMPLETED"
                                p_calib_id = r["calibration_run_id"]
                                p_val_id = r["validation_run_id"]
                                p_outcome = ValidationOutcome(val_out)
                                break
                            else:
                                p_status = "BOUNDARY_MISMATCH"
                                p_details = f"Constituent matches pericope {p_id} but violates required boundary."

                    if not authoritative_completed:
                        # Determine dominant failure status
                        any_blocked = any(r["job_status"] == "BLOCKED" or r["validation_outcome"] == "BLOCKED" for r in job_rows)
                        any_failed = any(r["job_status"] == "FAILED" for r in job_rows)
                        any_running = any(r["job_status"] == "RUNNING" for r in job_rows)
                        any_pending = any(r["job_status"] == "PENDING" for r in job_rows)

                        if any_blocked:
                            p_status = "BLOCKED"
                        elif any_failed:
                            p_status = "FAILED"
                        elif any_running:
                            p_status = "RUNNING"
                        elif any_pending:
                            p_status = "PENDING"
                        elif p_status != "BOUNDARY_MISMATCH":
                            p_status = "UNVALIDATED"

                elif comp_rows:
                    for r in comp_rows:
                        cal_stat = r["calibration_status"]
                        val_out = r["validation_outcome"]
                        boundary_ok = True
                        if source_corpus and r["source_corpus"] != source_corpus:
                            boundary_ok = False
                        if target_corpus and r["target_corpus"] != target_corpus:
                            boundary_ok = False
                        if pipeline_config_hash and r["configuration_hash"] != pipeline_config_hash:
                            boundary_ok = False

                        if cal_stat == "COMPLETED" and val_out in ("VALID", "VALID_WITH_WARNINGS"):
                            if boundary_ok:
                                authoritative_completed = True
                                p_status = "COMPLETED"
                                p_calib_id = r["calibration_run_id"]
                                p_val_id = r["validation_run_id"]
                                p_outcome = ValidationOutcome(val_out)
                                break
                            else:
                                p_status = "BOUNDARY_MISMATCH"

                    if not authoritative_completed:
                        if any(r["validation_outcome"] == "BLOCKED" for r in comp_rows):
                            p_status = "BLOCKED"
                        elif p_status != "BOUNDARY_MISMATCH":
                            p_status = "UNVALIDATED"
                else:
                    p_status = "MISSING"

                # Categorize
                if p_status == "COMPLETED":
                    pass
                elif p_status == "MISSING":
                    missing.append(p_id)
                elif p_status == "PENDING":
                    pending.append(p_id)
                elif p_status == "RUNNING":
                    running.append(p_id)
                elif p_status == "FAILED":
                    failed.append(p_id)
                elif p_status == "BLOCKED":
                    blocked.append(p_id)
                elif p_status == "UNVALIDATED":
                    unvalidated.append(p_id)
                elif p_status == "BOUNDARY_MISMATCH":
                    mismatched.append(p_id)

                pericopes_status[p_id] = PericopeCompletenessStatus(
                    pericope_id=p_id,
                    status=p_status,
                    calibration_run_id=p_calib_id,
                    validation_run_id=p_val_id,
                    validation_outcome=p_outcome,
                    details=p_details,
                )

            is_complete = (
                len(missing) == 0
                and len(pending) == 0
                and len(running) == 0
                and len(failed) == 0
                and len(blocked) == 0
                and len(unvalidated) == 0
                and len(mismatched) == 0
            )

            completed_count = len(required_pericopes) - (
                len(missing) + len(pending) + len(running) + len(failed) + len(blocked) + len(unvalidated) + len(mismatched)
            )

            report = CorpusCompletenessReport(
                corpus_id=corpus_id,
                is_complete=is_complete,
                total_required=len(required_pericopes),
                completed_count=completed_count,
                pericopes=pericopes_status,
                missing_pericopes=missing,
                pending_pericopes=pending,
                running_pericopes=running,
                failed_pericopes=failed,
                blocked_pericopes=blocked,
                unvalidated_pericopes=unvalidated,
                mismatched_pericopes=mismatched,
            )

            if raise_on_incomplete and not is_complete:
                issues = []
                if missing:
                    issues.append(f"missing ({len(missing)}): {missing[:5]}")
                if blocked:
                    issues.append(f"blocked ({len(blocked)}): {blocked[:5]}")
                if failed:
                    issues.append(f"failed ({len(failed)}): {failed[:5]}")
                if unvalidated:
                    issues.append(f"unvalidated ({len(unvalidated)}): {unvalidated[:5]}")
                if running:
                    issues.append(f"running ({len(running)}): {running[:5]}")
                if pending:
                    issues.append(f"pending ({len(pending)}): {pending[:5]}")
                if mismatched:
                    issues.append(f"boundary mismatched ({len(mismatched)}): {mismatched[:5]}")

                raise CorpusIncompleteError(
                    f"Corpus '{corpus_id}' is incomplete ({completed_count}/{len(required_pericopes)} pericopes completed). "
                    f"Issues: {'; '.join(issues)}."
                )

            return report

    # -------------------------------------------------------------------------
    # 2. CORPUS AGGREGATION & SYNTHESIS
    # -------------------------------------------------------------------------

    def aggregate_corpus(
        self,
        corpus_id: str,
        claims: Optional[Sequence[SynthesisClaimInput]] = None,
        tensions: Optional[Sequence[SynthesisTensionInput]] = None,
        config: Optional[SynthesisRunConfig] = None,
        pipeline_config: Optional[PipelineConfig] = None,
        source_corpus: Optional[str] = None,
        target_corpus: Optional[str] = None,
        source_version_id: Optional[str] = None,
        retrieval_lineage: Optional[RetrievalLineage] = None,
        run_id: Optional[str] = None,
        skip_completeness_check: bool = False,
    ) -> CorpusAggregationResult:
        """
        Aggregate a corpus into an authoritative CORPUS-level synthesis.
        Enforces completeness, hierarchy directionality, weakest-link confidence,
        idempotency fast-path, and epistemic validation.
        """
        cfg = config or SynthesisRunConfig()
        pipe_cfg = pipeline_config or PipelineConfig()
        pipe_cfg_hash = pipe_cfg.configuration_hash

        # Step 1: Verify Corpus Completeness
        if not skip_completeness_check:
            self.verify_corpus_completeness(
                corpus_id=corpus_id,
                source_corpus=source_corpus,
                target_corpus=target_corpus,
                source_version_id=source_version_id,
                pipeline_config_hash=pipe_cfg_hash,
                raise_on_incomplete=True,
            )

        # Step 2: Establish Authoritative Lower-Level Constituents
        with self.engine.connect() as conn:
            books_in_corpus = get_canonical_books_for_corpus(conn, corpus_id)

        actual_claims: List[SynthesisClaimInput] = []
        if claims is not None:
            if not claims:
                raise SynthesisValidationError(
                    f"Corpus synthesis for '{corpus_id}' must contain at least one claim."
                )

            # Enforce hierarchy on provided claims: Constituents MUST be BOOK-level
            for c in claims:
                for con in c.constituents:
                    if con.constituent_scope != SynthesisScope.BOOK:
                        raise SynthesisScopeJumpError(
                            f"Scope Progression Violated: Synthesis at scope 'CORPUS' (level 4) "
                            f"cannot skip directly to constituent '{con.constituent_scope.value}'. "
                            f"CORPUS must consume 'BOOK' constituents."
                        )
                    if books_in_corpus and con.constituent_target_id not in books_in_corpus:
                        raise CorpusHierarchyViolationError(
                            f"Constituent target '{con.constituent_target_id}' does not belong to corpus '{corpus_id}'."
                        )
            actual_claims = list(claims)
        else:
            # Reconstruct claims from completed BOOK-level synthesis runs
            with self.engine.connect() as conn:
                for b_id in books_in_corpus:
                    b_cur = conn.execute(
                        """
                        SELECT c.claim_id, c.claim_tier, c.primary_evidence_class,
                               c.claim_text, c.epistemic_status, c.synthesized_confidence,
                               c.authorial_context
                        FROM synthesis_claims c
                        JOIN synthesis_runs r ON c.run_id = r.run_id
                        WHERE c.scope = 'BOOK' AND c.target_id = ? AND r.status = 'COMPLETED'
                        ORDER BY c.claim_id
                        """,
                        (b_id,),
                    )
                    b_rows = b_cur.fetchall()
                    for row in b_rows:
                        actual_claims.append(
                            SynthesisClaimInput(
                                claim_id=f"CLM-CORP-{corpus_id}-{b_id}-{row['claim_id']}",
                                claim_tier=ClaimTier(row["claim_tier"]),
                                primary_evidence_class=EvidenceClass(row["primary_evidence_class"]),
                                claim_text=row["claim_text"],
                                epistemic_status=SynthesisClaimStatus(row["epistemic_status"]),
                                authorial_context=row["authorial_context"],
                                constituents=[
                                    ConstituentInput(
                                        constituent_scope=SynthesisScope.BOOK,
                                        constituent_target_id=b_id,
                                        constituent_confidence=float(row["synthesized_confidence"]),
                                        constituent_claim_id=row["claim_id"],
                                        is_critical_dependency=True,
                                    )
                                ],
                            )
                        )

            if not actual_claims:
                raise SynthesisMissingConstituentError(
                    f"No authoritative completed BOOK-level constituents found for corpus '{corpus_id}'."
                )

        actual_tensions = list(tensions or ())

        # Step 3: Extract Constituent Identities & Lineage
        constituent_identities: List[str] = []
        linked_claim_ids: List[str] = []
        evidence_ids: List[str] = []

        for c in actual_claims:
            for con in c.constituents:
                con_sig = f"{con.constituent_scope.value}:{con.constituent_target_id}:{con.constituent_claim_id or ''}"
                constituent_identities.append(con_sig)
                if con.constituent_claim_id:
                    linked_claim_ids.append(con.constituent_claim_id)
                if con.constituent_evidence_id:
                    evidence_ids.append(con.constituent_evidence_id)

        constituent_identities = sorted(list(set(constituent_identities)))
        linked_claim_ids = sorted(list(set(linked_claim_ids)))
        evidence_ids = sorted(list(set(evidence_ids)))

        # Step 4: Compute Logical Synthesis Identity
        logical_identity = compute_corpus_synthesis_identity(
            canonical_corpus_id=corpus_id,
            constituent_identities=constituent_identities,
            pipeline_config_hash=pipe_cfg_hash,
            engine_version=self.engine_version,
            schema_version=self.schema_version,
        )

        # Step 5: Fast-Path / Idempotency / Crash Recovery Check
        existing_run: Optional[SynthesisRunRecord] = None
        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT run_id, metadata_json
                FROM synthesis_runs
                WHERE scope = 'CORPUS' AND target_id = ? AND status = 'COMPLETED'
                ORDER BY created_at DESC
                """,
                (corpus_id,),
            )
            for row in cur.fetchall():
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
                    WHERE target_type = 'CORPUS_SYNTHESIS' AND target_id = ?
                    ORDER BY executed_at DESC
                    """,
                    (existing_run.run_id,),
                )
                v_row = v_cur.fetchone()

            if v_row:
                out = ValidationOutcome(v_row["final_outcome"])
                if out == ValidationOutcome.BLOCKED:
                    # Do not override blocked validation
                    raise PipelineBlockedValidationError(
                        f"Authoritative validation is BLOCKED for existing corpus synthesis '{existing_run.run_id}'."
                    )
                # Valid existing result: fast-path return
                val_run = self.validation_engine.get_validation_run(v_row["run_id"])
                return CorpusAggregationResult(
                    synthesis_run=SynthesisRunResult(
                        run_id=existing_run.run_id,
                        scope=existing_run.scope,
                        target_id=existing_run.target_id,
                        status=existing_run.status,
                        aggregate_confidence=existing_run.aggregate_confidence,
                        claims_created=len(actual_claims),
                        tensions_created=len(actual_tensions),
                        constituents_linked=len(constituent_identities),
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
                    constituents_linked=len(constituent_identities),
                    provenance_id=existing_run.provenance_id,
                    version_id=existing_run.version_id,
                    input_content_hash=existing_run.input_content_hash,
                    configuration_hash=existing_run.configuration_hash,
                    output_hash=existing_run.output_hash,
                    created_at=existing_run.created_at,
                )
        else:
            # Step 6: Create New CORPUS Synthesis Run through HierarchicalSynthesisManager
            augmented_metadata = dict(cfg.metadata or {})
            augmented_metadata.update({
                "logical_identity": logical_identity,
                "canonical_corpus_id": corpus_id,
                "constituent_identities": constituent_identities,
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
                scope=SynthesisScope.CORPUS,
                target_id=corpus_id,
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
        # Ensure authoritative retrieval lineage
        ret_lineage = retrieval_lineage or self._ensure_retrieval_lineage(
            corpus_id=corpus_id,
            constituent_identities=constituent_identities,
            input_content_hash=synth_input_hash,
            config_hash=pipe_cfg_hash,
        )

        val_input = ValidationInput(
            target=ValidationTarget(
                target_type="CORPUS_SYNTHESIS",
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
                "canonical_corpus_id": corpus_id,
                "scope": "CORPUS",
                "constituent_identities": constituent_identities,
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
            raise PipelineBlockedValidationError(
                f"Epistemic Validation BLOCKED for corpus synthesis '{synth_target_id}'. "
                f"Checks failed: {val_run.checks_failed}, violations: {len(val_run.violations)}."
            )

        return CorpusAggregationResult(
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
        corpus_id: str,
        constituent_identities: List[str],
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
        pack = self.retrieval_engine.execute_retrieval(f"Corpus {corpus_id}")
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

