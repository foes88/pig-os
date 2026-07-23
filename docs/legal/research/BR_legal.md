# PigOS 브라질 법무 리서치 — LGPD 및 관련 규제 분석 (초안)

## 0. 문서 성격 및 검토 기준일

> **본 문서는 브라질 변호사(현지 자격 보유) 검토 전 초안(draft)이다.** 법률 자문이 아니며, 약관·계약·상품 설계의 최종 근거로 사용할 수 없다. "적법/위법" 단정은 하지 않고, 요건·리스크·질의 형태로 서술한다. 확인하지 못한 사항은 "미확인 — 변호사 질의"로 표기했다.
>
> - **검토 기준일: 2026-07-21** (웹 확인 수행일)
> - 대상 서비스: 글로벌 양돈 SaaS "PigOS" (운영: 한국 법인 와이즈레이크, 서버: 한국)
> - 검토 범위: LGPD 적용·법적 근거 매핑·익명화·국외 이전·B2B 아웃리치·철회/삭제권·소규모 처리자·인테그레이터 이슈

---

## 1. 적용 법제

| 법령/규정 | 내용 | 확인 근거 |
|---|---|---|
| **LGPD** (Lei Geral de Proteção de Dados, Lei nº 13.709/2018) | 개인정보 일반법. 법적 근거 10종(Art. 7), 민감정보(Art. 11), 익명화(Art. 5 XI, 12), 역외 적용(Art. 3), 국외 이전(Art. 33), 제재(Art. 52, 브라질 내 매출의 2%·건당 최대 R$5,000만) | 원문: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm |
| **Resolution CD/ANPD nº 19/2024** | 국외 이전 규정 + 브라질 표준계약조항(SCC). 기존 계약의 SCC 편입 유예기간 **2025-08-23 종료(경과)** | https://www.mayerbrown.com/en/insights/publications/2025/08/end-of-grace-period-implementation-of-brazils-standard-contractual-clauses-in-international-transfers-of-personal-data |
| **Resolution CD/ANPD nº 2/2022** | 소규모 처리자(ATPP: agentes de tratamento de pequeno porte) 완화 규정 (DPO 임명 면제, 기록 간소화, 기한 2배 등) | https://habeasdata.kvlaw.com.br/en/regulamento-de-aplicacao-da-lgpd-para-agentes-de-tratamento-de-pequeno-porte-esta-em-vigor/ |
| **Resolution CD/ANPD nº 32/2026** (2026-01-27) | **EU/EEA에 대한 브라질 최초 적정성 결정** (EU 집행위의 브라질 적정성 결정 2026-01-26과 상호 인정). **한국은 미포함** | https://www.whitecase.com/insight-alert/mutual-adequacy-between-eu-and-brazil-new-era-transatlantic-data-transfers |
| **ANPD 정당한 이익 가이드** (Guia Orientativo sobre Legítimo Interesse, 2024-02) | Art. 7 IX·Art. 10 적용 3단계 LIA(목적 적법성 → 필요성 → 형량·안전장치), 민감정보에는 LI 사용 불가, LIA 문서화 권고 | https://www.mattosfilho.com.br/en/unico/anpd-legal-data-processing-brazil/ |
| **ANPD 규제 아젠다 2025–2026 (16개 과제) + 우선순위 맵 2026–2027** (2025-12-24 공표) | 익명화·가명처리, AI, 고위험 처리, DPIA, 동의 등 규정화 예정. **익명화·AI 규정은 아직 확정 전** → 현재는 법문+가이드 기준으로 보수적 설계 필요 | https://www.machadomeyer.com.br/en/recent-publications/publications/digital-law/anpd-s-2025-2026-regulatory-agenda-highlights-16-topics / https://www.trenchrossi.com/en/legal-alerts/anpd-publishes-map-of-priority-issues-2026-2027-biennium-and-update-of-the-regulatory-agenda-2025-2026-biennium/ |
| **Marco Civil da Internet** (Lei nº 12.965/2014) | 인터넷 서비스 일반(프라이버시 보호) | https://www.planalto.gov.br/ccivil_03/_ato2011-2014/2014/lei/l12965.htm |
| **소비자보호법 CDC** (Lei nº 8.078/1990) | 전자 마케팅·약관 남용조항 통제. 소규모 개인 농가에 적용될 가능성(완화된 최종수요자론) — 미확인 — 변호사 질의 | https://www.dlapiperdataprotection.com/index.html?t=electronic-marketing&c=BR |
| **CAPEM** (이메일 마케팅 자율규제 코드) | 자율규제(법적 구속력 없음): 사전 동의 또는 기존 관계(soft opt-in), 발신자 식별, 옵트아웃 의무 | https://mmnj.adv.br/2021/08/01/c%C3%B3digo-de-autorregulamenta%C3%A7%C3%A3o-para-a-pr%C3%A1tica-de-e-mail-marketing-capem/ |
| **인테그레이션 계약법** (Lei nº 13.288/2016) | 양돈 등 계약생산(integração)에서 인테그레이터–계약농가 간 권리·의무·정보제공 규율 | https://www2.camara.leg.br/legin/fed/lei/2016/lei-13288-16-maio-2016-783112-norma-pl.html |
| (참고) Resolution CD/ANPD nº 15/2024(침해 통지), nº 18/2024(DPO/encarregado 규정) | 침해신고 절차·DPO 역할 규정. 세부 요건 — **미확인 — 변호사 질의** | gov.br/anpd (세부 미확인) |

**역외 적용(Art. 3) — 당사 해당 여부**: LGPD는 (i) 브라질 영토 내 처리, (ii) **브라질 내 개인에 대한 재화·서비스 제공 목적 처리**, (iii) **브라질에서 수집된 개인정보 처리** 중 하나에 해당하면 처리자의 소재지와 무관하게 적용된다(Art. 3 I–III). PigOS가 브라질 농가를 대상으로 서비스하면 (ii)·(iii)에 해당하여 **한국 법인·한국 서버라도 LGPD 적용 대상으로 보는 것이 안전**하다. GDPR과 달리 LGPD에는 역외 사업자의 **국내대리인 지정 의무 조항이 없다**(단, DPO/encarregado 지정 의무는 존재 — §7 참조).

**중요한 전제 — "개인정보"의 범위**: LGPD는 자연인(pessoa natural) 정보만 보호한다. 법인 농장의 순수 운영·생산 데이터(두수, 사료, 폐사율 등)는 그 자체로는 개인정보가 아닐 수 있다. 그러나 브라질 양돈 농가 상당수는 **개인 명의(CPF) 농업생산자**이며, 이 경우 농장 데이터가 개인과 연결되어 개인정보로 취급될 소지가 크다. 사용자 계정정보·연락처·직원/수의사 정보는 명백히 개인정보다. → 개인사업 농가 비중과 데이터 항목별 분류는 변호사 질의(§8 Q1).

---

## 2. 데이터 사용 목적 6종별 법적 근거(base legal) 매핑

LGPD Art. 7의 10개 근거: I 동의 / II 법적 의무 / III 공공정책 / IV **연구기관(órgão de pesquisa)의 연구** / V 계약 이행 / VI 소송상 권리행사 / VII 생명보호 / VIII 보건 / IX **정당한 이익(legítimo interesse)** / X 신용보호.

| 목적 | 1순위 근거(안) | 대안/비고 | 리스크 |
|---|---|---|---|
| ① 서비스 운영(필수) | **Art. 7 V 계약 이행** | 부수적 보안·부정방지는 Art. 7 IX(LI) 병용 | LOW |
| ② 익명·집계 통계(기본, PigSignal 판매) | **익명화 "처리행위" 자체 → Art. 7 IX LI + LIA** | 완전 익명화 달성 후 산출물은 LGPD 밖(Art. 12). 단 익명화 불충분 시 전체가 개인정보 처리로 회귀. 옵트아웃+투명성은 LI 형량에 유리 | MED |
| ③ AI 모델 학습(선택) | **동의(옵트인) — 설계안 유지 권장** | LI도 이론상 가능하나 ANPD의 Meta 사건(2024)에서 LI 기반 AI 학습에 예방조치(중지명령)를 발동했고, 투명성·옵트아웃·아동 배제 등 강한 안전장치 하에서만 재개 허용. B2B 농장 데이터라도 개인 농가 데이터 포함 시 보수적 접근 필요 | MED |
| ④ 특정 기업 연구(선택) | **동의(옵트인) 필수적** | Art. 7 IV의 "연구" 근거는 **비영리 연구기관(órgão de pesquisa, Art. 5 XVIII)에 한정** — 영리기업 위탁연구에는 사용 불가. LI는 제3자 이익 형량에서 불리 | MED |
| ⑤ 거래연결·리드 제공(선택) | **동의(옵트인) 필수적** | 제3자에게 식별 상태로 제공 → 정보주체의 합리적 기대 범위 밖일 가능성 높아 LI 형량 통과 곤란. 동의는 특정적·목적별이어야 하며 포괄 동의는 무효(Art. 8 §4) | HIGH(동의 없이는) / LOW(옵트인 시) |
| ⑥ 외부 AI 처리(OCR 등, 국외 이전 수반) | **처리 근거: Art. 7 V(계약 이행) + 수탁자(operador) 계약** | 국외 이전은 근거와 별도로 Art. 33 이전 메커니즘 필요(§4). 이전 근거를 "동의"로 잡을 경우 특정적·명시적·사전고지 요건(Art. 33 VIII) 부담 큼 → SCC 권장 | MED |

**동의 vs LI 선택 전략**:
- ANPD 가이드(2024-02)상 LI 사용 시 **3단계 LIA**(목적의 적법성·구체성 / 필요성·최소침해 / 형량·합리적 기대·안전장치) 수행이 사실상 요구되고, ANPD는 LIA 기록 제출을 요구할 수 있다(Art. 10 §3). 문서화는 "권고"이나 실무상 필수로 취급 권장.
- **민감정보(Art. 11)에는 LI 사용 불가.** 농장주 건강·생체정보가 유입되지 않도록 입력 필드 설계 단계에서 차단 필요.
- 글로벌 설계안(선택 목적 옵트인·기본 OFF)은 브라질에서 **가장 방어력이 높은 구조**다. 목적 ②를 옵트아웃+LI로 두는 분기는 LIA 문서화·고지·형량이 전제되어야 하며, 한국 스냅샷의 옵트아웃 모델을 그대로 이식하는 것보다 리스크가 있다(§6 참조).
- 동의 채택 시 유의: 목적별 개별 동의, 포괄 동의 무효(Art. 8 §4), 언제든 철회 가능(Art. 8 §5), 목적 변경 시 재동의(Art. 8 §6, Art. 9 §2). 동의 철회가 잦은 환경에서는 운영상 LI가 안정적이라는 실무 견해도 있으나, 위 형량 요건이 관건.

참고(Meta 사건): ANPD는 2024-07 Meta의 LI 기반 AI 학습을 잠정 중지시켰다가, 투명성 강화·옵트아웃 제공 등 컴플라이언스 플랜 승인 후 재개를 허용했다. https://fpf.org/blog/processing-of-personal-data-for-ai-training-in-brazil-takeaways-from-anpds-preliminary-decisions-in-the-meta-case/ / https://digitalpolicyalert.org/event/22305-announced-suspension-of-preventive-measures-and-approval-of-compliance-plan-in-anpd-investigation-into-metas-privacy-policy-allowing-the-use-of-personal-data-for-ai-training

---

## 3. 익명·집계 정보의 법적 지위와 판매 요건

- **법적 지위**: 익명화된 데이터(dado anonimizado, Art. 5 XI)는 원칙적으로 개인정보가 아니다(Art. 12 본문). 따라서 **완전 익명·집계된 PigSignal 산출물의 유상 판매 자체는 LGPD의 직접 규율 대상 밖**이라는 구성이 가능하다.
- **재식별 가능성 기준**: 익명화가 "**합리적 수단(meios razoáveis)**"으로 되돌릴 수 있으면 개인정보로 취급된다(Art. 12 본문·§1). 합리성은 **비용·시간·가용 기술** 등 객관적 요소로 판단한다(§1). 또한 행동 프로파일 형성에 사용되는 경우 개인정보로 간주될 수 있음에 유의(Art. 12 §2).
- **코호트 최소 5에 대한 관점**: LGPD·ANPD 규정에는 **수치 기준이 없다**. ANPD는 2024-02 익명화·가명처리 예비연구 공개 협의를 진행했고(https://www.mattosfilho.com.br/en/unico/anonymization-pseudonymization-subject-rights/), 규제 아젠다 2025–2026 Phase 1 과제로 규정화가 예정되어 있으나 **2026-07 현재 확정 규정 미확인**. 따라서 k=5는 "충분"의 보증이 아니라 하나의 통제수단일 뿐이며, 특히 **특정 지역·특정 인테그레이터 계열 농가가 소수인 세그먼트**에서는 k=5로도 간접 재식별(싱글링아웃) 가능성이 남는다. 리스크 기반 평가(모집단 밀도, 준식별자 조합, 공개 데이터 결합 가능성)를 문서화해 두는 것이 방어에 유리. → 익명화 적정성 평가 방법론은 변호사+기술 검토 병행(§8 Q3).
- **판매 요건 정리(안)**: (i) 익명화 이전 단계의 처리에 유효한 근거(②의 LI 또는 동의) + 고지, (ii) 익명화 기법·재식별 통제의 문서화, (iii) 구매기업 계약에 재식별 금지·결합 제한 조항, (iv) 익명화 실패 시 처리 중단·통지 절차. ANPD 익명화 규정 확정 시 재검토 트리거 설정.

---

## 4. 국외 이전(브라질 → 한국 서버) 요건

- **적용**: 브라질 농가 데이터가 한국 서버에 저장되는 구조는 LGPD Art. 33의 **국제 이전(transferência internacional)**에 해당. 목적 ⑥(외부 AI 처리)이 제3국 벤더를 쓰면 재이전(onward transfer)도 발생.
- **한국의 적정성**: **ANPD의 적정성 인정 없음.** 2026-07 현재 ANPD가 인정한 적정성은 **EU/EEA가 유일**(Resolution CD/ANPD 32/2026, 2026-01-27; EU 측 브라질 적정성 결정과 상호 인정, 4년 내 재검토). 한국은 EU 적정성은 보유하나 브라질 기준으로는 무관. → **한국 이전은 적정성 루트 사용 불가.**
  - 출처: https://www.whitecase.com/insight-alert/mutual-adequacy-between-eu-and-brazil-new-era-transatlantic-data-transfers / https://lefosse.com/en/news/alerts/international-transfers-of-personal-data-anpd-announces-mutual-adequacy-decision-between-brazil-and-the-european-union/
- **실무 경로 — 브라질 SCC (Resolution CD/ANPD 19/2024)**:
  - 이전 메커니즘: 적정성 / **ANPD 표준계약조항(SCC)** / 동등조항(현재 승인 사례 없음) / BCR(ANPD 승인 필요) / 특정 상황 근거(명시적 동의 등, Art. 33 VIII — 특정적·명시적·사전고지 요건으로 SaaS 대량 이용에 부적합).
  - **SCC 본문은 수정 불가**(수정 시 무효 리스크), 지정 필드(당사자, 역할[controller/operator, exporter/importer], 데이터 범주, 목적, 보유기간, 보안조치, 재이전 조건)만 기입.
  - **기존 계약 편입 유예기간 2025-08-23 종료** — 신규 진출인 PigOS는 **출시 시점부터 SCC 편입 필수**. 브라질 약관 부속조항 또는 별도 부속서(SCC 원문 포르투갈어)로 편입하는 방식 설계 필요.
  - 출처: https://www.mayerbrown.com/en/insights/publications/2025/08/end-of-grace-period-implementation-of-brazils-standard-contractual-clauses-in-international-transfers-of-personal-data / https://www.trade.gov/market-intelligence/brazils-new-rules-international-data-transfers
- **부수 의무**: 프라이버시 고지에 이전 사실·목적지국·메커니즘 명시, ⑥의 외부 AI 벤더(제3국)에 대한 재이전 조건 SCC 반영, 이전 기록 유지.
- **미확인 — 변호사 질의**: SCC를 B2B 클릭랩 약관 부속으로 편입하는 방식의 유효성(서명 요건 여부), 완전 익명·집계 데이터의 국외 반출은 Art. 33 적용 제외로 볼 수 있는지.

---

## 5. B2B 콜드 아웃리치(콜드 이메일) 적법성

- **LGPD 관점**: 브라질에는 별도 스팸 금지법이 없고, 업무용 이메일 주소라도 개인 식별 가능하면 LGPD 적용. B2B 마케팅의 근거로는 **동의 또는 정당한 이익(LI)** 이 논의되며, LI 채택 시 LIA + (i) 출처 적법성(스크래핑·구매 리스트는 형량에 매우 불리), (ii) 직무 관련성(양돈 관련 직책), (iii) 첫 메일 내 출처 고지·간편 옵트아웃, (iv) 옵트아웃 즉시 이행이 요구된다. 출처: https://www.dlapiperdataprotection.com/index.html?t=electronic-marketing&c=BR
- **자율규제(CAPEM)**: 법적 구속력은 없으나 실무 표준 — 사전 동의 또는 기존 거래관계(soft opt-in), 발신자 명확 표시, 유효한 옵트아웃 제공. 위반 시 평판·ISP 차단 리스크. 출처: https://mmnj.adv.br/2021/08/01/c%C3%B3digo-de-autorregulamenta%C3%A7%C3%A3o-para-a-pr%C3%A1tica-de-e-mail-marketing-capem/
- **소비자법(CDC) 관점**: 수신자가 개인 농가(최종수요자로 인정될 경우) CDC의 남용적 관행 규제가 중첩될 수 있음. 판례상 "완화된 최종수요자론(finalismo mitigado)" 적용 여부는 사안별 — **미확인 — 변호사 질의**.
- **실무 권고(안)**: 회사 대표주소(contato@) 우선 사용, 개인 주소는 공개된 직무 정보 기반으로 최소화, 발송 전 LIA 기록, 수신거부 리스트 전사 관리.

---

## 6. 철회·삭제권 범위 — "기제공분 소급회수 불가" + "20년 보유"의 방어 가능성

- **철회의 효력**: 동의 철회는 장래효(Art. 8 §5 — 철회 전 처리의 유효성 유지). 따라서 **철회 이전에 적법하게 익명·집계되어 제3자에게 제공된 산출물의 소급 회수 불가 조항은 구조적으로 방어 가능성이 있다.**
- **삭제권과의 관계**: 삭제권(Art. 18 VI)은 "동의에 기반해 처리된 **개인정보**"가 대상. **완전 익명화된 데이터는 개인정보가 아니므로 삭제권 대상 밖**(Art. 12). 또한 처리 종료 후에도 통계 목적 등을 위해 **익명화된 형태의 보존은 허용**(Art. 16 IV — 컨트롤러의 배타적 사용, 제3자 접근 차단, 익명화 조건. 그 외 Art. 16 I 법적 의무 등).
- **20년 보유 조항의 평가**: 보유 대상이 **완전 익명·집계 데이터라면** LGPD 보유기간 규율 밖이어서 20년 자체가 직접 위법 쟁점이 되기 어렵다. 다만 (i) 익명화가 불충분하면 필요최소·목적구속 원칙(Art. 6 I·III) 위반으로 전환되는 취약점, (ii) Art. 16 IV의 "배타적 사용" 요건과 **제3자 판매 모델 간 긴장** — 탈퇴 후 보존 데이터를 계속 신규 판매 상품에 쓰는 것이 Art. 16 IV로 커버되는지 불명확(핵심 질의, §8 Q6), (iii) CDC상 남용조항 심사 가능성이 남는다.
- **설계 권고(안)**: "탈퇴 시 개인정보는 삭제, 익명·집계 산출물은 재식별 불가 상태로 존속하며 삭제 대상이 아님"을 고지 문구로 명확화. 20년이라는 숫자보다 "익명화 시점 이후 LGPD 밖"이라는 논리를 앞세우되, 익명화 적정성 문서로 뒷받침.

---

## 7. 소규모 처리자(ATPP) 완화 + 인테그레이터 이슈

**7.1 소규모 처리자 (Resolution CD/ANPD 2/2022)**
- 대상: 영세기업(ME)·소기업(EPP)·**스타트업(Lei Complementar 182/2021 기준)** 등. 매출 상한은 LC 123/2006(ME/EPP)·LC 182/2021(스타트업, 연매출 R$1,600만 이하 등) 기준으로 판단 — 상한 수치의 현행성은 **미확인 — 변호사 질의**.
- 제외: **고위험 처리**(대규모 처리, 민감정보 등 Resolution Art. 4 기준) 수행 시 완화 적용 배제, 경제그룹 합산 매출 초과 시 배제.
- 완화 내용: **DPO(encarregado) 임명 면제**(단 정보주체 소통채널은 필수), **간소화된 처리기록(ANPD 템플릿)**, 정보주체 요청·ANPD 통지·침해신고 **기한 2배**, 간소화된 보안정책·침해신고 절차.
- 출처: https://habeasdata.kvlaw.com.br/en/regulamento-de-aplicacao-da-lgpd-para-agentes-de-tratamento-de-pequeno-porte-esta-em-vigor/
- **와이즈레이크 해당 여부 — 핵심 쟁점**: (i) **외국(한국) 법인이 브라질 법상 ME/EPP/스타트업 정의에 포섭되는지 불명확**(브라질 사업자 등록 전제 개념일 가능성), (ii) PigSignal의 산업 데이터 대량 집적이 "대규모/고위험 처리"로 평가되면 어차피 배제. → **완화 적용을 전제로 컴플라이언스를 설계하지 말 것.** DPO는 임명하는 방향을 기본값으로 권장(외부 DPO 서비스 가능 — Resolution CD/ANPD 18/2024, 세부 미확인). §8 Q7.

**7.2 인테그레이터 소속 농장 데이터 권리 귀속**
- 브라질 양돈은 BRF, JBS/Seara, Aurora 등 인테그레이터 계약생산 비중이 높음. **Lei 13.288/2016**이 인테그레이터–계약농가(integrado) 관계·정보의무를 규율하며, 실제 데이터 귀속은 개별 인테그레이션 계약이 좌우한다. 출처: https://www2.camara.leg.br/legin/fed/lei/2016/lei-13288-16-maio-2016-783112-norma-pl.html
- 쟁점: (i) 사료·유전자원·사양 프로그램이 인테그레이터 소유인 구조에서 **생산성 데이터에 대한 인테그레이터의 계약상 권리(영업비밀·비밀유지 조항) 주장 가능성**, (ii) 농가가 PigOS에 입력하는 행위가 인테그레이션 계약의 비밀유지 위반이 될 위험(와이즈레이크에 대한 제3자 채권침해 유사 청구 리스크), (iii) 집계 데이터에서 특정 인테그레이터 계열의 성과가 드러나는 경우 경쟁정보 분쟁. LGPD 문제라기보다 **계약·영업비밀·경쟁법 이슈**이며, 약관에 "이용자는 입력 데이터에 대한 적법한 권리 보유를 보증"하는 진술보증 + 인테그레이터 식별 가능 세그먼트 통계 억제 설계가 필요. → §8 Q8.

---

## 8. 변호사 확인 필수 질의 목록

1. **Q1. 개인정보 경계**: 개인 명의(CPF) 농업생산자의 농장 운영 데이터를 어디까지 개인정보로 취급해야 하는가? 법인 농장 데이터 중 개인정보로 전환되는 항목(담당자, 위치정보 등) 분류 기준.
2. **Q2. 목적 ② 근거 확정**: 익명화 전 단계 처리를 LI+옵트아웃으로 운영하는 설계의 LIA 통과 가능성. ANPD 심사 실무 기준 및 LIA 문서 포맷.
3. **Q3. 익명화 적정성**: 코호트 5 기준이 브라질 실무(ANPD 예비연구·향후 규정)상 방어 가능한 수준인지. 재식별 위험 평가 방법론과 규정 확정 시 소급 영향.
4. **Q4. SCC 편입 방식**: Resolution 19/2024 SCC를 B2B 온라인 약관 부속서(클릭랩)로 편입하는 방식의 유효성, 포르투갈어 원문 요구 여부, 서명·형식 요건. 외부 AI 벤더 재이전 체인 구성.
5. **Q5. 익명 데이터의 국외 반출**: 완전 익명·집계 데이터의 한국 이전이 Art. 33 적용 제외로 정리되는지.
6. **Q6. Art. 16 IV 해석**: 탈퇴 후 보존한 익명 데이터를 신규 상업 상품(PigSignal)에 계속 사용하는 것이 "컨트롤러의 배타적 사용" 요건과 충돌하는지. "20년 보유+소급회수 불가" 문구의 CDC 남용조항 심사 리스크.
7. **Q7. ATPP 해당성 및 DPO**: 한국 법인이 ATPP(스타트업) 완화를 원용할 수 있는지; 불가 시 encarregado 지정 방식(현지 외부 DPO 수탁 가능 여부, Resolution 18/2024 요건), 역외 사업자의 실무상 연락체계 요건.
8. **Q8. 인테그레이터 이슈**: 계약농가의 데이터 입력이 인테그레이션 계약 위반이 될 경우 와이즈레이크의 책임 구조; 진술보증·면책 조항 설계; 인테그레이터 식별 가능 통계의 영업비밀·경쟁법 리스크.
9. **Q9. B2B 콜드 이메일**: 공개 출처 기반 직무 이메일 발송의 LI 구성 요건과 최근 ANPD/사법 집행 사례 유무; CDC 중첩 적용 여부.
10. **Q10. 미확인 규정 최신화**: Resolution 15/2024(침해통지)·18/2024(DPO) 세부 요건, 익명화·AI·고위험 처리 규정 초안 진행 상황(2025–2026 아젠다), Digital ECA(아동·청소년) 관련 신규 의무의 당사 무관성 확인.

---

## 9. 리스크 등급표

| # | 이슈 | 등급 | 근거 한 줄 |
|---|---|---|---|
| 1 | 한국 서버 국외 이전 (SCC 미편입 상태 개시) | **HIGH** | 적정성 없음 + SCC 유예기간(2025-08-23) 이미 종료 → 출시 시점부터 SCC 필수 |
| 2 | 목적 ⑤ 리드 제공을 동의 없이 운영 | **HIGH** | 제3자 제공은 합리적 기대 밖 → LI 형량 통과 곤란, 옵트인 필수적 |
| 3 | 인테그레이터 계약과의 충돌 (데이터 권리 귀속) | **MED–HIGH** | 계약생산 비중 높고 데이터 귀속이 개별 계약에 좌우 — 진술보증·통계 억제 설계 전 미해결 |
| 4 | 익명화 적정성 (코호트 5 충분성) | **MED** | 수치 기준 없음 + ANPD 익명화 규정 제정 중 → 실패 시 ②·⑥·보유 조항 전체가 개인정보 규율로 회귀 |
| 5 | 목적 ③ AI 학습 근거 | **MED** | Meta 사건에서 LI 기반 AI 학습에 중지명령 전례 — 옵트인 설계 유지 시 완화 |
| 6 | "20년 보유+소급회수 불가" 조항 | **MED** | 완전 익명화 전제 시 방어 논리 존재하나 Art. 16 IV 해석·CDC 남용조항 심사 리스크 잔존 |
| 7 | ATPP 완화 원용 불가 가능성 (DPO 의무) | **MED** | 외국 법인의 해당성 불명확 + 대규모 처리 시 배제 → DPO 지정 기본값 권장 |
| 8 | B2B 콜드 이메일 | **LOW–MED** | 전용 스팸법 없음, LI+옵트아웃+CAPEM 준수 시 관리 가능하나 리스트 출처가 관건 |
| 9 | 목적 ① 서비스 운영 | **LOW** | 계약 이행(Art. 7 V)으로 안정적 |
| 10 | 목적 ② 익명 통계 (옵트인/옵트아웃 분기) | **LOW–MED** | LI+LIA+투명성으로 구성 가능하나 익명화 적정성(#4)에 종속 |

---

*본 초안은 2026-07-21 기준 공개 자료 웹 확인에 기반하며, 포르투갈어 원문 규정 전문 대조는 수행하지 않았다. 모든 결론은 브라질 현지 변호사 검토를 거쳐 확정할 것.*
