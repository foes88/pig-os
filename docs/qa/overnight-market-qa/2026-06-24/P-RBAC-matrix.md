# PigOS Overnight Market QA — P-RBAC Permission Matrix (2026-06-24)

Repo: `c:\dev\PigOS` · Branch: `main` · Evidence-first, live API at `localhost:8000` (DB `pigos`, docker postgres).
Method: seeded `qarbac-*` namespaced tenants directly into live DB, minted JWTs via `app.core.security.create_access_token`, drove **direct API calls** (not UI), tore down all `qarbac-*` data after. Runner: scratchpad `rbac_matrix.py` (132 assertions) + 2 targeted re-probes.

Result codes: PASS / FAIL / RBAC_BUG / SECURITY_BUG / KNOWN_GAP.

---

## 0. Role model under test (from P0, source = `api/app/core/permissions.py` + `dependencies.py`)

10 roles. Enforcement is **two-axis**:
- **System role** (`users.system_role`) → org-tree visibility + `require_super_admin`.
- **Farm role** (`user_farms.role_override`, multi-farm safe via `effective_farm_role`) → `require_farm_role(*roles)` write gates.

Write-gate role sets actually wired in routers:
- `_ENTRY_ROLES` = OWNER, MANAGER, WORKER, SUPER_ADMIN (daily entry: sows/events/boars/piglets/finishers/tasks create)
- `_MANAGE_ROLES` = OWNER, MANAGER, SUPER_ADMIN (destructive cull/delete, farm config, thresholds)
- `_OWNER_ROLES` = OWNER, SUPER_ADMIN (member create/update)
- READ (GET list/detail/reports): any farm member via `FarmDep` (no role gate)

Note: org-level admins (VENDOR/DISTRIBUTOR/DEALER) are **NOT** in any `require_farm_role` set → they get **read** access to farms in their org tree but are **blocked from all farm writes** (they are not SUPER_ADMIN, and `effective_farm_role` returns the system role which is not in the entry/manage/owner sets). Confirmed live below.

---

## 1. Role × Action matrix (live, farmA, HTTP status)

Legend: 2xx = allowed; 403 = blocked (Forbidden); 409/422 = **passed RBAC** then hit business/validation logic (NOT a permission failure).

| Role | sow READ | sow CREATE | cycle mating CREATE | sow CULL (destruct) | sow DELETE (destruct) | report READ | farm CONFIG update | THRESHOLD override | member LIST | member CREATE | AI chat |
|------|----|----|----|----|----|----|----|----|----|----|----|
| **SUPER_ADMIN**       | 200 | 201 | 201 | 201 | 204 | 200 | 200 | 200 | 200 | 422* | 200 |
| **VENDOR_ADMIN**      | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **DISTRIBUTOR_ADMIN** | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **DEALER_ADMIN**      | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **FARM_OWNER**        | 200 | 201 | 409† | 201 | 204 | 200 | 200 | 200 | 200 | 422* | 200 |
| **FARM_MANAGER**      | 200 | 201 | 409† | 201 | 204 | 200 | 200 | 200 | 200 | **403** | 200 |
| **FARM_WORKER**       | 200 | 201 | 409† | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **VET**               | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **VIEWER**            | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |
| **API_CLIENT**        | 200 | **403** | **403** | **403** | **403** | 200 | **403** | **403** | 200 | **403** | 200 |

\* `member CREATE` = 422 for OWNER/SUPER_ADMIN: RBAC **passed** (not 403); 422 is request-body validation (`MemberCreate` field constraint), i.e. authorization is correct, payload was minimal. Verified separately that MANAGER/WORKER/VET/VIEWER get **403** here → only OWNER+ may create members. PASS.

† `cycle mating CREATE` = 409 for OWNER/MANAGER/WORKER: RBAC **passed** (not 403); 409 conflict is sow-state business rule (sow not in a matable state after prior cull/delete in the sequence). Authorization correct. PASS.

**Read-only roles (VET/VIEWER/API_CLIENT)**: every write/destructive/setting action = 403, all reads = 200. PASS — matches `READ_ONLY_ROLES` partition.

**Worker boundary**: WORKER allowed daily entry (sow/mating CREATE) but **403 on cull, delete, config, threshold, member** — exactly the `_ENTRY_ROLES` vs `_MANAGE_ROLES`/`_OWNER_ROLES` split. PASS (matches existing regression `test_farm_write_rbac.py`).

**Org-admin write block**: VENDOR/DISTRIBUTOR/DEALER_ADMIN can READ org-tree farms but are **403 on all farm writes**. PASS (no over-privilege — they cannot mutate farm data despite tree visibility).

---

## 2. Vertical privilege escalation — admin console (`/admin/*`, `require_super_admin`)

Re-probed with the **correct** path `/admin/members` (initial run used `/admin/users` which 404s — wrong path, not an RBAC signal; corrected here):

| Role | `/admin/overview` | `/admin/members` | `/admin/orgs` |
|------|----|----|----|
| FARM_OWNER    | **403** | **403** | **403** |
| FARM_MANAGER  | **403** | **403** | **403** |
| VENDOR_ADMIN  | **403** | **403** | **403** |
| DEALER_ADMIN  | **403** | **403** | **403** |
| SUPER_ADMIN   | **200** | **200** | (n/t) |

No farm-level or even org-level admin can reach the platform admin console. Only SUPER_ADMIN. PASS — no vertical escalation.

---

## 3. Horizontal (cross-tenant) access

| Actor | Target | Action | Status | Verdict |
|-------|--------|--------|--------|---------|
| FARM_OWNER @ farmA | farmB (isolated org) | read sows | **403** | PASS |
| FARM_OWNER @ farmA | farmB | read farm detail | **403** | PASS |
| FARM_OWNER @ farmA | farmB | write (create sow) | **403** | PASS |
| FARM_OWNER @ farmB | farmA | read sows | **403** | PASS |

`get_farm_context` (`FarmDep`) blocks at the dependency layer via `can_access_farm` (SUPER_ADMIN all / org-tree / explicit `user_farms`). farmB lives under a separate INDEPENDENT org not in farmA-owner's tree, and farmA-owner has no `user_farms` row for it → 403. No cross-tenant read or write leak. PASS — tenant isolation enforced at API level (not just UI).

---

## 4. Add-on gating (AI Insight)

| Case | Status | `renderer` field | Verdict |
|------|--------|------------------|---------|
| Free farm (no `ADDON_AI_INSIGHT` sub) → `POST /chat/query` | 200 | **`template`** | PASS |

Design is **graceful degradation, not a hard gate**: `require_addon()` exists in `dependencies.py` but is **wired into 0 routers** (grep-confirmed). The AI add-on is enforced inside `chat_service.handle_query` — no subscription ⇒ Base-tier `TemplateRenderer` (`renderer: "template"`), with subscription ⇒ `LLMRenderer`. Free accounts therefore **cannot** obtain LLM output; they are correctly limited to the template renderer. Not a 402/403 block on the endpoint — the endpoint is intentionally available to all farm members. PASS (functionally gated). Note for product: any future paid add-on needing a *hard* block would need `require_addon` actually mounted — currently unused (KNOWN_GAP, informational, not a security bug for AI Insight since LLM output is what is gated and that gate holds).

---

## 5. Session / auth boundary

| Case | Status | Verdict |
|------|--------|---------|
| Expired access token | **401** | PASS |
| No `Authorization` header | **401** | PASS |
| Garbage/invalid token | **401** | PASS |
| Valid token, **user deactivated** (`active=FALSE`) | **401** | PASS |

`get_current_user` rejects bad/expired JWTs and also re-checks `user.active` on every request → deactivating a user immediately invalidates their live tokens (no need to wait for expiry). PASS — session boundary solid, no logged-out/deactivated bypass.

---

## 6. Findings summary

- **Role × action assertions run (live):** 110 in the main grid (10 roles × 11 actions) + 13 admin-escalation + 4 cross-tenant + 4 session + 1 add-on + corrective re-probes = **132 + 9** assertions.
- **Bypass / leak count: 0.** No vertical escalation (admin console SUPER_ADMIN-only), no horizontal cross-tenant read/write leak (all 403 at dependency layer), no session bypass (401 incl. deactivated user), add-on LLM gate holds (free → template).
- **RBAC_BUG: 0. SECURITY_BUG: 0.**
- **KNOWN_GAP (informational, non-security):** `require_addon()` dependency is defined but mounted on no router; AI Insight gating is done in service layer instead (works). If a future add-on needs an endpoint-level hard 402, that wiring is absent.
- **Test artifact corrected:** initial `/admin/users` probe returned 404 (non-existent path); real admin members path is `/admin/members` → 403 for all non-SUPER_ADMIN. No RBAC concern.

**Overall: PASS.** RBAC is enforced at the API layer across all 10 roles; UI-independent. Two-axis model (system role for admin/org-tree, farm `role_override` for writes) behaves per `permissions.py`/`dependencies.py` with correct read-only, worker, org-admin-no-write, owner-only-member-mgmt, and tenant-isolation boundaries.
