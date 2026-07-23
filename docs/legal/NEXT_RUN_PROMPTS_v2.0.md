# NEXT_RUN_PROMPTS v2.0
## PigOS 법무 파이프라인 — 다음 단계 실행 프롬프트 세트 (COUNTRY_LEGAL_PROMPTS v1.0 후속)

> **사용법**: 각 RUN 블록을 개별 Claude 세션에 투입. 입력 파일은 PigOS 프로젝트 `docs/legal/` (또는 v3 zip). 순서: E1·E2는 즉시 병렬 가능 → F는 변호사 회신 수신 후 → G·H는 F 이후.
> **현재 상태**: 리서치 7개국 + 증거 스냅샷 v2.1 + FINDINGS/DECISION_REGISTER(D-01~04 DECIDED)/LAWYER_BRIEF(질의 30)/OPEN_QUESTIONS + 약관·방침·부속 6벌 초안 + CONSENT/ANONYM/DISPLAY 스펙 + 교차검증 PASS. **국가 리서치 재실행 금지.**

---

## 공통 규칙 블록 (모든 RUN 맨 앞에 붙임)

```
[공통 규칙]
- 원본 보존: docs/legal/research/*.md 7개, reference/evidence/*.txt, SUMMARY_INDEX는 수정 금지. 수정은 drafts/·스펙·레지스터류만.
- 출처 우선순위: ①evidence 전문 ②SNAPSHOT v2.1 ③리서치의 법령·규제기관 인용 ④리서치의 로펌·2차 자료 ⑤SUMMARY_INDEX ⑥분석자 해석. 상위 우선, 동급 충돌은 OPEN_QUESTIONS 승격.
- 상태 태그: LEGAL_REQUIREMENT / OFFICIAL_GUIDANCE / DRAFT_GUIDANCE / CASE_OR_ENFORCEMENT / INDUSTRY_PRACTICE / INTERNAL_POLICY_PROPOSAL / COUNSEL_CONFIRMATION_REQUIRED.
- 사업조건 발명 금지: 크레딧·환불·SLA·배상 상한·수익 배분·대리인 실명 등은 입력에 확정값 없으면 [OPEN] 유지.
- 고객 노출 본문에 태그·주석 삽입 금지 — HTML 코멘트(REVIEW NOTE) 또는 별도 맵.
- 산출 후 CROSS_DOCUMENT_VALIDATION 10항목 재검사, 결과 보고. FINAL·게시 가능 표현 금지.
- commit/push/deploy/운영 게시 금지.
- 종료 시 보고: 생성·수정 파일 / 무수정 원본 / OPEN 증감 / 검증 PASS·FAIL.
```

---

## RUN E1 — 운영 실사 (V1~V5) 결과 반영

```
[공통 규칙] +
아래 실사 결과를 내가 입력한다 (실사 자체는 내부 인력 수행 — 체크리스트: FINDINGS §C).
  V1: 가입 UI의 데이터 활용 동의 화면 캡처 + 동의 로그 DB 존재 여부·스키마
  V2: 앱 내 게시 약관 캡처 (버전 확인)
  V3: 2026-05-30 이전 구약관 파일
  V4: PigSignal 기제공 이력 (수신처·기간·계약서의 재식별 금지 조항 유무)
  V5: 콜드 이메일 발송 현황 (대상국·수신자 출처·동의 유무·발송량)
작업:
1. 입력 결과로 FINDINGS §C를 VERIFIED로 갱신, F5(동의 모델 상충)의 사실관계 확정
2. V5에서 KR 무동의 발송 확인 시: 즉시 중단 권고문 + 위험 노출 정리(정통망법 제50조 제재 기준) 1페이지
3. V1 결과가 D-01 전제와 다르면 D-01 REOPEN 플래그
4. LAWYER_BRIEF 해당 질의(사실관계 대기 표시분)에 실사 결과 각주 추가
산출: FINDINGS v1.1, (해당 시) URGENT_ACTIONS.md
```

## RUN E2 — 증거 등급 상향 (T1)

```
[공통 규칙] +
브라우저(Chrome 연동 세션)로 다음 4페이지를 렌더링 캡처:
  pigplan.io/landing/term-of-service.do · privacy-policy.do / pigos.ai/terms · /privacy
각각: 전체 페이지 스크린샷 + 인쇄 PDF + 캡처 시각(KST) 기록 → reference/evidence/에 저장,
SNAPSHOT v2.1의 T1 TODO를 완료 표시하고 파일 해시 추가 (v2.2).
텍스트가 기존 evidence .txt와 다르면 diff를 스냅샷에 기록 (게시본이 변경된 것 — 중대 플래그).
```

## RUN F — 변호사 회신 반영·문서 확정 런 (회신 수신 후)

```
[공통 규칙] +
입력: LAWYER_BRIEF 30개 질의에 대한 변호사 회신 (내가 첨부).
작업:
1. 회신을 질의 ID별로 DECISION_REGISTER·OPEN_QUESTIONS에 매핑 — 각 항목 CLOSE/REOPEN/추가질의 분류
2. D-01~D-04(조건부 DECIDED): 반대 의견 있으면 REOPEN + 초안 수정안 제시, 없으면 조건부 해제
3. D-05/D-06: 회신 기준으로 k값 확정 → ANONYMIZATION_AND_RELEASE_STANDARD 수치 확정판(v2)
4. drafts/ 약관·방침·부속조항에 회신 반영 — 변경분은 diff 요약표로 보고
5. REVIEW NOTE 중 해소된 항목 제거, 잔존 항목만 유지
6. CROSS_DOCUMENT_VALIDATION 재실행 (v2)
산출: 각 문서 v2 + COUNSEL_RESPONSE_MAP.md (질의→회신→반영 위치 추적표)
주의: 회신이 없는 질의를 임의로 CLOSE 하지 않는다.
```

## RUN G — 번역 런 (RUN F 완료 후)

```
[공통 규칙] +
확정된 마스터 약관·방침·부속조항의 영어본 우선 작성 (법적 우선본 국가: US·GB 등 — TERMS_DISPLAY_SPEC §5).
- 법률 문서 번역 원칙: 의역 금지, 정의어 일관(용어집 먼저 생성), 조항 번호 유지
- 산출: *_EN.md + TERMS_GLOSSARY.md (국문·영문 대역 용어집)
- 태국어·베트남어·포르투갈어는 전문 번역+현지 변호사 감수 대상으로 표시만 (기계 번역본을 법적 우선본으로 쓰지 않는다)
- 각 번역본 서두: "번역 검수 전 초안 — 게시 금지"
```

## RUN H — 개발 구현 런 (코딩 세션, pigos-landing/앱 저장소 연결)

```
[공통 규칙 — 단, 이 런은 코드 작성 런이므로 저장소 수정 허용. 운영 배포는 금지] +
입력: TERMS_DISPLAY_SPEC.md + CONSENT_AND_DATA_USE_SPEC.md §3~§5
작업 (스펙 §7 체크리스트 순):
1. jurisdiction resolver (국가 + US 주, 농장 단위)
2. 약관 렌더러: 마스터+방침+부속조항 조합 표시, notice_version 관리
3. 가입 동의 UI: 필수 2체크 / ②고지 블록(국가별 문구) / ③④⑤ 토글(기본 OFF) / NE 옵트인 단계 / VN ⑤ 미노출
4. consent_ledger 테이블·API (CONSENT_SPEC §5 스키마 그대로)
5. CN 차단·TH/VN 게이트 (기능 플래그)
6. CA Do Not Sell 링크·GPC 신호
주의: 약관 본문 텍스트는 drafts/가 아직 DRAFT이므로 placeholder 파일로 연결(문서 확정 시 교체).
법적 문구를 코드에 하드코딩하지 않는다 — 버전 관리되는 콘텐츠 파일로 분리.
산출: PR 초안 (배포 금지) + 스펙 대비 구현 커버리지 표.
```

---

## 실행 순서 요약

| 순서 | RUN | 선행 조건 | 담당 |
|---|---|---|---|
| 지금 | E1 실사 입력 / E2 증거 캡처 | 없음 (병렬) | 내부 인력 + Claude |
| 지금 | 변호사에게 v3 zip + LAWYER_BRIEF 전달 | 없음 | 대표 |
| 회신 후 | F 확정 런 | 변호사 회신 | Claude |
| F 후 | G 번역 / H 구현 | 문서 확정 | Claude (병렬) |

## 변경 이력
| v2.0 | 2026-07-21 | 최초 작성 — 리서치 완료·초안 완성 이후 단계 (E1·E2·F·G·H) |
