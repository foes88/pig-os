# PigOS Overnight Market QA — FINAL MORNING REPORT (2026-06-24)

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000` + API `localhost:8000` (docker postgres `pigos`).
Evidence-first. Phases: P0 baseline · P-INTEGRITY (×3) · P-RBAC · P-REF (PigPlan parity) · P5 validation · P2 market matrix (8 rows) + i18n.
Result codes: PASS / PASS_WITH_KNOWN_GAPS / FAIL / BLOCKED.

---

## 1. OVERALL VERDICT — **PASS_WITH_KNOWN_GAPS**

Core safety properties hold under stress: tenant isolation (API-layer 403/404 everywhere), RBAC (0 bypass / 0 leak across 10 roles, 141 live assertions), input validation (19/19 hard-blocked), and the **primary breeding-cycle KPI aggregates held drift=0 across 34 randomized mutations**. Baseline green (pytest 485 passed, tsc exit 0; web 307, api `{"status":"ok","version":"0.1.0"}`).

But **4 INTEGRITY_BUGs** were reproduced deterministically (1 HIGH crash, 2 MEDIUM, 1 LOW-MED), plus a 1 HIGH PigPlan-parity gap (FOSTER_OUT). None corrupts the core breeding aggregates today, but **INTEG-1 (weaning 500 on realistic ear_tags) is a release blocker** because it makes the happy-path un-completable for a normal data shape and deadlocks the sow lifecycle.

---

## 2. RELEASE BLOCKERS — Top 3

1. **[HIGH · BLOCKER] Weaning HTTP 500 on `ear_tag` length ≥ 16** (group_code `VARCHAR(30)` overflow). A realistic tag like `KR-FARM-SOW-0001-2025` (21 chars) makes full-weaning impossible → sow stuck in `LACTATING` → cycle deadlock → PSY/MSY permanently un-recorded. Threshold proven: ≤15 = 201, ≥16 = 500. `SowCreate.ear_tag` allows 30 chars, so it is reachable in normal use. Found independently by **two** integrity phases (aggregate-truth BUG-1, edit-idempotency INTEG-1).
   - Locus: `api/app/services/event_service.py` `record_weaning()` L510-511 (`f"WG-{yymmdd}-{sow.ear_tag}-{id[:4]}"`).

2. **[MEDIUM · fix-before-launch] Dashboard `farrowing_rate` ignores soft-delete.** YTD numerator/denominator omit `deleted_at IS NULL`, so deleted matings/farrowings keep inflating/deflating the rate; **does not self-correct**. Reproduced: dashboard FR=1.0 vs source-of-truth 0.667 (Δ 33pp, permanent). Same surface disagrees with `/reports/reproduction` (which is delete-aware) → two numbers for one KPI. Found by two phases (aggregate-truth BUG-2, edit-idempotency INTEG-2).
   - Locus: `api/app/services/kpi_service.py` `get_dashboard()` L603-614 (the adjacent week_* counts filter correctly → in-function asymmetry).

3. **[HIGH · parity / data-integrity hardening] FOSTER_OUT has no nursing-capacity guard.** A sow can foster OUT more piglets than it currently nurses; effective nursing goes negative and `record_weaning`'s `max(0,…)` (L430) silently masks it, breaking the weaned-head identity. PigPlan blocks this with the same `pouDusu < dusu` check it uses for deaths (msg.032). Repro: farrow BA=10 → FOSTER_OUT 12 → currently **accepted (201)**.
   - Locus: `api/app/services/event_service.py` `record_piglet_event` L726 (DEATH and FOSTER_IN are guarded; FOSTER_OUT is not).

> All other findings below are non-blocking (KNOWN_GAP: seed/localization) or LOW/latent.

---

## 3. EXECUTIVE SUMMARY

- **Stack & baseline (P0): PASS.** web 307, api ok v0.1.0; pytest 485 passed (0 fail) in 49.75s; `tsc --noEmit` exit 0. Git dirty only with 14 pre-existing screenshot PNGs + 2 untracked handoff docs — **no source changes, no commit** (guardrail honored across all phases).
- **Data integrity (P-INTEGRITY): the core invariant holds, but 4 wiring bugs found.** The breeding-cycle aggregates (`total_born`, `born_alive`, `weaned`, PSY/NPD views) recomputed drift=0 over 34 randomized create+delete mutations and 15-round PATCH churn; soft-delete is soft; status rollback chains are exact; weight units round-trip with no hidden kg↔lb conversion. The bugs are at the **edges** (long ear_tag, soft-delete-blind dashboard FR, orphan piglet_group after weaning delete, write-only cross-tenant FK).
- **RBAC (P-RBAC): PASS — 0 bypass, 0 leak.** 10 roles × full action grid live (141 assertions). No vertical escalation (admin console SUPER_ADMIN-only), no horizontal cross-tenant read/write (403 at dependency layer), session boundary solid (401 incl. deactivated user). Worker/org-admin/read-only/owner-only partitions all correct.
- **PigPlan parity (P-REF): 31/34 rules MATCH-or-STRONGER (~91%).** PigOS exceeds the oracle on exact total_born identity, gestation/nursing windows, auto-mirror foster record, explicit delete→status rollback, and period-lock (423) on edits. 3 gaps: 1 HIGH (FOSTER_OUT, blocker #3), 2 LOW data-quality.
- **Input validation (P5): PASS 19/19.** Every invalid payload hard-blocked (422/409/404/423); valid control 201. BE validators authoritative; FE Zod pre-blocks for UX.
- **Market matrix (P2) + i18n: 8/8 market rows PASS.** All 7 locales (en/ko/zh/es/vi/pt/th) have **1337/1337 key parity, 0 missing, 0 Korean leak, 0 "MVP", 0 raw-key render**. Country (not language) drives KPI thresholds — proven live. KNOWN_GAPs are cross-market seed/localization, not per-market failures.
- **Guardrails:** stillborn formula `(sb+mum)/tb` confirmed consistent with the PigPlan oracle (`CHONGSAN=SILSAN+MILA+SASAN`) — **not** flagged/fixed. `benchmark_missing → rule silence` treated as PASS everywhere; no threshold values injected. No KR block in code → KR is a valid test target (P0 judgment (b)).

---

## 4. DATA INTEGRITY (P-INTEGRITY) — **highest priority**

### 4a. Bugs found (reproducible)

| ID | Class | Severity | Self-corrects? | Repro seed / boundary | Locus |
|----|-------|----------|----------------|------------------------|-------|
| **INTEG-1 / BUG-1** | INTEGRITY_BUG (crash + state-lock) | **HIGH** | n/a (atomic rollback) | `ear_tag` len ≤15 → 201, **≥16 → 500**; e.g. `KR-FARM-SOW-0001-2025`. Farrow then full-wean. group_code overflows `VARCHAR(30)`. Sow stuck `LACTATING`. | `event_service.py` L510-511 |
| **INTEG-2 / BUG-2** | INTEGRITY_BUG (stale KPI) | **MEDIUM** | **NO** | New farm, 3 matings/3 farrowings, delete 1 → dashboard FR stays 1.0, truth=0.667 (Δ 0.333 permanent). Missing `deleted_at IS NULL`. | `kpi_service.py` L603-614 |
| **BUG-3** | INTEGRITY_BUG (phantom inventory) | **LOW-MED** | **NO** | Soft-delete 1 of 12 weanings → `/piglets` still shows 12 active `WG-*` groups (9 phantom heads). No KPI uses piglet_groups (MSY reads finisher_groups) → no KPI drift. | `delete_weaning` L966-981 (mirror create L510-520) |
| **TENANT FINDING #1** | INTEGRITY_BUG (cross-tenant dangling FK) | **MEDIUM (latent)** | n/a | A posts piglet_event with `target_farrowing_id` = **Farm B's** farrowing → **201**, stored cross-tenant. Write-only field (never read) → no leak today; latent risk if a future feature joins on it. | `record_piglet_event` L746 (no farm-scope check) |
| **C3 (P-REF)** | INTEGRITY_BUG (missing guard vs oracle) | **HIGH (hardening)** | n/a | farrow BA=10 → FOSTER_OUT 12 → **201**; effective nursing negative, masked by `max(0,…)`. | `record_piglet_event` L726 |

### 4b. Integrity checks that PASSED (evidence, not "looks good")

- `total_born_sum` / `born_alive_sum` vs source SQL (`deleted_at IS NULL`): **34 randomized create+delete mutations, max|drift| = 0**.
- Aggregate self-corrects after delete: weaned 141→132 (Δ exactly =9), ba 141→132 (Δ exactly =9), drift=0.
- Weaning weaned_count 15× random (0–14) PATCH churn → source always reflects set value, **drift 0**. Double-PATCH idempotent (ba/tb stable).
- Soft-delete is soft (rows retained, `deleted_at` set); status rollback chain OPEN→LACTATING→PREGNANT→OPEN exact; cascade delete leaves 0 dangling children.
- Referential guards: farrowing-delete blocked while weaning exists (409); mating-delete blocked while farrowing exists (409); double-delete not re-applied (404, rollback once).
- Double-submit dedup: identical mating → 2nd 422; identical farrowing → 2nd 409 (no silent dup).
- Within-farm piglet conservation: 6×ba=12 = 72 → after **20 randomized fosters still 72**; FOSTER_OUT Σ == FOSTER_IN Σ; no negative nursing.
- Cross-tenant access: read/write/delete/event-injection/report-pull on another tenant all **403/404** (×3–×5 each); cross-FARM cross-foster blocked (422). PSY/NPD views + herd KPI filter `deleted_at IS NULL` (view defs confirmed). Weight unit no hidden kg↔lb conversion (1.55kg in = 1.55 stored = 1.55 out).
- **SKIP_NOT_IMPLEMENTED:** true parallel double-submit race (sequential re-submit + randomized ordering covered; threaded row-lock probe not run — no double-application observed in sequential stress).

---

## 5. PERMISSIONS (P-RBAC) — **0 SECURITY_BUG, 0 RBAC_BUG**

10 roles, two-axis enforcement (`users.system_role` for admin/org-tree, `user_farms.role_override` for farm writes). 141 live assertions (132 grid + 9 re-probes), `qarbac-*` namespaced, torn down.

| Surface | Result | Evidence |
|---------|--------|----------|
| Role × action grid (10×11, live) | **PASS** | Write=7 roles, ReadOnly=3 (VET/VIEWER/API_CLIENT) all-403-on-write; WORKER entry-yes/manage-no; OWNER-only member create |
| Org-admin write block (VENDOR/DISTRIBUTOR/DEALER) | **PASS** | read org-tree farms = 200, **all farm writes = 403** (tree visibility ≠ write) |
| Vertical escalation (`/admin/*`) | **PASS** | every non-SUPER_ADMIN = 403; only SUPER_ADMIN 200 |
| Horizontal (cross-tenant farmA↔farmB) | **PASS** | read/detail/write all **403** at `FarmDep` dependency layer (UI-independent) |
| Add-on gating (AI Insight) | **PASS** | free farm → `renderer:"template"` (LLM gated in service); endpoint open by design |
| Session/auth boundary | **PASS** | expired/missing/garbage token → 401; **deactivated user → 401 immediately** |

KNOWN_GAP (informational, non-security): `require_addon()` is defined but mounted on 0 routers; AI Insight is gated in the service layer (works). A future *hard* endpoint-level 402 add-on would need that wiring.

---

## 6. PigPlan ↔ PigOS PARITY (P-REF)

Oracle (read-only): `DataValidationChk.java::isMdWkValidate()/isWkDateValidate()` + pmd/inputmd event services. 34 enforceable rules extracted; mapped onto PigOS `validators/` + `event_service` + `sow_state`.

- **MATCH or STRONGER: 31/34 (~91%).**
- **Gaps: 3** — **HIGH** C3 FOSTER_OUT capacity (blocker #3); **LOW** M3 (AI-method slots not sequence-validated; boars are); **LOW** F4 (per-death-cause field not capped at 25 individually — aggregate/nursing bounds still hold).
- **N/A (PigPlan-specific): 3** — A2 retired reason code `050001`, W3 re-suckle event, method note (not in PigOS V1).
- **PigOS STRONGER than oracle:** exact `total_born = ba+sb+mum` identity; gestation 100–130d & nursing 10–60d windows; cross-foster auto-mirror record; explicit `ROLLBACK_STATUS_ON_DELETE` map + re-mating preservation; born_alive-reduction guard on edit; period-lock 423 on edit.
- **Guardrail:** stillborn `(sb+mum)/tb` confirmed consistent with oracle `CHONGSAN=SILSAN+MILA+SASAN` — not flagged, no external-benchmark FAIL.

---

## 7. VALIDATION (P5) · MARKET MATRIX (P2) · i18n

### 7a. Input validation (P5) — PASS 19/19

All 8 brief categories covered & hard-blocking: farrowing-sum (TB>35, BA≠M+F, avg-wt>3.0 → 422), weaning identity (422), date-order (422), state-transition (mating on PREGNANT → 422; GILT-no-mating → 404; re-wean → 409), locked-month (PATCH → **423**), foster cap >25 (422), finisher range (entry 5–50kg, exit ≤200kg, ship>remaining → 422), pregnancy-check on non-PREGNANT (422). Valid control → 201. BE authoritative; FE Zod pre-blocks.
KNOWN_GAP (non-blocking): (a) no API to *create* period locks (close-month UX) — 423 enforcement works, lock seeded via SQL; (b) 423 enforced on edit/delete not create; (c) dead `PeriodLockedError=409` class diverges from live 423; (d) FE foster cap 30 vs BE 25 (server enforces — cosmetic).

### 7b. Market matrix (P2) — 8/8 rows PASS

| Market | Country drives thresholds | Seed coverage | UI lang | Report unit | Verdict |
|--------|---------------------------|---------------|---------|-------------|---------|
| US | PASS (region layers over global) | seeded (11 region rows) | en | kg (US=lb gap) | **PASS** + 2 KNOWN_GAP |
| KR | PASS (27 region rows; PSY warn 22 ≠ US 26) | seeded | en (ko=admin-only by design) | kg ✓ | **PASS** + 2 KNOWN_GAP |
| KR-en | PASS (KR thresholds under en UI) | seeded | en | kg ✓ | **PASS** |
| CN | PASS (PSY 24/20 distinct) | seeded | zh | kg ✓ | **PASS** + 2 KNOWN_GAP |
| BR | PASS (9 region + 15 global) | seeded | pt | kg ✓ | **PASS** + 2 KNOWN_GAP |
| VN | PASS (VN-specific) | seeded (partial; NULLs silent) | vi | kg ✓ | **PASS** + 2 KNOWN_GAP |
| **MX** | PASS (23/23 global fallback, **0 foreign leak**) | **NOT seeded** | es | kg ✓ | **PASS** + **KNOWN_GAP (no MX seed)** |
| **TH** | PASS (global fallback, **0 foreign leak**) | **NOT seeded** | th | kg ✓ | **PASS** + **KNOWN_GAP (no TH seed)** |

Decisive proof country (not language) selects thresholds: KR/ko == KR/en (22.0==22.0); KR(22) ≠ US(26). MX/TH with no seed → **global** fallback (scope=`global`), **never** another country's row (would be FAIL) — verified in DB (`region MX=0`, `region TH=0`) and live API.

### 7c. i18n — PASS (all 7 locales)

`en/ko/zh/es/vi/pt/th`: **1337/1337 key parity, 0 missing, 0 extra, 0 empty values, 0 Korean(Hangul) leak in non-ko values, 0 "MVP" literal, 0 raw-key render** (full parity ⇒ no raw-key fallback possible). Real localized content spot-checked (e.g. th `เข้าสู่ระบบ PigOS`, sow statuses localized per P5-2 spec).

### 7d. KNOWN_GAPs (cross-market, not per-market failures — record, do not inject)

1. **MX & TH have no region threshold seed** → safe global fallback (expected per brief). No foreign-country threshold borrowed.
2. **US weight-unit lb not wired** — `region_defaults`/`market_defaults` are empty (0 rows), so every country (incl. US) falls back to hardcoded `"kg"`; the lb code path (`KG_TO_LB`) exists but is never triggered. Correct for non-US markets; a US data-seeding gap.
3. **Currency** falls back to USD/$ for all (region_defaults empty) — KR should be KRW, MX MXN, BR BRL; read-only display, non-integrity.
4. **Chat free-text renderer is en/ko only** — for es/vi/zh/pt the *structured findings are correct & country-driven*, but the prose `answer` falls back to English (Addon #1 / `engine/renderer.py` territory; web-UI i18n is fully localized).
5. **Chat finding cause/action codes not localized** — `chat/page.tsx` renders domain enum codes (e.g. `insufficient_weaning_records`) raw; these are enum values, not next-intl keys (raw-i18n-key count = 0), but display as English snake_case for non-en users.
6. **`/onboarding` pre-auth page + 1 bottom-nav "Settings" label hard-coded English** — identical across all locales (not a raw-key leak), affects every non-en locale equally.

---

## 8. BUGS FOUND / UNFIXED + RECOMMENDED NEXT ACTIONS

**Unfixed (per guardrail: record-only, no source edit, no commit):** all 5 integrity findings (§4a) + 6 market KNOWN_GAPs (§7d) + P5 KNOWN_GAPs (§7a) + RBAC `require_addon` informational gap.

**Recommended next actions (priority order):**

1. **Fix INTEG-1 (blocker)** — make `group_code` fixed-width ≤30 (hash/truncate `ear_tag`, the `[:4]` weaning-id suffix already guards uniqueness) **or** widen `piglet_groups.group_code`. Add a regression test at ear_tag len 16/21/30. *(Spec-touching → needs human sign-off per guardrail; this is the gate for launch.)*
2. **Fix INTEG-2** — add `Mating.deleted_at.is_(None)` / `Farrowing.deleted_at.is_(None)` to `kpi_service.py` L603-614 (match the adjacent week_* counts). Reconcile dashboard FR with `/reports/reproduction`.
3. **Fix C3 (FOSTER_OUT guard)** — extend the L726 nursing check to `event_type in ("DEATH","FOSTER_OUT")`. Closes the last reproduction head-count integrity gap vs PigPlan.
4. **Fix BUG-3** — in `delete_weaning`, soft-delete the matching auto `WG-*` piglet_group (mirror the create at L510-520).
5. **Harden TENANT FINDING #1** — validate `target_farrowing_id` belongs to `target_sow_id` within `farm_id` (else 422), or ignore the client value and derive in-farm (the auto-mirror already does). Closes the latent cross-tenant FK before any consumer ships.
6. **Seed `region_defaults`/`market_defaults`** (US lb + per-country currency) before US/LatAm launch; add MX/TH benchmark seed when localized data exists.
7. **Extend chat renderer** to es/vi/zh/pt (Addon #1) and localize finding cause/action enum codes — for full non-en chat parity.

---

### Evidence index (per phase)
`P0-baseline.md` · `P-INTEGRITY-aggregate-truth.md` · `P-INTEGRITY-edit-idempotency.md` · `P-INTEGRITY-tenant-isolation.md` · `P-RBAC-matrix.md` · `pigplan-rule-inventory.md` (worktree `wf_10d9e087-c13-2`) · `P5-validation.md` · `market-{US,KR,KR-en,CN,BR,VN,MX,TH}.md` — all under `docs/qa/overnight-market-qa/2026-06-24/`.

**Guardrails honored across all phases:** no source modified, no commit/push, no deploy/AWS/paid-API/.env.production changes. All test data isolated under `qa-*` namespaces; no prod/operational DB mutation. Stillborn formula and PSY/threshold values untouched (read from seed). benchmark_missing → silence treated as PASS; no numbers injected.
