# DEBATE ARENA — JUDGE & SCORING ENGINE

## STATUS
LOCKED SYSTEM SPECIFICATION

This document defines the official adjudication and scoring architecture of Debate Arena.
It extends:
- `01_DEBATE_CORE_CONSTITUTION.md`
- `02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md`
- `03_DEBATE_ROUND_ENGINE_ROUND_RULES.md`
- `04_DEBATE_MODERATOR_REFEREE_ENGINE.md`

This document defines: **HOW DEBATE PERFORMANCE IS EVALUATED AND HOW THE OFFICIAL RESULT IS PRODUCED.**

---

## 1. CORE PRINCIPLE
The Scoring Engine evaluates debate performance quality—never ideology, speaker identity, or personal preference:
$$\text{ARGUMENT QUALITY} + \text{EVIDENCE} + \text{REASONING} + \text{RESPONSIVENESS} + \text{REBUTTAL} + \text{CROSS-EX} + \text{STRATEGY} + \text{TEAM CONTRIBUTION} + \text{COMPLIANCE}$$

---

## 2 & 3. THREE INDEPENDENT JUDGES
- **JUDGE A (Logic & Argument)**: Premise validity, causal inference, internal coherence, argument structures, and clash handling.
- **JUDGE B (Evidence & Factuality)**: Factual accuracy, source quality, manuscript citations, claim match, and evidentiary integrity.
- **JUDGE C (Strategy & Responsiveness)**: Directness of answers, rebuttal effectiveness, cross-ex pressure, prioritization, and team coordination.
- **Independence Principle**: Judges evaluate independently without seeing each other's scores before aggregation to eliminate correlated bias.

---

## 4 & 5. GLOBAL INDIVIDUAL SCORE (100 POINTS MAX)
- Argument Quality: **20**
- Evidence & Factuality: **15**
- Logical Reasoning: **15**
- Rebuttal: **15**
- Cross Examination: **10**
- Responsiveness: **10**
- Clarity & Structure: **5**
- Debate Strategy: **5**
- Team Contribution: **5**
- **TOTAL: 100 POINTS**

---

## 6 to 12. MICRO-SCORING, NORMALIZATION, CAPS & ANTI-DOUBLE-COUNTING
- Meaningful events generate micro-evaluations (`category`, `raw_score`, `confidence`, `reason`, `event_ref`).
- Micro-scores are normalized into category contributions up to category caps.
- **Anti-Double-Counting**: A single factual error affects Evidence/Factuality, not every category indiscriminately.
- Monotonicity: Penalties require unique event references.

---

## 13 to 27. CATEGORY EVALUATION STANDARDS
- **Evidence**: Source quality, claim match, context, recency, avoidance of cherry-picking.
- **Logic**: Premise support, valid inferences, absence of non-sequiturs.
- **Rebuttal**: Targeted vulnerability, counter-evidence, consequence explanation, case reinforcement.
- **Cross-Examination**: Question relevance/precision, answer directness/consistency under pressure.
- **Fallacies**: Evaluated contextually (`MINOR: -0.5`, `MODERATE: -1.0`, `MAJOR: -2.0`, `SEVERE: -4.0`).
- **Evasion & Repetition**: Deductions applied specifically to Responsiveness / Strategy without global corruption.

---

## 28 & 29. SEPARATION OF PROCEDURAL PENALTIES
- Substantive Argument Scores and Procedural Violation Penalties remain completely separate in the audit log.
$$\text{FINAL ADJUSTED SCORE} = \text{SUBSTANTIVE BASE SCORE} - \text{AUTHORIZED PROCEDURAL PENALTIES}$$

---

## 31, 32 & 33. INDEPENDENT TEAM SCORE (100 POINTS MAX)
Team score evaluates team performance as a coordinated unit, NOT an arithmetic average of individual debaters:
- Team Case Strength: **20**
- Team Coherence: **15**
- Team Strategy: **15**
- Team Synergy: **15**
- Clash Performance: **15**
- Evidence Integration: **10**
- Rebuttal Coordination: **10**
- **TOTAL: 100 POINTS**

---

## 34 to 45. SCORE AGGREGATOR & DETERMINISTIC VERDICT
- Combines Judge A, B, C evaluations + Team Analysis + Procedural Adjustments.
- Preserves judge disagreement, flags outliers (`OUTLIER_DETECTED`), tracks evaluation confidence.
- Runs position-neutrality / swap tests to eliminate systematic ideological or positional bias.

---

## 46, 47 & 48. AUDITABILITY & RECONSTRUCTIBILITY
- Every score delta is immutable with reason, judge source, timestamp, confidence, and evidence reference.
- The final match score must be 100% reconstructible from the sequential score event log.

---

## 49 to 55. VERDICT, MARGIN, CLOSE MATCHES & AWARDS
- Official Adjudication output: Winner, Margin, Key Clash Results, Decisive Turning Point.
- Awards: Winning Team, Best Debater, Best Argument, Best Rebuttal, Best Evidence, Best Cross-Ex.
- Audience poll displays remain strictly informational and cannot override judge adjudication.
