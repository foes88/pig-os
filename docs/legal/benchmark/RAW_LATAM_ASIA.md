# RAW BENCHMARK — 양돈/축산 SaaS 약관·개인정보 (LATAM · 아시아)

- 작성일: 2026-07-22
- 목적: PigOS 글로벌(BR·CN·VN·TH 등) 약관/개인정보 부속서 설계를 위한 실제 게시 문안 구조 벤치마크
- 방법: WebSearch + WebFetch로 실제 공개된 Terms/Privacy 페이지 구조·접근방식만 추출. 문안 대량 복사 금지, 1문장 이하 핵심 문구만 인용. WebFetch 실패 시 우회하지 않고 다른 서비스로 대체.
- 저작권: 아래 인용은 조항의 존재·접근방식을 입증하기 위한 최소 인용(각 항목 한 구절 이하).

조사 완료 서비스: **Agriness (BR, 최우선)**, 农信互联/Nxin 猪联网 (CN), CPF/Charoen Pokphand Foods (TH), PigPro (VN), PorciWeb (LATAM/콜롬비아·스페인어). 보조 참고: 中 牧原·温氏(공개 약관 없음, 아래 주석), 韓 팜스플랜/이지팜(직접경쟁, 아래 주석).

---

## 카드 1 — Agriness (브라질, LATAM 최대 양돈 SW) ★최우선

- **문서·URL·언어**: Privacy Notice 존재. EN: `https://agriness.com/en/privacy-notice/` / PT: `https://agriness.com/politica-de-privacidade/`. 포르투갈어 원본 + 영어 병행. (독립 ToS는 별도 확인 안 됨 — 개인정보 문서에 데이터소유·활용이 통합 서술)
- **데이터 소유권**: DB 소유권을 **Agriness에 귀속**시킴. PT "a base de dados...é de nossa propriedade e está sob nossa responsabilidade" (수집으로 형성된 DB는 자사 소유·책임). → 고객 원장 데이터가 아닌 "수집으로 형성된 DB"를 자사 자산으로 명시.
- **집계·익명 데이터 활용/판매**: **명시적 상업 활용**. PT "dados agregados e anonimizados, com empresas especializadas em marketing e análise de dados" (집계·익명화 데이터를 **마케팅·데이터분석 전문업체와 공유**). EN "aggregated and anonymized, can be freely shared." → 판매 명시는 아니나 **제3자(마케팅/분석사) 공유를 정면으로 허용**. LATAM 시장의 실제 선례로 강력.
- **LGPD 특유**:
  - 법적 근거: **동의(consentimento)** 를 신제품 개발·개선 활용의 근거로 명시("com o seu consentimento, poderemos utilizar seus dados para...novos produtos"). 정당한 이익(legítimo interesse)을 별도 base로 정식 구분하진 않음 — 계약이행·법적의무는 서술되나 LIA식 명명은 없음.
  - 국제이전: **타국 발생 데이터를 브라질로 이전·호스팅**("Dados originários de outros países são transferidos para o Brasil"). 즉 브라질 중앙 집중형.
  - ANPD/DPO: **ANPD 통지 의무 명시**("notificará a Autoridade Nacional de Proteção de Dados (ANPD)...em prazo razoável"). 단 **명명된 Encarregado(DPO) 직함은 없음**, 연락 창구 `privacy@agriness.com`만 제공.
- **AI/자동화**: 자동화 의사결정 기준·절차 정보요청권 명시("criteria and procedures used for automated decision"). AI 학습 활용은 위 "신제품 개발" 동의 조항으로 포괄.
- **관할·분쟁**: 브라질법·**Florianópolis/SC 관할**("eleito o foro de Florianópolis/SC").
- **보유·삭제**: 계약관계 존속 동안 보유, 목적 종료 후 **폐기 또는 익명화**("descartadas ou anonimizadas").
- **특이(인테그레이터-계약농가 귀속)**: 해당 조항 **없음**. Agriness는 이 문제를 약관에서 다루지 않음 → PigOS가 인테그레이터 모델을 명문화하면 시장 대비 차별점.

---

## 카드 2 — 农信互联(Nxin) / 猪联网 (중국) 

- **문서·URL·언어**: 隐私政策(개인정보처리방침) 존재. `https://passport.nxin.com/home/agreement/50171`. 중국어. (농업/양돈 B2B 플랫폼 猪联网 운영사)
- **데이터 소유권**: 소유권 귀속은 **명시 안 함**. 대신 이용자 권리 강조("您有权查阅、复制、转移您的个人信息" 열람·복제·이전권).
- **집계·익명 활용**: **去标识化 정보 자사 활용권 명시**("我们有权使用已经去标识化的信息" 비식별화된 정보는 사용할 권리가 있음). 판매 언급은 없음.
- **아시아 특유(PIPL·현지화·중요데이터)**:
  - PIPL 명시 인용은 **없음**("法律法规要求"로 포괄) — 중국 중소 플랫폼의 전형.
  - **데이터 현지화 명시**: "将...您的个人信息存储于中华人民共和国境内" (개인정보를 **중국 경내 저장**).
  - 중요데이터: 명시적 "重要数据" 용어는 없으나 敏感信息에 "加密、权限控制、去标识化"(암호화·권한통제·비식별) 적용.
  - 跨境(국경간): "目前，我们不会将...传输至境外，如果...将会遵循相关国家规定或者征求您的同意" (**현재 국외이전 안 함**, 이전 시 규정 준수+동의).
- **AI/데이터 활용**: 별도 AI 조항 없음. 去标识화 활용권이 사실상 분석·모델 활용 근거.
- **관할·분쟁**: "向被告住所地有管辖权的法院提起诉讼" (**피고 주소지 법원** 관할) — 중국 표준.
- **보유·삭제**: "自交易完成之日起不少于三年"(거래완료 후 **최소 3년** 보유) 후 "删除或匿名化"(삭제 또는 익명화).
- **특이**: 인테그레이터-농가 귀속 조항 없음.

---

## 카드 3 — CPF / Charoen Pokphand Foods (태국) 

- **문서·URL·언어**: Master Privacy Notice 존재(HR·Vendor 별도 notice도 운영). `https://www.cpfworldwide.com/en/privacynotice`. 영어/태국어. (태국 최대 축산·양돈 통합업체 — 인테그레이터 원형)
- **데이터 소유권**: 소유권 조항 별도 없음(전형적 개인정보 notice 형식).
- **집계·익명 활용**: 삭제 대안으로 **익명화** 제시("anonymize your Personal Data, unless...continue to retain"). 상업적 판매 언급 없음.
- **아시아 특유(태국 PDPA)**:
  - **PDPA 정면 인용**: "Personal Data Protection Act B.E. 2562 (2019) and subordinate laws" — 아시아 카드 중 **법령 인용이 가장 명확**.
  - 법적근거 5종 병기: 계약·**legitimate interest**·동의·법적의무·생명/건강 위험방지 → 태국은 정당한이익 base 활용이 정착.
  - 정보주체 권리 8종(열람·이동·이의·삭제·제한·정정·동의철회·불복) 명시.
  - 국경간이전: 수령국 "sufficient standard for the protection" 확인 의무.
  - **DPO 명시**: `dpooffice@cpf.co.th` + 실주소(방콕 Silom) → 아시아 카드 중 **유일하게 명명된 DPO 창구**.
- **AI/데이터 활용**: 행동 프로파일링·개인화 마케팅·행동분석을 **동의 필요 목적**으로 공개.
- **관할·분쟁**: (개인정보 notice에는 관할 조항 없음 — 계약서 본문 소관)
- **보유·삭제**: 법정 요건 없으면 "**not exceeding 10 years**" (관계 종료일 기산 최대 10년).
- **특이**: 인테그레이터 원형 기업이나, 계약농가 데이터 귀속은 이 공개 notice에서 다루지 않음(개별 계약 소관 추정).

---

## 카드 4 — PigPro (베트남) 

- **문서·URL·언어**: "Điều khoản sử dụng và bảo mật thông tin"(이용약관+정보보안 통합) 존재. `https://pigpro.vn/dieu-khoan-su-dung`. 베트남어. 최종개정 2024-08-21. (Bắc Ninh 소재 양돈 관리 SW)
- **데이터 소유권**: **이용자에게 귀속 명시**. "Người dùng giữ lại tất cả các quyền đối với dữ liệu của Người dùng"(이용자가 자기 데이터에 대한 모든 권리 보유). → Agriness와 정반대 접근, 고객친화형.
- **집계·익명 활용/판매**: 관련 조항 **없음**(집계·익명 활용/판매 언급 자체가 없음).
- **베트남 특유**: **Nghị định 13/2023(PDPD) 인용 없음**. "quy định pháp luật hiện hành"(현행법)만 포괄 언급, 국경간이전 규정 미비 → 베트남 중소 SW의 전형적 미비.
- **AI/데이터 활용**: 언급 없음.
- **보유·삭제**: 만료 후 "**hoàn toàn bị xóa vĩnh viễn...sau 1 tháng**"(1개월 후 영구삭제), 백업 책임은 이용자("Người dùng cần tự chủ động...sao lưu").
- **관할·분쟁**: 베트남 관할 암시, 분쟁은 이메일/핫라인/채팅/방문 등 비공식 창구.
- **특이**: 인테그레이터 귀속 조항 없음. 소유권을 이용자에 명시한 점이 유일한 강점, 법령 준수 문안은 취약.

---

## 카드 5 — PorciWeb (LATAM 스페인어 / 콜롬비아 기반) 

- **문서·URL·언어**: Política de Privacidad 존재. `https://porciweb.com/politica-privacidad`. 스페인어. (양돈 관리 SW)
- **데이터 소유권**: 명시적 소유권 귀속보다 "**NO vende ni alquila su información personal**"(개인정보 판매·임대 안 함)로 방어적 서술 → 이용자 사실상 소유.
- **집계·익명 활용/판매**: 상업 판매 없음. 비활성 데이터 "**eliminados o anonimizados después de 5 años**"(5년 비활성 후 삭제/익명화).
- **LGPD/역내법**: 브라질 LGPD가 아니라 **콜롬비아 Ley 1581 de 2012 + Decreto 1377 de 2013 + GDPR + Google Consent Mode v2** 준거 → LATAM 스페인어권은 자국 데이터보호법+GDPR 병기 패턴.
- **국제이전**: "**Cláusulas contractuales estándar**"(SCC) 기반 국제이전 명시 → 중소 SW 중 이례적으로 SCC 언급.
- **보유·삭제**: 계정 활성/법정요건 동안 보유, 비활성 약 5년 후 삭제.
- **관할·분쟁**: 콜롬비아 관할, **SIC(Superintendencia de Industria y Comercio)** 감독기구 명시.
- **특이**: 인테그레이터 조항 없음. 중소 규모임에도 SCC·감독기구 명시로 문안 성숙도는 PigPro보다 높음.

---

## 보조 참고(공개 약관 미확보)

- **中 牧原(Muyuan)·温氏(Wens)**: 스마트양돈(AI·로봇) 대규모 자체 운영이나 **외부용 ToS/Privacy 공개 문서 미발견** — 수직계열 자가운영이라 대외 SaaS 약관을 게시하지 않음. 중국 시장의 대외 약관 벤치마크는 农信互联(카드 2)가 대표.
- **韓 팜스플랜(Farmsplan, 한국축산데이터)·이지팜(EZFARM)**: PigPlan 직접경쟁. 앱·웹 서비스 운영 중이나 이번 세션에서 조항 본문까지는 미추출(앱스토어/랜딩만 확인). KR 부속은 별도 KR_legal 문서 및 PIGPLAN 스냅샷 기준으로 처리 권장.

---

## LATAM·아시아 관행 요약

1. **데이터 소유권 양극화**: Agriness(BR)는 "수집 DB = 자사 소유"로 **공급자 귀속**을, PigPro(VN)·PorciWeb(CO)는 "이용자 보유/판매 안 함"으로 **고객 귀속**을 택함. 시장에 단일 표준이 없어 PigOS는 선택 여지가 있음(단 인테그레이터 모델은 아무도 다루지 않음).
2. **집계·익명 데이터의 상업 활용은 Agriness가 가장 공격적**: 익명·집계 데이터를 "마케팅·데이터분석 전문업체와 공유"까지 명문화 → LATAM 최대 사업자가 이미 시장에 이 관행을 정착시킴. 이는 PigOS BR 부속에서 유사 조항을 넣을 실질적 선례가 된다(단 동의 근거 + 재식별금지 전제).
3. **법령 인용 성숙도 격차**: 태국 CPF(PDPA B.E.2562 정면 인용 + DPO 명주소)와 콜롬비아 PorciWeb(Ley 1581 + GDPR + SCC)이 최상위. 반대로 中 农信互联는 PIPL 미인용, 越 PigPro는 Nghị định 13 미인용 — **중국·베트남 로컬 사업자는 법령 명시가 취약**하여 PigOS가 명시적으로 하면 오히려 차별화·신뢰 우위.
4. **중국 데이터 현지화는 "경내 저장 + 현재 국외이전 안 함 + 이전 시 동의"가 실무 표준**(农信互联). 重要데이터 용어는 중소 사업자 문안엔 거의 안 나오고, 敏感信息에 암호화·비식별 통제를 붙이는 수준.
5. **보유기간 관행**: 중국 "거래 후 최소 3년", 태국 "최대 10년", 베트남 "만료 1개월 후 영구삭제", LATAM "비활성 5년" — 지역별 편차 큼. 익명화를 삭제의 대체수단으로 두는 패턴은 5개사 전부 공통.

## PigOS BR·CN·VN·TH 대비 시사점 (5)

1. **BR 부속**: Agriness의 "익명·집계 데이터를 마케팅/분석사와 공유" + "Florianópolis 관할" + "ANPD 통지 명시(단 DPO 미명명)" 조합이 실제 시장 표준이다. PigOS BR은 **① 익명·집계 데이터 활용 조항을 동의 기반 + 재식별금지로 정당화하고, ② Agriness가 빠뜨린 명명된 Encarregado(DPO)를 명시**하면 준수 우위 + 관행 정합을 동시에 확보.
2. **BR 법적근거**: Agriness는 사실상 "동의" 단일 근거에 의존하고 legítimo interesse를 정식 구분하지 않음. PigOS는 **활용 유형별로 consentimento vs legítimo interesse(+LIA)를 명확히 분리**하면 ANPD 가이드 정합성에서 앞선다.
3. **CN 부속**: 农信互联 수준(경내 저장 + 현재 국외이전 안 함 + 이전 시 동의 + 去标识化 활용권 + 敏감정보 비식별)이 시장 하한선. PigOS CN은 여기에 **PIPL 명시 인용 + (해당 시)重要데이터/국외이전 안전평가 트리거**를 추가해야 대기업 고객·규제 대응에서 통과 가능(이미 INTERNAL_LAUNCH_GATE_CN 존재 — 정합 확인 필요).
4. **VN 부속**: 로컬 경쟁(PigPro)이 Nghị định 13/2023을 전혀 인용하지 않는 저성숙 시장. PigOS VN이 **PDPD 근거·국경간이전 명시**만 해도 신뢰·규제 양면에서 즉시 차별화. 단 PigPro의 "이용자 데이터 소유권 명시"는 현지 기대치이므로 PigOS도 소유권 조항을 고객친화적으로 정렬 권장.
5. **TH 부속**: CPF가 PDPA·법적근거 5종·DPO 실주소·8대 권리·10년 보유를 이미 표준화. PigOS TH는 **CPF 수준을 최소 기준으로 매칭**하되(명명 DPO 창구, legitimate interest base, 국외이전 적정성 확인), CPF가 공개 notice에서 다루지 않는 **인테그레이터-계약농가 데이터 귀속**을 계약/약관에 명문화하면 태국 통합모델 시장에서 유일한 명확성 제공.
