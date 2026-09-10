# Autonomous Implementation Plan for Master Prompt #2

---

### Phase 1: Knowledge Store Synchronization & Baseline Lock
- Non-destructive sync of 4 fork analyses into `/home/ubuntu/apologetica/knowledge/analyses/`.
- Update Canonical `DEBATE-FALLACY-AUDIT-FORENSIC-AUDIT.md` to verified full 204KB version.
- Non-destructive commit of 9 canonical sources into `/home/ubuntu/Polya-AI/`.
- Synchronize `KNOWLEDGE_INDEX.md` with complete 166-entity catalog.

### Phase 2: Indexing & Retrieval Engine Construction
- Build local SQLite FTS5 / BM25 index over all sources, claims, and analyses.
- Add metadata filtering by specialist, step, and tradition.
- Implement retrieval query builder with claim decomposition.

### Phase 3: Runtime Activation Layer
- Connect Polia Knowledge Engine to Hermes as an MCP tool provider or custom skill.
- Enable automatic context activation based on user query intent.
- Implement Debate State memory schema.

### Phase 4: Verification & Acceptance Testing
- Run battery of 30 benchmark queries.
- Measure retrieval latency (<100ms) and token efficiency.
