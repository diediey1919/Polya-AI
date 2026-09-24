# DEBATE ARENA — PROMPT 9

DEBATE REPLAY + ANALYTICS ENGINE

STATUS

LOCKED SYSTEM SPECIFICATION

This layer extends and consumes:

1. "01_DEBATE_CORE_CONSTITUTION.md"
2. "02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md"
3. "03_DEBATE_ROUND_ENGINE_RULES.md"
4. "04_DEBATE_MODERATOR_REFEREE_ENGINE.md"
5. "05_DEBATE_JUDGE_SCORING_ENGINE.md"
6. "06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md"
7. "07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md"
8. "08_DEBATE_AI_COMMENTARY_ENGINE.md"

Do not modify the authority or behavior of previous layers.

Prompt 9 is an observability, reconstruction, replay, and post-match intelligence layer.

It must never become the authority over:

- Event State
- Referee
- Score
- Judge
- Evidence
- Argument Graph
- Clash Graph
- Momentum

---

1. CORE PRINCIPLE

A completed debate must be reconstructable from its immutable event history.

The system must answer:

«What happened?»

«When did it happen?»

«Who did it?»

«What argument did it affect?»

«What evidence supported or challenged it?»

«Which clash did it affect?»

«Did momentum change?»

«What did the judges evaluate?»

«How did the final result emerge?»

The system must not merely store a transcript.

It must store the causal structure of the debate.

---

2. REPLAY ARCHITECTURE

Primary source:

IMMUTABLE EVENT LOG
        ↓
REPLAY ENGINE
        ↓
STATE RECONSTRUCTION
        ↓
ARGUMENT GRAPH
        ↓
CLASH GRAPH
        ↓
MOMENTUM TIMELINE
        ↓
EVIDENCE HISTORY
        ↓
COMMENTARY HISTORY
        ↓
JUDGE / SCORE HISTORY
        ↓
ANALYTICS

The immutable event log remains the historical source of truth.

Derived analytics must be rebuildable.

---

3. EVENT LOG IS AUTHORITATIVE

Never use a derived analytics table as the sole source of truth.

For example:

momentum_snapshot
score_snapshot
clash_snapshot
argument_snapshot

are derived representations.

They must be reconstructable from authoritative events.

---

4. REPLAY MODES

Support at minimum:

FULL_REPLAY
ROUND_REPLAY
CLASH_REPLAY
ARGUMENT_REPLAY
EVIDENCE_REPLAY
MOMENTUM_REPLAY
SCORE_REPLAY
COMMENTARY_REPLAY

---

5. FULL REPLAY

Full replay reconstructs the entire debate from:

SETUP
→
TOPIC LOCK
→
ROUND 1
→
...
→
VERDICT
→
ARCHIVE

The replay must preserve event order.

---

6. ROUND REPLAY

Allow replay of a specific round.

Example:

ROUND 5 — REBUTTAL

The replay should include only events relevant to that round while preserving required historical context.

---

7. ARGUMENT REPLAY

Selecting:

PRO-ARG-004

must show:

INTRODUCED
↓
SUPPORTED
↓
ATTACKED
↓
DEFENDED
↓
REBUILT
↓
RESOLVED / UNRESOLVED

with all relevant evidence and clashes.

---

8. CLASH REPLAY

Selecting:

CLASH-003

must show:

CLASH CREATED
↓
PROPOSITION POSITION
↓
OPPOSITION POSITION
↓
ATTACKS
↓
DEFENSES
↓
EVIDENCE CHANGES
↓
ADVANTAGE CHANGES
↓
FINAL CLASH STATUS

---

9. EVIDENCE REPLAY

Selecting a claim or evidence item must show:

CLAIM INTRODUCED
↓
SOURCE PROVIDED
↓
VERIFICATION REQUEST
↓
VERIFICATION RESULT
↓
STATUS CHANGES
↓
RELATED ARGUMENT
↓
RELATED CLASH
↓
JUDGE IMPACT

Do not invent missing transitions.

---

10. MOMENTUM REPLAY

The replay must visualize:

TIME / ROUND
        ↓
MOMENTUM
        ↓
SIGNIFICANT EVENT
        ↓
REASON FOR CHANGE

Every major movement must have a source event.

---

11. SCORE REPLAY

The score timeline must reconstruct:

SPEAKER EVENT
↓
EVALUATION EVENT
↓
RUBRIC CATEGORY
↓
DELTA
↓
RUNNING TOTAL

The replay must distinguish:

SUBSTANTIVE SCORE
PROCEDURAL PENALTY

Never merge them into an unexplained number.

---

12. COMMENTARY REPLAY

For every commentary event:

Show:

COMMENTARY
↓
TRIGGER EVENT
↓
ARGUMENT / CLASH / EVIDENCE CONTEXT
↓
MOMENTUM CONTEXT

The viewer must be able to understand why the commentary appeared.

---

13. EVENT-BY-EVENT TIMELINE

Create an interactive timeline.

Each event should expose:

timestamp
round
event_type
actor
team
speaker
summary
source_refs
target_refs
strategic_impact

Examples:

CLAIM_CREATED
ARGUMENT_CREATED
EVIDENCE_ADDED
ATTACK_CREATED
DEFENSE_CREATED
REBUTTAL_CREATED
CLASH_ACTIVATED
CLASH_ADVANTAGE_CHANGED
MOMENTUM_SHIFT
RULE_WARNING
RULE_PENALTY
SCORE_UPDATE
COMMENTARY_PUBLISHED
VERDICT_ANNOUNCED

---

14. EVENT FILTERS

Support filters by:

ROUND
TEAM
SPEAKER
EVENT TYPE
ARGUMENT
CLASH
EVIDENCE
SCORE CATEGORY
COMMENTARY
REFEREE EVENT

---

15. TIMELINE NAVIGATION

The replay interface should support:

PLAY
PAUSE
RESUME
STEP FORWARD
STEP BACKWARD
JUMP TO EVENT
JUMP TO ROUND
JUMP TO CLASH
JUMP TO TURNING POINT

---

16. REPLAY SPEED

Support:

0.25x
0.5x
1x
2x
4x
8x

Replay speed changes presentation only.

It must not alter reconstructed state.

---

17. STATE CHECKPOINTS

The replay engine may create checkpoints.

Example:

ROUND_START
ROUND_END
MAJOR_CLASH_CHANGE
MAJOR_MOMENTUM_SHIFT
VERDICT

Checkpoints improve performance.

They remain derived data.

---

18. CHECKPOINT VALIDATION

Any checkpoint must be reproducible from immutable events.

If:

CHECKPOINT != REPLAY_RESULT

mark the checkpoint invalid.

Do not silently repair it.

---

19. CAUSAL EVENT CHAIN

Important events should maintain causal references.

Example:

EVIDENCE-023
↓
supports
↓
PRO-ARG-007
↓
affects
↓
CLASH-002
↓
changes
↓
MOMENTUM-EVENT-014
↓
evaluated_by
↓
JUDGE-B-EVENT-031

This is the Debate Causal Chain.

---

20. CAUSAL GRAPH

Create a derived causal graph.

Supported relationships may include:

CAUSED
SUPPORTED
ATTACKED
DEFENDED
AFFECTED
TRIGGERED
RESPONDED_TO
EVALUATED
RESULTED_IN

Every causal link must reference actual events.

---

21. TURNING POINT ENGINE

Replay Analytics must identify important turning points.

Potential signals:

CENTRAL ARGUMENT COLLAPSE
MAJOR REBUILD
DECISIVE EVIDENCE
IMPORTANT CONCESSION
SUCCESSFUL CENTRAL REBUTTAL
CRITICAL CLASH REVERSAL
MAJOR MOMENTUM REVERSAL

---

22. TURNING POINT SCORE

Create a configurable analytical importance score.

Example conceptual model:

Turning Point Importance =
Argument Impact
+
Clash Impact
+
Evidence Impact
+
Momentum Impact
+
Strategic Centrality

Normalize to:

0–100

This score is analytical only.

It does not modify official judging.

---

23. TURNING POINT VALIDATION

A turning point must reference:

- source event
- affected argument
- affected clash where applicable
- momentum state where applicable
- confidence

No narrative-only turning points.

---

24. DEBATE SUMMARY ENGINE

After completion generate:

EXECUTIVE SUMMARY

Include:

- motion
- teams
- winner
- final score
- score margin
- decisive clashes
- major arguments
- evidence developments
- turning points
- strongest rebuttals
- major concessions
- unresolved questions

---

25. WIN REASON DECOMPOSITION

Do not simply output:

«"Proposition won."»

Instead reconstruct:

WIN
↓
DECISIVE CLASHES
↓
ARGUMENT PERFORMANCE
↓
EVIDENCE QUALITY
↓
REBUTTAL PERFORMANCE
↓
JUDGE EVALUATION
↓
FINAL RESULT

---

26. WIN REASON AUDIT

Every claimed reason for victory must reference actual adjudication data.

Example:

Reason:
Proposition won Clash-002.

Evidence:
CLASH-002 final status
Judge A evaluation
Judge B evaluation
Judge C evaluation

---

27. COUNTERFACTUAL ANALYSIS

Support optional analytical questions such as:

«"What would have changed if this argument had been successfully rebutted?"»

This must be clearly labeled:

COUNTERFACTUAL

It is not part of official adjudication.

Do not alter historical results.

---

28. COUNTERFACTUAL ISOLATION

Counterfactual simulations must run on a copy of reconstructed state.

Never mutate:

IMMUTABLE EVENT LOG
OFFICIAL SCORE
OFFICIAL VERDICT

---

29. INDIVIDUAL DEBATER ANALYTICS

Generate per-debater analysis:

ARGUMENT QUALITY
EVIDENCE
REASONING
REBUTTAL
CROSS-EXAM
RESPONSIVENESS
CLARITY
STRATEGY
TEAM CONTRIBUTION

These must map to the locked scoring rubric.

---

30. SPEAKER PERFORMANCE TIMELINE

For each debater:

ROUND
↓
ACTION
↓
ARGUMENT
↓
RESPONSE
↓
SCORE EVENT
↓
STRATEGIC EFFECT

---

31. TEAM PERFORMANCE ANALYTICS

Analyze:

CASE COHERENCE
ARGUMENT CONTINUITY
EVIDENCE INTEGRATION
REBUTTAL COORDINATION
ROLE COMPLEMENTARITY
CONSISTENCY
TEAM SYNERGY

Do not calculate team quality merely as:

(P1 + P2 + P3) / 3

Team performance remains independently evaluated.

---

32. CROSS-EXAM ANALYTICS

Post-debate analytics should show:

- strongest questions
- strongest answers
- unanswered questions
- evasive responses
- successful follow-ups
- exposed inconsistencies
- evidence pressure
- strategic consequences

---

33. EVIDENCE ANALYTICS

Generate:

TOTAL CLAIMS
VERIFIED
PARTIALLY VERIFIED
UNVERIFIED
CONTRADICTED
OUTDATED
MISREPRESENTED

Also show:

SOURCE QUALITY
PROVENANCE
RELEVANCE
CLAIM MATCH
CONTEXT

---

34. ARGUMENT ANALYTICS

Generate:

TOTAL ARGUMENTS
CORE ARGUMENTS
SUCCESSFUL ARGUMENTS
WEAKENED ARGUMENTS
COLLAPSED ARGUMENTS
REBUILT ARGUMENTS
ABANDONED ARGUMENTS
UNRESOLVED ARGUMENTS

---

35. CLASH ANALYTICS

For each critical clash:

QUESTION
PROPOSITION POSITION
OPPOSITION POSITION
ARGUMENTS
EVIDENCE
ATTACKS
DEFENSES
ADVANTAGE TIMELINE
FINAL STATUS
JUDGE RELEVANCE

---

36. MOMENTUM ANALYTICS

Generate:

STARTING STATE
PEAK PROPOSITION MOMENTUM
PEAK OPPOSITION MOMENTUM
MAJOR REVERSALS
TURNING POINTS
FINAL MOMENTUM

Important:

Final momentum is not necessarily the winner.

---

37. PRESSURE ANALYTICS

Show:

PRESSURE CREATED
PRESSURE ABSORBED
SUCCESSFUL PRESSURE
FAILED PRESSURE
CROSS-EXAM PRESSURE
REBUTTAL PRESSURE

---

38. STRATEGIC ADAPTATION REPORT

Identify changes such as:

POSITION NARROWING
ARGUMENT REBUILD
NEW EVIDENCE
TACTICAL CONCESSION
REBUTTAL STRATEGY CHANGE
CLASH PRIORITY CHANGE

---

39. DEBATE QUALITY REPORT

Create an overall analytical report:

EVIDENCE INTEGRITY
ARGUMENT QUALITY
LOGICAL QUALITY
RESPONSIVENESS
RULE COMPLIANCE
TEAM COHERENCE

Do not combine these into a fake "objective truth" score.

They remain separate dimensions.

---

40. FORENSIC AUDIT VIEW

Provide a forensic mode.

The user can inspect:

EVENT
→ SOURCE
→ DERIVED STATE
→ SCORE
→ COMMENTARY

Every important analytical conclusion should be traceable.

---

41. SCORE DISPUTE INSPECTION

If a score is questioned:

The system must be able to show:

SCORE
↓
RUBRIC CATEGORY
↓
EVALUATION EVENT
↓
SOURCE SPEECH
↓
ARGUMENT / EVIDENCE
↓
JUDGE

---

42. SCORE RECONSTRUCTION

Reconstruct score from immutable events.

Expected:

RECONSTRUCTED SCORE
=
ORIGINAL SCORE

with mathematical precision.

---

43. ANALYTICS RECONSTRUCTION

Clear all derived analytics.

Then replay.

Verify:

ARGUMENT GRAPH
=
ORIGINAL

CLASH GRAPH
=
ORIGINAL

MOMENTUM TIMELINE
=
ORIGINAL

COMMENTARY TRIGGERS
=
ORIGINAL

SCORE HISTORY
=
ORIGINAL

---

44. DETERMINISM

Given:

same immutable events
+
same configuration
+
same engine version

the derived state should be deterministic.

If an AI-generated narrative is non-deterministic, preserve its original output and source references.

---

45. VERSIONING

Every replay should record:

engine_version
rules_version
scoring_version
evidence_engine_version
analytics_version

This prevents confusion when engines evolve.

---

46. HISTORICAL COMPATIBILITY

If future engine versions change analytical calculations:

Do not silently rewrite historical official results.

Historical match data must preserve:

ORIGINAL OFFICIAL RESULT
ORIGINAL SCORE
ORIGINAL ENGINE VERSIONS

New analytics may be marked:

REANALYZED

---

47. PRIVACY / VISIBILITY

Separate:

PUBLIC
PARTICIPANT
JUDGE
ADMIN
FORENSIC

visibility.

Do not expose private judge deliberation or internal reasoning.

---

48. NO CHAIN-OF-THOUGHT STORAGE

Do not store or expose hidden model chain-of-thought.

Store only:

- evaluation result
- score
- confidence
- concise rationale
- source references

---

49. EXPORT

Support future export of:

JSON
CSV
PDF
MATCH REPORT
EVENT LOG
ANALYTICS REPORT

Exports must use reconstructed authoritative data.

---

50. API / MODULE BOUNDARY

Create a clean module boundary such as:

replay_engine.py
analytics_engine.py
causal_graph.py
turning_point_engine.py
debate_replay_service.py

Use the existing architecture where appropriate.

Do not duplicate existing engines.

---

51. PERFORMANCE

Replay must support large debates.

Do not recompute unnecessary state.

Use:

EVENT INDEX
CHECKPOINTS
INCREMENTAL RECONSTRUCTION
LAZY ANALYTICS

where appropriate.

---

52. FAILURE HANDLING

If one analytics module fails:

The official match record remains intact.

Example:

ANALYTICS_PARTIAL

The system must identify which analytics failed.

Never fabricate missing analytics.

---

53. TEST — FULL REPLAY

Run a complete simulated debate.

Save final derived state.

Clear derived state.

Replay from immutable events.

Compare all major state structures.

Expected:

100% MATCH

---

54. TEST — ROUND REPLAY

Replay each round independently.

Verify the correct event boundaries.

---

55. TEST — ARGUMENT REPLAY

Select several arguments.

Verify their entire lifecycle is reconstructed.

---

56. TEST — CLASH REPLAY

Select each critical clash.

Verify all attacks, defenses, evidence and advantage changes appear in chronological order.

---

57. TEST — EVIDENCE REPLAY

Select verified, unverified, contradicted and partially verified evidence.

Verify status transitions are preserved.

---

58. TEST — MOMENTUM REPLAY

Verify every significant momentum shift has a source event.

Attempt to create a momentum shift without a source event.

Expected:

REJECTED
INVALID_SOURCE_EVENT

---

59. TEST — SCORE REPLAY

Reconstruct all individual and team scores.

Verify:

LIVE SCORE
=
REPLAY SCORE

---

60. TEST — TURNING POINT

Create a major clash reversal.

Verify turning point detection references:

SOURCE EVENT
CLASH
ARGUMENT
MOMENTUM

---

61. TEST — WIN REASON AUDIT

After verdict:

Generate win explanation.

Verify every stated reason references actual adjudication data.

---

62. TEST — COUNTERFACTUAL ISOLATION

Run a hypothetical:

«"What if PRO-ARG-002 had failed?"»

Verify:

- hypothetical state changes
- official history unchanged
- official score unchanged
- official verdict unchanged

---

63. TEST — VERSIONING

Replay with a recorded engine version.

Verify the historical version is preserved.

---

64. TEST — FAILURE ISOLATION

Force Analytics Engine failure.

Verify:

- official event remains intact
- score remains intact
- verdict remains intact
- replay source remains intact
- failure is explicitly recorded

---

65. TEST — FULL FORENSIC CHAIN

Verify:

SPEECH
↓
CLAIM
↓
EVIDENCE
↓
ARGUMENT
↓
ATTACK
↓
DEFENSE
↓
CLASH
↓
MOMENTUM
↓
COMMENTARY
↓
JUDGE
↓
SCORE
↓
VERDICT
↓
ANALYTICS

Every stage must remain traceable.

---

66. DEFINITION OF DONE

Prompt 9 is complete only when:

- full replay works
- round replay works
- argument replay works
- clash replay works
- evidence replay works
- momentum replay works
- score replay works
- commentary replay works
- event timeline exists
- causal graph exists
- turning points are traceable
- win reasons are auditable
- individual analytics exist
- team analytics exist
- cross-exam analytics exist
- evidence analytics exist
- argument analytics exist
- clash analytics exist
- momentum analytics exist
- pressure analytics exist
- strategic adaptation analytics exist
- forensic audit exists
- score reconstruction works
- derived-state reconstruction works
- versioning works
- historical results remain immutable
- counterfactual analysis is isolated
- failure isolation works
- no hidden chain-of-thought is stored
- all previous test suites remain green

---

FINAL DIRECTIVE

The fundamental rule remains:

EVENT LOG → REPLAY → ANALYTICS

not:

AI narrative → reconstructed history.

The history must always come first.
