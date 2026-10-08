# POLYA APOLOGETICS INTELLIGENCE & AUTONOMOUS RESEARCH ENGINE
## ARCHITECTURE SPECIFICATION (MASTER PROMPT #2)

---

## 1. ARCHITECTURAL OVERVIEW & SEPARATION OF LAYERS

The Polya Intelligence Engine is designed to enforce an immutable epistemological hierarchy:

```text
TRUTH / SOURCE EVIDENCE
    ↓
PROVENANCE & AUDIT
    ↓
EXEGESIS & PHILOLOGICAL REASONING
    ↓
ARGUMENT GRAPH & STEELMAN COUNTERARGUMENT
    ↓
EVALUATION & VERIFICATION GATE
    ↓
ZUMA DEBATE PERSONA & RHETORICAL STRATEGY
    ↓
DEBATE-READY PRESENTATION
```

### Invariant Rules:
1. **Never ZUMA Persona → Evidence**: The debate persona cannot invent facts or alter scriptural translations.
2. **Never Model Opinion → Truth**: Claims must be grounded in verified witnesses (NA28/UBS5, BHS, Dead Sea Scrolls, Papyrus witnesses).
3. **Never Debate Style → Evidence**: Rhetorical momentum must rest on underlying forensic grammatical facts.

---

## 2. MULTI-AGENT ARCHITECTURE & AGENT CAPABILITY REGISTRY

The multi-agent architecture coordinates live OS processes through `AgentRuntime` and dynamically selects optimal agents via `AgentCapabilityRegistry`:

| Agent ID | Runtime Adapter | Model / Core | Capabilities | Specialties | Role Mappings |
|---|---|---|---|---|---|
| `hermes` | `/home/ubuntu/.local/bin/hermes` | Hermes Agent v3 | `gateway`, `supervisor`, `dispatch`, `debate_prep`, `coordination` | Gateway Routing, Multi-Agent Orchestration, ZUMA Posture | `DEBATE_AGENT`, `RESEARCH_AGENT` |
| `codex` | `/home/ubuntu/.npm-global/bin/codex` | GPT-4o Code | `code`, `schema_validation`, `data_transformation`, `unit_testing` | Schema Transformation, Deterministic Transforms | `VERIFICATION_AGENT` |
| `cloud_code` | `/home/ubuntu/.npm-global/bin/claude` | Claude 3.5 Sonnet | `deep_reasoning`, `philology`, `exegesis`, `theology`, `counterargument` | Koine Greek Syntax, Hebrew Semantics, Forensic Exegesis | `PHILOLOGY_AGENT`, `SCRIPTURE_AGENT`, `COUNTERARGUMENT_AGENT`, `SYNTHESIS_AGENT` |
| `anti_gravity` | `/home/ubuntu/.local/bin/agy` | Gemini 1.5 Pro | `infrastructure`, `database_verification`, `integrity_audit`, `docker` | SQLite Evidence Ledger, Audit Trail Verification, Integrity Gates | `SOURCE_AGENT`, `FACT_CHECK_AGENT`, `VERIFICATION_AGENT` |

---

## 3. LANGGRAPH 14-NODE ORCHESTRATION PIPELINE

The end-to-end intelligence pipeline is coordinated as a stateful, checkpointable LangGraph directed graph:

```text
                       [USER CLAIM]
                            │
                            ▼
                     [01. entry_node]
                            │
                            ▼
              [02. task_decomposition_node]
                            │
                            ▼
              [03. research_dispatch_node]
                            │
                            ▼
              [04. evidence_retrieval_node]
                            │
                            ▼
                [05. claim_analysis_node]
                            │
                            ▼
                [06. argument_graph_node]
                            │
                            ▼
           [07. steelman_counterargument_node]
                            │
                            ▼
           [08. contradiction_detection_node]
                            │
                            ▼
                 [09. verification_node]
                            │
                            ▼
                [10. gap_detection_loop] ◄────────┐
                            │ (Bounded Loop)       │
                            ├──────────────────────┘
                            │ (Coverage Met / Budget Met)
                            ▼
            [11. synthesis_evaluation_node]
                            │
                            ▼
           [12. zuma_debate_preparation_node]
                            │
                            ▼
            [13. case_file_persistence_node]
                            │
                            ▼
                [14. final_response_node]
                            │
                            ▼
                         [ END ]
```

---

## 4. TASK DECOMPOSITION & EXECUTION PLAN

Incoming claims are decomposed into canonical 10-task directed acyclic graphs:
1. `task_01_claim_ident`: Semantic scope and subject-predicate identification.
2. `task_02_pauline_passages`: Primary scripture retrieval from Pauline corpus (Roma 3:31, Roma 7:12, Roma 10:4, Galatia 3:13, Efesus 2:15).
3. `task_03_torah_gospel_baseline`: Torah perpetuity (Ulangan 4:2, Keluaran 31:16-17) and Jesus' baseline (Matius 5:17-19).
4. `task_04_philology`: Greek morphology (BDAG parsing of καταργέω, ἵστημι, πληρόω, νόμος).
5. `task_05_historical_context`: Second Temple Judaism halakha and table fellowship.
6. `task_06_contradiction_detection`: Contextual tension audit between Roma 3:31 and Efesus 2:15.
7. `task_07_steelman_counterarg`: Formidable opponent argument formulation without strawmanning.
8. `task_08_verification_audit`: Citation accuracy and manuscript provenance audit.
9. `task_09_synthesis_evaluation`: Multi-dimensional evaluation across 10 discrete analytical metrics.
10. `task_10_debate_preparation`: ZUMA Socratic interrogation funnel and cross-examination questions.

---

## 5. SOURCE-LANGUAGE EVIDENCE RETRIEVAL & PHILOLOGY

### Evidence Classification Hierarchy
- `PRIMARY_SOURCE`: Early manuscript witnesses (P46, Codex Sinaiticus, Codex Vaticanus).
- `DIRECT_EVIDENCE`: Direct syntactic clauses addressing the proposition.
- `CONTEXTUAL_EVIDENCE`: Surrounding pericope discourse and socio-historical setting.
- `SECONDARY_SOURCE`: Patristic commentaries and rabbinic literature.
- `INTERPRETIVE`: Systematic theological formulations.
- `DISPUTED`: Textual variant units or contested syntactic readings.

### Linguistic Fact vs. Theological Interpretation
- **Textual Fact**: Roma 3:31 contains the verb `καταργοῦμεν` in a rhetorical question followed by `μὴ γένοιτο` and `νόμον ἱστάνομεν`.
- **Linguistic Interpretation**: `ἱστάνομεν` (present active indicative) is durative, expressing continual establishment.
- **Theological Interpretation**: Paul denies that justification by faith abrogates the moral revelation of God's Law.

---

## 6. CLAIM & ARGUMENT GRAPH

### Canonical Claim Schema
- `claim_id`: Unique persistent identifier.
- `claim_type`: `THEOLOGICAL_EXEGETICAL`.
- `subject`: `Paulus dari Tarsus`.
- `predicate`: `membatalkan (katargeō)`.
- `objects`: `Hukum Taurat`, `Ordinances`.
- `sources`: Primary scripture references.
- `counterclaims`: Documented opposing positions.
- `confidence`: Calibrated statistical score (0.0 to 1.0).

### Argument Graph Nodes
- **Argument**: Claim → Premises → Evidence Links → Inferences → Conclusion.
- **Steelman Counterargument**: Opponent Claim → Opponent Evidence → Opponent Reasoning → Opponent Assumptions → Opponent Strength → Weaknesses → Rebuttal → Rebuttal Evidence.

---

## 7. CONTRADICTION CLASSIFICATION ENGINE

Contradictions are audited against 6 explicit epistemic tiers:
1. `DIRECT_CONTRADICTION`: Incompatible factual statements within identical scope and definition.
2. `POTENTIAL_CONTRADICTION`: Apparent tension requiring manuscript or lexical disambiguation.
3. `APPARENT_CONTRADICTION`: Superficial tension easily resolved by immediate context.
4. `CONTEXTUAL_DIFFERENCE`: Valid statements differing in recipient audience, covenantal timing, or semantic scope.
5. `NO_CONTRADICTION`: Fully harmonized statements.
6. `UNRESOLVED`: Insufficient historical or textual data to adjudicate.

---

## 8. ZUMA STRATEGIC DEBATE LAYER

The ZUMA layer transforms exegetical findings into sharp, cold, Socratic debate weapons:
- **Textual Anchoring**: *"Buka pasal dan ayatnya"*—forcing opponents to cite primary text before philosophical retreat.
- **Immanent Critique (*Ilzam al-Khasm*)**: Refuting antinomian positions using the opponent's own Pauline corpus.
- **Maieutic Funnel**: Framing constructive dilemmas where either horn forces a critical concession.
- **Strict Nomenclature Rules**: Complete book names (*Roma*, *Matius*, *Galatia*), exact chapter:verse (*Roma 3:31*), standard *Bible* nomenclature, zero open web links.

---

## 9. PERSISTENT CANONICAL CASE FILE & AUDIT TRACE

Every execution is stored in `data/polya_arena.db`:
- Table `case_files_v2`: Resumable JSON state, user context, 10 canonical fields.
- Table `execution_traces`: Full telemetry tracing every step: `run_id`, `thread_id`, `task_id`, `node`, `agent`, `status`, `start`, `finish`, `duration`.
