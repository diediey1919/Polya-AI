# ARCHITECTURE AUDIT: POLYA PHILOLOGICAL BIBLE ENGINE
**Environment**: AWS Ubuntu Linux x86_64 (`ip-172-31-16-239`, Kernel 7.0.0-1011-aws)  
**Contract Version**: Architecture v2.0 — FROZEN  
**Date**: 2026-09-30  
**Lead Architect & Auditor**: AGY (Antigravity CLI Agent)

---

## 1. System & Host Environment Overview
- **User & Path**: `ubuntu` (`/home/ubuntu`), Python 3.14.4 (system) and Python 3.11.16 (`/home/ubuntu/venv` and `/home/ubuntu/.hermes/hermes-agent/venv`).
- **Core CLI Binaries Verified**:
  - `agy`: `/home/ubuntu/.local/bin/agy` (Lead Architect, Implementation Agent)
  - `hermes`: `/home/ubuntu/.local/bin/hermes` v0.21.3 (Orchestration Layer & Gateway)
  - `codex`: `/home/ubuntu/.npm-global/bin/codex` v0.157.1 (Independent Engineering Worker)
  - `claude`: `/home/ubuntu/.npm-global/bin/claude` v2.1.283 (Independent Review Worker)
  - `git`: `/usr/bin/git` v2.43.0
  - `docker`: `/usr/bin/docker` (daemon active)
  - `sqlite3`: `/usr/bin/sqlite3` v3.46.1

---

## 2. Multi-Agent Ecosystem Discovery & Live Status

| Agent | Discovery Path / Binary | Live Process / Service Status | API / CLI Integration Mode | Identified Scope / Role |
| :--- | :--- | :--- | :--- | :--- |
| **AGY** | `/home/ubuntu/.local/bin/agy` | Running as current session | Native CLI & MCP interface | Lead Architect, Implementer, Integrator |
| **Hermes** | `/home/ubuntu/.local/bin/hermes` | Systemd user gateway PID 595437; MCP server PID 718705 | CLI (`hermes`), MCP (`hermes`), REST Gateway | Task orchestration, retry, workgraph |
| **Codex** | `/home/ubuntu/.npm-global/bin/codex` | App-server daemon PID 470005, 698024 | Non-interactive CLI (`codex exec`, `codex review`), IPC | Engineering, debugging, refactoring, tests |
| **Claude Code** | `/home/ubuntu/.npm-global/bin/claude` | Available on PATH | Non-interactive CLI (`claude -p`), JSON agent defs | Independent review, critique, safety audit |

---

## 3. Repositories & Knowledge Bases

### 3.1 Repository Topography
1. **`/home/ubuntu/Polya-AI`** (`main`, commit `d01a3b3`):
   - Contains Python runtime, LangGraph orchestrator (`orchestrator/`), SQLite knowledge base (`.polya/polya_index.db`), MCP server (`polya_mcp_server.py`), and test suites.
   - **Primary target repository** for the Polya Philological Bible Engine backend and knowledge schemas.
2. **`/home/ubuntu/Polya-Engine`** (`experiment/google-credential`, commit `ca08794`):
   - React Native / Expo mobile application codebase (frontend UI / arena display).
3. **`/home/ubuntu/.polya/polya_index.db`**:
   - Live SQLite3 knowledge base containing FTS5 tables (`knowledge_fts`, `youtube_catalog_fts`, `task_queue`, `arena_users`, etc.).
   - Contains initial catalog and schema foundations.

---

## 4. Architectural Gaps vs Contract v2.0

1. **Source Immutability & Token Registry**:
   - Current schema lacks an explicit Level 0 / Level 1 canonical text store with SHA-256 cryptographic provenance for Greek (NA28/Byzantine/MSS), Hebrew (MT/LXX/DSS), and Aramaic.
2. **Pericope & Boundary Registry**:
   - Exegesis currently operates ad-hoc via prompts rather than an indexed relational Pericope Registry (start token, end token, boundary confidence).
3. **Evidence Ledger & Epistemic Typing**:
   - Lack of a dedicated SQLite/PostgreSQL schema for tracking `[E1]`–`[E11]` evidence classes, conflicting hypotheses, and formal verification gates (V1–V10).
4. **Deterministic Multi-Agent Delegation Harness**:
   - Existing LangGraph orchestrator in `Polya-AI/orchestrator` has runners for mobile/debate, but lacks dedicated Philological Orchestra roles (Textual Critic, Morphology Analyst, Syntax Analyst, Exegete, Validator).

---

## 5. Architectural Verdict
The host VPS environment possesses all required tools, runtimes, daemons, and database engines to support the **Architecture v2.0 — FROZEN** implementation contract without inventing any missing components.
