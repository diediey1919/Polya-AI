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

