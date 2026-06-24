# P-INTEGRITY — Aggregate Truth (Data Integrity Stress)

Date: 2026-06-24 · Dimension: `aggregate-truth` (user #1 priority — "무조건 정합성, 꼬이면 안됨")
Target: live API `localhost:8000` + docker postgres `pigos`. Namespace: `qa-integ-aggregate-truth-*` (isolated test farms).
Method: inject source events via REST → recompute the same aggregate from source SQL (`deleted_at IS NULL`) → assert drift. Repeated / randomized / re-submitted (no single happy-path pass). Evidence-first.

Result codes: PASS / FAIL / INTEGRITY_BUG / SECURITY_BUG / INFO / KNOWN_GAP.

---

## VERDICT

**3 integrity issues found** (0 SECURITY). None is a *silent KPI-drift on the primary breeding-cycle aggregates* — those held drift=0 across 34 randomized mutations. Severity:

| # | Class | Severity | Self-corrects? | One-line |
|---|-------|----------|----------------|----------|
| BUG-1 | INTEGRITY_BUG (availability) | **HIGH** | n/a (atomic rollback) | Weaning POST returns **HTTP 500** whenever `ear_tag` length ≥ 16 — auto-generated `piglet_groups.group_code` overflows `VARCHAR(30)`. Weaning becomes impossible for those sows. |
| BUG-2 | INTEGRITY_BUG (KPI drift) | **MEDIUM** | **NO** | Dashboard `farrowing_rate` counts matings/farrowings **without** `deleted_at IS NULL` — soft-deleted events still inflate/deflate the rate. Drift vs source-of-truth does **not** self-correct after delete. Reproduced: 0.667 dashboard vs 1.0 truth (Δ 0.333). |
| BUG-3 | INTEGRITY_BUG (phantom inventory) | **LOW-MED** | **NO** | Deleting a weaning soft-deletes the weaning + rolls back sow status, but leaves the auto-created `WG-*` `piglet_groups` row active. `/piglets` list shows a phantom weaned group (head_count_in) with no backing weaning. Does NOT affect KPI/MSY rollups (those read `finisher_groups`). |

Per guardrails: **recorded only, not fixed** (working tree untouched; no commits).

---

## What PASSED (the core invariant holds)

| Check | Evidence | Result |
|-------|----------|--------|
| Dashboard `active_sows` = SQL status count | api=12 sql=12 | PASS |
| Dashboard `lactating` / `gestating(PREGNANT)` / `weaned(OPEN+ACC)` = SQL | api/sql identical (0/0/12) | PASS |
| Reproduction report `total_born_sum` / `born_alive_sum` = SQL (`deleted_at IS NULL`) | **34 randomized create+delete mutations, max\|drift\|=0** | PASS |
| Dashboard idempotent on repeated reads | 5× fetch → distinct=1 | PASS |
| Soft-delete is soft, not hard | weaning/farrowing/mating `deleted_at` set, rows retained | PASS |
| Aggregate self-corrects after delete (weaned_sum, ba_sum) | weaned 141→132 (Δ exactly =9), ba 141→132 (Δ exactly =9), drift=0 | PASS |
| No dangling children after farrowing delete | active weanings pointing at deleted farrowing = 0 | PASS |
| No dangling farrowing after mating delete | 34-round fuzz: farrowings whose mating soft-deleted = **0** | PASS |
| Referential guard: farrowing-delete blocked while weaning exists | HTTP 409 | PASS |
| Referential guard: mating-delete blocked while farrowing exists | HTTP 409 (code path verified `delete_mating` L855-857) | PASS |
| Status rollback chain on cascade delete | OPEN→LACTATING→PREGNANT→OPEN (exact) | PASS |
| Weight unit round-trip — no hidden kg↔lb conversion | in=1.55kg, stored=1.55, api=1.55 | PASS |
| Re-submit identical mating (idempotency) | 2nd → HTTP 422, active matings stays 1 (no silent dup) | PASS |
| TZ drift on event windows | mating/farrowing/weaning dates are `DATE` (no TZ) → window-immune | PASS |

---

## BUG-1 — Weaning HTTP 500 on long ear_tag (group_code VARCHAR(30) overflow)

- **Class**: INTEGRITY_BUG (correctness/availability). The weaning event — the PSY→MSY chain link — is unrecordable.
- **Symptom**: `POST /farms/{id}/events/weanings` → `500 Internal Server Error` for any sow whose `ear_tag` is ≥ 16 chars.
- **Root cause**: `api/app/services/event_service.py:511`
  ```python
  code = f"WG-{req.weaning_date:%y%m%d}-{sow.ear_tag}-{str(weaning.id)[:4]}"
  ```
  `group_code` length = `3 + 6 + 1 + len(ear_tag) + 1 + 4 = 15 + len(ear_tag)`. Column `piglet_groups.group_code` is `VARCHAR(30)`. Overflow when `len(ear_tag) > 15`. `SowCreate.ear_tag` allows up to **30** chars → reachable in normal use.
- **DB exception** (captured in-process):
  `asyncpg.exceptions.StringDataRightTruncationError: value too long for type character varying(30)` on the `INSERT INTO piglet_groups (... group_code ...) VALUES ('WG-260618-QI-1782289837-6337-S000-4a4b' ...)` (38 chars).
- **Reproduction**:
  1. Create sow with `ear_tag` of 16+ chars (e.g. `QI-1782289837-6337-S000`).
  2. Record mating + farrowing (succeed).
  3. Record weaning → **500**.
- **Threshold table**: ear_tag len 15 → group_code 30 (ok); 16 → 31 (**500**); 30 → 45 (**500**).
- **Integrity note (good news)**: the failing INSERT is inside the same flush/commit as the weaning + status transition, so the txn **rolls back atomically** — verified: 0 weanings, 0 piglet_groups, sow stays `LACTATING`. No partial/dangling state. So this is an availability/correctness bug, **not** corruption.
- **Suggested fix direction (NOT applied)**: truncate/hash `sow.ear_tag` inside the code (or widen the column) so `group_code` ≤ 30. The `[:4]` weaning-id suffix already guards uniqueness.

## BUG-2 — Dashboard farrowing_rate ignores soft-delete (KPI drift, no self-correction)

- **Class**: INTEGRITY_BUG — violates the mission invariant "KPI 롤업 = 원천 이벤트 재계산값(드리프트0)".
- **Root cause**: `api/app/services/kpi_service.py:603-614` — `mating_count` / `farrowing_count` for the YTD `farrowing_rate` filter only on `farm_id` + date `>= Jan 1`, **missing** `deleted_at IS NULL`. Every other aggregate (weekly counts L624/631/638, reproduction report, trend) correctly excludes soft-deleted rows. Asymmetric.
- **Reproduced** (`fr_bug.py`, fresh farm, current year): 3 sows mated, 2 farrowed, 1 mated-only.
  - BEFORE delete: dashboard_fr=**0.6667**, source-of-truth=0.6667 — agree.
  - Soft-delete the mated-only mating (`DELETE matings/{id}` → 204).
  - AFTER delete: dashboard_fr=**0.6667** (unchanged), source-of-truth=**1.0** (2 farrowings / 2 active matings).
  - **Drift = 0.3333 (33 pp), permanent.**
- **Impact**: any soft-delete (or PATCH that changes farrowing/mating) in the current year leaves dashboard FR stale vs reality. Note dashboard FR also disagrees with the `/reports/reproduction` FR (which is deleted-aware) — two surfaces, two numbers.
- **Suggested fix direction (NOT applied)**: add `Mating.deleted_at.is_(None)` / `Farrowing.deleted_at.is_(None)` to both counts.

## BUG-3 — Orphaned auto piglet_group after weaning delete (phantom inventory)

- **Class**: INTEGRITY_BUG (phantom inventory; low blast radius).
- **Root cause**: `record_weaning` auto-creates a `piglet_groups` row `WG-{date}-{ear_tag}-{id4}` (event_service.py:510-520). `delete_weaning` (L966-981) soft-deletes the weaning + rolls back sow status + reopens cycle, but **never** soft-deletes / decrements that auto-created group.
- **Reproduced**: after soft-deleting 1 of 12 weanings, `GET /farms/{id}/piglets` still returns **12** active `WG-*` groups; SQL `piglet_groups deleted_at IS NULL & WG-%` = 12; phantom `head_count_in` with no backing live weaning = **9**.
- **Impact bound** (verified): no KPI uses `piglet_groups` — MSY/grow-finish/FCR read `finisher_groups` (kpi_service.py:245-252). So **no dashboard/report KPI drift**. The leak is confined to the piglet-inventory list endpoint (phantom head count).
- **Suggested fix direction (NOT applied)**: in `delete_weaning`, soft-delete the matching auto `WG-*` group (or reconcile head_count) — mirror the create at L510-520.

---

## Guardrails honored

- **No fixes / no commits** — working tree unchanged (temp repro file `_qa_repro_wean.py` created then removed; verified `git status` clean of source edits).
- **Stillborn formula** `(sb+mum)/tb` (report_service.py:146 `birth_loss_rate`) — recognized as PigOS spec, **not** flagged.
- **benchmark/threshold** — not injected; no benchmark-missing KPI flagged as fail.
- Test data isolated under `qa-integ-aggregate-truth-*` farms; no prod/operational mutation; no AWS/paid-API/.env changes.

## Harness (scratchpad, reproducible)

`integ.py` (setup+inject) · `verify.py` (agg-truth + cascade soft-delete) · `stress.py` (unit/idempotency) · `fuzz.py` (34-round randomized drift) · `fr_bug.py` (BUG-2 proof). DB recompute via `docker exec pigos-postgres psql -U pigos -d pigos`.
