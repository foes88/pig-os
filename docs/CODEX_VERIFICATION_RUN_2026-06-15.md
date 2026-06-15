# Codex Verification Run - 2026-06-15

Scope: verified the current dirty worktree at `C:\dev\PigOS`. No commit and no push were made. `.git\index.lock` did not exist, so `git reset` was not run in order to preserve the existing staged/unstaged state.

## Environment

- Docker: 19.03.1
- Python: 3.14.2
- uv: 0.7.19
- system Node: v20.11.1
- temporary Node used for Vitest compatibility check: v22.22.3 via `npx -y node@22`

## Results

| Check | Command | Result |
|-------|---------|--------|
| Backend deps | `cd api && uv sync` | PASS |
| Backend unit tests | `cd api && uv run pytest tests/unit -q` | PASS: 219 passed |
| Docker services | `docker compose up -d postgres redis` | PASS |
| Test DB | `docker exec pigos-postgres psql -U pigos -tc "SELECT 1 FROM pg_database WHERE datname = 'pigos_test';"` | PASS: DB exists |
| Alembic | `cd api && uv run alembic upgrade head` | PASS: upgraded through `f1a2b3c4d5e6` |
| Backend full tests | `cd api && uv run pytest tests/ -q` | PASS: 249 passed |
| Ruff | `cd api && uv run ruff check .` | FAIL: 53 fixable lint errors |
| Frontend deps | `cd src && npm install` | PASS with EBADENGINE warnings |
| TypeScript | `cd src && npx tsc --noEmit` | PASS: 0 errors |
| Vitest deps | `cd src && npm i -D vitest jsdom @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event` | PASS with EBADENGINE warnings |
| Vitest on system Node | `cd src && npm test -- --run` | FAIL: Node v20.11.1 lacks `node:util` export `styleText` required by installed Vite/Rolldown |
| Vitest on Node 22 | `cd src && npx -y node@22 node_modules\vitest\vitest.mjs --run` | PASS: 3 files, 7 tests |
| API health | `curl http://localhost:8000/health` after `docker compose up -d` | PASS: 200, `{"status":"ok","version":"0.1.0"}` |
| API login | POST `/api/v1/auth/login` with `test001@pigos.io` / `12312300` | PASS: 200, token returned |
| API protected smoke | alerts overdue, config repro, reproduction report | PASS: all 200 |

## Ruff Failure Summary

- `alembic/env.py`: `I001`
- Alembic versions: `I001`, `UP035`, `UP007`
- `scripts/seed_master.py`: `I001`
- `test_auth.py`, `test_auth2.py`: `E401`, `I001`
- Ruff reported: `Found 53 errors. 53 fixable with the --fix option.`

## Frontend Notes

- The installed Vite/Vitest stack requires Node `^20.19.0` or Node `>=22.12.0` for several packages, but the system Node is `v20.11.1`.
- `npm` had `offline = true` in the environment. The Rolldown Windows native optional binding was present in `package-lock.json` but missing in `node_modules`; temporarily installing `@rolldown/binding-win32-x64-msvc@1.0.3` directly allowed the Node 22 Vitest run to pass. The direct manifest entry was removed after verification.
- `npm audit` reports 3 vulnerabilities: 2 moderate, 1 high.

## Not Run

- Manual UI 11-item browser checklist was not completed in this pass. Automated frontend checks and API smoke were completed.
