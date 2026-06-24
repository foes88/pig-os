# 국가별 KPI 적용 감사 + 결정 필요 체크리스트 (2026-06-24)

> 목적: Rule Engine 40종이 **5개 시장(US/CN/SEA[VN·TH]/LatAm[BR·es]/KR)마다 올바른 KPI 임계로 작동**하는지 전수 점검.
> **이 문서는 "무엇을 정해야 하는지" 정리** — 실제 국가별 수치는 사람이 출처 확보 후 결정/시드(위조 0).
> 작동 구조: 임계 = `rule_configs`(운영자) → `default_metric_values`(국가 region scope) → 코드 기본값. region 행 없으면 system → 코드기본으로 폴백.

---

## 1. 현재 커버리지 매트릭스 (rule KPI × 국가)

범례: ✅ 국가값(sourced) · ⚙️ system/글로벌 기본 폴백 · ⌨️ 코드기본만(시드 0) · ❌ 없음(룰 미발화)

| KPI (룰) | KR | US | BR | CN | VN | **TH** | 비고 |
|---|---|---|---|---|---|---|---|
| PSY | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | TH만 글로벌 |
| NPD | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | ⚠️평균>warn 이슈(아래 Q3) |
| FARROWING_RATE | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | |
| WSI | ✅ | ✅ | ✅ | ⚙️ | ✅ | ⚙️ | CN·TH 글로벌 |
| RTS_RATE | ✅ | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | KR·US만 |
| ABORTION_RATE | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| PRE_WEANING_MORTALITY(PWMR) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | |
| STILLBORN_RATE | ✅ | ✅ | ✅ | ⚙️ | ⚙️ | ⚙️ | CN·VN·TH 글로벌 |
| BORN_ALIVE | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | |
| WEANED_COUNT | ✅ | ✅ | ✅ | ✅ | ✅ | ⚙️ | |
| WEANING_WEIGHT | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| WEANING_AGE_LOW | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| WEANING_AGE_HIGH | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | 국가행 0(system만) |
| CULLING_RATE | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| SOW_MORTALITY | ✅ | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | KR·US만 |
| HIGH_PARITY_RATIO | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| FCR | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만** |
| MSY | ✅ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | **KR만**, BEP 17(아래 Q8) |
| MUMMIFIED_RATE / TOTAL_BORN / BIRTH_WEIGHT / ADG / FINISH_MORTALITY | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | ⚙️ | 전부 system 글로벌(국가행 0) |
| **REPLACEMENT_RATE · SECOND_LITTER_DROP · ACCIDENT_P1_RATIO · SUMMER_FARROW_DROP · CONCEPTION_RATE · CRUSHING_RATE · DEATH_AGE_0_3_RATIO · BOAR_FARROW_RATE · BATCH_DOW_CONCENTRATION** | ⌨️ | ⌨️ | ⌨️ | ⌨️ | ⌨️ | ⌨️ | **시드 0 — 코드기본값만**(9종) |
| SOW 잔여가치(loss.sow_culling) | ✅(₩) | ❌ | ❌ | ❌ | ❌ | ❌ | KR만 → 타국 loss 미발화 |
| MARKET_PRICE_HEAD(손실단가) | ✅실 | ✅실 | ⚠️추정 | ⚠️추정 | ⚠️추정 | ❌ | TH 없음→TH 손실 미발화 |

---

## 2. 손실계산 단가 현황 (per-country)
| 국가 | 단가 | 통화 | 신뢰 | 출처 |
|---|---|---|---|---|
| KR | 450,000 | KRW | 실 | 축산물품질평가원 경락가 2025 |
| US | 210 | USD | 실 | USDA lean hog 2024 |
| BR | 700 | BRL | 추정 | ABCS 시세추정 2024 |
| CN | 1,500 | CNY | 추정 | 중국 시세추정 2025 |
| VN | 5,000,000 | VND | 추정 | 베트남 시세추정 2024 |
| **TH** | **없음** | — | — | **→ TH 손실룰(loss.*) 전부 미발화** |

---

## 3. 검증 발견 — 애매한 점 / 결정 질문 (핵심)

- **Q1. TH(태국) benchmark 0행** — SEA 타겟인데 모두 글로벌. 어떻게? ① 태국 양돈 출처 확보(태국양돈협회/Thai study) ② SEA 지역 프록시(VN 기반, is_proxy 표기) 허용? ③ 일단 글로벌 유지?
- **Q2. LatAm 스페인어권 국가코드 미지원** — 현재 LatAm은 BR(포르투갈)만. 멕시코·아르헨티나 등 es farm은 글로벌 폴백. 어느 국가코드를 시장으로 잡나(MX? AR? CL?) — 각자 값 필요? or BR/지역 프록시?
- **Q3. NPD 임계 vs 전국평균 역전** — BR(avg48/warn42)·CN(52/45)·VN(54/45)·US(44/38)는 **평균 농가가 이미 warning 구간**. KR만 정상(avg31<warn35). 의도(공격적 개선유도)인가, 재보정(warn을 평균 위로) 필요한가? **5개국 NPD 임계 재확정 필요.**
- **Q4. KR 전용 6종**(CULLING·FCR·MSY·ABORTION·WEANING_WEIGHT·HIGH_PARITY) — 타국은 글로벌 기본. US/BR/CN/VN/TH **국가값 출처 필요?** or 글로벌 기본으로 충분?
- **Q5. 코드기본값만 9종**(REPLACEMENT·SECOND_LITTER·ACCIDENT_P1·SUMMER_DROP·CONCEPTION·CRUSHING·DEATH_AGE·BOAR·BATCH) — 대부분 **생물학적 보편값**이라 국가차등 불필요로 보임. 단 CONCEPTION/REPLACEMENT는 국가차 가능 → 차등 필요 여부 결정.
- **Q6. SOW 잔여가치(조기도태 손실)** — KR(₩, S2_SOW_RETIREMENT)만. 타국은 **통화·산차별 잔존가 테이블** 없어 loss.sow_culling 미발화. 시장별 잔여가치 확보 필요(우선순위?).
- **Q7. 손실단가** — TH 없음(추가 필요), BR/CN/VN은 "추정" → **실시세 확정** 필요(손실금액 정확도 직결).
- **Q8. MSY 손익분기(BEP)** — 현재 17.0(글로벌). 국가별 BEP 다름(US/덴마크 더 높음). per-country BEP 필요?
- **Q9. WEANING_AGE_HIGH(이유일령 상한)** — 국가행 0. 이유일령 상한이 국가별로 다른가(EU 28일 규제 등)? 규제 연동 필요?
- **Q10. WSI/RTS/STILLBORN/SOW_MORTALITY 부분 커버** — CN·VN·TH 등 일부만. 나머지 sourced 필요 여부.

---

## 4. 나라별 "잡아야 할 것" 체크리스트 (사람이 값 확보 후 시드)

각 시장별 **출처 있는 실측치**를 채우면 1개 마이그레이션으로 주입(Phase A 방식). 우선순위 제안: ★ = 출시 직결.

**TH(태국) ★** — 전부(PSY·FARROWING_RATE·NPD·PWMR·BORN_ALIVE·WEANED_COUNT·WSI·STILLBORN) + **단가(THB)**. 최소 핵심 8종.
**US** — RTS는 있음. CULLING·FCR·MSY·ABORTION·WEANING_WEIGHT·HIGH_PARITY 국가값(있으면).
**BR** — STILLBORN 있음. RTS·SOW_MORTALITY + 위 KR전용군. **단가 실시세(BRL) 확정**.
**CN** — WSI·STILLBORN 추가 + KR전용군. **단가 실시세(CNY) 확정**.
**VN** — STILLBORN·RTS·SOW_MORTALITY + KR전용군. **단가 실시세(VND) 확정**.
**전 국가 공통** — NPD 임계 재확정(Q3), 코드기본 9종 국가차등 여부(Q5), SOW 잔여가치 타국(Q6).

> 값 확보되면: `api/alembic/versions/`에 Phase A 형식 마이그레이션 1개 추가(region scope, source_ref·is_proxy 표기) → `alembic upgrade head` → 즉시 적용. 코드 변경 0.

---

## 5. 검증 상태 (현재)
- **해석(resolve) 메커니즘 정상**: rule_config→benchmark(국가)→코드기본 우선순위 단위테스트(TestResolvePrecedence) + 라이브 6개국 resolve 확인(PSY/FARROWING/STILLBORN/CULLING/FCR 차등 적용 확인).
- **탐지 파이프라인 정상**: 실데이터→herd집계→룰탐지→알림(test_rule_detection_pipeline, CRITICAL/RED 롤업).
- **갭**: 위 매트릭스의 ⚙️/⌨️/❌ = 국가 실측치 미확보분. 메커니즘은 준비됨, **데이터만 채우면 됨.**
