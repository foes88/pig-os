# 검증 리포트 — /sync 영속 버그 + 백엔드 테스트 환경 (2026-06-16)

> 대상: Codex 재검증용. 작성: Windows(한국어) 개발 PC 세션.
> 범위: 백엔드(`pigos`) — pytest/라이브 E2E로 **검증 완료**. iOS(`pigos-ios`) — 작성만, **Mac/CI 검증 대기**.
> SSOT 계약: `docs/mobile-integration-contract.md`.

---

## 0. 한 줄 요약
`/sync` 경로의 영속 버그 **4종**(farrowing·piglet·weaning·reproductive)을 발견·수정하고 **회귀테스트로 가드**.
백엔드 `pytest 283 passed` + 모바일↔백엔드 라이브 전여정 그린.

---

## 1. 검증 결과 (이 PC에서 그린 확인)

| 검증 | 명령 | 결과 |
|---|---|---|
| 백엔드 전체 | `cd api; uv run pytest -q` | **283 passed** |
| /sync 회귀 | `uv run pytest tests/integration/test_sync_farrowing.py -v` | **3 passed** |
| 라이브 E2E(§8a) | (백엔드 기동 후) `pigos-android> pwsh scripts/Run-IntegrationQa.ps1` | **통과** (farrowings/piglet_events DB 영속 실측: 40/39) |

### 백엔드 기동 (라이브 검증용)
```powershell
cd c:\dev\pigos\api
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000   # /docs 200 확인
```

---

## 2. 백엔드 테스트 환경 — Windows 한국어 PC 막힘 2건 (해결됨)
`uv run pytest` 가 처음엔 219 passed / **61 errors** 였음. 원인:
1. **psycopg2 `UnicodeDecodeError: 'utf-8' ... byte 0xb8`** (connect 시): Postgres 메시지가 cp949(한국어 locale).
   ```powershell
   $env:PGPASSWORD="pigos"
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "ALTER SYSTEM SET lc_messages='C';"
   Restart-Service postgresql-x64-16
   ```
2. **`FATAL: database "pigos_test" does not exist`** (integration은 `<db>_test` 사용):
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -h localhost -c "CREATE DATABASE pigos_test OWNER pigos;"
   ```
3. dev DB(`pigos`)가 마이그레이션 8개 밀려 있었음(`alembic current`=6cbf1c758818) → `uv run alembic upgrade head`.
   이게 onboarding/complete 500(`column users.system_role does not exist`)의 원인이었음.

> Linux CI에선 1·2가 안 나지만, 로컬(특히 한국어 Windows) 재현 시 위 조치 필요.

---

## 3. 🔴 수정한 /sync 영속 버그 4종 (#8 부류)
공통 원인: `_process_*`가 ORM에 **잘못된 컬럼명 kwarg** 또는 **NOT NULL FK 누락**, 그리고 세션이 `autoflush=False`라 **같은 sync 배치의 직전 레코드 조회 전 flush 누락**. 직접 `POST /events` 경로만 테스트돼 `/sync` 경로가 무방비였음.

| 엔티티 | 증상 | 수정 | 커밋 |
|---|---|---|---|
| farrowing | `born_dead/mummies/farrowing_type`(모델 `stillborn/mummified/farrowing_ease`)+`mating_id`(NOT NULL) 누락 → INTERNAL_ERROR, 분만 100% 유실 | 컬럼명 교정 + 최근 mating 연결 + flush | `9fc008a` |
| piglet_event | farrowing 조회 전 flush 누락 → `NO_ACTIVE_FARROWING` 연쇄 | flush 추가 | `9fc008a` |
| weaning | `avg_weight_kg`(모델 `avg_weaning_weight_kg`)+`farrowing_id`(NOT NULL) 누락 → 이유 100% 유실 | 컬럼명 교정 + 최근 farrowing 연결 + flush | `16f0b3c` |
| reproductive | `TRANSFER_OUT`→`sow.status="TRANSFER_OUT"`(무효 SowStatus v2 → /sows?status= 422) | `TRANSFER`로 교정, `ABORTION→ACCIDENT` 추가 | `29767d6` |

- 회귀테스트: `api/tests/integration/test_sync_farrowing.py` (3) — `5511236`, `16f0b3c`, `29767d6`.
- 계약 공지: `docs/mobile-integration-contract.md §6 G6` (`2f0e025`).

---

## 4. Codex 재검증 / 확인 요청
1. **#8 재회귀 방지**: 누군가 `app/services/sync_service.py`를 다시 만지면 `test_sync_farrowing`가 잡아야 함 → 이 테스트 유지/통과 확인. (이 path는 과거 2회 silent 회귀했음.)
2. **reproductive `SOLD` 의미 분기**: `event_service`(직접)는 SOLD/TRANSFER_OUT에 상태전이 안 함(SOLD는 `/cull` 전용). `/sync`(오프라인)는 reproductive로 SOLD→상태전이함. 의도된 분기인지 도메인 판단 필요. (이번 수정은 무효값 `TRANSFER_OUT`만 교정, SOLD 동작 보존.)
3. **계약서 §4 stale**: `mobile-integration-contract.md §4`가 `reproductive_events`·`health_events`를 push/pull 목록에서 누락. 실코드(`sync_service` 637-642 / ServerChanges 551-571)는 둘 다 처리함 → 문서 갱신 권장.
4. **iOS 미검증**: `pigos-ios`의 SowStatus v2(`21a5c39`)·entry_type(`de8fff9`)·디바이스 등록(`c74d9c9`)·base URL(`308a82a`)·KPI 포팅(`3ff63ce`)은 **Windows 빌드 불가로 미검증**. Mac/Xcode `xcodegen`+빌드 또는 iOS CI에서 컴파일·§8b 글루 확인 필요.

---

## 5. 관련 커밋 (pigos)
```
29767d6 fix(sync): reproductive status -> valid SowStatus v2
16f0b3c fix(sync): /sync weaning persistence (#8-class)
2f0e025 docs(contract): §6 G6
5511236 test(sync): regression guard /sync farrowing+piglet (#8)
9fc008a fix(sync): /sync farrowing + piglet_event persistence (#8)
```
