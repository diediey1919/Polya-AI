"""
Polya Philological Bible Engine - Core Package.
Provides foundational database layer, models, and exegesis utilities.
"""

from bible_engine.config import DatabaseConfig, DEFAULT_DB_PATH
from bible_engine.database import (
    DatabaseEngine,
    create_connection,
    create_in_memory_database,
    init_schema,
)
from bible_engine.errors import (
    AmbiguousMigrationOrderError,
    BibleEngineDatabaseError,
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseTransactionError,
    DuplicateMigrationError,
    MalformedMigrationNameError,
    MigrationChecksumMismatchError,
    MigrationError,
    MigrationExecutionError,
    MigrationIntegrityError,
    MissingMigrationFileError,
    ReadOnlyViolationError,
    SchemaInitializationError,
)
from bible_engine.migrations import (
    MigrationFile,
    MigrationRecord,
    MigrationRunner,
    MigrationStatus,
    compute_sha256,
    split_sql_statements,
)
from bible_engine.provenance import (
    ChainIntegrityResult,
    HashStatus,
    HashVerificationResult,
    ProvenanceChain,
    ProvenanceRecord,
    ProvenanceRelation,
    ProvenanceTracker,
    RelationType,
    TargetType,
    TransformationType,
    compute_canonical_hash,
    verify_hash,
)
from bible_engine.errors import (
    ProvenanceChainBrokenError,
    ProvenanceError,
    ProvenanceHashMismatchError,
    ProvenanceImmutabilityError,
    ProvenanceIntegrityError,
    ProvenanceMissingParentError,
    ProvenanceRecordNotFoundError,
)

__all__ = [
    "DatabaseConfig",
    "DEFAULT_DB_PATH",
    "DatabaseEngine",
    "create_connection",
    "create_in_memory_database",
    "init_schema",
    "BibleEngineDatabaseError",
    "DatabaseConfigurationError",
    "DatabaseConnectionError",
    "DatabaseTransactionError",
    "ReadOnlyViolationError",
    "SchemaInitializationError",
    "MigrationError",
    "MigrationIntegrityError",
    "MigrationChecksumMismatchError",
    "MissingMigrationFileError",
    "DuplicateMigrationError",
    "MalformedMigrationNameError",
    "AmbiguousMigrationOrderError",
    "MigrationExecutionError",
    "MigrationFile",
    "MigrationRecord",
    "MigrationRunner",
    "MigrationStatus",
    "compute_sha256",
    "split_sql_statements",
    "ProvenanceTracker",
    "ProvenanceRecord",
    "ProvenanceRelation",
    "ProvenanceChain",
    "TargetType",
    "TransformationType",
    "RelationType",
    "HashStatus",
    "HashVerificationResult",
    "ChainIntegrityResult",
    "compute_canonical_hash",
    "verify_hash",
    "ProvenanceError",
    "ProvenanceRecordNotFoundError",
    "ProvenanceIntegrityError",
    "ProvenanceImmutabilityError",
    "ProvenanceHashMismatchError",
    "ProvenanceMissingParentError",
    "ProvenanceChainBrokenError",
]


