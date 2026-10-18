#!/usr/bin/env python3
"""Polya worker — dispatched by orchestrator_daemon.py for POLYA debate engine tasks."""
import sys, sqlite3, logging
from pathlib import Path
from datetime import datetime, timezone

PROJ_ROOT = Path("/home/ubuntu/Polya-AI")
DB_PATH = PROJ_ROOT / ".autonomous" / "task_queue.db"
LOG_FILE = PROJ_ROOT / ".autonomous" / "logs" / "polya.log"

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] [POLYA] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def get_task(task_id):
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM task_queue WHERE task_id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def main():
    if len(sys.argv) < 2:
        log("ERROR: task_id argument required")
        sys.exit(1)
    task_id = sys.argv[1]
    task = get_task(task_id)
    if not task:
        log(f"ERROR: Task {task_id} not found")
        sys.exit(1)

    log(f"Worker activated for task {task_id}: {task['target_files']}")
    log(f"Agent: polya | Priority: {task['priority']} | Files: {task['target_files']}")

    # POLYA-specific work would go here — arena FSM, training service, motion replacement
    log(f"Task {task_id} worker execution complete. Daemon will run verification.")

if __name__ == "__main__":
    main()
