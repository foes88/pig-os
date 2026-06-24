# PigOS Overnight Market QA — P2 [CN] (country=CN, lang=zh)

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000`, API `localhost:8000`, docker postgres `pigos`. Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: CN PASS** (with 2 scoped KNOWN_GAPs that affect all markets equally, not CN-specific). zh UI is fully localized (0 raw keys / 0 Korean leak / 0 "MVP"), and **country=CN drives KPI thresholds** (proven: CN PSY target 26 / warn 24 / crit 20, distinct from US/KR/BR/SYSTEM).

Test identity: org/farm `qa-cn-zh-1782292947`, country **CN**, farm_id `f7fd5c6e-032f-40f4-9611-08a6e2456712`, email `qa-cn-zh-1782292947@example.com`. Isolated org (own org_id `164c59fe-…`).

---

## Step 1 — Account/farm creation (country=CN) + login — PASS

| Action | Command | Result |
|--------|---------|--------|
| Onboarding (org+user+farm, country=CN) | `POST /api/v1/onboarding/complete` | **HTTP 201** — org_id/farm_id/user_id + tokens returned |
| Login | `POST /api/v1/auth/login` | **HTTP 200** — `role=FARM_OWNER`, `farm_ids=[f7fd…]` |
| Farm detail | `GET /api/v1/farms/{id}` | **200** — `"country":"CN"`, `farm_code=FARM-CN-164C59`, `unit_system=METRIC` |

KR routing: per P0 judgment (b), KR signup is **not blocked in code** (no geo/country gate in `middleware.ts` / onboarding). So full CN signup was the correct path; no config-only fallback needed. CN is a clean test target.

---

## Step 2 — zh language: UI refresh, no Korean leak, no raw keys, no "MVP" — PASS

### 2a. Static i18n integrity (`src/messages/zh.json` vs `en.json`)
| Check | Method | Result |
|-------|--------|--------|
| Key parity | recursive leaf-key diff (UTF-8) | **1337 / 1337 keys, 0 missing, 0 extra** (en/ko/zh/es/vi all 1337) |
| Korean leak in zh values | regex `[가-힣]` over all zh string values | **0 hits** |
| "MVP" literal in zh | substring scan | **0 hits** |
| Untranslated (zh value == en value, ≥3 ascii letters) | value-equality scan | 10 hits — all **legitimate non-translatables**: `AI Active`, `Rule Engine`, `Data Dividend Program`, `IoT`, `Beta`, `PWMR-A`, `PWMR-B`, KPI codes `PSY`/`NPD`, and template `{metric} {value}{unit}`. No defect. |
| Sow-status terms (CLAUDE.md spec) | `zh.sowStatus` | **MATCH**: GILT→后备母猪, OPEN→空怀, PREGNANT→妊娠, LACTATING→哺乳, ACCIDENT→事故, CULLED→淘汰, DEAD→死亡 |

### 2b. Live rendered UI (Playwright, real login as qa-cn account, `NEXT_LOCALE=zh`)
Spec: `src/e2e-live/_uat_tmp/market-cn-zh.live.spec.ts` (reuses `expectNoRawI18nKeys` + adds Korean-leak / MVP / lb assertions). **Result: 1 passed (23.9s), exit 0.**

| Page | language-switcher | raw i18n keys | Korean leak | "MVP" | console/page errors | shot |
|------|-------------------|---------------|-------------|-------|---------------------|------|
| `/` (dashboard) | **=zh** | **0** | **0** | **0** | **0** | `_uat_tmp/shots/market_cn_dash_zh.png` |
| `/sows` | — | **0** | **0** | **0** | — | `_uat_tmp/shots/market_cn_sows_zh.png` |
| `/reports` | — | **0** | **0** | (no `\blb\b`) | — | `_uat_tmp/shots/market_cn_reports_zh.png` |

zh is available to a non-admin FARM_OWNER (only **ko** is admin-gated per the existing `i18n-lang-switch` spec) — so the CN customer persona can use zh. KR/en threshold note: thresholds are country-driven (Step 3), independent of UI language, so en/zh selection does not relax CN's KR/strict numbers.

---

## Step 3 — Country KPI thresholds (country, not language, decides) — PASS

Threshold resolution chain (`api/app/engine/rules/_common.py::resolve`): `rule_configs` (operator) → **country benchmark** (`default_metric_values` region row) → code default. Loader (`kpi_service._all_benchmarks`) calls `effective_metric_values(farm_id, region_code=farm.country, 'SYSTEM')`.

### 3a. CN benchmark rows exist and resolve for the CN farm
`SELECT … FROM effective_metric_values('f7fd…','CN','SYSTEM')`:

| metric | warn | crit | dir | result |
|--------|------|------|-----|--------|
| PSY | 24.00 | 20.00 | below | CN-specific |
| NPD | 45.00 | 62.00 | above | CN-specific |
| FARROWING_RATE | 82.00 | 78.00 | below | CN-specific |
| PRE_WEANING_MORTALITY (→PWMR alias) | 10.00 | 14.00 | above | CN-specific |
| BORN_ALIVE | 11.00 | 10.00 | below | CN-specific |
| WEANED_COUNT | 10.50 | 9.00 | below | CN-specific |
| MARKET_PRICE_HEAD | (null) | (null) | below | **benchmark_missing → rule silence = PASS** |

### 3b. Country (not language) decides — PSY cross-region proof
`default_metric_values` PSY warn/crit: **CN 24/20**, US 26/23, BR 28/25, KR 22/18, SYSTEM 22/18. CN is distinct → a CN farm uses CN numbers regardless of zh/en UI.

### 3c. End-to-end: thresholds flow into engine even with locale=zh
- `GET /kpi/dashboard` (CN farm) → `"country":"CN"`, `benchmarks.PSY={avg:24.34, top25:31.5, target:26.0}`, `NPD.target:30`, `FARROWING_RATE.target:85` — **CN region values**, not SYSTEM/US.
- `POST /chat/query {locale:"zh"}` → finding `psy.no_data`, **`target_value: 24.0`** = CN PSY threshold. Confirms zh language does **not** alter the country-driven number. Empty farm → `current_value: null` (no fabrication), `psy.no_data` INFO — correct.
- MARKET_PRICE_HEAD has no thresholds → no price rule fires = PASS (benchmark_missing), no numbers injected.

CN has full seed coverage, so there is **no global-fallback KNOWN_GAP for CN** (unlike MX/TH which lack seed rows). No foreign-country thresholds were used.

---

## Step 4 — Report units (US=lb / else=kg) — PASS for CN (kg)

- `GET /farms/{id}/config` → `weight_unit:"kg"`, `currency_symbol:"$"`.
- `units.ts` formats weight by `weight_unit` (kg vs lb). CN resolves **kg** (METRIC) → `/reports` rendered with **no `\blb\b`** token (asserted in live spec). Correct: CN must not use lb. PASS.

---

## KNOWN_GAPs (not CN-specific; affect all markets equally — recorded, not "fixed")

1. **`region_defaults` table is empty (0 rows).** `farm_service.get_local_config` therefore always falls back to `weight_unit="kg"` and `currency = farm.currency or "USD"`. Consequences:
   - CN currency shows **USD / `$`**, not CNY / ¥ (cosmetic; benchmarks/thresholds unaffected).
   - The "US=lb" half of the unit rule is **not data-driven** — a US farm would also get kg until a US `region_defaults` row (weight_unit=lb) is seeded. For **CN this is correct** (kg), so CN passes; the US-lb mapping is a separate seed gap. **KNOWN_GAP (seed), do not inject values.**
2. **Chat template renderer supports only en/ko** (`api/app/engine/renderer.py` header "Locales supported: en, ko"; `_CAUSE_KO/_ACTION_KO` else English). For `locale=zh` the **structured findings are correct and country-driven** (severity, `target_value=24.0`), but the prose `answer` string renders in **English**, not Chinese. Web UI i18n (1337 keys) is fully zh; this gap is only the AI-chat free-text layer. **KNOWN_GAP (Addon #1 renderer), not a web-UI defect.**

---

## Summary

| Step | Result |
|------|--------|
| 1. CN account/farm + login | **PASS** (201 / 200, country=CN) |
| 2. zh UI (raw keys / KO leak / MVP) | **PASS** (static 0/0/0 + live spec 1 passed) |
| 3. Country-driven KPI thresholds | **PASS** (CN PSY 24/20 distinct; flows into dashboard + chat at locale=zh; benchmark_missing→silence) |
| 4. Report units (kg for CN) | **PASS** (weight_unit=kg, no lb in reports) |

**CN = PASS.** Two KNOWN_GAPs noted (empty `region_defaults` → USD currency + US-lb mapping not seeded; chat renderer en/ko-only) — both are cross-market, neither blocks the CN/zh persona, and per guardrail no values were injected.
