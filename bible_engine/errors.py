"""
Database Exceptions for Polya Philological Bible Engine (Phase 1, Task 1.2).
Strictly adheres to Architecture v2.0 FROZEN specification.
"""

import sqlite3


class BibleEngineDatabaseError(Exception):
    """Base exception for all Bible Engine database layer errors."""
    pass


class DatabaseConnectionError(BibleEngineDatabaseError):
    """Raised when an SQLite connection cannot be established or database file is inaccessible."""
    pass


class DatabaseConfigurationError(BibleEngineDatabaseError):
    """Raised when an invalid database configuration or illegal pragma modification is attempted."""
    pass


class DatabaseTransactionError(BibleEngineDatabaseError):
    """Raised on transaction lifecycle violations (e.g. invalid nesting, commit on closed connection)."""
    pass


class ReadOnlyViolationError(BibleEngineDatabaseError):
    """Raised when a write/mutation operation is attempted against a read-only connection."""
    pass


class SchemaInitializationError(BibleEngineDatabaseError):
    """Raised when schema bootstrap from 001_initial_schema.sql fails."""
    pass


class MigrationError(BibleEngineDatabaseError):
    """Base exception for all migration runner errors."""
    pass


class MigrationIntegrityError(MigrationError):
    """Raised on migration integrity violations (e.g. checksum mismatch, pragma tampering)."""
    pass


class MigrationChecksumMismatchError(MigrationIntegrityError):
    """Raised when an already-applied migration script differs from its recorded database checksum."""
    pass


class MissingMigrationFileError(MigrationError):
    """Raised when a recorded applied migration file is absent from the filesystem."""
    pass


class DuplicateMigrationError(MigrationError):
    """Raised when duplicate migration sequence numbers or IDs are discovered."""
    pass


class MalformedMigrationNameError(MigrationError):
    """Raised when a migration filename violates the strict NNN_name.sql naming convention."""
    pass


class AmbiguousMigrationOrderError(MigrationError):
    """Raised on ambiguous ordering, out-of-order pending migrations, or unexpected sequence gaps."""
    pass


class MigrationExecutionError(MigrationError):
    """Raised when executing a migration script fails, wrapping the underlying database error."""

    def __init__(self, migration_id: str, cause: Exception, statement: str = "") -> None:
        self.migration_id = migration_id
        self.cause = cause
        self.statement = statement
        msg = f"Failed to execute migration '{migration_id}': {cause}"
        if statement:
            stmt_snippet = statement.strip().replace("\n", " ")[:80]
            msg += f" (at statement: {stmt_snippet}...)"
        super().__init__(msg)


class ProvenanceError(BibleEngineDatabaseError):
    """Base exception for all provenance subsystem errors."""
    pass


class ProvenanceRecordNotFoundError(ProvenanceError):
    """Raised when a requested provenance record does not exist."""
    pass


class ProvenanceIntegrityError(ProvenanceError):
    """Raised when a provenance integrity check fails."""
    pass


class ProvenanceImmutabilityError(ProvenanceIntegrityError):
    """Raised when an illegal modification or deletion of provenance records is attempted."""
    pass


class ProvenanceHashMismatchError(ProvenanceIntegrityError):
    """Raised when content verification fails against the recorded SHA-256 provenance hash."""
    pass


class ProvenanceMissingParentError(ProvenanceIntegrityError):
    """Raised when a referenced parent provenance record is missing or unresolved."""
    pass


class ProvenanceChainBrokenError(ProvenanceIntegrityError):
    """Raised when an object's lineage chain is broken, disconnected, or unverified."""
    pass


class VersioningError(BibleEngineDatabaseError):
    """Base exception for all versioning subsystem errors."""
    pass


class VersionNotFoundError(VersioningError):
    """Raised when a requested object version does not exist."""
    pass


class VersionIntegrityError(VersioningError):
    """Raised when a version integrity check fails."""
    pass


class DuplicateVersionError(VersionIntegrityError):
    """Raised when attempting to create a duplicate version or version number for an object."""
    pass


class VersionInvalidParentError(VersionIntegrityError):
    """Raised when a referenced parent version does not exist or violates lineage rules."""
    pass


class VersionInvalidProvenanceError(VersionIntegrityError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class VersionHashMismatchError(VersionIntegrityError):
    """Raised when content verification fails against the recorded content hash."""
    pass


class IllegalStateTransitionError(VersionIntegrityError):
    """Raised when an illegal version status transition is attempted."""
    pass


class VersionImmutabilityError(VersionIntegrityError):
    """Raised when an illegal modification or deletion of an immutable version is attempted."""
    pass


class VersionConcurrencyConflictError(VersioningError):
    """Raised when concurrent writers conflict during atomic version creation."""
    pass


# =============================================================================
# SOURCE REGISTRY ERRORS (Task 1.6)
# =============================================================================

class SourceRegistryError(BibleEngineDatabaseError):
    """Base exception for all source registry subsystem errors."""
    pass


class SourceNotFoundError(SourceRegistryError):
    """Raised when a requested registered source does not exist."""
    pass


class DuplicateSourceError(SourceRegistryError):
    """Raised when registering a source with a duplicate identifier or canonical name."""
    pass


class InvalidSourceTypeError(SourceRegistryError):
    """Raised when an invalid or unclassified source type is specified."""
    pass


class InvalidSourceLanguageError(SourceRegistryError):
    """Raised when an invalid or unclassified source language is specified."""
    pass


class InvalidSourceAuthorityError(SourceRegistryError):
    """Raised when an invalid functional authority level is specified."""
    pass


class InvalidVerificationStatusError(SourceRegistryError):
    """Raised when an invalid verification status is specified."""
    pass


class SourceTranslationFirewallError(SourceRegistryError):
    """Raised when translation firewall invariants are violated (e.g. translation marked as primary witness)."""
    pass


class SourceImmutabilityError(SourceRegistryError):
    """Raised when an illegal modification or deletion of source registry records is attempted."""
    pass


class SourceInvalidProvenanceError(SourceRegistryError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SourceInvalidVersionError(SourceRegistryError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SourceHashMismatchError(SourceRegistryError):
    """Raised when content hash validation fails against source artifact."""
    pass


class IllegalSourceStateTransitionError(SourceRegistryError):
    """Raised when an illegal verification status transition is attempted."""
    pass


# =============================================================================
# SOURCE TEXT SUBSYSTEM EXCEPTIONS (Task 2.1)
# =============================================================================

class SourceTextError(BibleEngineDatabaseError):
    """Base exception for all Source Text subsystem errors."""
    pass


class SourceTextNotFoundError(SourceTextError):
    """Raised when a requested source text record does not exist."""
    pass


class DuplicateSourceTextError(SourceTextError):
    """Raised when registering a source text with a duplicate identifier or conflicting unique key."""
    pass


class SourceTextImmutabilityError(SourceTextError):
    """Raised when an illegal modification, update of raw content/hash, or deletion of source text is attempted."""
    pass


class SourceTextTranslationFirewallError(SourceTextError):
    """Raised when translation firewall invariants are violated in source text operations."""
    pass


class SourceTextHashMismatchError(SourceTextError):
    """Raised when content hash validation fails against source text artifact."""
    pass


class MalformedContentHashError(SourceTextError):
    """Raised when a provided content hash violates the required 64-character lowercase hexadecimal format."""
    pass


class InvalidSourceTextLanguageError(SourceTextError):
    """Raised when an invalid or unclassified source text language is specified."""
    pass


class InvalidRepresentationTypeError(SourceTextError):
    """Raised when an invalid or unclassified representation type is specified."""
    pass


class SourceTextInvalidProvenanceError(SourceTextError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SourceTextInvalidVersionError(SourceTextError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SourceTextOrphanError(SourceTextError):
    """Raised when attempting to register or persist a source text without a valid registered source."""
    pass


# =============================================================================
# TOKENIZATION SUBSYSTEM EXCEPTIONS (Task 2.2)
# =============================================================================

class TokenError(BibleEngineDatabaseError):
    """Base exception for all Tokenization subsystem errors."""
    pass


class TokenNotFoundError(TokenError):
    """Raised when a requested token or tokenization run does not exist."""
    pass


class DuplicateTokenError(TokenError):
    """Raised when registering a token with a duplicate identifier or colliding position."""
    pass


class TokenImmutabilityError(TokenError):
    """Raised when an illegal modification or deletion of a token or tokenization run is attempted."""
    pass


class TokenSourceNotFoundError(TokenError):
    """Raised when a referenced source text for tokenization does not exist."""
    pass


class TokenOffsetError(TokenError):
    """Raised when token character/byte offsets are invalid, negative, out of bounds, or inverted."""
    pass


class TokenReconstructionError(TokenError):
    """Raised when token surface form does not match the source text slice at the specified offsets."""
    pass


class TokenLanguageMismatchError(TokenError):
    """Raised when tokenization language conflicts with source text language."""
    pass


class InvalidTokenTypeError(TokenError):
    """Raised when an invalid or unclassified token type is specified."""
    pass


class TokenNormalizationFirewallError(TokenError):
    """Raised when normalization firewall rules are violated during tokenization."""
    pass


class TokenInvalidProvenanceError(TokenError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class TokenInvalidVersionError(TokenError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass
