# PigOS Overnight Market QA — Market TH (Thailand)

Date: 2026-06-24 · Market row: **TH** (country=TH, lang=th) · Evidence-first.
Target: live API `localhost:8000` + web `localhost:3000` + docker postgres `pigos`.
Namespace: `qa-th-th-*` (isolated). Result codes: PASS / FAIL / KNOWN_GAP / PARTIAL / SKIP_NOT_IMPLEMENTED.

---

## VERDICT — **PASS (with one KNOWN_GAP)**

| # | Step | Result | One-line |
|---|------|--------|----------|
| 1 | Account/farm creation (country=TH) + login | **PASS** | Onboarding 201, login 200, `farms.country='TH'` in DB |
| 2 | Language `th` UI / no leakage | **PASS** | th locale supported & customer-visible; 0 Korean leak, 0 raw-key, 0 "MVP", full key parity (1337/1337) |
| 3 | Country-driven KPI thresholds | **KNOWN_GAP** | TH has **no region seed** → all metrics resolve to **SYSTEM/global** fallback. No foreign-country threshold borrowed. Benchmark-missing → rule silence (PASS). |
| 4 | Report unit (US=lb / else=kg) | **PASS** | TH farm `weight_unit="kg"` (correct for TH) |

KR routing precondition: per `P0-baseline.md §5`, KR is judgment **(b) TEST TARGET** — no KR block/redirect exists in code. So TH onboarding proceeds normally (no PigPlan handoff gate). Config-level verification done regardless.

Guardrails honored: no fixes, no commit, no prod/AWS/paid-API/.env changes. No threshold values injected/fabricated. Stillborn formula `(sb+mum)/tb` not flagged.

---

## Step 1 — TH account + farm creation + login — PASS

- `POST /api/v1/onboarding/complete` with `country:"TH"`, `timezone:"Asia/Bangkok"` → **HTTP 201**.
  - `farm_id=09f924ae-bd8f-41c7-8542-ad63c75c9cbc`, `org_id=dec51309-…`, `user_id=f2f8e3d9-…`.
- DB confirm (docker postgres `pigos`):
  `SELECT id,name,country FROM farms WHERE id='09f924ae-…'` → `qa-th-th-1782293507-farm | TH`.
- `POST /api/v1/auth/login` → **HTTP 200**, `role=FARM_OWNER`, `farm_ids=["09f924ae-…"]`, access token issued (277-char JWT).
- Note: email `.test` TLD rejected by validator (`example.com` used). Not a TH issue — global email validation.

## Step 2 — Language `th` / leakage — PASS

**Locale support (code):**
- `src/middleware.ts:4` `LOCALES = [... "th" ...]` and `src/i18n/config.ts:2` `locales = [... "th" ...]` — `th` is a first-class locale.
- `src/i18n/config.ts:8` `ADMIN_ONLY_LOCALES = ["ko"]` — **only `ko` is admin-gated**; `th` is customer-visible (no gate). KR-only locale restriction does not affect TH.

**th.json integrity (`src/messages/th.json`, 1584 lines):**
- Key parity vs en.json: **en 1337 / th 1337, missing 0, extra 0**.
- Korean hangul leak in values: **0** (regex `[가-힣]`).
- Raw i18n key used as value (e.g. `auth.login`): **0**.
- Empty string values: **0**.
- Literal `"MVP"` occurrences: **0**.

**Real Thai content (spot-check, decoded):**
- `auth.login.title="เข้าสู่ระบบ PigOS"`, `.email="อีเมล"`, `.password="รหัสผ่าน"`, `.submit="เข้าสู่ระบบ"`.
- `nav.dashboard="แดชบอร์ด"`, `nav.sows="แม่สุกร"`, `dashboard.title="แดชบอร์ด AI"`, `common.save="บันทึก"`, `common.cancel="ยกเลิก"`.
- Sow statuses (matches P5-2 localized-term spec): `OPEN="ว่าง"`, `GILT="สุกรสาว"`, `PREGNANT="ตั้งท้อง"`, `LACTATING="ให้นม"`, `ACCIDENT="กลับสัด/อุบัติเหตุ"`.

(Live HTML body is empty — Next.js client-rendered SPA — so i18n verified via locale config + message catalog, which is the SSR source of truth.)

**KR/en threshold persistence:** thresholds are decided by **country**, not language (see Step 3). An English (lang=en) UI on a KR-country farm still resolves KR-country thresholds because the resolver keys on `farm.country` (`region_code=farm.country`), independent of UI locale. Verified by code path, not assumed.

## Step 3 — Country-driven KPI thresholds — **KNOWN_GAP** (global fallback, correct & safe)

**Resolution mechanism (code):**
- `kpi_service.py:29-51` `_get_benchmark()` calls SQL `effective_metric_values(:farm_code, :region_code, :market_code)` with `region_code = farm.country`, `market_code='SYSTEM'`.
- `threshold_service.py:14-34` priority: **farm → region(country) → system(global)**. Logic is country-neutral; only numbers vary by scope.

**Seed reality (`default_metric_values`):**
- Region scopes present: **BR, CN, KR, US, VN** + SYSTEM. **TH region rows = 0** (`SELECT count(*) … scope_code='TH'` → 0).

**Live resolution for the TH farm** (`effective_metric_values('09f924ae-…','TH','SYSTEM')`):

| metric | TH-resolved avg | warn | crit | source |
|--------|-----------------|------|------|--------|
| PSY | 24.30 | 22 | 18 | **SYSTEM** (= global, *not* KR 24.73, *not* US 27.10) |
| NPD | 30.00 | 40 | 55 | SYSTEM |
| FARROWING_RATE | 81.00 | 80 | 70 | SYSTEM |
| MSY | 22.00 | — | — | SYSTEM |
| FCR | 2.60 | 3.00 | 3.30 | SYSTEM |

- **No foreign-country threshold is borrowed.** Cross-check: KR PSY avg=24.73, US PSY avg=27.10/warn 26/crit 23 — TH gets neither; it gets SYSTEM 24.30/22/18. This is the documented global-fallback behavior (guardrail: "MX/TH seed없으면 글로벌 폴백=KNOWN_GAP; 타국 임계 무단사용 시 FAIL"). **Not a FAIL** — fallback is to global, not to another market.

**Live dashboard (`GET /farms/{TH}/kpi/dashboard`, HTTP 200):**
- `"country":"TH"` correctly propagated.
- `"benchmarks":{"PSY":{"avg":24.3,...},"NPD":{"avg":30.0,...},"FARROWING_RATE":{"avg":81.0,...}}` — all global values.
- KPIs null (empty farm) → only `inventory.zero` (SOW_COUNT=0) and `farm.health_class` alerts fire. **No PSY/NPD/FR rule fabricated** against missing data — correct silence.

**Benchmark-missing → silence (PASS):** 10 TH metrics have `benchmark_avg = NULL` (ABORTION_RATE, ADG, BIRTH_WEIGHT, CULLING_RATE, FINISH_MORTALITY, HIGH_PARITY_RATIO, MUMMIFIED_RATE, SOW_MORTALITY, TOTAL_BORN, WEANING_WEIGHT). Avg-comparison on these stays silent (no injected number) — matches guardrail `benchmark_missing → 침묵=PASS`.

**KNOWN_GAP statement:** TH-specific benchmark/threshold seed does not exist; the system safely degrades to global defaults. This is expected pre-launch for a non-seeded market and is recorded, not "fixed" (no values injected per guardrail).

## Step 4 — Report unit (kg for TH) — PASS

- `GET /farms/{TH}/config` → `"weight_unit":"kg"`, `currency_code:"USD"`.
- `farm_service.py:99-108` `get_local_config()`: `weight_unit` = `region_defaults.weight_unit` → fallback `"kg"`. `region_defaults` is empty (0 rows), so fallback applies → **"kg" for TH = correct**.
- (Side note / out of scope: same empty `region_defaults` means a US farm would also currently fall back to "kg" instead of "lb" — a US KNOWN_GAP, not a TH defect. Reports endpoints returned `[]` for the empty TH farm, HTTP 200.)

---

## Evidence index

- Onboarding/login: `curl` 201/200 captured; JWT `farm_ids` includes TH farm.
- DB: `docker exec pigos-postgres psql -U pigos -d pigos` — farm row, `default_metric_values` scopes, `effective_metric_values('…','TH','SYSTEM')`.
- i18n: `src/messages/th.json` parity + leak scan (Python `[가-힣]`, raw-key, empty, "MVP"); `src/i18n/config.ts`, `src/middleware.ts` locale support.
- Dashboard JSON: `country=TH`, global benchmarks, correct alert silence.
- Config JSON: `weight_unit=kg`.

## Final

**TH = PASS** on creation, language, and report unit. **KNOWN_GAP** on country KPI thresholds: no TH benchmark seed → safe global fallback (no foreign-market threshold misuse, benchmark-missing rules correctly silent). No source modified, no commit, no prod/env/AWS/paid-API actions.
