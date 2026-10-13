"""
Idempotent schema migrations for the C5 automation state store.

Safety contract:
- Migrations are numbered and recorded in `automation_schema_migrations`.
- Every migration is idempotent: re-running is a no-op.
- Data (jobs, executions, approvals, leases, audit records) is never dropped.
- Migrations are NEVER run implicitly at supervisor startup. The supervisor performs a
  read-only version check and refuses to execute jobs on an un-migrated database.

Why this exists: `CREATE TABLE IF NOT EXISTS` in SCHEMA_SQL cannot add columns to a
table that already exists, so databases created before fencing tokens landed would
silently lack `automation_job_leases.fencing_token` and
`automation_executions.fencing_token`, making every fenced write fail.
"""

import logging
import sqlite3
from typing import Dict, List, Optional, Tuple

from orchestrator.automation.job_store import SCHEMA_SQL

logger = logging.getLogger("orchestrator.automation.migrations")

# Bump when a new migration is appended.
SCHEMA_VERSION = 3

_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS automation_schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Each entry: (version, name, list_of_column_additions)
#   (table, column, column_type)
# ---------------------------------------------------------------------------
MIGRATIONS: List[Tuple[int, str, List[Tuple[str, str, str]]]] = [
    (
        1,
        "initial_schema_v1",
        [],
    ),
    (
        2,
        "add_fencing_token_to_leases_and_executions",
        [
            ("automation_job_leases", "fencing_token", "INTEGER NOT NULL DEFAULT 0"),
            ("automation_executions", "fencing_token", "INTEGER"),
        ],
    ),
    (
        3,
        "add_release_nonces_table",
        [],
    ),
]


class MigrationError(Exception):
    """Raised when a migration cannot be applied safely."""


class SchemaVersionError(Exception):
    """Raised when the database schema is older than the code requires."""


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Creates the migration ledger. MUST NOT be called on a read-only connection."""
    conn.execute(_MIGRATIONS_TABLE_SQL)


def _table_exists_safe(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def current_version(conn: sqlite3.Connection) -> int:
    """Returns the highest applied migration version, or 0 for a legacy database.

    Read-only safe: if the ledger table does not exist yet (legacy database, or a
    query_only connection) no DDL is attempted.
    """
    if not _table_exists_safe(conn, "automation_schema_migrations"):
        return 0
    row = conn.execute(
        "SELECT MAX(version) FROM automation_schema_migrations"
    ).fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def pending_migrations(conn: sqlite3.Connection) -> List[Tuple[int, str]]:
    """Returns [(version, name)] for migrations not yet applied."""
    version = current_version(conn)
    return [(v, n) for v, n, _ in MIGRATIONS if v > version]


def inspect_schema(conn: sqlite3.Connection) -> Dict[str, object]:
    """Read-only structural report used by tests and operators."""
    report: Dict[str, object] = {"version": current_version(conn), "tables": {}}
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall():
        name = row[0]
        report["tables"][name] = {  # type: ignore[index]
            "columns": [c[1] for c in conn.execute(f"PRAGMA table_info({name})").fetchall()],
            "row_count": conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0],
        }
    return report


def _apply_one(conn: sqlite3.Connection, version: int, name: str, columns: List[Tuple[str, str, str]]) -> None:
    if version == 3:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS automation_release_nonces (
                nonce TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                operator_key_id TEXT NOT NULL,
                used_at TEXT NOT NULL,
                expires_at REAL NOT NULL,
                FOREIGN KEY (job_id) REFERENCES automation_jobs(job_id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_release_nonces_job ON automation_release_nonces(job_id);")

    for table, column, coltype in columns:
        if not _table_exists(conn, table):
            # Table absent: SCHEMA_SQL (executescript) creates it fresh, already with
            # the column, so there is nothing to ALTER.
            logger.info(
                "Migration %d: table %s absent; skipped column %s (created fresh by SCHEMA_SQL)",
                version, table, column,
            )
            continue
        existing = _columns(conn, table)
        if column in existing:
            logger.info("Migration %d: %s.%s already present; no-op", version, table, column)
            continue
        logger.info("Migration %d: ALTER TABLE %s ADD COLUMN %s %s", version, table, column, coltype)
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

    conn.execute(
        "INSERT OR REPLACE INTO automation_schema_migrations (version, name, applied_at) "
        "VALUES (?, ?, datetime('now'))",
        (version, name),
    )


def migrate(db_path: str) -> Dict[str, object]:
    """Applies all pending migrations to the automation database at `db_path`.

    NEVER call this against a live/production database without explicit approval.
    Idempotent: safe to call repeatedly.

    The initial SCHEMA_SQL creates tables fresh (already carrying the new columns) on
    a brand-new database; migrations then only stamp the ledger.
    """
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute("PRAGMA foreign_keys=ON;")
        ensure_migrations_table(conn)
        before = inspect_schema(conn)
        applied: List[int] = []
        for version, name, columns in MIGRATIONS:
            if version > current_version(conn):
                _apply_one(conn, version, name, columns)
                applied.append(version)
        conn.commit()
        after = inspect_schema(conn)
        logger.info("Migrations applied: %s (schema now v%d)", applied, after["version"])
        return {"applied": applied, "before": before, "after": after}
    finally:
        conn.close()


def check_schema_version(db_path: str) -> None:
    """Read-only guard. Raises SchemaVersionError if migrations are pending.

    Used by the supervisor at startup so it can refuse to run jobs rather than
    failing deep inside a fenced write. Never writes.
    """
    if db_path == ":memory:":
        return
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        conn.execute("PRAGMA query_only=ON;")
        version = current_version(conn)
        if version < SCHEMA_VERSION:
            pending = ", ".join(f"v{v} ({n})" for v, n in pending_migrations(conn))
            raise SchemaVersionError(
                f"Automation database {db_path} is at schema v{version}, but code requires "
                f"v{SCHEMA_VERSION}. Pending: {pending}. "
                "Run the migration explicitly and review the procedure before enabling the scheduler. "
                "The supervisor will not migrate this database automatically."
            )
    finally:
        conn.close()