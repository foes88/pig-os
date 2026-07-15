# RULE: 포유/대리포유 모돈 도폐사 시 자돈 처리

> 상태: **백엔드 구현 완료(2026-07-15, 옵션 b)** — pytest 6종 통과, openapi 반영. 모바일/웹 UI(disposition 선택) 잔여.
> 출처 = 피그플랜 실동작 분석(2026-07-10).
> 영역: 이벤트 검증(validators) + 이관(import_pigplan) + 모바일/웹 cull 플로우.
>
> **구현 요약**: `POST /farms/{id}/sows/{sow_id}/cull` 에 옵셔널 필드 `piglet_disposition`
> (`FOSTER_TO`|`DEATH`|`WEAN`) + `foster_target_sow_id` + `piglet_death_reason` 추가.
> 포유 모돈 도태 시 잔여 미이유 자돈수>0 인데 disposition 미지정 → **422**(하위호환: 종전에도 422였음).
> 지정 시 해당 처리(전출/폐사/이유) 실행 후 도태. 잔여 0 이면 처리 불필요(종전 무조건 차단 완화).
> **모바일 TODO**: 도폐사 모달에서 LACTATING + 잔여>0 이면 처리방식 선택 UI 노출.

---

## 1. 트리거
**포유돈(LACTATING)** 또는 **대리포유(LACTATING + nurse_sow_flag)** 상태의 모돈을 **도폐사(CULLED/DEAD/SOLD/TRANSFER_OUT)** 할 때.

## 2. 피그플랜 실제 동작 (레거시)
1. 모돈 자동 이유 (`TB_EU`, `DUSU=0`) → 포유 종료.
2. 포유 중이던 자돈을 **양자전출 자동생성** (`TB_MODON_JADON_TRANS`: `GUBUN_CD='160004'`, `AUTO_GB='Z'`).
3. 전출 **대상 모돈 지정 시** → 그 모돈에 양자전입(`160003`) 생성.
4. 전출 **대상 미지정 시** → `IO_PIG_NO IS NULL` 로 **전출만** 되고 전입처 없음
   = **자돈 미아/손실** (폐사 기록도 아니고, 다른 모돈에도 안 붙음).

> ⚠️ 4번이 레거시의 **데이터 무결성 구멍**: 자돈이 조용히 사라져 카운트가 어긋남.

## 3. PigOS 결정사항

### ① 이관(replay) 처리 — 과거 데이터 [필수]
`TB_MODON_JADON_TRANS` 에서 `AUTO_GB='Z' AND GUBUN_CD='160004' AND IO_PIG_NO IS NULL`
= **destination 없는 자동 전출**.

→ **명시 replay**: `piglet_event(event_type='FOSTER_OUT', target_sow_id=NULL, reason='SOW_CULLED')`
로 기록. **안 하면 자돈수 정합성 붕괴**(사라진 만큼 카운트 어긋남).

- 현재 임포터는 KPI(PSY/NPD) 목적상 양자/폐사를 합성폐사로 근사 → 이 케이스는 별도 명시 필요.
- reason enum에 `SOW_CULLED` 추가 검토(현 enum: CRUSHING/SCOURS/STARVATION/CONGENITAL/HYPOTHERMIA/OTHER → `OTHER`+notes로도 가능).

### ② go-forward 신제품 로직 — 설계 선택 [추천: (b)]
| 안 | 내용 | 평가 |
|---|---|---|
| (a) 그대로 복제 | 미아 허용(피그플랜과 동일) | ❌ 무결성 구멍 답습 |
| **(b) 개선(추천)** | 포유 모돈 cull 시 자돈이 있으면 **전출 대상 지정 강제** 또는 **자돈 폐사 명시** 중 택일 강제. 조용히 사라지는 것 차단 | ✅ 무결성 보장 |

**(b) 구체화**:
- cull(LACTATING, un-weaned 자돈 > 0) 시 요청에 **piglet_disposition** 필수:
  - `FOSTER_TO`(target_sow_id 필수) — 남은 자돈 전출 대상 지정, OR
  - `DEATH` — 자돈 폐사로 명시(사유), OR
  - `WEAN`(일령 충족 시) — 조기 이유 처리.
- 미지정 시 **422** — "포유 모돈 도폐사 시 잔여 자돈 처리(전출/폐사/이유)를 지정해야 합니다".

## 4. 구현 지점
- **검증(②)**: `app/services/event_service.py::apply_terminal_reproductive` (cull 전이) — LACTATING + 잔여 포유두수>0 이면 disposition 요구. `app/validators/` 신규 룰.
- **이관(①)**: `api/scripts/import_pigplan.py` — TB_MODON_JADON_TRANS의 `AUTO_GB='Z' & 160004 & IO_PIG_NO NULL` 을 FOSTER_OUT(dest=NULL) 명시 replay.
- **스키마**: `piglet_events.reason` 에 `SOW_CULLED` 또는 notes 규약. `target_sow_id NULL` 허용 확인(전출 미아).
- **UI(모바일/웹)**: 모돈 도폐사 모달에서 LACTATING이면 "잔여 자돈 처리" 선택 UI(전출대상/폐사/이유) 노출.
- **i18n**: 신규 검증 메시지 7개어.

## 5. KPI 영향
- **PSY**: 잔여 자돈은 이유두수에 안 잡히므로 PSY 분자 무영향. 단 pre-wean 폐사율/자돈 정합엔 영향.
- **자돈 정합**: FOSTER_OUT(dest=NULL) 명시로 "떠난 자돈" 추적 → `_calc_piglet_adjustments`가 effective_litter에서 차감(이미 foster_out 반영). 미아 방지.

## 6. 오픈 이슈
- `target_sow_id=NULL` FOSTER_OUT을 정식 허용할지, 아니면 별도 event_type(`REMOVE_ORPHAN`) 둘지.
- 조기이유(WEAN) 옵션의 최소일령 예외 허용 여부.
