# UAT 실행 결과 — 2026-06-19 09:14 (1단계: 기존 스펙 실행 + 갭 진단)

> AI_UAT_PROMPT.md §9.0 **1단계** 모드. 기존 live 스펙만 실행, 새 spec 미작성.
> 절대규칙 준수: 통과 위조 0, 미커버 항목은 SKIP+사유 명시.

## 스택 기동 (Preflight)
- API :8000 `/health` → **200**
- 웹 `/` → **200** (프로덕션 빌드 `next start`, dev .next 락 회피)
- `NEXT_PUBLIC_API_URL` = `http://192.168.3.46:8000` (로컬 API로 라우팅 OK)
- git branch: `main` / status: untracked 문서·_uat_tmp만 (working tree 깨끗)
- 테스트 계정 `e2e@pigos.io` 로그인 가능 확인

## 실행 명령
```
cd src && npm run test:e2e:live -- --reporter=list
```
- config: `src/playwright.live.config.ts` (reporter=list, trace=on-first-retry, screenshot=only-on-failure)
- 결과: **28 passed / 0 failed / 0 flaky (50.3s)** — 14 spec 파일
- 로그: `docs/verification/uat_20260619_0914/run.log`

---

## 항목별 판정 (docs/uat-checklist.md §1~§8 매핑)

### §1 인증/온보딩
- [PASS] 로그인 → 대시보드 렌더(크래시/원시키 0) — `auth.live.spec.ts`
- [PASS] 세션 쿠키 + 토큰 저장 — `auth.live.spec.ts:18`
- [PASS] 언어 전환 ko/en/zh/es/vi — 대시보드·/sows raw i18n 키 0 + 스위처 반영 — `_uat_tmp/i18n-lang-switch.live.spec.ts`
  - ⚠️ 단, **번역 자연스러움**은 시각·해석 판정 필요(§9.8) → 사람 검수 SKIP
- [SKIP] 아이디 저장 체크 → 이메일 프리필 — 사유: 기존 스펙 미커버
- [SKIP] 잘못된 비번 → 401 + 해당 언어 에러 — 사유: 기존 스펙 미커버
- [SKIP] 회원가입/온보딩(신규 농장 생성) — 사유: 기존 스펙 미커버

### §2 돈군 CRUD
- [PASS] 모돈 등록(귀표/품종/RFID) → 목록 즉시 반영 — `sow-crud.live.spec.ts`
- [PASS] 모돈 도폐사 → 성공 배너 + 활성 목록서 제외 — `cull.live.spec.ts`
- [PASS] 비육돈 그룹 등록 → 목록 반영 — `finisher-crud.live.spec.ts`
- [SKIP] 모돈 검색(부분일치)+상태 필터 — 사유: 미커버
- [SKIP] 모돈 수정(귀표/품종) 저장 — 사유: 미커버
- [SKIP] 모돈 상세 번식 이력 타임라인/산차별 성적 — 사유: 미커버
- [SKIP] 웅돈 등록/수정 · 자돈 그룹 등록/이동 — 사유: 렌더만 확인(read), CRUD 왕복 미커버

### §3 번식 이벤트 (핵심)
- [PASS] 교배→분만→이유 전체 사이클 + 상태전이(실 DB) — `breeding-cycle.live.spec.ts`
- [PASS] 사고(RTS) → 상태 ACCIDENT — `repro-accident.live.spec.ts`
- [PASS] 분만 후 자돈 폐사 기록(실 DB) — `piglet-death.live.spec.ts`
- [PASS] 이유두수 공식 불일치 → 422 표시 + 저장 안 됨 — `validation.live.spec.ts`
- [PASS] 이벤트 삭제 → 상태 롤백(교배삭제 PREGNANT→OPEN) — `event-rollback.live.spec.ts`
- [SKIP] 교배 저장 후 **insights 배너**(정상/경고/심각) 표시 검증 — 사유: 미커버(사이클 전이만 검증)
- [SKIP] 분만 **숫자 타이핑(+/- 아님)** · born_alive 자동계산 — 사유: 미커버(값 검증은 422만)
- [SKIP] 월마감 잠금 기간 수정 시 423 — 사유: 미커버

### §4 KPI / 보고서
- [PASS] 대시보드 KPI 화면(/kpi) 실데이터 렌더 — `read.live.spec.ts`
- [PASS] 작업대장(work ledger) 렌더 + 교배 필터 — `ledger.live.spec.ts`
- [PASS] 일일보고 렌더 + 날짜 변경 — `daily-report.live.spec.ts`
- [PASS] /reports · /reports/reproduction 실데이터 렌더 — `read.live.spec.ts`
- [SKIP] 생산성적 **품종별 토글**(group_by=breed) · 국가 기준 대비 색상 — 사유: 시각·해석 판정 + 인터랙션 미커버
- [SKIP] 비육성적(ADG/FCR/폐사율) 값 검증 — 사유: 렌더만
- [SKIP] 통합표 국가 기준값 · CSV 내보내기 값 일치 · PRRS/모돈 보고서 — 사유: 미커버

### §5 할 일·알림 (통합 2탭)
- [PASS] 알림 화면 2탭(관리대상/시스템알림) 전환 + 실데이터 렌더 — `alerts-tabs.live.spec.ts`
- [PASS] /tasks · /notifications · /alerts 실데이터 렌더 — `read.live.spec.ts`
- [SKIP] 관리대상 6유형 + 도태권고 + 액션버튼(교배/이유 이동) — 사유: 탭 렌더만, 데이터유형·이동 미커버
- [SKIP] 시스템알림 개별/전체 읽음 · 유형 필터 — 사유: 미커버
- [SKIP] 사이드바 통합 배지(관리대상+미읽음) — 사유: 미커버
- [SKIP] 오늘 할 일 완료/무시/담당자 배정 — 사유: 미커버

### §6 설정/권한/기타
- [PASS] RBAC — OWNER는 모돈 등록 버튼 보임 — `rbac.live.spec.ts:11`
- [PASS] RBAC — VIEWER는 등록 버튼 숨김(읽기전용) — `rbac.live.spec.ts:17`
- [PASS] /settings 실데이터 렌더 — `read.live.spec.ts`
- [SKIP] 농장 설정 저장 → 알림 기준 즉시 변경 — 사유: 미커버
- [SKIP] thresholds override 입력/삭제 → 국가/글로벌 복귀 — 사유: 미커버
- [SKIP] VIEWER 서버 쓰기 차단(403) 직접 검증 — 사유: UI gating만 검증(버튼 숨김), 서버 403 응답 직접 미커버
- [SKIP] 언어×국가 단위/통화 분리 — 사유: 시각·해석 판정(§9.8)
- [SKIP] Ask AI(챗) Rule-grounded 응답 — 사유: 미커버

### §7 모바일 웹/반응형·미관
- [SKIP] 전 항목 — 사유: 사람 시각 판정(§9.8). 1단계는 새 spec·수동 스크린샷 미작성.
  - md 이하 사이드바→하단탭 / 이모지 잔존 0 / 빈·로딩·에러 상태 카피 — 사람 검수 필요

### §8 콘솔/네트워크
- [PASS] 14개 라우트 순회(/, /sows, /boars, /piglets, /finishers, /kpi, /reports, /reports/reproduction, /alerts, /notifications, /tasks, /settings) — 크래시 0 + raw i18n 키 0 — `read.live.spec.ts`
  - read/auth 스펙은 콘솔 error·페이지 크래시 시 실패하도록 작성됨 → 통과 = 콘솔 error 0
  - `validation.live.spec.ts`의 422는 **의도된 negative case**(§9.4) — FAIL 아님
- [SKIP] 새로고침/뒤로가기 시 상태 유지(인증/언어/필터) — 사유: 미커버

---

## 요약
**PASS 19 / FAIL 0 / SKIP 22** (체크리스트 항목 기준, 자동화 28 테스트 전부 green)

- FAIL 없음 ✅
- SKIP 대부분 = 기존 10+4 스펙이 커버 안 하는 인터랙션(검색/수정/설정 저장/CSV/Ask AI) + 시각·해석 판정(§7 미관, 번역 자연스러움, 국가 단위)

### 확인된 갭 (2단계 보강 후보 — 사람 승인 시에만)
1. **§1** 아이디 프리필 / 잘못된 비번 401 / 온보딩 신규농장
2. **§2** 모돈 검색·필터·수정, 상세 타임라인, 웅돈/자돈 CRUD 왕복
3. **§3** insights 배너 표시, 분만 숫자 타이핑·자동계산, 월마감 423
4. **§4** 품종별 토글, CSV 값 일치, 비육성적 값
5. **§5** 6유형 알림+액션이동, 읽음/필터, 오늘할일 액션
6. **§6** 설정 저장 반영, thresholds override, VIEWER 서버 403, Ask AI
7. **§7** 모바일/반응형/미관 — 사람 스크린샷 검수

## 생성·수정 파일
- `docs/verification/uat_20260619_0914/run.log` (실행 로그)
- `docs/verification/uat_20260619_0914/REPORT.md` (본 보고서)
- 프로덕션 코드·기존 스펙·helpers·DB 마이그레이션 **수정 없음** (규칙 4 준수)
- git add/commit/push **안 함**

## 스크린샷/trace
- screenshot=only-on-failure + 실패 0 → **자동 캡처 없음** (지어내지 않음)
- HTML report 없음(list reporter) → `run.log`로 대체

## 2단계 보강 (사람 승인 후 — 2026-06-19)
사용자 지시로 P0 신규 검증의 **브라우저 노출**을 확인하는 격리 spec 추가 (`src/e2e-live/_uat_tmp/p0-client-validation.live.spec.ts`):
- [PASS] 교배 미래일 → 제출 전 클라(Zod) 검증 에러 + 저장 안 됨 (FE-3)
- [PASS] 이유체중 >12kg → 클라 검증 에러 + 저장 안 됨 (FE-2/BE-2)
→ 2단계 **2 passed**. 누적 live: **30 passed / 0 failed**. (기존 스펙·helpers·프로덕션 코드 미수정)

## 2단계 후속 (2026-06-19) — 데이터 품질 리포트(#5) 추가 검증 + cleanup
- 신규 기능 **데이터 품질 리포트** (`GET /reports/data-quality`, `/reports/data-quality` 페이지) live 200 확인 (실제 MISSING_FARROWING 이슈 반환). 백엔드 pytest 4건 통과.
- stage-2 client-validation spec 최종: 교배 미래일(FE-3) + 비육 입식체중>50kg(FE-7) → **2 passed (안정)**.
- ⚠️ **테스트 인프라 관찰**: 반복 live 실행으로 e2e farm 모돈 78두 누적 → `/sows`(ear_tag 정렬, per_page 50) 1페이지에 신규 모돈 미노출 → `createSowViaUI` 일시 실패. **제품 버그 아님**(실사용은 검색·페이지네이션으로 접근). 격리 farm 모돈 soft-delete로 정리(§9.5) 후 **전체 30 passed** 회복.
- 최종 회귀: **live 30 passed / pytest 375 passed / tsc 0 / build OK**.

## 테스트 데이터 / cleanup
- 스펙은 `uniqueTag()` 고유 prefix로 생성(모돈·비육그룹·이벤트)
- **격리 농장**(`932208a6…` e2e 전용)에만 생성됨 → 운영 데이터 무영향
- best-effort cleanup: 일부 스펙은 등록만 검증(삭제 안 함) → 격리 농장에 테스트 데이터 잔존(허용). 누적 시 `scripts/seed_e2e.py` 재시드로 초기화 가능.
