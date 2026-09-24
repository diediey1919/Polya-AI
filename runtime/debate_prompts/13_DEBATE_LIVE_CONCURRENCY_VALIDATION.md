# DEBATE ARENA — PROMPT 13 ARCHITECTURAL SPECIFICATION
## Real Human 3-vs-3 Live Match & Concurrency Validation

---

### 1. Absolute Participant Model
- **Proposition Team**: Exactly 3 Human Debaters (`P1`, `P2`, `P3`).
- **Opposition Team**: Exactly 3 Human Debaters (`C1`, `C2`, `C3`).
- **AI Roles**: Strictly **NON-PARTICIPANT** Event Intelligence.
  - Moderator, Referee, Timekeeper, Fact-Checker, Evidence Analyst, Argument Graph Analyst, Clash Analyst, Momentum Tracker, Commentary Engine, 3 Independent Judges (`Judge A` - Logic, `Judge B` - Evidence, `Judge C` - Strategy), Adjudication & Replay Engine.
  - AI is forbidden from taking debater speaker seats, submitting claims as a participant, voting as a team member, or accumulating debater speaker points.

---

### 2. Concurrency & Authority Safeguards

```
[Client P1]   [Client P2]   [Client P3]   [Client C1]   [Client C2]   [Client C3]
     │             │             │             │             │             │
     └─────────────┴─────────────┼─────────────┴─────────────┴─────────────┘
                                 ▼
                     [Authoritative State Bridge]
                   (Thread-Safe Mutex / RLock)
                                 │
           ┌─────────────────────┼─────────────────────┐
           ▼                     ▼                     ▼
 [Lobby / Session Engine] [Speaker Authority Gate] [Idempotency Filter]
  - 6 Seat Registry        - Active Speaker Lock    - Request Deduplication
  - Team Alignment Guard   - Out-of-Turn Rejection  - Nonce / Request ID Cache
  - Single Active Session  - Referee Auditing
           │                     │                     │
           └─────────────────────┼─────────────────────┘
                                 ▼
                    [Debate Arena Event Engine]
               - 10-Round Deterministic State Machine
               - Real-Time Protocol & Cross-Examination
               - Immutable Event Log (Source of Truth)
```

---

### 3. Key Operational Verifications (Prompt 13 Acceptance Matrix)

1. **6-Participant Lobby**:
   - `P1`, `P2`, `P3` (PROPOSITION) and `C1`, `C2`, `C3` (OPPOSITION) join lobby.
   - Ready status tracked (`0/6 READY` $\rightarrow$ `6/6 READY`).
   - Transition to `TEAM_READY` only upon complete 6/6 ready confirmation.
2. **AI Non-Participant Enforcement**:
   - Attempts to assign participant identities to AI roles (`MODERATOR`, `REFEREE`, `JUDGE_A`, `HOST`) are strictly rejected.
3. **Wrong Team Rejection**:
   - Attempts by `P1`/`P2`/`P3` to join Opposition, or `C1`/`C2`/`C3` to join Proposition, are rejected with `"Wrong team assignment"`.
4. **Late Join / Match Lock**:
   - After match start (`TOPIC_LOCK` / `TEAM_READY`), new/unauthorized participant registration is blocked.
5. **Duplicate Session Isolation**:
   - Opening a second session for the same debater invalidates the previous session and reclaims the single authoritative connection without duplicate speaker or score events.
6. **Multi-Client Synchronization**:
   - 6 independent clients polling or connected via WebSocket receive identical round phase, active speaker, timer countdown, and permission state.
7. **Speaker Authority & Out-of-Turn Rejection**:
   - When `P1` is speaking, speech submissions by `C2` or `P2` are rejected as authority violations and recorded by the AI Referee.
8. **Race Condition Protection**:
   - Concurrent submissions across threads are serialized safely using re-entrant locks (`RLock`) without state corruption.
9. **Double Submission Idempotency**:
   - Repeated requests with identical `request_id` return cached authoritative results without duplicate argument nodes or double scoring.
10. **Network Interruption & Reconnect**:
    - Disconnect of active debater does not crash or replace them with AI; reconnect delivers fresh authoritative state for the current round.
11. **Moderator Pause / Resume**:
    - `PAUSE` halts timer and locks actions; `RESUME` restores live state seamlessly.
12. **Timer Expiration**:
    - Server-authoritative timer transitions cleanly on expiration (0s).
13. **Cross-Examination Turn Protocol**:
    - `QUESTION` $\rightarrow$ `ANSWER` $\rightarrow$ `FOLLOW_UP` $\rightarrow$ `RESPONSE` micro-protocol enforced.
14. **Input Validation & Client Trust Guard**:
    - Empty speech, oversized speech (>10,000 chars), and malicious client manipulation (injecting fake winner/score/round fields) are blocked.
15. **Score Privacy**:
    - Raw judge evaluations remain hidden from participants during live rounds and are only revealed at deliberation/verdict.
16. **Analytical Service Degradation Resilience**:
    - Degraded Commentary or Momentum subsystems do not halt core debate flow.
17. **Golden Live Match 001 Fixture (`DEBATE_ARENA_LIVE_GOLDEN_001`)**:
    - 100% full lifecycle execution with 6 human debaters and complete replay parity.

---

### 4. Verification Status
- **Prompt 13 Suite**: 18 / 18 Tests PASSED (100%).
- **Prior Prompts 1–12 Suites**: 100% PASSED — ZERO REGRESSION.
