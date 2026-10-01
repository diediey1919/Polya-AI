-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 024: CROSS-CORPUS CALIBRATION & EXEGETICAL PIPELINE (Task 4.1)
-- Specification: Architecture Revision V4 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   1. SOURCE-LANGUAGE PRIORITY:
--      Comparison operates on source-grounded textual evidence and synthesized claims.
--   2. SEPARATION OF CONCERNS:
--      CrossCorpusComparison stores structural and comparative relationships.
--      NO confidence scores, weights, multipliers, penalties, or boosts are stored.
--      Confidence remains owned exclusively by evidence_ledger.
--   3. CANONICAL RELATIONSHIP ONTOLOGY:
--      Strictly 7 values: PARALLEL, ANALOGOUS, DISTINCT, CONTRADICTORY,
--      ORTHOGONAL_TENSION, INCOMMENSURABLE, UNKNOWN.
--   4. CATEGORICAL BOUNDARIES:
--      Boundary findings are preserved categorically (temporal, semantic, identity/referential).
--      No numerical scoring or adjustments.
--   5. DETERMINISTIC COMPARISON IDENTITY & CANONICAL HASHING:
--      Identity and hash depend strictly on semantic inputs, versions, and configs.
--      Timestamps and execution metadata do not participate.
--   6. IMMUTABLE APPEND-ONLY LEDGER:
--      Tables are append-only, protected by BEFORE UPDATE and BEFORE DELETE triggers.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CROSS-CORPUS CALIBRATION RUNS (Immutable Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cross_corpus_calibration_runs (
    calibration_run_id TEXT PRIMARY KEY,
    calibration_identity TEXT NOT NULL UNIQUE,
    input_content_hash TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    source_corpus TEXT NOT NULL,
    target_corpus TEXT NOT NULL,
    total_comparisons INTEGER NOT NULL CHECK(total_comparisons >= 0),
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    CONSTRAINT uq_cross_corpus_run_identity UNIQUE (calibration_identity)
);

CREATE INDEX IF NOT EXISTS idx_cross_corpus_runs_ident ON cross_corpus_calibration_runs(calibration_identity);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_runs_hash ON cross_corpus_calibration_runs(input_content_hash);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_runs_corpora ON cross_corpus_calibration_runs(source_corpus, target_corpus);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_runs_prov ON cross_corpus_calibration_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. CROSS-CORPUS COMPARISONS (Comparative Structural Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cross_corpus_comparisons (
    comparison_id TEXT PRIMARY KEY,
    calibration_run_id TEXT NOT NULL REFERENCES cross_corpus_calibration_runs(calibration_run_id) ON DELETE RESTRICT,
    canonical_comparison_hash TEXT NOT NULL UNIQUE,
    source_corpus TEXT NOT NULL,
    source_target_type TEXT NOT NULL,
    source_target_id TEXT NOT NULL,
    target_corpus TEXT NOT NULL,
    target_target_type TEXT NOT NULL,
    target_target_id TEXT NOT NULL,
    comparison_dimension TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN (
        'PARALLEL',
        'ANALOGOUS',
        'DISTINCT',
        'CONTRADICTORY',
        'ORTHOGONAL_TENSION',
        'INCOMMENSURABLE',
        'UNKNOWN'
    )),
    primary_evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    temporal_boundary TEXT NOT NULL CHECK(temporal_boundary IN (
        'ANACHRONISTIC',
        'CONTEMPORANEOUS',
        'ANTECEDENT',
        'SUBSEQUENT',
        'INDETERMINATE'
    )),
    semantic_boundary TEXT NOT NULL CHECK(semantic_boundary IN (
        'IDENTICAL_SEMANTIC_FIELD',
        'OVERLAPPING_RANGE',
        'DIVERGENT_SENSE',
        'RADICAL_DISCONTINUITY',
        'ASYMMETRIC_MAPPING',
        'INDETERMINATE'
    )),
    identity_boundary TEXT NOT NULL CHECK(identity_boundary IN (
        'ONTOLOGICAL_DISTINCTION',
        'METAPHORICAL_ALIGNMENT',
        'FUNCTIONAL_EQUIVALENCE',
        'STRICT_ONTOLOGICAL_IDENTITY',
        'CATEGORY_CONFUSION',
        'INDETERMINATE'
    )),
    epistemic_justification TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    CONSTRAINT uq_cross_corpus_comp_hash UNIQUE (canonical_comparison_hash)
);

CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_run ON cross_corpus_comparisons(calibration_run_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_source ON cross_corpus_comparisons(source_corpus, source_target_type, source_target_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_target ON cross_corpus_comparisons(target_corpus, target_target_type, target_target_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_rel ON cross_corpus_comparisons(relationship_type);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_evidence ON cross_corpus_comparisons(primary_evidence_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_comp_prov ON cross_corpus_comparisons(provenance_id);

-- ----------------------------------------------------------------------------
-- 3. CROSS-CORPUS SUPPORTING EVIDENCE (Relational Dependency Linkage)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cross_corpus_supporting_evidence (
    link_id TEXT PRIMARY KEY,
    comparison_id TEXT NOT NULL REFERENCES cross_corpus_comparisons(comparison_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    relevance_role TEXT NOT NULL CHECK(relevance_role IN (
        'PRIMARY_WARRANT',
        'CORROBORATING',
        'COUNTER_EVIDENCE',
        'CONTEXTUAL_BOUNDARY',
        'HISTORICAL_WITNESS'
    )),
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    created_at TEXT NOT NULL,
    CONSTRAINT uq_cross_corpus_supp_ev UNIQUE (comparison_id, evidence_id, relevance_role)
);

CREATE INDEX IF NOT EXISTS idx_cross_corpus_supp_comp ON cross_corpus_supporting_evidence(comparison_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_supp_ev ON cross_corpus_supporting_evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_cross_corpus_supp_role ON cross_corpus_supporting_evidence(relevance_role);

-- ----------------------------------------------------------------------------
-- 4. IMMUTABILITY ENFORCEMENT TRIGGERS (Append-Only Protection)
-- ----------------------------------------------------------------------------

-- A. Calibration Runs Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_runs_upd
BEFORE UPDATE ON cross_corpus_calibration_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_calibration_runs are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_runs_del
BEFORE DELETE ON cross_corpus_calibration_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_calibration_runs are immutable and cannot be deleted.');
END;

-- B. Comparisons Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_comp_upd
BEFORE UPDATE ON cross_corpus_comparisons
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_comparisons are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_comp_del
BEFORE DELETE ON cross_corpus_comparisons
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_comparisons are immutable and cannot be deleted.');
END;

-- C. Supporting Evidence Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_supp_upd
BEFORE UPDATE ON cross_corpus_supporting_evidence
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_supporting_evidence are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_cross_corpus_supp_del
BEFORE DELETE ON cross_corpus_supporting_evidence
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: cross_corpus_supporting_evidence are immutable and cannot be deleted.');
END;
