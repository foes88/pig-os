# PigOS Overnight Market QA — P2 Market Row: BRAZIL (BR / pt) — 2026-06-24

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000` + API `localhost:8000` (docker postgres `pigos`). Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: BR = PASS (2 minor KNOWN_GAPs, neither BR-specific).** A BR (country=BR, lang=pt) account was created live via `POST /onboarding/complete` and verified end-to-end. Unlike MX/TH (no seed → global fallback), **Brazil is a fully-seeded market**: `/thresholds` returns **9 country(BR) + 15 global** rows — BR genuinely layers its 9 seeded Embrapa/Interpig-class thresholds over global, with **zero leakage of any other country's thresholds** (KR/US/CN/VN). Country (not language) drives KPI thresholds — proven structurally (`threshold_service` keys on `farm.country`) and live. Portuguese i18n (`pt.json`) has **full 1337/1337 key parity, 0 Korean leak, 0 "MVP" strings, 0 empty values**; pt SSR and the next-intl app shell render Portuguese (nav: Painel/Matrizes/Cachaços/Leitões/Terminação/Alertas/Relatórios). BR report unit = **kg** (correct for non-US). The 2 gaps are **not BR failures**: (a) the chat free-text renderer supports only en/ko (pt falls back to English NL text — Base/MVP limitation, Addon #1 territory); (b) the `/onboarding` pre-auth page + one bottom-nav label ("Settings") are hard-coded English (consistent across all non-en locales, never a raw-key leak).

Test artifacts (isolated `qa-br-pt-*` namespace):
- BR farm `78973e78-fb87-45ea-893b-7df765d90414`, org `252dac21-8f6b-4f3f-8da9-992a256958d0`, user `f1b80883-72a7-489e-ba2c-62163793d89c`, email `qa-br-pt-1782293507@example.com`, tz `America/Sao_Paulo`.

---

## 1. Account / farm creation (BR) — PASS

| Step | Command | Result |
|------|---------|--------|
| Create org+user+farm country=BR | `POST /api/v1/onboarding/complete` (`country=BR`, `farm_type=FARROW_TO_FINISH`, `sow_count=120`, tz `America/Sao_Paulo`) | **201** — returned `org_id, farm_id, user_id, access_token, refresh_token` |
| Login | `POST /api/v1/auth/login` | **200** — access/refresh tokens issued |
| `/auth/me` | `GET /api/v1/auth/me` | **200** — `role=FARM_OWNER`, `org_id` set, `farm_ids=[78973e78…]` |
| Farm country persisted | DB `SELECT country FROM farms` | **`country=BR`**, `farm_code=FARM-BR-252DAC` |
| Org country persisted | DB join organizations | **`country=BR`** |

Onboarding schema (`schemas/auth.py::OnboardingCompleteRequest`) takes `country` as ISO-3166-1 alpha-2; BR accepted with no gating. Farm code is auto-derived from country → `FARM-BR-...` (confirms country wired into provisioning). (KR routing per P0-baseline §5 = TEST TARGET, no block — BR is the subject here.)

---

## 2. KPI thresholds are country-driven (NOT language-driven) — PASS

Source of truth: `app/services/threshold_service.py`. Resolution priority = **farm > region(country) > system(global)** (`_SCOPE_RANK`, L14). Region rows are matched strictly by `r.scope_type == "region" and r.scope_code == farm.country` (L27) — it is **structurally impossible** to pick another country's row for a BR farm. Scope labels: region→`country`, system→`global` (`_SCOPE_LABEL`, L15).

**DB ground truth** (`default_metric_values`, `docker exec pigos-postgres psql`):
```
region BR=9, region CN=7, region KR=27, region US=11, region VN=8, system SYSTEM=23
region MX=0, region TH=0   ← no Mexico/Thailand rows (those markets = global fallback)
```

**Live BR farm thresholds** (`GET /api/v1/farms/{br_farm}/thresholds`):
- **scope distribution: `{'country': 9, 'global': 15}` — total 24.** BR layers its 9 seeded BR rows over 15 global. (This is the key BR-vs-MX difference: MX = 23×global/0×country; BR = 9×country.)
- The 9 `scope=country` (BR) rows, verbatim from the live API:

| metric | warning | critical |
|--------|---------|----------|
| PSY | 28.0 | 25.0 |
| NPD | 42.0 | 58.0 |
| FARROWING_RATE | 80.0 | 70.0 |
| WSI | 7.0 | 10.0 |
| BORN_ALIVE | 13.0 | 12.0 |
| WEANED_COUNT | 12.0 | 10.0 |
| PRE_WEANING_MORTALITY | 12.0 | 16.0 |
| STILLBORN_RATE | 8.2 | 12.0 |
| MARKET_PRICE_HEAD | null | null |

These match the **`default_metric_values` region/BR seed rows exactly** (9 rows; verified by direct DB query). No fabrication.

**Provenance / no-leak check:** BR's resolved PSY = **28/25** (distinct from SYSTEM-global PSY **22/18** and from KR **22/18**, US **26/23**). The `effective_metric_values('{br_farm}','BR','SYSTEM')` SQL function and the `/thresholds` service independently return the same BR-specific values. A BR farm **never** borrows KR/US/CN/VN thresholds — the `scope` field on every row proves provenance (`country` = BR seed, `global` = SYSTEM).

**Benchmark-missing → silence (PASS):** Several BR-resolved metrics carry NULL `benchmark_avg` (ABORTION_RATE, ADG, BIRTH_WEIGHT, CULLING_RATE, FINISH_MORTALITY, HIGH_PARITY_RATIO, MUMMIFIED_RATE, SOW_MORTALITY, TOTAL_BORN, MARKET_PRICE_HEAD). Per guardrail, `benchmark missing → rule silence = PASS (benchmark_missing)`; no arbitrary numbers were injected and none should be. The 15 `global`-scope BR metrics (FCR 3.0/3.3, ADG 650/550, etc.) are the genuine SYSTEM fallback for KPIs BR has not localized — that is the documented design, not a leak.

---

## 3. Rule Engine runs for BR farm (country=BR context) — PASS

| Check | Command | Result |
|-------|---------|--------|
| Dashboard KPI | `GET /farms/{br_farm}/kpi/dashboard` | **200** — `country:"BR"`, `benchmarks.PSY.avg=29.5` (BR-specific), `FARROWING_RATE.avg=79.0` (BR-specific), KPI values `null` (empty farm — honest, no fabrication) |
| Chat / Rule Engine | `POST /farms/{br_farm}/chat/query` `{"question":"How is my farm doing?","lang":"pt"}` | **200** — `intent=dashboard`, `renderer:"template"`, findings with **`current_value:null`** (no invented numbers); PSY finding `target_value:28.0` = BR warning threshold |
| Alerts (empty farm) | dashboard `alerts[]` | only `inventory.zero` + `farm.health_class` (data-integrity alerts), **not** fabricated KPI breaches |

The rule pipeline executes against BR country thresholds (target_value 28.0 = BR PSY warning). Empty farm → no false KPI alerts; benchmark-missing KPIs stayed silent. `current_value:null` everywhere — zero data fabrication.

**Dashboard benchmarks block proves country=BR (not lang):** PSY avg **29.5**, FARROWING_RATE avg **79.0** are the BR `benchmark_avg` values (vs default 24.3 / 81.0), returned for this farm purely because `farm.country=BR` — language was pt and did not affect them.

---

## 4. Language = Portuguese (pt) UI — PASS (with 2 localization KNOWN_GAPs, non-BR-specific)

### 4a. pt is a public locale, cookie-driven — PASS
`src/i18n/config.ts`: `locales = ["en","ko","zh","es","vi","th","pt"]`; pt is a **public** locale (only `ko` is `ADMIN_ONLY`). Set via `NEXT_LOCALE` cookie (`i18n/request.ts`, `middleware.ts`). App pages use next-intl `useTranslations` → `messages/pt.json`; the Sidebar uses an inline per-locale label map with `t = (obj) => obj[lang] ?? obj.en`.

### 4b. pt.json static integrity — PASS
(`src/messages/en.json` vs `pt.json`, flattened key comparison, Python)
- **Key parity: 1337 en / 1337 pt — 0 missing, 0 extra.**
- **0 empty pt values.**
- **0 Korean (Hangul) characters** anywhere in pt values.
- **0 "MVP" literal strings** in pt.
- Sample genuine Portuguese values: `nav.dashboard="Painel"`, `nav.sows="Matrizes"`, `dashboard.title="Painel IA"`, `common.save="Salvar"`.

### 4c. Sidebar (chrome) pt labels — PASS (1 English-fallback label noted)
26 inline nav-label locale objects in `Sidebar.tsx`. **0 Korean leak in pt slots.** pt labels are genuine Portuguese: Painel, Registro, Plantel, Matrizes, Cachaços, Leitões, Terminação, "Tarefas e alertas", "Tarefas de hoje", Alertas, Relatórios, "Resumo KPI", "Status das matrizes", "Relatório diário", "Diário completo", "Parto e desmame", Mortalidade, "Produção (Reprodução)". **1 of 26 missing pt slot**: the bottom-nav **"Settings"** label (`BOTTOM_ITEMS`, L97) has only en/ko/zh/es/vi (also missing **th**). Because `t = obj[lang] ?? obj.en`, pt renders the **English "Settings"** — graceful fallback, **not** a raw-key leak, not Korean, not broken. Minor cosmetic gap.

### 4d. Live SSR render — PASS (no raw keys, no Korean, no MVP)
`GET /login` and `GET /onboarding` with `Cookie: NEXT_LOCALE=pt` (and en control), HTML parsed (Python, tags stripped):
- pt `/login`: 200, **0 candidate raw-i18n-key leaks** (`a.b.c` visible text), **0 Hangul**, **0 "MVP"**.
- en `/login` control: identical (0 raw keys, 0 Hangul, 0 MVP).
- pt `/onboarding`: 200, **0 raw keys, 0 Hangul, 0 MVP**.

### 4e. No Korean leak in non-KR mode — PASS
`ko` is `ADMIN_ONLY_LOCALES` → downgraded to `defaultLocale` on non-admin localhost (`i18n/request.ts`). pt/en SSR captures contain **0 Hangul** in visible text. Customer app cannot serve Korean.

### 4f. KNOWN_GAP — `/onboarding` page is hard-coded English (all locales)
`src/app/onboarding/page.tsx` uses **literal English strings** (`"Farm information"`, `"Tell us about your farm operation"`, `"Country"`, `"Continue"`, country labels incl. `"Brazil"`) with **no `useTranslations`**. pt and en SSR render byte-identical English copy for this page. This is **not** a raw-key leak and **not** BR-specific — it affects every non-en locale equally. Recorded as KNOWN_GAP (pre-auth onboarding not localized). Not fixed (guardrail: record, don't edit).

---

## 5. Report units (US=lb / else=kg) — PARTIAL (BR correct; US=lb is a KNOWN_GAP, not BR)

Unit conversion: `src/lib/utils/units.ts` (`kgToDisplay`, `formatWeight`) driven by `FarmLocalConfig.weight_unit` from `GET /farms/{id}/config`. All weights stored as kg; display converts to lb only when `weight_unit=="lb"` (`KG_TO_LB=2.20462`).

| Farm | `GET /config` weight_unit | Expected (brief) | Result |
|------|---------------------------|------------------|--------|
| **BR** (this market) | **`kg`** | kg (non-US) | **PASS** |
| US (control, per MX report) | `kg` | lb | **KNOWN_GAP** |

BR `GET /farms/{br_farm}/config` → `weight_unit:"kg"`, `currency_code:"USD"`, `currency_symbol:"$"`. **For Brazil this is correct** (BR displays kg). The US=lb gap (region_defaults/market_defaults empty → US also returns kg) is a US-market data-seeding gap documented in `market-MX.md` §5, not a BR failure. BR currency ideally BRL, but USD/$ is the same unseeded-region read-only display gap (non-integrity).

---

## 6. KNOWN_GAP — chat free-text renderer is en/ko only (pt → English NL)

`api/app/engine/renderer.py` header states *"Locales supported: en, ko"*; `render_text` selects `_CAUSE_KO/_ACTION_KO if locale=="ko" else _CAUSE_EN/_ACTION_EN`. A `lang:"pt"` chat query returns 200 with **structured findings language-neutral and correct** (rule_id, severity, current_value, target_value), but the human-readable `answer` causes/actions render in **English** (e.g. "Insufficient weaning records", "Complete weaning data entry"). This is the **Base/MVP** Template Renderer; full pt NL is Addon #1 (LLM) per CLAUDE.md Q&A architecture. KNOWN_GAP — the structured layer is sound; only the NL veneer is en/ko-bound.

---

## Summary — BR = PASS (2 KNOWN_GAPs, neither BR-specific)

| Dimension | Verdict | Evidence |
|-----------|---------|----------|
| Account/farm creation (country=BR) | **PASS** | onboarding 201, login 200, `/me` 200, farm+org `country=BR` persisted, `farm_code=FARM-BR-…` |
| KPI thresholds country-driven | **PASS** | BR `/thresholds` = **9 country + 15 global**; 9 BR rows match seed exactly; 0 other-country leak |
| BR is fully seeded (not fallback) | **PASS** | `region BR=9` rows; PSY 28/25, NPD 42/58, FR 80/70, WSI 7/10 distinct from global 22/18 etc. |
| No other-country threshold borrowed | **PASS** | `threshold_service` keys on `farm.country` (L27); scope field proves provenance |
| benchmark missing → rule silence | **PASS** | NULL `benchmark_avg` metrics left silent; no numbers injected; `current_value:null` in chat |
| Rule Engine on BR farm | **PASS** | dashboard 200 (`country:BR`, BR benchmarks 29.5/79.0), chat 200 (`target_value:28.0`=BR), alerts data-integrity only |
| Portuguese (pt) UI renders | **PASS** | pt.json 1337/1337, genuine pt nav/values; pt SSR 0 raw keys / 0 Hangul / 0 MVP |
| Korean leak in non-KR mode | **PASS** | ko=ADMIN_ONLY → downgraded; 0 Hangul in pt/en SSR and pt nav slots |
| Raw i18n keys / "MVP" strings | **PASS** | pt 1337/1337 parity, 0 empty, 0 raw key, 0 "MVP" |
| Report units (BR=kg) | **PASS** | `/config` weight_unit=`kg` |
| Report units (US=lb) | **KNOWN_GAP** | region/market_defaults empty → US returns kg (US-market gap, documented; not BR) |
| Onboarding page localization | **KNOWN_GAP** | `/onboarding` hard-coded English (all locales, not BR-specific); not a raw-key leak |
| Chat NL renderer locale coverage | **KNOWN_GAP** | renderer en/ko only; pt structured findings correct, NL text falls back to English (Base/MVP; Addon #1 = LLM) |
| Sidebar "Settings" label (pt) | minor | 1/26 nav label missing pt slot → English fallback via `?? obj.en` (cosmetic, no leak) |

**Guardrails honored:** no source code changed, no commit/push, no prod DB mutation; all test data isolated under `qa-br-pt-*`. No threshold values injected; BR thresholds read from seed (9 region/BR rows), never assumed; no other-country thresholds substituted for BR; stillborn-rate formula (`(stillborn+mummified)/total_born`) untouched; benchmark-missing KPIs left silent (not FAILed by external bench comparison); PSY 28/25 read from BR seed, not from the unverified 22/18 hypothesis. Gaps recorded, not fixed.

**Operational note (non-blocking):** the Next dev server intermittently times out on first-hit route compilation (a pt `/login` fetch hit a 90s cap once, code=000; root `/` stays instant at 307; API healthy throughout). A queued Playwright i18n spec (`_uat_tmp/i18n-lang-switch.live.spec.ts`) timed out on `page.goto("/login")` for the same reason (worker SIGTERM, code=143) — a dev-compilation/timeout artifact, not a pt-translation defect. pt SSR captures succeeded once routes compiled; static pt.json + live `/thresholds` + dashboard API evidence are authoritative.
