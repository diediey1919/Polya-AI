#!/bin/bash
# verify-hermes.sh - Verify Hermes Agent installation and configuration
# This script checks all components are properly installed

set -e

echo "=========================================="
echo "Hermes Agent Verification"
echo "=========================================="

HERMES_HOME="$HOME/.hermes"
ERRORS=0

check() {
  local desc="$1"
  local cmd="$2"
  
  if eval "$cmd" > /dev/null 2>&1; then
    echo "✓ $desc"
  else
    echo "✗ $desc"
    ERRORS=$((ERRORS + 1))
  fi
}

check_output() {
  local desc="$1"
  local cmd="$2"
  local expected="$3"
  
  local output=$(eval "$cmd" 2>&1)
  if echo "$output" | grep -q "$expected"; then
    echo "✓ $desc"
  else
    echo "✗ $desc (expected: $expected)"
    ERRORS=$((ERRORS + 1))
  fi
}

echo ""
echo "=== System Requirements ==="
check "Python 3.11 installed" "python3.11 --version"
check "Node.js v22 installed" "node --version"
check "npm installed" "npm --version"
check "uv installed" "uv --version"
check "ffmpeg installed" "ffmpeg -version"

echo ""
echo "=== Hermes Installation ==="
check "Hermes home exists" "[ -d $HERMES_HOME ]"
check "Hermes Agent repo exists" "[ -d $HERMES_HOME/hermes-agent ]"
check "Hermes CLI executable" "command -v hermes"
check "Hermes venv exists" "[ -d $HERMES_HOME/hermes-agent/venv ]"
check "Node modules installed" "[ -d $HERMES_HOME/hermes-agent/node_modules ]"

echo ""
echo "=== Configuration Files ==="
check "config.yaml exists" "[ -f $HERMES_HOME/config.yaml ]"
check "SOUL.md exists" "[ -f $HERMES_HOME/SOUL.md ]"
check "MEMORY.md exists" "[ -f $HERMES_HOME/memories/MEMORY.md ]"
check "USER.md exists" "[ -f $HERMES_HOME/memories/USER.md ]"

echo ""
echo "=== Patches Applied ==="
check "agent_init.py patched" "grep -q 'is None' $HERMES_HOME/hermes-agent/agent/agent_init.py"
check "voice_mode.py patched" "grep -q 'terima kasih' $HERMES_HOME/hermes-agent/tools/voice_mode.py"

echo ""
echo "=== TTS Configuration ==="
check "Chatterbox script exists" "[ -f $HERMES_HOME/scripts/chatterbox_tts.py ]"
check "TTS model directory exists" "[ -d $HOME/tts-models/chatterbox-indonesian ]"
if [ -d "$HOME/tts-models/chatterbox-indonesian" ]; then
  check "model.safetensors exists" "[ -f $HOME/tts-models/chatterbox-indonesian/model.safetensors ]"
  check "s3gen.safetensors exists" "[ -f $HOME/tts-models/chatterbox-indonesian/s3gen.safetensors ]"
  check "t3_cfg.safetensors exists" "[ -f $HOME/tts-models/chatterbox-indonesian/t3_cfg.safetensors ]"
  check "tokenizer.json exists" "[ -f $HOME/tts-models/chatterbox-indonesian/tokenizer.json ]"
  check "ve.safetensors exists" "[ -f $HOME/tts-models/chatterbox-indonesian/ve.safetensors ]"
  check "example1.wav exists" "[ -f $HOME/tts-models/chatterbox-indonesian/example1.wav ]"
fi

echo ""
echo "=== Apologetica Knowledge Base ==="
check "Apologetica directory exists" "[ -d $HOME/apologetica ]"
if [ -d "$HOME/apologetica" ]; then
  check "Master index exists" "[ -f $HOME/apologetica/APOLOGETICA_MASTER_INDEX.md ]"
  check "Governance exists" "[ -f $HOME/apologetica/KNOWLEDGE_BASE_GOVERNANCE.md ]"
  
  # Count files
  SOURCE_COUNT=$(find "$HOME/apologetica/sources" -name "*.md" 2>/dev/null | wc -l)
  ANALYSIS_COUNT=$(find "$HOME/apologetica/knowledge/analyses" -name "*.md" 2>/dev/null | wc -l)
  
  echo "  Sources: $SOURCE_COUNT"
  echo "  Analyses: $ANALYSIS_COUNT"
  
  # Check for STEP 100 canonical file
  STEP100_CANONICAL="$HOME/apologetica/knowledge/analyses/FULL-CHRISTOLOGY-TRINITY-CROSS-SYSTEM-FORENSIC-AUDIT.md"
  if [ -f "$STEP100_CANONICAL" ]; then
    echo "✓ STEP 100 canonical file found"
    echo "  Path: $STEP100_CANONICAL"
    echo "  Size: $(wc -c < "$STEP100_CANONICAL") bytes"
    echo "  Lines: $(wc -l < "$STEP100_CANONICAL")"
    echo "  Note: STEP 100 is stored as canonical cross-system forensic analysis (no standalone STEP_100.md)"
  else
    echo "⚠ STEP 100 canonical file not found at $STEP100_CANONICAL"
  fi
fi

echo ""
echo "=== Environment Variables ==="
check "PATH includes ~/.local/bin" "echo \$PATH | grep -q '.local/bin'"

# Check for required environment variables (without printing values)
if [ -f "$HERMES_HOME/.env" ]; then
  echo "✓ .env file exists"
  grep -q "OPENROUTER_API_KEY" "$HERMES_HOME/.env" && echo "  ✓ OPENROUTER_API_KEY set" || echo "  ✗ OPENROUTER_API_KEY missing"
  grep -q "GEMINI_API_KEY" "$HERMES_HOME/.env" && echo "  ✓ GEMINI_API_KEY set" || echo "  ✗ GEMINI_API_KEY missing"
else
  echo "✗ .env file missing"
  ERRORS=$((ERRORS + 1))
fi

echo ""
echo "=== Gateway Service ==="
if systemctl --user is-enabled hermes-gateway > /dev/null 2>&1; then
  echo "✓ Gateway service enabled"
  if systemctl --user is-active hermes-gateway > /dev/null 2>&1; then
    echo "✓ Gateway service running"
  else
    echo "⚠ Gateway service not running"
  fi
else
  echo "⚠ Gateway service not installed"
fi

echo ""
echo "=========================================="
if [ $ERRORS -eq 0 ]; then
  echo "✓ All checks passed!"
  echo ""
  echo "Hermes Agent is ready."
  echo "Start with: hermes gateway start"
else
  echo "✗ $ERRORS check(s) failed"
  echo ""
  echo "Review the errors above and fix them."
fi
echo "=========================================="

exit $ERRORS