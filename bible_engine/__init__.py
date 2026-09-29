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
    BibleEngineDatabaseError,
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseTransactionError,
    ReadOnlyViolationError,
    SchemaInitializationError,
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
]
