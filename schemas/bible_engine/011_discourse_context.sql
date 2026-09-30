-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 011: DISCOURSE & CONTEXT FOUNDATION (Task 2.7)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
--
-- Core principle: CONTEXT IS NOT AUTOMATICALLY EVIDENCE.
-- Every contextual observation is stored as a typed OBSERVATION with an
-- explicit epistemic status. Context records never assert theological or
-- doctrinal claims, never collapse ontological or strict identity, and never
-- derive truth from contextual frequency.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. CREATE DISCOURSE_RUNS TABLE (Execution Ledger for Discourse Analysis)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_runs (
    run_id TEXT PRIMARY KEY,
    source_text_id TEXT REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    tokenization_id TEXT REFERENCES tokenization_runs(tokenization_id) ON DELETE RESTRICT,
    morphology_run_id TEXT REFERENCES morphology_runs(run_id) ON DELETE RESTRICT,
    syntax_run_id TEXT REFERENCES syntax_runs(run_id) ON DELETE RESTRICT,
    semantic_run_id TEXT REFERENCES semantic_runs(run_id) ON DELETE RESTRICT,
    referential_run_id TEXT REFERENCES referential_runs(run_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    analyzer_id TEXT NOT NULL,
    analyzer_version TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    representation_type TEXT NOT NULL CHECK(representation_type IN (
        'RAW', 'NORMALIZED', 'TRANSLITERATED', 'TRANSFORMED'
    )),
    configuration_hash TEXT NOT NULL,
    input_content_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    unit_count INTEGER NOT NULL DEFAULT 0,
    segment_count INTEGER NOT NULL DEFAULT 0,
    relation_count INTEGER NOT NULL DEFAULT 0,
    participant_count INTEGER NOT NULL DEFAULT 0,
    continuity_candidate_count INTEGER NOT NULL DEFAULT 0,
    information_structure_count INTEGER NOT NULL DEFAULT 0,
    ambiguity_count INTEGER NOT NULL DEFAULT 0,
    is_exact_reproducible INTEGER NOT NULL DEFAULT 1 CHECK(is_exact_reproducible IN (0, 1)),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 2. DISCOURSE_UNITS (Clause-Level Discourse Anchor; never a syntax re-parse)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_units (
    unit_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    clause_id TEXT REFERENCES clauses(clause_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    unit_order INTEGER NOT NULL DEFAULT 0 CHECK(unit_order >= 0),
    unit_type TEXT NOT NULL CHECK(unit_type IN (
        'CLAUSE_UNIT',
        'SENTENCE_UNIT',
        'VERSE_UNIT',
        'UTTERANCE_UNIT',
        'PARENTHETICAL_UNIT',
        'QUOTATION_UNIT',
        'OTHER'
    )),
    parent_unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    start_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    end_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    parse_index INTEGER NOT NULL DEFAULT 0 CHECK(parse_index >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 0 CHECK(is_preferred IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_status TEXT NOT NULL DEFAULT '[INFERRED]' CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    language TEXT CHECK(language IS NULL OR language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    raw_unit_surface TEXT NOT NULL,
    observation_note TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(run_id, unit_order, parse_index)
);

-- ----------------------------------------------------------------------------
-- 3. DISCOURSE_SEGMENTS (Higher-Level Grouping; context, not evidence)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_segments (
    segment_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    parent_segment_id TEXT REFERENCES discourse_segments(segment_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
    segment_order INTEGER NOT NULL DEFAULT 0 CHECK(segment_order >= 0),
    segment_type TEXT NOT NULL CHECK(segment_type IN (
        'PROPOSITIONAL',
        'NARRATIVE',
        'DISCOURSE_UNIT',
        'QUOTATION_FRAME',
        'CHAINTING',
        'EPISTOLARY_FRAME',
        'HYMNIC',
        'POLEMIC',
        'EXHORTATIVE',
        'OTHER'
    )),
    start_unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    end_unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    start_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    end_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    parse_index INTEGER NOT NULL DEFAULT 0 CHECK(parse_index >= 0),
    is_preferred INTEGER NOT NULL DEFAULT 0 CHECK(is_preferred IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    evidence_status TEXT NOT NULL DEFAULT '[INFERRED]' CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    language TEXT CHECK(language IS NULL OR language IN (
        'GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC', 'OTHER', 'MULTILINGUAL'
    )),
    raw_segment_surface TEXT NOT NULL,
    observation_note TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(run_id, segment_order, parse_index)
);

-- ----------------------------------------------------------------------------
-- 4. DISCOURSE_RELATIONS (Typed Discourse Links; never morphological inference)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_relations (
    relation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    source_kind TEXT NOT NULL CHECK(source_kind IN ('UNIT', 'SEGMENT')),
    source_ref_id TEXT NOT NULL,
    target_kind TEXT NOT NULL CHECK(target_kind IN ('UNIT', 'SEGMENT')),
    target_ref_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN (
        'ELABORATION',
        'CONTRAST',
        'PARALLEL',
        'RESULT',
        'CAUSE',
        'PURPOSE',
        'CONDITION',
        'CONCESSION',
        'TEMPORAL_SEQUENCE',
        'GROUND',
        'BACKGROUND',
        'MEANS',
        'MANNER',
        'SUMMARY',
        'QUOTATION_FRAME',
        'BOUNDARY_UNRESOLVED',
        'OTHER'
    )),
    directionality TEXT NOT NULL DEFAULT 'FORWARD' CHECK(directionality IN (
        'FORWARD', 'BACKWARD', 'SYMMETRIC', 'UNDIRECTED'
    )),
    grammatical_justification TEXT NOT NULL,
    connector_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    justification_basis TEXT NOT NULL CHECK(justification_basis IN (
        'EXPLICIT_CONJUNCTION',
        'GRAMMATICAL_MARKER',
        'LEXICAL_COHESION',
        'SYNTACTIC_STRUCTURE',
        'INFORMATION_STRUCTURE',
        'MULTIPLE_CONVERGING',
        'UNSPECIFIED_OBSERVATION'
    )),
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    syntax_clause_span_cited INTEGER NOT NULL DEFAULT 0 CHECK(syntax_clause_span_cited IN (0, 1)),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    is_ambiguity_flagged INTEGER NOT NULL DEFAULT 0 CHECK(is_ambiguity_flagged IN (0, 1)),
    observation_note TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    -- A discourse relation must never be self-referential.
    CHECK(source_ref_id != target_ref_id OR source_kind != target_kind),

    -- Discourse relations are not derivable from morphology alone: when a
    -- relation is justified by a conjunction or grammatical marker, the
    -- actual connector token must be cited as an anchor.
    CHECK(
        justification_basis NOT IN ('EXPLICIT_CONJUNCTION', 'GRAMMATICAL_MARKER')
        OR connector_token_id IS NOT NULL
    )
);

-- ----------------------------------------------------------------------------
-- 5. DISCOURSE_CONTEXT_LAYERS (Immediate / Pericope / Book / Corpus)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_context_layers (
    context_layer_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    layer_scope TEXT NOT NULL CHECK(layer_scope IN (
        'IMMEDIATE',
        'PERICOPE',
        'BOOK',
        'CORPUS',
        'UNRESOLVED'
    )),
    anchor_unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    anchor_segment_id TEXT REFERENCES discourse_segments(segment_id) ON DELETE RESTRICT,
    anchor_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    anchor_pericope_id TEXT REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    anchor_book_id TEXT REFERENCES books(book_id) ON DELETE RESTRICT,
    span_start_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    span_end_passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    scope_declared INTEGER NOT NULL DEFAULT 1 CHECK(scope_declared IN (0, 1)),
    observation_kind TEXT NOT NULL CHECK(observation_kind IN (
        'PARTICIPANT_CONTINUITY',
        'TOPIC_CONTINUITY',
        'LEXICAL_REPETITION',
        'SYNTACTIC_PATTERN',
        'GENRE_FRAME',
        'QUOTATION_FRAME',
        'ARGUMENT_PROGRESSION',
        'BOUNDARY_OBSERVATION',
        'OTHER'
    )),
    observation TEXT NOT NULL,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    is_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_evidence = 0),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 6. DISCOURSE_PARTICIPANTS (Speaker / Addressee / Referent Role Inventory)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_participants (
    participant_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    segment_id TEXT REFERENCES discourse_segments(segment_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    entity_id TEXT REFERENCES entities(entity_id) ON DELETE RESTRICT,
    entity_mention_id TEXT REFERENCES entity_mentions(mention_id) ON DELETE RESTRICT,
    participant_role TEXT NOT NULL CHECK(participant_role IN (
        'SPEAKER',
        'ADDRESSEE',
        'THIRD_PARTY',
        'NARRATOR',
        'AUTHORIAL_VOICE',
        'QUOTED_SPEAKER',
        'COLLECTIVE_SPEAKER',
        'INDETERMINATE',
        'OTHER'
    )),
    role_status TEXT NOT NULL DEFAULT 'OBSERVED' CHECK(role_status IN (
        'OBSERVED', 'DECLARED', 'INFERRED', 'CONTESTED', 'UNRESOLVED'
    )),
    grammatical_person TEXT CHECK(grammatical_person IS NULL OR grammatical_person IN (
        'FIRST', 'SECOND', 'THIRD', 'IMPERSONAL', 'UNSPECIFIED'
    )),
    grammatical_number TEXT CHECK(grammatical_number IS NULL OR grammatical_number IN (
        'SINGULAR', 'DUAL', 'PLURAL', 'UNSPECIFIED'
    )),
    anchor_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    identity_asserted INTEGER NOT NULL DEFAULT 0 CHECK(identity_asserted = 0),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 7. REFERENTIAL_CONTINUITY_CANDIDATES
--    Anaphoric / Cataphoric / Deictic reference CANDIDATES.
--    Multiple competing antecedents must remain representable (no forced pick).
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS referential_continuity_candidates (
    candidate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    referring_token_id TEXT NOT NULL REFERENCES tokens(token_id) ON DELETE RESTRICT,
    referring_mention_id TEXT REFERENCES entity_mentions(mention_id) ON DELETE RESTRICT,
    unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    continuity_type TEXT NOT NULL CHECK(continuity_type IN (
        'ANAPHORIC',
        'CATAPHORIC',
        'DEICTIC',
        'EXOPHORIC',
        'DISCOURSE_DEICTIC',
        'UNRESOLVED'
    )),
    candidate_antecedent_token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    candidate_antecedent_entity_id TEXT REFERENCES entities(entity_id) ON DELETE RESTRICT,
    candidate_antecedent_unit_id TEXT REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    antecedent_distance_tokens INTEGER CHECK(antecedent_distance_tokens IS NULL OR antecedent_distance_tokens >= 0),
    candidate_rank INTEGER NOT NULL DEFAULT 1 CHECK(candidate_rank >= 1),
    is_resolved INTEGER NOT NULL DEFAULT 0 CHECK(is_resolved IN (0, 1)),
    resolution_status TEXT NOT NULL CHECK(resolution_status IN (
        'CANDIDATE_SET',
        'PREFERRED_CANDIDATE',
        'UNRESOLVED_AMBIGUOUS',
        'NO_CANDIDATE',
        'CONTESTED'
    )),
    multiplicity_preserved INTEGER NOT NULL DEFAULT 1 CHECK(multiplicity_preserved = 1),
    resolution_rationale TEXT,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    identity_asserted INTEGER NOT NULL DEFAULT 0 CHECK(identity_asserted = 0),
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT,

    UNIQUE(run_id, referring_token_id, candidate_rank),
    -- A resolved candidate must have an actual antecedent anchor.
    CHECK(is_resolved = 0 OR (
        candidate_antecedent_token_id IS NOT NULL
        OR candidate_antecedent_entity_id IS NOT NULL
        OR candidate_antecedent_unit_id IS NOT NULL
    ))
);

-- ----------------------------------------------------------------------------
-- 8. INFORMATION_STRUCTURE (Topic / Focus / Prominence Foundation)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS information_structure (
    info_structure_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    unit_id TEXT NOT NULL REFERENCES discourse_units(unit_id) ON DELETE RESTRICT,
    passage_id TEXT REFERENCES passages(passage_id) ON DELETE RESTRICT,
    token_id TEXT REFERENCES tokens(token_id) ON DELETE RESTRICT,
    constituent_id TEXT REFERENCES syntactic_constituents(constituent_id) ON DELETE RESTRICT,
    information_role TEXT NOT NULL CHECK(information_role IN (
        'TOPIC',
        'FOCUS',
        'THEME',
        'RHEME',
        'GIVEN',
        'NEW',
        'CONTRASTIVE_FOCUS',
        'TAIL',
        'SETTING',
        'UNMARKED',
        'UNDETERMINED'
    )),
    markedness TEXT NOT NULL DEFAULT 'MARKEDNESS_UNDETERMINED' CHECK(markedness IN (
        'MARKED',
        'UNMARKED',
        'MARKEDNESS_UNDETERMINED'
    )),
    marking_device TEXT NOT NULL DEFAULT 'NONE_OBSERVED' CHECK(marking_device IN (
        'WORD_ORDER',
        'PARTICLE',
        'DETERMINER_USE',
        'PRONOMINAL_FORM',
        'FRONTING',
        'POSTPOSITION',
        'VERBAL_FORM',
        'MULTIPLE_DEVICES',
        'NONE_OBSERVED'
    )),
    syntax_clause_id TEXT REFERENCES clauses(clause_id) ON DELETE RESTRICT,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    confidence_score REAL CHECK(confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    confidence_level TEXT NOT NULL DEFAULT 'PROVISIONAL' CHECK(confidence_level IN (
        'CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED', 'AMBIGUOUS'
    )),
    observation_note TEXT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 9. DISCOURSE_AMBIGUITIES (Unresolved Ambiguity Must Remain Representable)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS discourse_ambiguities (
    ambiguity_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES discourse_runs(run_id) ON DELETE RESTRICT,
    source_text_id TEXT NOT NULL REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    version_id TEXT NOT NULL REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    provenance_id TEXT NOT NULL REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    ambiguity_type TEXT NOT NULL CHECK(ambiguity_type IN (
        'UNIT_BOUNDARY',
        'SEGMENT_BOUNDARY',
        'RELATION_TYPE',
        'RELATION_DIRECTION',
        'PARTICIPANT_ROLE',
        'ANAPHORIC_ANTECEDENT',
        'DEICTIC_ANCHOR',
        'INFORMATION_ROLE',
        'CONTEXT_LAYER_SCOPE',
        'OTHER'
    )),
    subject_ref_id TEXT NOT NULL,
    competing_interpretations_json TEXT NOT NULL,
    competing_interpretation_count INTEGER NOT NULL DEFAULT 0 CHECK(competing_interpretation_count >= 0),
    resolution_status TEXT NOT NULL DEFAULT 'UNRESOLVED' CHECK(resolution_status IN (
        'UNRESOLVED', 'PARTIALLY_RESOLVED', 'RESOLVED', 'PERMANENTLY_UNDECIDABLE'
    )),
    preservation_required INTEGER NOT NULL DEFAULT 1 CHECK(preservation_required = 1),
    collapse_prohibited INTEGER NOT NULL DEFAULT 1 CHECK(collapse_prohibited = 1),
    description TEXT NOT NULL,
    evidence_status TEXT NOT NULL DEFAULT '[AMBIGUOUS]' CHECK(evidence_status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    evidence_id TEXT REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    metadata_json TEXT
);

-- ----------------------------------------------------------------------------
-- 10. INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_discourse_runs_source ON discourse_runs(source_text_id);
CREATE INDEX IF NOT EXISTS idx_discourse_runs_syntax ON discourse_runs(syntax_run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_runs_semantic ON discourse_runs(semantic_run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_runs_referential ON discourse_runs(referential_run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_units_run ON discourse_units(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_units_clause ON discourse_units(clause_id);
CREATE INDEX IF NOT EXISTS idx_discourse_units_passage ON discourse_units(passage_id);
CREATE INDEX IF NOT EXISTS idx_discourse_units_parent ON discourse_units(parent_unit_id);
CREATE INDEX IF NOT EXISTS idx_discourse_segments_run ON discourse_segments(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_segments_pericope ON discourse_segments(pericope_id);
CREATE INDEX IF NOT EXISTS idx_discourse_segments_parent ON discourse_segments(parent_segment_id);
CREATE INDEX IF NOT EXISTS idx_discourse_relations_run ON discourse_relations(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_relations_type ON discourse_relations(relation_type);
CREATE INDEX IF NOT EXISTS idx_discourse_relations_source ON discourse_relations(source_ref_id);
CREATE INDEX IF NOT EXISTS idx_discourse_relations_target ON discourse_relations(target_ref_id);
CREATE INDEX IF NOT EXISTS idx_discourse_relations_evidence ON discourse_relations(evidence_id);
CREATE INDEX IF NOT EXISTS idx_discourse_context_run ON discourse_context_layers(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_context_scope ON discourse_context_layers(layer_scope);
CREATE INDEX IF NOT EXISTS idx_discourse_context_evidence ON discourse_context_layers(evidence_id);
CREATE INDEX IF NOT EXISTS idx_discourse_participants_run ON discourse_participants(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_participants_entity ON discourse_participants(entity_id);
CREATE INDEX IF NOT EXISTS idx_discourse_participants_role ON discourse_participants(participant_role);
CREATE INDEX IF NOT EXISTS idx_continuity_candidates_run ON referential_continuity_candidates(run_id);
CREATE INDEX IF NOT EXISTS idx_continuity_candidates_token ON referential_continuity_candidates(referring_token_id);
CREATE INDEX IF NOT EXISTS idx_continuity_candidates_entity ON referential_continuity_candidates(candidate_antecedent_entity_id);
CREATE INDEX IF NOT EXISTS idx_information_structure_run ON information_structure(run_id);
CREATE INDEX IF NOT EXISTS idx_information_structure_unit ON information_structure(unit_id);
CREATE INDEX IF NOT EXISTS idx_information_structure_role ON information_structure(information_role);
CREATE INDEX IF NOT EXISTS idx_discourse_ambiguities_run ON discourse_ambiguities(run_id);
CREATE INDEX IF NOT EXISTS idx_discourse_ambiguities_type ON discourse_ambiguities(ambiguity_type);
CREATE INDEX IF NOT EXISTS idx_discourse_ambiguities_status ON discourse_ambiguities(resolution_status);

-- ----------------------------------------------------------------------------
-- 11. IMMUTABILITY TRIGGERS
-- ----------------------------------------------------------------------------

CREATE TRIGGER IF NOT EXISTS trg_discourse_runs_no_delete
BEFORE DELETE ON discourse_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse runs are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_runs_immutable_fields
BEFORE UPDATE ON discourse_runs
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse runs are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_units_no_delete
BEFORE DELETE ON discourse_units
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse units are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_units_immutable_fields
BEFORE UPDATE ON discourse_units
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse units are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_segments_no_delete
BEFORE DELETE ON discourse_segments
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse segments are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_segments_immutable_fields
BEFORE UPDATE ON discourse_segments
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse segments are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_relations_no_delete
BEFORE DELETE ON discourse_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse relations are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_relations_immutable_fields
BEFORE UPDATE ON discourse_relations
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse relations are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_context_no_delete
BEFORE DELETE ON discourse_context_layers
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse context layers are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_context_immutable_fields
BEFORE UPDATE ON discourse_context_layers
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse context layers are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_participants_no_delete
BEFORE DELETE ON discourse_participants
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse participants are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_participants_immutable_fields
BEFORE UPDATE ON discourse_participants
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse participants are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_continuity_candidates_no_delete
BEFORE DELETE ON referential_continuity_candidates
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential continuity candidates are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_continuity_candidates_immutable_fields
BEFORE UPDATE ON referential_continuity_candidates
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Referential continuity candidates are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_information_structure_no_delete
BEFORE DELETE ON information_structure
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Information structure records are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_information_structure_immutable_fields
BEFORE UPDATE ON information_structure
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Information structure records are immutable: UPDATE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_ambiguities_no_delete
BEFORE DELETE ON discourse_ambiguities
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse ambiguities are immutable: DELETE is strictly prohibited.');
END;

CREATE TRIGGER IF NOT EXISTS trg_discourse_ambiguities_immutable_fields
BEFORE UPDATE ON discourse_ambiguities
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Discourse ambiguities are immutable: UPDATE is strictly prohibited.');
END;
