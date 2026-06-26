# PROMPT — 작업 A+B+C 교차검증 (Codex용) ★ US 적재 전 필수

대상: Codex (활성 dev PC, c:\dev\PigOS)
기준 문서: `handoff/KPI_GOVERNANCE_v3.1.md` **§10(v3.2)** (단일 진실 소스)
검증 대상 커밋: A=`bcf75fb`, B=`5d0b4ef`, **C=`9c41221`**
검증 head: `uv run alembic current` → **`d7f9b2c4e6a1`** (C 적용 후) / 회귀 기대 **530 passed**
역할: **독립 적대적 감사자.** 고치지 말고 보고. 결함은 재현절차+문서조항 근거 포함.

## 0. 왜 지금(US 적재 전)인가
- B 작업 중 **mutation 1건 발견됨**(`benchmark_seed.py` ★⑧ transform_formula 가드가 `if False and …`로 무력화 → test_06이 RED로 적발 → 복원). **한 번 뚫렸으면 다른 가드도 의심**한다 — 이게 이 검증의 1순위.
- US 적재는 verified/normalized_verified를 **실제로 박는 쓰기 작업**. 게이트가 새는 채로 US를 넣으면 잘못된 verified가 안 잡힌다. 데이터 쌓이기 전 **구조만 있는 지금**이 검증 최적기.

## 1. 절대 규칙
- 코드 수정·커밋 금지(검증만). KR verified 승격 금지. BR/VN/CN/TH/MX 수치 시드 금지. 문서 없는 KPI 추가 금지.
- assert True 류 빈 통과 적발. 테스트 안 한 항목 PASS 금지.

## 2. ★1순위 — mutation 재발 점검 (가드 무력화 스캔)
Claude self-scan은 `if False/if True/and False/or True` 0건, 주석처리 raise 0건 보고함. **독립 재확인 + 더 깊게**:
- 전 코드에서 무력화 패턴 스캔(중복 확인): 
  ```
  grep -rnE "if (False|True)\b|and False\b|or True\b|#\s*(raise|assert)" app/ | grep -v ".pyc"
  ```
- **mutation 테스트(능동)**: validate_benchmark의 ★⑦/⑧/⑫ 각 규칙을 **하나씩 일시 무력화**(주석/반전)하고 `pytest tests/integration/test_benchmark_governance.py tests/integration/test_kr27_reverification.py` 실행 → **각 규칙마다 대응 테스트가 RED로 변하는지** 확인. RED 안 되는 규칙 = 빈 테스트(결함). **확인 후 반드시 원복**.
  - 매핑: ★⑦→test_09, ★⑧→test_06/test_10, ★⑫-4→test_08/test_12, ★⑫-5→test_13, ★⑫-6→test_14, 복합FK→test_07, active-verified→test_15.
- severity_for(★⑪)의 each branch도 부호 반전 시 test_01/02/03/11이 잡는지.

## 3. ★2순위 — DB CHECK 실작동 (seed validator 우회)
seed validator(Python)는 통과시켜도, **DB CHECK가 직접 INSERT를 막는지**를 SQL로 검증(파이썬 우회):
```
docker exec pigos-postgres psql -U pigos -d pigos -c "\d+ benchmarks"   # CHECK 8종 + uq index 실재
```
각 제약을 **위반하는 raw INSERT**가 DB에서 거부되는지(테스트DB 아닌 dev pigos에서, 트랜잭션 롤백으로):
```
-- ★⑦: verified인데 transformed_value NULL → 거부돼야
BEGIN; INSERT INTO benchmarks(country_code,kpi_code,definition_id,benchmark_status,is_provisional,comparison_status)
       VALUES('XX','psy','PIGOS_PSY_V1','verified',false,'compatible'); ROLLBACK;
-- ★⑧: normalized_verified인데 transform_formula NULL → 거부
-- ★⑫-5: missing인데 transformed_value 값 있음 → 거부
-- ★⑫-6: comparison_status='incompatible'인데 warning_min 값 → 거부
-- 복합FK: definition_id='PIGOS_WRONG_V1' → 거부
-- value_scale: 'percent' 같은 비허용값 → 거부
```
각각 **ERROR(거부)면 PASS, 통과(삽입성공)면 FAIL**. 어느 CHECK가 DDL에는 있는데 실제로 안 막으면 치명.
- **active-verified unique 실증**: 동일 (country,kpi,def) active verified 2건 raw INSERT → 2번째 거부되는지. is_active=false면 중복 허용되는지(부분 인덱스 동작).

## 4. ★3순위 — A 결과 정합 재확인 (DB 실측)
```
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*) FROM kpi_definitions;"          -- 16
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*),count(value_scale),count(direction) FROM kpi_definitions;"  -- 16/16/16
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*) FROM source_observations WHERE country_code='KR';"          -- 27
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT benchmark_status,count(*) FROM benchmarks WHERE country_code='KR' GROUP BY 1;"  -- provisional 10 + missing 1
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*) FROM default_metric_values WHERE scope_code='KR';"          -- 27 (원본 삭제 0)
```
- **KR verified/normalized_verified 0건** 재확인(있으면 FAIL).
- §2 표 ↔ kpi_definitions 16행 한 줄씩 대조(분자/분모/denom_type/direction/value_scale). 특히 stillbirth_rate=(사산+미라)/total_born/lower_better.
- direction별 칸 배치(★⑪) 역배치 없는지: higher(psy/msy/farrowing_rate/weaned_per_litter)=min칸, lower(npd/sow_mortality/wsi/fcr/prewean_mortality)=max칸, range(culling_rate)=상단.

## 5. ★4순위 — B 판정 정합
- orphan 16 전부 §2 미정의인지(매핑 가능한데 빠진 "누락 orphan"이 정말 0인지) 독립 재확인: 각 orphan source_kpi_code ↔ kpi_definitions.kpi_code 대조.
- 사산율 missing 근거(원자료 raw_fields 없음)가 맞는지: KR stillbirth source_observations.raw_fields_json에 stillborn/mummified/total_born **분리수치가 없는지** 확인.
- **D-7 누수 재현**: 非KR 농장 컨텍스트에서 loss.py의 sow_cull_loss류가 SOW_RESIDUAL/SOW_SALVAGE(KRW)로 발화 가능한지 코드 경로 추적. (사용자 결정: 출시 전 KR 전용 분리, P2 일반화 — 단 이 검증은 "누수 실재 여부" 확인까지만, 분리 구현은 별도 작업.)

## 5.5 ★ 작업 C 검증 (KR verified 승격 — 1차자료 한돈팜스 2025)
C는 **verified를 실제로 박은 쓰기 작업**이라 게이트가 새면 잘못된 verified가 들어간다. 집중 감사:
```
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT benchmark_status,population_scope,count(*) FROM benchmarks WHERE country_code='KR' GROUP BY 1,2 ORDER BY 1,2;"
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT kpi_code,population_scope,transformed_value,value_scale,comparison_status,transform_formula FROM benchmarks WHERE country_code='KR' AND benchmark_status IN ('verified','normalized_verified') ORDER BY benchmark_status,kpi_code;"
```
- **national_general verified 7종** = psy22.4/msy18.9/farrowing_rate85.7/prewean_survival89.1/postwean_survival84.3/weaned_per_litter10.45/sow_turnover2.14. 값/value_scale이 §10.3 및 kpi_definitions와 일치하는가(override 0)?
- 7종 모두 comparison_status=`compatible`, transform_formula=NULL(verified는 ★⑫-3), transformed_value NOT NULL(★⑦)?
- **professional stillbirth_rate** normalized_verified 9.3%, transform_formula·obs_group 기록, comparison_status=`normalized`(★⑧ 6조건)?
- **전국 stillbirth_rate는 여전히 missing**인가? (전문 9.3%가 national_general로 새지 않았는지 — 모집단 혼입 ★) :
  ```
  docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT population_scope,benchmark_status FROM benchmarks WHERE country_code='KR' AND kpi_code='stillbirth_rate';"
  ```
  → (NULL/missing) + (professional/normalized_verified) 2행이어야. national_general verified면 **FAIL**.
- **드롭 확인**: total_born·market_age가 benchmarks/kpi_definitions에 신규 생성되지 않았는가(범위 밖 코드 신설 금지)?
- **npd** 여전히 provisional(전국 데이터 없음, D-1 무관)인가?
- population_scope unique: national+professional 같은 kpi 공존 / 같은 population 중복 차단(SQL raw INSERT 재현). is_provisional/transformed_value 정합(★⑦).
- C 마이그레이션 downgrade가 깨끗한가(provisional 복원·신규3 삭제·professional 삭제·컬럼 drop) — `alembic downgrade -1` 후 `upgrade head` 왕복 테스트(dev에서, 데이터 무손상 확인).

## 6. 회귀
- `cd api && uv run pytest tests/ -q` → **530 passed** 재현, 0 fail/error.
- `uv run alembic current` → `d7f9b2c4e6a1`.
- git diff로 A·B·C 변경 범위가 신규파일 + models(benchmark.py population_scope) + benchmark_seed 복원뿐인지(기존 default_metric_values·Rule Engine·이벤트 로직 무변경) 확인.

## 7. 출력
- mutation 재점검 결과표(규칙→테스트 RED 여부). RED 안 되는 규칙 있으면 ★P0.
- DB CHECK 실작동표(제약→거부 여부). 안 막는 CHECK 있으면 ★P0.
- A/B 정합 재확인 결과(16/27/10+1/삭제0/verified0).
- 새 P0 구조결함(있으면). 컬럼네이밍·취향은 제외.
- **US 적재 진입 가능 판정**(블로커 유무). 블로커 0이면 "US 적재 GO".
- 발견된 신규 D질문.

## 8. 통과 후 다음(이번엔 하지 말 것)
US PigCHAMP source_observations 적재 → 사산율 normalized_verified(9.93%, formula) / 분만율 verified(83.81%) / PWMFY→psy missing. 그 다음 EU/GB(D-3 후) provisional, TH/MX global_fallback. BR/VN/CN 1차자료 전 금지.
참고 해소된 결정: **D-8**=validator 8개(base+도메인7, 8번째=finisher.py) / **D-13**=fcr value_scale n/a / **D-7·D-10**=손실액 통화일반화 P2(출시 전 KR분리).
