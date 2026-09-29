# IMPLEMENTATION GAPS: POLYA PHILOLOGICAL BIBLE ENGINE
**Contract Reference**: Architecture v2.0 — FROZEN  
**Target Scope**: Genesis to Revelation (Hebrew, Aramaic, Koine Greek)  
**Date**: 2026-09-30  

---

## 1. Gaps Matrix by Contract Clause

| Clause / Domain | Required Architecture (v2.0) | Current State in Repository | Gap Severity | Action Required in Plan |
| :--- | :--- | :--- | :--- | :--- |
| **Clause 14–15: Source Immutability** | Cryptographic hash (SHA-256), Level 0 witness immutability, provenance audit trail. | General FTS5 database in `polya_index.db`, no source hash enforcement. | **CRITICAL** | Design immutable source schema with witness and edition tables. |
| **Clause 16–17: Corpus & Pericopes** | Canonical Pericope Registry (Genesis–Revelation), pericope boundary confidence, token offsets. | Pericopes identified dynamically per prompt without registry table. | **HIGH** | Build relational pericope registry and boundary boundary metadata schema. |
| **Clause 18: Textual Criticism** | Critical reading vs variants, primary witness tracking (א, B, DSS, MT, LXX), external/internal rating. | Textual variants discussed in markdown text only; no relational schema. | **HIGH** | Build variant unit schema and apparatus data structures. |
| **Clause 19–24: Linguistic Engine** | Token-level morphology, syntax dependency graphs, discourse analysis, semantic range isolation. | BibleHub parsing standard described in prompt/skill; lacks programmatic validator. | **HIGH** | Implement AST / token model with grammar guards (e.g. perfect aspect guard). |
| **Clause 25–26: Identity & Symbolism Firewall** | Referential engine separating MENTION, REFERENCE, ASSOCIATION, IDENTITY, and SYMBOL. | Prompt guardrails exist; no deterministic validator or rejection gate. | **HIGH** | Implement automated firewall rejecting illicit equations (A associated with B $\neq$ A = B). |
| **Clause 31–33: Evidence Ledger** | Relational ledger of Observations, Claims, Supporting Evidence, Contrary Evidence, Calibrated Confidence. | Narrative tables produced in markdown; no machine-readable queryable ledger. | **HIGH** | Build Evidence Ledger schema and epistemic typing system (`TIER_0`–`TIER_4`). |
| **Clause 39–40: Validation Engine** | 10-layer verification gate (V1 Source to V10 Output) with anti-hallucination checks. | Manual review only. | **CRITICAL** | Implement automated test harness and validation pipeline with pass/fail gates. |
| **Clause 41–45: Multi-Agent Orchestra** | Hermes orchestrator coordinating Textual Critic, Philologist, Syntax Analyst, Exegete, Validator. | Orchestrator exists for Mobile/Debat, but lacks Philological Bible roles. | **MEDIUM** | Extend LangGraph / Hermes runner with specialized philological agent roles. |
| **Clause 65–67: Test Architecture & Golden Corpus** | 50–100 pericopes golden corpus across Greek, Hebrew, Aramaic with adversarial edge cases. | No structured biblical test suite in repo. | **HIGH** | Create golden corpus dataset with 50+ annotated pericopes and adversarial tests. |

---

## 2. Priority Gaps Requiring Immediate Architectural Design
1. **Database Schema & Migration Layer (Phase 1)**: Core tables for texts, witnesses, variants, pericopes, tokens, and evidence ledger.
2. **Deterministic Validation Harness (Phase 8)**: Programmatic rule checker enforcing *No conclusion outruns its evidence* and preventing theological retro-fitting.
3. **Multi-Agent Coordination Harness (Phase 9)**: Scripted wrappers interfacing AGY, Codex, Claude Code, and Hermes for review and implementation cycles.
