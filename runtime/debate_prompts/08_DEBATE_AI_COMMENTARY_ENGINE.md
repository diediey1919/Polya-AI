# DEBATE ARENA — AI COMMENTARY ENGINE

STATUS

LOCKED SYSTEM SPECIFICATION

This document defines the AI Commentary Engine for Debate Arena.

It extends:

- "01_DEBATE_CORE_CONSTITUTION.md"
- "02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md"
- "03_DEBATE_ROUND_ENGINE_RULES.md"
- "04_DEBATE_MODERATOR_REFEREE_ENGINE.md"
- "05_DEBATE_JUDGE_SCORING_ENGINE.md"
- "06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md"
- "07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md"

Do not modify the authority of previous layers.

---

1. CORE PRINCIPLE

The AI Commentator is a neutral broadcast analyst.

It explains what is happening strategically.

It does not participate in the debate.

It does not control the event.

It does not enforce rules.

It does not fact-check independently.

It does not judge the official winner.

It does not coach participants.

Its role is:

OBSERVE
↓
INTERPRET
↓
EXPLAIN
↓
BROADCAST

---

2. COMMENTATOR ROLE

The Commentator explains:

- important arguments
- attacks
- defenses
- critical clashes
- evidence developments
- strategic adaptations
- momentum changes
- turning points
- unanswered arguments
- concessions
- pressure
- team coordination

The Commentator translates complex analytical state into concise human-readable broadcast commentary.

---

3. STRICT ROLE SEPARATION

The architecture must preserve:

EVENT ENGINE
= controls the match

MODERATOR
= controls procedural communication

REFEREE
= enforces rules

FACT CHECKER
= verifies claims/evidence

ARGUMENT ENGINE
= maps arguments

CLASH ENGINE
= maps strategic disputes

MOMENTUM ENGINE
= tracks competitive movement

JUDGE
= evaluates performance

SCORE ENGINE
= calculates scores

COMMENTATOR
= explains strategic developments

No component may silently become another component.

---

4. COMMENTATOR MUST NEVER

The Commentator must never:

- argue for Proposition
- argue for Opposition
- suggest what a participant should say
- provide a rebuttal on behalf of a participant
- introduce new arguments
- invent evidence
- invent facts
- alter scores
- alter momentum
- alter clash status
- alter event state
- change speaker permissions
- interrupt the debate
- issue referee decisions
- announce hidden judge scores
- declare the official winner before adjudication

---

5. COMMENTARY IS READ-ONLY

The Commentary Engine operates against analytical state.

Conceptually:

ARGUMENT GRAPH
+
CLASH GRAPH
+
EVIDENCE STATE
+
MOMENTUM STATE
+
EVENT STATE
↓
COMMENTARY ENGINE
↓
COMMENTARY

The Commentary Engine must be read-only against the authoritative event state.

It cannot mutate:

- arguments
- claims
- evidence
- clashes
- scores
- momentum
- timer
- speaker state
- event state

---

6. COMMENTARY SOURCES

The Commentator may consume:

CURRENT ROUND
CURRENT SPEAKER
RECENT SPEECH
ARGUMENT GRAPH
CLAIM REGISTRY
EVIDENCE STATUS
CRITICAL CLASHES
MOMENTUM
PRESSURE
UNANSWERED ARGUMENTS
CONCESSIONS
TEAM SYNERGY
REFEREE PUBLIC EVENTS

Only data relevant to the current commentary should be injected.

---

7. NO RAW FULL-TRANSCRIPT DEPENDENCY

Do not send the entire debate transcript to every commentary request.

Prefer:

CURRENT EVENT
+
CURRENT ROUND
+
RECENT EVENTS
+
RELEVANT ARGUMENTS
+
ACTIVE CLASH
+
MOMENTUM SNAPSHOT
+
EVIDENCE DEVELOPMENTS

Use historical context only when needed.

---

8. COMMENTARY TYPES

Support at minimum:

OPENING_COMMENTARY
ROUND_COMMENTARY
ARGUMENT_COMMENTARY
EVIDENCE_COMMENTARY
CROSS_EXAM_COMMENTARY
REBUTTAL_COMMENTARY
CLASH_COMMENTARY
MOMENTUM_COMMENTARY
TURNING_POINT_COMMENTARY
TEAM_COMMENTARY
TRANSITION_COMMENTARY
POST_ROUND_COMMENTARY
FINAL_ANALYSIS

---

9. OPENING COMMENTARY

At event opening:

The Commentator may explain:

- what the motion concerns
- what the broad strategic landscape is
- what major questions are likely to matter

It must not predict a winner.

Example:

«"The central dispute appears likely to involve both the policy's effectiveness and the cost of implementation."»

Avoid:

«"Proposition has the stronger case."»

before substantive debate exists.

---

10. ROUND COMMENTARY

During a round, Commentary may explain:

- what the current round is testing
- why the current exchange matters
- what strategic question is being examined

Example:

«"This cross-examination is testing the assumption underlying Proposition's central economic argument."»

---

11. ARGUMENT COMMENTARY

When a meaningful argument appears:

The Commentator may explain:

- what the argument claims
- what premise it relies on
- why it matters
- which existing argument it supports or attacks

Example:

«"P2 has moved the discussion from whether the policy is effective to whether its benefits justify the implementation cost."»

The Commentator must reference actual argument state.

---

12. ATTACK COMMENTARY

When one argument attacks another:

Explain:

ATTACKER
↓
TARGET
↓
ATTACK TYPE
↓
STRATEGIC SIGNIFICANCE

Example:

«"C2 is attacking the causal premise of P1's argument rather than disputing the underlying statistic."»

Do not invent a stronger attack than the speaker actually made.

---

13. DEFENSE COMMENTARY

When an argument is defended:

Explain:

- what was defended
- how it was defended
- whether the defense changed scope
- whether new evidence was introduced
- whether the original argument was rebuilt

Example:

«"P3 has narrowed the claim, limiting it to the population represented in the cited study."»

---

14. EVIDENCE COMMENTARY

The Commentator may describe evidence developments.

Example:

«"The evidence supporting that claim has now been verified for the stated region, but the speaker's broader national conclusion remains unsupported."»

This commentary must derive from Evidence Engine output.

Do not independently fact-check.

---

15. EVIDENCE UNCERTAINTY

If evidence is uncertain:

Use language such as:

«"The claim remains unverified."»

or:

«"The available evidence is contested."»

Never say:

«"This claim is definitely false."»

unless the Evidence Engine has explicitly established a sufficiently strong contradicted status and public display rules permit that wording.

---

16. CROSS-EXAM COMMENTARY

Commentary should focus on strategic pressure.

Possible observations:

- question targets central premise
- response directly answers
- response changes scope
- question exposes inconsistency
- respondent successfully defends assumption
- follow-up increases pressure

Example:

«"P3's follow-up keeps the exchange focused on the same causal assumption rather than allowing the discussion to move elsewhere."»

---

17. CROSS-EXAM NO COACHING

Bad:

«"P3 should now ask whether C1 has evidence."»

Good:

«"The exchange has not yet resolved the evidence supporting C1's claim."»

The first coaches.

The second analyzes.

---

18. REBUTTAL COMMENTARY

Explain whether a rebuttal appears to address:

- central premise
- evidence
- inference
- scope
- impact
- consistency

Example:

«"That rebuttal targets the conclusion, but the underlying premise remains largely untouched."»

Do not assign official score.

---

19. CLASH COMMENTARY

When a Critical Clash becomes active:

Explain:

- the central question
- each team's position
- why the clash matters
- what evidence or arguments currently affect it

Example:

«"The central clash has shifted from whether regulation is necessary to whether its economic cost is proportionate to the claimed safety benefit."»

---

20. CLASH NEUTRALITY

Do not phrase commentary as advocacy.

Avoid:

«"Proposition finally destroyed the Opposition's argument."»

Prefer:

«"The Opposition's original premise has now been directly challenged and remains unresolved."»

The Commentator can describe strategic advantage when sufficiently supported.

---

21. MOMENTUM COMMENTARY

Momentum may be described when a meaningful change occurs.

Example:

«"This exchange appears to have shifted the debate's strategic balance because the Opposition has now forced a qualification of Proposition's central claim."»

Do not equate momentum with probability of victory.

Never say:

«"Proposition now has an 80% chance of winning."»

unless a separate explicitly configured prediction system exists.

---

22. MOMENTUM THRESHOLD

Do not generate commentary for every tiny momentum fluctuation.

Only significant changes should trigger commentary.

Use configurable thresholds.

Example:

MINOR SHIFT
→ silent

MODERATE SHIFT
→ optional commentary

MAJOR SHIFT
→ commentary candidate

TURNING POINT
→ high-priority commentary

---

23. TURNING POINT COMMENTARY

A turning point must reference an actual event.

Structure:

WHAT HAPPENED
↓
WHAT CHANGED
↓
WHY IT MATTERS

Example:

«"The turning point came when C3 challenged the evidence underlying Proposition's second argument. The argument has since been qualified, changing the structure of the first critical clash."»

Do not manufacture drama.

---

24. TEAM COMMENTARY

The Commentator may analyze coordination.

Example:

«"P1 established the premise, P2 supplied the supporting evidence, and P3 has now defended that same line under cross-examination."»

Or:

«"The team's arguments have begun to diverge, with C2 pursuing a different premise from the one established by C1."»

Team commentary must be based on Argument Graph and Team Analysis.

---

25. TEAM SYNERGY

Do not equate:

more speaking
=
better teamwork

Evaluate:

- continuity
- complementarity
- reinforcement
- coordinated rebuttal
- consistency

---

26. UNANSWERED ARGUMENT COMMENTARY

If a central argument remains unanswered:

The Commentator may state:

«"The central argument remains without a direct response at this stage."»

Do not state:

«"That means Opposition has lost."»

Unanswered arguments remain subject to adjudication.

---

27. CONCESSION COMMENTARY

When a participant concedes something:

Explain the strategic significance.

Example:

«"P2 has conceded the short-term implementation cost while maintaining that the long-term benefit justifies it."»

A concession is not automatically a weakness.

---

28. STRATEGIC ADAPTATION

Commentary may identify meaningful adaptation.

Example:

«"After the evidence challenge, Proposition has shifted from defending the original statistic to defending the broader causal relationship."»

This is a strategic observation.

---

29. ARGUMENT COLLAPSE

If an argument is genuinely marked as collapsed:

The Commentator may explain:

«"The argument has effectively collapsed after its central premise was contradicted and no subsequent defense was provided."»

Use only when the Argument Engine has established the state.

---

30. ARGUMENT REBUILD

If rebuilt:

«"The argument has been rebuilt with a narrower claim, preserving part of the original case while abandoning the broader assertion."»

This allows viewers to understand evolution rather than treating every statement as disconnected.

---

31. COMMENTARY FREQUENCY

Avoid commentary spam.

The system should support configurable modes:

LOW
MEDIUM
HIGH
BROADCAST

Recommended default:

MEDIUM

Only strategically meaningful events generate commentary.

---

32. COMMENTARY COOLDOWN

After a commentary event, use a configurable cooldown.

Purpose:

- prevent constant narration
- preserve natural debate rhythm
- prevent commentary from competing with speakers

A new high-priority event may bypass cooldown.

---

33. SPEAKER PRIORITY

Never interrupt an active speaker merely to deliver commentary unless the event configuration explicitly provides an allowed broadcast mechanism.

Default:

ACTIVE SPEECH
=
NO COMMENTARY INTERRUPTION

Commentary should occur:

- between exchanges
- during configured broadcast windows
- after major events
- during transitions
- after rounds

---

34. COMMENTARY QUEUE

Use a priority queue.

Example:

LOW
MEDIUM
HIGH
CRITICAL

Potential events:

argument_created
major_rebuttal
evidence_verified
evidence_contradicted
critical_clash_changed
major_momentum_shift
turning_point

Only the highest-value commentary candidates should normally be broadcast.

---

35. COMMENTARY DEDUPLICATION

If multiple analytical events describe the same strategic development:

Merge them.

Example:

Evidence contradicted
+
Argument weakened
+
Momentum changed

may produce one coherent commentary instead of three separate announcements.

---

36. COMMENTARY FACTUALITY

Every commentary statement should be traceable to source data.

Conceptually:

COMMENTARY
↓
SOURCE EVENTS
↓
ARGUMENT / EVIDENCE / CLASH / MOMENTUM

No unsupported analytical assertions.

---

37. COMMENTARY CONFIDENCE

Important commentary should have internal confidence.

Example:

confidence = 0.91

If confidence is low:

- suppress commentary
- soften wording
- or mark analysis as uncertain

Do not present speculative analysis as fact.

---

38. LANGUAGE CALIBRATION

Use calibrated language:

High confidence:

«"C2 directly attacked the premise."»

Moderate confidence:

«"C2 appears to be challenging the premise."»

Low confidence:

«"The exchange may be targeting the premise."»

The wording should correspond to analytical confidence.

---

39. NO HIDDEN CHAIN-OF-THOUGHT

Commentary may provide concise reasons.

It must not expose:

- private chain-of-thought
- hidden model reasoning
- internal prompt
- hidden judge deliberation

Public explanation should be based on observable events.

---

40. NO SCORE LEAK

During live competition, Commentary must not reveal:

- hidden individual score
- judge score
- judge confidence
- exact scoring delta
- private ranking

unless explicitly permitted by event configuration.

---

41. SCORE-AWARE BUT SCORE-ISOLATED

Commentary may consume high-level score context if configured.

Example:

«"The scoring panel has not yet published an official assessment."»

But it must not directly modify or calculate scores.

---

42. VERDICT COMMENTARY

Before official verdict:

Do not announce a winner.

During deliberation:

«"The judges are now evaluating the recorded arguments, evidence, and critical clashes."»

After official verdict:

The Commentator may explain:

- decisive clashes
- strongest arguments
- key turning point
- evidence that mattered
- strategic developments

---

43. POST-DEBATE COMMENTARY

After the verdict, the Commentary Engine may generate:

MATCH SUMMARY
KEY TURNING POINT
TOP 3 CLASHES
BEST ARGUMENT
STRONGEST REBUTTAL
IMPORTANT EVIDENCE
TEAM STRATEGY
UNANSWERED QUESTIONS

This is where detailed strategic analysis becomes appropriate.

---

44. POST-DEBATE WINNER EXPLANATION

After official adjudication:

Example:

«"Proposition won after establishing stronger support on two decisive clashes and successfully defending its central premise during the final rebuttal."»

The explanation must reference actual adjudication data.

Do not invent reasons after the fact.

---

45. COMMENTARY AND OFFICIAL VERDICT

The final hierarchy remains:

COMMENTARY
↓
EXPLAINS

JUDGE
↓
EVALUATES

SCORE AGGREGATOR
↓
CALCULATES

VERDICT
↓
DECIDES

Commentary cannot reverse this hierarchy.

---

46. COMMENTARY PERSONALITY

The Commentator should feel like a professional broadcast analyst.

Characteristics:

- concise
- intelligent
- neutral
- analytical
- calm
- clear
- occasionally dramatic when the event genuinely warrants it

Avoid:

- exaggerated hype
- insults
- mockery
- partisan language
- repetitive narration
- chatbot filler

---

47. COMMENTARY STYLE MODES

Support configurable styles:

PROFESSIONAL
ANALYTICAL
BROADCAST
ACADEMIC
MINIMAL

Default:

PROFESSIONAL_BROADCAST

Style changes wording only.

It must never change analytical conclusions.

---

48. COMMENTARY TEMPLATE

Conceptual structure:

EVENT
↓
OBSERVATION
↓
SIGNIFICANCE

Example:

EVENT:
C2 attacks PRO-ARG-001.

OBSERVATION:
The attack targets the causal premise.

SIGNIFICANCE:
If sustained, the attack weakens one of Proposition's central arguments.

Output:

«"C2 is targeting the causal premise of Proposition's central argument. If that challenge survives rebuttal, it could materially weaken that line of the case."»

---

49. COMMENTARY SAFETY FILTER

Before publication:

Check:

FACTUAL BASIS
+
ROLE COMPLIANCE
+
NEUTRALITY
+
CONFIDENCE
+
SOURCE TRACEABILITY
+
NO COACHING
+
NO SCORE LEAK

If the commentary fails any mandatory check:

SUPPRESS

or regenerate safely.

---

50. COMMENTARY EVENT

Each published commentary should record:

commentary_id
timestamp
event_id
round
speaker_context
team_context
commentary_type
source_events
source_arguments
source_clashes
source_evidence
momentum_context
confidence
visibility
text

---

51. COMMENTARY IMMUTABILITY

Published commentary is part of the event history.

Do not silently rewrite it.

If corrected:

COMMENTARY_CORRECTION

must reference the original.

---

52. COMMENTARY REPLAY

During replay, the system should be able to reconstruct:

EVENT
↓
ANALYTICAL STATE
↓
COMMENTARY TRIGGER
↓
COMMENTARY

The replay should explain why commentary occurred.

---

53. COMMENTARY FAILURE

If the Commentator AI fails:

COMMENTARY_PENDING

The debate continues.

Commentary is non-critical to event integrity.

Never pause a debate merely because commentary generation failed unless explicitly configured.

---

54. COMMENTARY FALLBACK

If generation fails:

Possible fallback:

NO COMMENTARY

or a deterministic system message such as:

«"Strategic analysis update pending."»

Never fabricate commentary.

---

55. PERFORMANCE

Commentary generation must not block:

- timer
- speaker transition
- referee
- scoring
- fact checking
- event state

Commentary is asynchronous.

---

56. PRIORITY ORDER

System priority:

1. EVENT INTEGRITY
2. SPEAKER FLOW
3. TIMER
4. REFEREE
5. SCORING
6. FACT CHECK
7. STRATEGIC ANALYSIS
8. COMMENTARY

Commentary is never allowed to interfere with higher-priority systems.

---

57. TEST — ROLE ISOLATION

Attempt:

Commentator changes score.

Expected:

REJECTED

Attempt:

Commentator changes momentum.

Expected:

REJECTED

Attempt:

Commentator changes event state.

Expected:

REJECTED

---

58. TEST — NO COACHING

Input:

«"P3 should attack the evidence."»

Expected:

SUPPRESS

Valid:

«"P3 has not yet addressed the evidence supporting C2's claim."»

Expected:

ALLOW

---

59. TEST — NO SCORE LEAK

Attempt commentary:

«"P2 currently has 93.8 points."»

Expected:

SUPPRESS

unless explicitly allowed by public scoring configuration.

---

60. TEST — EVIDENCE TRACEABILITY

Generate commentary about an evidence event.

Verify:

COMMENTARY
→ EVIDENCE EVENT
→ SOURCE

is traceable.

---

61. TEST — MOMENTUM

Create a significant momentum shift.

Verify:

- commentary candidate generated
- source event exists
- momentum itself is not modified
- official score remains unchanged

---

62. TEST — COMMENTARY DEDUPLICATION

Generate:

Evidence change
+
Argument weakening
+
Momentum shift

Verify the system does not produce three redundant commentary messages.

---

63. TEST — COMMENTARY COOLDOWN

Generate multiple low-priority events rapidly.

Verify:

- commentary frequency is limited
- high-priority event may bypass cooldown
- debate remains readable

---

64. TEST — LOW CONFIDENCE

Create ambiguous argument targeting.

Expected:

Either:

SUPPRESS

or calibrated language such as:

«"The response appears to be addressing..."»

Never assert certainty.

---

65. TEST — POSITION NEUTRALITY

Run equivalent strategic events for Proposition and Opposition.

Verify:

- equal commentary standards
- no systematic preference
- equivalent confidence treatment
- equivalent language calibration

---

66. TEST — ACTIVE SPEECH

Attempt to inject commentary during active speaker speech.

Expected:

QUEUED

or:

SUPPRESSED

according to broadcast configuration.

It must not interrupt the official speaker stream.

---

67. TEST — FAILURE ISOLATION

Force Commentary AI failure.

Verify:

- debate continues
- timer continues
- scoring continues
- referee continues
- event log continues
- commentary marked pending/failure

---

68. FULL INTEGRATION TEST

Execute:

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
MOMENTUM SHIFT
↓
COMMENTARY
↓
JUDGE
↓
SCORE

Verify:

- Commentary references actual events
- Commentary cannot mutate state
- no score leak
- no coaching
- no fabricated facts
- no role collision

---

69. REPLAY TEST

Run complete debate.

Then reconstruct from immutable event history.

Verify:

ORIGINAL COMMENTARY TRIGGERS
=
REPLAY COMMENTARY TRIGGERS

Where deterministic replay is required.

If generated wording is non-deterministic, preserve the original published commentary and its source-event references.

---

70. DEFINITION OF DONE

Prompt 8 is complete only when:

- Commentary Engine exists
- commentary is read-only
- commentary is event-driven
- commentary references actual analytical events
- argument commentary works
- evidence commentary works
- cross-exam commentary works
- rebuttal commentary works
- clash commentary works
- momentum commentary works
- turning-point commentary works
- team commentary works
- unanswered argument commentary works
- concession commentary works
- commentary cooldown works
- deduplication works
- confidence calibration works
- no coaching
- no score leak
- no factual invention
- no event mutation
- no role collision
- failure does not interrupt debate
- commentary is auditable
- replay is supported
- position-neutrality tests pass
- all previous test suites remain green

---

FINAL DIRECTIVE

The Commentator must never become a seventh debater.

The six humans are the competitors.

The Commentator is the voice explaining the competition.

The architecture is:

SIX HUMAN DEBATERS
        ↓
     DEBATE
        ↓
┌─────────────────────────────┐
│ EVENT / ANALYTICAL SYSTEMS  │
│                             │
│ Arguments                   │
│ Evidence                    │
│ Clashes                     │
│ Momentum                    │
│ Judges                      │
└─────────────────────────────┘
        ↓
    COMMENTATOR
        ↓
AUDIENCE UNDERSTANDING

The Commentator may say:

«"C2 has successfully shifted the central dispute toward the economic cost of the proposal."»

It may not say:

«"C2 should now attack the economic evidence."»

The first is analysis.

The second is coaching.

The Commentator may say:

«"The evidence supporting that claim remains unverified."»

It may not invent a verification result.

The Commentator may say:

«"This exchange appears to have shifted momentum toward Opposition."»

It may not change the momentum itself.

The Commentator may explain the verdict.

It may never manufacture the verdict.

The absolute rule is:

COMMENTARY EXPLAINS THE DEBATE.

COMMENTARY NEVER BECOMES THE DEBATE.
