---
name: run-cv-platform
description: Start, run, smoke-test and screenshot the Careerly (CV-Platform) app - FastAPI backend + React/Vite frontend. Use when asked to run or start the app, check it works, drive the UI, take a screenshot of a page, or verify an API/frontend change end to end.
---

Careerly is a FastAPI backend (`api/`, port 8000) plus a React/Vite frontend (`frontend/`, port 5173)
backed by the shared AWS Postgres + S3 dev resources in `.env`. Drive it with the scripts in this
directory: `start.sh` → `smoke.py` (API checks, `--ui` adds a headless-Chrome run of `drive_ui.mjs`) → `stop.sh`.

All paths are relative to the repo root. Verified on Windows 11 with Git Bash.

## Prerequisites

- `venv/` on **Python 3.12** with `requirements.txt` installed, Node + npm, `frontend/node_modules`,
  Google Chrome installed (the driver uses `channel: 'chrome'`, no Playwright browser download).
- `.env` at the repo root with `DATABASE_URL`, AWS and Anthropic keys (gitignored - ask the team).

```bash
./venv/Scripts/python -m pip install -r requirements.txt
./venv/Scripts/python -m pip check        # must say "No broken requirements found"
```

## Setup (once)

Install the browser driver library into the skill's gitignored `.deps/`:

```bash
npm install --prefix .claude/skills/run-cv-platform/.deps playwright-core
```

## Run (agent path)

```bash
bash .claude/skills/run-cv-platform/start.sh                       # starts both, waits until they serve
./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py      # API checks only
./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py --ui # + browser flow
./venv/Scripts/python .claude/skills/run-cv-platform/smoke.py --ui dashboard profile  # screenshot pages instead
bash .claude/skills/run-cv-platform/stop.sh
```

`smoke.py` creates two throwaway users (`smoketest-owner|other-<epoch>@example.com`) with profiles in
the **real dev database**, runs the checks, and always deletes them in a `finally` (all tables cascade
from `users`). It prints `PASS/FAIL` per check and ends with `ALL PASSED` (exit 0) or `FAILURES:` (exit 1).
It never calls Claude.

| What | Checks |
|---|---|
| API | invalid signup email → 422; signup/login; wrong password → 401; application add/update/delete; no token → 401; other user's application → 404 and hidden from their list; blank job description → 422 (cover letter) / 400 (tailored CV) |
| `--ui` default flow | signup page shows "Please enter a valid email address." for `a@b`; login lands on `/dashboard`; tracker add → status Offer → reload persists → delete → reload gone; fails on any browser console error |
| `--ui <page> ...` | logs in and screenshots each page (e.g. `dashboard profile`); fails on console errors |

Screenshots → `.claude/skills/run-cv-platform/out/*.png` (a `failure.png` is written on error).
Server logs → `.claude/skills/run-cv-platform/out/api.log` and `web.log`. **Look at the screenshots.**

To drive the UI with an existing account instead: `node .claude/skills/run-cv-platform/drive_ui.mjs <email> <password> [page ...]`.
Extend `drive_ui.mjs` when a change touches a page it doesn't cover - copy the tracker block's pattern
(wait for the API response, assert its status, reload, assert, screenshot).

## Run (human path)

```bash
./venv/Scripts/python -m uvicorn api.main:app --port 8000   # Ctrl-C to stop
cd frontend && npm run dev                                  # http://localhost:5173
```

## Test

```bash
./venv/Scripts/python -m pytest -q
```

Fast, offline (DB, S3 and Claude are faked in `tests/test_api.py`). 63 passed at time of writing.

## Gotchas

- **Smoke tests write to the shared dev database.** The cleanup is in a `finally`, but if the process is
  killed mid-run, delete leftovers: `DELETE FROM users WHERE email LIKE 'smoketest-%@example.com'`.
- **Claude-backed endpoints cost money** - the scripts deliberately stop before any `call_claude`
  (validation rejects blank job descriptions first). Don't add generation calls to the smoke run casually.
- **A CORS error in the browser usually means a 500.** FastAPI's CORS middleware doesn't add headers to
  unhandled-exception responses, so the browser reports "blocked by CORS policy". Read `out/api.log` for
  the real traceback.
- **Git Bash rewrites `/dashboard` into `C:/Program Files/Git/dashboard`** when passed to Windows
  programs. Pass page names without the leading slash; the driver adds it.
- **Stopping `npm run dev` leaves Vite running** on 5173 (npm doesn't forward the kill). `stop.sh` kills
  the listener by port, and only if its command line is uvicorn/vite.
- **`database/db_client.py` calls `logging.basicConfig(INFO)` on import**, so any script importing it
  logs every httpx request. `smoke.py` sets the `httpx` logger to WARNING.
- **The venv can end up with Python 3.14 wheels** (`*.cp314-*.pyd`) even though it runs 3.12 - imports
  then fail with `No module named 'pydantic_core._pydantic_core'` / `'jiter.jiter'` / `'psycopg2._psycopg'`.
  `pip check` lists them as "not supported on this platform". Fix by reinstalling the same versions:
  `./venv/Scripts/python -m pip install --force-reinstall --no-deps <pkg>==<version>`. Always install
  with `./venv/Scripts/python -m pip`, never a bare `pip`.
- **Schema isn't migrated automatically** - nothing calls `init_db()`. When the code adds a table, the
  live DB won't have it until someone runs `./venv/Scripts/python -c "from database.db_client import init_db; init_db()"`
  (only `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`, safe to re-run). On 2026-10-04
  `tailored_cv_results` and `password_reset_tokens` were missing, which made `GET /profile/history` 500.

## Troubleshooting

- **`Port 8000 or 5173 already in use - run stop.sh first.`**: a previous run is still up. `bash .claude/skills/run-cv-platform/stop.sh`.
- **`API not reachable at http://localhost:8000`**: run `start.sh` first; if it timed out, read `out/api.log`.
- **`UI FAILED: browser errors: Access to XMLHttpRequest at 'http://localhost:8000/profile/history' ... blocked by CORS policy`**:
  a 500 from the API (see the CORS gotcha). It was `psycopg2.errors.UndefinedTable: relation "tailored_cv_results" does not exist` - fixed by running `init_db()` (see Gotchas).
- **`ValueError: the environment variable is longer than 32767 characters`** (pytest on Windows): a
  `parametrize` case containing a huge value became the test ID - give it `ids=[...]`.
