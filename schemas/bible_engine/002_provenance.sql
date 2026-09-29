-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 002: PROVENANCE SUBSYSTEM (Task 1.4)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. PROVENANCE RECORDS (AUDITABLE ORIGIN & TRANSFORMATION LEDGER)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS provenance_records (
    provenance_id TEXT PRIMARY KEY,
    target_type TEXT NOT NULL CHECK(target_type IN (
        'PRIMARY_SOURCE',
        'TEXTUAL_WITNESS',
        'CRITICAL_EDITION',
        'SOURCE_TEXT',
        'PASSAGE',
        'PERICOPE',
        'TOKEN',
        'MORPHOLOGY',
        'SYNTAX',
        'SEMANTIC_ANALYSIS',
        'EVIDENCE',
        'CLAIM',
        'INTERPRETATION',
        'VALIDATION_RESULT',
        'DERIVED_ARTIFACT'
    )),
    target_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    transformation_type TEXT NOT NULL CHECK(transformation_type IN (
        'ORIGIN',
        'DETERMINISTIC',
        'GENERATIVE',
        'HYBRID',
        'HUMAN_INPUT'
    )),
    source_hash TEXT,
    input_hash TEXT,
    output_hash TEXT,
    schema_version TEXT NOT NULL,
    agent_id TEXT,
    agent_version TEXT,
    model TEXT,
    model_version TEXT,
    prompt_hash TEXT,
    prompt_version TEXT,
    config_hash TEXT,
    retrieval_version TEXT,
    job_id TEXT,
    parent_provenance_id TEXT,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    FOREIGN KEY (parent_provenance_id) REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 2. PROVENANCE RELATIONS (DIRECTED DERIVATION & EPISTEMIC DEPENDENCY)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS provenance_relations (
    relation_id TEXT PRIMARY KEY,
    subject_provenance_id TEXT NOT NULL,
    object_provenance_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'SOURCE_OF',
        'DERIVED_FROM',
        'GENERATED_FROM',
        'TRANSFORMED_FROM',
        'ANALYZED_FROM',
        'VALIDATED_AGAINST',
        'SUPPORTED_BY',
        'CONTRADICTED_BY'
    )),
    created_at TEXT NOT NULL,
    FOREIGN KEY (subject_provenance_id) REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    FOREIGN KEY (object_provenance_id) REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    UNIQUE(subject_provenance_id, object_provenance_id, relation_type)
);

-- ----------------------------------------------------------------------------
-- 3. PROVENANCE IMMUTABILITY ENFORCEMENT TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_prevent_provenance_records_update
BEFORE UPDATE ON provenance_records
BEGIN
    SELECT RAISE(FAIL, 'PROVENANCE_IMMUTABILITY_VIOLATION: Provenance records are append-only and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_provenance_records_delete
BEFORE DELETE ON provenance_records
BEGIN
    SELECT RAISE(FAIL, 'PROVENANCE_IMMUTABILITY_VIOLATION: Provenance records are append-only and cannot be deleted.');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_provenance_relations_update
BEFORE UPDATE ON provenance_relations
BEGIN
    SELECT RAISE(FAIL, 'PROVENANCE_IMMUTABILITY_VIOLATION: Provenance relations are append-only and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_provenance_relations_delete
BEFORE DELETE ON provenance_relations
BEGIN
    SELECT RAISE(FAIL, 'PROVENANCE_IMMUTABILITY_VIOLATION: Provenance relations are append-only and cannot be deleted.');
END;

-- ----------------------------------------------------------------------------
-- 4. PERFORMANCE & LOOKUP INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_provenance_records_target ON provenance_records(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_provenance_records_content_hash ON provenance_records(content_hash);
CREATE INDEX IF NOT EXISTS idx_provenance_records_parent ON provenance_records(parent_provenance_id);
CREATE INDEX IF NOT EXISTS idx_provenance_records_agent ON provenance_records(agent_id, created_at);
CREATE INDEX IF NOT EXISTS idx_provenance_relations_subject ON provenance_relations(subject_provenance_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_provenance_relations_object ON provenance_relations(object_provenance_id, relation_type);
