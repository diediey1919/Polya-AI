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
