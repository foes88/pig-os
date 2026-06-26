# PigOS KPI 정의서 (KPI_DEFINITIONS)

> 목적: KPI **계산식(정의)** 과 국가별 **benchmark 수치** 를 분리한다.
> 이 문서는 **정의·방향성·단위**만 확정한다. **벤치마크 수치(mean·percentile·target·threshold)는 여기에 절대 적지 않는다.**
> 검증된 수치는 별도 시드 단계에서 `kpi_benchmarks` 테이블에 `benchmark_status='verified'`로 주입한다.
> 작성: 2026-06-24. 변경 시 이 문서 = 단일 소스. 코드/시드는 이 정의를 따른다.

---

## 0. 원칙

- **로직(룰)은 국가 중립 1벌**, **수치(임계·벤치마크)만 국가별로 조정**한다.
- **방향성(direction)** 은 정의의 일부다(수치 아님) → 이 문서와 스키마에 NOT NULL로 명시한다.
- **definition_id** 는 "어떤 정의로 계산된 값인지"를 식별한다. 외부 벤치마크의 정의가 PigOS와 다르면 재정규화 없이는 비교 금지(§4).
- 수치 자리는 전부 **NULL + benchmark_status='missing'** 으로 시작한다.

---

## 1. KPI 정의표

| kpi_code | 한글명 | 분자(numerator) | 분모(denominator) | 단위 | direction | definition_id |
|---|---|---|---|---|---|---|
| `PSY` | 모돈당 연간 이유두수 | Σ 이유두수(rolling 12m) | 평균 모돈 사육두수 | head/sow/yr | higher_better | `pigos.psy.v1` |
| `MSY` | 모돈당 연간 출하두수 | Σ 출하두수(rolling 12m) | 평균 모돈 사육두수 | head/sow/yr | higher_better | `pigos.msy.v1` |
| `farrowing_rate` | 분만율 | 분만 복수 | 교배(서비스) 복수 | % | higher_better | `pigos.frate.v1` |
| `prewean_mortality` | 포유기 폐사율 | 이유전 자돈 폐사수 | 생시 실산자(born_alive) | % | **lower_better** | `pigos.preweanmort.v1` |
| `postwean_mortality` | 이유후 폐사율 | 이유후~출하 폐사수 | 이유두수(+전입) | % | **lower_better** | `pigos.postweanmort.v1` |
| `sow_turnover` | 모돈 교체율 | 도폐사 모돈수(rolling 12m) | 평균 모돈 사육두수 | % | ⚠️ **결정필요**(§5) | `pigos.sowturnover.v1` |
| `NPD` | 비생산일수 | 비생산일 합(이유~재교배 등) | (모돈·기간 합, 연환산) | days | **lower_better** | `pigos.npd.v1` |
| `stillbirth_rate` | 사산율(PigOS 정의) | **stillborn + mummified** | total_born | % | **lower_better** | `pigos.stillbirth.v1` |
| `WSI` | 이유-재교배 간격 | 이유~재교배 일수 합 | 해당 모돈수 | days | **lower_better** | `pigos.wsi.v1` |

> 위 표의 `definition_id`는 "PigOS 내부 정의 v1" 식별자다. 외부 벤치마크 행은 자신의 정의를 별도 `definition_id`로 갖고, PigOS 정의와 다르면 §4 재정규화 규칙을 적용한다.

### 1-1. direction 분류표

| higher_better (낮을 때 발화) | lower_better (높을 때 발화) | 결정필요 |
|---|---|---|
| PSY · MSY · farrowing_rate | prewean_mortality · postwean_mortality · NPD · stillbirth_rate · WSI | sow_turnover |

- `higher_better`: 값이 `warning_threshold` **이하**면 WARNING, `critical_threshold` **이하**면 CRITICAL.
- `lower_better`: 값이 `warning_threshold` **이상**이면 WARNING, `critical_threshold` **이상**이면 CRITICAL.
- 단일 임계 + direction 모델. (warning_min/max·critical_min/max 4컬럼을 쓰지 않는다.)

---

## 2. PigOS 내부 정의 ↔ 업계 컨벤션 차이 (★ 비교 주의)

### 2-1. `stillbirth_rate` — ★ 약 3%p 높음 (직접 비교 금지)
- **PigOS 정의**: `(stillborn + mummified) / total_born`.
- **업계 컨벤션**: 대개 `stillborn / total_born` (미라(mummified) 별도 집계).
- 따라서 PigOS 사산율은 업계 수치보다 **미라 비율만큼(통상 ~2~3%p) 높게** 나온다.
- **결론: 외부 사산율 벤치마크를 PigOS stillbirth_rate에 그대로 시드하면 안 된다.** §4 재정규화가 가능할 때만(=출처가 stillborn/mummified를 분리 제공) 변환 후 시드. 분리 불가 출처는 `missing` 유지.

### 2-2. `prewean_mortality` 분모
- PigOS: `born_alive` 기준. 일부 외부 출처는 `total_born` 또는 `nursing_head`(양자 후) 기준 → 분모 다르면 재정규화 필요(§4).

### 2-3. `PSY` / `MSY` 분모(평균 모돈 사육두수)
- 평균 재고 산정 방식(일별 평균 vs 기말 vs (기초+기말)/2)에 따라 값이 달라진다. 외부 출처의 분모 정의가 다르면 definition_id로 구분, 재정규화 가능 시에만 비교.

### 2-4. `farrowing_rate` 분모(서비스 정의)
- 분모가 "첫 교배만" vs "모든 교배(재교배 포함)"인지에 따라 다르다. PigOS 정의(`pigos.frate.v1`)는 [분모 정의 — 코드 확정 후 본 문서 갱신]. 외부 출처와 분모 정의 다르면 재정규화.

---

## 3. 단위·집계 표기

- 비율 KPI(farrowing_rate, *_mortality, stillbirth_rate, sow_turnover)는 **percent(0~100)** 로 저장·비교한다.
- 일수 KPI(NPD, WSI)는 **days**.
- 두수/연 KPI(PSY, MSY)는 **head/sow/year**.
- 스키마 `unit` 컬럼에 단위 코드를 명시한다(혼동 방지).

---

## 4. 외부 벤치마크 재정규화 규칙 (시드 가능 판단)

외부 출처 수치를 `kpi_benchmarks`에 넣을 때:

1. **definition_id 일치**: 출처의 분자/분모 정의가 PigOS와 동일하면 그대로 시드(status='verified', confidence_level은 출처 신뢰도).
2. **재정규화 가능**: 정의가 다르지만 **출처가 변환에 필요한 구성요소를 분리 제공**하면, 변환 후 시드한다. 예: 출처가 stillborn·mummified를 분리 제공 → `(stillborn+mummified)/total_born`로 재계산해 PigOS 정의에 맞춤. `notes`에 변환 내역 기록.
3. **재정규화 불가 → missing 유지**: 출처가 합산만 제공하고 분리 불가하면(예: "사산"이 stillborn/mummified 미분리), 해당 KPI는 **provisional로도 넣지 않고 `missing`** 으로 둔다. 추정·역산으로 채우지 않는다.
4. **추정 금지**: 인터넷 검색·"일반적으로 알려진 값"·다른 국가값 복사로 채우지 않는다. 출처·연도·URL 없는 값은 시드하지 않는다.

> 판단 기준 한 줄: **"이 수치를 PigOS 정의로 정확히 환산할 수 있는가?" 예 → verified/provisional, 아니오 → missing.**

---

## 5. 미해결 결정사항 (코드가 임의 결정하지 않음)

- **sow_turnover direction**: 단일 임계+direction 모델은 교체율에 부적합(과교체=비용↑, 과소교체=노령화 둘 다 위험). 단일 방향 강제 시 어느 쪽? 또는 target-range 모델 별도 도입? → **결정 필요.** (스키마엔 일단 행을 넣되 numeric 전부 NULL·status='missing'·notes에 본 한계 명시.)
- **farrowing_rate 분모 정의**: 첫 교배만 vs 전체 교배 — 코드 확정 후 §2-4 갱신.
- **KR 전용 KPI 6종 / ko 로케일**: 한돈팜스 등 KR 데이터는 "발화 룰"이 아니라 "데이터 출처"인지, ko는 관리자 전용 로케일인지 → 별도 결정(본 작업 산출물의 결정질문 참조).
