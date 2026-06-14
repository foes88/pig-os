# PigOS — Codex 실행 검증 런북 (User-Run Verification)

> 목적: Cowork 세션에서 작성/검증된 코드를 **사용자 머신(또는 Codex CLI)에서 실제 실행**해
> 동일 결과가 나오는지 확인한다. 각 단계는 **명령 → 기대 출력 → 합격 기준** 순.
> 환경 제약(샌드박스)으로 Cowork에서 "실행"하지 못한 통합테스트·Vitest를 여기서 통과시킨다.

---

## 사전 준비

| 도구 | 버전 | 확인 |
|------|------|------|
| Docker + Compose | 최신 | `docker --version` |
| Python | 3.12+ | `python --version` |
| uv | 최신 | `uv --version` |
| Node | 22+ | `node --version` |

```bash
cd C:\dev\PigOS    # (Windows) 또는 프로젝트 루트
```

---

## Phase 0 — git 정리 (1분)

세션 첫 커밋 때 생긴 stale lock 정리. **커밋·워킹트리는 정상**, 인덱스만 잠김.

```bat
del .git\index.lock 2>nul
git reset
git status            REM  내 커밋 외 변경은 줄바꿈 정규화된 옛 파일들(이번 세션 무관)
git log --oneline -20
```
**합격**: `git log`에 `feat(phaseN)...` 커밋들이 보이고, `git status`가 더 이상 validators/alerts 등을 "deleted"로 표시하지 않음.

---

## Phase 1 — 백엔드 유닛 테스트

```bash
cd api
uv sync
uv run pytest tests/unit -q
```
**기대 출력 끝줄**: `219 passed`
**합격**: 219 passed, 0 failed.

---

## Phase 2 — 백엔드 통합 테스트 (Docker DB)

```bash
# 루트에서
docker compose up -d postgres redis
# pigos_test DB 생성 (최초 1회)
docker exec -it pigos-postgres psql -U pigos -c "CREATE DATABASE pigos_test;" || true

cd api
uv run alembic upgrade head        # 마이그레이션 (f1a2b3c4d5e6 = llm_usage_logs 포함)
uv run pytest tests/ -q            # 유닛 + 통합 전체
```
**기대**: 유닛 219 + 통합 ~30 = 약 **249 passed**.
**합격**: integration 디렉터리 테스트가 connection refused 없이 실행되어 통과.
**참고**: 통합 테스트 파일 4종 —
`test_validation_errors.py`(7) · `test_alert_service.py`(4) · `test_full_breeding_cycle.py`(2) · `test_reports.py`(2) + 기존 `test_event_service.py`.

---

## Phase 3 — 프론트 타입체크

```bash
cd src
npm install
npx tsc --noEmit
```
**합격**: 출력 없음(에러 0), 종료코드 0.

---

## Phase 4 — 프론트 Vitest (이번에 신규 설치)

```bash
cd src
npm i -D vitest jsdom @vitejs/plugin-react @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm test -- --run
```
**기대**: `tests/components/QuickInputDrawer.test.tsx`, `Sidebar.test.tsx`, `tests/pages/alerts.test.tsx` 통과.
**합격**: 모든 test files passed. (실패 시 §트러블슈팅)

---

## Phase 5 — API 스모크 (서버 기동 후 curl)

```bash
docker compose up -d          # api 포함 전체
curl -s http://localhost:8000/health
```
**기대**: `{"status":"ok","version":"..."}`

```bash
# 로그인 → 토큰
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test001@pigos.io","password":"12312300"}'
```
**기대**: `access_token` 포함 JSON 200.
> 토큰을 TOKEN 변수에 넣고 farm_id를 확인 후 아래 호출:
```bash
TOKEN=...; FARM=...
curl -s "http://localhost:8000/api/v1/farms/$FARM/alerts/overdue" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/api/v1/farms/$FARM/config/repro" -H "Authorization: Bearer $TOKEN"
curl -s "http://localhost:8000/api/v1/farms/$FARM/reports/reproduction?start_date=2026-01-01&end_date=2026-06-01&period=monthly" -H "Authorization: Bearer $TOKEN"
```
**합격**: 각 200, JSON 스키마가 OverdueSummary/FarmReproConfig/ReproductionRow[] 형태.

---

## Phase 6 — 수동 UI 스모크 체크리스트

`docker compose up` + `cd src && npm run dev` → http://localhost:3000 (test001@pigos.io / 12312300)

| # | 페이지 | 동작 | 기대 |
|---|--------|------|------|
| 1 | `/` 대시보드 | 로드 | KPI 카드 + "관리대상 모돈" 카드 → 클릭 시 `/alerts` |
| 2 | `/alerts` | 로드 | 6유형 요약카드 + 과기한 테이블 + 도태권고. Sidebar Alerts에 **배지 숫자** |
| 3 | `/sows` | 상태 필터/검색 | 목록 + 등록/수정 모달 |
| 4 | `/sows/{id}` | 상세 | 번식 타임라인 + **산차별 성적표** + **다음 예정 이벤트** + "최근 삭제" |
| 5 | `/record` | 모바일 폭 축소 | 좌우→상하 스택 전환(반응형) |
| 6 | `/boars`, `/finishers` | 21개+ 등록 | **페이지네이션(이전/다음)** 노출. finishers **그룹 수정** 모달 |
| 7 | `/reports/reproduction` | 기간 프리셋 | 월별 표 + **CSV 다운로드** |
| 8 | `/reports/grow-finish` | 로드 | 그룹별 ADG/FCR/폐사율 + CSV |
| 9 | `/settings/farm` | 값 변경+저장 | PATCH 반영, 저장 토스트 |
| 10 | `/settings/benchmarks` | 로드 | 국가별 참고표 + 현재 설정값 |
| 11 | `/notifications` | 필터 탭 | 전체/위험/주의/정보 필터 동작 |

**합격**: 11개 모두 콘솔 에러 없이 동작.

---

## 합격 종합표

| Phase | 항목 | 합격 기준 | 결과 |
|-------|------|-----------|------|
| 1 | 유닛 | 219 passed | ☐ |
| 2 | 통합 | ~30 passed (DB) | ☐ |
| 3 | tsc | 0 errors | ☐ |
| 4 | Vitest | all passed | ☐ |
| 5 | API smoke | 200 + 스키마 | ☐ |
| 6 | UI 11항목 | 무에러 동작 | ☐ |

전부 ☑ 이면 → **검토 후 `git push`** (자동 push 안 함).

---

## 트러블슈팅

- **`ModuleNotFoundError: datetime.UTC`** → Python 3.10 사용 중. 3.12로 실행(`uv python install 3.12`).
- **integration connection refused** → `docker compose up -d postgres` 누락 또는 `pigos_test` DB 미생성.
- **Vitest 모듈 못 찾음** → Phase 4 install 명령 누락. 설치 후 재실행.
- **alembic 충돌** → `uv run alembic heads` 로 head 확인(`f1a2b3c4d5e6`). 다중 head면 `alembic merge`.
- **vercel/CI** → `src/vercel.json`, `.github/workflows/ci.yml` 존재. CI는 PR→development 트리거.

---

## 참고
- 전체 세션 내역: `docs/AUTONOMOUS_SESSION_REPORT_2026-06-10.md`
- 다음 단계/로드맵: `docs/NEXT_STEPS.md`
- QA 점검 결과: `docs/QA_REPORT.md`
