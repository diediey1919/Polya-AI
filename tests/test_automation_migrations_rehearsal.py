import os
import sqlite3
import pytest
from pathlib import Path

from orchestrator.automation.migrations import (
    MIGRATIONS,
    SCHEMA_VERSION,
    SchemaVersionError,
    check_schema_version,
    current_version,
    inspect_schema,
    migrate,
    pending_migrations,
)
from orchestrator.automation.job_store import DatabaseManager, JobStore, LeaseLockStore, ExecutionStore
from orchestrator.automation.models import AutomationJob, ExecutionRecord
from orchestrator.automation.states import JobState, ExecutionPhase, ExecutionStatus


LEGACY_V0_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE automation_jobs (
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

CREATE TABLE automation_approvals (
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

CREATE TABLE automation_executions (
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

CREATE TABLE automation_job_leases (
    job_id TEXT PRIMARY KEY,
    worker_id TEXT NOT NULL,
    acquired_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
);

CREATE INDEX idx_jobs_state ON automation_jobs(state);
CREATE INDEX idx_approvals_job ON automation_approvals(job_id);
CREATE INDEX idx_executions_job ON automation_executions(job_id);
"""


def test_migration_rehearsal_and_data_preservation(tmp_path):
    """
    Test migrating a legacy database populated with jobs, executions,
    approvals, and leases to v2, verifying zero data loss and column presence.
    """
    db_file = str(tmp_path / "legacy_test.db")
    conn = sqlite3.connect(db_file)
    conn.executescript(LEGACY_V0_SCHEMA)

    # Seed legacy data
    conn.execute(
        "INSERT INTO automation_jobs VALUES ('job-1', 'sha123', 'phash123', 'chash123', 'READY_FOR_APPROVAL', '2026-10-01', 'user1', 'w1', 'c1', '2026-10-01')"
    )
    conn.execute(
        "INSERT INTO automation_approvals VALUES ('appr-1', 'job-1', 'phash123', 'sha123', 'human_auditor', '2026-10-01', 'APPROVED', 'good')"
    )
    conn.execute(
        "INSERT INTO automation_executions VALUES ('exec-1', 'job-1', 'PLANNING', '2026-10-01', 'COMPLETED', 'w1', '2026-10-01', NULL, '{}')"
    )
    conn.execute(
        "INSERT INTO automation_job_leases VALUES ('job-1', 'w1', 1000.0, 2000.0)"
    )
    conn.commit()
    conn.close()

    # Pre-migration check
    with pytest.raises(SchemaVersionError):
        check_schema_version(db_file)

    # Run migration
    res = migrate(db_file)
    applied = res.get("applied", [])
    assert isinstance(applied, list)
    assert 1 in applied
    assert 2 in applied

    # Verify schema version
    check_schema_version(db_file)
    conn = sqlite3.connect(db_file)
    assert current_version(conn) == SCHEMA_VERSION

    # Verify columns added
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(automation_executions)")
    exec_cols = [r[1] for r in cur.fetchall()]
    assert "fencing_token" in exec_cols

    cur.execute("PRAGMA table_info(automation_job_leases)")
    lease_cols = [r[1] for r in cur.fetchall()]
    assert "fencing_token" in lease_cols

    # Verify data preserved exactly
    cur.execute("SELECT * FROM automation_jobs WHERE job_id='job-1'")
    job_row = cur.fetchone()
    assert job_row is not None
    assert job_row[0] == "job-1"

    cur.execute("SELECT * FROM automation_approvals WHERE approval_id='appr-1'")
    appr_row = cur.fetchone()
    assert appr_row is not None
    assert appr_row[4] == "human_auditor"

    cur.execute("SELECT execution_id, fencing_token FROM automation_executions WHERE execution_id='exec-1'")
    exec_row = cur.fetchone()
    assert exec_row[0] == "exec-1"
    assert exec_row[1] is None  # legacy record has NULL fencing_token

    cur.execute("SELECT job_id, fencing_token FROM automation_job_leases WHERE job_id='job-1'")
    lease_row = cur.fetchone()
    assert lease_row[0] == "job-1"
    assert lease_row[1] == 0  # DEFAULT 0 applied

    conn.close()

    # Idempotency: run migrate() again
    res2 = migrate(db_file)
    applied2 = res2.get("applied", [])
    assert applied2 == []
    after2 = res2.get("after", {})
    assert isinstance(after2, dict)
    assert after2.get("version") == SCHEMA_VERSION


def test_migration_corrupted_db_and_rollback(tmp_path):
    """
    Test that schema check handles corrupted or invalid DB safely.
    """
    db_file = str(tmp_path / "corrupt.db")
    with open(db_file, "w") as f:
        f.write("NOT A SQLITE DATABASE")

    with pytest.raises(sqlite3.DatabaseError):
        migrate(db_file)

    with pytest.raises(sqlite3.DatabaseError):
        check_schema_version(db_file)


def test_migration_atomic_rollback_on_partial_failure(tmp_path):
    """
    Test that if an error occurs during migration execution, changes are rolled back.
    """
    db_file = str(tmp_path / "atomic_test.db")
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE dummy (id INTEGER);")
    conn.commit()
    conn.close()

    from unittest.mock import patch

    with patch("orchestrator.automation.migrations._apply_one", side_effect=RuntimeError("Disk full simulation")):
        with pytest.raises(RuntimeError, match="Disk full simulation"):
            migrate(db_file)

    # Verify schema version was NOT updated
    conn2 = sqlite3.connect(db_file)
    cur = conn2.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='automation_schema_migrations'")
    has_table = cur.fetchone() is not None
    if has_table:
        cur.execute("SELECT COUNT(*) FROM automation_schema_migrations")
        count = cur.fetchone()[0]
        assert count == 0
    conn2.close()
