# CANONICAL DEBATE ARENA SPECIFICATION
## Comprehensive Master Specification & Operational Blueprint

**System Identity**: Polya Debate Arena Engine  
**Authoritative Locations**:
- Prompts 01–14: `runtime/debate_prompts/` (Foundational Constitution, Engine Protocol, Rubrics)
- Canonical Document: `docs/architecture/CANONICAL_DEBATE_ARENA_SPECIFICATION.md`
- Core Python Engine: `runtime/polya_runtime/debate_engine/` (32 Python modules)
- Presentation & Web UI: `web/static/arena.html` & `web/app.py`
- Test Suite: `runtime/test_debate_engine.py`, `runtime/test_judge_scoring.py`, `runtime/test_round_engine.py`, `runtime/test_moderator_referee.py`, `runtime/test_fact_check_evidence.py`, `runtime/test_training_debate_engine.py`, `runtime/test_ui_presentation_layer.py`, `runtime/test_live_concurrency_validation.py`, `runtime/test_full_system_audit_certification.py`

---

## 1. Authority
The authoritative source for the Debate Arena is the constitutional corpus established in `runtime/debate_prompts/01_DEBATE_CORE_CONSTITUTION.md` through `14_DEBATE_TRAINING_AND_AI_DEBATER_ENGINE.md`, synchronized into `docs/architecture/CANONICAL_DEBATE_ARENA_SPECIFICATION.md` and locked by 73 automated tests in `runtime/`. The deterministic state machine (`polya_runtime.debate_engine.state_machine`) serves as the runtime Single Source of Truth; AI generation cannot override state machine transitions.

---

## 2. Purpose
The Debate Arena provides a high-stakes, competitive, epistemically grounded debate platform for theological, philosophical, and biblical cross-examinations. It enforces rigorous source-language philology, logical coherence, strict floor permissions, and impartial adjudication.

---

## 3. Official Format
- **Format**: Competitive Human-vs-Human 3-vs-3 Debate Match.
- **Match Structure**: 5 Standard Rounds.
- **Clock & Timing**: Managed deterministically by `TimerEngine` with speech limits, grace periods, and POI windows.

---

## 4. Participants
- **Total Human Debaters**: Exactly 6 participants in competitive matches.
- **Human vs AI Division**: 
  - In **Live Match Mode**: Strictly 6 human debaters. AI debater participation is forbidden.
  - In **Training Sparring Mode**: 1 human trainee vs AI Debater (Persona Zuma / synthetic sparring agent).

---

## 5. Team Structure
- **Proposition Team**:
  - **P1 (Prime Minister)**: Motion setup, definitions, constructive cases 1 & 2.
  - **P2 (Deputy Prime Minister)**: Clash, rebuttal, defense of framework, constructive case 3.
  - **P3 (Proposition Whip)**: Summary, clash crystallization, defense (no new arguments).
- **Opposition Team**:
  - **C1 (Leader of Opposition)**: Counter-framework, direct refutation of setup, constructive cases 1 & 2.
  - **C2 (Deputy Leader of Opposition)**: Clash, defense of counter-model, rebuttal.
  - **C3 (Opposition Whip)**: Final summary, crystallization of opposition victory points (no new arguments).

---

## 6. AI Roles
AI functional roles are strictly modularized and decoupled:
- **Host**: Ceremonial welcome and conclusion.
- **Moderator**: Floor control, turn management, speaker cues.
- **Timekeeper**: Clock enforcement and bell alerts.
- **Referee**: Rules enforcement, foul issuance, penalty deduction.
- **Fact-Checker / Evidence Analyst**: Source authenticity, manuscript verification, distortion detection.
- **Argument & Clash Analyst**: Causal DAG tracking (`Claim -> Evidence -> Warrant -> Impact`), unresolved clash mapping.
- **Judge & Score Engine**: Impartial scoring across 6 constitutional rubrics (100 points scale).
- **Commentator**: Live non-partisan tactical play-by-play analysis.
- **Post-Debate Analyst**: Match debriefing, statistics, and turning point graphs.

### Prohibitions on AI (Absolute Neutrality Axiom):
The AI must **never**:
1. Introduce arguments for either team.
2. Defend or attack a team on its own behalf during a live match.
3. Inject personal, partisan, or dogmatic opinions.
4. Replace a human debater or act as P4/C4 in official matches.
5. Favor one team's case over the other.

---

## 7. Moderator Rules
- Governed by `ModeratorEngine` and `PermissionMatrix`.
- Controls turn progression, introduces speakers, and announces transitions.
- Grants floor access according to current speech state.

---

## 8. Referee Rules & Sanctions
- Governed by `RefereeEngine`.
- Enforces procedural rules, decorum, and anti-fallacy standards.
- **Sanction Hierarchy**:
  1. *Verbal Caution*: Informal reminder without point penalty.
  2. *Formal Warning (Foul)*: Recorded in match event ledger, rendered on UI.
  3. *Point Deduction*: Minor (-1 to -3 pts) or Major (-5 to -10 pts) applied to debater's score.
  4. *Disqualification / Forfeit*: Applied for gross ad-hominem, hate speech, or sustained insubordination.

---

## 9. Fact Checker & Evidence Engine Rules
- Governed by `EvidenceFactEngine`.
- Verifies citations against primary manuscripts and lexical databases.
- Identifies citation fabrications, verse truncations, and translational shifts.
- Annotates claims with confidence ratings and provenance tiering.

---

## 10. Evidence Rules & Truth Hierarchy
Strict source classification:
- **Tier 1 (Primary Text)**: Biblical manuscripts (Codex Sinaiticus, Vaticanus, Papyri P46, P66, P75, DSS), classical Hebrew/Greek critical editions (NA28, BHS).
- **Tier 2 (Direct Evidence)**: Explicit lexical or syntactic clauses directly speaking to the motion.
- **Tier 3 (Contextual Evidence)**: Pericope discourse context, historical situation.
- **Tier 4 (Secondary Scholarship)**: Patristic commentaries, peer-reviewed academic monographs, standard lexicons (BDB, HALOT, BDAG).
- **Tier 5 (Interpretive)**: Systematic theological dogmatics (cannot override Tier 1–3).

---

## 11. Debate Flow
1. Setup & speaker check-in (`SETUP` -> `READY`)
2. Official event commencement (`EVENT_START`)
3. Sequential execution of Rounds 1 through 5
4. Round transitions via `ROUND_INTRO`, `SPEECH_ACTIVE`, `SPEECH_CONCLUSION`, `ROUND_REVIEW`, `INTERMISSION`
5. Concluding stage (`DEBATE_CONCLUSION`)
6. Adjudication and final score tabulation (`ADJUDICATION`)
7. Announcement of winner and statistics (`RESULTS_ANNOUNCED` -> `EVENT_CLOSED` -> `ARCHIVED`)

---

## 12. Round Structure
1. **Round 1: Constructive Speeches** (P1 vs C1)
2. **Round 2: Cross-Examination / POI Arena** (Structured Q&A with strict turn limits)
3. **Round 3: Rebuttal Speeches** (P2 vs C2)
4. **Round 4: Defense & Consolidation** (Deep textual substantiation & fallacy exposure)
5. **Round 5: Whip / Summary Speeches** (P3 vs C3; strict prohibition on new constructive material)

---

## 13. Speaking Order
1. P1 (Constructive) -> C1 (Constructive)
2. Cross-Examination exchanges (P vs C / C vs P alternating)
3. P2 (Rebuttal) -> C2 (Rebuttal)
4. P2/P1 (Defense) -> C2/C1 (Defense)
5. C3 (Opposition Whip) -> P3 (Proposition Whip - final right of reply)

---

## 14. Rebuttal Rules
- Must directly target opposing claims, evidence, warrants, or impacts.
- Dropped arguments are logged in the Causal DAG as conceded clashes.
- Strawman representations are flagged as fouls by the Referee.

---

## 15. Cross-Examination & POI Rules
- Governed by `ActionValidator` and `PermissionMatrix`.
- Questions must be concise, targeted, and relevant to previous speeches.
- Respondents must provide direct answers; evasion is penalized in Matter & Manner scores.
- POIs (Points of Information) are restricted to designated windows (protected time at start/end of speeches).

---

## 16. Prohibited Conduct
- Ad-hominem attacks, slurs, and personal insults.
- Unparliamentary interruptions and speaking without floor authorization.
- Fabrication of biblical verses or falsification of manuscript data.
- Introducing new constructive lines in Round 5 (Whip Speeches).

---

## 17. Fallacy Handling
- Real-time fallacy tagging (Strawman, Ad Hominem, False Equivalence, Begging the Question, Appeal to Ignorance).
- Fallacies reduce Logic & Reasoning scores and may trigger Referee verbal cautions or fouls.

---

## 18. Scoring (6 Constitutional Rubrics, 100 Points Total per Debater)
1. **Matter (25 pts)**: Substantive depth, textual accuracy, evidence rigor.
2. **Manner (20 pts)**: Rhetorical control, delivery, composure, adherence to decorum.
3. **Method (15 pts)**: Structural coherence, time management, fulfillment of speaker role.
4. **Logic & Reasoning (15 pts)**: Deductive/inductive validity, absence of logical fallacies.
5. **Cross-Examination & Responsiveness (15 pts)**: Precision in questioning, directness in answering.
6. **Clash & Rebuttal (10 pts)**: Engagement with and refutation of core opposing arguments.

---

## 19. Winner Determination
- Aggregated team scores calculated across all 3 speakers (Max 300 points per team) minus team penalties.
- Individual awards calculated: Best Speaker (highest individual score), Best Inquirer, Best Respondent.
- Victory declared for the team with the higher net points following adjudication.

---

## 20. State Machine (16 Authoritative States)
```text
1. SETUP
2. READY
3. EVENT_START
4. ROUND_INTRO
5. SPEECH_ACTIVE
6. POI_ACTIVE
7. CROSS_EXAM
8. SPEECH_CONCLUSION
9. ROUND_REVIEW
10. INTERMISSION
11. NEXT_ROUND
12. DEBATE_CONCLUSION
13. ADJUDICATION
14. RESULTS_ANNOUNCED
15. EVENT_CLOSED
16. ARCHIVED
```

---

## 21. Evidence / Provenance
- Every cited text is verified through the Polya Evidence Pipeline (`.polya/polya_index.db` and Bible Engine database).
- Verification outputs include: exact verse string, morphology check, critical manuscript witness, and tier classification.

---

## 22. Implementation Mapping
| Constitutional Rule / Domain | Python Implementation Module | Automated Test File |
|---|---|---|
| State Machine & Protocol | `polya_runtime/debate_engine/state_machine.py` | `runtime/test_debate_engine.py` |
| Round Engine & Rules | `polya_runtime/debate_engine/round_engine.py` | `runtime/test_round_engine.py` |
| Moderator Engine | `polya_runtime/debate_engine/moderator_engine.py` | `runtime/test_moderator_referee.py` |
| Referee & Sanctions | `polya_runtime/debate_engine/referee_engine.py` | `runtime/test_moderator_referee.py` |
| Judge & Scoring (6 Rubrics) | `polya_runtime/debate_engine/judge_engine.py` | `runtime/test_judge_scoring.py` |
| Evidence & Fact-Checking | `polya_runtime/debate_engine/evidence_fact_engine.py`| `runtime/test_fact_check_evidence.py` |
| Argument & Clash Graph | `polya_runtime/debate_engine/clash_engine.py` | `runtime/test_debate_engine.py` |
| AI Commentary Engine | `polya_runtime/debate_engine/commentary_engine.py` | `runtime/test_debate_engine.py` |
| Replay & Analytics Engine | `polya_runtime/debate_engine/replay_engine.py` | `runtime/test_debate_engine.py` |
| Persona Zuma Debater | `polya_runtime/debate_engine/persona_engine.py` | `runtime/tests/test_zuma_persona.py` |
| Training Sparring Engine | `polya_runtime/debate_engine/training_engine.py` | `runtime/test_training_debate_engine.py` |
| Presentation Layer | `web/static/arena.html` | `runtime/test_ui_presentation_layer.py` |
| Live Concurrency & Locks | `polya_runtime/debate_engine/timer_engine.py` | `runtime/test_live_concurrency_validation.py` |
| REST API Endpoints | `polya_runtime/debate_engine/api.py` | `runtime/test_full_system_audit_certification.py` |

---

## 23. Test Coverage
- **Total Debate Arena Core Tests**: 73 passing tests (`runtime/test_*.py`).
- **Full Runtime Suite**: 186 passing tests.
- **Coverage**: 100% of state transitions, scoring bounds, penalty applications, and permissions matrix constraints are locked by unit and integration tests.

---

## 24. Historical Sources
1. Master Prompts `01_DEBATE_CORE_CONSTITUTION.md` through `14_DEBATE_TRAINING_AND_AI_DEBATER_ENGINE.md` created on 2026-09-13.
2. Architecture Specification `CANONICAL_DEBATE_ARENA_SPECIFICATION.md` generated on 2026-10-04.
3. Git Commit history reflecting vertical slice integration (`a514674`, `28f4cf5`, `f9a92b1`, `f82b9c1`).

---

## 25. Conflicts / Unresolved Items
- None. Prompts 01–14, `CANONICAL_DEBATE_ARENA_SPECIFICATION.md`, and Python engine implementations in `runtime/polya_runtime/debate_engine/` are fully consistent and synchronized.
