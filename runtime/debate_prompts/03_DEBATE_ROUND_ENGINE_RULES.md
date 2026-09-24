# DEBATE ARENA — ROUND ENGINE & ROUND RULES

## STATUS
LOCKED SYSTEM SPECIFICATION

This document is the operational specification for the individual rounds of Debate Arena.
It extends:
- `01_DEBATE_CORE_CONSTITUTION.md`
- `02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md`

Do not replace or modify the authority of those documents.
This document defines: **WHAT HAPPENS INSIDE EACH ROUND.**

---

## 1. ROUND ENGINE PRINCIPLE

The Round Engine controls the internal flow of every debate round.
The hierarchy is:

```
EVENT CONSTITUTION
        ↓
EVENT STATE ENGINE
        ↓
ROUND ENGINE
        ↓
ROUND RULES
        ↓
SPEAKER TURN
        ↓
ACTION
        ↓
ANALYSIS
        ↓
SCORING EVENT
```

The Round Engine must never bypass the Event State Engine.
The Event State Engine remains the ultimate authority for event state and transitions.

---

## 2. STANDARD PROFESSIONAL FORMAT

- **ROUND 0**: Introduction
- **ROUND 1**: Opening Statements
- **ROUND 2**: Constructive Case
- **ROUND 3**: Evidence & Argument
- **ROUND 4**: Cross Examination
- **ROUND 5**: Rebuttal
- **ROUND 6**: Critical Clash
- **ROUND 7**: Final Rebuttal
- **ROUND 8**: Closing Statements
- **ROUND 9**: AI Deliberation
- **ROUND 10**: Verdict

---

## 3. SPEAKER IDENTIFICATION & STRATEGIC ROLES

### PROPOSITION
- **P1**: Case Builder (Framing, Definitions, Core Thesis)
- **P2**: Argument & Evidence Specialist (Substantive Logic, Deep Citations)
- **P3**: Rebuttal & Closing Specialist (Dialectical Cross-Ex, Rebuttals, Clash Synthesis)

### OPPOSITION
- **C1**: Case Builder (Counter-Framing, Definitions, Core Thesis)
- **C2**: Argument & Evidence Specialist (Substantive Logic, Deep Citations)
- **C3**: Rebuttal & Closing Specialist (Dialectical Cross-Ex, Rebuttals, Clash Synthesis)

---

## 4. ROUND 1 — OPENING STATEMENTS
- **Purpose**: Establish fundamental case, definitions, framing, and thesis.
- **Order**: P1 → C1.
- **Restrictions**: No interruptions, no cross-ex, no off-turn rebuttal.
- **AI**: Records arguments, claims, preliminary clashes. Does NOT introduce arguments.

---

## 5. ROUND 2 — CONSTRUCTIVE CASE
- **Purpose**: Substantively develop the case established in opening.
- **Order**: P2 → C2.
- **Team Continuity**: AI evaluates whether P2/C2 logically develops P1/C1's foundational thesis.

---

## 6. ROUND 3 — EVIDENCE & ARGUMENT
- **Purpose**: Deep forensic citations, manuscripts, and structured argumentation (`CLAIM → REASONING → EVIDENCE → IMPACT`).
- **Participants**: P2/P3 vs C2/C3.
- **AI**: Evaluates source quality, claim match, detects unsupported claims, updates Argument Graph & Evidence Registry.

---

## 7 & 8 & 9. ROUND 4 — CROSS EXAMINATION & MICRO-PROTOCOL
- **Purpose**: Test opposing claims under structured dialectical pressure.
- **Default Structure**: P3 questions C1/C2 → C3 questions P1/P2.
- **Micro-Protocol Sequence**: `QUESTION → ANSWER → FOLLOW-UP → RESPONSE`.
- **Enforcement**: Strict question & answer duration, max follow-ups (default: 1-2), no uncontrolled speeches.

---

## 10 & 11. ROUND 5 — REBUTTAL & STRAWMAN DETECTION
- **Purpose**: Target opposing premises and evidence directly (`TARGET ARGUMENT → WEAKNESS → COUNTER-REASONING / EVIDENCE → IMPACT`).
- **Order**: P3 → C3.
- **Strawman Protection**: Detects distorted representations of opponent arguments and adjusts evaluation contextually.

---

## 12, 13 & 14. ROUND 6 — CRITICAL CLASH
- **Purpose**: Condense debate to 3–5 decisive disputes (e.g. Safety vs Innovation, Literalism vs Historical Context, Divine Plurality vs Pure Monotheism).
- **Procedure**: Moderator announces Clash #N → Speakers engage specifically on that clash.
- **Tracking**: Advantage tracker (`PROPOSITION_ADVANTAGE`, `OPPOSITION_ADVANTAGE`, `CONTESTED`, `INSUFFICIENT_EVIDENCE`).

---

## 15. ROUND 7 — FINAL REBUTTAL
- **Purpose**: Final opportunity to answer major unresolved attacks and critical clashes.
- **Focus**: Core clashes and pivotal arguments (not trivial peripheral points).

---

## 16. ROUND 8 — CLOSING
- **Purpose**: Summarize why the team's case is superior.
- **Order**: P3 → C3 (or P1 → C1).
- **Rule**: Substantive new arguments are forbidden during closing unless configured otherwise.

---

## 17 & 18. SPEAKER ROTATION & CONFIGURATION
- Explicit deterministic order, durations, max follow-ups, allowed actions, scoring priorities, and completion criteria.

---

## 19 & 20. ROUND START & END EVENTS
- Round starts trigger `ROUND_START` event.
- Round completes only when all speaker turns or configured micro-exchanges finish deterministically.

---

## 21 & 22. SPEECH START & END EVENTS
- `SPEECH_STARTED` and `SPEECH_ENDED` trigger automated claim/evidence extraction, scoring analysis, and transcript capture.

---

## 23 & 24. INTERRUPTIONS & NEUTRAL MODERATION
- Controlled Points of Order/Clarification.
- Moderator controls procedure neutrally ("Please address the question directly") without judging substance.

---

## 25 & 26. ROUND-SPECIFIC SCORING & MICRO-EVALUATIONS
- Specific scoring categories prioritized per round (Opening: Argument & Logic; Evidence: Factuality; Cross-Ex: Responsiveness & Cross-Ex; Rebuttal: Rebuttal & Impact).
- Micro-evaluation events attach confidence, score deltas, and evidence references.

---

## 27 & 28. ROUND MEMORY & CONTEXT COMPRESSION
- Argument lineage preserved across rounds (`PRO-A01` introduced $\rightarrow$ developed $\rightarrow$ attacked $\rightarrow$ defended $\rightarrow$ clash marked).
- Context compression sends relevant argument lineage rather than raw bloated transcripts.

---

## 29, 30, 31, 32 & 33. RELIABILITY, UX & EVENT LOGGING
- AI failures fail soft (`FACT_CHECK_PENDING`, pause/recover) without breaking the event clock.
- Complete deterministic log: `ROUND_STARTED`, `SPEECH_STARTED`, `SPEECH_ENDED`, `QUESTION_STARTED`, `ANSWER_STARTED`, `REBUTTAL_STARTED`, `CLASH_STARTED`, `ROUND_COMPLETED`.

---

## 34, 35, 36, 37 & 38. DETERMINISTIC FLOW & DEFINITION OF DONE
- Fully automated testable simulation verifying round transitions, speaker permissions, cross-exam micro-protocols, clash tracking, score lineage, and complete match execution from Round 0 to Round 10.
