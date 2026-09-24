# DEBATE ARENA — MODERATOR & REFEREE ENGINE

## STATUS
LOCKED SYSTEM SPECIFICATION

This document defines the operational behavior of:
1. **MODERATOR ENGINE**
2. **REFEREE ENGINE**

It extends:
- `01_DEBATE_CORE_CONSTITUTION.md`
- `02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md`
- `03_DEBATE_ROUND_ENGINE_ROUND_RULES.md`

Do not modify the authority hierarchy established by those documents.

---

## 1. CORE PRINCIPLE

The Moderator and Referee are separate functional responsibilities:
- **MODERATOR**: Controls event communication and procedural flow.
- **REFEREE**: Enforces rules, validates compliance, and adjudicates procedural violations.

Neither is a debate participant. Neither argues for either team. Neither determines the substantive winner by personal opinion.

---

## 2. AUTHORITY HIERARCHY

```
EVENT CONSTITUTION
        ↓
EVENT STATE ENGINE
        ↓
ROUND ENGINE
        ↓
ROUND RULES
        ↓
SPEAKER PERMISSIONS
        ↓
REFEREE
        ↓
MODERATOR
        ↓
COMMENTARY / PRESENTATION
```

---

## 3 & 4 & 5. MODERATOR ENGINE & DISCIPLINE
- **Responsibilities**: Open event, announce locked topic, introduce teams, explain rules, announce rounds/speakers, issue time warnings, manage interruptions neutrally, announce deliberation and verdict.
- **Prohibitions**: Never argue for either side, coach speakers, invent arguments, reveal hidden judge scores, or declare winners before deliberation.
- **Communication Style**: Authoritative, concise, neutral, professional broadcast style without conversational chatbot fluff.

---

## 6 to 14. PROCEDURAL ANNOUNCEMENTS & TIME MANAGEMENT
- **Event Opening & Topic**: Exact locked motion stated clearly without subjective paraphrasing.
- **Team Introduction**: Proposition (P1, P2, P3) & Opposition (C1, C2, C3) introduced with equal parity.
- **Rule Briefing**: Formally states time limits, cross-ex micro-protocol, interruption rules, and scoring rubrics.
- **Speaker Introduction**: Neutral floor assignment ("Proposition P1, you have the floor").
- **Time Management**: Driven by Timer Engine events (`TIME_WARNING`, `TIME_EXPIRED`). Moderator does not count time manually.

---

## 15 to 20. CROSS-EX, RELEVANCE, REPETITION & EVIDENCE REQUESTS
- **Cross-Ex Moderation**: Enforces time, turn, and follow-up count without answering or coaching.
- **Relevance / Repetition**: Neutral redirection ("Please address the question directly", "Please advance the argument").
- **Evidence Requests**: Procedural prompt to cite sources; fact checking is delegated to Fact Checker / Evidence Engine.

---

## 21 to 30. REFEREE ENGINE & VIOLATION MANAGEMENT
- **Responsibilities**: Validates actions, verifies speaker permissions, classifies violations, determines procedural penalties, logs violations, and maintains match integrity.
- **Violation Classification**: `SPEAKER_PERMISSION`, `TIME`, `INTERRUPTION`, `RELEVANCE`, `CONDUCT`, `EVIDENCE_PROCEDURE`, `FORMAT`.
- **Severity & Escalation**: `MINOR` $\rightarrow$ `MODERATE` $\rightarrow$ `MAJOR` $\rightarrow$ `SEVERE`; Escalation: `WARNING` $\rightarrow$ `FORMAL_WARNING` $\rightarrow$ `PENALTY` $\rightarrow$ `ESCALATION`.
- **Score Separation**: Procedural penalties are tracked separately in an explicit audit event and NEVER silently conflated with substantive argument scoring.

---

## 31, 32 & 33. STRICT ROLE SEPARATION
- **EVENT ENGINE**: What is happening?
- **MODERATOR**: How is it communicated?
- **REFEREE**: Is it allowed?
- **JUDGE**: How good was it?
- **FACT CHECKER**: Is the claim supported?
- **COMMENTATOR**: What does it mean strategically?

---

## 34 to 42. INTERVENTION LOGGING & PIPELINE
- Pipeline: `ACTION → REFEREE VALIDATION → DECISION → MODERATOR COMMUNICATION`.
- Structured Intervention Record: `intervention_id`, `timestamp`, `state`, `round`, `speaker`, `team`, `type`, `reason`, `severity`, `rule_id`, `action_taken`, `score_effect`.

---

## 43 to 53. PUBLIC VS PRIVATE DATA & AUDIT INTEGRITY
- **Public**: Speaker, round, timer, procedural warnings, public evidence requests, moderator statements, live commentary.
- **Private (Judge Layer)**: Raw micro-scores, internal confidence, judge reasoning, multi-judge deliberations.

---

## 54, 55, 56 & 57. ADVERSARIAL TESTING & DEFINITION OF DONE
- All invalid speaker actions, illegal interruptions, expired timer overruns, illegal state jumps, and topic tampering attempts must be deterministically rejected and logged.
