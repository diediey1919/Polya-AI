-- ============================================================================
-- POLYA PHILOLOGICAL BIBLE ENGINE
-- SCHEMA MIGRATION 004: SOURCE REGISTRY (Task 1.6)
-- Specification: Architecture v2.0 — FROZEN
-- Dialect: SQLite 3.46+ (Strict Foreign Keys & Immutability Triggers)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SOURCE REGISTRY (AUTHORITATIVE CATALOG & IDENTITY LAYER)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS source_registry (
    source_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL CHECK(source_type IN (
        'PRIMARY_WITNESS',
        'CRITICAL_EDITION',
        'SOURCE_LANGUAGE_TEXT',
        'ANCIENT_TRANSLATION',
        'LEXICON',
        'GRAMMAR',
        'MORPHOLOGY_RESOURCE',
        'SYNTAX_RESOURCE',
        'SEMANTIC_RESOURCE',
        'HISTORICAL_SOURCE',
        'EARLY_RECEPTION',
        'SECONDARY_SCHOLARSHIP',
        'MODERN_TRANSLATION',
        'OTHER'
    )),
    language TEXT NOT NULL CHECK(language IN (
        'GREEK',
        'HEBREW',
        'ARAMAIC',
        'LATIN',
        'SYRIAC',
        'COPTIC',
        'OTHER',
        'MULTILINGUAL'
    )),
    description TEXT,
    authority_level TEXT NOT NULL CHECK(authority_level IN (
        'PRIMARY',
        'TEXTUAL_CRITICAL',
        'LINGUISTIC',
        'HISTORICAL',
        'RECEPTION',
        'SECONDARY',
        'TRANSLATION'
    )),
    provenance_id TEXT,
    current_version_id TEXT,
    content_hash TEXT CHECK(content_hash IS NULL OR (length(content_hash) = 64 AND content_hash GLOB '[0-9a-f]*')),
    creator TEXT,
    date_or_period TEXT,
    geographic_origin TEXT,
    textual_family TEXT,
    repository TEXT,
    external_identifier TEXT,
    external_identifier_type TEXT CHECK(external_identifier_type IS NULL OR external_identifier_type IN (
        'GREGORY_ALAND',
        'RAHLFS',
        'DEAD_SEA_SCROLL',
        'SHELFMARK',
        'ISBN',
        'DOI',
        'URN',
        'OTHER'
    )),
    external_identifier_verified INTEGER NOT NULL DEFAULT 0 CHECK(external_identifier_verified IN (0, 1)),
    witness_id TEXT,
    edition_id TEXT,
    verification_status TEXT NOT NULL DEFAULT 'REGISTERED' CHECK(verification_status IN (
        'REGISTERED',
        'VERIFIED',
        'PARTIALLY_VERIFIED',
        'UNVERIFIED',
        'DEPRECATED',
        'RESTRICTED'
    )),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY (provenance_id) REFERENCES provenance_records(provenance_id) ON DELETE RESTRICT,
    FOREIGN KEY (current_version_id) REFERENCES object_versions(version_id) ON DELETE RESTRICT,
    FOREIGN KEY (witness_id) REFERENCES witnesses(witness_id) ON DELETE RESTRICT,
    FOREIGN KEY (edition_id) REFERENCES critical_editions(edition_id) ON DELETE RESTRICT,
    -- Translation Firewall: Modern translations can never have authority_level = PRIMARY
    CHECK(NOT (source_type = 'MODERN_TRANSLATION' AND authority_level = 'PRIMARY')),
    -- Translation Firewall: Modern translations can never masquerade as manuscript witnesses
    CHECK(NOT (source_type = 'MODERN_TRANSLATION' AND witness_id IS NOT NULL))
);

-- Indexes for performance and deterministic filtering
CREATE INDEX IF NOT EXISTS idx_source_registry_type ON source_registry(source_type);
CREATE INDEX IF NOT EXISTS idx_source_registry_language ON source_registry(language);
CREATE INDEX IF NOT EXISTS idx_source_registry_status ON source_registry(verification_status);
CREATE INDEX IF NOT EXISTS idx_source_registry_authority ON source_registry(authority_level);
CREATE INDEX IF NOT EXISTS idx_source_registry_ext_id ON source_registry(external_identifier);
CREATE INDEX IF NOT EXISTS idx_source_registry_witness ON source_registry(witness_id);
CREATE INDEX IF NOT EXISTS idx_source_registry_edition ON source_registry(edition_id);
CREATE INDEX IF NOT EXISTS idx_source_registry_provenance ON source_registry(provenance_id);
CREATE INDEX IF NOT EXISTS idx_source_registry_version ON source_registry(current_version_id);

-- ----------------------------------------------------------------------------
-- 2. SOURCE REGISTRY AUDIT LEDGER (AUDITABLE METADATA REVISION HISTORY)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS source_registry_audit (
    audit_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN (
        'REGISTER',
        'UPDATE_METADATA',
        'VERIFY',
        'DEPRECATE',
        'ATTACH_VERSION',
        'ATTACH_PROVENANCE'
    )),
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    old_data_json TEXT,
    new_data_json TEXT,
    change_reason TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES source_registry(source_id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_source_registry_audit_source ON source_registry_audit(source_id);
CREATE INDEX IF NOT EXISTS idx_source_registry_audit_action ON source_registry_audit(action);

-- ----------------------------------------------------------------------------
-- 3. IMMUTABILITY & FIREWALL TRIGGERS
-- ----------------------------------------------------------------------------

-- Prevent deletion of registered sources
CREATE TRIGGER IF NOT EXISTS trg_prevent_source_registry_delete
BEFORE DELETE ON source_registry
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Deletions from source_registry are strictly prohibited. Historical registration must be preserved.');
END;

-- Prevent deletion of audit ledger records
CREATE TRIGGER IF NOT EXISTS trg_prevent_source_registry_audit_delete
BEFORE DELETE ON source_registry_audit
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Deletions from source_registry_audit are strictly prohibited.');
END;

-- Prevent update of audit ledger records
CREATE TRIGGER IF NOT EXISTS trg_prevent_source_registry_audit_update
BEFORE UPDATE ON source_registry_audit
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'Updates to source_registry_audit are strictly prohibited.');
END;

-- Enforce immutability of primary identity and translation firewall on source_registry updates
CREATE TRIGGER IF NOT EXISTS trg_enforce_source_registry_immutability
BEFORE UPDATE ON source_registry
FOR EACH ROW
BEGIN
    -- 1. Prevent modification of immutable primary identity fields
    SELECT RAISE(ABORT, 'Modification of source_id is prohibited')
    WHERE OLD.source_id IS NOT NEW.source_id;

    SELECT RAISE(ABORT, 'Modification of canonical_name is prohibited; canonical identity is immutable')
    WHERE OLD.canonical_name IS NOT NEW.canonical_name;

    SELECT RAISE(ABORT, 'Modification of created_at timestamp is prohibited')
    WHERE OLD.created_at IS NOT NEW.created_at;

    -- 2. Translation Firewall: Modern translations cannot be converted to primary witnesses or critical editions
    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translations cannot be converted to primary witnesses or critical editions')
    WHERE OLD.source_type = 'MODERN_TRANSLATION' AND NEW.source_type IN ('PRIMARY_WITNESS', 'CRITICAL_EDITION', 'SOURCE_LANGUAGE_TEXT');

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translations must have authority_level = TRANSLATION')
    WHERE NEW.source_type = 'MODERN_TRANSLATION' AND NEW.authority_level != 'TRANSLATION';

    SELECT RAISE(ABORT, 'Translation Firewall violation: Modern translations cannot have witness_id')
    WHERE NEW.source_type = 'MODERN_TRANSLATION' AND NEW.witness_id IS NOT NULL;

    -- 3. Terminal state: DEPRECATED cannot transition to any other status
    SELECT RAISE(ABORT, 'Illegal status transition: DEPRECATED is a terminal state')
    WHERE OLD.verification_status = 'DEPRECATED' AND NEW.verification_status != 'DEPRECATED';
END;
