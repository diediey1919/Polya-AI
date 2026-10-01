-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 025: PERICOPE BATCH PROCESSING ENGINE (Task 4.2)
-- Specification: Architecture Revision V3 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PROCESSING UNITS (Immutable Logical Workload Contract)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS processing_units (
    unit_id TEXT PRIMARY KEY,                       -- e.g. 'UNIT-a7f3c9e120b4'
    unit_hash TEXT NOT NULL UNIQUE,                 -- SHA256(source_corpus:target_corpus:pericope_id:source_version_id:config_hash:engine_ver:schema_ver)
    source_corpus TEXT NOT NULL,                    -- e.g. 'HB'
    target_corpus TEXT NOT NULL,                    -- e.g. 'GNT'
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    source_version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    pipeline_config_hash TEXT NOT NULL,             -- SHA256 of frozen PipelineConfig payload
    engine_version TEXT NOT NULL,                   -- e.g. '2.0.0'
    schema_version TEXT NOT NULL,                   -- e.g. '025'
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_processing_units_hash ON processing_units(unit_hash);
CREATE INDEX IF NOT EXISTS idx_processing_units_pericope ON processing_units(pericope_id);

CREATE TRIGGER IF NOT EXISTS trg_immut_processing_units_upd
BEFORE UPDATE ON processing_units
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: processing_units records are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_processing_units_del
BEFORE DELETE ON processing_units
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: processing_units records are immutable and cannot be deleted.');
END;

-- ----------------------------------------------------------------------------
-- 2. BATCH RUNS (Mutable Operational Execution Ledger)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batch_runs (
    batch_run_id TEXT PRIMARY KEY,                  -- e.g. 'BATCH-2026-10-02-001'
    corpus_id TEXT NOT NULL,                        -- e.g. 'CANON-NT'
    pipeline_config_hash TEXT NOT NULL,
    total_units INTEGER NOT NULL CHECK(total_units >= 0),
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'BLOCKED', 'FAILED', 'CANCELLED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_batch_runs_status ON batch_runs(status);

-- ----------------------------------------------------------------------------
-- 3. BATCH JOBS (Mutable Operational Queue & Execution State)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS batch_jobs (
    job_id TEXT PRIMARY KEY,                        -- e.g. 'JOB-9b4f2e1a3c'
    batch_run_id TEXT NOT NULL REFERENCES batch_runs(batch_run_id) ON DELETE RESTRICT,
    unit_id TEXT NOT NULL REFERENCES processing_units(unit_id) ON DELETE RESTRICT,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),   -- Deterministic processing sequence number
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'RUNNING', 'COMPLETED', 'BLOCKED', 'FAILED')),
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
    max_retries INTEGER NOT NULL DEFAULT 3 CHECK(max_retries >= 0),
    worker_id TEXT,                                 -- Active worker instance identifier
    heartbeat_at TEXT,                              -- UTC timestamp of last worker heartbeat
    calibration_run_id TEXT REFERENCES cross_corpus_calibration_runs(calibration_run_id) ON DELETE RESTRICT,
    validation_run_id TEXT REFERENCES validation_runs(run_id) ON DELETE RESTRICT,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    CONSTRAINT uq_batch_job_run_unit UNIQUE (batch_run_id, unit_id)
);

CREATE INDEX IF NOT EXISTS idx_batch_jobs_run_ordinal ON batch_jobs(batch_run_id, ordinal);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_unit ON batch_jobs(unit_id);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_claim ON batch_jobs(batch_run_id, status, ordinal);
