# CONSENT_AND_DATA_USE_SPEC v0.1
## PigOS 글로벌 — 동의·데이터 사용 목적 제품 스펙 (2026-07-21)

> **본 문서는 변호사 확정 전 초안(pre-counsel draft)이다.** 제품·엔지니어링 구현 착수를 위한 스펙이며 법률 자문이 아니다.
> 미결 값은 `[D-xx]`로 표기하고 `DECISION_REGISTER.md`를 참조한다. 근거 출처는 `research/` 7개국 리서치 문서의 섹션 번호로 인용한다(모두 pre-counsel research 지위 — `CURRENT_STATE_FINDINGS.md` §B).
> 상태 태그: `LEGAL_REQUIREMENT` `OFFICIAL_GUIDANCE` `DRAFT_GUIDANCE` `CASE_OR_ENFORCEMENT` `INDUSTRY_PRACTICE` `INTERNAL_POLICY_PROPOSAL` `COUNSEL_CONFIRMATION_REQUIRED`

---

## 1. 목적 코드 정의표

| purpose_code | # | 설명 | 데이터 범위 | 기본값 | 철회(옵트아웃/이의) 효과 |
|---|---|---|---|---|---|
| `SERVICE_OPERATION` | ① | 서비스 제공·운영: 계정, 인증, 생산기록 저장·동기화, KPI·알림, 결제·크레딧, 보안·부정방지 | 계정·기기·로그, 생산기록(교배·분만·이유·폐사), KPI, 결제 정보 | **필수 — 동의 토글 아님** (계약 이행 근거) | 철회 개념 없음. 중단 = 서비스 해지·탈퇴 |
| `ANON_AGG_STATS` | ② | 익명·집계 산업 통계 산출 및 제3자 제공(PigSignal 유상 포함) | 생산성적·운영 데이터 → 비가역 익명화·집계 산출물 | **국가별 법적근거 분기 [D-01]** — 동의 토글 아님(EU/GB·BR·KR·US), TH=COUNSEL_PENDING(§24(5) LI 확정 전 보수), VN·CN=동의형 | 철회/이의/제외요청 접수 시점 이후 생성되는 모든 통계 배치에서 해당 농장 데이터 제외. 기산출·기제공 익명 산출물은 존속 [D-04] |
| `AI_MODEL_TRAINING` | ③ | 원(식별) 데이터를 사용하는 AI 모델 학습·개선 | 생산기록 원데이터, AI 입출력, 업로드 이미지 | **옵트인 · 기본 OFF · 개별 토글 [D-02]** | 철회 시점 이후 학습 배치 투입 중단. 기학습 모델의 처리는 §4.3 참조 |
| `NAMED_RESEARCH` | ④ | 특정 기업(사료·약품·금융·연구기관)의 위탁 연구를 위한 데이터 제공 | 목적별 동의서에 특정된 항목·세밀도 (②보다 세밀할 수 있음 — US §3.2의 분리 원칙) | **옵트인 · 기본 OFF · 개별 토글 [D-02]** | 철회 이후 신규 제공 중단 + 수령기업에 후속 릴리스 제외 통지 |
| `TRANSACTION_MATCHING` | ⑤ | 거래연결·리드 제공: 이용자 본인 연락처·거래의사를 공급업체 등 제3자에 유상 제공 | 이용자 본인의 식별 연락처·농장 프로필·거래 관심 정보 (**본인 정보로 한정** — US §3.3) | **옵트인 · 기본 OFF · 개별 토글 [D-02]** — 익명·가명 우회 불가(KR §2⑤, GB_EU §2⑤, BR §2⑤, VN §3.2 등 4개국+ HIGH) | 철회 즉시 신규 리드 제공 중단. 기제공 리드는 수령자에게 삭제·이용중단 요청 발송(계약 조항 필요) |
| `EXTERNAL_AI_PROCESSING` | ⑥ | 외부 AI 벤더 처리(OCR·LLM 등) — 수탁(처리위탁) + 국외이전 메커니즘 | 사용자가 해당 기능에 투입하는 문서 이미지·AI 입력 | 수탁+이전 메커니즘으로 처리. **별도 동의는 필요 국가만**(§2 매트릭스 — CN·VN 등). 기능 사용 시점 just-in-time 고지 | 기능 사용 중단 = 전송 중단. 벤더 zero-retention/no-training 계약 전제(KR §4, GB_EU §4.3, US §2⑥) |

공통 원칙:
- ③④⑤ 동의는 ①과 묶을 수 없고, 거부해도 서비스 제공을 거부하지 않는다(KR PIPA 제22조, TH PDPA §19 조건화 금지, VN PDPL 목적 특정 원칙). `LEGAL_REQUIREMENT`
- ②를 "동의 토글"로 UI 노출하면 EU에서 동의 프레임(철회 소급 논쟁)을 자초한다(GB_EU §2 권고 구조) — ②는 동의 목록이 아닌 "데이터 활용 고지 + 제외요청/이의 채널"로 분리 표기한다. [D-01]

---

## 2. 목적×법역 lawful basis 매트릭스

범례: 근거 / UI 요건 / 상태태그. 출처는 리서치 문서 §번호.

### ① SERVICE_OPERATION

| 법역 | 근거 | UI 요건 | 태그·출처 |
|---|---|---|---|
| KR | PIPA 제15조1항4호 계약 이행 — 동의 불요 | 방침 고지 | `LEGAL_REQUIREMENT` KR §2① |
| EU/GB | Art. 6(1)(b) 계약 이행 — 동의 구성 금지(유효성 문제) | 프라이버시 노티스 | `LEGAL_REQUIREMENT` GB_EU §2① |
| US | 계약 이행 처리 — 고지로 충분. 고지-실제 일치가 FTC §5 관건 | 프라이버시 고지 | `LEGAL_REQUIREMENT` US §2① |
| BR | LGPD Art. 7 V 계약 이행(+보안은 Art. 7 IX 병용) | 노티스 | `LEGAL_REQUIREMENT` BR §2① |
| TH | PDPA §24(3) 계약 이행 — 동의 구성 시 철회 리스크로 비권장 | §23 고지 | `LEGAL_REQUIREMENT` TH §2① |
| VN | PDPL 계약 이행 동의 예외(세부 시행령 대조 필요) | 고지 | `COUNSEL_CONFIRMATION_REQUIRED` VN §2① |
| CN | PIPL 제13조2호 계약 이행. **단 한국 서버 = 국외이전으로 제39조 별도동의가 ①에도 중첩** | 가입 시 국외이전 별도동의 화면 | `LEGAL_REQUIREMENT` CN §3 공통, [D-07] HOLD |

### ② ANON_AGG_STATS — [D-01] 국가별 분기 (핵심)

| 법역 | 근거 | UI 요건 | 태그·출처 |
|---|---|---|---|
| EU/GB | Art. 6(1)(f) 정당한 이익(익명화 행위 자체의 근거 — EDPB 02/2026 초안이 Art. 6 근거 필요 명시) + Art. 89(1) 안전조치 | LIA 문서화 + Art. 13/14 고지 + **Art. 21 이의권(옵트아웃) 채널**. 동의 체크박스 금지 | `DRAFT_GUIDANCE`(EDPB 02/2026, 의견수렴 ~2026-10-30) + `OFFICIAL_GUIDANCE`(ICO 2025-03) GB_EU §2②·§3 |
| BR | Art. 7 IX 정당한 이익 + ANPD LI 가이드 3단계 LIA | LIA + 고지 + 옵트아웃 | `OFFICIAL_GUIDANCE`(ANPD LI 가이드 2024-02) BR §2② |
| KR | 제58조의2 익명정보(법 적용 제외) — 익명처리 행위 자체의 근거는 질의 Q2 | **고지 + 제외요청 채널**. 현행 landing 약관의 "별도 동의" 자기구속(F5) 해소 선행 | `COUNSEL_CONFIRMATION_REQUIRED`(Q2·Q4) KR §2②·§3·§7 |
| US | de-identified 3요건(합리적 조치 + 재식별 금지 공개 약속 + 수령자 계약 구속) 충족 시 '개인정보' 밖 | 고지(관행 기술). **예외: NE 등 농업데이터법 주 — 식별가능 농업데이터 판매는 명확·현저한 고지에 의한 서면(전자) 옵트인**(LB525, 위반당 $1,000·치유기간 없음) | `LEGAL_REQUIREMENT`(NE LB525 2026-07-17 발효) + `CASE_OR_ENFORCEMENT`(FTC 익명화 집행 경향) US §1.4·§2②·§3 |
| TH | LI(§24(5)) 주장 가능하나 PDPC 선례 미확립 → **고지 + 옵트아웃 병행**, 확정 전 보수 운영 | 노티스 명시 + 이의 수단 | `COUNSEL_CONFIRMATION_REQUIRED`(Q3·Q4) TH §2② |
| VN | 비식별 산출물은 개인정보 제외로 분석되나, 상업적 재판매 목적은 **고지 목적에 명시 + 동의 항목 포함(보수 기준선)** | 목적 고지에 익명화·통계·판매 명시 | `COUNSEL_CONFIRMATION_REQUIRED` VN §2②·§3.1 |
| CN | 익명화 처리행위의 동의 논점 + 익명이어도 중요 데이터·동물방역법 疫情 공표 금지 잔존 — **옵트인 전환 필요 여부 질의(Q11), 진입 자체 HOLD** | (HOLD) | `COUNSEL_CONFIRMATION_REQUIRED` CN §3②·§4.2, [D-07] |

### ③ AI_MODEL_TRAINING (옵트인 공통 [D-02])

| 법역 | 근거 | UI 요건 | 태그·출처 |
|---|---|---|---|
| KR | 원데이터 학습 = 옵트인 별도 동의(익명/가명 경로는 별도 트랙 — Q7) | 개별 토글, 철회 용이 | `OFFICIAL_GUIDANCE`(PIPC 생성형 AI 안내서 2025-08) KR §2③·§8 |
| EU/GB | 옵트인 동의(Art. 7 요건) — LI 가능성 있으나 옵트인이 방어적 선택. 근거 혼합 금지 | 개별 토글 + 철회 시 학습 중단 영향 고지 | `OFFICIAL_GUIDANCE`(EDPB Opinion 28/2024 방향) GB_EU §2③ |
| US | 고지 필수, 2차 목적 시 동의(VA형) — 옵트인 설계로 충족. VT(2028) LLM 학습 공개 의무 선반영 | 토글 + 프라이버시 고지 기재 | `LEGAL_REQUIREMENT` US §2③ |
| BR | 옵트인 — ANPD Meta 사건(LI 기반 AI 학습 중지명령 전례) | 개별 토글 | `CASE_OR_ENFORCEMENT` BR §2③ |
| TH | 옵트인(§19 분리동의) | 개별 토글, 태국어 제공 | `LEGAL_REQUIREMENT` TH §2③ |
| VN | 옵트인(목적 특정 원칙, ①에 묶기 불가) | 개별 토글 | `LEGAL_REQUIREMENT` VN §2③ |
| CN | 옵트인 + 국외 서버 학습 시 제39조 별도동의 중첩 | (HOLD) | `LEGAL_REQUIREMENT` CN §3③, [D-07] |

### ④ NAMED_RESEARCH (옵트인 공통 [D-02])

| 법역 | 근거 | UI 요건 | 태그·출처 |
|---|---|---|---|
| KR | 옵트인('과학적 연구' 포섭 불확실 — Q3) | 제공받는 자 범주·목적 고지 | `COUNSEL_CONFIRMATION_REQUIRED` KR §2④ |
| EU/GB | 별도 동의(식별 상태 제공 시). 익명화 후 제공이면 §3 기준 충족 시 GDPR 밖 | 토글 + 수령자 범주 고지 | GB_EU §2④ |
| US | 식별 수준 제공 = 'sale' — 옵트인 설계가 옵트아웃 요건 상회. NE 농장은 LB525 서면동의 | Do Not Sell 인프라(CA) 병행 | `LEGAL_REQUIREMENT` US §2④ |
| BR | 옵트인 필수적 — Art. 7 IV '연구' 근거는 비영리 연구기관 한정, 영리 위탁연구 사용 불가 | 토글 | `LEGAL_REQUIREMENT` BR §2④ |
| TH | 옵트인 — LI 정당화 곤란. 동의서에 상대방 범주·목적 특정 | §19 분리동의 | `LEGAL_REQUIREMENT` TH §2④ |
| VN | 옵트인 — 수령자·목적·항목 특정 | 토글 | `LEGAL_REQUIREMENT` VN §2④ |
| CN | 제23조 별도동의(单独同意) | (HOLD) | `LEGAL_REQUIREMENT` CN §3④, [D-07] |

### ⑤ TRANSACTION_MATCHING (옵트인 공통 [D-02] — 우회 불가)

| 법역 | 근거 | UI 요건 | 태그·출처 |
|---|---|---|---|
| KR | PIPA 제17조 별도 동의(제공받는 자·목적·항목·기간 고지) + 유상 제공 사실 고지 권고 | 토글 + 제공 상세 고지 | `LEGAL_REQUIREMENT` KR §2⑤ |
| EU/GB | 옵트인 — 제3자 마케팅 목적은 LI 형량 탈락 위험. ePrivacy 국가별 규제 별도(§7 게이팅) | 토글 | GB_EU §2⑤ |
| US | 명백한 'sale' — 옵트인 상회 + 브로커 등록 검토(본인 정보 한정 시 비해당 논거) | 토글 + CA Do Not Sell 링크 | US §2⑤·§3.3 |
| BR | 옵트인 — 포괄 동의 무효(Art. 8 §4) | 목적별 개별 동의 | `LEGAL_REQUIREMENT` BR §2⑤ |
| TH | 옵트인 — §19 분리동의·조건화 금지 엄수 | 토글 | `LEGAL_REQUIREMENT` TH §2⑤ |
| VN | 옵트인 + **'개인정보 매매' 성질결정 리스크(불법수익 10배 과징금)** — 예외 요건 확인 전 VN에서 ⑤ 미출시 권고 | (VN 미출시 기본) | `COUNSEL_CONFIRMATION_REQUIRED`(VN Q4) VN §2⑤·§3.2 |
| CN | 제23조 별도동의 | (HOLD) | CN §3⑤, [D-07] |

### ⑥ EXTERNAL_AI_PROCESSING (수탁+국외이전 메커니즘)

| 법역 | 메커니즘 | 별도 동의 필요? | 태그·출처 |
|---|---|---|---|
| KR | 제28조의8 제1항3호 — 계약 이행 위한 처리위탁·보관은 방침 공개(항목·국가·일시방법·수탁자·목적·기간)로 동의 갈음 | **불요**(이행 필수 시). 학습 겸용·이행 비필수면 별도 동의 | `LEGAL_REQUIREMENT` + Q5 KR §2⑥·§4 |
| EU/GB | Art. 28 DPA + Ch. V — EU/UK→KR 적정성 결정 유효(2022/254, UK 2022 Regs), KR→제3국 재이전 체인은 계약·리전·DPF 확인으로 통제 | **불요** — Art. 49(1)(a) 동의를 이전 근거로 쓰지 않음(반복 이전 부적합). 노티스 기재 필수 | `LEGAL_REQUIREMENT` GB_EU §2⑥·§4 |
| US | processor DPA. 국외이전 일반 제한 없음. 우려국 벤더 배제(DOJ Bulk Data Rule) + BIPA(이미지 내 인물) 입력 필터 | **불요** | US §2⑥·§4 |
| BR | operador 계약 + **Art. 33 브라질 SCC(Resolution 19/2024) 편입 필수**(유예 종료) | **불요**(SCC 경로) — 동의 경로는 요건 과중으로 비권장 | `LEGAL_REQUIREMENT` BR §2⑥·§4 |
| TH | processor DPA + §29 적절한 보호조치 필요 — 구체 이전수단(SCC 등)은 현지 확인 후 확정 | 수단 확정 전 보수 운영 | `COUNSEL_CONFIRMATION_REQUIRED` TH §4, [D-09] |
| VN | 위탁 법리 + **국외이전 동의(고지 항목에 수령국·수령자 포함) + TIA 60일 내 A05 제출** | **필요** — 국외이전 사실을 동의·고지 항목에 반영 | `LEGAL_REQUIREMENT` VN §2⑥·§4.1, [D-08] |
| CN | 제21조 위탁 + **제39조 국외이전 별도동의** + SCC 신고(onward transfer 명시) | **필요** | `LEGAL_REQUIREMENT` CN §3⑥, [D-07] |

---

## 3. 가입·설정 UI 스펙

### 3.1 가입 시 화면 구조

**원칙: 필수(동의 아닌 고지·계약) / 선택(개별 옵트인 토글) / 국가별 추가 동의(국외이전 등) 3계층 분리. 묶음동의 금지**(TH PDPA §19 분리동의 명문, KR 제22조, VN 목적 특정, BR Art. 8 §4 포괄동의 무효 — `LEGAL_REQUIREMENT`).

```
[STEP 1] 필수 — 체크박스 1개씩, 사전 체크 금지
  □ (필수) 이용약관 동의
  □ (필수) 개인정보 처리방침 확인   ← "동의"가 아닌 "확인" 프레임 가능 국가는 확인으로(EU) — 국가 분기
[STEP 2] 데이터 활용 안내 (② — 동의 토글 아님·스크롤 통과형 고지)  ※ EU/GB·BR·KR·US
  ▸ "귀하의 농장 데이터는 개인·농장을 알아볼 수 없는 익명·집계 통계로
     가공되어 산업 통계(유상 제공 포함)에 활용됩니다. 언제든 설정에서
     제외를 요청할 수 있습니다. [자세히 보기·이의/제외 신청]"
  ※ TH·VN(·CN): 이 항목이 별도 동의 체크박스로 전환됨 (기본 미체크)
[STEP 3] 선택 — 개별 토글, 기본 전부 OFF [D-02]
  ○ (선택·OFF) AI 모델 학습 참여        purpose: AI_MODEL_TRAINING
  ○ (선택·OFF) 기업 연구 데이터 제공     purpose: NAMED_RESEARCH
  ○ (선택·OFF) 거래연결·리드 서비스      purpose: TRANSACTION_MATCHING
  ⚠ 각 토글 하단 고정 문구: "동의하지 않아도 서비스 이용에 제한이 없습니다."
[STEP 4] 국가별 추가 블록 (country_code 분기)
  - CN: 국외이전 별도동의(수령자·연락처·목적·방식·유형·권리행사 방법 고지) — [D-07] HOLD 중 미노출
  - VN: 국외이전 고지·동의 항목(수령국=한국, TIA 제출 사실)
  - NE(US주): 농업데이터 판매 서면(전자) 옵트인 별도 화면 — "명확·현저한 고지" 요건
  - EU/GB: 대리인(Art. 27) 정보·이전 근거(적정성) 노티스 링크
```

### 3.2 문구 초안 (국문 — 번역 기준 원문)

- **② 고지형(KR)**: "회사는 회원의 농장 운영 데이터를 개인과 농장을 알아볼 수 없도록 비가역적으로 익명처리한 후 집계하여 전국·지역 단위 양돈 통계로 활용하며, 사료·동물약품·금융·연구 기관 등에 **유상으로 제공(판매)할 수 있습니다**. 익명처리된 통계는 개인정보에 해당하지 않습니다. 회원은 언제든지 [설정 > 데이터 활용]에서 향후 통계 산출 제외를 요청할 수 있습니다." (유상 명시 — KR §7(c) redline 반영)
- **② 이의권형(EU/GB·BR)**: "당사는 정당한 이익(legitimate interest)에 근거하여 귀하의 데이터를 익명·집계 통계로 가공합니다. 귀하는 언제든지 이 처리에 **이의를 제기(object)** 할 수 있습니다. [이의 제기]"
- **③ 토글**: "(선택) 내 농장 데이터를 PigOS AI 기능 개선을 위한 모델 학습에 사용하는 것에 동의합니다. 언제든 철회할 수 있으며, 철회 시 이후 학습에 사용되지 않습니다."
- **④ 토글**: "(선택) 회사가 지정·고지하는 연구기관(사료·약품·금융·연구 기관)의 연구를 위해 내 데이터를 제공하는 것에 동의합니다. 제공 상대방 범주와 항목은 [상세 고지]에서 확인할 수 있습니다."
- **⑤ 토글**: "(선택) 거래연결 서비스: 내 연락처와 거래 관심 정보를 공급업체 등 제3자에게 제공(유상 포함)하는 것에 동의합니다. 제공받는 자·목적·항목·보유기간은 [상세 고지] 참조." (KR 제17조 고지사항 — `LEGAL_REQUIREMENT`)
- **⑥ just-in-time(기능 최초 사용 시)**: "이 기능은 문서 이미지를 해외 소재 AI 처리업체({벤더명}, {국가})에 전송하여 처리합니다. 전송 데이터는 처리 후 저장되지 않으며 벤더의 모델 학습에 사용되지 않습니다. [처리업체 목록]" — VN·CN은 동의 버튼, 그 외 확인 버튼.

### 3.3 설정 화면 (내 데이터 활용 관리)

- 토글별 표기: 현재 상태(ON/OFF) · 최초 동의일 · 고지 버전(notice_version) · [철회] 버튼. 철회는 동의와 동일한 클릭 수 이내(§19 "동의만큼 쉬워야" — TH `LEGAL_REQUIREMENT`, EU Art. 7(3)).
- ② 전용 행: 토글이 아닌 "통계 활용 중 / [제외 요청]" 상태 표시(고지형 국가) 또는 토글(동의형 국가).
- 철회 시 확인 다이얼로그에 §4의 효과 범위(장래효, 기산출 익명 산출물 존속 [D-04])를 요약 고지.

### 3.4 국가 코드 분기 로직

```
jurisdiction = resolve(country_code)   # 농장 소재지 기준(계정 국적 아님). 확정 규칙: COUNSEL_CONFIRMATION_REQUIRED
switch jurisdiction:
  KR          → ②=NOTICE_EXEMPT(제58조의2)+제외요청, ⑥=위탁공개(동의 없음)
  EU / GB     → ②=LI+OBJECT, ⑥=적정성 노티스, Art.27 대리인 표기
  US(주 분기) → ②=DEIDENTIFIED+NOTICE; state==NE(농업데이터법 주 목록)이면 ②·④에 WRITTEN_OPTIN 강제
                CA면 Do-Not-Sell 링크·GPC 신호 처리 활성화
  BR          → ②=LI+OBJECT, ⑥=BR SCC 편입 확인 게이트
  TH          → ②=CONSENT_OR_LI_PENDING(보수: 동의), 출시게이트 [D-09] 미해제 시 유료·마케팅 차단
  VN          → ②=NOTICE+CONSENT(보수), ⑤=미노출, ⑥=국외이전 동의, 출시게이트 [D-08]
  CN          → 전체 HOLD [D-07] — 가입 차단
default(기타국) → EU 프로파일 적용(최고 수준 기본값) — INTERNAL_POLICY_PROPOSAL
```

---

## 4. 철회 처리 스펙

### 4.1 철회의 효과 범위 (공통 설계)

- **장래효 원칙**: 철회는 철회 전 적법 처리의 효력에 영향을 주지 않는다(KR §6.1, TH §19, BR Art. 8 §5, CN PIPL 제15조 2문 — `LEGAL_REQUIREMENT`. VN은 명문 확인 필요 — `COUNSEL_CONFIRMATION_REQUIRED` VN Q10).
- **기제공분 처리 [D-04]**: "소급회수 불가"는 **"철회 전 적법 처리 + 이미 제3자 제공 + 비가역 익명화 완료 산출물"에 한정**하여 적용한다. 개인정보·가명정보 상태의 기제공분에는 부적용을 명시한다(전 법역 공통 결론 — KR §6.1, GB_EU §6, US §6.1, BR §6, TH §6, VN §6, CN §7). 익명성 입증 실패 시 이 방어선 전체가 무너지므로 릴리스 게이트([D-05])가 전제 조건이다.
- **목적별 중단 범위**:

| purpose | 철회 시점 이후 중단되는 것 | 존속하는 것 |
|---|---|---|
| ② | 다음 통계 산출 배치부터 원데이터 투입 제외(§6 파이프라인) | 철회 전 릴리스된 익명·집계 산출물 [D-04] |
| ③ | 신규 학습 배치 투입 | 기학습 완료 모델(모델에서의 영향 제거 의무 여부 — `COUNSEL_CONFIRMATION_REQUIRED`, GB_EU §2③·KR Q7 연계. 확정 전 고지문에 "철회 이후 학습에 미사용" 수준으로만 약속) |
| ④ | 신규 제공 | 철회 전 제공분 중 익명 산출물만. 식별 상태 제공분은 수령기업 계약상 삭제 조항 발동 |
| ⑤ | 신규 리드 제공 즉시 중단 | 없음 — 기제공 리드도 수령자 이용중단 요청 대상(식별 정보이므로 [D-04] 존속 예외 비적용) |
| ⑥ | 기능 사용 중단 시 전송 중단 | 벤더 zero-retention 계약상 잔존 데이터 없음이 원칙 |

### 4.2 처리 SLA — `INTERNAL_POLICY_PROPOSAL` (법정 상한 내 설계)

| 단계 | SLA | 법정 상한·근거 |
|---|---|---|
| 철회·이의·제외요청 접수 → ledger 반영(consent_status 변경) | **즉시(시스템 자동)** | — |
| 신규 처리(학습 투입·리드 제공) 중단 | **접수 후 3영업일 내** | KR §6.1 redline "요청 후 ○영업일" 명시 요구 반영 |
| 통계 파이프라인 제외 전파(§6) | **다음 릴리스 배치 전, 최대 30일** | EU: "다음 분기 반영" 등 지연은 다툼 소지(GB_EU §6 추가 항목) |
| 삭제 요구 이행(철회 + 삭제 요청 병행 시) | **30일 (TH는 90일 법정 상한 내)** | TH 삭제 고시 90일(`LEGAL_REQUIREMENT` TH §6), KR "지체 없이" |
| 처리 결과 통지 | 이행 완료 후 7일 내 | KR §6.1 redline(통지 방법 명시) |

---

## 5. consent_ledger 스키마

동의·고지·철회의 전 이력을 append-only로 기록한다. 감사·분쟁 시 동의 입증(F5/V1 재발 방지)과 §6 릴리스 대조의 단일 원천(source of truth).

### 5.1 필드 정의

| 필드 | 타입 | 정의 |
|---|---|---|
| `ledger_id` | uuid | 레코드 식별자(불변) |
| `account_id` / `farm_id` | uuid | 동의 주체 계정·농장 (농장 단위 목적은 farm_id 필수) |
| `purpose_code` | enum | §1의 6개 코드 |
| `jurisdiction` | string | ISO 3166-1 alpha-2 (+ US는 `US-NE`처럼 주 코드) — §3.4 분기 결과값 |
| `lawful_basis` | enum | `CONTRACT` \| `CONSENT` \| `LEGITIMATE_INTEREST` \| `ANONYMIZED_EXEMPT`(KR 제58조의2) \| `DEIDENTIFIED_EXEMPT`(US) \| `PROCESSOR_TRANSFER`(⑥ 수탁·이전 메커니즘) |
| `consent_status` | enum | `GRANTED` \| `NOTICE_GIVEN`(동의 아닌 고지형 — ②·LI형) \| `WITHDRAWN` \| `OBJECTED`(Art.21형 이의) \| `EXCLUSION_REQUESTED`(KR 제외요청) \| `EXPIRED`(재동의 필요 상태) |
| `notice_version` | string | 동의/고지 시점에 제시된 고지문 버전(semver + 문서 해시) |
| `accepted_at` / `withdrawn_at` | timestamptz | 동의(고지 노출)·철회 시각. UTC |
| `effective_from` | timestamptz | 상태 효력 개시 시각(철회 레코드는 처리 중단 기준 시각 — §4.2 SLA 기산점) |
| `downstream_recipient` | string[] | 이 동의로 제공 가능한 수령자 범주 또는 계약 ID(④⑤⑥). ②는 릴리스 채널 ID |
| `collection_context` | enum | `UI_SIGNUP` \| `UI_SETTINGS` \| `UI_JIT`(기능 내 just-in-time) \| `API` \| `MIGRATION`(기존 회원 이관 — F5·V1 검증 플래그 필수) |
| `evidence_ref` | string | 동의 화면 스냅샷·체크박스 이벤트 로그·서면(NE) 파일의 저장소 URI + 해시 |

제약: (purpose_code, farm_id) 별 최신 레코드가 현재 상태. `WITHDRAWN` 이후 재동의는 신규 레코드(이력 보존). `lawful_basis=CONSENT`인데 `evidence_ref`가 없는 레코드는 무효 처리 대상(KR R2 삼중 리스크 방지).

### 5.2 예시 레코드 3건

```json
{
  "ledger_id": "0198a1b2-...-01",
  "account_id": "acc_7f3e", "farm_id": "farm_2291",
  "purpose_code": "ANON_AGG_STATS",
  "jurisdiction": "KR",
  "lawful_basis": "ANONYMIZED_EXEMPT",
  "consent_status": "NOTICE_GIVEN",
  "notice_version": "kr-privacy-3.0.0#sha256:9c1f...",
  "accepted_at": "2026-08-01T02:14:09Z",
  "withdrawn_at": null,
  "effective_from": "2026-08-01T02:14:09Z",
  "downstream_recipient": ["pigsignal_release_channel"],
  "collection_context": "UI_SIGNUP",
  "evidence_ref": "s3://consent-evidence/2026/08/acc_7f3e/signup_step2.json#sha256:b2aa..."
}
```

```json
{
  "ledger_id": "0198a1b2-...-02",
  "account_id": "acc_91cd", "farm_id": "farm_5514",
  "purpose_code": "AI_MODEL_TRAINING",
  "jurisdiction": "TH",
  "lawful_basis": "CONSENT",
  "consent_status": "WITHDRAWN",
  "notice_version": "th-consent-1.2.0#sha256:44de...",
  "accepted_at": "2026-09-12T07:30:00Z",
  "withdrawn_at": "2027-01-05T11:02:44Z",
  "effective_from": "2027-01-05T11:02:44Z",
  "downstream_recipient": [],
  "collection_context": "UI_SETTINGS",
  "evidence_ref": "s3://consent-evidence/2027/01/acc_91cd/withdraw_toggle.json#sha256:0e17..."
}
```

```json
{
  "ledger_id": "0198a1b2-...-03",
  "account_id": "acc_ab20", "farm_id": "farm_8802",
  "purpose_code": "ANON_AGG_STATS",
  "jurisdiction": "DE",
  "lawful_basis": "LEGITIMATE_INTEREST",
  "consent_status": "OBJECTED",
  "notice_version": "eu-notice-2.1.0#sha256:71c0...",
  "accepted_at": "2026-10-02T09:00:00Z",
  "withdrawn_at": "2026-11-20T16:45:10Z",
  "effective_from": "2026-11-20T16:45:10Z",
  "downstream_recipient": ["pigsignal_release_channel"],
  "collection_context": "UI_SETTINGS",
  "evidence_ref": "s3://consent-evidence/2026/11/acc_ab20/art21_objection.json#sha256:5fd9..."
}
```

---

## 6. Downstream Exclusion 스펙 (철회·제외 요청의 릴리스 반영)

`INTERNAL_POLICY_PROPOSAL` — 릴리스 게이트 수치는 [D-05]/[D-06] 확정 전 후보값.

1. **릴리스 시점 스냅샷**: 모든 PigSignal 릴리스(및 ④ 제공 배치)는 빌드 시각 `T`에 consent_ledger를 조회하여 `effective_from ≤ T`인 최신 상태 기준 **포함 대상 farm_id 목록(inclusion snapshot)** 을 생성·서명 저장한다. 스냅샷 해시는 릴리스 메타데이터에 기록한다.
2. **제외 규칙**: `WITHDRAWN` / `OBJECTED` / `EXCLUSION_REQUESTED` / `EXPIRED` 상태의 farm은 해당 purpose의 원데이터 투입 단계에서 제외한다(산출물 후처리 제외가 아닌 **입력 단계 제외**).
3. **대조 검증(release gate 일부)**: 배포 직전 파이프라인이 산출물 대상 farm 집합과 ledger 스냅샷을 자동 대조하고 불일치 시 릴리스를 차단한다. 대조 결과는 릴리스별 감사 로그로 보존.
4. **차분 공격 통제**: 직전 릴리스 대비 이탈 farm이 존재하는 셀은 차분으로 개별 값이 역산되지 않도록 억제·병합 규칙을 적용한다(GB_EU §3.2-3 차분 공격, KR §3.3). 최소 코호트·지배율 통제는 `ANONYMIZATION_AND_RELEASE_STANDARD.md`([D-05] 후보: k=10/세분화 k=20 + 단일 70%/상위2 85%)를 따른다.
5. **수령자 전파**: ④의 식별 수준 기제공분은 철회 시 수령기업에 계약상 후속 릴리스 제외·이용중단 통지를 발송하고 통지 이력을 `downstream_recipient` 연계로 기록한다. ⑤ 리드는 §4.1 표에 따라 이용중단 요청까지 발송.
6. **재식별 금지 계약 전제**: 모든 수령자 계약에 재식별 금지·재판매 제한·결합 제한 조항(US de-identified 3요건, KR §3.1, BR §3, ICO 환경 통제)이 없는 채널로는 릴리스 자체를 금지한다. `LEGAL_REQUIREMENT`(US)·`OFFICIAL_GUIDANCE`(ICO)

---

## 7. 마케팅 채널 게이팅 — B2B 콜드 이메일 [D-10]

원칙: **국가 코드 게이팅 + KR 즉시 중단**(KR R1 HIGH — 정통망법 제50조 B2B 예외 없음, 건당 과태료. `LEGAL_REQUIREMENT` KR §5).

### 7.1 발송 금지 목록 (옵트인 국가 — 사전 동의 없는 콜드 발송 금지)

| 국가 | 근거 | 태그·출처 |
|---|---|---|
| **KR** | 정통망법 제50조 — B2B 예외 없음, 명함≠동의(실무 해석, Q6) | `LEGAL_REQUIREMENT` KR §5 |
| **DE** | UWG §7(2) — B2B 포함 명시적 사전 동의, Abmahnung 집행 활발 | `LEGAL_REQUIREMENT`+`CASE_OR_ENFORCEMENT` GB_EU §5 |
| **DK** | Markedsføringsloven §10 — B2B 포함 엄격 옵트인, 건당 벌금 | `LEGAL_REQUIREMENT` GB_EU §5 |
| **IT** | Codice Privacy Art. 130 — B2B 완화 예외 없음, Garante 집행 활발 | `LEGAL_REQUIREMENT` GB_EU §5 |
| **PL** | PKE Art. 398 — B2B 포함 사전 동의 원칙 | `LEGAL_REQUIREMENT` GB_EU §5 |
| **CN** | 2006 전자우편판법·광고법 제43조·PIPL — B2B 예외 없음 | `LEGAL_REQUIREMENT` CN §6 |
| **VN** | Decree 91/2020 — 옵트인 원칙, B2B 예외 미확인 | `LEGAL_REQUIREMENT` VN §5 |

### 7.2 조건부 국가 (요건 충족 시 발송 가능 — 발송 전 요건 체크 강제)

| 국가 | 조건 | 출처 |
|---|---|---|
| ES | LSSI Art. 21 원칙 옵트인 — B2B LI 해석 여지 좁음, **확인 전 금지 목록 준용** | GB_EU §5, Q5 |
| NL | 법인 가입자 완화(개인 지정 주소는 개인 취급) — 확인 전 보수 운영 | GB_EU §5, Q5 |
| FR | 직무 관련성 있으면 고지+옵트아웃 가능(CNIL) | GB_EU §5 |
| SE | 법인 대상 옵트아웃 허용(이름@회사 주소는 논점) | GB_EU §5 |
| GB | corporate subscriber는 PECR 동의 불요(신원 표시+옵트아웃). **sole trader·파트너십은 옵트인 대상** — 농장주 다수가 개인사업자이므로 실질 보수 운영 + UK GDPR Art. 14 고지·LIA 병행 | `LEGAL_REQUIREMENT` GB_EU §5 |
| TH | 스팸법 없음·CCA §11(건당 THB 200k) — 옵트아웃 명시 + 7일 내 중단 + LIA 문서화 | TH §5 |
| BR | 전용 스팸법 없음 — LI+LIA + 출처 적법성 + CAPEM(옵트아웃) 준수 | BR §5 |

### 7.3 옵트아웃 운영권 — US CAN-SPAM 체크리스트 (`LEGAL_REQUIREMENT` US §5)

발송 시스템이 아래 8항목을 강제(미충족 시 발송 차단):
1. 헤더 진실성 — 발신자명·From·회신주소·도메인이 와이즈레이크/PigOS를 정확히 표시(대행 사용 시에도)
2. 제목줄 비기만 — 거래 가장 제목 금지
3. 광고임을 명확·현저하게 식별 가능하게 표시
4. 유효한 물리적 우편주소 기재(한국 본사 주소 가능 여부 — `COUNSEL_CONFIRMATION_REQUIRED` US Q9, 확정 전 미국 등록대리인 주소 사용)
5. 명확한 옵트아웃 수단 + 30일 이상 유효한 수신거부 링크
6. 옵트아웃 10영업일 내 이행, 수수료·로그인·추가 정보 요구 금지, 거부 주소의 제3자 이전 금지
7. 발송대행 감독 — 대행 위반도 광고주 책임
8. SMS/전화는 TCPA 별도 — 검토 전 전면 금지

공통 인프라: 전사 suppression list(옵트아웃·이의 주소 통합, 채널·국가 불문 대조), 발송 전 국가 코드 게이트 통과 로그 보존. EU 대상 수집 시 Art. 14 고지(1개월 내 또는 첫 접촉 시) 자동화(GB_EU §5 공통).

---

## 8. 미결 항목 목록

| ID | 본 스펙에서의 위치 | 미결 내용 | 상태 |
|---|---|---|---|
| [D-01] | §1 ②, §2 ②매트릭스, §3.1 STEP 2 | ②의 국가별 분기 확정(특히 KR 익명처리 행위 근거 Q2, TH LI 인정 Q3, VN 동의 요부) — V1(동의 UI·로그)·F5 해소 선행 | PROPOSED |
| [D-02] | §1 ③④⑤, §3.1 STEP 3 | ③④⑤ 옵트인·기본 OFF·개별 토글 — 확정 시 본 스펙 그대로 구현 | PROPOSED |
| [D-04] | §4.1, §6 | 기제공분 존속 범위 한정(비가역 익명화 완료 산출물 한정) 문안 확정 | PROPOSED |
| [D-05] | §6.4 | 릴리스 게이트 수치(k=10/20 + 지배율) — 변호사+통계 검증 후 확정 | OPEN |
| [D-06] | §6.4 | KR 코호트 5 → 글로벌 상향 통일 여부 | OPEN |
| [D-07] | §2 CN 전 행, §3.4 | 중국 진입 구조 HOLD — 해제 전 CN 가입 차단 유지 | OPEN |
| [D-08] | §2 ⑥ VN, §3.4 | 베트남 출시 게이트(TIA·데이터 서비스 라이선스·현지화) — 해제 전 유료·마케팅 보류, ⑤ 미노출 | OPEN |
| [D-09] | §2 ⑥ TH, §3.4 | 태국 출시 게이트(현지 대리인 §37(5)·Thai SCC) — 해제 전 유료·본격 마케팅 보류 | OPEN |
| [D-10] | §7 | 콜드 이메일 국가 게이팅 + KR 즉시 중단 — 운영 현황 V5 확인 병행 | PROPOSED |
| — | §3.4 | jurisdiction 판정 기준(농장 소재지 vs 계정), 기타국 기본 프로파일 | `COUNSEL_CONFIRMATION_REQUIRED` |
| — | §4.1 ③ | 철회 시 기학습 모델의 영향 처리 범위 | `COUNSEL_CONFIRMATION_REQUIRED` |
| — | §5.1 | MIGRATION 컨텍스트(기존 피그플랜 회원 이관)의 동의 승계 규칙 — F5·V1·V3 해소 후 별도 스펙 | 대기 |

선행 의존: 본 스펙의 최종 확정은 D-01~D-06 DECIDED + LAWYER_BRIEF 회신 이후(DECISION_REGISTER 선행 의존 관계 참조).

---

*작성: 2026-07-21, PigOS 제품·법무 스펙 세션. 근거: research/ 7개국 리서치(§2 중심), DECISION_REGISTER v1.0, CURRENT_STATE_FINDINGS v1.0.*
