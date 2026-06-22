# UAT 2단계 — 2026-06-22 (디자인 전면개편 + 리포트 회귀 검증)

> AI_UAT_PROMPT.md §9.0 **2단계** 모드. Deep Forest Green 색 시스템 전면 적용 +
> 종합일보/생산성적/P0 검증 이후 **전 스택 회귀**. 절대규칙: 통과 위조 0, 미커버는 SKIP+사유.

## 검증 대상 변경분 (이번 사이클)
- Deep Forest Green 컬러 시스템 (토큰 재정의, severity enum normal|warning|critical|insufficient, blue/purple 전수 제거)
- 자동 언어감지(middleware) + 로그인 ID/언어 기억
- record 6패널(교배~자돈폐사) 키트 재디자인 + 우측 모돈 컨텍스트 레일
- 종합일보(Comprehensive Daily) 백엔드 6섹션 + 프론트 일계/월계
- P0 검증 13종 + delete_mating 롤백 버그 수정 + 인증 무한루프 수정

## 스택 기동 (Preflight)
- API :8000 `/health` → **200**
- 웹 `/login` → **200** (프로덕션 빌드 `next start`)
- API 베이스 = 상대경로 + Next 프록시(`/api` → :8000) — LAN-IP 취약성 제거(c594932)
- 테스트 계정 `e2e@pigos.io` 로그인 OK

## 실행 결과

### 백엔드 (pytest)
```
cd api && uv run pytest tests/ -q
→ 390 passed (42.06s)
```
- unit(검증기/룰엔진/상태전이) + integration(번식사이클/검증오류/알람/리포트) 전부 그린
- 회귀: `test_delete_only_mating_rolls_back_to_open` (delete_mating 롤백 버그 재발 방지) 포함

### 프론트 live E2E (실 DB·실 API)
```
cd src && npx playwright test --config=playwright.live.config.ts
→ 30 passed (1.5m)
```
- 14 spec 파일, mock 아님(실제 API 응답 렌더)
- read 스윕 13개 라우트(신규 `/reports/comprehensive-daily` 포함) 크래시/원시 i18n 키 0
- 핵심 플로우: 교배→분만→이유 사이클, 이벤트 삭제→상태 롤백, RTS→ACCIDENT, 자돈폐사, 검증 422 화면표시, RBAC(OWNER/VIEWER) 게이팅

### 타입·빌드
- `tsc --noEmit` 0 에러 · `next build` OK · i18n 5개어 1136키 일치

---

## 항목별 판정 (uat-checklist.md §1~§8)

### §1 인증/온보딩
- [PASS] 로그인 → 대시보드 렌더(크래시/원시키 0) — `auth.live.spec.ts`
- [PASS] 세션 쿠키+토큰 저장, 토큰만료 무한루프 차단 — `auth.live.spec.ts` + 수정 e4acde4
- [PASS] 언어 전환 ko/en/zh/es/vi raw 키 0 — read 스윕
- [SKIP] 번역 자연스러움 — 사람 시각검수 필요(§9.8)

### §2 돈군 CRUD
- [PASS] 모돈 등록/도폐사, 비육 그룹 등록 — sow-crud / cull / finisher-crud
- [SKIP] 검색·필터, 모돈 수정 저장 — live 스펙 미커버(단위/통합 pytest로는 커버)

### §3 이벤트 입력·검증
- [PASS] 번식 사이클 전 구간 + 상태전이 — breeding-cycle.live
- [PASS] 검증 422 화면표시(이유두수 공식) — validation.live
- [PASS] 이벤트 삭제 → 상태 롤백 — event-rollback.live
- [PASS] P0 검증 13종 — pytest unit/integration

### §4 리포트
- [PASS] 일일보고 렌더+날짜변경 — daily-report.live
- [PASS] 번식성적 리포트 렌더 — read `/reports/reproduction`
- [PASS] 종합일보 6섹션 일계/월계 렌더 — read `/reports/comprehensive-daily` (신규)
- [PASS] 작업대장 + 필터 — ledger.live

### §5 디자인(Forest Green)
- [PASS] blue/purple/violet 전수 제거 — bac2bd9/8e82d00 (grep 0)
- [SKIP] 색감·느낌 최종판정 — 사람 시각검수(사용자가 "그 느낌 보고 수정" 명시)

---

## 미커버/후속 (정직 고지)
- **07~10 풀 hifi 레이아웃**(KPI 스파크라인, AI 2열 상세, 개체 테이블): 토큰+de-blue만 적용,
  풀 레이아웃은 **사용자 시각검수 게이트** 대기 ("그 느낌 보고 수정해야할듯")
- **생산성적 단일화면 통합**: reproduction/farrowing/production-summary 개별 존재, 통합 화면은 폴리시 잔여
- **vitest 프론트 단위테스트**: Node 20.11<20.12 (styleText 미지원)로 차단 → Node 업그레이드는 사용자 작업

## 결론
이번 사이클 변경분(색 시스템·record·종합일보·P0·버그수정) **회귀 0**.
백엔드 390 + live 30 + 타입/빌드 그린. 깨진 화면·원시 i18n 키 없음.
