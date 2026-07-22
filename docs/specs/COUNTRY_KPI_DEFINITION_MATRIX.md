# 국가별 KPI 산정 방식·정의 차이 매트릭스 (Phase B 준비)

> **목적**: KPI의 *값(벤치마크)*이 아니라 **계산 공식/정의/분모/포함규칙**이 국가별로 다른 지점을 정리.
> 값 차이는 `2026-06-17_country-kpi-differences.md`(축 a~c) 참조. 본 문서는 **축(d) 정의차등을 계산 레벨로 확장**.
>
> **현재 코드 상태(2026-07-22)**: PigOS는 전 지표를 **단일 SSOT 공식(KR/PigPlan 기준)**으로 계산.
> `kpi_convention_origin=KR` 고정. 국가별 공식 분기는 **미구현** — 본 매트릭스가 Phase B 착수 근거.
>
> **위조 0 규율**: '국가 관례' 칸은 **검증 출처 있는 것만** 기입. 없으면 `⬜ 출처미확보`.
> 임의 추정 금지. 출처 확보 후에만 코드 분기 or "외부 비교 무효" 표시로 반영.
>
> **범례**: 🟢 PigOS 현행 = 국가 관례와 동일(분기 불요) / 🟡 다름(분기 or 병기 필요) / ⬜ 관례 출처미확보 / ❌ 비교무효(정의상 대입 금지)

---

## A. 분모/모집단 차이 (가장 영향 큼)

### PSY (두/모돈/년)
| 항목 | PigOS 현행(SSOT) | KR PigPlan | US PigCHAMP | CN/BR/VN |
|---|---|---|---|---|
| 분자 | Σ이유두수(rolling 12mo) | 동일 | (확인필요) | ⬜ |
| 분모 | 평균 **상시모돈=경산(parity≥1)**, exit기반 | 상시모돈(035001) 🟢 | **female inventory**(후보 포함?) 🟡 | ⬜ |
| 리서치 | — | — | **PigCHAMP PSY 분모에 gilt 포함 여부·"mated female year" 여부** | 각국 분모 정의 |

> COUNTRY_KPI_RULE_SPEC §카드: "PSY 분모=상시모돈, **mated female 기준과 상이·외부 수치 대입 금지**" — 즉 이미 "분모가 달라 외부 PSY와 직접 비교 불가"로 규정됨. 국가별 PSY를 **각자 분모로 재계산**할지, 아니면 PigOS 분모로 통일하고 비교무효 표시할지 = Phase B 결정.

### 모돈회전율 (litters/sow/year)
| PigOS 현행 | KR PigPlan | 국가 관례 |
|---|---|---|
| 창내 분만복수 / 평균 상시모돈(경산) | **분만간격(FI) 기반 추정**(2807 대조서 count방식 2.29 vs PigPlan 2.42 = FI기반) 🟡 | US/BR: litters/mated female/yr (분모 상이) ⬜ |

> 2807 실측: count방식과 FI방식이 PigPlan을 사이에 두고 갈림. **PigPlan 035 회전율 정확 공식(FI 산정법) 출처 필요**.

### 비생산일수 NPD
| PigOS 현행 | KR PigPlan | US PigCHAMP |
|---|---|---|
| 여집합 `365×(사육일−임신일−포유일)/사육일` (herd) | ⬜ 035 공식 미확보(2807서 우리52.7 vs 표기30.4=관례차) 🟡 | NPD = Σ(non-productive days/female) 방식(분모·포함 상이) ⬜ |

> **리서치 최우선**: (1) PigPlan 035 비생산일수 정확 산식 (2) PigCHAMP NPD 정의(gilt entry~first service 포함 여부, cull 후 처리). 우리 여집합값은 self-consistent하나 관례 정확일치는 출처 필요. **역-피팅 금지**.

---

## B. 포함/제외 규칙 차이

### 분만율 FARROWING_RATE
| PigOS 현행 | 관례 차이 |
|---|---|
| 코호트 **초교배(mating_number=1)** 중 분만 성공%, 교배후115일 폐사 분모제외 (스펙§4) | US PigCHAMP: **farrowing rate = farrowings / services**(초교배 아닌 서비스 기준일 수 있음) 🟡 ⬜ / 재교배 포함 여부 국가차 |

### 사산율 STILLBORN_RATE
| PigOS 현행 | 관례 차이 |
|---|---|
| **(사산+미라)÷총산** (APPROVED SSOT) | US/BR 등 다수: **사산÷총산**(미라 별도) → ❌ **외부 비교 무효**(스펙§164 확정). 국가별 재계산 대신 비교무효 표시 유지 |

### 평균총산/실산 (BORN_ALIVE / TOTAL_BORN)
| PigOS 현행 | 관례 차이 |
|---|---|
| 총산=실산+사산+미라, 실산=silsan | 대부분 동일(총산 정의는 국제 표준) 🟢. 단 **미라 포함 여부**가 사산율과 연동 |

### 이유전폐사율 PWMR
| PigOS 현행 | 관례 차이 |
|---|---|
| (실산합−이유합)/실산합 | **양자(cross-foster) 보정** 처리 국가차 ⬜ / 분모를 nursing_head로 볼지 born_alive로 볼지 🟡 |

### 모돈도폐사율 SOW_MORTALITY
| PigOS 현행 | 관례 차이 |
|---|---|
| (미구현/정의확정 전) | ❌ KR PigPlan median 39% = **도태+폐사+판매 누적률 의심** → US 12.2%(사망만)와 정의 상이. **정의 확정 전 시드·비교 금지**(스펙§93·120) |

---

## C. 정의(관행/규정) 차이 — 비교 왜곡 요인

### 이유일령 / 포유기간 WEANING_AGE
| 국가 | 법정/관행 이유일령 | 출처 |
|---|---|---|
| KR | ≈24.6일(PigPlan2025 median) | PigPlan2025 |
| US | ≈21일 | (관행, 법정근거 ⬜) |
| EU | 최소 28일(복지규정) — **본 5개 시장셋 밖** | 알려진 기준 |
| CN/VN/BR | ⬜ 출처미확보 | — |

> **왜곡 경로**: 이유일령↓ → 포유기간↓ → NPD·회전율·PSY 모두 영향. 국가 비교 시 "이유일령 기준" 병기 필수(스펙§108). **US 21일 vs KR 24.6일 = 구조적 차이**, 값 정제 아니라 정의 병기로 해결.

### 초교배일령 GILT_FIRST_MATING_AGE
| PigOS 현행 | 관례 차이 |
|---|---|
| farm_config 기본 240일 | 국가별 목표 상이 ⬜ (품종·시장 관행) |

---

## D. 단위 차이 (반영됨 🟢)
- **US = lb**, 그 외 kg. 저장 kg(canonical), 표시만 변환(1kg=2.20462lb). 임계 비교는 동일 단위. (스펙 축c, 기존 구현)
- 통화/가격단위: market_defaults. KPI 차등 범위 밖.

---

## E. 리서치 체크리스트 (사용자 조사 → 출처 확보 시 채움)

> Claude/GPT 등으로 **각국 공식 정의의 1차 출처**(PigCHAMP Data Sharing Definitions, NPB PorkCheckoff, Agriness metodologia, WEPIG 지표정의)를 확보. 확보 전엔 빈칸 유지.

- [ ] **US PigCHAMP**: PSY 분모 정의(gilt 포함?), NPD 산식, farrowing rate 기준(service vs 초교배), 사산율(미라 포함?)
- [ ] **KR PigPlan**: 035 비생산일수 정확 산식, 회전율(FI 산정법), 모돈도폐사율 정의
- [ ] **LatAm Agriness**: PSY/NPD/사산율 metodologia, 이유일령 기준
- [ ] **CN WEPIG**: 지표 정의서(있으면)
- [ ] **SEA/VN**: 법정 최소 이유일령, 산정 관행
- [ ] 공통: 각국 **법정 최소 이유일령**, MSY의 "marketed" 정의(판매 vs 도축)

## F. Phase B 반영 원칙 (출처 확보 후)
1. **분모·포함규칙 차이**: 국가별 재계산 분기 or PigOS 분모 통일 + "외부 비교 무효" 표시 — 지표별 결정.
2. **정의 차이(이유일령 등)**: 값 조작 금지, **리포트에 기준 병기**.
3. **비교무효 지표(사산율·모돈도폐사율)**: 산식 유지, 외부 벤치마크 대입 차단(fail-closed).
4. 모든 국가별 산식은 **Decision Register 승인 + 출처 병기** 후 코드 반영. 미승인 = seed·코드 금지.
