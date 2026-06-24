# PigOS Overnight Market QA — P0 Baseline (2026-06-24)

Repo: `c:\dev\PigOS` · Branch: `main` · QA evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

---

## 1. Stack health — PASS

| Target | Expected | Actual | Result |
|--------|----------|--------|--------|
| `http://localhost:3000` | 307 | **307** (`curl -s -o /dev/null -w "%{http_code}"`) | PASS |
| `http://localhost:8000/health` | ok | **`{"status":"ok","version":"0.1.0"}`** | PASS |

Both services up. Web returns 307 (middleware locale/auth redirect), API health ok.

---

## 2. Baseline tests — PASS

| Check | Command | Result |
|-------|---------|--------|
| Backend pytest | `cd api && uv run pytest tests/ -q` | **485 passed in 49.75s** — 0 fail/error |
| Frontend typecheck | `cd src && npx tsc --noEmit` | **EXIT=0** (clean, no type errors) |

Evidence: pytest tail shows `============================ 485 passed in 49.75s =============================`. tsc printed no diagnostics, exit 0.

---

## 3. Git status — dirty (not clean)

- Branch: `main` (tracking `origin/main`).
- 14 modified files: all are E2E screenshot artifacts under `src/e2e-live/_uat_tmp/shots/*.png` (dash_/sows_ × 7 locales). No source code modified.
- 2 untracked docs: `handoff/PROMPT_data_integrity_audit.md`, `handoff/pigplan-domain-integrity.md`.
- Per guardrail: no auto-commit. Working tree changes are pre-existing artifacts/handoff notes, not introduced by this QA run.

---

## 4. RBAC role model (discovered from code, not assumed)

Source of truth: `api/app/core/permissions.py`, `api/app/core/dependencies.py`, `api/app/db/models/platform.py`.

### Role storage
- `users.system_role` (String(30), default `FARM_OWNER`) — primary RBAC field.
- `users.role` (String(30), default `FARM_WORKER`) — **legacy**; mapped via `LEGACY_SYSTEM_ROLE_MAP` (`ADMIN→SUPER_ADMIN`, `COMPANY→VENDOR_ADMIN`).
- `user_farms.role_override` (String(30), nullable) — **per-farm** role for multi-farm users; NULL falls back to system role.
- `effective_system_role(user)`: returns system_role if known, else maps legacy, else **fail-safe `FARM_OWNER`**. Always within `_KNOWN_ROLES`.

### Full role list (10 roles, from `permissions.py`)

**ORG_LEVEL_ROLES** (org-tree scoped, recursive CTE, max depth 8):
- `SUPER_ADMIN` — all orgs + all active farms (platform operator)
- `VENDOR_ADMIN`
- `DISTRIBUTOR_ADMIN`
- `DEALER_ADMIN`

**FARM_LEVEL_ROLES** (scoped via `user_farms` membership):
- `FARM_OWNER`
- `FARM_MANAGER`
- `FARM_WORKER`
- `VET`
- `VIEWER`
- `API_CLIENT`

### Permission partitions
- **WRITE_ROLES** (7): SUPER_ADMIN, VENDOR_ADMIN, DISTRIBUTOR_ADMIN, DEALER_ADMIN, FARM_OWNER, FARM_MANAGER, FARM_WORKER.
- **READ_ONLY_ROLES** (3): VET, VIEWER, API_CLIENT.
- `is_org_admin()` = role ∈ ORG_LEVEL_ROLES. `is_write_allowed()` = role ∈ WRITE_ROLES.

### Enforcement guards (dependencies.py)
- `get_farm_context` / `FarmDep` — validates user↔farm; SUPER_ADMIN bypass, org roles via org-tree, farm roles via `user_farms`. Inactive/missing farm → 403 ForbiddenError.
- `require_role(*roles)` — global system_role gate (403 if not matched).
- `require_super_admin` / `SuperAdmin` — SUPER_ADMIN only (admin console `/admin`).
- `require_farm_role(*roles)` — per-farm role gate via `effective_farm_role()` (multi-farm correct; uses role_override).
- `require_addon(addon_code)` — 402 if farm lacks active AddonSubscription.

Access resolution: `get_accessible_org_ids`, `get_accessible_farm_ids`, `can_access_farm` — SUPER_ADMIN = all; org admins = recursive org-tree of active farms; farm users = explicit `user_farms` rows. All filter `farms.active = TRUE`.

---

## 5. KR routing decision — **(b) TEST TARGET** (KR signup is allowed)

Evidence (no KR block / no PigPlan-handoff anywhere):
- `src/middleware.ts`: redirects are only (a) admin-host/admin-path domain separation and (b) auth-session gate (`pigos_session` cookie → `/login`). Locale auto-detect maps `ko`→Korean UI but does **not** block. No country/geo/KR branch.
- `src/app/onboarding/page.tsx`: `COUNTRIES` list includes `{ value: "KR", label: "South Korea" }` and KR is the **default** (`country: "KR"` in initial form state). Selectable, no gating in `canProceed()`.
- Backend grep (`api/app`) for `KR | Korea | pigplan | block | allowed_countr | reject_country`: only benign references — `country` is a free-form ISO-3166-1 alpha-2 attribute on farm/org used for benchmarks (`master.py` regional_prevalence/approved_regions), disease prevalence, and RuleContext.country. **No signup/onboarding/farm-creation gate on country.**

Conclusion: The product does NOT block or redirect KR signups in code. Any "KR → PigPlan" positioning is business/strategy, not enforced in this codebase. KR is a valid QA test target. (If product intends to block KR, that is a KNOWN_GAP — not implemented.)

---

## Summary
- Stack: PASS (web 307, api ok 0.1.0).
- Tests: PASS (pytest 485 passed, tsc exit 0).
- Git: dirty — only PNG screenshot artifacts + 2 untracked handoff docs; no source changes (no commit per guardrail).
- RBAC: 10 roles — 4 org-level (SUPER_ADMIN, VENDOR_ADMIN, DISTRIBUTOR_ADMIN, DEALER_ADMIN) + 6 farm-level (FARM_OWNER, FARM_MANAGER, FARM_WORKER, VET, VIEWER, API_CLIENT). Write=7, ReadOnly=3 (VET/VIEWER/API_CLIENT).
- KR: judgment (b) TEST TARGET — no KR block/redirect in code; KR is default onboarding country.
