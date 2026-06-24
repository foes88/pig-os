# PigOS 정합성 검증 참조 — 모바일 미러용 단일 소스 (2026-06-23)

> 목적: iOS/Android가 **웹과 동일한 입력 검증**을 클라이언트에서 즉시 피드백하도록 규칙을 한곳에 정리.
> **원칙: 백엔드가 권위(authority).** 모바일/웹 클라 검증은 UX(즉시 차단)일 뿐, 최종 판정은 서버 응답(422/409/423).
> 출처(코드): `api/app/validators/*.py` · `api/app/routers/base/{sows,events,finishers}.py` · `api/app/services/event_service.py` · 웹 Zod `src/lib/validation/eventSchemas.ts`.
> 표기: **HARD**=제출 차단(422) · **CONFLICT**=409 · **LOCK**=423(월마감) · **SOFT**=경고(저장 허용).

---

## 1. 분만 (Farrowing)  — `validators/farrowing.py`
| 규칙 | 임계 | 유형 | 메시지키/코드 |
|---|---|---|---|
| 총산자 상한 | total_born ≤ 35 | HARD | totalBornMax |
| 사산 상한 | stillborn ≤ 25 | HARD | stillbornMax |
| 미라 상한 | mummified ≤ 25 | HARD | mummifiedMax |
| 실산자 정합 | total_born = born_alive + stillborn + mummified | HARD | bornAliveSum |
| (암수 입력 시) born_alive = male + female | — | HARD | — |
| 평균 출생체중 | ≤ 3.0 kg | HARD | birthWeightMax |
| 실산자(born_alive) 자동계산 | total − sb − mum, 음수면 빨강 차단 | HARD(클라) | errExceed |

## 2. 이유 (Weaning)  — `validators/weaning.py` + `event_service`
| 규칙 | 식 | 유형 |
|---|---|---|
| 이유두수 항등식 | weaned = nursing_head − piglet_deaths − transfers_out + transfers_in | HARD |
| 이유 체중 범위 | 2 ≤ avg_weaning_weight ≤ 12 kg | HARD |
| 부분이유(is_partial=true) | weaned ≤ remaining(잔여) 허용, 모돈 LACTATING 유지 | 규칙 |
| 최종이유(is_partial=false) | 잔여 전량 강제 → 모돈 OPEN | 규칙 |
| 잔여 0에서 추가 이유 | 차단 | CONFLICT(409) |

## 3. 교배 (Mating)  — `validators/mating.py` + `event_service`
| 규칙 | 내용 | 유형 |
|---|---|---|
| 모돈 상태 | GILT / OPEN / ACCIDENT 만 교배 허용 | HARD(상태전이) |
| 웅돈 순서 | boar_2는 boar_1 있어야 / boar_3은 boar_2 있어야 | HARD |
| 웅돈 상태 | ACTIVE 웅돈만 사용 | HARD |
| 동일일자 중복 교배 | 같은 모돈·같은 날짜 중복 | CONFLICT(409) |

## 3b. 임신감정 (Pregnancy check, D1)  — `event_service.record_pregnancy_check`
| 규칙 | 내용 | 유형 |
|---|---|---|
| 대상 모돈 상태 | **PREGNANT만**(교배 후) | HARD(422) |
| result enum | POSITIVE / NEGATIVE / UNCERTAIN | HARD |
| 음성(NEGATIVE) 전이 | 공태 → 모돈 **ACCIDENT** + 사이클 FAILED (서버 자동) | 서버 |
| 감정일 ≥ 입식일 | event_within_sow_lifespan | HARD |
> 엔드포인트 `POST/GET /events/pregnancy_checks`. 음성=재교배 대기, 모바일은 상태 반영만.

## 4. 양자 (Cross-fostering)  — `validators/cross_fostering.py` + `event_service`
| 규칙 | 내용 | 유형 |
|---|---|---|
| 1회 이전 두수 | ≤ 25 | HARD |
| 대상 모돈 | target_sow_id 필수, 본인 불가, 같은 농장 활성 LACTATING 모돈 | HARD |
| 거울 레코드 | 한쪽만 전송해도 서버가 상대편 자동 생성(전입↔전출 정합) | 서버 자동 |

## 5. 도폐사 (Removal/Cull)  — `sows.py` + `event_service`
| 규칙 | 내용 | 유형 |
|---|---|---|
| 포유 중 도태/판매/전출 | 자돈 고아 방지 → 이유·양자 먼저 (DEAD만 허용) | HARD |
| 임신 중 도폐사 | 사유 필수 | HARD |
| 도폐사일 ≥ 입식일 | removal_date < entry_date 차단 | HARD |

## 6. 비육 (Finisher)  — `validators/finisher.py`
| 규칙 | 임계 | 유형 |
|---|---|---|
| 입식 두수 | ≥ 1 | HARD |
| 입식 평균체중 | 5 ≤ w ≤ 50 kg | HARD |
| 출하 두수 | ≥ 1 | HARD |
| 출하 평균체중 | ≤ 200 kg, **출하 > 입식 체중** | HARD |
| 출하 완료 그룹 | 추가 이벤트 차단 | HARD |

## 7. 상태 전이 (State machine)  — `validators/sow_state.py`
허용 전이만 가능, 아니면 422(현재 상태 + 허용목록 반환):
```
mating    : GILT / OPEN / ACCIDENT   → PREGNANT
farrowing : PREGNANT                 → LACTATING
weaning   : LACTATING                → OPEN
rts       : PREGNANT                 → ACCIDENT
culling   : 모든 활성상태             → CULLED
```

## 8. 날짜 정합 (Date rules)  — `validators/date_rules.py`
| 규칙 | 내용 |
|---|---|
| 이벤트 ≥ 입식일 | 모든 이벤트 date ≥ sow.entry_date |
| 이벤트 ≤ 도폐사일 | 도폐사 후 이벤트 불가 |
| 교배 > 직전 이유일 | 재교배 순서 |
| 분만 > 교배일 | |
| 이유 > 분만일 | |
| 자돈 이벤트(폐사/양자) | 분만일 ≥, (이유 완료 시) 이유일 ≤ |
| **미래일 금지(+1일 유예)** | entry/removal_date ≤ UTC today + 1일 (UTC서버 vs 앞선 타임존 허용; 클라 notFuture는 로컬 기준). 진짜 미래(내일+)=차단 |

## 9. 이벤트 수정/삭제 + 월마감
| 규칙 | 내용 | 유형 |
|---|---|---|
| 삭제 시 상태 롤백 | mating삭제→OPEN · farrowing삭제→PREGNANT · weaning삭제→LACTATING | 서버 |
| 월마감 잠금 | `period_locks` 기간 데이터 수정/삭제 차단 | LOCK(423) |

## 10. 모바일 구현 가이드
1. **클라 사전검증**: 위 HARD 규칙을 입력 폼에서 즉시 표시(웹 Zod와 동일 메시지키 → i18n 공유).
2. **서버 = 최종 판정**: 클라 통과해도 POST 응답 422/409/423을 항상 처리(메시지 detail 표시).
3. **거울 레코드·삭제 롤백·항등식**은 서버 책임 — 모바일은 결과 반영만.
4. **i18n 메시지키**: `validation`·`errors` 네임스페이스 7개어(en/zh/es/vi/th/pt + ko 관리자) 공유.
5. **검증 게이트(릴리스)**: iOS·Android 동일 케이스로 422/409 재현 → 웹과 결과 동일해야 함(글루 버그 0).

## 11. 탐지 계층(SOFT / AI Rule Engine) — 검증과 별개
HARD 검증(위 1~10, 입력 차단)과 달리, **탐지는 막지 않고 알려준다**(저장 후 또는 herd 집계 기준).
- **이벤트 insights**: 이벤트 POST 응답 `insights[]`(분만 사산율·실산자, 이유 포유폐사율·이유일령, 교배 WSI 등) → 배너 렌더만.
- **AI Rule Engine 40종**: 번식·자돈·비육·모돈군·웅돈·손실·종합·건강 KPI 탐지. 전수 = `docs/RULE_ENGINE_CATALOG.md`. 노출처 = 대시보드 알림 · `GET /alerts/*` · 챗. **목록 가변**(운영자 `/admin/rules` 추가/조정) → 모바일은 서버 rule_id/severity/문구 렌더만, 하드코딩 금지.
- **임계는 운영자/국가가 조정**: `/admin/rules`(DB·무배포) + 국가 benchmark. **모바일은 판정/임계 재구현 0** — 서버 severity·문구만 표시.

> 변경 시 이 문서 = 단일 소스. 백엔드 검증 추가/변경되면 여기 + 웹 Zod + 모바일 동시 갱신.
