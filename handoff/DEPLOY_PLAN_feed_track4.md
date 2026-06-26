# 배포계획 — Feed + Track4 B·C 묶음 (TARGET_ENV)

> dev 검증 산출물. **실제 배포는 사람이 수행.** governance(A-하이브리드) 제외 묶음.
> TARGET_ENV = staging|prod (미확정 — 환경값 박지 않음).

## 1. 포함 커밋 (이 4개만)
| 커밋 | 내용 |
|---|---|
| `cabeb96` | Feed 입력 백엔드 (POST/GET/DELETE feed-records + 검증 + 테스트) |
| `9ed03e1` | Feed 입력 프론트 (/feed 페이지 + 7개어 + Sidebar) |
| `a7960ca` | Track4-B D-7 원화누수 게이트 (loss.sow_culling KR 전용) |
| `97c286c` | Track4-C PeriodLockedError 409→423 |

## 2. 변경 파일
**백엔드**: `app/main.py`(feed 라우터 등록), `app/routers/base/feed.py`, `app/schemas/feed.py`, `app/services/feed_service.py`, `app/engine/rules/loss.py`(D-7), `app/core/exceptions.py`(423), `app/services/event_service.py`(PeriodLockedError) + 테스트 3파일
**프론트**: `src/app/(app)/feed/page.tsx`, `src/lib/api/endpoints/feed.ts`, `src/components/Sidebar.tsx`, `src/messages/{en,ko,zh,es,vi,th,pt}.json`

## 3. 마이그레이션 — **없음 (0개)** ★
- 번들 4커밋에 alembic 마이그레이션 **0개**. `feed_records`는 **초기 스키마**(`f36cde9d762c_initial_schema`)라 prod에 이미 존재 → 신규 DDL 불요.
- ⚠️ **`alembic upgrade` 실행 금지.** 현재 브랜치(main)는 미배포 governance 마이그레이션 4개를 포함:
  `c5e7a9b1d3f0 → d7f9b2c4e6a1 → e1a3c5d7f9b2 → f2b4d6e8a0c1` (전부 A-하이브리드, 본 묶음 제외).
  raw 브랜치로 `alembic upgrade head` 하면 이들이 prod에 적용됨 = 변수 오염. **금지.**
- 가역성: 번들 자체 마이그레이션 0 → DB 롤백 불요. (governance 4개는 downgrade 정의돼 있으나 이번에 적용 안 함.)

## 4. 격리 배포 방식 (governance 코드·마이그레이션 둘 다 배제)
브랜치 raw 배포는 governance 코드(inert여도)·마이그레이션을 끌고 오므로 **금지**. 둘 중 택1:
- **(권장) 릴리스 브랜치 cherry-pick**: prod 베이스라인(`b3d5f7091a2c` 시점 커밋)에서 분기 → 위 4커밋만 cherry-pick → 그 브랜치로 빌드·배포. governance 코드/마이그레이션 0. alembic 불필요(또는 no-op).
- (대안) 코드 파일 오버레이: 변경 파일만 prod에 scp → api/web/worker recreate. alembic 미실행. (이미지 빌드 없이 파일 교체 — 비권장이나 가능)

## 5. 신규 엔드포인트
- `POST /api/v1/farms/{farm_id}/feed-records` (WORKER+) — 수기 급이량 생성
- `GET  /api/v1/farms/{farm_id}/feed-records` — 목록
- `DELETE /api/v1/farms/{farm_id}/feed-records/{id}` (관리자) — soft-delete
- 프론트 라우트: `/feed`

## 6. 배포 절차 (TARGET_ENV, 사람 수행)
1. 릴리스 브랜치 준비(§4 권장안) — governance 미포함 확인(`git log` diff).
2. `USE_GOVERNANCE_BENCHMARKS=false` 확인(env). 켜지 않음.
3. 빌드: web(프론트 NEXT_PUBLIC_* build-arg) + api/worker.
4. **alembic upgrade 실행 안 함**(번들 마이그레이션 0).
5. recreate: api·web·worker. (worker는 자체 이미지 — `build worker` 별도)
6. 스모크: `/feed` 200, `POST feed-records` 201, 잠긴기간 423, 기존 도메인 200.

## 7. 롤백 절차
- 코드: 4커밋 revert(또는 직전 이미지로 재배포). DB 변화 0이라 DB 롤백 불요.
- flag: 변화 없음(계속 OFF).

## 8. 사전 확인 게이트 결과 (dev)
- G1 격리: ✅ 4커밋 governance 무오염
- G2 검증: ✅ pytest 654 / tsc 0 / flag OFF
- G3 마이그레이션: ✅ 번들 0개, feed_records 기존(초기스키마), 비가역 0
