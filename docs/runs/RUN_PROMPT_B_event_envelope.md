# RUN_PROMPT_B — Canonical Event Envelope 모델 + 검증기
## 밤샘 자율 실행 프롬프트 (2026-07-21)

> **레포**: C:\dev\PigOS / **스펙 SSOT**: docs/specs/COUNTRY_KPI_RULE_SPEC_v0.3.1.md §15
> **런 로그**: [PLACEHOLDER]
> **아키텍처 변수**: envelope 계약 1개. **기존 입력 경로 배선(rewiring) 금지** — 계약·검증기·테스트만. 연결은 감독 세션에서.

## G0 — 선행조건 (FAIL 시 즉시 중단)
1. baseline 커밋 `[PLACEHOLDER]` / 전체 테스트 `[PLACEHOLDER]`개 PASS
2. 브랜치 `feat/canonical-envelope` (baseline에서 분기 — 런 A와 독립)

## 작업
### T1 — Envelope 모델
스펙 §15 필드 그대로 Pydantic 모델 + enum:
- 필수: event_id, tenant_id, farm_id, country_code, event_type, occurred_at, available_at, source_system, mapping_status, created_at
- 조건부: currency(금액), source_document_id(문서 기반), canonical_code/value/unit(매핑 후)
- source_system: MANUAL|PIGPLAN_IMPORT|OCR|VOICE|SENSOR|API
- **canonical_unit은 SI만** — 기존 단위 상수 모듈 참조. 목록에 없으면 발명 말고 로그 후 중단

### T2 — 검증기
- 필수 필드 부재 → 명시적 ValidationError (silent default 금지)
- available_at < occurred_at 허용 여부: **스펙에 규정 없음 → 검증하지 말고 open question 보고만** (백데이트 입력이 정상일 수 있음 — 판단 발명 금지)
- mapping_status·quality_status enum 강제

### T3 — 테스트
T-V1 필수 필드 결여 거부(필드별) / occurred·available 분리 저장 / SI 외 단위 거부 / enum 외 source_system 거부

## 게이트
G1 단위 테스트 PASS → G2 기존 전체 무회귀

## 금지
push/deploy · 기존 이벤트 경로 수정 · DB 마이그레이션(계약만) · 스펙 외 필드 · 검증 규칙 발명

## 완료 보고
표준 형식 + **open questions 섹션 필수** (스펙 공백 발견분)
