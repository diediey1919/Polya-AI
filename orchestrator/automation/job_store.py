"""
Persistent Database Stores for Automation Controller.
Contains dedicated tables and transactional operations for:
- Automation Jobs (JobStore)
- Approvals (ApprovalStore)
- Execution Records (ExecutionStore)
- Worker Leases (Locking / Lease mechanism)
Uses SQLite with WAL mode, foreign keys, and atomic transactions.
DOES NOT touch the production Bible Engine database.
"""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from orchestrator.automation.models import AutomationJob, ApprovalRecord, ExecutionRecord
from orchestrator.automation.states import JobState, ApprovalDecision, ExecutionPhase, ExecutionStatus, ALLOWED_TRANSITIONS


SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS automation_jobs (
    job_id TEXT PRIMARY KEY,
    commit_sha TEXT NOT NULL,
    plan_hash TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    worker_id TEXT,
    correlation_id TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS automation_approvals (
    approval_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    plan_hash TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    decision TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS automation_executions (
    execution_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    started_at TEXT NOT NULL,
    status TEXT NOT NULL,
    worker_id TEXT NOT NULL,
    completed_at TEXT,
    error_summary TEXT,
    metadata_json TEXT,
    fencing_token INTEGER,
    target_job_state TEXT NULL,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS automation_job_leases (
    job_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    acquired_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    fencing_token INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS automation_release_nonces (
    nonce TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    operator_key_id TEXT NOT NULL,
    used_at TEXT NOT NULL,
    expires_at REAL NOT NULL,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_state ON automation_jobs(state);
CREATE INDEX IF NOT EXISTS idx_approvals_job ON automation_approvals(job_id);
CREATE INDEX IF NOT EXISTS idx_executions_job ON automation_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_release_nonces_job ON automation_release_nonces(job_id);
"""


class _ManagedConnection:
    """Context wrapper that commits/rolls back AND closes the sqlite connection.

    sqlite3.Connection.__exit__ commits the transaction but does NOT close the
    handle. Using bare connections as context managers leaked one file
    descriptor per statement, exhausting the process fd limit during larger
    test runs. This wrapper preserves the existing call-site contract
    (`with self.db._get_connection() as conn:`) while guaranteeing close().
    """

    __slots__ = ("_conn",)

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def __enter__(self) -> sqlite3.Connection:
        return self._conn

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._conn.close()
        return False


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        # Remember whether the file already existed: a brand-new database is created
        # with the current schema already in place, so its migration ledger can be
        # stamped safely. A pre-existing (legacy) database is left untouched and must
        # be migrated explicitly by an operator.
        self._preexisting = os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0
        self._init_db()
        if not self._preexisting:
            self._stamp_fresh_ledger()

    def _stamp_fresh_ledger(self) -> None:
        """Records the current schema version for a database created in this process."""
        from orchestrator.automation.migrations import SCHEMA_VERSION

        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS automation_schema_migrations (
                    version    INTEGER PRIMARY KEY,
                    name       TEXT NOT NULL,
                    applied_at TEXT NOT NULL
                )
                """
            )
            for version in range(1, SCHEMA_VERSION + 1):
                conn.execute(
                    "INSERT OR IGNORE INTO automation_schema_migrations (version, name, applied_at) "
                    "VALUES (?, ?, datetime('now'))",
                    (version, f"initial_schema_v{version}"),
                )

    def _get_connection(self) -> _ManagedConnection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level="EXCLUSIVE")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return _ManagedConnection(conn)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(SCHEMA_SQL)


class JobStore:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_job(self, job: AutomationJob) -> AutomationJob:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO automation_jobs (
                    job_id, commit_sha, plan_hash, config_hash, state,
                    created_at, created_by, worker_id, correlation_id, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.job_id,
                    job.commit_sha,
                    job.plan_hash,
                    job.config_hash,
                    job.state.value if isinstance(job.state, JobState) else job.state,
                    job.created_at,
                    job.created_by,
                    job.worker_id,
                    job.correlation_id,
                    job.updated_at or job.created_at,
                )
            )
            return job

    def get_job(self, job_id: str) -> Optional[AutomationJob]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM automation_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return AutomationJob(
                job_id=row["job_id"],
                commit_sha=row["commit_sha"],
                plan_hash=row["plan_hash"],
                config_hash=row["config_hash"],
                state=JobState(row["state"]),
                created_at=row["created_at"],
                created_by=row["created_by"],
                worker_id=row["worker_id"],
                correlation_id=row["correlation_id"],
                updated_at=row["updated_at"],
            )

    def list_jobs(self, state: Optional[JobState] = None, limit: int = 100) -> List[AutomationJob]:
        """Lists jobs deterministically ordered by creation timestamp, optionally filtered by state."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            if state is not None:
                state_val = state.value if isinstance(state, JobState) else state
                cursor.execute(
                    "SELECT * FROM automation_jobs WHERE state = ? ORDER BY created_at ASC, job_id ASC LIMIT ?",
                    (state_val, limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM automation_jobs ORDER BY created_at ASC, job_id ASC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [
                AutomationJob(
                    job_id=r["job_id"],
                    commit_sha=r["commit_sha"],
                    plan_hash=r["plan_hash"],
                    config_hash=r["config_hash"],
                    state=JobState(r["state"]),
                    created_at=r["created_at"],
                    created_by=r["created_by"],
                    worker_id=r["worker_id"],
                    correlation_id=r["correlation_id"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def transition_state(
        self,
        job_id: str,
        new_state: JobState,
        worker_id: Optional[str] = None,
        require_lease: bool = False,
        fencing_token: Optional[int] = None,
    ) -> AutomationJob:
        """Transitions a job state atomically with strict state machine verification.

        Worker-originated transitions MUST pass require_lease=True together with the
        fencing token that was issued by LeaseLockStore.acquire_lease. Lease ownership
        and token equality are validated inside the same BEGIN EXCLUSIVE transaction
        that performs the UPDATE, so a worker that lost its lease cannot mutate job
        state (including into FAILED, COMPLETED, or READY_FOR_APPROVAL).

        Administrative transitions (recovery, human approval, authorization boundary)
        keep the previous unfenced behaviour and are the caller's responsibility.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db._get_connection() as conn:
            if require_lease:
                conn.execute("BEGIN EXCLUSIVE")
            cursor = conn.cursor()

            if require_lease:
                cursor.execute(
                    "SELECT worker_id, fencing_token, expires_at FROM automation_job_leases WHERE job_id = ?",
                    (job_id,),
                )
                lease = cursor.fetchone()
                if lease is None:
                    raise FencedCommitRejected(
                        f"Transition of job {job_id} rejected: no lease held by {worker_id}."
                    )
                if lease["worker_id"] != worker_id:
                    raise FencedCommitRejected(
                        f"Transition of job {job_id} rejected: lease held by {lease['worker_id']}, not {worker_id}."
                    )
                if fencing_token is None or int(fencing_token) != int(lease["fencing_token"] or 0):
                    raise FencedCommitRejected(
                        f"Transition of job {job_id} rejected: stale fencing token "
                        f"{fencing_token} (current {int(lease['fencing_token'] or 0)})."
                    )
                if lease["expires_at"] <= time.time():
                    raise FencedCommitRejected(
                        f"Transition of job {job_id} rejected: lease expired at {lease['expires_at']}."
                    )

            cursor.execute("SELECT * FROM automation_jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Job {job_id} does not exist.")

            current_state = JobState(row["state"])
            allowed = ALLOWED_TRANSITIONS.get(current_state, set())
            if new_state not in allowed:
                raise ValueError(
                    f"Forbidden state transition: Cannot transition job {job_id} from {current_state.value} to {new_state.value}."
                )

            now_iso = datetime.now(timezone.utc).isoformat()
            cursor.execute(
                """
                UPDATE automation_jobs
                SET state = ?, updated_at = ?, worker_id = COALESCE(?, worker_id)
                WHERE job_id = ?
                """,
                (new_state.value, now_iso, worker_id, job_id)
            )
            
            cursor.execute("SELECT * FROM automation_jobs WHERE job_id = ?", (job_id,))
            updated_row = cursor.fetchone()
            return AutomationJob(
                job_id=updated_row["job_id"],
                commit_sha=updated_row["commit_sha"],
                plan_hash=updated_row["plan_hash"],
                config_hash=updated_row["config_hash"],
                state=JobState(updated_row["state"]),
                created_at=updated_row["created_at"],
                created_by=updated_row["created_by"],
                worker_id=updated_row["worker_id"],
                correlation_id=updated_row["correlation_id"],
                updated_at=updated_row["updated_at"],
            )

    def update_plan_hash(self, job_id: str, new_plan_hash: str) -> AutomationJob:
        with self.db._get_connection() as conn:
            now_iso = datetime.now(timezone.utc).isoformat()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE automation_jobs SET plan_hash = ?, updated_at = ? WHERE job_id = ?",
                (new_plan_hash, now_iso, job_id)
            )
            return self.get_job(job_id)


class ApprovalStore:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def record_approval(self, approval: ApprovalRecord) -> ApprovalRecord:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO automation_approvals (
                    approval_id, job_id, plan_hash, commit_sha,
                    approved_by, approved_at, decision, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval.approval_id,
                    approval.job_id,
                    approval.plan_hash,
                    approval.commit_sha,
                    approval.approved_by,
                    approval.approved_at,
                    approval.decision.value if isinstance(approval.decision, ApprovalDecision) else approval.decision,
                    approval.notes,
                )
            )
            return approval

    def get_approval_for_job(self, job_id: str) -> Optional[ApprovalRecord]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            # Order by approved_at DESC to get the latest record if any
            cursor.execute(
                "SELECT * FROM automation_approvals WHERE job_id = ? ORDER BY approved_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return ApprovalRecord(
                approval_id=row["approval_id"],
                job_id=row["job_id"],
                plan_hash=row["plan_hash"],
                commit_sha=row["commit_sha"],
                approved_by=row["approved_by"],
                approved_at=row["approved_at"],
                decision=ApprovalDecision(row["decision"]),
                notes=row["notes"],
            )


class FencedCommitRejected(Exception):
    pass

class LegacyRecordMissingTargetState(FencedCommitRejected):
    pass
    """Raised when a fenced write is attempted with a stale or missing fencing token.

    Signals that the caller lost lease authority (crash, takeover, or expiry) between
    starting work and committing the result. The write is rolled back atomically.
    """


class ExecutionStore:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def record_start(self, execution: ExecutionRecord) -> ExecutionRecord:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO automation_executions (
                    execution_id, job_id, phase, started_at, status,
                    worker_id, completed_at, error_summary, metadata_json, fencing_token
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    execution.execution_id,
                    execution.job_id,
                    execution.phase.value if isinstance(execution.phase, ExecutionPhase) else execution.phase,
                    execution.started_at,
                    execution.status.value if isinstance(execution.status, ExecutionStatus) else execution.status,
                    execution.worker_id,
                    execution.completed_at,
                    execution.error_summary,
                    json.dumps(execution.metadata or {}),
                    execution.fencing_token,
                )
            )
            return execution

    def complete_execution_and_transition_fenced(
        self,
        execution_id: str,
        job_id: str,
        worker_id: str,
        fencing_token: int,
        status: ExecutionStatus,
        error_summary: Optional[str] = None,
        metadata_json: Optional[str] = None,
        target_job_state: Optional[JobState] = None,
    ) -> ExecutionRecord:
        """Atomic 6-tuple idempotent execution completion and state transition (SEC-P1-18)."""
        now_iso = datetime.now(timezone.utc).isoformat()
        canon_req_meta = "{}"
        if metadata_json:
            try:
                parsed_meta = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
                canon_req_meta = json.dumps(parsed_meta, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
            except Exception:
                canon_req_meta = metadata_json

        with self.db._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT execution_id, job_id, status, error_summary, metadata_json, target_job_state, worker_id, fencing_token FROM automation_executions WHERE execution_id = ?",
                (execution_id,)
            )
            exec_row = cursor.fetchone()
            if not exec_row:
                raise ValueError(f"Execution {execution_id} not found")
            if exec_row["job_id"] != job_id:
                raise FencedCommitRejected(f"Job ID mismatch for execution {execution_id}: expected {exec_row['job_id']}, got {job_id}")

            # Branch A: Already terminal execution record
            if exec_row["status"] in (ExecutionStatus.SUCCESS.value, ExecutionStatus.FAILED.value, ExecutionStatus.ABORTED.value):
                if exec_row["target_job_state"] is None:
                    raise LegacyRecordMissingTargetState("Legacy execution record missing target_job_state (Fail-Closed)")
                
                stored_canon_meta = "{}"
                if exec_row["metadata_json"]:
                    try:
                        stored_parsed = json.loads(exec_row["metadata_json"])
                        stored_canon_meta = json.dumps(stored_parsed, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
                    except Exception:
                        stored_canon_meta = exec_row["metadata_json"]

                stored_err = exec_row["error_summary"] or ""
                req_err = error_summary or ""

                if (
                    exec_row["worker_id"] == worker_id and
                    int(exec_row["fencing_token"] or 0) == int(fencing_token or 0) and
                    exec_row["status"] == (status.value if isinstance(status, ExecutionStatus) else status) and
                    stored_err == req_err and
                    stored_canon_meta == canon_req_meta and
                    exec_row["target_job_state"] == (target_job_state.value if isinstance(target_job_state, JobState) else target_job_state)
                ):
                    # Identical replay: zero DB mutation
                    cursor.execute("SELECT * FROM automation_executions WHERE execution_id = ?", (execution_id,))
                    row = cursor.fetchone()
                    return ExecutionRecord(
                        execution_id=row["execution_id"],
                        job_id=row["job_id"],
                        phase=ExecutionPhase(row["phase"]),
                        started_at=row["started_at"],
                        status=ExecutionStatus(row["status"]),
                        worker_id=row["worker_id"],
                        completed_at=row["completed_at"],
                        error_summary=row["error_summary"],
                        metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
                    )
                else:
                    raise FencedCommitRejected("Replay mismatch against existing terminal execution record")

            # Branch B: First-time completion
            cursor.execute(
                "SELECT worker_id, fencing_token, expires_at FROM automation_job_leases WHERE job_id = ?",
                (job_id,)
            )
            lease = cursor.fetchone()
            now_ts = time.time()
            if not lease or lease["worker_id"] != worker_id or int(lease["fencing_token"] or 0) != int(fencing_token or 0) or float(lease["expires_at"] or 0) <= now_ts:
                raise FencedCommitRejected(f"Active lease required for completion of job {job_id}")

            status_val = status.value if isinstance(status, ExecutionStatus) else status
            target_state_val = target_job_state.value if isinstance(target_job_state, JobState) else target_job_state

            cursor.execute(
                """
                UPDATE automation_executions
                SET status = ?, completed_at = ?, error_summary = ?, metadata_json = ?, target_job_state = ?
                WHERE execution_id = ?
                """,
                (status_val, now_iso, error_summary, canon_req_meta, target_state_val, execution_id)
            )
            if cursor.rowcount == 0:
                raise FencedCommitRejected(f"Failed to update execution {execution_id}")

            if target_state_val:
                cursor.execute(
                    "UPDATE automation_jobs SET state = ? WHERE job_id = ?",
                    (target_state_val, job_id)
                )

            cursor.execute("SELECT * FROM automation_executions WHERE execution_id = ?", (execution_id,))
            row = cursor.fetchone()
            return ExecutionRecord(
                execution_id=row["execution_id"],
                job_id=row["job_id"],
                phase=ExecutionPhase(row["phase"]),
                started_at=row["started_at"],
                status=ExecutionStatus(row["status"]),
                worker_id=row["worker_id"],
                completed_at=row["completed_at"],
                error_summary=row["error_summary"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            )

    def complete_execution_fenced(
        self,
        execution_id: str,
        job_id: str,
        worker_id: str,
        fencing_token: int,
        status: ExecutionStatus,
        error_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[ExecutionRecord]:
        """Commits an execution result ONLY if `fencing_token` is still the current lease token.

        Token validation and the UPDATE happen inside a single BEGIN EXCLUSIVE
        transaction. If another worker has taken the lease, the stored token will have
        advanced and this write is rejected with FencedCommitRejected -- no partial
        write is possible because the same transaction rolls back.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db._get_connection() as conn:
            conn.execute("BEGIN EXCLUSIVE")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT worker_id, fencing_token, expires_at FROM automation_job_leases WHERE job_id = ?",
                (job_id,),
            )
            lease = cursor.fetchone()
            if lease is None:
                raise FencedCommitRejected(
                    f"No lease exists for job {job_id}; fenced write from worker {worker_id} rejected."
                )
            current_token = int(lease["fencing_token"] or 0)
            if lease["worker_id"] != worker_id:
                raise FencedCommitRejected(
                    f"Job {job_id} lease is held by {lease['worker_id']}, not {worker_id}; write rejected."
                )
            if fencing_token is None:
                raise FencedCommitRejected(
                    f"Fenced write for job {job_id} from worker {worker_id} rejected: no fencing token supplied."
                )
            if int(fencing_token) != current_token:
                raise FencedCommitRejected(
                    f"Stale fencing token {fencing_token} for job {job_id}; current token is {current_token}."
                )

            cursor.execute(
                """
                UPDATE automation_executions
                SET status = ?, completed_at = ?, error_summary = ?,
                    metadata_json = CASE WHEN ? IS NOT NULL THEN ? ELSE metadata_json END
                WHERE execution_id = ? AND job_id = ? AND worker_id = ?
                """,
                (
                    status.value if isinstance(status, ExecutionStatus) else status,
                    now_iso,
                    error_summary,
                    json.dumps(metadata) if metadata is not None else None,
                    json.dumps(metadata) if metadata is not None else None,
                    execution_id,
                    job_id,
                    worker_id,
                ),
            )
            if cursor.rowcount == 0:
                raise FencedCommitRejected(
                    f"Execution {execution_id} does not exist for job {job_id} / worker {worker_id}."
                )
            cursor.execute("SELECT * FROM automation_executions WHERE execution_id = ?", (execution_id,))
            row = cursor.fetchone()
            return ExecutionRecord(
                execution_id=row["execution_id"],
                job_id=row["job_id"],
                phase=ExecutionPhase(row["phase"]),
                started_at=row["started_at"],
                status=ExecutionStatus(row["status"]),
                worker_id=row["worker_id"],
                completed_at=row["completed_at"],
                error_summary=row["error_summary"],
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            )

    def record_completion(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        authorized_by: Optional[str] = None,
    ) -> Optional[ExecutionRecord]:
        """UNFENCED completion path. Retained only for compatibility/audit tooling.

        This method performs NO fencing-token validation and therefore cannot be used
        by an autonomous worker to persist results. Callers must pass
        authorized_by=<operator identity>; agent/scheduler/worker identities are
        refused outright. Worker code must use complete_execution_fenced instead.
        """
        if not authorized_by:
            raise FencedCommitRejected(
                f"Unfenced completion of {execution_id} refused: no authorized_by identity supplied. "
                "Use complete_execution_fenced for worker writes."
            )
        _identity = authorized_by.lower()
        if (
            _identity.startswith("agent")
            or _identity.startswith("cron")
            or _identity.startswith("scheduler")
            or _identity.startswith("worker")
            or _identity.startswith("sup")
        ):
            raise PermissionError(
                f"Security Violation: identity '{authorized_by}' may not use the unfenced "
                "completion API. Use complete_execution_fenced with a fencing token."
            )

        with self.db._get_connection() as conn:
            now_iso = datetime.now(timezone.utc).isoformat()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE automation_executions
                SET status = ?, completed_at = ?, error_summary = ?,
                    metadata_json = CASE WHEN ? IS NOT NULL THEN ? ELSE metadata_json END
                WHERE execution_id = ?
                """,
                (
                    status.value if isinstance(status, ExecutionStatus) else status,
                    now_iso,
                    error_summary,
                    json.dumps(metadata) if metadata is not None else None,
                    json.dumps(metadata) if metadata is not None else None,
                    execution_id,
                )
            )
            return self.get_execution(execution_id)

    def get_execution(self, execution_id: str) -> Optional[ExecutionRecord]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM automation_executions WHERE execution_id = ?", (execution_id,))
            row = cursor.fetchone()
            if not row:
                return None
            metadata = {}
            if row["metadata_json"]:
                try:
                    metadata = json.loads(row["metadata_json"])
                except Exception:
                    pass
            return ExecutionRecord(
                execution_id=row["execution_id"],
                job_id=row["job_id"],
                phase=ExecutionPhase(row["phase"]),
                started_at=row["started_at"],
                status=ExecutionStatus(row["status"]),
                worker_id=row["worker_id"],
                completed_at=row["completed_at"],
                error_summary=row["error_summary"],
                metadata=metadata,
                fencing_token=(row["fencing_token"] if "fencing_token" in row.keys() else None),
            )

    def list_executions_for_job(self, job_id: str, phase: Optional[ExecutionPhase] = None) -> List[ExecutionRecord]:
        """Lists all persisted execution attempts for a job in deterministic order.

        Used for persistent (cross-process) retry accounting and audit trails.
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            if phase is not None:
                phase_val = phase.value if isinstance(phase, ExecutionPhase) else phase
                cursor.execute(
                    "SELECT * FROM automation_executions WHERE job_id = ? AND phase = ? "
                    "ORDER BY started_at ASC, execution_id ASC",
                    (job_id, phase_val),
                )
            else:
                cursor.execute(
                    "SELECT * FROM automation_executions WHERE job_id = ? "
                    "ORDER BY started_at ASC, execution_id ASC",
                    (job_id,),
                )
            rows = cursor.fetchall()
            return [
                ExecutionRecord(
                    execution_id=r["execution_id"],
                    job_id=r["job_id"],
                    phase=ExecutionPhase(r["phase"]),
                    started_at=r["started_at"],
                    status=ExecutionStatus(r["status"]),
                    worker_id=r["worker_id"],
                    completed_at=r["completed_at"],
                    error_summary=r["error_summary"],
                    metadata=json.loads(r["metadata_json"]) if r["metadata_json"] else {},
                )
                for r in rows
            ]

    def get_successful_production_executions(self, job_id: str) -> List[ExecutionRecord]:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM automation_executions
                WHERE job_id = ? AND phase = ? AND status = ?
                """,
                (job_id, ExecutionPhase.PRODUCTION_EXECUTION.value, ExecutionStatus.SUCCESS.value)
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                metadata = {}
                if r["metadata_json"]:
                    try:
                        metadata = json.loads(r["metadata_json"])
                    except Exception:
                        pass
                results.append(
                    ExecutionRecord(
                        execution_id=r["execution_id"],
                        job_id=r["job_id"],
                        phase=ExecutionPhase(r["phase"]),
                        started_at=r["started_at"],
                        status=ExecutionStatus(r["status"]),
                        worker_id=r["worker_id"],
                        completed_at=r["completed_at"],
                        error_summary=r["error_summary"],
                        metadata=metadata,
                    )
                )
            return results


class LeaseLockStore:
    """Persistent lease locking in SQLite preventing concurrent workers from running the same job."""
    def __init__(self, db_manager: DatabaseManager, default_lease_ttl: float = 60.0):
        self.db = db_manager
        self.default_lease_ttl = default_lease_ttl

    def acquire_lease(self, job_id: str, worker_id: str, ttl_seconds: Optional[float] = None) -> bool:
        """Acquires or renews a lease, minting a monotonically increasing fencing token.

        Token semantics (authority epochs, not heartbeats):
        - First grant                                  -> token 1
        - Takeover of an expired lease by a new worker -> token N+1 (strictly higher)
        - Renewal by the SAME owner (heartbeat)       -> token UNCHANGED

        A renewal must not change the token: in-flight work holds the token it was
        issued, and a heartbeat would otherwise invalidate the holder's own pending
        commit and lease cleanup. Only a change of ownership advances the epoch, which
        is exactly the event that must fence the previous owner out.
        """
        ttl = ttl_seconds or self.default_lease_ttl
        now = time.time()
        expires = now + ttl

        with self.db._get_connection() as conn:
            conn.execute("BEGIN EXCLUSIVE")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT worker_id, expires_at, fencing_token FROM automation_job_leases WHERE job_id = ?",
                (job_id,),
            )
            row = cursor.fetchone()

            if row:
                existing_worker = row["worker_id"]
                existing_expires = row["expires_at"]
                next_token = int(row["fencing_token"] or 0) + 1
                if existing_worker == worker_id:
                    # Renew lease. Ownership is unchanged, so the fencing token stays
                    # the same: this is a heartbeat, not a new authority epoch.
                    cursor.execute(
                        "UPDATE automation_job_leases SET acquired_at = ?, expires_at = ? "
                        "WHERE job_id = ?",
                        (now, expires, job_id),
                    )
                    return True
                elif now > existing_expires:
                    # Lease expired; take over with a strictly higher token.
                    cursor.execute(
                        "UPDATE automation_job_leases SET worker_id = ?, acquired_at = ?, expires_at = ?, "
                        "fencing_token = ? WHERE job_id = ?",
                        (worker_id, now, expires, next_token, job_id),
                    )
                    return True
                else:
                    # Active lease held by another worker
                    return False
            else:
                try:
                    cursor.execute(
                        "INSERT INTO automation_job_leases "
                        "(job_id, worker_id, acquired_at, expires_at, fencing_token) VALUES (?, ?, ?, ?, 1)",
                        (job_id, worker_id, now, expires),
                    )
                    return True
                except sqlite3.IntegrityError:
                    return False

    def get_fencing_token(self, job_id: str) -> Optional[int]:
        """Returns the current fencing token for a job, or None when no lease exists."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fencing_token FROM automation_job_leases WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return int(row["fencing_token"] or 0)

    def release_lease(
        self,
        job_id: str,
        worker_id: str,
        fencing_token: Optional[int] = None,
    ) -> bool:
        """Releases a lease, optionally requiring the fencing token to still match.

        Passing fencing_token makes the delete conditional on token equality so a
        worker whose lease was already taken over cannot delete the new owner's lease.
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            if fencing_token is None:
                cursor.execute(
                    "DELETE FROM automation_job_leases WHERE job_id = ? AND worker_id = ?",
                    (job_id, worker_id),
                )
            else:
                cursor.execute(
                    "DELETE FROM automation_job_leases "
                    "WHERE job_id = ? AND worker_id = ? AND fencing_token = ?",
                    (job_id, worker_id, int(fencing_token)),
                )
            return cursor.rowcount > 0

    def is_locked_by_other(self, job_id: str, worker_id: str) -> bool:
        now = time.time()
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT worker_id, expires_at FROM automation_job_leases WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return False
            if row["worker_id"] != worker_id and row["expires_at"] > now:
                return True
            return False
