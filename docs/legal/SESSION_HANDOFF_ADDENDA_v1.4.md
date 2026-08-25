# SESSION HANDOFF — 부속조항 v1.4 (2026-07-22 세션)

> 이 문서는 2026-07-22 Cowork 세션의 결과 요약 + 다음 세션 실행 프롬프트다. NEXT_RUN_PROMPTS_v2.0.md의 공통 규칙을 그대로 적용한다.

## 1. 이 세션에서 한 일

- `legal:review-contract` 스킬로 6벌 부속조항 셀프 검토 → `internal/PRE_COUNSEL_SELF_REVIEW_ADDENDA.md`
- v1.1: D-13 역할 매핑 참조 조항을 6벌에 통일 신설 (US는 CCPA business/service provider 개념으로)
- v1.2: 컨트롤러=와이즈레이크(주) 전 문서 명시. 대리인 해법 확정 — **BR·US=현지 대리인 불요, EU·GB·TH=상용 대행 서비스(rep-as-a-service)로 지정(계약만 하면 됨, 출시 게이트), VN=의무 존부 미확인(확인 시 동일 방식)**
- v1.3: DPO·개인정보 문의처 **wiselake@wiselake.ai** 6벌 기입 (대표 결정. 단, 이 메일함이 실제 수신·응답되는지 운영 확인 필요)
- v1.4: 재검토 패스 — EU·GB·TH 대리인 문구 오기 정정("별개 사업자 아님" 표현 제거), "DPO 기능 수행"→"문의처 운영+지정 의무 검토 중"으로 정정(컨트롤러≠자기 DPO), 헤더 버전 정리
- 정본 반영: `drafts/COUNTRY_ADDENDA/`에 BR·TH·US·VN 교체, **EU·GB 분리본 신규 추가**
- **EU·GB 분리본을 정본으로 확정, 구버전 합본(ADDENDUM_EU_GB.md)은 프로젝트에서 삭제** (2026-08-04 대표 승인)

## 2. 미결 사항 (다음 세션이 확인할 것)

1. 실값 잔여: EU·GB·TH 대행업체 명칭·주소(계약 후), BR SCC 전문(포르투갈어), wiselake@wiselake.ai 실운영 확인.
2. LIA 문서 미작성 (아래 RUN L).
3. 변호사 회신 대기 → 회신 후 RUN F (NEXT_RUN_PROMPTS_v2.0.md).

## 3. 다음 세션 실행 프롬프트

### RUN L — LIA 초안 작성 (즉시 실행 가능)

```
[NEXT_RUN_PROMPTS_v2.0.md 공통 규칙 적용] +
입력: docs/legal/ 전체 (특히 CONSENT_AND_DATA_USE_SPEC, ANONYMIZATION_AND_RELEASE_STANDARD,
research/GB_EU_legal.md·BR_legal.md·TH_legal.md, drafts/COUNTRY_ADDENDA/ v1.4)
작업:
1. 목적②(PigSignal 익명·집계 통계 판매)의 정당한 이익 평가(LIA) 초안 작성
   — 3단계: (1) 목적 테스트(적법성) (2) 필요성 테스트 (3) 형량 테스트(안전장치 포함)
2. 관할 변형: EU/GB(Art.6(1)(f)+Art.21), BR(Art.7 IX, 민감정보 LI 불가 확인), TH(§24(5))
3. 각 판단에 상태 태그(INTERNAL_POLICY_PROPOSAL / COUNSEL_CONFIRMATION_REQUIRED) 부착.
   회사만 아는 사실(처리량·보유기간 등)은 [OPEN — 운영 기입]으로.
산출: docs/legal/internal/LIA_PURPOSE2_DRAFT.md (변호사 검토 전 초안 표시)
주의: "LIA 완료·LI 확정" 표현 금지 — 초안이며 변호사·운영 기입 후 확정.
```

### RUN F' — 변호사 회신 반영 (회신 수신 후, RUN F 변형)

```
[NEXT_RUN_PROMPTS_v2.0.md 공통 규칙 + RUN F 본문 그대로] +
추가 컨텍스트: 부속조항은 drafts/COUNTRY_ADDENDA/ v1.4가 최신 정본이다
(EU·GB 분리본 확정 — 합본 ADDENDUM_EU_GB.md는 삭제됨).
v1.4 변경 이력(각 문서 하단)을 읽고, 회신 반영 시 v1.4 기준으로 diff를 만든다.
DPO 문의처는 wiselake@wiselake.ai로 이미 기입됨 — 회신에서 달리 지시하지 않는 한 유지.
```

### RUN R — 대행업체 실값 기입 (대행 계약 체결 후)

```
[공통 규칙] + 입력: EU·GB·TH 대행 대리인 계약서(명칭·주소).
작업: drafts/COUNTRY_ADDENDA/ ADDENDUM_EU·GB·TH 제1조의 [OPEN — 상용 대행 서비스 계약 후...]를
실값으로 교체, 글로벌 프라이버시 노티스 제1조③에도 동일 기재, 변경 이력 추가,
CROSS_DOCUMENT_VALIDATION 해당 항목 갱신.
```

---

## 4. (추가 — 2026-08-05) 이후 진행 상황

- **GPT 교차검증 2라운드 반영 완료**: DECISION_ONE_PAGERS v1.2(D-13 확정문·독립 controller 정밀화), LIA_PURPOSE2_DRAFT v0.3(§0 기업고객 데이터 제외, §2B 동의 비교 분리, Art.6(4)=OPEN, 3관점 익명성), T1_RECHECK v1.2.
- **T1 핵심 발견**: 글로벌 게시본 정본 URL은 **pigos.io**(pigos.ai 아님). 현행 pigos.io 공개본은 익명·집계 활용에 **"별도 동의" 자기구속(F-T1e)** — LI 전환 시 30일 사전 공지 + 부속조항 우선구조 게시 필요. 게시본 오류 P1: 대표자 표기 모순(진교문 vs Seung Hwan An), 이메일 3원 불일치(co.kr/ai/ezfarm).
- **게시 후보본 v1.0-rc 생성**: `docs/legal/publish_candidate/` — 마스터 약관 + 글로벌 방침 + 부속조항 6벌(총 8종). 내부 주석 전체 제거, 결정값(wiselake@wiselake.ai) 반영. 게시 조건: [OPEN] 확정 → 변호사 → 대표 승인 → 시행일. **PigSignal 목적② 처리는 실행 게이트 충족 전 OFF 유지.**
- 잔여 빈칸: 마스터 [OPEN] 6(손배 상한·결제/세금·크레딧·환불·회사 주소·시행일), 방침 [OPEN] 11+[V] 12(책임자 성명·수탁자 목록·보유기간 등 실측), 부속 국가당 2~3(대행 대리인 EU/GB/TH·BR SCC 전문).

## 5. (추가 — 2026-08-05) 출시 대상국 확정 사실 (대표 확인)

- **공식 타겟**: 5개 시장 (US·CN·SEA[VN+TH]·LatAm·KR) × 8개 언어(en/ko/zh/es/vi/th/pt/ru) — LANDING_SYNC.md [확정] 기준.
- **KR = 레퍼런스 전용, PigOS 공개·가입 없음** (대표 확인 2026-08-05). → 가입 시스템에서 KR 차단/피그플랜 안내 플래그 필요. 단 한국법(PIPA·준거법·법정 보존)은 회사 본국법으로서 계속 적용, F5·재동의 이슈는 피그플랜 트랙에 존속.
- **EU·GB = 타겟 아님** → 대리인 계약 불요(부속조항은 향후 진출 대비 보존). **현재 대리인 계약 필요 0건.** TH는 태국 출시 시점에(Q9 확인 후), CN은 D-07 HOLD 해제 후(PIPL 제53조 현지 대표 필요).
- **리서치 갭 2건**: ① 스페인어권 LatAm(멕시코·콜롬비아 등 — BR만 커버됨) ② 러시아어권(러시아/CIS — 리서치 제로, 데이터 현지화법 중대). 해당 시장 활성화 전 리서치·부속조항 필요.
- 변호사 검토 우선순위: **US 최우선**(1차 출시) + KR(회사 본국법 관점) → BR/TH/VN(순차 출시 전) → CN(HOLD 해제 시). EU·GB 질의는 보류 가능.
- CLAUDE.md의 "타겟 5개 시장" 줄은 유효하나 KR 성격(레퍼런스·비공개) 주석 현행화 권장.

## 6. (추가 — 2026-08-05) 언어 갭과 RUN G' (영어 선행 번역)

**확인된 갭**: publish_candidate 8종이 전부 국문. 그러나 1차 출시=US → 영어본이 법적 정본. 원계획(RUN G: 변호사 확정 후 번역)의 순서를 조정하여 **영어만 선행 초벌 번역**한다. th/vi/pt는 원칙대로 확정 후 전문 번역+현지 감수(변경 없음).

### RUN G' — 영어 선행 번역 런 (새 세션에서 실행)

```
[NEXT_RUN_PROMPTS_v2.0.md 공통 규칙] +
입력: docs/legal/publish_candidate/ 8종 (v1.0-rc 국문)
작업:
1. TERMS_GLOSSARY.md 생성 — 정의어 국문·영문 대역 용어집 먼저 (예: 농장 데이터=Farm Data,
   익명 통계 산출물=Anonymized Statistical Output, 크레딧=Credits, 부속조항=Country Addendum)
2. 8종을 영어로 전문 번역 — 의역 금지, 조항 번호·구조 유지, 용어집 일관 적용.
   [OPEN]·[COUNSEL] placeholder는 영문으로 유지(값 발명 금지)
3. 각 영문본 서두: "DRAFT — Not for publication. Pending legal review." 배너
4. 산출: docs/legal/publish_candidate/en/ 아래 *_EN.md 8종 + TERMS_GLOSSARY.md
주의: 이 영문본은 초벌이며 변호사/감수 확정 전 게시 금지. 변호사 회신(RUN F) 반영 시
국문 diff를 영문본에도 동기 반영한다. US·GB 정본=영어, BR=포르투갈어(추후), KR문=작성 원본.
```

## 7. (추가 — 2026-08-05) ⚠ 상태 정정: PigOS는 이미 출시됨

- **pigos.io는 라이브 서비스** (게시 약관 시행일 2026-05-30 = 현행 유효 약관). 본 세션의 publish_candidate 세트는 "신규 게시"가 아니라 **"현행 약관의 개정·전환"** 절차로 적용해야 한다.
- 전환 경로: 변호사 확인 → **30일 사전 공지(중대변경)** + 재고지 배너(구현돼 있음, notice_version) → 국가별 부속조항 체계로 전환. 기존 회원 경과조치는 마스터 부칙 [COUNSEL] 항목.
- **핵심 운영 제약**: 현행 라이브 약관이 익명·집계 활용을 "별도 동의한 경우에 한하며"로 자기구속(F-T1e) → **기존 가입자 데이터는 별도 동의 기록(consent ledger) 없으면 PigSignal 편입 금지.** 목적② OFF 유지가 필수인 이유.
- **신규 최우선 실측(V16)**: 현재 가입자의 국가별 분포 집계 — 어느 관할 의무가 이미 가동 중인지 판정 기준. (예: VN 가입자 존재 시 TIA 시계가 이미 진행 중)
