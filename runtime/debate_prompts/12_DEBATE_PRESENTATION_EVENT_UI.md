# DEBATE ARENA — PROMPT 12: PROFESSIONAL PRESENTATION & EVENT UI LAYER

## Status & Certification
- **Status**: 100% PASS — ZERO REGRESSION
- **Architecture**: Authoritative Core Backend $\rightarrow$ Presentation & Event UI Layer
- **Interface**: Professional Live 3-vs-3 Dialectical Debate Broadcast Arena

---

## 1. Absolute UI Principles
1. **Engine as Sole Source of Truth**: UI strictly consumes and visualizes authoritative state from `DebateArenaEventEngine`. No duplicate debate rules or logic are implemented in frontend.
2. **AI Non-Participant Principle**: AI operates exclusively as Event Intelligence (`AI Event Control`, `AI Moderator`, `AI Referee`, `AI Commentary`, `AI Judges`, `AI Analytics`). Debater roster is strictly human 3-vs-3 (Proposition: P1, P2, P3 vs Opposition: C1, C2, C3).
3. **Landscape-First Studio Design**: Optimized for broadcast display, desktop, and studio landscape viewports with dark mode high contrast aesthetics.

---

## 2. Core Presentation Modules
- **Master Live Arena Stage**:
  - Live Speaker Spotlight Podium with active speech transcript and animated audio wave meters.
  - Subdued state for non-active debaters.
  - Synchronized Master Timer Engine (Normal $\rightarrow$ Warning $\rightarrow$ Critical $\rightarrow$ Expired).
  - Proposition & Opposition Team Booths (P1, P2 with ZUMA tag, P3 vs C1, C2, C3).
  - Active Strategic Argument, Critical Clash, and Primary Evidence verification cards.
  - Non-intrusive Fact-Check alert bar.
- **AI Event Control Layer**:
  - AI Moderator Ruling Feed & Interventions.
  - AI Referee Active Compliance & Violation Flag Tracker.
  - AI Commentary Broadcast Layer (Read-Only, strictly score-isolated).
  - Strategic Momentum Gauge & Trajectory (Strictly analytical, score-isolated).
  - 3 Independent Multi-Judge Panel (Logic, Evidence, Strategy - scores masked during live match, revealed at deliberation/verdict).
- **Post-Debate Adjudication & Awards**:
  - Official Verdict Trophy Reveal (Winning Team, Victory Margin, Point Aggregates).
  - Audit-based "Why Did They Win?" decomposition (Clash dominance, Argument lineage, Multi-judge consensus).
  - Individual Debater Scorecard with 9-rubric breakdown.
  - Official Event Awards (Winning Team, Best Debater, Best Argument, Best Rebuttal, Best Evidence, Best Cross-Exam, Best Clash, Best Closing).
- **Interactive Replay & Forensic Analytics**:
  - Argument Battle Map with dependency graph and attack/defense links.
  - Critical Clash Map with turning point resolution.
  - ZUMA Apologetics Persona Telemetry (Pattern Alignment %, Pattern IDs, Corpus Provenance).
- **Resilience & Idempotency**:
  - Degraded state handling ("ANALYTICS TEMPORARILY UNAVAILABLE").
  - Idempotent event feed with duplicate event filtering.

---

## 3. Endpoints
- `GET /arena` / `GET /`: Serves `arena.html`
- `GET /api/arena/state`: Complete authoritative state snapshot
- `POST /api/arena/action`: Executes debate actions via state machine & referee
- `POST /api/arena/golden_match`: 1-Click Golden Match 001 simulation
- `POST /api/arena/reset`: Match reinitialization
- `POST /api/arena/degraded`: Toggles degraded state testing
- `GET /api/arena/replay`: Replay timeline & causal turning points
- `GET /api/arena/forensics`: Forensics data & ZUMA persona telemetry
- `WebSocket /api/arena/ws`: Real-time state broadcasting
