# PigOS — Codex 독립 UAT 재검증 프롬프트 (2026-06-19)

> 목적: Claude가 보고한 UAT 결과(`docs/verification/uat_20260619_0914/REPORT.md` — 28 passed / 0 failed)를
> **그대로 믿지 말고 codex가 직접 재실행**해서 진위를 검증한다. 위조·날조·SKIP 은폐가 없는지 감사한다.

---

## 0. 역할

너는 PigOS 웹앱 UAT의 **독립 검증자(2nd opinion)**다. Claude가 만든 보고서를 신뢰하지 말고,
스택을 직접 띄워 동일 live E2E를 재실행하고, **Claude의 PASS/SKIP 분류가 정직한지** 교차 감사한다.

**절대 규칙 (위반 시 보고 무효):**
1. 통과를 위조하지 않는다. 안 돌린 항목은 `SKIP + 사유`.
2. 프로덕션 코드/기존 스펙/helpers/DB 마이그레이션 **수정 금지**. 읽기·실행·보고 전용.
3. `git add/commit/push` 금지.
4. 판정 근거(명령 출력·로그 경로·관찰값)를 항목마다 남긴다.
5. Claude 보고서와 **결과가 다르면** 어디가 다른지 명시한다(어느 쪽이 맞는지 근거 포함).

---

## 1. 환경 (Windows / 경로)

- repo: `C:/dev/PigOS`
- 인프라: Docker Desktop의 postgres·redis 컨테이너
- API: FastAPI(uv), uvicorn `:8000`
- 웹: Next.js 15 (`src/`) — 현재 **프로덕션 빌드(`next start`) 로 :3000** 서빙 중
  (dev 모드 `.next` 파일 락 이슈 회피용. dev로 돌려도 무방하나, 돌린 모드를 보고서에 기록)
- 계정: `e2e@pigos.io` / `e2e!2026pw` (격리 농장 `932208a6-e693-4f79-bd7a-aa41fb5e109c`, FARM_OWNER)
- `NEXT_PUBLIC_API_URL` = `http://192.168.3.46:8000` (= 로컬 :8000으로 라우팅)

---

## 2. Preflight (먼저 확인하고 출력)

```bash
cd C:/dev/PigOS
git branch --show-current          # main 기대
git status --short                 # 프로덕션 코드 변경 없어야(문서/_uat_tmp만 untracked)
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/health   # 200 기대
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/login    # 200 기대
```
- 둘 중 하나라도 비정상이면 스택을 직접 기동:
  ```bash
  docker compose up -d postgres redis
  cd api && alembic upgrade head && PYTHONPATH=. uv run python scripts/seed_e2e.py
  cd api && uvicorn app.main:app --host 0.0.0.0 --port 8000     # 별도 셸
  cd src && npm run dev                                          # 별도 셸 (또는 npm run build && npm start)
  ```
- API/웹 health 실패 시 즉시 중단(위조 금지).

---

## 3. 독립 재실행 (핵심)

```bash
cd C:/dev/PigOS/src
npm run test:e2e:live -- --reporter=list 2>&1 | tee ../docs/verification/uat_codex_<yyyyMMdd_HHmm>/run.log
```
- config: `src/playwright.live.config.ts`, 기존 spec: `src/e2e-live/*.spec.ts` (14파일/28테스트)
- **새 spec 작성 금지**(기존 것만 실행). 통과/실패 개수를 직접 집계한다.

기대치(Claude 보고 — 이게 맞는지 검증할 대상):
- `28 passed / 0 failed`
- 14 spec: auth, read, sow-crud, breeding-cycle, event-rollback, validation, cull,
  repro-accident, alerts-tabs, finisher-crud, ledger, daily-report, piglet-death, rbac,
  + `_uat_tmp/i18n-lang-switch`

---

## 4. 백엔드 독립 sanity (Claude 주장 교차검증)

로그인 토큰으로 직접 호출해 응답코드를 본다(Claude는 "전 엔드포인트 200" 주장):
```bash
API=http://localhost:8000
AT=$(curl -s -X POST $API/api/v1/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"e2e@pigos.io","password":"e2e!2026pw"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
FARM=932208a6-e693-4f79-bd7a-aa41fb5e109c
for ep in kpi/dashboard alerts/overdue alerts/cull-candidates tasks kpi/trend "sows?limit=50"; do
  echo "[$(curl -s -o /dev/null -w '%{http_code}' "$API/api/v1/farms/$FARM/$ep" -H "Authorization: Bearer $AT")] $ep"
done
```
전부 200이어야 한다. 다르면 보고.

---

## 5. 보고서 정직성 감사 (Claude REPORT.md 대조)

`docs/verification/uat_20260619_0914/REPORT.md`를 읽고 **각 PASS 항목이 실제 spec으로 뒷받침되는지** 확인:
- PASS인데 근거 spec이 없는 항목 → **거짓 PASS**로 지적
- SKIP인데 사실은 spec이 커버하는 항목 → **과소 보고**로 지적
- `run.log`의 실제 통과/실패 수 ≠ 보고서 요약 → 불일치로 지적
- screenshot/HTML report 경로를 지어낸 흔적 있는지(실패 0이면 스크린샷 없어야 정상)

---

## 6. 출력 형식

```
## Codex UAT 재검증 — {날짜시각}
### 스택/Preflight: API [200/실패] · 웹 [200/실패] · git status [깨끗/오염]
### 재실행 결과: N passed / M failed  (Claude 보고 28/0 과 [일치/불일치])
### 백엔드 sanity: 엔드포인트별 코드 (전부 200 [예/아니오])
### 보고서 정직성 감사:
  - 거짓 PASS: [없음 / 항목 나열]
  - 과소 SKIP: [없음 / 항목 나열]
  - 수치 불일치: [없음 / 상세]
### 최종 판정: [Claude UAT 보고 신뢰 가능 / 일부 수정 필요 / 신뢰 불가]
### 생성 파일: docs/verification/uat_codex_*/ (commit 안 함)
```

FAIL 또는 불일치가 하나라도 있으면 보고서 맨 위에 `⚠️ 불일치/FAIL 있음`을 먼저 출력한다.

---

## 7. 참고 문서 (읽기 전용)
- `docs/AI_UAT_PROMPT.md` — 원 UAT 실행 규칙(§9 정밀화 규칙 포함)
- `docs/uat-checklist.md` — §1~§8 체크리스트 원문
- `docs/verification/uat_20260619_0914/REPORT.md` — Claude 1단계 결과(검증 대상)
- `docs/mobile-integration-contract.md`, `docs/api/openapi-v1.yaml` — 기대 동작 근거
