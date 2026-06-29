# Codex 독립검증 프롬프트 — PigOS V&V 후속 (Opus 수정분 재검증)

> 목적: Opus가 이번 세션에 적용한 수정(아래 commit)을 **독립적으로 적대 재검증**.
> 추측 금지·창작 금지. 코드/스펙 근거만. 수정 금지(검증만) — BUG 발견 시 보고서에 재현절차로 기록.

## 0. CONTEXT
- repo: C:\dev\PigOS (foes88/pig-os). 백엔드 C:\dev\PigOS\api (FastAPI, uv), 프론트 C:\dev\PigOS\src (Next.js).
- DB: 로컬 docker `pigos`(운영 아님). 테스트DB `pigos_test`. 테스트: `cd api && uv run pytest tests/ -q`. 프론트: `cd src && npm run test:run`(Node22 필요).
- admin = 별도앱 아님(메인 Next.js `src/app/admin/*`가 메인 백엔드 `/api/v1/admin/*` 공유).

## 1. 재검증 대상 commit (각각 surgical patch가 의도대로인지 + 우회/회귀 없는지)
- `cd586ca` ACC-R2: GET /farms/{id}/members에 require_farm_role(_OWNER_ROLES). → WORKER/VIEWER/VET 403, OWNER/조직롤 200인지. 다른 list 엔드포인트도 동일 PII 열거 갭 없는지 횡단 점검.
- `058f54d` ADM-RULES-NULLCLEAR: model_fields_set으로 null-클리어. → enabled/warning/critical 조합(누락 vs 명시null vs 값) 전수, warning>=critical 가드 유지, 감사로그 정확.
- `09613a6` ACC-C-hardening: MemberCreate/Update extra=forbid. → 프론트가 보내는 필드와 정확히 일치하는지(과차단으로 정상요청 422 안 나는지), 다른 입력 스키마(이벤트/모돈/피드)도 mass-assignment 방어 필요한지.
- `54bb802` F2 + `a77510f` F1: 조직롤이 서브트리 농장 write 가능 + effective_farm_role 서브트리 강제. → require_farm_role 단독(FarmDep 없는) 라우트가 있는지 전수(있으면 F1 우회 가능), 조직롤이 서브트리 '밖' write 시 403인지.
- `f5bc505` sync #8/#4 + `158f7ab` C4/H1: 항목별 savepoint·tz·사이클연결. → dry_run 누수, 재동기화 멱등, 같은배치 IntegrityError 격리 실제 동작.
- `952f8c9` M4 / `580488a` M5: 보고서 빈기간 채움·농장tz. → 분기/연 경계, breed 그룹 미영향, tz 폴백.
- `9b70620` H1-H5/M2: 두수상한·크로스테넌트 모돈이력.

## 2. 중점 적대 시나리오 (NO-GO 후보)
- **테넌트 격리**: 2개 org/farm 구성, A 자격으로 B의 모든 read/write → 전부 차단인지(특히 신규/누락 엔드포인트).
- **권한 경계**: 역할×연산 negative 매트릭스 재실행. require_farm_role 없는 write 라우트 grep.
- **계정 수명주기**: suspend된 계정 토큰 즉시 무효, 권한상향 차단.

## 3. 산출물
- 재현가능 BUG 로그(test_id/repro/expected/actual/severity/layer/classification). BUG vs DATA vs CONFIG 구분.
- Opus 수정 중 **불완전/우회 가능/회귀 유발** 항목 명시. 깨끗하면 "확인됨"으로.
- 숫자/benchmark 필요 시 창작 금지 → 표기 후 STOP.
