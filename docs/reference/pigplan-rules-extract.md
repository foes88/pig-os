# PigPlan 룰 엔진 추출 — PigOS 반영용 (2026-06-16)

> 출처: PigPlan TS_INS_AI_RULES (실운영, 한국). 사용자 DB 덤프 분석.
> ⚠ 핵심 발견: **PigPlan은 고정 warning/critical 임계값을 거의 안 쓴다.**

---

## 0. 가장 중요한 아키텍처 발견 — 임계값 철학

PigPlan의 경보 방식 = **고정 밴드 아님 → 전국 상위10% 농장 대비 상대비교**.
- `BENCHMARK/COMPARE_METHOD`: `top10_basis=PSY`, `default_compare=top10`, `percentile_threshold=0.1`, `min_farm_count=100`.
  거의 모든 KPI(분만율·실산·이유두수·폐사율·재귀율 등)를 **"전국 상위10% 평균과 비교"** 한다.
- 즉 "사산율 8%면 경고"가 아니라 "**전국 상위10% 농장 사산율 대비** 내 농장이 나쁜가"로 판정.
- 이건 내 비교분석 문서가 권고한 "운영 데이터 기반 재캘리브레이션"과 정확히 일치 → **PigPlan이 정공법**.

→ **PigOS 설계 함의**: default_metric_values에 이미 `benchmark_avg/benchmark_top25`가 있다.
  KR(및 데이터 쌓인 국가)은 **고정 임계 대신 top25(≈top10 프록시) 대비 상대판정**으로 갈 수 있다.
  고정 밴드는 데이터 없는 신규국 폴백으로만 유지.

---

## 1. PigPlan에서 직접 가져올 수 있는 구체값 (KR 시드)

`BENCHMARK/TAB_THRESHOLDS` + `GRADING` + `VALID_RANGES`에 박힌 실값:

| 항목 | 값 | PigOS 반영 |
|------|-----|-----------|
| **재발율(재교배)** | safe ≤5% / warn ≤12% | RTS_RATE warning=5, critical=12 (KR) ← 직접 시드 |
| **분만율 목표** | target 85%, max_gain 10% | FARROWING_RATE target=85 (KR) |
| **수태율(46일)** | excellent ≥85% / warn ≥70% | 신규 메트릭 후보 |
| **NPD(예정지연)** | npd_target_days=14 | 순수 NPD(입력지연 제외) 목표 |
| **임신기간 표준** | **114일** (normal 110~120) | PigOS 기본 114 확정 (이전 "115"는 오류) |
| **포유기간 KR** | 21~25일 (normal 14~50) | WEANING_AGE 밴드 KR 정렬 |
| **LSY 생물상한** | 2.66 (invalid >2.8) | 입력검증 참고 |
| **PSY 등급** | S/A≥28, B+ 25~28, B 22~25, C 그외 | PSY grade 확정(기존과 일치) |
| **THI 폭염** | severe 82 / moderate 78 / mild 72 | 계절보정(v2) |

> 입력검증 상한(총산35·사산25·체중3.0·양자25)은 이미 PigOS validators에 반영됨(일치 확인).

## 2. PigPlan의 진짜 차별점 = 다음 단계로 흡수할 3대 자산

### 2-1. LOSS_CALC — 두당/총 손실액 (경제효과) ★최고가치
인사이트에 "사산율 18% → **약 ₩X 손실**" 붙일 수 있음. 공식 확보:
- **모돈 도폐사**: residual_by_parity `0산=840만/1=710/2=580/3=450/4=330/5=195/6=80/7+=0`,
  교체비 150만, 잔존가치 도태30만·폐사0. **조기도태(≤3산) 방지가 핵심**.
- **임신사고**: 건수 × 지연일 × (PSY/365) × 육성율 × 출하단가.
- **자돈폐사**: 폐사두수 × 이유후육성율 × 출하단가.
- **출하등급**: Σ(두수×도체중×등급차단가), 1+기준 차액(1등급 120·2등급 350·D 800원/kg).
- **NPD**: 모돈일손실 = PSY×육성율×두당가격/365.

### 2-2. KPI_DRIVER_MAP + DIAGNOSIS — 원인·권고 (insight의 causes/actions)
- `DIAGNOSIS/KPI_DRIVER_MAP`: KPI마다 driver(원인 지표) + 공식 + weekly/monthly focus.
  예: 분만율 ← 재발교배비율·수태율 / 사산율 ← 평균총산·분만복수.
- `DIAGNOSIS/PSY_DRILLDOWN`: PSY 6-component 기여도 분해.
- `DIAGNOSIS/SEASONAL_DIAGNOSIS`: 여름>30°C 수태율↓/사산↑, 겨울 자돈동사 등.
- → 인사이트의 `causes` + `recommended_actions`에 직접 매핑.

### 2-3. DISEASE_IMPACT — 질병 근접 경보
- ASF/FMD/PED/PRRS 등 위험도·반경(km)·경보일·KPI영향·조치. 지오 기반 알림(별도 기능).

## 3. PigPlan에 "고정 임계로는" 없는 것 (top10 비교로 처리됨)
사산율·PWMR·생존산자·이유두수 warning/critical = **고정값 없음**. 전부 top10% 대비 상대판정.
→ PigOS는 (a) 데이터 있는 국가는 top25 대비 상대, (b) 없는 국가는 글로벌 고정밴드 폴백.

---

## 4. 결론 — PigOS 반영 계획
1. **KR 직접값 시드**: RTS_RATE 5/12, FARROWING_RATE target 85, gestation 114 정렬, 포유 21~25.
2. **상대판정 모드 추가**: benchmark_top25 있으면 "상위25% 대비 격차"로 severity (PigPlan식). 고정밴드는 폴백.
3. **(차별점) 인사이트 v2**: LOSS_CALC 손실액 + KPI_DRIVER_MAP 원인/권고 부착 → "PigPlan급" 인사이트.
4. **PSY/NPD grade**: GRADING 값으로 확정.
