# DATA_RIGHTS_CONSENT_SPEC v0.1 (SKELETON)
## 데이터 권리·동의·약관 구조 스펙

> **상태**: SKELETON — 골격 확정용. 조항 문안은 변호사 산출물로 채움. 런 D(docs/runs/RUN_PROMPT_D)가 국가별 리서치로 보강.
> **역할**: 신규 국가 가입 오픈 게이트 (country_launch_registry.can_signup의 문서 근거).
> **근거**: 2026-07-21 회의 §3 · 법무 분석(소유권≠활용권) · docs/legal-review-notes.md

---

## 1. 확정 구조

### 1.1 약관 계층 — "주마다 개정" 아님
```
공통 마스터 약관 (1벌)
 └ 국가별 부속조항 (US / VN / TH / BR / CN ...)
    └ US 주별 프라이버시 부칙 (1벌 — 주별 조항을 조건부로 담아 해당 주 사용자에 자동 적용)
```
개정 시 마스터 또는 해당 부속조항만 수정.

### 1.2 계약 4조항 + 결과물 권리
① 원본 데이터 권리 = 농장 귀속 ② 회사의 서비스 처리권 ③ **익명·집계 결과의 상업적 이용권** (범위 구체 기술 — 광범위 조항 = 불공정약관 리스크) ④ 원본·가명정보 제3자 제공 제한. + 표준분류체계·예측모델·산업벤치마크·AI 인사이트 = 회사 지식재산 명시.

### 1.3 동의 목적 (purpose_code)

| purpose_code | 내용 | 유형 |
|---|---|---|
| SERVICE_OPERATION | 서비스 운영 필수 | 기본 |
| ANONYMOUS_AGGREGATE | 익명·집계 통계 | 기본 |
| AI_MODEL_TRAINING | AI 학습·개선 | **선택** |
| PARTNER_RESEARCH | 특정 기업 연구 | **선택** |
| TRANSACTION_MATCHING | 거래연결·리드 | **선택** — 거래연결 BM 전제 |
| EXTERNAL_AI_PROCESSING | 외부 생성형 AI 처리(OCR 등) | 고지+국외이전 |

AI 학습은 "서비스 개선" 총칭 금지 — 5단계 분리 고지 (해당 농장 서비스 / 전체 정확도 / 범용모델 / 외부 AI 전달 / 파트너 맞춤).

### 1.4 동의 UI (대표 지시 = 개발 요구사항)
핵심 조항 볼드 강조 / 선택 목적 별도 체크(기본 OFF) / **동의 화면 스냅샷·hash 보관(증빙)** / 무료 이용과 선택 동의 비연동.

## 2. Consent Ledger 스키마 초안
```sql
consent_records:
  user_id, tenant_id,
  country_code, region_code,      -- region_code = US 주 등
  policy_type, policy_version,
  purpose_code, consent_status,   -- GRANTED|DENIED|REVOKED
  consented_at, revoked_at,
  rendered_document_hash, locale, ip_address, user_agent
```
- 철회 시 기존 파생 자산(집계·모델) 처리 = TBD-법무
- 목적 변경 시 재동의 트리거 / 유료 전환 시 활용권 유효성(대표 질의) = TBD-법무

## 3. 법무 의뢰 4건 (의뢰서 요구사항)
1. PigOS 이용약관 — **마스터+부속조항 구조, US 주별 부칙 포함** 명시
2. 농장 데이터 이용·라이선스 조항 (§1.2)
3. 개인정보처리방침 + 국외이전 (한국 서버, 외부 AI 처리)
4. PigSignal 기업용 데이터 라이선스 계약 (재식별·재판매·타깃영업 금지 조항)

동반 질의: 크레딧 환불의 전자금융거래법 성격 / 보도자료 "비공유·비판매" 문장의 익명·집계 예외 가능 여부 / AHDB 라이선스(B-02) / TRANSACTION_MATCHING 금융·보험 중개 규제 / **수집 컨택(명함·LinkedIn·크롤링) 콜드 아웃리치 국가별 적법성**.

→ 통합 질의서는 런 D 산출물 `docs/legal/LAWYER_BRIEF_v0.1.md`. Claude legal 스킬 입력으로 사용.

## 4. TBD
조항 문안(변호사) / 철회 파생물 처리 / 국가 부속 우선순위(US→VN→TH→BR→CN) / 지역 저장 요구(B-08 연동)

## 변경 이력
| v0.1 | 2026-07-21 | 스켈레톤. 구조·purpose·Ledger·의뢰 요구 확정 |
