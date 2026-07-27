# PigOS 다음 개발 사항 (이어가기용)

> 갱신 2026-07-23. 브랜치 `feat/consent-infra` (PR #1 draft, https://github.com/wiselake/pig-os/pull/1). **배포 미실시.**
> 세션 상세는 PROGRESS.md 최상단(2026-07-23). 원칙: 위조0 · prod alembic 금지(divergent) · 배포는 사람 결정.
> (이전 2026-06-10 판은 MVP 스프린트 기준 — 아래로 대체됨.)

---

## 0. 복귀 직후 (환경)
```bash
# Docker가 자주 죽음(chronic) → 재시작 후 postgres 기동
powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'"
docker start pigos-postgres          # pg_isready -U pigos 로 확인
cd api && uv run pytest tests/unit -q                 # 418 pass 기대
cd src && NODE_OPTIONS=--experimental-require-module npx vitest run   # 69 pass, tsc clean
```
- 노드: `/c/Users/bjh/AppData/Roaming/nvm/v22.11.0`. 프론트 빌드/테스트는 `NODE_OPTIONS=--experimental-require-module` 필요.
- 프로드 백필 등 prod write는 하네스 분류기가 게이트 → 사람이 `--write` 직접 실행.

## 1. 지금까지 (이번 세션 완료, 전부 커밋·push)
- **동의 인프라**: 법역판별·consent_ledger·API·온보딩 연결·재고지 배너 (문구 DRAFT placeholder)
- **KPI PigPlan 정합**: PSY 29.0≈29.1·NPD 여집합·모돈회전율 신규·하베스트 orphan 복구·2807 백필 (deep-research V1~V7 검증)
- **i18n 규칙4 완결**: 인라인 딕셔너리·하드코딩 전부 messages 8개어
- **KPI v0.4 P1 골격**: country_kpi_policy 테이블 + 상속 리졸버 + GLOBAL seed 14(현재 동작 codify, priority_class=NULL)

---

## 2. 다음 개발 (우선순위)

### B1. KPI v0.4 P1-b — 리졸버를 대시보드/룰엔진에 연결 【자율 가능·추천】
현재 대시보드 KPI 카드 하드코딩(PSY/NPD/FR 고정) → `resolve_display_kpis()` 결과로 **동적 표시**하도록 리팩터. 룰엔진도 resolved `rule_enabled` 존중. 프론트/룰엔진은 resolved만 조회(원본 금지).
- 파일: `api/app/services/kpi_policy_resolver.py`, `src/app/(app)/page.tsx`, `api/app/engine/`. 선행 없음.

### B2. KPI v0.4 P1-c — priority_class 배정 【제품결정 필요】
NORTH_STAR(대표지표) 등 6분류를 (country×farm_type×stage)별 배정. 현재 seed priority_class=NULL(미결).
- 예: US·F2F NORTH_STAR=MSY? / 번식전업=PSY? (2026-07-21 회의 방향만, 미확정) → 대표 확인 후 APPROVED seed.

### B3. consent 국가별 표시 세부 【md 설계문서 대기】
인프라는 구현됨. 국가별 표시 문구/분기 세부는 사용자 추가 md 오면 착수. 참조 `docs/legal/TERMS_DISPLAY_SPEC.md`.

### B4. KPI Phase B — 국가별 산식 정제 【1차출처 조사 대기】
국가별 계산 공식/분모 차이 반영. **위조0**: PigCHAMP/PigPlan 1차문서·사산율(미라포함)·MSY 정의·China WEPIG·각국 법정 이유일령(EU만 확보)=미확보 빈칸.
- 참조: `docs/specs/COUNTRY_KPI_DEFINITION_MATRIX.md`(V1~V7) + `docs/kpi/gpt_country_draft_UNVERIFIED.md`(구조만 확정).
- 절차: 출처확보 → G-C1~C8 게이트 → Decision Register APPROVED → country_kpi_policy override 행.

### B5. 배포 & PR 머지 【사람 결정】
PR #1 draft → ready + 머지. 배포: `docker-compose.prod.yml -f docker-compose.deploy.yml` + `--force-recreate` + 서버 .env 보존. **prod alembic 금지**(consent_ledger·country_kpi_policy 마이그레이션 로컬/CI 전용, 스키마 수동 확인). 서버 ssh ubuntu@52.78.65.6(키 C:\dev_env\keyfile\wiselake-app-key.pem), ~/pigos.

---

## 3. 백로그 (CLAUDE.md 설계만)
- **Phase 2**: Task 자동배정(노동력 절감), PRRS 유전자 추적, Traceability Addon(B2B)
- **모바일 Android**: Kotlin+Compose+Room 오프라인 우선 (공용 자산: FastAPI/OpenAPI/sync/KPI공식/디자인토큰)
- **경영 KPI 도메인**(v0.3.1 §6): source_documents(OCR)·기간운영비·현금손익. B-08(보안) 해소 전 프로덕션 금지
- **R2 특화 예측**(유료, B-07 후) · 트라이얼/과금(BILLING_ARCHITECTURE_NOTE 참조)

## 4. 상시 규율 (위반 금지)
- **위조0**: APPROVED·VERIFIED 아닌 수치·정책은 코드/seed 금지, UNVERIFIED_DRAFT 격리. 역-피팅 금지.
- prod alembic 금지(divergent) · Oracle PKSU READ-ONLY(FARM_NM 등 PII 금지, 훅 차단) · 비밀값 env only
- i18n 8개어 파리티(i18n.test.ts) · 인라인 딕셔너리 금지 · admin은 ko전용(설계)
- 커밋 trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` · 피처 브랜치 커밋/push 자율 OK, prod 배포만 확인
