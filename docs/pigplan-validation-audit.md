# PigPlan ↔ PigOS 입력검증/정합성 감사 (2026-06-18)

> 데이터 두수·날짜·상태 꼬임 = deal-breaker. PigPlan 소스 + rules-extract 대조 결과.
> ✅ 완료 · ⬜ TODO. 백엔드 강제(웹·모바일 공통) 원칙.

## ✅ 이미 잘 된 검증 (PigOS 강점)
- 교배: 상태(GILT/OPEN/ACCIDENT)·웅돈 순서·5회 상한·날짜(입식이후/이전이유이후)
- 분만: 총산≤35·사산/미라≤25·생존=총산-사산-미라·암수합·체중≤3.0·임신100~130·분만>교배·중복1회
- 이유: 이유두수 공식(생존+양자in-out-폐사)·≤30·포유10~60·국가최소이유일령·이유>분만·중복1회
- 양자: 1회 ≤25 (cross_fostering)
- 도폐사: 상태전이·도폐사 후 이벤트 금지(exit_date)

## ✅ 이번에 해소 (정합성 HIGH)
- **분만 상태전이**: PREGNANT에서만 (event_service, 중복검사 뒤)
- **이유 상태전이**: LACTATING에서만
- **자돈 폐사 두수 상한**: 현재 포유두수(생존+양자in-out-기존폐사) 초과 차단
- **도폐사 날짜**: removal_date ≥ 입식일 + 미래일 금지
- **포유중 모돈 도태 차단**: LACTATING + CULLED/SOLD/TRANSFER → 422 (DEAD 허용)
- **이유 시 자돈그룹 자동생성**: weaned_count → PigletGroup (떠다니는 두수 방지, PSY→MSY)
- 회귀: `tests/integration/test_piglet_integrity.py` (10종)

## ⬜ 남은 검증 갭 (다음 작업 — 우선순위순)
| # | 갭 | 심각도 | 구현 방향 |
|---|----|------|----------|
| ~~V1~~ | ~~자돈 이벤트 날짜 순서~~ ✅ 완료 | — | `validate_piglet_event_date()` + lifespan, record_piglet_event 연결 |
| ~~V2~~ | ~~양자 전입 모돈 검증~~ ✅ 완료 | — | FOSTER 시 target_sow_id 필수 + target 활성·LACTATING 확인(고아 자돈 방지) |
| ~~V3~~ | ~~양자 합계 상한(과혼잡)~~ ✅ 완료 | — | FOSTER_IN 후 포유두수 > MAX_NURSING(24) 차단 |
| ~~V4~~ | ~~모돈 등록 날짜·중복귀표~~ ✅ 완료 | — | 입식일 미래금지 + 활성 귀표 중복 422 (create_sow). dob 필드 없어 생년월일 검증 제외 |
| V5 | 미이유 폐사 표시 | 낮(다음버전) | report-time 표기 — 리포트 개편 시 |
| ~~V6~~ | ~~도폐사 사유 세분류~~ ✅ 완료 | — | reason_category enum 9종(REPRODUCTIVE/LAMENESS/DISEASE/AGE/PERFORMANCE…) 이미 강제 + 프론트 select |
| ~~V7~~ | ~~edit 시 검증 적용~~ ✅ 완료 | — | update_weaning 두수 재검증 추가(update_farrowing은 기존 재검증). delete는 상태 롤백 검증됨 |

## 참고 소스
- PigPlan: `c:/dev/pigplan_mobile_2023/lib`, `c:/dev/m_pigplan/lib` (각 record 화면 검증)
- `docs/reference/pigplan-rules-extract.md` (임신114·포유21~25·상한값)
- PigOS: `api/app/validators/`, `api/app/services/event_service.py`, `api/app/schemas/events.py`

> 진행: V1(날짜순서)·V2(양자 전입) = 두수/고아 자돈 직결이라 우선. V4(모돈등록)·V7(수정삭제) 다음.
