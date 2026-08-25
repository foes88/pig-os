# Codex 독립검증 결과 — 2026-08-25

## 검증 기준과 범위

- 검증 시작 시 코드 기준은 `26a28d2`(`7417b01` fast-path 제거)였다.
- 검증 도중 HEAD가 문서 전용 커밋 `4b76322`로 이동했지만, 이 보고서의 대상 코드
  (`c262f5f`, `26a28d2`, `fa1ef3d`, `de4e68d`, `e530dca`)에는 변화가 없었다.
- 16:24 KST 이후 별도 작업자가 `api/app/core/farm_time.py`와 관련 미커밋 변경을 만들기
  시작했다. 이는 검증 시작 시점의 배포 대상이 아니며 전체 게이트도 그 변경 전 실행됐으므로,
  아래 TZ 결함 판정에서 제외했다. 작성 시점에도 부분 적용 상태라 별도 재검증이 필요하다.
- 코드 수정은 하지 않았다. 운영은 시계·스키마·인덱스·실행계획만 읽기 조회했고,
  DB 중단 실험과 마이그레이션 충돌 실험은 로컬 Docker DB에서만 수행했다.

## 게이트 실측

| 항목 | 결과 |
|---|---|
| 백엔드 전체 | `1136 passed, 1 skipped in 106.34s` |
| NPD·표시정책·에러 표적 | `57 passed in 4.80s` |
| 프론트 에러+i18n | `34 passed` (Node 22.11.0, node environment, threads) |
| TypeScript | `tsc_exit=0` |
| ruff | 기존 9건 재현, 이번 대상 파일 신규 건 없음 |
| 로컬 Alembic marker | 최종 `e2b5d7c9a1f3`로 복구 |
| `alembic check` | **실패** — 모델/마이그레이션 드리프트 다수 |

테스트 수는 인계문의 기대값과 일치하지만, 아래 실측 결함들은 기존 테스트가 모의 예외,
`Base.metadata.create_all()`, 구조 검사만 사용해 잡지 못했다.

---

## 결함

[MAJOR] [DB 마이그레이션] Alembic head가 실행 가능한 애플리케이션 스키마를 재현하지 못함

  재현:
  ```bash
  cd api
  uv run alembic upgrade head
  uv run alembic check
  docker exec pigos-postgres psql -U pigos -d pigos -c \
    "SELECT column_name FROM information_schema.columns
       WHERE table_name='farms' AND column_name IN ('data_origin','data_classification');"
  ```

  기대: `e2b5d7c9a1f3`가 `api/app/db/models`와 일치하고, head DB에서 ORM이 정상 동작해야 한다.

  실제:
  - marker는 head지만 로컬 DB에는 `farms.data_origin`, `farms.data_classification`이 없다.
    `Farm` ORM INSERT는 `UndefinedColumn: column farms.data_origin does not exist`로 실패했다.
  - 위 두 컬럼은 모델에만 있고 Alembic 버전 파일에는 없다. 운영에는 수동으로 존재한다.
  - 모델이 선언한 `idx_farms_classification`은 로컬 head와 운영 모두에 없다.
  - 로컬 head에는 `idx_matings_sow_date`, `idx_weanings_sow_date`,
    `idx_farrowings_mating`, `idx_removals_sow_date`도 없다. 운영의 앞 세 인덱스는 수동 존재한다.
  - `alembic check`는 위 컬럼/인덱스 외 nullable·unique/index 드리프트도 다수 보고하고 실패했다.
  - 통합 테스트는 `tests/integration/conftest.py:59-60`에서 Alembic 대신
    `Base.metadata.create_all()`을 사용하므로 이 결함을 숨긴다.

  분류: BUG

[MAJOR] [에러 계약] 실제 DB 순단이 503이 아니라 500으로 매핑됨

  재현:
  ```text
  1) 실제 app에 get_db 세션으로 SELECT 1을 실행하는 검증 라우트를 메모리에서 추가
  2) 요청 -> 200
  3) docker compose stop postgres
  4) 동일 프로세스/풀로 재요청
  5) docker compose start postgres, healthy 대기 후 재요청
  ```

  기대: `api/app/core/exceptions.py:89-106` 계약대로 `503 DB_UNAVAILABLE`,
  `Retry-After: 5`, CORS 헤더가 있어야 한다.

  실제:
  ```text
  before  200
  during  500 INTERNAL_ERROR / Retry-After 없음 / CORS 없음
  after   200
  ```
  중단 시 실제 예외는 asyncpg 연결 단계의 `ConnectionError: unexpected connection_lost() call`이었다.
  풀은 DB 복구 뒤 자동 정상화됐지만 실패 종류 계약은 지켜지지 않았다.

  원인: 현재 SQLAlchemy asyncpg 어댑터에서 연결 실패가 항상
  `sqlalchemy.exc.OperationalError` 또는 원본 `PostgresConnectionError`로 올라오지 않는다.
  어댑터 매핑상 `CannotConnectNow`, `TooManyConnections`, `QueryCanceled`, deadlock,
  serialization, invalid password, `PostgresConnectionError` 등 대부분의 `PostgresError`가
  generic DBAPI `Error`로 번역될 수 있다. 접속 거절은 이번처럼 일반 `ConnectionError`도 된다.
  현재 핸들러 두 개는 이들을 놓친다.

  잘못된 SQL(`SyntaxOrAccessError`, `UndefinedTable`)은 `ProgrammingError`로 번역되어 500에
  남으므로, 요청에서 우려한 “코드 버그가 무조건 503으로 둔갑”하는 과대 매핑은 현재
  asyncpg 경로에서는 확인되지 않았다. 반대로 실제 장애를 못 잡는 과소 매핑이 결함이다.

  분류: BUG

[MAJOR] [에러 계약/CORS] catch-all 500에서 브라우저가 안전한 에러 본문과 request_id를 읽을 수 없음

  재현:
  ```text
  TestClient(app, raise_server_exceptions=False)
  GET /__verify_boom
  Origin: https://verify.example
  ```

  기대: `api/app/main.py:82-89`의 CORS 계약이 500에도 적용되어 프론트가
  `INTERNAL_ERROR`와 `request_id`를 읽어야 한다.

  실제:
  ```text
  status=500
  access-control-allow-origin=None
  body={"code":"INTERNAL_ERROR",...,"request_id":"683710527223"}
  ```
  `Exception`/500 핸들러는 Starlette의 최외곽 `ServerErrorMiddleware`에서 실행되어 안쪽
  `CORSMiddleware`를 되통과하지 않는다. 같은 app의 전용 `OperationalError` 503 모의 응답에는
  CORS와 `Retry-After`가 모두 있었다. 캐시 무효화는 성공 응답만 대상으로 하므로 별도 회귀는
  관측되지 않았다.

  분류: BUG

[MAJOR] [TZ/KPI/이벤트] 농장 타임존이 있는데도 핵심 계산·검증이 컨테이너 UTC 날짜를 사용함

  재현:
  ```text
  운영 API: 2026-08-25T07:12:23+00:00
  운영 DB : TimeZone=Asia/Seoul, 2026-08-25 16:12:23+09
  로컬 Python: Asia/Seoul
  로컬 DB    : UTC
  ```
  운영 활성 농장 타임존은 UTC 47, Asia/Seoul 12, Asia/Manila 1,
  America/Chicago 4, America/Mexico_City 3이었다.

  기대: `Farm.timezone`(`api/app/db/models/platform.py:79`)을 사용해야 한다. 실제로
  알림(`alert_service.py:33-37`)과 리포트 라우터(`routers/base/reports.py:34-40`)는 이미
  농장 현지 날짜를 사용한다.

  실제: 검증 기준 커밋의 다음 경로는 `date.today()`/UTC 날짜를 사용한다.
  - `get_dashboard`와 이번주 경계: `kpi_service.py:791-837`
  - herd/loss/boar/rule context 및 trend: `kpi_service.py:393,577,611,637,691`
  - REST 교배 생성·수정: `event_service.py:184,908`
  - PSY/NPD 라우트, 연간 리포트, KPI worker, 정책 발효일 리졸버에도 동일 패턴이 있다.

  서울 농장의 월요일 00:00~09:00에는 API가 아직 일요일이라 `week_start`가 **지난주 월요일**로
  계산된다. 시카고/멕시코시티는 현지 저녁부터 서버 날짜가 하루 먼저 간다. NPD/PSY 일일
  기준일도 농장 자정이 아니라 UTC 자정에 바뀐다. 따라서 KST 23:59:59→00:00:01에는 갱신되지
  않고 09:00에 뒤늦게 하루 이동한다. 올바른 기준은 컨테이너 UTC나 DB KST 중 하나가 아니라
  이미 저장된 **농장 현지 타임존**이다.

  분류: BUG

[BLOCKER] [Sync/값 정합성] `mating_date=내일`이 수용되고 현재 KPI 경로끼리 값이 갈림

  재현: KR farm의 오늘을 `2026-08-25`로 두고 이유 10일 된 OPEN 모돈에
  `SyncMating(mating_date="2026-08-26")`을 `_process_mating`으로 넣은 뒤 같은 트랜잭션에서
  뷰와 inline repository를 조회했다.

  기대: 실제 농장 현지 기준 미래 사건은 거부되거나, 수용 정책이 있다면 모든 현재값 계산에서
  제외되어야 한다.

  실제:
  ```text
  accepted=True, rejected=None, conflict=False
  v_sow_npd: next_mating_date=2026-08-26, wei_days=11
  inline(as_of=2026-08-25): wei_days=None
  ```
  `sync_service.py:75,107-108`은 무조건 +1일을 허용한다. 뷰에는 `mating_date <= CURRENT_DATE`
  상한이 없어 미래 교배를 즉시 소비하지만 inline은 `:as_of`로 제외한다. 현재 앱 계산 경로는
  inline으로 격리돼 NPD 자체는 보호되지만, `get_dashboard`의 이번주 교배/분만/이유 쿼리
  (`kpi_service.py:817-836`)는 `>= week_start`만 있고 `<= today`가 없어 수용된 미래 사건을
  즉시 이번주 실적으로 센다. 미래 데이터 수용과 표시값 오염이 함께 재현됐다.

  분류: BUG

[MAJOR] [인덱스 마이그레이션] `IF NOT EXISTS`가 잘못된 동명이인 인덱스를 성공으로 오인하고 downgrade가 수동 인덱스를 삭제함

  재현:
  ```text
  alembic downgrade d1a4c6e8b2f5
  CREATE INDEX idx_farrowings_sow_date ON farrowings(farm_id, farrowing_date);
  alembic upgrade head
  -- marker=head지만 정의는 여전히 (farm_id, farrowing_date)
  alembic downgrade d1a4c6e8b2f5
  -- 수동 인덱스도 삭제됨
  ```

  기대: 운영에 미리 `CONCURRENTLY` 생성된 인덱스를 수용하되 정의가 정확한지 검증하고,
  downgrade가 마이그레이션 소유가 아닌 객체를 무조건 지우지 않아야 한다.

  실제: `CREATE INDEX IF NOT EXISTS`는 이름만 확인해 잘못된 정의도 성공 처리했다.
  이후 `DROP INDEX IF EXISTS`는 기원을 구분하지 않고 해당 이름을 삭제했다. 필요한 인덱스가
  없는데도 Alembic marker만 head가 될 수 있어 5초대 성능 회귀를 숨길 수 있다.

  분류: BUG

[MAJOR] [백업/설정 파싱] DATABASE_URL이 없으면 의도한 migration URL 폴백 전에 무출력 종료

  재현:
  ```text
  ENV_FILE=<MIGRATION_DATABASE_URL만 있는 파일> ./ops/backup_db.sh schema
  ENV_FILE=<MIGRATION_DATABASE_URL만 있는 파일> ./ops/backup_incremental.sh 3
  ```

  기대: 코드의 `case ''|*:6543/*)`대로 migration URL로 폴백하거나 명시적 오류를 내야 한다.

  실제: 두 스크립트 모두 `exit=1`, stdout/stderr **0 bytes**였다.
  `set -euo pipefail` 아래 `URL=$(grep '^DATABASE_URL=' ... | head | cut | tr)`의 `grep`이 1을
  반환해 `case` 전에 셸이 종료된다. 6543인데 migration URL이 없는 경우의 `ALT=$(grep...)`도
  같은 방식으로 의도한 오류문 전에 종료될 수 있다.

  선택 매트릭스의 나머지는 실측상 코드대로였다.
  - direct 5434가 있으면 `DATABASE_URL` 선택
  - direct 6543이면 `MIGRATION_DATABASE_URL` 선택
  - 다만 fallback 두 URL이 같은 라이브 DB인지 host/db identity를 확인하지 않아, stale
    migration URL이면 다시 과거 DB를 백업할 수 있다(CONFIG 위험).

  운영 현재값은 비밀번호를 제외해 확인한 결과 direct=`172.18.0.1:5434/pigos`,
  migration=`127.0.0.1:5434/pigos`, S3 bucket 설정 있음으로 정상 조합이다.

  분류: BUG

[MAJOR] [증분 백업] 테이블 일부 조회 실패를 성공한 부분 백업으로 확정·업로드함

  재현: 자동 탐색 결과를 `bad:created_at`, `good:updated_at`으로 모의하고 bad 조회만 실패시켰다.

  기대: 자동 탐색된 테이블 하나라도 실패하면 백업 전체가 실패(exit nonzero)하거나 결과가
  명시적으로 incomplete여야 한다.

  실제:
  ```text
  ⚠ bad 건너뜀(조회 실패)
  good 1행
  완료 ... 총 1행
  exit=0, inc-*.tar.gz 생성
  ```
  크론·모니터링과 S3는 이 부분 아카이브를 정상 백업으로 오인한다.

  분류: BUG

[MAJOR] [프론트 인증] 로그인 401도 토큰 refresh 인터셉터가 먼저 소비함

  재현: `authApi.login`은 `apiClient`를 사용한다(`src/lib/api/endpoints/auth.ts:15-16`).
  잘못된 자격증명으로 401을 받으면 `src/lib/api/client.ts:40-58`을 따라간다.

  기대: 보호 API의 401은 refresh/retry 후 최종 실패만 mapper로 가고, 로그인 자체의 401은
  즉시 로그인 화면의 “자격증명 불일치” 처리로 가야 한다.

  실제: 인터셉터는 요청 URL을 구분하지 않아 로그인 401에도 `_doRefresh()`를 시도한다.
  refresh token이 없거나 실패하면 인증정보를 지우고 `window.location.href="/login"`을 설정한
  뒤에야 원래 401을 reject한다. 로그인 페이지가 `resolveApiError`로 문구를 설정해도 동일 URL
  강제 탐색이 화면 상태를 초기화할 수 있다. 보호 API에서는 인터셉터가 mapper보다 먼저
  실행되는 순서 자체는 정상이나, 새 mapper의 실제 소비처인 로그인 경로가 예외 처리되지 않았다.
  기존 `apiErrors.test.ts`는 mapper 단위만 검사하고 인터셉터 체인은 검사하지 않는다.

  분류: BUG

[MINOR] [i18n] 러시아어 재시도 문구 한 건이 직역체임

  재현: `src/messages/ru.json`의 `errors.dbUnavailable` 확인.

  기대: 현지 사용자에게 자연스러운 장애 안내.

  실제: `Попробуйте через несколько мгновений.`은 의미는 정확하지만 일반 UI 러시아어로는
  `Попробуйте позже/через некоторое время.`보다 직역 느낌이 강하다. th·vi의 신규 에러 문구와
  돼지 업계 용어는 기능상 또는 명백한 의미 오류를 찾지 못했다. 네이티브 감수는 별도 필요하다.

  분류: BUG

---

## 확인됨

### `c262f5f` 인덱스 효과·값·비용

- 운영 최대 농장 10,251두(분만 42,899건)에서 실제 `_NPD_SQL`을
  `EXPLAIN (ANALYZE, BUFFERS, SETTINGS)`로 실행했다.
- `lact_open`의 `MAX(farrowing_date)`가
  `Index Scan Backward using idx_farrowings_sow_date`를 사용했다(965 loops, 각 약 0.004ms).
- 전체 실행은 약 223.6ms였다. 기존 `(farm_id, sow_id)` 인덱스는 해당 LATERAL에
  `farm_id` 조건이 없어 대체되지 않으며 새 인덱스는 중복이 아니다.
- 운영 531,760행에서 새 인덱스는 21MB(테이블 heap 86MB, 전체 인덱스 73MB)였고,
  생성 뒤 `idx_scan=51,659`로 실제 사용됐다.
- 로컬 520,000행 배치 모의에서 인덱스 없는 INSERT는 225~417ms, 새 인덱스 유지 INSERT는
  1,420~1,490ms, 인덱스 크기는 8.3MB였다. 실제 테이블은 다른 인덱스도 이미 유지하므로
  이 비율을 운영 단건 오버헤드로 그대로 환산할 수는 없지만, 절대 추가비용과 운영 사용량은
  성능 이득 대비 수용 가능 범위로 판단한다.
- `test_npd_*.py` 전부와 구조 가드 포함 표적 57개가 통과했다. 인덱스는 계산 SQL을 바꾸지
  않으므로 NPD 값 회귀는 관측되지 않았다.
- 단, 위의 동명이인 마이그레이션 안전성 결함은 별개다.

### fast-path 재도입 방지 가드

- 현재 계산 경로는 `v_sow_npd`, `CURRENT_DATE`, `now()`를 참조하지 않고 모든 기준일을
  `:as_of`로 바인드한다.
- 메모리에서 `_AVG_VIEW = SELECT ... FROM v_sow_npd ... CURRENT_DATE`를 재도입하자
  `test_no_view_or_wallclock_in_module_sql`이 의도대로 실패했다.
- 따라서 과거 방식의 직접 재도입은 가드가 막는다. 다만 다른 모듈에 별도 뷰 경로를 만드는
  우회까지 전역으로 막는 테스트는 아니다.

### 에러 응답의 비밀정보·request_id

- 500/503 모의 예외의 응답 body에는 스택, SQL, 스키마명, 원본 메시지가 없었다.
- 생성된 request_id는 같은 값이 로그 메시지 `[...]`와 응답에 남아 기본 uvicorn 포맷에서도
  검색 가능했다. 별도 formatter 필드가 없어도 메시지 본문에 포함되므로 추적은 된다.
- 결함은 일반 500의 CORS와 실제 DB 실패 분류이며, 본문 비밀정보 누출은 확인되지 않았다.

### 백업 S3 실패·보존

- 전체 백업을 모의해 S3 CLI 실패를 만들었을 때 로컬 `.sql.gz`는 남고 exit 0이었다.
  요청된 “S3 실패가 로컬 백업 자체를 실패시키지 않음”은 확인됐다.
- `find` 보존 삭제 대상은 `$BACKUP_DIR`/`$INC_DIR`의 로컬 파일뿐이며 S3 삭제 명령은 없다.
  S3 사본은 로컬 보존 정리에 영향받지 않는다.
- 실제 S3 쓰기/삭제는 수행하지 않았고 복원 경로도 이번 검증 범위에서 재시험하지 않았다.

### 테넌트 격리

- KPI 라우트는 계산·캐시 전에 `FarmDep -> get_farm_context -> can_access_farm`을 통과한다.
- 캐시 키도 farm UUID를 포함한다. 조직 A 자격으로 다른 조직 B 농장 접근이 403/404가 되는
  `test_org_hierarchy_access.py`와 전체 스위트가 통과했다.
- 인덱스와 제거된 fast-path는 이 권한 경로 및 SQL의 farm 필터를 변경하지 않았다.

### 표시 정책 `d1a4c6e8b2f5`

- 운영 실측: GLOBAL 14개, visible 3개 `{FARROWING_RATE,NPD,PSY}`,
  `compute_enabled=true` 14개.
- COUNTRY 정책이 없는 11개 운영 국가가 GLOBAL 최소값을 상속한다.
- `test_global_visible_minimum.py`와 BR 명시 정책 테스트가 통과했다.
  숨김과 계산 중단이 섞이는 회귀는 확인되지 않았다.

### 기간 잠금·알림·리포트

- period lock은 이벤트의 명시적 `date.year/date.month`로 조회해 DB/API 벽시계를 한 판정에
  섞지 않는다.
- 알림과 리포트 라우터의 기본 기간은 이미 농장 타임존을 사용한다.
- 반면 연간 리포트 내부의 현재연도 PSY/NPD cap은 `date.today()`를 다시 사용하므로 위 TZ
  결함에 포함했다.

## 테스트 공백 요약

- `test_error_contract.py`는 실제 DB를 내리지 않고 `OperationalError(...)`를 직접 생성한다.
  실제 asyncpg 예외 계층과 CORS middleware stack을 검증하지 않는다.
- 통합 DB는 Alembic이 아니라 `Base.metadata.create_all()`로 만들어 head 재현성을 검증하지 않는다.
- NPD 구조 가드는 강하지만 농장 현지 자정/주 경계 및 sync +1일과 뷰의 상호작용은 검증하지 않는다.
- 프론트 테스트는 순수 mapper만 검증하고 axios refresh 인터셉터와 로그인 요청의 결합을 검증하지 않는다.
- 백업 스크립트에는 URL 조합·부분 테이블 실패·S3 실패를 고정하는 자동 테스트가 없다.

## 최종 판정

**NO-GO(미래일 sync가 현재 실적을 오염시키는 BLOCKER, 실제 DB 순단 500/CORS 실패, Alembic head 비재현, 백업 부분성공·무출력 종료가 해소되고 동일 적대 시나리오를 재검증하기 전까지)**
