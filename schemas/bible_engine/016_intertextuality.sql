-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 016: INTERTEXTUAL ANALYSIS ENGINE (Task 3.3)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principle:
--   NO CONCLUSION MAY OUTRUN ITS EVIDENCE.
--
-- Critical Epistemic Firewalls:
--   1. Lexical similarity != intertextuality
--   2. Thematic similarity != intertextuality
--   3. Chronology != textual dependence
--   4. Same wording != automatic quotation
--   5. Shared tradition != direct quotation
--   6. E9 historical-linguistic parallel != E10 intertextual relationship
--   7. Translation != original-source identity
--   8. Reception source != authorial source
--   9. Entity identity != textual dependence
--   10. Unknown direction must remain UNKNOWN
--   11. AI-generated proposal != primary intertextual evidence
--   12. Modern commentary != ancient source
--   13. Confidence cannot upgrade evidence
--   14. Retrieval ranking cannot select truth
--   15. Competing hypotheses must remain preserved
--   16. Counter-evidence cannot be silently discarded
--   17. Direct quotation requires explicit evidence
--   18. Intertextual relation cannot be established solely by chronology
--   19. Intertextual claim cannot silently become theological claim
--   20. Unverified external identifier cannot be treated as verified
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. INTERTEXTUAL ANALYSIS RUNS (Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_runs (
    run_id TEXT PRIMARY KEY,
    target_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    target_pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    target_source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
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
    metadata_json TEXT,

    CHECK(target_passage_id IS NOT NULL OR target_pericope_id IS NOT NULL OR target_source_text_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_it_runs_passage ON intertextual_runs(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_it_runs_pericope ON intertextual_runs(target_pericope_id);
CREATE INDEX IF NOT EXISTS idx_it_runs_version ON intertextual_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_it_runs_provenance ON intertextual_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. INTERTEXTUAL SOURCE METADATA
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_source_metadata (
    source_metadata_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL CHECK(source_type IN (
        'BIBLICAL_PASSAGE',
        'BIBLICAL_PERICOPE',
        'CLAUSE',
        'NON_BIBLICAL_ANCIENT_TEXT',
        'INSCRIPTION',
        'PAPYRUS',
        'MANUSCRIPT_WITNESS',
        'ANCIENT_TRANSLATION',
        'ANCIENT_COMMENTARY_RECEPTION'
    )),
    canonical_reference TEXT NOT NULL,
    source_language TEXT NOT NULL CHECK(source_language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'OTHER', 'LATIN', 'SYRIAC', 'COPTIC', 'AKKADIAN', 'UGARITIC', 'EGYPTIAN'
    )),
    is_translation INTEGER NOT NULL DEFAULT 0 CHECK(is_translation IN (0, 1)),
    original_language TEXT,
    dating_period TEXT,
    approximate_date_bce_ce INTEGER,
    is_modern_commentary INTEGER NOT NULL DEFAULT 0 CHECK(is_modern_commentary = 0),
    external_identifier TEXT NOT NULL,
    external_identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(external_identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Translation cannot masquerade as original language
    CHECK(is_translation = 0 OR (original_language IS NOT NULL AND original_language != source_language)),
    -- Epistemic Firewall: Modern commentary cannot be ancient source
    CHECK(is_modern_commentary = 0)
);

CREATE INDEX IF NOT EXISTS idx_ism_type ON intertextual_source_metadata(source_type);
CREATE INDEX IF NOT EXISTS idx_ism_lang ON intertextual_source_metadata(source_language);
CREATE INDEX IF NOT EXISTS idx_ism_ext_id ON intertextual_source_metadata(external_identifier);

-- ----------------------------------------------------------------------------
-- 3. INTERTEXTUAL RELATIONSHIPS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_relationships (
    relationship_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES intertextual_runs(run_id) ON DELETE RESTRICT,
    target_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    target_pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    source_metadata_id TEXT NOT NULL REFERENCES intertextual_source_metadata(source_metadata_id) ON DELETE RESTRICT,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN (
        'TEXTUAL_REUSE',
        'DIRECT_QUOTATION',
        'STRONG_ALLUSION',
        'PROBABLE_ALLUSION',
        'POSSIBLE_ALLUSION',
        'LEXICAL_PARALLEL',
        'THEMATIC_PARALLEL',
        'TRADITIONAL_PARALLEL',
        'UNKNOWN'
    )),
    epistemic_classification TEXT NOT NULL CHECK(epistemic_classification IN (
        'DIRECT_QUOTATION',
        'STRONG_ALLUSION',
        'PROBABLE_ALLUSION',
        'POSSIBLE_ALLUSION',
        'LEXICAL_PARALLEL',
        'THEMATIC_PARALLEL',
        'NO_ESTABLISHED_RELATION'
    )),
    direction TEXT NOT NULL DEFAULT 'UNKNOWN' CHECK(direction IN (
        'SOURCE_TO_TARGET',
        'TARGET_TO_SOURCE',
        'BIDIRECTIONAL',
        'UNKNOWN'
    )),
    status TEXT NOT NULL CHECK(status IN (
        'PROPOSED',
        'POSSIBLE',
        'PROBABLE',
        'ESTABLISHED',
        'DISPUTED',
        'REJECTED',
        'UNKNOWN'
    )),
    target_language TEXT NOT NULL CHECK(target_language IN ('GREEK', 'HEBREW', 'ARAMAIC', 'OTHER')),
    source_language TEXT NOT NULL CHECK(source_language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'OTHER', 'LATIN', 'SYRIAC', 'COPTIC', 'AKKADIAN', 'UGARITIC', 'EGYPTIAN'
    )),
    is_translation_mediated INTEGER NOT NULL DEFAULT 0 CHECK(is_translation_mediated IN (0, 1)),
    has_explicit_quotation_formula INTEGER NOT NULL DEFAULT 0 CHECK(has_explicit_quotation_formula IN (0, 1)),
    quotation_formula_text TEXT,
    chronological_precedence_demonstrated INTEGER NOT NULL DEFAULT 0 CHECK(chronological_precedence_demonstrated IN (0, 1)),
    solely_chronological_basis INTEGER NOT NULL DEFAULT 0 CHECK(solely_chronological_basis = 0),
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated = 0),
    is_reception_history_source INTEGER NOT NULL DEFAULT 0 CHECK(is_reception_history_source IN (0, 1)),
    entity_agreement_only INTEGER NOT NULL DEFAULT 0 CHECK(entity_agreement_only IN (0, 1)),
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNSUPPORTED')),
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    retrieval_rank INTEGER,
    retrieval_score REAL,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Direct quotation requires explicit quotation evidence / formula or high confidence
    CHECK((relationship_type != 'DIRECT_QUOTATION' AND epistemic_classification != 'DIRECT_QUOTATION') OR has_explicit_quotation_formula = 1 OR confidence IN ('CERTAIN', 'VERY_HIGH', 'HIGH')),
    -- Epistemic Firewall: Shared tradition != direct quotation
    CHECK(relationship_type != 'TRADITIONAL_PARALLEL' OR epistemic_classification != 'DIRECT_QUOTATION'),
    -- Epistemic Firewall: Lexical parallel cannot assert direct quotation or strong allusion
    CHECK(relationship_type != 'LEXICAL_PARALLEL' OR epistemic_classification NOT IN ('DIRECT_QUOTATION', 'STRONG_ALLUSION')),
    -- Epistemic Firewall: Thematic parallel cannot assert direct quotation or strong allusion
    CHECK(relationship_type != 'THEMATIC_PARALLEL' OR epistemic_classification NOT IN ('DIRECT_QUOTATION', 'STRONG_ALLUSION', 'PROBABLE_ALLUSION')),
    -- Epistemic Firewall: Entity agreement alone cannot assert quotation or strong allusion
    CHECK(entity_agreement_only = 0 OR epistemic_classification NOT IN ('DIRECT_QUOTATION', 'STRONG_ALLUSION', 'PROBABLE_ALLUSION')),
    -- Epistemic Firewall: Reception source cannot be authorial source
    CHECK(is_reception_history_source = 0 OR direction != 'SOURCE_TO_TARGET'),
    -- Epistemic Firewall: Chronology alone cannot establish relation
    CHECK(solely_chronological_basis = 0),
    -- Epistemic Firewall: AI output cannot be primary evidence
    CHECK(is_ai_generated = 0)
);

CREATE INDEX IF NOT EXISTS idx_itr_run ON intertextual_relationships(run_id);
CREATE INDEX IF NOT EXISTS idx_itr_target_passage ON intertextual_relationships(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_itr_source_meta ON intertextual_relationships(source_metadata_id);
CREATE INDEX IF NOT EXISTS idx_itr_rel_type ON intertextual_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_itr_epistemic ON intertextual_relationships(epistemic_classification);
CREATE INDEX IF NOT EXISTS idx_itr_status ON intertextual_relationships(status);
CREATE INDEX IF NOT EXISTS idx_itr_evidence ON intertextual_relationships(evidence_id);

-- ----------------------------------------------------------------------------
-- 4. INTERTEXTUAL OBSERVATIONS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_observations (
    observation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES intertextual_runs(run_id) ON DELETE RESTRICT,
    relationship_id TEXT NOT NULL REFERENCES intertextual_relationships(relationship_id) ON DELETE RESTRICT,
    observation_type TEXT NOT NULL CHECK(observation_type IN (
        'WORDING_OVERLAP',
        'PHRASE_OVERLAP',
        'RARE_LEXICAL_SEQUENCE',
        'SYNTACTIC_CORRESPONDENCE',
        'STRUCTURAL_CORRESPONDENCE',
        'THEMATIC_CORRESPONDENCE',
        'DISTINCTIVE_MOTIF',
        'NARRATIVE_CORRESPONDENCE',
        'QUOTATION_FORMULA',
        'CITATION_FORMULA',
        'CONTEXTUAL_CORRESPONDENCE',
        'CANONICAL_PLACEMENT',
        'SOURCE_AVAILABILITY',
        'HISTORICAL_PLAUSIBILITY'
    )),
    observation_text TEXT NOT NULL,
    shared_elements TEXT,
    is_theological_claim INTEGER NOT NULL DEFAULT 0 CHECK(is_theological_claim = 0),
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Intertextual observation cannot become theological claim
    CHECK(is_theological_claim = 0)
);

CREATE INDEX IF NOT EXISTS idx_ito_run ON intertextual_observations(run_id);
CREATE INDEX IF NOT EXISTS idx_ito_rel ON intertextual_observations(relationship_id);
CREATE INDEX IF NOT EXISTS idx_ito_type ON intertextual_observations(observation_type);
CREATE INDEX IF NOT EXISTS idx_ito_evidence ON intertextual_observations(evidence_id);

-- ----------------------------------------------------------------------------
-- 5. INTERTEXTUAL HYPOTHESES (Multi-Candidate & Competing Hypotheses)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES intertextual_runs(run_id) ON DELETE RESTRICT,
    target_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    hypothesis_code TEXT NOT NULL,
    hypothesis_description TEXT NOT NULL,
    proposed_relationship_type TEXT NOT NULL CHECK(proposed_relationship_type IN (
        'TEXTUAL_REUSE',
        'DIRECT_QUOTATION',
        'STRONG_ALLUSION',
        'PROBABLE_ALLUSION',
        'POSSIBLE_ALLUSION',
        'LEXICAL_PARALLEL',
        'THEMATIC_PARALLEL',
        'TRADITIONAL_PARALLEL',
        'NO_ESTABLISHED_RELATION',
        'UNKNOWN'
    )),
    source_metadata_id TEXT REFERENCES intertextual_source_metadata(source_metadata_id) ON DELETE RESTRICT,
    is_primary INTEGER NOT NULL DEFAULT 0 CHECK(is_primary IN (0, 1)),
    status TEXT NOT NULL DEFAULT 'PROPOSED' CHECK(status IN (
        'PROPOSED', 'POSSIBLE', 'PROBABLE', 'ESTABLISHED', 'DISPUTED', 'REJECTED', 'UNKNOWN'
    )),
    retrieval_rank INTEGER,
    retrieval_score REAL,
    retrieval_forced_winner INTEGER NOT NULL DEFAULT 0 CHECK(retrieval_forced_winner = 0),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Retrieval ranking cannot force a single winner as truth
    CHECK(retrieval_forced_winner = 0)
);

CREATE INDEX IF NOT EXISTS idx_ith_run ON intertextual_hypotheses(run_id);
CREATE INDEX IF NOT EXISTS idx_ith_passage ON intertextual_hypotheses(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_ith_status ON intertextual_hypotheses(status);

-- ----------------------------------------------------------------------------
-- 6. INTERTEXTUAL EVIDENCE LINKS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS intertextual_evidence_links (
    link_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES intertextual_runs(run_id) ON DELETE RESTRICT,
    relationship_id TEXT REFERENCES intertextual_relationships(relationship_id) ON DELETE RESTRICT,
    hypothesis_id TEXT REFERENCES intertextual_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    evidence_class TEXT NOT NULL CHECK(evidence_class = 'E10_INTERTEXTUAL'),
    stance TEXT NOT NULL CHECK(stance IN (
        'SUPPORT',
        'CONTRADICT',
        'QUALIFY',
        'LIMIT',
        'REFINE'
    )),
    weight REAL NOT NULL DEFAULT 1.0 CHECK(weight >= 0.0 AND weight <= 1.0),
    is_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence IN (0, 1)),
    reasoning TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Floating evidence links not permitted
    CHECK(relationship_id IS NOT NULL OR hypothesis_id IS NOT NULL),

    -- Epistemic Firewall: Counter-evidence consistency
    CHECK((stance != 'CONTRADICT' AND stance != 'LIMIT') OR is_counter_evidence = 1)
);

CREATE INDEX IF NOT EXISTS idx_itel_run ON intertextual_evidence_links(run_id);
CREATE INDEX IF NOT EXISTS idx_itel_rel ON intertextual_evidence_links(relationship_id);
CREATE INDEX IF NOT EXISTS idx_itel_hyp ON intertextual_evidence_links(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_itel_ev ON intertextual_evidence_links(evidence_id);

-- ----------------------------------------------------------------------------
-- 7. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_it_runs_no_update
BEFORE UPDATE ON intertextual_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_runs is immutable except status transition from COMPLETED to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.target_passage_id IS NOT NEW.target_passage_id
       OR OLD.target_pericope_id IS NOT NEW.target_pericope_id
       OR OLD.target_source_text_id IS NOT NEW.target_source_text_id
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

CREATE TRIGGER IF NOT EXISTS trg_it_runs_no_delete
BEFORE DELETE ON intertextual_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_runs is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ism_no_update
BEFORE UPDATE ON intertextual_source_metadata
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_source_metadata is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ism_no_delete
BEFORE DELETE ON intertextual_source_metadata
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_source_metadata is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_itr_no_update
BEFORE UPDATE ON intertextual_relationships
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_relationships is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_itr_no_delete
BEFORE DELETE ON intertextual_relationships
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_relationships is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ito_no_update
BEFORE UPDATE ON intertextual_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_observations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ito_no_delete
BEFORE DELETE ON intertextual_observations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_observations is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ith_no_update
BEFORE UPDATE ON intertextual_hypotheses
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_hypotheses is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_ith_no_delete
BEFORE DELETE ON intertextual_hypotheses
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_hypotheses is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_itel_no_update
BEFORE UPDATE ON intertextual_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Mutation forbidden: intertextual_evidence_links is immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_itel_no_delete
BEFORE DELETE ON intertextual_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'Deletion forbidden: intertextual_evidence_links is immutable.');
END;
