# End-to-End Video Intelligence Pipeline Architecture
### Polya Apologetika — Video → Knowledge Bank → Debate Engine
**Document Version:** 1.0.0  
**Status:** Implemented & Verified  

---

## 1. Executive Overview

The Video Intelligence Pipeline transforms unstructured multimedia debate sources into enterprise-grade, verifiable, and dialectically reusable apologetics knowledge objects for **Polya-AI**. 

The fundamental architectural principle is **strict layer separation** and **provenance-first integrity**:
```
RAW DATA (01_raw)
   ↓
BASIC DATA (02_basic-data)
   ↓
BANK DATA (03_bank-data)
   ↓
KNOWLEDGE BANK (04_knowledge-bank)
   ↓
NARRATIVE ENGINE (05_narrative)
   ↓
DEBATE SIMULATION (06_debate)
   ↓
EVALUATION ENGINE (07_evaluation)
```

No claim is accepted as a fact purely because an interlocutor uttered it (**Rule 3 — No Hallucinated Facts**). Every claim retains explicit verification status (`unverified`, `supported`, `contested`, `refuted`) and backward-traceable provenance to exact timestamp and source URL.

---

## 2. Component Architecture & Modular Layout

```
Polya-AI/
├── schemas/video_pipeline/
│   ├── raw_metadata.schema.json
│   ├── basic_data.schema.json
│   ├── bank_data.schema.json
│   ├── knowledge_bank.schema.json
│   ├── narrative.schema.json
│   ├── debate_simulation.schema.json
│   ├── evaluation.schema.json
│   └── manifest.schema.json
│
├── runtime/polya_runtime/video_pipeline/
│   ├── __init__.py
│   ├── config.py              # Pipeline configuration, thresholds, paths
│   ├── storage.py             # Atomic file operations, idempotency, manifests
│   ├── models.py              # Enums (ClaimType, VerificationStatus, etc.)
│   ├── ingestion.py           # Stage A: Ingest metadata and raw transcripts
│   ├── transcription.py       # Stage B: Cleaning & timestamp normalization
│   ├── segmentation.py        # Stage B: Speaker attribution & reference detection
│   ├── extraction.py          # Stage C: Claims, arguments, evidence, fallacies, graph
│   ├── knowledge.py           # Stage D: Entity resolution & Knowledge Bank integration
│   ├── narrative.py           # Stage E: Balanced narrative reconstruction & argument map
│   ├── debate.py              # Stage F: Grounded Socratic debate simulation
│   ├── evaluation.py          # Stage G: Deterministic evaluation & knowledge gaps
│   ├── validation.py          # Strict JSON Schema & referential integrity auditor
│   ├── pipeline.py            # End-to-end orchestrator
│   └── cli.py                 # CLI interface
│
└── data/video_pipeline/
    ├── 01_raw/<video_id>/
    ├── 02_basic-data/<video_id>/
    ├── 03_bank-data/<video_id>/
    ├── 04_knowledge-bank/
    ├── 05_narrative/<video_id>/
    ├── 06_debate/<video_id>/
    ├── 07_evaluation/<video_id>/
    └── manifests/<video_id>.manifest.json
```

---

## 3. Stage Specifications

### Stage A — Raw Ingestion (`01_raw/`)
- Ingests video metadata and raw transcript.
- Preserves pristine source text without mutations.
- Stores extraction telemetry, source type, and quality ratings.

### Stage B — Basic Data (`02_basic-data/`)
- Parses transcript into timestamped segments (`SEG-<video_id>-XXXX`).
- Attributes speakers with confidence scores (`ZUMA`: 0.95, `OPPONENT`: 0.85).
- Scans and catalogs textual and scripture citations (e.g. Romans 15:20, Galatians 2:11-14).
- Produces `metadata.json`, `transcript.json`, `segments.json`, `speakers.json`, `references.json`, and `basic-data.md`.

### Stage C — Bank Data (`03_bank-data/`)
- Deconstructs conversation into syllogisms and propositional units:
  - **Claims**: Classified into 11 canonical types (`THEOLOGICAL_CLAIM`, `HISTORICAL_CLAIM`, `INFERENCE`, etc.).
  - **Arguments**: Premise 1 + Premise 2 + Assumptions -> Reasoning -> Conclusion.
  - **Evidence**: Source citations with reliability rating.
  - **Counterarguments & Rebuttals**: Explicitly mapped.
  - **Fallacies**: Detected and flagged as `is_ai_inference: true` to prevent confusing AI analysis with speaker utterances.
  - **Argument Graph**: Directed relational network (`supports`, `contradicts`, `attacks`, `rebutted_by`, `evidenced_by`).

### Stage D — Knowledge Bank (`04_knowledge-bank/`)
- Decouples single-video data into global enterprise Knowledge Bank objects.
- Entity resolution (`ENT-PERSON-PAULUS`, `ENT-PERSON-PETRUS`).
- Canonical key resolution (`canon_clm_...`).
- Cross-video scalable taxonomy (`topics/`, `entities/`, `claims/`, `relationships/`).

### Stage E — Narrative Engine (`05_narrative/`)
- Reconstructs faithful perspectives of both parties neutrally.
- Generates chronological dialectical flow and turning-point clash analyses.

### Stage F — Grounded Debate Simulation (`06_debate/`)
- Simulates apologetics exchanges strictly grounded in verified Knowledge Bank records.
- Zero-hallucination constraint: every speech must carry explicit provenance citations (`claim_id`, `segment_id`, `timestamp`, `video_url`).
- Formulates Socratic cross-examinations and fatal dilemmas.

### Stage G — Deterministic Evaluation & Knowledge Gaps (`07_evaluation/`)
- Performs backward provenance trace audits (verifies 100% of citations resolve to valid source segments).
- Evaluates logical consistency and argument quality score.
- Identifies **Knowledge Gaps**: flags contested or unverified claims for future academic research.

---

## 4. Scalability & Multi-Video Readiness

1. **Decoupled Canonical Keys**: Entities and topics use canonical UUIDs/keys, allowing seamless merges across 10, 100, or 2,600+ catalog videos without collision.
2. **Idempotency & Manifest Tracking**: Rerunning the pipeline on existing IDs reuses cached data and checks content fingerprints.
3. **ZUMA Persona Decoupling**: Linguistic habits and debate techniques are routed to the Persona/Skill layer (`skills/debate/zuma/`), preserving pristine truth records in the Knowledge Bank.
