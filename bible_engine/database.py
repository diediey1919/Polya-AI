"""
Core Database Access Layer for Polya Philological Bible Engine (Phase 1, Task 1.2).
Provides deterministic SQLite connection management, mandatory foreign-key enforcement,
isolated transactions, safe parameterized queries, and schema bootstrap.
Treats '001_initial_schema.sql' as schema authority.
"""

import contextlib
import os
import re
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

from bible_engine.config import DatabaseConfig
from bible_engine.errors import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseTransactionError,
    ReadOnlyViolationError,
    SchemaInitializationError,
)

# Regex to detect attempts to disable foreign key enforcement
_FK_DISABLE_PATTERN = re.compile(
    r"\bPRAGMA\s+foreign_keys\s*=\s*(OFF|0|NO|FALSE)\b",
    re.IGNORECASE,
)


def _assert_foreign_keys_protected(sql: str) -> None:
    """Ensure no SQL statement attempts to disable foreign keys."""
    if _FK_DISABLE_PATTERN.search(sql):
        raise DatabaseConfigurationError(
            "Bypassing foreign-key enforcement is prohibited by architecture contract."
        )


def create_connection(config: Optional[DatabaseConfig] = None) -> sqlite3.Connection:
    """
    Establish a deterministic SQLite connection adhering to Bible Engine standards.
    
    Settings applied:
    - isolation_level = None (autocommit mode for explicit transaction control)
    - PRAGMA foreign_keys = ON (mandatory, strictly verified)
    - PRAGMA busy_timeout = <busy_timeout_ms> (prevents instantaneous lock failures)
    - PRAGMA journal_mode = WAL (file databases; concurrent reads without blocking writer)
    - PRAGMA synchronous = NORMAL (WAL mode official safety standard)
    - PRAGMA query_only = ON (if read_only = True)
    """
    if config is None:
        config = DatabaseConfig()

    resolved_path = config.resolve_db_path()
    is_in_memory = config.is_in_memory()

    try:
        if config.read_only:
            if not is_in_memory:
                if not os.path.exists(resolved_path):
                    raise DatabaseConnectionError(
                        f"Database file not found for read-only connection: {resolved_path}"
                    )
                # Open with SQLite URI mode=ro for OS-level write prevention
                uri_path = f"file:{os.path.abspath(resolved_path)}?mode=ro"
                conn = sqlite3.connect(
                    uri_path,
                    timeout=config.busy_timeout_ms / 1000.0,
                    isolation_level=None,
                    uri=True,
                    check_same_thread=False,
                )
            else:
                conn = sqlite3.connect(
                    resolved_path,
                    timeout=config.busy_timeout_ms / 1000.0,
                    isolation_level=None,
                    check_same_thread=False,
                )
        else:
            conn = sqlite3.connect(
                resolved_path,
                timeout=config.busy_timeout_ms / 1000.0,
                isolation_level=None,
                check_same_thread=False,
            )
    except sqlite3.Error as e:
        raise DatabaseConnectionError(
            f"Failed to connect to SQLite database at '{resolved_path}': {e}"
        ) from e

    # Configure Row factory for structured column access
    conn.row_factory = sqlite3.Row

    # Enforce deterministic PRAGMA sequence
    try:
        # 1. Foreign keys: MANDATORY
        conn.execute("PRAGMA foreign_keys = ON;")
        fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        if fk_status != 1:
            conn.close()
            raise DatabaseConfigurationError("Failed to enable PRAGMA foreign_keys = ON.")

        # 2. Busy timeout
        conn.execute(f"PRAGMA busy_timeout = {config.busy_timeout_ms};")

        # 3. WAL and synchronous mode (file-based databases only)
        if not is_in_memory and not config.read_only:
            if config.wal_mode:
                conn.execute("PRAGMA journal_mode = WAL;")
            if config.synchronous:
                conn.execute(f"PRAGMA synchronous = {config.synchronous};")

        # 4. Read-only guard
        if config.read_only:
            conn.execute("PRAGMA query_only = ON;")

    except sqlite3.Error as e:
        conn.close()
        raise DatabaseConfigurationError(
            f"Failed to apply database pragmas on initialization: {e}"
        ) from e

    return conn


def init_schema(
    conn: sqlite3.Connection,
    schema_path: Optional[str] = None,
) -> None:
    """
    Initialize authoritative database schema from 001_initial_schema.sql.
    
    This function provides the minimal bootstrap needed to establish a usable
    database connection for development, testing, and operations.
    It does NOT implement migration version tracking or migration runner logic.
    """
    if schema_path is None:
        cfg = DatabaseConfig()
        schema_path = cfg.resolve_schema_path()
    else:
        p = Path(schema_path).resolve()
        if not p.is_file():
            raise SchemaInitializationError(
                f"Specified schema file does not exist: {schema_path}"
            )
        schema_path = str(p)

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
    except OSError as e:
        raise SchemaInitializationError(
            f"Cannot read schema file at '{schema_path}': {e}"
        ) from e

    _assert_foreign_keys_protected(schema_sql)

    try:
        # executescript executes a COMMIT before running and executes multiple statements
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
    except sqlite3.IntegrityError:
        # Integrity errors must propagate cleanly
        raise
    except sqlite3.Error as e:
        raise SchemaInitializationError(
            f"Failed to execute authoritative schema '{schema_path}': {e}"
        ) from e


def create_in_memory_database(
    init_schema_tables: bool = True,
    config: Optional[DatabaseConfig] = None,
) -> sqlite3.Connection:
    """
    Factory creating a fully initialized in-memory database instance.
    Ideal for unit tests, isolated simulations, and ephemeral validation.
    """
    if config is None:
        mem_config = DatabaseConfig(db_path=":memory:")
    else:
        mem_config = DatabaseConfig(
            db_path=":memory:",
            read_only=config.read_only,
            busy_timeout_ms=config.busy_timeout_ms,
            wal_mode=False,
            schema_path=config.schema_path,
        )

    conn = create_connection(mem_config)

    if init_schema_tables:
        init_schema(conn, mem_config.resolve_schema_path())

    return conn


class DatabaseEngine:
    """
    High-level generic Database Engine for Polya Philological Bible Engine.
    
    Provides:
    - Connection lifecycle management
    - Read/write connection separation
    - Explicit transaction demarcation (BEGIN IMMEDIATE / COMMIT / ROLLBACK)
    - Safe nested transactions via SQLite SAVEPOINT
    - Parameterized query execution protecting against SQL injection and FK bypass
    - Zero theological data creation or biblical logic (remains pure infrastructure)
    """

    def __init__(self, config: Optional[DatabaseConfig] = None) -> None:
        self.config = config or DatabaseConfig()
        self._local = threading.local()
        self._lock = threading.Lock()
        self._all_conns: set[sqlite3.Connection] = set()
        self._extra_conns: List[sqlite3.Connection] = []

    @property
    def _write_conn(self) -> Optional[sqlite3.Connection]:
        return getattr(self._local, "write_conn", None)

    @_write_conn.setter
    def _write_conn(self, val: Optional[sqlite3.Connection]) -> None:
        self._local.write_conn = val

    @property
    def _read_conn(self) -> Optional[sqlite3.Connection]:
        return getattr(self._local, "read_conn", None)

    @_read_conn.setter
    def _read_conn(self, val: Optional[sqlite3.Connection]) -> None:
        self._local.read_conn = val

    def get_write_connection(self) -> sqlite3.Connection:
        """Obtain primary read/write connection. Reuses open connection if healthy."""
        if self.config.read_only:
            raise ReadOnlyViolationError(
                "DatabaseEngine is configured as read-only; cannot acquire write connection."
            )

        conn = self._write_conn
        if conn is not None:
            try:
                conn.execute("SELECT 1;")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                conn = None

        if conn is None:
            conn = create_connection(self.config)
            self._write_conn = conn
            with self._lock:
                self._all_conns.add(conn)
        return conn

    def get_read_connection(self) -> sqlite3.Connection:
        """Obtain read-only connection with PRAGMA query_only = ON enforced. Reuses cached connection."""
        conn = self._read_conn
        if conn is not None:
            try:
                conn.execute("SELECT 1;")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                conn = None

        if conn is None:
            read_config = DatabaseConfig(
                db_path=self.config.db_path,
                read_only=True,
                busy_timeout_ms=self.config.busy_timeout_ms,
                wal_mode=self.config.wal_mode,
                synchronous=self.config.synchronous,
                schema_path=self.config.schema_path,
            )
            conn = create_connection(read_config)
            self._read_conn = conn
            with self._lock:
                self._all_conns.add(conn)
        return conn

    @contextlib.contextmanager
    def connect(self, read_only: Optional[bool] = None) -> Iterator[sqlite3.Connection]:
        """Context manager for acquiring a managed connection."""
        ro = self.config.read_only if read_only is None else read_only
        if ro:
            read_config = DatabaseConfig(
                db_path=self.config.db_path,
                read_only=True,
                busy_timeout_ms=self.config.busy_timeout_ms,
                wal_mode=self.config.wal_mode,
                synchronous=self.config.synchronous,
                schema_path=self.config.schema_path,
            )
            conn = create_connection(read_config)
            with self._lock:
                self._extra_conns.append(conn)
                self._all_conns.add(conn)
            try:
                yield conn
            finally:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
                with self._lock:
                    if conn in self._extra_conns:
                        self._extra_conns.remove(conn)
                    self._all_conns.discard(conn)
        else:
            conn = self.get_write_connection()
            yield conn

    @contextlib.contextmanager
    def transaction(
        self,
        conn: Optional[sqlite3.Connection] = None,
        savepoint: bool = True,
    ) -> Iterator[sqlite3.Connection]:
        """
        Explicit transaction context manager.
        
        Behavior:
        - Normal: executes BEGIN IMMEDIATE on entry; COMMIT on successful exit.
        - Exception / IntegrityError: executes ROLLBACK (or rollback to savepoint) and propagates.
        - Nested:
          * If savepoint=True: creates SAVEPOINT <id>; releases on success; rolls back on error.
          * If savepoint=False: raises DatabaseTransactionError when a transaction is already active.
        - Read-only connection: raises ReadOnlyViolationError if write transaction is attempted.
        """
        target_conn = conn if conn is not None else self.get_write_connection()

        # Check if target connection is query-only
        query_only = target_conn.execute("PRAGMA query_only;").fetchone()[0]
        if query_only == 1:
            raise ReadOnlyViolationError(
                "Cannot initiate transaction on read-only connection."
            )

        if target_conn.in_transaction:
            if not savepoint:
                raise DatabaseTransactionError(
                    "Active transaction already in progress; nested transactions require savepoints."
                )
            sp_name = f"sp_{uuid.uuid4().hex[:8]}"
            target_conn.execute(f"SAVEPOINT {sp_name};")
            try:
                yield target_conn
                target_conn.execute(f"RELEASE SAVEPOINT {sp_name};")
            except BaseException:
                target_conn.execute(f"ROLLBACK TO SAVEPOINT {sp_name};")
                target_conn.execute(f"RELEASE SAVEPOINT {sp_name};")
                raise
        else:
            target_conn.execute("BEGIN IMMEDIATE;")
            try:
                yield target_conn
                target_conn.execute("COMMIT;")
            except BaseException:
                target_conn.execute("ROLLBACK;")
                raise

    def execute(
        self,
        sql: str,
        params: Optional[Union[Tuple[Any, ...], Dict[str, Any], Sequence[Any]]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> sqlite3.Cursor:
        """
        Execute safe parameterized SQL.
        Strictly forbids foreign-key bypass attempts and requires parameter binding.
        """
        _assert_foreign_keys_protected(sql)
        target_conn = conn or (self.get_read_connection() if self.config.read_only else self.get_write_connection())
        
        cursor = target_conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        return cursor

    def execute_many(
        self,
        sql: str,
        seq_of_params: Sequence[Union[Tuple[Any, ...], Dict[str, Any]]],
        conn: Optional[sqlite3.Connection] = None,
    ) -> sqlite3.Cursor:
        """Execute parameterized SQL across a sequence of parameter sets."""
        _assert_foreign_keys_protected(sql)
        target_conn = conn or (self.get_read_connection() if self.config.read_only else self.get_write_connection())
        
        cursor = target_conn.cursor()
        cursor.executemany(sql, seq_of_params)
        return cursor

    def fetch_one(
        self,
        sql: str,
        params: Optional[Union[Tuple[Any, ...], Dict[str, Any], Sequence[Any]]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[sqlite3.Row]:
        """Execute parameterized query and fetch a single row."""
        cursor = self.execute(sql, params, conn=conn)
        return cursor.fetchone()

    def fetch_all(
        self,
        sql: str,
        params: Optional[Union[Tuple[Any, ...], Dict[str, Any], Sequence[Any]]] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[sqlite3.Row]:
        """Execute parameterized query and fetch all rows."""
        cursor = self.execute(sql, params, conn=conn)
        return cursor.fetchall()

    def init_database(self) -> None:
        """Bootstrap database schema using authoritative 001_initial_schema.sql."""
        write_conn = self.get_write_connection()
        init_schema(write_conn, self.config.resolve_schema_path())

    def close(self) -> None:
        """Close all managed write and read connections cleanly."""
        with self._lock:
            for conn in list(self._all_conns):
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
            self._all_conns.clear()
            self._extra_conns.clear()
        self._write_conn = None
        self._read_conn = None
