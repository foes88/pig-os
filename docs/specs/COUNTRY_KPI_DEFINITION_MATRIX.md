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

## ★ 연구 검증 결과 (deep-research 2026-07-22, 21소스·25클레임·23확정)

> 1차/권위 출처로 검증된 findings. 신뢰도·투표·출처 병기. **미확인 항목은 빈칸 유지(위조0)**.

**V1. NPD 여집합 정의 = 정식 (우리 구현 검증됨)** [high, 3-0]
- `NPD = 365 − [litters/female/yr × (임신일+포유일)]` — 미국 PorkGateway(USPCE)와 한국 NIAS(김두완, 정부) **양쪽이 동일 정의**. "모돈/도입 후보돈이 임신도 포유도 아닌 모든 날."
- 출처: porkgateway.org(비생산일수), nias.go.kr(모돈회전율·비생산일수 PDF), pig333.
- **함의**: 우리 `calculate_npd` 여집합 방식은 **국제 표준 정의와 일치**. 2807의 52.7은 공식 오류가 아님.

**V2. NPD는 후보돈 비생산일·재발·도태 종료구간 포함** [high, 3-0]
- 'Gilt Specific NPD'(도입→초교배), 이유→교배, 교배후 재발/불임, 도태/폐사 종료구간 전부 포함(Koketsu 6구간).
- ⚠️ **경계 관례차**: PorkGateway=**후보돈 도입**부터 / Koketsu(mated inventory)=**초교배**부터. 우리 현행은 parity≥1(경산)만 → **후보돈 NPD 미포함**. 관례 선택 필요.
- 출처: porkgateway.org, nias.go.kr, Koketsu J Anim Sci 2005(PubMed 15890819).

**V3. 회전율 2정의 공존 — 우리 것 = US 정의, PigPlan = KR 정의** [high, 3-0/2-1]
- **US NPPC/SMS**: `연간 분만수 ÷ 평균 교배모돈(mated female) 재고` = 기록 기반. ← **우리 count방식과 동종**.
- **KR NIAS**: `모돈회전율 = (365 − 비생산일수)/(임신기간+포유기간)` = NPD 항등식. ← **PigPlan이 쓰는 방식**.
- **결정적**: PigPlan NPD 30.4 ⟺ 회전율 2.42가 이 항등식으로 정확히 맞물림: (365−30.4)/138.7=**2.41** ✓. 우리 52.7 ⟺ 2.25. **즉 NPD와 회전율 격차는 하나의 관례차**(per-cycle vs herd-inventory).
- 출처: nationalhogfarmer.com(NPPC/SMS), nias.go.kr, pignpork/pigpeople.

**V4. PSY 분모 = 교배모돈(mated female), 미교배 후보 제외** [high, 3-0]
- US NPPC/SMS: `연간 이유두수 ÷ 평균 교배모돈 재고`. 후보돈은 **초교배 시점에 분모 진입**. "per mated female"로 후보 변동성 제외.
- ⚠️ 우리 현행 분모 = **parity≥1(초산 이상)** — 교배후~초분만 전 임신 후보는 제외. **US는 교배시점 포함** → 미묘한 분모차. 단 PigPlan 상시모돈과는 실측 정합(PSY 29.0≈29.1).
- 출처: nationalhogfarmer.com. **CAVEAT: PigCHAMP 자체 문서·PigPlan 상시모돈 1차정의 미확인**.

**V5. 모돈도폐사율 = 사망만(≠removal) — 우리 스펙 의심 확정** [high, 3-0]
- 사망률(mortality) = 폐사(안락사/자연사) ÷ 평균재고 ≈ 12~14%. **제거율(removal) = 도태(도축)+폐사 ≈ 40~48%**. KR 39%는 removal(누적) → US 12%(사망)와 **정의 상이, 직접비교 무효**.
- 출처: UMN SHMP(PigCHAMP 데이터), Heinonen PMC6540429.

**V6. 분만율 — Agriness=예정일 기준, "farrowings/sows-mated"·"초교배only"는 반증됨** [high, 3-0 / 반증 1-2·0-3]
- Agriness: 해당기간 **예정분만일(due date)** 모돈 중 분만%. adjusted rate는 임신중 폐사·비번식 도태를 분모 제외.
- pig333의 "분만수/교배모돈"·"초교배 기준"은 **검증에서 반증(encode 금지)**. 우리 현행(초교배 코호트)도 이 관례와 다름 → 재검토 대상.
- 출처: ajuda.agriness.com.

**V7. 최소 이유일령 — EU만 확정(28일, 특수사육 21일)** [high, 3-0]
- EU Directive 2008/120/EC: 최소 28일(모/자돈 복지 예외 시 21일, 별도 세척 사육시설 이동 조건).
- **US/KR/CN/VN/BR 법정 최소 이유일령은 1차출처 미확보 → 빈칸**. (관행: US~21, KR~24.6 median은 관행이지 법정 아님)
- 출처: eur-lex.europa.eu.

**미확인 → 빈칸 유지(추정 금지)**: PigCHAMP PSY 분모 자체문서 · PigPlan 상시모돈/035 1차 스펙 · **사산율(미라 포함 여부, Q4 — 클레임 0)** · **MSY(Q8 — 클레임 0)** · China WEPIG 전체 · US/KR/CN/VN/BR 법정 이유일령.

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

- [x] **NPD 정의** — 여집합=국제표준 확정(V1), 우리 구현 검증됨. 후보돈/초교배 경계만 선택(V2).
- [x] **회전율 2정의** — US 기록기반 vs KR NPD항등식 확정(V3). PigPlan=KR 방식.
- [x] **PSY 분모** — US=교배모돈 확정(V4). 단 PigCHAMP 자체문서·PigPlan 상시모돈 1차정의 **미확인**.
- [x] **모돈도폐사율** — 사망≠removal 확정(V5). KR 39%=removal.
- [x] **분만율** — Agriness=예정일 기준(V6). pig333 초교배설 반증.
- [x] **이유일령** — EU 28일 확정(V7). 나머지 국가 법정치 **미확보**.
- [ ] **US PigCHAMP 1차문서**: 자체 PSY 분모 명문(gilt 포함?) — 미확보
- [ ] **KR PigPlan 035 1차 스펙**: 상시모돈·비생산일수 정확 정의 문서 — 미확보(현재 실측 정합으로 역추정만)
- [ ] **사산율(Q4)**: 미라 포함 여부 — **클레임 0, 완전 미확보**
- [ ] **MSY(Q8)**: "marketed" 정의·분모 — **클레임 0, 완전 미확보**
- [ ] **China WEPIG**: 지표 정의서 전체 — 미확보
- [ ] **법정 최소 이유일령**: US/KR/CN/VN/BR — EU만 확보

> 사용자님 Claude/GPT 조사는 **미확보 항목**(PigCHAMP/PigPlan 1차문서, 사산율, MSY, WEPIG, 각국 이유일령)에 집중하면 교차검증 효율적. deep-research 결과와 대조해 출처 확정.

## F. Phase B 반영 원칙 (출처 확보 후)
1. **분모·포함규칙 차이**: 국가별 재계산 분기 or PigOS 분모 통일 + "외부 비교 무효" 표시 — 지표별 결정.
2. **정의 차이(이유일령 등)**: 값 조작 금지, **리포트에 기준 병기**.
3. **비교무효 지표(사산율·모돈도폐사율)**: 산식 유지, 외부 벤치마크 대입 차단(fail-closed).
4. 모든 국가별 산식은 **Decision Register 승인 + 출처 병기** 후 코드 반영. 미승인 = seed·코드 금지.
