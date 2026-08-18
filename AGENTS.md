# AGENTS.md

Persian-language copper-mining data Q&A assistant ("دستیار هوشمند مس"). An LLM agent answers questions about `Employees`, `Equipment`, and `Production` data stored in MySQL by generating SQL.

## Architecture

- `agent.py` — core pipeline: security checks → SQL generation → run → final answer, all via a local Ollama LLM (`http://127.0.0.1:11434`, default model `qwen3:4b-instruct-2507-q4_K_M`, override with `MODEL_NAME` env var). Deliberately strips `HTTP_PROXY`/`HTTPS_PROXY` and sets `NO_PROXY=localhost,127.0.0.1` so Ollama calls never route through a proxy — don't remove.
- `api_server.py` — FastAPI wrapper on port **8000** exposing the agent to the Next.js frontend. Requires a valid JWT; role/user never trusted from request body/URL (see `require_matching_user`). `/api/ask/stream` yields SSE events `meta` → `token`* → `done` (`frontend/lib/api.ts` parses this contract).
- `app.py` — legacy Streamlit UI (same backend, session-based login). `frontend/` — Next.js 16 App Router UI (current).
- `chat_storage.py` — chat history, `AppUsers` (login/RBAC), and `AuditLog` tables, written with hardcoded SQL (never LLM-generated). Uses its own engine + pooled connection. Also defines `is_session_owner()` (IDOR guard), `list_audit_log()` (manager review), and `CONFIDENTIAL_CATEGORIES` (redacts stored question text).
- `auth.py` — PBKDF2-SHA256 hashing (`<iterations>$<salt_hex>$<hash_hex>`).
- `schema_constants.py` — **single source of truth** for every categorical value (Mines, Genders, Departments, JobTitles, Employee Shifts incl. `روز`, Equipment Categories/Manufacturers/Statuses incl. `در حال کار`, Production Shifts) plus `fmt_values()` for LLM prompt rendering. `agent.py` builds TABLE_CONTEXT and `FIXED_WORKFORCE_QUERY` from these constants — always edit the constants, never hardcode new values in prompts.
- `check_schema_consistency.py` — verifies the constants against `data/*.xlsx` (and live DB with `--db`). Run it after touching `schema_constants.py`.
- `data/*.xlsx` — source data. `load_data.py` **drops and recreates** the three tables from these files (destructive; de-dupes on primary key). `data 2/` is a gitignored leftover.
- Root `Columns.py`, `check_duplicates.py`, `test_connection.py`, `Unique Data.py`, `Storage Chats.py` are one-off debugging helpers, not part of the app — ignore them.

## Setup / run

- MySQL must be running with the `mining_ai` DB, and Ollama must be running locally with the model pulled. `.env` (gitignored) holds `DB_*` and `JWT_SECRET`; the app will not start without it. Copy `.env.example` as a template (see `CORS_ORIGINS` for the allowed-frontend list and `MODEL_NAME` for the model).
- Use the venv Python (`venv\Scripts\python.exe` or activate `venv`). `requirements.txt` is generated via `pip freeze` — pin to current versions, do not upgrade packages.
- Backend: `venv\Scripts\python.exe -m uvicorn api_server:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev` (port 3000). The backend URL is `http://localhost:8000` by default and overridable via `NEXT_PUBLIC_API_BASE` (see `frontend/.env.local.example`). CORS defaults to `http://localhost:3000`, overridable via `CORS_ORIGINS`.
- Seed users once: `python_create_initial_users.py` (default: `staff1`/`super1`/`manager1`, password `ChangeMe123`). Note the file name has no `python_` prefix in its own docstring.
- Data (re)load: `python load_data.py` (from repo root, needs `data/` present).
- If the backend throws `[WinError 10054]` (idle MySQL connection dropped), it's a known issue already handled by `pool_pre_ping`/`pool_recycle` in both `agent.py` and `chat_storage.py` — don't change those settings.

## Testing

Tests use **pytest** (`tests/`), split into two markers:
- Offline (no marker) — pure functions / stubbed agent, run anywhere: `venv\Scripts\python.exe -m pytest -m "not integration"`.
- `integration` — need a live MySQL DB (skipped automatically when unavailable): `venv\Scripts\python.exe -m pytest -m integration`.
- `tests/conftest.py` stubs `SQLDatabase` before `agent.py` imports so the offline suite never needs MySQL/Ollama; integration tests use `chat_storage.storage_engine` directly.
- The old self-test scripts still work as smoke tests: `python chat_storage.py` (AppUsers + audit redaction), `python auth.py` (hashing round-trip).
- Frontend: `npm run lint` (eslint) and `npm run build` (typechecks via Next) in `frontend/`. Known pre-existing failures unrelated to the agent work: `app/chat/page.tsx` (react-hooks set-state-in-effect) and `app/page.tsx` + `components/demo.tsx` (`Spotlight` has no `fill` prop).

## Security model — do not weaken

Three independent stages in `agent.py` must all pass before SQL touches the DB: LLM classification → regex guards → generated-SQL inspection. Preserve all three and the audit logging (`log_audit_event`).
- Roles `staff` / `supervisor` / `manager` come **only** from authenticated login/JWT, never from question text.
- `staff` may never see salary data, even aggregated; `manager` may do individual lookups but never `SELECT *`. `REFUSED_INDIVIDUAL_LOOKUP` / refusal messages are role-sensitive.
- `CONFIDENTIAL_CATEGORIES` in `chat_storage.py` redact the stored question text for individual-data questions.
- Login is throttled in `api_server.py` (HTTP 429 after repeated failures, never a permanent lockout); session ownership is enforced via `is_session_owner`; `GET /api/audit` is manager-only.

## Persian-data gotchas (frequently the root cause of "wrong answer")

- Mine/Department/JobTitle values are stored in Persian; copy them **verbatim** into SQL, never translate. Equipment `Category`/`Manufacturer` stay in English.
- Mine names contain a ZWNJ half-space (e.g. `خاتون‌آباد`, `برق‌کار`). Always match with `LIKE '%خاتون%'`, never `= 'خاتون‌آباد'`.
- Never join `Employees` to `Production` row-by-row (one employee appears in many production rows → massively inflated sums). Pre-aggregate each table by `Mine`, then join the aggregates.
- Salary/OvertimePay are in **تومان** (not ریال); answers must label the currency. RecoveryRate is a percentage (0–100); DowntimeHours is in hours, not a percentage.

## Frontend notes

- `frontend/lib/api.ts` uses `NEXT_PUBLIC_API_BASE` (default `http://localhost:8000`) and clears `rad_ai_token` / `rad_ai_user` + redirects home on HTTP 401. `rad_ai_token` / `rad_ai_user` live in localStorage.
- `frontend/AGENTS.md` and the `<!-- BEGIN:nextjs-agent-rules -->` block are **auto-written by `next dev`** (Next 16 has breaking changes — check `node_modules/next/dist/docs/`). Commit the block rather than deleting it; do not edit it by hand.
- All UI copy is Persian (RTL); preserve ZWNJ characters when editing Persian strings.