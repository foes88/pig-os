# 피그플랜(Oracle) → PigOS(PostgreSQL) 이관 매핑 설계 (2단계 준비)

> 상태: 1단계 스키마 덤프(`pigplan_schema_dump.md`) 수신 전 **선행 설계**.
> 확정된 Oracle 앵커(사용자 검증) + PigOS 타깃(이 리포 확인)으로 구조는 고정.
> `⟵덤프` 표시 셀은 스키마 덤프의 컬럼·코드값으로 채운다.
>
> 원칙: **raw INSERT 금지.** PigOS 서비스 레이어(`app/services/event_service.py`)의
> `record_*`를 시간순 재생(replay)해서 breeding_cycle 자동구성 + 스냅샷 재계산까지 태운다.
> → 검증(밸리데이터) + 사이클 조립 + KPI 로직을 그대로 통과 = 정합성 검증의 핵심.

---

## 1. 엔티티 매핑 (Oracle → PigOS)

| Oracle | PigOS 타깃 | 진입점(서비스) |
|---|---|---|
| `TA_FARM` | `farms` (+ `organizations`) | 직접 생성(온보딩 상당). FARM_NO→외부키 보존 |
| `TB_MODON` | `sows` | 직접 upsert (마스터) |
| `TB_UNGDON` | `boars` | 직접 upsert (마스터) |
| `TB_GYOBAE` | `matings` (+ breeding_cycle) | `record_mating` |
| `TB_BUNMAN` | `farrowings` | `record_farrowing` |
| `TB_EU` | `weanings` | `record_weaning` |
| `TB_SAGO` | `reproductive_events` | `record_reproductive_event` |
| `TB_MODON_JADON_TRANS` | `cross_fostering` | `record_piglet_event`(FOSTER_IN/OUT) |
| `TG_BUN_JADON` | 포유자돈 폐사 → `piglet_events` | `record_piglet_event`(DEATH) |
| `TB_MODON_WK` | (이벤트 분해 소스) | WK_GUBUN으로 위 이벤트로 분기 |
| `TC_FARM_CONFIG` | `farm_config`(임신/포유/WSI 등) | 농장 설정 반영 |

> `TB_MODON_WK` vs `TB_GYOBAE/TB_BUNMAN/TB_EU` 관계는 덤프 A절에서 확정.
> (WK가 헤더+상세FK인지, 상세테이블이 독립인지 → 조인키 결정)

## 2. 필드 매핑 — 핵심 테이블

### TB_MODON → sows
| Oracle | PigOS | 비고 |
|---|---|---|
| `FARM_NO,PIG_NO` | (외부키 보존용 `source_ref`) | PigOS PK는 uuid 신규 |
| `FARM_PIG_NO` | `ear_tag` | 귀표번호 |
| `PUMJONG_CD` | `breed` | 코드→명 (`TC_CODE_JOHAP` PCODE='041') ⟵덤프 |
| `BIRTH_DT` | `date_of_birth` | |
| `IN_DT` | `entry_date` | |
| `IN_SANCHA` | `parity`(초기) | 입식 산차 |
| `STATUS_CD` | `status` | 코드 매핑 §3 ⟵덤프 |
| `OUT_DT` | `cull_date`/`exit_date` | |
| `OUT_GUBUN_CD` | 도폐사 유형(CULL/DEAD/SOLD) | `TC_CODE_SYS` PCODE='08' ⟵덤프 |
| `OUT_REASON_CD` | `reason_category` | `TC_CODE_JOHAP` PCODE='031' ⟵덤프 |

### TB_GYOBAE → matings (`record_mating`)
| Oracle | PigOS | 비고 |
|---|---|---|
| `FARM_NO,PIG_NO` | sow 조회 | |
| 교배일 | `mating_date` | 컬럼명 ⟵덤프 |
| 교배구분(AI/자연) | `mating_type` | ⟵덤프 |
| 웅돈 | `boar_id` | TB_UNGDON 조인 ⟵덤프 |
| `SANCHA` | 사이클 parity | |

### TB_BUNMAN → farrowings (`record_farrowing`)
| Oracle | PigOS | 비고 |
|---|---|---|
| 분만일 | `farrowing_date` | ⟵덤프 |
| 총산 | `total_born` | ⟵덤프 |
| 실산 | `born_alive` | ⟵덤프 |
| 사산 | `stillborn` | ⟵덤프 |
| 미라 | `mummified` | ⟵덤프 |
| 평균생시체중 | `avg_birth_weight` | 있으면 ⟵덤프 |

### TB_EU → weanings (`record_weaning`)
| Oracle | PigOS | 비고 |
|---|---|---|
| 이유일 | `weaning_date` | ⟵덤프 |
| 이유두수 | `weaned_count` | ⟵덤프 |
| 이유일령 | `weaning_age_days` | ⟵덤프 |

### TB_SAGO → reproductive_events (`record_reproductive_event`)
| Oracle | PigOS | 비고 |
|---|---|---|
| 사고일 | event_date | ⟵덤프 |
| 사고구분(재발정/유산/공태) | event_type (RTS/ABORTION/…) | 코드 ⟵덤프 |

## 3. 코드값 매핑 — ✅ 덤프/CSV로 확정 (2026-07-10)

**모돈상태 STATUS_CD (PCODE 01)**: 010001 후보돈→GILT · 010002 임신돈→PREGNANT · 010003 포유돈→LACTATING · 010004 대리모돈→LACTATING · 010005 이유모돈→OPEN · 010006 재발돈→ACCIDENT · 010007 유산돈→ACCIDENT · 010008 도폐사돈→CULLED/DEAD

**사고 sago_gubun_cd (TB_SAGO, PCODE 05)** → ReproductiveEvent.event_type:
050001 (구)재발불임→RETURN_TO_ESTRUS · 050002 유산→ABORTION · 050003 도태→CULLED · 050004 폐사→DEAD · 050005 임돈전출→TRANSFER_OUT · 050006 임돈판매→SOLD · 050007 공태→EMPTY · 050008 재발→RETURN_TO_ESTRUS · 050009 불임→INFERTILE

**교배 method_1 (TB_GYOBAE)**: `A`→AI · `N`→NATURAL. boar=ungdon_pig_no_1

**양자/폐사 gubun_cd (TB_MODON_JADON_TRANS, PCODE 16)** → PigletEvent:
160001 포유자돈폐사→DEATH(reason=OTHER) · 160003 양자전입→FOSTER_IN(target=io_pig_no) · 160004 양자전출→FOSTER_OUT(target=io_pig_no) · 160002 부분이유→(스킵/부분이유 플래그)

**출하 out_gubun_cd (TB_MODON, PCODE 08)**: 080001 도태→CULL · 080002 폐사→DEAD · 080003 전출→TRANSFER · 080004 판매→SOLD

**분만 TB_BUNMAN**: silsan→born_alive · sasan→stillborn · mila→mummified · avg_birth_weight = saengsi_kg(총중량)/silsan · silsan_am/su(암/수) 대부분 0→스킵
**이유 TB_EU**: dusu→weaned_count · ilryung→(PigOS가 분만일로 계산) · avg_weaning_weight = total_kg/dusu
**국가**: TA_FARM.country_code=`KOR`(alpha-3) → PigOS `KR`. 날짜: wk_dt=`YYYYMMDD`, TB_MODON.birth_dt=`YYYY-MM-DD`

### (참고) 원래 초안 매핑 표 — ⟵덤프 D절로 확정

| Oracle STATUS_CD(PCODE 01) 추정 | PigOS status |
|---|---|
| 임신 | `PREGNANT` |
| 포유 | `LACTATING` |
| 이유후/공태 | `OPEN` |
| 후보(미교배) | `GILT` |
| 사고/재발정 대기 | `ACCIDENT` |
| 도태 | `CULLED` |
| 폐사 | `DEAD` |

> PigOS 허용 status: `GILT/OPEN/PREGNANT/LACTATING/ACCIDENT`(활성) + `CULLED/DEAD`(종료).
> 구 코드 `GESTATING/WEANED/DRY/ACTIVE`는 폐기됨 — 낡은 가이드 참조 금지.

## 3.5 추출 필수 컬럼 체크리스트 (PigOS Create 스키마로 검증됨)

> `record_*`가 요구하는 **필수/enum 필드** — 2단계 추출이 반드시 포함해야 함(빠지면 재추출).

| PigOS 이벤트 | 필수 필드 | enum 제약 | Oracle에서 뽑을 것 |
|---|---|---|---|
| **mating** | `mating_date`, `mating_type` | `mating_type ∈ {AI, NATURAL}` | TB_GYOBAE **교배구분코드**(→AI/NATURAL), 교배일, 교배회차(→mating_number 1~5), 웅돈번호(→boar) |
| **farrowing** | `farrowing_date`, `born_alive` | — (`total_born`=실산+사산+미라 **서비스가 자동합산**) | TB_BUNMAN **실산·사산·미라 3개 분리**(총산 아님!), 평균생시체중, (암/수) |
| **weaning** | `weaning_date`, `weaned_count`(0~30) | — (이유일령은 서비스가 분만일로 계산) | TB_EU 이유일, 이유두수 |
| **reproductive** | `event_date`, `event_type` | `∈ {RETURN_TO_ESTRUS, ABORTION, EMPTY, INFERTILE, CULLED, DEAD, TRANSFER_OUT, SOLD, HEAT_DETECTED}` | TB_SAGO **사고구분코드** → 위 9종 매핑 (코드사전 필수) |
| **piglet** | `event_date`, `event_type`, `piglet_count`(≥1) | `event_type ∈ {STILLBORN_REMOVAL, DEATH, FOSTER_IN, FOSTER_OUT}`, `reason ∈ {CRUSHING,SCOURS,STARVATION,CONGENITAL,HYPOTHERMIA,OTHER}` | TG_BUN_JADON(폐사→DEATH+사유), TB_MODON_JADON_TRANS(양자→FOSTER_IN/OUT + **target 모돈**, 두수) |

**주의 3가지 (추출·매핑 시 반드시)**
1. **분만은 실산/사산/미라를 분리 추출.** PigOS가 `total_born = born_alive+stillborn+mummified`로 재계산 → 총산만 있으면 못 씀. 피그플랜 총산과 합이 안 맞으면 로그.
2. **mating_type·event_type은 enum 고정.** 교배구분·사고구분 코드값(⟵덤프 D절)을 위 enum으로 매핑하는 표를 먼저 확정. 매핑 안 되는 코드는 격리.
3. **시간순 replay.** `record_farrowing/weaning/piglet`은 ID 생략 시 "최근 열린 교배/분만"에 자동링크 → **모돈별 이벤트를 WK_DT 오름차순**으로 재생하면 링크 자동 해결. 순서 뒤섞이면 오링크.

## 4. 임포트 순서 (농장 1개 기준, 트랜잭션)

1. `TA_FARM` → organization+farm 생성, `TC_FARM_CONFIG` → farm_config 반영
2. `TB_MODON`/`TB_UNGDON` → sows/boars upsert (source_ref로 idempotent)
3. 모돈별 **이벤트를 시간순 정렬** 후 순차 `record_*` 재생:
   교배→(사고?)→분만→(양자입출/포유폐사)→이유→… 반복
   - 각 단계 validator 통과해야 함(불통과 로우는 격리·리포트)
4. 농장 전체 완료 후 KPI 스냅샷 재계산 잡 트리거
5. **정합성 검증**: PigOS 계산 PSY/NPD/FR ↔ 피그플랜 실제 수치 대조표 출력

## 5. 검증 산출물 (정합성)
- 농장별: `{ farm, sow_count, PigOS_PSY, PigPlan_PSY, diff, PigOS_NPD, PigPlan_NPD, diff }`
- 두수 정합: 이유두수 = 실산 + 양자입 − 양자출 − 포유폐사 (모돈별)
- 격리 리포트: validator 422로 걸린 로우 목록 + 사유

## 6. 구현 위치 (예정)
- `api/scripts/import_pigplan.py` — CSV 로더 + 서비스 replay 러너
- 입력: `tests/db/pigplan_data/*.csv` (2단계 추출 산출물)
- `--farm`, `--since`, `--dry-run` 옵션
