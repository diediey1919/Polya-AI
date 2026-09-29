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
]

