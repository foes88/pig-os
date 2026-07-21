# RUN_PROMPT_D — 국가·주별 약관 요건 리서치 (legal 스킬 활용)
## 밤샘 자율 실행 프롬프트 (2026-07-21)

> **레포**: C:\dev\PigOS / **입력 SSOT**: docs/legal/DATA_RIGHTS_CONSENT_SPEC.md (구조·purpose 체계) · docs/PIGOS_SPEC_INDEX.md · docs/legal-review-notes.md
> **활용 스킬**: legal:compliance-check · legal:legal-risk-assessment (없으면 일반 리서치로 진행하고 보고)
> **런 로그**: [PLACEHOLDER] / **성격**: 문서 전용 리서치. 코드·스키마 금지.

## ⚠️ 최상위 규칙 — 산출물의 법적 지위
1. **법률 자문 아님.** 산출물 = 변호사 질의 보강 자료. 전 파일 상단 "변호사 검토 전 초안 — 법적 효력 없음" 배너 필수.
2. **약관 문안 작성 금지.** 조항 초안·문구 제안 금지(변호사 몫). 허용: 요건 정리·질문 도출·리스크 플래그.
3. **출처 게이트**: 법령·규정 언급마다 source_url + checked_at 필수. 웹 확인 불가분은 본문 기재 금지 → UNVERIFIED_CLAIM 섹션 격리. **출처 없는 법령명·조항 번호가 본문에 존재 = 게이트 FAIL.**
4. 학습 지식만으로 "현행" 단정 금지 — 웹 확인 시점 명시.

## G0
baseline `[PLACEHOLDER]` / 브랜치 `docs/legal-research` / Consent Spec 존재 확인

## 작업
### T1 — 국가별 리서치 노트 (`docs/legal/research/{국가}.md`)
우선순위: **US(연방+주) → VN → TH → BR → CN → GB → EU 공통 프레임.** KR은 기존 파악분 정리만.
규격: ①적용 법제(개인정보/데이터법·발효 상태·역외 적용, 농업 데이터 특칙, 전자 동의 유효 요건 — source_url 있는 것만 본문) ②Consent 매핑(purpose 6종 각각 기본/별도/불가, 익명·집계의 법적 취급, 국외이전 요건, 철회·삭제권) ③**콜드 아웃리치 적법성**(B2B 이메일 옵트인/아웃, 크롤링·명함 데이터 마케팅 사용 가부) ④변호사 질의 후보 ⑤UNVERIFIED_CLAIM ⑥리스크 등급(HIGH/MED/LOW+근거)

### T2 — US 주별 (`docs/legal/research/US_STATES.md`)
포괄 프라이버시법 보유 주 목록(checked_at 명시) / 주별 B2B 적용·농업 특칙·적용 임계값(**숫자는 출처 URL 필수, 없으면 미기재**) / **핵심 산출: "주별 부칙 1벌" 설계용 차이점 매트릭스** — 어떤 조항이 주별 분기를 요구하는지 / 양돈 밀집 주 우선(밀집 주 목록도 출처 확인 후)

### T3 — 변호사 질의서 통합본 (`docs/legal/LAWYER_BRIEF_v0.1.md`)
Consent Spec §3의 4건+동반질의를 T1·T2로 보강. **신규 필수**: ①수집 컨택(명함·LinkedIn·크롤링) 콜드 아웃리치 국가별 적법 범위 ②국가별 purpose 동의 유형 검증 ③US 주별 부칙 필요 조항 검증. 형식: 질문 + 리서치 결과(출처) + 원하는 결론 방향 — 변호사가 바로 답할 수 있게. (→ Claude legal 스킬 입력용)

### T4 — Consent Spec 패치 제안 (`docs/legal/CONSENT_SPEC_patch_proposal.md`)
직접 수정 금지. 반영 필요 항목만 제안.

## 게이트
G1 출처 감사 — 본문 법령 인용 전수 source_url 존재 (grep) / G2 문안 부재 — 약관 조항 문구 산출 0건 / G3 배너 존재 — 전 파일

## 금지
약관 문안 · 출처 없는 법령 인용 · "적법/위법" 단정(→ "~요건 확인됨, 변호사 검증 필요") · Consent Spec 직접 수정 · 코드

## 완료 보고
표준 형식 + 국가별 리스크 요약표 + UNVERIFIED_CLAIM 총목록 + 질의 최종 개수
