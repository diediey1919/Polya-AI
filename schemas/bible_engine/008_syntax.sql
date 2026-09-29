-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 008: SYNTAX FOUNDATION (Task 2.4)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE SYNTAX_RUNS TABLE (Level 2 Derived Artifact Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS syntax_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN (
        'GREEK',
        'HEBREW',
        'ARAMAIC',
        'LATIN',
        'SYRIAC',
        'COPTIC',
        'OTHER',
        'MULTILINGUAL'
    )),
    representation_type TEXT NOT NULL CHECK(representation_type IN (
        'RAW',
        'NORMALIZED',
        'TRANSLITERATED',
        'TRANSFORMED'
    )),
    syntax_model_type TEXT NOT NULL CHECK(syntax_model_type IN (
        'DEPENDENCY',
        'CONSTITUENCY',
        'HYBRID'
    )),
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    clause_count INTEGER NOT NULL DEFAULT 0,
    dependency_count INTEGER NOT NULL DEFAULT 0,
    constituent_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. CREATE CLAUSES_V2 TABLE (Independent Clause Boundaries & Hierarchy)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS clauses_v2 (
    clause_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    parent_clause_id TEXT REFERENCES clauses_v2(clause_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    clause_order INTEGER NOT NULL DEFAULT 0,
    clause_type TEXT NOT NULL CHECK(clause_type IN (
        'INDEPENDENT',
        'SUBORDINATE_PURPOSE',
        'SUBORDINATE_CAUSAL',
        'SUBORDINATE_RELATIVE',
        'SUBORDINATE_TEMPORAL',
        'SUBORDINATE_CONDITIONAL',
        'SUBORDINATE_RESULT',
        'SUBORDINATE_COMPARATIVE',
        'VERBLESS_NOMINAL',
        'PARTICIPIAL_CONSTRUCTION',
        'CONDITIONAL_PROTASIS',
        'CONDITIONAL_APODOSIS',
        'INFINITIVAL',
        'COORDINATE',
        'PARENT_EMBEDDED',
        'OTHER'
    )),
    relation_to_parent TEXT CHECK(relation_to_parent IS NULL OR relation_to_parent IN (
        'COORDINATION',
        'SUBORDINATION',
        'APPOSITION',
        'PARENT_EMBEDDED',
        'COMPLEMENT',
        'ADJUNCT',
        'RELATIVE',
        'OTHER'
    )),
    start_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    end_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    lead_conjunction_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    parse_index INTEGER NOT NULL DEFAULT 0 CHECK(parse_index >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 1 CHECK(is_preferred IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT CHECK(confidence_level IS NULL OR confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    raw_clause_string TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(run_id, clause_order, parse_index)
);

-- ----------------------------------------------------------------------------
-- 3. CREATE SYNTACTIC_CONSTITUENTS TABLE (Constituency Spans & Phrase Trees)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS syntactic_constituents (
    constituent_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    clause_id TEXT NOT NULL REFERENCES clauses_v2(clause_id) ON DELETE RESTRICT,
    parent_constituent_id TEXT REFERENCES syntactic_constituents(constituent_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    constituent_type TEXT NOT NULL CHECK(constituent_type IN (
        'NOUN_PHRASE',
        'VERB_PHRASE',
        'PREPOSITIONAL_PHRASE',
        'ADJECTIVAL_PHRASE',
        'ADVERBIAL_PHRASE',
        'PARTICIPIAL_PHRASE',
        'INFINITIVE_PHRASE',
        'CONSTRUCT_CHAIN',
        'CLAUSE_CONSTITUENT',
        'OTHER'
    )),
    grammatical_role TEXT CHECK(grammatical_role IS NULL OR grammatical_role IN (
        'SUBJECT',
        'PREDICATE',
        'OBJECT',
        'INDIRECT_OBJECT',
        'MODIFIER',
        'ADJUNCT',
        'COMPLEMENT',
        'APPOSITION',
        'COORDINATION',
        'SUBORDINATION',
        'RELATIVE',
        'PREPOSITIONAL_COMPLEMENT',
        'VOCATIVE',
        'SPECIFIER',
        'CONJUNCT',
        'COPULA',
        'DETERMINER',
        'ADVERBIAL',
        'CONSTRUCT_GENITIVE',
        'ROOT',
        'OTHER'
    )),
    head_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    start_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    end_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    parse_index INTEGER NOT NULL DEFAULT 0 CHECK(parse_index >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 1 CHECK(is_preferred IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT CHECK(confidence_level IS NULL OR confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 4. CREATE SYNTAX_DEPENDENCIES_V2 TABLE (Dependency Relations)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS syntax_dependencies_v2 (
    dependency_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    clause_id TEXT NOT NULL REFERENCES clauses_v2(clause_id) ON DELETE RESTRICT,
    head_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    dependent_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'SUBJECT',
        'PREDICATE',
        'OBJECT',
        'INDIRECT_OBJECT',
        'MODIFIER',
        'ADJUNCT',
        'COMPLEMENT',
        'APPOSITION',
        'COORDINATION',
        'SUBORDINATION',
        'RELATIVE',
        'PREPOSITIONAL_COMPLEMENT',
        'VOCATIVE',
        'SPECIFIER',
        'CONJUNCT',
        'COPULA',
        'DETERMINER',
        'ADVERBIAL',
        'CONSTRUCT_GENITIVE',
        'ROOT',
        'OTHER'
    )),
    language_specific_tag TEXT,
    morphology_annotation_id TEXT REFERENCES morphology_annotations(annotation_id) ON DELETE RESTRICT,
    parse_index INTEGER NOT NULL DEFAULT 0 CHECK(parse_index >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 1 CHECK(is_preferred IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT CHECK(confidence_level IS NULL OR confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(head_token_id IS NULL OR head_token_id != dependent_token_id),
    UNIQUE(run_id, clause_id, dependent_token_id, parse_index)
);

-- ----------------------------------------------------------------------------
-- 5. UPGRADE & MIGRATE LEGACY DATA
-- ----------------------------------------------------------------------------

-- Step 5a: Create placeholder run if legacy clauses exist
INSERT OR IGNORE INTO syntax_runs (
    run_id, source_text_id, version_id, provenance_id, analyzer_id, analyzer_version,
    language, representation_type, syntax_model_type, configuration_hash, input_content_hash,
    output_hash, clause_count, dependency_count, constituent_count, is_exact_reproducible,
    created_at, is_immutable, metadata_json
)
SELECT
    'RUN-MIGRATION-LEGACY-SYNTAX',
    COALESCE(MIN(t.source_text_id), (SELECT source_text_id FROM source_texts LIMIT 1)),
    COALESCE(MIN(t.version_id), (SELECT version_id FROM object_versions LIMIT 1)),
    COALESCE(MIN(t.provenance_id), (SELECT provenance_id FROM provenance_records LIMIT 1)),
    'legacy-syntax-migrator',
    '1.0',
    COALESCE(MIN(t.language), 'GREEK'),
    'RAW',
    'DEPENDENCY',
    'legacy-syntax-config-hash',
    'legacy-syntax-input-hash',
    'legacy-syntax-output-hash',
    COUNT(DISTINCT c.clause_id),
    0,
    0,
    0,
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    1,
    '{"note": "Placeholder run for legacy clauses"}'
FROM clauses c
LEFT JOIN tokens t ON t.passage_id = c.passage_id
GROUP BY 'RUN-MIGRATION-LEGACY-SYNTAX';

-- Step 5b: Copy legacy clauses if table exists and has rows
INSERT OR IGNORE INTO clauses_v2 (
    clause_id, run_id, source_text_id, version_id, provenance_id, passage_id,
    clause_order, clause_type, start_token_id, end_token_id, raw_clause_string,
    created_at, is_immutable
)
SELECT
    c.clause_id,
    'RUN-MIGRATION-LEGACY-SYNTAX',
    COALESCE(t.source_text_id, (SELECT source_text_id FROM source_texts LIMIT 1)),
    COALESCE(t.version_id, (SELECT version_id FROM object_versions LIMIT 1)),
    COALESCE(t.provenance_id, (SELECT provenance_id FROM provenance_records LIMIT 1)),
    CASE WHEN EXISTS (SELECT 1 FROM passages p WHERE p.passage_id = c.passage_id) THEN c.passage_id ELSE NULL END,
    c.clause_order,
    c.clause_type,
    COALESCE(t.token_id, (SELECT token_id FROM tokens LIMIT 1)),
    COALESCE(t.token_id, (SELECT token_id FROM tokens LIMIT 1)),
    c.raw_clause_string,
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    1
FROM clauses c
LEFT JOIN tokens t ON t.passage_id = c.passage_id
WHERE EXISTS (SELECT 1 FROM syntax_runs WHERE run_id = 'RUN-MIGRATION-LEGACY-SYNTAX')
GROUP BY c.clause_id;

DROP TABLE IF EXISTS clauses;

ALTER TABLE clauses_v2 RENAME TO clauses;
ALTER TABLE syntax_dependencies_v2 RENAME TO syntax_dependencies;

-- ----------------------------------------------------------------------------
-- 5c. SYNTAX_TREES (Backwards Compatibility Table for Phase 1 Gate)
-- ----------------------------------------------------------------------------

-- Maintain syntax_trees as an actual table for legacy queries and Phase 1 gate verification
CREATE TABLE IF NOT EXISTS syntax_trees (
    syntax_node_id TEXT PRIMARY KEY,
    clause_id TEXT NOT NULL REFERENCES clauses(clause_id) ON DELETE CASCADE,
    head_token_id TEXT REFERENCES tokens(token_id) ON DELETE CASCADE,
    dependent_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'HIGH', 'AMBIGUOUS')),
    is_alternative_parse INTEGER NOT NULL DEFAULT 0 CHECK(is_alternative_parse IN (0, 1))
);

-- ----------------------------------------------------------------------------
-- 6. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_syntax_runs_source ON syntax_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_syntax_runs_morph ON syntax_runs(morphology_run_id);
CREATE INDEX IF NOT EXISTS idx_clauses_run_id ON clauses(run_id);
CREATE INDEX IF NOT EXISTS idx_clauses_source_text ON clauses(source_text_id);
CREATE INDEX IF NOT EXISTS idx_clauses_tokens ON clauses(start_token_id, end_token_id);
CREATE INDEX IF NOT EXISTS idx_clauses_parent ON clauses(parent_clause_id);

CREATE INDEX IF NOT EXISTS idx_constituents_run ON syntactic_constituents(run_id);
CREATE INDEX IF NOT EXISTS idx_constituents_clause ON syntactic_constituents(clause_id);
CREATE INDEX IF NOT EXISTS idx_constituents_parent ON syntactic_constituents(parent_constituent_id);
CREATE INDEX IF NOT EXISTS idx_constituents_tokens ON syntactic_constituents(start_token_id, end_token_id);

CREATE INDEX IF NOT EXISTS idx_dependencies_run ON syntax_dependencies(run_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_clause ON syntax_dependencies(clause_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_head ON syntax_dependencies(head_token_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_dependent ON syntax_dependencies(dependent_token_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_relation ON syntax_dependencies(relation_type);

-- ----------------------------------------------------------------------------
-- 7. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_syntax_runs_no_delete
BEFORE DELETE ON syntax_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntax runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_syntax_runs_immutable_fields
BEFORE UPDATE ON syntax_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntax runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_clauses_no_delete
BEFORE DELETE ON clauses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Clauses are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_clauses_immutable_fields
BEFORE UPDATE ON clauses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Clauses are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_syntactic_constituents_no_delete
BEFORE DELETE ON syntactic_constituents
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntactic constituents are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_syntactic_constituents_immutable_fields
BEFORE UPDATE ON syntactic_constituents
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntactic constituents are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_syntax_dependencies_no_delete
BEFORE DELETE ON syntax_dependencies
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntax dependencies are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_syntax_dependencies_immutable_fields
BEFORE UPDATE ON syntax_dependencies
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Syntax dependencies are immutable: UPDATE is strictly prohibited.');
END;
