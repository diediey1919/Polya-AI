# DEBATE ARENA — ARGUMENT ENGINE + CRITICAL CLASH ENGINE + MOMENTUM ENGINE

## STATUS
LOCKED SYSTEM SPECIFICATION

This document defines the strategic intelligence layer of Debate Arena.
It extends:
- `01_DEBATE_CORE_CONSTITUTION.md`
- `02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md`
- `03_DEBATE_ROUND_ENGINE_RULES.md`
- `04_DEBATE_MODERATOR_REFEREE_ENGINE.md`
- `05_DEBATE_JUDGE_SCORING_ENGINE.md`
- `06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md`

This document defines: **HOW THE SYSTEM UNDERSTANDS ARGUMENT STRUCTURE, CENTRAL CLASHES, AND DEBATE MOMENTUM.**

---

## 1. CORE PRINCIPLE
A debate is a dynamic strategic network:
$$\text{CLAIM} \rightarrow \text{REASONING} \rightarrow \text{EVIDENCE} \rightarrow \text{ARGUMENT} \rightarrow \text{ATTACK / DEFENSE} \rightarrow \text{CLASH} \rightarrow \text{MOMENTUM}$$
- **ARGUMENT ENGINE**: What arguments exist and how are they related?
- **CLASH ENGINE**: Which disagreements actually determine the debate?
- **MOMENTUM ENGINE**: How is competitive advantage changing over time?

---

## 2 to 19. ARGUMENT ENGINE & GRAPH ARCHITECTURE
- **Argument Identifiers**: `PRO-ARG-001`, `CON-ARG-001`.
- **12 Relation Types**: `SUPPORTS`, `ATTACKS`, `DEFENDS`, `REFUTES`, `QUALIFIES`, `CONTRADICTS`, `DEPENDS_ON`, `EXTENDS`, `REBUILDS`, `ABANDONS`, `CONCEDES`.
- **Hierarchy & Importance**: `DECISIVE`, `CENTRAL`, `IMPORTANT`, `SUPPORTING`, `MINOR`.
- **Lifecycle Tracking**: `INTRODUCED` $\rightarrow$ `DEVELOPED` $\rightarrow$ `CHALLENGED` $\rightarrow$ `DEFENDED` $\rightarrow$ `WEAKENED` $\rightarrow$ `REBUILT` $\rightarrow$ `QUALIFIED` $\rightarrow$ `ABANDONED` $\rightarrow$ `RESOLVED`.
- **Argument Rebuilds**: Preserves both original and rebuilt versions with explicit lineage linking.
- **Concessions & Unanswered Arguments**: Tracks `FULL`, `PARTIAL`, `CONDITIONAL`, `STRATEGIC` concessions and `UNANSWERED` states without assuming automatic loss.
- **Orphan Protection**: Validates that all attacks, defenses, and parent references link to real existing argument nodes.

---

## 20 to 34. CRITICAL CLASH ENGINE
- **Clash Object**: `clash_id`, `title`, `question`, `proposition_position`, `opposition_position`, `argument_refs`, `claim_refs`, `importance`, `status`, `advantage`, `confidence`.
- **Dynamic Ranking**: Prioritizes 3–5 decisive clashes based on:
$$\text{Clash Importance} = \text{Motion Relevance} + \text{Centrality} + \text{Evidence Weight} + \text{Strategic Attention} + \text{Impact}$$
- **Clash Advantage**: `PROPOSITION_ADVANTAGE`, `OPPOSITION_ADVANTAGE`, `CONTESTED`, `INSUFFICIENT_EVIDENCE`.
- **Round 6 Integration**: Supplies top unresolved clashes to Moderator without inventing positions.

---

## 35 to 46. MOMENTUM ENGINE & PRESSURE INDEX
- **Bounded Momentum Scale**: $[-100 \text{ (Opposition)} \dots 0 \dots +100 \text{ (Proposition)}]$.
- **Signal-Driven with Decay**: Driven by decisive rebuttals, strong evidence, cross-ex pressure, concessions, and clash shifts. Decays over rounds.
- **Reversals & Turning Points**: Flags `MOMENTUM_REVERSAL` and evidence-based `TURNING_POINT`.
- **Pressure Index**: Separate metric $[-100 \dots +100]$ measuring the defensive workload and demand placed on opponent.
- **CRITICAL CONSTRAINT**: Momentum does NOT add points to official scores ($\text{Momentum} \ne \text{Score}$).

---

## 47 to 71. INTEGRATION, IMMUTABILITY, AND REPLAY
- **Replay Engine**: Reconstructing from immutable event logs yields 100% identical Argument Graphs, Clash Rankings, and Momentum Timelines.
- **Position Neutrality**: Argument mapping and clash ranking operate identically regardless of team labels.
