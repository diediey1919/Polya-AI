-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 021: THEOLOGICAL COMPARISON & ILZAM AL-KHASM ENGINE (Task 3.8)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core Epistemic Principles:
--   1. HARD THEOLOGY FIREWALL:
--      T0–T3 evidence -> theological audit -> T4 proposition assessment.
--      T4 dogmatic propositions CANNOT contaminate, rewrite, upgrade, or define T0–T3 facts.
--   2. NO SELF-PROVING DOGMA:
--      A theological proposition cannot serve as evidence for its own underlying premises.
--      Circular dependency chains are strictly forbidden.
--   3. ILZAM AL-KHASM (INTERNAL CRITIQUE):
--      Evaluates propositions strictly against a framework's own stated premises,
--      acknowledged texts, and linguistic constraints.
--   4. SYMMETRICAL EVALUATION:
--      Every framework evaluated against identical evidence and rules; zero majority-vote.
--   5. ANTI-ANACHRONISM FIREWALL:
--      Post-biblical reception terminology (E12) cannot be retrojected as original intent.
--   6. IDENTITY FIREWALL:
--      Metaphorical agency or divine representation != ontological identity.
--   7. WEAKEST-CRITICAL-DEPENDENCY CONFIDENCE:
--      Confidence of audit <= min(constituent evidence confidences).
--   8. IMMUTABILITY & PROVENANCE:
--      Full SHA-256 provenance lineage; UPDATE/DELETE blocked by triggers.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. THEOLOGICAL FRAMEWORKS (Confessional / Traditio-Historical Registry)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS theological_frameworks (
    framework_id TEXT PRIMARY KEY,
    framework_name TEXT NOT NULL,
    tradition_family TEXT NOT NULL CHECK(tradition_family IN (
        'CHRISTIAN_PATRISTIC',
        'CHRISTIAN_HETERODOX',
        'JUDAISM_SECOND_TEMPLE',
        'JUDAISM_RABBINIC',
        'ISLAMIC_TAWHIDIC',
        'ENLIGHTENMENT_SOCINIAN',
        'OTHER'
    )),
    historical_period TEXT NOT NULL,
    description TEXT NOT NULL,
    canonical_source_corpus TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_theo_fw_tradition ON theological_frameworks(tradition_family);
CREATE INDEX IF NOT EXISTS idx_theo_fw_prov ON theological_frameworks(provenance_id);
CREATE INDEX IF NOT EXISTS idx_theo_fw_ver ON theological_frameworks(version_id);

-- ----------------------------------------------------------------------------
-- 2. DOGMATIC PROPOSITIONS (T4 Theological Formulations)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dogmatic_propositions (
    proposition_id TEXT PRIMARY KEY,
    framework_id TEXT NOT NULL REFERENCES theological_frameworks(framework_id) ON DELETE RESTRICT,
    claim_tier TEXT NOT NULL DEFAULT 'T4_THEOLOGICAL_CLAIM' CHECK(claim_tier = 'T4_THEOLOGICAL_CLAIM'),
    formulation_title TEXT NOT NULL,
    proposition_text TEXT NOT NULL,
    formal_creedal_source TEXT NOT NULL,
    historical_era TEXT NOT NULL CHECK(historical_era IN (
        'BIBLICAL_ERA',
        'APOSTOLIC_FATHERS',
        'EARLY_PATRISTIC',
        'NICENE_ERA',
        'POST_CHALCEDONIAN',
        'MEDIEVAL',
        'REFORMATION',
        'MODERN'
    )),
    contains_post_biblical_terminology INTEGER NOT NULL DEFAULT 0 CHECK(contains_post_biblical_terminology IN (0, 1)),
    post_biblical_terms_json TEXT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_dogma_prop_fw ON dogmatic_propositions(framework_id);
CREATE INDEX IF NOT EXISTS idx_dogma_prop_era ON dogmatic_propositions(historical_era);
CREATE INDEX IF NOT EXISTS idx_dogma_prop_status ON dogmatic_propositions(status);
CREATE INDEX IF NOT EXISTS idx_dogma_prop_prov ON dogmatic_propositions(provenance_id);

-- ----------------------------------------------------------------------------
-- 3. THEOLOGICAL COMPARISON RUNS (Execution & Audit Runs)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS theological_comparison_runs (
    run_id TEXT PRIMARY KEY,
    proposition_id TEXT NOT NULL REFERENCES dogmatic_propositions(proposition_id) ON DELETE RESTRICT,
    comparator_id TEXT NOT NULL,
    comparator_version TEXT NOT NULL,
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    audit_verdict TEXT NOT NULL CHECK(audit_verdict IN (
        'SUPPORTED',
        'PARTIALLY_SUPPORTED',
        'IN_TENSION',
        'INSUFFICIENTLY_WARRANTED',
        'CONTRADICTED',
        'UNRESOLVED'
    )),
    overall_confidence REAL NOT NULL CHECK(overall_confidence >= 0.0 AND overall_confidence <= 1.0),
    status TEXT NOT NULL DEFAULT 'COMPLETED' CHECK(status IN ('INITIALIZED', 'PROCESSING', 'COMPLETED', 'FAILED', 'SUPERSEDED')),
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_theo_runs_prop ON theological_comparison_runs(proposition_id);
CREATE INDEX IF NOT EXISTS idx_theo_runs_verdict ON theological_comparison_runs(audit_verdict);
CREATE INDEX IF NOT EXISTS idx_theo_runs_status ON theological_comparison_runs(status);
CREATE INDEX IF NOT EXISTS idx_theo_runs_prov ON theological_comparison_runs(provenance_id);

-- ----------------------------------------------------------------------------
-- 4. PROPOSITION EVIDENCE AUDITS (T4 Deconstruction against T0-T3 Evidence)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS proposition_evidence_audits (
    audit_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES theological_comparison_runs(run_id) ON DELETE RESTRICT,
    proposition_id TEXT NOT NULL REFERENCES dogmatic_propositions(proposition_id) ON DELETE RESTRICT,
    deconstructed_premise_text TEXT NOT NULL,
    target_evidence_tier TEXT NOT NULL CHECK(target_evidence_tier IN (
        'T0_RAW_OBSERVATION',
        'T1_LINGUISTIC_FACT',
        'T2_CONTEXTUAL_CLAIM',
        'T3_INTERPRETIVE_CLAIM'
    )),
    target_claim_id TEXT REFERENCES claims(claim_id) ON DELETE RESTRICT,
    target_synthesis_claim_id TEXT REFERENCES synthesis_claims(claim_id) ON DELETE RESTRICT,
    target_evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    target_passage_or_pericope_id TEXT NOT NULL,
    alignment_status TEXT NOT NULL CHECK(alignment_status IN (
        'TEXTUALLY_SUPPORTED',
        'LEXICALLY_UNSUPPORTED',
        'ANACHRONISTIC_RETROJECTION',
        'CATEGORY_MISTAKE_IDENTITY',
        'EXEGETICAL_TENSION',
        'CONTRADICTION',
        'UNWARRANTED_EXTRAPOLATION',
        'ABSENCE_OF_TEXTUAL_WARRANT'
    )),
    evidence_confidence REAL NOT NULL CHECK(evidence_confidence >= 0.0 AND evidence_confidence <= 1.0),
    audit_confidence REAL NOT NULL CHECK(audit_confidence >= 0.0 AND audit_confidence <= 1.0),
    is_anachronism_detected INTEGER NOT NULL DEFAULT 0 CHECK(is_anachronism_detected IN (0, 1)),
    is_identity_collapse_detected INTEGER NOT NULL DEFAULT 0 CHECK(is_identity_collapse_detected IN (0, 1)),
    audit_finding_detail TEXT NOT NULL,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    CHECK(audit_confidence <= evidence_confidence + 0.00001)
);

CREATE INDEX IF NOT EXISTS idx_prop_audits_run ON proposition_evidence_audits(run_id);
CREATE INDEX IF NOT EXISTS idx_prop_audits_prop ON proposition_evidence_audits(proposition_id);
CREATE INDEX IF NOT EXISTS idx_prop_audits_status ON proposition_evidence_audits(alignment_status);
CREATE INDEX IF NOT EXISTS idx_prop_audits_target ON proposition_evidence_audits(target_passage_or_pericope_id);

-- ----------------------------------------------------------------------------
-- 5. ILZAM CRITIQUE RECORDS (Internal Critique / إلزام الخصم)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ilzam_critique_records (
    critique_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES theological_comparison_runs(run_id) ON DELETE RESTRICT,
    target_framework_id TEXT NOT NULL REFERENCES theological_frameworks(framework_id) ON DELETE RESTRICT,
    target_proposition_id TEXT NOT NULL REFERENCES dogmatic_propositions(proposition_id) ON DELETE RESTRICT,
    critique_type TEXT NOT NULL CHECK(critique_type IN (
        'INTERNAL_PREMISE_CONTRADICTION',
        'UNSUPPORTED_INFERENCE',
        'INVALID_EXTRAPOLATION',
        'CONTRADICTION_WITH_ACKNOWLEDGED_TEXT',
        'ANACHRONISTIC_CATEGORY_LEAKAGE',
        'CIRCULAR_PROOF_STRUCTURE',
        'AMBIGUITY_OR_UNRESOLVED_ANTINOMY'
    )),
    acknowledged_premise_a TEXT NOT NULL,
    acknowledged_premise_b TEXT,
    dependency_chain_json TEXT NOT NULL,
    demonstration_text TEXT NOT NULL,
    critique_severity TEXT NOT NULL CHECK(critique_severity IN (
        'FATAL_INTERNAL_CONTRADICTION',
        'UNWARRANTED_LEAP',
        'FORMAL_AMBIGUITY',
        'INFORMATIONAL_TENSION'
    )),
    is_circularity_rejected INTEGER NOT NULL DEFAULT 0 CHECK(is_circularity_rejected IN (0, 1)),
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_ilzam_run ON ilzam_critique_records(run_id);
CREATE INDEX IF NOT EXISTS idx_ilzam_fw ON ilzam_critique_records(target_framework_id);
CREATE INDEX IF NOT EXISTS idx_ilzam_prop ON ilzam_critique_records(target_proposition_id);
CREATE INDEX IF NOT EXISTS idx_ilzam_type ON ilzam_critique_records(critique_type);

-- ----------------------------------------------------------------------------
-- 6. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

-- A. Theological Frameworks: strictly immutable (no UPDATE / DELETE)
CREATE TRIGGER IF NOT EXISTS trg_immut_theo_fw_upd
BEFORE UPDATE ON theological_frameworks
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: theological_frameworks are immutable and cannot be updated.');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_theo_fw_del
BEFORE DELETE ON theological_frameworks
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: theological_frameworks are immutable and cannot be deleted.');
END;

-- B. Dogmatic Propositions: only status may transition to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_dogma_prop_upd
BEFORE UPDATE ON dogmatic_propositions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: dogmatic_propositions status may only transition to SUPERSEDED.')
    WHERE OLD.proposition_id != NEW.proposition_id
       OR OLD.framework_id != NEW.framework_id
       OR OLD.claim_tier != NEW.claim_tier
       OR OLD.formulation_title != NEW.formulation_title
       OR OLD.proposition_text != NEW.proposition_text
       OR OLD.formal_creedal_source != NEW.formal_creedal_source
       OR OLD.historical_era != NEW.historical_era
       OR OLD.contains_post_biblical_terminology != NEW.contains_post_biblical_terminology
       OR OLD.post_biblical_terms_json IS NOT NEW.post_biblical_terms_json
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_dogma_prop_del
BEFORE DELETE ON dogmatic_propositions
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: dogmatic_propositions are immutable and cannot be deleted.');
END;

-- C. Theological Comparison Runs: only status may transition to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_theo_runs_upd
BEFORE UPDATE ON theological_comparison_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: theological_comparison_runs status may only transition to SUPERSEDED.')
    WHERE OLD.run_id != NEW.run_id
       OR OLD.proposition_id != NEW.proposition_id
       OR OLD.comparator_id != NEW.comparator_id
       OR OLD.comparator_version != NEW.comparator_version
       OR OLD.configuration_hash != NEW.configuration_hash
       OR OLD.input_content_hash != NEW.input_content_hash
       OR OLD.output_hash != NEW.output_hash
       OR OLD.audit_verdict != NEW.audit_verdict
       OR OLD.overall_confidence != NEW.overall_confidence
       OR OLD.is_exact_reproducible != NEW.is_exact_reproducible
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'COMPLETED' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_theo_runs_del
BEFORE DELETE ON theological_comparison_runs
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: theological_comparison_runs are immutable and cannot be deleted.');
END;

-- D. Proposition Evidence Audits: only status may transition to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_prop_audits_upd
BEFORE UPDATE ON proposition_evidence_audits
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: proposition_evidence_audits status may only transition to SUPERSEDED.')
    WHERE OLD.audit_id != NEW.audit_id
       OR OLD.run_id != NEW.run_id
       OR OLD.proposition_id != NEW.proposition_id
       OR OLD.deconstructed_premise_text != NEW.deconstructed_premise_text
       OR OLD.target_evidence_tier != NEW.target_evidence_tier
       OR OLD.target_claim_id IS NOT NEW.target_claim_id
       OR OLD.target_synthesis_claim_id IS NOT NEW.target_synthesis_claim_id
       OR OLD.target_evidence_id IS NOT NEW.target_evidence_id
       OR OLD.target_passage_or_pericope_id != NEW.target_passage_or_pericope_id
       OR OLD.alignment_status != NEW.alignment_status
       OR OLD.evidence_confidence != NEW.evidence_confidence
       OR OLD.audit_confidence != NEW.audit_confidence
       OR OLD.is_anachronism_detected != NEW.is_anachronism_detected
       OR OLD.is_identity_collapse_detected != NEW.is_identity_collapse_detected
       OR OLD.audit_finding_detail != NEW.audit_finding_detail
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_prop_audits_del
BEFORE DELETE ON proposition_evidence_audits
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: proposition_evidence_audits are immutable and cannot be deleted.');
END;

-- E. Ilzam Critique Records: only status may transition to SUPERSEDED
CREATE TRIGGER IF NOT EXISTS trg_immut_ilzam_upd
BEFORE UPDATE ON ilzam_critique_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: ilzam_critique_records status may only transition to SUPERSEDED.')
    WHERE OLD.critique_id != NEW.critique_id
       OR OLD.run_id != NEW.run_id
       OR OLD.target_framework_id != NEW.target_framework_id
       OR OLD.target_proposition_id != NEW.target_proposition_id
       OR OLD.critique_type != NEW.critique_type
       OR OLD.acknowledged_premise_a != NEW.acknowledged_premise_a
       OR OLD.acknowledged_premise_b IS NOT NEW.acknowledged_premise_b
       OR OLD.dependency_chain_json != NEW.dependency_chain_json
       OR OLD.demonstration_text != NEW.demonstration_text
       OR OLD.critique_severity != NEW.critique_severity
       OR OLD.is_circularity_rejected != NEW.is_circularity_rejected
       OR OLD.provenance_id != NEW.provenance_id
       OR OLD.version_id != NEW.version_id
       OR OLD.created_at != NEW.created_at
       OR OLD.is_immutable != NEW.is_immutable
       OR OLD.metadata_json IS NOT NEW.metadata_json
       OR NOT (OLD.status = 'ACTIVE' AND NEW.status = 'SUPERSEDED');
END;

CREATE TRIGGER IF NOT EXISTS trg_immut_ilzam_del
BEFORE DELETE ON ilzam_critique_records
FOR EACH ROW
WHEN OLD.is_immutable = 1
BEGIN
    SELECT RAISE(ABORT, 'IMMUTABILITY_VIOLATION: ilzam_critique_records are immutable and cannot be deleted.');
END;
