-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 017: RECEPTION HISTORY ENGINE (Task 3.4)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principle:
--   NO CONCLUSION MAY OUTRUN ITS EVIDENCE.
--
-- Critical Epistemic Firewalls:
--   1. Later interpretation != original authorial intent
--   2. Early reception != proof of original meaning
--   3. Patristic interpretation != automatic apostolic interpretation
--   4. Rabbinic interpretation != automatic Second Temple interpretation
--   5. Medieval interpretation != automatic biblical interpretation
--   6. Modern scholarly consensus != textual evidence
--   7. Denominational doctrine != ancient authorial intent
--   8. Chronology != influence
--   9. Citation != interpretation
--   10. Allusion != quotation
--   11. Translation != original source
--   12. Lexical similarity != reception
--   13. Thematic parallel != reception
--   14. Doctrinal formulation != textual reading
--   15. Reception source != authorial source
--   16. Reception history != canonical authority
--   17. Reception history != theological truth
--   18. Majority interpretation != verified fact
--   19. AI-generated summary != primary source
--   20. Modern commentary != historical witness
--   21. External identifier != verified identity
--   22. Confidence score != evidence upgrade
--   23. Temporal direction must not be reversed without evidence
--   24. Counter-evidence cannot be suppressed
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. RECEPTION ANALYSIS RUNS (Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_runs (
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

CREATE INDEX IF NOT EXISTS idx_rec_runs_passage ON reception_runs(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_rec_runs_pericope ON reception_runs(target_pericope_id);
CREATE INDEX IF NOT EXISTS idx_rec_runs_version ON reception_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_rec_runs_provenance ON reception_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 2. RECEPTION ACTORS (Historical Figures, Communities, Authors, Commentators)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_actors (
    actor_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK(actor_type IN (
        'INDIVIDUAL_AUTHOR',
        'CHURCH_FATHER',
        'RABBINIC_SAGE',
        'MEDIEVAL_SCHOLAR',
        'REFORMER',
        'COMMUNITY',
        'COUNCIL_SYNOD',
        'DENOMINATION',
        'MODERN_SCHOLAR',
        'ANONYMOUS_TRADITION'
    )),
    identity_status TEXT NOT NULL DEFAULT 'DEFINITE' CHECK(identity_status IN ('DEFINITE', 'UNCERTAIN', 'ANONYMOUS', 'DISPUTED')),
    historical_era TEXT NOT NULL CHECK(historical_era IN (
        'APOSTOLIC_SUBAPOSTOLIC',
        'PATRISTIC_ANTE_NICENE',
        'PATRISTIC_POST_NICENE',
        'RABBINIC_TANNAITIC',
        'RABBINIC_AMORAIC',
        'MEDIEVAL_BYZANTINE',
        'MEDIEVAL_WESTERN',
        'MEDIEVAL_ISLAMIC_ERA_JUDAISM',
        'REFORMATION_EARLY_MODERN',
        'MODERN_CRITICAL',
        'MODERN_DENOMINATIONAL',
        'UNKNOWN'
    )),
    approximate_start_bce_ce INTEGER,
    approximate_end_bce_ce INTEGER,
    date_precision TEXT NOT NULL DEFAULT 'EXACT' CHECK(date_precision IN ('EXACT', 'DECADE', 'CENTURY', 'CIRCA', 'UNKNOWN')),
    tradition_affiliation TEXT,
    external_identifier TEXT NOT NULL,
    external_identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(external_identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    CHECK(approximate_start_bce_ce IS NULL OR approximate_end_bce_ce IS NULL OR approximate_start_bce_ce <= approximate_end_bce_ce)
);

CREATE INDEX IF NOT EXISTS idx_rec_actors_type ON reception_actors(actor_type);
CREATE INDEX IF NOT EXISTS idx_rec_actors_era ON reception_actors(historical_era);

-- ----------------------------------------------------------------------------
-- 3. RECEPTION SOURCES (Texts, Commentaries, Tractates, Homilies, Epistles, Decrees)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_sources (
    source_id TEXT PRIMARY KEY,
    canonical_work_title TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN (
        'PATRISTIC_HOMILY',
        'PATRISTIC_COMMENTARY',
        'PATRISTIC_TREATISE',
        'PATRISTIC_EPISTLE',
        'RABBINIC_MISHNAH',
        'RABBINIC_TALMUD',
        'RABBINIC_MIDRASH',
        'RABBINIC_TARGUM',
        'MEDIEVAL_GLOSS_COMMENTARY',
        'MEDIEVAL_SCHOLASTIC_SUMMA',
        'REFORMATION_COMMENTARY',
        'REFORMATION_CONFESSION',
        'CREED_COUNCIL_DECREE',
        'LITURGICAL_HYMN_TEXT',
        'MODERN_ACADEMIC_COMMENTARY',
        'MODERN_CRITICAL_MONOGRAPH',
        'DENOMINATIONAL_CATECHISM',
        'ANCIENT_TRANSLATION_SOURCE'
    )),
    primary_actor_id TEXT REFERENCES reception_actors(actor_id) ON DELETE RESTRICT,
    source_language TEXT NOT NULL CHECK(source_language IN (
        'GREEK', 'LATIN', 'HEBREW', 'ARAMAIC', 'SYRIAC', 'COPTIC', 'GEEZ', 'ARMENIAN', 'ARABIC', 'GERMAN', 'FRENCH', 'ENGLISH', 'OTHER'
    )),
    is_translation INTEGER NOT NULL DEFAULT 0 CHECK(is_translation IN (0, 1)),
    original_language TEXT,
    dating_period TEXT,
    approximate_date_bce_ce INTEGER,
    date_precision TEXT NOT NULL DEFAULT 'EXACT' CHECK(date_precision IN ('EXACT', 'DECADE', 'CENTURY', 'CIRCA', 'UNKNOWN')),
    is_modern_commentary INTEGER NOT NULL DEFAULT 0 CHECK(is_modern_commentary IN (0, 1)),
    is_primary_historical_witness INTEGER NOT NULL DEFAULT 1 CHECK(is_primary_historical_witness IN (0, 1)),
    external_identifier TEXT NOT NULL,
    external_identifier_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK(external_identifier_status IN ('VERIFIED', 'UNVERIFIED', 'DISPUTED')),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Translation cannot masquerade as original language
    CHECK(is_translation = 0 OR (original_language IS NOT NULL AND original_language != source_language)),
    -- Epistemic Firewall: Modern commentary cannot claim to be ancient primary witness
    CHECK(NOT (is_modern_commentary = 1 AND is_primary_historical_witness = 1))
);

CREATE INDEX IF NOT EXISTS idx_rec_sources_type ON reception_sources(source_type);
CREATE INDEX IF NOT EXISTS idx_rec_sources_actor ON reception_sources(primary_actor_id);
CREATE INDEX IF NOT EXISTS idx_rec_sources_lang ON reception_sources(source_language);

-- ----------------------------------------------------------------------------
-- 4. RECEPTION RECORDS (Discrete Exegetical Comments / Readings on Passage)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_records (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES reception_runs(run_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES reception_sources(source_id) ON DELETE RESTRICT,
    actor_id TEXT REFERENCES reception_actors(actor_id) ON DELETE RESTRICT,
    target_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    target_pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    witness_passage_reference TEXT NOT NULL,
    citation_text TEXT NOT NULL,
    citation_language TEXT NOT NULL CHECK(citation_language IN (
        'GREEK', 'LATIN', 'HEBREW', 'ARAMAIC', 'SYRIAC', 'COPTIC', 'GEEZ', 'ARMENIAN', 'ARABIC', 'GERMAN', 'FRENCH', 'ENGLISH', 'OTHER'
    )),
    exegetical_method TEXT NOT NULL CHECK(exegetical_method IN (
        'LITERAL_HISTORICAL',
        'ALLEGORICAL_TYPOLOGICAL',
        'MORAL_TROPOLOGICAL',
        'ANAGOGICAL_ESCHATOLOGICAL',
        'MIDRASHIC_PESHER',
        'POLEMICAL_APOLOGETIC',
        'DOGMATIC_SYSTEMATIC',
        'HISTORICAL_CRITICAL',
        'LITERARY_CANONICAL',
        'UNKNOWN'
    )),
    hermeneutical_summary TEXT NOT NULL,
    reception_era TEXT NOT NULL CHECK(reception_era IN (
        'EARLY_RECEPTION',
        'PATRISTIC',
        'RABBINIC',
        'MEDIEVAL',
        'REFORMATION_EARLY_MODERN',
        'MODERN',
        'DENOMINATIONAL',
        'SCHOLARLY',
        'THEOLOGICAL'
    )),
    is_translation_mediated INTEGER NOT NULL DEFAULT 0 CHECK(is_translation_mediated IN (0, 1)),
    translation_language TEXT,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    CHECK(target_passage_id IS NOT NULL OR target_pericope_id IS NOT NULL),
    CHECK(is_translation_mediated = 0 OR translation_language IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_rec_records_run ON reception_records(run_id);
CREATE INDEX IF NOT EXISTS idx_rec_records_source ON reception_records(source_id);
CREATE INDEX IF NOT EXISTS idx_rec_records_actor ON reception_records(actor_id);
CREATE INDEX IF NOT EXISTS idx_rec_records_passage ON reception_records(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_rec_records_pericope ON reception_records(target_pericope_id);
CREATE INDEX IF NOT EXISTS idx_rec_records_evidence ON reception_records(evidence_id);

-- ----------------------------------------------------------------------------
-- 5. RECEPTION CLAIMS (Epistemic Claims Derived from or Evaluating Reception)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_claims (
    claim_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES reception_runs(run_id) ON DELETE RESTRICT,
    record_id TEXT NOT NULL REFERENCES reception_records(record_id) ON DELETE RESTRICT,
    claim_type TEXT NOT NULL CHECK(claim_type IN (
        'RECEPTION_OCCURRENCE',
        'HERMENEUTICAL_READING',
        'INFLUENCE_HYPOTHESIS',
        'TRADITION_CONTINUITY',
        'DOCTRINAL_DEVELOPMENT',
        'RECEPTION_DIVERGENCE',
        'AUTHORIAL_INTENT_PROPOSAL'
    )),
    claim_tier TEXT NOT NULL CHECK(claim_tier IN ('T0_RAW_OBSERVATION', 'T1_LINGUISTIC_FACT', 'T2_CONTEXTUAL_CLAIM', 'T3_INTERPRETIVE_CLAIM', 'T4_THEOLOGICAL_CLAIM')),
    claim_statement TEXT NOT NULL,
    temporal_direction TEXT NOT NULL CHECK(temporal_direction IN (
        'TEXT_TO_RECEPTION',
        'RECEPTION_TO_LATER_RECEPTION',
        'RECEPTION_TO_INTERPRETATION',
        'UNKNOWN'
    )),
    claim_relevance TEXT NOT NULL CHECK(claim_relevance IN (
        'RECEPTION_HISTORY_PRIMARY',
        'AUTHORIAL_INTENT_SECONDARY',
        'THEOLOGICAL_TRADITION_RELEVANT',
        'IRRELEVANT_TO_ORIGINAL_MEANING'
    )),
    is_authorial_intent_equated INTEGER NOT NULL DEFAULT 0 CHECK(is_authorial_intent_equated = 0),
    is_theological_truth_equated INTEGER NOT NULL DEFAULT 0 CHECK(is_theological_truth_equated = 0),
    confidence_level TEXT NOT NULL CHECK(confidence_level IN ('CERTAIN', 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNSUPPORTED')),
    ledger_claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Later reception cannot equate itself to original authorial intent
    CHECK(is_authorial_intent_equated = 0),
    -- Epistemic Firewall: Reception cannot equate itself to absolute theological truth
    CHECK(is_theological_truth_equated = 0),
    -- Epistemic Firewall: E11/E12 reception claims cannot masquerade as T1 linguistic facts without independent primary evidence
    CHECK(claim_tier != 'T1_LINGUISTIC_FACT')
);

CREATE INDEX IF NOT EXISTS idx_rec_claims_run ON reception_claims(run_id);
CREATE INDEX IF NOT EXISTS idx_rec_claims_record ON reception_claims(record_id);
CREATE INDEX IF NOT EXISTS idx_rec_claims_tier ON reception_claims(claim_tier);
CREATE INDEX IF NOT EXISTS idx_rec_claims_ledger ON reception_claims(ledger_claim_id);

-- ----------------------------------------------------------------------------
-- 6. RECEPTION RELATIONS (Cross-Witness, Lineage & Competing Hypotheses)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_relations (
    relation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES reception_runs(run_id) ON DELETE RESTRICT,
    source_record_id TEXT NOT NULL REFERENCES reception_records(record_id) ON DELETE RESTRICT,
    target_record_id TEXT NOT NULL REFERENCES reception_records(record_id) ON DELETE RESTRICT,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'DIRECT_DEPENDENCE',
        'TRADITION_DEVELOPMENT',
        'HERMENEUTICAL_POLEMIC',
        'COMPETING_INTERPRETATION',
        'HARMONIZING_READING',
        'INDEPENDENT_PARALLEL',
        'UNKNOWN_RELATION'
    )),
    temporal_direction TEXT NOT NULL CHECK(temporal_direction IN (
        'TEXT_TO_RECEPTION',
        'RECEPTION_TO_LATER_RECEPTION',
        'RECEPTION_TO_INTERPRETATION',
        'UNKNOWN'
    )),
    chronological_order_verified INTEGER NOT NULL DEFAULT 0 CHECK(chronological_order_verified IN (0, 1)),
    is_influence_asserted INTEGER NOT NULL DEFAULT 0 CHECK(is_influence_asserted IN (0, 1)),
    hypothesis_id TEXT NOT NULL,
    counter_evidence_preserved INTEGER NOT NULL DEFAULT 1 CHECK(counter_evidence_preserved = 1),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    notes TEXT,

    -- Epistemic Firewall: Self-relation is illegal
    CHECK(source_record_id != target_record_id),
    -- Epistemic Firewall: Influence assertion requires verified chronological order
    CHECK(is_influence_asserted = 0 OR chronological_order_verified = 1),
    -- Epistemic Firewall: Counter-evidence must always be preserved
    CHECK(counter_evidence_preserved = 1)
);

CREATE INDEX IF NOT EXISTS idx_rec_rels_run ON reception_relations(run_id);
CREATE INDEX IF NOT EXISTS idx_rec_rels_src ON reception_relations(source_record_id);
CREATE INDEX IF NOT EXISTS idx_rec_rels_tgt ON reception_relations(target_record_id);
CREATE INDEX IF NOT EXISTS idx_rec_rels_hyp ON reception_relations(hypothesis_id);

-- ----------------------------------------------------------------------------
-- 7. RECEPTION EVIDENCE LINKS (Ledger Association & Epistemic Firewalling)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reception_evidence_links (
    link_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES reception_runs(run_id) ON DELETE RESTRICT,
    record_id TEXT NOT NULL REFERENCES reception_records(record_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    evidence_class TEXT NOT NULL CHECK(evidence_class IN ('E11_EARLY_RECEPTION', 'E12_LATER_INTERPRETATION')),
    claim_id TEXT NOT NULL REFERENCES claims(claim_id) ON DELETE RESTRICT,
    stance TEXT NOT NULL CHECK(stance IN ('SUPPORT', 'CONTRADICT', 'QUALIFY', 'LIMIT', 'REFINE')),
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated = 0),
    is_synthetic_evaluation INTEGER NOT NULL DEFAULT 0 CHECK(is_synthetic_evaluation = 0),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),

    -- Epistemic Firewall: AI generated summaries cannot be E11/E12 primary evidence
    CHECK(is_ai_generated = 0),
    -- Epistemic Firewall: Synthetic evaluations cannot be E11/E12 primary evidence
    CHECK(is_synthetic_evaluation = 0),
    UNIQUE(record_id, evidence_id, claim_id, stance)
);

CREATE INDEX IF NOT EXISTS idx_rec_ev_links_run ON reception_evidence_links(run_id);
CREATE INDEX IF NOT EXISTS idx_rec_ev_links_rec ON reception_evidence_links(record_id);
CREATE INDEX IF NOT EXISTS idx_rec_ev_links_ev ON reception_evidence_links(evidence_id);
CREATE INDEX IF NOT EXISTS idx_rec_ev_links_cl ON reception_evidence_links(claim_id);

-- ----------------------------------------------------------------------------
-- 8. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_runs_upd
BEFORE UPDATE ON reception_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_runs is immutable except status transition from COMPLETED to SUPERSEDED.')
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

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_runs_del
BEFORE DELETE ON reception_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_runs records are immutable and cannot be deleted.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_actors_upd
BEFORE UPDATE ON reception_actors
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_actors records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_actors_del
BEFORE DELETE ON reception_actors
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_actors records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_sources_upd
BEFORE UPDATE ON reception_sources
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_sources records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_sources_del
BEFORE DELETE ON reception_sources
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_sources records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_records_upd
BEFORE UPDATE ON reception_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_records_del
BEFORE DELETE ON reception_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_claims_upd
BEFORE UPDATE ON reception_claims
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_claims are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_claims_del
BEFORE DELETE ON reception_claims
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_claims are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_relations_upd
BEFORE UPDATE ON reception_relations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_relations are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_relations_del
BEFORE DELETE ON reception_relations
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_relations are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_ev_links_upd
BEFORE UPDATE ON reception_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_evidence_links are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_rec_ev_links_del
BEFORE DELETE ON reception_evidence_links
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: reception_evidence_links are immutable.');
END;
