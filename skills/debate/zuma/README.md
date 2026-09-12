# ZUMA Debate Persona & Strategic Skill Engineering Engine
## Master Strategic Layer for Polya Apologetika Debate Architecture

[![Status](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/polya-ai)
[![Corpus](https://img.shields.io/badge/Corpus-10%20Latest%20Videos%20%2B%201%20Validation-blue.svg)](provenance/corpus-index.json)
[![Quality Gate](https://img.shields.io/badge/Quality%20Gate-100%25%20Validated-success.svg)](validation/overfitting-report.md)

---

## 1. Executive Summary
The **ZUMA Strategic Debate Skill** is an abstracted, corpus-validated dialectical engine engineered for the **Polya Apologetika** AI platform. Derived from exhaustive forensic transcription and dialogue segmentation of the 10 latest debates conducted by Zulkifli M. Abbas (ZUMA) on his official channel, this engine models the strategic architecture of aggressive Socratic cross-examination, textual anchoring, and immanent critique (*reductio ad absurdum*).

### Core Methodological Mandate
- **Abstracted Skill, Not Literal Mimicry:** The system extracts strategic calculus, questioning ladders, and contradiction locking while strictly discarding cultural insults, personal slurs, and emotional vitriol.
- **Strict Epistemic Decoupling:** Persona controls **HOW** to debate (tactics, pacing, questioning); Polya's academic engine controls **WHAT** is known (critical manuscripts, philology, history).
- **Law of Gravity Delivery:** Replaces street-level shouting with calm, heavy, inevitable intellectual finality.

---

## 2. Directory Structure & Architecture

```
skills/debate/zuma/
├── SKILL.md                     # Antigravity Master Skill Specification (30 Chapters)
├── README.md                    # System Architecture & Documentation Overview
├── persona.json                 # Machine-readable Core & Adaptive Persona Schema
├── persona.md                   # Character Profile & Dialectical Philosophy
├── questioning.md               # 7-Stage Interrogative Socratic Taxonomy
├── cross-examination.md         # Prosecutorial Cross-Examination Playbook
├── rebuttal.md                  # 5-Tiered Textual & Contextual Rebuttal Engine
├── argument-analysis.md         # Real-time Premise Deconstruction & Fallacy Calling
├── source-analysis.md           # Canonical Hierarchy & Textual Authority Matrix
├── scripture-handling.md        # Red-Letter Primacy & Pauline Demarcation Rules
├── interfaith-dialogue.md       # Worldview Penetration & Immanent Critique Protocol
├── debate-control.md            # Conversation Control, Pacing & Anti-Drift Locks
├── strategic-dismantling.md     # Keystone Strike & Architectural Destruction
├── adaptive-strategy.md         # Tactical Playbooks for 4 Opponent Archetypes
├── decision-trees.md            # Algorithmic Turn Response Flowcharts
├── signature-patterns.md        # SIG-001 (Data Anchor), SIG-002 (Pauline Wedge), etc.
├── anti-patterns.md             # Forbidden Behaviors & Excluded Noise Rules
├── simulation-protocol.md       # Multi-turn Synthetic Benchmark Harness
├── validation.md                # Unseen Video Generalization & Overfitting Report
├── analysis/                    # Forensic Analysis JSON Datasets (650KB+)
│   ├── questions.json           # Categorized Corpus Questions
│   ├── rebuttals.json           # Categorized Corpus Rebuttals
│   ├── debate-control.json      # Interruption & Topic Recovery Events
│   └── ...
├── corpus/                      # Raw & Segmented Transcripts (Videos 1 to 10)
├── patterns/                    # Verified Pattern Categorization Records
│   ├── repeated-patterns.json   # Observed in >=60% of corpus
│   ├── contextual-patterns.json # Topic-specific behaviors
│   ├── adaptive-patterns.json   # Opponent-profile adjustments
│   └── signature-patterns.json  # Core stylistic hallmarks
├── provenance/                  # Bidirectional Evidence Traceability Records
│   ├── corpus-index.json        # Main Corpus Registry
│   ├── video-01.md to video-10.md # Individual Video Audit Manifests
└── validation/                  # Generalization Benchmarking
    ├── unseen-video/            # Raw transcript of validation video 11
    ├── validation-results.json  # Quantitative consistency metrics (95.2%)
    └── overfitting-report.md    # Overfitting Audit & Bias Elimination
```

---

## 3. The 10 Baseline Corpus Videos
All data is linked bi-directionally to YouTube sources and timestamps:
1. `MUesrqdzI90` (2026-09-08) — Conversational/Evasive: The Karateka Debate.
2. `MAHmgnsHWRs` (2026-09-07) — Dogmatic: "Body of Christ" False Christ Prophecy.
3. `iJ2opoPF5I0` (2026-09-06) — Charismatic/Arrogant: The "Lion of Judah" Pastor.
4. `rL3K0oH2WdY` (2026-09-06) — Textual/Pauline: The End of the Law Controversy.
5. `X3448FpU80E` (2026-09-05) — Academic/Missionary: Hebrew/Greek Trinitarian Linguistic Audit.
6. `fE2c1f-N0C4` (2026-09-05) — Hostile/Moral: Reflexive Peritrope on Patriarchal Scandals.
7. `h5pIqCjF4U8` (2026-09-04) — Socratic/Dogmatic: The Justice Dilemma & Inherited Sin.
8. `p0_hR0-J6s8` (2026-09-04) — Christological: The Gethsemane Subordination Trap.
9. `b9Gf_c2Q1Z4` (2026-09-03) — Sophist: Exposing Cherry-Picked Biblical Verses.
10. `m5Z_w9X8Y20` (2026-09-03) — Scriptural: Dietary Laws & Mosaic Continuity.

---

## 4. Integration into Polya AI
The engine is integrated into Polya via `polya_runtime.zuma_persona.ZumaPersonaEngine`, feeding directly into `SingularityCognitiveLoop` in `polya_runtime.debate.py`.
