-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 023: AUTOMATED 10-LAYER EPISTEMIC VALIDATION ENGINE (Task 4.0)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   1. VALIDATION GATE != TRUTH ENGINE:
--      A validation result records that an artifact passed defined validation
--      constraints. It does NOT mean the proposition is true.
--   2. INDEPENDENT ORTHOGONAL DIMENSIONS:
--      V1–V10 are independent validation layers. Not an epistemic ladder.
--      All applicable layers execute. One blocking violation does not halt
--      unrelated layers.
--   3. OUTCOME DETERMINISM:
--      VALID: 0 blocking violations, 0 warnings.
--      VALID_WITH_WARNINGS: 0 blocking violations, >= 1 warnings.
--      BLOCKED: >= 1 blocking violations. Warnings must not conceal blocking violations.
--   4. DETERMINISTIC VALIDATION IDENTITY:
--      validation_identity = SHA256(validation_input_hash:engine_version:schema_version).
--      Timestamps do not participate in validation identity.
--   5. IMMUTABLE VALIDATION LEDGER:
--      No RUNNING/FAILED rows. Atomic terminal persistence only.
--      No UPDATE. No DELETE.
--   6. HISTORICAL VALIDATION CERTIFICATE:
--      Issued only for VALID or VALID_WITH_WARNINGS. Never for BLOCKED.
--      Records validation event; contains NO epistemic confidence score.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. VALIDATION RUNS (Immutable Terminal Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS validation_runs (
    run_id TEXT PRIMARY KEY,
    validation_identity TEXT NOT NULL UNIQUE,
    validation_input_hash TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    final_outcome TEXT NOT NULL CHECK(final_outcome IN ('VALID', 'VALID_WITH_WARNINGS', 'BLOCKED')),
    checks_total INTEGER NOT NULL CHECK(checks_total >= 0),
    checks_passed INTEGER NOT NULL CHECK(checks_passed >= 0),
    checks_failed INTEGER NOT NULL CHECK(checks_failed >= 0),
    warnings_total INTEGER NOT NULL CHECK(warnings_total >= 0),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    executed_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    CONSTRAINT uq_validation_input_engine_schema UNIQUE (validation_input_hash, engine_version, schema_version)
);

CREATE INDEX IF NOT EXISTS idx_validation_runs_identity ON validation_runs(validation_identity);
CREATE INDEX IF NOT EXISTS idx_validation_runs_input_hash ON validation_runs(validation_input_hash);
CREATE INDEX IF NOT EXISTS idx_validation_runs_target ON validation_runs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_validation_runs_outcome ON validation_runs(final_outcome);
CREATE INDEX IF NOT EXISTS idx_validation_runs_prov ON validation_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. VALIDATION LAYER RESULTS (Layer-by-Layer Audited Dimensions V1–V10)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS validation_layer_results (
    result_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES validation_runs(run_id) ON DELETE RESTRICT,
    layer_code TEXT NOT NULL CHECK(layer_code IN ('V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10')),
    layer_name TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('VALID', 'VALID_WITH_WARNINGS', 'BLOCKED')),
    checks_evaluated INTEGER NOT NULL CHECK(checks_evaluated >= 0),
    violations_count INTEGER NOT NULL CHECK(violations_count >= 0),
    warnings_count INTEGER NOT NULL CHECK(warnings_count >= 0),
    summary_notes TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    CONSTRAINT uq_validation_layer_run_code UNIQUE (run_id, layer_code)
);

CREATE INDEX IF NOT EXISTS idx_validation_layer_run ON validation_layer_results(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_layer_code ON validation_layer_results(layer_code);
CREATE INDEX IF NOT EXISTS idx_validation_layer_outcome ON validation_layer_results(outcome);

-- ----------------------------------------------------------------------------
-- 3. VALIDATION VIOLATIONS (Granular Blocking and Warning Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS validation_violations (
    violation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES validation_runs(run_id) ON DELETE RESTRICT,
    layer_code TEXT NOT NULL CHECK(layer_code IN ('V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V10')),
    severity TEXT NOT NULL CHECK(severity IN ('BLOCKING', 'WARNING')),
    rule_code TEXT NOT NULL,
    message TEXT NOT NULL,
    context_json TEXT,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_validation_viol_run ON validation_violations(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_viol_layer ON validation_violations(layer_code);
CREATE INDEX IF NOT EXISTS idx_validation_viol_sev ON validation_violations(severity);
CREATE INDEX IF NOT EXISTS idx_validation_viol_rule ON validation_violations(rule_code);

-- ----------------------------------------------------------------------------
-- 4. VALIDATION CERTIFICATES (Immutable Historical Validation Record)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS validation_certificates (
    certificate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES validation_runs(run_id) ON DELETE RESTRICT,
    validation_identity TEXT NOT NULL UNIQUE REFERENCES validation_runs(validation_identity) ON DELETE RESTRICT,
    validation_input_hash TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    validation_status TEXT NOT NULL CHECK(validation_status IN ('VALID', 'VALID_WITH_WARNINGS')),
    layer_summary_json TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    validated_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_validation_cert_run ON validation_certificates(run_id);
CREATE INDEX IF NOT EXISTS idx_validation_cert_identity ON validation_certificates(validation_identity);
CREATE INDEX IF NOT EXISTS idx_validation_cert_target ON validation_certificates(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_validation_cert_status ON validation_certificates(validation_status);

-- ----------------------------------------------------------------------------
-- 5. IMMUTABILITY TRIGGERS (Append-Only Authoritative Enforcers)
-- ----------------------------------------------------------------------------

-- A. Validation Runs Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_validation_runs_upd
BEFORE UPDATE ON validation_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_runs are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_validation_runs_del
BEFORE DELETE ON validation_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_runs are immutable and cannot be deleted.');
END;

-- B. Validation Layer Results Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_validation_layer_results_upd
BEFORE UPDATE ON validation_layer_results
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_layer_results are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_validation_layer_results_del
BEFORE DELETE ON validation_layer_results
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_layer_results are immutable and cannot be deleted.');
END;

-- C. Validation Violations Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_validation_violations_upd
BEFORE UPDATE ON validation_violations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_violations are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_validation_violations_del
BEFORE DELETE ON validation_violations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_violations are immutable and cannot be deleted.');
END;

-- D. Validation Certificates Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_validation_certificates_upd
BEFORE UPDATE ON validation_certificates
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_certificates are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_validation_certificates_del
BEFORE DELETE ON validation_certificates
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: validation_certificates are immutable and cannot be deleted.');
END;
