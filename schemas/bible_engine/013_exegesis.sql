-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 013: EXEGESIS FOUNDATION (Task 2.9)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core principle: NO CONCLUSION MAY OUTRUN ITS EVIDENCE.
-- Epistemic Pipeline:
--   OBSERVATION
--   → LINGUISTIC_FACT
--   → CONTEXTUAL_FACT
--   → CLAIM
--   → HYPOTHESIS
--   → COMPETING_INTERPRETATIONS
--   → EVIDENCE_AUDIT
--   → CALIBRATED_CONCLUSION
--
-- Critical rules:
--   1. EXEGESIS MUST NOT:
--      - rewrite source text
--      - rewrite morphology
--      - rewrite syntax
--      - rewrite semantic senses
--      - rewrite entity identity
--      - promote translation into source evidence
--      - convert confidence into evidence
--      - convert model agreement into truth
--      - suppress competing interpretations
--      - suppress counter-evidence
--      - silently resolve ambiguity
--      - create STRICT_IDENTITY without independent evidence
--      - directly manufacture unsupported T4 theology
--   2. Pericope is the primary exegesis unit. Verse remains reference unit.
--   3. Competing interpretations must coexist; no majority vote.
--   4. Final calibrated conclusion preserves: supporting evidence, counter-evidence,
--      unresolved ambiguity, weakest critical dependency, confidence, and provenance.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. EXEGESIS RUNS (Primary Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exegesis_runs (
    run_id TEXT PRIMARY KEY,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    syntax_run_id TEXT REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    semantic_run_id TEXT REFERENCES semantic_runs(run_id) ON DELETE RESTRICT,
    discourse_run_id TEXT REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    referential_run_id TEXT REFERENCES referential_runs(run_id) ON DELETE RESTRICT,
    evidence_run_id TEXT REFERENCES evidence_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    model_name TEXT,
    relevant_clauses_json TEXT NOT NULL DEFAULT '[]',
    relevant_tokens_json TEXT NOT NULL DEFAULT '[]',
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_exegesis_runs_pericope ON exegesis_runs(pericope_id);
CREATE INDEX IF NOT EXISTS idx_exegesis_runs_source_text ON exegesis_runs(source_text_id);

-- ----------------------------------------------------------------------------
-- 2. EXEGESIS OBSERVATIONS (Level 1: Raw Observations & Linguistic/Contextual Anchors)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exegesis_observations (
    observation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    observation_type TEXT NOT NULL CHECK(observation_type IN (
        'RAW_OBSERVATION',
        'TEXTUAL_VARIANT',
        'GRAMMATICAL_FEATURE',
        'LEXICAL_OCCURRENCE',
        'DISCOURSE_FEATURE',
        'REFERENTIAL_OCCURRENCE'
    )),
    source_reference TEXT NOT NULL,
    observed_text_or_data TEXT NOT NULL,
    is_translation_derived INTEGER NOT NULL DEFAULT 0 CHECK(is_translation_derived = 0),
    is_ai_generated INTEGER NOT NULL DEFAULT 0 CHECK(is_ai_generated = 0),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_exegesis_observations_run ON exegesis_observations(run_id);
CREATE INDEX IF NOT EXISTS idx_exegesis_observations_pericope ON exegesis_observations(pericope_id);

-- ----------------------------------------------------------------------------
-- 3. EXEGESIS LINGUISTIC FINDINGS (Level 2: Morphology, Syntax, Lexical Semantics)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exegesis_linguistic_findings (
    finding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    category TEXT NOT NULL CHECK(category IN ('MORPHOLOGY', 'SYNTAX', 'LEXICAL_SEMANTICS')),
    finding_text TEXT NOT NULL,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    confidence_score REAL NOT NULL DEFAULT 1.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_exegesis_linguistic_run ON exegesis_linguistic_findings(run_id);

-- ----------------------------------------------------------------------------
-- 4. EXEGESIS CONTEXTUAL FINDINGS (Level 3: Discourse, Referential, Literary Context)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS exegesis_contextual_findings (
    context_finding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    category TEXT NOT NULL CHECK(category IN (
        'IMMEDIATE_CONTEXT',
        'DISCOURSE_STRUCTURE',
        'REFERENTIAL_COGNITION',
        'BOOK_CONTEXT',
        'CORPUS_CONTEXT',
        'HISTORICAL_LINGUISTIC'
    )),
    finding_text TEXT NOT NULL,
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    confidence_score REAL NOT NULL DEFAULT 1.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_exegesis_contextual_run ON exegesis_contextual_findings(run_id);

-- ----------------------------------------------------------------------------
-- 5. INTERPRETIVE HYPOTHESES (Level 4: Hypotheses & Interpretation States)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS interpretive_hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    claim_id TEXT REFERENCES claims(claim_id) ON DELETE RESTRICT,
    hypothesis_text TEXT NOT NULL,
    hypothesis_state TEXT NOT NULL CHECK(hypothesis_state IN (
        'PROPOSED',
        'SUPPORTED',
        'QUALIFIED',
        'CONTESTED',
        'REJECTED',
        'UNRESOLVED'
    )),
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'T0_RAW_OBSERVATION', 'T1_LINGUISTIC_FACT', 'T2_CONTEXTUAL_CLAIM', 'T3_INTERPRETIVE_CLAIM', 'T4_THEOLOGICAL_CLAIM',
        'T0', 'T1', 'T2', 'T3', 'T4'
    )),
    is_theology_independent INTEGER NOT NULL DEFAULT 0 CHECK(is_theology_independent IN (0, 1)),
    confidence_score REAL NOT NULL DEFAULT 0.0 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_interpretive_hypotheses_run ON interpretive_hypotheses(run_id);
CREATE INDEX IF NOT EXISTS idx_interpretive_hypotheses_pericope ON interpretive_hypotheses(pericope_id);

-- ----------------------------------------------------------------------------
-- 6. COMPETING INTERPRETATIONS (Coexistence & Anti-Suppression Firewall)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS competing_interpretations (
    competing_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    hypothesis_a_id TEXT NOT NULL REFERENCES interpretive_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    hypothesis_b_id TEXT NOT NULL REFERENCES interpretive_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    tension_type TEXT NOT NULL CHECK(tension_type IN (
        'MUTUALLY_EXCLUSIVE',
        'ALTERNATIVE_READING',
        'SEMANTIC_AMBIGUITY',
        'SYNTACTIC_AMBIGUITY',
        'REFERENTIAL_AMBIGUITY',
        'DIALECTICAL_TENSION'
    )),
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('COEXISTING', 'UNRESOLVED', 'CONTESTED', 'QUALIFIED', 'RESOLVED')),
    is_suppressed INTEGER NOT NULL DEFAULT 0 CHECK(is_suppressed = 0),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    CHECK(hypothesis_a_id != hypothesis_b_id)
);

CREATE INDEX IF NOT EXISTS idx_competing_interp_run ON competing_interpretations(run_id);

-- ----------------------------------------------------------------------------
-- 7. EVIDENCE AUDITS (Detailed Audit of Supporting & Counter Evidence)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_audits (
    audit_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    hypothesis_id TEXT NOT NULL REFERENCES interpretive_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    relationship TEXT NOT NULL CHECK(relationship IN ('SUPPORT', 'CONTRADICT', 'QUALIFY', 'LIMIT', 'REFINE')),
    is_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence IN (0, 1)),
    is_critical INTEGER NOT NULL DEFAULT 0 CHECK(is_critical IN (0, 1)),
    audit_notes TEXT NOT NULL,
    evidence_confidence REAL NOT NULL DEFAULT 1.0 CHECK(evidence_confidence >= 0.0 AND evidence_confidence <= 1.0),
    audited_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_evidence_audits_hyp ON evidence_audits(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_evidence_audits_ev ON evidence_audits(evidence_id);

-- ----------------------------------------------------------------------------
-- 8. UNRESOLVED ISSUES (Preservation of Ambiguity and Contradictions)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS unresolved_issues (
    issue_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    hypothesis_id TEXT REFERENCES interpretive_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    issue_type TEXT NOT NULL CHECK(issue_type IN (
        'AMBIGUITY',
        'TEXTUAL_VARIANT',
        'UNRESOLVED_CONTRADICTION',
        'UNRESOLVED_COUNTER_EVIDENCE',
        'INSUFFICIENT_EVIDENCE',
        'UNSUPPORTED_LEAP'
    )),
    description TEXT NOT NULL,
    is_silently_resolved INTEGER NOT NULL DEFAULT 0 CHECK(is_silently_resolved = 0),
    is_resolved INTEGER NOT NULL DEFAULT 0 CHECK(is_resolved IN (0, 1)),
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1)
);

CREATE INDEX IF NOT EXISTS idx_unresolved_issues_run ON unresolved_issues(run_id);
CREATE INDEX IF NOT EXISTS idx_unresolved_issues_pericope ON unresolved_issues(pericope_id);

-- ----------------------------------------------------------------------------
-- 9. CALIBRATED CONCLUSIONS (Calibrated Output Preserving All Epistemic Bounds)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS calibrated_conclusions (
    conclusion_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES exegesis_runs(run_id) ON DELETE RESTRICT,
    pericope_id TEXT NOT NULL REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    hypothesis_id TEXT NOT NULL REFERENCES interpretive_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'T0_RAW_OBSERVATION', 'T1_LINGUISTIC_FACT', 'T2_CONTEXTUAL_CLAIM', 'T3_INTERPRETIVE_CLAIM', 'T4_THEOLOGICAL_CLAIM',
        'T0', 'T1', 'T2', 'T3', 'T4'
    )),
    conclusion_text TEXT NOT NULL,
    epistemic_status TEXT NOT NULL CHECK(epistemic_status IN (
        'SUPPORTED',
        'QUALIFIED',
        'CONTESTED',
        'UNRESOLVED',
        'DISPUTED',
        'REJECTED'
    )),
    calibrated_confidence REAL NOT NULL CHECK(calibrated_confidence >= 0.0 AND calibrated_confidence <= 1.0),
    weakest_critical_dependency TEXT,
    weakest_critical_confidence REAL CHECK(weakest_critical_confidence IS NULL OR (weakest_critical_confidence >= 0.0 AND weakest_critical_confidence <= 1.0)),
    supporting_evidence_count INTEGER NOT NULL DEFAULT 0,
    counter_evidence_count INTEGER NOT NULL DEFAULT 0,
    unresolved_ambiguity_count INTEGER NOT NULL DEFAULT 0,
    has_unresolved_contradiction INTEGER NOT NULL DEFAULT 0 CHECK(has_unresolved_contradiction IN (0, 1)),
    model_name TEXT,
    analyzer_id TEXT NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT '1970-01-01T00:00:00Z',
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),

    CHECK(supporting_evidence_count > 0 OR epistemic_status != 'SUPPORTED'),
    CHECK(has_unresolved_contradiction = 0 OR epistemic_status != 'SUPPORTED'),
    CHECK(weakest_critical_confidence IS NULL OR calibrated_confidence <= weakest_critical_confidence + 0.0001)
);

CREATE INDEX IF NOT EXISTS idx_calibrated_conclusions_run ON calibrated_conclusions(run_id);
CREATE INDEX IF NOT EXISTS idx_calibrated_conclusions_pericope ON calibrated_conclusions(pericope_id);

-- ----------------------------------------------------------------------------
-- 10. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_exegesis_runs_no_delete
BEFORE DELETE ON exegesis_runs
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_runs_no_update
BEFORE UPDATE ON exegesis_runs
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_observations_no_delete
BEFORE DELETE ON exegesis_observations
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis observations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_observations_no_update
BEFORE UPDATE ON exegesis_observations
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis observations are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_linguistic_findings_no_delete
BEFORE DELETE ON exegesis_linguistic_findings
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis linguistic findings are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_linguistic_findings_no_update
BEFORE UPDATE ON exegesis_linguistic_findings
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis linguistic findings are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_contextual_findings_no_delete
BEFORE DELETE ON exegesis_contextual_findings
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis contextual findings are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_exegesis_contextual_findings_no_update
BEFORE UPDATE ON exegesis_contextual_findings
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Exegesis contextual findings are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_interpretive_hypotheses_no_delete
BEFORE DELETE ON interpretive_hypotheses
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Interpretive hypotheses are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_interpretive_hypotheses_no_update
BEFORE UPDATE ON interpretive_hypotheses
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Interpretive hypotheses are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_competing_interpretations_no_delete
BEFORE DELETE ON competing_interpretations
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Competing interpretations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_competing_interpretations_no_update
BEFORE UPDATE ON competing_interpretations
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Competing interpretations are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_audits_no_delete
BEFORE DELETE ON evidence_audits
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Evidence audits are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_audits_no_update
BEFORE UPDATE ON evidence_audits
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Evidence audits are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_unresolved_issues_no_delete
BEFORE DELETE ON unresolved_issues
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Unresolved issues are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_unresolved_issues_no_update
BEFORE UPDATE ON unresolved_issues
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Unresolved issues are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_calibrated_conclusions_no_delete
BEFORE DELETE ON calibrated_conclusions
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Calibrated conclusions are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_calibrated_conclusions_no_update
BEFORE UPDATE ON calibrated_conclusions
FOR EACH ROW BEGIN
    SELECT RAISE(ABORT, 'Calibrated conclusions are immutable: UPDATE is strictly prohibited.');
END;
