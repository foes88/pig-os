# UAT 실행 결과 — 2026-06-18 22:19

> 모드: §9.0 **1단계** (기존 e2e-live 스펙 실행 + 갭 진단). 새 spec 미작성. 위조 0.

## 환경 / Preflight
- git branch: `main` · git status: 미커밋 WIP 존재(`api/app/routers/base/sows.py`, `api/app/services/event_service.py`, `?? api/tests/integration/test_piglet_integrity.py`) — **건드리지 않음**
- API `:8000` /health → **200** · 웹 `/`(localhost:3000, Playwright webServer) → 기동 성공
- NEXT_PUBLIC_API_URL = `http://192.168.3.46:8000` (이 PC LAN IP = 동일 API)
- 시드 계정 `e2e@pigos.io` 로그인 → 200, DB users count=1
- 실행: `cd src && npm run test:e2e:live` (playwright.live.config.ts, workers=1, retries=1)
- ⚠️ 참고: API는 현재 working tree 코드로 기동(미커밋 WIP 포함 가능). EPERM 방지 위해 `.next` 삭제 후 단일 dev서버로 실행.

## 항목별 판정 (§1~§8 매핑)

### §1 인증·온보딩·언어전환
- [PASS] 시드 계정 실로그인 → 대시보드 크래시/원시키 0 — auth.live.spec.ts:8
- [PASS] 세션 쿠키 + 토큰 저장(실 로그인 결과) — auth.live.spec.ts:18
- [SKIP] 온보딩 위저드(회원가입→농장설정) — 기존 스펙 미커버(시드 계정 로그인만). 사유: 1단계 스펙 갭
- [SKIP] 언어전환 5개(ko/en/zh/es/vi) raw키 0 — 기존 스펙은 en 로케일만. 사유: 1단계 스펙 갭 + 시각·해석 판정 필요(§9.8)

### §2 모돈(슬개) CRUD
- [PASS] 모돈 등록 → 목록 즉시 반영(실 DB) — sow-crud.live.spec.ts:8
- [PASS] 도태 처리 → 성공 배너 + 활성 목록에서 제거 — cull.live.spec.ts:7

### §3 번식 이벤트(기록 입력 — 핵심)
- [PASS] 교배→분만→이유 전체 사이클(실 DB 상태전이) — breeding-cycle.live.spec.ts:9
- [PASS] 교배→PREGNANT→삭제→OPEN 롤백 — event-rollback.live.spec.ts:9
- [PASS] 교배→RTS→ACCIDENT(실 DB) — repro-accident.live.spec.ts:7
- [PASS] 분만 후 자돈 폐사 기록(실 DB) — piglet-death.live.spec.ts:7
- [PASS] 이유두수 공식 불일치 → 422 + 저장 안 됨 — validation.live.spec.ts:8

### §4 KPI·보고서(PSY/NPD/FR)
- [PASS] /kpi · /reports · /reports/reproduction 실데이터 렌더(크래시/원시키 0) — read.live.spec.ts
- [PASS] 일일보고 렌더 + 날짜 변경 — daily-report.live.spec.ts:7
- [PASS] 작업대장 렌더 + 교배 필터 — ledger.live.spec.ts:8
- [SKIP] KPI 임계/badge 색·해석, 값 정확도 — 사유: 시각·해석 판정 필요(§9.8)

### §5 손익알리미(통합 2차)
- [SKIP] 전 항목 — 기존 스펙 미커버. 사유: 2차 기능, 1단계 스펙 갭

### §6 설정·권한·기타
- [PASS] RBAC: OWNER 모돈 등록 버튼 노출 — rbac.live.spec.ts:11
- [PASS] RBAC: VIEWER 등록 버튼 숨김(읽기전용) — rbac.live.spec.ts:17
- [PASS] /settings 실데이터 렌더 — read.live.spec.ts
- [SKIP] 전체 권한 매트릭스(역할별 전 기능) — 시드 계정 한정. 사유: 1단계 스펙 갭

### §7 모바일·반응형·미관
- [SKIP] 전 항목 — 사유: 사람 시각 판정 필요(§9.8). 데스크탑 chromium만 실행.

### §8 콘솔·네트워크
- [PASS] 전 페이지 렌더 시 크래시/raw i18n 키 0 (read.live 12개 라우트) — read.live.spec.ts
- [PASS] 27 스펙 전체 그린, 의도된 422(validation) 외 예상치 못한 4xx/5xx 0, EPERM 0

## 요약
**PASS 27 / FAIL 0 / SKIP (섹션 단위) 6영역 항목** (실행된 자동 스펙 27개 전부 통과, 1.6분)

- FAIL 상세: 없음
- SKIP 상세: §1 온보딩 위저드·5개 언어전환 / §4 KPI badge·값 해석 / §5 손익알리미 / §6 전체 권한 매트릭스 / §7 모바일·미관 — 사유: 1단계 스펙 갭 또는 시각·해석 판정 필요
- 1차 실행(별도)에서 auth 세션·cull 실패는 Next `.next` EPERM(웹서버 불안정) 환경 원인 → 본 clean 재실행에서 전부 PASS로 확정

## 데이터 정리(§9.5)
- 각 스펙이 `uniqueTag()` 고유 prefix로 생성 후 자체 정리(기존 스펙 설계). 별도 잔류 정리 시도 없음.

## 아티팩트
- run.log: `docs/verification/uat_20260618_2219/run.log`
- 본 보고서: `docs/verification/uat_20260618_2219/report.md`
- (config: reporter=list → HTML report 없음. 실패 0이라 trace/스크린샷 미생성)

## 생성/수정 파일
- `docs/verification/uat_20260618_2219/{run.log, report.md}` (git commit 안 함)
- 프로덕션 코드·문서·기존 스펙·helpers 수정 없음
