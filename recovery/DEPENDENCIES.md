# Dependencies

## System Information

- OS: Ubuntu 26.04.1 LTS (Resolute Raccoon)
- Architecture: x86_64
- Kernel: 7.0.0-1011-aws

## Python

- **System Python**: 3.14.4 (Ubuntu 26.04 default)
- **Hermes venv Python**: 3.11.16
- **Requirement**: Python 3.11.x for Hermes venv
- Install via deadsnakes PPA or pyenv if not available

## Node.js

- **Version**: v22.23.2
- **npm**: 10.9.8
- **Requirement**: Node.js 22.x LTS
- Install via NodeSource or nvm

## uv (Python package manager)

- **Version**: 0.12.9
- **Location**: ~/.hermes/bin/uv
- Installed by Hermes installer

## tirith

- **Location**: ~/.hermes/bin/tirith
- Installed by Hermes installer

## ffmpeg

- **Version**: 8.0.1-3ubuntu2
- **Location**: /usr/bin/ffmpeg
- **Package**: ffmpeg (APT)
- Required for TTS audio conversion (WAV -> MP3)

## browser-use

- Installed as part of Hermes npm dependencies
- Backend: browser-use (configured in config.yaml)

## cua-driver

- Installed via installer script
- PATH entry: /home/ubuntu/.local/bin
- Backend: cua (configured in config.yaml)

## Chatterbox TTS Requirements

Python packages (in venv):
- chatterbox_tts==0.1.7
- torch==2.6.0
- torchaudio==2.6.0
- safetensors==0.5.3

System requirements:
- ffmpeg (for WAV->MP3 conversion)
- ~8GB RAM recommended (CPU-only inference)
- No GPU required (works on CPU, ~3min/sentence)

## Critical APT Packages

These are the non-standard packages Hermes depends on:

```
build-essential        # C compiler for native extensions
cmake                  # Build system
curl                   # HTTP client
ffmpeg                 # Audio/video processing
git                    # Version control
jq                     # JSON processor
nodejs                 # Node.js runtime
python3                # System Python
python3-dev            # Python headers
ripgrep                # Fast search
tmux                   # Terminal multiplexer
tree                   # Directory listing
unzip                  # Archive extraction
wget                   # HTTP download
zip                    # Archive creation
```

Full APT package list: see APT/packages.txt

## Python Packages

Full pip freeze output: see PYTHON/requirements-hermes.txt

Key packages:
- hermes_agent==0.21.0
- openai==2.24.0
- discord_py==2.7.1
- chatterbox_tts==0.1.7
- torch==2.6.0
- faster_whisper==1.2.1
- groq==1.7.0
- dashscope==1.27.4
- edge_tts==7.2.7
- mcp==2.0.0
- browser-use (via npm)

## Node Packages

Hermes uses npm workspaces. See NODE/package-lock-reference.md.
Root package.json is at ~/.hermes/hermes-agent/package.json.
