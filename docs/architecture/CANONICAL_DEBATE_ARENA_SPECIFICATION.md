# CANONICAL DEBATE ARENA SPECIFICATION
## Comprehensive Master Specification & Operational Blueprint

**System Identity**: Polya Debate Arena Engine  
**Authoritative Location**: `runtime/debate_prompts/` (Prompts 01–14)  
**Implementation**: `runtime/polya_runtime/debate_engine/` (32 Python modules)  
**Presentation Layer**: `web/static/arena.html`  
**API Routing**: `runtime/polya_runtime/debate_engine/api.py` (Mounted in `web/app.py` under `/api/debate`)  
**Certification Status**: 100% Certified, Zero Regression  

---

## 1. CONSTITUTIONAL FOUNDATION (Prompt 01: Core Constitution)

### 1.1 System Role
- The Debate Arena operates as a professional, competitive, human-versus-human 3-vs-3 debate event system.
- **Team Proposition**: Debaters P1, P2, P3.
- **Team Opposition**: Debaters C1, C2, C3.
- **Total Debaters**: Exactly 6 human participants.

### 1.2 The Absolute Neutrality Axiom
- **The AI is strictly NOT a debater.**
- The AI must **never**:
  1. Introduce arguments for either team.
  2. Defend or attack a team on its own behalf.
  3. Inject personal, partisan, or doctrinal opinions.
  4. Replace a human debater or act as P4/C4.
  5. Favor one team's case over the other.
- The AI's role is strictly supervisory, analytical, refereeing, and adjudicative.

### 1.3 Separated AI Functional Roles
Even when powered by the same underlying model, functional roles are strictly modularized:
- **Host**: Ceremonial welcome and conclusion.
- **Moderator**: Turn and floor controller.
- **Timekeeper**: Strict clock and bell enforcement.
- **Referee**: Sanction and rule enforcer (warnings, point deductions, disqualifications).
- **Fact-Checker & Evidence Analyst**: Source authenticity and provenance verification.
- **Argument & Clash Analyst**: Causal tracking of unresolved clashes.
- **Judge & Score Engine**: Impartial point allocation across 6 rubrics.
- **Commentator**: Non-partisan tactical play-by-play analysis.
- **Post-Debate Analyst**: Comprehensive statistical and strategic match debriefing.

---

## 2. EVENT STATE ENGINE & DEBATE PROTOCOL (Prompt 02)

### 2.1 Authoritative Finite State Machine (16 States)
The state machine is the **Single Source of Truth** (`polya_runtime.debate_engine.state_machine`). AI responses can never override state machine decisions.

```text
SETUP
  ↓
READY
  ↓
EVENT_START
  ↓
ROUND_INTRO
  ↓
SPEECH_ACTIVE ⇄ POI_ACTIVE / CROSS_EXAM
  ↓
SPEECH_CONCLUSION
  ↓
ROUND_REVIEW
  ↓
INTERMISSION
  ↓
NEXT_ROUND / REPEAT
  ↓
DEBATE_CONCLUSION
  ↓
ADJUDICATION
  ↓
RESULTS_ANNOUNCED
  ↓
EVENT_CLOSED
  ↓
ARCHIVED
```

---

## 3. ROUND ENGINE & ROUND RULES (Prompt 03)

### 3.1 Match Structure (5 Standard Rounds)
1. **Round 1: Constructive Speeches**
   - P1 (Prime Minister): Frame motion, define parameters, present substantive cases 1 & 2.
   - C1 (Leader of Opposition): Refute setup, offer counter-model, present opposition cases 1 & 2.
2. **Round 2: Cross-Examination / POI Arena**
   - Structured interrogations with strict floor rights and direct answer requirements.
3. **Round 3: Rebuttal Speeches**
   - P2 / C2: Direct clash on core substantive points; defense of original framework.
4. **Round 4: Defense & Consolidation**
   - Deep textual defense, historical substantiation, exposure of opponents' structural fallacies.
5. **Round 5: Whip / Summary Speeches**
   - P3 / C3: Zero new arguments permitted; crystallized clash summary; crystallization of why their team won the decisive clashes.

---

## 4. MODERATOR & REFEREE ENGINE (Prompt 04)

### 4.1 Turn & Floor Control
- `PermissionMatrix` enforces who may speak, type, or raise POIs at any millisecond.
- Speaking out of turn triggers immediate floor muting and warning issuance.

### 4.2 Sanction Hierarchy
1. **Verbal Caution**: Informal warning without point deduction.
2. **Formal Foul / Warning**: Recorded in match ledger; displayed on UI.
3. **Point Deduction**: Minor (-1 to -3 points) or Major (-5 to -10 points) applied to speaker score.
4. **Disqualification / Forfeit**: For gross ad-hominem, hate speech, or sustained insubordination.

---

## 5. JUDGE & SCORING ENGINE (Prompt 05)

### 5.1 Six Scoring Dimensions (100 Points Total per Debater)
1. **Matter (25 pts)**: Depth of argument, factual accuracy, textual evidence grounding.
2. **Manner (20 pts)**: Persuasiveness, rhetorical control, composure, professional delivery.
3. **Method (15 pts)**: Structural coherence, time allocation, team role fulfillment.
4. **Logic & Reasoning (15 pts)**: Absence of fallacies, valid deductive/inductive soundness.
5. **Cross-Examination & Responsiveness (15 pts)**: Directness in answering, precision in questioning.
6. **Clash & Rebuttal (10 pts)**: Success in engaging and neutralizing opposing core arguments.

---

## 6. FACT-CHECK & EVIDENCE ENGINE (Prompt 06)

### 6.1 Source Truth Hierarchy
Strict source classification prevents manufactured citations:
1. **Tier 1 (Primary Text)**: Biblical manuscripts (Codex Sinaiticus, Vaticanus, Papyri P46/P66), classical Hebrew/Greek critical editions (NA28, BHS).
2. **Tier 2 (Direct Evidence)**: Explicit lexical or syntactic clauses directly speaking to the claim.
3. **Tier 3 (Contextual Evidence)**: Pericope discourse context, historical situation.
4. **Tier 4 (Secondary Scholarship)**: Patristic commentaries, peer-reviewed monographs.
5. **Tier 5 (Interpretive)**: Systematic theological dogmatics.

---

## 7. ARGUMENT, CLASH & MOMENTUM ENGINE (Prompt 07)

### 7.1 Causal Graph & Clash Points
- Tracks arguments as DAG nodes (`Claim -> Evidence -> Warrant -> Impact`).
- Maps clashes when contradictory claims collide on the same factual or theological node.
- Computes real-time win probability shifts and momentum indicators.

---

## 8. AI COMMENTARY ENGINE (Prompt 08)

### 8.1 Play-by-Play Strategic Commentary
- Generates live analysis: tactical momentum shifts, concession traps, missed opportunities.
- Strictly non-partisan tone: analyzes *mechanics of persuasion*, never endorses opinions.

---

## 9. REPLAY & ANALYTICS ENGINE (Prompt 09)

### 9.1 Match Telemetry & Replay
- Every turn, action, score, and sanction is recorded with nanosecond timestamps.
- Generates post-match Debater Stat Cards, turning point graphs, and shareable match logs.

---

## 10. PERSONA ZUMA INTEGRATION (Prompt 10)

### 10.1 Zuma Apologetics Layer
- Activates Polya's canonical Socratic posture:
  1. High signal-to-noise ratio, zero emotional rhetoric.
  2. Forensic source-language interrogation (Koine Greek / Biblical Hebrew).
  3. Concession extraction: trapping opponents within their own textual premises (*Ilzam al-Khasm*).

---

## 11. PRESENTATION & EVENT UI LAYER (Prompt 12)

### 11.1 Component Specification (`web/static/arena.html`)
- **Stage Podium**: Active speaker spotlight with round title and clock.
- **Team Pods**: 3 Debater cards for Proposition (P1, P2, P3) and 3 for Opposition (C1, C2, C3).
- **Momentum Bar**: Live win probability visualization.
- **Referee Alert Box**: Active fouls and penalties counter.
- **Fact-Check Banner**: Live source verification status.
- **Strategic Commentary Feed**: Live play-by-play tactical stream.

---

## 12. LIVE CONCURRENCY & STREAMING (Prompt 13)

### 12.1 Concurrency Architecture
- WebSocket and SSE pub-sub broadcast.
- Match locks guarantee linear event execution without race conditions.

---

## 13. DEBATE TRAINING & AI DEBATER ENGINE (Prompt 14)

### 13.1 Strict Constitutional Mode Isolation
- **Live Match Mode**: AI is strictly supervisory. AI debater participation is forbidden.
- **Training Sparring Mode**: AI is explicitly instantiated as a synthetic sparring partner to train human debaters through calibrated Socratic cross-examinations.

---

## 14. SOURCE CODE REPOSITORY INVENTORY

| Subsystem | File Path |
|---|---|
| Master Constitution | `runtime/debate_prompts/01_DEBATE_CORE_CONSTITUTION.md` |
| Event Protocol | `runtime/debate_prompts/02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md` |
| Round Rules | `runtime/debate_prompts/03_DEBATE_ROUND_ENGINE_RULES.md` |
| Moderator & Referee | `runtime/debate_prompts/04_DEBATE_MODERATOR_REFEREE_ENGINE.md` |
| Judge & Scoring | `runtime/debate_prompts/05_DEBATE_JUDGE_SCORING_ENGINE.md` |
| Fact-Checking | `runtime/debate_prompts/06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md` |
| Argument & Clash | `runtime/debate_prompts/07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md` |
| Commentary | `runtime/debate_prompts/08_DEBATE_AI_COMMENTARY_ENGINE.md` |
| Replay Analytics | `runtime/debate_prompts/09_DEBATE_REPLAY_ANALYTICS_ENGINE.md` |
| Persona Zuma | `runtime/debate_prompts/10_DEBATE_PERSONA_ZUMA_INTEGRATION.md` |
| Full Integration | `runtime/debate_prompts/11_DEBATE_FULL_INTEGRATION_STRESS_TEST.md` |
| UI Presentation | `runtime/debate_prompts/12_DEBATE_PRESENTATION_EVENT_UI.md` |
| Live Concurrency | `runtime/debate_prompts/13_DEBATE_LIVE_CONCURRENCY_VALIDATION.md` |
| AI Debater Training | `runtime/debate_prompts/14_DEBATE_TRAINING_AND_AI_DEBATER_ENGINE.md` |
| Reference Transcript | `runtime/debate_prompts/golden_match_001.json` |
| Core Python Engine | `runtime/polya_runtime/debate_engine/engine.py` |
| State Machine | `runtime/polya_runtime/debate_engine/state_machine.py` |
| Round Engine | `runtime/polya_runtime/debate_engine/round_engine.py` |
| Referee Engine | `runtime/polya_runtime/debate_engine/referee_engine.py` |
| Judge Engine | `runtime/polya_runtime/debate_engine/judge_engine.py` |
| Fact Engine | `runtime/polya_runtime/debate_engine/evidence_fact_engine.py` |
| Clash Engine | `runtime/polya_runtime/debate_engine/clash_engine.py` |
| Commentary Engine | `runtime/polya_runtime/debate_engine/commentary_engine.py` |
| Replay Engine | `runtime/polya_runtime/debate_engine/replay_engine.py` |
| Persona Engine | `runtime/polya_runtime/debate_engine/persona_engine.py` |
| Training Engine | `runtime/polya_runtime/debate_engine/training_engine.py` |
| API Endpoints | `runtime/polya_runtime/debate_engine/api.py` |
| Presentation UI | `web/static/arena.html` |
