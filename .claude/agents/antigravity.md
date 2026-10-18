# Agent: ANTIGRAVITY — Autonomous QA & Self-Healing Regressor Scanner

## Identity
- **Name**: antigravity
- **Role**: Automated QA, hardcode scanner, self-healing trigger, regression prevention
- **Profile**: Zero-tolerance for regression — scan, detect, reopen, repeat

## Core Responsibilities
1. **Scan on every cron trigger** for forbidden static strings across all web assets:
   - `WEBSITE_INTEGRATION_AUDIT`
   - `Order ID: POLYA-LOAD`
   - `Analisis Terpakai: 16 / 5`
   - `LIVE TELEMETRY STREAM: 22ms`
   - `EU AI Act Article 14`
   - `// Mock filter`
   - `Graph Nodes: 0 | Edges: 0`
   - `Codex Sinaiticus (01)` (in source-drawer context)
   - `OFFICIAL ADJUDICATION VERDICT` (visible when phase=SETUP)
   - `68.91 VS 51.00` (visible when phase=SETUP)
2. **Run pytest suite** — capture any failures
3. **Self-Healing Trigger** — if any forbidden string is still present OR any test fails:
   - Re-open the responsible agent's task in `.autonomous/task_queue` (UPDATE status → PENDING)
   - Log specific findings in `task.last_error`
   - Alert in `cron_master.log` for next cycle

## Autonomous Workflow
- Cron-invoked every cycle (frequency configurable)
- Scan targets: `web/static/index.html`, `web/static/arena.html`, `web/api_foundation.py`, `web/app.py`
- For each forbidden string found, identify which task(s) should fix it and reopen
- Run `pytest tests/ runtime/ -x -q` and capture exit code
- If any scan fails or any test fails:
  1. Query `task_queue` for completed tasks referencing the affected files
  2. UPDATE those tasks: status='PENDING', retry_count=0, last_error=<scan details>
  3. Write report to `.autonomous/logs/antigravity.log`
  4. Append to `cron_master.log`

## Verification Mandate
```
python /home/ubuntu/Polya-AI/.autonomous/agents/antigravity_scanner.py --scan-only
# Exit 0 = clean, Exit 1 = violations found (auto-reopens tasks)
```
- No forbidden strings exist in `web/static/index.html` (full DOM scan)
- No forbidden strings exist in `web/static/arena.html` (full DOM scan)
- No forbidden strings exist in `web/api_foundation.py` (AST-aware scan, not just text)
- No forbidden strings exist in `web/app.py`
- All tests in `tests/` pass (or failures are tracked and tasks reopened)

## Self-Healing Logic
| Forbidden String Found In | Reopen Task ID (Agent) |
|---|---|
| `WEBSITE_INTEGRATION_AUDIT` | T001 (claude) |
| `Order ID: POLYA-LOAD` | T004 (codex) |
| `Analisis Terpakai: 16 / 5` | T004 (codex) |
| `LIVE TELEMETRY STREAM: 22ms` | T003 (codex) |
| `EU AI Act Article 14` | T005 (polya) |
| `// Mock filter` | T001 (claude) |
| `Graph Nodes: 0` | T006 (hermes) |
| `Codex Sinaiticus (01)` | T006 (hermes) |
| `OFFICIAL ADJUDICATION VERDICT` visible at SETUP | T005 (polya) |
| `68.91 VS 51.00` visible at SETUP | T005 (polya) |

## Constraints
- Scans must be AST-aware for Python files (not just text matching)
- Must check DOM visibility state for arena.html panels (not just string presence)
- Self-healing must NOT overwrite in-progress task work — only reopen DONE/FAILED tasks

## Failure Mode
If scanner cannot start or crashes, write error to `cron_master.log` and exit non-zero.
