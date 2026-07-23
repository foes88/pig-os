# RAW_NA — 북미(미국·캐나다) 양돈/축산 SaaS 약관 벤치마크

- 작성일: 2026-07-22
- 목적: 북미 양돈/축산 생산관리 SaaS의 실제 게시 약관(ToS/Privacy/DPA/Cookie/SLA) **구조·접근방식** 파악. PigOS / PigSignal(집계·익명 데이터 활용) 모델의 시장 선례 확인.
- 저작권 원칙: 문안 대량 복제 금지. 조항의 **존재 여부·구조·짧은 핵심 문구(1문장 이하)**만 추출.
- 방법: WebSearch + WebFetch. 표기 없는 항목은 "해당 문서에서 미확인"을 의미(존재하지 않는다는 확정은 아님).

---

## 서비스 카드

### 1. PigCHAMP (양돈 전용, 미국 Iowa 소재)

두 개의 별도 프라이버시 문서를 운영 — 일반 소프트웨어용과 **벤치마킹 프로그램용**. 벤치마킹 문서가 PigSignal 모델의 핵심 선례.

**A. 일반 Privacy Policy** (https://www.pigchamp.com/privacy-policy)
1. 문서: Privacy 있음. Terms&Conditions 참조됨(별도). DPA/Cookie/SLA 미확인.
2. 데이터 소유권: 명시 없음(누가 소유하는지 불명).
3. 집계·익명 활용: **있음, 광범위**. "PigCHAMP reserves the right to maintain, update, disclose or otherwise use Anonymous Information, without limitation." 익명정보에 사실상 무제한 사용권 유보.
4. AI/알고리즘: 없음.
5. DPA/수탁: 없음. 비즈니스 파트너가 특정 기능 위해서만 개인정보 접근. 자산매각 시 인수자 이전 가능.
6. CCPA/미국 프라이버시: 없음(캘리포니아 고지·Do Not Sell 미확인).
7. 관할·분쟁: 별도 T&C 참조, 본문에 준거법 미상.
8. 보유·삭제: 없음.
9. 과금: 없음.
10. 특이: 마케팅 이메일 **옵트아웃** 방식만.

**B. Benchmark Program Privacy Policy** (https://www.pigchamp.com/benchmarking/privacy-policy) — ★PigSignal 직접 선례
1. 문서: 벤치마킹 전용 별도 프라이버시 존재.
2. 데이터 소유권: 명시 없음("PigCHAMP License Agreement" 하에 수집으로만 기술).
3. 집계·익명 활용: **핵심**. 회사가 집계 데이터를 (a) 연구자에게 기초·응용 연구용, (b) 기타 산업 파트너·이해관계자에게 "internal research and marketing purposes"로 제공. **판매 언급은 없음**.
4. AI/알고리즘: 없음.
5. DPA/수탁: 없음.
6. CCPA: 없음. USDA의 생산자 데이터 기밀 정책 준수만 언급.
7. 관할: 미상(Iowa 주소).
8. 보유·삭제: 없음.
9. 과금: 없음.
10. **특이(재식별 방지 안전장치)**: 집계는 **최소 3개 농장 시스템** 필요, **단일 농장 기여 60% 초과 금지** — 익명화 임계값을 약관에 수치로 명문화. PigSignal의 "k-익명성/최소농장수" 설계에 그대로 참고 가능한 선례.

---

### 2. MetaFarms (양돈 중심 생산관리, 미국)

URL: https://www.metafarms.com/privacy.html (Privacy). B2B 지향 문서.
1. 문서: Privacy 있음. ToS/DPA/Cookie/SLA 별도 미확인.
2. 데이터 소유권: 명시 없음(연락처·거래정보 등 B2B 정보 중심).
3. 집계·익명 활용: **있음, 매우 관대**. "aggregated or anonymized … no longer considered personal information … may use for any purpose." 익명화하면 개인정보 아님 → 목적 무제한.
4. AI/알고리즘: 없음.
5. DPA/수탁: 최소. 서비스제공자에 "다른 목적 사용·공개 금지" 의무만, 정식 DPA 프레임워크 부재.
6. CCPA/미국: **부분**. 캘리포니아 Shine the Light Act(§1798.83, 제휴사 공유 선호) 언급. Do Not Sell 메커니즘은 없음.
7. 관할·분쟁: 본 프라이버시 문서엔 미상.
8. 보유·삭제: 보유만("as long as necessary", 법적·보고 요건 기준). 삭제권 메커니즘 없음.
9. 과금: 없음.
10. 특이: 제3자(마케팅·분석 벤더 등)에 "other parties for any purpose we disclose"로 광범위 공개 여지. 옵트아웃(unsubscribe)만.

---

### 3. Ever.Ag / Farms.com 계열 (농업 데이터 플랫폼, 미국 Texas) — ★생산자 데이터 소유권 모델 선례

생산자용/비생산자용 ToU를 분리 운영. 축산 포함 광범위 농업 SaaS.

**A. Terms of Use for Producers** (https://ever.ag/terms-of-use-for-producers)
1. 문서: 생산자용 ToU + 비생산자용 ToU + Privacy + CCPA Notice 별도 존재. DPA/SLA 미확인.
2. 데이터 소유권: **있음, 고객(생산자) 유지**. "any Producer Data collected through the Software is owned by you." → PigOS가 지향하는 "고객 유지 + 회사 라이선스" 구조의 대표 선례.
3. 집계·익명 활용: **있음**. "Ever.Ag may aggregate the Producer Data with other data (so that it is not individually identifiable)." 세부 공유는 Privacy Policy로 위임, 명시적 옵트아웃 메커니즘은 본문에 없음.
4. AI/알고리즘: 없음(진단·수의 대체 아님 면책도 없음).
5. DPA/수탁: 없음(controller/processor 용어 미사용).
6. CCPA: 본 ToU엔 없음, 푸터에 별도 CCPA Notice 링크.
7. 관할·분쟁: **Texas 준거법**. "governed by the laws of the State of Texas." 중재·집단소송 포기 조항은 없음.
8. 보유·삭제: 약함. 접근 중단만 규정, 삭제 기한 없음.
9. 과금: **있음**. 분기 단위 청구("payable … on a quarterly basis"), 연체료 월 1.5%. 환불정책 명시 없음.
10. 특이: 생산자/비생산자 약관 분리 — 데이터 기여자와 데이터 소비자를 다른 계약군으로 취급.

**B. Privacy Policy** (https://ever.ag/privacy-policy)
- 집계·익명: 있음("does not identify you"), 집계정보 자체는 판매 안 함 명시.
- 옵트인/아웃: **혼합**. 쿠키는 기본 수집(브라우저 거부), 위치는 명시 동의, **제3자 공유는 사전 옵트인**.
- DPA/수탁: 서비스제공자에 목적 제한 의무 부과(경량).
- CCPA: 있음(별도 California Notice 링크).
- 데이터브로커: 언급 없음.
- 보유·삭제: 있음("no longer than necessary", 법정 보유요건 준수).

**C. CCPA Privacy Notice for California Residents** (https://ever.ag/ccpa-privacy-notice)
- 수집 카테고리(이름·이메일·전화 + 위치 등) 명시.
- 캘리포니아 권리 3종: 접근/이동성, 삭제, 차별금지.
- **Do Not Sell/Share 링크·메커니즘은 미확인**(문서상 명시 없음).
- HIPAA 건강정보·GLBA 금융정보 제외 명시. 민감정보 목록화는 안 함.
- 데이터브로커 자기규정 없음.

---

### 4. Zoetis (동물약품 대기업 디지털 자산, 미국 New Jersey)

URL: https://www.zoetis.com/terms-of-use (제품 SaaS가 아닌 코퍼레이트 사이트 ToU지만, 대기업 표준 조항 참고용).
1. 문서: ToU + Privacy(글로벌 프라이버시 센터) 있음.
2. 데이터 소유권(업로드): 회사에 관대. 사용자 업로드의 아이디어·개념을 "for any purpose whatsoever, without … limitations" 사용 가능 — 사용자 업로드 콘텐츠 광범위 라이선스.
3. 집계·익명: 미확인.
4. AI: 없음.
5. 수의/진단 면책: **본 ToU엔 미확인**(별도 제품·의료 콘텐츠 고지에서 다룰 가능성).
6. 관할: **New Jersey / 미국법**.
7. 분쟁: 뉴저지 법원 관할, 중재·집단소송 포기 없음.
8. 책임제한: **있음, 상한 $100** ("maximum aggregate liability … exceed ONE HUNDRED US dollars").
9. 특이: 대기업이 책임상한을 소액($100) 고정 — SaaS형 프로바이더 책임한도 설계 참고.

---

### 5. Herdwatch (축우·양 등 가축관리, 아일랜드 본사·북미 판매)

URL: https://herdwatch.com/privacy-policy/ (참고: EU/아일랜드법 기반, 북미 판매 대조군).
1. 문서: Privacy 있음(오래된 버전 인상).
2. 데이터 소유권: 명시 없음.
3. 집계·익명 활용/판매: 언급 없음(데이터 상업화보다 서비스 개선 중심).
4. AI/ML: 없음.
5. DPA/수탁: 경량. Irish Data Protection Acts 1988·2003 참조, controller/processor 정의 부재.
6. CCPA/GDPR: 명시 없음(GDPR·CCPA 이전 아일랜드법만 참조 — 갱신 지연 시사).
7. 관할: 아일랜드법 함의.
8. 보유·삭제: 무기한 성격("reasonable period or as long as the law requires").
9. 과금: 없음.
10. 특이: 축산 전용 SaaS라도 프라이버시 문서가 구식일 수 있음을 보여주는 대조 사례.

---

### 6. 산업 표준 프레임워크 — Ag Data Transparent (ADT) Core Principles (2024 개정)

URL: https://www.agdatatransparent.com/principles — 개별 서비스는 아니지만, **북미 농가데이터 계약의 사실상 업계 표준**. 여러 대형 프로바이더가 ADT 인증을 받고 이 원칙에 약관을 정렬. PigOS 약관 설계의 체크리스트로 직접 사용 가능.

- **소유권/통제**: 농가가 자기 운영 데이터를 소유해야 함. 소유권이 프로바이더로 이전되면 계약에 명시할 것.
- **수집·동의**: 데이터 카테고리(농경·토지·재무·기계·기상·**축산**)별 명시적 동의 요구. 동의 범위 밖 수집 금지.
- **제3자 공유**: 접근하는 제3자군(통합파트너·비즈니스파트너·제휴사·신뢰자문가)을 정의.
- **프로바이더 매각 시**: 데이터 처리 설명, 농가 통지 + **삭제 선택권** 부여.
- **동의·선택**: 농가는 옵트인/옵트아웃/기능 비활성 선택 가능, 선택별 이용 가능 기능 명확화.
- **이동성(Portability)**: 비익명 데이터는 합리적 기간 내 사용 가능한 형식으로 반환. **익명·집계 데이터는 이동성 의무 없음**.
- **보유·삭제**: 종료/이용 중단 후 삭제권·프로바이더 의무를 계약에 명시.
- **AI/알고리즘**: "explain whether ag data will be used in training machine learning or artificial intelligence models" — **AI 학습 이용 여부를 고지하라**는 원칙 명문화(2024 신규 개념).
- **익명화·집계**: 익명 데이터셋 포함 여부를 고지하고 **농가에 옵트아웃 제공**을 권고.

---

## 북미 공통 관행 요약 (쟁점별 시장 관행)

**데이터 소유권**
- 두 갈래로 갈림. (a) **명시적으로 고객(생산자) 유지 + 회사 라이선스** 구조를 두는 진영(Ever.Ag "owned by you", ADT 원칙) vs (b) 소유권을 **아예 언급하지 않는** 진영(PigCHAMP, MetaFarms, Herdwatch). 축산 전용 소프트웨어일수록 소유권 침묵 경향, 범용 대형 ag-data 플랫폼일수록 소유권 명문화 경향.
- 업계 표준(ADT)은 "농가 소유 + 이전 시 명시"를 요구 → 명문화가 모범.

**집계·익명 데이터 활용 (PigSignal 핵심)**
- **광범위 활용은 시장 표준이며 정상 관행**. 거의 모든 사례가 "익명화하면 개인정보 아님 → 목적 제한 없이 활용" 논리를 채택(MetaFarms "any purpose", PigCHAMP "without limitation", Ever.Ag 집계 공유).
- **판매(sale)는 대체로 회피**. 집계데이터 "자체는 판매 안 함"을 명시하거나(Ever.Ag), 판매를 언급하지 않고 "연구자·산업파트너 제공"으로 프레이밍(PigCHAMP). 노골적 "데이터 판매" 조항은 드묾.
- **동의 방식은 대체로 옵트아웃/묵시**(별도 벤치마킹 동의 없이 이용약관 수락으로 집계 편입). 단 ADT 표준과 Ever.Ag의 제3자 공유는 **옵트인/옵트아웃 선택권 제공**을 권고·채택.
- **재식별 방지 임계값을 수치로 명문화한 선례 존재**: PigCHAMP의 "최소 3개 시스템·단일농장 60% 상한" — PigSignal 신뢰 확보용으로 그대로 벤치마킹 가치.

**AI/알고리즘**
- **현행 게시 약관 대부분에 AI 조항 부재** (PigCHAMP·MetaFarms·Ever.Ag·Zoetis·Herdwatch 모두 없음). 진단·수의 대체 아님 면책도 대부분 없음.
- 그러나 **업계 표준(ADT 2024)은 "AI 학습 이용 여부 고지"를 신규 원칙으로 도입** → 시장은 아직 약관에 반영 못 했으나 방향은 명확. PigOS가 AI 학습 이용·수의 대체 아님 면책을 선제적으로 넣으면 **경쟁사 대비 앞서는 위치**.

**DPA/수탁**
- 양돈/축산 전용 SaaS 진영은 **정식 DPA·controller/processor 프레임워크가 거의 없음**(경량 "서비스제공자 목적제한" 문구 수준). 별도 DPA 문서를 갖춘 곳을 찾기 어려움.
- B2B 글로벌 확장(EU/GB 등)을 노리는 PigOS 입장에선 **정식 DPA 제공 자체가 차별화 요소**가 될 수 있음.

**CCPA/미국 프라이버시**
- 편차 큼. Ever.Ag는 별도 CCPA Notice + 캘리포니아 권리(접근·삭제·차별금지) 보유하나 **Do Not Sell/Share 링크·메커니즘은 불명확**. MetaFarms는 구식 Shine the Light만. PigCHAMP·Herdwatch는 사실상 없음.
- 데이터브로커 자기규정은 어느 곳도 안 함. (한편 캘리포니아는 2025~26년 Delete Act·데이터브로커 단속 강화 중 — 규제 리스크 상승.)

**관할·분쟁**
- 프로바이더 본사 주(州)법 지정이 표준: Ever.Ag=Texas, Zoetis=New Jersey.
- **중재·집단소송 포기 조항은 조사 대상 대부분에서 미확인** — 이 세그먼트는 아직 강한 분쟁조항을 표준화하지 않음.

**보유·삭제 / 과금**
- 보유는 "필요기간·법정요건"의 모호한 표준이 지배적, **구체적 삭제 기한·반환 절차 명문화는 드묾**(ADT만 계약 명시 권고).
- 과금은 구독형이 표준. Ever.Ag는 분기 청구 + 연체료 월 1.5%. 크레딧/환불 구조를 약관에 상세히 둔 사례는 확인 안 됨.

---

## PigOS 대비 시사점 (5)

1. **집계·익명 활용은 시장이 이미 폭넓게 허용 — PigSignal 모델은 선례가 충분**. "익명화 시 개인정보 아님 → 목적 제한 없이 활용"은 북미 표준 프레이밍. 다만 **노골적 "판매(sell)" 표현은 시장이 회피**하므로, PigOS도 "연구·산업 인사이트 제공/라이선스"로 프레이밍하고 직접 판매 문구는 신중히.

2. **재식별 방지 임계값을 약관에 수치로 명문화하라**. PigCHAMP의 "최소 3개 시스템·단일농장 60% 상한"이 유일한 구체 선례이자 신뢰 장치. PigOS는 k-익명 최소농장수·기여도 상한을 CONSENT_AND_DATA_USE_SPEC / ANONYMIZATION_STANDARD과 정합되게 약관에 명시하면 경쟁 우위.

3. **데이터 소유권을 "고객 유지 + 회사 라이선스"로 명문화하라**. 침묵(PigCHAMP·MetaFarms)보다 Ever.Ag식 "owned by you" + 집계 라이선스가 ADT 업계표준·글로벌 신뢰에 부합. 축산 전용 경쟁사 다수가 침묵 중이므로 명문화 자체가 차별화.

4. **AI 학습 이용 고지 + 수의/진단 대체 아님 면책을 선제 도입하라**. 현행 경쟁사 약관엔 AI 조항이 거의 없으나 ADT 2024가 "AI 학습 고지"를 원칙화. PigOS가 (a) 데이터의 AI 학습 이용 여부·옵트, (b) AI 출력이 수의 진단·처방 대체 아님 면책을 넣으면 규제 흐름 선점.

5. **정식 DPA·강화된 분쟁/삭제 조항으로 B2B·글로벌에서 앞서라**. 이 세그먼트는 정식 DPA, controller/processor, 구체적 삭제기한, 중재/집단소송 포기가 대부분 미비. PigOS가 별도 DPA 문서(이미 PIGOS_B2B_DPA_DRAFT 존재)와 국가별 부속서, 명확한 보유·삭제 기한을 갖추면 "약관 성숙도" 자체가 세일즈 포인트가 됨.

---

## 조사 소스
- PigCHAMP Privacy — https://www.pigchamp.com/privacy-policy
- PigCHAMP Benchmark Privacy — https://www.pigchamp.com/benchmarking/privacy-policy
- MetaFarms Privacy — https://www.metafarms.com/privacy.html
- Ever.Ag Terms of Use for Producers — https://ever.ag/terms-of-use-for-producers
- Ever.Ag Privacy Policy — https://ever.ag/privacy-policy
- Ever.Ag CCPA Notice — https://ever.ag/ccpa-privacy-notice
- Zoetis Terms of Use — https://www.zoetis.com/terms-of-use
- Herdwatch Privacy Policy — https://herdwatch.com/privacy-policy/
- Ag Data Transparent Core Principles (2024) — https://www.agdatatransparent.com/principles
