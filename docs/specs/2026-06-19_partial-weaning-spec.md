# 부분이유 (Partial Weaning) 설계 — P1 #1

> 작성: 2026-06-19. MVP_SCOPE: "부분이유 지원 결정 시 **nursing_head 연동 검증과 함께** 구현".
> 전제: P0에서 `farrowings.nursing_head`(초기값=born_alive) 컬럼 + 이유두수 항등식 도입 완료.

## 개념
한 분만(litter)을 **여러 번에 나눠 이유**. 일부만 이유하고 나머지는 계속 포유 → 모돈은 마지막 이유까지 **LACTATING 유지**.

## 핵심 모델 — 잔여 포유두수(remaining)
```
effective_litter = born_alive + foster_in - foster_out - deaths   (piglet_events 집계)
prior_weaned     = Σ(해당 farrowing의 기존 비삭제 weaning.weaned_count)
remaining        = effective_litter - prior_weaned                 (현재 포유 중 두수)
```

## record_weaning 규칙 (is_partial 플래그)
| 조건 | 동작 |
|------|------|
| `remaining <= 0` | **409 Conflict** "Litter already fully weaned" (기존 dedup 대체) |
| `weaned_count > remaining` | **422** (effective litter 초과) |
| `is_partial=False`(최종) AND `weaned_count != remaining` | **422** 항등식 위반 (weaned must == remaining) |
| `is_partial=True` AND 이유 후 remaining>0 | 모돈 **LACTATING 유지**, cycle FARROWED 유지 |
| 이유 후 remaining==0 (최종 or 부분이 잔량 0) | 모돈 **OPEN**, cycle WEANED, ended_at 설정 |

- 각 weaning 1건 = PigletGroup 1개 자동(기존 유지). 같은 날 복수 이유 대비 **group_code에 weaning 단축 suffix** 부여(충돌 방지).
- 이유체중 2~12 / 포유기간 / 컴플라이언스 검증은 매 이유 건에 그대로 적용.

## 하위호환 (기본 is_partial=False)
- 첫 이유: prior_weaned=0 → remaining=effective_litter → 최종이유는 `weaned==effective` 강제 = **기존 P0 항등식과 동일**.
- 2차 이유 시도(첫 이유가 최종): remaining=0 → 409 = **기존 dedup과 동일 효과**.
- 따라서 기존 pytest(중복이유 409, 항등식 422, 정상이유 OPEN) **전부 그대로 통과**.

## 데이터 품질 리포트 연동
- WEANED_MISMATCH: farrowing별 **Σweaned > effective_litter** 기준으로 갱신(단건→합계).

## 프론트/모바일
- WeaningPanel에 "부분이유" 토글(is_partial). 켜면 잔여>0 허용, 안내문구.
- `WeaningCreate.is_partial: bool=false` — 계약서/모바일 동기화. 미전송 시 최종이유(하위호환).
