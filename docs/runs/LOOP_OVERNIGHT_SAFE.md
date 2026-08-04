# LOOP_OVERNIGHT_SAFE — 퇴근 후 자율 loop 프롬프트 (안전·비날조)

> 목적: 사람 대기 없이 몇 시간 자율. **법무 빈칸 자동생성 금지**(그건 `docs/legal/HUMAN_INPUT_QUEUE.md`로 분리 — 손대지 말 것). 법무는 안전분 1회만, 나머지 시간은 검증가능한 코드 하드닝.

## 하드 규칙 (매 iteration 준수)
1. **push 금지 · 배포 금지.** 로컬 `git commit`까지만(trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`).
2. **위조0**: `HUMAN_INPUT_QUEUE.md`의 빈칸([OPEN]·대리인·[COUNSEL]·사업조건)을 **채우지 말 것**. 값 없으면 리포트만.
3. **각 변경 검증 후에만 커밋**: 백엔드 `cd api && uv run pytest tests/unit -q && uv run ruff check .`; 프론트 `cd src && NODE_OPTIONS=--experimental-require-module npx tsc --noEmit && npx vitest run`. 실패하면 **되돌리고** 다음으로.
4. **1 변경 = 1 커밋**(원자적). 동작 바꾸지 말 것(테스트 추가·리팩터·문서만). 스키마/마이그레이션/과금/권한 손대면 멈추고 리포트.
5. **Docker 자주 죽음** → 죽으면 `powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'"` 후 대기 → `docker start pigos-postgres`. 3회 실패 시 DB 불필요 작업(unit·tsc·문서)만.
6. **막히거나 애매하면 멈추고** 그 지점을 리포트(추측 진행 금지).

## PHASE 1 — 법무 안전분 (1회, DRAFT·internal)
- **RUN L**: `SESSION_HANDOFF_ADDENDA_v1.4.md`의 RUN L(LIA 초안)을 `NEXT_RUN_PROMPTS_v2.0.md` 공통 규칙대로 실행 → `docs/legal/internal/LIA_PURPOSE2_DRAFT.md` 저장. **DRAFT·변호사 확정 전·게시 금지** 배너 필수. (변호사 회신 불요 항목)
- **갭맵**: v1.4 부속조항 6벌을 "PigPlan/경쟁사 vetted 파생(저위험) vs PigOS 신규·비KR(검토 필요)"로 분류 → `docs/legal/internal/ADDENDA_RISK_GAP_MAP.md`. **분석만**(문안 생성 아님), 출처 인용.
- ⚠️ **consent 인프라에 v1.4 실문안 배선은 하지 말 것**(구조 결정 필요 → 대화형 세션). Phase 1은 여기까지.

## PHASE 2 — 코드 하드닝 (시간/예산까지 반복)
우선순위 순, 각 단위 검증 후 커밋:
1. **프론트 테스트 커버리지 확대** (현재 vitest 69 → 미커버 페이지·컴포넌트 스모크/회귀): consent(ConsentForm·AmendmentBanner·settings/data)·kpi policy·reports·finishers·record 편집 등. 렌더·주요 상호작용·빈상태.
2. **백엔드 통합테스트 보강** (미커버 엔드포인트): consent record/withdraw 엣지, kpi/policy, reports CSV, 알림 필터. 기존 fixture 재사용.
3. **엣지케이스·접근성**: 빈데이터·에러상태·aria-label 커버.
4. **회귀 안전 리팩터**: 명백한 중복·미사용 제거(동작 무변경, 테스트로 보장).

## STOP 조건
- 테스트 전부 green + 뚜렷한 커버리지 갭 소진 / 예산·시간 도달 / 애매·블로커 → 리포트하고 종료.

## 종료 시 리포트
- 커밋 목록(로컬) · 추가 테스트 수 · 발견했으나 못한 것(사람 필요 항목) · HUMAN_INPUT_QUEUE에 새로 추가할 빈칸(있으면).
