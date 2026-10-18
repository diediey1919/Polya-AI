# Agent: POLYA — Dialectical Engine & Debate Arena FSM Specialist

## Identity
- **Name**: polya
- **Role**: ZUMA Socratic sparring engine, debate training service, FSM state management
- **Profile**: ZUMA Dialectical Persona — Socratic pressure, logical trap extraction, rigid text dissection

## Core Responsibilities
1. Fix `web/static/arena.html` `/arena`:
   - Hide `OFFICIAL ADJUDICATION VERDICT` panel (`68.91 VS 51.00`) when CURRENT PHASE = SETUP
   - Hide `DEBATE QUALITY INDEX` panel (`8.98 / 10`) when CURRENT PHASE = SETUP
   - Hide `ZUMA_DEBATE_CORPUS_EP01` when CURRENT PHASE = SETUP
   - Only reveal verdict after `COMPLETED` phase
2. Replace AI regulation motion (`Regulasi Forensik Kecerdasan Buatan` / `EU AI Act Article 14`) with dynamic apologetika theological motion
3. Fix `ANALYTICS TEMPORARILY UNAVAILABLE` → connect to live analytics endpoint
4. Ensure navigation from `index.html` → `/arena` works (full SPA routing)
5. Connect `/persona` view to 10 `DebateTrainingService` endpoints:
   - `POST /api/training/session/create`
   - `POST /api/training/session/configure`
   - `POST /api/training/session/start`
   - `POST /api/training/session/round`
   - `POST /api/training/session/challenge`
   - `POST /api/training/session/counter`
   - `POST /api/training/session/adjudicate`
   - `POST /api/training/session/summary`
   - `POST /api/training/session/save`
   - `POST /api/training/session/complete`

## Autonomous Workflow
- Inspect `polya_runtime/debate_engine/training_api.py` — confirm 10 endpoints exist
- Patch `web/static/index.html` persona section JS to call `/api/training/session/*`
- Patch `web/static/arena.html` — add phase-gating conditionals (hide verdict until COMPLETED)
- Replace hardcoded AI motion with canonical theological motion from `bible_engine/graph.py`
- Connect analytics display to `GET /api/arena/state` or live WebSocket

## Verification Mandate
```
pytest runtime/test_debate_engine.py runtime/test_training_debate_engine.py runtime/test_persona_zuma_engine.py -x -q
```
- WebSocket initial payload check: `POST /api/arena/ws` sends JSON with `current_phase` = "SETUP"
- When phase = SETUP, DOM element `#verdict-panel` has `display: none` or `aria-hidden: true`
- Motion text contains apologetika subject (e.g., "kasih", "penebukan hati", "roh kehidupan") — NOT "EU AI Act"
- `/persona` has 10 active event listeners for training session endpoints

## Constraints
- FSM must respect 16-state architecture in `polya_runtime/debate_engine/`
- Apologetika motions must come from canonical corpus, not external regulation text

## Failure Mode
If FSM verification fails 3 times, mark FAILED and re-open for next cron cycle.
