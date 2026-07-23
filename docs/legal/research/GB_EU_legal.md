# PigOS 글로벌 — GB(영국) + EU 법무 리서치 초안

## 0. 문서 성격

> **본 문서는 변호사 검토 전 초안(pre-counsel draft)이다.** 사내 리서치 목적으로 작성되었으며, 법률 자문이 아니다. 모든 결론은 "요건·리스크·질의" 형태로 서술하였고, 적법/위법 단정을 하지 않는다. §9의 질의 목록에 대해 EU/UK 자격 변호사 확인 후 확정할 것.
>
> - **검토 기준일: 2026-07-21** (웹 확인 기준일 동일)
> - 대상: 와이즈레이크(한국 법인, 서버 한국)의 PigOS 글로벌 — EU 27개국 + 영국(GB)
> - 전제: 농장 데이터 중 (i) 개인사업자(sole trader) 농장주의 데이터 및 농장 직원·연락처 데이터는 GDPR상 개인정보, (ii) 법인 농장의 순수 운영 데이터(두수, 사료, 출하성적 등)는 그 자체로는 개인정보가 아닐 수 있으나, 자연인과 연결 가능한 한(담당자 계정, 소규모 농장의 사실상 1인 운영 등) 개인정보로 취급하는 것이 안전하다는 점

---

## 1. 적용 법제 (확인 결과 포함)

| 법제 | 핵심 조항 | 2026-07 기준 상태 / 확인 출처 |
|---|---|---|
| **EU GDPR** (Reg. (EU) 2016/679) | Art. 3(2), 5, 6, 9, 13–14, 17, 21, 25, 27, 28, 44–49, 89; Recital 26 | 시행 중. [EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj) |
| **UK GDPR + DPA 2018** | 위와 병렬 (UK GDPR Art. 3(2), 27 등) | 시행 중. **Data (Use and Access) Act 2025(DUAA)** 로 일부 개정(인정된 정당한 이익 목록 등) — EU는 2025-12 UK 적정성 **갱신** 결정 채택(즉 DUAA에도 불구 EU→UK 적정성 유지). [EC 적정성 목록](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en) |
| **한국에 대한 EU 적정성 결정** (Decision (EU) 2022/254) | 2021-12-17 채택 | **유효(in force)** — EC 공식 목록에 등재 확인. **1차 재심사(first review) 보고서는 미공표** (Japan 2023-04, US DPF 2024-10은 공표됨; Korea는 미확인 — 변호사 질의 §9-Q1). [EC](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en), [EC Q&A](https://ec.europa.eu/commission/presscorner/detail/en/qanda_21_6916) |
| **UK의 한국 적정성 규정** (The Data Protection (Adequacy) (Republic of Korea) Regulations 2022) | 2022-12-19 발효 | **유효** — 영국 최초의 독자 적정성("data bridge"). 철회·개정 정황 미발견. [legislation.gov.uk IA](https://www.legislation.gov.uk/ukia/2022/92/pdfs/ukia_20220092_en.pdf), [Securiti](https://securiti.ai/blog/uk-first-data-adequacy-decision-south-korea/), [BDO](https://www.bdo.co.uk/en-gb/insights/advisory/risk-and-advisory-services/adequacy-decision-with-south-korea) |
| **EDPB Guidelines 01/2025 (가명처리)** | 가명정보=개인정보 재확인, 안전조치 역할 | 2025-01-17 초안 채택, 공개의견수렴 2025-02-28 종료. **최종본 채택 여부 미확인 — 변호사 질의** (§9-Q2). [EDPB](https://www.edpb.europa.eu/our-work-tools/documents/public-consultations/2025/guidelines-012025-pseudonymisation_en), [EDPB 뉴스](https://www.edpb.europa.eu/news/news/2025/edpb-adopts-pseudonymisation-guidelines-and-paves-way-improve-cooperation_en) |
| **EDPB Guidelines 02/2026 (익명화)** ★신규 | WP29 Opinion 05/2014 대체 예정 | **2026-07-07 초안 채택, 공개의견수렴 2026-07-08 ~ 2026-10-30 진행 중.** 3대 누적 기준(개별화·연결·추론 불가) + "reasonably likely means" 상대적 접근 + **집계통계도 추론 위험 명시** + **익명화 행위 자체에 Art. 6 법적 근거 필요** 명시. [EDPB](https://www.edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en), [Freshfields 분석](https://www.freshfields.com/en/our-thinking/blogs/technology-quotient/anonymous-or-not-the-edpbs-new-draft-guidelines-on-anonymisation-102nbv5) |
| **ICO 익명화·가명화 지침(최종)** | motivated intruder, spectrum of identifiability | **2025-03-28 최종 공표.** [ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/about-this-guidance/), [HelloDPO](https://hellodpo.com/ico-finalises-guidance-on-anonymisation-and-pseudonymisation/) |
| **ePrivacy 지침** (2002/58/EC) Art. 13 + 국가별 이행법 | 전자적 직접마케팅 opt-in 원칙 + soft opt-in | 국가별 상이 — §5 매트릭스. ePrivacy Regulation 제정은 사실상 좌초 상태(지침 체제 유지) |
| **UK PECR 2003** reg. 22–23 | 개인 가입자(individual subscriber) opt-in; **corporate subscriber 예외** | 시행 중. [legislation.gov.uk](https://www.legislation.gov.uk/uksi/2003/2426/regulation/22) |
| **EU Data Act** (Reg. (EU) 2023/2854) | Art. 3–7(커넥티드 제품 데이터 접근·제3자 제공), Art. 13(B2B 불공정 계약조항 무효), Ch. VI(클라우드 전환), Art. 32(비개인정보의 제3국 정부 접근 방어) | **2025-09-12부터 적용 개시.** [Eubelius](https://www.eubelius.com/en/news/the-eu-data-act-in-force-what-changes-on-12-september-2025), [Skadden](https://www.skadden.com/insights/publications/2025/06/eu-data-act), [Latham](https://www.lw.com/en/insights/eu-data-act-what-businesses-need-to-know) |
| **EU AI Act** (Reg. (EU) 2024/1689) | Art. 50(투명성), Annex III(고위험 목록 — 농업 미포함) | 단계 시행 중(GPAI 2025-08, 고위험 2026-08~). 양돈 생산성 AI는 Annex III 고위험 범주 비해당으로 보이나 확인 필요(§9-Q10) |

---

## 2. 데이터 사용 목적 6종별 법적 근거 요건 (EU/UK GDPR)

| # | 목적 | 판정(초안) | 근거·조건 |
|---|---|---|---|
| ① | 서비스 운영(필수) | **기본 가능** | Art. 6(1)(b) 계약 이행. 계정·연락처 등 개인 데이터 포함. 별도 동의 불요·불가(동의로 구성하면 오히려 유효성 문제) |
| ② | 익명·집계 통계(기본) | **LI 가능(권고)** — 단 조건부 | 익명화 "행위 자체"가 처리이므로 Art. 6 근거 필요(EDPB 02/2026 초안 명시). Art. 6(1)(f) 정당한 이익 + Art. 5(1)(b)·Recital 50 양립성(통계 목적은 Art. 89(1) 안전조치 전제 시 양립 간주) 경로가 표준. **LIA(3단계 테스트) 문서화 + 고지(Art. 13/14) + 이의권(Art. 21) 보장** 필수. §3 참조 |
| ③ | AI 모델 학습(선택) | **LI 가능하나 옵트인 유지도 방어적 선택지** | EDPB Opinion 28/2024(AI 모델) 방향상 LI 가능성 인정되나 조건 엄격. 옵트인으로 가면 Art. 7 동의 요건(자유·특정·정보·철회 용이) 및 **철회 시 학습 중단·영향 처리** 설계 필요. 혼합 금지: 근거를 하나로 정하고 고지 일관성 유지 |
| ④ | 특정 기업 연구(선택) | **별도 동의 또는 엄격한 LI+계약장치** | 식별 가능 상태로 제3자에 제공되면 별도 동의가 안전. 익명화 후 제공이면 §3 기준 충족 시 GDPR 범위 밖. 옵트인(기본 OFF) 설계 타당 |
| ⑤ | 거래연결·리드 제공(선택) | **동의 사실상 필수(옵트인)** | 제3자 마케팅 목적의 개인 데이터 제공은 LI 형량에서 탈락 위험 높음(EDPB LI 가이드라인 태도). sole trader 농장주 데이터 포함 시 특히. 옵트인 설계가 맞음 + ePrivacy 국가별 규제 별도(§5) |
| ⑥ | 외부 AI 처리(OCR 등, 국외 이전 수반) | **동의 문제가 아니라 처리자 계약+이전 문제** | Art. 28 DPA 체결(처리자), Ch. V 이전 근거(§4). 이용자 동의를 이전 근거(Art. 49(1)(a))로 쓰는 구조는 반복적 이전에 부적합 — 지양. 고지에는 명시 필요 |

**옵트인(기본 OFF) 설계가 동의 프레임을 자초하는가 (질의 대상 핵심 논점):**
- 리스크는 실재한다. 목적 ②를 "선택 항목"처럼 UI에 노출하면 규제당국·이용자가 이를 Art. 6(1)(a) 동의로 해석하고, 이후 철회(Art. 7(3)) 시 **소급 효과·기제공분 논쟁**을 자초한다.
- 권고 구조: **②는 "동의 토글"이 아니라 "정당한 이익 + 이의권(opt-out)"으로 설계**하고 약관·프라이버시 노티스에 LI 근거를 명시. ③④⑤만 옵트인(기본 OFF) 유지. 이렇게 하면 ②의 철회는 "이의권 행사"로 처리되어 장래효만 문제되고, 익명화 완료분은 GDPR 범위 밖 논리가 유지된다(§6).
- 단, 이 전략은 **LIA 문서 + 익명화 유효성(§3)** 이 전제다. 익명화가 부실하면 LI 형량 자체가 무너진다.

---

## 3. 익명·집계 정보의 법적 지위와 판매 요건 + 최소 코호트 권고 (Release Gate 답변)

### 3.1 법적 기준
- **Recital 26 (EU/UK GDPR 공통)**: "합리적으로 사용될 가능성이 있는 모든 수단(all the means reasonably likely to be used)"으로 식별 불가할 때만 익명정보 → GDPR 적용 제외. 판매 자체를 금지하는 규정 없음.
- **ICO 최종 지침(2025-03-28)**: 식별가능성 스펙트럼 + **motivated intruder 테스트**(전문 해커가 아닌, 동기 있는 보통 수준의 침입자가 공개 자료·합리적 수단으로 재식별 가능한가). 절대적 0% 위험이 아니라 "합리적으로 낮은(remote) 위험" 기준. 익명화도 그 행위 자체는 처리로 봄. [ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/how-do-we-ensure-anonymisation-is-effective/)
- **EDPB Guidelines 02/2026 초안(2026-07-07)**: WP29 Opinion 05/2014의 3대 위험(**singling out / linkability / inference**)을 누적 기준으로 유지·갱신. 상대적 접근(수령자별 수단 고려) 또는 보수적 단순 접근 중 택일. **집계통계(group-level statistics)도 수리적 분석·AI 질의로 개인 속성 추론이 가능함을 명시** — "집계했으니 익명"이라는 단순 논리를 배척. [EDPB](https://www.edpb.europa.eu/public-consultations/guidelines-022026-on-anonymisation_en)
- WP29 Opinion 05/2014: k-anonymity 단독으로는 불충분(동질성 공격 → l-diversity/t-closeness 보완 필요)임을 이미 지적.

### 3.2 PigSignal 판매 모델에의 적용 요건 (충족해야 할 것)
1. 산출물(판매 데이터)에서 **개별 농장의 singling out 불가** — 농장 단위도 sole trader면 개인 단위와 등치될 수 있음.
2. **연결 공격 방어**: 구매 기업이 보유할 수 있는 보조 정보(도축장 출하 기록, 사료회사 납품 데이터, 지역 축산 통계, 농장 등록부)와 결합해도 특정 불가해야 함. 양돈업계는 **지역×규모 조합만으로 농장이 특정되는 희소 셀**이 많음(예: 특정 군에 모돈 1,000두 이상 농장 1곳).
3. **추론 방어**: 시계열·중첩 릴리스 간 차분(differencing)으로 개별 농장 값 역산 불가(예: n=6 코호트에서 1개 농장 이탈 후 재발행 시 차분으로 이탈 농장 값 노출).
4. **지배 농장 문제**: 한 농장이 집계값의 대부분을 차지하면 코호트 수와 무관하게 사실상 그 농장 값이 노출됨.
5. 익명화 이전 단계 처리의 적법성(§2-②) + 재식별 금지·재판매 제한 등 **구매자 계약 통제**(ICO 지침이 환경·통제 요소를 식별가능성 평가에 반영).

### 3.3 최소 코호트 권고 — **Release Gate TBD(10~20) 닫기**

**권고: 기본 하한 k=10, 세분화(지역 세밀 단위 × 월 단위 이하 시계열 × 판매용 외부 릴리스) 산출물은 k=20. 현행 KR 기준 5는 EU/GB 판매용으로는 상향 필요.**

| 항목 | 권고값 | 근거 |
|---|---|---|
| 판매용(PigSignal) 최소 코호트 | **k≥10 (하드 플로어)** | (a) 법령·ICO·EDPB 모두 **숫자를 규정하지 않음**(위험 기반) — 따라서 수치는 통계기관 관행에서 도출하는 것이 방어 논리. (b) 영국·EU 통계공개관리(SDC) 관행: 소수 셀 억제 임계 3~7(예: NHS/보건통계의 1~7 억제, 각국 통계청 3 또는 5)은 **공익·무상 공표** 기준이고, **상업적 판매 + 구매자가 보조정보 보유** 시나리오는 motivated intruder 강도가 높아 그보다 보수적이어야 함. (c) 업계 데이터 상품 관행에서 k=10이 사실상의 보수적 기준선으로 널리 사용됨 |
| 고세분화·시계열 산출물 | **k≥20** | 차분·연결 공격 표면이 커질수록 k 상향. 지역(NUTS3 이하)×월 단위 이하 조합은 20 권장 |
| 지배율 규칙(dominance / p%-rule) | **1개 농장이 셀 합계의 예: 70% 초과 시(또는 상위 2개 85% 초과) 억제·병합** | 통계기관 SDC 표준 기법((n,k)-dominance, p% rule). 코호트 수만으로는 방어 불가한 시나리오 차단 — **양돈처럼 대형 농장 편중 산업에 필수** (구체 임계치는 데이터 분포 분석 후 확정) |
| 보완 규칙 | 보조 억제(complementary suppression), 릴리스 간 차분 통제, 반올림/노이즈, 희소 조합 병합, 산출물별 재식별 위험 평가서 + 연 1회 재평가 | EDPB 02/2026 초안의 추론 위험 명시 및 ICO의 "익명화는 일회성이 아닌 지속 관리" 태도 |

- **결론(초안)**: KR 코호트 5를 EU/GB에 그대로 이식하는 것은 "집계=익명" 주장을 유지하기에 취약. **k=10 + dominance rule + 차분 통제**를 글로벌 공통 하한으로, 판매용 세분화 상품은 k=20. 이 수치는 규범상 확정 수치가 아니므로 최종적으로 **재식별 위험 평가 결과로 정당화**해야 하며, EDPB 02/2026 최종본(의견수렴 2026-10-30 종료 후) 반영 시 재검토(§9-Q3).

---

## 4. 국외 이전

### 4.1 적정성 결정 확인 결과 (2026-07-21 기준)
- **EU→한국: Decision (EU) 2022/254 (2021-12-17 채택) 유효.** EC 공식 적정성 목록 등재 확인. 1차 재심사 보고서는 미공표 — 유효성에는 영향 없으나 모니터링 필요. 적용 범위: PIPA 적용 대상 처리(종교단체·정당 등 일부 예외). [EC](https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/adequacy-decisions_en)
- **UK→한국: Data Protection (Adequacy) (Republic of Korea) Regulations 2022 (2022-12-19 발효) 유효.** UK 적정성은 EU판보다 범위가 넓다는 평가(예외 축소). [Securiti](https://securiti.ai/blog/uk-first-data-adequacy-decision-south-korea/), [Ropes & Gray](https://www.ropesgray.com/en/insights/viewpoints/102i2zc/the-uks-first-data-adequacy-regulation-bridges-the-data-transfer-gap-with-south)

### 4.2 구조 정리
- **EU/GB 농장 데이터 → 한국 서버 저장 = Ch. V 국외 이전에 해당**한다(와이즈레이크가 Art. 3(2) 역외 적용을 받는 컨트롤러이더라도, 제3국 소재 수령·저장은 이전으로 취급 — EDPB Guidelines 05/2021의 이전 3요소 논의상 역외 컨트롤러의 자체 수집도 이전 개념 관련 쟁점이 있으나, 보수적으로 이전으로 취급하고 적정성 결정을 근거로 원용하는 것이 실무 표준).
- 적정성 결정 유효 → **SCC/IDTA 불요, 이전 근거 문제 대폭 단순화.** 단 프라이버시 노티스에 이전 사실 + 적정성 근거 명시(Art. 13(1)(f)).
- 조건: 한국 측에서 **PIPA + 적정성 결정 부속 보완규정(개인정보보호위원회 고시)** 준수 — 특히 EU발 데이터의 처리 목적 제한, 정보주체 권리 보장.

### 4.3 목적 ⑥ — onward transfer (한국 → 제3국 외부 AI)
- EU/GB발 데이터를 한국 서버에서 다시 제3국(예: 미국 OCR/LLM API)으로 보내는 것은 **재이전(onward transfer)**. 적정성 결정은 재이전 시에도 보호 연속성을 요구 — 한국 PIPA의 국외 이전 규정(제28조의8 등: 동의, 계약, 인증 등) + 적정성 보완규정에 따라 처리해야 하며, EU 관점에서 보호 수준이 실질적으로 훼손되면 적정성 원용 구조 전체가 흔들림.
- 실무 요건(초안): (i) 외부 AI 벤더와 처리자 계약 + 학습 금지·보존 제한 조항, (ii) 가능하면 EU 리전/제로 리텐션 옵션 선택, (iii) 프라이버시 노티스에 재이전 체인 공개, (iv) 미국 벤더면 DPF 인증 여부 확인. 세부 적합 구조는 §9-Q4.

---

## 5. B2B 콜드 아웃리치 국가별 매트릭스 (수집 명함·LinkedIn 기반 이메일)

전제: ePrivacy 지침 Art. 13(1)은 자연인 대상 전자우편 마케팅에 사전 동의(opt-in)를 요구하고, soft opt-in(기존 고객, 유사 상품, 용이한 거부)을 예외로 허용. **B2B(법인 가입자) 취급은 회원국 재량**이라 국가별 편차가 큼. 아래는 2026-07 기준 초안 — 국가별 최신 집행 동향은 현지 검증 필요. 공통: 이메일 주소가 특정 개인 식별형(홍길동@회사)이면 GDPR도 병행 적용 — **Art. 14 고지(수집 후 1개월 내 또는 첫 접촉 시) + LIA + 억제 목록(suppression list)** 필요.

| 국가 | B2B 이메일 규칙(초안) | 콜드 이메일 리스크 | 비고 |
|---|---|---|---|
| **DE 독일** | UWG §7(2) Nr.2: **B2B 포함 명시적 사전 동의 필요**. §7(3) soft opt-in은 기존 고객 한정. "추정적 동의" 법리는 극히 좁음 | **HIGH** | 경쟁법(UWG) 기반 경고장(Abmahnung)·경쟁사 제소 관행 → 집행 확률 높음. [DLA Piper DE](https://www.dlapiperdataprotection.com/index.html?t=electronic-marketing&c=DE) |
| **FR 프랑스** | CNIL 해석: B2B는 **직무 관련성 있으면 사전 동의 없이 가능**(고지+opt-out). 개인 이메일은 opt-in | **LOW–MED** | 직무 관련성(양돈업 관계자에게 양돈 데이터 상품) 입증 용이한 편 |
| **NL 네덜란드** | Telecommunicatiewet Art. 11.7: 자연인 가입자 opt-in. **법인 가입자는 완화**(단, 특정 개인 지정 주소는 개인 취급 경향) | **MED** | ACM 집행 사례 존재. 미확인 세부 — 변호사 질의 §9-Q5 |
| **ES 스페인** | LSSI Art. 21: opt-in + 기존 계약관계 예외. **B2B에도 원칙 적용** | **MED–HIGH** | AEPD 제재 활발. B2B 직무 이메일에 LI를 인정한 해석 여지 있으나 좁음 — 미확인, §9-Q5 |
| **IT 이탈리아** | Codice Privacy Art. 130: opt-in 원칙, B2B 완화 예외 명문 없음 | **HIGH** | Garante 텔레마케팅·이메일 집행 매우 활발 |
| **PL 폴란드** | **PKE(전자통신법, 2024-11 시행) Art. 398**: 상업적 전자 커뮤니케이션 B2B 포함 사전 동의 원칙. 실무상 info@ 등 **비개인 일반 법인 주소는 예외** 해석 + "동의 요청 이메일" 관행은 회색지대 | **HIGH** | 구 UŚUDE 체제 대체. [DMSales 해설](https://dmsales.com/en/blog/electronic-communications-law-and-b2b-prospecting-in-poland/) — 로펌 검증 필요 §9-Q5 |
| **DK 덴마크** | Markedsføringsloven §10: **B2B 포함 엄격 opt-in**, 예외 협소 | **HIGH** | 건당 벌금 산정 관행(옴부즈만 집행 활발). 스팸 벌금 공식 존재 |
| **SE 스웨덴** | Marknadsföringslagen: 자연인 opt-in, **법인 대상은 opt-out 허용** | **LOW–MED** | 개인 지정 주소(이름@회사)의 자연인성 논점 존재 |
| **GB 영국** | PECR reg. 22: **individual subscriber만 opt-in 적용. corporate subscriber(법인 가입자) 이메일은 PECR 동의 불요**(신원 표시+opt-out 제공 필요, reg. 23). 단 UK GDPR은 병행 적용(LIA, Art. 14 고지) | **LOW–MED** | sole trader·파트너십은 individual subscriber로 분류됨 → **개인사업자 농장주는 opt-in 대상**. [PECR reg.22](https://www.legislation.gov.uk/uksi/2003/2426/regulation/22), ICO 직접마케팅 지침 |

**LinkedIn/명함 수집 공통 리스크**: 공개 프로필이라도 GDPR 적용(수집·저장·프로파일링 = 처리). LinkedIn 이용약관상 스크레이핑 금지는 별도 계약 리스크. Art. 14 고지 미이행이 집행 단골 사유. 국가별 발송 전 **국가 코드 기반 게이팅**(HIGH 국가는 동의 확보 채널로 전환: 전시회 opt-in, 파트너 소개, 우편/전화 대체) 권고.

---

## 6. 철회·삭제권 — 피그플랜 현행 조항의 EU/GB 방어 가능성

피그플랜 KR 스냅샷: 익명 유상판매(옵트아웃) / 최소 코호트 5 / 탈퇴 후 통계 데이터 20년 보유 / 기제공분 소급회수 불가.

| 현행 조항 | EU/GB에서 걸리는 지점 | 방어 가능성(초안) |
|---|---|---|
| 익명 판매를 **옵트아웃**으로 운영 | 동의가 아닌 LI 기반이면 옵트아웃(=Art. 21 이의권) 구조 자체는 성립 가능. 단 **LIA 문서·고지·이의권 실효성**이 전제. 동의처럼 보이는 UI(체크박스)로 운영하면 동의 요건 미충족 문제로 역전됨 | **조건부 방어 가능** — §2-② 구조로 재설계 필요 |
| **코호트 5** | §3 — EDPB 02/2026 초안의 집계 추론 위험 명시로 소코호트 방어력 약화 | **상향 필요(k=10/20)** |
| **기제공분 소급회수 불가** | 진정한 익명 데이터는 GDPR 범위 밖 → 이미 판매된 익명 집계물 회수 의무 없음(Art. 17 부적용). **단 익명성 입증 책임은 와이즈레이크에 있으며**, 익명화 부실 판정 시 이 조항은 Art. 17 침해 조항이 됨. 또한 조항 문구가 "개인정보를 회수하지 않는다"로 읽히면 Art. 17과의 충돌로 무효·불공정 조항 리스크 | **익명성 유효 시 방어 가능** — 문구를 "익명·집계 산출물"로 한정할 것 |
| **탈퇴 후 20년 보유** | (a) **익명 통계 자체**의 20년 보유: GDPR 밖 — 가능. (b) **익명화 전 원본/가명 데이터**의 탈퇴 후 보유: Art. 5(1)(e) 보존 제한 위반 소지 큼 — 계약 종료 후 단기 보존(법정 의무 한도) 외 정당화 곤란 | **(a) 방어 가능 / (b) 곤란** — 조항을 분리·명확화 필요 |
| (참고) 20년·회수불가를 **약관**으로만 처리 | Art. 7(2)(동의의 구분 표시), 불공정조항지침(93/13/EEC, B2C 요소 있을 시), **Data Act Art. 13(B2B 데이터 관련 일방적 불공정 조항 무효, 2025-09-12 적용)** 검토 필요 — 특히 중소 농가 상대 일방 조항 | **재작성 권고** |

추가: 철회·이의 후 파이프라인 — 이의 접수 시 **장래 집계 배치에서 즉시 제외**하는 기술 프로세스를 약관과 일치시켜야 함(약관상 "다음 분기 반영" 등 지연은 다툼 소지).

---

## 7. 역외 적용(Art. 3(2))과 대리인(Art. 27) 지정 의무

- **역외 적용 성립**: EU/GB 소재 농장(그 농장주·직원인 자연인)에게 유상·무상 서비스를 제공(offering of services) → EU GDPR Art. 3(2)(a) 및 UK GDPR 대응 조항 적용. 현지어 UI, 현지 통화 결제, 현지 마케팅은 targeting 징표(Recital 23).
- **대리인 지정 의무**: Art. 27 예외(occasional + 대규모 특별범주 아님 + 저위험)는 SaaS 상시 처리에 부적합 → **EU 대리인 1곳(주요 대상 회원국 소재) + UK 대리인 1곳 별도 지정 필요.** 대리인 정보는 프라이버시 노티스에 기재.
- 미지정 시 Art. 83(4) 과징금 상한(1,000만 유로 또는 전세계 매출 2%) 카테고리. 상용 대리인 서비스(연 1~3천 유로 수준)로 해소 가능한 저비용·고노출 항목이므로 **출시 전 완료 권고**.
- 부수 의무: Art. 30 처리 기록, (해당 시) DPO 지정 여부 검토(Art. 37 — 대규모 정기적 모니터링 해당성, §9-Q7), PigSignal용 DPIA(Art. 35 — 혁신적 기술·대규모 매칭 요소).

---

## 8. 부속조항 구조 권고 (EU 1벌 vs 국가별)

**권고: "EU 부속조항 1벌 + 국가별 미세조정 스케줄(마케팅·언어·강행규정만)" + GB 별도 1벌.**

근거:
1. GDPR은 직접 적용 규정이라 27개국 공통 — 데이터 조항(목적 6종, 익명화, 이전, 권리)은 **EU 단일 부속조항**으로 충분하고 유지비가 낮다.
2. 국가별 실질 편차는 (a) ePrivacy 이행(§5 — 마케팅 동의 문구·기본값), (b) 언어 요건(예: 프랑스 Loi Toubon — 소비자 대상 프랑스어), (c) 개별 강행 민사규정(관할·준거법 제한) 정도 → 본문이 아니라 **국가별 1~2쪽 스케줄**로 처리.
3. GB는 UK GDPR/PECR/DUAA 체계가 형식상 분리되어 있고 감독기관(ICO)·대리인·이전 근거가 다르므로 **별도 부속조항 1벌**이 깔끔.
4. 미국식 "주별 부칙" 모델을 EU에 이식(27개국 부속)하면 개정 동기화 비용이 크고 불일치 리스크만 커짐 — 비권고.
5. 준거법·관할: B2B 약관이라도 농장주가 소비자 유사 지위로 판정될 여지(개인사업자)에 대비, EU 회원국 강행규정 우선 조항(savings clause) 삽입.

---

## 9. 변호사 확인 필수 질의 목록

1. **[이전]** 한국 EU 적정성 결정의 1차 재심사 진행 상황·예상 시점, 재심사 리스크(PIPA 개정 사항 반영) — 유효성 전제의 지속 가능성 평가. (미확인 사항)
2. **[가명처리]** EDPB Guidelines 01/2025 최종본 채택 여부·초안 대비 변경점. (미확인 사항)
3. **[익명화]** §3.3 코호트 k=10/20 + dominance rule 초안의 타당성 검증. EDPB Guidelines 02/2026 의견수렴(~2026-10-30) 결과 반영 계획 포함. **Release Gate 최종 승인 필요.**
4. **[onward transfer]** 한국 서버 경유 제3국 AI 벤더 재이전 체인의 적정성 결정 정합 구조(PIPA 국외이전 요건과의 교차) 및 노티스 문구.
5. **[ePrivacy]** NL·ES·PL의 B2B 이메일 최신 집행 기준 확인(§5에서 미확인 표기 항목) + DE 발송 전면 중단 여부 판단.
6. **[LI 전략]** 목적 ②를 LI+옵트아웃으로 설계하는 §2 구조에 대한 LIA 초안 검토·국가별 감독기관 수용성.
7. **[거버넌스]** DPO 지정 의무 해당성(Art. 37), DPIA 필요성(Art. 35), Art. 30 기록 양식.
8. **[약관]** "기제공분 소급회수 불가"·"익명 통계 장기 보유" 문구의 EU 소비자법·Data Act Art. 13 불공정 조항 심사 통과 가능 문구.
9. **[Data Act]** PigOS가 커넥티드 제품 연동(IoT 센서) 시 "related service/data holder" 해당 여부 및 Art. 4–6상 농장의 데이터 접근·제3자 제공 요구권이 PigSignal 모델과 충돌하는 지점(특히 Art. 6(2) 파생 인사이트 제한, 클라우드 전환 Ch. VI 대응).
10. **[AI Act]** PigOS AI 기능의 위험 분류 확정(Annex III 비해당 확인) 및 Art. 50 투명성 의무 해당 여부.
11. **[경계]** 법인 농장 운영 데이터 중 개인정보로 전환되는 경계(담당자 계정 연결 데이터, 1인 법인) 처리 기준서 검토.
12. **[UK]** DUAA 2025의 "recognised legitimate interests"·연구 목적 완화가 목적 ②③에 주는 실익.

---

## 10. 리스크 등급표

| # | 이슈 | 등급 | 근거 한 줄 |
|---|---|---|---|
| 1 | 코호트 5 그대로 EU/GB 판매 (익명성 부인 → 전체 판매 모델이 무근거 처리로 전환) | **HIGH** | EDPB 02/2026 초안이 집계통계 추론 위험을 명시, 소코호트+보조정보 결합 시 재식별 항변 취약 |
| 2 | DE·DK·IT·PL 콜드 이메일 (명함·LinkedIn 기반) | **HIGH** | B2B 포함 opt-in 명문(UWG §7, Markedsføringsloven §10, Art. 130, PKE 398) + 활발한 집행 관행 |
| 3 | 탈퇴 후 원본·가명 데이터 20년 보유 | **HIGH** | Art. 5(1)(e) 보존 제한 정면 충돌 — 익명화 전 데이터에는 정당화 곤란 |
| 4 | EU/UK 대리인(Art. 27) 미지정 상태로 출시 | **MED** | 의무 성립은 명확하나 저비용으로 즉시 해소 가능; 미지정 자체가 과징금 카테고리 |
| 5 | 목적 ② 를 동의 토글로 설계(동의 프레임 자초) | **MED** | 철회 소급 논쟁·기제공분 조항과 충돌 유발 — LI+이의권 재설계로 회피 가능 |
| 6 | 기제공분 소급회수 불가 조항 | **MED** | 진정 익명이면 방어 가능하나 익명성 입증 실패 시 Art. 17 위반 조항으로 전환되는 조건부 리스크 |
| 7 | 목적 ⑤ 리드 제공(제3자 마케팅) | **MED** | sole trader 데이터 포함 시 동의 필수 성격 — 옵트인 설계로 관리 가능하나 ePrivacy 중첩 |
| 8 | onward transfer(외부 AI 재이전) 체인 미정비 | **MED** | 적정성 원용 구조의 연속성 요건 — 벤더 계약·리전 선택으로 통제 가능 |
| 9 | EU→KR 이전 자체 | **LOW** | 적정성 결정(EU 2022/254·UK 2022 Regs) 모두 유효 확인 — 노티스 기재만 하면 단순 |
| 10 | 익명 통계 산출물 자체의 판매·장기 보유 | **LOW** | 익명 인정 시 GDPR 범위 밖 — 판매 금지 규범 없음(단 #1 전제) |
| 11 | FR·SE·GB(법인 대상) B2B 이메일 | **LOW–MED** | soft opt-in/corporate subscriber 예외 존재 — 단 GB sole trader는 opt-in 대상, GDPR 고지 의무 병행 |
| 12 | Data Act·AI Act 적용 | **LOW(모니터링)** | 현행 수동입력 SaaS 구조에선 주변부 — IoT 연동·클라우드 전환 조항은 로드맵 단계에서 재평가 |

---

*작성: PigOS 법무 리서치 세션 (2026-07-21). 본 초안의 웹 확인 출처는 각 절에 인라인 표기. "미확인 — 변호사 질의" 항목은 §9 번호로 연결됨.*
