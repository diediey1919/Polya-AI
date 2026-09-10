# Current Runtime Architecture Audit

---

### 1. Current Request Lifecycle
```
USER INPUT
  ↓
Hermes Gateway / Antigravity
  ↓
LLM Prompt (SOUL.md + System Prompt + Tools)
  ↓
Tool Execution (Manual file read / web / bash)
  ↓
Response Generation
```

### 2. Polia Component Integration Status
- **`system/99_AI_SYSTEM_PROMPT.md`:** Chief Apologetics Agent prompt exists (732 lines) but is NOT loaded as Hermes's active system prompt (`~/.hermes/SOUL.md` currently loads Hermes default).
- **Specialist Modules (01–12):** Registered on disk, but NOT loaded dynamically into the context.
- **Runtime Activation:** NOT YET IMPLEMENTED.
- **Debate State / Session Memory:** Hermes has general conversational SQLite storage (`state.db`), but NO apologetic debate-state tracking.
