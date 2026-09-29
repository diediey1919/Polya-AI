-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 007: MORPHOLOGY FOUNDATION (Task 2.3)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE MORPHOLOGY_RUNS TABLE (Level 2 Derived Artifact Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS morphology_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
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
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    annotation_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. UPGRADE & RECREATE MORPHOLOGY_ANNOTATIONS TABLE
-- ----------------------------------------------------------------------------
-- Addresses legacy 001 schema limitation:
-- 1. Removes UNIQUE(token_id) constraint to support multiple competing parses.
-- 2. Strictly separates Greek vs Semitic morphological dimension spaces.
-- 3. Binds observations to token_id, source_text_id, version_id, provenance_id.
-- 4. Establishes Confidence and Evidence firewalls.
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS morphology_annotations_v2 (
    annotation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    lemma_id TEXT REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
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
    parse_index INTEGER NOT NULL DEFAULT 0,
    is_preferred INTEGER NOT NULL DEFAULT 1 CHECK(is_preferred IN (0, 1)),
    pos_tag TEXT NOT NULL,

    -- Greek-Specific Morphological Dimensions
    greek_pos TEXT CHECK(greek_pos IS NULL OR greek_pos IN (
        'NOUN', 'VERB', 'ADJECTIVE', 'ARTICLE', 'PRONOUN', 'PREPOSITION', 'CONJUNCTION', 'ADVERB', 'PARTICLE', 'INTERJECTION', 'OTHER'
    )),
    grammatical_case TEXT CHECK(grammatical_case IS NULL OR grammatical_case IN (
        'NOMINATIVE', 'GENITIVE', 'DATIVE', 'ACCUSATIVE', 'VOCATIVE'
    )),
    gender TEXT CHECK(gender IS NULL OR gender IN (
        'MASCULINE', 'FEMININE', 'NEUTER', 'COMMON'
    )),
    number TEXT CHECK(number IS NULL OR number IN (
        'SINGULAR', 'PLURAL', 'DUAL'
    )),
    person TEXT CHECK(person IS NULL OR person IN (
        'FIRST', 'SECOND', 'THIRD'
    )),
    tense TEXT CHECK(tense IS NULL OR tense IN (
        'PRESENT', 'IMPERFECT', 'FUTURE', 'AORIST', 'PERFECT', 'PLUPERFECT'
    )),
    voice TEXT CHECK(voice IS NULL OR voice IN (
        'ACTIVE', 'MIDDLE', 'PASSIVE', 'MIDDLE_PASSIVE'
    )),
    mood TEXT CHECK(mood IS NULL OR mood IN (
        'INDICATIVE', 'SUBJUNCTIVE', 'OPTATIVE', 'IMPERATIVE', 'INFINITIVE', 'PARTICIPLE'
    )),
    degree TEXT CHECK(degree IS NULL OR degree IN (
        'POSITIVE', 'COMPARATIVE', 'SUPERLATIVE'
    )),
    declension TEXT,

    -- Semitic-Specific Morphological Dimensions (Hebrew & Aramaic)
    lexical_category TEXT CHECK(lexical_category IS NULL OR lexical_category IN (
        'NOUN', 'VERB', 'ADJECTIVE', 'PREPOSITION', 'CONJUNCTION', 'PRONOUN', 'PARTICLE', 'ADVERB', 'INTERJECTION', 'OTHER'
    )),
    state TEXT CHECK(state IS NULL OR state IN (
        'ABSOLUTE', 'CONSTRUCT', 'EMPHATIC'
    )),
    stem TEXT CHECK(stem IS NULL OR stem IN (
        'QAL', 'NIPHAL', 'PIEL', 'PUAL', 'HIPHIL', 'HOPHIL', 'HITHPAEL',
        'PEAL', 'PEIL', 'PAEL', 'ITHPEEL', 'ITHPAAL', 'APHEL', 'HAPHEL', 'SHAPHEL',
        'POEL', 'POAL', 'HITPOEL', 'OTHER'
    )),
    verbal_aspect TEXT CHECK(verbal_aspect IS NULL OR verbal_aspect IN (
        'PERFECT', 'IMPERFECT', 'WEQATAL', 'WAYYIQTOL', 'IMPERATIVE',
        'INFINITIVE_CONSTRUCT', 'INFINITIVE_ABSOLUTE', 'PARTICIPLE_ACTIVE', 'PARTICIPLE_PASSIVE'
    )),
    suffix_person TEXT CHECK(suffix_person IS NULL OR suffix_person IN ('FIRST', 'SECOND', 'THIRD')),
    suffix_gender TEXT CHECK(suffix_gender IS NULL OR suffix_gender IN ('MASCULINE', 'FEMININE', 'COMMON')),
    suffix_number TEXT CHECK(suffix_number IS NULL OR suffix_number IN ('SINGULAR', 'PLURAL', 'DUAL')),
    is_construct INTEGER CHECK(is_construct IS NULL OR is_construct IN (0, 1)),

    -- Confidence & Evidence Firewall
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT CHECK(confidence_level IS NULL OR confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_ref TEXT,

    -- Provenance & Immutability
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    metadata_json TEXT,

    CHECK(parse_index >= 0),
    UNIQUE(token_id, run_id, parse_index)
);

-- Step 2a: Create placeholder run if legacy annotations exist to satisfy foreign key
INSERT OR IGNORE INTO morphology_runs (
    run_id, source_text_id, version_id, provenance_id, analyzer_id, analyzer_version,
    language, representation_type, configuration_hash, input_content_hash, output_hash,
    annotation_count, is_exact_reproducible, created_at, is_immutable, metadata_json
)
SELECT
    'RUN-MIGRATION-LEGACY',
    MIN(t.source_text_id),
    MIN(t.version_id),
    MIN(t.provenance_id),
    'legacy-migrator',
    '1.0',
    MIN(t.language),
    'RAW',
    'legacy-migration-placeholder',
    'legacy-migration-placeholder',
    'legacy-migration-placeholder',
    COUNT(m.annotation_id),
    0,
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    1,
    '{"note": "Auto-created placeholder run for legacy annotations"}'
FROM morphology_annotations m
JOIN tokens t ON m.token_id = t.token_id
GROUP BY 'RUN-MIGRATION-LEGACY';

-- Step 2b: Copy legacy annotations if table exists and has rows
INSERT OR IGNORE INTO morphology_annotations_v2 (
    annotation_id, run_id, token_id, source_text_id, version_id, provenance_id,
    language, pos_tag, grammatical_case, gender, number, person,
    voice, mood, confidence_level, analyzer_id, analyzer_version, created_at
)
SELECT
    m.annotation_id,
    'RUN-MIGRATION-LEGACY',
    m.token_id,
    t.source_text_id,
    t.version_id,
    t.provenance_id,
    t.language,
    m.pos_tag,
    m.grammatical_case,
    m.gender,
    m.number,
    m.person,
    m.voice,
    m.mood,
    m.confidence,
    m.analyzer_provenance,
    'legacy-1.0',
    (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
FROM morphology_annotations m
JOIN tokens t ON m.token_id = t.token_id
WHERE EXISTS (SELECT 1 FROM morphology_runs WHERE run_id = 'RUN-MIGRATION-LEGACY');

DROP TABLE morphology_annotations;

ALTER TABLE morphology_annotations_v2 RENAME TO morphology_annotations;

-- ----------------------------------------------------------------------------
-- 3. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_morph_ann_token_id ON morphology_annotations(token_id);
CREATE INDEX IF NOT EXISTS idx_morph_ann_run_id ON morphology_annotations(run_id);
CREATE INDEX IF NOT EXISTS idx_morph_ann_source_text ON morphology_annotations(source_text_id);
CREATE INDEX IF NOT EXISTS idx_morph_ann_version_id ON morphology_annotations(version_id);
CREATE INDEX IF NOT EXISTS idx_morph_ann_lemma_id ON morphology_annotations(lemma_id);
CREATE INDEX IF NOT EXISTS idx_morph_ann_language ON morphology_annotations(language);
CREATE INDEX IF NOT EXISTS idx_morph_ann_preferred ON morphology_annotations(token_id, is_preferred);
CREATE INDEX IF NOT EXISTS idx_morph_ann_pos_tag ON morphology_annotations(pos_tag);

CREATE INDEX IF NOT EXISTS idx_morph_runs_source_text ON morphology_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_morph_runs_version_id ON morphology_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_morph_runs_tokenization ON morphology_runs(tokenization_id);

-- ----------------------------------------------------------------------------
-- 4. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_morphology_runs_no_delete
BEFORE DELETE ON morphology_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Morphology runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_morphology_runs_immutable_fields
BEFORE UPDATE ON morphology_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Morphology runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_morphology_annotations_no_delete
BEFORE DELETE ON morphology_annotations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Morphological annotations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_morphology_annotations_immutable_fields
BEFORE UPDATE ON morphology_annotations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Morphological annotations are immutable: UPDATE is strictly prohibited.');
END;
