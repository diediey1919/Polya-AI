"""
Task 1.2 Focused Test Suite: Database Access Layer.
Verifies connection lifecycle, foreign-key enforcement, transaction semantics,
read/write separation, safe parameterization, and authoritative schema initialization.
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bible_engine import (
    DEFAULT_DB_PATH,
    DatabaseConfig,
    DatabaseEngine,
    create_connection,
    create_in_memory_database,
    init_schema,
)
from bible_engine.errors import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseTransactionError,
    ReadOnlyViolationError,
    SchemaInitializationError,
)


class TestDatabaseLayer(unittest.TestCase):
    """Focused Task 1.2 Database Layer Tests."""

    def setUp(self) -> None:
        self.base_tmp = Path(__file__).resolve().parent / "_test_tmp"
        self.base_tmp.mkdir(parents=True, exist_ok=True)
        self.temp_dir = tempfile.TemporaryDirectory(dir=str(self.base_tmp))
        self.db_file = os.path.join(self.temp_dir.name, "test_bible.db")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        if self.base_tmp.exists():
            try:
                self.base_tmp.rmdir()
            except OSError:
                pass

    # -------------------------------------------------------------------------
    # 1. Connection opens successfully
    # -------------------------------------------------------------------------
    def test_01_connection_opens_successfully(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        conn = create_connection(cfg)
        self.assertIsNotNone(conn)
        row = conn.execute("SELECT 1 AS alive;").fetchone()
        self.assertEqual(row["alive"], 1)
        conn.close()

    # -------------------------------------------------------------------------
    # 2. Foreign keys are enabled
    # -------------------------------------------------------------------------
    def test_02_foreign_keys_are_enabled(self) -> None:
        cfg = DatabaseConfig(db_path=":memory:")
        conn = create_connection(cfg)
        fk = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        self.assertEqual(fk, 1, "PRAGMA foreign_keys must be 1 (ON).")

        conn.execute("CREATE TABLE parent (id TEXT PRIMARY KEY);")
        conn.execute(
            "CREATE TABLE child (id TEXT PRIMARY KEY, parent_id TEXT, "
            "FOREIGN KEY (parent_id) REFERENCES parent(id));"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO child VALUES ('c1', 'nonexistent_p');")

        # Verify configuration cannot disable foreign keys
        with self.assertRaises(DatabaseConfigurationError):
            DatabaseConfig(foreign_keys=False)

        # Verify SQL execution blocks disabling foreign keys
        engine = DatabaseEngine(cfg)
        with self.assertRaises(DatabaseConfigurationError):
            engine.execute("PRAGMA foreign_keys = OFF;")
        with self.assertRaises(DatabaseConfigurationError):
            engine.execute("PRAGMA foreign_keys=0;")
        engine.close()
        conn.close()

    # -------------------------------------------------------------------------
    # 3. Valid parameterized query executes
    # -------------------------------------------------------------------------
    def test_03_valid_parameterized_query_executes(self) -> None:
        cfg = DatabaseConfig(db_path=":memory:")
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT, n INTEGER);")

        # Positional tuple parameterization
        engine.execute(
            "INSERT INTO kv (k, v, n) VALUES (?, ?, ?);",
            ("witness_alpha", "Codex Sinaiticus", 4),
        )
        row = engine.fetch_one("SELECT * FROM kv WHERE k = ?;", ("witness_alpha",))
        self.assertIsNotNone(row)
        self.assertEqual(row["k"], "witness_alpha")
        self.assertEqual(row["v"], "Codex Sinaiticus")
        self.assertEqual(row["n"], 4)

        # Named dictionary parameterization
        engine.execute(
            "INSERT INTO kv (k, v, n) VALUES (:k, :v, :n);",
            {"k": "witness_beta", "v": "Codex Vaticanus", "n": 4},
        )
        row_named = engine.fetch_one("SELECT * FROM kv WHERE k = :k;", {"k": "witness_beta"})
        self.assertIsNotNone(row_named)
        self.assertEqual(row_named["v"], "Codex Vaticanus")

        # Execute many
        batch = [
            ("batch_1", "Text A", 10),
            ("batch_2", "Text B", 20),
        ]
        engine.execute_many("INSERT INTO kv (k, v, n) VALUES (?, ?, ?);", batch)
        all_rows = engine.fetch_all("SELECT * FROM kv ORDER BY n;")
        self.assertEqual(len(all_rows), 4)

        engine.close()

    # -------------------------------------------------------------------------
    # 4. Transaction commits
    # -------------------------------------------------------------------------
    def test_04_transaction_commits(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE ledger (id TEXT PRIMARY KEY, amount INT);")

        with engine.transaction() as conn:
            conn.execute("INSERT INTO ledger VALUES ('TX1', 100);")
            conn.execute("INSERT INTO ledger VALUES ('TX2', 200);")

        rows = engine.fetch_all("SELECT * FROM ledger ORDER BY id;")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "TX1")
        self.assertEqual(rows[1]["id"], "TX2")
        engine.close()

    # -------------------------------------------------------------------------
    # 5. Transaction rolls back
    # -------------------------------------------------------------------------
    def test_05_transaction_rolls_back(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE audit (id TEXT PRIMARY KEY, note TEXT);")

        with self.assertRaises(RuntimeError):
            with engine.transaction() as conn:
                conn.execute("INSERT INTO audit VALUES ('A1', 'committed note');")
                raise RuntimeError("Simulated failure inside transaction")

        rows = engine.fetch_all("SELECT * FROM audit;")
        self.assertEqual(len(rows), 0, "All uncommitted rows must be rolled back on exception.")
        engine.close()

    # -------------------------------------------------------------------------
    # 6. Integrity errors propagate
    # -------------------------------------------------------------------------
    def test_06_integrity_errors_propagate(self) -> None:
        cfg = DatabaseConfig(db_path=":memory:")
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE unique_tbl (id TEXT PRIMARY KEY);")
        engine.execute("INSERT INTO unique_tbl VALUES ('primary_key_1');")

        # Test UNIQUE constraint violation
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            with engine.transaction() as conn:
                conn.execute("INSERT INTO unique_tbl VALUES ('primary_key_1');")

        self.assertIn("UNIQUE constraint failed", str(ctx.exception))

        # Verify transaction state was cleanly rolled back
        rows = engine.fetch_all("SELECT * FROM unique_tbl;")
        self.assertEqual(len(rows), 1)
        engine.close()

    # -------------------------------------------------------------------------
    # 7. Connection closes cleanly
    # -------------------------------------------------------------------------
    def test_07_connection_closes_cleanly(self) -> None:
        cfg = DatabaseConfig(db_path=":memory:")
        conn = create_connection(cfg)
        conn.close()

        with self.assertRaises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1;")

    # -------------------------------------------------------------------------
    # 8. In-memory database works for tests
    # -------------------------------------------------------------------------
    def test_08_in_memory_database_works_for_tests(self) -> None:
        conn = create_in_memory_database(init_schema_tables=True)
        self.assertIsNotNone(conn)

        # Check tables populated from 001_initial_schema.sql
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        table_names = {t["name"] for t in tables}

        expected_core_tables = {
            "schema_migrations",
            "canons",
            "testaments",
            "books",
            "pericopes",
            "passages",
            "witnesses",
            "critical_editions",
            "source_texts",
            "tokens",
            "lemmas",
            "evidence_ledger",
            "claims",
            "referential_relations",
        }
        for expected in expected_core_tables:
            self.assertIn(expected, table_names, f"Expected table '{expected}' missing from schema.")

        conn.close()

    # -------------------------------------------------------------------------
    # 9. Two independent connections do not unexpectedly share transaction state
    # -------------------------------------------------------------------------
    def test_09_two_independent_connections_do_not_share_transaction_state(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        
        # Prepare table
        init_conn = create_connection(cfg)
        init_conn.execute("CREATE TABLE isolation_test (id TEXT PRIMARY KEY, val TEXT);")
        init_conn.close()

        conn1 = create_connection(cfg)
        conn2 = create_connection(cfg)

        # Conn1 begins an explicit transaction and inserts a row
        conn1.execute("BEGIN IMMEDIATE;")
        conn1.execute("INSERT INTO isolation_test VALUES ('iso_1', 'uncommitted_state');")

        # Conn2 queries the table; row should NOT be visible before commit
        row_conn2 = conn2.execute("SELECT * FROM isolation_test WHERE id = 'iso_1';").fetchone()
        self.assertIsNone(row_conn2, "Uncommitted transaction in conn1 must not leak into conn2.")

        # Conn1 commits
        conn1.execute("COMMIT;")

        # Now conn2 sees it
        row_conn2_after = conn2.execute("SELECT * FROM isolation_test WHERE id = 'iso_1';").fetchone()
        self.assertIsNotNone(row_conn2_after)
        self.assertEqual(row_conn2_after["val"], "uncommitted_state")

        conn1.close()
        conn2.close()

    # -------------------------------------------------------------------------
    # 10. Database layer does not silently disable schema constraints
    # -------------------------------------------------------------------------
    def test_10_database_layer_does_not_silently_disable_schema_constraints(self) -> None:
        conn = create_in_memory_database(init_schema_tables=True)

        # 10.1 Check CHECK constraint on books.original_primary_language
        # Valid: 'HEBREW', 'ARAMAIC', 'GREEK'
        # First insert prerequisite canon & testament
        conn.execute("INSERT INTO canons VALUES ('PROT_66', 'Protestant', '66 Books', '2026-09-30');")
        conn.execute("INSERT INTO testaments VALUES ('NT', 'PROT_66', 'New Testament', 2);")

        # Invalid language 'LATIN' must trigger IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'LATIN', 22);"
            )

        # 10.2 Check Foreign Key constraint: reference non-existent testament
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO books VALUES ('REV', 'NONEXISTENT_TESTAMENT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);"
            )

        # 10.3 Check Identity Firewall constraint on referential_relations:
        # CHECK(relation_type != 'STRICT_IDENTITY' OR (is_identity_established = 1 AND evidence_id IS NOT NULL))
        # Prerequisites: books -> pericopes -> passages -> entities
        conn.execute("INSERT INTO books VALUES ('REV', 'NT', 66, 'Wahyu', 'Revelation', 'GREEK', 22);")
        conn.execute(
            "INSERT INTO pericopes VALUES ('PER-1', 'REV', 'Wahyu 19:7-9', 19, 7, 19, 9, 'APOCALYPTIC', 'NA28', 'HIGH', 'REGISTERED', '1.0', '2026-09-30');"
        )
        conn.execute(
            "INSERT INTO passages VALUES ('REV-19-08', 'PER-1', 'REV', 19, 8, 1);"
        )
        conn.execute(
            "INSERT INTO entities VALUES ('ENT-1', 'Entity A', 'SYMBOLIC_FIGURE', 'SYMBOL', 'desc');"
        )
        conn.execute(
            "INSERT INTO entities VALUES ('ENT-2', 'Entity B', 'CORPORATE_COMMUNITY', 'LITERAL_ENTITY', 'desc');"
        )

        # STRICT_IDENTITY without evidence_id and without is_identity_established=1 must FAIL (Identity Firewall)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO referential_relations ("
                "relation_id, source_entity_id, target_entity_id, passage_id, relation_type, "
                "evidence_id, grammatical_justification, evidence_status, is_identity_established"
                ") VALUES ('REL-1', 'ENT-1', 'ENT-2', 'REV-19-08', 'STRICT_IDENTITY', "
                "NULL, 'No evidence', '[UNSUPPORTED]', 0);"
            )

        conn.close()

    # -------------------------------------------------------------------------
    # 11. Read/Write separation and query_only enforcement
    # -------------------------------------------------------------------------
    def test_11_read_write_separation(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE ro_test (id TEXT PRIMARY KEY, val TEXT);")
        engine.execute("INSERT INTO ro_test VALUES ('r1', 'initial_val');")

        # Acquire read-only connection
        read_conn = engine.get_read_connection()
        self.assertEqual(read_conn.execute("PRAGMA query_only;").fetchone()[0], 1)

        # Attempt write on read connection must fail
        with self.assertRaises(sqlite3.OperationalError):
            read_conn.execute("INSERT INTO ro_test VALUES ('r2', 'illegal_mutation');")

        # Attempt write transaction on read connection via engine must raise ReadOnlyViolationError
        with self.assertRaises(ReadOnlyViolationError):
            with engine.transaction(conn=read_conn):
                pass

        read_conn.close()
        engine.close()

    # -------------------------------------------------------------------------
    # 12. Nested transaction with SAVEPOINT
    # -------------------------------------------------------------------------
    def test_12_nested_transaction_savepoint(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE sp_test (id TEXT PRIMARY KEY);")

        with engine.transaction() as conn:
            conn.execute("INSERT INTO sp_test VALUES ('outer_1');")

            # Nested transaction with savepoint that fails
            try:
                with engine.transaction(conn=conn, savepoint=True):
                    conn.execute("INSERT INTO sp_test VALUES ('inner_fail');")
                    raise ValueError("Inner failure")
            except ValueError:
                pass

            # Outer transaction proceeds
            conn.execute("INSERT INTO sp_test VALUES ('outer_2');")

        rows = engine.fetch_all("SELECT * FROM sp_test ORDER BY id;")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["id"], "outer_1")
        self.assertEqual(rows[1]["id"], "outer_2")

        # Nested transaction without savepoint disallowed
        with self.assertRaises(DatabaseTransactionError):
            with engine.transaction() as conn:
                with engine.transaction(conn=conn, savepoint=False):
                    pass

        engine.close()

    # -------------------------------------------------------------------------
    # 13. Graceful handling of connection failures
    # -------------------------------------------------------------------------
    def test_13_connection_failure_handling(self) -> None:
        non_existent_file = os.path.join(self.temp_dir.name, "does_not_exist.db")
        cfg = DatabaseConfig(db_path=non_existent_file, read_only=True)
        with self.assertRaises(DatabaseConnectionError):
            create_connection(cfg)

    # -------------------------------------------------------------------------
    # 14. Schema initialization error handling
    # -------------------------------------------------------------------------
    def test_14_schema_init_failure_on_invalid_path(self) -> None:
        conn = create_connection(DatabaseConfig(db_path=":memory:"))
        with self.assertRaises(SchemaInitializationError):
            init_schema(conn, "/path/to/nonexistent/schema.sql")
        conn.close()

    # -------------------------------------------------------------------------
    # 15. Environment-based configuration resolution
    # -------------------------------------------------------------------------
    def test_15_config_env_resolution(self) -> None:
        custom_path = os.path.join(self.temp_dir.name, "env_bible.db")
        old_env = os.environ.get("POLYA_BIBLE_DB_PATH")
        try:
            os.environ["POLYA_BIBLE_DB_PATH"] = custom_path
            cfg = DatabaseConfig.from_env()
            self.assertEqual(cfg.db_path, custom_path)
            self.assertEqual(cfg.resolve_db_path(), str(Path(custom_path).resolve()))
        finally:
            if old_env is not None:
                os.environ["POLYA_BIBLE_DB_PATH"] = old_env
            else:
                os.environ.pop("POLYA_BIBLE_DB_PATH", None)

    # -------------------------------------------------------------------------
    # 16. Protection against all foreign-key bypass patterns
    # -------------------------------------------------------------------------
    def test_16_foreign_key_bypass_patterns_blocked(self) -> None:
        cfg = DatabaseConfig(db_path=":memory:")
        engine = DatabaseEngine(cfg)

        bypass_attempts = [
            "PRAGMA foreign_keys = OFF;",
            "pragma foreign_keys=off;",
            "PRAGMA foreign_keys = 0;",
            "pragma   foreign_keys  =  0 ;",
            "PRAGMA foreign_keys = NO;",
            "PRAGMA foreign_keys = FALSE;",
        ]
        for bypass_sql in bypass_attempts:
            with self.assertRaises(DatabaseConfigurationError, msg=f"Should block: {bypass_sql}"):
                engine.execute(bypass_sql)

        engine.close()

    # -------------------------------------------------------------------------
    # 17. Engine connect context manager lifecycle
    # -------------------------------------------------------------------------
    def test_17_engine_connect_context_manager(self) -> None:
        cfg = DatabaseConfig(db_path=self.db_file)
        engine = DatabaseEngine(cfg)
        engine.execute("CREATE TABLE ctx_test (id TEXT PRIMARY KEY);")

        with engine.connect(read_only=False) as conn:
            conn.execute("INSERT INTO ctx_test VALUES ('val1');")

        with engine.connect(read_only=True) as conn:
            row = conn.execute("SELECT * FROM ctx_test;").fetchone()
            self.assertEqual(row["id"], "val1")
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("INSERT INTO ctx_test VALUES ('val2');")

        engine.close()


if __name__ == "__main__":
    unittest.main()

