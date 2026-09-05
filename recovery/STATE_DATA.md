# State Data

## Classification

### CRITICAL STATE

**~/.hermes/state.db** (101 MB)
- SQLite database containing conversation history, session data, and agent state
- Contains private user conversations and session metadata
- **Restoration**: Optional - can start fresh or restore from backup
- **Privacy**: May contain sensitive conversation data

### IMPORTANT STATE

**~/.hermes/skills/** (4.6 MB)
- Custom skills and procedures learned during operation
- Contains task-specific workflows and knowledge
- **Restoration**: Recommended - preserves learned procedures
- **Location**: Can be copied directly or regenerated through use

**~/.hermes/pastes/** (1.5 MB)
- Temporary paste storage for code snippets and text
- **Restoration**: Optional - ephemeral data

### OPTIONAL STATE

**~/.hermes/kanban.db** (116 KB)
- Kanban board state for task management
- **Restoration**: Optional - can be recreated

**~/.hermes/verification_evidence.db** (32 KB)
- Verification evidence for audit trails
- **Restoration**: Optional - historical data

## Restoration Procedure

### Option 1: Fresh Start (Recommended for Privacy)
```bash
# Skip state restoration
# Hermes will create fresh databases on first run
```

### Option 2: Selective Restore
```bash
# Restore skills (recommended)
cp -r backup/skills/ ~/.hermes/skills/

# Restore kanban (optional)
cp backup/kanban.db ~/.hermes/

# Skip state.db for privacy
```

### Option 3: Full Restore
```bash
# Restore all state (includes private conversations)
cp backup/state.db ~/.hermes/
cp backup/kanban.db ~/.hermes/
cp backup/verification_evidence.db ~/.hermes/
cp -r backup/skills/ ~/.hermes/skills/
cp -r backup/pastes/ ~/.hermes/pastes/
```

## Backup Strategy

Create encrypted backups of state data separately from the recovery repository:

```bash
# Create encrypted backup
tar czf hermes-state-$(date +%Y%m%d).tar.gz \
  ~/.hermes/state.db \
  ~/.hermes/skills/ \
  ~/.hermes/kanban.db \
  ~/.hermes/verification_evidence.db

# Encrypt with GPG
gpg --symmetric --cipher-algo AES256 hermes-state-$(date +%Y%m%d).tar.gz

# Store encrypted backup in secure location (not in Git)
```

## Privacy Notice

**state.db contains private conversation data.** Do not:
- Commit state.db to Git
- Share state.db without encryption
- Restore state.db on shared systems without consent

Consider starting fresh on new systems for privacy.