# Recovery Manifest

Complete inventory of all files and data relevant to Hermes recovery.

## Files Included in This Package

| Path | Size | Description |
|------|------|-------------|
| PATCHES/agent_init_context_floor.patch | 13 lines | Context length floor bypass for Qwen |
| PATCHES/voice_mode_indonesian.patch | 32 lines | Indonesian Whisper hallucination filter |
| CONFIG/config.yaml.template | ~5KB | Sanitized Hermes config (no secrets) |
| CONFIG/SOUL.md | 667B | System prompt / personality |
| CONFIG/memories/MEMORY.md | 1.7KB | Agent persistent memory |
| CONFIG/memories/USER.md | 787B | User profile memory |
| CONFIG/systemd/hermes-gateway.service | ~400B | Systemd unit (template) |
| CONFIG/bashrc.template | ~600B | Shell configuration additions |
| SCRIPTS/bootstrap-vps.sh | — | Fresh VPS setup script |
| SCRIPTS/install-hermes.sh | — | Hermes installation script |
| SCRIPTS/restore-hermes.sh | — | Full restore orchestrator |
| SCRIPTS/verify-hermes.sh | — | Post-install verification |
| SCRIPTS/chatterbox_tts.py | ~2KB | Chatterbox TTS custom provider |
| APT/packages.txt | — | APT package list |
| PYTHON/requirements-hermes.txt | — | Python pip freeze output |
| NODE/package-lock-reference.md | — | Node.js dependency reference |
| SECRETS/README.md | — | Secret inventory (no values) |
| MODELS.md | — | TTS model documentation |
| HERMES_VERSION.md | — | Version and commit pins |
| DEPENDENCIES.md | — | Full dependency documentation |

## Files EXCLUDED (Never Commit)

| Path | Reason |
|------|--------|
| ~/.hermes/.env | Contains API keys and tokens |
| ~/.hermes/auth.json | Contains authentication credentials |
| ~/.hermes/state.db | 101MB — conversation history (private data) |
| ~/.hermes/state.db-wal | WAL journal |
| ~/.hermes/state.db-shm | Shared memory journal |
| venv/ | Python virtual environment (rebuild) |
| node_modules/ | Node dependencies (rebuild) |
| ~/.cache/ | UV/pip/npm caches |
| /home/ubuntu/tts-models/ | 5GB binary model files |
| *.pem, *.key, *.token | Cryptographic material |

## State Data Classification

### CRITICAL STATE (restore for full functionality)

| Path | Size | Description |
|------|------|-------------|
| ~/.hermes/state.db | 101MB | Main state database (sessions, conversations, tool outputs) |
| /home/ubuntu/apologetica/ | ~4MB | Apologetica Knowledge Base (108+2+3 = 113 files) |

### IMPORTANT STATE (restore for convenience)

| Path | Size | Description |
|------|------|-------------|
| ~/.hermes/skills/ | 4.6MB | Custom and curated skills (22 categories) |
| ~/.hermes/kanban.db | 116KB | Kanban board state |
| ~/.hermes/verification_evidence.db | 32KB | Forensic audit evidence cache |
| ~/.hermes/channel_directory.json | 9KB | Discord channel mapping |
| ~/.hermes/context_length_cache.yaml | 586B | Model context cache |

### OPTIONAL STATE (can be rebuilt)

| Path | Size | Description |
|------|------|-------------|
| ~/.hermes/pastes/ | 1.5MB | ~165 paste files (ephemeral tool outputs) |
| ~/.hermes/cache/ | varies | Browser, web search, extraction caches |
| ~/.hermes/audio_cache/ | varies | TTS audio cache |
| ~/.hermes/cron/ | varies | Scheduled job definitions |
| ~/.hermes/gateway/ | varies | Gateway runtime state |

## Apologetica KB Status (STEP 100)

- Sources: 25 (verified: 108 source files in knowledge/)
- Claims: 17 (verified: 2 claim files)
- Analyses: 65 (verified: 3 analysis files)
- Conflicts: 0
- Orphans: 0
- Duplicates: 0
- Last STEP: 100 (Pre-Nicene Fathers Trinitarian Development)

Note: File counts from find differ from KB metadata counts because
the KB tracks logical entities, not filesystem files. The metadata
counts (25/17/65/0) are authoritative.
