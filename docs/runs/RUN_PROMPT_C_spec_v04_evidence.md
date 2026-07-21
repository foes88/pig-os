# RUN_PROMPT_C — KPI 스펙 v0.4 개편 + Evidence Register + 대표 결정요청서 (문서 전용 런)
## 밤샘 자율 실행 프롬프트 (2026-07-21)

> **레포**: C:\dev\PigOS
> **입력**: docs/specs/COUNTRY_KPI_RULE_SPEC_v0.3.1.md · docs/PIGOS_SPEC_INDEX.md · KPI_GOVERNANCE_v3.2 · docs/KPI_DEFINITIONS.md · docs/RULE_ENGINE_CATALOG.md · **docs/specs/2026-06-17_country-kpi-differences.md (기존 국가 KPI 분석 — 반드시 대조, 모순 시 보고)** · Safe Claim Matrix v0.4 · docs/meetings/MEETING_NOTES_2026-07-21.md · [PLACEHOLDER: GPT 국가별 초안 파일 경로 — 반드시 UNVERIFIED 취급]
> **런 로그**: [PLACEHOLDER]
> **성격**: 문서 전용. 코드·스키마·seed 일절 생성 금지.

## G0 — 선행조건
baseline `[PLACEHOLDER]` / 브랜치 `docs/kpi-spec-v0.4` / 입력 문서 전부 존재 확인

## ⚠️ 최상위 규칙 — 미검증 격리
GPT 국가별 초안(Pork Checkoff·Agriness·Embrapa·AHDB·SEGES·IFIP·Teagasc 인용 포함)은 **검증된 바 없다**:
- 전부 `evidence_status: UNVERIFIED_DRAFT`로만 수록
- source_year·cohort·denominator를 추정으로 채우지 않는다 — 비워둔다
- UNVERIFIED_DRAFT의 상위 승격 금지 (승격 = 웹 원문 대조 실사 후 사람이)
- 인용 기관명이 그럴듯해도 사실 확인으로 취급하지 않는다

## 작업
### T1 — v0.4 스펙 (`docs/specs/COUNTRY_KPI_RULE_SPEC_v0.4.md` 신규, v0.3.1 보존)
1. 정책 차원 확장: 국가 × farm_type(BREEDING|PIGLET_PRODUCTION|NURSERY|GROW_FINISH|FARROW_TO_FINISH|MULTIPLIER) × production_stage(GILT_DEVELOPMENT~WHOLE_HERD 10종). DDL 변경은 제안만·구현 금지
2. `priority_class` 신설: NORTH_STAR|DRIVER|GUARDRAIL|FINANCIAL|QUALITY|CONTEXT (정의 포함. CONTEXT = verdict 금지 명시. display_role과 구분: priority=왜 중요한가 / display=UI 위치)
3. US/BR 문장 범위 축소: "MSY PRIMARY는 FARROW_TO_FINISH 한정 PROPOSED. BREEDING 일괄 적용 금지"
4. EU 단일 프로필 폐기 → GB/DK/FR/ES/NL/IE 분리 (EU는 규제 context·PigSignal 시장 통계 용도만)
5. **CN 열 신설** (기존 누락). JP는 닫지 않고 STANDARD_COMMERCIAL/BRANDED_SPECIALTY 분리 옵션을 B-06 결정 자료로 (결정 대체 금지)
6. 국가 정책 승인 게이트 G-C1~C8: 정의 / 공식·분모 / 의사결정 용도 / 출처 4요소 / **입력 수집 가능성** / **경보 actionability** / 현지 검토 / 승인
7. 출처 우선순위 5단계 (정부·공공 > 상업농장 집계 > 동료심사 > 벤더 > 기사. 4~5 단독 승격 금지)
8. 테스트 계획 T-K1~K10 (농장유형별 상이 resolved / EU 프로필 저장 거부 / INSUFFICIENT 승격 불가 / farm_type 미지정 안전 기본 / denominator 없는 C1 금지 / VN·TH 숫자 비교문 0건 / NORTH_STAR·GUARDRAIL UI 분리 / JP 프로필 분리 / GB indoor·outdoor 혼합 금지 / 승인 전 seed 0건)
9. 변경 이력 + v0.3.1 diff 요약

### T2 — Evidence Register 스텁 (`docs/kpi/evidence/`)
- 13개국: US·BR·GB·DK·FR·IE·ES·NL·CN·VN·TH·JP·KR_INTERNAL.md
- 각 파일: 레코드 규격(country/farm_type/production_stage/kpi_code/recommended_display_role/priority_class/source_title/owner/year/cohort/denominator/representativeness/license_status/evidence_status[CONFIRMED|REVIEWED_DIRECTION|INSUFFICIENT|UNVERIFIED_DRAFT]/decision_status/notes) + "실사 시 원출처 대조 필수" 배너 + GPT 초안 해당분 UNVERIFIED_DRAFT 격리 수록
- KR_INTERNAL: 한돈팜스 7 KPI(기검증)는 CONFIRMED, A-rule 차단 명시
- 실사 우선순위: US → VN·TH → CN → BR → EU 국가들

### T3 — INDEX 패치 제안 (`docs/kpi/INDEX_patch_proposal.md`)
직접 수정 금지. #1 범위 추가안(차원 확장·priority_class·evidence/·G-C)만 제안.

### T4 — 대표 결정 요청서 (`docs/meetings/CEO_DECISION_BRIEF_v0.1.md`)
안건 4건, 각 1페이지 이내, [배경 3줄 / 선택지 / 권고 / 결정 시 풀리는 것] 형식 — 대표가 그 자리에서 O/X 가능한 형태:
① Entitlement Matrix 결재 — D-08(두수 무제한)/D-09(경영 P0)/D-10(R1·R2) 요약 + 승인 시 착수 개발 항목 (docs/product/PIGOS_FEATURE_ENTITLEMENT_MATRIX.md 요약)
② D-07 KR 데이터 해외 비교 — A-rule 충돌 사실관계 + 대안(공개 벤치마크/축적 데이터) + "금지 유지" 권고와 근거
③ B-06 일본 — T1-5의 프로필 분리 옵션을 결정지로
④ Safe Claim Matrix 개정안 — "제3자 출처 인용 기반 사실 비교 허용" 예외 문안 초안 (Matrix 자체 수정 금지 — 제안만)
금지: decision_status 변경 / 승인 대체 / 회의록에 없는 근거 발명

## 게이트
G1 미검증 격리 자가 감사 — UNVERIFIED_DRAFT 외 상태로 승격된 GPT 유래 항목 0건 (grep)
G2 수치 0건 — evidence에 임계·평균값 기입 0건 (4요소 완비 기존 CONFIRMED 제외)
G3 모순 검사 — A-rule·R1/C1/R2·zero override·Asset Policy 문장 변경 0건 + **2026-06-17_country-kpi-differences.md와의 모순 발견 시 보고 섹션에 명시 (임의 조정 금지)**

## 금지
코드·DDL·seed · 수치 발명 · GPT 초안 승격 · A-rule/Asset Policy 변경 · B-06·D-07 결정 대체 · INDEX·Matrix 직접 수정

## 완료 보고
표준 형식 + 미확정 목록(근거 없는 국가/라이선스 미확인/현지 검토 필요국) + G1~G3 감사 결과 + 기존 문서 모순 목록
