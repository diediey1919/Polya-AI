-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 018: EVIDENCE ADJUDICATION SUBSYSTEM (Task 3.5)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principle:
--   NO CONCLUSION MAY OUTRUN ITS EVIDENCE.
--
-- Critical Epistemic Firewalls:
--   1. Majority vote != truth
--   2. Scholarly or ecclesial consensus != truth
--   3. Fewer supporting sources != justifiable elimination of hypothesis
--   4. Counter-evidence cannot be suppressed or silently omitted
--   5. Absence of evidence != evidence of absence
--   6. Later reception != authorial intent
--   7. Increased source volume != claim tier upgrade
--   8. Incompatible evidence cannot be averaged into artificial consensus
--   9. Confidence aggregation cannot exceed weakest critical dependency
--   10. Lower-tier evidence cannot masquerade as higher-tier evidence
--   11. Competing hypotheses must remain preserved when evidence is inconclusive
--   12. Unresolved conflict is a valid, preserved epistemic state
--   13. Fallacy rejection must be auditable, rule-based, and deterministic
--   14. Immutability enforced by SQL triggers; revisions require supersession
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. ADJUDICATION RUNS (Execution Ledger)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS adjudication_runs (
    run_id TEXT PRIMARY KEY,
    target_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    target_pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    adjudicator_id TEXT NOT NULL,
    adjudicator_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(target_passage_id IS NOT NULL OR target_pericope_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_adj_runs_target_pas ON adjudication_runs(target_passage_id);
CREATE INDEX IF NOT EXISTS idx_adj_runs_target_peri ON adjudication_runs(target_pericope_id);
CREATE INDEX IF NOT EXISTS idx_adj_runs_prov ON adjudication_runs(provenance_id);
CREATE INDEX IF NOT EXISTS idx_adj_runs_ver ON adjudication_runs(version_id);
CREATE INDEX IF NOT EXISTS idx_adj_runs_status ON adjudication_runs(status);

-- ----------------------------------------------------------------------------
-- 2. ADJUDICATION HYPOTHESES (Competing Interpretations & Claims)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS adjudication_hypotheses (
    hypothesis_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES adjudication_runs(run_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    hypothesis_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM'
    )),
    base_confidence REAL NOT NULL CHECK(base_confidence >= 0.0 AND base_confidence <= 1.0),
    propagated_confidence REAL NOT NULL CHECK(propagated_confidence >= 0.0 AND propagated_confidence <= 1.0),
    confidence_level TEXT NOT NULL CHECK(confidence_level IN (
        'CERTAIN',
        'VERY_HIGH',
        'HIGH',
        'MEDIUM',
        'LOW',
        'UNSUPPORTED'
    )),
    status TEXT NOT NULL CHECK(status IN (
        'ACTIVE',
        'DEFENDED',
        'UNDETERMINED',
        'CONTESTED',
        'DEFEATED',
        'SUPERSEDED'
    )),
    is_eliminated INTEGER NOT NULL DEFAULT 0 CHECK(is_eliminated IN (0, 1)),
    elimination_reason TEXT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- Epistemic guard: propagated confidence cannot escalate above base confidence
    CHECK(propagated_confidence <= base_confidence),
    -- Epistemic guard: elimination must document justifiable evidence-based reason
    CHECK(NOT (is_eliminated = 1 AND (elimination_reason IS NULL OR length(trim(elimination_reason)) = 0)))
);

CREATE INDEX IF NOT EXISTS idx_adj_hyp_run ON adjudication_hypotheses(run_id);
CREATE INDEX IF NOT EXISTS idx_adj_hyp_pas ON adjudication_hypotheses(passage_id);
CREATE INDEX IF NOT EXISTS idx_adj_hyp_peri ON adjudication_hypotheses(pericope_id);
CREATE INDEX IF NOT EXISTS idx_adj_hyp_status ON adjudication_hypotheses(status);
CREATE INDEX IF NOT EXISTS idx_adj_hyp_tier ON adjudication_hypotheses(claim_tier);

-- ----------------------------------------------------------------------------
-- 3. ADJUDICATION CONFLICTS (Dialectic Asymmetry & Preservation)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS adjudication_conflicts (
    conflict_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES adjudication_runs(run_id) ON DELETE RESTRICT,
    hypothesis_a_id TEXT NOT NULL REFERENCES adjudication_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    hypothesis_b_id TEXT NOT NULL REFERENCES adjudication_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    conflict_type TEXT NOT NULL CHECK(conflict_type IN (
        'MUTUALLY_EXCLUSIVE',
        'PARTIAL_CONTRADICTION',
        'TENSION',
        'EVIDENTIARY_ASYMMETRY',
        'UNRESOLVED_DISPUTE'
    )),
    conflict_severity TEXT NOT NULL CHECK(conflict_severity IN (
        'IRRECONCILABLE',
        'HIGH',
        'MODERATE',
        'LOW'
    )),
    is_resolved INTEGER NOT NULL DEFAULT 0 CHECK(is_resolved IN (0, 1)),
    resolution_method TEXT CHECK(resolution_method IN (
        'PRIMARY_TEXT_OVER_RECEPTION',
        'GRAMMATICAL_DEFEAT',
        'WITNESS_APPARATUS_SUPERIORITY',
        'HISTORICAL_PRIORITY',
        'UNRESOLVED_PRESERVED',
        'NONE'
    )),
    resolution_reasoning TEXT,
    -- Epistemic Firewalls: strictly forbidden to apply majority vote, consensus, or suppression
    is_majority_vote_applied INTEGER NOT NULL DEFAULT 0 CHECK(is_majority_vote_applied = 0),
    is_consensus_equated_truth INTEGER NOT NULL DEFAULT 0 CHECK(is_consensus_equated_truth = 0),
    is_counter_evidence_suppressed INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence_suppressed = 0),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(hypothesis_a_id != hypothesis_b_id),
    CHECK(NOT (is_resolved = 1 AND (resolution_reasoning IS NULL OR length(trim(resolution_reasoning)) = 0)))
);

CREATE INDEX IF NOT EXISTS idx_adj_conf_run ON adjudication_conflicts(run_id);
CREATE INDEX IF NOT EXISTS idx_adj_conf_hyp_a ON adjudication_conflicts(hypothesis_a_id);
CREATE INDEX IF NOT EXISTS idx_adj_conf_hyp_b ON adjudication_conflicts(hypothesis_b_id);
CREATE INDEX IF NOT EXISTS idx_adj_conf_type ON adjudication_conflicts(conflict_type);

-- ----------------------------------------------------------------------------
-- 4. FALLACY AUDIT RECORDS (Deterministic Hermeneutical & Logical Filters)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fallacy_audit_records (
    audit_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES adjudication_runs(run_id) ON DELETE RESTRICT,
    hypothesis_id TEXT NOT NULL REFERENCES adjudication_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    fallacy_type TEXT NOT NULL CHECK(fallacy_type IN (
        'ILLEGITIMATE_TOTALITY_TRANSFER',
        'ROOT_FALLACY',
        'SEMANTIC_ANACHRONISM',
        'UNWARRANTED_GENERALIZATION',
        'MAJORITY_CONSENSUS_FALLACY',
        'CONFIDENCE_ESCALATION_FALLACY',
        'ABSENCE_AS_PROOF_FALLACY',
        'COUNTER_EVIDENCE_SUPPRESSION_FALLACY',
        'AI_BLACK_BOX_FALLACY',
        'RECEPTION_AS_AUTHORIAL_FALLACY'
    )),
    violating_inference TEXT NOT NULL,
    evidence_used_json TEXT NOT NULL,
    applicable_rule TEXT NOT NULL,
    enforcing_firewall TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('FATAL_INVALIDATION', 'HIGH_RISK', 'WARNING')),
    is_fatal INTEGER NOT NULL CHECK(is_fatal IN (0, 1)),
    detected_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_adj_fallacy_run ON fallacy_audit_records(run_id);
CREATE INDEX IF NOT EXISTS idx_adj_fallacy_hyp ON fallacy_audit_records(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_adj_fallacy_type ON fallacy_audit_records(fallacy_type);

-- ----------------------------------------------------------------------------
-- 5. ADJUDICATED VERDICTS (Calibrated Epistemic Outcomes)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS adjudicated_verdicts (
    verdict_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES adjudication_runs(run_id) ON DELETE RESTRICT,
    hypothesis_id TEXT NOT NULL REFERENCES adjudication_hypotheses(hypothesis_id) ON DELETE RESTRICT,
    verdict_status TEXT NOT NULL CHECK(verdict_status IN (
        'ESTABLISHED_FACT',
        'PROBABLE_CONCLUSION',
        'COMPETING_INTERPRETATION_PRESERVED',
        'INSUFFICIENT_EVIDENCE',
        'FALSIFIED_BY_PRIMARY_EVIDENCE',
        'INVALIDATED_BY_FALLACY'
    )),
    epistemic_tier TEXT NOT NULL CHECK(epistemic_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM',
        'T4_THEOLOGICAL_CLAIM'
    )),
    confidence_score REAL NOT NULL CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    weakest_critical_dependency_id TEXT,
    weakest_critical_confidence REAL CHECK(weakest_critical_confidence >= 0.0 AND weakest_critical_confidence <= 1.0),
    supporting_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK(supporting_evidence_count >= 0),
    contrary_evidence_count INTEGER NOT NULL DEFAULT 0 CHECK(contrary_evidence_count >= 0),
    unresolved_conflict_count INTEGER NOT NULL DEFAULT 0 CHECK(unresolved_conflict_count >= 0),
    fallacy_count INTEGER NOT NULL DEFAULT 0 CHECK(fallacy_count >= 0),
    -- Epistemic Firewalls: consensus or majority vote cannot generate verdict
    is_consensus_derived INTEGER NOT NULL DEFAULT 0 CHECK(is_consensus_derived = 0),
    is_majority_vote_derived INTEGER NOT NULL DEFAULT 0 CHECK(is_majority_vote_derived = 0),
    is_competing_preserved INTEGER NOT NULL DEFAULT 1 CHECK(is_competing_preserved IN (0, 1)),
    verdict_rationale TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- Epistemic Firewall: confidence cannot exceed weakest critical dependency
    CHECK(NOT (weakest_critical_confidence IS NOT NULL AND confidence_score > weakest_critical_confidence)),
    -- Epistemic Firewall: cannot establish fact if contrary evidence exists
    CHECK(NOT (contrary_evidence_count > 0 AND verdict_status = 'ESTABLISHED_FACT')),
    -- Epistemic Firewall: fatal fallacy invalidation cannot have ESTABLISHED_FACT or PROBABLE_CONCLUSION status
    CHECK(NOT (fallacy_count > 0 AND verdict_status IN ('ESTABLISHED_FACT', 'PROBABLE_CONCLUSION')))
);

CREATE INDEX IF NOT EXISTS idx_adj_verd_run ON adjudicated_verdicts(run_id);
CREATE INDEX IF NOT EXISTS idx_adj_verd_hyp ON adjudicated_verdicts(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_adj_verd_status ON adjudicated_verdicts(verdict_status);
CREATE INDEX IF NOT EXISTS idx_adj_verd_tier ON adjudicated_verdicts(epistemic_tier);

-- ----------------------------------------------------------------------------
-- 6. IMMUTABILITY & AUDIT TRIGGERS (Append-Only & Controlled Supersession)
-- ----------------------------------------------------------------------------

-- A. Runs: only status update COMPLETED -> SUPERSEDED allowed
CREATE TRIGGER IF NOT EXISTS trg_immut_adj_runs_upd
BEFORE UPDATE ON adjudication_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_runs are immutable except status transition COMPLETED -> SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.target_passage_id IS NOT NEW.target_passage_id
       OR OLD.target_pericope_id IS NOT NEW.target_pericope_id
       OR OLD.version_id != NEW.version_id
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.adjudicator_id != NEW.adjudicator_id
       OR OLD.adjudicator_version != NEW.adjudicator_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.is_exact_reproducible != NEW.is_exact_reproducible
       OR OLD.created_at != NEW.created_at
       OR NOT (OLD.status = 'COMPLETED' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_adj_runs_del
BEFORE DELETE ON adjudication_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_runs records are immutable and cannot be deleted.');
END;

-- B. Hypotheses: completely immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_adj_hyp_upd
BEFORE UPDATE ON adjudication_hypotheses
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_hypotheses are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_adj_hyp_del
BEFORE DELETE ON adjudication_hypotheses
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_hypotheses are immutable.');
END;

-- C. Conflicts: completely immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_adj_conf_upd
BEFORE UPDATE ON adjudication_conflicts
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_conflicts are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_adj_conf_del
BEFORE DELETE ON adjudication_conflicts
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudication_conflicts are immutable.');
END;

-- D. Fallacy Audits: completely immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_adj_fallacy_upd
BEFORE UPDATE ON fallacy_audit_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: fallacy_audit_records are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_adj_fallacy_del
BEFORE DELETE ON fallacy_audit_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: fallacy_audit_records are immutable.');
END;

-- E. Verdicts: completely immutable
CREATE TRIGGER IF NOT EXISTS trg_immut_adj_verd_upd
BEFORE UPDATE ON adjudicated_verdicts
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudicated_verdicts are immutable.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_adj_verd_del
BEFORE DELETE ON adjudicated_verdicts
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: adjudicated_verdicts are immutable.');
END;
