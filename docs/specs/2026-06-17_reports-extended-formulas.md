# 보고서 확장 지표 공식 (R3)

> `2026-03-19_kpi-calculation-specs.md` 보완. R3에서 reports API에 추가한 지표 공식·경계.
> 구현: `api/app/services/report_service.py::build_reproduction_rows` (순수 빌더, unit test 동반).
> (기존 파일이 CP949 인코딩이라 한글 혼입 손상을 피해 별도 UTF-8 문서로 분리.)

## 그룹핑 (group_by)
- `period` (기본): 버킷 키 = `period_key(date, period)` (monthly=YYYY-MM, quarterly=YYYY-Q#, annual=YYYY).
- `breed`: 버킷 키 = sow.breed (None → "unknown"). 행의 `period` 필드에 품종 라벨이 들어감.
- 레퍼런스 xlsx의 '품종'축은 보고서 섹션이었으므로, 실제 품종 분해는 PigOS `sows.breed` 기준(R2 비고 참조).

## 신규 지표 공식 (분모 0 → None, fail-safe)
- `total_born_sum` = Σ total_born, `born_alive_sum` = Σ born_alive (버킷 합).
- `total_stillborn` = Σ stillborn, `total_mummified` = Σ mummified.
- `stillborn_rate(%)` = total_stillborn / total_born_sum × 100 (tb_sum>0, 소수1자리). tb_sum=0 → None.
- `mummified_rate(%)` = total_mummified / total_born_sum × 100.
- `birth_loss_rate(%)` = (total_stillborn + total_mummified) / total_born_sum × 100. (= 생시자돈사고율, R1 #90)
- `mating_1_count / mating_2_count / mating_3plus_count` = mating_number==1 / ==2 / ≥3 건수.
- `ai_count / natural_count` = mating_type∈{AI, NATURAL} 건수 (대문자 정규화 후 매칭).
- 기존 지표(fr/avg_tb/avg_ba/avg_weaned/avg_lactation_days/pwmr_a/pwmr_b/rts_rate) 공식·동작은 무변경(회귀 테스트 유지).

## 경계/엣지 (unit test로 잠금 — `tests/unit/test_report_service.py`)
- 확장 인자 미전달(기존 positional 호출) → 신규 카운트 0, 비율은 tb_sum 기준(0 또는 None). **기존 동작 무회귀**.
- tb_sum=0 → 모든 비율 None (분모 0 가드).
- group_by=breed + breed None → "unknown" 버킷.
- 병렬 리스트는 인덱스 paired; 길이 부족 시 안전 무시(`i < len(...)`).

## production-summary (benchmark 동봉)
- `GET /reports/production-summary?start&end&period&group_by` → `ProductionSummary` envelope.
- `benchmarks[]` = `threshold_service.list_effective(farm)` 해석값(농장>국가>글로벌)을 `benchmark_values_from_effective()`로 변환(target/avg/top25/warning/critical/direction/unit/source/confidence).
- **원칙**: 프론트는 행 값과 benchmark를 '비교'만(판정/등급 재구현 금지 — 기존 인사이트 원칙과 동일).
- country 기준값은 `default_metric_values` region scope(국가코드), 출처는 R2 문서/`f3a7c2e9` 시드.

## 미반영(③ 데이터부족 — R1 백로그)
- 생시체중·보정21일체중·재포유·분만4구분·후보돈사육일수 등은 스키마 확장 후 별도 작업(R1 ③ 26지표).
