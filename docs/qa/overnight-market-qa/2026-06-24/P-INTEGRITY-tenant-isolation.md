# P-INTEGRITY [tenant-isolation] — Overnight Market QA (2026-06-24)

Dimension: **데이터 정합성 스트레스 (tenant-isolation)** — user #1 priority ("무조건 정합성, 꼬이면 안됨").
Target: live API `localhost:8000`, docker postgres `pigos`. Namespace isolation: `qa-integ-tenant-isolation-*`.
Method: two+ independent tenants (org+user+farm via `POST /onboarding/complete`), **no happy-path-once** — every probe looped/randomized/re-submitted. Evidence = HTTP status + DB rows + assertions.

Harness: `scratchpad/integ_test.py` (cross-tenant access), `integ_test2.py` (within-farm conservation/mirror, 20 randomized fosters), `integ_test3.py` (adversarial edge cases), `integ_test4.py` (RTS cycle attribution). DB audit via psql.

---

## VERDICT

**꼬임 발견: 1건. 심각도: MEDIUM (latent, 현재 무해).** No CRITICAL/HIGH tenant-isolation breach.
API-level cross-tenant access control is solid (403/404 everywhere). Within-farm piglet/mirror conservation is exact. The one finding is a stored cross-tenant FK pointer that is written but never read.

| # | Test | Result | Evidence |
|---|------|--------|----------|
| 1 | Cross-tenant sow read (A→B) | **PASS** | `GET /farms/B/sows/{B.sow}` A-token → **403** (×5); `GET /farms/A/sows/{B.sow}` → **404** (×5) |
| 2 | Cross-tenant write (A mutate/delete B's sow) | **PASS** | PATCH → **403** (×3); DELETE → **403** (×3) |
| 3 | Cross-tenant event injection (A→B farm) | **PASS** | `POST /farms/B/events/matings` A-token → **403** (×3) |
| 4 | Cross-FARM cross-foster (A.sow → B.sow target) | **PASS** | **422** "target_sow_id is not a valid active sow in this farm" (×3) |
| 5 | Within-farm nursing conservation (zero-sum foster) | **PASS** | 6 sows × ba=12 = **72**; after **20 randomized** fosters → still **72** |
| 6 | Mirror symmetry (FOSTER_OUT ↔ FOSTER_IN) | **PASS** | out: 20 recs / Σ46  ==  in: 20 recs / Σ46 |
| 7 | No negative nursing count | **PASS** | all sow nursing ≥ 0 after random stress |
| 8 | Sow-filtered event ownership | **PASS** | `?sow_id=X` returns only sow_id==X |
| 9 | Re-read determinism | **PASS** | nursing total identical on re-read |
| 10 | A reads B's sow-history via A's farm path | **PASS** | `GET /farms/A/reports/sows/{B.sow}/history` → **200 rows=0** (×3); cross-farm cycles filtered, no leak in output |
| 11 | Cross-tenant report pull (A→B reproduction) | **PASS** | `GET /farms/B/reports/reproduction` A-token → **403** |
| 12 | List isolation (A list ⟂ B list) | **PASS** | no sow-id overlap; A sees only A's, B only B's |
| 13 | RTS multi-cycle parity attribution | **PASS** | farrowing(ba=11) bound to exactly 1 cycle; no cross-cycle smearing; both pre-farrow cycles correctly parity=1 |
| 14 | **target_farrowing_id cross-tenant injection** | **FAIL (MEDIUM)** | A's piglet_event accepted (**201**) with `target_farrowing_id` = B's farrowing; stored cross-tenant FK |

---

## FINDING #1 — cross-tenant `target_farrowing_id` accepted unvalidated  [MEDIUM · INTEGRITY_BUG · latent]

**증상**: `POST /farms/{A}/events/piglet_events` accepts a body whose `target_farrowing_id` points at a farrowing owned by a **different tenant (Farm B)**. The event is created (HTTP 201) and the cross-tenant pointer is persisted in Farm A's `piglet_events` row.

**재현 절차 (시드)**:
1. Onboard tenant A and tenant B (independent orgs/farms).
2. In each farm, create a sow, mate, farrow → lactating. Capture B's `farrowing_id` (`B1_farrow`).
3. In farm A, create 2 lactating sows A1, A2.
4. A posts: `POST /farms/{A}/events/piglet_events` with
   `{sow_id: A1, event_type: "FOSTER_OUT", piglet_count: 2, target_sow_id: A2, target_farrowing_id: B1_farrow}`
5. Response **201**. (Repeated ×3, all 201.)

**원천 vs 집계 차이**:
- 원천(stored row): cross-tenant pointer IS written. DB proof:
  ```
  SELECT pe.farm_id AS pe_farm, f.farm_id AS tgt_farm, (pe.farm_id=f.farm_id) AS same_farm
  FROM piglet_events pe JOIN farrowings f ON f.id=pe.target_farrowing_id
  WHERE pe.id='8552851f-...';
  -- pe_farm=d7991d9b(A)  tgt_farm=4461fa6b(B)  same_farm = f   ← FALSE
  ```
- 집계/읽기: **no impact today.** `target_farrowing_id` is **write-only** in the codebase — grep shows it is set in `event_service.py` L746/L773 and never read by any query, aggregation, response schema, or KPI path. No B data appears in A's reads; B's farm gains **0** phantom events (auto-mirror uses `target_sow_id`'s own farrowing, which is A2 in-farm, so the mirror stays in Farm A). DB-wide audit: only the 3 deliberately-injected rows exist; `target_sow_id` cross-tenant = **0**, own `farrowing_id` cross-tenant = **0**.

**근본 원인**: `api/app/services/event_service.py` `record_piglet_event` validates `target_sow_id` (must be active sow in `farm_id`, L706–710) but assigns `target_farrowing_id=req.target_farrowing_id` (L746) **without any farm-scope / ownership / existence check**.

**영향 / 왜 MEDIUM (not CRITICAL)**: Currently inert (no read path dereferences it; no leak; no aggregation corruption; conservation unaffected). Risk is **latent**: any future feature that joins on `target_farrowing_id` (e.g., "trace where fostered piglets went", a litter-flow report, or a mirror-repair job) would dereference a pointer across the tenant boundary and could surface or mutate another tenant's litter. It is a stored tenant-isolation violation waiting for a consumer.

**분류**: `INTEGRITY_BUG` (cross-tenant dangling FK). Severity MEDIUM.

**수정 보류 (guardrail)**: not fixed. Suggested fix for the owner (record-only): in `record_piglet_event`, if `req.target_farrowing_id` is provided, validate it belongs to a farrowing of `target_sow_id` within `farm_id` (else 422) — mirroring the existing `target_sow_id` guard. The auto-mirror block already computes the correct in-farm `target_farrowing` from `target_sow_id`, so the client-supplied value is arguably redundant and could simply be ignored/overwritten.

---

## What PASSED firmly (no 꼬임)

- **API access control**: cross-tenant read/write/delete/event-injection on sows, events, and reports all return **403** (own-membership path) or **404** (foreign id under own farm). `FarmDep` (`get_farm_context` → `can_access_farm`) gates every `/farms/{farm_id}/...` route; all queries additionally filter `farm_id == farm.id`. Defense in depth holds.
- **Cross-foster mirror / piglet conservation**: zero-sum across 20 randomized transfers (72→72); FOSTER_OUT total == FOSTER_IN total (record count and piglet sum); no negative nursing; auto-mirror counterpart created only within-farm via validated `target_sow_id`.
- **Cross-FARM fostering blocked**: `target_sow_id` must be an active sow in the same farm (422) — no piglet leak across tenants. DB confirms 0 cross-tenant `target_sow_id`.
- **Cycle/parity attribution**: RTS (return-to-estrus) opens a new breeding cycle; farrowing+weaning attach to the correct single cycle; no weaned>born smearing; pre-farrow cycles share parity=1 correctly (parity = completed farrowings).
- **Event ownership**: every `piglet_events.farrowing_id` matches its own farm (DB audit: 0 cross-tenant). Sow-filtered event lists never return another sow's rows.
- **Weaning conservation validator**: enforces `weaned == nursing_head - (deaths + out - in)` (422 on mismatch) — observed live, correct.

---

## Notes / SKIP

- **Concurrency (true parallel double-submit)** not exercised under real DB-level race; sequential re-submit (idempotency) and randomized ordering covered. Marking concurrent-write race as **SKIP_NOT_IMPLEMENTED** for this run (would need threaded client + row-lock inspection). No evidence of double-application in sequential stress (conservation exact).
- Test data is namespaced `qa-integ-tenant-isolation-*` / `qa-<run>-*` and left in `pigos` DB (isolated from product data by namespace; no cleanup per evidence-retention).

**최종**: 꼬임 1건 / MEDIUM / latent (`target_farrowing_id` cross-tenant FK, write-only, no active leak). 수정 보류, 기록 완료.
