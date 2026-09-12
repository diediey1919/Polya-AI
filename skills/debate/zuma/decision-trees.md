# ALGORITHMIC DECISION TREES FOR TURN PROCESSING
## Formal Logic Trees for Real-Time Debate Interaction

---

## Master Turn Decision Tree (ASCII Schematic)

```
[OPPONENT MAKES STATEMENT]
           │
           ▼
   [Is citation present?]
   ├── NO  ──► [PAT-REP-001: Demand explicit scripture (Kitab, pasal, ayat)]
   │
   └── YES ──► [Is the citation quoted accurately in context?]
               ├── NO (Cherry-picked) ──► [Expand pericope, read +-5 verses (PAT-REP-003)]
               │
               └── YES ────────────────► [Does it conflict with Red-Letter Jesus?]
                                         ├── YES ──► [SIG-002: Apply Pauline Wedge]
                                         │
                                         └── NO  ──► [Is opponent evading the active lock?]
                                                     ├── YES ──► [PAT-REP-004: Execute Topic Recovery]
                                                     └── NO  ──► [PAT-REP-002: Deploy Socratic Dichotomy Lock]
```

---

## Evasion Interception Decision Tree
```
[OPPONENT STARTS SPEAKING]
           │
     [Start Timer]
           │
  [Speech > 15s without data?]
  ├── NO  ──► [Allow opponent to complete point]
  │
  └── YES ──► [Is semantic drift > 50% from original question?]
              ├── NO  ──► [Allow 10s grace period]
              └── YES ──► [INTERRUPT: Snap back to original question verbatim]
```
