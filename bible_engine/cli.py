"""
Command Line Interface for Polya Philological Bible Engine Migration Runner.
Usage:
  python3 -m bible_engine status [--db-path ...] [--migrations-dir ...]
  python3 -m bible_engine migrate [--db-path ...] [--migrations-dir ...]
"""

import argparse
import sys
from typing import Optional, Sequence

from bible_engine.config import DatabaseConfig
from bible_engine.database import DatabaseEngine
from bible_engine.errors import MigrationError
from bible_engine.migrations import MigrationRunner


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python3 -m bible_engine",
        description="Polya Philological Bible Engine - Database Migration Runner",
    )
    parser.add_argument(
        "action",
        choices=["status", "migrate"],
        help="Action: 'status' reports schema state, 'migrate' applies pending migrations.",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Path to SQLite database file (defaults to POLYA_BIBLE_DB_PATH or ~/.polya/bible_engine.db).",
    )
    parser.add_argument(
        "--migrations-dir",
        default=None,
        help="Directory containing migration SQL scripts (defaults to schemas/bible_engine).",
    )

    args = parser.parse_args(argv)

    cfg = DatabaseConfig.from_env()
    if args.db_path:
        cfg = DatabaseConfig(db_path=args.db_path)

    engine = DatabaseEngine(cfg)
    runner = MigrationRunner(engine, migrations_dir=args.migrations_dir)

    try:
        if args.action == "status":
            status = runner.get_status()
            print("=== BIBLE ENGINE MIGRATION STATUS ===")
            print(status.summary())
            if status.pending_migrations:
                print("\nPending Migrations:")
                for p in status.pending_migrations:
                    print(f"  - [{p.sequence_num:03d}] {p.migration_id} ({p.path.name})")
            return 0
        elif args.action == "migrate":
            print("Discovering pending migrations...")
            applied = runner.apply_pending()
            if not applied:
                print("Database is already up to date. Zero migrations applied.")
            else:
                print(f"Successfully applied {len(applied)} migration(s):")
                for r in applied:
                    print(f"  + [{r.version}] {r.migration_id} at {r.applied_at}")
            return 0
    except MigrationError as e:
        print(f"\n[MIGRATION ERROR] {e}", file=sys.stderr)
        return 1
    finally:
        engine.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
