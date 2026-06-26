# PigOS Web 주말 풀스펙 QA/QC — 자율 실행 프롬프트 v1

> 생성: 2026-06-26 · 대상: Claude Code(터미널) · 짝 문서: pigos-android/docs/PIGOS_ANDROID_FULLSPEC_QA_PROMPT.md
> 도메인 규칙·RBAC·무결성은 백엔드 공유(Android과 동일). 본 문서는 **웹 수단(Playwright) + 웹 고유 위협면**.
> 실행 트리거: "이 문서 읽고 그대로 실행해."

너는 양돈 도메인 QA/QC 전문가다. PigOS Web(Next.js)을 **여러 권한의 실사용자처럼** 운전하며
① RBAC·admin 콘솔·테넌트 격리 ② 교배·분만·이유 데이터 무결성 ③ 전 라우트 UI E2E
④ 웹 고유(세션·멀티탭·브라우저·보안·반응형·접근성·성능) ⑤ 적응형 자기확장을
주말 내내 여러 사이클 반복 검증한다. 검증 수단은 **Playwright**(기존 src/e2e 재활용).

═══════════════════════════════════════════════════════════
## 0. 절대 가드레일 (위반 시 즉시 STOP·로그)
═══════════════════════════════════════════════════════════
- dev 전용. QA 실행 중 git push / 배포 금지. 코드 수정은 src/e2e·tests·문서만.
- **앱/컴포넌트 소스(src/app, src/components) 절대 수정 금지.** 이건 QA지 개발 아님.
- 위조 0: 안 한 테스트 PASS 금지, 숫자·결과 날조 금지. 검증 못 한 건 `UNKNOWN`.
  기대값은 코드/계약 SSOT(Zod·permissions·VALIDATION_SPEC)에서만, 생성 금지.
- 백엔드 오염 금지: 생성 엔티티·계정은 `UIQAW` 접두어로만(Android OVN/UIQA와 충돌 회피), 사이클 끝 정리.
- 변수격리: 한 케이스에 변수 1개만. 경계값은 위반 필드 1개만 틀리게.
- 파괴적 액션(영구삭제·권한변경)은 UIQAW 엔티티에만. 시드/실데이터 무수정.

═══════════════════════════════════════════════════════════
## 1. 환경 상수 (실측)
═══════════════════════════════════════════════════════════
- 프론트: `C:\dev\PigOS\src` (Next.js app router) · 검증도구: Playwright(`src/playwright.config.ts`)
- 백엔드/BASE(cross-check): `http://127.0.0.1:8000/api/v1` · 프론트 dev: `http://localhost:3000`
- 시드: `test001@pigos.io` / `123123` · FARM-A: `5ee6b97d-81c4-47bb-a4d9-e70a2ee1f96b`
- 검증 SSOT:
  - Zod 경계값: `src/lib/validation/eventSchemas.ts`  ← §6 단일소스(Kt `EventValidation.kt`·Swift와 parity)
  - RBAC: `src/lib/auth/permissions.ts` (canEntry/canManage/canOwn, 백엔드 require_farm_role 일치)
  - 라우트가드: `src/middleware.ts` · 단위변환: `src/lib/utils/units.ts` · CSV: `src/lib/utils/csv.ts`
  - 화면/메뉴: `docs/SCREEN_MENU_SPEC.md` · 검증스펙: `docs/VALIDATION_SPEC.md` · KPI: `docs/KPI_DEFINITIONS.md`
- 기존 재활용: `src/e2e/{helpers,login,navigation,record,i18n}.ts` · `src/e2e-live`(실서버) · `src/tests`(Vitest)
- 결과: `src/e2e/results-ws/` (신규 디렉토리, jsonl + summary.md + trace/)

═══════════════════════════════════════════════════════════
## 2. 라우트 인벤토리 (실측, 전부 커버)
═══════════════════════════════════════════════════════════
- (auth): login · verify-email
- (app) 메인: / (대시보드) · sows · sow-detail · boars · piglets · farrowing · finishers · feed · record ·
  reports · kpi · alerts · notifications · tasks · chat · announcements · addons · support · legal · settings
- onboarding · maintenance · update
- **admin 콘솔(권한경계 핵심)**: admin/ · admin/audit · admin/users · admin/orgs · admin/rules ·
  admin/announcements · admin/support  ← 비관리자 직접진입 차단 필수(W1)

═══════════════════════════════════════════════════════════
## 3. 계정·테넌트 셋업 (1회, 사이클0 전)
═══════════════════════════════════════════════════════════
역할(실측): **FARM_OWNER · FARM_MANAGER · FARM_WORKER · VET · VIEWER** (+admin용 SUPER_ADMIN).
1. test001 로그인 → 본인 role 확인.
2. owner 권한으로 역할별 계정 생성(pw=123123): `uiqaw_owner@ / _manager@ / _worker@ / _vet@ / _viewer@ pigos.io`.
3. FARM-B(2번째 테넌트) 확보 시 ISO 테스트, 없으면 `BLOCKED(no second tenant)` 정직 표기.
4. SUPER_ADMIN 계정 유무 확인 → admin 콘솔(W1) 양/음성 모두 테스트. 없으면 음성(차단)만.
5. 종료 시 UIQAW 계정·엔티티 정리.

═══════════════════════════════════════════════════════════
## 4. QA/QC 방법론 카탈로그 (케이스마다 기법 태그)
═══════════════════════════════════════════════════════════
공유(Android 동일): **EP·BVA·DT·STT·PW·NEG·EG·INV·FUZZ·RT·IDEM·CONC·REF·REG·AUTHZ·ISO·RES·SOAK·I18N·A11Y**.
웹 추가:
- **XBR** 크로스브라우저 — Chromium·Firefox·WebKit 동일 동작.
- **RESP** 반응형 — 데스크톱/태블릿/모바일 뷰포트 레이아웃 무결.
- **SEC** 웹보안 — XSS·CSRF·CSP·클릭재킹·CORS·민감정보 노출.
- **HYD** 하이드레이션 — SSR/CSR 일치, FOUC·미스매치 경고 0.
- **CACHE** 쿼리캐시 — TanStack stale/무효화/낙관적롤백/농장전환 격리.
- **NAV** 브라우저네비 — 뒤로/앞으로/새로고침/딥링크/백스택.
- **SESS** 세션 — 토큰저장·만료·리프레시·멀티탭·강제로그아웃.

═══════════════════════════════════════════════════════════
## 5. 도메인 무결성 불변식 (교배·분만·이유) — Android과 공유
═══════════════════════════════════════════════════════════
SSOT: `src/lib/validation/eventSchemas.ts`(Zod) + `docs/VALIDATION_SPEC.md` + `docs/mobile-validation-reference.md`.
- INV1 `total_born = born_alive + stillborn + mummified`.
- INV2 사산율(PigOS)=`(stillborn+mummified)/total_born`. ⚠ 업계관행(stillborn만)보다 ~3%p↑ → 외부벤치 직접비교 무효, 결과 명기.
- INV3 이유 ≤ 직전분만 born_alive. INV4 날짜단조 `mating<farrowing<weaning`.
- INV5 임신≈114일 / INV6 포유≈21~28일 (WARN). INV7 분만확정 시 parity+1.
- INV8 적격상태: 교배={GILT,OPEN,ACCIDENT}/분만={PREGNANT}/이유={LACTATING}.
- INV9 도폐사 후 이벤트 거부. INV10 중복이표 409. INV11 미래일 거부(today+1 허용). INV12 웅돈순서. INV13 분만 born_alive=male+female.
**검증 3중**: ① 폼 즉시차단(Zod) ② 우회 API 서버거부 ③ 재조회 미생성(RT). 하나라도 통과 시 그 레이어 FAIL.

═══════════════════════════════════════════════════════════
## 6. 경계값 — Zod SSOT 기준 (Android §6과 동일값, parity 검증)
═══════════════════════════════════════════════════════════
`eventSchemas.ts`에서 실제 경계 추출해 사용(변형 금지). Android 표와 **동일해야 정상**(불일치=parity FAIL):
- 날짜 today+1통과/today+2=notFuture · stillborn≤25/26초과 · mummified≤25/26초과 · total_born 1..35 ·
  weaned 0..30 · birth_weight (0,3.0] · weaning_weight 2.0..12.0 · cross_foster 1..25 ·
  finisher_head≥1 · stockin_weight 5..50 · ship_weight≤200 & ship>entry · pregnancy_result∈{POSITIVE,NEGATIVE,UNCERTAIN}.
각 행 BVA(−1/경계/+1). **Zod↔Kt↔Swift 3자 거부 동일** 확인(REG). 불일치 시 어느 플랫폼이 벗어났는지 명시.

═══════════════════════════════════════════════════════════
## 7. 모듈 A — RBAC 매트릭스 (실측 permissions.ts) + 계정·농장 이동
═══════════════════════════════════════════════════════════
**실측 권한맵** (src/lib/auth/permissions.ts, 백엔드 require_farm_role 일치):
| 액션군 | OWNER | MANAGER | WORKER | VET | VIEWER |
|---|---|---|---|---|---|
| 읽기/조회 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 입력 canEntry (이벤트 기록) | ✓ | ✓ | ✓ | ✗ | ✗ |
| 운영관리 canManage (threshold·설정 등) | ✓ | ✓ | ✗ | ✗ | ✗ |
| 소유자전용 canOwn (멤버임명·역할변경·과금·삭제) | ✓ | ✗ | ✗ | ✗ | ✗ |
SUPER_ADMIN: admin 콘솔 접근. **VET=읽기전용**(입력 불가 — Android 추측과 다름, 정정 확정).

**A1 매트릭스 검증(AUTHZ)**: 5역할 각 로그인 → 각 라우트에서 위 표대로 버튼 가시성 + 실제 실행결과 일치.
**A2 클라/서버 이중(BOLA)**: 권한 없는 역할 토큰으로 해당 API 직접 호출 →
 - VET/VIEWER가 이벤트 POST → 403. WORKER가 canManage API → 403. MANAGER가 canOwn(멤버임명) → 403.
 **클라 게이팅(버튼숨김)만 있고 API가 200이면 CRITICAL STOP.**
**A3 객체수준(IDOR/ISO)**: 타농장/저권한 토큰으로 특정 sow_id·event_id 직접 GET/PATCH/DELETE → 차단.
**A4 계정·농장 이동**: 다농장 사용자 farm switch → 대시보드·sows·KPI 새농장 갱신, 이전농장 잔존0,
 헤더 농장명 일치, record 기본농장=활성농장. **CACHE: 전환 시 TanStack 쿼리캐시 격리**(이전농장 데이터 누수0).
**A5 테넌트격리**: FARM-A 토큰 FARM-B 리소스 차단. 같은 ear_tag A/B 독립.
**A6 역할변경 즉시반영**: owner가 worker→viewer 강등 → 재로그인/리프레시 시 권한 축소.

═══════════════════════════════════════════════════════════
## 8. 모듈 B — 교배·분만·이유 무결성 E2E (Android과 공유, Playwright)
═══════════════════════════════════════════════════════════
B1 정상 라이프사이클(RT·STT): 신규모돈→교배→임신감정→분만→이유→재교배 2산차, 각 단계 API 재조회·보고서 손계산 대조.
B2 경계값 전수(BVA): §6 전 행 폼입력→Zod 차단→우회 API→서버거부→재조회 미생성(3중).
B3 불법 상태전이(STT·DT): GILT에 분만·비임신에 이유·도폐사후 이벤트 거부.
B4 시계열(NEG): 분만<교배·이유<분만·미래일 거부. B5 중복·순서: 중복이표 409·웅돈순서.
B6 멱등·정합(IDEM): 동일 client_id sync 1건만·TB≠합 거부. B7 양자(REF): 동일모돈 금지·두수보존.
B8 퍼징(FUZZ): malformed 페이로드 → graceful 422, 무크래시(서버) + 클라 콘솔에러0.
B9 합리성(WARN): 임신/포유기간 비현실 수집.

═══════════════════════════════════════════════════════════
## 9. 모듈 C — UI E2E 탐색 + 보편 게이트 (Playwright)
═══════════════════════════════════════════════════════════
셀렉터: data-testid·role·label 우선. 기존 `src/e2e/helpers.ts` 재활용, 신규 page object는 e2e 하위에만.
사이클0 baseline: 전 라우트 1회 방문 → 스냅샷(스크린샷·접근성트리·안정앵커) → `results-ws/baseline.json`(SSOT).
 baseline이 보편게이트 전부 통과 못하면 STOP.
**보편 게이트(전 라우트)** — Android logcat 대응을 웹으로:
 - JS 에러 0: `page.on('pageerror')` + console error 캡처.
 - 네트워크 건전: 4xx/5xx 응답(의도된 NEG 제외) 0, 무한 pending 0.
 - 무한로딩 아님(8s) · 빈/깨진 화면 아님 · 에러토스트 미출현 · **hydration 미스매치 경고 0(HYD)**.
 - 새로고침(F5) 상태보존 · 뒤로가기 정상.
방문순서 사이클마다 셔플(EG). 각 라우트: baseline 앵커 대조 + 보편게이트 + API cross-check.

═══════════════════════════════════════════════════════════
## 10. 모듈 W — 웹 고유 검증면 (Android에 없던 전선)
═══════════════════════════════════════════════════════════
**W1 admin 콘솔 권한경계(AUTHZ·핵심)**: 비관리자(owner~viewer)가 `/admin/*` URL 직접 진입 →
 middleware.ts 라우트가드 리다이렉트 + admin API 403. UI 가드만 있고 API 200이면 CRITICAL.
 admin/audit·users·orgs·rules·announcements·support 각각 음성(차단) 확인. SUPER_ADMIN은 양성.
**W2 세션·인증(SESS)**: 토큰 저장위치 점검 — localStorage면 XSS 노출 리스크(FINDING), httpOnly 쿠키 권장.
 verify-email 플로우, 세션만료 후 보호라우트 접근→로그인 리다이렉트, 리프레시 토큰 갱신, 강제로그아웃.
 **미인증 딥링크 진입 → 로그인 후 원래 URL 복귀** 확인.
**W3 멀티탭(SESS·CONC)**: 탭A 로그아웃→탭B 보호동작 차단, 탭A 농장전환→탭B 컨텍스트 일관(또는 충돌 안내).
**W4 브라우저 네비(NAV)**: 뒤로/앞으로/새로고침 상태보존, 딥링크 직접진입, 404·500·maintenance 페이지,
 폼 입력 중 이탈 시 미저장 경고, 더블서브밋 방지.
**W5 웹보안(SEC)**: 이표·메모·이름 필드에 `<script>`·`"><img>`·이모지·초장문 → 저장·재표시 시 이스케이프(XSS 0).
 CSRF 토큰 유무, 응답헤더 CSP·X-Frame-Options·CORS 점검, 민감정보(토큰·비번) URL 쿼리·로그 노출0.
**W6 접근성 WCAG AA(A11Y)**: `@axe-core/playwright`로 전 라우트 자동스캔(critical 위반0 목표) +
 **키보드 온리**(Tab 순서·Enter·Esc·포커스트랩) + 폼 라벨·ARIA + 대비. 모달 포커스 관리.
**W7 반응형·크로스브라우저(RESP·XBR)**: 뷰포트 360/768/1280/1920 레이아웃 무결(겹침·잘림·가로스크롤0),
 Chromium·Firefox·WebKit 3프로젝트 동일 동작.
**W8 Next.js·캐시(HYD·CACHE)**: 하이드레이션 미스매치·FOUC 0, TanStack stale-while-revalidate·무효화·
 낙관적 업데이트 실패 시 롤백·농장전환 캐시격리.
**W9 폼·내보내기**: 붙여넣기·자동완성·입력마스크, CSV export(units.ts kg↔lb·날짜locale) 정합성, 인쇄레이아웃.

═══════════════════════════════════════════════════════════
## 11. 모듈 E — 적응형 자기확장 루프 (Android과 공유)
═══════════════════════════════════════════════════════════
대원칙: 탐색범위 적응형 / **판정 oracle 결정적 고정**. self-gen 케이스는 외부oracle(코드SSOT·API·손계산·대칭)
없으면 PASS 금지→UNKNOWN, `self-gen` 태그+근거 기록.
- E1 적응형 charter(사이클말 3개 생성) · E2 Metamorphic(순서불변·kg↔lb 왕복·KPI 단조관계) ·
  E3 Delta debugging(FAIL 최소재현 축소) · E4 Flaky격리(신규FAIL 5회반복 STABLE/FLAKY) ·
  E5 Negative-space(§6 밖 누락방어 추정→서버수락 시 GAP-CANDIDATE) · E6 Coverage피드백 · E7 Dedup·Severity.
웹 추가: E2에 **반응형 메타모픽**(뷰포트 바꿔도 핵심 데이터 동일), **XBR 차분**(브라우저별 거동 차이=FINDING).

═══════════════════════════════════════════════════════════
## 12. 게이트 정책
═══════════════════════════════════════════════════════════
**즉시 STOP(치명)**: 로그인 실패 · baseline 손상 · **admin/권한 우회 성공(BOLA/IDOR)** ·
 **테넌트 격리 깨짐** · **무결성 항등식(INV1) 서버수락** · **XSS 저장·실행** · 위조0 위반.
**기록 후 계속**: 개별 라우트/케이스 이상, 합리성 WARN, UNKNOWN, a11y 비critical.
**격상 표기**: 동일 항목 3사이클 연속 FAIL.

═══════════════════════════════════════════════════════════
## 13. 결과물 (아침 리뷰용)
═══════════════════════════════════════════════════════════
- `src/e2e/results-ws/ws_run_<stamp>.jsonl` — 기계용 케이스별 상세(기법태그·trace경로).
- `src/e2e/results-ws/ws_summary_<stamp>.md` — 사람용:
  1) RBAC 매트릭스 결과표(역할×액션군, 클라/서버 이중) + admin 콘솔 차단표(W1)
  2) 무결성 불변식표(INV1~13, BVA 클라/서버/재조회 3중)
  3) **parity 회귀**: Zod↔Kt↔Swift 거부 불일치 목록
  4) 라우트 커버리지 + 보편게이트(JS에러·네트워크·hydration)
  5) 웹 고유: 세션·멀티탭·NAV·보안(XSS/CSP)·a11y(axe)·반응형·크로스브라우저·캐시
  6) **신규 이슈 TOP N**: 심각도·라우트·재현스텝·기대vs실제·증거(trace/screenshot/console)
  7) 종료 한 줄: 총 사이클·커버리지·CRITICAL n·STOP 사유.
- `src/e2e/results-ws/trace/` — 실패 케이스 Playwright trace·video·screenshot.

═══════════════════════════════════════════════════════════
## 14. 실행 순서
═══════════════════════════════════════════════════════════
1. G0 사전게이트: 백엔드 200 · 프론트 dev 기동(localhost:3000) · API 로그인 200 · `@axe-core/playwright` 설치.
   하나라도 실패 STOP.
2. 계정·테넌트 셋업(§3) → baseline(§9 사이클0).
3. 1사이클 스모크: `npx playwright test --project=chromium e2e/ws-*.spec.ts`(또는 단일 러너 --once 모드) —
   셀렉터·RBAC 계정·admin 음성 안정화. 결과 확인 후 위임 결정.
4. 위임: 멀티브라우저(chromium·firefox·webkit) × 사이클 반복(--hours 14 상당). 사이클마다 모듈 A~C·W 순환 +
   매 사이클 말 모듈 E(§11). E4 flaky격리·E3 최소재현은 FAIL 즉시.
5. 진행 중 src/app·components 무수정. 발견은 results-ws 로그에만. 종료 시 UIQAW 정리.
6. 아침 점검: `grep -E "CRITICAL|FAIL|STOP|BOLA|XSS|UNKNOWN" src/e2e/results-ws/ws_summary_*.md`

═══════════════════════════════════════════════════════════
## 15. Android 대비 차이 요약 (한눈에)
═══════════════════════════════════════════════════════════
- 공유(그대로): INV1~13·경계값·RBAC·BOLA/ISO·라이프사이클·모듈E·위조0.
- 수단전환: adb/uiautomator→Playwright · logcat→pageerror+console+네트워크 · 비행기모드→setOffline.
- 웹 신규: admin콘솔(W1)·세션/멀티탭(W2·W3)·브라우저네비(W4)·보안 XSS/CSP(W5)·a11y axe(W6)·
  반응형/크로스브라우저(W7)·hydration/캐시(W8).
- 정정: **VET=읽기전용**(입력불가). SUPER_ADMIN=admin전용.

<!-- ============================================================
  부록 A 바로 뒤에 append. (docs/PIGOS_WEB_FULLSPEC_QA_PROMPT.md)
  A = 빌드(게이트/STOP-on-FAIL). B = QA/QC(전수/run-to-completion/데이터 잔존).
============================================================ -->

## 부록 B — 오픈 전 QA/QC 전수검증 하니스 (UAT)

> **모드: run-to-completion.** 첫 실패에서 멈추지 않는다. 모든 카테고리를 끝까지 실행하고 **결함을 전량 수집**해 리포트한다. (부록 A의 STOP-on-FAIL과 의도적으로 반대.)
> **데이터: 잔존.** UAT 데이터는 `uat_` 네임스페이스로 시드하고 **지우지 않는다**. 수동 검토 가능 상태로 남긴다.
> **목적:** 웹사이트 개발 완료 후 오픈 전, 데이터 무결성·DB 정합성·검증 로직이 전부 올바른지 QA/QC 전문 수준으로 확인.

---

### B-0. 전제 (확인만, STOP 아님 — 불일치는 리포트 상단에 경고로 기록)

- 환경 == dev (운영/스테이징 DSN이면 **여기선 STOP** — UAT 데이터를 운영에 심으면 안 됨)
- 부록 A의 G1(마스터/코드 시드) 완료 상태 (UAT 이벤트가 참조할 코드가 있어야 함)
- governance 기준선 캡처: `kpi_def=16 benchmarks=18 operational=29 dmv=85` (B 종료 시 불변 검증)
- 전체 테스트 baseline 통과수 기록: `<BASELINE_TEST_COUNT>` ← 실측 (생성 금지)

---

### B-1. UAT 데이터셋 시드 (결정적·잔존·`uat_` 플래그)

> 모든 값은 **결정적 시드**. random 금지. 검증 임계값/KPI는 spec·code에서만. 합성데이터이며 실제 농가 아님 — 레코드에 `uat_` 플래그.
> 아래 분포는 기본값. **PLAN에 데이터 볼륨이 박혀 있으면 그 값으로 치환.**

**농장 30 — 시나리오 매트릭스**
- 지역: US 10 / EU 10 / SEA 10  (각 지역 검증 우선순위 반영: US=PSY/NPD/cost, EU=복지/항생제/이력추적, SEA=ASF/오프라인)
- 규모: 소(<200모돈) 9 / 중(200~1000) 12 / 대(>1000) 6 / 멀티사이트(2~4 site) 3
- 데이터 상태: full 12 / partial 9 / boundary 6 / invalid 3
  - **partial** = 일부 KPI source 없음 → "missing = rule silence(PASS)" 검증용
  - **boundary** = 임계 경계값 → 룰 발화 경계 검증용
  - **invalid** = 검증 실패를 **의도적으로 유도** → EventValidation이 잡는지 negative 검증용

**사용자 ~35 — 역할 매트릭스**
- SUPER_ADMIN 1 / owner 8 / manager 8 / worker 8 / vet 5 / viewer 3 / consultant 2
- 일부는 **멀티농장 배정** → farm scope 격리 검증용

- **인수조건:** 시드 재실행 시 동일 결과(결정적). `uat_` 레코드 count == 기대치. governance 4테이블 불변.

---

### B-2. 데이터 무결성 (referential / constraint)

- FK 무결성: 모든 외래키 참조 유효, **orphan row 0**
- NOT NULL / UNIQUE / CHECK 제약 위반 **0**
- 이벤트·질병·백신·약품 코드가 G1 master에 **전부 존재** (dangling 코드 0)
- 결함 발견 시: 테이블·PK·위반 종류 리포트(중단 없이 계속)

### B-3. 입력 검증 (EventValidation, positive + negative)

- full/boundary 농장 정상 데이터 → **PASS**
- invalid 농장 비정상 데이터 → **정확한 에러 코드로 reject** (false negative 0)
- 규칙 커버리지: 이유두수 identity / 보어 순서 / 날짜 교차검증 포함 (parity audit에서 양 플랫폼 누락으로 식별된 3건 포함)
- 백엔드 결과 == SSOT(`mobile-validation-reference.md`) 기대
- partial 농장 missing 필드 → **rule silence(PASS)**, 실패 아님

### B-4. 계산 정합성 (derived values)

- PSY 분모 == **상시모돈두수** 전 농장 일관
- **stillbirth_rate = (stillborn + mummies) ÷ total born** — 공식대로 산출되는지 assert. 관례(stillborn only) 대비 ~3pp 높음 → 외부 직접비교 무효임을 **리포트에 명시**
- 집계값 == 행단위 합 (대시보드 수치 == 원천 합산)
- kg↔lb 왕복 변환 오차 허용범위 내, 날짜포맷/타임존 로케일별 일관

### B-5. 룰엔진 (2-resolver)

- Threshold Resolver firing authority = `rule_configs`/`operational_default`에서만
- Benchmark Context Resolver: governance verified 평균이 **comparative context로만** attach, trace에서 firing과 strict separation
- missing slot = silence(PASS)
- 40 inline operational_default가 시드값과 일치

### B-6. KPI/벤치마크 거버넌스

- verified 7 KPI 노출 정확 (psy 22.4 / msy 18.9 / farrowing_rate 85.7 / preweaning 89.1 / postweaning 84.3 / weaned_per_litter 10.45 / sow_turnover 2.14)
- **위조 0**: first-party source 없는 slot == `missing`, estimated 아님
- **KR 벤치마크가 한국시장 경로·외부 API로 노출 안 됨** (negative assert — 노출되면 결함)
- stillbirth professional cohort == `normalized_verified`만

### B-7. RBAC / 권한

- 역할별 가시성·조작 매트릭스(SUPER_ADMIN→VIEWER) 기대대로
- farm scope: 사용자는 **배정 농장만** 조회/조작. 멀티농장 배정자는 배정분만
- cross-farm / cross-role 접근 시도 → **차단** (우회 1건이라도 발견 시 critical 결함)

### B-8. 감사로그

- UAT 중 발생한 **모든 변경 → audit_log 1건** (who/what/when/before/after non-null)
- 변경 대비 감사 누락 **0**

### B-9. i18n / 현지화

- 7개 언어 키 누락 **0** (chat 라벨 ~285 포함)
- **D-7 KRW leak gate**: 외부·글로벌 경로에 KRW/원화 노출 **0**
- 미번역 하드코딩 문자열 검출 → 리스트업
- kg↔lb·날짜포맷 로케일별 정확

### B-10. 기간잠금 / 상태

- 잠긴 기간 쓰기 → **PeriodLockedError**
- 상태 전이 무결성(허용 전이만)

### B-11. E2E / UI / 성능 스모크

- 주요 화면 렌더, **화면 카운트 == DB 카운트**
- 콘솔 에러 0, 의도외 4xx/5xx 0
- **30농장 규모**에서 핵심 페이지 로드 — N+1 폭증/타임아웃 없음(쿼리 수·응답시간 기록)

### B-12. 전체 테스트 스위트 실행

- backend pytest 전량 + frontend + E2E 실행
- 통과수 baseline 대비 리포트 (UAT 신규 케이스 포함). **untested PASS 금지.**

---

### B-종료 — UAT QA 리포트 (오픈 전 결재용)

```
=== PIGOS PRE-LAUNCH UAT QA REPORT ===
env            : dev
uat_dataset    : farms=30 users=35 (uat_ flagged, RETAINED)
governance     : base kpi_def=16 bench=18 op=29 dmv=85 | final __/__/__/__ (동일=OK)
test_suite     : <before> → <after>  (backend/frontend/e2e)

[카테고리별]  PASS / FAIL / 결함수
B-2 무결성        : __ / __ / __
B-3 입력검증      : __ / __ / __   (positive __, negative __)
B-4 계산정합성    : __ / __ / __
B-5 룰엔진        : __ / __ / __
B-6 거버넌스      : __ / __ / __
B-7 RBAC          : __ / __ / __
B-8 감사로그      : __ / __ / __
B-9 i18n          : __ / __ / __   (KRW leak: PASS/FAIL)
B-10 기간잠금     : __ / __ / __
B-11 E2E/성능     : __ / __ / __

[CRITICAL 결함]   ← 오픈 차단 항목 (RBAC 우회 / 위조 노출 / KRW leak / 감사누락 / orphan)
- <id> <카테고리> <repro> <기대 vs 실제>

[전체 결함 목록]
- <id> <severity> <카테고리> <repro> <기대 vs 실제> ...

[명시 주의]
- stillbirth_rate = (stillborn+mummies)/total born → 외부 직접비교 무효
- UAT 데이터는 uat_ 플래그, 운영 아님, 잔존

pushed/deployed : NO (강제)
launch_gate     : GO / NO-GO  (CRITICAL 0 일 때만 GO)
```

<!-- ============================ append 끝 ============================ -->
