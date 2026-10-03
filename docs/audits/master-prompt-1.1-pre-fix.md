# MASTER PROMPT #1.1 — PRE-FIX FORENSIC AUDIT SNAPSHOT

**Audit Date**: 2026-10-04T03:50:00+07:00  
**Lead Investigator**: Anti-Gravity (AGY) — Engineering Supervisor & Runtime Lead  
**Target Repository**: `/home/ubuntu/Polya-AI`  

---

## 1. GIT STATE & BRANCH FORENSICS

- **Current Working Branch**: `main`
- **Current HEAD**: `d864abd45a8d87e40d1fa8239fd381c4a7fc7c0d` (`test(bible-engine): isolate regression baseline from production db`)
- **Remote Configuration**: `origin git@github.com:diediey1919/Polya-AI.git` (HEAD is 41 commits ahead of `origin/main`)
- **Branch Containing MP1 Implementation**: `feat/polya-apologetika-web-foundation`
- **MP1 Branch HEAD**: `c9249872c3b4b5a1ea2e1f8147b1abd9c79c6d04` (`docs(audit): add empirical architecture and runtime verification report for MP1`)
- **Common Merge Base**: `3c5515ccd9bcc856ca339a0c990b22fbbd82f253` (`fix(bible-engine): harden api and database concurrency`)

### Changed Files Between `main` and `feat/polya-apologetika-web-foundation`:
```text
docs/audits/master-prompt-1-verification.md |  115 +
web/api_foundation.py                       |  214 +
web/app.py                                  |   26 +
web/models.py                               |  101 +
web/services.py                             |  448 ++
web/static/index.html                       | 6494 ++++++---------------------
web/static/index.html.arena-backup          | 5332 ++++++++++++++++++++++
7 files changed, 7620 insertions(+), 5110 deletions(-)
```

---

## 2. ARCHITECTURAL DIVERGENCE (SOURCE OF TRUTH)

- **`main` Working Tree**:
  - `web/app.py`: Legacy monolithic TikTok Arena backend (83 KB, PID 1065078). Lacks MP1 endpoints (`/api/v1/calculator/analyze`, `/api/v1/payment/*`, `/api/v1/account/billing`).
  - `web/static/index.html`: Legacy TikTok Arena UI.
  - Lacks `web/api_foundation.py`, `web/models.py`, `web/services.py`.
- **`feat/polya-apologetika-web-foundation`**:
  - Contains modular Apologetics Workspace SPA (`web/static/index.html`, 6494 lines) implementing Onboarding, 17 Locales, Perspective selection, Calculator, Case File, Premium Gate (Rp99.000), Midtrans simulation, Knowledge/Theme/Evidence/Provenance tabs, and ZUMA Persona UI.
  - Contains modular backend services (`web/services.py`, `web/models.py`, `web/api_foundation.py`, `web/app.py`).

---

## 3. DATABASE STATE FORENSICS

- **File**: `/home/ubuntu/Polya-AI/data/polya_arena.db`
- **File Size**: `0 bytes` (untracked, empty)
- **Tables Present**: `0`
- **Runtime Failure**: Inbound HTTP requests hitting backend services trigger:
  `sqlite3.OperationalError: no such table: user_entitlements`
- **Root Cause**: Database initialization (`init_foundation_db()` in `web/services.py`) is not wired into the FastAPI lifespan or application startup routine. Fresh or empty database files are not initialized automatically.

---

## 4. RUNNING PROCESS & SYSTEMD SERVICE

- **Systemd Unit**: `polya-web.service`
  - Location: `/etc/systemd/system/polya-web.service`
  - Working Directory: `/home/ubuntu/Polya-AI/web`
  - ExecStart: `/home/ubuntu/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"`
  - Active Status: `active (running)`, PID 1065078
  - Disconnect: The daemon was started when feature files were temporarily on disk, but on-disk files on `main` do not match memory state, and static files served from disk revert to legacy arena.

---

## 5. LANGGRAPH ORCHESTRATOR GRAPH FORENSICS

- **File**: `/home/ubuntu/Polya-AI/orchestrator/graph.py`
- **Architecture**: `StateGraph(AgentState)` with dynamic conditional routing across 4 nodes (`hermes`, `codex`, `cloud_code`, `anti_gravity`).
- **Checkpointer Status**: `workflow.compile()` is invoked without `checkpointer`.
- **Impact**: State serialization across interruptions and resumes (`thread_id`) is not active in production graph.

---

## 6. MULTI-AGENT RUNNER STATUS & RUNTIME AUDIT

- **Runner Files**:
  - `orchestrator/agents/hermes/runner.py`: Deterministic route plan generator.
  - `orchestrator/agents/codex/runner.py`: Static dictionary rule-based checker for Android.
  - `orchestrator/agents/cloud_code/runner.py`: Local SQLite table counter & mock theological framework dictionary.
  - `orchestrator/agents/anti_gravity/runner.py`: Local `docker --version` subprocess checker.
- **Available Live Agent Runtimes on Host**:
  - **Hermes**: `/home/ubuntu/.local/bin/hermes` exists. Systemd user service `hermes-gateway.service` active. Hermes gateway daemon running on PID 595437 (`python -m hermes_cli.main gateway run`).
  - **Codex**: `/home/ubuntu/.npm-global/bin/codex` exists. Codex daemon active on PID 470005 & PID 907122 (`codex app-server --listen unix:// --managed-daemon`).
  - **Claude Code**: `/home/ubuntu/.npm-global/bin/claude` exists.
  - **Anti-Gravity (AGY)**: `/home/ubuntu/.local/bin/agy` exists. Running PID 969403, 1067626, 1068152.
- **Deficiency**: LangGraph nodes currently bypass these live runtimes and return static mock reports.
