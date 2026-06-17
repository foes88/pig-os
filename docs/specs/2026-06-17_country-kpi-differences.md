# 국가별 KPI 차등 지표 (R2)

> R1의 "④ 국가차등 Y" 41지표 중, **검증된 출처가 있는 항목만** 국가별 값으로 정리.
> 국가셋: **KR / US / CN / SEA / LatAm**. 본 MVP 시드 가용 프록시: **SEA→VN(베트남), LatAm→BR(브라질)**.
> 작성일 2026-06-17.

## 출처 규칙 (엄격 — 위반 시 빈칸)
- **KR** = PigPlan 실데이터(`전체농가_품종별_주요생산성적_2025.xlsx`, 전체농가 집계) + 한돈팜스 공개값 + PigPlan 확정 임계.
- **US** = PigCHAMP / PorkCheckoff(NPB) 공개 벤치마크.
- **LatAm(BR)** = Agriness 2024. **CN** = WEPIG 2025. **SEA(VN)** = Agriness VIE 표본(29농장, proxy·low confidence).
- 위 출처가 없는 칸은 **빈칸 + "출처 미확보"**. 절대 임의 생성하지 않음. 글로벌 폴백은 `default_metric_values` system scope.
- 기존 검증 시드: `api/alembic/versions/f3a7c2e9b5d1_seed_country_kpi_thresholds.py` (3자 대조), 근거 `docs/specs/2026-06-16_threshold-research-comparison.md`, `docs/reference/pigplan-rules-extract.md`.
- **KR 2025 신규 실측**: 본 작업에서 xlsx 전체농가(n=456)로 단순 산출. 0값(데이터 없는 농가) 다수 포함되어 **중앙값(median)을 대표값**으로 인용(평균은 0-inflated). 원자료 `docs/specs/_pigplan_kr_means.txt`.

---

## 축 (a) 벤치마크 (benchmark_avg / top25 / target) — 검증 출처만

> 빈칸 = 출처 미확보. KR target/threshold는 PigPlan 확정, KR avg는 한돈팜스2023 또는 PigPlan2025(median, ★표시).

### PSY (두/모돈/년) — 국가차 가장 큼
| 국가 | avg | top25 | target | 출처 |
|------|-----|-------|--------|------|
| KR | 22.1 (한돈팜스23) · **24.73★**(PigPlan2025 median, n=456) | 28.0 | 24.0 | 한돈팜스2023 / PigPlan |
| US | 27.1 | 31.0 | 28.0 | PigCHAMP2024 |
| CN | 24.34 | 31.5 | 26.0 | WEPIG2025 |
| LatAm(BR) | 29.5 | 37.2 | 30.0 | Agriness2024 |
| SEA(VN) | 25.41 (proxy) | 33.5 | 24.0 | AgrinessVIE-sample(low) |

### 분만율 FARROWING_RATE (%)
| 국가 | avg | target | warn | crit | 출처 |
|------|-----|--------|------|------|------|
| KR | **83.19★**(PigPlan2025 median) | 85.0 | 83.0 | 78.0 | PigPlan / PigPlan2025 |
| US | 83.8 | 85.0 | 82.0 | 78.0 | PorkCheckoff2024 |
| CN | 83.26 | 85.0 | 82.0 | 78.0 | WEPIG2025 |
| LatAm(BR) | _출처 미확보_ | | | | (시드에 BR FR 없음) |
| SEA(VN) | _출처 미확보_ | | | | |

### 평균실산 BORN_ALIVE (두/복)
| 국가 | avg | top25 | target | 출처 |
|------|-----|-------|--------|------|
| KR | 11.35 (한돈팜스) · **12.22★**(PigPlan2025 median) | — | 12.0 | 한돈팜스2023 / PigPlan2025 |
| US | 13.94 | 15.2 | 15.0 | PorkCheckoff2024 |
| CN | 12.19 (proxy) | 15.1 | 14.0 | WEPIG2025 |
| LatAm(BR) | 13.87 | 15.56 | 15.0 | Agriness2024 |
| SEA(VN) | 11.75 (proxy) | 14.6 | 12.0 | AgrinessVIE-sample |

### 평균이유두수 WEANED_COUNT (두/복)
| 국가 | avg | top25 | target | 출처 |
|------|-----|-------|--------|------|
| KR | 10.37 (한돈팜스) · **10.85★**(PigPlan2025 median) | 11.6 | 11.0 | 한돈팜스2023 / PigPlan2025 |
| US | 11.61 | 13.0 | 14.0 | PorkCheckoff2024 |
| CN | 11.25 | 13.5 | 12.0 | WEPIG2025 |
| LatAm(BR) | 12.57 | 14.85 | 14.0 | Agriness2024 |
| SEA(VN) | 11.13 (proxy) | 13.5 | 11.0 | AgrinessVIE-sample |

### 이유전폐사율 PRE_WEANING_MORTALITY (%)
| 국가 | avg | top25 | target | 출처 |
|------|-----|-------|--------|------|
| KR | 10.0 | — | 8.0 | 한돈팜스2023 |
| US | 14.6 | 9.85 | 10.0 | PorkCheckoff2024 |
| CN | 8.89 | 4.13 | 8.0 | WEPIG2025 |
| LatAm(BR) | 9.0 | 4.73 | 10.0 | Agriness2024 |
| SEA(VN) | 6.1 (proxy/ThaiStudy2018) | — | 10.0 | proxy(low) |

### 재귀발정 WSI (일)
| 국가 | avg | target | warn | crit | 출처 |
|------|-----|--------|------|------|------|
| KR | 6.9 · **6.30★**(PigPlan2025 median) | 7.0 | 7.0 | 10.0 | PigPlan-140008 / PigPlan2025 |
| US | 6.7 | 5.5 | 7.0 | 9.0 | PorkCheckoff2024 |
| CN | _출처 미확보_ | | | | |
| LatAm(BR) | 6.3 | 5.5 | 7.0 | 10.0 | Agriness2024 |
| SEA(VN) | 7.99 (proxy) | 5.5 | 7.0 | 10.0 | AgrinessVIE-sample |

### 재발교배비율 RTS_RATE (%)
| 국가 | target | warn | crit | 출처 |
|------|--------|------|------|------|
| KR | 5.0 | 5.0 | 12.0 | PigPlan-TAB_THRESHOLDS |
| US | 5.0 | 10.0 | 15.0 | PigCHAMP2023 |
| CN/BR/VN | _출처 미확보_ | | | |

### 사산율 STILLBORN_RATE (%)
| 국가 | avg | top25 | target | warn | crit | 출처 |
|------|-----|-------|--------|------|------|------|
| US | 8.0 | 5.7 | 6.0 | 8.0 | 12.0 | PigCHAMP2023 |
| LatAm(BR) | 8.19 | 7.41 | 6.0 | 8.2 | 12.0 | Agriness2024 |
| KR/CN/VN | _출처 미확보_ | | | | | (KR 2025 사산율은 xlsx에 사산율 지표 존재 → R4에서 산출 검토) |

### 모돈도폐사율 SOW_MORTALITY (%)
| 국가 | avg | target | warn | crit | 출처 |
|------|-----|--------|------|------|------|
| US | 12.2 | 8.0 | 12.0 | 15.0 | PorkCheckoff2024 |
| KR | (PigPlan2025 모돈도폐사율 median 39.3% — **정의 상이 의심**, 도태+폐사+판매 누적률로 보임 → target/threshold용으로 직접 사용 금지, R4에서 정의 확정 후) | | | | PigPlan2025(정의확인 필요) |
| CN/BR/VN | _출처 미확보_ | | | | |

---

## 축 (b) 임계값(warning/critical) 차등
- 위 표의 warn/crit 열 참조. **방향(alert_direction)**: below형(PSY/BORN_ALIVE/WEANED/FARROWING_RATE), above형(WSI/RTS/PWMR/STILLBORN/SOW_MORTALITY).
- 국가별 warn/crit는 f3a7c2e9 시드에 검증 수록(US/KR/CN/BR/VN). 폴백은 글로벌(system) scope.

## 축 (c) 단위 차등
- `market_defaults.weight_unit`: **US = lb**, 그 외(KR/CN/VN/BR) = **kg**. 무게계 지표(생시체중·이유체중·출하체중·평균체중)는 US 표시 단위 lb 변환 필요.
- 가격단위/통화도 market_defaults(currency_code/pricing_unit)에서 시장별 상이 — 본 KPI 차등 범위 밖(가격 KPI는 본 146목록에 없음).
- 변환 규칙: 1 kg = 2.20462 lb. **저장은 kg(canonical), 표시만 시장 단위**(기존 정책과 동일). 임계값 비교는 동일 단위로.

## 축 (d) 정의 차등 (관습/규정 — 검증분만 명시)
- **이유일령(평균이유일령)**: KR PigPlan2025 median ≈ 24.6일. 시장별 관행 차이가 큼(미국 약 21일, EU는 복지규정상 최소 28일이 잘 알려진 기준이나 **EU는 본 5개 시장셋에 없음**). US/CN/VN/BR의 법정 최소 이유일령은 본 작업에서 **출처 미확보** → 빈칸. 정의가 다르면 PSY/PWMR 비교가 왜곡되므로 보고서에 "이유일령 기준" 병기 권장.
- **포유기간(평균복당포유기간)**: 이유일령과 연동(KR2025 median ≈ 24.6일). 동일하게 시장 규정 출처 미확보.
- **초교배일령(평균초교배일령)**: 후보돈 초교배 관습이 시장별로 다름(일반적으로 210~240일). 정량 출처 미확보 → 빈칸, R1에서 ③(데이터부족, sow.birth_date 필요)으로도 분류됨.
- **PSY vs MSY**: PSY=이유두수 기준(weaned/sow/yr), MSY=출하/판매 기준(sold/sow/yr). KR xlsx에 MSY 컬럼은 비어 있음(미집계) → KR MSY benchmark **출처 미확보**.
- **보정 21일령 체중**: 21일 보정식이 표준이나 시장별 보정계수 차이 가능 → 출처 미확보 + R1 ③.

---

## R4 시드 후보 (검증값만 — 그대로 INSERT 대상)
- 이미 `f3a7c2e9` 시드에 region scope로 적재된 9지표×최대5국은 **재시드 불필요**(존재).
- **신규 추가 후보(검증 출처 보유)**: KR 2025 실측 갱신값 — `PSY avg=24.73`, `FARROWING_RATE avg=83.19`, `BORN_ALIVE avg=12.22`, `WEANED_COUNT avg=10.85`, `WSI avg=6.30` (전부 PigPlan2025 median, scope=region/KR, confidence=high, source_ref=`PigPlan2025-xlsx`, benchmark_avg만 갱신·target/threshold는 기존 PigPlan 확정값 유지).
- **추가 금지(출처 미확보)**: CN/VN/BR의 FARROWING_RATE·RTS·WSI 일부, KR/CN/VN STILLBORN, 전 시장 MSY, 이유일령/포유기간/초교배일령 정의값 → 빈칸 유지.
- ⚠ 모돈도폐사율 KR median(39%)은 정의 불일치 의심 → 시드 제외(정의 확정 전).

## 비고 — 레퍼런스 xlsx의 "품종" 축 정정
- xlsx `품종명` 컬럼 실제값 = {교배, 분만, 이유, 번식주기, 농장회전율} → **품종(breed)이 아니라 보고서 섹션**임을 확인.
- 따라서 R3 "품종(breed)별 분해"는 이 레퍼런스가 아니라 **PigOS `sow.breed`** 기반으로 구현해야 함(레퍼런스는 지표 정의의 gold standard로만 사용).
