# DEBATE ARENA — EVENT STATE ENGINE & DEBATE PROTOCOL

## STATUS
LOCKED SYSTEM SPECIFICATION

This document defines how a Debate Arena match actually operates.
It is the operational layer below: `01_DEBATE_CORE_CONSTITUTION.md`

The Constitution defines what Debate Arena is.
This document defines: **HOW THE DEBATE RUNS.**

Do not merge this document into the Core Constitution.
Treat both documents as separate but connected system layers.

---

## 1. CORE ARCHITECTURE

Debate Arena must operate as an explicit event-driven system.
The fundamental hierarchy is:

```
DEBATE CONSTITUTION
        ↓
EVENT PROTOCOL
        ↓
STATE MACHINE
        ↓
ROUND CONFIGURATION
        ↓
SPEAKER PERMISSIONS
        ↓
AI ROLE INSTRUCTIONS
        ↓
LIVE EVENT CONTEXT
        ↓
AI OUTPUT / SYSTEM ACTION
```

The AI must never determine the event state by itself.
The Event Engine is authoritative.

---

## 2. SINGLE SOURCE OF TRUTH

The Event State Engine is the authoritative source for:
- current event state
- current round
- current phase
- current speaker
- active team
- speaker permissions
- remaining time
- allowed actions
- prohibited actions
- next valid transition
- event status

AI interpretation must never override Event Engine state.
If an AI response conflicts with the Event Engine: **EVENT ENGINE WINS.**

---

## 3. EVENT STATES

The standard Debate Arena lifecycle is:

```
SETUP
↓
TOPIC_LOCK
↓
TEAM_READY
↓
INTRODUCTION
↓
RULE_BRIEFING
↓
OPENING
↓
CONSTRUCTIVE
↓
EVIDENCE_ARGUMENT
↓
CROSS_EXAMINATION
↓
REBUTTAL
↓
CLASH_ROUND
↓
FINAL_REBUTTAL
↓
CLOSING
↓
DELIBERATION
↓
VERDICT
↓
POST_DEBATE_ANALYSIS
↓
ARCHIVE
```

Every state must be represented explicitly in the application.
Do not implement the debate as a collection of loosely connected screens.

---

## 4. STATE MACHINE REQUIREMENT

Every state must define:
- `STATE_ID`
- `PURPOSE`
- `ENTRY_CONDITIONS`
- `ACTIVE_TEAM`
- `ACTIVE_SPEAKER`
- `ALLOWED_ACTIONS`
- `FORBIDDEN_ACTIONS`
- `TIME_RULE`
- `MODERATOR_AUTHORITY`
- `SCORING_MODE`
- `EXIT_CONDITIONS`
- `NEXT_VALID_STATES`

---

## 5. STATE TRANSITION RULE

State transitions must be deterministic.
A state can only transition when its exit conditions are satisfied.
AI may recommend a transition. AI must not silently execute an invalid transition.

---

## 6. EVENT STATE OBJECT

The application maintains a structured event state:
- `event_id`
- `topic`
- `status`
- `current_state`
- `current_round`
- `current_team`
- `current_speaker`
- `speaker_role`
- `turn_index`
- `remaining_time`
- `round_time`
- `allowed_actions`
- `active_clash`
- `active_arguments`
- `active_claims`
- `active_evidence`
- `score_state`
- `moderator_state`
- `event_flags`

---

## 7. EVENT FLAGS

The engine supports event flags:
- `TIME_WARNING`
- `TIME_EXPIRED`
- `RULE_VIOLATION`
- `RELEVANCE_WARNING`
- `REPETITION_WARNING`
- `EVASION_DETECTED`
- `EVIDENCE_CHALLENGE`
- `FACT_CHECK_REQUIRED`
- `MODERATOR_INTERVENTION`
- `SPEAKER_CHANGE`
- `ROUND_COMPLETE`
- `CLASH_UPDATED`
- `SCORING_EVENT`

Flags are event signals; they do not automatically determine the winner.

---

## 8. SETUP
- Prepare match: topic, teams (Proposition P1-P3, Opposition C1-C3), assignments, time, ruleset, scoring, AI configuration.
- No debate speech allowed.

## 9. TOPIC LOCK
- Topic fixed, definitions established, positions locked.
- Changes require explicit admin reset. AI cannot alter the motion.

## 10. TEAM READY
- Verify all 6 speakers present, positions fixed, configuration loaded.

## 11. INTRODUCTION
- Host introduces event, topic, teams, speakers, format neutrally without arguments.

## 12. RULE BRIEFING
- Moderator explains format, speaking order, time limits, cross-ex rules, interruption rules, evidence rules, scoring principles, conduct rules, adjudication.

## 13. OPENING
- P1 & C1 establish framing, definitions, thesis, core case, strategic direction. Interruption forbidden unless explicitly allowed.

## 14. CONSTRUCTIVE
- P2 & C2 develop substantive case, reasoning, supporting evidence, team case connection. AI tracks argument units.

## 15. EVIDENCE & ARGUMENT
- Substantive reasoning & evidence recorded (claims, arguments, premises, reasoning, evidence, impacts). Handled by Evidence Engine.

## 16 & 17. CROSS EXAMINATION & PERMISSIONS
- Controlled protocol: QUESTIONER → QUESTION → RESPONDENT → ANSWER → QUESTIONER → FOLLOW-UP → RESPONDENT → RESPONSE.
- Engine controls speaker turn, permitted actions, time, interruption rules.

## 18. REBUTTAL
- Direct engagement with target argument/claim/evidence/clash.

## 19. CLASH ROUND
- Focus on central decisive clashes. Moderator directs focus toward unresolved disputes without taking positions.

## 20. FINAL REBUTTAL
- Final opportunity to answer major attacks, prioritize unresolved central arguments.

## 21. CLOSING
- Summarize case, strongest evidence, clash outcomes, final strategic framing. No major new material.

## 22. DELIBERATION
- Live debate closed. AI Judge layer independently evaluates 9 categories across Judges A, B, C. Isolated from debaters.

## 23. VERDICT
- Adjudication results: winning team, team score, individual scores, margin, clash results, key arguments, turning point, integrity score.

## 24. POST-DEBATE ANALYSIS
- Detailed analytical report, argument graph, fallacy report, unanswered arguments, momentum, team synergy, coaching recommendations.

## 25. ARCHIVE
- Immutable record of entire match, speeches, evidence, logs, scores.

---

## 26. SPEAKER PERMISSION MATRIX
Backend validates at all times:
- WHO MAY SPEAK?
- WHO MAY ASK?
- WHO MAY ANSWER?
- WHO MAY INTERRUPT?
- WHO MAY REQUEST CLARIFICATION?
- WHO MAY CHALLENGE?
- WHO MAY TRIGGER MODERATION?

---

## 27. ACTION VALIDATION
Every action passes: `ACTION → STATE CHECK → SPEAKER PERMISSION → TEAM CHECK → ROUND CHECK → TIME CHECK → VALIDATION → EXECUTE (or REJECT + REASON)`.

---

## 28 & 29. TIMER ENGINE & EXPIRATION
Authoritative backend event timer independent from AI generation. Emits `TIME_WARNING`, `TIME_EXPIRED`. Rules determine grace period / moderator trigger.

---

## 30 & 31. INTERRUPTIONS & MODERATOR AUTHORITY
Explicit points of order / clarification / challenges. Moderator controls flow, enforces rules, issues warnings, pauses/resumes, but NEVER argues or alters scores secretly.

---

## 32, 33 & 34. PAUSE/RESUME, ERROR RECOVERY, LATENCY ISOLATION
Pause preserves full state. AI latency or failures are treated as infrastructure events with retry/fallbacks—never corrupting event state or advancing clocks artificially.

---

## 35 & 36. CONFIGURABLE RULESET & EVENT COMMANDS
Declarative commands (`CREATE_EVENT`, `LOCK_TOPIC`, `START_ROUND`, `START_SPEECH`, `START_CROSS_EXAM`, `END_DEBATE`, `START_DELIBERATION`, `ISSUE_VERDICT`, etc.) validate against current state.

---

## 37 & 38. EVENT LOG & EVENT REPLAY
Deterministic event log enables full auditable replay and analytics reconstruction.

---

## 39 & 40. SECURITY & UI DERIVATION
Frontend state strictly derived from backend Event State Object. UI has no authority to alter state/scores/timer directly.

---

## 41, 42, 43, 44 & 45. AI CONTEXT BUILDER & ROLE PROMPT SEPARATION
AI calls receive structured contextual packages (`CORE_CONSTITUTION` + `EVENT_PROTOCOL` + `CURRENT_STATE` + `ROUND_RULES` + `ROLE_INSTRUCTION` + `RELEVANT_CONTEXT` + `PERSONA`). Higher layers override lower layers.

---

## 46, 47 & 48. NO NATURAL LANGUAGE STATE & PROFESSIONAL EVENT DISCIPLINE
State transitions are strictly executed by State Machine, not natural language suggestions.

---

## 49 & 50. IMPLEMENTATION STEPS & DEFINITION OF DONE
Complete state machine, speaker matrix, timer engine, event log, AI context builder, validation, error recovery, and event replay.
