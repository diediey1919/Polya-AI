-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 027: CORPUS IMPORT IDENTITY & MAPPING SUBSYSTEM
-- Specification: Architecture v2.0 — FROZEN (Task C.4.7 Approved)
-- Dialect: SQLite 3.46+ (Strict Typing, Composite Lineage FKs, Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CORPUS IMPORT RUNS (EXECUTION RUN ENVELOPE)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus_import_runs (
    run_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES source_registry(source_id) ON DELETE RESTRICT,
    source_version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    runner_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('INITIALIZED', 'RUNNING', 'COMPLETED', 'FAILED', 'ABORTED')),
    config_hash TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_summary TEXT,
    metadata_json TEXT,
    -- Unique keys for artifact and descendant composite FK binding
    UNIQUE(run_id, source_id),
    UNIQUE(run_id, source_id, source_version_id)
);

CREATE INDEX IF NOT EXISTS idx_import_runs_source ON corpus_import_runs(source_id, source_version_id);
CREATE INDEX IF NOT EXISTS idx_import_runs_status ON corpus_import_runs(status);

-- ----------------------------------------------------------------------------
-- 2. CORPUS IMPORT ARTIFACTS (RAW INGESTION ARTIFACTS)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus_import_artifacts (
    artifact_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    uri TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    mime_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    -- Enforce artifact belongs to run AND shares exact source_id
    FOREIGN KEY (run_id, source_id)
        REFERENCES corpus_import_runs(run_id, source_id) ON DELETE RESTRICT,
    UNIQUE(run_id, uri)
);

CREATE INDEX IF NOT EXISTS idx_import_artifacts_run ON corpus_import_artifacts(run_id, source_id);
CREATE INDEX IF NOT EXISTS idx_import_artifacts_hash ON corpus_import_artifacts(sha256_hash);

-- ----------------------------------------------------------------------------
-- 3. CORPUS IMPORT CHECKPOINTS (ATOMIC WORK UNIT & LEASE ENGINE)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus_import_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    unit_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_version_id TEXT NOT NULL,
    book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE RESTRICT,
    chapter INTEGER NOT NULL CHECK(chapter >= 0),
    sub_partition TEXT NOT NULL DEFAULT '',
    config_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('PENDING', 'LEASED', 'COMPLETED', 'FAILED_CONFLICT', 'REPLAY_IDENTICAL')),
    worker_id TEXT,
    lease_expires_at TEXT,
    fence_token INTEGER NOT NULL DEFAULT 0,
    records_processed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (run_id, source_id, source_version_id)
        REFERENCES corpus_import_runs(run_id, source_id, source_version_id) ON DELETE RESTRICT,
    UNIQUE(run_id, unit_id),
    UNIQUE(checkpoint_id, run_id, source_id, source_version_id)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_unit ON corpus_import_checkpoints(unit_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_run ON corpus_import_checkpoints(run_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_lease ON corpus_import_checkpoints(status, lease_expires_at);

-- ----------------------------------------------------------------------------
-- 4. CORPUS SOURCE VERSES (PHYSICAL OCCURRENCE LEDGER — STRICTLY IMMUTABLE)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus_source_verses (
    verse_record_id TEXT PRIMARY KEY,
    checkpoint_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_version_id TEXT NOT NULL,
    source_coordinate TEXT NOT NULL,
    language_code TEXT NOT NULL CHECK(language_code IN ('HEBREW', 'ARAMAIC', 'GREEK', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER')),
    raw_content TEXT NOT NULL,
    raw_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (checkpoint_id, run_id, source_id, source_version_id)
        REFERENCES corpus_import_checkpoints(checkpoint_id, run_id, source_id, source_version_id) ON DELETE RESTRICT,
    UNIQUE(source_version_id, source_coordinate)
);

CREATE INDEX IF NOT EXISTS idx_source_verses_lookup ON corpus_source_verses(source_version_id, source_coordinate);
CREATE INDEX IF NOT EXISTS idx_source_verses_checkpoint ON corpus_source_verses(checkpoint_id);
CREATE INDEX IF NOT EXISTS idx_source_verses_run ON corpus_source_verses(run_id);

CREATE TRIGGER IF NOT EXISTS trg_corpus_source_verses_no_delete
BEFORE DELETE ON corpus_source_verses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'corpus_source_verses records are strictly immutable: DELETE is prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_corpus_source_verses_no_update
BEFORE UPDATE ON corpus_source_verses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'corpus_source_verses records are strictly immutable: UPDATE is prohibited.');
END;

-- ----------------------------------------------------------------------------
-- 5. CORPUS SOURCE VERSE MAPPINGS (ASSOCIATION & VERSIONED ALIGNMENT LAYER)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus_source_verse_mappings (
    mapping_id TEXT PRIMARY KEY,
    verse_record_id TEXT NOT NULL REFERENCES corpus_source_verses(verse_record_id) ON DELETE RESTRICT,
    canonical_passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    mapping_provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    mapping_type TEXT NOT NULL CHECK(mapping_type IN ('EXACT_ONE_TO_ONE', 'ONE_TO_MANY_SPLIT', 'MANY_TO_ONE_MERGE', 'FRAGMENT')),
    sub_verse TEXT NOT NULL DEFAULT '',
    rule_hash TEXT NOT NULL,
    mapping_version INTEGER NOT NULL CHECK(mapping_version > 0),
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL,
    UNIQUE(verse_record_id, canonical_passage_id, sub_verse, rule_hash)
);

CREATE INDEX IF NOT EXISTS idx_mappings_target ON corpus_source_verse_mappings(canonical_passage_id);
CREATE INDEX IF NOT EXISTS idx_mappings_verse ON corpus_source_verse_mappings(verse_record_id);
CREATE INDEX IF NOT EXISTS idx_mappings_provenance ON corpus_source_verse_mappings(mapping_provenance_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_mapping_target
ON corpus_source_verse_mappings(verse_record_id, canonical_passage_id, sub_verse)
WHERE status = 'ACTIVE';

CREATE TRIGGER IF NOT EXISTS trg_corpus_source_verse_mappings_no_delete
BEFORE DELETE ON corpus_source_verse_mappings
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'corpus_source_verse_mappings records cannot be deleted: DELETE is prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_corpus_source_verse_mappings_immutable_fields
BEFORE UPDATE ON corpus_source_verse_mappings
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Immutable field mutation prohibited in corpus_source_verse_mappings.')
    WHERE OLD.mapping_id IS NOT NEW.mapping_id
       OR OLD.verse_record_id IS NOT NEW.verse_record_id
       OR OLD.canonical_passage_id IS NOT NEW.canonical_passage_id
       OR OLD.source_text_id IS NOT NEW.source_text_id
       OR OLD.mapping_provenance_id IS NOT NEW.mapping_provenance_id
       OR OLD.mapping_type IS NOT NEW.mapping_type
       OR OLD.sub_verse IS NOT NEW.sub_verse
       OR OLD.rule_hash IS NOT NEW.rule_hash
       OR OLD.mapping_version IS NOT NEW.mapping_version
       OR OLD.created_at IS NOT NEW.created_at;

    SELECT RAISE(ABORT, 'Invalid status transition: Only ACTIVE -> SUPERSEDED is permitted.')
    WHERE OLD.status != 'ACTIVE' OR NEW.status != 'SUPERSEDED';
END;

-- ----------------------------------------------------------------------------
-- 6. HARDENED PARENT LINEAGE TRIGGERS (EXISTS / NOT EXISTS SEMANTICS)
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_runs_source_version_lineage_ins
BEFORE INSERT ON corpus_import_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Parent lineage mismatch: source_version_id does not reference an existing object_versions row with object_type = ''SOURCE'' and matching source_id.')
    WHERE NOT EXISTS (
        SELECT 1 FROM object_versions
        WHERE version_id = NEW.source_version_id
          AND object_type = 'SOURCE'
          AND object_id = NEW.source_id
    );
END;

CREATE TRIGGER IF NOT EXISTS trg_checkpoints_source_version_lineage_ins
BEFORE INSERT ON corpus_import_checkpoints
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Parent lineage mismatch: checkpoint source_version_id does not reference an existing object_versions row with object_type = ''SOURCE'' and matching source_id.')
    WHERE NOT EXISTS (
        SELECT 1 FROM object_versions
        WHERE version_id = NEW.source_version_id
          AND object_type = 'SOURCE'
          AND object_id = NEW.source_id
    );
END;
