# cowork 밤샘 작업 프롬프트 — 실백엔드 E2E CRUD 스위트

> 실행: `cd C:/dev/PigOS && claude --dangerously-skip-permissions`
> 프롬프트: `/loop docs/cowork-e2e-crud-overnight.md 의 작업을 위에서부터 순서대로 진행해. 각 단계 완료 시 통과 확인 후 git commit. push 금지.`
> 최종 갱신: 2026-06-18

---

## 0. 미션
기존 `src/e2e/`(헤르메틱·mock)와 **별도로**, **실제 API+DB를 상대로** 브라우저에서 전체 사용자 여정(CRUD)을
끝까지 검증하는 라이브 E2E 스위트 `src/e2e-live/` 를 만들고 **그린**으로 만든다.
목적: mock이 못 잡는 "데이터가 실제로 흐르는가"(create→DB→재조회→KPI/보고서 반영→수정→삭제 롤백)를 차단.

## 1. 전제 (스택 기동 — 먼저 확인/실행)
- DB/Redis: `docker compose up -d postgres redis`
- 마이그레이션: `cd api && uv run alembic upgrade head`
- 시드(전용 농장): `cd api && PYTHONPATH=. uv run python scripts/seed_e2e.py`
  - 계정 **e2e@pigos.io / e2e!2026pw**, FARM_OWNER, country KR (격리 농장 — 데이터 마음껏 생성 가능)
- API: `cd api && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` (백그라운드)
- 웹: `cd src && npm run dev` (Playwright webServer가 자동기동/재사용)
- ⚠️ 라이브 E2E는 **헤르메틱 아님** → API가 떠 있어야 한다. 안 떠 있으면 그 지점 명시하고 멈춰라(통과 위조 금지).

## 2. 설정
- `src/playwright.live.config.ts` 신규: `testDir: ./e2e-live`, baseURL `http://localhost:3000`, **api 라우트 mock 안 함**, workers 1, retries 1.
  - 환경변수로 API base 주입 가능하게(기본 `.env.local`의 `NEXT_PUBLIC_API_URL` 사용 — 웹이 이미 그쪽을 호출).
- `package.json` 스크립트: `test:e2e:live`(= `playwright test -c playwright.live.config.ts`), `test:e2e:live:ui`.
- `src/e2e-live/helpers.ts`: 시드계정 로그인 헬퍼(실 `/auth/login`), 고유 식별자 생성기(`uniqueTag()` = `E2E-<epoch>-<n>`로 충돌 방지 — Date.now 대신 test 시작 시각 1회 캡쳐), 생성물 추적→afterAll 정리(가능 범위).

## 3. 테스트 시나리오 (실데이터 왕복)
> 각 테스트는 고유 귀표/그룹코드로 생성 → 단언 → 가능하면 삭제까지. 단언은 **실제 응답/화면 값** 기준.

- [ ] **auth-live**: 시드계정 로그인 → 대시보드 진입, `pigos-auth`/세션쿠키 셋, 401→refresh 동작
- [ ] **sow-crud**: 모돈 등록(고유 귀표) → 목록/검색에 보임 → 상세 진입 → 수정(품종) 반영 → 도폐사 → 목록서 제외(상태 종료)
- [ ] **breeding-cycle**: 모돈 등록 → 교배(GILT→PREGNANT, insights 배너 확인) → 분만(PREGNANT→LACTATING, 숫자 타이핑 입력) → 이유(LACTATING→OPEN) → 상태 전이 각 단계 화면 확인
- [ ] **event-edit-delete**: 위 사이클의 이벤트 수정(pre-fill 값) → 삭제 → **모돈 상태 롤백** 확인
- [ ] **finisher-crud**: 비육 그룹 등록 → 주간성적 입력 → 수정 → 출하
- [ ] **kpi-report-reflect**: 사이클 생성 후 대시보드 KPI/보고서(reproduction, group_by=breed)에 **수치 반영** 확인(0→증가)
- [ ] **alerts-tabs**: 알림 화면 2탭(관리대상/시스템알림) 전환, 배지
- [ ] **validation-live**: 분만 총산>35 등 → 화면에 422 메시지(해당 언어)
- [ ] (선택) **rbac-live**: VIEWER 계정 추가 후 쓰기 버튼 비활성/403

## 4. 규칙
- ❌ git push, 운영 DB/AWS/외부 유료 API. (로컬 dev DB·시드는 허용)
- ❌ 통과 위조: API 미기동/실패 시 명시하고 멈춤. flaky는 retries로 흡수하되 silent skip 금지.
- ✅ 생성 데이터는 고유 식별자 + afterAll 정리(불가 항목은 로그로 남김). 시드 농장 외 농장 건드리지 말 것.
- ✅ 단계 완료 시 `git commit -m "test(e2e-live): ..."`. 기존 `src/e2e/`(헤르메틱) 회귀 깨지 말 것.

## 5. 산출물 (아침 확인)
1. `src/e2e-live/` 스위트 + `playwright.live.config.ts` + `test:e2e:live` 스크립트
2. `src/e2e-live/helpers.ts`(실로그인·고유식별자·정리)
3. **라이브 E2E 통과 로그**(몇 개 통과/실패, 각 시나리오 결과)
4. 미해결/환경의존(예: API 미기동으로 못 돌린 항목)은 명시
5. PROGRESS.md 갱신 + 헤르메틱 `test:e2e:smoke` 여전히 green 확인
