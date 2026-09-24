# DEBATE ARENA — PROMPT 10

DEBATER PERSONA ENGINE + ZUMA APOLOGETICS INTEGRATION

STATUS

LOCKED SYSTEM SPECIFICATION

This layer extends:

1. "01_DEBATE_CORE_CONSTITUTION.md"
2. "02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md"
3. "03_DEBATE_ROUND_ENGINE_RULES.md"
4. "04_DEBATE_MODERATOR_REFEREE_ENGINE.md"
5. "05_DEBATE_JUDGE_SCORING_ENGINE.md"
6. "06_DEBATE_FACT_CHECK_EVIDENCE_ENGINE.md"
7. "07_DEBATE_ARGUMENT_CLASH_MOMENTUM_ENGINE.md"
8. "08_DEBATE_AI_COMMENTARY_ENGINE.md"
9. "09_DEBATE_REPLAY_ANALYTICS_ENGINE.md"

Do not modify the authority of previous layers.

---

1. ABSOLUTE CONSTITUTIONAL RULE

Debate Arena remains:

HUMAN PROPOSITION
P1 + P2 + P3

        VS

HUMAN OPPOSITION
C1 + C2 + C3

AI is NOT a seventh debater.

AI must never enter the official debate as a competitor.

AI remains:

Moderator
Referee
Timekeeper
Fact Checker
Evidence Analyst
Argument Analyst
Clash Analyst
Judge
Score Engine
Commentator
Replay / Analytics Engine

---

2. PURPOSE OF PROMPT 10

Create a Debater Persona Engine that controls how a participant approaches a debate without changing:

- event rules
- speaker permissions
- scoring rules
- referee authority
- evidence verification
- official verdict
- critical clash state
- event state machine

Persona affects:

STRATEGY
ARGUMENT APPROACH
QUESTIONING STYLE
REBUTTAL APPROACH
EVIDENCE EMPHASIS
COMMUNICATION STYLE

Persona does NOT affect:

TRUTH
FACT-CHECK RESULT
OFFICIAL SCORE
RULES
JUDGE AUTHORITY
VERDICT
EVENT STATE

---

3. PERSONA HIERARCHY

The AI context hierarchy must remain:

EVENT RULES
↓
STATE MACHINE
↓
ROUND RULES
↓
SPEAKER PERMISSIONS
↓
ROLE INSTRUCTIONS
↓
SCORING RUBRICS
↓
PERSONA
↓
LANGUAGE STYLE

Persona is subordinate to all higher layers.

---

4. PERSONA ≠ SCRIPT

A persona must never produce a fixed script that the debater is forced to repeat.

Instead it provides:

TACTICAL PREFERENCES
ARGUMENTATION PATTERNS
QUESTIONING PREFERENCES
REBUTTAL PREFERENCES
EVIDENCE PREFERENCES
COMMUNICATION CHARACTERISTICS

The participant remains responsible for the actual statement.

---

5. PERSONA DATA MODEL

Each persona should support:

persona_id
name
description
strategic_profile
argumentation_profile
evidence_profile
cross_exam_profile
rebuttal_profile
clash_profile
communication_profile
strengths
weaknesses
preferred_tactics
avoid_tactics
training_notes
version

---

6. PERSONA LAYER SEPARATION

Separate:

PERSONA

from:

SKILL

and:

STYLE

Architecture:

DEBATER
 ↓
ROLE
 ↓
PERSONA
 ↓
SKILLS
 ↓
STRATEGY
 ↓
STYLE

Example:

Persona:
Analytical Apologist

Skills:
Evidence Analysis
Cross Examination
Rebuttal
Textual Analysis

Style:
Calm / Precise / Socratic

---

7. ZUMA APOLOGETICS

Implement ZUMA as a specialized persona/skill profile based on the approved ZUMA Debate Persona dataset already available in the project.

Do NOT invent characteristics that are not supported by the project's ZUMA source data.

The system should distinguish:

OBSERVED ZUMA PATTERN

from:

SYSTEM-GENERATED INTERPRETATION

and:

GENERIC DEBATE BEHAVIOR

---

8. ZUMA PROFILE

The ZUMA profile may contain dimensions such as:

Argument Framing
Questioning Strategy
Cross Examination
Rebuttal Strategy
Evidence Handling
Textual Analysis
Premise Testing
Definition Analysis
Contradiction Detection
Burden of Proof
Logical Pressure
Concession Handling
Clash Prioritization
Closing Strategy

Only activate dimensions actually supported by the project's ZUMA dataset.

---

9. ZUMA PATTERN PURITY

The system must distinguish:

ZUMA-SPECIFIC PATTERN

from:

COMMON DEBATE PATTERN

A behavior should not be labeled "ZUMA" merely because it is effective debating.

Maintain provenance:

pattern_id
source_video
source_segment
confidence
pattern_category
frequency

---

10. ZUMA PATTERN CONFIDENCE

Every extracted ZUMA pattern should have:

confidence
frequency
source_count

Repeated patterns across multiple source videos receive stronger confidence.

A behavior appearing once must not automatically become a defining persona characteristic.

---

11. ZUMA EVOLUTION

The persona must support versioning.

Example:

ZUMA_PERSONA_v1
ZUMA_PERSONA_v2
ZUMA_PERSONA_v3

When new video corpus data is processed:

NEW DATA
↓
PATTERN EXTRACTION
↓
DUPLICATION
↓
CROSS-VIDEO VALIDATION
↓
CONFIDENCE UPDATE
↓
PERSONA VERSION

Never silently overwrite the historical persona.

---

12. PERSONA ACTIVATION

A participant may be configured with:

persona_id
skill_set
style_profile

Example:

P1
Persona: ZUMA_APOLOGETICS
Skills:
- Premise Testing
- Cross Examination
- Evidence Analysis
Style:
- Calm
- Direct
- Analytical

---

13. PERSONA DOES NOT OVERRIDE REAL HUMAN INPUT

If the user is manually debating:

USER SPEECH
=
AUTHORITATIVE

The persona does not rewrite the participant's statement.

The system only analyzes the behavior and optionally provides training feedback where permitted.

---

14. PERSONA IN LIVE ARENA

During an official human-vs-human match:

Persona should primarily function as:

ANALYTICAL PROFILE

rather than an invisible coach.

The system may record:

observed_behavior
persona_alignment
strategic_pattern

after the participant speaks.

---

15. NO HIDDEN COACHING

Do not secretly inject suggestions into a participant's live debate.

Examples of prohibited behavior:

"Attack C2's premise now."
"Ask this question."
"Use this verse."
"Change your strategy."

unless the event explicitly runs in a configured Training / Coaching Mode.

Official competition must remain competition.

---

16. TRAINING MODE

Create a separate:

DEBATE TRAINING MODE

In Training Mode, AI may provide:

- suggested questions
- possible rebuttal approaches
- evidence recommendations
- strategic alternatives
- persona coaching
- practice scenarios

Training Mode must be clearly separated from Official Arena Mode.

---

17. OFFICIAL MODE VS TRAINING MODE

OFFICIAL ARENA
AI = OBSERVER / OFFICIAL SYSTEM

TRAINING ARENA
AI = COACH / SIMULATION ASSISTANT

Never mix the two.

---

18. PERSONA OBSERVATION ENGINE

After each meaningful speech, optionally classify:

Observed Strategy
Observed Tactic
Observed Question Pattern
Observed Rebuttal Pattern
Observed Evidence Behavior
Observed Clash Behavior

Then compare with the active persona.

Example:

Expected ZUMA Pattern
vs
Observed Participant Behavior

---

19. PERSONA ALIGNMENT

Calculate an analytical alignment score:

PERSONA ALIGNMENT
0–100

This is NOT a debate score.

It must never modify the official 100-point debate score.

---

20. PERSONA ALIGNMENT DIMENSIONS

Possible dimensions:

Argument Framing
Premise Testing
Evidence Handling
Cross Examination
Rebuttal
Clash Selection
Burden of Proof
Concession Handling
Closing
Communication

Only applicable dimensions should be evaluated.

---

21. PERSONA ALIGNMENT EXAMPLE

ZUMA PERSONA
Premise Testing: 90
Cross Examination: 95
Evidence Handling: 82
Rebuttal: 88

Observed P2:
Premise Testing: strong
Cross Examination: strong
Evidence Handling: moderate
Rebuttal: strong

Generate:

Persona Alignment: 89

This remains separate from:

Official Debate Score: 93.8

---

22. PERSONA DRIFT

Detect when a participant consistently behaves differently from the selected persona.

Example:

Selected:
ZUMA_APOLOGETICS

Observed:
Primarily rhetorical
Low premise testing
Low evidence engagement

The system may report:

«"Observed debate behavior shows substantial divergence from the selected persona profile."»

Do not penalize the participant.

---

23. PERSONA STRENGTHS

After the debate identify:

Strongest persona-aligned behaviors

Example:

- premise testing
- direct questioning
- burden-of-proof pressure
- targeted rebuttal

---

24. PERSONA WEAKNESSES

Identify:

Weak persona dimensions

Example:

- evidence integration
- follow-up precision
- closing synthesis

Again:

No automatic official-score penalty.

---

25. PERSONA VS PERFORMANCE

Keep two separate analytical dimensions:

DEBATE PERFORMANCE

and:

PERSONA ALIGNMENT

A participant can:

High Performance
Low Persona Alignment

or:

High Persona Alignment
Low Performance

Both are valid.

---

26. PERSONA VS ZUMA SOURCE

If a ZUMA behavior is claimed:

The system should be able to trace:

OBSERVED BEHAVIOR
↓
ZUMA PATTERN
↓
SOURCE VIDEO
↓
SOURCE SEGMENT
↓
CONFIDENCE

No unsupported attribution.

---

27. APOLOGETICS SKILL INTEGRATION

The ZUMA Apologetics profile should integrate with relevant debate skills such as:

Premise Analysis
Definition Analysis
Burden of Proof
Textual Analysis
Contextual Analysis
Historical Reasoning
Comparative Argumentation
Contradiction Detection
Evidence Evaluation
Cross Examination
Rebuttal
Clash Management

Skills must remain modular.

---

28. KNOWLEDGE BASE SEPARATION

Persona knowledge must not be confused with factual knowledge.

Separate:

KNOWLEDGE
=
WHAT IS KNOWN

PERSONA
=
HOW TO APPROACH DEBATE

STYLE
=
HOW TO EXPRESS IT

---

29. KNOWLEDGE SOURCE INTEGRITY

ZUMA persona must never automatically grant factual authority to any proposition.

For example:

ZUMA_PERSONA
≠
FACTUAL_SOURCE

Factual claims remain subject to:

FACT CHECK ENGINE
EVIDENCE ENGINE

---

30. PERSONA + ARGUMENT ENGINE

The Argument Engine may record:

argument_strategy
persona_pattern

Example:

ARG-P2-007

Strategy:
Premise Challenge

Persona Pattern:
ZUMA-PATTERN-014

Confidence:
0.91

This creates analytical linkage without changing the argument itself.

---

31. PERSONA + CLASH ENGINE

When a participant selects or attacks a critical clash:

Record:

clash_selection_strategy
persona_alignment

Example:

«"P2 consistently prioritized premise-level clashes, consistent with the active persona profile."»

---

32. PERSONA + CROSS EXAMINATION

Record:

question_type
question_structure
follow_up_pattern
premise_target
evidence_target
persona_alignment

This allows detailed post-match analysis.

---

33. PERSONA + REBUTTAL

Record:

rebuttal_target
attack_level
premise_attack
evidence_attack
scope_attack
impact_attack
persona_pattern

---

34. PERSONA + CLOSING

Analyze:

case synthesis
clash synthesis
evidence synthesis
unanswered argument summary
strategic framing
persona alignment

---

35. ZUMA STYLE IS NOT ZUMA PERSONA

Separate:

ZUMA_PERSONA

from:

ZUMA_STYLE

Persona describes strategic behavior.

Style describes linguistic expression.

Do not classify generic Indonesian language habits as strategic ZUMA characteristics without evidence.

---

36. STYLE TRANSFORMATION SAFETY

If a ZUMA style is activated:

It must not cause:

- fabricated claims
- fabricated quotations
- invented evidence
- false attribution
- aggressive harassment
- rule violations

Style remains subordinate to factuality and event rules.

---

37. PERSONA STACKING

Support multiple skills without allowing contradictory instructions.

Example:

Persona:
ZUMA_APOLOGETICS

Skills:
Cross Examination
Evidence Analysis
Historical Analysis

Style:
Professional Analytical

Resolve conflicts using:

EVENT RULES
>
ROLE
>
PERSONA
>
SKILL
>
STYLE

---

38. PERSONA CONFLICT

If two persona instructions conflict:

Do not randomly choose.

Use deterministic priority.

Example:

ZUMA PERSONA:
Direct Questioning

EVENT RULE:
Question not permitted in current round

Result:

EVENT RULE WINS

---

39. PERSONA TRANSPARENCY

The UI should be able to show:

Active Persona
Active Skills
Active Style

for the participant where visibility is permitted.

---

40. OFFICIAL JUDGING IS PERSONA-BLIND

Judges must not reward or punish a participant merely for matching a particular persona.

Official score evaluates:

ARGUMENT
EVIDENCE
REASONING
REBUTTAL
CROSS EXAM
RESPONSIVENESS
CLARITY
STRATEGY
TEAM CONTRIBUTION

not:

"How much did they resemble ZUMA?"

---

41. FAIRNESS

The system must never assume:

ZUMA = BETTER

ZUMA is one strategic profile.

Other personas must be equally valid.

---

42. PERSONA PERFORMANCE COMPARISON

Support post-debate comparison:

Selected Persona
vs
Observed Behavior
vs
Official Performance

This produces training intelligence without contaminating judging.

---

43. PERSONA RECOMMENDATION ENGINE

After enough data, the system may recommend:

Potential Persona Fit

based on observed behavior.

Example:

«"Observed behavior is more consistent with an Evidence Specialist profile than the currently selected persona."»

Recommendations must be analytical only.

---

44. PERSONA EVOLUTION

For recurring debaters, maintain:

PERSONA PROFILE
↓
MATCH HISTORY
↓
OBSERVED BEHAVIOR
↓
STRENGTHS
↓
WEAKNESSES
↓
EVOLUTION

This creates a long-term debate development profile.

---

45. NO AUTOMATIC IDENTITY CLAIM

Do not claim:

«"This person is ZUMA."»

unless explicitly configured and supported by verified identity/profile data.

The system should instead say:

«"This participant is using the ZUMA Apologetics persona."»

---

46. PERSONA AUDIT LOG

Record:

persona_activation
persona_version
skill_activation
style_activation
observed_pattern
pattern_confidence
persona_alignment
source_refs

---

47. REPLAY INTEGRATION

Prompt 9 replay must be able to reconstruct:

PERSONA ACTIVE
↓
SKILLS ACTIVE
↓
SPEECH
↓
OBSERVED STRATEGY
↓
PERSONA ALIGNMENT

Historical persona versions must be preserved.

---

48. ANALYTICS INTEGRATION

Post-debate analytics should include:

PERSONA PERFORMANCE
PERSONA ALIGNMENT
STRATEGIC PATTERNS
PERSONA DRIFT
STRENGTHS
WEAKNESSES
EVOLUTION

These remain separate from official judging.

---

49. TRAINING REPORT

Optional training report:

WHAT THE PERSONA DOES WELL
WHAT THE PARTICIPANT ACTUALLY DID
WHERE THEY MATCHED
WHERE THEY DIVERGED
WHAT SKILLS NEED DEVELOPMENT

---

50. TEST — PERSONA ISOLATION

Attempt:

Persona modifies score.

Expected:

REJECTED

Attempt:

Persona modifies referee decision.

Expected:

REJECTED

Attempt:

Persona changes event state.

Expected:

REJECTED

---

51. TEST — OFFICIAL MODE

Run human 3-vs-3 debate.

Verify:

AI NEVER BECOMES PARTICIPANT

---

52. TEST — TRAINING MODE

Enable training mode.

Verify coaching capabilities are available only inside the training boundary.

---

53. TEST — PERSONA ALIGNMENT

Use known persona behavior.

Verify:

alignment calculated
official score unchanged

---

54. TEST — PERSONA DRIFT

Generate behavior substantially different from selected persona.

Verify:

drift detected
no score penalty

---

55. TEST — ZUMA PROVENANCE

Use a known ZUMA pattern.

Verify:

pattern
→ source
→ confidence

is traceable.

---

56. TEST — UNSUPPORTED ZUMA ATTRIBUTION

Attempt to label a generic debate behavior as ZUMA-specific without source evidence.

Expected:

REJECTED / GENERIC_PATTERN

---

57. TEST — PERSONA CONFLICT

Create:

PERSONA INSTRUCTION
vs
ROUND RULE

Verify:

ROUND RULE WINS

---

58. TEST — JUDGE BLINDNESS

Run two participants with different personas but equivalent argument quality.

Verify official judging does not award points merely because one uses the ZUMA persona.

---

59. TEST — REPLAY

Complete debate.

Replay.

Verify persona activation and observed patterns are reconstructed.

---

60. TEST — VERSIONING

Change ZUMA persona version.

Verify historical matches retain the previous persona version.

---

61. TEST — ZERO REGRESSION

Run all previous suites:

test_debate_engine.py
test_round_engine.py
test_moderator_referee.py
test_judge_scoring.py
test_fact_check_evidence.py
test_strategic_engines.py
test_commentary_engine.py
test_replay_analytics.py

All must remain:

100% PASSED

---

62. DEFINITION OF DONE

Prompt 10 is complete only when:

- Persona Engine exists
- Persona / Skill / Style are separated
- ZUMA profile integrates correctly
- ZUMA pattern provenance exists
- ZUMA confidence exists
- ZUMA versioning exists
- Persona does not alter official score
- Persona does not alter rules
- Persona does not alter referee
- Persona does not alter verdict
- Official judging is persona-blind
- Official Mode has no hidden coaching
- Training Mode is isolated
- Persona alignment works
- Persona drift works
- Persona analytics work
- Replay reconstructs persona state
- Historical persona versions are preserved
- Unsupported ZUMA attribution is rejected
- All previous tests remain green
- Zero regression
