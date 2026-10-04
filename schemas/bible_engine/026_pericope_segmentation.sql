-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 026: PERICOPE SEGMENTATION WITNESSES & ASSOCIATIONS
-- Specification: Architecture Revision V3 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys, Composite Keys & Immutability)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SEGMENTATION WITNESS REGISTRY
-- ----------------------------------------------------------------------------
CREATE TABLE segmentation_witnesses (
    segmentation_id     TEXT PRIMARY KEY,
    witness_name        TEXT NOT NULL,
    witness_type        TEXT NOT NULL CHECK(witness_type IN (
        'CANONICAL_PARTITION',
        'EDITORIAL_PARTITION',
        'DISCOURSE_SPANS',
        'LITURGICAL_LECTIONARY'
    )),
    authority_level     TEXT NOT NULL CHECK(authority_level IN (
        'PROVISIONAL',
        'SCHOLARLY_OPEN',
        'CRITICAL_EDITION',
        'TRADITIONAL'
    )),
    license             TEXT NOT NULL,
    description         TEXT,
    is_active_baseline  INTEGER NOT NULL DEFAULT 0 CHECK(is_active_baseline IN (0, 1)),
    source_provenance   TEXT NOT NULL,
    created_at          TEXT NOT NULL
);

-- Partial Unique Index enforcing at most ONE active baseline witness
CREATE UNIQUE INDEX idx_segmentation_witnesses_active_baseline
ON segmentation_witnesses(is_active_baseline)
WHERE is_active_baseline = 1;

-- ----------------------------------------------------------------------------
-- 2. SEED ACTIVE CANONICAL BASELINE WITNESS
-- ----------------------------------------------------------------------------
INSERT INTO segmentation_witnesses (
    segmentation_id,
    witness_name,
    witness_type,
    authority_level,
    license,
    description,
    is_active_baseline,
    source_provenance,
    created_at
) VALUES (
    'WIT-SEG-PROVISIONAL-CHAPTER',
    'Provisional Chapter Baseline',
    'CANONICAL_PARTITION',
    'PROVISIONAL',
    'Public Domain',
    'Provisional mechanical chapter partition. Carries zero scholarly or exegetical boundary authority.',
    1,
    'CANONICAL_CHAPTER_FALLBACK',
    '2026-10-04T00:00:00Z'
);

-- ----------------------------------------------------------------------------
-- 3. REBUILD PERICOPES (Add segmentation_id & Composite Unique Constraint)
-- ----------------------------------------------------------------------------
CREATE TABLE pericopes_new (
    pericope_id         TEXT PRIMARY KEY,
    book_id             TEXT NOT NULL,
    segmentation_id     TEXT NOT NULL REFERENCES segmentation_witnesses(segmentation_id) ON DELETE RESTRICT,
    reference           TEXT NOT NULL,
    start_chapter       INTEGER NOT NULL,
    start_verse         INTEGER NOT NULL,
    end_chapter         INTEGER NOT NULL,
    end_verse           INTEGER NOT NULL,
    genre               TEXT NOT NULL,
    boundary_source     TEXT NOT NULL,
    boundary_confidence TEXT NOT NULL CHECK(boundary_confidence IN ('HIGH', 'MEDIUM', 'LOW', 'BOUNDARY_UNCERTAIN')),
    status              TEXT NOT NULL CHECK(status IN ('REGISTERED', 'INGESTED', 'ANNOTATED', 'VALIDATED', 'NEEDS_REVIEW')),
    version             TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT,
    UNIQUE(segmentation_id, pericope_id)
);

INSERT INTO pericopes_new (
    pericope_id, book_id, segmentation_id, reference, start_chapter, start_verse,
    end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at
)
SELECT 
    pericope_id, book_id, 'WIT-SEG-PROVISIONAL-CHAPTER', reference, start_chapter, start_verse,
    end_chapter, end_verse, genre, boundary_source, boundary_confidence, status, version, created_at
FROM pericopes;

DROP TABLE pericopes;
ALTER TABLE pericopes_new RENAME TO pericopes;

CREATE INDEX idx_pericopes_book ON pericopes(book_id);
CREATE INDEX idx_pericopes_seg ON pericopes(segmentation_id);

-- ----------------------------------------------------------------------------
-- 4. PERICOPE-PASSAGE MULTI-WITNESS ASSOCIATION TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE pericope_passages (
    association_id      TEXT PRIMARY KEY,
    segmentation_id     TEXT NOT NULL,
    pericope_id         TEXT NOT NULL,
    passage_id          TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    ordinal             INTEGER NOT NULL CHECK(ordinal >= 1),
    containment_type    TEXT NOT NULL CHECK(containment_type IN ('FULL_VERSE', 'PARTIAL_VERSE')),
    boundary_position   TEXT NOT NULL CHECK(boundary_position IN ('INTERNAL', 'START_BOUNDARY', 'END_BOUNDARY', 'SINGLE_VERSE_PERICOPE')),
    created_at          TEXT NOT NULL,
    FOREIGN KEY (segmentation_id, pericope_id) REFERENCES pericopes(segmentation_id, pericope_id) ON DELETE RESTRICT,
    UNIQUE(pericope_id, passage_id),
    UNIQUE(segmentation_id, passage_id, ordinal)
);

CREATE INDEX idx_pericope_passages_pericope
ON pericope_passages(segmentation_id, pericope_id, ordinal);

CREATE INDEX idx_pericope_passages_lookup
ON pericope_passages(passage_id, segmentation_id);
