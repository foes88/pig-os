# RUN_PROMPT_A — 정책 벡터 + Resolved Policy 구현
## 밤샘 자율 실행 프롬프트 (2026-07-21)

> **레포**: C:\dev\PigOS / **스펙 SSOT**: docs/specs/COUNTRY_KPI_RULE_SPEC_v0.3.1.md §4
> **런 로그**: [PLACEHOLDER: 런 로그 경로]
> **아키텍처 변수**: country_kpi_policy 도입 1개. 다른 시스템 변경 금지.

## G0 — 선행조건 (하나라도 FAIL 시 즉시 중단, 아무것도 수정하지 않음)
1. baseline 커밋 = `d54e897` 일치
2. 전체 테스트 `[PLACEHOLDER: 기대 테스트 수]`개 전부 PASS
3. 스펙 v0.3.1 존재·§4 로드
4. 신규 브랜치: `feat/kpi-policy-vector`

## 작업
### T1 — 스키마
- `country_kpi_policy`: 스펙 §4.2 DDL 그대로. 제약 3개 필수: chk_scope_keys / chk_global_complete / chk_approved_decided
- `kpi_policy_exceptions`: §4.8 (expires_at NOT NULL)
- Alembic 마이그레이션. 기존 테이블 변경 없음.

### T2 — Resolution 엔진
- GLOBAL → COUNTRY → FARM_TYPE(+production_system, herd_size_band 와일드카드) → TENANT. NULL 아닌 축만 override
- resolved 캐시(버전 태그). **리졸버·API는 resolved만 읽음** — 원본 직접 조회 경로 금지
- 재계산 실패 시 이전 버전 유지 + 로그 (fail-closed)
- decision_status != APPROVED 행 제외
- Override 방향 검증(§4.7): 완화 방향 저장 → 쓰기 시점 422
- 예외 만료분 resolved 미반영

### T3 — 테스트
T-A1'(compute=false 무평가 / HIDDEN&compute 분리) · T-A3(PROPOSED 미로드) · T-A4~A7(전 축 완화 거부) · T-A5(부분 override 상속) · T-A6(scope CHECK) · T-A8(예외 만료) · T-A9(resolved 전용)

### T4 — 시드
**시드 생성 금지.** APPROVED 행이 없으므로 빈 상태가 정답. GLOBAL 기본값 필요 시 docs/kpi/seed_proposal.md에 제안만 기록 후 중단.

## 게이트
G1 마이그레이션 왕복 성공 → G2 T2 단위 PASS → G3 신규 테스트 PASS + 기존 전체 무회귀. FAIL 시 revert 후 중단·사유 기록.

## 금지
push/deploy · 기존 리졸버 수정(연결은 별도 런) · 시드 값 발명 · 스펙 외 축·enum 추가 · 기존 테스트 수정으로 통과 조작

## 완료 보고
수정 파일 / 신규 테스트 수·결과 / 게이트 현황 / 미해결·제안 / 최종 커밋 해시
