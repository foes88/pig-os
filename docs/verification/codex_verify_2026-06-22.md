# Codex Independent Verification - 2026-06-22

Source prompt: `docs/CODEX_VERIFY_2026-06-22.md`

Rules followed: no push, no production DB/deploy/env changes. Local dev stack only. Results below are based on executed commands and live local checks.

## Summary

Overall: **yellow / issue count: 1**

Issue found:
- [FAIL] `docs/PRESS_RELEASE_PigOS_draft.md:42` and `docs/PRESS_RELEASE_PigOS_EN.md:29` contain an unsupported competitor-wide claim:
  - KO: "SME 최적화·무료 진입·오픈 API·AI를 동시에 만족하는 제품은 현재 없다"
  - EN: "No competitor today satisfies SME-optimization, free entry, open API, and AI simultaneously."
  This is not the literal "first/only" wording, but it is the same kind of substantiation-sensitive market exclusivity claim. It should be removed, softened, or backed by evidence before external release.

## 0. Stack Health

- [PASS] `curl.exe -s -o NUL -w "%{http_code}" http://localhost:8000/health` -> `200`
- [PASS] `curl.exe -s -o NUL -w "%{http_code}" http://localhost:3000/login` -> `200`

## 1. Baseline Regression

- [PASS] `cd api; uv run pytest tests/ -q` -> `395 passed in 41.72s`
- [PASS] `cd src; npx playwright test --config=playwright.live.config.ts` -> `33 passed (1.2m)`
  - Note: first sandboxed attempts failed on generated `test-results` cleanup / worker spawn permissions. Re-ran with escalation for local generated test output and Playwright worker launch.
- [PASS] `cd src; npx tsc --noEmit` -> exit 0
- [PASS] `cd src; npm run build` -> compiled successfully, generated static pages `(44/44)`
  - Build emitted existing metadata warnings (`metadataBase`, `themeColor` placement), but build succeeded.

## 2a. KPI / Alerts / Sows Hifi

- [PASS] Raw hex search:
  - `rg -n "#[0-9a-fA-F]{6}" "src/app/(app)/kpi" "src/app/(app)/alerts" "src/components/ui/charts.tsx"` -> no matches.
- [PASS] `/kpi` live DOM check:
  - Independent Playwright script found `PSY=true`, `NPD=true`, AI/summary area present, `main svg` count `5`.
- [PASS] Loss amount trap:
  - `src/app/(app)/kpi/page.tsx` renders loss amount only from `data.estimated_loss`.
  - If absent, it renders severity counts only. Search found no fake per-signal KRW/amount rendering.
- [PASS] `/alerts` live DOM check:
  - Severity tabs present, signal links count `3`.
  - `/alerts/open_overdue_mating` detail check found rule, current value, related animals, and recommended actions sections.
- [PASS] `/sows` risk column:
  - Live DOM check found Risk column and `14` risk cells.
  - `rg -n "\b(cyan|slate|orange|blue)-|#[0-9a-fA-F]{6}" "src/app/(app)/sows/page.tsx"` -> no matches.

## 2b. Reports Hub

- [PASS] `ReportsTabs` static search:
  - `/reports`, `/reports/reproduction`, `/reports/farrowing`, `/reports/grow-finish`, `/reports/comprehensive-daily` each import and render `ReportsTabs` once.
- [PASS] Live DOM check:
  - Each of the five report URLs had `5` `reports-tab-*` elements.
- [PASS] `/reports` BarChart de-hex:
  - `src/app/(app)/reports/page.tsx` and `src/components/ui/charts.tsx` use `currentColor`; raw hex search found no matches in the checked paths.

## 2c. Korean Language Gate

- [PASS] Login page:
  - Live DOM: `language-option-ko` count `0`; options were `English`, `中文`, `Español`, `Tiếng Việt`.
- [PASS] FARM_OWNER (`e2e@pigos.io / e2e!2026pw`):
  - `NEXT_LOCALE=ko` forced cookie, 5 reload checks with `networkidle`: switcher value `en`, `ko` option count `0`, no Hangul UI lines after settle.
- [PASS] SUPER_ADMIN (`admin@pigos.io / admin!2026pw`):
  - Live DOM: Topbar `option[value="ko"]` count `1`.
- [PASS] E2E:
  - `npx playwright test --config=playwright.live.config.ts -g "i18n 5-language"` -> `2 passed (14.1s)`
- [PASS] i18n parity:
  - Node key script -> `en 1273 ko 1273 missing []`

## 2d. Admin Console Phase 0

- [PASS] Targeted tests:
  - `cd api; uv run pytest tests/integration/test_admin_console.py -q` -> `5 passed in 3.17s`
- [PASS] Live API gate:
  - `admin@pigos.io` -> `/api/v1/admin/overview` status `200`, keys `farms,organizations,sows,users`, values are integers.
  - `e2e@pigos.io` -> status `403`.
  - No token -> status `401`.
- [PASS] Frontend gate:
  - `admin@pigos.io` -> `/admin`, shell and overview cards present.
  - `e2e@pigos.io` -> `/admin` redirected to `/`.
- [PASS] Router-wide gate:
  - `api/app/routers/admin/admin.py` uses `dependencies=[Depends(require_super_admin)]` on the admin router.
- [PASS] `system_role` trap:
  - One-off local script with `role=SUPER_ADMIN`, `system_role=FARM_OWNER`:
    - `effective_system_role FARM_OWNER`
    - `require_super_admin BLOCK ForbiddenError Required role: SUPER_ADMIN`

## 2e. Press Release Facts

- [PASS] KO/EN both state 4 target markets excluding Korea, while preserving Korean/PigPlan heritage.
- [PASS] KO/EN both state six public languages excluding Korean.
- [PASS] KO/EN both use future launch timing for July 1, 2026.
- [PASS] KO/EN pricing is undisclosed/in development.
- [PASS] Contact is company-level only: `wiselake@wiselake.co.kr`, `pigos.io`.
- [FAIL] Unsupported exclusivity/no-competitor claim remains. See Summary.

## 3. Adversarial Checks

- [PASS] Tenant isolation:
  - OWNER farm: `932208a6-e693-4f79-bd7a-aa41fb5e109c`
  - Other existing farm selected via SUPER_ADMIN `/api/v1/farms`: `da64cb26-b46a-4818-a56d-1488940aa805`
  - FARM_OWNER access to other farm:
    - `/api/v1/farms/{other}/sows` -> `403`
    - `/api/v1/farms/{other}/reports/production-summary?...` -> `403`
    - `/api/v1/farms/{other}/events/ledger` -> `403`
- [PASS] Korean gate bypass:
  - `NEXT_LOCALE=ko` + non-admin repeated reloads settled to `en`, no Korean option, no settled Hangul UI lines.
- [PASS] Delete event rollback:
  - Full live run included `event-rollback.live.spec.ts` -> passed.
  - `cd api; uv run pytest tests/unit/test_event_rollback.py -q` -> `5 passed in 3.42s`
- [PASS] `/admin` route protection:
  - Backend router-wide dependency verified.
  - Frontend owner redirect and backend 403 verified.

## Notes

- Local `uv run` repeatedly printed a package-cache warning about `sqlalchemy-2.0.49.dist-info` missing `RECORD`, while tests still passed. This looks environmental rather than an application failure.
- Worktree already contained unrelated modified/untracked files during verification; they were not reverted.
