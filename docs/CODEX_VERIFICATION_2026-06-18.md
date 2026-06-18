# Codex 적대적 검증 의뢰 — 2026-06-18 (보고서·국가KPI·메뉴·라이브E2E)

> 목적: 직전 세션(2026-06-17 이후) 변경분을 **적대적으로 반증**한다. "통과처럼 보이는데 실제로 틀린 것"을 찾아라.
> 실행 위치: `c:/dev/PigOS` (main). 검증 후 Findings를 아래 형식으로.

## 스택 기동(검증 전제)
```
docker compose up -d postgres redis
cd api && uv run alembic upgrade head
cd api && PYTHONPATH=. uv run python scripts/seed_e2e.py
cd api && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000   # 라이브 검증용
cd src && npm run dev
```
테스트: `cd api && uv run pytest tests/ -q` · `cd src && npx tsc --noEmit` · `npm run test:e2e:smoke`(헤르메틱) · `npm run test:e2e:live`(실스택).

## 검증 대상 + 적대적 질문 (P=우선순위)

### [P0] 보고서 국가별 KPI 기준값 — **수치 날조 0** 인가
- 파일: `docs/specs/2026-06-17_country-kpi-differences.md`, `2026-06-17_pigplan-metrics-mapping.md`,
  마이그레이션 `b1c2d3e4f5a6`(KR PigPlan2025 benchmark_avg, region scope), `default_metric_values` region 45행.
- 공격: 시드된 KR 값이 **레퍼런스 `c:/dev/realtime/전체농가_품종별_주요생산성적_2025.xlsx` 실데이터와 일치**하는가? 출처 없는 값이 몰래 채워졌나? US/CN/SEA/LatAm 칸이 "출처 미확보"인데 임의값이 들어갔나? `source_ref/confidence` 메타가 값과 맞나?
- 닫는 조건: 시드 값 ↔ xlsx 중앙값/근거 대조표. 불일치 1건이라도 = finding.

### [P0] 보고서 계산식(R3) 정확성
- `app/services/report_service.py`(또는 reports 집계), 스키마 `app/schemas/report.py`.
- 공격: `stillborn_rate/mummified_rate/birth_loss_rate` 분모(총산 vs 실산?) 정확? `mating_1/2/3plus_count` 합 = total_matings? `group_by=breed` 집계가 품종 경계 안 섞나? 빈 농장/분모0에서 NaN/크래시?
- pytest `tests/integration/test_reports.py` 픽스처가 실제 공식을 검증하나, 통과만 시키나(약한 단언)?

### [P1] 메뉴 재설계 무결성
- `src/components/Sidebar.tsx`, `AlertsTabs.tsx`, `app/(app)/alerts|notifications/page.tsx`, `BottomNav.tsx`.
- 공격: 제거한 `/farrowing`·`/notifications` 메뉴의 페이지가 **고아**(도달 불가)인가? `/notifications`는 AlertsTabs로만 도달 — 탭 링크 정상? 통합 배지(`overdue.total + unread_count`) 합산 맞나? 라우트 testid 회귀로 헤르메틱 E2E 깨지나?

### [P1] 라이브 E2E가 진짜 왕복을 검증하나 (가짜 그린 아님)
- `src/e2e-live/*`.
- 공격: `sow-crud.live`가 **정말 DB write**를 검증하나, 아니면 낙관적 캐시/로컬상태만 보고 통과하나? (API를 죽이고 돌리면 실패해야 정상 — 죽여서 확인.) `read.live`의 "원시키 0/pageerror 0"가 빈 농장이라 무의미하게 통과하나? retry로 가린 실패가 실제 버그인가?

### [P2] 모바일 계약서 정확성
- `docs/mobile-integration-contract.md` vs 실제 라우트(`/docs`, openapi-v1.yaml 67 paths).
- 공격: §3.0 화면↔API 매핑 중 실제 없는 엔드포인트/필드 있나? 보고서 스키마(BenchmarkValue 등) 실제와 일치? members/orgs 설명이 실제 권한/응답과 맞나?

### [P2] alembic 단일 head / 멱등
- 공격: `alembic heads` 단일인가? `b1c2d3e4f5a6` 재실행 멱등? downgrade 정의됐나? seed가 운영데이터 가정(없는 farm) 깨나?

## Findings 형식
```
[P?] <한줄 제목>
- 파일/라인:
- 재현: <명령/단계>
- 기대 vs 실제:
- 심각도: P0~P2 / 확신도: 높음·중간·낮음
```
- 실제 재현된 것만. 추측은 "확신도 낮음"으로 분리. 깨끗하면 "해당 영역 이상 없음"도 명시.
