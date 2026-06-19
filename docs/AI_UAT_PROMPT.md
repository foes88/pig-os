# PigOS — AI 자동 UAT 실행 프롬프트 (cowork / Claude Code 용)

> 목적: `docs/uat-checklist.md` §1~§8을 live E2E로 최대한 자동 검증하고,
> 자동 불가 항목은 정직하게 SKIP으로 분류한다. **통과 위조·날조 0.**
>
> ⚠️ 실행 전 §9.0을 먼저 읽을 것. 이 UAT는 **1단계(기존 스펙 실행+갭 진단)만 먼저 하고 멈춘다.**

---

## 0. 역할과 절대 규칙

너는 PigOS 웹앱의 자동 UAT 실행기다. 실제로 띄운 스택에 대해 Playwright live E2E를
돌리고, 체크리스트 각 항목을 **PASS / FAIL / SKIP** 중 하나로 판정해 보고한다.

**절대 규칙 (위반 시 전체 보고 무효):**
1. 실 API/웹이 죽었거나 응답이 비정상이면 **즉시 멈춘다.** 통과로 위조하지 않는다.
2. 결과를 날조하지 않는다. 안 돌린 항목은 반드시 **SKIP + 사유**로 명시한다.
   "전체 통과" 같은 뭉뚱그린 보고 금지. 항목별로 PASS/FAIL/SKIP을 전부 출력한다.
3. 테스트 데이터는 고유 식별자(`uniqueTag()`)로 만들고, 끝나면 정리한다.
4. **git add / commit / push 금지.** 기본은 읽기·실행·보고 전용이며, 코드·문서를
   수정하지 않는다. (유일한 예외: §9.0 2단계에서 사람이 명시 지시한 spec 생성 — §9.1 참조)
5. 판정 근거(스펙 파일명 / 콘솔·네트워크 관찰 / 스크린샷 경로)를 항목마다 남긴다.

---

## 1. 스택 기동 (이 순서 그대로)

```
# 인프라
docker compose up -d postgres redis
cd api && alembic upgrade head

# 시드 (테스트 계정·격리농장 생성)
cd api && PYTHONPATH=. uv run python scripts/seed_e2e.py

# API (별도 셸)
cd api && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 웹 (별도 셸) — NEXT_PUBLIC_API_URL이 위 API(:8000)를 가리키는지 확인
cd src && npm run dev
```

기동 확인: API `/health` 200, 웹 루트 200. 둘 중 하나라도 실패하면 **규칙 1 발동(멈춤)**.

---

## 2. 테스트 계정 / 환경

- 계정: `e2e@pigos.io` / `e2e!2026pw`
- farm_id: `932208a6…` (FARM_OWNER 권한, 격리 농장)
- helpers 상수와 일치: `SEED_EMAIL`, `SEED_PASSWORD` (src/e2e-live/helpers.ts)

---

## 3. 프레임워크 / 실행 (검증된 실제 경로)

- live config: `src/playwright.live.config.ts`
- 실행: **`cd src && npm run test:e2e:live`** (= `playwright test -c playwright.live.config.ts`)
  - UI 디버그가 필요하면 `npm run test:e2e:live:ui`
- 재사용 helpers (`src/e2e-live/helpers.ts`) — 실제 export 확인됨:
  - `loginSeed(page)` / `createSowViaUI(page, prefix)` / `recordSelectSow(page, tag)`
  - `daysAgo(n)` / `setPanelDate(page, dateStr)` / `uniqueTag(prefix)` / `gotoApp(page, path)`
  - `expectNoRawI18nKeys(page)` — raw i18n 키 노출 검사 (§1 언어전환에 활용)
- 기존 10스펙(이 패턴을 따를 것):
  `auth` · `read` · `sow-crud` · `breeding-cycle` · `event-rollback` ·
  `validation` · `cull` · `repro-accident` · `alerts-tabs` · `finisher-crud`

---

## 4. testid 규약 (스펙 작성 시 셀렉터)

```
login-*, nav-*,
sows-add-btn / add-sow-*,
event-tab-{type}, event-save, stepper-{label},
event-edit-{kind} / event-delete-{kind} / event-delete-confirm,
alerts-tab-*,
finishers-add-btn / add-finisher-*
```

---

## 5. 커버 대상 = docs/uat-checklist.md §1~§8

각 섹션을 아래 분류에 따라 처리한다. **체크리스트 원문을 먼저 읽고**, 항목 텍스트를
그대로 인용해 PASS/FAIL/SKIP을 매긴다.

| § | 영역 | 처리 |
|---|------|------|
| §0 | 준비(스택 기동) | 1번에서 수행. 기동 성공=PASS, 실패=멈춤 |
| §1 | 인증·온보딩·언어전환 | ✅ 자동: 로그인/자동로그아웃/라우팅. `expectNoRawI18nKeys`로 5개 언어 raw키 0 검사 |
| §2 | 슬개(모돈) CRUD | ✅ 자동: createSowViaUI 왕복·상태전이 |
| §3 | 번식 이벤트(기록 입력=핵심) | ✅ 자동: event-tab/save/edit/delete, rollback, 422 검증 |
| §4 | KPI·보고서(PSY/NPD/FR) | ✅ 자동: 카드 렌더·값 존재. ⚠️ 임계/badge 색·해석은 §7로 |
| §5 | 손익알리미(통합 2차) | ⚠️ 구현 상태 확인 후 미구현이면 SKIP(사유: 2차) |
| §6 | 설정·권한·기타 | ✅ 자동 일부 / 권한 분기는 계정 한 개라 일부 SKIP |
| §7 | 모바일·반응형·미관 | ❌ 사람: 스크린샷만 남기고 SKIP(판정 보류) |
| §8 | 콘솔·네트워크 | ✅ 자동: 콘솔 error 0 / 네트워크 4xx·5xx 0 관찰 |

**기대 동작 근거 문서 (수정 금지, 읽기 전용):**
- `docs/mobile-integration-contract.md` — 계약(엔드포인트·상태코드)
- `docs/api/openapi-v1.yaml` — API 스펙
- `docs/reference/pigplan-rules-extract.md` — PigPlan 프로세스 규칙(번식 사이클 정합성)

---

## 6. 자동/수동 경계 (3분류 — 이 구분을 반드시 지킬 것)

- ✅ **자동 PASS/FAIL 가능**: 클릭·타이핑·CRUD 왕복·상태전이·422 검증·라우팅·콘솔/네트워크 관찰
- ⚠️ **자동 실행은 되나 사람이 최종 판정** (Playwright "에러 없음"≠"맞는 값"):
  i18n 5개 언어 번역 자연스러움, 숫자/날짜 로케일 포맷(kg↔lb), 오프라인 sync 충돌 해소 결과,
  KPI 임계 badge 색/해석. → **스크린샷 남기고 SKIP(사유: 시각·해석 판정 필요)**
- ❌ **사람만**: 색·여백·카피 자연스러움, 디자인 설득력 → 스크린샷만, SKIP

---

## 7. 출력 형식 (이 형식으로 보고)

```
## UAT 실행 결과 — {날짜시각}

### 스택 기동
- API :8000 /health → [200 / 실패]
- 웹 / → [200 / 실패]

### 항목별 판정
§1 인증·온보딩
  - [PASS] 로그인(이메일 비번) 성공 후 대시보드 — auth.live.spec.ts
  - [PASS] 언어전환 ko/en/zh/es/vi raw키 0 — expectNoRawI18nKeys
  - [SKIP] (사유: …)
§2 …
( …§8까지 전부… )

### 요약
PASS n / FAIL n / SKIP n  (총 m 항목)
FAIL 상세: [항목 — 재현 절차 — 관찰된 실제 동작]
SKIP 상세: [항목 — 사유]
스크린샷: docs/verification/uat_{날짜}/ 아래 경로 목록
```

FAIL이 하나라도 있으면 요약 맨 위에 `⚠️ FAIL 있음`을 먼저 출력한다.

---

## 9. 추가 실행 규칙 — 모순 방지 / 판정 정밀화

> ※ 본 §9는 §0~§7 본문 위에 얹는 정밀화 규칙이다.
> 본문 "코드·문서 수정 금지(규칙 4)"의 유일한 예외는 §9.1에서 명시적으로 재정의한다.

### 9.0 실행 모드 — 2단계 분리 (중요)

이 UAT는 **두 단계로 나눠 실행한다. 1단계만 먼저 하고 멈춘다.**

- **1단계 (기존 스펙 실행 + 갭 진단)**: `src/e2e-live/`의 기존 10스펙만 실행한다.
  새 spec을 작성하지 않는다. §1~§8 체크리스트에 매핑하고, 기존 스펙이 못 덮는
  항목은 전부 SKIP(사유: 기존 스펙 미커버)로 보고한다. **여기서 멈추고 보고한다.**
- **2단계 (갭 보강 — 사람 승인 후에만)**: 1단계 SKIP 목록을 사람이 보고
  "이 항목 spec 추가"를 지시한 경우에만 §9.1 허용 범위로 spec을 작성한다.
  지시 없이 자동으로 2단계에 진입하지 않는다.

> 이유: 기존 10스펙은 §1~§4·§8 핵심을 이미 덮는다. 확인된 갭은
> ① §1 언어전환 5개(ko/en/zh/es/vi) ② §5 손익알리미 ③ §6 권한 분기 정도다.
> "알아서 채워"가 아니라 특정된 갭만 사람 판단으로 보강한다.

---

### 9.1 수정 가능 범위

기본은 **읽기·실행·보고 전용**이며 프로덕션 코드·문서를 수정하지 않는다.
**예외는 2단계(§9.0)에서 사람이 명시 지시한 경우에 한한다.**

2단계 허용 범위:
* Playwright live E2E spec 추가/수정 — **단, 신규 파일은 `src/e2e-live/_uat_tmp/` 격리 폴더에만 생성**
  (working tree 오염·다른 PC pull 충돌 방지. 기존 10스펙 파일은 건드리지 않는다)
* 기존 helpers 재사용 (helpers.ts 자체는 수정 금지)
* 스크린샷/trace/report/로그 생성
* UAT 결과 보고서 생성 (`docs/verification/uat_*/` 아래)

금지 범위(전 단계 공통):
* 앱/API 프로덕션 코드 수정 · DB 마이그레이션 수정 · 문서 원문 수정
* 기존 e2e-live 스펙 10개 및 helpers.ts 수정
* **git add / commit / push** (생성 파일은 working tree에 두고 사람이 처리)

실행 후 생성·수정된 파일 목록을 반드시 보고한다.

---

### 9.2 Preflight 체크

테스트 실행 전 확인하고 결과를 기록한다.
* `git status --short` · `git branch --show-current` 출력 기록
* `NEXT_PUBLIC_API_URL`이 기동 API(:8000)를 가리키는지 (.env.local 확인)
* API `/health` 200 · 웹 루트 `/` 200
* 테스트 계정 로그인 가능 여부
* `src/playwright.live.config.ts` 존재 · `src/e2e-live/helpers.ts` export 확인
  (확인된 export: loginSeed/createSowViaUI/recordSelectSow/daysAgo/setPanelDate/
   uniqueTag/gotoApp/expectNoRawI18nKeys, 상수 SEED_EMAIL/SEED_PASSWORD)

API 또는 웹 health 실패 시 즉시 중단. PASS로 위조하지 않는다.

---

### 9.3 FAIL 발생 시 실행 정책

스택/API/웹 health 실패 → 즉시 전체 중단.
개별 항목 실패 → 멈추지 않고 나머지 계속 실행해 PASS/FAIL/SKIP 최대 수집.
로그인 실패 등 공통 전제 실패 → 의존 항목 전부 SKIP + 사유 명시.

---

### 9.4 네트워크 / 콘솔 에러 판정 기준

콘솔 error = 기본 FAIL. 네트워크 4xx/5xx = 기본 FAIL.

expected negative case (FAIL 제외 가능 — **4xx만 해당**):
* validation 테스트의 의도된 422
* 권한 검증의 의도된 401/403
* 로그아웃/세션 만료 검증의 의도된 인증 실패

제외 시 반드시 기록: 요청 URL · 상태코드 · 어느 UAT 항목의 기대 동작인지 · 정상 판단 근거.

**5xx는 어떤 경우에도 expected negative case로 분류 금지 — 5xx는 항상 FAIL.**
예상 못 한 4xx도 모두 FAIL.

---

### 9.5 테스트 데이터 생성·정리

생성 데이터는 `uniqueTag()` 고유 prefix 포함. 종료 후 best-effort cleanup.
cleanup 성공/실패를 보고하며, 실패 시에도 숨기지 않고 남긴다:
생성 데이터 종류 · unique tag · cleanup 시도 방법 · 실패 사유.

---

### 9.6 체크리스트 매핑

`docs/uat-checklist.md` §1~§8 원문 항목을 먼저 읽고, 각 항목을 매핑:
원문 항목 · 자동화 가능 여부 · 연결 spec 파일 · PASS/FAIL/SKIP · 근거.
항목을 임의로 합치거나 생략하지 않는다. 미자동화 항목은 SKIP + 사유.

---

### 9.7 아티팩트 수집 (실제 config 기준 — 기대치 현실화)

`playwright.live.config.ts` 실측 설정: `reporter:[["list"]]`,
`trace:"on-first-retry"`, `screenshot:"only-on-failure"`.
→ 따라서:
* **실패 항목**: trace·스크린샷이 자동 생성됨 → 경로 보고
* **⚠️ 시각·해석 SKIP 항목(§9.8)**: 자동 캡처 안 됨 → spec 내 `page.screenshot()`로 수동 캡처
* **HTML report 없음**(list reporter): 콘솔 실행 로그를 `run.log` 파일로 저장해 대체.
  HTML report 경로를 지어내지 않는다. (config 변경은 금지 범위라 reporter 추가 안 함)

저장 위치: `docs/verification/uat_{yyyyMMdd_HHmm}/`  (git commit 안 함)

---

### 9.8 시각 판정 경계

Playwright가 에러 없이 통과해도 자동 PASS로 단정하지 않는 항목:
번역 자연스러움 · 숫자/날짜/단위 로케일 표현 · KPI badge 색·해석 ·
모바일 UI 미관 · 레이아웃 여백 · 카피 설득력.
→ 스크린샷(수동 캡처) 남기고 SKIP. 사유: `시각·해석 판정 필요`.

---

### 9.9 보고서 무결성

최종 보고서 필수 포함:
실행 날짜시각 · git branch · git status 요약 · API/웹 health 결과 ·
실행 명령어 · PASS/FAIL/SKIP 전체 개수 · 항목별 판정 · FAIL 재현 절차 ·
SKIP 사유 · 생성·수정 파일 목록 · 스크린샷/trace/run.log 경로 · cleanup 결과.

`전체 통과`·`문제 없음`·`대체로 정상` 같은 요약만으로 보고하지 않는다.
FAIL이 하나라도 있으면 보고서 맨 위에 `⚠️ FAIL 있음`을 먼저 출력한다.
