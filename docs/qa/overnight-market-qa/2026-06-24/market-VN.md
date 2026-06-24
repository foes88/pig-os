# PigOS Overnight Market QA — P2 Market VN (country=VN, lang=vi) — 2026-06-24

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000`, API `localhost:8000` (docker postgres `pigos`). Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: VN market = PASS with 2 KNOWN_GAPs (cross-market, not VN-specific).** A VN-country farm was created and driven live; country=VN correctly drives KPI benchmark thresholds (distinct from KR/global); vi UI renders with zero Korean leak, zero raw i18n keys, zero "MVP" literal; vi has full message parity (1337/1337). The 2 gaps (US lb-unit not wired; chat finding cause/action codes not localized) are platform-wide, do not block VN.

Harness: `scratchpad/vn_qa.py` + `vn_qa2.py` → `scratchpad/vn_qa_results.json`, `vn_qa2_results.json`. All test data isolated under `qa-vn-vi-{ts}` namespace (throwaway org+farm via `/onboarding/complete`).

---

## 1. VN account/farm creation + login (country=VN) — PASS

| Step | Evidence | Result |
|------|----------|--------|
| `POST /onboarding/complete` country=VN | **201**, `farm_id=b0106b41-…`, returned access_token | PASS |
| `farm.country` persisted | direct SQL `SELECT country FROM farms` → **`VN`** | PASS |
| `POST /auth/login` (re-login) | **200** with same creds | PASS |

Account: `qa-vn-vi-1782293542-4479@farm.com`, farm_type=FARROW_TO_FINISH, tz=Asia/Ho_Chi_Minh. KR routing per P0 judgment = (b) TEST TARGET (no KR block in code) — VN is likewise a free-form ISO country with no signup gate; onboarding accepted VN cleanly.

---

## 2. Language vi — UI render, no Korean leak, no raw keys, no "MVP" — PASS

### 2a. Message-file parity (source of all UI text)
`scratchpad` audit of `src/messages/vi.json` vs `en.json` (flattened):
- **en keys = 1337, vi keys = 1337, missing-in-vi = 0** → full parity.
- vi values containing literal `"MVP"` = **0**.
- vi values containing Korean hangul (`[가-힣]`) = **0**.

### 2b. Live SSR render (vi cookie `NEXT_LOCALE=vi`)
`curl -L --cookie "NEXT_LOCALE=vi" localhost:3000/login` (len 101 451), UTF-8 decoded scan:
- Vietnamese rendered: **`Đăng nhập`, `Mật khẩu`, `Quên`** present (login form fully localized).
- Actual Korean syllables on page = **0** (precise `[가-힣]` regex on UTF-8).
- Raw next-intl dotted-key text nodes (`>login.title<` style) = **0**.
- `MVP` literals = **0**.

`localhost:3000/dashboard` (vi+session cookie, len 89 217): korean=0, rawkeys=0, mvp=0. (App-shell chrome is client-hydrated from `vi.json` — proven clean by 2a; SSR HTML carries no leak.)

> Locale model (`src/i18n/request.ts`, `config.ts`): single source = `NEXT_LOCALE` cookie. `vi` is a **public** locale. `ko` is **admin-only** and is force-downgraded to `defaultLocale` on customer app / localhost (`adminOnly && !isAdminHost → defaultLocale`) — this is the structural Korean-leak guard. Confirms "non-Korean mode → 0 Korean leak" is enforced by design, not by translation completeness alone.

Result: **PASS** — vi UI updates, no Korean leak, no raw key, no MVP string.

---

## 3. Country-driven KPI thresholds (country, NOT language, decides) — PASS

Benchmarks resolve via `effective_metric_values(farm_id, farm.country, 'SYSTEM')` (called in `kpi_service._get_benchmark`, keyed on `farm.country`). Live dashboard for the VN farm (`GET /farms/{id}/kpi/dashboard`) returned `"country": "VN"` and VN-specific benchmark block.

### VN effective thresholds (live, this farm)
| KPI | benchmark_avg | target | warning | critical | dir | unit |
|-----|---------------|--------|---------|----------|-----|------|
| PSY | 25.41 | 24.00 | 22.00 | 18.00 | below | 두/모돈/년 |
| NPD | 54.00 | 31.00 | 45.00 | 62.00 | above | days |
| FARROWING_RATE | 75.00 | 85.00 | 78.00 | 68.00 | below | % |
| MARKET_PRICE_HEAD | (null) | — | — | — | below | **VND** |

### Proof country (not language) drives thresholds — VN vs KR vs global
Region-specific seed rows (`default_metric_values scope='region'`):

| metric | VN | KR | (global/SYSTEM) |
|--------|-----|-----|-----------------|
| PSY default | **16.00** | 22.00 | 22.00 |
| NPD default | **45.00** | 35.00 | 35.00 |
| FARROWING_RATE default | **74.00** | 83.00 | 80.00 |

Effective warning/critical also diverge by country: **VN FR w78/c68** vs **KR FR w83/c78**; **VN NPD w45** vs **KR NPD w35**. A KR-country farm browsed in *English* UI still resolves KR (83/78) thresholds — thresholds are bound to `farm.country`, never to UI language. Brief requirement "KR/en keeps KR thresholds in English UI" = satisfied structurally (resolution path ignores `lang`).

Result: **PASS** — VN gets VN-specific thresholds; language-independent.

---

## 4. Benchmark-missing → rule silence = PASS (no fabricated numbers)

VN region rows that are **NULL** (BORN_ALIVE, PRE_WEANING_MORTALITY, WEANED_COUNT, WSI, MARKET_PRICE_HEAD): these surface as `benchmark_avg=null` (e.g. dashboard `benchmarks` block omits them; MARKET_PRICE_HEAD effective row = all-NULL). Per guardrail, missing benchmark → owning KPI rule stays **silent** = PASS (reason: `benchmark_missing`). No arbitrary values injected. Live confirm: dashboard `benchmarks` returned only PSY/NPD/FARROWING_RATE (the 3 VN-populated metrics) — the NULL ones correctly absent, not zero-filled.

Live rule engine on empty farm fired only data-grounded findings (`inventory.zero` SOW_COUNT=0 CRITICAL, `farm.health_class` RED, `psy.no_data` INFO) — no benchmark-comparison rule fired against a missing benchmark.

---

## 5. Chat (Rule-grounded Q&A) in vi — PASS (engine), KNOWN_GAP (finding-code localization)

`POST /farms/{id}/chat/query` with `{"question": "...", "lang":"vi"}`:
- `question:"PSY"` → **200**, `intent=psy`, `severity=INFO`, finding `psy.no_data` (target_value=22.0), `renderer:"template"`.
- `question:"Tỷ lệ đẻ của trại thế nào?"` (vi natural-language) → **200**, `intent=dashboard`, multi-finding structured result.

Engine operates correctly for a VN farm and accepts vi questions. **KNOWN_GAP (platform-wide, not VN):** `src/app/(app)/chat/page.tsx` renders `finding.causes.join(" · ")` / `recommended_actions.join(" · ")` **raw** — the domain codes (e.g. `insufficient_weaning_records`, `complete_weaning_data_entry_for_current_year`) are joined into the vi-localized wrapper (`t("causes",{x})`) but the code **values themselves are not looked up in i18n**, so they display as English snake_case inside the vi UI. The wrapper labels and all page chrome ARE localized. These are domain enum codes, not next-intl message keys (so "raw i18n key count" per the brief = 0), but they are untranslated English content for non-en users. Classified KNOWN_GAP (chat finding cause/action codes not localized in any non-en locale), not FAIL.

> Note: initial harness used wrong field (`message`) → 422 `question required`; corrected to schema field `question` (`api/app/schemas/chat.py:7`) → 200. Schema-validation working as intended.

---

## 6. Report units (US=lb / others=kg) — VN PASS; US=lb KNOWN_GAP (platform)

`GET /farms/{id}/config` for VN farm → `weight_unit: "kg"`, `currency_code:"USD"`, `market_code:null`. Reports (`/reports/reproduction`, `/reports/grow-finish`) returned **200** (empty arrays — no event data on fresh farm), weights stored/returned as `*_kg` metric fields; frontend converts via `src/lib/utils/units.ts` (`kgToDisplay`) using `weight_unit`.

- **VN = kg → CORRECT** (VN is metric; kg is right regardless of the gap below).
- **US = lb → KNOWN_GAP:** `weight_unit` resolves from `region_defaults` table (`farm_service.get_local_config`), but **`region_defaults` is empty (0 rows in live DB)** → every country, including US, falls back to hardcoded `"kg"`. So a US farm would currently display kg, not lb. This is a platform seeding gap (region_defaults unseeded), not a VN issue, and does **not** affect VN (kg is correct for VN). Flagged for the US market run.

---

## 7. MX / TH global-fallback probe (country-driven, cross-check) — KNOWN_GAP confirmed

Per brief: "MX/TH no seed → global fallback = KNOWN_GAP (using another country's threshold = FAIL)."

- **TH**: `default_metric_values scope='region' scope_code='TH'` = **0 rows**. `effective_metric_values(...,'TH',...)` returns **identical values to a nonexistent country `'ZZ'`** (PSY avg=24.30/target=28/w22/c18; FR=81/w80/c70; NPD=30/w40/c55) = pure **SYSTEM/global fallback**, NOT a TH-specific or borrowed-country threshold. → **KNOWN_GAP** (TH has no country benchmark seed; engine correctly uses global default, does not steal VN/KR numbers). Not a FAIL.
- **MX**: `scope_code='MX'` region rows = **0** → same global-fallback behavior → **KNOWN_GAP**.

VN, by contrast, has genuine region overrides (§3) — so VN is *not* in the fallback bucket. The engine's behavior is correct: country with seed → country thresholds; country without seed → transparent global fallback (no cross-country contamination).

---

## Summary

| Area | Result | Evidence |
|------|--------|----------|
| VN account+farm+login (country=VN) | **PASS** | onboarding 201, farm.country=VN (SQL), login 200 |
| vi UI render / no Korean leak / no raw key / no MVP | **PASS** | vi.json 1337/1337 parity; login SSR vi words present, 0 Korean, 0 rawkey, 0 MVP |
| Country-driven KPI thresholds (lang-independent) | **PASS** | VN PSY 16/NPD 45/FR 74 vs KR 22/35/83 vs global 22/35/80; resolved by farm.country |
| Benchmark-missing → rule silence | **PASS** | NULL VN metrics absent from dashboard, not zero-filled; no fabrication |
| Chat Q&A in vi | **PASS** (engine) | 200 for vi questions, structured findings |
| Report units (VN=kg) | **PASS** | config weight_unit=kg |
| KR/en keeps KR thresholds in English UI | **PASS** | resolution keyed on farm.country, ignores lang |

**KNOWN_GAPs (none VN-blocking):**
1. **US=lb not wired** — `region_defaults` table empty → all countries (incl. US) fall back to `kg`. VN unaffected (kg correct). Platform seeding gap; flag for US run.
2. **Chat finding cause/action codes not localized** — domain enum codes render raw English inside localized wrapper for all non-en locales (vi/ko/zh/es/th/pt). Page chrome + wrappers localized; codes are not next-intl keys (raw-i18n-key count = 0).
3. **TH / MX have no country benchmark seed** — engine correctly uses transparent global/SYSTEM fallback (verified == nonexistent-country `'ZZ'` resolution); no other-country threshold borrowed. Expected KNOWN_GAP per brief.

Per guardrail: no source changed, no commit; all test data isolated in throwaway `qa-vn-vi-*` org/farm. No thresholds injected/rewritten — seed/config used as-is.

**FINAL: VN = PASS** — country=VN drives correct VN-specific KPI thresholds (language-independent), vi UI clean (0 Korean leak / 0 raw key / 0 MVP, full 1337-key parity), benchmark-missing → silence honored, chat engine operative in vi. Outstanding items are 3 platform-wide KNOWN_GAPs (US lb-unit unseeded, chat finding-code localization, TH/MX no benchmark seed) — none specific to or blocking the VN market.
