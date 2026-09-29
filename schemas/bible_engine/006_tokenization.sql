-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 006: TOKENIZATION FOUNDATION (Task 2.2)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE TOKENIZATION_RUNS TABLE (Level 1 Derived Artifact Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tokenization_runs (
    tokenization_id TEXT PRIMARY KEY,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    tokenizer_id TEXT NOT NULL,
    tokenizer_version TEXT NOT NULL,
    representation_type TEXT NOT NULL CHECK(representation_type IN (
        'RAW',
        'NORMALIZED',
        'TRANSLITERATED',
        'TRANSFORMED'
    )),
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
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible = 1),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. UPGRADE & RECREATE TOKENS TABLE (Level 1 Linguistic Tokens)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tokens_v2 (
    token_id TEXT PRIMARY KEY,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    token_index INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL DEFAULT 0,
    token_type TEXT NOT NULL DEFAULT 'WORD' CHECK(token_type IN (
        'WORD',
        'PUNCTUATION',
        'NUMBER',
        'WHITESPACE',
        'OTHER'
    )),
    surface_form TEXT,
    surface_original TEXT,
    surface_cleaned TEXT,
    normalized_form TEXT,
    start_offset INTEGER NOT NULL DEFAULT 0,
    end_offset INTEGER NOT NULL DEFAULT 0,
    start_byte INTEGER NOT NULL DEFAULT 0,
    end_byte INTEGER NOT NULL DEFAULT 0,
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
    representation_type TEXT NOT NULL DEFAULT 'RAW' CHECK(representation_type IN (
        'RAW',
        'NORMALIZED',
        'TRANSLITERATED',
        'TRANSFORMED'
    )),
    lemma_id TEXT REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK(surface_form IS NOT NULL OR surface_original IS NOT NULL),
    CHECK(start_offset >= 0 AND end_offset >= start_offset),
    CHECK(start_byte >= 0 AND end_byte >= start_byte)
);

INSERT INTO tokens_v2 (
    token_id, source_text_id, passage_id, position, surface_original, surface_cleaned,
    surface_form, lemma_id, language, token_index, created_at
)
SELECT
    token_id, source_text_id, passage_id, position, surface_original, surface_cleaned,
    surface_original, lemma_id, language, position, (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
FROM tokens;

DROP TABLE tokens;

ALTER TABLE tokens_v2 RENAME TO tokens;

-- ----------------------------------------------------------------------------
-- 3. INDEXES
-- ----------------------------------------------------------------------------

CREATE UNIQUE INDEX IF NOT EXISTS idx_tokens_tokenization_index ON tokens(tokenization_id, token_index);
CREATE INDEX IF NOT EXISTS idx_tokens_source_text_id ON tokens(source_text_id);
CREATE INDEX IF NOT EXISTS idx_tokens_tokenization_id ON tokens(tokenization_id);
CREATE INDEX IF NOT EXISTS idx_tokens_passage_id ON tokens(passage_id);
CREATE INDEX IF NOT EXISTS idx_tokens_version_id ON tokens(version_id);
CREATE INDEX IF NOT EXISTS idx_tokens_token_type ON tokens(token_type);
CREATE INDEX IF NOT EXISTS idx_tokens_language ON tokens(language);
CREATE INDEX IF NOT EXISTS idx_tokens_rep_type ON tokens(representation_type);

CREATE INDEX IF NOT EXISTS idx_tokenization_runs_source_text ON tokenization_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_tokenization_runs_version_id ON tokenization_runs(version_id);

-- ----------------------------------------------------------------------------
-- 4. DATABASE-LEVEL IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_tokenization_runs_no_delete
BEFORE DELETE ON tokenization_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Tokenization runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_tokenization_runs_immutable_fields
BEFORE UPDATE ON tokenization_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Mutation of tokenization_id is strictly prohibited.')
    WHERE OLD.tokenization_id IS NOT NEW.tokenization_id;

    SELECT RAISE(ABORT, 'Mutation of source_text_id is strictly prohibited.')
    WHERE OLD.source_text_id IS NOT NEW.source_text_id;

    SELECT RAISE(ABORT, 'Mutation of version_id is strictly prohibited.')
    WHERE OLD.version_id IS NOT NEW.version_id;

    SELECT RAISE(ABORT, 'Mutation of provenance_id is strictly prohibited.')
    WHERE OLD.provenance_id IS NOT NEW.provenance_id;

    SELECT RAISE(ABORT, 'Mutation of tokenizer_id is strictly prohibited.')
    WHERE OLD.tokenizer_id IS NOT NEW.tokenizer_id;

    SELECT RAISE(ABORT, 'Mutation of tokenizer_version is strictly prohibited.')
    WHERE OLD.tokenizer_version IS NOT NEW.tokenizer_version;

    SELECT RAISE(ABORT, 'Mutation of representation_type is strictly prohibited.')
    WHERE OLD.representation_type IS NOT NEW.representation_type;

    SELECT RAISE(ABORT, 'Mutation of language is strictly prohibited.')
    WHERE OLD.language IS NOT NEW.language;

    SELECT RAISE(ABORT, 'Mutation of configuration_hash is strictly prohibited.')
    WHERE OLD.configuration_hash IS NOT NEW.configuration_hash;

    SELECT RAISE(ABORT, 'Mutation of input_content_hash is strictly prohibited.')
    WHERE OLD.input_content_hash IS NOT NEW.input_content_hash;

    SELECT RAISE(ABORT, 'Mutation of output_hash is strictly prohibited.')
    WHERE OLD.output_hash IS NOT NEW.output_hash;

    SELECT RAISE(ABORT, 'Mutation of token_count is strictly prohibited.')
    WHERE OLD.token_count IS NOT NEW.token_count;

    SELECT RAISE(ABORT, 'Mutation of is_exact_reproducible is strictly prohibited.')
    WHERE OLD.is_exact_reproducible IS NOT NEW.is_exact_reproducible;

    SELECT RAISE(ABORT, 'Mutation of created_at is strictly prohibited.')
    WHERE OLD.created_at IS NOT NEW.created_at;

    SELECT RAISE(ABORT, 'Mutation of is_immutable is strictly prohibited.')
    WHERE OLD.is_immutable IS NOT NEW.is_immutable;
END;

CREATE TRIGGER IF NOT EXISTS trg_tokens_no_delete
BEFORE DELETE ON tokens
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Token records are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_tokens_immutable_fields
BEFORE UPDATE ON tokens
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation of token_id is strictly prohibited.')
    WHERE OLD.token_id IS NOT NEW.token_id;

    SELECT RAISE(ABORT, 'Mutation of tokenization_id is strictly prohibited.')
    WHERE OLD.tokenization_id IS NOT NEW.tokenization_id;

    SELECT RAISE(ABORT, 'Mutation of source_text_id is strictly prohibited.')
    WHERE OLD.source_text_id IS NOT NEW.source_text_id;

    SELECT RAISE(ABORT, 'Mutation of version_id is strictly prohibited.')
    WHERE OLD.version_id IS NOT NEW.version_id;

    SELECT RAISE(ABORT, 'Mutation of provenance_id is strictly prohibited.')
    WHERE OLD.provenance_id IS NOT NEW.provenance_id;

    SELECT RAISE(ABORT, 'Mutation of token_index is strictly prohibited.')
    WHERE OLD.token_index IS NOT NEW.token_index;

    SELECT RAISE(ABORT, 'Mutation of token_type is strictly prohibited.')
    WHERE OLD.token_type IS NOT NEW.token_type;

    SELECT RAISE(ABORT, 'Mutation of surface_form is strictly prohibited.')
    WHERE OLD.surface_form IS NOT NEW.surface_form;

    SELECT RAISE(ABORT, 'Mutation of surface_original is strictly prohibited.')
    WHERE OLD.surface_original IS NOT NEW.surface_original;

    SELECT RAISE(ABORT, 'Mutation of normalized_form is strictly prohibited.')
    WHERE OLD.normalized_form IS NOT NEW.normalized_form;

    SELECT RAISE(ABORT, 'Mutation of start_offset is strictly prohibited.')
    WHERE OLD.start_offset IS NOT NEW.start_offset;

    SELECT RAISE(ABORT, 'Mutation of end_offset is strictly prohibited.')
    WHERE OLD.end_offset IS NOT NEW.end_offset;

    SELECT RAISE(ABORT, 'Mutation of start_byte is strictly prohibited.')
    WHERE OLD.start_byte IS NOT NEW.start_byte;

    SELECT RAISE(ABORT, 'Mutation of end_byte is strictly prohibited.')
    WHERE OLD.end_byte IS NOT NEW.end_byte;

    SELECT RAISE(ABORT, 'Mutation of language is strictly prohibited.')
    WHERE OLD.language IS NOT NEW.language;

    SELECT RAISE(ABORT, 'Mutation of representation_type is strictly prohibited.')
    WHERE OLD.representation_type IS NOT NEW.representation_type;

    SELECT RAISE(ABORT, 'Mutation of created_at is strictly prohibited.')
    WHERE OLD.created_at IS NOT NEW.created_at;

    SELECT RAISE(ABORT, 'Mutation of is_immutable is strictly prohibited.')
    WHERE OLD.is_immutable IS NOT NEW.is_immutable;
END;
