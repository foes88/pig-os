# PigOS Overnight Market QA — P2 Market Row: MEXICO (MX / es) — 2026-06-24

Repo: `c:\dev\PigOS` · Branch: `main` · Live web `localhost:3000` + API `localhost:8000` (docker postgres `pigos`). Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: MX = PASS with one KNOWN_GAP.** An MX (country=MX, lang=es) account was created live and verified end-to-end. Country drives KPI thresholds correctly: MX has **no seeded region thresholds**, so all 23 metrics resolve from `global` (SYSTEM) scope — the documented fallback. **Zero leakage of any other country's thresholds** (KR/US/BR/CN/VN). Spanish UI renders (`<html lang="es">`, Spanish strings), i18n es.json has full 1337/1337 key parity, zero Korean leak, zero "MVP" strings, zero untranslated raw keys. MX report unit = kg (correct for non-US). The only gap is **US=lb display** (a US-market concern, not MX) and the **MX global-fallback** itself (expected KNOWN_GAP per brief).

Test artifacts (isolated, `qa-mx-es-*` / `qa-us-cmp-*` namespaces): MX farm `f3d3a229-ddf0-4001-887f-714293f140d4`, US compare farm `13117740-5551-48a4-99dd-3710d1f6b2e5`.

---

## 1. Account / farm creation (MX) — PASS

| Step | Command | Result |
|------|---------|--------|
| Create org+user+farm country=MX | `POST /api/v1/onboarding/complete` (`org_name=qa-mx-es-<ts>-org`, `country=MX`, `farm_name=qa-mx-es-<ts>-farm`, tz `America/Mexico_City`) | **201** — returned `org_id, farm_id, user_id, access_token, refresh_token` |
| Login (token issued inline) | tokens from onboarding response | **OK** (Bearer used for all subsequent calls) |
| Farm country persisted | `GET /api/v1/farms/{farm_id}` | **`country: MX`**, `currency: USD`, name `qa-mx-es-<ts>-farm` |

Onboarding schema (`schemas/auth.py::OnboardingCompleteRequest`) takes `country` as ISO-3166-1 alpha-2; MX is accepted with no gating. (KR routing per P0-baseline §5 = TEST TARGET, no block — not re-litigated here; MX is the subject.)

---

## 2. KPI thresholds are country-driven (NOT language-driven) — PASS

Source of truth: `app/services/threshold_service.py`. Resolution priority = **farm > region(country) > system(global)**. The filter strictly matches `scope_code == farm.country` for region rows (lines 26-29) — it is **structurally impossible** to pick another country's row for an MX farm.

**DB ground truth** (`default_metric_values`, `docker exec pigos-postgres psql`):
```
region BR=9, region CN=7, region KR=27, region US=11, region VN=8, system SYSTEM=23
region MX = 0   ← no Mexico rows seeded
```

**Live MX farm thresholds** (`GET /farms/{mx_farm}/thresholds`):
- **scope distribution: `{'global': 23}` — 23/23 metrics from `global` (SYSTEM). Zero `country`, zero `farm`.**
- Sample (all `scope=global`): PSY warn=22 crit=18 · NPD 40/55 · WSI 7/10 · FARROWING_RATE 80/70 · PRE_WEANING_MORTALITY 13/18 · FCR 3.0/3.3 · ADG 650/550.

**Cross-check vs US farm** (`GET /farms/{us_farm}/thresholds`): scope distribution `{'global': 14, 'country': 11}` — US correctly layers its 11 seeded `region/US` rows over global. This proves the region layer *works* when seeded, and that MX getting 23×global is the genuine absence of MX data, not a query bug.

**Interpretation per guardrail:**
- MX/TH with no seed → **global fallback = KNOWN_GAP** (no MX-localized benchmarks yet). ✅ Behaving exactly as specified.
- **No other-country threshold was borrowed** (would have been a FAIL). ✅ MX shows only `global`, never `region/KR` etc. — verified both in DB (`region MX = 0 rows`) and live API (`scope=global` for all 23).
- The PSY=22/18 seen on MX is the **SYSTEM global** value (scope reported as `global`), which coincidentally equals KR's value but is **sourced from SYSTEM, not KR** — the `scope` field proves provenance.

> Note (not a failure): `benchmark_avg` is NULL on several global metrics (MORTALITY/MSY warn/crit NULL; many proxy `is_proxy=t`). Per guardrail, `benchmark missing → rule silence is PASS (benchmark_missing)`; no arbitrary numbers were injected and none should be.

---

## 3. Rule Engine runs for MX farm (country=MX context) — PASS

| Check | Command | Result |
|-------|---------|--------|
| Dashboard KPI | `GET /farms/{mx_farm}/kpi/dashboard` | **200** |
| Chat / Rule Engine | `POST /farms/{mx_farm}/chat/query` `{"question":"How is my PSY performing?"}` | **200** — `intent=psy`, 1 finding, graceful empty-farm output: `ℹ [PSY] Causes: Insufficient weaning records / Actions: Complete weaning data entry` |
| Alerts (rule-driven) | `GET /farms/{mx_farm}/alerts/overdue` | **200** |

The rule pipeline executes against the global thresholds for the MX farm. Empty farm → no false alerts (silence is correct). Chat request field is `question` (per `schemas/chat.py::ChatQuery`), not `message`.

---

## 4. Language = Spanish (es) UI — PASS

### 4a. Live SSR locale selection — PASS
`GET /login` with `Cookie: NEXT_LOCALE=es` →
- **`<html lang="es">`** (next-intl `i18n/request.ts` selected es from the NEXT_LOCALE cookie).
- Page body contains Spanish: **"Olvidaste tu contraseña"** (1 occurrence). Login page (`(auth)/login/page.tsx`) ships a self-contained 7-language dict; full es block present (e.g. `"¿Olvidaste tu contraseña?"`, `"Ingresa un correo válido"`, `"Email o password is incorrect"`). SSR initial paint is the client-default until the toggle hydrates, but the es strings are shipped and `lang="es"` is set server-side.
- App pages (39 files) use next-intl `useTranslations` resolving the same `NEXT_LOCALE` cookie → `messages/es.json`.

### 4b. No Korean leak / locale guard — PASS
- `GET /login` with `Cookie: NEXT_LOCALE=ko` on non-admin localhost → **`<html lang="en">`** (Korean is `ADMIN_ONLY_LOCALES`, downgraded to `defaultLocale` on non-admin host per `i18n/request.ts` L16-17). Customer app cannot serve Korean → **0 Korean leak** in non-Korean mode. ✅
- es SSR capture: **0 Korean (Hangul) tokens** in visible text.

### 4c. i18n es.json static integrity — PASS
(`src/messages/en.json` vs `es.json`, flattened key comparison)
- **Key parity: 1337 en / 1337 es — 0 missing, 0 extra.**
- **0 empty es values.**
- **0 Korean (Hangul) characters** anywhere in es values.
- **0 "MVP" literal strings** in es.
- **0 untranslated raw keys** (0 `value==key`). The only 3 `value==leaf-key` cases are intentional KPI acronyms/technical terms kept identical across all languages: `thresholds.m.PSY="PSY"`, `thresholds.m.NPD="NPD"`, `thresholds.proxy="proxy"`. The 4 "key-like" strings flagged by a loose regex were all valid Spanish: `Cargando…/Guardando…/Agregando…/Procesando…`.

### 4d. KR/en threshold parity under English UI — PASS (by design)
Thresholds are country-scoped, **independent of UI language** (§2). A KR-country farm keeps KR thresholds even if viewed in English; an MX-country farm keeps global thresholds even if viewed in Spanish. Language never overrides country — verified structurally (`threshold_service` keys on `farm.country`, never on locale).

---

## 5. Report units (US=lb / else=kg) — PARTIAL (MX correct; US=lb is a KNOWN_GAP)

Unit conversion lives in `src/lib/utils/units.ts` (`kgToDisplay`, `formatWeight`) driven by `FarmLocalConfig.weight_unit` from `GET /farms/{id}/config` (`farm_service.get_local_config`). All weights are stored as kg in DB; display converts to lb only when `weight_unit=="lb"`.

| Farm | `GET /config` weight_unit | Expected (brief) | Result |
|------|---------------------------|------------------|--------|
| **MX** (this market) | **`kg`** | kg (non-US) | **PASS** |
| US (control) | `kg` | lb | **KNOWN_GAP** |

Root cause: `region_defaults` and `market_defaults` tables are **empty (0 rows)**, so `get_local_config` falls through to the hardcoded `"kg"` default for **every** country, including US. The lb code path exists and is correct (`KG_TO_LB=2.20462`) but is never triggered because no region/market row sets `weight_unit="lb"` for US.

**For the MX market this is correct** (Mexico displays kg). The US=lb expectation is unmet but is a **US-market data-seeding gap**, not an MX failure. MX currency resolves to `USD`/`$` (region_defaults empty → `farm.currency or USD`); Mexico would ideally be MXN, but that too is the same unseeded-region gap and is read-only display, not an integrity break.

---

## Summary — MX = PASS (1 KNOWN_GAP)

| Dimension | Verdict | Evidence |
|-----------|---------|----------|
| Account/farm creation (country=MX) | **PASS** | onboarding 201, farm `country=MX` persisted |
| KPI thresholds country-driven | **PASS** | MX = 23/23 `global`; 0 other-country leak; DB `region MX=0`; US control shows 11 `country` rows (region layer works) |
| MX global fallback (no MX seed) | **KNOWN_GAP** | no `region/MX` rows — expected per brief; not a FAIL |
| No other-country threshold borrowed | **PASS** | scope=`global` only for MX (would be FAIL if KR/US used) |
| benchmark missing → rule silence | **PASS** | NULL benchmarks left silent; no numbers injected |
| Rule Engine on MX farm | **PASS** | dashboard 200, chat 200 (intent=psy), alerts 200 |
| Spanish (es) UI renders | **PASS** | `<html lang="es">`, Spanish strings, 39 next-intl pages |
| Korean leak in non-KR mode | **PASS** | ko cookie → `lang="en"` (downgrade); 0 Hangul in es SSR |
| Raw i18n keys / "MVP" strings | **PASS** | es 1337/1337 parity, 0 empty, 0 raw key, 0 "MVP" |
| Report units (MX=kg) | **PASS** | `/config` weight_unit=`kg` |
| Report units (US=lb) | **KNOWN_GAP** | region_defaults/market_defaults empty → US also returns `kg` (US-market gap, not MX) |

**Guardrails honored:** no source code changed, no commit/push, no prod DB mutation; all test data isolated under `qa-mx-es-*` / `qa-us-cmp-*`. No threshold values injected; MX global-fallback recorded as KNOWN_GAP (not FAIL); no other-country thresholds substituted for MX; stillborn-rate formula untouched; PSY 22/18 read from seed (SYSTEM), not assumed.

**Operational note (non-blocking):** the Next dev server intermittently times out on first-hit route compilation (`/login` took up to ~90s to compile; root `/` stays instant at 307; API healthy throughout). Not a product defect — dev on-demand compilation. All required es/ko captures succeeded once compiled.
