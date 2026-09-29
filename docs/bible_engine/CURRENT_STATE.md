# CURRENT STATE: REPOSITORY & INFRASTRUCTURE BASELINE
**Repository**: `/home/ubuntu/Polya-AI` (Git branch: `main`)  
**Companion Repositories**: `/home/ubuntu/Polya-Engine` (Expo/React Native)  
**Contract Baseline**: v2.0 Architecture Frozen  
**Audit Date**: 2026-09-30  

---

## 1. Git & Version Control Baseline
- **Active Git Repository**: `/home/ubuntu/Polya-AI`
  - Current Commit: `d01a3b3` (`feat(orchestrator): backup VPS LangGraph orchestrator system...`)
  - Branch: `main` (synchronized with `origin/main`)
  - Status: Clean working tree
- **Skills Directory**:
  - `/home/ubuntu/skills/domain/polya-linguistic-exegesis/SKILL.md` (Version 2.0.0 Master Skill)
  - `/home/ubuntu/.agents/skills/polya-linguistic-exegesis` (Live symlink verified)
  - `/home/ubuntu/skills/registry/skills.yaml` (Skill registered and active)
  - Workspace Rules: `/home/ubuntu/AGENTS.md` and `/home/ubuntu/GEMINI.md` enforcing canonical trigger `aktifkan eksegesa` and 20-section response template.

---

## 2. Live Runtime & Daemons State
1. **Hermes Gateway & Agent Framework**:
   - Version: Hermes Agent v0.21.3
   - Service: Active under user systemd (PID 595437)
   - MCP Server: Active on PID 718705 (`hermes mcp serve --accept-hooks`)
   - Plugins: A2A, Home Assistant, Mattermost, Photon, WeCom, WhatsApp configured.
2. **Codex Local Daemon**:
   - Version: `codex-cli 0.157.1`
   - Active Daemons: PID 470005 (`codex app-server daemon pid-update-loop`), PID 698024 (`codex app-server --listen unix://`)
   - Capabilities: `codex exec`, `codex review`, `codex app-server`
3. **Claude Code**:
   - Version: `claude 2.1.283`
   - Execution Model: Non-interactive batch execution via `claude -p`
4. **Polya MCP & FTS5 Server**:
   - Active on PID 595450, 718707, 718741 (`/home/ubuntu/.polya/polya_mcp_server.py`)
   - Database: `/home/ubuntu/.polya/polya_index.db` (SQLite 3.46.1)
   - Exposes tools: `mcp_search_corpus`, `mcp_get_transcript`, `mcp_search_exegesis`, `mcp_queue_status`.

---

## 3. Data & Corpora State
- **Primary Database**: `/home/ubuntu/.polya/polya_index.db`
  - Size: ~34 MB
  - Tables: `knowledge_fts`, `youtube_catalog_fts`, `task_queue`, `arena_chat_messages`, `arena_users`.
- **Existing Linguistic Assets**:
  - `skills/domain/eksegesa-kata/`: Semitic & Hellenistic lexicon authorities (BDB, HALOT, BDAG, Thayer, LSJ) and methodology (*Ilzam al-Khasm*).
  - `skills/domain/polya-linguistic-exegesis/`: Source-Language-First 20-section exegesis specification.

---

## 4. Test Framework Baseline
- Pytest runtime available via `/home/ubuntu/venv/bin/pytest` and system Python.
- Existing tests in `Polya-AI/runtime/`:
  - `test_commentary_engine.py`
  - `test_fact_check_evidence.py`
  - `test_full_integration_e2e.py`
  - `test_persona_zuma_engine.py`
- Test framework for Biblical Philological Engine is currently unpopulated and scheduled for Phase 1–8.
