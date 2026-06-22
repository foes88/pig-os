# Codex 독립 검증 프롬프트 — 2026-06-22 야간 작업 교차검증

> 목적: Claude Code가 오늘 한 작업을 **독립적으로(코드를 의심하며) 재검증**한다.
> 절대규칙: **통과 위조 0.** 실제로 명령을 실행해 결과로만 판정. 미확인은 "미검증"으로 표기.
> push 금지·운영DB/배포/env 변경 금지. 로컬 dev 스택만.

## 0. 스택 기동 확인
- `curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health` → 200 기대
- `curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/login` → 200 기대
- 죽었으면: Docker Desktop → `docker compose up -d postgres redis` → `cd api && uv run alembic upgrade head` → `uv run uvicorn app.main:app --port 8000` / `cd src && npx next start -p 3000`

## 1. 베이스라인 회귀 (직접 실행해 숫자 확인)
- `cd api && uv run pytest tests/ -q` → **395 passed** 기대. 다르면 실패 목록 보고.
- `cd src && npx playwright test --config=playwright.live.config.ts` → **33 passed** 기대.
- `cd src && npx tsc --noEmit` → 0 에러.
- `cd src && npm run build` → 성공(44 routes).

## 2. 오늘 변경분 — 항목별 독립 검증

### 2a. 07~10 풀 hifi (커밋 9c10665, a81f483)
- `/kpi`: 스파크라인 KPI카드·PSY/NPD 추이차트·손실/신호요약·전월비교·AI정형요약 렌더. **raw hex 없어야** → `grep -rnE "#[0-9a-fA-F]{6}" src/app/\(app\)/kpi src/app/\(app\)/alerts src/components/ui/charts.tsx` 결과 0.
- `/alerts`: 심각도 탭(긴급/주의/정보) + 타입별 신호카드. 신호 클릭 → `/alerts/[type]` 상세(감지규칙·현재값vs임계·관련개체·권장조치).
- `/sows`: Forest 토큰 배지(블루계열 cyan/slate/orange 잔재 없어야) + overdue 연동 '위험' 컬럼.
- **함정 점검**: 손실 '금액'을 실제 데이터 없이 위조했는가? → 코드에서 손실 금액은 `estimated_loss`(백엔드 제공) 있을 때만, 신호별 가짜 ₩ 없어야. 확인.

### 2b. 생산성적 보고서 단일 허브 (a81f483)
- `/reports`·`/reports/{reproduction,farrowing,grow-finish,comprehensive-daily}` 상단에 ReportsTabs 5개 탭. 각 페이지 ReportsTabs 1회씩.
- `/reports` BarChart de-hex 확인(currentColor 토큰).

### 2c. 한국어 = 플랫폼 관리자 전용 (dea053f, 0fb2032)
- **로그인 전**(`/login`): 언어 옵션에 한국어 **없어야**(EN/中文/ES/VI). `language-option-ko` 부재.
- **FARM_OWNER 로그인**(e2e@pigos.io/e2e!2026pw): Topbar 언어 스위처에 ko 없음. ko 쿠키 강제해도 en으로 클램프.
- **SUPER_ADMIN 로그인**(admin@pigos.io/admin!2026pw): ko 포함 5개어 노출.
- 관련 E2E: `npx playwright test --config=playwright.live.config.ts -g "i18n 5-language"` → 2 passed.
- i18n 패리티: `node -e "const en=require('./src/messages/en.json'),ko=require('./src/messages/ko.json'); const f=(o,p='')=>Object.entries(o).flatMap(([k,v])=>v&&typeof v=='object'?f(v,p+k+'.'):[p+k]); const e=f(en),k=f(ko); console.log('en',e.length,'ko',k.length,'missing',e.filter(x=>!k.includes(x)))"` → 누락 0 기대(5개 파일 교차).

### 2d. 운영자 콘솔 Phase 0 (0d68151)
- 백엔드 게이트(토큰 발급 후):
  - admin → `GET /api/v1/admin/overview` 200 + `{organizations,farms,users,sows}` 정수.
  - FARM_OWNER → 403. 무토큰 → 401.
  - `cd api && uv run pytest tests/integration/test_admin_console.py -q` → 5 passed.
- 프론트: `admin@pigos.io`로 `/admin` 접근 → 개요 카드. `e2e@pigos.io`로 `/admin` → `/`로 리다이렉트(차단).
- **함정 점검**: `system_role`(게이트 권위 필드)과 `role` 둘 다 SUPER_ADMIN인지. role만 SUPER_ADMIN이고 system_role=FARM_OWNER면 게이트 우회/오작동.

### 2e. 보도자료 (91b5be1) — 사실관계만
- KO/EN 양쪽: 한국이 **타깃 시장에서 제외**(4개: 미국·중국·동남아·중남미), 단 27년 피그플랜 한국 **헤리티지는 유지**.
- 공개 언어 6개(한국어 제외). 시제 미래형(7/1 출시). 요금 '개발 중'(수치 비공개). 연락처 wiselake@wiselake.co.kr/pigos.io만.
- 과장표현("최초/유일") 근거 없는 단정 없어야.

## 3. 적대적 점검 (버그 적극 탐색)
- 테넌트 격리: admin이 아닌 FARM_OWNER가 **다른 farm_id**의 /sows·/reports·/events 접근 시 403/404인지.
- 한국어 게이트 우회: ko 쿠키 + 비관리자에서 새로고침 반복 시 ko로 새는 경로 없는지.
- delete 이벤트 롤백: 교배 삭제 → 모돈 OPEN 복귀(이미 회귀테스트 있음, 재확인).
- /admin 라우터: 라우터 전체 `dependencies=[require_super_admin]` 걸렸는지(경로별 누락 없는지).

## 4. 판정 리포트 형식
각 항목 [PASS]/[FAIL]/[미검증] + 근거(명령·출력). FAIL은 재현 절차. 위조 절대 금지.
종합: green/이슈수. 발견 이슈는 `docs/verification/`에 기록.
