#!/bin/bash
# restore-hermes.sh - Restore Hermes & Polya-AI configuration, patches, and state
# This script restores the system to its full configured state

set -e

echo "=========================================="
echo "Hermes Agent & Polya-AI Full Restoration"
echo "=========================================="

HERMES_HOME="$HOME/.hermes"
POLYA_HOME="$HOME/.polya"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RECOVERY_DIR="$REPO_DIR/recovery"

echo ""
echo "Repository directory: $REPO_DIR"
echo "Recovery directory: $RECOVERY_DIR"
echo "Hermes home: $HERMES_HOME"
echo "Polya home: $POLYA_HOME"

# Step 1: Hermes Patches
if [ -d "$HERMES_HOME/hermes-agent" ]; then
  echo ""
  echo "Step 1: Applying patches to Hermes Agent..."
  cd "$HERMES_HOME/hermes-agent"
  if [ -f "$RECOVERY_DIR/PATCHES/agent_init_context_floor.patch" ]; then
    git apply "$RECOVERY_DIR/PATCHES/agent_init_context_floor.patch" 2>/dev/null || echo "Info: agent_init patch already applied"
  fi
  if [ -f "$RECOVERY_DIR/PATCHES/voice_mode_indonesian.patch" ]; then
    git apply "$RECOVERY_DIR/PATCHES/voice_mode_indonesian.patch" 2>/dev/null || echo "Info: voice_mode patch already applied"
  fi
fi

# Step 2: Restore Configuration Files & Memories
echo ""
echo "Step 2: Restoring configuration files & memories..."
mkdir -p "$HERMES_HOME/memories" "$POLYA_HOME"
chmod 700 "$HERMES_HOME" "$POLYA_HOME"

if [ -f "$RECOVERY_DIR/CONFIG/memories/MEMORY.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/memories/MEMORY.md" "$HERMES_HOME/memories/MEMORY.md"
  echo "✓ MEMORY.md restored"
fi
if [ -f "$RECOVERY_DIR/CONFIG/memories/USER.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/memories/USER.md" "$HERMES_HOME/memories/USER.md"
  echo "✓ USER.md restored"
fi
if [ -f "$RECOVERY_DIR/CONFIG/SOUL.md" ]; then
  cp "$RECOVERY_DIR/CONFIG/SOUL.md" "$HERMES_HOME/SOUL.md"
  echo "✓ SOUL.md restored"
fi

# Step 3: Restore Polya Knowledge Base Index
echo ""
echo "Step 3: Restoring Polya Knowledge Index SQLite..."
if [ -f "$REPO_DIR/data/polya_index_schema_and_catalog.sql" ]; then
  if [ ! -f "$POLYA_HOME/polya_index.db" ]; then
    echo "Creating $POLYA_HOME/polya_index.db from SQL dump..."
    sqlite3 "$POLYA_HOME/polya_index.db" < "$REPO_DIR/data/polya_index_schema_and_catalog.sql"
    echo "✓ polya_index.db restored"
  else
    echo "Info: polya_index.db already exists"
  fi
fi

# Step 4: Run Polya Runtime Index Verification
echo ""
echo "Step 4: Verifying Polya Runtime index..."
if [ -d "$REPO_DIR/runtime" ]; then
  python3 -c "
import sys
sys.path.insert(0, '$REPO_DIR/runtime')
try:
    from polya_runtime.indexer import KnowledgeIndexer
    idx = KnowledgeIndexer()
    print('Polya DB stats:', idx.get_stats())
except Exception as e:
    print('Indexer status:', e)
" || true
fi

echo ""
echo "=========================================="
echo "Restoration complete!"
echo "=========================================="
