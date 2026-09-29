-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- FOUNDATION RELATIONAL SCHEMA (Task 1.1)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Typing & Foreign Keys Enforced) / ANSI PostgreSQL Compatible
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- 1. SYSTEM, MIGRATIONS & SCHEMA VERSIONING
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,          -- e.g. "001_initial_schema"
    version TEXT NOT NULL,                  -- e.g. "2.0.0"
    applied_at TEXT NOT NULL,               -- ISO 8601 UTC timestamp
    checksum_sha256 TEXT NOT NULL,          -- Hash of the migration script
    description TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 2. CORPUS HIERARCHY & CANON STRUCTURE
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS canons (
    canon_id TEXT PRIMARY KEY,              -- e.g. "PROTESTANT_66", "CATHOLIC_73", "EASTERN_ORTHODOX_79"
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS testaments (
    testament_id TEXT PRIMARY KEY,          -- e.g. "OLD_TESTAMENT", "NEW_TESTAMENT"
    canon_id TEXT NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL,
    FOREIGN KEY (canon_id) REFERENCES canons(canon_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,               -- e.g. "GEN", "PSA", "MAT", "JOH", "REV"
    testament_id TEXT NOT NULL,
    canonical_order INTEGER NOT NULL UNIQUE,
    standard_name TEXT NOT NULL UNIQUE,     -- Complete official Indonesian name e.g. "Kejadian", "Wahyu"
    english_name TEXT NOT NULL,             -- e.g. "Genesis", "Revelation"
    original_primary_language TEXT NOT NULL CHECK(original_primary_language IN ('HEBREW', 'ARAMAIC', 'GREEK')),
    chapter_count INTEGER NOT NULL,
    FOREIGN KEY (testament_id) REFERENCES testaments(testament_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS sections (
    section_id TEXT PRIMARY KEY,            -- e.g. "SEC-REV-19-01-10"
    book_id TEXT NOT NULL,
    title TEXT NOT NULL,
    start_chapter INTEGER NOT NULL,
    start_verse INTEGER NOT NULL,
    end_chapter INTEGER NOT NULL,
    end_verse INTEGER NOT NULL,
    genre TEXT NOT NULL,                    -- e.g. "APOCALYPTIC", "EPISTLE", "NARRATIVE", "POETRY", "LEGAL"
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT
);

-- Primary unit of exegesis (Clause 16–17)
CREATE TABLE IF NOT EXISTS pericopes (
    pericope_id TEXT PRIMARY KEY,           -- e.g. "PER-REV-19-07-09"
    book_id TEXT NOT NULL,
    reference TEXT NOT NULL,                -- Complete citation e.g. "Wahyu 19:7-9"
    start_chapter INTEGER NOT NULL,
    start_verse INTEGER NOT NULL,
    end_chapter INTEGER NOT NULL,
    end_verse INTEGER NOT NULL,
    genre TEXT NOT NULL,
    boundary_source TEXT NOT NULL,          -- e.g. "NA28_SECTION", "UBS5", "TR_TRADITION", "USER_DEFINED"
    boundary_confidence TEXT NOT NULL CHECK(boundary_confidence IN ('HIGH', 'MEDIUM', 'LOW', 'BOUNDARY_UNCERTAIN')),
    status TEXT NOT NULL CHECK(status IN ('REGISTERED', 'INGESTED', 'ANNOTATED', 'VALIDATED', 'NEEDS_REVIEW')),
    version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS passages (
    passage_id TEXT PRIMARY KEY,            -- Canonical verse address e.g. "REV-19-08"
    pericope_id TEXT NOT NULL,
    book_id TEXT NOT NULL,
    chapter INTEGER NOT NULL,
    verse INTEGER NOT NULL,
    sort_order INTEGER NOT NULL UNIQUE,
    FOREIGN KEY (pericope_id) REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT,
    UNIQUE(book_id, chapter, verse)
);

-- ----------------------------------------------------------------------------
-- 3. PROVENANCE, WITNESSES & CRITICAL EDITIONS (LEVEL 0 / LEVEL 1)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS witnesses (
    witness_id TEXT PRIMARY KEY,            -- e.g. "MS-ALEPH-01" (Codex Sinaiticus), "MS-B-03" (Codex Vaticanus), "DSS-1QISA-A"
    siglum TEXT NOT NULL UNIQUE,            -- e.g. "א", "B", "1QIsa-a", "P46", "P75"
    name TEXT NOT NULL,
    witness_type TEXT NOT NULL CHECK(witness_type IN ('PAPYRUS', 'UNCIAL', 'MINUSCULE', 'LECTIONARY', 'DEAD_SEA_SCROLL', 'MASORETIC_CODEX', 'INSCRIPTION', 'EARLY_TRANSLATION')),
    language TEXT NOT NULL CHECK(language IN ('GREEK', 'HEBREW', 'ARAMAIC', 'LATIN', 'SYRIAC', 'COPTIC')),
    century_origin TEXT NOT NULL,           -- e.g. "IV CE", "II-III CE", "II BCE"
    dating_estimate_start INTEGER,
    dating_estimate_end INTEGER,
    repository TEXT,                        -- e.g. "British Library Add MS 43725"
    provenance_hash TEXT NOT NULL,          -- SHA-256 hash of witness digital record
    is_source_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_source_immutable = 1)
);

CREATE TABLE IF NOT EXISTS critical_editions (
    edition_id TEXT PRIMARY KEY,            -- e.g. "ED-NA28", "ED-UBS5", "ED-BHS", "ED-BHQ", "ED-BYZ2018", "ED-TR1550"
    name TEXT NOT NULL,
    scholarly_apparatus TEXT NOT NULL,      -- e.g. "Nestle-Aland 28th Edition", "Biblia Hebraica Stuttgartensia"
    publication_year INTEGER NOT NULL,
    publisher TEXT NOT NULL,
    source_language TEXT NOT NULL CHECK(source_language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    provenance_hash TEXT NOT NULL,
    is_source_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_source_immutable = 1)
);

-- Source string level (Immutable Level 0 / 1)
CREATE TABLE IF NOT EXISTS source_texts (
    source_text_id TEXT PRIMARY KEY,        -- e.g. "ST-REV-19-08-NA28"
    passage_id TEXT NOT NULL,
    edition_id TEXT,                        -- NULL if raw witness
    witness_id TEXT,                        -- NULL if critical composite edition
    source_type TEXT NOT NULL CHECK(source_type IN ('CRITICAL_EDITION', 'PRIMARY_WITNESS', 'USER_SUPPLIED_CANDIDATE')),
    language TEXT NOT NULL CHECK(language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    raw_source_string TEXT NOT NULL,        -- Exact immutable original character stream
    normalized_source_string TEXT NOT NULL,
    sha256_hash TEXT NOT NULL UNIQUE,       -- Cryptographic verification of immutability
    created_at TEXT NOT NULL,
    is_immutable INTEGER NOT NULL DEFAULT 1 CHECK(is_immutable = 1),
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT,
    FOREIGN KEY (edition_id) REFERENCES critical_editions(edition_id) ON DELETE RESTRICT,
    FOREIGN KEY (witness_id) REFERENCES witnesses(witness_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 4. TEXTUAL CRITICISM & VARIANT UNITS (Clause 18, 42.8)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS variant_units (
    variant_unit_id TEXT PRIMARY KEY,       -- e.g. "VAR-REV-19-08-01"
    passage_id TEXT NOT NULL,
    word_position_start INTEGER NOT NULL,
    word_position_end INTEGER NOT NULL,
    base_text_reading TEXT NOT NULL,        -- Reading in the base critical edition
    critical_significance TEXT NOT NULL CHECK(critical_significance IN ('HIGH', 'MEDIUM', 'LOW', 'ORTHOGRAPHIC_ONLY')),
    editorial_status TEXT NOT NULL CHECK(editorial_status IN ('CERTAIN', 'PROBABLE', 'UNCERTAIN', 'DISPUTED')),
    notes TEXT,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS variant_readings (
    reading_id TEXT PRIMARY KEY,            -- e.g. "READ-REV-19-08-01-A"
    variant_unit_id TEXT NOT NULL,
    reading_siglum TEXT NOT NULL,           -- e.g. "Reading A", "Reading B"
    greek_or_hebrew_string TEXT NOT NULL,
    external_evidence_summary TEXT NOT NULL,-- e.g. "א, A, 046, 1611, 2329"
    internal_evidence_evaluation TEXT NOT NULL,
    reading_category TEXT NOT NULL CHECK(reading_category IN ('ORIGINAL_PREFERRED', 'MAJORITY_READING', 'EARLY_CORRECTION', 'SCRIBAL_HARMONIZATION', 'ORTHOGRAPHIC_VARIANT')),
    reading_confidence TEXT NOT NULL CHECK(reading_confidence IN ('VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'AMBIGUOUS')),
    FOREIGN KEY (variant_unit_id) REFERENCES variant_units(variant_unit_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS variant_witness_attestations (
    attestation_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL,
    witness_id TEXT NOT NULL,
    folio_or_page TEXT,
    is_correction INTEGER NOT NULL DEFAULT 0 CHECK(is_correction IN (0, 1)),
    transcription_text TEXT,
    FOREIGN KEY (reading_id) REFERENCES variant_readings(reading_id) ON DELETE CASCADE,
    FOREIGN KEY (witness_id) REFERENCES witnesses(witness_id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------------
-- 5. LINGUISTIC TOKENS, MORPHOLOGY & SYNTAX (LEVEL 2)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS lemmas (
    lemma_id TEXT PRIMARY KEY,              -- e.g. "LEM-G1039", "LEM-G1345"
    language TEXT NOT NULL CHECK(language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    lemma_string TEXT NOT NULL,             -- Lexical form e.g. "βύσσινος", "δικαίωμα"
    strong_code TEXT,                       -- e.g. "G1039", "H7225"
    lexical_category TEXT NOT NULL,         -- e.g. "NOUN", "VERB", "ADJECTIVE", "PARTICLE"
    bdb_entry_id TEXT,
    halot_entry_id TEXT,
    bdag_entry_id TEXT,
    thayer_entry_id TEXT,
    lsj_entry_id TEXT,
    UNIQUE(language, lemma_string)
);

CREATE TABLE IF NOT EXISTS tokens (
    token_id TEXT PRIMARY KEY,              -- e.g. "TOK-REV-19-08-005"
    source_text_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    position INTEGER NOT NULL,              -- 1-indexed token offset in verse
    surface_original TEXT NOT NULL,         -- Exact string with punctuation
    surface_cleaned TEXT NOT NULL,          -- String without punctuation/accents
    lemma_id TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('GREEK', 'HEBREW', 'ARAMAIC')),
    FOREIGN KEY (source_text_id) REFERENCES source_texts(source_text_id) ON DELETE RESTRICT,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT,
    FOREIGN KEY (lemma_id) REFERENCES lemmas(lemma_id) ON DELETE RESTRICT,
    UNIQUE(source_text_id, position)
);

CREATE TABLE IF NOT EXISTS morphology_annotations (
    annotation_id TEXT PRIMARY KEY,
    token_id TEXT NOT NULL UNIQUE,
    pos_tag TEXT NOT NULL,                  -- Part of speech e.g. "N-NNS", "V-AIA-3S"
    grammatical_case TEXT CHECK(grammatical_case IN ('NOMINATIVE', 'GENITIVE', 'DATIVE', 'ACCUSATIVE', 'VOCATIVE', 'ABSOLUTE', 'CONSTRUCT')),
    gender TEXT CHECK(gender IN ('MASCULINE', 'FEMININE', 'NEUTER', 'COMMON')),
    number TEXT CHECK(number IN ('SINGULAR', 'PLURAL', 'DUAL')),
    person TEXT CHECK(person IN ('FIRST', 'SECOND', 'THIRD')),
    tense_form TEXT,                        -- e.g. "PRESENT", "IMPERFECT", "AORIST", "PERFECT", "QAL", "PIEL", "HIPHIL"
    aspect TEXT CHECK(aspect IN ('PERFECTIVE', 'IMPERFECTIVE', 'STATIVE', 'INGRESSIVE', 'DURATIVE', 'UNKNOWN')),
    voice TEXT CHECK(voice IN ('ACTIVE', 'MIDDLE', 'PASSIVE', 'MIDDLE_PASSIVE')),
    mood TEXT CHECK(mood IN ('INDICATIVE', 'SUBJUNCTIVE', 'OPTATIVE', 'IMPERATIVE', 'INFINITIVE', 'PARTICIPLE')),
    declension TEXT,
    literal_gloss TEXT NOT NULL,
    syntactic_role TEXT NOT NULL,           -- e.g. "SUBJECT", "PREDICATE_NOMINATIVE", "DIRECT_OBJECT"
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'HIGH', 'PROVISIONAL', 'DISPUTED')),
    analyzer_provenance TEXT NOT NULL,      -- Engine or model producing annotation
    FOREIGN KEY (token_id) REFERENCES tokens(token_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clauses (
    clause_id TEXT PRIMARY KEY,             -- e.g. "CLS-REV-19-08-01"
    passage_id TEXT NOT NULL,
    clause_order INTEGER NOT NULL,
    clause_type TEXT NOT NULL CHECK(clause_type IN ('INDEPENDENT', 'SUBORDINATE_PURPOSE', 'SUBORDINATE_CAUSAL', 'SUBORDINATE_RELATIVE', 'SUBORDINATE_TEMPORAL', 'PARTICIPIAL_CONSTRUCTION', 'CONDITIONAL_PROTASIS', 'CONDITIONAL_APODOSIS')),
    lead_conjunction TEXT,                  -- e.g. "γὰρ", "ἵνα", "ὅτι"
    raw_clause_string TEXT NOT NULL,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS syntax_trees (
    syntax_node_id TEXT PRIMARY KEY,
    clause_id TEXT NOT NULL,
    head_token_id TEXT,                     -- NULL if root of clause
    dependent_token_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,            -- Dependency relation e.g. "COPULA", "PREDICATE", "MODIFIER", "GENITIVE_ATTRIBUTIVE", "GENITIVE_POSSESSIVE", "GENITIVE_SOURCE", "APPOSITION", "OBJECT"
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'HIGH', 'AMBIGUOUS')),
    is_alternative_parse INTEGER NOT NULL DEFAULT 0 CHECK(is_alternative_parse IN (0, 1)),
    FOREIGN KEY (clause_id) REFERENCES clauses(clause_id) ON DELETE CASCADE,
    FOREIGN KEY (head_token_id) REFERENCES tokens(token_id) ON DELETE CASCADE,
    FOREIGN KEY (dependent_token_id) REFERENCES tokens(token_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 6. SEMANTICS, ENTITIES & REFERENTIAL IDENTITY (LEVEL 3)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS semantic_senses (
    sense_id TEXT PRIMARY KEY,
    lemma_id TEXT NOT NULL,
    sense_label TEXT NOT NULL,              -- e.g. "righteous_actions", "fine_linen"
    definition TEXT NOT NULL,
    contemporary_domain TEXT NOT NULL,      -- 1st century Hellenistic / Semitic usage
    lexicon_source TEXT NOT NULL,           -- e.g. "BDAG p. 249", "HALOT p. 112"
    FOREIGN KEY (lemma_id) REFERENCES lemmas(lemma_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,             -- e.g. "ENT-BRIDE", "ENT-SAINTS", "ENT-LAMB", "ENT-NEW_JERUSALEM"
    standard_name TEXT NOT NULL UNIQUE,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('DIVINE', 'HUMAN_INDIVIDUAL', 'CORPORATE_COMMUNITY', 'CITY_PERSONIFICATION', 'SYMBOLIC_FIGURE', 'LOCATION', 'OBJECT')),
    ontological_category TEXT NOT NULL CHECK(ontological_category IN ('LITERAL_ENTITY', 'PERSONIFICATION', 'METAPHOR', 'SYMBOL', 'VISIONARY_REPRESENTATION', 'TYPOLOGY', 'UNKNOWN')),
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entity_mentions (
    mention_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    token_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    referential_status TEXT NOT NULL CHECK(referential_status IN ('EXPLICIT_NAMING', 'PRONOMINAL_REFERENCE', 'SYMBOLIC_ASSOCIATION', 'TYPOLOGICAL_FIGURE')),
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'STRONG', 'AMBIGUOUS', 'UNSUPPORTED')),
    FOREIGN KEY (entity_id) REFERENCES entities(entity_id) ON DELETE RESTRICT,
    FOREIGN KEY (token_id) REFERENCES tokens(token_id) ON DELETE CASCADE,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT
);

-- Referential Firewall: Prevents illicit association -> identity collapse (Clause 20, 25)
CREATE TABLE IF NOT EXISTS referential_relations (
    relation_id TEXT PRIMARY KEY,
    source_entity_id TEXT NOT NULL,
    target_entity_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK(relation_type IN ('MENTION', 'REFERENCE', 'ASSOCIATION', 'REPRESENTATION', 'STRICT_IDENTITY')),
    grammatical_justification TEXT NOT NULL,
    evidence_status TEXT NOT NULL CHECK(evidence_status IN ('[EXPLICIT]', '[GRAMMATICALLY ESTABLISHED]', '[INFERRED]', '[PLAUSIBLE]', '[AMBIGUOUS]', '[UNSUPPORTED]', '[CONTRADICTED]')),
    is_identity_established INTEGER NOT NULL DEFAULT 0 CHECK(is_identity_established IN (0, 1)),
    FOREIGN KEY (source_entity_id) REFERENCES entities(entity_id) ON DELETE RESTRICT,
    FOREIGN KEY (target_entity_id) REFERENCES entities(entity_id) ON DELETE RESTRICT,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT,
    CHECK(relation_type != 'STRICT_IDENTITY' OR is_identity_established = 1)
);

-- ----------------------------------------------------------------------------
-- 7. EVIDENCE LEDGER & EPISTEMIC TYPING (LEVEL 3 / LEVEL 4)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_ledger (
    evidence_id TEXT PRIMARY KEY,           -- e.g. "EVID-REV-19-08-001"
    pericope_id TEXT NOT NULL,
    passage_id TEXT NOT NULL,
    evidence_class TEXT NOT NULL CHECK(evidence_class IN (
        'E1_DIRECT_SOURCE_STRING',
        'E2_MANUSCRIPT_WITNESS',
        'E3_MORPHOLOGICAL_FORM',
        'E4_SYNTACTIC_STRUCTURE',
        'E5_LEXICAL_SEMANTIC_RANGE',
        'E6_CONTEMPORARY_LINGUISTIC',
        'E7_HISTORICAL_CULTURAL',
        'E8_LITERARY_CONTEXT',
        'E9_INTERTEXTUAL_ALLUSION',
        'E10_SECONDARY_SCHOLARSHIP',
        'E11_THEOLOGICAL_INTERPRETATION'
    )),
    epistemic_tier TEXT NOT NULL CHECK(epistemic_tier IN (
        'TIER_0_RAW_OBSERVATION',
        'TIER_1_LINGUISTIC_FACT',
        'TIER_2_CONTEXTUAL_CLAIM',
        'TIER_3_INTERPRETIVE_CLAIM',
        'TIER_4_THEOLOGICAL_CLAIM'
    )),
    source_reference TEXT NOT NULL,         -- String citation, MSS siglum, or verse address
    extracted_text_or_data TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        '[EXPLICIT]',
        '[GRAMMATICALLY ESTABLISHED]',
        '[LEXICALLY SUPPORTED]',
        '[CONTEXTUALLY STRONG]',
        '[INFERRED]',
        '[PLAUSIBLE]',
        '[AMBIGUOUS]',
        '[UNSUPPORTED]',
        '[CONTRADICTED]'
    )),
    confidence TEXT NOT NULL CHECK(confidence IN ('CERTAIN', 'VERY_HIGH', 'HIGH', 'MEDIUM', 'LOW', 'UNSUPPORTED')),
    is_counter_evidence INTEGER NOT NULL DEFAULT 0 CHECK(is_counter_evidence IN (0, 1)),
    created_at TEXT NOT NULL,
    provenance_hash TEXT NOT NULL,
    FOREIGN KEY (pericope_id) REFERENCES pericopes(pericope_id) ON DELETE RESTRICT,
    FOREIGN KEY (passage_id) REFERENCES passages(passage_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,              -- e.g. "CLM-REV-19-08-01"
    pericope_id TEXT NOT NULL,
    claim_tier TEXT NOT NULL CHECK(claim_tier IN (
        'TIER_0_RAW_OBSERVATION',
        'TIER_1_LINGUISTIC_FACT',
        'TIER_2_CONTEXTUAL_CLAIM',
        'TIER_3_INTERPRETIVE_CLAIM',
        'TIER_4_THEOLOGICAL_CLAIM'
    )),
    claim_text TEXT NOT NULL,
    claimed_by TEXT NOT NULL,               -- e.g. "USER_HYPOTHESIS", "EXEGESIS_ENGINE", "SCHOLAR_X"
    epistemic_status TEXT NOT NULL CHECK(epistemic_status IN ('VERIFIED_FACT', 'STRONG_INFERENCE', 'POSSIBLE_INTERPRETATION', 'UNPROVEN_DOGMA', 'CONTRADICTED_BY_TEXT')),
    doctrinal_system TEXT,                  -- Optional denomination/doctrine if theological claim
    is_theology_independent INTEGER NOT NULL DEFAULT 0 CHECK(is_theology_independent IN (0, 1)),
    FOREIGN KEY (pericope_id) REFERENCES pericopes(pericope_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS claim_evidence_links (
    link_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    relationship TEXT NOT NULL CHECK(relationship IN ('SUPPORTS', 'CONTRADICTS', 'QUALIFIES', 'IRRELEVANT')),
    reasoning TEXT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence_ledger(evidence_id) ON DELETE RESTRICT,
    UNIQUE(claim_id, evidence_id)
);

-- ----------------------------------------------------------------------------
-- 8. EXEGESIS, TRANSLATIONS & VALIDATION GATES (LEVEL 4 / LEVEL 5)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS translations (
    translation_id TEXT PRIMARY KEY,
    pericope_id TEXT NOT NULL,
    translation_type TEXT NOT NULL CHECK(translation_type IN ('SOURCE_ORIENTED_LITERAL', 'NATURAL_INDONESIAN', 'HISTORICAL_VULGATE', 'HISTORICAL_SEPTUAGINT', 'POPULAR_LAI_TB', 'POPULAR_KJV')),
    translated_text TEXT NOT NULL,
    translation_notes TEXT,
    language_target TEXT NOT NULL,
    is_primary_source INTEGER NOT NULL DEFAULT 0 CHECK(is_primary_source = 0), -- Guard: Translations can NEVER be primary source
    FOREIGN KEY (pericope_id) REFERENCES pericopes(pericope_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS exegesis_reports (
    report_id TEXT PRIMARY KEY,             -- e.g. "RPT-REV-19-08-V2"
    pericope_id TEXT NOT NULL,
    report_version TEXT NOT NULL,
    rendered_20_section_markdown TEXT NOT NULL,
    what_text_actually_says TEXT NOT NULL,  -- Section 16
    what_reasonably_inferred TEXT NOT NULL, -- Section 17
    what_text_does_not_establish TEXT NOT NULL, -- Section 18 (Mandatory firewall)
    final_conclusion TEXT NOT NULL,         -- Section 19
    overall_confidence TEXT NOT NULL CHECK(overall_confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    orchestrator_agent TEXT NOT NULL,       -- e.g. "AGY", "HERMES_WORKFLOW"
    model_version TEXT NOT NULL,
    provenance_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    validation_status TEXT NOT NULL CHECK(validation_status IN ('PENDING', 'PASS', 'PASS_WITH_WARNINGS', 'NEEDS_REVISION', 'BLOCKED', 'FAILED')),
    FOREIGN KEY (pericope_id) REFERENCES pericopes(pericope_id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS validation_gate_results (
    gate_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    gate_layer TEXT NOT NULL CHECK(gate_layer IN (
        'V1_SOURCE_INTEGRITY',
        'V2_TEXTUAL_CRITICISM',
        'V3_MORPHOLOGY_PRECISION',
        'V4_SYNTAX_COHERENCE',
        'V5_SEMANTIC_FALLACY_CHECK',
        'V6_CONTEXT_PROGRESSION',
        'V7_EVIDENCE_TRACEABILITY',
        'V8_REASONING_AND_FIREWALL',
        'V9_PROVENANCE_HASH',
        'V10_20_SECTION_TEMPLATE_COMPLIANCE'
    )),
    status TEXT NOT NULL CHECK(status IN ('PASS', 'WARN', 'FAIL')),
    diagnostic_details TEXT NOT NULL,
    tested_at TEXT NOT NULL,
    FOREIGN KEY (report_id) REFERENCES exegesis_reports(report_id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------------
-- 9. AUDIT LOG & REPRODUCIBILITY (IMMUTABILITY LEDGER)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('INSERT', 'VERSION_UPDATE', 'VALIDATE', 'FLAG_DISPUTED')),
    agent_id TEXT NOT NULL,                 -- e.g. "AGY", "CODEX", "CLAUDE_CODE", "HERMES"
    model_name TEXT,
    prompt_hash TEXT,
    old_hash TEXT,
    new_hash TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    reason TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- 10. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_passages_lookup ON passages(book_id, chapter, verse);
CREATE INDEX IF NOT EXISTS idx_tokens_passage ON tokens(passage_id, position);
CREATE INDEX IF NOT EXISTS idx_source_texts_hash ON source_texts(sha256_hash);
CREATE INDEX IF NOT EXISTS idx_syntax_trees_clause ON syntax_trees(clause_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ledger_pericope ON evidence_ledger(pericope_id, evidence_class);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_claim ON claim_evidence_links(claim_id);
CREATE INDEX IF NOT EXISTS idx_referential_relations ON referential_relations(source_entity_id, target_entity_id);
CREATE INDEX IF NOT EXISTS idx_variant_units_passage ON variant_units(passage_id);
CREATE INDEX IF NOT EXISTS idx_validation_report ON validation_gate_results(report_id, gate_layer);
