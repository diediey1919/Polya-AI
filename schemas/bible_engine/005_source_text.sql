-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 005: SOURCE TEXT FOUNDATION (Task 2.1)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SEED CANONICAL ROOT SOURCE (Guarantees Zero Orphaned Source Texts)
-- ----------------------------------------------------------------------------

INSERT OR IGNORE INTO source_registry (
    source_id,
    canonical_name,
    source_type,
    language,
    authority_level,
    description,
    created_at,
    updated_at
) VALUES (
    'SRC-CANONICAL-ROOT',
    'Canonical Scripture Foundation Root',
    'CRITICAL_EDITION',
    'GREEK',
    'TEXTUAL_CRITICAL',
    'Root baseline scholarly source for unlinked legacy passages',
    '2026-01-01T00:00:00Z',
    '2026-01-01T00:00:00Z'
);

-- ----------------------------------------------------------------------------
-- 2. UPGRADE & RECREATE SOURCE_TEXTS TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS source_texts_v2 (
    source_text_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL DEFAULT 'SRC-CANONICAL-ROOT' REFERENCES source_registry(source_id) ON DELETE RESTRICT,
    version_id TEXT REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    edition_id TEXT REFERENCES critical_editions(edition_id) ON DELETE RESTRICT,
    witness_id TEXT REFERENCES witnesses(witness_id) ON DELETE RESTRICT,
    source_type TEXT NOT NULL CHECK(source_type IN (
        'PRIMARY_WITNESS',
        'CRITICAL_EDITION',
        'SOURCE_LANGUAGE_TEXT',
        'ANCIENT_TRANSLATION',
        'MODERN_TRANSLATION',
        'USER_SUPPLIED_CANDIDATE'
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
    representation_type TEXT NOT NULL DEFAULT 'RAW' CHECK(representation_type IN (
        'RAW',
        'NORMALIZED',
        'TRANSLITERATED',
        'TRANSFORMED'
    )),
    raw_content TEXT,
    raw_source_string TEXT NOT NULL,
    normalized_content TEXT,
    normalized_source_string TEXT NOT NULL,
    content_hash TEXT CHECK(content_hash IS NULL OR (length(content_hash) = 64 AND NOT content_hash GLOB '*[^0-9a-f]*')),
    sha256_hash TEXT NOT NULL UNIQUE,
    encoding TEXT NOT NULL DEFAULT 'UTF-8',
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    CHECK(raw_content IS NULL OR raw_content = raw_source_string),
    CHECK(content_hash IS NULL OR content_hash = sha256_hash),
    CHECK(normalized_content IS NULL OR normalized_content = normalized_source_string)
);

INSERT INTO source_texts_v2 (
    source_text_id, source_id, version_id, provenance_id, passage_id,
    edition_id, witness_id, source_type, language, representation_type,
    raw_content, raw_source_string, normalized_content, normalized_source_string,
    content_hash, sha256_hash, encoding, created_at, is_immutable, metadata_json
)
SELECT
    source_text_id, 'SRC-CANONICAL-ROOT', NULL, NULL, passage_id,
    edition_id, witness_id, source_type, language, 'RAW',
    raw_source_string, raw_source_string, normalized_source_string, normalized_source_string,
    CASE WHEN length(sha256_hash) = 64 AND NOT sha256_hash GLOB '*[^0-9a-f]*' THEN sha256_hash ELSE NULL END,
    sha256_hash, 'UTF-8', created_at, is_immutable, NULL
FROM source_texts;

DROP TABLE source_texts;

ALTER TABLE source_texts_v2 RENAME TO source_texts;

CREATE INDEX IF NOT EXISTS idx_source_texts_source_id ON source_texts(source_id);
CREATE INDEX IF NOT EXISTS idx_source_texts_passage_id ON source_texts(passage_id);
CREATE INDEX IF NOT EXISTS idx_source_texts_version_id ON source_texts(version_id);
CREATE INDEX IF NOT EXISTS idx_source_texts_provenance_id ON source_texts(provenance_id);
CREATE INDEX IF NOT EXISTS idx_source_texts_language ON source_texts(language);
CREATE INDEX IF NOT EXISTS idx_source_texts_rep_type ON source_texts(representation_type);
CREATE INDEX IF NOT EXISTS idx_source_texts_sha256 ON source_texts(sha256_hash);

-- ----------------------------------------------------------------------------
-- 3. ABSOLUTE IMMUTABILITY TRIGGERS (Codex Findings H-002, D1, D10)
-- ----------------------------------------------------------------------------
-- Protects every single column in source_texts against unauthorized mutation.
-- Using IS NOT handles NULL-to-value and value-to-NULL transitions.
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_source_texts_no_delete
BEFORE DELETE ON source_texts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Source text records are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_source_texts_immutable_fields
BEFORE UPDATE ON source_texts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Mutation of source_text_id is strictly prohibited.')
    WHERE OLD.source_text_id IS NOT NEW.source_text_id;

    SELECT RAISE(ABORT, 'Mutation of source_id is strictly prohibited.')
    WHERE OLD.source_id IS NOT NEW.source_id;

    SELECT RAISE(ABORT, 'Mutation of version_id is strictly prohibited.')
    WHERE OLD.version_id IS NOT NEW.version_id;

    SELECT RAISE(ABORT, 'Mutation of provenance_id is strictly prohibited.')
    WHERE OLD.provenance_id IS NOT NEW.provenance_id;

    SELECT RAISE(ABORT, 'Mutation of passage_id is strictly prohibited.')
    WHERE OLD.passage_id IS NOT NEW.passage_id;

    SELECT RAISE(ABORT, 'Mutation of edition_id is strictly prohibited.')
    WHERE OLD.edition_id IS NOT NEW.edition_id;

    SELECT RAISE(ABORT, 'Mutation of witness_id is strictly prohibited.')
    WHERE OLD.witness_id IS NOT NEW.witness_id;

    SELECT RAISE(ABORT, 'Mutation of source_type is strictly prohibited.')
    WHERE OLD.source_type IS NOT NEW.source_type;

    SELECT RAISE(ABORT, 'Mutation of language is strictly prohibited.')
    WHERE OLD.language IS NOT NEW.language;

    SELECT RAISE(ABORT, 'Mutation of representation_type is strictly prohibited.')
    WHERE OLD.representation_type IS NOT NEW.representation_type;

    SELECT RAISE(ABORT, 'Mutation of raw_source_string is strictly prohibited.')
    WHERE OLD.raw_source_string IS NOT NEW.raw_source_string;

    SELECT RAISE(ABORT, 'Mutation of raw_content is strictly prohibited.')
    WHERE OLD.raw_content IS NOT NEW.raw_content;

    SELECT RAISE(ABORT, 'Mutation of normalized_source_string is strictly prohibited.')
    WHERE OLD.normalized_source_string IS NOT NEW.normalized_source_string;

    SELECT RAISE(ABORT, 'Mutation of normalized_content is strictly prohibited.')
    WHERE OLD.normalized_content IS NOT NEW.normalized_content;

    SELECT RAISE(ABORT, 'Mutation of sha256_hash is strictly prohibited.')
    WHERE OLD.sha256_hash IS NOT NEW.sha256_hash;

    SELECT RAISE(ABORT, 'Mutation of content_hash is strictly prohibited.')
    WHERE OLD.content_hash IS NOT NEW.content_hash;

    SELECT RAISE(ABORT, 'Mutation of encoding is strictly prohibited.')
    WHERE OLD.encoding IS NOT NEW.encoding;

    SELECT RAISE(ABORT, 'Mutation of created_at timestamp is strictly prohibited.')
    WHERE OLD.created_at IS NOT NEW.created_at;

    SELECT RAISE(ABORT, 'Mutation of is_immutable flag is strictly prohibited.')
    WHERE OLD.is_immutable IS NOT NEW.is_immutable;

    SELECT RAISE(ABORT, 'Mutation of metadata_json is strictly prohibited.')
    WHERE OLD.metadata_json IS NOT NEW.metadata_json;
END;

-- ----------------------------------------------------------------------------
-- 4. TRANSLATION FIREWALL TRIGGERS (Codex Finding D3)
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_source_texts_translation_firewall_ins
BEFORE INSERT ON source_texts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation cannot be registered as primary witness, critical edition, or source language text.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'MODERN_TRANSLATION'
      AND NEW.source_type IN ('PRIMARY_WITNESS', 'CRITICAL_EDITION', 'SOURCE_LANGUAGE_TEXT');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Ancient translation cannot be registered as primary source-language text or critical edition.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'ANCIENT_TRANSLATION'
      AND NEW.source_type IN ('PRIMARY_WITNESS', 'CRITICAL_EDITION', 'SOURCE_LANGUAGE_TEXT');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation cannot have source_type PRIMARY_WITNESS, CRITICAL_EDITION, or SOURCE_LANGUAGE_TEXT.')
    WHERE NEW.source_type = 'MODERN_TRANSLATION'
      AND NEW.language IN ('GREEK', 'HEBREW', 'ARAMAIC');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation language cannot be silently promoted to biblical source language.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'MODERN_TRANSLATION'
      AND NEW.language IN ('GREEK', 'HEBREW', 'ARAMAIC');
END;

CREATE TRIGGER IF NOT EXISTS trg_source_texts_translation_firewall_upd
BEFORE UPDATE ON source_texts
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation cannot be registered as primary witness, critical edition, or source language text.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'MODERN_TRANSLATION'
      AND NEW.source_type IN ('PRIMARY_WITNESS', 'CRITICAL_EDITION', 'SOURCE_LANGUAGE_TEXT');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Ancient translation cannot be registered as primary source-language text or critical edition.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'ANCIENT_TRANSLATION'
      AND NEW.source_type IN ('PRIMARY_WITNESS', 'CRITICAL_EDITION', 'SOURCE_LANGUAGE_TEXT');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation cannot have source_type PRIMARY_WITNESS, CRITICAL_EDITION, or SOURCE_LANGUAGE_TEXT.')
    WHERE NEW.source_type = 'MODERN_TRANSLATION'
      AND NEW.language IN ('GREEK', 'HEBREW', 'ARAMAIC');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translation language cannot be silently promoted to biblical source language.')
    WHERE (SELECT source_type FROM source_registry WHERE source_id = NEW.source_id) = 'MODERN_TRANSLATION'
      AND NEW.language IN ('GREEK', 'HEBREW', 'ARAMAIC');
END;
