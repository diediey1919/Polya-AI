#!/bin/bash
# restore-hermes.sh - Restore Hermes configuration, patches, and state
# This script restores the Hermes Agent to its configured state

set -e

echo "=========================================="
echo "Hermes Agent Restoration"
echo "=========================================="

HERMES_HOME="$HOME/.hermes"
RECOVERY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo "Recovery directory: $RECOVERY_DIR"
echo "Hermes home: $HERMES_HOME"

# Verify recovery directory exists
if [ ! -d "$RECOVERY_DIR/CONFIG" ]; then
  echo "Error: Recovery directory not found at $RECOVERY_DIR"
  echo "Run this script from the recovery package directory"
  exit 1
fi

# Verify Hermes is installed
if [ ! -d "$HERMES_HOME/hermes-agent" ]; then
  echo "Error: Hermes Agent not installed"
  echo "Run install-hermes.sh first"
  exit 1
fi

echo ""
echo "Step 1: Apply patches..."
cd "$HERMES_HOME/hermes-agent"

# Apply agent_init.py patch
if [ -f "$RECOVERY_DIR/PATCHES/agent_init_context_floor.patch" ]; then
  echo "Applying agent_init_context_floor.patch..."
  git apply "$RECOVERY_DIR/PATCHES/agent_init_context_floor.patch" || echo "Warning: Patch may already be applied"
fi

# Apply voice_mode.py patch
if [ -f "$RECOVERY_DIR/PATCHES/voice_mode_indonesian.patch" ]; then
  echo "Applying voice_mode_indonesian.patch..."
  git apply "$RECOVERY_DIR/PATCHES/voice_mode_indonesian.patch" || echo "Warning: Patch may already be applied"
fi

echo ""
echo "Step 2: Restore configuration files..."
mkdir -p "$HERMES_HOME"
chmod 700 "$HERMES_HOME"

# Restore config.yaml template
if [ -f "$RECOVERY_DIR/CONFIG/config.yaml.template" ]; then
  if [ ! -f "$HERMES_HOME/config.yaml" ]; then
    cp "$RECOVERY_DIR/CONFIG/config.yaml.template" "$HERMES_HOME/config.yaml"
    chmod 600 "$HERMES_HOME/config.yaml"
    echo "✓ config.yaml restored (edit to add secrets)"
  else
    echo "⚠ config.yaml already exists, skipping (backup at config.yaml.bak)"
    cp "$HERMES_HOME/config.yaml" "$HERMES_HOME/config.yaml.bak"
  fi
fi

# Restore SOUL.md
if [ -f "$RECOVERY_DIR/CONFIG/SOUL.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/SOUL.md" "$HERMES_HOME/SOUL.md"
  echo "✓ SOUL.md restored"
fi

# Restore memories
mkdir -p "$HERMES_HOME/memories"
if [ -f "$RECOVERY_DIR/CONFIG/memories/MEMORY.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/memories/MEMORY.md" "$HERMES_HOME/memories/MEMORY.md"
  echo "✓ MEMORY.md restored"
fi
if [ -f "$RECOVERY_DIR/CONFIG/memories/USER.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/memories/USER.md" "$HERMES_HOME/memories/USER.md"
  echo "✓ USER.md restored"
fi

# Restore TTS script
mkdir -p "$HERMES_HOME/scripts"
if [ -f "$RECOVERY_DIR/CONFIG/../SCRIPTS/../chatterbox_tts.py" ]; then
  cp "$RECOVERY_DIR/SCRIPTS/../chatterbox_tts.py" "$HERMES_HOME/scripts/chatterbox_tts.py"
  chmod +x "$HERMES_HOME/scripts/chatterbox_tts.py"
  echo "✓ chatterbox_tts.py restored"
fi

echo ""
echo "Step 3: Configure bashrc..."
if [ -f "$RECOVERY_DIR/CONFIG/bashrc.template" ]; then
  echo "Appending Hermes configuration to ~/.bashrc..."
  cat "$RECOVERY_DIR/CONFIG/bashrc.template" >> "$HOME/.bashrc"
  echo "✓ bashrc updated"
fi

echo ""
echo "Step 4: Setup systemd service (optional)..."
if [ -f "$RECOVERY_DIR/CONFIG/systemd/hermes-gateway.service" ]; then
  read -p "Install systemd service? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/.config/systemd/user"
    cp "$RECOVERY_DIR/CONFIG/systemd/hermes-gateway.service" "$HOME/.config/systemd/user/hermes-gateway.service"
    systemctl --user daemon-reload
    echo "✓ systemd service installed"
    echo "  Enable with: systemctl --user enable --now hermes-gateway"
  fi
fi

echo ""
echo "Step 5: Restore Apologetica Knowledge Base..."
if [ -d "$RECOVERY_DIR/../apologetica" ]; then
  if [ ! -d "$HOME/apologetica" ]; then
    cp -r "$RECOVERY_DIR/../apologetica" "$HOME/apologetica"
    echo "✓ Apologetica KB restored"
  else
    echo "⚠ Apologetica already exists at $HOME/apologetica"
  fi
fi

echo ""
echo "=========================================="
echo "Restoration complete!"
echo ""
echo "Required manual steps:"
echo "  1. Edit ~/.hermes/config.yaml and add API keys"
echo "  2. Create ~/.hermes/.env with secrets (see recovery/SECRETS/README.md)"
echo "  3. Download TTS model (see recovery/MODELS.md)"
echo "  4. Reload shell: source ~/.bashrc"
echo "  5. Verify: ./verify-hermes.sh"
echo "  6. Start gateway: hermes gateway start"
echo "=========================================="