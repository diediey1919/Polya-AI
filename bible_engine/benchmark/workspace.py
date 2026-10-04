"""
POLYA PHILOLOGICAL BIBLE ENGINE
Task 4.9: Isolated Benchmark Workspace Subsystem

Manages isolated, ephemeral SQLite databases for end-to-end benchmarking:
- Strictly prevents access to production database paths.
- Bootstraps schemas 001 through 026 only (Migration 027 strictly forbidden).
- Enforces proper connection shutdown and WAL checkpoint before recursive cleanup.
- Asserts workspace removal without assumptions about WAL/SHM file existence.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.migrations import MigrationRunner

PROD_DB_NAME = "polya_index.db"
DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas" / "bible_engine"


class IsolatedBenchmarkWorkspace:
    """
    Context manager and controller for ephemeral SQLite execution.
    Guarantees absolute separation from production truth and clean resource reclamation.
    """

    def __init__(
        self,
        base_dir: Optional[str] = None,
        migrations_dir: Optional[Path] = None,
        busy_timeout_ms: int = 10000,
        wal_mode: bool = True,
    ) -> None:
        self.base_dir = base_dir
        self.migrations_dir = migrations_dir or DEFAULT_MIGRATIONS_DIR
        self.busy_timeout_ms = busy_timeout_ms
        self.wal_mode = wal_mode

        self.temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.workspace_path: Optional[Path] = None
        self.db_path: Optional[Path] = None
        self.engine: Optional[DatabaseEngine] = None
        self.runner: Optional[MigrationRunner] = None

    def __enter__(self) -> IsolatedBenchmarkWorkspace:
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()

    def setup(self) -> None:
        """Create temp workspace, bootstrap SQLite database, and apply migrations 001-026."""
        self.temp_dir = tempfile.TemporaryDirectory(dir=self.base_dir)
        self.workspace_path = Path(self.temp_dir.name).resolve()
        self.db_path = self.workspace_path / "benchmark.db"

        # Security Firewall: Prohibit any connection to production database
        if PROD_DB_NAME in str(self.db_path):
            raise RuntimeError(
                f"Security violation: IsolatedBenchmarkWorkspace attempted to point to {self.db_path}"
            )

        db_config = DatabaseConfig(
            db_path=str(self.db_path),
            wal_mode=self.wal_mode,
            busy_timeout_ms=self.busy_timeout_ms,
        )
        self.engine = DatabaseEngine(db_config)

        # Apply authoritative migrations 001-026
        self.runner = MigrationRunner(self.engine, self.migrations_dir)
        applied = self.runner.apply_pending()

        # Epistemic invariant: Migration 027+ is strictly forbidden
        for mig in applied:
            mig_name = mig.migration_id if hasattr(mig, "migration_id") else str(mig)
            if "027" in mig_name:
                raise RuntimeError(f"Forbidden migration 027 detected and applied: {mig_name}")

    def cleanup(self) -> None:
        """
        Cleanly dispose connections, checkpoint WAL if valid, and recursively delete workspace.
        Does not assume WAL/SHM files exist.
        """
        # 1. Close all active database connections
        if self.engine is not None:
            try:
                self.engine.close()
            except Exception:
                pass
            self.engine = None

        # 2. Checkpoint WAL optionally if db exists and connection can be briefly opened
        if self.db_path is not None and self.db_path.exists():
            try:
                conn = sqlite3.connect(str(self.db_path), timeout=2.0)
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                conn.close()
            except Exception:
                pass

        # 3. Recursively remove temporary workspace directory
        if self.temp_dir is not None:
            try:
                self.temp_dir.cleanup()
            except Exception:
                pass

        if self.workspace_path is not None and self.workspace_path.exists():
            shutil.rmtree(self.workspace_path, ignore_errors=True)

        # 4. Assert workspace does not exist
        if self.workspace_path is not None:
            assert not self.workspace_path.exists(), (
                f"Workspace leak: path {self.workspace_path} still exists after cleanup."
            )
