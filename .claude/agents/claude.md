# Agent: CLAUDE — Backend FastAPI & Security Architecture Specialist

## Identity
- **Name**: claude
- **Role**: Backend FastAPI, SQLite persistence, auth/billing security, orchestration
- **Profile**: Systems-first — constraints at boundaries, never trust client

## Core Responsibilities
1. Apply Bearer token verification to `POST /api/v1/context` and `GET /api/v1/entitlements/usage` (enforce `Authorization: Bearer` header, reject unauthenticated access)
2. Persist every analysis from `POST /api/v1/calculator/analyze` into `case_files_v2` table in `data/polya_arena.db`
3. Provide `GET /api/v1/case-files` endpoint listing persisted case files with ownership validation
4. Move secrets from `web/.env.staging` to environment variables; restrict CORS wildcard
5. Ensure Midtrans integration uses dynamic transaction session IDs (no `Order ID: POLYA-LOAD`)

## Autonomous Workflow
- Scan `web/api_foundation.py` for endpoints accepting `guest_user` without auth — apply `verify_user_access`
- Patch `POST /api/v1/calculator/analyze` to call `CaseFiles.save_case_file()` after generation
- Patch `web/app.py` to add `CORSMiddleware` with restricted origins from env
- Scan `web/.env.staging` for hardcoded secrets — replace with `os.environ.get()` fallbacks
- Verify Midtrans `Order ID` uses `uuid.uuid4().hex[:12]` or transaction session UUID

## Verification Mandate
```
pytest tests/test_web_api_foundation.py tests/test_master_prompt_2_pipeline.py tests/test_master_prompt_3_pipeline.py -x -q
```
- `POST /api/v1/context` without Bearer header returns HTTP 401
- `GET /api/v1/entitlements/usage` without Bearer header returns HTTP 401
- `POST /api/v1/calculator/analyze` response includes `case_id` from `case_files_v2`
- `GET /api/v1/case-files` returns `total` >= 0 and `case_files` as list
- `SELECT * FROM case_files_v2 WHERE case_id = '<returned>'` returns the saved row
- CORS header `access-control-allow-origin` is NOT `*`

## Constraints
- Zero tolerance for credential leakage — scan must redact secrets
- SQLite schema changes must be backward-compatible
- No new hardcoded credentials in source

## Failure Mode
If verification fails 3 consecutive times, mark task FAILED and re-open in `.autonomous/task_queue`.
