# RAW_EU — 유럽/GDPR 양돈·축산 SaaS 약관 벤치마크 (원자료)

> 조사일: 2026-07-22 · 방식: WebSearch + WebFetch 공개 게시문서 구조 분석
> **저작권 원칙 준수**: 조항 존재·구조·접근방식만 기록. 원문 대량 복사 없음. 핵심 문구는 1문장 이하 인용.
> 대상: 실제 게시 문서를 확인한 5개 서비스. Porcitec/Agritec(ES)는 공개 페이지에서 법률문서 링크가 노출되지 않아 카드에서 제외(각주 참조).

---

## 서비스 카드

### 1. Herdwatch (IE 본사, UK/IE 축산·양돈 기록 SaaS)
- **문서 존재/URL**: Privacy Policy(`herdwatch.com/privacy-policy/`), Terms & Conditions(`herdwatch.com/terms-conditions/`). 별도 DPA·SLA·독립 Cookie Policy **없음**(쿠키는 프라이버시 본문 §4에 통합).
- **데이터 소유권**: 고객이 콘텐츠 소유(업로드 데이터 소유 보증). 제공자에 **"non-exclusive, transferable, revocable, sub-licensable, royalty-free"** 광범위 라이선스 부여. 독립 백업 권고.
- **집계·익명 데이터**: 집계·익명 데이터 활용/판매 **명시 조항 없음**.
- **GDPR 법적 근거**: 놀랍게도 GDPR을 정면 인용하지 않고 **아일랜드 구법(Data Protection Acts 1988·2003)** 프레임 + **동의(consent)** 기반. Art. 6 대체근거(정당한 이익 등) 미언급 → GDPR 대비 노후.
- **정보주체 권리**: 열람·정정·연락동의 철회만. 삭제·이동·이의·자동화결정 권리 미언급(불완전).
- **국외이전**: SCC·적정성·이전 위치 **언급 없음**("cloud upload"만).
- **EU/UK 대리인(Art.27)**: 미표기.
- **쿠키 CMP**: 사전동의 배너/분리 쿠키정책 확인 안 됨. Google Analytics만 언급.
- **Subprocessor**: 목록 미공개("third-party cloud storage provider"만).
- **AI 면책**: **Herdi AI 어시스턴트 면책 명시** — "전문가 조언의 대체 아님", 산출물 기반 행위 손해 무면책, 사용자 검증 의무. (수의 대체 아님 취지 포함)
- **관할·분쟁**: **미국 텍사스(Houston) 법·전속관할** — 아일랜드 기업임에도 US 관할 선택(EU 소비자·강행규정과 충돌 소지 큼). 분쟁: 비공식→AAA 조정→소송.
- **보유·삭제**: "합리적 기간 또는 법정 요구 기간" — 구체 기간 없음.
- **책임한도**: 직전 12개월 지급액 상한, 간접·데이터손실 배제, "as is".
- **특이**: EU 축산 서비스인데 준거법·프라이버시 프레임이 US/구아일랜드법 혼재 → GDPR 정합성 낮은 반면교사 사례.

### 2. AgroVision B.V. (NL, 양돈 소프트웨어 — AgroSoft NetFarm 계열 모회사)
- **문서 존재/URL**: Privacy Statement(`agrovision.com/legal-documents/privacy-statement/`). Terms·DPA·독립 Cookie Policy는 이 문서 내 미확인.
- **데이터 소유권**: 프라이버시 문서 범위. (별도 SaaS 계약 라이선스는 미확인)
- **집계·익명 데이터**: 별도 명시 없음.
- **GDPR 법적 근거**: **4개 근거 명시적 분리** — 동의(파생데이터 수집), 계약이행(서비스·인보이스·지원), 법적의무(세무 보존), **정당한 이익(서비스 개선·제품 혁신·마케팅)**. → LI/consent 구분이 뚜렷한 모범형.
- **정보주체 권리**: 열람·정정·삭제(해지 후 1개월 내, 법정보존 유보)·이의(마케팅 옵트아웃)·이동권(과도요청 시 수수료).
- **국외이전**: **처리 EEA 내로 한정**, 처리자도 EU/EEA 소재. SCC·적정성 명시적 언급은 없음(EEA 한정으로 회피).
- **EU 대리인(Art.27)**: 불요(NL 소재) → 미표기.
- **쿠키 CMP**: 별도 쿠키정책 미제공, 파생데이터 수집 동의만 언급.
- **Subprocessor**: **5개 처리자 실명 공개** — ZitCom, Equinix, UniWeb bvba, UViON bvba, Microsoft Nederland (전부 EU 소재).
- **AI 면책**: 이 문서엔 없음.
- **관할·분쟁**: 컨트롤러 AgroVision B.V.(Deventer, NL), 불복은 네덜란드 DPA.
- **보유·삭제**: 해지 후 요청 시 1개월 내 삭제(법정보존 우선).
- **특이**: **데이터 EEA 국내 완결 전략** — 국외이전 근거 논쟁을 원천 회피(PigOS 한국서버 모델과 대비되는 지점).

### 3. Nedap Livestock Management (NL, 젖소/양돈 센서·소프트웨어)
- **문서 존재/URL**: Privacy Statement & Disclaimer(`nedap-livestockmanagement.com/privacy-statement-disclaimer/`), API Terms of Use(`connect.nedap-livestockmanagement.com/home/terms-of-use/`). 앱/SW 프라이버시 개요 PDF 별도 존재.
- **데이터 소유권**: (API 약관) **Nedap가 IP·데이터 소유 또는 라이선서 소유**, 고객은 **non-exclusive license**로 API-Data 접근만 — 고객 데이터 소유권을 고객에 두지 않는 이례적 강한 벤더 지향.
- **집계·익명 데이터**: 판매/활용 조항 없음.
- **GDPR 법적 근거**: 계약이행·법적의무·동의·정당한 이익 4근거 언급(처리별 세분화는 약함).
- **정보주체 권리**: 열람·정정·삭제·제한·이의 + NL DPA 불복. **요청 처리 전 여권 신원확인 요구**(과도 검증 소지).
- **국외이전**: EEA 외 공유는 "adequate level" 보장 시만. SCC·적정성 명시 없음. **Google Analytics는 IP 마스킹 후 US 전송, Google DPA 의존**.
- **EU 대리인(Art.27)**: 불요(NL) → 미표기.
- **쿠키**: 단일 문서 Part B에 쿠키 섹션 통합, 동적 CMP 배너 서술 없음.
- **Subprocessor**: 전용 목록/공개 메커니즘 없음. Google만 언급.
- **AI 면책**: 명시 AI/수의 면책 없음. 대신 "정확성·신뢰성·적합성" 일반 면책.
- **관할·분쟁**: **네덜란드법 + ICC 중재**(경영진 회의→ICC), UN 매매협약 배제.
- **보유·삭제**: "목적에 필요한 기간"만, 카테고리별 기간 없음.
- **특이**: SaaS/센서 하이브리드로 **데이터 소유를 벤더에 두는 조항** + ICC 중재 채택.

### 4. Breedr (UK 설립·US 지주, 축산/소 관리 앱)
- **문서 존재/URL**: Privacy Policy(`breedr.co/privacy-policy`), 별도 Cookie Policy(링크), 별도 Third-Party Processors 페이지(링크). Terms 별도.
- **데이터 소유권**: (프라이버시 범위) — 라이선스 조항은 Terms.
- **집계·익명 데이터**: 미언급.
- **GDPR 법적 근거**: **5범주 명시** — 동의(분석쿠키·마케팅), 계약이행, **정당한 이익(사업운영·마케팅 조율·공급자 관리)**, 법적의무, **명시적 동의(알러지·식이·접근성 등 특별범주)**. → 근거 매핑이 가장 상세한 축.
- **정보주체 권리**: 철회·SAR(신원확인)·마케팅 옵트아웃·**자동화결정 이의**·정정·삭제·차단·이동(기계판독)·침해보상. 광범위.
- **국외이전**: **UK·US로 이전 발생 명시**. 단 SCC/적정성 구체 언급 없이 "합리적 조치"만 → 표현 약함.
- **EU/UK 대리인(Art.27)**: 미표기(US 지주 구조인데 공백 — 취약점).
- **쿠키 CMP**: **별도 쿠키정책 링크 분리** 운영.
- **Subprocessor**: **별도 "Third Party Processors" 페이지로 공개** — 분리형 공개 모범.
- **AI 면책**: 자동화결정 이의권은 다루나 별도 AI/수의 면책 문구는 이 문서에 없음.
- **관할·분쟁**: 컨트롤러 Breedr Holdings Inc.+자회사(Breedr Limited 등), 연락 Austin TX. 감독기관은 "귀하 관할의 관련 기관"으로 모호.
- **보유·삭제**: **계약기간+7년** 등 구체 기간 명시(회원·공급자·직원별). 사업기록은 "법정기간".
- **특이**: **보유기간을 카테고리별 구체 연수로 명시** + subprocessor·cookie 분리 공개 = 문서 구조 성숙도 높음. 반면 국외이전 근거·Art.27은 공백.

### 5. Pigax / Research Link (NL, 무료 양돈 관리 SaaS — 가장 온-포인트)
- **문서 존재/URL**: Privacy Policy(`pigax.com/en/PrivacyPolicy`), Terms(`/TermsOfUse`), **전용 DPA(`/DataProcessingAgreement`)**, FAQ. 양돈 SaaS 중 **DPA를 별도 게시한 드문 사례**.
- **데이터 소유권**: **고객이 controller, Pigax는 processor** 명시 — "You are the controller of the data you input". 데이터는 사용자 지시로 EEA 서버 저장. 제공자에 상업화 라이선스 부여 안 함.
- **집계·익명 데이터**: 프라이버시·약관·DPA 모두 **집계/익명/판매 조항 없음**(= 2차 활용을 아예 안 함).
- **GDPR 법적 근거**: 계약이행·법적의무·**정당한 이익(플랫폼 개선)**·동의(마케팅/교육). 근거별 분리.
- **정보주체 권리**: 열람·정정·삭제·제한·이동·이의·철회·감독기관 불복 (privacy@pigax.com).
- **국외이전**: **"모든 데이터 EEA 내 호스팅"** + EEA 외 이전 시 **SCC 사용 명시** + GDPR Art.44–49 인용. → 이전 장치를 명시적으로 언급한 유일 사례.
- **EU 대리인(Art.27)**: 미표기(NL 소재 → 불요).
- **쿠키 CMP**: **Cookie Consent Manager 제공** 언급, 단 별도 쿠키정책 문서 링크는 없음.
- **Subprocessor**: **카테고리 공개**(AWS, Azure, Mailgun, SendGrid, 지원 플랫폼) + "완전 목록 요청 시 제공".
- **DPA 세부**: processor의 정보주체권리 지원 의무, **침해 지체없이 통지**, 종료 후 **15일 내 삭제·반환**(법적보존 예외), 재이전 GDPR Ch.V 준수, subprocessor 일반승인.
- **AI 면책**: 없음(약관에 AI·수의 면책 문구 부재).
- **관할·분쟁**: 네덜란드법·네덜란드 법원. DSA 준수 언급, 소비자보호는 EU법 우선.
- **보유·삭제**: 계정/커뮤니케이션 = 폐쇄 후 5년, 농장데이터 = 계정존속/사용자삭제까지, 해지 후 15일 내 완전삭제.
- **특이**: **controller/processor 역할을 고객=controller로 뒤집은 순수 처리자 모델** + 전용 DPA + SCC 명시 = GDPR 문서 정합성 최상위. 단 2차 데이터 활용 자체를 포기하는 구조.

---

## 유럽 / GDPR 공통 관행 요약

**1) 법적 근거 — Legitimate Interest vs Consent 이원화가 표준.**
성숙한 NL/UK 서비스(AgroVision·Breedr·Pigax·Nedap)는 Art.6 근거를 **처리목적별로 4~5범주 분리 매핑**(계약이행·법적의무·정당한 이익·동의, 특별범주는 명시적 동의)한다. 마케팅·분석쿠키·특별범주(건강/식이)는 **consent**, 서비스운영·제품개선·플랫폼 향상은 **legitimate interest**로 배치하는 패턴이 일관적. 반면 Herdwatch는 동의 단일 프레임+구법 인용으로 GDPR 대비 노후 → 반면교사.

**2) 집계·익명 데이터 — 유럽 벤치마크는 대부분 "명시 조항 없음/2차 활용 안 함".**
조사 5개사 중 어느 곳도 **집계·익명 데이터의 적극적 활용·판매 조항을 게시하지 않음**. Pigax는 순수 processor로 2차활용을 아예 포기, 나머지는 침묵. 즉 유럽 관행상 "익명·집계 데이터 재활용"을 약관 전면에 내세우는 사례가 희소 → PigOS 목적②(LI+opt-out 기반 익명·집계)는 유럽 시장에서 **오히려 선진적/공격적 포지션**이며, 그만큼 LIA·고지·이의권 실효성 문서화가 차별화 겸 방어선이 됨.

**3) 쿠키 CMP — 성숙도 편차 큼.**
Breedr만 **별도 쿠키정책 분리**, Pigax는 **Cookie Consent Manager(CMP)** 운영. AgroVision·Nedap·Herdwatch는 프라이버시 본문에 쿠키 섹션을 **통합**하고 사전동의 배너 서술이 약함. 즉 양돈 특화 SaaS 다수가 ePrivacy 사전동의 배너 요건에서 미흡 → PigOS가 분리형 쿠키정책+CMP를 갖추면 상위 관행.

**4) DPA·Subprocessor 공개 — 분리·목록화가 상위 관행.**
Pigax(전용 DPA + subprocessor 카테고리 공개 + 요청시 전체목록), Breedr(별도 Processors 페이지), AgroVision(프라이버시 내 5개 실명)이 상위. Nedap·Herdwatch는 subprocessor 목록 미공개. 표준 요소: **종료 후 삭제·반환 기한(Pigax 15일)**, 침해 지체없이 통지, 정보주체권리 지원, 일반/개별 subprocessor 승인.

**5) EU 대리인(Art.27) — NL/IE/UK 소재사는 대부분 불요·미표기, 역외 지주 구조에서 공백 발생.**
NL 소재(AgroVision·Nedap·Pigax)는 EU 내 설립으로 Art.27 불요. 문제는 **US 지주 구조(Breedr, Herdwatch의 US 관할 선택)에서 대리인 지정 공백**이 드러남 → 역외 사업자(PigOS=한국)에겐 Art.27 EU/UK 대리인 지정이 명확한 차별화·의무이행 지점.

**6) 국외이전 — "EEA 국내 완결"이 지배적 회피전략, SCC 명시는 소수.**
AgroVision·Nedap·Pigax 모두 1차 방어를 **EEA 내 호스팅 한정**으로 삼음. SCC/적정성을 문서에 명시한 곳은 **Pigax(SCC+Art.44-49)가 사실상 유일**. 한국 서버를 쓰는 PigOS는 EEA 완결이 불가하므로, **한→EU/UK 적정성 결정 근거를 노티스에 명시**하는 접근(PigOS EU/GB 부속 제2조)이 유럽 관행보다 오히려 투명.

**7) 관할·AI 면책 — 편차.**
관할은 소재지법(NL·IE)이 원칙이나 Herdwatch가 US 텍사스 관할을 택해 EU 강행규정과 충돌 소지. AI 수의 대체 면책을 **명시한 곳은 Herdwatch(Herdi AI)뿐** — 신흥 관행이라 PigOS PigSignal 면책은 선도 여지.

---

## PigOS EU/GB 부속·방침 대비 시사점 (5개)

1. **목적② 익명·집계 LI 구조는 유럽에서 선진적이나 벤치마크가 희박 → 방어문서로 차별화하라.**
   조사 5개사 중 집계·익명 재활용을 약관에 명문화한 곳이 전무. PigOS의 Art.6(1)(f) LI + Art.21 opt-out 구조(부속 제4조)는 시장에 선례가 적으므로, **LIA 3단계 테스트·Art.13/14 고지·이의 즉시반영**을 오히려 경쟁우위로 전면 문서화하는 것이 안전 겸 마케팅 포인트.

2. **한국 서버 국외이전은 유럽 관행(EEA 완결)과 정면 배치 → 적정성 근거 노출을 더 두텁게.**
   벤치마크 다수가 "EEA 내 호스팅"으로 이전 문제를 회피하는 반면 PigOS는 회피 불가. 부속 제2조의 EU/UK→한국 **적정성 결정 명시 + 재심사 시 SCC/IDTA 대체 트리거**는 Pigax(SCC 명시) 수준 이상의 투명성을 노티스에 전면 배치해야 신뢰 격차를 상쇄.

3. **Art.27 EU/UK 대리인 실지정은 즉시 차별화 지점 — 역외 경쟁사(Breedr형) 공백을 메워라.**
   US 지주형 경쟁사조차 대리인 공백을 노출. 한국 사업자인 PigOS가 **EU·UK 대리인을 실제 지정·노티스 기재**(부속 제1조 placeholder 해소)하면 규제 정합성에서 즉시 우위. 출시 전 지정 완료를 게이트로 유지.

4. **DPA·Subprocessor 분리 공개 + 종료 후 삭제기한 명문화가 상위 관행 — Pigax/Breedr 수준을 목표.**
   상위 벤치마크의 공통 요소는 **전용 DPA·별도 subprocessor 페이지·종료 후 삭제기한(예: 15일)·재이전 Ch.V**. PigOS B2B DPA에 재이전 체인 공개(부속 제2조4 외부 AI 벤더)와 subprocessor 목록·삭제기한을 이 수준으로 정렬하면 B2B 조달 심사 통과력이 높아짐.

5. **쿠키 CMP·AI 수의 면책은 양돈 SaaS 다수가 미흡 → PigOS가 저비용으로 선도 가능.**
   분리형 쿠키정책+사전동의 CMP를 갖춘 곳은 Breedr·Pigax 정도, AI 수의 대체 면책은 Herdwatch뿐. PigOS가 **ePrivacy 사전동의 배너(국가별) + PigSignal의 "수의 진단 대체 아님·알고리즘 면책"**(부속 제9조·마스터 약관)을 정비하면, 낮은 비용으로 유럽 양돈 SaaS 상위 관행을 선점.

---

*각주 — 미확인/제외 서비스*: Porcitec/Agritec(ES)는 제품 페이지에서 Privacy/Cookie/Legal 링크가 노출되지 않아 문서 구조 확인 불가(스페인 LSSI상 Aviso Legal·Cookie 배너가 별도 존재할 개연성은 있으나 미검증). Dan-Ex/DanBred·FarmWizard·Cranswick/Ingham 계열은 공개된 표준 SaaS 법률문서 세트가 확인되지 않아 이번 카드에서 제외. 필요 시 2차 조사 대상.
