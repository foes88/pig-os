# Codex 독립검증 결과 — 2026-08-25 세션

검증일: 2026-08-26 KST

검증 HEAD: `8476d16` (`main`)

대상 커밋: `c262f5f`, `26a28d2`(및 되돌린 `7417b01`), `011c972`, `bfa8774`, `32b032d`, `fa1ef3d`, `de4e68d`, `e530dca`

원칙: 소스 수정 없음. 로컬·운영 DB에는 읽기 전용 조회만 수행했다. 기존 사용자 변경 `docs/adr/ADR-KPI-08-backend-owned-kpi-status.md`는 건드리지 않았다.

## 결론 요약

**최종 판정: NO-GO**

출시 전에 최소한 다음 사항이 해소되고 동일한 적대 시나리오가 다시 통과해야 한다.

1. 계정 삭제 화면이 실제 `DELETE /auth/me`를 호출하고, 소유자가 아닌 일반 계정도 앱 안에서 삭제를 시작할 수 있어야 한다.
2. 실제 DB 단절이 `503 DB_UNAVAILABLE` + `Retry-After` + 브라우저에서 읽을 수 있는 CORS 응답으로 귀결되어야 한다.
3. Alembic head만으로 ORM이 요구하는 스키마를 재현해야 한다.
4. 농장 현지 날짜를 도입하면서 남은 feed 검증, 서부 시간대 KPI 스케줄, PSY 기본 연도, sync/REST 불일치를 해소해야 한다.
5. 백업 URL 누락의 무출력 종료와 증분 백업의 부분 성공을 실패로 감지할 수 있어야 한다.

회귀 테스트가 모두 통과한다는 사실은 아래 런타임·운영 경로 결함을 반증하지 않는다. 현재 테스트는 실제 DB 연결 단절, 브라우저 CORS, 앱 삭제 버튼과 배포 가능한 Alembic 스키마를 통과시키지 않는다.

## 환경과 실행 결과

| 항목 | 결과 |
|---|---|
| 로컬 Alembic | `e2b5d7c9a1f3 (head)` |
| 운영 Alembic | `e2b5d7c9a1f3`; PostgreSQL 17.11, DB TZ `Asia/Seoul` |
| 운영 데이터 개요 | farms 68, sows 141,361, farrowings 531,760 |
| 운영 농장 TZ | UTC 47, Asia/Seoul 12, America/Chicago 5, America/Mexico_City 3, Asia/Manila 1 |
| 백엔드 전체 | `1167 passed, 1 skipped in 114.54s` |
| 계정삭제·TZ·NPD 경로격리·에러계약 | `52 passed` |
| NPD·표시정책·BR pilot | `34 passed` |
| 프론트 apiErrors+i18n | `34 passed` (Node 22.11.0, node env, threads) |
| TypeScript | `npx tsc --noEmit`, exit 0 |
| Ruff | 기존 9건으로 exit 1; 모두 테스트 파일의 미사용 import/변수 또는 import 정렬 |
| Alembic check | exit 1; 모델/마이그레이션 드리프트 다수 검출 |

## 결함

[BLOCKER] [계정 삭제/App Review] 삭제 화면이 API를 호출하지 않아 앱 내 계정 삭제가 불가능함

  재현: `/settings/delete-account`에서 확인 문자열을 입력하고 활성화된 “계정 영구 삭제” 버튼을 누른다. 네트워크 요청·상태 변경·페이지 이동이 모두 없다. 소유자가 아닌 계정은 화면 자체가 `ownerOnly`로 차단된다.

  기대: 계정을 생성할 수 있는 모든 사용자가 앱 안에서 삭제를 시작할 수 있고, 재인증용 비밀번호를 입력한 뒤 `DELETE /api/v1/auth/me`가 호출되어야 한다. Apple은 계정 생성을 지원하는 앱이 앱 내부에서 삭제를 시작하도록 요구하며, 모든 사용자가 대상이라고 명시한다. 재인증 요구는 허용된다. 근거: [Apple 계정 삭제 지원 문서](https://developer.apple.com/support/offering-account-deletion-in-your-app/), [App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).

  실제: `src/app/(app)/settings/delete-account/page.tsx:72-76`의 삭제 버튼에는 `onClick`이 없고, 페이지에는 백엔드가 필수로 요구하는 password 입력도 없다. 프론트 API endpoint 모듈에도 `/auth/me` 삭제 호출이 없다. `page.tsx:14-25`는 `canOwn(useActiveRole())`로 일반 구성원의 개인 계정 삭제를 막는다.

  분류: BUG

[MAJOR] [DB 마이그레이션] Alembic head가 ORM 스키마를 재현하지 못함

  재현:
  ```text
  cd api
  uv run alembic current
  uv run alembic heads
  uv run alembic check
  ```

  기대: `e2b5d7c9a1f3`까지 적용한 DB가 모델과 일치하고 `alembic check`가 통과해야 한다.

  실제: current/head는 모두 `e2b5d7c9a1f3`지만 check는 exit 1이다. 특히 모델이 요구하는 `farms.data_origin`, `farms.data_classification`, `idx_farms_classification`이 로컬 head DB에 없으며, 네 개의 sow/date 계열 인덱스 등 추가 드리프트도 검출된다. 운영에는 두 컬럼과 네 인덱스가 수동으로 존재하지만 `idx_farms_classification`은 없다. 즉 운영의 수동 보정이 새 환경·복구 환경에서 재현되지 않는다. 통합 테스트는 Alembic이 아니라 `Base.metadata.create_all()`을 사용하므로 이 결함을 숨긴다.

  분류: BUG

[MAJOR] [에러 계약/DB 장애] 실제 DB 단절이 503이 아니라 500으로 반환됨

  재현: 로컬 `pigos-postgres`를 중지하고 실제 앱에 `POST /api/v1/auth/login`을 보낸 뒤 DB를 다시 시작하여 같은 요청을 재시도했다.

  기대: 장애 중 `503`, body `DB_UNAVAILABLE`, `Retry-After: 5`; 복구 후 새 연결로 정상 응답.

  실제: 장애 중 `500 INTERNAL_ERROR`, `Retry-After` 없음, CORS 없음이었다. 원인은 새 asyncpg 연결 실패가 `ConnectionRefusedError`/`TimeoutError`로 올라오지만 `api/app/core/exceptions.py:87-103`은 `sqlalchemy.exc.OperationalError`와 `asyncpg.PostgresConnectionError`만 503으로 처리하기 때문이다. DB 재시작 후에는 같은 프로세스가 정상적인 `401` 로그인 실패를 반환해 자동 복구 자체는 확인됐다.

  분류: BUG

[MAJOR] [에러 계약/CORS] catch-all 500을 브라우저가 읽을 수 없음

  재현: 실제 app에 `RuntimeError`를 내는 검증 route를 메모리에서 추가하고 `Origin: https://verify.example`로 TestClient 요청했다. 파일 변경은 하지 않았다.

  기대: 프론트가 안전한 `INTERNAL_ERROR`와 `request_id`를 읽을 수 있도록 500에도 CORS가 있어야 한다.

  실제: body는 안전했고 SQL·stack·비밀 문자열은 노출되지 않았지만 `access-control-allow-origin=None`이었다. 반면 직접 생성한 `OperationalError`의 503에는 CORS와 `Retry-After: 5`가 있었다. Starlette의 catch-all 처리 위치가 `CORSMiddleware` 바깥이어서 일반 500만 우회한다. request ID는 응답과 로그 메시지에 동일하게 남아 추적 가능했다.

  분류: BUG

[MAJOR] [시간대/이벤트 입력] feed REST 경로가 여전히 UTC 날짜로 현지 오늘을 거부함

  재현: UTC `2026-08-25 22:00` = KST `2026-08-26 07:00`으로 고정하고 `FeedRecordCreate(record_date=2026-08-26, ...)`를 생성했다.

  기대: 서울 농장의 현지 오늘인 `2026-08-26`을 허용해야 한다.

  실제: `api/app/schemas/feed.py:24-29`가 농장 context 전에 `datetime.now(UTC).date()`와 비교하여 `record_date cannot be in the future`로 거부했다. 서울 00:00~09:00의 원 결함이 feed 경로에 남아 있다.

  분류: BUG

[MAJOR] [시간대/KPI worker] UTC cron과 농장 현지 날짜 조합이 미주 농장의 주·월 스냅샷을 늦춤

  재현: `api/app/jobs/worker.py:53-57`의 월간 cron `day=1, 00:15 UTC`를 Chicago 농장에 적용했다. 이 시각의 현지는 전월 마지막 날이다. `_period_bounds("monthly", local_today)`도 함께 계산했다.

  기대: 각 농장의 완료된 직전 월/주가 한 번씩 적시에 집계되어야 한다.

  실제: 2026-09-01 00:15 UTC에 Chicago는 2026-08-31이고 함수는 7월을 계산한다. 8월 스냅샷은 10월 1일 UTC까지 한 달 늦어진다. 주간도 월요일 00:10 UTC가 Chicago 일요일이므로 직전 주가 아니라 그 전 주를 다시 계산하고 최신 주는 일주일 늦어진다. unique key가 중복 row는 막지만 `_upsert_snapshot`은 SELECT 후 INSERT라 동시 실행 시 원자적 upsert도 아니다.

  분류: BUG

[MAJOR] [시간대/PSY API] 기본 연도가 import 시점의 서버 연도로 고정됨

  재현: `api/app/routers/base/kpi.py:100`의 `Query(default=date.today().year)`를 연말부터 새해까지 재시작 없이 유지하는 프로세스로 평가한다.

  기대: query의 year 생략 시 요청 시점 농장 현지 연도를 사용해야 한다.

  실제: 기본값이 모듈 import 때 한 번 UTC로 계산된다. 서울 1월 1일 00:00~09:00에는 이전 연도이며, 프로세스가 재시작하지 않으면 이후에도 계속 이전 연도가 기본값이다. `farm_today(farm)`은 그 뒤 상한에만 적용돼 기본 year 오류를 교정하지 못한다.

  분류: BUG

[MAJOR] [시간대/설정 검증] 잘못된 IANA timezone을 저장할 수 있고 조용히 UTC로 대체함

  재현: `FarmCreate`/`FarmUpdate`에 오타 난 timezone 문자열을 넣은 뒤 `farm_today`를 호출한다.

  기대: 저장 전에 유효한 IANA timezone인지 검증하거나, 최소한 오류를 관측 가능하게 기록해야 한다.

  실제: `api/app/schemas/farm.py:27-42`에는 timezone 검증이 없다. `api/app/core/farm_time.py:58-62`와 `alert_service.py:30-37`은 모든 예외를 잡아 로그 없이 UTC 날짜를 반환한다. 운영의 현재 5종 timezone은 모두 유효하지만, 향후 오타 하나가 원래의 날짜 경계 결함을 재발시키고 탐지를 막는다.

  분류: CONFIG

[MAJOR] [Sync/데이터 정합성] 같은 미래 이벤트를 REST와 sync가 다르게 판정함

  재현: 서버 오늘의 다음 날을 `mating_date`로 제출한다. `sync_service._is_future_date`와 REST 농장 현지 검증을 비교했다.

  기대: 동일 farm/event는 입력 경로와 무관하게 같은 판정을 받아야 한다.

  실제: `api/app/services/sync_service.py:75,107-119`는 서버 날짜 +1일까지 허용해 tomorrow를 통과시키지만 REST는 농장 현지 오늘보다 크면 거부한다. UTC·Chicago 농장에서는 같은 이벤트가 sync 성공/REST 실패가 된다. UTC+14가 세계 최대 실제 offset이라는 전제와 1일 tolerance 자체는 2025~2030 tzdata 598개 zone 전수 계산으로 확인했지만, `process_sync`는 이미 Farm을 보유하므로 농장 날짜를 계산하지 못할 이유는 없다.

  분류: BUG

[MAJOR] [계정 삭제/고지·보유] UI의 영구삭제·30일 복구 고지와 서버 동작·정책이 서로 모순됨

  재현: `src/messages/ko.json:1049-1062`, `en.json:1049-1062`, `account_deletion_service.py:118-157`, 개인정보처리방침 후보본 제9조를 대조했다.

  기대: 삭제되는 데이터, 조직 소유 데이터의 보존, 복구 가능 기간, 법정 보존 항목을 실제 처리와 동일하게 고지해야 한다.

  실제: UI는 모돈·농장 운영 데이터·AI/보고서·결제정보가 사라지고 30일 복구 후 영구 삭제된다고 말한다. 서버는 계정 식별자를 즉시 비가역 익명화하고 shared farm 원천 데이터와 consent ledger를 유지한다. 정책 `docs/legal/publish_candidate/PIGOS_GLOBAL_PRIVACY_NOTICE.md:142-150`은 원천 데이터 반환/파기와 consent ledger의 근거·기간을 여전히 `[OPEN]`/`[COUNSEL]`로 둔다. 한국 개인정보보호법 제21조도 불필요해진 개인정보의 파기를 원칙으로 하고 다른 법령상 보존만 예외로 두므로, 현재 열린 정책 항목을 확정된 근거처럼 간주할 수 없다. 근거: [개인정보보호법 제21조](https://law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0021&lsiSeq=270351&urlMode=lsScJoRltInfoR).

  분류: CONFIG

[MAJOR] [계정 삭제/농장 소유권] 비활성 구성원 link가 active orphan farm을 만들 수 있음

  재현: 유일한 active owner와 이미 `active=false`인 다른 사용자 사이에 같은 farm의 `UserFarm` link가 남은 상태에서 owner를 삭제한다.

  기대: 실질적으로 남은 active 구성원이 없으면 farm을 비활성화해야 한다.

  실제: `account_deletion_service.py:83-91`은 다른 `UserFarm` row 수만 세고 `User.active`를 join하지 않는다. 비활성 사용자의 오래된 membership도 shared farm으로 간주되어 farm은 active로 남고, owner membership만 삭제된다. 이후 active farm job은 실행되지만 접근 가능한 active 사용자가 없는 orphan 상태가 된다.

  분류: BUG

[MAJOR] [백업/URL 선택] DATABASE_URL key가 없으면 fallback·오류 안내 전에 무출력 종료함

  재현: `MIGRATION_DATABASE_URL`만 있는 임시 env와 mock `grep`로 `backup_db.sh`, `backup_incremental.sh`를 실행했다. 검증용 임시 파일은 즉시 삭제했다.

  기대: migration URL로 명시적으로 fallback하거나 구체적인 오류를 출력해야 한다.

  실제: 두 스크립트 모두 exit 1, stdout/stderr 0 byte였다. `set -euo pipefail` 아래 `URL=$(grep '^DATABASE_URL=' ... | head | cut | tr)`에서 grep 1이 case문 전에 스크립트를 종료한다. 6543 direct URL일 때 migration URL key가 없는 경우도 같은 방식으로 의도한 오류문 전에 끝난다. 또한 증분 스크립트에는 full script의 “대체 URL도 6543이면 거부” 검사가 없다.

  분류: BUG

[MAJOR] [증분 백업] 일부 테이블 조회 실패를 성공한 부분 백업으로 업로드함

  재현: 한 테이블의 psql 조회만 실패하고 다른 테이블은 성공하도록 명령을 대체해 증분 스크립트 흐름을 실행했다.

  기대: 테이블 하나라도 실패하면 전체 작업이 nonzero 또는 명시적 incomplete 상태여야 한다.

  실제: `ops/backup_incremental.sh:70`은 경고 후 `continue`하고, 다른 CSV가 하나라도 있으면 archive 생성·S3 업로드·exit 0으로 끝난다. 모니터링은 부분 백업을 정상 백업으로 오인한다. 증분 CSV는 삭제 row를 표현하지 못한다는 복구 한계도 별도 문서화가 필요하다.

  분류: BUG

[MINOR] [인덱스 마이그레이션] `IF NOT EXISTS`가 동일 이름의 잘못된 정의를 승인하고 downgrade가 수동 인덱스도 삭제함

  재현: head 직전 DB에 `idx_farrowings_sow_date`라는 이름으로 `(farm_id, farrowing_date)` 인덱스를 만든 후 upgrade/downgrade 흐름을 검토했다.

  기대: 기존 인덱스 정의가 `(sow_id, farrowing_date)`인지 검증하고, 마이그레이션이 소유하지 않은 객체는 downgrade에서 보존해야 한다.

  실제: `api/alembic/versions/e2b5d7c9a1f3_farrowings_sow_date_index.py:33-42`는 이름만 존재하면 upgrade를 성공 처리하고 downgrade는 동일 이름을 무조건 drop한다. 현재 운영 인덱스 정의는 정확하므로 즉시 장애는 아니지만 재해복구·수동 선적용 시 잠복 결함이다.

  분류: BUG

[MINOR] [KPI 표시정책/발효일] “회사 기준일”이 명시적 timezone이 아니라 프로세스 timezone에 종속됨

  재현: KST 자정 직후와 UTC 자정 직후에 `effective_from=2026-08-26`인 정책을 `ref` 생략으로 resolve한다.

  기대: 농장별 시간이 아니라 회사가 정한 하나의 명시적 governance timezone/날짜로 전 국가에 일관되게 발효해야 한다.

  실제: `api/app/services/kpi_policy_resolver.py:164,224,261`은 `date.today()`를 사용한다. 컨테이너 UTC에서는 한국 회사 기준 자정보다 9시간 늦게 발효된다. “농장 timezone을 쓰지 않는다”는 논리는 국가 내 일관성 면에서 타당하지만, 대안이 배포 호스트의 암묵적 timezone이어서는 안 된다.

  분류: CONFIG

## 확인 완료 항목

### `c262f5f` farrowings 인덱스

- 운영의 `idx_farrowings_sow_date` 정의는 `(sow_id, farrowing_date)`로 정확하다.
- 531,760행에서 크기는 21 MB, `idx_scan`은 검증 시점 51,671회였다.
- 10,251두 농장의 실제 `_NPD_SQL` LATERAL은 `Index Scan Backward using idx_farrowings_sow_date`를 사용했다.
- 같은 조회의 warm 실행은 약 52.2 ms와 47.0 ms였다. 첫 cold 실행 약 704 ms는 3,468 block read를 포함하므로 warm 값과 직접 비교하면 안 된다.
- 기존 `idx_farrowings_farm_sow(farm_id,sow_id)`는 해당 LATERAL에 `f.farm_id` 조건이 없고 leading column도 달라 대체 인덱스가 아니다.
- 인덱스 추가 전후 NPD 경로 테스트는 통과했고, 인덱스는 값을 바꾸지 않는다.
- 실제 운영 INSERT latency에 대한 인덱스 단독 증분 비용은 **미확보**다. 21 MB 저장비용과 높은 scan 사용량만 확인했으며 수치를 만들지 않았다.

### `7417b01 -> 26a28d2` WEI view fast-path 제거

- 운영 10,251두 warm 비교: inline 31.461 ms, view 31.907 ms, 평균값 동일.
- 운영 1,508두 warm 비교: inline 12.337 ms, view 12.066 ms, 평균값 동일.
- 유의미한 성능 이득은 없고 DB `CURRENT_DATE`와 API `as_of` timezone 차이의 정확성 위험은 실제 존재한다. 제거 판단은 타당하다.
- 메모리에서 repository SQL에 `SELECT * FROM v_sow_npd`를 주입하자 `test_npd_calc_path_isolation.py`가 예상대로 red가 됐다. guard는 직접 view 재도입을 막는다. 별도 모듈로 우회하는 변형까지 전역 탐지하는 테스트는 아니다.

### 계정 삭제 백엔드

- 실제 서명된 기존 access token을 `active=false` 사용자에 적용하자 `get_current_user`가 `User not found or inactive`로 거부했다. 토큰 만료 때까지 접근 가능한 결함은 없다.
- 삭제 service는 flush만 하고 router가 마지막에 commit하므로 중간 예외 시 session 종료 rollback이 가능하다.
- 재가입 테스트에서 새 UUID, 이전 org 연결 없음, membership 제거가 확인됐다.
- 순차 두 번째 삭제는 inactive 사용자 단계에서 막힌다. 완전히 동시인 두 요청은 두 요청 모두 204가 될 여지는 있지만 unique/FK 오염은 확인되지 않았다.
- 소유 판단은 `UserFarm.role_override or user.role`로 명시된 farm membership을 기준으로 하므로 조직 admin을 자동 소유자로 오인하는 경로는 확인되지 않았다.

### 테넌트 격리와 표시 정책

- farm KPI route는 계산·cache 전에 `FarmDep -> get_farm_context -> can_access_farm`을 통과하며 cache key도 farm UUID를 포함한다.
- 전체 suite의 `test_farm_access`, `test_org_hierarchy_access`, `test_kpi_display_tenant`가 통과했다. A 조직 자격으로 B 조직 farm KPI를 읽는 우회는 확인되지 않았다.
- global minimum 정책은 미결정 국가에서 visible 3개만 노출하고 14개 모두 `compute_enabled=true`를 유지한다. BR pilot override와 상속 테스트도 통과했다.

### 시간대 수정의 정상 범위

- 서울 현지 오늘이 UTC상 내일인 이벤트 거부와 Chicago 일요일 주 경계의 원 결함을 먼저 재현했고, 수정된 `farm_today` 대상 경로 테스트는 통과했다.
- period lock은 이벤트 자체의 year/month로 검사하므로 wall-clock timezone 회귀는 확인되지 않았다.
- 운영 21개 non-UTC active farm을 UTC/현지 인접 날짜로 읽기 전용 계산했을 때 PSY는 0/21, NPD는 2/21에서 달랐다. 서울 표본은 136.9→136.1, 다른 표본은 365.0→364.8이었다. 이는 현지 `as_of`로 기준일이 하루 전진한 결과로 방향성 오류 증거가 아니다.
- 같은 farm snapshot key에는 unique 제약이 있어 row 중복은 차단된다. 다만 위 worker 지연과 SELECT-then-INSERT 경쟁은 별도 결함이다.

### 에러·프론트·i18n

- 500/503 응답 body와 header에 원본 SQL, stack, schema명, 주입한 비밀 문자열은 노출되지 않았다.
- `request_id`는 응답과 error log에 동일하게 기록됐다.
- axios 401 interceptor는 먼저 refresh/retry하고 `resolveApiError`는 최종 rejection만 받는다. refresh 요청은 bare axios라 재귀하지 않는다.
- 8개 언어 key 완전성과 프론트 테스트는 통과했다. th/vi/ru 문구에 명백한 key·영문 잔존 오류는 찾지 못했지만, 원어민 품질 검수는 **미확보**다.

### 백업의 정상 범위

- `bash -n`은 두 스크립트 모두 통과했다.
- full backup은 pg_dump 실패·gzip 무결성 실패를 실패로 처리한다.
- S3 업로드 실패는 로컬 파일을 남기고 작업 자체는 계속한다. 요청된 “로컬 백업 보존” 동작과 일치한다.
- `find ... -mtime ... -delete` 대상은 로컬 backup directory뿐이며 S3 객체는 삭제하지 않는다.
- 운영 현재 direct/migration URL은 모두 PostgreSQL 17 port 5434의 같은 `pigos` DB를 가리키는 정상 조합이었다. 이는 스크립트가 향후 stale URL을 식별한다는 보장은 아니다.

## 적대 시나리오 판정

| 시나리오 | 판정 | 근거 |
|---|---|---|
| 1. 자정 경계 NPD | 부분 통과 | 대상 dashboard/NPD는 farm-local `as_of`; feed와 worker에 누락 경로 존재 |
| 2. 미래 날짜 sync | 실패 | tomorrow는 sync 통과, REST 거부 |
| 2b. 삭제 후 기존 token | 통과 | 실제 서명 token이 inactive DB row에서 즉시 거부 |
| 3. DB 차단/복구 | 실패 | 차단 중 500·Retry-After/CORS 없음; 복구 후 정상 |
| 4. 테넌트 격리 | 통과 | 접근 dependency·farm cache key·통합 테스트 확인 |
| 5. 표시 정책 | 통과 | visible 3, compute 14, BR override 확인 |
| 6. 서울/Chicago 경계 | 부분 통과 | 수정 대상 경로 테스트 통과; feed·cron·PSY default 반례 존재 |

## 미확보·STOP 항목

- 운영 이벤트 INSERT에 대한 새 인덱스의 독립적인 latency 증가량: 미확보.
- th/vi/ru 원어민 감수: 미확보.
- 개인정보처리방침의 consent ledger 보존 근거·기간과 B2B 원천 데이터 반환/삭제 기준: 문서 자체가 `[COUNSEL]`/`[OPEN]`; 법률 자문 전 확정 불가.
- 실제 App Store 심사 결과: 미확보. 다만 현재 UI는 공식 요구 이전에 기능적으로도 삭제 요청을 만들지 못한다.

## 최종 판정

**NO-GO — 계정 삭제 UI/App Review BLOCKER, 실제 DB 장애 계약 실패, 재현 불가능한 Alembic head, 현지 날짜 적용 누락, 백업의 무출력·부분 성공을 해소하고 위 적대 시나리오를 재검증하기 전까지 출시 불가.**
