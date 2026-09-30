-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 012: EVIDENCE & CLAIM FOUNDATION (Task 2.8)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core principle: NO CONCLUSION MAY OUTRUN ITS EVIDENCE.
-- Critical rules:
--   1. CONFIDENCE MUST NEVER BECOME EVIDENCE.
--   2. AI output is never automatically E0-E12 primary evidence.
--   3. Translation output cannot become E0 DIRECT_TEXT.
--   4. Morphology/Syntax/Semantic Sense/Discourse cannot directly create T3/T4 claims.
--   5. Entity association cannot directly create STRICT_IDENTITY.
--   6. Counter-evidence must be representable independently.
--   7. Claims with unresolved contradiction cannot be marked established.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE EVIDENCE_RUNS TABLE (Execution Ledger for Evidence & Claims)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    syntax_run_id TEXT REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    semantic_run_id TEXT REFERENCES semantic_runs(run_id) ON DELETE RESTRICT,
    referential_run_id TEXT REFERENCES referential_runs(run_id) ON DELETE RESTRICT,
    discourse_run_id TEXT REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    evidence_count INTEGER NOT NULL DEFAULT 0,
    claim_count INTEGER NOT NULL DEFAULT 0,
    link_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. STAGE CLAIM_EVIDENCE_LINKS TABLE (Prevent cascade deletions and FK locks)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS staging_claim_evidence_links AS
SELECT link_id, claim_id, evidence_id, relationship, reasoning
FROM claim_evidence_links;

DROP TABLE IF EXISTS claim_evidence_links;

-- ----------------------------------------------------------------------------
-- 3. UPGRADE CLAIMS TABLE (Epistemic Tiers, Types, Uncertainty & Contradictions)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS claims_v2 (
    claim_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES evidence_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'T0_RAW_OBSERVATION', 'T0', 'RAW_OBSERVATION', 'TIER_0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT', 'T1', 'LINGUISTIC_FACT', 'TIER_1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM', 'T2', 'CONTEXTUAL_CLAIM', 'TIER_2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM', 'T3', 'INTERPRETIVE_CLAIM', 'TIER_3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM', 'T4', 'THEOLOGICAL_CLAIM', 'TIER_4_THEOLOGICAL_CLAIM'
    )),
    epistemic_type TEXT NOT NULL CHECK(epistemic_type IN (
        'RAW_OBSERVATION',
        'LINGUISTIC_FACT',
        'CONTEXTUAL_FACT',
        'HISTORICAL_FACT',
        'INFERENCE',
        'INTERPRETATION',
        'THEOLOGICAL_CLAIM'
    )),
    claim_text TEXT NOT NULL,
    claimed_by TEXT NOT NULL,
    epistemic_status TEXT NOT NULL CHECK(epistemic_status IN (
        'VERIFIED_FACT',
        'STRONG_INFERENCE',
        'POSSIBLE_INTERPRETATION',
        'UNPROVEN_DOGMA',
        'CONTRADICTED_BY_TEXT',
        'UNRESOLVED_CONTRADICTION',
        'PROVISIONAL',
        'DISPUTED'
    )),
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    calculated_confidence REAL NOT NULL DEFAULT 0.0 CHECK(calculated_confidence >= 0.0 AND calculated_confidence <= 1.0),
    is_unresolved_contradiction INTEGER NOT NULL DEFAULT 0 CHECK(is_unresolved_contradiction IN (0, 1)),
    has_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(has_counter_evidence IN (0, 1)),
    doctrinal_system TEXT,
    is_theology_independent INTEGER NOT NULL DEFAULT 0 CHECK(is_theology_independent IN (0, 1)),
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- Epistemic Firewall: A claim with unresolved contradiction must not be silently marked established
    CHECK(is_unresolved_contradiction = 0 OR epistemic_status != 'VERIFIED_FACT')
);

INSERT OR IGNORE INTO claims_v2 (
    claim_id, pericope_id, claim_tier, epistemic_type, claim_text,
    claimed_by, epistemic_status, doctrinal_system, is_theology_independent
)
SELECT
    claim_id,
    pericope_id,
    claim_tier,
    CASE
        WHEN claim_tier IN ('T0_RAW_OBSERVATION', 'TIER_0_RAW_OBSERVATION') THEN 'RAW_OBSERVATION'
        WHEN claim_tier IN ('T1_LINGUISTIC_FACT', 'TIER_1_LINGUISTIC_FACT') THEN 'LINGUISTIC_FACT'
        WHEN claim_tier IN ('T2_CONTEXTUAL_CLAIM', 'TIER_2_CONTEXTUAL_CLAIM') THEN 'CONTEXTUAL_FACT'
        WHEN claim_tier IN ('T3_INTERPRETIVE_CLAIM', 'TIER_3_INTERPRETIVE_CLAIM') THEN 'INTERPRETATION'
        WHEN claim_tier IN ('T4_THEOLOGICAL_CLAIM', 'TIER_4_THEOLOGICAL_CLAIM') THEN 'THEOLOGICAL_CLAIM'
        ELSE 'INFERENCE'
    END,
    claim_text,
    claimed_by,
    epistemic_status,
    doctrinal_system,
    is_theology_independent
FROM claims;

DROP TABLE IF EXISTS claims;
ALTER TABLE claims_v2 RENAME TO claims;

-- ----------------------------------------------------------------------------
-- 4. UPGRADE EVIDENCE_LEDGER TABLE (Strict Evidence Class, Epistemic Tier & Firewalls)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_ledger_v2 (
    evidence_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES evidence_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    evidence_class TEXT NOT NULL CHECK(evidence_class IN (
        'E0_DIRECT_TEXT',
        'E1_TEXTUAL_MANUSCRIPT',
        'E2_MORPHOLOGY',
        'E3_SYNTAX',
        'E4_LEXICAL',
        'E5_DISCOURSE',
        'E6_IMMEDIATE_CONTEXT',
        'E7_BOOK_CONTEXT',
        'E8_CORPUS_CONTEXT',
        'E9_HISTORICAL_LINGUISTIC',
        'E10_INTERTEXTUAL',
        'E11_EARLY_RECEPTION',
        'E12_LATER_INTERPRETATION'
    )),
    epistemic_tier TEXT NOT NULL CHECK(epistemic_tier IN (
        'T0_RAW_OBSERVATION', 'T0', 'RAW_OBSERVATION', 'TIER_0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT', 'T1', 'LINGUISTIC_FACT', 'TIER_1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM', 'T2', 'CONTEXTUAL_CLAIM', 'TIER_2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM', 'T3', 'INTERPRETIVE_CLAIM', 'TIER_3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM', 'T4', 'THEOLOGICAL_CLAIM', 'TIER_4_THEOLOGICAL_CLAIM'
    )),
    epistemic_type TEXT CHECK(epistemic_type IS NULL OR epistemic_type IN (
        'RAW_OBSERVATION',
        'LINGUISTIC_FACT',
        'CONTEXTUAL_FACT',
        'HISTORICAL_FACT',
        'INFERENCE',
        'INTERPRETATION',
        'THEOLOGICAL_CLAIM'
    )),
    source_reference TEXT NOT NULL,
    extracted_text_or_data TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[LEXICALLY SUPPORTED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]',
        'EXPLICIT',
        'GRAMMATICALLY_ESTABLISHED',
        'LEXICALLY_SUPPORTED',
        'CONTEXTUALLY_STRONG',
        'INFERRED',
        'PLAUSIBLE',
        'AMBIGUOUS',
        'UNSUPPORTED',
        'CONTRADICTED'
    )),
    confidence TEXT NOT NULL CHECK(confidence IN (
        'CERTAIN', 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNSUPPORTED'
    )),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    is_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence IN (0, 1)),
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated IN (0, 1)),
    is_translation_derived INTEGER NOT NULL DEFAULT 0 CHECK(is_translation_derived IN (0, 1)),
    is_contradicted INTEGER NOT NULL DEFAULT 0 CHECK(is_contradicted IN (0, 1)),
    provenance_id TEXT REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    provenance_hash TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- Epistemic Firewall: Translation cannot become E0 DIRECT_TEXT
    CHECK(is_translation_derived = 0 OR evidence_class != 'E0_DIRECT_TEXT'),
    -- Epistemic Firewall: AI output is never primary evidence (E0-E1)
    CHECK(is_ai_generated = 0 OR evidence_class NOT IN ('E0_DIRECT_TEXT', 'E1_TEXTUAL_MANUSCRIPT'))
);

INSERT OR IGNORE INTO evidence_ledger_v2 (
    evidence_id, pericope_id, passage_id, token_id, evidence_class,
    epistemic_tier, source_reference, extracted_text_or_data, status,
    confidence, is_counter_evidence, created_at, provenance_hash
)
SELECT
    evidence_id, pericope_id, passage_id, token_id, evidence_class,
    epistemic_tier, source_reference, extracted_text_or_data, status,
    confidence, is_counter_evidence, created_at, provenance_hash
FROM evidence_ledger;

DROP TABLE IF EXISTS evidence_ledger;
ALTER TABLE evidence_ledger_v2 RENAME TO evidence_ledger;

-- ----------------------------------------------------------------------------
-- 5. RESTORE & UPGRADE CLAIM_EVIDENCE_LINKS TABLE
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS claim_evidence_links (
    link_id TEXT PRIMARY KEY,
    run_id TEXT REFERENCES evidence_runs(run_id) ON DELETE RESTRICT,
    claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE CASCADE,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    relationship TEXT NOT NULL CHECK(relationship IN (
        'SUPPORT', 'CONTRADICT', 'QUALIFY', 'LIMIT', 'REFINE',
        'SUPPORTS', 'CONTRADICTS', 'QUALIFIES', 'IRRELEVANT'
    )),
    is_critical_dependency INTEGER NOT NULL DEFAULT 0 CHECK(is_critical_dependency IN (0, 1)),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
    reasoning TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,
    UNIQUE(claim_id, evidence_id)
);

INSERT OR IGNORE INTO claim_evidence_links (
    link_id, claim_id, evidence_id, relationship, reasoning
)
SELECT
    link_id, claim_id, evidence_id, relationship, reasoning
FROM staging_claim_evidence_links;

DROP TABLE IF EXISTS staging_claim_evidence_links;

-- ----------------------------------------------------------------------------
-- 5. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_evidence_runs_source ON evidence_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_evidence_runs_version ON evidence_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_run ON evidence_ledger(run_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_pericope ON evidence_ledger(pericope_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_passage ON evidence_ledger(passage_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_token ON evidence_ledger(token_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_class ON evidence_ledger(evidence_class);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_tier ON evidence_ledger(epistemic_tier);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_counter ON evidence_ledger(is_counter_evidence);
CREATE INDEX IF NOT EXISTS idx_claims_run ON claims(run_id);
CREATE INDEX IF NOT EXISTS idx_claims_pericope ON claims(pericope_id);
CREATE INDEX IF NOT EXISTS idx_claims_passage ON claims(passage_id);
CREATE INDEX IF NOT EXISTS idx_claims_tier ON claims(claim_tier);
CREATE INDEX IF NOT EXISTS idx_claims_epistemic_type ON claims(epistemic_type);
CREATE INDEX IF NOT EXISTS idx_claims_epistemic_status ON claims(epistemic_status);
CREATE INDEX IF NOT EXISTS idx_claims_unresolved ON claims(is_unresolved_contradiction);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_links_claim ON claim_evidence_links(claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_links_evidence ON claim_evidence_links(evidence_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_links_relationship ON claim_evidence_links(relationship);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_links_run ON claim_evidence_links(run_id);

-- ----------------------------------------------------------------------------
-- 6. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_evidence_runs_no_delete
BEFORE DELETE ON evidence_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Evidence runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_runs_immutable_fields
BEFORE UPDATE ON evidence_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Evidence runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_ledger_no_delete
BEFORE DELETE ON evidence_ledger
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Evidence ledger records are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_ledger_immutable_fields
BEFORE UPDATE ON evidence_ledger
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Evidence ledger records are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_claims_no_delete
BEFORE DELETE ON claims
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Claims are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_claims_immutable_fields
BEFORE UPDATE ON claims
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Claims are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_claim_evidence_links_no_delete
BEFORE DELETE ON claim_evidence_links
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Claim evidence links are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_claim_evidence_links_immutable_fields
BEFORE UPDATE ON claim_evidence_links
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Claim evidence links are immutable: UPDATE is strictly prohibited.');
END;
