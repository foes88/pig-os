# 작업 — Rule Engine ↔ 3-table Benchmark 연결 (토대 완료 + STOP 보고)

> 기준: handoff/KPI_GOVERNANCE_v3.1.md / "Rule Engine ↔ 3-table 연결" 프롬프트
> 실행일 2026-06-25, dev 전용. 운영 미반영. git push 안 함.

## §0 게이트 — 보고사항 2건
1. **head 불일치**: 프롬프트 가정 `c5e7a9b1d3f0` ≠ 현재 `e1a3c5d7f9b2`. 원인 = 그 사이 **작업 C(KR verified)·US 적재** 완료(우리 커밋). 악성 아님, 더 진전된 상태. → 현재 head에서 진행.
2. **verified에 임계 부재**: verified/normalized 10개 전부 transformed_value(국가 평균)만 있고 warning/critical NULL.

## 완료 (동작변화 0 — flag OFF)
- `services/benchmark_service.py` **resolve_benchmark()**: §4 발화게이트(benchmark_status∈verified류 + comparison∈{exact,compatible,normalized} + value_scale 일치 + direction별 threshold 유효) + §3.1 임계해석 + §4.2 global_fallback + §7 trace + insufficient_reason.
- `USE_GOVERNANCE_BENCHMARKS` flag (config, 기본 **False** = 현행 default_metric_values 경로). True 전환 = governance 전용(metric-level fallback 금지).
- 읽기전용 admin API `/admin/governance/*` (kpi-definitions·benchmarks·resolve, super_admin).
- 테스트 +13 (게이트 전 분기·can_fire·global_fallback·range 4-bound·trace 필드), **전체 555 passed**.

## §10 before/after 실측 (dev, governance 조회 시)
**발화 적격 0 / 18 (전부 차단)**:
| 사유 | 건수 |
|---|---|
| threshold_missing (verified/normalized — 임계 없음) | 11 |
| benchmark_status=provisional | 6 |
| value_scale_mismatch (US psy=missing) | 1 |

→ **§10.1 중단 기준에 설계대로 걸림**(provisional 발화 금지 + verified 임계 부재). 절대중단(설계위반 발화) 0건. **엔진 default 전환은 보류.**

## 🔑 결정 필요 — 임계 정책 (이게 진짜 블로커)
verified benchmark는 **검증된 국가 평균**만 있고 **알림 임계(warning/critical)가 없다.** 1차자료(한돈팜스/PigCHAMP)도 평균만 주지 임계는 안 줌. 발화하려면 임계가 어디선가 와야 함:

| 옵션 | 내용 | 평가 |
|---|---|---|
| **A. rule_configs(운영자) 임계 + governance=평균/맥락** (권장) | 발화 임계는 기존 운영자 rule_configs→code default가 권위. governance verified는 "검증된 국가 평균"을 비교·표시·맥락으로 결합. verified가 즉시 유의미(평균 대비 위치), 발화는 안전. §5 위반 아님(default_metric_values metric fallback이 아니라 운영자 계층) | 안전·즉효 |
| B. 평균에서 임계 도출 | higher_better warning=mean×k 등 정책 | k 근거 약함, 위조성 |
| C. verified에 임계 별도 시드 | 1차자료에 임계 없음 → 위조 위험 | 비추 |

**권장 A**: 임계 권위=rule_configs/code default, governance benchmark=검증 평균(비교·표시·trace). 그러면 엔진을 governance로 연결해도 발화가 죽지 않고, verified 평균이 "국가 대비 우리 농장 위치"로 즉시 쓰임.

→ 이 결정 나면: resolver를 "임계는 rule_configs, 비교평균은 governance" 하이브리드로 확장 + 엔진 연결 + §10 diff 재측정.

## 남은(이번 범위 밖)
- 엔진 default 전환(flag ON 배선) — 임계정책 결정 후
- EU/GB(D-3) · BR/VN(1차자료) · 운영 배포(확인)
