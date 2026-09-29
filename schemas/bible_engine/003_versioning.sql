-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 003: VERSIONING SUBSYSTEM (Task 1.5)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. OBJECT VERSIONS (HISTORICAL IMMUTABLE ARTIFACT & DATA REVISION LEDGER)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS object_versions (
    version_id TEXT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    version_number INTEGER NOT NULL CHECK(version_number > 0),
    content_hash TEXT NOT NULL,
    parent_version_id TEXT,
    provenance_id TEXT,
    status TEXT NOT NULL CHECK(status IN ('DRAFT', 'ACTIVE', 'SUPERSEDED', 'INVALIDATED')),
    change_reason TEXT NOT NULL CHECK(change_reason IN (
        'INITIAL_CREATION',
        'CORRECTION',
        'REFINEMENT',
        'REANALYSIS',
        'REGENERATED_OUTPUT',
        'SCHEMA_CHANGE',
        'MODEL_CHANGE',
        'PROMPT_CHANGE',
        'PARSER_CHANGE',
        'SOURCE_CHANGE',
        'EVIDENCE_CHANGE',
        'HUMAN_CORRECTION'
    )),
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    invalidation_reason TEXT,
    invalidated_at TEXT,
    invalidated_by TEXT,
    metadata TEXT,
    FOREIGN KEY (parent_version_id) REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    UNIQUE(object_type, object_id, version_number)
);

-- At most one ACTIVE version per object entity at any given time
CREATE UNIQUE INDEX IF NOT EXISTS idx_object_versions_unique_active
ON object_versions(object_type, object_id)
WHERE status = 'ACTIVE';

-- ----------------------------------------------------------------------------
-- 2. VERSION RELATIONS (EXPLICIT DIRECTED VERSION LINEAGE & SUPERSEDENCE)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS version_relations (
    relation_id TEXT PRIMARY KEY,
    source_version_id TEXT NOT NULL,
    target_version_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'SUPERSEDES',
        'SUPERSEDED_BY',
        'DERIVED_FROM',
        'CORRECTION_OF',
        'REFINEMENT_OF',
        'REANALYSIS_OF',
        'REGENERATED_FROM',
        'TRANSFORMATION_OF',
        'HUMAN_REVISION_OF'
    )),
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_version_id) REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_version_id) REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    UNIQUE(source_version_id, target_version_id, relation_type)
);

-- ----------------------------------------------------------------------------
-- 3. VERSION IMMUTABILITY ENFORCEMENT TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_prevent_object_versions_delete
BEFORE DELETE ON object_versions
BEGIN
    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: Historical versions are permanent and cannot be deleted.');
END;

CREATE TRIGGER IF NOT EXISTS trg_enforce_object_version_immutability
BEFORE UPDATE ON object_versions
BEGIN
    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: version_id cannot be modified.')
    WHERE OLD.version_id IS NOT NEW.version_id;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: object_type cannot be modified.')
    WHERE OLD.object_type IS NOT NEW.object_type;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: object_id cannot be modified.')
    WHERE OLD.object_id IS NOT NEW.object_id;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: version_number cannot be modified.')
    WHERE OLD.version_number IS NOT NEW.version_number;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: content_hash cannot be modified.')
    WHERE OLD.content_hash IS NOT NEW.content_hash;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: parent_version_id cannot be modified.')
    WHERE OLD.parent_version_id IS NOT NEW.parent_version_id;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: provenance_id cannot be modified.')
    WHERE OLD.provenance_id IS NOT NEW.provenance_id;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: created_at cannot be modified.')
    WHERE OLD.created_at IS NOT NEW.created_at;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: created_by cannot be modified.')
    WHERE OLD.created_by IS NOT NEW.created_by;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: change_reason cannot be modified.')
    WHERE OLD.change_reason IS NOT NEW.change_reason;

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: metadata cannot be modified.')
    WHERE OLD.metadata IS NOT NEW.metadata;

    SELECT RAISE(FAIL, 'ILLEGAL_STATE_TRANSITION: DRAFT can only transition to ACTIVE or INVALIDATED.')
    WHERE OLD.status = 'DRAFT' AND NEW.status NOT IN ('DRAFT', 'ACTIVE', 'INVALIDATED');

    SELECT RAISE(FAIL, 'ILLEGAL_STATE_TRANSITION: ACTIVE can only transition to SUPERSEDED or INVALIDATED.')
    WHERE OLD.status = 'ACTIVE' AND NEW.status NOT IN ('ACTIVE', 'SUPERSEDED', 'INVALIDATED');

    SELECT RAISE(FAIL, 'ILLEGAL_STATE_TRANSITION: SUPERSEDED can only transition to INVALIDATED.')
    WHERE OLD.status = 'SUPERSEDED' AND NEW.status NOT IN ('SUPERSEDED', 'INVALIDATED');

    SELECT RAISE(FAIL, 'ILLEGAL_STATE_TRANSITION: INVALIDATED is terminal and cannot transition.')
    WHERE OLD.status = 'INVALIDATED' AND NEW.status != 'INVALIDATED';

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: Invalidation fields can only be set when invalidating a version.')
    WHERE OLD.status != 'INVALIDATED' AND NEW.status != 'INVALIDATED' AND (
        NEW.invalidation_reason IS NOT NULL OR
        NEW.invalidated_at IS NOT NULL OR
        NEW.invalidated_by IS NOT NULL
    );

    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: Invalidation metadata is permanent once set.')
    WHERE OLD.status = 'INVALIDATED' AND (
        OLD.invalidation_reason IS NOT NEW.invalidation_reason OR
        OLD.invalidated_at IS NOT NEW.invalidated_at OR
        OLD.invalidated_by IS NOT NEW.invalidated_by
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_version_relations_update
BEFORE UPDATE ON version_relations
BEGIN
    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: Version relations are append-only and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_prevent_version_relations_delete
BEFORE DELETE ON version_relations
BEGIN
    SELECT RAISE(FAIL, 'VERSION_IMMUTABILITY_VIOLATION: Version relations are append-only and cannot be deleted.');
END;

-- ----------------------------------------------------------------------------
-- 4. PERFORMANCE & LOOKUP INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_object_versions_lookup ON object_versions(object_type, object_id, version_number);
CREATE INDEX IF NOT EXISTS idx_object_versions_parent ON object_versions(parent_version_id);
CREATE INDEX IF NOT EXISTS idx_object_versions_provenance ON object_versions(provenance_id);
CREATE INDEX IF NOT EXISTS idx_object_versions_hash ON object_versions(content_hash);
CREATE INDEX IF NOT EXISTS idx_version_relations_source ON version_relations(source_version_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_version_relations_target ON version_relations(target_version_id, relation_type);
