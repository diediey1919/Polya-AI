# System Discovery Baseline
## Polia Apologetica AI & Hermes Runtime Architecture

**Audit Date:** 2026-09-11
**Auditor:** Antigravity (Advanced Agentic Coding)
**Status:** FACTUAL BASELINE ESTABLISHED

---

### 1. Environment Baseline
- **Host OS:** Linux ip-172-31-16-239 (Ubuntu 26.04 LTS, kernel 7.0.0-1011-aws, x86_64)
- **User:** `ubuntu` (uid=1000, gid=1000)
- **Current Working Directory:** `/home/ubuntu`
- **Git Repositories:**
  - `/home/ubuntu/Polya-AI`: Clean working tree at commit `ccd0cf9` (`origin/main`), remote `git@github.com:diediey1919/Polya-AI.git`.
  - `/home/ubuntu/.hermes/hermes-agent`: Upstream Nous Research hermes-agent git repo at commit `63279301` (`main`).
  - `/home/ubuntu/apologetica`: Canonical working knowledge store (unversioned folder, separate from Git repo).
- **Runtimes:**
  - Python 3.11 (`/home/ubuntu/.hermes/hermes-agent/venv/bin/python`, `/usr/bin/python3`)
  - Node.js 22 (`/home/ubuntu/.npm-global/bin/`)
  - Package Managers: `apt`, `uv`, `pip`, `npm`

### 2. Services & Daemons
- **`hermes-gateway.service`:** Active (running since 2026-09-10 11:13:16 WIB), user systemd unit.
  - Subprocesses: Hermes agent gateway, `/home/ubuntu/.npm-global/bin/claude mcp serve`, TTS/voice handler.
- **MCP Servers Registered:**
  - Antigravity (`~/.gemini/config/mcp_config.json`): `hermes` (`hermes mcp serve --accept-hooks`) and `hermes-tools` (`hermes-tools-mcp`).
  - Hermes (`~/.hermes/config.yaml`): `claude_code` (`/home/ubuntu/.npm-global/bin/claude mcp serve`).
  - Claude Code (`~/.claude.json`): `hermes-tools` (`hermes-tools-mcp`).

### 3. Identity and Separation
- **Polia / Polya Role:** Chief Apologetics Agent (Muslim Apologetics AI) with strict evidence-based reasoning covering Islam, Christianity, and Judaism.
- **Hermes Role:** Autonomous agent platform, execution harness, and messaging gateway.
- **Independence:** The Apologetica KB (`/home/ubuntu/apologetica/`) is architecturally independent from the Hermes execution engine. Hermes interacts with it as a file-backed knowledge asset.
