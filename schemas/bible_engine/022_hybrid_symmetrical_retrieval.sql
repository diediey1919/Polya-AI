-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 022: HYBRID SYMMETRICAL RETRIEVAL ENGINE (Task 3.9)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   1. SYMMETRICAL SEARCH OBLIGATION:
--      Every retrieval execution must symmetrically query primary and counter branches.
--      Counter-search is mandatory and non-optional.
--   2. SEARCH BRANCH != EVIDENCE ROLE:
--      Search branch (PRIMARY_SEARCH / COUNTER_SEARCH) discovers candidates;
--      Evidence role (SUPPORTING, COUNTER_EVIDENCE, NEUTRAL_CONTEXT, ORTHOGONAL_TENSION)
--      is assigned strictly through post-retrieval validation.
--   3. STRICT E/T TIER SEPARATION:
--      Retrieval pack items reference evidence_ledger and optionally claims(claim_id).
--      No standalone or synthetic claim_tier on retrieval_pack_items.
--   4. GRAPH FIREWALL:
--      Graph connectivity, path length, degree, or centrality are candidate signals only.
--      They never establish truth, relevance, or epistemic confidence.
--   5. T4 THEOLOGY FIREWALL:
--      T4 dogmatic propositions cannot serve as evidence for T0–T3 claims.
--   6. ABSENCE-OF-EVIDENCE FIREWALL:
--      NOT_FOUND never equates to NO_COUNTER_EVIDENCE_EXISTS.
--   7. WEAKEST-CRITICAL-DEPENDENCY CONFIDENCE:
--      Pack confidence <= min(critical evidence confidences).
--      Ranking, BM25 score, or frequency cannot inflate confidence.
--   8. DETERMINISTIC CANONICAL HASH:
--      Pack hash is computed via deterministic canonical payload serialization.
--   9. IMMUTABILITY & PROVENANCE:
--      Append-only authoritative tables; UPDATE/DELETE blocked by triggers.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. RETRIEVAL QUERIES (Immutable Query Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retrieval_queries (
    query_id TEXT PRIMARY KEY,
    raw_query TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    query_hash TEXT NOT NULL UNIQUE,
    target_type TEXT NOT NULL CHECK(target_type IN (
        'CLAIM', 'PROPOSITION', 'PASSAGE', 'PERICOPE', 'FREE_TEXT'
    )),
    target_id TEXT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrieval_query_hash ON retrieval_queries(query_hash);
CREATE INDEX IF NOT EXISTS idx_retrieval_query_target ON retrieval_queries(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_query_prov ON retrieval_queries(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. RETRIEVAL RUNS (Execution & Configuration Registry)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retrieval_runs (
    run_id TEXT PRIMARY KEY,
    query_id TEXT NOT NULL REFERENCES retrieval_queries(query_id) ON DELETE RESTRICT,
    run_seed INTEGER NOT NULL DEFAULT 42,
    config_hash TEXT NOT NULL,
    config_json TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrieval_runs_query ON retrieval_runs(query_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_runs_config ON retrieval_runs(config_hash);
CREATE INDEX IF NOT EXISTS idx_retrieval_runs_prov ON retrieval_runs(provenance_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_runs_ver ON retrieval_runs(version_id);

-- ----------------------------------------------------------------------------
-- 3. RETRIEVAL COVERAGE RECORDS (Branch Coverage & Methodology Audit)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retrieval_coverage_records (
    coverage_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES retrieval_runs(run_id) ON DELETE RESTRICT,
    search_branch TEXT NOT NULL CHECK(search_branch IN ('PRIMARY_SEARCH', 'COUNTER_SEARCH')),
    search_strategy TEXT NOT NULL,
    query_formulation TEXT NOT NULL,
    target_scope TEXT NOT NULL,
    candidate_count INTEGER NOT NULL CHECK(candidate_count >= 0),
    matched_count INTEGER NOT NULL CHECK(matched_count >= 0),
    coverage_status TEXT NOT NULL CHECK(coverage_status IN (
        'PRIMARY_EVIDENCE_FOUND',
        'PRIMARY_EVIDENCE_NOT_FOUND',
        'PRIMARY_EVIDENCE_NOT_DETERMINABLE',
        'COUNTER_EVIDENCE_FOUND',
        'COUNTER_EVIDENCE_NOT_FOUND',
        'COUNTER_EVIDENCE_NOT_DETERMINABLE'
    )),
    methodology_notes TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrieval_cov_run ON retrieval_coverage_records(run_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_cov_branch ON retrieval_coverage_records(search_branch);
CREATE INDEX IF NOT EXISTS idx_retrieval_cov_status ON retrieval_coverage_records(coverage_status);

-- ----------------------------------------------------------------------------
-- 4. RETRIEVAL CONTEXT PACKS (Deterministic Context Pack Output)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retrieval_context_packs (
    pack_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES retrieval_runs(run_id) ON DELETE RESTRICT,
    query_id TEXT NOT NULL REFERENCES retrieval_queries(query_id) ON DELETE RESTRICT,
    pack_hash TEXT NOT NULL UNIQUE,
    aggregate_confidence REAL NOT NULL CHECK(aggregate_confidence >= 0.0 AND aggregate_confidence <= 1.0),
    primary_count INTEGER NOT NULL CHECK(primary_count >= 0),
    counter_count INTEGER NOT NULL CHECK(counter_count >= 0),
    total_item_count INTEGER NOT NULL CHECK(total_item_count >= 0),
    counter_evidence_status TEXT NOT NULL CHECK(counter_evidence_status IN (
        'COUNTER_EVIDENCE_FOUND',
        'COUNTER_EVIDENCE_NOT_FOUND',
        'COUNTER_EVIDENCE_NOT_DETERMINABLE'
    )),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrieval_packs_run ON retrieval_context_packs(run_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_packs_query ON retrieval_context_packs(query_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_packs_hash ON retrieval_context_packs(pack_hash);

-- ----------------------------------------------------------------------------
-- 5. RETRIEVAL PACK ITEMS (Granular Retrieved Evidence Items)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS retrieval_pack_items (
    item_id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL REFERENCES retrieval_context_packs(pack_id) ON DELETE RESTRICT,
    search_branch TEXT NOT NULL CHECK(search_branch IN ('PRIMARY_SEARCH', 'COUNTER_SEARCH')),
    evidence_role TEXT NOT NULL CHECK(evidence_role IN (
        'SUPPORTING', 'COUNTER_EVIDENCE', 'NEUTRAL_CONTEXT', 'ORTHOGONAL_TENSION'
    )),
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    linked_claim_id TEXT REFERENCES claims(claim_id) ON DELETE RESTRICT,
    candidate_source TEXT NOT NULL CHECK(candidate_source IN (
        'FTS5', 'GRAPH_RELATION', 'SYNTHESIS_GROUNDING', 'DIRECT_LOOKUP'
    )),
    item_confidence REAL NOT NULL CHECK(item_confidence >= 0.0 AND item_confidence <= 1.0),
    item_rank INTEGER NOT NULL CHECK(item_rank >= 1),
    relevance_score REAL NOT NULL,
    validation_notes TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_retrieval_items_pack ON retrieval_pack_items(pack_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_items_evidence ON retrieval_pack_items(evidence_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_items_claim ON retrieval_pack_items(linked_claim_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_items_branch ON retrieval_pack_items(search_branch);
CREATE INDEX IF NOT EXISTS idx_retrieval_items_role ON retrieval_pack_items(evidence_role);

-- ----------------------------------------------------------------------------
-- 6. FULL-TEXT SEARCH VIRTUAL TABLE (FTS5 Evidence Index)
-- ----------------------------------------------------------------------------

CREATE VIRTUAL TABLE IF NOT EXISTS retrieval_fts_index USING fts5(
    evidence_id UNINDEXED,
    text_content,
    context_notes,
    tokenize='unicode61'
);

-- ----------------------------------------------------------------------------
-- 7. IMMUTABILITY TRIGGERS (Append-Only Authoritative Enforcers)
-- ----------------------------------------------------------------------------

-- A. Retrieval Queries Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_queries_upd
BEFORE UPDATE ON retrieval_queries
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_queries are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_queries_del
BEFORE DELETE ON retrieval_queries
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_queries are immutable and cannot be deleted.');
END;

-- B. Retrieval Runs Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_runs_upd
BEFORE UPDATE ON retrieval_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_runs are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_runs_del
BEFORE DELETE ON retrieval_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_runs are immutable and cannot be deleted.');
END;

-- C. Retrieval Coverage Records Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_cov_upd
BEFORE UPDATE ON retrieval_coverage_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_coverage_records are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_cov_del
BEFORE DELETE ON retrieval_coverage_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_coverage_records are immutable and cannot be deleted.');
END;

-- D. Retrieval Context Packs Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_packs_upd
BEFORE UPDATE ON retrieval_context_packs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_context_packs are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_packs_del
BEFORE DELETE ON retrieval_context_packs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_context_packs are immutable and cannot be deleted.');
END;

-- E. Retrieval Pack Items Immutability
CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_items_upd
BEFORE UPDATE ON retrieval_pack_items
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_pack_items are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_retrieval_items_del
BEFORE DELETE ON retrieval_pack_items
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: retrieval_pack_items are immutable and cannot be deleted.');
END;
