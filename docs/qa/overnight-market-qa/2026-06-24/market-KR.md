# PigOS Overnight Market QA — Market [KR] (country=KR, lang=ko) — 2026-06-24

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000` + API `localhost:8000` (docker postgres `pigos`).
Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.
All test data isolated under `qa-kr-ko-*` namespace (created then deleted — 0 residual).

**Headline: KR market = PASS, with 2 documented KNOWN_GAPs (currency fallback, ko is admin-only by design).**
KR is a fully-seeded market: 27 region-scoped KPI thresholds drive the rule engine. Country (not language) selects thresholds — proven live (KR PSY warning=22 vs US=26, language-invariant). Report weight unit = kg for KR (PASS). ko UI is intentionally admin-console-only; the KR customer-facing farm app renders English by design (no ko leak on customer host — proven live).

Harness: `scratchpad/kr_market_qa.py` → `scratchpad/kr_qa_results.json` (**10/10 PASS**). i18n parity via flatten-diff of `src/messages/{en,ko}.json`. Live SSR locale gating via `curl` against both customer (`localhost`) and admin (`admin.localhost`) hosts.

---

## Protocol item 1 — KR signup/login (P0 = TEST TARGET)

P0 baseline judged KR as **(b) TEST TARGET** — no country block/redirect in code; KR is the default onboarding country. Full E2E performed (not config-only).

| Check | Evidence | Result |
|-------|----------|--------|
| KR signup (`POST /onboarding/complete` country=KR) | **201** — org+user+farm+tokens returned | PASS |
| KR login round-trip (`POST /auth/login`) | **200** + `access_token` | PASS |
| `farm.country` persisted | DB `farms.country = 'KR'` | PASS |

No KR-specific gate exists in `src/middleware.ts`, `onboarding.py`, or backend (`country` is a free-form ISO-3166 attribute). Any "KR→PigPlan" positioning is business strategy, not enforced in code.

---

## Protocol item 3 — Country (not language) drives KPI thresholds — PASS (decisive)

**Mechanism (from code):** `kpi_service.build_rule_context` sets `RuleContext.country = farm.country`, then `_all_benchmarks` calls SQL `effective_metric_values(farm, region=farm.country, market='SYSTEM')`. Rule engine (`engine/rules/base.py _psy_analysis`, `rules/_common.py resolve`) reads `ctx.benchmarks[kpi]["warning"/"critical"]`. **Logic is country-neutral (1 codebase); only the numeric thresholds vary by country.**

**Live proof** — onboarded a KR farm and a US farm, queried `POST /farms/{id}/chat/query` ("What is my PSY?"), inspected `finding.target_value` (= resolved warning threshold):

| Farm | Locale queried | PSY warning resolved | Source (DB seed) |
|------|---------------|----------------------|------------------|
| KR | ko | **22.0** | `default_metric_values` region KR PSY w/c = **22.00/18.00** |
| KR | en | **22.0** (identical) | language-invariant ✔ |
| US (control) | en | **26.0** | region US PSY w/c = **26.00/23.00** |

- `KR(22) ≠ US(26)` → **country determines threshold**. PASS.
- `KR/ko == KR/en (22.0 == 22.0)` → **language does NOT change threshold**. PASS.

**KR is a fully-seeded market — NOT benchmark-missing.** Live DB `default_metric_values` has **27 region-scoped KR rows** (PSY, NPD, WSI, RTS_RATE, FARROWING_RATE, PRE_WEANING_MORTALITY, BORN_ALIVE, WEANED_COUNT, STILLBORN_RATE, ABORTION_RATE, CULLING_RATE, sow residual/salvage P0–P6, etc.). Sample KR thresholds (warning / critical / target):
`PSY 22/18/24` · `WSI 7/10/7` · `RTS_RATE 5/12/5` · `FARROWING_RATE 83/78/85` · `PRE_WEANING_MORTALITY 10/14/8` · `NPD 35/50/20`.

Note (guardrail-aligned): the **PSY 22/18** values are the **real seed** — confirmed by direct DB read, not injected. Where a metric/country row is absent the rule correctly stays silent (benchmark fallback), which is the intended behavior; no fabricated numbers were introduced.

---

## Protocol item 4 — Report units (US=lb / others=kg) — KR PASS

`farm_service.get_local_config` resolves `weight_unit` by `farm.country → region_defaults → "kg"`. FE `useFarmConfig` / `lib/utils/units.ts` formats kg unless unit=="lb".

| Check | Evidence | Result |
|-------|----------|--------|
| KR `GET /farms/{id}/config` `weight_unit` | **`kg`** (status 200) | PASS |

**KNOWN_GAP (unit/currency source unseeded):** live `region_defaults` table has **0 rows**. So `weight_unit` always falls back to the hardcoded `"kg"`, and `currency_code` falls back to `USD`.
- For **KR this yields the *correct* unit (kg)** → item 4 PASS for KR.
- KR currency resolves to **USD**, not KRW → **KNOWN_GAP** (KR-relevant; benchmark seed `2026-03-19_seed-data.sql` lists KR currency `KRW`, but `region_defaults` is not seeded so it never reaches the API).
- Side note (out of KR scope): because `region_defaults` is empty, a **US** farm would also fall back to kg, i.e. would **not** get `lb` — a US-market KNOWN_GAP, not a KR failure. Flagged for the US market run.

---

## Protocol item 2 — ko language UI / no leak / no raw keys / no "MVP" — PASS (by-design: ko = admin-only)

### 2a. i18n message-file integrity (`src/messages/en.json` vs `ko.json`)
Flatten-diff (nested keys expanded):

| Check | Evidence | Result |
|-------|----------|--------|
| Key parity en↔ko | **1337 / 1337**, missing=0, extra=0 | PASS |
| Raw-key / empty-value leaks in ko | **0** | PASS |
| `"MVP"` literal in ko (and all locales) | **0** | PASS |
| ko values without Hangul | 7, all intentional proper-nouns / KPI codes (`AI Active`, `Rule Engine`, `PWMR-A`, `PWMR-B`, `Beta`, `Data Dividend Program`, `{metric} {value}{unit}` template) | PASS |

All 7 locales (en/ko/zh/es/vi/th/pt) carry identical key counts (1459 raw lines / 1337 flattened keys).

### 2b. Live SSR locale gating — **ko is platform-admin-only by design**
Source of truth: `src/i18n/config.ts` (`ADMIN_ONLY_LOCALES = ["ko"]`) + `src/i18n/request.ts` (ko allowed only when `host.startsWith("admin.")`, else downgraded to `defaultLocale`). Commit `f06c57c` ("ko SSR 누수 차단 — admin 호스트에서만 허용"). Login page (`(auth)/login/page.tsx` line 17) explicitly: "한국어는 로그인 전 화면에 노출하지 않음(해외 출시)".

Live `curl` evidence:

| Host | Cookie | Page | Rendered `lang` | Nav text | Result |
|------|--------|------|-----------------|----------|--------|
| `localhost:3000` (customer) | `NEXT_LOCALE=ko` | `/login` | **`lang="en"`** | English | PASS (ko downgraded — no leak) |
| `localhost:3000` (customer) | `NEXT_LOCALE=ko` | `/` (app) | **`lang="en"`** | Dashboard/Sows/Record/Analytics/Reports (English) | PASS (ko downgraded) |
| `localhost:3000` (customer) | `NEXT_LOCALE=en` | `/` (app) | `lang="en"` | **0 raw dotted-key leaks** in rendered text | PASS |
| `admin.localhost` (admin) | `NEXT_LOCALE=ko` | `/login` | **`lang="ko"`** | — | PASS (ko allowed on admin host) |
| `admin.localhost` (admin) | `NEXT_LOCALE=ko` | `/admin` | **200, `lang="ko"`** | Korean admin console renders | PASS |
| `admin.localhost` (admin) | `NEXT_LOCALE=ko` | `/`, `/sows` | **307 → `/admin`** | app routes redirected off admin host (domain separation) | PASS |

**Interpretation:** The KR *customer-facing farm app* is intentionally **English-only** (ko is reserved for the platform admin console at `admin.*`). This matches the documented "해외 출시 / KR→PigPlan" business posture. Therefore:
- "비한국어모드 한국어 누수 0" → **PASS** (customer host with ko cookie still renders English; verified no Hangul leak in customer SSR).
- "ko 전환 → UI 갱신" → the ko UI is reachable and correct **only on the admin host** (proven: `/admin` renders `lang="ko"`). On the customer host it is by-design unavailable → **KNOWN_GAP** *only if* the product intends Korean customer UI; per current strategy this is the intended design, so **PASS with KNOWN_GAP note**.
- "raw i18n키 0 / MVP 0" → **PASS** (message files + live customer HTML both clean).
- "KR/en은 영어 UI에서도 KR 임계 유지" → **PASS** — proven in item 3 (KR farm queried in en still resolves KR PSY=22, because country, not locale, drives thresholds).

---

## Summary

| # | Protocol item | Result | Key evidence |
|---|---------------|--------|--------------|
| 1 | KR signup→login (country=KR) | **PASS** | onboarding 201, login 200, farms.country='KR' |
| 2 | ko UI / no leak / no raw-key / no "MVP" | **PASS** (ko=admin-only by design) | en↔ko 1337/1337, 0 leaks/0 MVP; customer host ko→en, admin host lang=ko |
| 3 | Country drives KPI thresholds (not language) | **PASS** | KR PSY=22 vs US=26, KR/ko==KR/en; 27 KR region rows seeded |
| 4 | Report units (KR=kg) | **PASS** | `/farms/{id}/config` weight_unit=`kg` |

**KNOWN_GAPs (non-blocking, documented — not "fixed" per guardrail):**
1. `region_defaults` table is **unseeded (0 rows)** → `weight_unit` always falls back to `kg` (correct for KR, **wrong for US** which should be lb — US-market gap) and KR currency falls back to **USD instead of KRW**.
2. ko locale is **platform-admin-only** by design; the KR customer farm app ships English UI (intended per overseas-launch strategy; flagged in case product later wants Korean customer UI).
3. Chat `ChatQuery.locale` pattern allows only `en|ko|zh|es|vi` — **excludes th/pt** (those 2 markets' Q&A would 422 on a th/pt locale param and need `en` fallback). Out of KR scope; noted for TH/PT runs.

**Guardrail compliance:** No source code changed, no commit, no push. No threshold/benchmark values injected — all read from live seed. PSY 22/18 confirmed as real seed (not the hypothesized guardrail value). Test data (`qa-kr-ko-*`: 4 orgs/4 farms/4 users) created and fully deleted (0 residual). The unseeded `region_defaults` / USD-currency findings are **recorded, not patched**.

**FINAL: KR = PASS** (+ 3 documented KNOWN_GAPs above; none compromise KR KPI-threshold correctness, which is the core market requirement).
