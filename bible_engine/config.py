"""
Database Configuration for Polya Philological Bible Engine (Phase 1, Task 1.2).
Handles path resolution, environment variables, pragmas, and schema authority location.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from bible_engine.errors import DatabaseConfigurationError, SchemaInitializationError

DEFAULT_DB_PATH = "/home/ubuntu/.polya/bible_engine.db"


@dataclass
class DatabaseConfig:
    """
    Configuration parameters for SQLite database connection and operations.
    Enforces mandatory foreign-key constraints and deterministic connection settings.
    """
    db_path: str = DEFAULT_DB_PATH
    read_only: bool = False
    busy_timeout_ms: int = 5000
    wal_mode: bool = True
    synchronous: str = "NORMAL"
    foreign_keys: bool = True
    schema_path: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.foreign_keys:
            raise DatabaseConfigurationError(
                "Foreign key enforcement (PRAGMA foreign_keys = ON) is mandatory and cannot be disabled."
            )
        if self.busy_timeout_ms < 0:
            raise DatabaseConfigurationError("busy_timeout_ms must be non-negative.")

    @classmethod
    def from_env(cls, read_only: bool = False) -> "DatabaseConfig":
        """Build DatabaseConfig from environment variables with fallbacks."""
        db_path = (
            os.environ.get("POLYA_BIBLE_DB_PATH")
            or os.environ.get("BIBLE_ENGINE_DB_PATH")
            or os.environ.get("POLYA_DB_PATH")
            or DEFAULT_DB_PATH
        )
        schema_path = os.environ.get("BIBLE_SCHEMA_PATH")
        return cls(
            db_path=db_path,
            read_only=read_only,
            schema_path=schema_path,
        )

    def is_in_memory(self) -> bool:
        """Check if target database is an SQLite in-memory instance."""
        return self.db_path == ":memory:" or self.db_path.startswith("file::memory:")

    def resolve_db_path(self) -> str:
        """
        Resolve absolute database file path.
        Creates parent directories for file-based databases if not in read-only mode.
        """
        if self.is_in_memory():
            return self.db_path

        path_obj = Path(self.db_path).expanduser().resolve()
        resolved_str = str(path_obj)

        if not self.read_only:
            path_obj.parent.mkdir(parents=True, exist_ok=True)

        return resolved_str

    def resolve_schema_path(self) -> str:
        """
        Resolve authoritative schema path (001_initial_schema.sql).
        Verifies existence and readability.
        """
        candidates = []
        if self.schema_path:
            candidates.append(Path(self.schema_path))

        env_path = os.environ.get("BIBLE_SCHEMA_PATH")
        if env_path:
            candidates.append(Path(env_path))

        # Check relative to module location (root of Polya-AI repo)
        repo_root = Path(__file__).resolve().parent.parent
        candidates.append(repo_root / "schemas" / "bible_engine" / "001_initial_schema.sql")

        # Check relative to cwd
        candidates.append(Path.cwd() / "schemas" / "bible_engine" / "001_initial_schema.sql")

        # Static absolute fallback
        candidates.append(Path("/home/ubuntu/Polya-AI/schemas/bible_engine/001_initial_schema.sql"))

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate.resolve())

        raise SchemaInitializationError(
            f"Authoritative schema file '001_initial_schema.sql' not found. "
            f"Searched candidates: {[str(c) for c in candidates]}"
        )
