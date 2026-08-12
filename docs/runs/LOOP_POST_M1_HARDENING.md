# LOOP_POST_M1_HARDENING — M1 이후 자율 하드닝 loop

> 목적: M1(NPD/WEI 오표시 제거) 이후, **DB 정상 상태에서 드러나는 실제 테스트 실패**를 고치고
> 그 과정을 회귀테스트로 고정한다. 계산식·스키마 무변경 원칙 유지.
> 기준 브랜치: `fix/kpi-npd-wei-m1` (origin/main + M1 7커밋).

## 하드 규칙 (매 iteration)
1. **push 금지 · 배포 금지.** 로컬 `git commit`까지만 (trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`).
2. **위조 0**: 값·정책·법무 빈칸을 발명하지 말 것. 모르면 리포트.
3. **각 변경 검증 후에만 커밋**:
   - 백엔드 `cd api && uv run pytest <해당파일> -q -p no:cacheprovider && uv run ruff check <파일>`
   - 프론트 `cd src && PATH="/c/Users/bjh/AppData/Roaming/nvm/v22.11.0:$PATH" NODE_OPTIONS=--experimental-require-module npx tsc --noEmit && npx vitest run <파일> --no-file-parallelism`
   실패하면 **되돌리고** 다음으로.
4. **1 변경 = 1 커밋**(원자적). 동작 바꾸는 수정은 반드시 재현테스트 먼저.
5. **손대면 멈추고 리포트**: 스키마/마이그레이션/과금/권한/계산식(`calculate_npd_breakdown`·`v_sow_npd`·PSY 분모)/M1 INTERIM 트리거.
6. **Docker 죽으면** `powershell.exe -Command "Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'"` → `docker start pigos-postgres` → `pg_isready`. 3회 실패 시 DB 불필요 작업만.
7. 막히거나 애매하면 **멈추고 리포트**(추측 진행 금지).

## 우선순위
1. **P0 — 실패(FAILED) 테스트 수정.** DB 정상 상태에서 나는 진짜 실패. 원인 규명 → 최소 수정 → 회귀테스트.
2. **P1 — collection ERROR 해소.** import·픽스처 깨짐(예: 존재하지 않는 심볼 import). 코드가 옳고 테스트가 낡았으면 테스트를 현행화.
3. **P2 — 남은 setup ERROR**가 환경(마이그레이션 미적용 등)이면, 재현 절차를 `docs/`에 기록만 하고 코드 변경 없음.
4. **P3 — 커버리지 갭**: M1이 건드린 영역(KpiCard nullable·report metric_code·npd.overdue 비활성)의 회귀테스트 보강.

## STOP 조건
- FAILED 0 + 신규 회귀테스트 green / 또는 남은 것이 전부 환경·사람 필요 항목 → 리포트하고 종료.
- 예산·시간 도달 → 리포트하고 종료.

## 종료 리포트
- 로컬 커밋 목록 · 고친 실패 수(before/after) · 추가 테스트 수 · **못 고친 것과 이유**(사람/환경 필요 항목 명시).
