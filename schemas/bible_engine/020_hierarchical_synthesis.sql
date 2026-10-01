-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 020: HIERARCHICAL SYNTHESIS ENGINE (Task 3.7)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principle:
--   SYNTHESIS IS AGGREGATION, NOT INVENTION.
--   HIGHER SCOPES DO NOT CREATE NEW EVIDENCE.
--
-- Critical Epistemic Firewalls:
--   1. Directionality Invariant:
--      Strict bottom-up induction: PERICOPE -> SECTION -> BOOK -> CORPUS -> CANON.
--      Reverse dependencies and circular scope references are strictly forbidden.
--   2. Anti-Harmonization Firewall:
--      Divergent authors and traditions are never forced into false consensus.
--      Unresolved conflicts are persisted explicitly as TENSION / COMPETING / UNRESOLVED.
--   3. Weakest-Critical-Dependency Propagation:
--      Confidence of synthesis claim <= min(critical constituent confidences).
--      No arithmetic averaging, vote counts, or frequency escalation.
--   4. Authorial Distinctives:
--      Author-specific theological claims remain separated unless explicit dependency exists.
--   5. Reception Firewall:
--      E11/E12 reception history cannot be converted into original authorial intent (E0-E5).
--   6. Evidence Tier Protection:
--      E0-E12 and T0-T4 classifications are preserved across all synthesis scopes.
--   7. Immutability & Provenance:
--      All synthesis records trace to cryptographic provenance; UPDATE/DELETE blocked.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SYNTHESIS RUNS (Execution & Aggregation Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS synthesis_runs (
    run_id TEXT PRIMARY KEY,
    scope TEXT NOT NULL CHECK(scope IN ('PERICOPE', 'SECTION', 'BOOK', 'CORPUS', 'CANON')),
    target_id TEXT NOT NULL,
    parent_scope TEXT CHECK(parent_scope IN ('PERICOPE', 'SECTION', 'BOOK', 'CORPUS', 'CANON')),
    parent_target_id TEXT,
    synthesizer_id TEXT NOT NULL,
    synthesizer_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    aggregate_confidence REAL NOT NULL CHECK(aggregate_confidence >= 0.0 AND aggregate_confidence <= 1.0),
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_synth_runs_scope ON synthesis_runs(scope, target_id);
CREATE INDEX IF NOT EXISTS idx_synth_runs_prov ON synthesis_runs(provenance_id);
CREATE INDEX IF NOT EXISTS idx_synth_runs_ver ON synthesis_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_synth_runs_status ON synthesis_runs(status);

-- ----------------------------------------------------------------------------
-- 2. SYNTHESIS CLAIMS (Inductive Aggregated Claims)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS synthesis_claims (
    claim_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES synthesis_runs(run_id) ON DELETE RESTRICT,
    scope TEXT NOT NULL CHECK(scope IN ('PERICOPE', 'SECTION', 'BOOK', 'CORPUS', 'CANON')),
    target_id TEXT NOT NULL,
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM'
    )),
    primary_evidence_class TEXT NOT NULL CHECK(primary_evidence_class IN (
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
    claim_text TEXT NOT NULL,
    epistemic_status TEXT NOT NULL CHECK(epistemic_status IN (
        'CONVERGENT',
        'TENSION',
        'COMPETING',
        'UNRESOLVED',
        'SUPERSEDED'
    )),
    synthesized_confidence REAL NOT NULL CHECK(synthesized_confidence >= 0.0 AND synthesized_confidence <= 1.0),
    weakest_constituent_confidence REAL NOT NULL CHECK(weakest_constituent_confidence >= 0.0 AND weakest_constituent_confidence <= 1.0),
    authorial_context TEXT NOT NULL,
    is_harmonized INTEGER NOT NULL DEFAULT 0 CHECK(is_harmonized IN (0, 1)),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(synthesized_confidence <= weakest_constituent_confidence + 0.00001)
);

CREATE INDEX IF NOT EXISTS idx_synth_claims_run ON synthesis_claims(run_id);
CREATE INDEX IF NOT EXISTS idx_synth_claims_scope ON synthesis_claims(scope, target_id);
CREATE INDEX IF NOT EXISTS idx_synth_claims_status ON synthesis_claims(epistemic_status);
CREATE INDEX IF NOT EXISTS idx_synth_claims_prov ON synthesis_claims(provenance_id);

-- ----------------------------------------------------------------------------
-- 3. SYNTHESIS TENSIONS (Explicit Registry of Theological & Exegetical Divergence)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS synthesis_tensions (
    tension_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES synthesis_runs(run_id) ON DELETE RESTRICT,
    scope TEXT NOT NULL CHECK(scope IN ('PERICOPE', 'SECTION', 'BOOK', 'CORPUS', 'CANON')),
    target_id TEXT NOT NULL,
    tension_type TEXT NOT NULL CHECK(tension_type IN (
        'AUTHORIAL_DIVERGENCE',
        'CHRONOLOGICAL_DEVELOPMENT',
        'GENRE_DISPARITY',
        'COMPETING_THEOLOGICAL_EMPHASIS',
        'UNRESOLVED_ANTINOMY'
    )),
    primary_claim_id TEXT NOT NULL REFERENCES synthesis_claims(claim_id) ON DELETE RESTRICT,
    secondary_claim_id TEXT NOT NULL REFERENCES synthesis_claims(claim_id) ON DELETE RESTRICT,
    description TEXT NOT NULL,
    preservation_rationale TEXT NOT NULL,
    resolution_status TEXT NOT NULL DEFAULT 'UNRESOLVED' CHECK(resolution_status IN (
        'UNRESOLVED',
        'PRESERVED_TENSION',
        'HISTORICAL_DEVELOPMENT',
        'SUPERSEDED'
    )),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(primary_claim_id != secondary_claim_id)
);

CREATE INDEX IF NOT EXISTS idx_synth_tensions_run ON synthesis_tensions(run_id);
CREATE INDEX IF NOT EXISTS idx_synth_tensions_scope ON synthesis_tensions(scope, target_id);
CREATE INDEX IF NOT EXISTS idx_synth_tensions_claims ON synthesis_tensions(primary_claim_id, secondary_claim_id);

-- ----------------------------------------------------------------------------
-- 4. SYNTHESIS CONSTITUENTS (Traceable Bottom-Up Evidence Links)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS synthesis_constituents (
    constituent_link_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES synthesis_runs(run_id) ON DELETE RESTRICT,
    claim_id TEXT NOT NULL REFERENCES synthesis_claims(claim_id) ON DELETE RESTRICT,
    constituent_scope TEXT NOT NULL CHECK(constituent_scope IN ('PERICOPE', 'SECTION', 'BOOK', 'CORPUS', 'CANON')),
    constituent_target_id TEXT NOT NULL,
    constituent_claim_id TEXT,
    constituent_adjudication_verdict_id TEXT REFERENCES adjudicated_verdicts(verdict_id) ON DELETE RESTRICT,
    constituent_graph_node_id TEXT REFERENCES graph_nodes(node_id) ON DELETE RESTRICT,
    constituent_evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    constituent_confidence REAL NOT NULL CHECK(constituent_confidence >= 0.0 AND constituent_confidence <= 1.0),
    is_critical_dependency INTEGER NOT NULL DEFAULT 1 CHECK(is_critical_dependency IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_synth_const_run ON synthesis_constituents(run_id);
CREATE INDEX IF NOT EXISTS idx_synth_const_claim ON synthesis_constituents(claim_id);
CREATE INDEX IF NOT EXISTS idx_synth_const_scope ON synthesis_constituents(constituent_scope, constituent_target_id);
CREATE INDEX IF NOT EXISTS idx_synth_const_adj ON synthesis_constituents(constituent_adjudication_verdict_id);
CREATE INDEX IF NOT EXISTS idx_synth_const_node ON synthesis_constituents(constituent_graph_node_id);

-- ----------------------------------------------------------------------------
-- 5. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

-- A. Synthesis Runs: status transition only to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_synth_runs_upd
BEFORE UPDATE ON synthesis_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_runs status may only transition to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.scope != NEW.scope
       OR OLD.target_id != NEW.target_id
       OR OLD.parent_scope IS NOT NEW.parent_scope
       OR OLD.parent_target_id IS NOT NEW.parent_target_id
       OR OLD.synthesizer_id != NEW.synthesizer_id
       OR OLD.synthesizer_version != NEW.synthesizer_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.aggregate_confidence != NEW.aggregate_confidence
       OR OLD.is_exact_reproducible != NEW.is_exact_reproducible
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'COMPLETED' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_synth_runs_del
BEFORE DELETE ON synthesis_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_runs are immutable and cannot be deleted.');
END;

-- B. Synthesis Claims: status transition only to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_synth_claims_upd
BEFORE UPDATE ON synthesis_claims
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_claims status may only transition to SUPERSEDED.')
    WHERE OLD.claim_id != NEW.claim_id
       OR OLD.run_id != NEW.run_id
       OR OLD.scope != NEW.scope
       OR OLD.target_id != NEW.target_id
       OR OLD.claim_tier != NEW.claim_tier
       OR OLD.primary_evidence_class != NEW.primary_evidence_class
       OR OLD.claim_text != NEW.claim_text
       OR OLD.synthesized_confidence != NEW.synthesized_confidence
       OR OLD.weakest_constituent_confidence != NEW.weakest_constituent_confidence
       OR OLD.authorial_context != NEW.authorial_context
       OR OLD.is_harmonized != NEW.is_harmonized
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.epistemic_status IN ('CONVERGENT', 'TENSION', 'COMPETING', 'UNRESOLVED') AND NEW.epistemic_status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_synth_claims_del
BEFORE DELETE ON synthesis_claims
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_claims are immutable and cannot be deleted.');
END;

-- C. Synthesis Tensions: status transition only to SUPERSEDED or PRESERVED_TENSION / HISTORICAL_DEVELOPMENT
CREATE TRIGGER IF NOT EXISTS trg_immut_synth_tensions_upd
BEFORE UPDATE ON synthesis_tensions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_tensions fields are immutable except resolution_status.')
    WHERE OLD.tension_id != NEW.tension_id
       OR OLD.run_id != NEW.run_id
       OR OLD.scope != NEW.scope
       OR OLD.target_id != NEW.target_id
       OR OLD.tension_type != NEW.tension_type
       OR OLD.primary_claim_id != NEW.primary_claim_id
       OR OLD.secondary_claim_id != NEW.secondary_claim_id
       OR OLD.description != NEW.description
       OR OLD.preservation_rationale != NEW.preservation_rationale
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.resolution_status = 'UNRESOLVED' AND NEW.resolution_status IN ('PRESERVED_TENSION', 'HISTORICAL_DEVELOPMENT', 'SUPERSEDED'));
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_synth_tensions_del
BEFORE DELETE ON synthesis_tensions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_tensions are immutable and cannot be deleted.');
END;

-- D. Synthesis Constituents: strictly immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_synth_const_upd
BEFORE UPDATE ON synthesis_constituents
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_constituents are strictly immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_synth_const_del
BEFORE DELETE ON synthesis_constituents
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: synthesis_constituents are strictly immutable.');
END;
