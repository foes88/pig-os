# PigOS Validation Specification
> 출처: PigPlan 소스코드 역분석 (DataValidationChk.java, MdChildbirthWr.jsp 등)
> 목표: 모돈 번식 사이클의 데이터 정합성 보장
> 최종 점검일: 2026-06-19

---

## 한 줄 요약

**P0 (지금 만들 것)** = 전입 → 교배 → 분만 → 양자/포유폐사 → 이유 → 도폐사  
이 사이클이 데이터 정합성의 전부다. 나머지는 나중에.

---

## 구현 현황 범례

| 기호 | 의미 |
|------|------|
| ✅ | 구현됨 |
| ⚠️ | 코드는 있지만 연결 안 됨 |
| ❌ | 없음 — 신규 구현 필요 |

---

## 1. 모돈 전입

**PigPlan 기준**: 귀표 필수 + 중복 불가, 전입일 오늘 이전, 산차 0~20

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 귀표 중복 체크 | ✅ `routers/sows.py` | ✅ 수동 |
| 전입일 미래 금지 | ✅ `routers/sows.py` | ❌ |
| 산차 0~20 | ✅ `schemas/sow.py` ge=0, le=20 | ❌ |
| entry_type enum | ✅ `schemas/sow.py` | ❌ |

**프론트 추가 필요**
```typescript
z.object({
  ear_tag: z.string().min(1),
  entry_date: z.string().refine(d => new Date(d) <= new Date()),
  parity: z.number().int().min(0).max(20),
  entry_type: z.enum(["GILT", "PURCHASE", "TRANSFER", "BORN"]),
})
```

---

## 2. 교배

**PigPlan 기준**: GILT/OPEN/ACCIDENT만 교배 가능, 웅돈 순서 강제, 동일 날짜 중복 불가, 사이클 최대 5회

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 상태 GILT/OPEN/ACCIDENT | ✅ `mating.py` | ❌ |
| 이유 이후 교배 | ✅ `event_service.py` | ❌ |
| 웅돈 순서 강제 (boar_2→boar_1) | ⚠️ 함수 있음, 인자 미전달 | ❌ |
| 사이클당 최대 5회 | ✅ `event_service.py` | ❌ |
| 동일 날짜 중복 방지 | ❌ | ❌ |
| 교배 시 웅돈 ACTIVE 상태 확인 | ❌ | ❌ |

**백엔드 수정 필요**
```python
# 1. 웅돈 인자 전달 (event_service.py)
validate_mating(sow_status=sow.status, boar_1=req.boar_id, boar_2=..., boar_3=...)

# 2. 중복 방지 쿼리 추가
dup = await db.scalar(select(Mating).where(
    Mating.sow_id == sow.id,
    Mating.mating_date == req.mating_date,
    Mating.deleted_at.is_(None),
))
if dup:
    raise ConflictError("해당 날짜에 이미 교배 기록이 있습니다")

# 3. 웅돈 상태 확인
boar = await db.get(Boar, req.boar_id)
if boar and boar.status != "ACTIVE":
    raise ValidationError(f"웅돈 {boar.ear_tag}은 {boar.status} 상태로 교배 불가")
```

---

## 3. 분만

**PigPlan 기준** (MdChildbirthWr.jsp L929~1858)

| 항목 | 조건 | 백엔드 | 프론트 |
|------|------|--------|--------|
| 대상 상태 | PREGNANT만 | ✅ | ❌ |
| total_born = BA + SB + MUM | 일치 필수 | ✅ | ❌ |
| total_born ≤ 35 | | ✅ | ❌ |
| stillborn / mummified ≤ 25 | 각각 | ✅ | ❌ |
| avg_birth_weight_kg ≤ 3.0kg | | ⚠️ 인자 미전달 | ❌ |
| 암+수 합계 = born_alive | | ⚠️ 인자 미전달 | ❌ |
| 임신기간 100~130일 | 100일 미만 경고 | ✅ | ❌ |
| 중복 분만 방지 | | ✅ | ❌ |
| nursing_head 자동계산 | born_alive + 전입 - 전출 - 도태 | ❌ | ❌ |

**백엔드 수정 필요**
```python
# 1. validate_farrowing 인자 완성 (event_service.py)
validate_farrowing(
    total_born=req.total_born, born_alive=req.born_alive,
    stillborn=req.stillborn, mummified=req.mummified,
    avg_birth_weight_kg=req.avg_birth_weight_kg,  # ← 추가
    male=req.born_alive_male,                      # ← 추가
    female=req.born_alive_female,                  # ← 추가
)

# 2. nursing_head 컬럼 추가 (models/events.py)
nursing_head: Mapped[int | None] = mapped_column(Integer)

# 3. nursing_head 초기값 세팅 (event_service.py)
farrowing = Farrowing(..., nursing_head=req.born_alive, ...)
```

**프론트 추가 필요** (실시간 계산 포함)
```typescript
z.object({
  farrowing_date: z.string().refine(d => new Date(d) <= new Date()),
  total_born: z.number().int().min(0).max(35),
  born_alive: z.number().int().min(0).max(35),
  stillborn: z.number().int().min(0).max(25),
  mummified: z.number().int().min(0).max(25),
  avg_birth_weight_kg: z.number().min(0).max(3.0).optional(),
}).refine(d => d.total_born === d.born_alive + d.stillborn + d.mummified, {
  message: "총산 = 실산 + 사산 + 미라",
  path: ["total_born"],
})
// UI: total_born 실시간 자동계산 표시
// UI: nursing_head 실시간 표시 (born_alive 기준)
```

---

## 4. 포유자돈 폐사

**PigPlan 기준**: 폐사일 분만일~이유일 사이, 폐사두수 ≤ nursing_head, 자돈 일령 자동계산

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 날짜 범위 (분만~이유) | ✅ `date_rules.py` | ❌ |
| 폐사두수 ≤ nursing_head | ✅ `event_service.py` | ❌ |
| age_days 자동계산 | ❌ | — |

**백엔드 추가 필요**
```python
# models/events.py
age_days: Mapped[int | None] = mapped_column(Integer)

# event_service.py
event = PigletEvent(..., age_days=(req.event_date - farrowing.farrowing_date).days)
```

---

## 5. 양자 (Cross-Fostering)

**PigPlan 기준** (MdYangjaWr.jsp): 25두 상한, target_sow LACTATING, **거울 레코드 자동생성**

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 날짜 범위 | ✅ | ❌ |
| 25두 상한 | ✅ `cross_fostering.py` | ❌ |
| target_sow LACTATING | ✅ `event_service.py` | ❌ |
| **거울 레코드 자동생성** | ❌ | — |

**핵심: 거울 레코드** (MdYangjaWrMapper.xml L383~398)  
FOSTER_OUT 저장 시 → target_sow에 FOSTER_IN 자동 생성. 없으면 두 모돈의 nursing_head 합산이 틀어짐.

```python
# event_service.py — FOSTER_OUT/IN 저장 후 실행
if req.event_type in ("FOSTER_IN", "FOSTER_OUT"):
    mirror_type = "FOSTER_IN" if req.event_type == "FOSTER_OUT" else "FOSTER_OUT"
    target_farrowing = await db.scalar(
        select(Farrowing)
        .where(Farrowing.sow_id == req.target_sow_id, Farrowing.deleted_at.is_(None))
        .order_by(Farrowing.farrowing_date.desc()).limit(1)
    )
    if target_farrowing:
        db.add(PigletEvent(
            farm_id=farm_id, farrowing_id=target_farrowing.id,
            sow_id=req.target_sow_id, event_date=req.event_date,
            event_type=mirror_type, piglet_count=req.piglet_count,
            target_sow_id=sow.id, target_farrowing_id=farrowing.id,
            notes=f"auto-mirror:{event.id}", created_by=user_id,
        ))
```

---

## 6. 이유

**PigPlan 기준** (DataValidationChk.java L747~760)

| 항목 | 조건 | 백엔드 | 프론트 |
|------|------|--------|--------|
| 대상 상태 | LACTATING만 | ✅ | ❌ |
| 포유기간 | 10~60일 | ✅ | ❌ |
| **이유두수 공식** | weaned = nursing_head - deaths - out + in | ⚠️ 함수 있음, 미호출 | ❌ |
| 이유체중 | 2~12kg | ❌ | ❌ |
| 국가별 최소일령 | KR 21일, EU 28일 | ✅ | ❌ |

**백엔드 수정 필요**
```python
# event_service.py 상단에 import 추가
from app.validators.weaning import validate_weaning

# record_weaning 안에 추가 (_calc_piglet_adjustments 이후)
foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
validate_weaning(
    weaned=req.weaned_count,
    nursing_head=farrowing.nursing_head or farrowing.born_alive,
    deaths=deaths, transfers_out=foster_out, transfers_in=foster_in,
)

# 이유체중 범위 추가
if req.avg_weaning_weight_kg and not (2.0 <= req.avg_weaning_weight_kg <= 12.0):
    raise ValidationError("이유체중은 2~12kg 범위여야 합니다")
```

---

## 7. 도폐사 / 판매

**PigPlan 기준** (DataValidationChk.java L537~553)

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 처리구분 필수 (CULLED/DEAD/SOLD/TRANSFER) | ✅ | ❌ |
| 포유 중 도태/판매/전출 불가 | ✅ `routers/sows.py` | ❌ |
| 임신 중 도폐사 → 사유 필수 | ❌ | ❌ |
| exit_date 설정 + Removal 이력 | ✅ | — |

**백엔드 추가 필요**
```python
if sow.status == "PREGNANT" and req.removal_type in ("CULLED", "DEAD"):
    if not req.notes:
        raise ValidationError("임신돈 도폐사 시 사유를 입력해야 합니다")
```

---

## 8. 웅돈 (Boar)

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 귀표 중복 | ✅ | ✅ 수동 |
| semen_quality enum | ✅ | ❌ |
| 교배 시 ACTIVE 확인 | ❌ (§2에서 처리) | ❌ |

---

## 9. 비육돈 (Grow-Finish)

**PigPlan 기준** (DataValidationChk.java L943~1047)

| 항목 | 백엔드 | 프론트 |
|------|--------|--------|
| 입식두수 ≥ 1 | ✅ | ⚠️ 수동 |
| 그룹코드 중복 | ✅ | ❌ |
| **잔여두수 기반 폐사/출하 검증** | ❌ | ❌ |
| 입식체중 5~50kg | ❌ | ❌ |
| 출하체중 > 입식체중, ≤ 200kg | ❌ | ❌ |
| 출하 완료 그룹 이벤트 차단 | ✅ | ❌ |

**신규 파일 필요: `api/app/validators/finisher.py`**
```python
MIN_ENTRY_WEIGHT_KG, MAX_ENTRY_WEIGHT_KG, MAX_EXIT_WEIGHT_KG = 5.0, 50.0, 200.0

def validate_finisher_entry(*, entry_count, avg_entry_weight_kg=None):
    if entry_count < 1:
        raise ValidationError("입식두수는 1두 이상이어야 합니다")
    if avg_entry_weight_kg and not (MIN_ENTRY_WEIGHT_KG <= avg_entry_weight_kg <= MAX_ENTRY_WEIGHT_KG):
        raise ValidationError(f"입식체중은 {MIN_ENTRY_WEIGHT_KG}~{MAX_ENTRY_WEIGHT_KG}kg 범위여야 합니다")

def validate_finisher_event_count(*, action_count, remaining_head, label):
    if action_count > remaining_head:
        raise ValidationError(f"{label} {action_count}두가 잔여두수 {remaining_head}두를 초과합니다")

def validate_finisher_exit_weight(*, avg_exit_weight_kg, avg_entry_weight_kg=None):
    if avg_exit_weight_kg > MAX_EXIT_WEIGHT_KG:
        raise ValidationError(f"출하체중이 최대 {MAX_EXIT_WEIGHT_KG}kg을 초과합니다")
    if avg_entry_weight_kg and avg_exit_weight_kg <= avg_entry_weight_kg:
        raise ValidationError("출하체중은 입식체중보다 커야 합니다")

# 잔여두수 공식
def calc_remaining_head(group) -> int:
    return (group.entry_count
            + (group.total_transfers_in or 0)
            - (group.total_deaths or 0)
            - (group.total_transfers_out or 0)
            - (group.total_shipped or 0))
```

---

## 이벤트 수정/삭제 규칙

| 항목 | 백엔드 |
|------|--------|
| 월마감 후 수정/삭제 금지 | ✅ `_ensure_period_unlocked()` |
| 분만 있는 교배 삭제 금지 | ✅ `delete_mating()` |
| 이유 있는 분만 삭제 금지 | ✅ `delete_farrowing()` |
| 삭제 시 상태 롤백 | ✅ ROLLBACK_STATUS_ON_DELETE |
| 분만 수정 시 avg_birth_weight 재검증 | ⚠️ `update_farrowing` 누락 |

---

## 구현 체크리스트

### 지금 당장 (P0 백엔드)

| # | 작업 | 파일 |
|---|------|------|
| 1 | `validate_weaning()` 호출 연결 | `event_service.py` |
| 2 | 이유체중 2~12kg 범위 검증 추가 | `event_service.py` |
| 3 | 양자 거울 레코드 자동생성 | `event_service.py` |
| 4 | `nursing_head` 컬럼 추가 + 자동계산 | `models/events.py` + `event_service.py` |
| 5 | `age_days` 컬럼 추가 + 자동계산 | `models/events.py` + `event_service.py` |
| 6 | `validate_farrowing()` 인자 완성 (체중, 암수) | `event_service.py` |
| 7 | 교배 중복 날짜 방지 쿼리 | `event_service.py` |
| 8 | 교배 시 웅돈 ACTIVE 상태 확인 | `event_service.py` |
| 9 | 교배 시 웅돈 인자 전달 | `event_service.py` |
| 10 | 임신 중 도폐사 사유 필수 | `event_service.py` |
| 11 | `validators/finisher.py` 신규 생성 | 신규 파일 |
| 12 | 비육돈 잔여두수 검증 연결 | `routers/finishers.py` |
| 13 | 분만 수정 시 avg_birth_weight 재검증 | `event_service.py` `update_farrowing` |

### 지금 당장 (P0 프론트)

| # | 작업 | 위치 |
|---|------|------|
| 14 | 분만 Zod schema + total_born 실시간 계산 | 분만 form |
| 15 | 이유 Zod schema | 이유 form |
| 16 | 교배 Zod schema | 교배 form |
| 17 | 자돈 이벤트 Zod schema | 자돈 form |
| 18 | 도폐사 Zod schema | 도폐사 form |
| 19 | 모돈 전입 Zod schema | sows form |
| 20 | 비육돈 입식/출하 Zod schema | finishers form |

### 나중에 (P1 — 번식 보조)

- 부분이유: nursing_head 연동 필수 (지원 결정 시)
- 초발정 기록
- 모돈 장소이동
- 모돈 그룹관리
- 모돈 농장이동 (멀티팜 결정 시)

### 나중에 (P2 — 부가 관리)

- 사료급이기록
- 백신기록
- 등지방 관리
- 일괄작업 / Excel 업로드

---

## 모돈 상태 전이 맵

```
전입
 └→ GILT ──교배──→ PREGNANT ──분만──→ LACTATING ──이유──→ OPEN
              ↑                │                            │
            교배              임신사고                     교배
              │                ↓                            │
            OPEN ←──────── ACCIDENT ◄─────────────────────┘
              │
     도폐사/판매 → CULLED / DEAD / SOLD / TRANSFER (EXIT)
```

---

## PigPlan ↔ PigOS 상태 코드 매핑

| PigPlan | 설명 | PigOS |
|---------|------|-------|
| A (wkGubun) | 후보돈 | `GILT` |
| G | 임신돈 | `PREGNANT` |
| B | 포유돈 | `LACTATING` |
| E | 이유돈/공태 | `OPEN` |
| F | 사고돈 | `ACCIDENT` |
| outGubunCd 080001 | 도태 | `CULLED` |
| outGubunCd 080002 | 폐사 | `DEAD` |
| outGubunCd 080003 | 전출 | `TRANSFER` |
| outGubunCd 080004 | 판매 | `SOLD` |

---

## PigPlan 출처 레퍼런스

| 항목 | 파일 | 라인 |
|------|------|------|
| 교배 상태 체크 | DataValidationChk.java | 444~450 |
| 웅돈 순서 강제 | DataValidationChk.java | 505~520 |
| 총산 ≤ 35 | MdChildbirthWr.jsp | 1580 |
| 사산/미라 ≤ 25 | MdChildbirthWr.jsp | 1598 |
| 출생체중 ≤ 3kg | MdChildbirthWr.jsp | 1848 |
| 임신기간 100일 경고 | MdChildbirthWr.jsp | 1766 |
| 포유개시두수 공식 | MdChildbirthWrMapper.xml | 40~54 |
| 이유두수 공식 | DataValidationChk.java | 747~752 |
| 이유체중 2~12kg | DataValidationChk.java | 753~760 |
| 양자 거울 레코드 | MdYangjaWrMapper.xml | 383~398 |
| 자돈 일령 계산 | MdPjadongDiedWrMapper.xml | 342~346 |
| 도폐사 포유 중 금지 | DataValidationChk.java | 537~553 |
| 비육돈 잔여두수 | DataValidationChk.java | 943~1047 |
