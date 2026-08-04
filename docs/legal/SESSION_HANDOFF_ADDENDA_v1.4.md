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
