# Hermes Recovery Package — Polya AI

## Overview

This recovery package contains everything needed to restore a fully functional
Hermes Agent installation for the Polya Apologetica AI system on a fresh
Ubuntu VPS.

## Recovery Flow

```
CURRENT VPS (this machine)
        |
        v
GitHub Recovery Repository
  https://github.com/diedie1919/Polya-AI.git
        |
        v
Fresh Ubuntu VPS (26.04 LTS, x86_64)
        |
        v
[1] Install system dependencies (APT)
        |
        v
[2] Install uv, Node.js 22
        |
        v
[3] Install Hermes Agent from upstream
    git clone https://github.com/NousResearch/hermes-agent.git ~/.hermes/hermes-agent
    cd ~/.hermes/hermes-agent
    git checkout 9c4c548c
    git cherry-pick 63279301
        |
        v
[4] Apply local patches
    cd ~/.hermes/hermes-agent
    git apply recovery/PATCHES/agent_init_context_floor.patch
    git apply recovery/PATCHES/voice_mode_indonesian.patch
        |
        v
[5] Install Python dependencies (venv)
    python3.11 -m venv venv
    venv/bin/pip install -r recovery/PYTHON/requirements-hermes.txt
        |
        v
[6] Install Node dependencies
    cd ~/.hermes/hermes-agent
    npm install
        |
        v
[7] Restore configuration
    cp recovery/CONFIG/config.yaml.template ~/.hermes/config.yaml
    # Edit: fill in API keys, tokens
    cp recovery/CONFIG/SOUL.md ~/.hermes/SOUL.md
    cp recovery/CONFIG/memories/MEMORY.md ~/.hermes/memories/MEMORY.md
    cp recovery/CONFIG/memories/USER.md ~/.hermes/memories/USER.md
        |
        v
[8] Restore secrets
    # Manually set environment variables as documented in SECRETS/README.md
    # Create ~/.hermes/.env with actual secret values
        |
        v
[9] Restore Knowledge Base
    cp -r apologetica/ ~/apologetica/
        |
        v
[10] Restore state (optional)
    # See MANIFEST.md for state classification
    # Copy state.db, kanban.db, verification_evidence.db if needed
        |
        v
[11] Restore TTS model
    # See MODELS.md for download/restore procedure
    # ~5GB Chatterbox Indonesian model -> /home/ubuntu/tts-models/chatterbox-indonesian/
        |
        v
[12] Restore TTS script
    mkdir -p ~/.hermes/scripts/
    cp recovery/SCRIPTS/chatterbox_tts.py ~/.hermes/scripts/chatterbox_tts.py
        |
        v
[13] Install systemd service
    sudo cp recovery/CONFIG/systemd/hermes-gateway.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable hermes-gateway
    sudo systemctl start hermes-gateway
        |
        v
[14] Run verification
    bash recovery/SCRIPTS/verify-hermes.sh
        |
        v
HERMES READY
```

## Directory Structure

```
recovery/
├── README.md              <- You are here
├── MANIFEST.md            <- Complete file manifest and state classification
├── HERMES_VERSION.md      <- Version pins and commit history
├── DEPENDENCIES.md        <- Full dependency tree
├── MODELS.md              <- TTS model documentation
├── PATCHES/
│   ├── agent_init_context_floor.patch
│   └── voice_mode_indonesian.patch
├── CONFIG/
│   ├── config.yaml.template
│   ├── SOUL.md
│   ├── memories/
│   │   ├── MEMORY.md
│   │   └── USER.md
│   ├── systemd/
│   │   └── hermes-gateway.service
│   └── bashrc.template
├── SCRIPTS/
│   ├── bootstrap-vps.sh
│   ├── install-hermes.sh
│   ├── restore-hermes.sh
│   ├── verify-hermes.sh
│   └── chatterbox_tts.py
├── APT/
│   └── packages.txt
├── PYTHON/
│   └── requirements-hermes.txt
├── NODE/
│   └── package-lock-reference.md
└── SECRETS/
    └── README.md
```

## Important Warnings

- NEVER commit .env, auth.json, or any file containing actual secrets
- The TTS model (~5GB) is NOT in this repository — see MODELS.md
- state.db (~101MB) contains conversation history — handle with care
- The Apologetica KB is preserved separately in /home/ubuntu/apologetica/

## Recovery Gaps

1. **TTS Model**: 5GB binary — requires external backup (S3, encrypted tarball)
2. **state.db**: Contains private conversation data — excluded from Git by policy
3. **.env/auth.json**: Secrets must be re-entered manually
4. **Skills**: Custom skills in ~/.hermes/skills/ are documented but not fully exported
5. **Systemd service**: May not exist on current VPS (was not found) — template provided
