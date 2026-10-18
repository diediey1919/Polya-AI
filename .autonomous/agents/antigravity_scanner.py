#!/usr/bin/env python3
"""
Antigravity Self-Healing Scanner
---------------------------------
Scans web assets for forbidden hardcoded strings and test failures.
If violations found, reopens assigned agent tasks in task_queue.db.

Usage:
  python antigravity_scanner.py --scan-only   # scan only, reopen tasks on violation
  python antigravity_scanner.py --verbose     # print all findings
"""
import os
import sys
import ast
import re
import json
import sqlite3
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timezone

PROJ_ROOT = Path("/home/ubuntu/Polya-AI")
AUTO_DIR = PROJ_ROOT / ".autonomous"
DB_PATH = AUTO_DIR / "task_queue.db"
LOGS_DIR = AUTO_DIR / "logs"
SCAN_LOG = LOGS_DIR / "antigravity.log"

# ─── Forbidden strings and their responsible tasks ──────────────────────────
# Maps forbidden_string → list of (task_id, agent, files_to_scan)
FORBIDDEN_MAP = {
    "Website Integration Audit Report": {
        "task_id": "T001", "agent": "claude",
        "files": ["web/static/index.html"],
        "note": "Hardcoded audit report block in DOM",
    },
    "Order ID: POLYA-LOAD": {
        "task_id": "T004", "agent": "codex",
        "files": ["web/static/index.html"],
        "note": "Static Midtrans order ID",
    },
    "Analisis Terpakai: 16 / 5": {
        "task_id": "T004", "agent": "codex",
        "files": ["web/static/index.html"],
        "note": "Static quota mismatch text",
    },
    "LIVE TELEMETRY STREAM: 22ms": {
        "task_id": "T003", "agent": "codex",
        "files": ["web/static/index.html"],
        "note": "Static telemetry value",
    },
    "EU AI Act Article 14": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Static AI regulation motion (should be apologetika)",
    },
    "Regulasi Forensik Kecerdasan Buatan": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Static AI regulation motion in Indonesian",
    },
    "// Mock filter": {
        "task_id": "T001", "agent": "claude",
        "files": ["web/static/index.html", "web/static/arena.html", "web/api_foundation.py"],
        "note": "Mock filter placeholder in code",
    },
    "Graph Nodes: 0 | Edges: 0": {
        "task_id": "T006", "agent": "hermes",
        "files": ["web/static/index.html"],
        "note": "Static knowledge graph counts",
    },
    "Codex Sinaiticus (01)": {
        "task_id": "T006", "agent": "hermes",
        "files": ["web/static/index.html"],
        "note": "Static manuscript label in source-drawer",
    },
}

# Strings that are context-dependent (only flagged in specific DOM context)
CONTEXTUAL_FORBIDDEN = {
    "OFFICIAL ADJUDICATION VERDICT": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Verdict panel visible during SETUP phase",
    },
    "68.91 VS 51.00": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Static score visible during SETUP phase",
    },
    "DEBATE QUALITY INDEX": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Quality index visible during SETUP phase",
    },
    "8.98 / 10": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Static quality score during SETUP",
    },
    "ZUMA_DEBATE_CORPUS_EP01": {
        "task_id": "T005", "agent": "polya",
        "files": ["web/static/arena.html"],
        "note": "Static corpus reference during SETUP",
    },
    "Mengambil katalog tema dari server": {
        "task_id": "T008", "agent": "gemini",
        "files": ["web/static/index.html"],
        "note": "Loading placeholder instead of dynamic theme list",
    },
    "Friksi Paulus vs Petrus": {
        "task_id": "T008", "agent": "gemini",
        "files": ["web/static/index.html"],
        "note": "Static theme card",
    },
}

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s UTC] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(SCAN_LOG), mode="a"),
    ],
)
log = logging.getLogger("antigravity")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def check_python_file(filepath, forbidden_strings):
    """AST-aware scan of Python file. Checks string literals AND comments."""
    findings = []
    source = None
    try:
        with open(filepath, "r", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=str(filepath))

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for fs in forbidden_strings:
                    if fs in node.value:
                        findings.append({
                            "file": str(filepath),
                            "line": node.lineno,
                            "string": fs,
                            "context": "Python string literal (AST)",
                        })
    except FileNotFoundError:
        pass
    except SyntaxError:
        pass  # fallback: text scan below

    # Also text-scan to catch string constants (AST may miss multi-line)
    if source is not None:
        for i, line in enumerate(source.split("\n"), 1):
            for fs in forbidden_strings:
                if fs in line:
                    existing = any(f["line"] == i and f["string"] == fs for f in findings)
                    if not existing:
                        findings.append({
                            "file": str(filepath),
                            "line": i,
                            "string": fs,
                            "context": "Text match",
                        })
    return findings


def check_html_file(filepath, forbidden_strings):
    """DOM-aware scan of HTML file — strips HTML tags for text content check."""
    findings = []
    try:
        with open(filepath, "r", errors="replace") as f:
            source = f.read()
        # Text-only content (strip tags)
        text_only = re.sub(r'<[^>]+>', '', source)
        for fs in forbidden_strings:
            if fs in text_only:
                # Find line number
                for i, line in enumerate(source.split("\n"), 1):
                    if fs in line:
                        findings.append({
                            "file": str(filepath),
                            "line": i,
                            "string": fs,
                            "context": "HTML text content",
                        })
                        break
                if not any(f["string"] == fs for f in findings):
                    findings.append({
                        "file": str(filepath),
                        "line": 0,
                        "string": fs,
                        "context": "HTML text content (no line found)",
                    })
    except FileNotFoundError:
        pass
    return findings


def scan_all_files():
    """Scan all target files for forbidden strings."""
    all_findings = []
    all_forbidden = {}
    all_forbidden.update(FORBIDDEN_MAP)
    all_forbidden.update(CONTEXTUAL_FORBIDDEN)

    for forbidden, info in all_forbidden.items():
        for filepath in info["files"]:
            full_path = PROJ_ROOT / filepath
            if not full_path.exists():
                continue
            if filepath.endswith(".py"):
                file_findings = check_python_file(full_path, [forbidden])
            else:
                file_findings = check_html_file(full_path, [forbidden])
            all_findings.extend(file_findings)

    return all_findings


def run_tests():
    """Run pytest suite, return (success, output)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-x", "-q", "--tb=line"],
            capture_output=True, text=True, timeout=120,
            cwd=str(PROJ_ROOT),
            env={**os.environ, "PYTHONPATH": str(PROJ_ROOT)},
        )
        output = (result.stdout + "\n" + result.stderr).strip()[-1000:]
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "TEST SUITE TIMEOUT"
    except Exception as e:
        return False, f"TEST ERROR: {e}"


def reopen_tasks(conn, findings, test_failures):
    """Reopen tasks that are DONE/FAILED but still have violations."""
    reopened = []
    tasks_to_reopen = set()

    for f in findings:
        info = all_forbidden_lookup.get(f["string"])
        if info:
            tasks_to_reopen.add(info["task_id"])

    if test_failures:
        # Reopen the task associated with test failures — typically T001, T002, etc.
        # Use a broad set of test-related tasks
        cur = conn.cursor()
        cur.execute("SELECT task_id FROM task_queue WHERE status IN ('DONE','FAILED') AND assigned_agent IN ('claude','hermes')")
        for row in cur.fetchall():
            tasks_to_reopen.add(row[0])

    for task_id in tasks_to_reopen:
        cur = conn.cursor()
        cur.execute("SELECT status, retry_count FROM task_queue WHERE task_id = ?", (task_id,))
        row = cur.fetch_row if hasattr(cur, 'fetch_row') else cur.fetchone()
        row = cur.fetchone()
        if row and row[0] in ('DONE', 'FAILED'):
            error_detail = []
            for f in findings:
                info = all_forbidden_lookup.get(f["string"])
                if info and info["task_id"] == task_id:
                    error_detail.append(f"{f['file']}:{f['line']} contains '{f['string']}'")
            if test_failures:
                error_detail.append(f"Test suite failure: {test_failures[:300]}")

            cur.execute("""
                UPDATE task_queue
                SET status = 'PENDING',
                    retry_count = retry_count + 1,
                    last_error = ?,
                    updated_at = ?
                WHERE task_id = ?
            """, ("; ".join(error_detail), now_iso(), task_id))
            conn.commit()
            reopened.append(task_id)
            log.warning(f"SELF-HEALING: Reopened task {task_id} (retry_count +1)")

    return reopened


# Global lookup (built from both maps)
all_forbidden_lookup = {}
all_forbidden_lookup.update(FORBIDDEN_MAP)
all_forbidden_lookup.update(CONTEXTUAL_FORBIDDEN)


def main():
    scan_only = "--scan-only" in sys.argv
    verbose = "--verbose" in sys.argv

    log.info(f"Antigravity scan started at {now_iso()}")

    # 1. Scan for forbidden strings
    findings = scan_all_files()
    log.info(f"Forbidden string scan: {len(findings)} violations found")

    if verbose:
        for f in findings:
            log.info(f"  VIOLATION: {f['file']}:{f['line']} — '{f['string']}' ({f['context']})")

    # 2. Run test suite
    test_success, test_output = run_tests()
    log.info(f"Test suite: {'PASS' if test_success else 'FAIL'}")
    if not test_success:
        log.error(f"Test output: {test_output[:500]}")

    # 3. If violations or test failures → reopen tasks
    if findings or not test_success:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        reopened = reopen_tasks(conn, findings, test_output if not test_success else None)
        conn.close()
        log.warning(f"Self-healing: Reopened {len(reopened)} tasks: {reopened}")

        # Write summary to cron_master.log
        with open(LOGS_DIR / "cron_master.log", "a") as cf:
            cf.write(f"\n[{now_iso()}] ANTIGRAVITY: {len(findings)} violations, tests {'FAIL' if not test_success else 'PASS'}, {len(reopened)} tasks reopened\n")
            for f in findings:
                cf.write(f"  - {f['file']}:{f['line']} '{f['string']}'\n")

        sys.exit(1)  # nonzero exit signals cron_master
    else:
        log.info("Antigravity scan: ALL CLEAR — no violations, all tests pass")
        with open(LOGS_DIR / "cron_master.log", "a") as cf:
            cf.write(f"\n[{now_iso()}] ANTIGRAVITY: CLEAN — 0 violations, tests PASS\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())