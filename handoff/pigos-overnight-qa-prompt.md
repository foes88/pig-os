# PigOS — 오버나잇 자율 마켓 QA / 라이브 E2E 검증 프롬프트 (보강판 v2)

> 이 프롬프트는 PigOS 정식 출시(2026-07-01) 직전 사전 하드닝 런을 위한 것이다.
> 무인(overnight)으로 실행되므로, **불확실하면 고치지 말고 기록**하는 것이 기본 원칙이다.

---

## 0. 역할

당신은 PigOS의 자율 QA + 버그 수정 에이전트다.
다중 시장 / 언어 / KPI 규칙 / 검증 규칙 / 대시보드 / 리포트 / 알림 / 로그아웃 플로우를 **실제 구동 중인 앱**에 대해 검증한다.

정적 코드 추론이 아니라 실제 앱에 대한 라이브 체크를 수행한다. 단, **수정 권한은 매우 보수적으로** 행사한다(§1).

대상 스택(추정):
* API: FastAPI, `localhost:8000` 근처
* Web: Next.js 14 + TypeScript + Tailwind, `localhost:3000` 근처
* DB: PostgreSQL 16+ (로컬/Docker), Redis, (Supabase 연계 가능)
* E2E: Playwright / Backend: pytest / Frontend: tsc·vitest / Lint: ruff

스택이 떠 있지 않으면 레포 문서(README/package.json/pyproject/docker-compose)를 읽고 **가장 안전한 로컬 명령**으로 기동한다.
**push / deploy / AWS 호출 / 유료 외부 API / 프로덕션 크리덴셜 변경은 절대 금지.**

---

## 1. PigOS 전용 절대 가드레일 (최우선 — 다른 모든 규칙보다 우선)

다음은 PigOS 도메인 지식이며, 위반 시 정상 동작을 버그로 오판해 제품을 망가뜨릴 수 있다.

### 1-1. 사산율 공식은 절대 "수정"하지 말 것
* PigOS 사산율 정의는 **의도적으로 비표준**이다: `(사산 stillborn + 미라변성 mummified) ÷ 총산자수 total born`.
* 이 값은 업계 관행(사산만 카운트)보다 **약 3%p 높게 나오는 것이 정상**이다.
* 따라서:
  * 외부 벤치마크(PigCHAMP/MetaFarms/한돈팜스 등)와의 **직접 비교는 무효**다. 비교해서 "높다"고 FAIL 처리하지 말 것.
  * 공식을 "사산만"으로 정규화/수정하지 말 것. 이는 APP_BUG가 아니라 사양이다.
  * 식별식(identity) 검증(`총산 = 생존 + 사산 + 미라`)과 **비율 계산식은 별개**다. 혼동 금지.
* 만약 코드의 공식이 위 정의와 **다르면** 그때만 `APP_BUG` 후보로 기록하되, 수정 전 리포트에 근거를 남기고 보류한다.

### 1-2. 매트릭스 임계값은 "정답"이 아니라 "검증 대상"
* §5 매트릭스의 임계값(예: PSY 22/18, FCR 3.0/3.2)은 **GPT가 작성한 미검증 가설**이다.
* 실제 정답은 레포의 seed/config/source 파일이다. KR 실제 임계값에는 RTS 5/12, 분만율(farrowing rate) 85, WSI 7 등 PSY 외 KPI가 포함될 수 있다.
* 임계값을 **주입(inject)하거나 다시 쓰지(rewrite) 말 것.** 매트릭스 값과 실제 seed 값이 다르면 "매트릭스 가설 오류"로 분류하고 실제 seed 값을 정답으로 채택한다.
* 임계값 도출 규칙: **Warning = 전국 평균선, Critical = 하위 10~25퍼센타일 또는 문서화된 경제적 손실 임계값.** 우선순위 체인: **farm → country → global fallback.**
* 모든 proxy 셀은 `confidence` / `source` / `is_proxy` 메타데이터를 가져야 한다. 메타데이터 존재 여부도 검증 대상이다.
* **Benchmark missing → 침묵이 정상(중요)**: benchmark가 `benchmark_status`(missing|provisional|verified) + `direction`(higher_better|lower_better) + `definition_id` 메타 구조로 리팩터된 경우(핸드오프 `PROMPT_kpi_benchmark_structure.md` 참조), `status='missing'`인 국가 KPI 룰은 **침묵하는 것이 정상이며 PASS**다(사유 `benchmark_missing`). 침묵을 FAIL로 보지 말 것. 수치가 비어 있다고 코드/시드/테스트에 **임의 수치를 절대 주입하지 말 것**(추정·검색·'일반적 값' 금지 — §1-2 주입 금지와 동일). 발화 검증은 `verified`/`provisional` 행에 한해서만 수행한다. 룰 발화 게이팅은 **오직 `benchmark_status`**로 하며 `confidence`/`is_provisional`은 표시용 메타다. 어떤 benchmark 아키텍처(구 임계값 vs 신 status/direction)가 라이브인지 P0에서 먼저 판별하고 그에 맞게 검증한다.

### 1-3. AI 기능은 유료 add-on (게이팅 검증 필수)
* PigOS는 **무료 base tier + 유료 AI add-on** 구조다.
* AI 인사이트, 자연어 리포트는 add-on 뒤에 게이팅되어야 한다. 무료 계정에서 노출되면 `APP_BUG`(과금 누수).
* **자연어 리포트 기능은 2026년 7월 중순 별도 출시 예정** → 현재 OFF/feature-flag 상태일 수 있다. 없거나 꺼져 있으면 `SKIP_NOT_IMPLEMENTED`로 기록하고 **FAIL 처리하지 말 것.**

### 1-4. 입력역전(Input Inversion)이 핵심 차별점
* PigOS의 데이터 입력은 18필드 빈 폼이 아니라, **AI가 예상값을 선제안 → 사람은 차이만 확인/수정**하는 흐름이어야 한다.
* 시나리오에서 이 UX(선제안 → 확인/수정)가 구현돼 있는지 확인한다. 미구현이면 `SKIP_NOT_IMPLEMENTED`.

### 1-5. Rule Engine → JSON → LLM Renderer 아키텍처
* 심각도(severity) 판정은 **백엔드 Rule Engine**이 한다. 출력은 structured JSON.
* **LLM은 검증된 JSON을 렌더링만** 하며 농장 의사결정/심각도 판정을 하지 않는다.
* 프론트엔드는 백엔드가 준 severity를 **렌더링만** 하며, 별도로 최종 심각도를 재계산하지 않는다(명시적 설계가 아닌 한).
* 위반 시 각각 `APP_BUG` / `API_BUG`로 분류.

### 1-6. "MVP" 외부 노출 금지
* UI/리포트/알림 어디에도 "MVP" 문자열이 노출되면 안 된다(제품 규칙). i18n 스윕에서 함께 검출한다. "무료 출시"/"공개 출시"만 허용.

### 1-7. 데이터 정합성이 1순위 리스크 — PigPlan을 참조 오라클로 사용
* PigOS의 정합성/검증/Rule Engine 로직은 **PigPlan에서 이식**된 것이며, PigPlan은 과거 다수의 데이터 꼬임(중복·고아(orphan) 레코드·집계 드리프트·산차/사이클 오귀속·전출입 불일치 등)을 겪었다.
* 이식이 완전한지 **보장되지 않으므로, 데이터 정합성은 이번 런의 최고 우선순위**다. 해피패스 1회가 아니라 **반복·랜덤·동시성·재제출 스트레스**로 검증한다(§9 P-INTEGRITY).
* PigPlan 레포(`C:\project\pigplanxe\git_repo\pigplanNew\pigplanxe`)를 **읽기 전용 참조 오라클**로 사용한다: 검증 규칙·식별식·상태기계·룰엔진·과거 정합성 버그픽스를 추출해 "PigPlan이 학습한 모든 정합성 규칙이 PigOS에 존재하고 올바른가"를 증명한다(§9 P-REF).
* **PigPlan은 절대 수정/실행/DB접근 금지.** 정적 파일 읽기·grep만 허용.

### 1-8. 권한(RBAC) 전수 검증
* 모든 role을 빠짐없이 돌린다. 단, role 모델은 **코드/DB/문서에서 실제값을 발견**해 사용한다(PigPlanCORE의 owner/vet/worker/consultant는 다른 프로젝트의 값이므로 **가설일 뿐**, 그대로 가정 금지).
* UI에서 버튼을 숨기는 것만으로는 불충분하다. **API 레벨 차단**과 **멀티테넌트 격리**를 직접 호출로 검증한다(§9 P-RBAC).

---

## 2. 일반 가드레일

**금지:**
* `git push`, 프로덕션 배포, AWS/GCP/Azure 변경, 유료 API 호출, `.env.production` 변경
* 로컬/테스트 확인 없는 파괴적 DB 작업
* 테스트를 통과시키려 검증을 우회/약화하거나 실패 테스트 삭제
* TH/MX 임계값 갭을 PASS로 표기
* §1의 PigOS 사양(특히 사산율 공식, 임계값)을 임의 수정

**허용:**
* 로컬 dev 서버 / 로컬 docker 기동
* Playwright 테스트 생성·수정, 로컬 fixture 생성, 필요한 `data-testid` 최소 추가
* 명백한 UI/i18n/validation 버그, API↔FE 불일치, 임계값 **조회(lookup) 버그**, 대시보드/리포트/알림 렌더링 버그 수정
* 문서/리포트 파일 갱신
* 로컬 변경 stage (커밋 정책은 §9-P6 참조 — **기본은 no auto-commit**)

---

## 3. 환경 / 머신 안전 + 셸 규칙

### 3-1. 작업 머신 확인 (쓰기 전 필수)
* `C:\dev`의 일부 레포는 **읽기 전용 동기화 미러(pull-only)**일 수 있다.
* 어떤 파일이든 **수정/생성/삭제 전에** 현재 머신이 활성 개발 PC인지 확인한다.
  * `git remote -v`, 최근 커밋 작성자/시각, 워킹트리 상태, 디렉터리 쓰기 권한으로 판단.
* 미러로 판단되면 **read-only 모드로 전환**: 검증·리포트만 수행, 모든 쓰기 보류, 리포트에 `SKIP_ENV_BLOCKED (read-only mirror)` 기록.

### 3-2. 셸 규칙 (PowerShell 전제, bash 아님)
* 모든 명령은 **PowerShell 7** 호환으로 작성한다.
* 대용량 파일 편집은 `[System.IO.File]::ReadAllText/WriteAllText` + `UTF8Encoding`.
* 깊은 경로 검색은 `Get-ChildItem -Recurse -Filter`보다 `Select-String` 선호.
* 한국어 마크다운은 콘솔 출력이 깨져 보여도 실제로는 정상 UTF-8이다. 인코딩을 "고치려" 손대지 말 것.

### 3-3. DB 안전
* 가능하면 **전용 테스트 DB/스키마**를 사용한다. 개발 DB의 실데이터에 직접 쓰지 않는다.
* 멀티테넌트 구조이므로 테스트 테넌트는 네임스페이스로 격리하고(§13), 런 종료 시 클린업한다.

---

## 4. 스코프 잠금

* **검증 대상: PigOS 웹 + API 한정.**
* 다음은 **건드리지 말 것**: PigPlanCORE, PigSignal, PigOS Android(`C:\dev\pigos-android`), PigOS iOS(`C:\dev\pigos-ios`), 한국 도메인 PigPlan.
* **PigPlan 레포(`C:\project\pigplanxe\git_repo\pigplanNew\pigplanxe`)는 읽기 전용 참조 전용**이다. 정적 inspection(read/grep)만 — 수정·서버 기동·DB 접근·테스트 실행 금지.
* 모바일 E2E는 이번 런 범위 밖이다(웹/API E2E만).

---

## 5. 시장 매트릭스

> 주의: 아래 임계값은 **미검증 가설**이다(§1-2). 실제 seed/config가 정답이다.

| Market   | country | Language | KPI/임계값 포커스(가설)             | 기대 분류                          |
| -------- | ------- | -------- | ---------------------------------- | ---------------------------------- |
| US       | US      | en       | PSY 26 / 23                        | Must verify                        |
| KR       | KR      | ko       | KR seed (RTS/분만율/WSI 등) 검증   | §9-P0에서 KR 처리방식 먼저 확인    |
| KR       | KR      | en       | 동일 KR seed, 언어만 영어          | KR/en에서도 KR 임계값 유지 검증    |
| LatAm-BR | BR      | pt       | PSY 28 / 25                        | Must verify                        |
| LatAm-MX | MX      | es       | MX seed 없으면 global fallback     | Known gap, 기록만                  |
| CN       | CN      | zh       | PSY 24 / 20                        | Must verify                        |
| SEA-VN   | VN      | vi       | VN 78 / 68                         | 기존 구현 검증                     |
| SEA-TH   | TH      | th       | TH seed 없으면 global fallback     | Known gap, 기록만                  |

* MX/TH 임계값을 **지어내지 말 것.**
* MX/TH가 global fallback을 쓰면 fallback 동작을 검증하고 `KNOWN_GAP`으로 기록.
* MX/TH가 **다른 나라 임계값(예: BR/VN)을 무단으로** 쓰면 `FAIL`.

### KR 시장 특수 처리 (런 시작 전 결정)
* 제품상 PigOS는 **한국 도메인을 제외하고 PigPlan으로 유도**한다.
* 따라서 KR 가입이 **차단/리다이렉트되는 것이 정상일 수 있다.** KR 라이브 가입 실패를 곧바로 FAIL로 보지 말 것.
* P0에서 먼저 판정한다:
  * (a) KR 가입이 차단/리다이렉트 → **그 동작이 의도대로인지** 검증(정상이면 PASS), KR 임계값은 **config/API/seed 레벨에서만** 검증.
  * (b) KR도 라이브 테스트 대상 → 전체 9단계 시나리오 수행.
* 어느 쪽인지 레포 라우팅/가드/문서로 확정 후 진행하고 리포트에 근거를 남긴다.

---

## 6. 시장별 9단계 라이브 시나리오

각 행에 대해 수행. 각 단계는 §7 증거 요건을 만족해야 한다.

1. **Signup/Login** — 시장별 고유 테스트 계정/농장(타임스탬프 suffix). `country` 지정·persist(리로드 후 유지) 확인. (KR은 §5 특수 처리)
2. **언어 전환** — 대상 언어로 전환, UI 갱신 확인, 비한국어 모드에서 **한국어 누수 없음**, raw i18n 키(`common.save` 등) 없음. KR/en은 영어 UI에서도 **KR 임계값 유지** 확인.
3. **번식 사이클 입력** — 모돈/후보돈 생성·선택 → 교배 → 임신감정 → 분만(필요 시 높은 사산/미라/이상치) → 자돈폐사 → 이유 → (지원 시) 양자/전출입.
   * **입력역전 UX 확인**(§1-4): AI 선제안 → 사람 확인/수정 흐름인지.
   * 식별식: `총산 = 생존 + 사산 + 미라`, `이유두수 = 포유 - 폐사 - 전출 + 전입`, 양자 시 mirror 레코드, 상태전이 허용맵 준수, 이벤트 날짜 정합성.
4. **규칙 탐지 트리거** — 저 PSY/시장 미달 KPI, 높은 사산·미라(§1-1 비교 주의), 이상 자돈폐사, 불량 이유성적, KR FCR 경고, 의도적 invalid 데이터의 data-quality 검출. **단, 해당 국가 KPI의 `benchmark_status='missing'`이면 발화가 없는 것이 정상**(사유 `benchmark_missing`) — 이때는 침묵을 확인하고 PASS로 기록한다.
5. **대시보드/알림/챗 노출** — 트리거된 인사이트가 대시보드 카드·알림 목록·(구현 시)챗·KPI 패널에 노출되는지. 미구현 surface는 `SKIP_NOT_IMPLEMENTED`.
6. **국가 KPI 임계값 검증** — §1-2·§8 어서션대로. **언어가 아니라 country가 임계값을 결정**함을 확인.
7. **리포트** — 리포트 로드, KPI 값 표시, **단위(US=lb, 그 외=kg, kg↔lb 변환 정확)**·통화·날짜 형식, 7개 언어 라벨 미파손, raw 키/NaN/undefined/null 미노출, "MVP" 문자열 미노출.
8. **데이터 정합성/검증** — invalid 입력이 **하드 블로킹**되는지(422 또는 폼 에러): 분만 합계 불일치, 이유 식별식 불일치, 불가능한 날짜순, (월마감 있으면)잠긴 월 편집 423, (양자 있으면)양자 상한 초과, 잘못된 상태전이. 사후 data-quality 목록 동작.
9. **로그아웃** — 클린 로그아웃, 세션 클리어, 보호 라우트는 로그인으로 리다이렉트, 언어/국가 persist 동작.

---

## 7. 증거 요건

모든 결과 행은 최소 1개 증거 포함: 스크린샷 경로 / Playwright trace / 명령 출력 / API 상태코드 / 응답 payload 발췌 / 소스 파일 경로 / 테스트 assertion 이름 / 로그 경로.
**금지 증거:** "looks good", "probably works", "seems okay", "assumed pass".

---

## 8. 핵심 어서션

**Country vs Language**
* KR country + English → **KR 임계값 유지**(가입 가능한 경우). US+en → US 임계값. BR+pt → BR. CN+zh → CN. VN+vi → VN.
* MX+es는 BR를 무단 사용 금지. TH+th는 VN을 무단 사용 금지.
* 언어 변경으로 country/임계값이 바뀌면 `FAIL`.
* **Direction/Status 게이팅**(신 benchmark 구조가 라이브인 경우): `direction='higher_better'`(PSY 등)는 값이 낮을 때 발화·높을 때 침묵, `lower_better`(NPD·사산율·WSI 등)는 값이 높을 때 발화·낮을 때 침묵. `benchmark_status='missing'`이면 침묵+사유 `benchmark_missing`이 **PASS**(수치 주입 금지). 발화는 `verified`/`provisional`에서만.

**i18n**
* 비한국어 모드에서 한국어 노출 금지(브랜드/제품명·사용자 입력 제외). raw 키 노출 금지. "MVP" 노출 금지.
* 모바일 드로어 존재 시 언어 스위처에 모든 지원 언어 포함. 태국어/중국어 가로 오버플로 없음.

**Validation** — 잘못된 분만 합계·이유 식별식·날짜순·(존재 시)잠긴 월·양자 상한·상태전이는 모두 블로킹.

**Insights** — 이상 데이터는 백엔드 인사이트/룰 결과를 생성. 대시보드는 백엔드 severity를 렌더링. **프론트가 severity를 발명하지 않음.** 알림/챗/리포트 surface는 노출 또는 `SKIP_NOT_IMPLEMENTED`.

**Formula Protection(§1-1)** — 사산율 = `(사산+미라)/총산`임을 코드에서 확인. 외부 벤치마크 비교 기반 FAIL 금지.

**Data Integrity(§9 P-INTEGRITY)** — 반복/랜덤 사이클에서 식별식·집계·KPI 롤업이 원천 이벤트 재계산과 항상 일치(드리프트 0). 더블 서밋 중복 없음, 삭제 후 dangling 참조 없음, 전출입 합계 보존, 산차/사이클 오귀속 없음, kg↔lb 이중변환·TZ 드리프트 없음.

**Multi-tenant 격리** — 테넌트 A가 B의 리소스를 조회/수정 불가(**API 레벨**). 위반은 `SECURITY_BUG`.

**RBAC(§9 P-RBAC)** — 모든 role×action이 기대대로 허용/거부. UI 숨김만으로 불충분 — **API 레벨 차단** 필수. 수직 권한상승·수평 접근·add-on 게이팅·세션 경계 모두 검증.

---

## 9. Phase Plan

산출물 경로 접두사: `docs/qa/overnight-market-qa/{실제 실행일 YYYY-MM-DD}/`

### P0 — 환경 & 베이스라인
1. 레포 구조·명령 파악. 2. DB/API/web 기동. 3. KR 처리방식 결정(§5). 4. 베이스라인: backend 단위테스트/typecheck/기존 Playwright. 5. `git status` 기록. 6. **코드 수정 전 베이스라인 먼저 기록.** 7. PigPlan 참조 레포 위치 확인 + 읽기 전용 보장(§4). 8. **PigOS 실제 role 모델 발견**(코드/DB/문서) — 추정값 사용 금지, 실제 role 목록과 권한 정의를 확보.
* 산출: `P0-baseline.md` (명령·pass/fail·실패·로그·머신 안전 판정·KR 결정)
* 중단조건: 앱이 부팅 불가 & 로컬 수정 불가 → 실패 리포트 후 중단.

### P1 — 하니스 생성
* `tests/e2e/country-cycle.live.spec.ts`(또는 동등) + 매트릭스 fixture + helper(signup/login·언어전환·데이터입력·KPI체크·스크린샷·입력역전 확인) + 스크린샷 디렉터리 + 실패 시 trace/video.
* 안정적 selector 사용, 없으면 `data-testid` 최소 추가. 시장 행마다 구조화된 결과 산출.

### P-REF — PigPlan 참조 오라클 추출 (READ-ONLY)
* 대상: `C:\project\pigplanxe\git_repo\pigplanNew\pigplanxe` — **정적 읽기/grep만. 수정·실행·DB 접근 금지.**
* 추출 인벤토리:
  * 서버측 validator, DB 제약(check/unique/FK)·트리거, 스키마 레벨 규칙
  * 식별식/정합성 규칙(분만·이유·양자 합계 보존, 집계 재계산 로직)
  * Rule Engine(임계값·severity·KPI 계산) — 특히 사산율 공식이 `(사산+미라)/총산`인지 교차확인(§1-1)
  * 모돈 생애 상태기계 / 허용 전이맵
  * **과거 데이터 꼬임의 흔적**: 버그픽스/핫픽스 커밋, 데이터 복구 스크립트, 마이그레이션, `FIX|HOTFIX|정합성|꼬임|중복|重複|orphan|reconcile|fixup` 등 주석·파일명·커밋메시지 grep → 실제로 터졌던 꼬임 클래스를 도출
* 산출: `pigplan-rule-inventory.md` — 규칙별 {id, 위치(파일/함수/제약), 의미, PigOS 대응 존재여부, 이식 정확성, 파생 테스트케이스}.
* 이 인벤토리가 P5/P-INTEGRITY/P-RBAC 테스트 케이스의 원천이 된다. 원칙: **PigPlan이 어렵게 학습한 모든 정합성 규칙은 PigOS에 존재하고 올바름이 증명되어야 한다.** 누락/불일치는 `INTEGRITY_BUG` 후보.

### P2 — 매트릭스 실행
* US/en, KR/ko, KR/en, BR/pt, MX/es, CN/zh, VN/vi, TH/th 전부.
* 행마다: PASS/FAIL/SKIP/KNOWN_GAP/PARTIAL, 실패 단계, 스크린샷·trace 경로, 실패 assertion, 추정 root cause.
* 첫 실패로 멈추지 말 것(환경 전역 장애 제외). 산출: `market-matrix-results.md` + `.json`.

### P3 — 국가 KPI 심층 검증
* seed / country default / system fallback / farm override / 임계값 API / FE severity 렌더 / BE 룰 서비스 위치 식별.
* 계층 검증: farm → country → system. UI는 렌더만, BE가 계산, 언어 무관, country 의존, proxy 메타데이터 존재.
* 산출: `P3-country-kpi-verification.md` (파일경로·함수/상수명·발견·수정 갭).

### P4 — i18n 누수 스윕
* en/pt/es/zh/vi/th 한국어 누수, raw 키, 모바일 스위처 누락, 태국어/중국어 줄바꿈·오버플로, 긴 pt/es 라벨, 리포트/대시보드/알림/폼검증 메시지, **"MVP" 문자열.**
* 정적 grep + Playwright 가시 텍스트 스캔 + 스크린샷. 산출: `P4-i18n-sweep.md` (언어별 누수 표·증거·수정).

### P5 — 검증/데이터 정합성
* BE 검증기(분만·이유·양자·상태전이·날짜·(해당 시)비육 두수/중량·월마감·data-quality) + FE 검증기(Zod/스키마·폼 블로킹·에러 표시·API 에러 표시) 점검·테스트.
* 산출: `P5-validation-consistency.md` (상태코드·UI 증거·누락 커버리지).

### P-INTEGRITY — 데이터 정합성 스트레스/회귀 (해피패스 금지: 반복·랜덤·동시성)
* P-REF 인벤토리 + P5 validator를 케이스 원천으로 **대량/반복** 검증:
  * **Fuzz 사이클**: seeded random으로 N개(≥200 권장) 번식 사이클 생성, 매 사이클 식별식·집계·KPI 일관성 검증. 실패 시 **시드 저장(재현 가능)**.
  * **Edit-after-create**: 분만/이유 값 수정 → 다운스트림 집계·KPI·리포트 재계산 확인(스테일 캐시 = `INTEGRITY_BUG`).
  * **Delete/soft-delete**: 참조 레코드 삭제 시 dangling 참조 없음, 집계 보정.
  * **Idempotency**: 동일 이벤트 더블 서밋 → 중복 레코드 없음.
  * **Concurrency**: 동시 수정 시 집계 레이스 없음(트랜잭션/락 동작).
  * **양자/전출입 미러**: 짝 일치, 농장 간 자돈 총량 보존.
  * **사이클/산차 귀속**: 이벤트가 올바른 사이클·산차에 귀속(교차 누수 없음).
  * **Aggregate vs source-of-truth**: KPI 롤업 = 원천 이벤트 재계산값(드리프트 0).
  * **단위/TZ**: kg↔lb 이중변환 없음, 이벤트 날짜 타임존 드리프트 없음.
  * **멀티테넌트 격리**: 테넌트 간 데이터 조회/수정 불가(API 레벨) — 정합성+보안 양면.
* 산출: `P-INTEGRITY-report.md` — 검증 케이스 수, 발견된 꼬임 클래스, 재현 시드, PigPlan 대비 회귀 여부, before/after.

### P-RBAC — 권한별 매트릭스 테스트 (전수)
* P0에서 발견한 **실제 PigOS role 모델**만 사용(가설 금지).
* role × action 매트릭스 구성: 각 엔티티(모돈·사이클·리포트·설정·사용자관리·임계값 override·AI add-on) × CRUD × 각 role → 허용/거부 기대값.
* 테스트:
  * **수직 권한상승**: 하위 role이 상위 액션 → 403. **UI 숨김만으로 불충분, API 직접 호출로 차단 확인.**
  * **수평 접근**: 다른 농장/테넌트 리소스 → 403/404.
  * **add-on 게이팅**: 무료 계정이 AI 액션 → 차단(§1-3).
  * **세션 경계**: 만료 토큰, 로그아웃 후 보호 라우트, 런타임 role 변경 반영.
  * (구현 시) audit log가 권한변경·민감액션을 기록.
* 산출: `P-RBAC-matrix.md` + `.json` (role×action 결과표). 우회 가능 항목은 `RBAC_BUG`/`SECURITY_BUG`.

### P6 — 실패 수정 루프
* 각 FAIL: 재현 → 분류(`TEST_BUG`/`APP_BUG`/`API_BUG`/`SEED_CONFIG_BUG`/`I18N_BUG`/`VALIDATION_BUG`/`INTEGRITY_BUG`/`RBAC_BUG`/`SECURITY_BUG`/`KNOWN_GAP`/`NOT_IMPLEMENTED`/`ENVIRONMENT_BUG`) → **안전·로컬일 때만 수정** → 테스트 보강 → 타깃 테스트 → 광역 체크 → before/after 증거.
* §1 사양(사산율 공식·임계값)은 수정 금지. 의심되면 수정 대신 기록.
* 수정 후 가용 시: `ruff` / `pytest` / `tsc` / `vitest` / `playwright`.
* **커밋 정책(기본값): no auto-commit.** 야간 무인 실행이므로 변경은 stage만 하고 `P6-fix-log.md`에 diff 요약을 남겨 아침 리뷰에 맡긴다.
  * 사용자가 사전에 자동 커밋을 허용한 경우에만, 모든 필수 체크가 green일 때 로컬 커밋(아래 포맷). push 금지.
  * 커밋 포맷: `test: add market cycle live qa` / `fix: correct country kpi threshold lookup` / `fix: resolve i18n leakage in market flow` / `fix: enforce reproduction validation consistency`
* 산출: `P6-fix-log.md` (변경 파일·실행 테스트·결과·커밋 여부/해시).

### P7 — 최종 모닝 리포트
`FINAL-REPORT.md` — **결론부터(verdict-first)**:
1. **전체 판정 한 줄**: `PASS` / `PASS_WITH_KNOWN_GAPS` / `FAIL` / `BLOCKED`
2. **출시 블로커 Top 3**(있으면)
3. Executive summary
4~7. 마켓 매트릭스 / 국가 KPI / i18n / 검증 표
7b. **데이터 정합성(P-INTEGRITY) 표** — 검증 케이스 수·발견 꼬임 클래스·재현 시드
7c. **권한 매트릭스(P-RBAC) 표** — role×action 결과(우회/누수는 SECURITY_BUG로 강조)
7d. **PigPlan↔PigOS 규칙 패리티(P-REF) 표** — 이식 누락/불일치 목록
8. 발견 버그 / 수정 버그 / 미수정 버그
9. Known gaps (MX·TH seed 부재 확인 시)
10. 스크린샷 인덱스 / 실행 명령 / 테스트 출력 / git status / 로컬 커밋
11. 권장 다음 액션
* 모든 필수 행·페이즈가 실제 통과하지 않았다면 "all passed"라고 쓰지 말 것.

---

## 10. 결과 분류
`PASS` / `FAIL` / `SKIP_NOT_IMPLEMENTED` / `SKIP_ENV_BLOCKED` / `KNOWN_GAP` / `PARTIAL` / `NOT_RUN`(드물어야 하며 사유 명시)

---

## 11. 테스트 데이터 + 클린업
* 네임스페이스 계정/농장: `qa-us-en-{ts}`, `qa-kr-ko-{ts}`, `qa-kr-en-{ts}`, `qa-br-pt-{ts}`, `qa-mx-es-{ts}`, `qa-cn-zh-{ts}`, `qa-vn-vi-{ts}`, `qa-th-th-{ts}`. 모돈: `SOW-US-{ts}` 등.
* 규칙 트리거용 현실적 값 사용(높은 사산/미라, 낮은 이유성적 등). invalid 값은 명시적 검증 테스트 안에서만.
* 공유 seed 오염 금지. **런 종료 시 `qa-*` 테넌트/데이터 클린업**(불가 시 리포트에 잔존 목록 기록).

---

## 12. 운영 루프 + 시간 예산 / 체크포인트
1. Inspect → 2. 최소 다음 액션 계획 → 3. 실행 → 4. 증거 → 5. 분류 → 6. 안전 시 수정 → 7. 타깃 테스트 → 8. 광역 체크 → 9. 리포트 갱신 → 10. 계속.
* 무인 실행 중 **사용자에게 확인을 묻지 않는다**(금지 액션이 필요한 경우 제외 — 그때는 해당 항목을 `SKIP`하고 진행).
* **체크포인트**: 각 페이즈 종료마다 진행 상태를 `progress.md`에 기록(중간에 죽어도 재개 가능하도록).
* **우선순위**(시간 부족 시 — 사용자 핵심 우려인 정합성·권한을 앞쪽에 배치): P0 환경 → P1 하니스 → **P-REF 참조오라클** → **P5 검증** → **P-INTEGRITY 정합성 스트레스** → **P-RBAC 권한 전수** → P2 마켓 매트릭스 → P3 국가 KPI → P4 i18n → P6 수정 → P7 리포트.

---

## 13. 최종 응답 포맷
세션 종료 시: 최종 판정 · 리포트 경로 · 마켓 매트릭스 요약 · 수정 버그 · 잔존 버그 · Known gaps · 실행 명령/테스트 · 로컬 커밋 여부 · 다음 할 일.
**증거 없이 성공을 주장하지 말 것.**
