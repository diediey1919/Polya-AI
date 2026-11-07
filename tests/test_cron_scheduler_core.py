"""
Test suite for cron scheduler core functionality.
Tests: registration, scheduling logic, idempotency, concurrency, recovery.
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.skip("Cron scheduler telah dikonsolidasikan ke controller.py", allow_module_level=True)

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from orchestrator.automation.cron_scheduler import CronScheduler, SchedulerLock
from orchestrator.automation.scheduled_states import ScheduledJobStatus

@pytest.fixture
def temp_db_path(tmp_path):
    return str(tmp_path / "test_cron_scheduler.db")

@pytest.fixture
def scheduler(temp_db_path):
    return CronScheduler(db_path=temp_db_path)

class TestSchedulerRegistration:
    def test_register_job(self, scheduler):
        """Test job registration creates proper records."""
        now = datetime.now(timezone.utc).isoformat()
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO automation_scheduled_jobs 
                (schedule_id, cron_expression, job_definition_hash, target_graph,
                 job_config_json, created_at, updated_at, next_run_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test_job_1", "*/5 * * * *", "test_hash", "canary", "{}", now, now, now)
            )
        
        with scheduler.controller.db_manager._get_connection() as conn:
            cursor = conn.cursor()
            row = cursor.execute(
                "SELECT * FROM automation_scheduled_jobs WHERE schedule_id = ?",
                ("test_job_1",)
            ).fetchone()
            
            assert row is not None
            assert row["schedule_id"] == "test_job_1"
            assert row["target_graph"] == "canary"
            assert row["status"] == "ACTIVE"

    def test_duplicate_registration_replaces(self, scheduler):
        """Test that duplicate schedule_id replaces existing entry."""
        now = datetime.now(timezone.utc).isoformat()
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                "INSERT INTO automation_scheduled_jobs (schedule_id, cron_expression, job_definition_hash, target_graph, job_config_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("dup_test", "*/5 * * * *", "h1", "canary", "{}", now, now)
            )
        
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO automation_scheduled_jobs (schedule_id, cron_expression, job_definition_hash, target_graph, job_config_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("dup_test", "*/10 * * * *", "h2", "canary", '{"updated": true}', now, now)
            )
        
        with scheduler.controller.db_manager._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM automation_scheduled_jobs WHERE schedule_id = 'dup_test'").fetchone()
            assert row["cnt"] == 1

class TestCronLogic:
    def test_cron_parsing_every_5_minutes(self, scheduler):
        """Test '*/5 * * * *' parsing."""
        result = scheduler._compute_next_run("*/5 * * * *")
        assert result is not None
        assert result.second == 0

    def test_cron_parsing_invalid(self, scheduler):
        """Test invalid cron expression returns None."""
        result = scheduler._compute_next_run("invalid cron expr")
        assert result is None

class TestIdempotency:
    def test_recent_execution_blocks_rerun(self, scheduler):
        """Test that jobs run within 10 minutes are blocked."""
        now = datetime.now(timezone.utc).isoformat()
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO automation_cron_executions 
                (execution_id, schedule_id, correlation_id, started_at, langgraph_thread_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("exec_test1", "test_job_1", "corr_1", now, "thread_1", "COMPLETED")
            )
        
        assert scheduler._idempotency_check("test_job_1") is True

    def test_old_execution_allows_rerun(self, scheduler):
        """Test that jobs older than 10 minutes don't block."""
        old_time = (datetime.now(timezone.utc).timestamp() - 600)
        old_dt = datetime.fromtimestamp(old_time, timezone.utc).isoformat()
        
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO automation_cron_executions 
                (execution_id, schedule_id, correlation_id, started_at, langgraph_thread_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                ("exec_old", "test_job_1", "corr_old", old_dt, "thread_old", "COMPLETED")
            )
        
        assert scheduler._idempotency_check("test_job_1") is False

class TestConcurrencyAndLocking:
    def test_single_instance_lock(self, tmp_path):
        """Test scheduler lock prevents multiple instances."""
        lock_file = str(tmp_path / "test_lock.lock")
        lock1 = SchedulerLock(lock_file)
        lock2 = SchedulerLock(lock_file)
        
        assert lock1.acquire() is True
        assert lock2.acquire() is False
        
        lock1.release()
        assert lock2.acquire() is True
        lock2.release()

    def test_is_disabled_check(self, scheduler, monkeypatch):
        """Test POLYA_CRON_DISABLED environment variable."""
        monkeypatch.setenv("POLYA_CRON_DISABLED", "1")
        assert scheduler._is_disabled() is True
        
        monkeypatch.setenv("POLYA_CRON_DISABLED", "0")
        assert scheduler._is_disabled() is False

class TestRecovery:
    def test_recover_stale_jobs(self, scheduler):
        """Test recovery resets stale RUNNING jobs to PENDING."""
        old_update = (datetime.now(timezone.utc).timestamp() - 7200)
        old_dt = datetime.fromtimestamp(old_update, timezone.utc).isoformat()
        
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO automation_scheduled_jobs 
                (schedule_id, cron_expression, job_definition_hash, target_graph, 
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                ("stale_job", "*/5 * * * *", "hash", "canary", "RUNNING", old_dt, old_dt)
            )
        
        recovered = scheduler.recover_stale_jobs()
        assert recovered == 1
        
        with scheduler.controller.db_manager._get_connection() as conn:
            row = conn.execute(
                "SELECT status FROM automation_scheduled_jobs WHERE schedule_id = 'stale_job'"
            ).fetchone()
            assert row["status"] == ScheduledJobStatus.PENDING.value

class TestDryRun:
    def test_dry_run_does_not_execute(self, scheduler):
        """Test --dry-run mode does not execute real jobs."""
        now = datetime.now(timezone.utc).isoformat()
        with scheduler.controller.db_manager._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO automation_scheduled_jobs 
                (schedule_id, cron_expression, job_definition_hash, target_graph,
                 job_config_json, created_at, updated_at, next_run_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("dryrun_test", "*/5 * * * *", "hash", "canary", "{}", now, now, now)
            )
        
        result = scheduler.run_cycle(dry_run=True)
        
        assert result["status"] == "SUCCESS"
        assert result["jobs_found"] == 1


if __name__ == "__main__":
    VENV_PYTHON = Path.home() / "venv" / "bin" / "python3"
    if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON)] + sys.argv)
    pytest.main([__file__])

