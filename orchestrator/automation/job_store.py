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
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS automation_job_leases (
    job_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    acquired_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_state ON automation_jobs(state);
CREATE INDEX IF NOT EXISTS idx_approvals_job ON automation_approvals(job_id);
CREATE INDEX IF NOT EXISTS idx_executions_job ON automation_executions(job_id);
"""


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).resolve())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0, isolation_level="EXCLUSIVE")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

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

    def transition_state(self, job_id: str, new_state: JobState, worker_id: Optional[str] = None) -> AutomationJob:
        """Transitions a job state atomically with strict state machine verification."""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
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
                    worker_id, completed_at, error_summary, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                )
            )
            return execution

    def record_completion(
        self,
        execution_id: str,
        status: ExecutionStatus,
        error_summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ExecutionRecord]:
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
            )

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
        ttl = ttl_seconds or self.default_lease_ttl
        now = time.time()
        expires = now + ttl

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            # Clean up expired leases or check current
            cursor.execute("SELECT worker_id, expires_at FROM automation_job_leases WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()

            if row:
                existing_worker = row["worker_id"]
                existing_expires = row["expires_at"]
                if existing_worker == worker_id:
                    # Renew lease
                    cursor.execute(
                        "UPDATE automation_job_leases SET acquired_at = ?, expires_at = ? WHERE job_id = ?",
                        (now, expires, job_id)
                    )
                    return True
                elif now > existing_expires:
                    # Lease expired; take over
                    cursor.execute(
                        "UPDATE automation_job_leases SET worker_id = ?, acquired_at = ?, expires_at = ? WHERE job_id = ?",
                        (worker_id, now, expires, job_id)
                    )
                    return True
                else:
                    # Active lease held by another worker
                    return False
            else:
                try:
                    cursor.execute(
                        "INSERT INTO automation_job_leases (job_id, worker_id, acquired_at, expires_at) VALUES (?, ?, ?, ?)",
                        (job_id, worker_id, now, expires)
                    )
                    return True
                except sqlite3.IntegrityError:
                    return False

    def release_lease(self, job_id: str, worker_id: str) -> bool:
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM automation_job_leases WHERE job_id = ? AND worker_id = ?",
                (job_id, worker_id)
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
