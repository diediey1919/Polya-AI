-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 015: HISTORICAL-LINGUISTIC & DIACHRONIC ENGINE (Task 3.2)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   HISTORICAL/LINGUISTIC PARALLEL != INTERTEXTUAL DEPENDENCE
--   LEXICAL SIMILARITY != BORROWING
--   BORROWING != THEOLOGICAL INFLUENCE
--   CHRONOLOGICAL PROXIMITY != CAUSATION
--   SHARED ROOT != SAME HISTORICAL SOURCE
--   LATER LINGUISTIC FORM != AUTOMATIC EARLIER READING
--   MODERN LINGUISTIC TERMINOLOGY != ANCIENT AUTHORIAL INTENT
--   AI-GENERATED ETYMOLOGY != PRIMARY EVIDENCE
--   TRANSLATION != HISTORICAL-LINGUISTIC SOURCE EVIDENCE
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. HISTORICAL-LINGUISTIC ANALYSIS RUNS (Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS historical_linguistic_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    token_start_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    token_end_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_hl_runs_passage ON historical_linguistic_runs(passage_id);
CREATE INDEX IF NOT EXISTS idx_hl_runs_pericope ON historical_linguistic_runs(pericope_id);
CREATE INDEX IF NOT EXISTS idx_hl_runs_version ON historical_linguistic_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_hl_runs_provenance ON historical_linguistic_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. DIACHRONIC STRATA & LINGUISTIC PERIOD CLASSIFICATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS diachronic_strata (
    stratum_id TEXT PRIMARY KEY,
    language TEXT NOT NULL CHECK(language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    period_code TEXT NOT NULL,
    period_name TEXT NOT NULL,
    approximate_start_bce_ce INTEGER,
    approximate_end_bce_ce INTEGER,
    description TEXT NOT NULL,
    is_controlled INTEGER NOT NULL DEFAULT 1 CHECK(is_controlled IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    UNIQUE(language, period_code)
);

CREATE INDEX IF NOT EXISTS idx_strata_lang_period ON diachronic_strata(language, period_code);

-- ----------------------------------------------------------------------------
-- 3. TOKEN / LEXEME DIACHRONIC ANNOTATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS diachronic_annotations (
    annotation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES historical_linguistic_runs(run_id) ON DELETE RESTRICT,
    token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    lemma_id TEXT REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
    stratum_id TEXT NOT NULL REFERENCES diachronic_strata(stratum_id) ON DELETE RESTRICT,
    classification_confidence TEXT NOT NULL CHECK(classification_confidence IN ('CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'UNCERTAIN')),
    is_period_uncertain INTEGER NOT NULL DEFAULT 0 CHECK(is_period_uncertain IN (0, 1)),
    linguistic_features TEXT NOT NULL,
    notes TEXT,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_da_run ON diachronic_annotations(run_id);
CREATE INDEX IF NOT EXISTS idx_da_token ON diachronic_annotations(token_id);
CREATE INDEX IF NOT EXISTS idx_da_lemma ON diachronic_annotations(lemma_id);
CREATE INDEX IF NOT EXISTS idx_da_stratum ON diachronic_annotations(stratum_id);
CREATE INDEX IF NOT EXISTS idx_da_evidence ON diachronic_annotations(evidence_id);

-- ----------------------------------------------------------------------------
-- 4. LOANWORD & BORROWING REGISTRY
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS loanword_registry (
    loanword_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES historical_linguistic_runs(run_id) ON DELETE RESTRICT,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL CHECK(target_language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    lexeme TEXT NOT NULL,
    lemma_id TEXT REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
    candidate_etymon TEXT NOT NULL,
    borrowing_type TEXT NOT NULL CHECK(borrowing_type IN (
        'DIRECT_LOAN',
        'CALQUE_LOAN_TRANSLATION',
        'SEMANTIC_LOAN',
        'MORPHOLOGICAL_ADAPTATION',
        'PHONOLOGICAL_BORROWING',
        'UNVERIFIED'
    )),
    chronological_range TEXT NOT NULL,
    external_reference TEXT NOT NULL,
    external_identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(external_identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    state TEXT NOT NULL CHECK(state IN (
        'PROPOSED',
        'POSSIBLE',
        'PROBABLE',
        'ESTABLISHED',
        'DISPUTED',
        'REJECTED',
        'UNKNOWN'
    )),
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNSUPPORTED')),
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated = 0),
    is_translation_derived INTEGER NOT NULL DEFAULT 0 CHECK(is_translation_derived = 0),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,
    CHECK(borrowing_type != 'UNVERIFIED' OR state != 'ESTABLISHED')
);

CREATE INDEX IF NOT EXISTS idx_lr_run ON loanword_registry(run_id);
CREATE INDEX IF NOT EXISTS idx_lr_target_lang ON loanword_registry(target_language);
CREATE INDEX IF NOT EXISTS idx_lr_state ON loanword_registry(state);
CREATE INDEX IF NOT EXISTS idx_lr_evidence ON loanword_registry(evidence_id);

-- ----------------------------------------------------------------------------
-- 5. ETYMOLOGICAL RELATIONSHIP RECORDS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS etymological_relations (
    relation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES historical_linguistic_runs(run_id) ON DELETE RESTRICT,
    lexeme_id TEXT,
    lexeme_text TEXT NOT NULL,
    target_language TEXT NOT NULL CHECK(target_language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    related_lexeme_text TEXT NOT NULL,
    source_language TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN (
        'COGNATE',
        'DIRECT_DERIVATION',
        'SHARED_ROOT',
        'BORROWING',
        'CALQUE',
        'INDEPENDENT_PARALLEL',
        'FOLK_ETYMOLOGY',
        'SPURIOUS_SIMILARITY',
        'UNKNOWN'
    )),
    state TEXT NOT NULL CHECK(state IN (
        'PROPOSED',
        'POSSIBLE',
        'PROBABLE',
        'ESTABLISHED',
        'DISPUTED',
        'REJECTED',
        'UNKNOWN'
    )),
    is_causal_relation INTEGER NOT NULL DEFAULT 0 CHECK(is_causal_relation IN (0, 1)),
    is_same_historical_source INTEGER NOT NULL DEFAULT 0 CHECK(is_same_historical_source IN (0, 1)),
    reconstruction_method TEXT NOT NULL,
    lexicon_source TEXT NOT NULL,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated = 0),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Shared root does NOT equal same historical source
    CHECK(relationship_type != 'SHARED_ROOT' OR is_same_historical_source = 0),
    -- Epistemic Firewall: Spurious or superficial similarity cannot assert causal relation
    CHECK(relationship_type != 'SPURIOUS_SIMILARITY' OR (is_causal_relation = 0 AND state IN ('REJECTED', 'DISPUTED')))
);

CREATE INDEX IF NOT EXISTS idx_er_run ON etymological_relations(run_id);
CREATE INDEX IF NOT EXISTS idx_er_state ON etymological_relations(state);
CREATE INDEX IF NOT EXISTS idx_er_type ON etymological_relations(relationship_type);
CREATE INDEX IF NOT EXISTS idx_er_evidence ON etymological_relations(evidence_id);

-- ----------------------------------------------------------------------------
-- 6. EPIGRAPHIC / PAPYROLOGICAL PARALLEL RECORDS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS epigraphic_papyrological_parallels (
    parallel_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES historical_linguistic_runs(run_id) ON DELETE RESTRICT,
    token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    parallel_corpus TEXT NOT NULL CHECK(parallel_corpus IN (
        'EPIGRAPHIC_INSCRIPTION',
        'DOCUMENTARY_PAPYRUS',
        'OSTRACON',
        'COIN_LEGEND',
        'CLASSICAL_LITERATURE',
        'RABBINIC_CORPUS',
        'DEAD_SEA_SCROLL',
        'TARGUM',
        'SEPTUAGINT_PAPYRUS'
    )),
    artifact_siglum TEXT NOT NULL,
    geographic_provenance TEXT,
    dating_period TEXT NOT NULL,
    parallel_text TEXT NOT NULL,
    linguistic_significance TEXT NOT NULL,
    is_intertextual_dependence INTEGER NOT NULL DEFAULT 0 CHECK(is_intertextual_dependence = 0),
    evidence_class TEXT NOT NULL DEFAULT 'E9_HISTORICAL_LINGUISTIC' CHECK(evidence_class = 'E9_HISTORICAL_LINGUISTIC'),
    external_identifier TEXT NOT NULL,
    external_identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(external_identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_epp_run ON epigraphic_papyrological_parallels(run_id);
CREATE INDEX IF NOT EXISTS idx_epp_corpus ON epigraphic_papyrological_parallels(parallel_corpus);
CREATE INDEX IF NOT EXISTS idx_epp_passage ON epigraphic_papyrological_parallels(passage_id);
CREATE INDEX IF NOT EXISTS idx_epp_evidence ON epigraphic_papyrological_parallels(evidence_id);

-- ----------------------------------------------------------------------------
-- 7. HISTORICAL LINGUISTIC OBSERVATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS historical_linguistic_observations (
    observation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES historical_linguistic_runs(run_id) ON DELETE RESTRICT,
    passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE RESTRICT,
    observation_scope TEXT NOT NULL CHECK(observation_scope IN ('TOKEN', 'LEXEME', 'SYNTACTIC_CONSTRUCTION', 'PASSAGE', 'PERICOPE')),
    evidence_scope TEXT NOT NULL CHECK(evidence_scope IN ('INTERNAL_LINGUISTIC', 'EXTERNAL_HISTORICAL')),
    observation_title TEXT NOT NULL,
    observation_text TEXT NOT NULL,
    chronological_proximity_noted TEXT,
    asserts_historical_causation INTEGER NOT NULL DEFAULT 0 CHECK(asserts_historical_causation = 0),
    asserts_theological_influence INTEGER NOT NULL DEFAULT 0 CHECK(asserts_theological_influence = 0),
    modern_terminology_imposed INTEGER NOT NULL DEFAULT 0 CHECK(modern_terminology_imposed = 0),
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    claim_id TEXT REFERENCES claims(claim_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_hlo_run ON historical_linguistic_observations(run_id);
CREATE INDEX IF NOT EXISTS idx_hlo_passage ON historical_linguistic_observations(passage_id);
CREATE INDEX IF NOT EXISTS idx_hlo_scope ON historical_linguistic_observations(observation_scope);
CREATE INDEX IF NOT EXISTS idx_hlo_evscope ON historical_linguistic_observations(evidence_scope);
CREATE INDEX IF NOT EXISTS idx_hlo_evidence ON historical_linguistic_observations(evidence_id);

-- ----------------------------------------------------------------------------
-- 8. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_hl_runs_no_update
BEFORE UPDATE ON historical_linguistic_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: historical_linguistic_runs is immutable except status transition from COMPLETED to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.source_text_id IS NOT NEW.source_text_id
       OR OLD.passage_id IS NOT NEW.passage_id
       OR OLD.pericope_id IS NOT NEW.pericope_id
       OR OLD.token_start_id IS NOT NEW.token_start_id
       OR OLD.token_end_id IS NOT NEW.token_end_id
       OR OLD.version_id != NEW.version_id
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.analyzer_id != NEW.analyzer_id
       OR OLD.analyzer_version != NEW.analyzer_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.is_exact_reproducible != NEW.is_exact_reproducible
       OR OLD.created_at != NEW.created_at
       OR NOT (OLD.status = 'COMPLETED' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_hl_runs_no_delete
BEFORE DELETE ON historical_linguistic_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: historical_linguistic_runs is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_diachronic_strata_no_update
BEFORE UPDATE ON diachronic_strata
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: diachronic_strata is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_diachronic_strata_no_delete
BEFORE DELETE ON diachronic_strata
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: diachronic_strata is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_diachronic_annotations_no_update
BEFORE UPDATE ON diachronic_annotations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: diachronic_annotations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_diachronic_annotations_no_delete
BEFORE DELETE ON diachronic_annotations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: diachronic_annotations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_loanword_registry_no_update
BEFORE UPDATE ON loanword_registry
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: loanword_registry is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_loanword_registry_no_delete
BEFORE DELETE ON loanword_registry
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: loanword_registry is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_etymological_relations_no_update
BEFORE UPDATE ON etymological_relations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: etymological_relations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_etymological_relations_no_delete
BEFORE DELETE ON etymological_relations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: etymological_relations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_epigraphic_parallels_no_update
BEFORE UPDATE ON epigraphic_papyrological_parallels
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: epigraphic_papyrological_parallels is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_epigraphic_parallels_no_delete
BEFORE DELETE ON epigraphic_papyrological_parallels
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: epigraphic_papyrological_parallels is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_hl_obs_no_update
BEFORE UPDATE ON historical_linguistic_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: historical_linguistic_observations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_hl_obs_no_delete
BEFORE DELETE ON historical_linguistic_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: historical_linguistic_observations is immutable.');
END;
