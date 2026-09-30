-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 010: REFERENTIAL & ENTITY FOUNDATION (Task 2.6)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE REFERENTIAL_RUNS TABLE (Execution Ledger for Referential Analysis)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS referential_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    syntax_run_id TEXT REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    semantic_run_id TEXT REFERENCES semantic_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    entity_count INTEGER NOT NULL DEFAULT 0,
    mention_count INTEGER NOT NULL DEFAULT 0,
    relation_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. ENHANCE ENTITIES TABLE (Language Separation & Provenance Tracking)
-- ----------------------------------------------------------------------------

ALTER TABLE entities ADD COLUMN language TEXT CHECK(language IS NULL OR language IN (
    'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
));

ALTER TABLE entities ADD COLUMN canonical_corpus TEXT CHECK(canonical_corpus IS NULL OR canonical_corpus IN (
    'OLD_TESTAMENT', 'NEW_TESTAMENT', 'APOCRYPHA', 'INTERTESTAMENTAL', 'GENERAL', 'OTHER'
));

ALTER TABLE entities ADD COLUMN provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT;

ALTER TABLE entities ADD COLUMN version_id TEXT REFERENCES object_versions(version_id) ON DELETE RESTRICT;

ALTER TABLE entities ADD COLUMN created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z';

ALTER TABLE entities ADD COLUMN is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1);

ALTER TABLE entities ADD COLUMN metadata_json TEXT;

-- ----------------------------------------------------------------------------
-- 3. UPGRADE ENTITY_MENTIONS TABLE (Token-Level Referential Anchors)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS entity_mentions_v2 (
    mention_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE RESTRICT,
    token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE CASCADE,
    passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    referential_status TEXT NOT NULL CHECK(referential_status IN (
        'EXPLICIT_NAMING',
        'PRONOMINAL_REFERENCE',
        'SYMBOLIC_ASSOCIATION',
        'TYPOLOGICAL_FIGURE',
        'APPOSITION',
        'EPITHET',
        'DEICTIC_REFERENCE',
        'METAPHORIC_REFERENCE',
        'OTHER'
    )),
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'STRONG', 'HIGH', 'AMBIGUOUS', 'UNSUPPORTED')),
    run_id TEXT REFERENCES referential_runs(run_id) ON DELETE RESTRICT,
    language TEXT CHECK(language IS NULL OR language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    syntax_clause_id TEXT REFERENCES clauses(clause_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

INSERT OR IGNORE INTO entity_mentions_v2 (
    mention_id, entity_id, token_id, passage_id, referential_status, confidence
)
SELECT
    mention_id, entity_id, token_id, passage_id, referential_status, confidence
FROM entity_mentions;

DROP TABLE IF EXISTS entity_mentions;
ALTER TABLE entity_mentions_v2 RENAME TO entity_mentions;

-- ----------------------------------------------------------------------------
-- 4. UPGRADE REFERENTIAL_RELATIONS TABLE (Evidence-Linked Identity Firewall)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS referential_relations_v2 (
    relation_id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE RESTRICT,
    target_entity_id TEXT NOT NULL REFERENCES entities(entity_id) ON DELETE RESTRICT,
    passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'MENTION',
        'REFERENCE',
        'ASSOCIATION',
        'REPRESENTATION',
        'IDENTITY',
        'STRICT_IDENTITY'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    grammatical_justification TEXT NOT NULL,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    is_identity_established INTEGER NOT NULL DEFAULT 0 CHECK(is_identity_established IN (0, 1)),
    run_id TEXT REFERENCES referential_runs(run_id) ON DELETE RESTRICT,
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    confidence_level TEXT NOT NULL DEFAULT 'HIGH' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(relation_type NOT IN ('IDENTITY', 'STRICT_IDENTITY') OR (is_identity_established = 1 AND evidence_id IS NOT NULL))
);

INSERT OR IGNORE INTO referential_relations_v2 (
    relation_id, source_entity_id, target_entity_id, passage_id,
    relation_type, evidence_id, grammatical_justification,
    evidence_status, is_identity_established
)
SELECT
    relation_id, source_entity_id, target_entity_id, passage_id,
    relation_type, evidence_id, grammatical_justification,
    evidence_status, is_identity_established
FROM referential_relations;

DROP TABLE IF EXISTS referential_relations;
ALTER TABLE referential_relations_v2 RENAME TO referential_relations;

-- ----------------------------------------------------------------------------
-- 5. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_entities_standard_name ON entities(standard_name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_language ON entities(language);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_entity ON entity_mentions(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_token ON entity_mentions(token_id);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_passage ON entity_mentions(passage_id);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_run ON entity_mentions(run_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations_source ON referential_relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations_target ON referential_relations(target_entity_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations_passage ON referential_relations(passage_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations_type ON referential_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_referential_relations_evidence ON referential_relations(evidence_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations_run ON referential_relations(run_id);
CREATE INDEX IF NOT EXISTS idx_referential_runs_source ON referential_runs(source_text_id);

-- ----------------------------------------------------------------------------
-- 6. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_entities_no_delete
BEFORE DELETE ON entities
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Entities are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_entities_immutable_fields
BEFORE UPDATE ON entities
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Entities are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_entity_mentions_no_delete
BEFORE DELETE ON entity_mentions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Entity mentions are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_entity_mentions_immutable_fields
BEFORE UPDATE ON entity_mentions
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Entity mentions are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_referential_relations_no_delete
BEFORE DELETE ON referential_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential relations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_referential_relations_immutable_fields
BEFORE UPDATE ON referential_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential relations are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_referential_runs_no_delete
BEFORE DELETE ON referential_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_referential_runs_immutable_fields
BEFORE UPDATE ON referential_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential runs are immutable: UPDATE is strictly prohibited.');
END;
