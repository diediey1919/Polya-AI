-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 009: SEMANTIC FOUNDATION (Task 2.5)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE LEXEMES TABLE (Lexeme Separation from Surface Form & Lemma)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lexemes (
    lexeme_id TEXT PRIMARY KEY,
    language TEXT NOT NULL CHECK(language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    citation_form TEXT NOT NULL,
    lemma_id TEXT REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
    etymological_root TEXT,
    homonym_number INTEGER NOT NULL DEFAULT 1 CHECK(homonym_number >= 1),
    lexical_category TEXT NOT NULL CHECK(lexical_category IN (
        'NOUN', 'VERB', 'ADJECTIVE', 'ADVERB', 'PREPOSITION', 'CONJUNCTION',
        'PRONOUN', 'PARTICLE', 'INTERJECTION', 'PROPER_NOUN', 'OTHER'
    )),
    morphological_pattern TEXT,
    is_borrowing INTEGER NOT NULL DEFAULT 0 CHECK(is_borrowing IN (0, 1)),
    language_of_origin TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(language, citation_form, homonym_number)
);

-- ----------------------------------------------------------------------------
-- 2. CREATE SEMANTIC_DOMAINS TABLE (Lexical Conceptual Domains)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS semantic_domains (
    domain_id TEXT PRIMARY KEY,
    domain_code TEXT NOT NULL UNIQUE,
    domain_name TEXT NOT NULL,
    parent_domain_id TEXT REFERENCES semantic_domains(domain_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    framework_source TEXT NOT NULL CHECK(framework_source IN (
        'LOUW_NIDA', 'TOWNSEND', 'FELDMAN', 'INTERNAL_TAXONOMY', 'OTHER'
    )),
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

-- ----------------------------------------------------------------------------
-- 3. UPGRADE SEMANTIC_SENSES TABLE (Level 3 Semantic Sense Identity)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS semantic_senses_v2 (
    sense_id TEXT PRIMARY KEY,
    lexeme_id TEXT NOT NULL REFERENCES lexemes(lexeme_id) ON DELETE RESTRICT,
    sense_number INTEGER NOT NULL DEFAULT 1 CHECK(sense_number >= 1),
    sense_label TEXT NOT NULL,
    definition TEXT NOT NULL,
    gloss_primary TEXT NOT NULL,
    gloss_secondary TEXT,
    domain_id TEXT REFERENCES semantic_domains(domain_id) ON DELETE RESTRICT,
    contemporary_domain TEXT NOT NULL,
    register_level TEXT CHECK(register_level IS NULL OR register_level IN (
        'LITERARY', 'FORMAL', 'INFORMAL', 'COLLOQUIAL', 'POETIC', 'ARCHAIC', 'TECHNICAL', 'OTHER'
    )),
    lexicon_source TEXT NOT NULL,
    external_resource_id TEXT,
    external_resource_uri TEXT,
    confidence_level TEXT NOT NULL DEFAULT 'HIGH' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(lexeme_id, sense_number)
);

-- Step 3a: Populate default lexemes from existing lemmas to preserve foreign keys
INSERT OR IGNORE INTO lexemes (
    lexeme_id, language, citation_form, lemma_id, homonym_number, lexical_category, created_at, is_immutable
)
SELECT
    'LEX-' || l.lemma_id,
    l.language,
    l.lemma_string,
    l.lemma_id,
    1,
    CASE
        WHEN l.lexical_category IN ('NOUN', 'VERB', 'ADJECTIVE', 'ADVERB', 'PREPOSITION', 'CONJUNCTION', 'PRONOUN', 'PARTICLE', 'INTERJECTION', 'PROPER_NOUN') THEN l.lexical_category
        ELSE 'OTHER'
    END,
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    1
FROM lemmas l;

-- Step 3b: Copy legacy semantic_senses rows into semantic_senses_v2
INSERT OR IGNORE INTO semantic_senses_v2 (
    sense_id, lexeme_id, sense_number, sense_label, definition, gloss_primary,
    contemporary_domain, lexicon_source, created_at, is_immutable
)
SELECT
    s.sense_id,
    'LEX-' || s.lemma_id,
    ROW_NUMBER() OVER (PARTITION BY s.lemma_id ORDER BY s.sense_id),
    s.sense_label,
    s.definition,
    s.sense_label,
    s.contemporary_domain,
    s.lexicon_source,
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    1
FROM semantic_senses s;

-- Step 3c: Drop old table and rename v2
DROP TABLE IF EXISTS semantic_senses;
ALTER TABLE semantic_senses_v2 RENAME TO semantic_senses;

-- ----------------------------------------------------------------------------
-- 4. CREATE SEMANTIC_RELATIONS TABLE (Lexical Relations between Senses)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS semantic_relations (
    relation_id TEXT PRIMARY KEY,
    source_sense_id TEXT NOT NULL REFERENCES semantic_senses(sense_id) ON DELETE RESTRICT,
    target_sense_id TEXT NOT NULL REFERENCES semantic_senses(sense_id) ON DELETE RESTRICT,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'SYNONYM',
        'NEAR_SYNONYM',
        'ANTONYM',
        'HYPONYM',
        'HYPERNYM',
        'MERONYM',
        'HOLONYM',
        'POLYSEMY_EXTENSION',
        'METAPHORICAL_EXTENSION',
        'METONYMIC_EXTENSION',
        'CONTRASTIVE',
        'OTHER'
    )),
    lexicon_source TEXT,
    confidence_level TEXT NOT NULL DEFAULT 'HIGH' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(source_sense_id != target_sense_id),
    UNIQUE(source_sense_id, target_sense_id, relation_type)
);

-- ----------------------------------------------------------------------------
-- 5. CREATE SEMANTIC_RUNS TABLE (Execution Ledger for Contextual Semantics)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS semantic_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    syntax_run_id TEXT REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    representation_type TEXT NOT NULL CHECK(representation_type IN (
        'RAW', 'NORMALIZED', 'TRANSLITERATED', 'TRANSFORMED'
    )),
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 6. CREATE CONTEXTUAL_SENSE_CANDIDATES TABLE (Token-Level Contextual Senses)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS contextual_sense_candidates (
    candidate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES semantic_runs(run_id) ON DELETE RESTRICT,
    token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    sense_id TEXT NOT NULL REFERENCES semantic_senses(sense_id) ON DELETE RESTRICT,
    candidate_rank INTEGER NOT NULL DEFAULT 1 CHECK(candidate_rank >= 1),
    is_preferred INTEGER NOT NULL DEFAULT 1 CHECK(is_preferred IN (0, 1)),
    contextual_gloss TEXT NOT NULL,
    contextual_nuance TEXT,
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'HIGH' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(run_id, token_id, candidate_rank)
);

-- ----------------------------------------------------------------------------
-- 7. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_lexemes_language ON lexemes(language);
CREATE INDEX IF NOT EXISTS idx_lexemes_lemma_id ON lexemes(lemma_id);
CREATE INDEX IF NOT EXISTS idx_semantic_senses_lexeme ON semantic_senses(lexeme_id);
CREATE INDEX IF NOT EXISTS idx_semantic_senses_domain ON semantic_senses(domain_id);
CREATE INDEX IF NOT EXISTS idx_semantic_relations_source ON semantic_relations(source_sense_id);
CREATE INDEX IF NOT EXISTS idx_semantic_relations_target ON semantic_relations(target_sense_id);
CREATE INDEX IF NOT EXISTS idx_semantic_runs_source ON semantic_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_contextual_senses_token ON contextual_sense_candidates(token_id);
CREATE INDEX IF NOT EXISTS idx_contextual_senses_run ON contextual_sense_candidates(run_id);
CREATE INDEX IF NOT EXISTS idx_contextual_senses_sense ON contextual_sense_candidates(sense_id);

-- ----------------------------------------------------------------------------
-- 8. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_lexemes_no_delete
BEFORE DELETE ON lexemes
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Lexemes are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_lexemes_immutable_fields
BEFORE UPDATE ON lexemes
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Lexemes are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_domains_no_delete
BEFORE DELETE ON semantic_domains
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic domains are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_domains_immutable_fields
BEFORE UPDATE ON semantic_domains
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic domains are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_senses_no_delete
BEFORE DELETE ON semantic_senses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic senses are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_senses_immutable_fields
BEFORE UPDATE ON semantic_senses
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic senses are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_relations_no_delete
BEFORE DELETE ON semantic_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic relations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_relations_immutable_fields
BEFORE UPDATE ON semantic_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic relations are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_runs_no_delete
BEFORE DELETE ON semantic_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_semantic_runs_immutable_fields
BEFORE UPDATE ON semantic_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Semantic runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_contextual_senses_no_delete
BEFORE DELETE ON contextual_sense_candidates
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Contextual sense candidates are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_contextual_senses_immutable_fields
BEFORE UPDATE ON contextual_sense_candidates
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Contextual sense candidates are immutable: UPDATE is strictly prohibited.');
END;
