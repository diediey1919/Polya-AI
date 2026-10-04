"""
Deterministic Migration Runner for Polya Philological Bible Engine (Phase 1, Task 1.3).
Provides strictly ordered, auditable schema migrations using SQLite transactional DDL,
checksum verification, and the authoritative schema_migrations metadata ledger.
Treats '001_initial_schema.sql' as authoritative schema baseline.
"""

import argparse
import hashlib
import os
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine, _assert_foreign_keys_protected
from bible_engine.errors import (
    AmbiguousMigrationOrderError,
    DatabaseConfigurationError,
    DuplicateMigrationError,
    MalformedMigrationNameError,
    MigrationChecksumMismatchError,
    MigrationError,
    MigrationExecutionError,
    MigrationIntegrityError,
    MissingMigrationFileError,
    SchemaInitializationError,
)

# Migration filename pattern: e.g. "001_initial_schema.sql", "002_evidence_index.sql"
_MIGRATION_FILE_PATTERN = re.compile(r"^(\d{3,})_([a-zA-Z0-9_\-]+)\.sql$")


def compute_sha256(content: Union[str, bytes]) -> str:
    """Compute deterministic SHA-256 hash of text or binary content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest().lower()


def compute_association_id(segmentation_id: str, pericope_id: str, passage_id: str) -> str:
    """
    Deterministic Canonical Association ID Generator for Pericope-Passage bindings.
    Contract: SHA256(segmentation_id + ":" + pericope_id + ":" + passage_id)
    """
    canonical_input = f"{segmentation_id}:{pericope_id}:{passage_id}".encode("utf-8")
    return hashlib.sha256(canonical_input).hexdigest().lower()


def _backfill_and_validate_migration_026(
    conn: sqlite3.Connection,
    segmentation_id: str = "WIT-SEG-PROVISIONAL-CHAPTER",
) -> None:
    """
    Migration 026 Python migration helper.
    Performs:
    1. Deterministic pericope_passages backfill for existing passages
    2. Projection parity validation
    3. Foreign key integrity validation (PRAGMA foreign_key_check)
    4. Active baseline & partition integrity validation
    5. Database integrity check (PRAGMA integrity_check)
    """
    cursor = conn.cursor()

    # 1. Deterministic association backfill
    passages = cursor.execute(
        "SELECT passage_id, pericope_id, sort_order FROM passages ORDER BY pericope_id, sort_order ASC;"
    ).fetchall()

    if passages:
        pericope_groups: Dict[str, List[Tuple[str, int]]] = {}
        for row in passages:
            pid = row["passage_id"] if isinstance(row, sqlite3.Row) else row[0]
            per_id = row["pericope_id"] if isinstance(row, sqlite3.Row) else row[1]
            s_order = row["sort_order"] if isinstance(row, sqlite3.Row) else row[2]
            pericope_groups.setdefault(per_id, []).append((pid, s_order))

        records = []
        now_iso = "2026-10-04T00:00:00Z"
        for per_id, pas_list in pericope_groups.items():
            total = len(pas_list)
            for idx, (pid, _) in enumerate(pas_list, start=1):
                assoc_id = compute_association_id(segmentation_id, per_id, pid)
                if total == 1:
                    b_pos = "SINGLE_VERSE_PERICOPE"
                elif idx == 1:
                    b_pos = "START_BOUNDARY"
                elif idx == total:
                    b_pos = "END_BOUNDARY"
                else:
                    b_pos = "INTERNAL"
                records.append((
                    assoc_id,
                    segmentation_id,
                    per_id,
                    pid,
                    idx,
                    "FULL_VERSE",
                    b_pos,
                    now_iso,
                ))

        cursor.executemany(
            """
            INSERT INTO pericope_passages (
                association_id, segmentation_id, pericope_id, passage_id, ordinal,
                containment_type, boundary_position, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            records,
        )

    # 2. Projection parity validation
    parity_violations = cursor.execute(
        """
        SELECT p.passage_id, p.pericope_id
        FROM passages p
        LEFT JOIN pericope_passages pp
          ON pp.passage_id = p.passage_id
         AND pp.pericope_id = p.pericope_id
         AND pp.segmentation_id = ?
        WHERE pp.association_id IS NULL;
        """,
        (segmentation_id,),
    ).fetchall()
    if parity_violations:
        raise MigrationIntegrityError(
            f"Projection parity validation failed for migration 026: {len(parity_violations)} unlinked passages."
        )

    # 3. Foreign key validation
    fk_violations = cursor.execute("PRAGMA foreign_key_check;").fetchall()
    if fk_violations:
        raise MigrationIntegrityError(
            f"Foreign key integrity check failed for migration 026: {fk_violations}"
        )

    # 4. Active baseline validation
    baseline_count = cursor.execute(
        "SELECT count(*) FROM segmentation_witnesses WHERE is_active_baseline = 1;"
    ).fetchone()[0]
    if baseline_count != 1:
        raise MigrationIntegrityError(
            f"Active baseline validation failed: expected exactly 1 active baseline, found {baseline_count}."
        )

    # 5. Partition overlap validation
    partition_overlaps = cursor.execute(
        """
        SELECT passage_id, count(*) as cnt
        FROM pericope_passages
        WHERE segmentation_id = ?
        GROUP BY passage_id
        HAVING cnt > 1;
        """,
        (segmentation_id,),
    ).fetchall()
    if partition_overlaps:
        raise MigrationIntegrityError(
            f"Partition validation failed: overlapping passages found in baseline partition: {partition_overlaps}"
        )

    # 6. Database integrity check
    integrity_rows = cursor.execute("PRAGMA integrity_check;").fetchall()
    if not integrity_rows or integrity_rows[0][0] != "ok":
        raise MigrationIntegrityError(
            f"Database integrity check failed after migration 026: {integrity_rows}"
        )


def split_sql_statements(sql_text: str) -> List[str]:
    """
    Split SQL script into discrete executable statements.
    Respects single quotes, double quotes, and comment blocks (-- and /* */).
    Guarantees semicolons inside string literals or comments do not split statements.
    """
    statements: List[str] = []
    current: List[str] = []
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    block_depth = 0
    i = 0
    n = len(sql_text)

    while i < n:
        c = sql_text[i]
        next_c = sql_text[i + 1] if i + 1 < n else ""

        # Handle line comments
        if in_line_comment:
            if c == "\n":
                in_line_comment = False
                current.append(c)
            i += 1
            continue

        # Handle block comments
        if in_block_comment:
            if c == "*" and next_c == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        # Check comment start when outside quotes
        if not in_single_quote and not in_double_quote:
            if c == "-" and next_c == "-":
                in_line_comment = True
                i += 2
                continue
            if c == "/" and next_c == "*":
                in_block_comment = True
                i += 2
                continue

        # Handle quote boundaries
        if c == "'" and not in_double_quote:
            # Check for escaped single quote ''
            if in_single_quote and next_c == "'":
                current.append("''")
                i += 2
                continue
            in_single_quote = not in_single_quote
            current.append(c)
            i += 1
            continue

        if c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(c)
            i += 1
            continue

        # Statement delimiter outside quotes/comments
        if not in_single_quote and not in_double_quote:
            # Detect BEGIN / END boundaries for compound statements like triggers
            word_match = re.match(r"^(BEGIN|END)\b", sql_text[i:], re.IGNORECASE)
            if word_match:
                word = word_match.group(1).upper()
                prev_char = current[-1] if current else " "
                if not prev_char.isalnum() and prev_char != "_":
                    if word == "BEGIN":
                        curr_upper = "".join(current).upper()
                        if "TRIGGER" in curr_upper:
                            block_depth += 1
                    elif word == "END" and block_depth > 0:
                        block_depth -= 1

            if c == ";" and block_depth == 0:
                stmt = "".join(current).strip()
                if stmt:
                    statements.append(stmt)
                current = []
                i += 1
                continue

        current.append(c)
        i += 1

    remaining = "".join(current).strip()
    if remaining:
        statements.append(remaining)

    return statements


@dataclass(frozen=True)
class MigrationFile:
    """Represents a discovered migration script on the filesystem."""
    sequence_num: int
    migration_id: str
    name: str
    path: Path
    checksum_sha256: str
    content: str
    description: str

    @property
    def is_initial(self) -> bool:
        return self.sequence_num == 1 or self.migration_id == "001_initial_schema"


@dataclass(frozen=True)
class MigrationRecord:
    """Represents an applied migration row from schema_migrations table."""
    migration_id: str
    version: str
    applied_at: str
    checksum_sha256: str
    description: str


@dataclass(frozen=True)
class MigrationStatus:
    """Structured report of migration system state."""
    current_version: Optional[str]
    latest_applied_id: Optional[str]
    total_discovered: int
    applied_count: int
    pending_count: int
    applied_migrations: List[MigrationRecord]
    pending_migrations: List[MigrationFile]
    is_clean: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_version": self.current_version,
            "latest_applied_id": self.latest_applied_id,
            "total_discovered": self.total_discovered,
            "applied_count": self.applied_count,
            "pending_count": self.pending_count,
            "is_clean": self.is_clean,
            "applied": [asdict(m) for m in self.applied_migrations],
            "pending": [
                {
                    "migration_id": m.migration_id,
                    "sequence_num": m.sequence_num,
                    "name": m.name,
                    "checksum_sha256": m.checksum_sha256,
                }
                for m in self.pending_migrations
            ],
        }

    def summary(self) -> str:
        lines = [
            f"Schema Version: {self.current_version or 'UNINITIALIZED'}",
            f"Latest Applied: {self.latest_applied_id or 'None'}",
            f"Applied: {self.applied_count} / {self.total_discovered}",
            f"Pending: {self.pending_count}",
            f"Status: {'CLEAN (All migrations applied)' if self.is_clean else 'PENDING MIGRATIONS'}",
        ]
        return "\n".join(lines)


class MigrationRunner:
    """
    Deterministic Migration Runner for SQLite.
    
    Guarantees:
    - 001_initial_schema.sql remains the authoritative schema baseline.
    - Deterministic NNN_name.sql ordering; rejects gaps and ambiguous names.
    - Transactional DDL execution with full rollback on failure.
    - Immutable applied migrations: rejects checksum changes.
    - Foreign keys enforced before, during, and after migration.
    - Mutual exclusion via SQLite BEGIN IMMEDIATE locking.
    """

    def __init__(
        self,
        engine: DatabaseEngine,
        migrations_dir: Optional[Union[str, Path]] = None,
    ) -> None:
        self.engine = engine
        if migrations_dir is not None:
            p = Path(migrations_dir).expanduser().resolve()
            if not p.is_dir():
                raise SchemaInitializationError(f"Migrations directory does not exist: {migrations_dir}")
            self.migrations_dir = p
        else:
            self.migrations_dir = Path(self.engine.config.resolve_migrations_dir())

    def discover_migrations(self) -> List[MigrationFile]:
        """
        Discover and parse migration files from the migrations directory.
        Strictly enforces NNN_name.sql naming convention, uniqueness, and contiguous ordering.
        """
        if not self.migrations_dir.exists():
            raise SchemaInitializationError(
                f"Migrations directory not found: {self.migrations_dir}"
            )

        sql_files = sorted(list(self.migrations_dir.glob("*.sql")))
        discovered: List[MigrationFile] = []
        seen_sequences: Dict[int, str] = {}
        seen_ids: Dict[str, Path] = {}

        for sql_file in sql_files:
            match = _MIGRATION_FILE_PATTERN.match(sql_file.name)
            if not match:
                raise MalformedMigrationNameError(
                    f"Migration file '{sql_file.name}' violates required format 'NNN_name.sql'."
                )

            seq_str, name_str = match.groups()
            seq_num = int(seq_str)
            migration_id = sql_file.stem

            # Check duplicate sequence numbers
            if seq_num in seen_sequences:
                raise DuplicateMigrationError(
                    f"Duplicate migration sequence number {seq_num}: "
                    f"conflict between '{seen_sequences[seq_num]}' and '{sql_file.name}'."
                )
            seen_sequences[seq_num] = sql_file.name

            # Check duplicate migration IDs
            if migration_id in seen_ids:
                raise DuplicateMigrationError(
                    f"Duplicate migration ID '{migration_id}' found in '{sql_file}'."
                )
            seen_ids[migration_id] = sql_file

            try:
                with open(sql_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError as e:
                raise SchemaInitializationError(f"Failed to read migration '{sql_file}': {e}") from e

            checksum = compute_sha256(content)

            # Extract description from header comment or filename
            description = name_str.replace("_", " ").capitalize()
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("--") and len(stripped) > 2:
                    potential = stripped[2:].strip()
                    if potential and not potential.startswith("="):
                        description = potential
                        break

            discovered.append(
                MigrationFile(
                    sequence_num=seq_num,
                    migration_id=migration_id,
                    name=name_str,
                    path=sql_file,
                    checksum_sha256=checksum,
                    content=content,
                    description=description,
                )
            )

        # Sort strictly by sequence number
        discovered.sort(key=lambda m: m.sequence_num)

        # Enforce sequence continuity (no unexpected gaps in filesystem migrations)
        if discovered:
            expected_seq = discovered[0].sequence_num
            for m in discovered:
                if m.sequence_num != expected_seq:
                    raise AmbiguousMigrationOrderError(
                        f"Migration sequence gap detected: expected {expected_seq:03d}, "
                        f"found {m.sequence_num:03d} ('{m.migration_id}')."
                    )
                expected_seq += 1

        return discovered

    def get_applied_migrations(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> List[MigrationRecord]:
        """Fetch all recorded applied migrations from schema_migrations table."""
        target_conn = conn or self.engine.get_write_connection()

        # Check if schema_migrations table exists
        cursor = target_conn.cursor()
        cursor.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_migrations';"
        )
        if cursor.fetchone()[0] == 0:
            return []

        cursor.execute(
            "SELECT migration_id, version, applied_at, checksum_sha256, description "
            "FROM schema_migrations ORDER BY CAST(version AS INTEGER) ASC, migration_id ASC;"
        )
        rows = cursor.fetchall()
        return [
            MigrationRecord(
                migration_id=r["migration_id"],
                version=str(r["version"]),
                applied_at=r["applied_at"],
                checksum_sha256=r["checksum_sha256"],
                description=r["description"],
            )
            for r in rows
        ]

    def get_current_version(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Optional[str]:
        """Return the current schema version string, or None if uninitialized."""
        applied = self.get_applied_migrations(conn=conn)
        if not applied:
            return None
        return applied[-1].version

    def get_status(
        self,
        conn: Optional[sqlite3.Connection] = None,
    ) -> MigrationStatus:
        """
        Evaluate full migration status, verifying checksums and detecting pending migrations.
        Raises MigrationIntegrityError on checksum mismatch, missing migration file, or gap.
        """
        discovered = self.discover_migrations()
        applied = self.get_applied_migrations(conn=conn)

        discovered_by_id = {m.migration_id: m for m in discovered}
        applied_by_id = {m.migration_id: m for m in applied}

        # 1. Verify all applied migrations exist on disk and checksums match
        for rec in applied:
            if rec.migration_id not in discovered_by_id:
                raise MissingMigrationFileError(
                    f"Applied migration '{rec.migration_id}' is recorded in database "
                    f"but missing from migrations directory '{self.migrations_dir}'."
                )

            disk_file = discovered_by_id[rec.migration_id]
            if disk_file.checksum_sha256 != rec.checksum_sha256:
                raise MigrationChecksumMismatchError(
                    f"Checksum mismatch for applied migration '{rec.migration_id}'. "
                    f"Database recorded: {rec.checksum_sha256}, "
                    f"On-disk file: {disk_file.checksum_sha256}. "
                    "Applied migrations are immutable."
                )

        # 2. Verify applied migrations form a contiguous prefix of discovered migrations
        if applied:
            max_applied_seq = max(discovered_by_id[r.migration_id].sequence_num for r in applied)
            for m in discovered:
                if m.sequence_num < max_applied_seq and m.migration_id not in applied_by_id:
                    raise AmbiguousMigrationOrderError(
                        f"Pending migration '{m.migration_id}' (sequence {m.sequence_num}) "
                        f"precedes already applied migrations (max sequence {max_applied_seq})."
                    )

        # 3. Identify pending migrations
        pending = [m for m in discovered if m.migration_id not in applied_by_id]

        latest_applied_id = applied[-1].migration_id if applied else None
        current_version = applied[-1].version if applied else None

        return MigrationStatus(
            current_version=current_version,
            latest_applied_id=latest_applied_id,
            total_discovered=len(discovered),
            applied_count=len(applied),
            pending_count=len(pending),
            applied_migrations=applied,
            pending_migrations=pending,
            is_clean=len(pending) == 0,
        )

    def apply_pending(
        self,
        target_migration_id: Optional[str] = None,
    ) -> List[MigrationRecord]:
        """
        Apply all pending migrations in strict deterministic order.
        
        Semantics:
        - Mutual exclusion guaranteed via BEGIN IMMEDIATE lock.
        - Each migration runs inside an isolated SAVEPOINT.
        - Checksum and metadata recorded in schema_migrations upon success.
        - On failure: SAVEPOINT rolls back the failed migration; database restored to prior state.
        - Foreign keys strictly verified before and after each migration.
        - Idempotent: returns empty list if all migrations already applied.
        """
        # Outer transaction with BEGIN IMMEDIATE ensures atomic concurrency lock
        with self.engine.transaction() as conn:
            status = self.get_status(conn=conn)
            if not status.pending_migrations:
                return []

            newly_applied: List[MigrationRecord] = []

            for pending in status.pending_migrations:
                # Pre-execution foreign key verification
                fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
                if fk_status != 1:
                    raise MigrationIntegrityError(
                        f"Foreign keys disabled prior to executing migration '{pending.migration_id}'."
                    )

                # Guard against embedded foreign key bypass
                _assert_foreign_keys_protected(pending.content)

                # Parse individual statements
                statements = split_sql_statements(pending.content)

                # Execute migration inside an isolated SAVEPOINT
                try:
                    with self.engine.transaction(conn=conn, savepoint=True):
                        for stmt in statements:
                            conn.execute(stmt)

                        # Migration-specific Python helper execution
                        if pending.sequence_num == 26 or pending.migration_id == "026_pericope_segmentation":
                            _backfill_and_validate_migration_026(conn)

                        # Post-execution foreign key verification
                        fk_check = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
                        if fk_check != 1:
                            raise MigrationIntegrityError(
                                f"Migration '{pending.migration_id}' attempted to disable foreign keys."
                            )

                        # Record applied migration metadata
                        applied_at = datetime.now(timezone.utc).isoformat()
                        version_str = str(pending.sequence_num)
                        conn.execute(
                            "INSERT INTO schema_migrations ("
                            "migration_id, version, applied_at, checksum_sha256, description"
                            ") VALUES (?, ?, ?, ?, ?);",
                            (
                                pending.migration_id,
                                version_str,
                                applied_at,
                                pending.checksum_sha256,
                                pending.description,
                            ),
                        )

                        rec = MigrationRecord(
                            migration_id=pending.migration_id,
                            version=version_str,
                            applied_at=applied_at,
                            checksum_sha256=pending.checksum_sha256,
                            description=pending.description,
                        )
                        newly_applied.append(rec)

                except Exception as e:
                    # Savepoint automatically rolled back
                    if isinstance(e, MigrationIntegrityError):
                        raise
                    raise MigrationExecutionError(pending.migration_id, e) from e

                if target_migration_id and pending.migration_id == target_migration_id:
                    break

            return newly_applied


def main() -> None:
    """CLI Entrypoint forwarding to bible_engine.cli."""
    from bible_engine.cli import main as cli_main
    sys.exit(cli_main())


if __name__ == "__main__":
    main()
