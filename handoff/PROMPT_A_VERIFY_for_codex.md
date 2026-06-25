# PROMPT — 작업 A 독립 검증 (Codex용)

대상: Codex (활성 dev PC, c:\dev\PigOS)
기준 문서: `handoff/KPI_GOVERNANCE_v3.1.md` (단일 진실 소스) + `PROMPT_A_schema_migration.md`
검증 대상 커밋: `bcf75fb` (feat(kpi-gov): 작업A …)
역할: **구현자가 아니라 독립 감사자.** 작업 A가 문서·프롬프트를 정확히·빠짐없이 이행했는지, 정합성이 깨지지 않았는지 적대적으로(adversarial) 검증한다. **고치지 말고 먼저 보고**. 결함 발견 시 재현 절차 + 근거(문서 조항) 포함.

## 0. 환경
- Windows / PowerShell 7. 백엔드: `cd api`. 테스트 DB: Docker postgres(pigos/pigos_test).
- 테스트: `cd api && uv run pytest tests/ -q` (488 기존 + 16 신규 = **504 기대**).
- 마이그레이션 head: `uv run alembic current` → `c5e7a9b1d3f0` 기대.
- 한국어 주석 정상(콘솔 깨짐은 표시 문제).

## 1. 절대 규칙 (작업 A와 동일)
- 문서 §정의·제약 임의 변경 금지. 다르면 고치지 말고 질문.
- KPI 수치 신규 생성 금지(위조 0). KR은 이전+강등만, 삭제 0.
- 테스트 안 한 항목 PASS 금지. assert True 같은 빈 통과 적발.
- KR을 verified로 올렸으면 **결함**(B에서 판정해야 함).

## 2. 검증 항목 (각각 PASS/FAIL + 근거)

### 2.1 스키마 정합 (문서 §3.1~3.3, §3.5)
- 3-테이블이 DDL과 일치하는가? 컬럼 임의 추가/삭제? (단 §5 is_active/effective_from·to·created_at 추가는 허용)
- `benchmarks` 복합 FK `(kpi_code, definition_id) → kpi_definitions` 존재?
- CHECK 제약 실재 확인(DB에서):
  ```
  docker exec pigos-postgres psql -U pigos -d pigos -c "\d+ benchmarks"
  docker exec pigos-postgres psql -U pigos -d pigos -c "\d+ kpi_definitions"
  ```
  ★⑦(verified→is_provisional=false+value NOT NULL), ★⑧(normalized_verified 6조건), ★⑫-1/3/5/6, value_scale enum, active-verified 부분 unique index가 **실제로 DB에 걸렸는지**.
- ⚠️ 쟁점: 구현이 benchmarks.value_scale에 `n/a`를 허용함(문서 §3.3 DDL 주석은 percent_0_100|ratio_0_1만 표기). 근거는 "count KPI(PSY/NPD) NULL이면 can_fire가 막아 발화불가". **이 확장이 타당한지 / 문서 위반인지 판정**하라.

### 2.2 kpi_definitions 시드 (§2)
- 16종 전부? direction/denominator_type/period_basis/unit/value_scale **누락 0**?
  ```
  docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*), count(value_scale), count(direction) FROM kpi_definitions;"
  docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT kpi_code, direction, denominator_type, period_basis, value_scale FROM kpi_definitions ORDER BY kpi_code;"
  ```
- §2 표와 한 줄씩 대조: 분자/분모/denom_type/direction/value_scale 일치? **특히 stillbirth_rate 분자=(사산+미라), denom=total_born, lower_better** 맞는가?
- **D-13 검증**: fcr value_scale을 `n/a`로 시드(문서 §2.2는 'ratio'). enum에 ratio 없음 → n/a 잠정이 합리적 강등인지, 아니면 다른 처리가 옳은지 판정.
- period_basis가 §2.2/§2.3에 명시 없는데 추론 시드(avg_inventory_sow→rolling_365, 그외→period)됨. 이 추론이 §2.1 패턴과 일관되며 위험 없는지 점검.

### 2.3 KR 27 이전 (§4.4) — 정합성 핵심
```
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*) FROM source_observations WHERE country_code='KR';"   -- 27 기대
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT benchmark_status, count(*) FROM benchmarks WHERE country_code='KR' GROUP BY 1;"  -- provisional 10 + missing 1
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT kpi_code, benchmark_status, mapping_status, comparison_status, warning_min, warning_max, critical_min, critical_max, target, value_scale FROM benchmarks WHERE country_code='KR' ORDER BY kpi_code;"
docker exec pigos-postgres psql -U pigos -d pigos -c "SELECT count(*) FROM default_metric_values WHERE scope_code='KR';"   -- 27 (원본 삭제 0 확인)
```
**적대적 체크리스트**:
- KR 중 **verified/normalized_verified가 1건이라도 있으면 FAIL**(B 영역 침범).
- direction별 칸 배치(★⑪) 정확? higher_better(psy/msy/farrowing_rate/weaned_per_litter)는 warning_min/critical_min, lower_better(npd/sow_mortality/wsi/fcr/prewean_mortality)는 warning_max/critical_max, range_target(culling_rate)는 상단. **반대로 들어간 칸 없는가**(NPD가 warning_min에 들어갔다면 역발화 버그).
- stillbirth_rate가 missing이며 transformed_value/threshold 전부 NULL인가(★⑫-5/6).
- orphan 16종이 benchmarks에 **안** 들어갔는가(복합FK 대상 KPI 없음). source_observations엔 보존됐는가(삭제 0).
- 강등 사유가 notes에 한국어로 기록됐는가.
- **재현 시도**: provisional KR 행 하나를 verified로 UPDATE 시도 → ★⑦/⑫ CHECK가 거부하는가? (DB 제약 실효성)
  ```
  docker exec pigos-postgres psql -U pigos -d pigos -c "UPDATE benchmarks SET benchmark_status='verified' WHERE kpi_code='psy' AND country_code='KR';"  -- 거부돼야(transformed_value NULL → ★⑦)
  ```

### 2.4 seed validator + threshold (§3.5, §6)
- `api/app/db/benchmark_seed.py validate_benchmark()`가 ★⑦⑧⑫ 6종 + 복합FK + ★⑫-4(크로스테이블 value_scale)를 전부 잡는가? **누락된 규칙 없는지** 문서 §3.5와 1:1 대조.
- `api/app/engine/benchmark_thresholds.py severity_for()`가 ★⑪ 방향 규칙과 정확히 일치? critical 우선순위 맞는가?
- `can_fire`/`should_generate_insight`가 incompatible/unknown/missing/value_scale없음을 침묵시키는가?

### 2.5 테스트 진정성 (★ 빈 통과 적발)
- `tests/integration/test_benchmark_governance.py` 15종이 **실제 실패조건을 검증**하는가? 각 테스트가 `pytest.raises`/실제 severity 비교를 하는지, assert True 류 없는지 한 개씩 확인.
- **변이(mutation) 검증**: validator의 한 규칙(예 ★⑫-5)을 일시 무력화하면 해당 테스트가 빨개지는가? (테스트가 진짜 그 규칙을 잡는지) — 확인 후 원복.
- DB 테스트(7,15)가 실제 IntegrityError를 발생시키는가(목이 아니라 진짜 DB).

### 2.6 회귀·격리
- `uv run pytest tests/ -q` → 504 pass, 0 fail/error.
- 기존 default_metric_values·Rule Engine·기타 모델 무변경 확인(git diff 범위가 신규 파일+models/__init__ 등록뿐인가).

## 3. 출력 (이 형식으로 보고)
- 항목별 PASS/FAIL 표(2.1~2.6).
- FAIL마다: 무엇이/문서 어느 조항 위반/재현 절차/제안(고치지 말고 제안만).
- "새 P0 구조결함" 있으면 별도 강조. 컬럼 네이밍·취향 수준은 제외(수렴됨).
- 작업 B 진입 가능 여부 판정(블로커 유무).
- D-13(fcr value_scale) 및 발견된 신규 D질문에 대한 의견.

## 4. 하지 말 것
- 코드 수정·커밋 금지(검증만). 결함은 보고.
- KR verified 승격 금지. BR/VN/CN/TH/MX 수치 시드 금지.
- 문서에 없는 KPI/임계 추가 제안을 "필수"로 올리지 말 것(B/후속 후보로만).
