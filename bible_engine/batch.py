"""
Task 4.2: Pericope Batch Processing Engine for Polya Philological Bible Engine.
Specification: Architecture Revision V3 — FROZEN.

Provides:
- ProcessingUnit (Immutable logical workload specification)
- BatchRun (Operational execution ledger)
- BatchJob (Mutable operational job queue)
- BatchProcessingEngine (Deterministic orchestration, atomic claiming, crash reconciliation, fast-path)
- compute_processing_unit_hash
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import sqlite3
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import uuid

from bible_engine.database import DatabaseEngine
from bible_engine.errors import (
    BatchConcurrencyError,
    BatchJobStateError,
    BatchReconciliationError,
    BatchSubsystemError,
    BatchUnitIntegrityError,
    IllegalStateTransitionError,
    PipelineBlockedValidationError,
    VersionNotFoundError,
)
from bible_engine.pipeline import (
    ExegeticalPipeline,
    PipelineConfig,
    PipelineExecutionResult,
)
from bible_engine.provenance import ProvenanceTracker, TargetType
from bible_engine.retrieval import RetrievalTarget, RetrievalTargetType
from bible_engine.validation import ValidationOutcome
from bible_engine.versioning import VersionManager, VersionStatus


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class BatchRunStatus(str, Enum):
    """Lifecycle state of a batch run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class BatchJobStatus(str, Enum):
    """Lifecycle state of an operational pericope batch job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


# =============================================================================
# DOMAIN MODELS
# =============================================================================

@dataclass(frozen=True)
class ProcessingUnit:
    """
    Immutable logical contract representing WHAT must be processed.
    Contains strictly no mutable execution state or cached calibration pointers.
    """
    unit_id: str
    unit_hash: str
    source_corpus: str
    target_corpus: str
    pericope_id: str
    source_version_id: str
    pipeline_config_hash: str
    engine_version: str
    schema_version: str
    created_at: str
    is_immutable: int = 1

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Deterministic canonical representation for hashing."""
        return {
            "engine_version": self.engine_version,
            "pericope_id": self.pericope_id,
            "pipeline_config_hash": self.pipeline_config_hash,
            "schema_version": self.schema_version,
            "source_corpus": self.source_corpus,
            "source_version_id": self.source_version_id,
            "target_corpus": self.target_corpus,
        }


@dataclass(frozen=True)
class BatchRunRecord:
    """Operational execution ledger record for a batch run."""
    batch_run_id: str
    corpus_id: str
    pipeline_config_hash: str
    total_units: int
    status: BatchRunStatus
    created_at: str
    updated_at: str
    provenance_id: str
    completed_at: Optional[str] = None


@dataclass(frozen=True)
class BatchJobRecord:
    """Operational state of a pericope processing job in a batch run."""
    job_id: str
    batch_run_id: str
    unit_id: str
    ordinal: int
    status: BatchJobStatus
    attempt_count: int
    max_retries: int
    created_at: str
    updated_at: str
    worker_id: Optional[str] = None
    heartbeat_at: Optional[str] = None
    calibration_run_id: Optional[str] = None
    validation_run_id: Optional[str] = None
    last_error: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass(frozen=True)
class AuthoritativePipelineCompletion:
    """Verified existing Task 4.1 & Task 4.0 completion result."""
    calibration_run_id: str
    calibration_identity: str
    validation_run_id: str
    validation_outcome: ValidationOutcome
    completed_at: str


@dataclass(frozen=True)
class BatchProgress:
    """Observable batch execution progress snapshot."""
    batch_run_id: str
    status: BatchRunStatus
    total_units: int
    completed_count: int
    pending_count: int
    running_count: int
    blocked_count: int
    failed_count: int
    current_job_id: Optional[str] = None
    current_pericope_id: Optional[str] = None
    last_error: Optional[str] = None


# =============================================================================
# DETERMINISTIC HASHING FUNCTIONS
# =============================================================================

def compute_processing_unit_hash(
    source_corpus: str,
    target_corpus: str,
    pericope_id: str,
    source_version_id: str,
    pipeline_config_hash: str,
    engine_version: str = "2.0.0",
    schema_version: str = "025",
) -> str:
    """
    Deterministic SHA-256 hash of canonical ProcessingUnit inputs:
    SHA256(source_corpus:target_corpus:pericope_id:source_version_id:config_hash:engine_ver:schema_ver)
    """
    payload = {
        "engine_version": engine_version,
        "pericope_id": pericope_id,
        "pipeline_config_hash": pipeline_config_hash,
        "schema_version": schema_version,
        "source_corpus": source_corpus,
        "source_version_id": source_version_id,
        "target_corpus": target_corpus,
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest().lower()


# =============================================================================
# BATCH DOMAIN ENGINE
# =============================================================================

class BatchProcessingEngine:
    """
    Task 4.2 Pericope Batch Processing Engine.
    Orchestrates pericope-by-pericope execution through Task 4.1 ExegeticalPipeline
    safely, deterministically, resumably, and idempotently.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        pipeline: ExegeticalPipeline,
        provenance_tracker: ProvenanceTracker,
        version_manager: VersionManager,
        stale_timeout_seconds: int = 300,
        worker_id: Optional[str] = None,
    ) -> None:
        self.engine = engine
        self.pipeline = pipeline
        self.prov_tracker = provenance_tracker
        self.version_mgr = version_manager
        self.stale_timeout_seconds = stale_timeout_seconds
        self.worker_id = worker_id or f"WORKER-{uuid.uuid4().hex[:8]}"

    # -------------------------------------------------------------------------
    # 1. BATCH RUN CREATION & INITIALIZATION
    # -------------------------------------------------------------------------

    def create_batch_run(
        self,
        corpus_id: str,
        source_corpus: str,
        target_corpus: str,
        source_version_id: str,
        pericope_ids: Sequence[str],
        pipeline_config: Optional[PipelineConfig] = None,
        max_retries: int = 3,
        batch_run_id: Optional[str] = None,
    ) -> BatchRunRecord:
        """
        Create a new deterministic batch run and populate processing units and jobs.
        """
        if not pericope_ids:
            raise BatchUnitIntegrityError("Cannot create batch run with empty pericope_ids list.")

        cfg = pipeline_config or PipelineConfig()
        config_hash = cfg.configuration_hash
        run_id = batch_run_id or f"BATCH-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        # Validate source version validity
        self._validate_source_version(source_version_id)

        # Record Provenance for Batch Run
        prov_record = self.prov_tracker.record_origin(
            target_type=TargetType.BATCH_PROCESS if hasattr(TargetType, "BATCH_PROCESS") else TargetType.PASSAGE,
            target_id=run_id,
            content=f"Batch run {run_id} for corpus {corpus_id} ({len(pericope_ids)} pericopes)",
        )

        with self.engine.transaction() as conn:
            # Insert batch_runs record
            conn.execute(
                """
                INSERT INTO batch_runs (
                    batch_run_id, corpus_id, pipeline_config_hash, total_units,
                    status, created_at, updated_at, completed_at, provenance_id
                ) VALUES (?, ?, ?, ?, 'PENDING', ?, ?, NULL, ?)
                """,
                (run_id, corpus_id, config_hash, len(pericope_ids), now, now, prov_record.provenance_id),
            )

            # Insert processing_units and batch_jobs in deterministic pericope order
            for ordinal, pericope_id in enumerate(pericope_ids):
                u_hash = compute_processing_unit_hash(
                    source_corpus=source_corpus,
                    target_corpus=target_corpus,
                    pericope_id=pericope_id,
                    source_version_id=source_version_id,
                    pipeline_config_hash=config_hash,
                    engine_version=cfg.engine_version,
                    schema_version=cfg.schema_version,
                )

                # Ensure processing_unit exists or insert
                cur = conn.execute("SELECT unit_id FROM processing_units WHERE unit_hash = ?", (u_hash,))
                row = cur.fetchone()
                if row:
                    unit_id = row[0]
                else:
                    unit_id = f"UNIT-{uuid.uuid4().hex[:12]}"
                    conn.execute(
                        """
                        INSERT INTO processing_units (
                            unit_id, unit_hash, source_corpus, target_corpus,
                            pericope_id, source_version_id, pipeline_config_hash,
                            engine_version, schema_version, created_at, is_immutable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            unit_id,
                            u_hash,
                            source_corpus,
                            target_corpus,
                            pericope_id,
                            source_version_id,
                            config_hash,
                            cfg.engine_version,
                            cfg.schema_version,
                            now,
                        ),
                    )

                # Insert batch_jobs entry
                job_id = f"JOB-{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO batch_jobs (
                        job_id, batch_run_id, unit_id, ordinal, status,
                        attempt_count, max_retries, worker_id, heartbeat_at,
                        calibration_run_id, validation_run_id, last_error,
                        created_at, updated_at, completed_at
                    ) VALUES (?, ?, ?, ?, 'PENDING', 0, ?, NULL, NULL, NULL, NULL, NULL, ?, ?, NULL)
                    """,
                    (job_id, run_id, unit_id, ordinal, max_retries, now, now),
                )

        return self.get_batch_run(run_id)

    # -------------------------------------------------------------------------
    # 2. SOURCE VERSION VALIDATION
    # -------------------------------------------------------------------------

    def _validate_source_version(self, source_version_id: str) -> None:
        """
        Verify that source_version_id exists and has valid status (ACTIVE or SUPERSEDED).
        Rejects DRAFT and INVALIDATED versions.
        """
        ver = self.version_mgr.get_version(source_version_id)
        if not ver:
            # Check direct query in case table wasn't accessed through VersionManager cache
            with self.engine.connect() as conn:
                r = conn.execute(
                    "SELECT status FROM object_versions WHERE version_id = ?",
                    (source_version_id,),
                ).fetchone()
                if not r:
                    raise VersionNotFoundError(f"Source version '{source_version_id}' not found in object_versions.")
                status_str = r[0]
        else:
            status_str = ver.status.value if hasattr(ver.status, "value") else str(ver.status)

        if status_str in (VersionStatus.DRAFT.value, VersionStatus.INVALIDATED.value, "DRAFT", "INVALIDATED"):
            raise IllegalStateTransitionError(
                f"Source version '{source_version_id}' has invalid status '{status_str}'. "
                "Only ACTIVE or SUPERSEDED versions are valid for execution."
            )

    # -------------------------------------------------------------------------
    # 3. FAST-PATH COMPLETION CHECK
    # -------------------------------------------------------------------------

    def check_fast_path(
        self,
        unit: ProcessingUnit,
        comparisons_generator: Any,
        config: Optional[PipelineConfig] = None,
    ) -> Optional[AuthoritativePipelineCompletion]:
        """
        Check if an authoritative Task 4.1 + Task 4.0 execution already exists for this unit.
        Does not mutate processing_units.
        """
        from bible_engine.cross_corpus import (
            CrossCorpusComparison,
            compute_calibration_identity,
            compute_run_input_content_hash,
        )

        cfg = config or PipelineConfig()

        # Generate structural comparisons for calibration identity calculation
        comps: Sequence[CrossCorpusComparison] = (
            comparisons_generator(None)
            if callable(comparisons_generator)
            else list(comparisons_generator)
        )
        if not comps:
            return None

        # Compute exact Task 4.1 calibration identity
        run_input_hash = compute_run_input_content_hash(
            source_corpus=unit.source_corpus,
            target_corpus=unit.target_corpus,
            comparisons=comps,
            configuration_hash=unit.pipeline_config_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
        )
        expected_calib_ident = compute_calibration_identity(
            input_content_hash=run_input_hash,
            configuration_hash=unit.pipeline_config_hash,
            engine_version=cfg.engine_version,
            schema_version=cfg.schema_version,
        )

        # Query authoritative completion
        with self.engine.connect() as conn:
            cur = conn.execute(
                """
                SELECT c.calibration_run_id, c.calibration_identity, v.run_id AS validation_run_id,
                       v.final_outcome, c.created_at
                FROM cross_corpus_calibration_runs c
                JOIN validation_runs v
                  ON v.target_type = 'CROSS_CORPUS_CALIBRATION'
                 AND v.target_id = c.calibration_run_id
                WHERE c.calibration_identity = ?
                  AND c.status = 'COMPLETED'
                  AND v.final_outcome IN ('VALID', 'VALID_WITH_WARNINGS')
                """,
                (expected_calib_ident,),
            )
            row = cur.fetchone()
            if row:
                return AuthoritativePipelineCompletion(
                    calibration_run_id=row["calibration_run_id"],
                    calibration_identity=row["calibration_identity"],
                    validation_run_id=row["validation_run_id"],
                    validation_outcome=ValidationOutcome(row["final_outcome"]),
                    completed_at=row["created_at"],
                )
        return None

    # -------------------------------------------------------------------------
    # 4. CRASH & STALE RECONCILIATION
    # -------------------------------------------------------------------------

    def reconcile_stale_jobs(
        self,
        batch_run_id: str,
        comparisons_generator: Optional[Any] = None,
    ) -> int:
        """
        Reconcile RUNNING jobs whose heartbeat has expired.
        If Task 4.1 committed before crash -> reconcile to COMPLETED.
        Otherwise -> reconcile to FAILED for retry.
        """
        reconciled_count = 0
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()

        with self.engine.transaction() as conn:
            # Find stale RUNNING jobs
            cur = conn.execute(
                """
                SELECT j.job_id, j.unit_id, j.heartbeat_at, j.attempt_count,
                       u.unit_hash, u.source_corpus, u.target_corpus, u.pericope_id,
                       u.source_version_id, u.pipeline_config_hash, u.engine_version,
                       u.schema_version, u.created_at AS unit_created_at
                FROM batch_jobs j
                JOIN processing_units u ON j.unit_id = u.unit_id
                WHERE j.batch_run_id = ? AND j.status = 'RUNNING'
                """,
                (batch_run_id,),
            )
            stale_candidates = cur.fetchall()

            for row in stale_candidates:
                hb = row["heartbeat_at"]
                if hb:
                    try:
                        hb_dt = datetime.fromisoformat(hb)
                        elapsed = (now_dt - hb_dt).total_seconds()
                        if elapsed < self.stale_timeout_seconds:
                            continue  # Still actively heartbeating
                    except Exception:
                        pass  # Invalid timestamp, treat as stale

                # Stale job detected
                unit = ProcessingUnit(
                    unit_id=row["unit_id"],
                    unit_hash=row["unit_hash"],
                    source_corpus=row["source_corpus"],
                    target_corpus=row["target_corpus"],
                    pericope_id=row["pericope_id"],
                    source_version_id=row["source_version_id"],
                    pipeline_config_hash=row["pipeline_config_hash"],
                    engine_version=row["engine_version"],
                    schema_version=row["schema_version"],
                    created_at=row["unit_created_at"],
                )

                completion: Optional[AuthoritativePipelineCompletion] = None
                if comparisons_generator:
                    try:
                        completion = self.check_fast_path(unit, comparisons_generator)
                    except Exception:
                        completion = None

                if completion:
                    # Post-commit crash recovery: Mark COMPLETED
                    conn.execute(
                        """
                        UPDATE batch_jobs
                        SET status = 'COMPLETED',
                            calibration_run_id = ?,
                            validation_run_id = ?,
                            completed_at = ?,
                            updated_at = ?
                        WHERE job_id = ?
                        """,
                        (
                            completion.calibration_run_id,
                            completion.validation_run_id,
                            completion.completed_at,
                            now_str,
                            row["job_id"],
                        ),
                    )
                else:
                    # Uncommitted crash recovery: Mark FAILED
                    conn.execute(
                        """
                        UPDATE batch_jobs
                        SET status = 'FAILED',
                            attempt_count = attempt_count + 1,
                            last_error = 'POST_COMMIT_CRASH_RECONCILED: UNCOMMITTED_PIPELINE',
                            updated_at = ?
                        WHERE job_id = ?
                        """,
                        (now_str, row["job_id"]),
                    )
                reconciled_count += 1

        return reconciled_count

    # -------------------------------------------------------------------------
    # 5. ATOMIC JOB CLAIMING & EXECUTION
    # -------------------------------------------------------------------------

    def claim_next_job(self, batch_run_id: str) -> Optional[Tuple[BatchJobRecord, ProcessingUnit]]:
        """
        Atomically claim the next PENDING or retryable FAILED job in deterministic ordinal order.
        """
        now = datetime.now(timezone.utc).isoformat()

        with self.engine.transaction() as conn:
            # Select first available candidate by ordinal
            cur = conn.execute(
                """
                SELECT j.job_id
                FROM batch_jobs j
                WHERE j.batch_run_id = ?
                  AND (
                    j.status = 'PENDING'
                    OR (j.status = 'FAILED' AND j.attempt_count < j.max_retries)
                  )
                ORDER BY j.ordinal ASC
                LIMIT 1
                """,
                (batch_run_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            target_job_id = row[0]

            # Atomically transition state to RUNNING with worker claim
            upd_cur = conn.execute(
                """
                UPDATE batch_jobs
                SET status = 'RUNNING',
                    worker_id = ?,
                    heartbeat_at = ?,
                    updated_at = ?
                WHERE job_id = ?
                  AND (
                    status = 'PENDING'
                    OR (status = 'FAILED' AND attempt_count < max_retries)
                  )
                """,
                (self.worker_id, now, now, target_job_id),
            )
            if upd_cur.rowcount == 0:
                # Lost race to rival worker
                return None

            # Fetch claimed job and unit
            job_row = conn.execute(
                "SELECT * FROM batch_jobs WHERE job_id = ?",
                (target_job_id,),
            ).fetchone()
            unit_row = conn.execute(
                "SELECT * FROM processing_units WHERE unit_id = ?",
                (job_row["unit_id"],),
            ).fetchone()

            job_rec = self._row_to_job(job_row)
            unit_rec = self._row_to_unit(unit_row)
            return job_rec, unit_rec

    def update_heartbeat(self, job_id: str) -> None:
        """Update worker heartbeat timestamp for active RUNNING job."""
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            conn.execute(
                """
                UPDATE batch_jobs
                SET heartbeat_at = ?, updated_at = ?
                WHERE job_id = ? AND status = 'RUNNING' AND worker_id = ?
                """,
                (now, now, job_id, self.worker_id),
            )

    # -------------------------------------------------------------------------
    # 6. EXECUTION OF SINGLE PERICOPE
    # -------------------------------------------------------------------------

    def process_job(
        self,
        job: BatchJobRecord,
        unit: ProcessingUnit,
        comparisons_generator: Any,
        pipeline_config: Optional[PipelineConfig] = None,
        intra_synthesis_inputs: Optional[List[Dict[str, Any]]] = None,
        theological_inputs: Optional[List[Dict[str, Any]]] = None,
    ) -> BatchJobRecord:
        """
        Execute Task 4.1 pipeline for a claimed job and update operational state.
        """
        now = datetime.now(timezone.utc).isoformat()
        cfg = pipeline_config or PipelineConfig()

        # 1. Check Fast Path
        completion = self.check_fast_path(unit, comparisons_generator, config=cfg)
        if completion:
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    UPDATE batch_jobs
                    SET status = 'COMPLETED',
                        calibration_run_id = ?,
                        validation_run_id = ?,
                        completed_at = ?,
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (
                        completion.calibration_run_id,
                        completion.validation_run_id,
                        completion.completed_at,
                        now,
                        job.job_id,
                    ),
                )
            return self.get_job(job.job_id)

        # 2. Execute Task 4.1 Pipeline
        try:
            self.update_heartbeat(job.job_id)
            res = self.pipeline.execute_pipeline(
                query=f"Pericope batch processing {unit.pericope_id}",
                retrieval_target=RetrievalTarget(
                    target_type=RetrievalTargetType.PERICOPE,
                    target_id=unit.pericope_id,
                ),
                source_corpus=unit.source_corpus,
                target_corpus=unit.target_corpus,
                comparisons_generator=comparisons_generator,
                intra_synthesis_inputs=intra_synthesis_inputs,
                theological_inputs=theological_inputs,
                config=cfg,
            )

            # Map successful pipeline result
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    UPDATE batch_jobs
                    SET status = 'COMPLETED',
                        calibration_run_id = ?,
                        validation_run_id = ?,
                        completed_at = ?,
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (
                        res.calibration_run_id,
                        res.validation_run_id,
                        now,
                        now,
                        job.job_id,
                    ),
                )

        except PipelineBlockedValidationError as err:
            # Epistemic rejection -> BLOCKED (Non-retryable)
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    UPDATE batch_jobs
                    SET status = 'BLOCKED',
                        last_error = ?,
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (str(err), now, job.job_id),
                )

        except Exception as err:
            # Infrastructure/runtime failure -> FAILED (Retryable)
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    UPDATE batch_jobs
                    SET status = 'FAILED',
                        attempt_count = attempt_count + 1,
                        last_error = ?,
                        updated_at = ?
                    WHERE job_id = ?
                    """,
                    (str(err), now, job.job_id),
                )

        return self.get_job(job.job_id)

    # -------------------------------------------------------------------------
    # 7. HIGH-LEVEL BATCH EXECUTION
    # -------------------------------------------------------------------------

    def process_next(
        self,
        batch_run_id: str,
        comparisons_generator: Any,
        pipeline_config: Optional[PipelineConfig] = None,
        intra_synthesis_inputs: Optional[List[Dict[str, Any]]] = None,
        theological_inputs: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[BatchJobRecord]:
        """
        Reconcile stale jobs, claim the next available job, and execute it.
        """
        # Reconcile any crashed jobs first
        self.reconcile_stale_jobs(batch_run_id, comparisons_generator)

        # Claim next job
        claimed = self.claim_next_job(batch_run_id)
        if not claimed:
            # Check if all jobs in batch are terminal to update batch_run status
            self._recalculate_batch_run_status(batch_run_id)
            return None

        job, unit = claimed
        res_job = self.process_job(
            job=job,
            unit=unit,
            comparisons_generator=comparisons_generator,
            pipeline_config=pipeline_config,
            intra_synthesis_inputs=intra_synthesis_inputs,
            theological_inputs=theological_inputs,
        )

        self._recalculate_batch_run_status(batch_run_id)
        return res_job

    def process_batch(
        self,
        batch_run_id: str,
        comparisons_generator: Any,
        max_units: Optional[int] = None,
        pipeline_config: Optional[PipelineConfig] = None,
        intra_synthesis_inputs: Optional[List[Dict[str, Any]]] = None,
        theological_inputs: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BatchJobRecord]:
        """
        Process multiple pending units up to max_units (or all if None).
        """
        processed: List[BatchJobRecord] = []
        count = 0

        while True:
            if max_units is not None and count >= max_units:
                break
            job_record = self.process_next(
                batch_run_id=batch_run_id,
                comparisons_generator=comparisons_generator,
                pipeline_config=pipeline_config,
                intra_synthesis_inputs=intra_synthesis_inputs,
                theological_inputs=theological_inputs,
            )
            if not job_record:
                break
            processed.append(job_record)
            count += 1

        return processed

    def _recalculate_batch_run_status(self, batch_run_id: str) -> None:
        """Update batch_runs status based on aggregated child jobs."""
        now = datetime.now(timezone.utc).isoformat()
        with self.engine.transaction() as conn:
            cur = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM batch_jobs
                WHERE batch_run_id = ?
                GROUP BY status
                """,
                (batch_run_id,),
            )
            counts = {row["status"]: row["count"] for row in cur.fetchall()}
            total = sum(counts.values())
            if total == 0:
                return

            completed = counts.get(BatchJobStatus.COMPLETED.value, 0)
            blocked = counts.get(BatchJobStatus.BLOCKED.value, 0)
            failed = counts.get(BatchJobStatus.FAILED.value, 0)
            running = counts.get(BatchJobStatus.RUNNING.value, 0)
            pending = counts.get(BatchJobStatus.PENDING.value, 0)

            if completed == total:
                new_status = BatchRunStatus.COMPLETED.value
                completed_at = now
            elif running > 0 or pending > 0:
                new_status = BatchRunStatus.RUNNING.value
                completed_at = None
            elif blocked > 0 and (completed + blocked) == total:
                new_status = BatchRunStatus.BLOCKED.value
                completed_at = now
            elif failed > 0:
                new_status = BatchRunStatus.FAILED.value
                completed_at = None
            else:
                new_status = BatchRunStatus.RUNNING.value
                completed_at = None

            conn.execute(
                """
                UPDATE batch_runs
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE batch_run_id = ?
                """,
                (new_status, now, completed_at, batch_run_id),
            )

    # -------------------------------------------------------------------------
    # 8. LOOKUP & OBSERVABILITY
    # -------------------------------------------------------------------------

    def get_batch_run(self, batch_run_id: str) -> Optional[BatchRunRecord]:
        """Fetch a batch run record by batch_run_id."""
        with self.engine.connect() as conn:
            cur = conn.execute("SELECT * FROM batch_runs WHERE batch_run_id = ?", (batch_run_id,))
            row = cur.fetchone()
            return self._row_to_batch_run(row) if row else None

    def get_job(self, job_id: str) -> Optional[BatchJobRecord]:
        """Fetch a batch job record by job_id."""
        with self.engine.connect() as conn:
            cur = conn.execute("SELECT * FROM batch_jobs WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            return self._row_to_job(row) if row else None

    def get_processing_unit(self, unit_id: str) -> Optional[ProcessingUnit]:
        """Fetch a processing unit record by unit_id."""
        with self.engine.connect() as conn:
            cur = conn.execute("SELECT * FROM processing_units WHERE unit_id = ?", (unit_id,))
            row = cur.fetchone()
            return self._row_to_unit(row) if row else None

    def get_processing_unit_by_hash(self, unit_hash: str) -> Optional[ProcessingUnit]:
        """Fetch a processing unit record by unit_hash."""
        with self.engine.connect() as conn:
            cur = conn.execute("SELECT * FROM processing_units WHERE unit_hash = ?", (unit_hash,))
            row = cur.fetchone()
            return self._row_to_unit(row) if row else None

    def get_progress(self, batch_run_id: str) -> Optional[BatchProgress]:
        """Fetch progress snapshot for observability."""
        with self.engine.connect() as conn:
            run_cur = conn.execute("SELECT * FROM batch_runs WHERE batch_run_id = ?", (batch_run_id,))
            run_row = run_cur.fetchone()
            if not run_row:
                return None

            jobs_cur = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM batch_jobs
                WHERE batch_run_id = ?
                GROUP BY status
                """,
                (batch_run_id,),
            )
            counts = {row["status"]: row["count"] for row in jobs_cur.fetchall()}

            # Find active or last error job
            active_cur = conn.execute(
                """
                SELECT j.job_id, u.pericope_id, j.last_error
                FROM batch_jobs j
                JOIN processing_units u ON j.unit_id = u.unit_id
                WHERE j.batch_run_id = ?
                ORDER BY CASE j.status WHEN 'RUNNING' THEN 1 WHEN 'FAILED' THEN 2 ELSE 3 END, j.ordinal ASC
                LIMIT 1
                """,
                (batch_run_id,),
            )
            act_row = active_cur.fetchone()

            return BatchProgress(
                batch_run_id=batch_run_id,
                status=BatchRunStatus(run_row["status"]),
                total_units=run_row["total_units"],
                completed_count=counts.get(BatchJobStatus.COMPLETED.value, 0),
                pending_count=counts.get(BatchJobStatus.PENDING.value, 0),
                running_count=counts.get(BatchJobStatus.RUNNING.value, 0),
                blocked_count=counts.get(BatchJobStatus.BLOCKED.value, 0),
                failed_count=counts.get(BatchJobStatus.FAILED.value, 0),
                current_job_id=act_row["job_id"] if act_row else None,
                current_pericope_id=act_row["pericope_id"] if act_row else None,
                last_error=act_row["last_error"] if act_row else None,
            )

    # -------------------------------------------------------------------------
    # 9. HYDRATION HELPERS
    # -------------------------------------------------------------------------

    def _row_to_batch_run(self, row: sqlite3.Row) -> BatchRunRecord:
        return BatchRunRecord(
            batch_run_id=row["batch_run_id"],
            corpus_id=row["corpus_id"],
            pipeline_config_hash=row["pipeline_config_hash"],
            total_units=row["total_units"],
            status=BatchRunStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            provenance_id=row["provenance_id"],
            completed_at=row["completed_at"],
        )

    def _row_to_job(self, row: sqlite3.Row) -> BatchJobRecord:
        return BatchJobRecord(
            job_id=row["job_id"],
            batch_run_id=row["batch_run_id"],
            unit_id=row["unit_id"],
            ordinal=row["ordinal"],
            status=BatchJobStatus(row["status"]),
            attempt_count=row["attempt_count"],
            max_retries=row["max_retries"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            worker_id=row["worker_id"],
            heartbeat_at=row["heartbeat_at"],
            calibration_run_id=row["calibration_run_id"],
            validation_run_id=row["validation_run_id"],
            last_error=row["last_error"],
            completed_at=row["completed_at"],
        )

    def _row_to_unit(self, row: sqlite3.Row) -> ProcessingUnit:
        return ProcessingUnit(
            unit_id=row["unit_id"],
            unit_hash=row["unit_hash"],
            source_corpus=row["source_corpus"],
            target_corpus=row["target_corpus"],
            pericope_id=row["pericope_id"],
            source_version_id=row["source_version_id"],
            pipeline_config_hash=row["pipeline_config_hash"],
            engine_version=row["engine_version"],
            schema_version=row["schema_version"],
            created_at=row["created_at"],
            is_immutable=row["is_immutable"],
        )
