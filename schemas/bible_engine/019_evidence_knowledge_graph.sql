-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 019: CROSS-PERICOPE EVIDENCE KNOWLEDGE GRAPH (Task 3.6)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principle:
--   THE KNOWLEDGE GRAPH IS AN EPISTEMIC DEPENDENCY STRUCTURE,
--   NOT A TRUTH-RANKING ENGINE.
--
-- Critical Epistemic Firewalls:
--   1. DAG Invariant: Cycles in dependency paths are strictly forbidden.
--   2. Connectivity != Certainty: Graph connectivity is NOT evidence strength.
--   3. Weakest-Link Propagation: PathConfidence <= min(critical edge confidences).
--   4. No Confidence Inflation: Confidence cannot be summed, averaged, or escalated.
--   5. Evidence Tier Protection: E0-E12 and T0-T4 cannot be silently upgraded.
--   6. Anti-Suppression: CONTRADICTS, COMPETING, and UNRESOLVED edges are preserved.
--   7. Identity Firewall: EQUATED_WITH requires explicit justification and provenance.
--   8. Reception Firewall: E11/E12 reception cannot masquerade as authorial intent (E0-E5).
--   9. Complete Provenance: All nodes and edges must link to cryptographic provenance.
--   10. Immutability: Nodes and edges are immutable historical records; supersession only.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. GRAPH RUNS (Execution & Build Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS graph_runs (
    run_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    graph_builder_id TEXT NOT NULL,
    graph_builder_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_graph_runs_prov ON graph_runs(provenance_id);
CREATE INDEX IF NOT EXISTS idx_graph_runs_ver ON graph_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_graph_runs_status ON graph_runs(status);

-- ----------------------------------------------------------------------------
-- 2. GRAPH NODES (Heterogeneous Knowledge & Epistemic Entities)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS graph_nodes (
    node_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES graph_runs(run_id) ON DELETE RESTRICT,
    node_type TEXT NOT NULL CHECK(node_type IN (
        'PERICOPE',
        'PASSAGE',
        'ENTITY',
        'TOKEN',
        'CLAIM',
        'EVIDENCE',
        'HYPOTHESIS',
        'ADJUDICATION_VERDICT',
        'CONFLICT_RECORD',
        'RECEPTION_RECORD',
        'INTERTEXTUAL_RECORD',
        'DIACHRONIC_RECORD'
    )),
    reference_id TEXT NOT NULL,
    label TEXT NOT NULL,
    evidence_class TEXT CHECK(evidence_class IS NULL OR evidence_class IN (
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
    claim_tier TEXT CHECK(claim_tier IS NULL OR claim_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM'
    )),
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    base_confidence REAL NOT NULL DEFAULT 1.0 CHECK(base_confidence >= 0.0 AND base_confidence <= 1.0),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUPERSEDED', 'DEPRECATED')),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_run ON graph_nodes(run_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_ref ON graph_nodes(reference_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_peri ON graph_nodes(pericope_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_pas ON graph_nodes(passage_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_ev_class ON graph_nodes(evidence_class);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_tier ON graph_nodes(claim_tier);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_status ON graph_nodes(status);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_prov ON graph_nodes(provenance_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_ver ON graph_nodes(version_id);

-- ----------------------------------------------------------------------------
-- 3. GRAPH EDGES (Directed Epistemic & Relational Assertions)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS graph_edges (
    edge_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES graph_runs(run_id) ON DELETE RESTRICT,
    source_node_id TEXT NOT NULL REFERENCES graph_nodes(node_id) ON DELETE RESTRICT,
    target_node_id TEXT NOT NULL REFERENCES graph_nodes(node_id) ON DELETE RESTRICT,
    edge_type TEXT NOT NULL CHECK(edge_type IN (
        'SUPPORTS',
        'CONTRADICTS',
        'EVALUATES',
        'SUPERSEDES',
        'ALLUDES_TO',
        'CITES',
        'DERIVED_FROM',
        'DIACHRONIC_PARALLEL',
        'EQUATED_WITH'
    )),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
    epistemic_confidence REAL NOT NULL CHECK(epistemic_confidence >= 0.0 AND epistemic_confidence <= 1.0),
    evidence_class TEXT CHECK(evidence_class IS NULL OR evidence_class IN (
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
    claim_tier TEXT CHECK(claim_tier IS NULL OR claim_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM'
    )),
    is_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence IN (0, 1)),
    epistemic_status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(epistemic_status IN ('ACTIVE', 'COMPETING', 'UNRESOLVED', 'SUPERSEDED')),
    identity_justification TEXT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(source_node_id != target_node_id),
    CHECK(
        (edge_type != 'EQUATED_WITH') OR
        (identity_justification IS NOT NULL AND length(trim(identity_justification)) > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_run ON graph_edges(run_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_src ON graph_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_tgt ON graph_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_src_tgt ON graph_edges(source_node_id, target_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_graph_edges_status ON graph_edges(epistemic_status);
CREATE INDEX IF NOT EXISTS idx_graph_edges_counter ON graph_edges(is_counter_evidence);
CREATE INDEX IF NOT EXISTS idx_graph_edges_prov ON graph_edges(provenance_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_ver ON graph_edges(version_id);

-- ----------------------------------------------------------------------------
-- 4. GRAPH EDGE EVIDENCE LINKS (Evidence Grounding Junction)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS graph_edge_evidence_links (
    link_id TEXT PRIMARY KEY,
    edge_id TEXT NOT NULL REFERENCES graph_edges(edge_id) ON DELETE RESTRICT,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    adjudication_verdict_id TEXT REFERENCES adjudicated_verdicts(verdict_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(evidence_id IS NOT NULL OR adjudication_verdict_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_graph_link_edge ON graph_edge_evidence_links(edge_id);
CREATE INDEX IF NOT EXISTS idx_graph_link_ev ON graph_edge_evidence_links(evidence_id);
CREATE INDEX IF NOT EXISTS idx_graph_link_verd ON graph_edge_evidence_links(adjudication_verdict_id);

-- ----------------------------------------------------------------------------
-- 5. IMMUTABILITY & LIFECYCLE AUDIT TRIGGERS
-- ----------------------------------------------------------------------------

-- A. Graph Runs: only COMPLETED -> SUPERSEDED transition allowed
CREATE TRIGGER IF NOT EXISTS trg_immut_graph_run_upd
BEFORE UPDATE ON graph_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_runs status may only transition from COMPLETED to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.version_id != NEW.version_id
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.graph_builder_id != NEW.graph_builder_id
       OR OLD.graph_builder_version != NEW.graph_builder_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.is_exact_reproducible != NEW.is_exact_reproducible
       OR OLD.created_at != NEW.created_at
       OR NOT (OLD.status = 'COMPLETED' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_graph_run_del
BEFORE DELETE ON graph_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_runs are immutable and cannot be deleted.');
END;

-- B. Graph Nodes: only ACTIVE -> SUPERSEDED transition allowed
CREATE TRIGGER IF NOT EXISTS trg_immut_graph_node_upd
BEFORE UPDATE ON graph_nodes
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_nodes status may only transition from ACTIVE to SUPERSEDED.')
    WHERE OLD.node_id != NEW.node_id
       OR OLD.run_id != NEW.run_id
       OR OLD.node_type != NEW.node_type
       OR OLD.reference_id != NEW.reference_id
       OR OLD.label != NEW.label
       OR OLD.evidence_class IS NOT NEW.evidence_class
       OR OLD.claim_tier IS NOT NEW.claim_tier
       OR OLD.pericope_id IS NOT NEW.pericope_id
       OR OLD.passage_id IS NOT NEW.passage_id
       OR OLD.base_confidence != NEW.base_confidence
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_graph_node_del
BEFORE DELETE ON graph_nodes
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_nodes are immutable and cannot be deleted.');
END;

-- C. Graph Edges: only ACTIVE/COMPETING/UNRESOLVED -> SUPERSEDED transition allowed
CREATE TRIGGER IF NOT EXISTS trg_immut_graph_edge_upd
BEFORE UPDATE ON graph_edges
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_edges status may only transition to SUPERSEDED.')
    WHERE OLD.edge_id != NEW.edge_id
       OR OLD.run_id != NEW.run_id
       OR OLD.source_node_id != NEW.source_node_id
       OR OLD.target_node_id != NEW.target_node_id
       OR OLD.edge_type != NEW.edge_type
       OR OLD.weight != NEW.weight
       OR OLD.epistemic_confidence != NEW.epistemic_confidence
       OR OLD.evidence_class IS NOT NEW.evidence_class
       OR OLD.claim_tier IS NOT NEW.claim_tier
       OR OLD.is_counter_evidence != NEW.is_counter_evidence
       OR OLD.identity_justification IS NOT NEW.identity_justification
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.epistemic_status IN ('ACTIVE', 'COMPETING', 'UNRESOLVED') AND NEW.epistemic_status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_graph_edge_del
BEFORE DELETE ON graph_edges
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_edges are immutable and cannot be deleted.');
END;

-- D. Edge Evidence Links: completely immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_graph_link_upd
BEFORE UPDATE ON graph_edge_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_edge_evidence_links are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_graph_link_del
BEFORE DELETE ON graph_edge_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: graph_edge_evidence_links are immutable.');
END;
