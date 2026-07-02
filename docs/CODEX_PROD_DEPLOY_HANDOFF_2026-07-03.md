# 백엔드 프로드 배포 핸드오프 (codex) — 2026-07-03

안드로이드 배포와 짝. **앱보다 백엔드가 먼저** 최신이어야 함(release AAB는 api.pigos.io를 봄).
아래를 프로드에서 실행해주세요.

## 0. 배포 대상
- 레포: `github.com:foes88/pig-os.git`
- 브랜치: `main` · 커밋: **`a5d324e`** (origin/main = 동일, 이미 push됨)
- alembic head: **`c3e5f7a9b1d4`**

## 1. 코드 배포
```bash
git fetch origin && git checkout main && git pull   # a5d324e 까지
# (기존 배포 파이프라인대로 재시작/재배포)
```

## 2. DB 마이그레이션 (순서대로, head까지)
```bash
cd api
alembic upgrade head
```
적용되는 미적용 리비전 3개 (a1c3e5b7d9f2 → b2d4f6a8c0e3 → c3e5f7a9b1d4):

| 리비전 | 내용 | 짝이 되는 코드 수정 |
|---|---|---|
| `a1c3e5b7d9f2` | PigletTransfer soft-delete 컬럼 + HealthEvent(vaccine_code·active_substance·dose_mg) 컬럼 | 삭제 캐스케이드·health 이벤트 D핸드오프 |
| `b2d4f6a8c0e3` | `default_metric_values.unit_code` 한국어("두/복"·"두/모돈/년"·"일") → 중립토큰(piglets/litter·piglets/sow/year·days) | 인사이트 알림/배너 한국어 leak 수정 |
| `c3e5f7a9b1d4` | tasks 유니크 인덱스 `uq_task_open_per_sow_type`를 `(farm,sow,task_type,status)` → **OPEN 한정 partial unique** | 작업 완료 409 버그 수정 |

- 전부 **forward-only 안전**. b2d4는 데이터 UPDATE(downgrade no-op), c3e5는 인덱스 재생성(downgrade는 구 4컬럼 복원).
- 마이그레이션 전 **DB 백업 권장**(관행대로).

## 3. 데이터 backfill (1회성)
```bash
cd api
python -m scripts.backfill_reproductive_links
```
- 과거 reproductive_events에 빠진 `mating_id`/`breeding_cycle_id`를 상관 서브쿼리로 채움(이전 로컬 실행: 11608→1162 unlinked). KPI 정확도용. **멱등**(재실행 안전).

## 4. 배포 후 검증
```bash
# (안드로이드 레포에 있는 스크립트 — 프로드 대상)
bash scripts/prod_deploy_check.sh   # /docs 200 · username 인증 · dashboard 200(=마이그레이션·KPI OK)
```
추가 스모크(선택):
- `GET /api/v1/farms/{id}/events/ledger` 응답에 **`subtype`/`count` 필드** 존재 → 새 코드 배포 확인
- 작업 완료→재생성→재완료가 **409 없이** 성공 → c3e5 마이그레이션 반영 확인
- 알림 body에 한국어 단위("두/복") 안 뜨고 유저 언어로 → b2d4 + i18n 반영 확인

## 5. 이 배포에 포함된 이 세션 수정(참고)
백엔드 STABLE 버그 5건 수정(전부 TDD·회귀·712 pytest green):
작업완료 409 · 자돈그룹 과다폐사/전출 상한 · 미래 교배일(create) · 미래 교배일(update PATCH) · sow status 전이 가드(LACTATING/PREGNANT는 이벤트로만).

## 6. 롤백
- 코드: 이전 태그/커밋으로 재배포.
- 마이그레이션: `alembic downgrade a1c3e5b7d9f2`(→b2d4 이전) 등. 단 b2d4(unit 정규화)·backfill은 데이터성이라 downgrade해도 원복 불완전(무해). 문제 시 코드만 롤백 권장.

— 검증(SOAK 25사이클 315×25 그린 · release게이트 PASS)은 로컬 완료. 프로드 적용만 부탁드립니다.
