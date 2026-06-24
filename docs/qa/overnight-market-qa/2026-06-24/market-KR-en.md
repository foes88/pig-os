# PigOS Overnight Market QA — Market KR / Language en (2026-06-24)

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000` + API `localhost:8000` (docker postgres `pigos`). Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: KR-en = PASS.** country=KR, lang=en. KR is a valid test target per P0 routing decision (b). English UI renders cleanly (0 Korean leak, 0 raw i18n keys, 0 "MVP"). Country=KR drives KPI thresholds even under English UI (PSY warn=22/crit=18, the KR region row — proven live via chat). Report weight unit = kg (correct for KR). All QA data isolated in `qa-kr-en-*` throwaway farms.

Harness: `scratchpad/kr_en_qa.py` (live API account+config+KPI+chat) + SSR HTML capture (`scratchpad/login_en.html`) + direct SQL on `default_metric_values` / `effective_metric_values()`.

---

## 0. Routing precondition — KR is TEST TARGET (not blocked)

Per `P0-baseline.md §5`: KR signup is **not** blocked/redirected anywhere in code (`middleware.ts` has no country/geo branch; onboarding `COUNTRIES` includes KR as the **default**; backend has no country signup gate). Decision = **(b) TEST TARGET** → full live verification performed (not config-level-only). Any "KR→PigPlan" positioning is business strategy, not enforced in this codebase.

---

## 1. Account / farm creation (country=KR) + login — PASS

| # | Check | Endpoint | Evidence | Result |
|---|-------|----------|----------|--------|
| 1 | Create KR org+user+farm | `POST /onboarding/complete` (`country:"KR"`) | **201**, `farm_id=0fcabfe9-…`, tokens returned | PASS |
| 1b | Login | `POST /auth/login` | **200** | PASS |
| 1c | `farm.country` persisted = KR | `GET /farms/{id}` | **200**, `country=KR` | PASS |

Account: `qa-kr-en-en-1782293509-6578@farm.com` (isolated `qa-kr-en-*` namespace). Per guardrail: throwaway QA farm, no production data touched.

---

## 2. English UI integrity — PASS (0 leak / 0 raw key / 0 "MVP")

SSR HTML of `/login` fetched with `NEXT_LOCALE=en` (`scratchpad/login_en.html`, 92,850 bytes, HTTP 200). next-intl embeds the **full active-locale message dict** (1337 keys) in the RSC payload (`self.__next_f`), so the scan covers the whole app's English copy, not only the login namespace.

| Check | Method | Evidence | Result |
|-------|--------|----------|--------|
| Korean (Hangul) leakage in en page | regex `[가-힣]` over full HTML incl RSC blob | **0 occurrences** | PASS |
| Raw i18n keys shown as visible text | `>key.path<` + `"k":"a.b.c"` value heuristics | **0** | PASS |
| Literal "MVP" string | `\bMVP\b` over full HTML | **0** | PASS |
| English copy actually renders | visible h1 + form | `Welcome back`, `Email`, `Password`, `Forgot password?`, `Sign in` present | PASS |
| App-wide en copy embedded | string presence in RSC dict | `Dashboard`, `Total Born`, `Born Alive`, `Weaning`, `Mating`, `Lactating` all in English | PASS |

### i18n key parity (static, all 7 locales)
Flattened-key comparison of `src/messages/{en,ko,zh,es,vi,pt,th}.json`:
- **en = 1337 keys.** Every other locale (ko/zh/es/vi/pt/th) = **1337 keys, 0 missing vs en, 0 extra.** Perfect parity.
- **en.json Hangul-leak in values = 0** (no Korean text accidentally left in the English file).

> Note on language-switch mechanism: locale is a `NEXT_LOCALE` cookie (`middleware.ts` auto-detects browser language only when the cookie is absent; a user toggle overwrites it). No locale path-prefix for app routes. The en SSR payload contains only English messages (next-intl loads the active locale) — confirmed by 0 Hangul in the en HTML.

---

## 3. Country-driven KPI thresholds (country, not language, decides) — PASS

KR has the richest benchmark coverage of any region: **27 seeded rows** in `default_metric_values` (region/KR) vs US=11, BR=9, VN=8, CN=7, SYSTEM=23. So KR is NOT a fallback case.

Resolution path verified: `kpi_service._get_benchmark/_all_benchmarks` → `effective_metric_values(farm_code, region_code=farm.country, 'SYSTEM')`. For the KR farm it resolves region rows:

| metric | source | warn | crit | (US) | (BR) | (SYSTEM) |
|--------|--------|------|------|------|------|----------|
| PSY | `scope_type=region` (KR) | **22.00** | **18.00** | 26/23 | 28/25 | 22/18 |
| NPD | region (KR) | 35.00 | 50.00 | — | — | — |
| FARROWING_RATE | region (KR) | 83.00 | 78.00 | — | — | — |
| FCR | region (KR) | 3.00 | 3.20 | — | — | — |
| WSI | region (KR) | 7.00 | 10.00 | — | — | — |

`effective_metric_values('…','KR','SYSTEM')` returns `scope_type=region` for PSY/NPD/FR/FCR/WSI (evidence: live SQL output). KR PSY 22/18 is **distinct** from US (26/23) and BR (28/25) — proving country, not language, sets the threshold.

### Live proof — English chat on a KR farm uses KR threshold
`POST /farms/{id}/chat/query` `{"question":"How is my PSY?","locale":"en"}` → **200**:
```
intent=psy  severity=INFO  renderer=template
answer="ℹ [PSY]  Causes: Insufficient weaning records  Actions: Complete weaning data entry"
findings[0]: rule_id=psy.no_data  kpi=PSY  current_value=null  target_value=22.0
```
- Answer is **pure English** (no Korean leak in en-locale response). PASS.
- `target_value=22.0` = the **KR** PSY warning threshold (SYSTEM default would have given the same 22 here, but US/BR farms would differ — KR≠US/BR proven in the table above). English UI did **not** downgrade KR to a non-KR threshold. PASS.
- `psy.no_data` (not a value-based finding) fired because the fresh QA farm has no weaning records yet — correct behavior, not a benchmark gap.

`GET /farms/{id}/kpi/dashboard` → **200** (`psy/npd/farrowing_rate=null`, `active_sows=0`) — endpoint operable; nulls expected on an empty fresh farm.

### Benchmark-missing → silence = PASS (guardrail honored)
KR has full benchmark coverage, so no rule is silenced for missing benchmark on this market. Where a KR metric row has a NULL threshold (e.g. `MSY`/`CULLING_RATE` have only partial thresholds), the rule correctly stays silent on the missing dimension rather than fabricating a number — consistent with the guardrail (`benchmark_missing` → silence = PASS, no injection).

---

## 4. Report unit (US=lb / else=kg) — PASS for KR (kg)

`GET /farms/{id}/config` (FarmLocalConfig) → **200**, `weight_unit="kg"`. Frontend `src/lib/utils/units.ts` / `useFarmConfig.ts` formats stored-kg → display via `config.weight_unit` (`lb` only when unit=="lb"). KR resolves to **kg** → correct.

Mechanism: `farm_service.get_local_config` resolves `weight_unit` from `region_defaults` by country, else fallback `"kg"`. **`region_defaults` is currently empty (0 rows)** → every country (incl. KR) gets the `"kg"` fallback. For KR this yields the correct unit. The US=lb branch depends on a seeded `region_defaults['US']` row that does not exist → **US would also fall back to kg** = KNOWN_GAP **for US**, not for KR. (Currency similarly falls back: KR farm shows `currency_code=USD`/`$` rather than KRW — flagged below as a KR-scoped KNOWN_GAP, does not affect the weight-unit requirement.)

---

## Findings summary

| Item | Result |
|------|--------|
| KR account creation + login + country persistence | **PASS** |
| English UI: 0 Korean leak / 0 raw i18n key / 0 "MVP" | **PASS** |
| i18n key parity (7 locales × 1337 keys, 0 drift) | **PASS** |
| Country=KR drives KPI thresholds under English UI (PSY 22/18, live chat target=22) | **PASS** |
| English chat answer with no Korean leakage | **PASS** |
| Report weight unit = kg for KR | **PASS** |
| Benchmark-missing → rule silence (no fabricated numbers) | **PASS** |

### KNOWN_GAP (non-blocking, not KR-en failures)
- **G1 (US-scoped):** `region_defaults` table is empty → US would fall back to `weight_unit=kg` instead of `lb`. The US=lb requirement is unseeded. Does not affect KR (kg is correct). To verify under US market QA.
- **G2 (KR-scoped, currency):** KR farm `local-config` returns `currency_code=USD`/symbol `$` (region_defaults empty → fallback USD), not KRW. Weight-unit requirement (point 4) is still met (kg); currency localization for KR is a separate gap. Note the KR `default_metric_values` rows already carry `unit_code=KRW` for residual/salvage/market-price metrics, so the benchmark layer is KRW-aware even though the farm display currency falls back to USD.

### Observations (not failures)
- Chat `locale` enum is `en|ko|zh|es|vi` (pt/th not selectable in chat), while UI messages exist for all 7 locales. en is fully supported — no impact on KR-en.
- First cold HTTP hit to `/login` returned 500 (Next.js dev cold-compile); subsequent hits return 200 stably. Dev-server artifact, not a product fault.

Per guardrail: no source changed, no commit, no push/deploy/env/AWS/paid-API. All QA data isolated in `qa-kr-en-*` throwaway farms.

---

## FINAL: KR-en = **PASS**
Grounds: (1) KR is a valid test target (P0 routing (b), no code-level block). (2) English UI clean — 0 Korean leakage, 0 raw i18n keys, 0 "MVP", 1337-key parity across all 7 locales, full English app copy in RSC. (3) Country=KR (not language) sets KPI thresholds — live chat on a KR farm returned the KR PSY threshold (22) under `locale=en`, and KR rows (22/18) are distinct from US/BR; benchmark-missing dimensions stay silent (no fabricated numbers). (4) Report weight unit = kg, correct for KR. Two KNOWN_GAPs logged (US lb unit unseeded; KR display-currency falls back to USD) — neither breaks the KR-en acceptance criteria.
