-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 014: TEXTUAL CRITICISM FOUNDATION (Task 3.1)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   1. Evidence class is not a universal truth ranking.
--   2. E11/E12 must never overwrite primary textual evidence (E1), but provide
--      evidence of reception/interpretation history.
--   3. Methodological criteria (lectio difficilior, lectio brevior, witness count,
--      witness age, textual family) are analytical considerations, NOT automatic
--      truth-selection formulas.
--   4. PREFERRED reading is never automatically CERTAIN_ORIGINAL.
--   5. All competing readings are preserved without suppression or deletion.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TEXTUAL CRITICISM RUNS (Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS textual_criticism_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    edition_id TEXT REFERENCES critical_editions(edition_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    token_start_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    token_end_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    model_name TEXT,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_tc_runs_passage ON textual_criticism_runs(passage_id);
CREATE INDEX IF NOT EXISTS idx_tc_runs_pericope ON textual_criticism_runs(pericope_id);
CREATE INDEX IF NOT EXISTS idx_tc_runs_version ON textual_criticism_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_tc_runs_provenance ON textual_criticism_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. WITNESS METADATA (Version 2 Metadata & Verification Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS witness_metadata_v2 (
    witness_id TEXT PRIMARY KEY REFERENCES witnesses(witness_id) ON DELETE RESTRICT,
    external_identifier TEXT,
    identifier_system TEXT NOT NULL DEFAULT 'UNVERIFIED',
    identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    textual_family TEXT CHECK(textual_family IS NULL OR textual_family IN (
        'ALEXANDRIAN', 'WESTERN', 'CAESAREAN', 'BYZANTINE',
        'PROTO_MASORETIC', 'PRE_SAMARITAN', 'MIXED', 'INDEPENDENT'
    )),
    geographic_origin TEXT,
    is_translation INTEGER NOT NULL DEFAULT 0 CHECK(is_translation IN (0, 1)),
    is_modern_translation INTEGER NOT NULL DEFAULT 0 CHECK(is_modern_translation IN (0, 1)),
    is_ai_synthetic INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_synthetic IN (0, 1)),
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- Epistemic Firewall: AI synthetic outputs cannot be registered as ancient witnesses
    CHECK(is_ai_synthetic = 0),
    -- Epistemic Firewall: Modern translations cannot be registered as ancient witness attestations
    CHECK(is_modern_translation = 0)
);

CREATE INDEX IF NOT EXISTS idx_witness_meta_family ON witness_metadata_v2(textual_family);
CREATE INDEX IF NOT EXISTS idx_witness_meta_status ON witness_metadata_v2(identifier_status);

-- ----------------------------------------------------------------------------
-- 3. VARIANT UNIT EXECUTIONS (Execution Links to 001 Variant Units)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS variant_unit_executions (
    execution_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES textual_criticism_runs(run_id) ON DELETE RESTRICT,
    variant_unit_id TEXT NOT NULL REFERENCES variant_units(variant_unit_id) ON DELETE RESTRICT,
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    token_start_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    token_end_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_vue_run ON variant_unit_executions(run_id);
CREATE INDEX IF NOT EXISTS idx_vue_unit ON variant_unit_executions(variant_unit_id);
CREATE INDEX IF NOT EXISTS idx_vue_evidence ON variant_unit_executions(evidence_id);

-- ----------------------------------------------------------------------------
-- 4. TEXTUAL DECISIONS (Apparatus Assessments & State)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS textual_decisions (
    decision_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES textual_criticism_runs(run_id) ON DELETE RESTRICT,
    variant_unit_id TEXT NOT NULL REFERENCES variant_units(variant_unit_id) ON DELETE RESTRICT,
    preferred_reading_id TEXT REFERENCES variant_readings(reading_id) ON DELETE RESTRICT,
    decision_state TEXT NOT NULL CHECK(decision_state IN ('UNDECIDED', 'PREFERRED', 'POSSIBLE', 'UNCERTAIN', 'DISPUTED', 'REJECTED')),
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    is_certain_original INTEGER NOT NULL DEFAULT 0 CHECK(is_certain_original = 0),
    competing_readings_count INTEGER NOT NULL DEFAULT 0,
    competing_readings_preserved INTEGER NOT NULL DEFAULT 1 CHECK(competing_readings_preserved = 1),
    external_evidence_summary TEXT NOT NULL,
    internal_evidence_summary TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    claim_id TEXT REFERENCES claims(claim_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_td_run ON textual_decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_td_unit ON textual_decisions(variant_unit_id);
CREATE INDEX IF NOT EXISTS idx_td_reading ON textual_decisions(preferred_reading_id);
CREATE INDEX IF NOT EXISTS idx_td_state ON textual_decisions(decision_state);
CREATE INDEX IF NOT EXISTS idx_td_evidence ON textual_decisions(evidence_id);

-- ----------------------------------------------------------------------------
-- 5. TEXTUAL CRITERION OBSERVATIONS (Methodological Criteria & Separation)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS textual_criterion_observations (
    observation_id TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES textual_decisions(decision_id) ON DELETE RESTRICT,
    reading_id TEXT NOT NULL REFERENCES variant_readings(reading_id) ON DELETE RESTRICT,
    evidence_type TEXT NOT NULL CHECK(evidence_type IN ('EXTERNAL', 'INTERNAL')),
    criterion TEXT NOT NULL CHECK(criterion IN (
        'EXTERNAL_WITNESS_ATTESTATION',
        'EXTERNAL_WITNESS_DATE',
        'EXTERNAL_GEOGRAPHIC_DISTRIBUTION',
        'EXTERNAL_TEXTUAL_FAMILY',
        'EXTERNAL_INDEPENDENT_STEMMA',
        'TRANSCRIPTIONAL_LECTIO_DIFFICILIOR',
        'TRANSCRIPTIONAL_LECTIO_BREVIOR',
        'TRANSCRIPTIONAL_HARMONIZATION_TENDENCY',
        'TRANSCRIPTIONAL_PALEOGRAPHIC_CONFUSION',
        'TRANSCRIPTIONAL_HOMOIOTELEUTON',
        'TRANSCRIPTIONAL_LITURGICAL_EXPANSION',
        'TRANSCRIPTIONAL_DOCTRINAL_ALTERATION',
        'INTRINSIC_AUTHORIAL_STYLE',
        'INTRINSIC_AUTHORIAL_VOCABULARY',
        'INTRINSIC_IMMEDIATE_CONTEXT',
        'INTRINSIC_THEMATIC_COHERENCE'
    )),
    observation_value TEXT NOT NULL,
    evaluation_score REAL NOT NULL DEFAULT 0.0 CHECK(evaluation_score >= 0.0 AND evaluation_score <= 1.0),
    is_automatic_priority INTEGER NOT NULL DEFAULT 0 CHECK(is_automatic_priority = 0),
    notes TEXT,
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),

    -- Epistemic Boundary Constraint: External criteria must match EXTERNAL evidence_type; Internal criteria must match INTERNAL
    CHECK(
        (evidence_type = 'EXTERNAL' AND criterion LIKE 'EXTERNAL_%')
        OR (evidence_type = 'INTERNAL' AND criterion NOT LIKE 'EXTERNAL_%')
    )
);

CREATE INDEX IF NOT EXISTS idx_tco_decision ON textual_criterion_observations(decision_id);
CREATE INDEX IF NOT EXISTS idx_tco_reading ON textual_criterion_observations(reading_id);
CREATE INDEX IF NOT EXISTS idx_tco_criterion ON textual_criterion_observations(criterion);
CREATE INDEX IF NOT EXISTS idx_tco_type ON textual_criterion_observations(evidence_type);

-- ----------------------------------------------------------------------------
-- 6. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_tc_runs_no_update
BEFORE UPDATE ON textual_criticism_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: textual_criticism_runs is immutable except status transition to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.source_text_id IS NOT NEW.source_text_id
       OR OLD.edition_id IS NOT NEW.edition_id
       OR OLD.passage_id IS NOT NEW.passage_id
       OR OLD.pericope_id IS NOT NEW.pericope_id
       OR OLD.token_start_id IS NOT NEW.token_start_id
       OR OLD.token_end_id IS NOT NEW.token_end_id
       OR OLD.version_id != NEW.version_id
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.analyzer_id != NEW.analyzer_id
       OR OLD.analyzer_version != NEW.analyzer_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.created_at != NEW.created_at
       OR (OLD.status = 'COMPLETED' AND NEW.status != 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_tc_runs_no_delete
BEFORE DELETE ON textual_criticism_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: textual_criticism_runs is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_witness_meta_no_update
BEFORE UPDATE ON witness_metadata_v2
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: witness_metadata_v2 is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_witness_meta_no_delete
BEFORE DELETE ON witness_metadata_v2
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: witness_metadata_v2 is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_vue_no_update
BEFORE UPDATE ON variant_unit_executions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: variant_unit_executions is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_vue_no_delete
BEFORE DELETE ON variant_unit_executions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: variant_unit_executions is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_td_no_update
BEFORE UPDATE ON textual_decisions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: textual_decisions is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_td_no_delete
BEFORE DELETE ON textual_decisions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: textual_decisions is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_tco_no_update
BEFORE UPDATE ON textual_criterion_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: textual_criterion_observations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_tco_no_delete
BEFORE DELETE ON textual_criterion_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: textual_criterion_observations is immutable.');
END;
