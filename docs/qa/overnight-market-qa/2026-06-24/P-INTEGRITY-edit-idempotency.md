# P-INTEGRITY — [edit-idempotency] (2026-06-24)

> Dimension: 데이터 정합성 스트레스 (사용자 #1 우선순위 "무조건 정합성, 꼬이면 안됨").
> Target: live API `localhost:8000` + docker postgres `pigos`. Namespace `qa-integ-edit-idempotency-*` (격리: 매 케이스 신규 온보딩 농장).
> Method: 해피패스 1회 금지 — 반복/랜덤/재제출(double-submit, double-delete, 15회 랜덤 PATCH churn)로 검증. 발견 시 {증상, 재현, 원천 vs 집계, 분류} 기록.
> Harness: `scratchpad/integ_edit_idempotency.py` (httpx, 실 HTTP, 실 커밋). 서버 traceback은 throwaway uvicorn(:8011, 종료완료)로 캡처.

## 결과 요약

**꼬임 2건 발견.** 심각도: 1 HIGH(crash/availability+정합성), 1 MEDIUM(stale KPI).

| # | 분류 | 심각도 | 증상 |
|---|------|--------|------|
| INTEG-1 | INTEGRITY_BUG (crash + 상태정지) | **HIGH** | ear_tag ≥ 16자 모돈의 **전량이유(full weaning)**가 500 에러로 트랜잭션 전체 실패 |
| INTEG-2 | INTEGRITY_BUG (stale aggregate) | **MEDIUM** | 교배/분만 **삭제 후에도 대시보드 `farrowing_rate`(분만율)가 soft-deleted 행을 계속 집계** |

정합성이 **정상 동작한** 차원(증거 기반 PASS): weaning 값수정→PSY 즉시 재계산, farrowing 값수정→total_born 재계산, mating/farrowing 더블서밋 중복차단, weaning 삭제→PSY 차감+상태롤백, 더블삭제 비재적용(404), 15회 랜덤 PATCH churn 무드리프트, 동일값 더블PATCH 멱등.

---

## INTEG-1 — 전량이유(full weaning)가 긴 ear_tag에서 500 크래시 [HIGH]

### 증상
모돈의 `ear_tag` 길이가 **16자 이상**이면 마지막(전량)이유 등록이 HTTP **500 Internal Server Error**로 실패한다. 이유 트랜잭션 전체가 롤백되어 **모돈이 LACTATING(포유)에 영구히 묶이고**, 해당 산차의 weaning/PSY가 영원히 기록되지 않는다. 부분이유나 짧은 ear_tag(≤15자)는 정상.

### 근본 원인
`api/app/services/event_service.py` `record_weaning()` L510-520 — 전량이유 시 자돈그룹(PigletGroup) 자동 생성:
```python
code = f"WG-{req.weaning_date:%y%m%d}-{sow.ear_tag}-{str(weaning.id)[:4]}"
```
생성 길이 = `WG-`(3) + yymmdd(6) + `-`(1) + len(ear_tag) + `-`(1) + 4 = **15 + len(ear_tag)**.
`piglet_groups.group_code`는 `VARCHAR(30)` (`db/models/sow.py:154`, 라이브 DB `character_maximum_length=30` 확인). 따라서 **len(ear_tag) ≥ 16 → group_code ≥ 31자 → asyncpg `StringDataRightTruncationError`**.
한편 `sows.ear_tag`는 입력상 최대 30자(`SowCreate.ear_tag: max_length=30`)까지 허용 → **정상 입력으로 도달 가능한 결함**.

서버 traceback (instrumented uvicorn 캡처):
```
sqlalchemy.exc.DBAPIError: asyncpg.exceptions.StringDataRightTruncationError:
  value too long for type character varying(30)
[SQL: INSERT INTO piglet_groups (... group_code ...) VALUES (...)]
  at event_service.py line 523 (record_weaning -> db.commit())
```

### 재현 (결정론적 임계값)
신규 농장 온보딩 → 모돈 등록(ear_tag만 변경) → 교배 → 분만(born_alive=12) → 전량이유(weaned_count=12):

| ear_tag 길이 | 예상 group_code 길이 | weaning HTTP |
|---|---|---|
| 2 (`S1`) | 17 | **201** |
| 7 (`sow-001`) | 22 | **201** |
| 15 (`ABCDEFGHIJKLMNO`) | 30 | **201** |
| 16 (`ABCDEFGHIJKLMNOP`) | 31 | **500** |
| 21 (`KR-FARM-SOW-0001-2025`) | 36 | **500** |

경계: **len(ear_tag) ≤ 15 = OK, ≥ 16 = 500.** (`KR-FARM-SOW-0001-2025` 같은 현실적 귀표가 실패)

### 영향
- availability: 핵심 해피패스(전량이유) 무작동.
- 정합성: 이유 실패 → 모돈 LACTATING 고착 → 후속 교배(LACTATING은 교배 불가 상태) 차단 → 사이클 데드락. weaning 미기록 → PSY/MSY 영구 누락.

### 분류: INTEGRITY_BUG (HIGH) — 수정 보류(가드레일: 로컬 자동수정 금지). 기록만.
> 참고 수정 방향(미적용): group_code 생성 시 ear_tag 잘라쓰기 또는 weaning id 해시 기반 고정폭 코드로 30자 보장. **사양 변경이므로 사람 확인 필요.**

---

## INTEG-2 — 삭제 후 대시보드 farrowing_rate가 soft-deleted 행을 계속 집계 [MEDIUM]

### 증상
교배/분만을 삭제(soft-delete)해도 대시보드 KPI `farrowing_rate`(연중 분만율)가 삭제 전 값 그대로 유지된다 → **stale aggregate**.

### 근본 원인
`api/app/services/kpi_service.py` `get_dashboard()` L603-614 — YTD 분만율 분자/분모가 `deleted_at IS NULL` 필터 누락:
```python
mating_count = ... Mating.farm_id==farm.id, Mating.mating_date >= Jan1   # deleted_at 필터 없음
farrowing_count = ... Farrowing.farm_id==farm.id, Farrowing.farrowing_date >= Jan1  # deleted_at 필터 없음
farrowing_rate = farrowing_count / mating_count * 100
```
바로 아래 `week_matings/week_farrowings/week_weanings`(L620-640)는 `deleted_at.is_(None)`을 올바로 건다 → 동일 함수 내 불일치. (대조적으로 PSY/NPD 뷰 `v_farm_psy`/`v_sow_npd`와 herd KPI(`build_herd_kpis`)는 `deleted_at IS NULL` 정상 — 라이브 뷰 정의로 확인.)

### 재현 (DB 직접 교차검증)
신규 농장에 현재연도(2026) 교배3 + 분만3 생성 → `farrowing_rate` 스냅샷 → 분만 1건 DELETE → 재조회. DB 원천 카운트와 대조:
```
DB: matings=3, farrowings_all=3 (live=2, deleted=1)
dashboard farrowing_rate = 1.0   (= 3/3, soft-deleted 1건 포함)
deleted_at-aware 정답      = 0.667 (= 2/3)
→ 대시보드가 stale-formula(f_all/m)와 일치, 정답(f_live/m)과 불일치 → 집계가 soft-delete 무시 확정
```
mating_count도 동일하게 deleted_at 미필터 → 교배 삭제 시에도 분모가 줄지 않음(같은 결함의 다른 갈래).

### 영향
정확도 한정(크래시 아님). 삭제 누적 시 분만율이 실제보다 높게 표시. period-lock 미적용 기간의 정정/삭제가 KPI에 반영 안 됨.

### 분류: INTEGRITY_BUG (MEDIUM) — 수정 보류. 기록만.
> 참고 수정 방향(미적용): L603-614 두 쿼리에 `Mating.deleted_at.is_(None)` / `Farrowing.deleted_at.is_(None)` 추가(아래 week_* 카운트와 동일 패턴).

---

## 정합성 PASS 항목 (증거)

| ID | 검증 | 증거 |
|----|------|------|
| A | weaning weaned_count 12→10 수정 → PSY total_weaned 즉시 재계산 | `total_weaned 12->10 (delta -2)` (stale 아님) |
| A2 | 이유 전 farrowing born_alive 14→10 수정 → total_born 재계산 | `ba 14->10, total_born 15->11` |
| B | 동일 mating(sow+date) 더블서밋 | `1st=201, 2nd=422 거부, ledger 1건(중복 없음)` |
| B2 | 동일 mating 대상 farrowing 더블서밋 | `1st=201, 2nd=409 거부, 분만 1건(중복 산자 없음)` |
| C | weaning 삭제 → PSY 차감 + 상태 롤백 | `total_weaned 22->10 (-12), sow status->LACTATING` |
| C2 | mating 더블삭제 비재적용 | `d1=204 d2=404, sow OPEN(1회만 롤백), live matings=0` |
| E | weaning weaned_count 15회 랜덤(0~14) PATCH churn | `원천이 항상 설정값 반영, drift 0건` |
| E2 | 동일값 farrowing 더블PATCH 멱등 | `p1=200 p2=200, ba/tb=9/9 안정` |

> 검증 시 발견된 부수 가드(정상 동작, 버그 아님): 이유미충족 부분weaning 422(`weaned must equal nursing_head`); 이미 이유된 복의 born_alive 하향 시 422(`born_alive too low: already weaned N exceeds effective litter`); 분만 보유 mating 삭제 409; weaning 보유 farrowing 삭제 409 — 모두 두수 꼬임 방지 가드로 의도된 동작.

---

## 환경/증거 메타
- API health: `{"status":"ok","version":"0.1.0"}` (8000, 테스트 전후 정상).
- group_code 컬럼: 라이브 `information_schema.columns` → `character_maximum_length=30`.
- 뷰 soft-delete: `pg_get_viewdef('v_farm_psy'|'v_sow_npd')` → 모두 `deleted_at IS NULL` 포함(PSY/NPD 재계산 정상).
- 격리: 케이스별 신규 온보딩 농장(qa-integ-edit-idempotency-* / qa-*@farm.com), 운영 데이터 미접촉.
- 가드레일 준수: 코드 수정/커밋/배포 없음. throwaway uvicorn(:8011) 종료 완료. 발견은 기록만.

## 최종
**꼬임 발견: 2건** — INTEG-1 full-weaning 500 crash(HIGH, ear_tag≥16자), INTEG-2 farrowing_rate stale-on-delete(MEDIUM). 둘 다 결정론적 재현 확보. 수정은 사양 영향(가드레일)으로 보류, 기록만.
