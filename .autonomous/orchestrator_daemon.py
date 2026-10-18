#!/usr/bin/env python3
"""
Autonomous Multi-Agent Orchestrator Daemon
-------------------------------------------
Orchestrates 6 specialist agents (hermes, claude, codex, gemini, polya, antigravity)
for the Polya Apologetika OS project.

Workflow per cycle:
  1. Acquire flock on .autonomous/locks/orchestrator.lock — prevents overlap
  2. Fetch highest-priority PENDING task from task_queue.db
  3. Dispatch to assigned agent worker
  4. Run verification command
  5. Update task status to VERIFYING → DONE or FAILED
  6. If FAILED and retry_count < max_retries → reset to PENDING
  7. Release lock

Cron entry (every 15 minutes):
  */15 * * * * cd /home/ubuntu/Polya-AI && /home/ubuntu/venv/bin/python .autonomous/orchestrator_daemon.py >> .autonomous/logs/cron_master.log 2>&1
"""
import os
import sys
import json
import time
import sqlite3
import subprocess
import fcntl
import logging
from pathlib import Path
from datetime import datetime, timezone

# ─── Paths ───────────────────────────────────────────────────────────────────
PROJ_ROOT = Path("/home/ubuntu/Polya-AI")
AUTO_DIR = PROJ_ROOT / ".autonomous"
DB_PATH = AUTO_DIR / "task_queue.db"
LOGS_DIR = AUTO_DIR / "logs"
LOCKS_DIR = AUTO_DIR / "locks"
PIDS_DIR = AUTO_DIR / "pids"
AGENTS_DIR = PROJ_ROOT / ".claude" / "agents"

for d in [AUTO_DIR, LOGS_DIR, LOCKS_DIR, PIDS_DIR, AGENTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Logging ─────────────────────────────────────────────────────────────────
MASTER_LOG = LOGS_DIR / "cron_master.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s UTC] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(MASTER_LOG), mode="a"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("orchestrator")

# ─── Agent worker script paths ───────────────────────────────────────────────
AGENT_SCRIPTS = {
    "hermes":       AUTO_DIR / "agents" / "hermes_worker.py",
    "claude":       AUTO_DIR / "agents" / "claude_worker.py",
    "codex":        AUTO_DIR / "agents" / "codex_worker.py",
    "gemini":       AUTO_DIR / "agents" / "gemini_worker.py",
    "polya":        AUTO_DIR / "agents" / "polya_worker.py",
    "antigravity":  AUTO_DIR / "agents" / "antigravity_scanner.py",
}

PYTHON = str(PROJ_ROOT.parent / "venv" / "bin" / "python") or sys.executable
if not Path(PYTHON).exists():
    PYTHON = sys.executable


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def acquire_lock():
    """Acquire exclusive flock to prevent overlapping cron runs."""
    lock_file = LOCKS_DIR / "orchestrator.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_fh = open(lock_file, "w")
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_fh
    except (IOError, OSError):
        log.warning("Orchestrator lock held by another process — exiting.")
        lock_fh.close()
        return None


def release_lock(lock_fh):
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_UN)
        lock_fh.close()
    except Exception:
        pass


def get_next_task(conn):
    """Fetch the highest-priority PENDING task (P0→P1→P2→P3)."""
    cur = conn.cursor()
    cur.execute("""
        SELECT task_id, assigned_agent, target_files, verification_cmd, retry_count, max_retries
        FROM task_queue
        WHERE status = 'PENDING'
        ORDER BY CASE priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END ASC,
                 created_at ASC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        return {
            "task_id": row[0],
            "agent": row[1],
            "target_files": row[2],
            "verification_cmd": row[3],
            "retry_count": row[4],
            "max_retries": row[5],
        }
    return None


def update_task_status(conn, task_id, status, error=None):
    """Update task status and error field."""
    cur = conn.cursor()
    cur.execute("""
        UPDATE task_queue
        SET status = ?, last_error = ?, updated_at = ?
        WHERE task_id = ?
    """, (status, error or "", now_iso(), task_id))
    conn.commit()
    log.info(f"Task {task_id} → {status}" + (f" | error: {error}" if error else ""))


def write_pid(pid_file):
    """Write current PID to pid file."""
    pid_path = PIDS_DIR / pid_file
    pid_path.write_text(str(os.getpid()))
    return pid_path


def remove_pid(pid_file):
    try:
        (PIDS_DIR / pid_file).unlink(missing_ok=True)
    except Exception:
        pass


def run_verification(cmd, timeout=120):
    """Run verification command, return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJ_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJ_ROOT)},
        )
        output = (result.stdout + "\n" + result.stderr).strip()[-500:]  # truncate
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "VERIFICATION TIMEOUT"
    except Exception as e:
        return False, f"VERIFICATION ERROR: {e}"


def dispatch_agent(task):
    """Dispatch task to the assigned agent worker script."""
    agent = task["agent"]
    worker = AGENT_SCRIPTS.get(agent)
    if not worker or not worker.exists():
        # If no worker script exists yet, run verification-only mode
        log.warning(f"No worker script for agent '{agent}' at {worker} — verification-only mode.")
        return True  # placeholder: agents make their own patches

    # Write PID
    write_pid(f"{agent}.pid")

    try:
        result = subprocess.run(
            [PYTHON, str(worker), task["task_id"]],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(PROJ_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJ_ROOT)},
        )
        agent_output = result.stdout[-1000:]  # truncate
        agent_log = LOGS_DIR / f"{agent}.log"
        agent_log.parent.mkdir(parents=True, exist_ok=True)
        with open(agent_log, "a") as f:
            f.write(f"\n[{now_iso()}] Task {task['task_id']} dispatched\n")
            f.write(agent_output)
            if result.stderr:
                f.write(f"\nSTDERR: {result.stderr[-500:]}")

        return True
    except subprocess.TimeoutExpired:
        log.error(f"Agent {agent} timed out on task {task['task_id']}")
        return False
    finally:
        remove_pid(f"{agent}.pid")


def main():
    lock_fh = acquire_lock()
    if not lock_fh:
        return

    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row

    # Also run antigravity scanner if no tasks are pending (always-on QA)
    task = get_next_task(conn)
    if task is None:
        # No tasks pending — run antigravity self-healing scan
        log.info("No PENDING tasks. Running antigravity self-healing scan...")
        ag_worker = AGENT_SCRIPTS["antigravity"]
        if ag_worker and ag_worker.exists():
            write_pid("antigravity.pid")
            try:
                subprocess.run(
                    [PYTHON, str(ag_worker), "--scan-only"],
                    timeout=60,
                    cwd=str(PROJ_ROOT),
                    env={**os.environ, "PYTHONPATH": str(PROJ_ROOT)},
                    stdout=open(LOGS_DIR / "antigravity.log", "a"),
                    stderr=subprocess.STDOUT,
                )
            finally:
                remove_pid("antigravity.pid")
        conn.close()
        release_lock(lock_fh)
        return

    log.info(f"Dispatching task {task['task_id']} (priority={task['priority'] if 'priority' in task else 'N/A'}, agent={task['agent']})")
    update_task_status(conn, task["task_id"], "IN_PROGRESS")

    # Dispatch to agent
    dispatch_success = dispatch_agent(task)
    if not dispatch_success:
        update_task_status(conn, task["task_id"], "FAILED", "Agent execution failed/timeout")
        # Check retry
        cur = conn.cursor()
        cur.execute("SELECT retry_count, max_retries FROM task_queue WHERE task_id = ?", (task["task_id"],))
        row = cur.fetchone()
        if row and row["retry_count"] < row["max_retries"]:
            cur.execute("""
                UPDATE task_queue
                SET status = 'PENDING', retry_count = retry_count + 1, updated_at = ?
                WHERE task_id = ?
            """, (now_iso(), task["task_id"]))
            conn.commit()
            log.info(f"Task {task['task_id']} requeued (retry {row['retry_count']+1}/{row['max_retries']})")
        else:
            log.error(f"Task {task['task_id']} exceeded max retries — staying FAILED")
        conn.close()
        release_lock(lock_fh)
        return

    # Run verification
    update_task_status(conn, task["task_id"], "VERIFYING")
    success, output = run_verification(task["verification_cmd"])
    if success:
        update_task_status(conn, task["task_id"], "DONE")
        log.info(f"Task {task['task_id']} VERIFIED and marked DONE ✓")
    else:
        update_task_status(conn, task["task_id"], "FAILED", output)
        cur = conn.cursor()
        cur.execute("SELECT retry_count, max_retries FROM task_queue WHERE task_id = ?", (task["task_id"],))
        row = cur.fetchone()
        if row and row["retry_count"] < row["max_retries"]:
            cur.execute("""
                UPDATE task_queue
                SET status = 'PENDING', retry_count = retry_count + 1, updated_at = ?
                WHERE task_id = ?
            """, (now_iso(), task["task_id"]))
            conn.commit()
            log.info(f"Task {task['task_id']} requeued for retry (attempt {row['retry_count']+1})")
        else:
            log.error(f"Task {task['task_id']} FAILED permanently after {row['max_retries'] if row else '?'} retries")

    conn.close()
    release_lock(lock_fh)
    log.info("Orchestrator cycle complete.")


if __name__ == "__main__":
    main()
