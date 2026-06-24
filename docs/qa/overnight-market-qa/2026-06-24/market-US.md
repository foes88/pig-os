# PigOS Overnight Market QA — Market [US] (country=US, lang=en) — 2026-06-24

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000`, API `localhost:8000`, docker postgres `pigos`. Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: US market is GO for country-driven KPI thresholds + English UI (PASS). Two KNOWN_GAPs: (a) report/UI weight-unit localization (US=lb) is not wired — UI shows kg; the country→lb data row and the `fmtWeight` consumer are both absent; (b) Template Renderer only translates en+ko, so es/vi/zh chat answers fall back to English text. Neither compromises data integrity. No KR block in code (P0 judgment (b)) — KR config-level thresholds independently confirmed via the same country-scope mechanism.**

Test account (isolated, qa-* namespace): `qa-us-en-1782292928@example.com` / org `cb43f233-…` / farm `acf6a35d-4847-4e42-a8b2-6e2b30e52893` (`farm_code=FARM-US-CB43F2`).

---

## Step 1 — US account/farm creation + login — PASS

| Check | Command / Evidence | Result |
|-------|--------------------|--------|
| Onboarding (org+user+farm, country=US) | `POST /api/v1/onboarding/complete` `{country:"US",…}` → **201**, returned org_id/farm_id/user_id + tokens | PASS |
| Login | `POST /api/v1/auth/login` → **200**, `role=FARM_OWNER`, `farm_ids=[acf6a35d-…]` | PASS |
| `/me` | **200** → `language=en`, `org_id` matches | PASS |
| Farm detail | `GET /api/v1/farms/{id}` → **200** → `country:"US"`, `farm_code:"FARM-US-CB43F2"`, `language:"en"`, `currency:"USD"`, `timezone:"America/Chicago"`, `unit_system:"METRIC"` | PASS |

Note: `farms.unit_system` field stored `METRIC` (default; onboarding does not set it from country). See Step 4.

**KR routing**: Per P0-baseline §5, code has **no KR signup/onboarding gate** (judgment (b) TEST TARGET). US onboarding is the active path here; KR config-level thresholds are independently verified by the same country-scope resolver (Step 3 shows thresholds key on `farm.country`, locale-independent), so KR-in-English-UI would retain KR thresholds by the identical mechanism (US→26 proves country, not language, drives the value).

---

## Step 2 — English UI: i18n integrity (no Korean leak / no raw key / no "MVP") — PASS

### 2a. i18n message files (static analysis)
Locale files: `src/messages/{en,ko,zh,es,vi,pt,th}.json` (7 locales).

| Check | Evidence | Result |
|-------|----------|--------|
| en leaf-key count | **1337** keys (recursive flatten) | — |
| Korean leak in en values (`[가-힣]`) | **0** | PASS |
| `"MVP"` substring in en values | **0** | PASS |
| en values equal to their own key-path (would look raw) | **0** | PASS |
| en values matching raw-key shape (`a.b.c`, lowercase dotted) | **0** | PASS |
| Locale parity vs en (missing / extra keys) | ko/zh/es/vi/pt/th all **missing=0, extra=0** (1337 each) | PASS |

Full key-parity (0 missing across all 6 non-en locales) means the UI **cannot** fall back to a raw key string in any locale → no raw-key render possible.

### 2b. Live English UI (rendered artifact)
`src/e2e-live/_uat_tmp/shots/dash_en.png` (in-repo Playwright artifact) read and inspected: language toggle reads **EN**; sidebar fully English — *Dashboard, Record Entry, Sows, Boars, Piglets, Finishers, Today's Tasks, Alerts, KPI Summary, Sow Status, Ask AI, Settings*; section headers *HERD / TASKS & ALERTS / REPORTS*. No Korean, no raw i18n keys, no "MVP" string. PASS.

### 2c. API responses in English (live)
`POST /chat/query` `{locale:"en"}` → answer `"ℹ [PSY]\n  Causes: Insufficient weaning records\n  Actions: Complete weaning data entry"` — clean English, no Korean, no raw key, no "MVP". PASS.

---

## Step 3 — Country KPI thresholds (country, not language, decides) — PASS

`default_metric_values` table seeded for **5 regions: BR, CN, KR, US, VN**. **US is first-class with its own thresholds** (live DB query, scope_type=region, scope_code=US):

| metric | warning | critical | benchmark_avg | direction | unit | confidence |
|--------|---------|----------|---------------|-----------|------|------------|
| PSY | 26.00 | 23.00 | 27.10 | below | 두/모돈/년 | high |
| NPD | 38.00 | 53.00 | 44.00 | above | days | — |
| FARROWING_RATE | 82.00 | 78.00 | 83.80 | below | % | high |
| BORN_ALIVE | 13.00 | 12.00 | 13.94 | below | 두/복 | high |
| WEANED_COUNT | 11.00 | 10.00 | 11.61 | below | 두/복 | high |
| PRE_WEANING_MORTALITY | 14.00 | 18.00 | 14.60 | above | % | high |
| STILLBORN_RATE | 8.00 | 12.00 | 8.00 | above | % | medium |
| SOW_MORTALITY | 12.00 | 15.00 | 12.20 | above | % | high |
| WSI | 7.00 | 9.00 | 6.70 | above | 일 | high |
| RTS_RATE | 10.00 | 15.00 | 6.00 | above | % | medium |
| MARKET_PRICE_HEAD | — | — | — (default_value=210.00 USD) | below | USD | medium |

US PSY (26/23) ≠ KR PSY (system/region 22) ≠ BR (19) — country-specific, validated seed values. **Do not treat as hypotheses** (these are the seeded source of truth).

### Country-vs-language proof (live, 5 locales on the US farm)
`POST /chat/query "How is my PSY?"` with `locale ∈ {en, ko, es, vi, zh}` — every response returned **`target_value = 26.0`** (the US PSY warning benchmark), proving the threshold is keyed on `farm.country` (US), independent of UI language:

```
[en] target=26.0  rule=psy.no_data  answer="ℹ [PSY]\n  Causes: Insufficient weaning records ..."
[ko] target=26.0  rule=psy.no_data  answer="ℹ [PSY]\n  원인: 이유 기록 부족 ..."
[es] target=26.0  rule=psy.no_data  answer="ℹ [PSY]\n  Causes: Insufficient weaning records ..."  (text falls back to EN)
[vi] target=26.0  rule=psy.no_data  answer="ℹ [PSY]\n  Causes: ..."                                  (text falls back to EN)
[zh] target=26.0  rule=psy.no_data  answer="ℹ [PSY]\n  Causes: ..."                                  (text falls back to EN)
```

Resolution chain (code, `insight_service._load_benchmark`): scope `farm > region(=country) > system`; US region row wins over system. **PASS.**

### Benchmark-missing → silence (per guardrail)
- `MARKET_PRICE_HEAD/US` has empty warning/critical/avg → price/loss rules stay **silent** = PASS (reason `benchmark_missing`). No numbers injected.
- `psy.no_data` finding fired only because the brand-new farm has **no weaning records** (INFO, `current_value=null`) — a data-volume state, not a benchmark gap. Correct.

### MX / TH (brief note)
`default_metric_values` region scopes = {BR, CN, KR, US, VN} only. **MX and TH are not seeded** → those countries would fall back to `system/SYSTEM` global thresholds = **KNOWN_GAP** (global fallback). No other country's thresholds are borrowed. (Not applicable to this US run; recorded per brief.)

---

## Step 4 — Report units (US=lb expected) — KNOWN_GAP (UI shows kg)

The US=lb requirement is **not satisfied**: there is no country→lb data, and the only country-aware weight-formatter is dead code. Evidence:

1. **Backend `weight_unit` resolves to `kg` for US.** `GET /api/v1/farms/{us}/config` → `{"weight_unit":"kg","currency_symbol":"$","market_code":null,...}`. Reason: `farm_service.get_local_config` reads `region_defaults` keyed by country, but **`region_defaults` is empty (0 rows)** — no US row, no any-country row, no seed defines it anywhere in `api/scripts` or `docs/master-data`. So `weight_unit` falls to the hardcoded `"kg"` default for every country, including US.
2. **The country-aware formatter is unused.** `src/lib/utils/units.ts` (`kgToDisplay`/`formatWeight`, `KG_TO_LB=2.20462`) + `src/hooks/useFarmConfig.ts` (`fmtWeight`, `weightUnit`) exist and are correct, but a repo-wide grep shows **`useFarmConfig`/`fmtWeight`/`weightUnit` are imported by 0 pages/components** — dead layer.
3. **UI weight display is hardcoded kg or a manual input toggle (not country-driven):**
   - `src/app/(app)/finishers/page.tsx:120` → `{g.avg_exit_weight_kg}kg` (always "kg").
   - `src/app/(app)/record/page.tsx:365` → local `useState<"kg"|"lbs">("kg")` input toggle, defaults kg; user-selectable, not derived from farm country.
   - `src/app/(app)/reports/page.tsx` renders **no weight-bearing columns** (only rate KPIs: PSY/NPD/FR/RTS/PWMR) — there is no kg/lb on the reports screen to localize. Report APIs (`/reports/reproduction`, `/reports/grow-finish`) return raw `*_kg` fields by schema; both returned `[]` for the empty US farm (HTTP 200).

**Classification: KNOWN_GAP** — automatic US→lb unit localization is not implemented (neither the seed data nor a UI consumer). Weights display in kg for US. No integrity risk (conversion math is correct where wired; storage is metric). This is a localization feature gap, not a regression. Per guardrails: not "fixing" — recorded only.

---

## Summary

| Step | Area | Result |
|------|------|--------|
| 1 | US account/farm create + login (country=US, en, USD) | **PASS** |
| 2 | English UI: 0 Korean leak / 0 raw key / 0 "MVP"; 7-locale key parity; live en dashboard artifact; en API text | **PASS** |
| 3 | Country (US) drives KPI thresholds — proven across 5 locales (target=26 = US PSY), US fully seeded, benchmark-missing→silence | **PASS** |
| 4 | Report/UI weight units (US=lb) | **KNOWN_GAP** (UI shows kg; `region_defaults` empty + `useFarmConfig` unused; reports show no weight columns) |

**KNOWN_GAPs (non-blocking):**
- (G1) US=lb weight localization not wired: `region_defaults` table empty (no country→unit seed) and the `fmtWeight`/`useFarmConfig`/`units.ts` layer is consumed by 0 components. Finishers hardcode "kg"; record page has a manual kg/lbs toggle; reports have no weight columns.
- (G2) Template Renderer translates only en+ko; es/vi/zh chat answers render English text (thresholds still correct per country). Matches CLAUDE.md ("renderer.py (en/ko)").
- (G3) MX/TH have no `default_metric_values` region seed → global(system) fallback if used (not exercised in this US run).

Per guardrail: no source changed, no commit; all test data isolated in throwaway `qa-us-en-1782292928` org/farm.

**FINAL: US PASS for core market readiness (country-driven KPI thresholds + clean English UI + USD). Weight-unit localization (US=lb) is a KNOWN_GAP — UI displays kg.**
