# POLYA AI — WEBSITE INTEGRATION AUDIT REPORT

**Date & Time**: 2026-10-11T22:05:00+07:00  
**Target Repository**: `/home/ubuntu/Polya-AI`  
**Branch**: `main` (HEAD Commit: `d364600`)  
**Audit Standard**: Empirical verification of code, routes, APIs, engines, database, tests, and runtime behavior.  

---

## 1. Baseline Architecture
- **Repository Root**: `/home/ubuntu/Polya-AI`
- **Frontend Stack**: 
  - Framework: Vanilla HTML5 / Vanilla CSS3 / Vanilla JavaScript Single Page Application (SPA).
  - Client Router: Custom HTML5 History API router (`navigateRoute`, `dispatchRoute`, `popstate`).
  - Presentation Files:
    - Primary App: `/home/ubuntu/Polya-AI/web/static/index.html` (~3,150 LOC)
    - Debate Arena: `/home/ubuntu/Polya-AI/web/static/arena.html` (~1,350 LOC)
- **Backend Stack**:
  - Web Server: Python 3.11 + FastAPI + Starlette + Uvicorn (`web/app.py` & `web/api_foundation.py`).
  - Multi-Agent Orchestrator: LangGraph StateGraph (`orchestrator/research_graph.py`).
  - Epistemic Engine: `orchestrator/epistemic_firewall.py`, `orchestrator/adversarial_engine.py`, `orchestrator/source_criticism.py`.
  - Canonical Debate Arena: `polya_runtime.debate_engine` (32 Python modules, 16-state deterministic FSM, 5 rounds).
  - Philological Engine: `bible_engine` (45+ modules for NA28/DSS Greek/Hebrew critical apparatus).
- **Database**:
  - SQLite: `/home/ubuntu/Polya-AI/data/polya_arena.db` (Tables: `arena_users`, `case_files_v2`, `execution_traces`, `payment_transactions`, `usage_entitlement_records`, `user_apologetics_context`, `user_entitlements`).

---

## 2. Frontend Routes Discovery
| Route | File | Purpose | Status | Backend Connected | Mock Data | Tested |
|---|---|---|---|---|---|---|
| `/` | `web/static/index.html` | Landing & Calculator | **REAL** | YES (`/api/v1/calculator/analyze`) | NO | YES |
| `/dashboard` | `web/static/index.html` | Research Dashboard | **PARTIAL** | YES (`/api/v1/entitlements/usage`) | YES (Static stats) | YES |
| `/calculator` | `web/static/index.html` | AI Apologetics Calculator | **REAL** | YES (`/api/v1/calculator/analyze`) | NO (Runs real engine) | YES |
| `/themes` | `web/static/index.html` | Themes Explorer & Case Files | **STATIC** | NO | YES (Hardcoded Friksi Paulus) | NO |
| `/knowledge` | `web/static/index.html` | Ontological Argument Graph | **STATIC** | NO | YES (Hardcoded SVG nodes) | NO |
| `/persona` | `web/static/index.html` | Zuma Strategic Telemetry | **STATIC** | NO | YES (Copy-only formula cards) | NO |
| `/pipeline` | `web/static/index.html` | Autonomous Research Pipeline | **STATIC** | NO | YES (Static HTML badges) | NO |
| `/settings` | `web/static/index.html` | Research & Language Settings | **REAL** | YES (`/api/v1/context`) | NO | YES |
| `/account` | `web/static/index.html` | Quota & Billing Ledger | **REAL** | YES (`/api/v1/account/billing`) | NO | YES |
| `/arena` | `web/static/arena.html` | 3v3 Parliamentary Debate Arena | **REAL** | YES (`WS /api/arena/ws`) | NO | YES |

---

## 3. Backend APIs Discovery & Wiring Matrix
| Method & Path | Auth Required | Database / Engine | Frontend Caller | Empirical Status |
|---|---|---|---|---|
| `GET /api/v1/meta/languages` | None | `LANGUAGE_REGISTRY` | `index.html` (`fetchLanguages`) | **REAL** |
| `GET /api/v1/context` | None | `user_apologetics_context` | None | **REAL** |
| `POST /api/v1/context` | None | `user_apologetics_context` | `index.html` (`completeOnboarding`) | **REAL** |
| `GET /api/v1/entitlements/usage` | None | `usage_entitlement_records` | `index.html` (`fetchUsage`) | **REAL** |
| `POST /api/v1/calculator/analyze` | Quota (5 free) | LangGraph `research_graph` | `index.html` (`runAnalysis`) | **REAL** |
| `GET /api/v1/calculator/source` | None | `orchestrator.evidence_engine` | **NONE** (Frontend uses static drawer) | **PARTIAL** |
| `POST /api/v1/calculator/challenge` | None | `orchestrator.research_graph` | **NONE** (No UI trigger) | **PARTIAL** |
| `POST /api/v1/calculator/weakest-point` | None | `orchestrator.adversarial_engine` | **NONE** (No UI trigger) | **PARTIAL** |
| `POST /api/v1/payment/checkout` | None | Midtrans Snap Gateway | `index.html` (`openCheckoutModal`) | **REAL** |
| `POST /api/v1/payment/webhook` | SHA-512 | `payment_transactions`, `user_entitlements` | Midtrans Server Webhook | **REAL** |
| `GET /api/v1/account/billing` | Bearer/User | `payment_transactions` | `index.html` (`fetchBillingHistory`) | **REAL** |
| `POST /api/v1/auth/session` | None | `SessionService`, `arena_users` | `index.html` (`triggerGoogleAuth`) | **REAL** |
| `GET /api/corpus/search` | None | Bible Corpus Engine | **NONE** | **UNCONNECTED** |
| `WS /api/arena/ws` | None | `arena_service` (Live Engine) | `arena.html` (`connectWebSocket`) | **REAL** |
| `GET /api/arena/state` | None | `arena_service` FSM State | `arena.html` (`fetchState`) | **REAL** |
| `POST /api/arena/action` | None | `arena_service` Operator Dispatch | `arena.html` (`sendAction`) | **REAL** |
| `POST /api/arena/golden_match` | None | `arena_service` Match Fixture | `arena.html` (`loadGoldenMatch`) | **REAL** |
| `POST /api/training/session/*` | None | `DebateTrainingService` (10 APIs) | **NONE** | **UNCONNECTED** |

---

## 4. Key Findings by Domain

### 4.1. Calculator & Adversarial Tools
- **LangGraph Integration**: `POST /api/v1/calculator/analyze` invokes the full LangGraph pipeline. In smoke tests, it produced 7 real Greek/critical evidence items with provenance hashes.
- **Frontend Display Deficiencies**:
  - The DOM template in `index.html` displays arguments, rebuttal, weakness, and evidence, but completely omits `counterargument`, `open_questions`, and `debate_preparation` from the rendered result card.
  - The three backend adversarial endpoints (`/calculator/challenge`, `/calculator/weakest-point`, `/calculator/source`) are fully functional in backend tests, but have NO corresponding trigger buttons in the frontend UI.
  - The "Inspect" button on source citations opens a drawer containing hardcoded static text ("Codex Sinaiticus Yohanes 10:30") rather than fetching dynamic source provenance from `/calculator/source`.

### 4.2. Epistemic & Philology Engine (MP3)
- The entire 24-point Master Prompt #3 Epistemic Engine (Epistemic Firewall, Claim Atomicity DAG, Source Criticism, Textual Criticism Firewall, Translation Audit, Concession Extraction, Uncertainty Calibration, Fallacy Detection) is complete in Python (`orchestrator/`) with 26/26 tests passing.
- None of these advanced epistemic reports are exposed as standalone inspection views in the web UI.

### 4.3. Debate Arena (Canonical 3-vs-3)
- The Canonical Specification (`docs/architecture/debate-arena-canonical-specification.md`) is 100% authoritative: 3-vs-3 human debaters, 5 rounds, 16-state FSM, 9 AI supervisory roles, 100-point rubric.
- The engine in `polya_runtime.debate_engine` and the client in `web/static/arena.html` are fully operational and synchronized over WebSocket.
- **Critical Architectural Disconnection**: `arena.html` is hosted at `/arena`, but the main Research OS in `index.html` has NO navigation links or buttons leading to it.

### 4.4. Research OS, Themes, & Knowledge Base
- `/pipeline` in `index.html` is a static visual badge layout. There is no live event stream showing LangGraph execution nodes in real-time.
- `/themes` contains a single hardcoded theme ("Friksi Paulus vs Petrus") and 6 static tabs without backend queries.
- `/knowledge` contains a static SVG graph with 3 dummy nodes ("Klaim Keilahian", "Yohanes 10:30", "Codex Sinaiticus") rather than reading from `bible_engine/graph.py` or `data/polya_arena.db`.

### 4.5. Case File Persistence
- `data/polya_arena.db` contains the table `case_files_v2` with 195 test-generated records.
- However, the web API does not insert newly generated analyses into `case_files_v2`. Results are held ephemerally in client memory and lost on refresh.

### 4.6. Auth, Quota, & Billing
- Quota: 5 free analyses per user. Strictly enforced server-side. The 6th request triggers HTTP 402 ("QUOTA_EXHAUSTED"). Idempotency prevents double consumption.
- Midtrans: SHA-512 signature key verification is enforced. Simulator flags are ignored. Valid webhooks successfully transition users to `PREMIUM_ACTIVE`.

---

## 5. Security Audit Findings
1. **SECURITY-001 (MEDIUM)**: Cleartext Midtrans Server Key and Google OAuth secrets exist in `web/.env.staging` and `web/.env`. (Remediation: Inject via container runtime secrets).
2. **SECURITY-002 (MEDIUM)**: `POST /api/v1/context` and `GET /api/v1/entitlements/usage` accept unauthenticated `user_id` query parameters. (Remediation: Bind to verified session token).
3. **SECURITY-003 (LOW)**: Hardcoded Google OAuth Client ID in client-side HTML. (Remediation: Expose via public config endpoint).

---

## 6. Priority Backlog
### P0 (Core Usability Blockers)
1. Wire Calculator Adversarial Controls: Add "Challenge Argument", "Weakest Point", and dynamic "Show Source" buttons to `/calculator`.
2. Render Missing Case File Fields: Inject `counterargument`, `open_questions`, and `debate_preparation` into `renderCaseFile()`.
3. Persist Case Files: Insert new analyses into SQLite `case_files_v2` table in `/api/v1/calculator/analyze`, and provide `GET /api/v1/case-files` listing.
4. Link Debate Arena: Add navigation links to `/arena` in `index.html` sidebar and dashboard.

### P1 (Dynamic Engine Wiring)
5. Wire Dynamic Knowledge Base: Connect `/knowledge` to `bible_engine/graph.py` and `/api/corpus/search`.
6. Wire Dynamic Themes: Create `GET /api/v1/themes` reading from `data/video_pipeline/themes`.
7. Pipeline Real-Time Telemetry: Stream LangGraph execution progress via SSE to `/pipeline`.
8. ZUMA Training UI: Build UI interface for 1-on-1 sparring connected to `/api/training/session/*`.

### P2 (Secondary Features)
9. Wire Global Search: Connect `handleGlobalSearch()` to `/api/corpus/search`.
10. Epistemic Status Tags: Display epistemic certainty badges (`DIRECTLY_VERIFIED`, `INFERRED`, etc.) on evidence items.

### P3 (Polish)
11. Debate Arena audio bell cues.
12. 17-language UI label dictionary localization.

---

## 7. Report Artifact Verification
- `docs/audits/website-integration-audit.md`: Written and verified on disk.
- `docs/audits/website-integration-matrix.json`: Written and verified on disk.
- `docs/audits/website-integration-audit.txt`: Written and verified on disk.
