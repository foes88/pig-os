# PigOS — 국가별 KPI Benchmark 구조 확정 프롬프트 (구조만 / 수치 0)

> **이 작업은 "구조·정의·방향성·status 처리"만 확정한다. 실제 benchmark 수치는 단 한 칸도 채우지 않는다.**
> 모든 수치는 `NULL` + `benchmark_status='missing'`으로 시작하고, 검증된 값은 이후 별도 시드 단계에서 주입한다.

## 실행 전·후 컨텍스트 (반드시 읽을 것)

* **실행 전 — 활성 PC 확인**: `C:\dev`가 스토리지/싱크 PC의 pull-only 미러면 수정 금지다. 활성 개발 PC인지 확인하고, 활성 PC 기준 경로에서 실행한다(`git remote -v`·최근 커밋·쓰기 권한으로 판단).
* **선행 작업**: 무결성 코어 리팩터(핸드오프 `handoff/pigplan-domain-integrity.md` §8, `handoff/pigplan-rules/` — 상태=이벤트 파생, 산차 double-entry 원장, 이벤트 계약, 정기 감사) **이후**에 실행하는 것을 권장한다. 이 프롬프트는 그 위에 KPI benchmark 계층만 얹는다.
* **후행 상태(정상)**: 이 작업이 끝나면 benchmark가 전부 `missing`이므로 **모든 국가 KPI 룰이 침묵**한다. 이는 버그가 아니라 의도된 종착 상태다. 검증 수치를 시드해야 비로소 발화한다.
* **미룬 것이지 없앤 것이 아님**: 다음 단계는 한돈팜스·PigCHAMP·AHDB·Agriness 등 1차자료로 **수치 검증표를 만드는 작업**이다. 이를 하지 않으면 출시(2026-07-01) 시점에 국가 KPI가 전부 침묵한 채 나간다. 최소 앵커 마켓(US/BR/VN 등)이라도 출시 전 verified 시드가 필요한지는 별도 결정 사항이다.

---

## 1. 절대 규칙

* 어떤 KPI benchmark 수치도 코드/시드에 임의로 넣지 않는다. **추정·인터넷 검색·"일반적으로 알려진 값"으로 채우는 것 전부 금지.**
* 외부 출처를 인용한 듯한 주석으로 수치를 끼워 넣지 않는다. 값 자리는 `NULL`, status는 `'missing'`.
* 테스트하지 않은 항목을 PASS로 쓰지 않는다. 문서 설명만으로 구현 완료로 판정하지 않는다.
* 기존 동작을 깨는 변경은 별도로 표시한다.
* 활성 PC가 아니거나 쓰기 권한이 없으면 작업을 중단하고 사유를 보고한다.

---

## 2. 목표

KPI 계산식과 국가별 benchmark를 분리하고, benchmark 스키마에 **방향성/정의/검증상태 메타**를 추가해, 검증된 수치만 나중에 안전하게 주입할 수 있는 골격을 만든다.

---

## 3. 작업

### 3-1. 현재 코드 조사
`benchmarks` / `country_defaults` / `rule_configs` / seed 관련 파일과 Rule Engine의 임계 비교 로직을 찾아 구조를 요약한다. **KPI 계산식과 benchmark 수치가 한곳에 섞여 있으면 분리 대상으로 표시**한다.

### 3-2. benchmark 스키마 정의
테이블 또는 seed 구조를 아래 컬럼으로 정의한다. **수치 컬럼은 전부 nullable, 기본 NULL.**

| 컬럼 | 설명 |
| --- | --- |
| `country_code` | |
| `production_system` | MVP는 `'all'` 고정. 컬럼만 만들고 indoor/outdoor 세분화는 하지 않는다 |
| `farm_size_band` | MVP는 `'all'` 고정 |
| `kpi_code` | |
| `definition_id` | 어떤 정의로 계산된 값인지 식별. **KPI_DEFINITIONS 레지스트리의 정의를 참조(FK 개념)하며 자유 텍스트 금지.** 외부값 재정규화 판단 기준 |
| `direction` | `'higher_better'` \| `'lower_better'`. **NOT NULL.** 임계 발화 방향 결정 |
| `numerator_def` | 분자 정의 텍스트. 예: `stillborn+mummified` |
| `denominator_def` | 분모 정의 텍스트. 예: `total_born` |
| `mean` / `median` / `p10` / `p25` / `p75` / `p90` | 전부 nullable. **기술통계(분포) 메타이며 발화 권위값이 아니다** |
| `target` | |
| `warning_threshold` / `critical_threshold` | **단일 임계. 발화의 권위값.** `direction`에 따라 상/하단으로 해석 |
| `unit` | |
| `source_name` / `source_year` / `source_url` | |
| `confidence_level` | `'A'`\|`'B'`\|`'C'`. 출처 신뢰도. **표시용 메타 — 발화 게이팅에 쓰지 않는다** |
| `is_provisional` | boolean. 잠정치 여부(confidence와 별개 축). 예: 연중 누적 잠정 발표치. **표시용 메타** |
| `benchmark_status` | `'missing'`\|`'provisional'`\|`'verified'`. 기본 `'missing'`. **발화 게이팅은 오직 이 컬럼으로 한다** |
| `notes` | |

**임계 해석 규칙**: `warning_min/max·critical_min/max` 4컬럼 대신 `direction` + 단일 `warning/critical_threshold`로 간다.
* `direction='lower_better'` → 값이 threshold **이상**일 때 발화
* `direction='higher_better'` → 값이 threshold **이하**일 때 발화

**권위 충돌 방지**: 발화 판정은 항상 `warning/critical_threshold`로 한다. percentile(p10~p90)은 분포 설명·향후 임계 도출 근거일 뿐, 룰 발화에 직접 쓰지 않는다(설계상 명시적으로 의도하지 않는 한).

**단위 정합**: 비교 시 farm 데이터 단위와 benchmark `unit`이 다르면 비교 전에 변환한다(특히 **kg↔lb**, US lb ↔ 미터법). 이중변환·미변환으로 인한 오발화를 방지한다.

### 3-3. KPI 정의서 생성 `docs/KPI_DEFINITIONS.md`
각 KPI마다: `kpi_code`, 한글명, 분자, 분모, 단위, `direction`, PigOS 내부 정의가 업계 컨벤션과 다른 경우 그 차이를 명시.
* 반드시 포함: **PSY, MSY, farrowing_rate, prewean_mortality, postwean_mortality, sow_turnover, NPD, stillbirth_rate, WSI**
* **`stillbirth_rate`**: PigOS 정의는 `(stillborn+mummified)/total_born`이며 업계 컨벤션(`stillborn/total_born`)보다 약 **3%p 높다.** 따라서 외부 벤치마크를 그대로 비교하면 안 된다는 점을 명시한다.
* `direction='lower_better'` KPI(NPD, prewean_mortality, postwean_mortality, stillbirth_rate, WSI 등)를 표로 명확히 구분한다.
* 이 문서의 각 KPI 항목이 `definition_id`의 정본(canonical) 레지스트리가 된다. 스키마의 `definition_id`는 여기 항목을 가리킨다.

### 3-4. 외부 벤치마크 재정규화 규칙 (같은 문서에 추가)
* 외부 출처의 분자/분모 정의가 PigOS `definition_id`와 다르면, **재정규화 가능한 경우에만** 변환 후 시드한다.
* **재정규화 불가능한 출처**(예: stillborn과 mummified가 분리되지 않은 사산 수치)는 해당 KPI를 provisional로도 넣지 말고 `missing`으로 둔다. 이 판단 기준을 문서에 명시한다.

### 3-5. Rule Engine 임계 비교 로직 수정 (direction 기반)
* `benchmark_status='missing'`이면 해당 KPI 룰은 **침묵**(경고 생성 안 함)하고, 사유를 `'benchmark_missing'`으로 표시한다.
* `'verified'`/`'provisional'`일 때만 임계 비교를 수행한다. provisional이면 경고에 provisional 플래그를 함께 반환한다.
* **발화 여부 게이팅은 오직 `benchmark_status`로** 한다. `confidence_level`/`is_provisional`은 경고에 함께 실어 보내는 표시용 메타일 뿐, 발화/침묵 결정에 쓰지 않는다.
* 국가 benchmark가 없을 때 global 평균으로 **조용히 대체하지 않는다.** 대체하더라도 `benchmark_status`와 사용된 fallback 계층을 반드시 반환한다.
* 임계 적용 계층 순서가 **운영자 `rule_configs` → country benchmarks → code defaults**인지 확인하고, 어긋나면 수정한다.

### 3-6. data-quality report ↔ 룰 침묵 교차 진단
* 침묵 중인 KPI의 사유를 구분해 노출: `'benchmark_missing'`(기준값 없음) vs `'no_data'`(실데이터 없음) vs `'coverage_low'`(집계일수/표본 부족).
* "경고가 안 뜨는 게 정상인지 파이프라인이 끊긴 건지"를 구분 가능하게 한다.

### 3-7. 테스트 추가
* `direction='lower_better'` KPI(NPD 등)가 값이 높을 때 경고, 낮을 때 침묵하는지
* `direction='higher_better'` KPI(PSY 등)가 값이 낮을 때 경고, 높을 때 침묵하는지
* `benchmark_status='missing'`일 때 룰이 침묵하고 사유가 `'benchmark_missing'`인지
* 임의 수치가 코드/시드에 들어가 있지 않은지 (**전 KPI 기본 NULL/missing 검증**)
* `definition_id` 불일치 시 외부값 비교가 차단되는지
* 임계 계층 순서(`rule_configs` → country → code default)
* 단위 불일치 시 비교 전 변환이 적용되는지(kg↔lb)

---

## 4. 검증 후 남길 질문 (코드가 임의 결정하지 말 것)

* KR 전용 6종 KPI가 '발화 룰'인지 '데이터 출처(한돈팜스)'인지. 발화 룰이면 글로벌 엔진에서 분리 대상(PigOS는 한국 내수 제외).
* validator 모듈이 7개인지 8개인지. 8번째가 있으면 무엇인지.
* `production_system` / `farm_size_band`를 MVP 이후 어느 시점에 세분화할지.
* benchmark의 **이력/버전 관리**(연도별 갱신 시 `valid_from`/version)가 필요한지 — 감사 로그 요건과 연계. MVP 구조에 컬럼만 둘지, 후속으로 미룰지.
* 출시 시점에 **앵커 마켓 verified 시드**가 필요한지, 아니면 전 국가 침묵 상태로 출시할지.

---

## 5. 출력

* 수정/생성 파일 목록
* 추가된 benchmark schema (DDL 또는 seed 구조)
* `docs/KPI_DEFINITIONS.md` 내용 요약
* `direction` 분류표 (higher_better / lower_better)
* 테스트 PASS/FAIL/SKIP 표
* `benchmark_status`가 전부 `missing`으로 시작하는지 확인 결과
* 남은 결정 질문 (§4 + 새로 발견된 것)
* 기존 동작을 깬 변경이 있으면 별도 표기
