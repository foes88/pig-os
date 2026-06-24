# PigOS Overnight Market QA — P5 Input-Validation Integrity (2026-06-24)

Repo: `c:\dev\PigOS` · Branch: `main` · Live API `localhost:8000` (docker postgres `pigos`). Evidence-first. Result codes: PASS / FAIL / SKIP_NOT_IMPLEMENTED / KNOWN_GAP / PARTIAL.

**Headline: 19 / 19 validation cases PASS.** Every invalid payload was hard-blocked (4xx) by the backend; valid control payload succeeded (201). Dual-layer (BE validator + FE Zod) confirmed.

Harness: `scratchpad/p5_validation.py` → results `scratchpad/p5_results.json`. Each case POSTs/PATCHes an INVALID payload to the live API on a throwaway `qa-p5-validation-*` farm (isolated org, created via `/onboarding/complete`) and asserts the HTTP status. Period-lock row inserted via direct SQL into `period_locks` (no HTTP endpoint creates locks — see §3).

---

## 1. Validation case matrix (live API, evidence = actual status + response body)

| # | Case | Endpoint | Sent (invalid) | Expected | Actual | Body | Result |
|---|------|----------|----------------|----------|--------|------|--------|
| C1 | Total Born > 35 | POST events/farrowings | BA=40 | 422 | **422** | `Total Born cannot exceed 35` | PASS |
| C1 | Stillborn > 25 | POST events/farrowings | SB=26 | 422 | **422** | `Stillborn cannot exceed 25` | PASS |
| C1 | Avg birth weight > 3.0 | POST events/farrowings | 3.5 kg | 422 | **422** | `Average birth weight cannot exceed 3.0 kg` | PASS |
| C1 | BA ≠ male+female | POST events/farrowings | BA=10, M=4,F=3 | 422 | **422** | `Born Alive (10) must equal Male + Female (4 + 3)` | PASS |
| C2 | Farrowing before mating | POST events/farrowings | farrow 2025-05-01 < mate 2025-06-01 | 422 | **422** | `Gestation period -31 days is outside 100~130 range` | PASS |
| C2 | Mating before sow entry_date | POST events/matings | 2024-12-01 < entry 2025-01-01 | 422 | **422** | `Mating date (2024-12-01) cannot be before the sow's entry date (2025-01-01)` | PASS |
| C3a | Farrowing on GILT w/o mating | POST events/farrowings | GILT, no mating | 4xx block | **404** | `No open mating found for this sow to record farrowing` | PASS¹ |
| C3b | Mating on PREGNANT sow | POST events/matings | status=PREGNANT | 422/409 | **422** | `Sow status is 'PREGNANT'. Mating is only allowed when status is one of GILT, OPEN, ACCIDENT` | PASS |
| C3c | Re-weaning a fully-weaned sow | POST events/weanings | already weaned | 409/422 | **409** | `Litter already fully weaned for farrowing …` | PASS¹ |
| C4 | Pregnancy-check on non-PREGNANT sow | POST events/pregnancy_checks | status=GILT | 422 | **422** | `Pregnancy check requires a PREGNANT sow (current: GILT)` | PASS |
| C5 | Cross-foster > 25 piglets | POST events/piglet_events | FOSTER_OUT 26 | 422 | **422** | `Cross-fostering cannot exceed 25 piglets per transfer` | PASS |
| C6 | Weaning weaned > litter (identity) | POST events/weanings | wean 20 vs litter 14 | 422 | **422** | `weaned_count (20) > remaining nursing (effective litter 14 - already weaned 0 = 14)` | PASS |
| C6 | Weaning before farrowing | POST events/weanings | wean 2025-09-01 < farrow 2025-09-27 | 422 | **422** | `Weaning date (2025-09-01) must be after the farrowing date (2025-09-27)` | PASS |
| C7 | Finisher entry weight > 50 kg | POST finishers | 80 kg | 422 | **422** | `Entry weight must be between 5.0 and 50.0 kg` | PASS |
| C7 | Finisher ship head > remaining | POST finishers/{id}/ship | out=500, rem=100 | 422 | **422** | `Shipped head count (500) exceeds remaining head count (100)` | PASS |
| C7 | Finisher exit weight > 200 kg | POST finishers/{id}/ship | 250 kg | 422 | **422** | `Exit weight exceeds maximum 200.0 kg` | PASS |
| C8 | Edit event in LOCKED month | PATCH events/matings/{id} | period 2025-06 locked | 423 | **423** | `Period 2025-06 is locked; unlock it before editing.` | PASS |
| C9 | Data-quality report operable | GET reports/data-quality | — | 200+list | **200** | `n_issues=1` | PASS |
| C10 | VALID farrowing (control) | POST events/farrowings | legal cycle | 201 | **201** | created row | PASS |

¹ **C3a / C3c — by-design status code, not 422, but still hard-blocking.** The service intentionally returns the *more specific* error first (`event_service.py` comment: "중복·미발견 검사 뒤 = 더 구체적 에러 우선"). For a GILT with no prior mating, "no mating found" (404) fires before `validate_transition`; for a fully-weaned sow, "litter already fully weaned" (409) fires before the transition guard. Both are correct hard blocks. The state-transition guard *itself* is independently proven by C3b (mating on PREGNANT → 422 via `validate_mating`/`ALLOWED_TRANSITIONS`).

All 8 categories required by the P5 brief are covered and blocking:
分만합계 불일치 (C1), 이유 식별식 불일치 (C6), 불가능한 날짜순 (C2/C6), 잘못된 상태전이 (C3b + C3a/C3c), 잠긴월 423 (C8), 양자 상한초과 (C5), 비육 두수/중량 범위 (C7), 임신감정 PREGNANT 아님 422 (C4).

---

## 2. BE validator ⇄ FE Zod dual-layer (cross-check)

Backend validators: `api/app/validators/` (pure functions raising `ValidationError`→422, wired in `event_service.py`). Frontend pre-validation: `src/lib/validation/eventSchemas.ts` (Zod), gated via `firstError(schema, data, tv)` **before** submit in `record/page.tsx` (lines 392, 505, 577 — farrowing/mating/weaning), plus `sows/page.tsx` and `finishers/page.tsx`.

| Rule | BE validator (authoritative) | FE Zod (UX pre-block) | Parity |
|------|------------------------------|------------------------|--------|
| Total Born ≤ 35 | `farrowing.py` MAX_TOTAL_BORN=35 | `farrowingSchema` `.max(35,"totalBornMax")` | MATCH |
| Stillborn ≤ 25 / Mummified ≤ 25 | `farrowing.py` MAX_*=25 | `.max(25,"stillbornMax"/"mummifiedMax")` | MATCH |
| Avg birth weight ≤ 3.0 | `farrowing.py` 3.0 | `.max(3.0,"birthWeightMax")` | MATCH |
| TB = BA+SB+MUM | `event_service` + derived | `.refine(total_born===ba+sb+mum)` | MATCH |
| Cross-foster ≤ 25 | `cross_fostering.py` 25 | `pigletEventSchema` `.max(30)` then FOSTER target req | **PARTIAL**² |
| Finisher entry 5–50 kg | `finisher.py` 5/50 | `finisherEntrySchema` `.min(5).max(50)` | MATCH |
| Finisher exit ≤ 200 kg | `finisher.py` 200 | `finisherShipSchema` `.max(200,"exitWeightMax")` | MATCH |
| Date not future | (BE: vs entry/event dates) | `dateNotFuture` refine | FE-only extra (harmless) |
| Mating eligible status | `mating.py` GILT/OPEN/ACCIDENT | `matingSchema` (date only — no status) | **BE-only**³ |
| Weaning identity | `weaning.py` + service | `weaningSchema` (no identity refine) | **BE-only**³ |

² FE `pigletEventSchema` caps piglet_count at 30, BE caps cross-foster at 25 — FE would let 26–30 through to the API where BE blocks (422). Server is authoritative, so **no integrity gap** (verified live in C5), only a minor FE/BE bound divergence (25 vs 30). KNOWN_GAP (cosmetic — server enforces).
³ FE intentionally does not replicate stateful checks (current sow status, persisted litter counts) it cannot know client-side; these are enforced server-side only (C3b, C6 prove it). This is the documented design ("최종 권위는 백엔드") — PASS, not a gap.

---

## 3. Notes / observations (not failures)

- **No HTTP endpoint creates period locks.** `period_locks` is read by `_ensure_period_unlocked` (423) but grep across `api/app/routers` finds no POST that writes a `PeriodLock` row. The month-close/lock action is **not exposed via API** → SKIP_NOT_IMPLEMENTED for the *lock-creation* UX. The 423 enforcement on edits **works** (C8, locked via direct SQL). KNOWN_GAP: no user-facing "close month" endpoint yet.
- **423 is enforced only on edit/delete (PATCH/DELETE), not create.** `_ensure_period_unlocked` is called in the Phase-12 edit/delete paths only; create paths do not check period locks. Consistent with "확정 데이터 수정 차단" (block *modification* of finalized data) — creating a brand-new record in a closed month is currently allowed. Flagging as a design observation, not a failure.
- **`PeriodLockedError` class is 409, but the live lock guard returns 423.** `core/exceptions.py` defines `PeriodLockedError.status_code = 409`, but the actual enforcement in `event_service._ensure_period_unlocked` raises `HTTPException(status_code=423,…)` directly (bypassing the exception class). The brief expects 423 and the live API returns 423 (C8 PASS). The unused 409 class is dead/divergent — minor cleanup candidate, no behavioral impact.
- **Schema-level (Pydantic) vs business-rule (validator) blocking both observed.** e.g. weaning `weaned_count` has a Pydantic bound `le=30`; within-bound but illogical values (20 > litter 14) are caught by the business validator (C6). Both surface as 422.

---

## Summary
- **19 / 19 P5 validation cases PASS** — all invalid inputs hard-blocked (422/409/404/423), valid control 201.
- All 8 brief-required categories covered and blocking (farrowing-sum, weaning-identity, date-order, state-transition, locked-month-423, foster-cap, finisher-range, pregnancy-check-422).
- Dual-layer confirmed: FE Zod pre-blocks via `firstError` before submit; BE validators are authoritative. One cosmetic FE/BE divergence (foster cap 30 vs 25) — server enforces, no integrity gap.
- KNOWN_GAPs (non-blocking): (a) no API to create period locks (close-month UX), (b) 423 enforced on edit not create, (c) dead `PeriodLockedError=409` class diverges from live 423. None compromise input-validation integrity.
- Per guardrail: no source changed, no commit; all test data isolated in throwaway `qa-p5-validation-*` farms.
