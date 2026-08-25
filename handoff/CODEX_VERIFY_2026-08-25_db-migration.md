# Codex 독립검증 프롬프트 — 2026-08-25 세션 (DB 이전 · 성능 · 에러계약)

> 목적: Claude Opus 5 가 이번 세션에 적용한 수정을 **독립적으로 적대 재검증**.
> 추측 금지 · 창작 금지 · 코드/스펙/실측 근거만. **수정 금지(검증만)** — 결함은 재현절차로 기록.
> 참조: `handoff/VERIFICATION_HANDOFF_for_codex.md` §1(실행법) · §9(이번 세션 상세)

---

## 0. CONTEXT

- repo `C:\dev\PigOS` — 백엔드 `api/`(FastAPI, uv), 프론트 `src/`(Next.js 15)
- **DB 가 바뀌었다**: Supabase 관리형 → 같은 EC2 자체설치 **PostgreSQL 17, 포트 5434**.
  로컬 검증용 DB 는 그대로 `docker compose up -d postgres redis`(운영 아님).
- alembic head = `e2b5d7c9a1f3`
- UI 텍스트 = **8개어**(en/ko/zh/es/vi/th/pt/ru), 1,774키

### ⚠️ 환경 함정 — 모르면 "테스트가 깨졌다"고 오판한다

1. **프론트 테스트가 기본 Node(v20.11.1)로는 한 개도 안 돈다.**
   vitest→rolldown 이 `node:util`의 `styleText`(Node 20.12+)를 요구해 시작 전에 죽는다.
   ```bash
   cd src && export PATH="$APPDATA/nvm/v22.11.0:$PATH"
   node node_modules/vitest/vitest.mjs run tests/apiErrors.test.ts tests/i18n.test.ts \
        --environment node --pool=threads      # 기대 34 passed
   ```
   `--environment node` 없으면 jsdom 이 `ERR_REQUIRE_ESM` 로, `--pool=threads` 없으면
   forks 워커가 안 뜬다.
2. **`tsc` 가 `Fatal process out of memory: Zone` 이면 시스템 메모리 부족**이다
   (힙 옵션 무관. Docker 내리고 재시도). **반드시 exit code 확인** — 빈 출력이 통과가 아니다.
   ```bash
   cd src && npx tsc --noEmit; echo "exit=$?"
   ```
3. 백엔드: `cd api && uv run pytest tests/ -q` → 기대 **1136 passed, 1 skipped**.
   `uv run ruff check app tests` → 기존 9건(다른 파일의 미사용 import·변수)은 이번 변경분 아님.

---

## 1. 재검증 대상 (커밋별 — 의도대로인지 + 우회·회귀 없는지)

### `c262f5f` farrowings by-sow 인덱스 (대시보드 5.67s → 0.57s)

주장: `_NPD_SQL` 의 `lact_open` LATERAL 이 모돈마다 `MAX(farrowing_date)` 를 조회하는데
`farrowings` 에 `(sow_id, farrowing_date)` 인덱스가 없어 3,691ms 를 썼다.

- [ ] **인덱스가 실제로 그 노드에 쓰이는가.** `EXPLAIN (ANALYZE, BUFFERS)` 로 확인.
      `idx_farrowings_farm_sow`(farm_id 선행)로도 충분했던 것은 아닌지 — 즉 **중복 인덱스**가 아닌지.
- [ ] **쓰기 비용**: farrowings 는 52만행이고 이벤트 등록 경로에서 자주 INSERT 된다.
      인덱스 하나 추가의 쓰기 오버헤드가 수용 가능한지.
- [ ] **NPD 값이 정말 불변인가.** 인덱스는 값에 영향이 없어야 한다 —
      `tests/integration/test_npd_*.py` 로 전후 값 동일성 확인.
- [ ] 마이그레이션 `IF NOT EXISTS` 라 **프로덕션에 수동 생성된 인덱스와 충돌하지 않는지**,
      `downgrade` 가 안전한지.

### `7417b01`(도입) → 후속 커밋(제거) WEI 뷰 fast-path ★ **TZ 전수 점검이 본론**

경위: `as_of == 오늘`이면 `v_sow_npd` 를 쓰는 최적화를 넣었다가 **같은 세션에 되돌렸다.**
프로덕션에는 나가지 않았다. 되돌린 이유 ②가 이 항목의 핵심이다:

```
API 컨테이너 TZ = UTC        (date.today())
DB TZ          = Asia/Seoul  (CURRENT_DATE / now())
```

매일 **00:00~09:00 KST 9시간** 동안 DB 날짜가 컨테이너보다 하루 앞선다.

- [ ] **위 TZ 불일치를 먼저 재확인**하라(운영·로컬 각각). 사실이 아니면 여기부터 보고.
- [ ] ★ **전수 점검**: `date.today()`/`datetime.now()`(컨테이너 TZ)와
      `CURRENT_DATE`/`now()`/`current_date`(DB TZ)가 **한 계산 안에 섞이는 곳**을 찾는다.
      섞이면 같은 방식으로 하루가 어긋난다. 우선 의심 대상:
      - `get_dashboard` 의 `week_start = today - timedelta(days=today.weekday())`
        → 이번주 교배/분만/이유 건수. 9시간 창에서 주 경계가 어긋나는가?
      - 알림·리포트 기간 경계, 월마감(`period_locks`) 판정
      - `calculate_psy` / `calculate_npd` 의 `ref_date`
- [ ] 어긋난다면 **어느 쪽이 옳은지**도 판단해서 제시하라(농장 현지 TZ? UTC? DB TZ?).
      PigOS 는 8개 법역 다국가 서비스다 — "KST 기준"이 기본값인 게 맞는지 자체가 질문이다.
      `farms` 에 타임존 컬럼이 있는지, 있다면 왜 안 쓰는지 확인.
- [ ] 가드 테스트 `tests/unit/test_npd_calc_path_isolation.py` 가 **실제로 재도입을 막는지**
      (fast-path 를 되살려 보고 빨간불이 뜨는지 확인).

### `fa1ef3d` 에러 종류 정형화

- [ ] **catch-all `Exception` 핸들러의 부작용**: Starlette 에서 이걸 등록하면 다른 미들웨어
      (CORS·캐시 무효화)를 우회하는지. **CORS 헤더가 빠져 브라우저에서 에러 본문을 못 읽게 되는지** 확인.
- [ ] `OperationalError` → 503 매핑이 **너무 넓지 않은지**. SQLAlchemy 는 여러 상황을
      `OperationalError` 로 감싼다 — 코드 결함(예: 잘못된 SQL)이 503("재시도하세요")으로
      둔갑하면 진짜 버그가 묻힌다. 어떤 하위 에러가 여기 걸리는지 열거.
- [ ] **정보 누출**: 스택·쿼리·스키마명이 응답 어디에도 없는지(헤더 포함).
- [ ] `request_id` 가 **로그에 실제로 남는지**(로깅 설정이 WARNING 이상만 받으면 `logger.error`
      는 남지만 포맷에 없을 수 있다). 남지 않으면 추적 ID 가 무의미하다.
- [ ] 프론트 `resolveApiError`: 401 이 **토큰 갱신 인터셉터와 충돌하지 않는지**
      (`lib/api/client.ts` 가 401 에서 refresh 후 재시도한다 — 그 경로가 먼저 타는지).
- [ ] 8개어 번역 **품질**(기계번역 티·업계 용어). 특히 **th·vi·ru**.

### `de4e68d` `e530dca` 백업

- [ ] `backup_db.sh` 의 대상 선택(`DATABASE_URL` 우선, 6543 이면 `MIGRATION_DATABASE_URL`)이
      **모든 조합에서 라이브 DB 를 고르는지**.
- [ ] `set -euo pipefail` 아래에서 **조용히 죽는 지점이 더 없는지**
      (`ls` glob 하나로 스크립트가 죽었던 전례가 있다).
- [ ] S3 실패가 **백업 자체를 실패로 만들지 않는지**(로컬 백업은 남아야 한다).
- [ ] 보존 정리 `find ... -mtime +7 -delete` 가 **S3 사본까지 지우지는 않는지**(지우면 안 된다).

---

## 2. 중점 적대 시나리오 (NO-GO 후보)

1. **자정 경계**: 23:59:59 와 00:00:01 에 대시보드를 호출해 NPD 가 튀지 않는지.
   컨테이너 TZ 와 DB TZ 가 다르면 여기서 터진다.
2. **미래 날짜 주입**: sync 페이로드로 `mating_date = 내일` 을 밀어 넣고
   (a) 거부되는지 (b) 통과한다면 뷰/인라인 값이 갈리는지.
3. **DB 순단**: DB 를 잠깐 내리고 요청 → **503 + Retry-After** 인지(500 이면 결함).
   복구 후 자동으로 정상화되는지(풀이 죽은 커넥션을 붙잡지 않는지).
4. **테넌트 격리 회귀**: 인덱스·fast-path 변경이 `farm_id` 필터를 우회하지 않는지 —
   A 농장 자격으로 B 농장 KPI 조회.
5. **표시 정책**: `d1a4c6e8b2f5` 적용 후 **미결정 국가에서 3개만** 나오는지,
   `compute_enabled` 는 14개 전부 유지인지(숨김 ≠ 계산 중단).

---

## 3. 판단 기준

- **결함 등급**: BLOCKER(데이터 오염·격리 붕괴·값 위조) / MAJOR(오동작) / MINOR(문구·정리)
- **BUG vs DATA vs CONFIG** 를 구분한다.
- 수치가 필요한데 근거가 없으면 **창작하지 말고 "미확보"로 표기 후 STOP**.
- Opus 수정 중 **불완전 / 우회 가능 / 회귀 유발** 항목을 명시. 깨끗하면 "확인됨".

## 4. 산출물

`handoff/CODEX_RESULT_2026-08-25.md` 에:

```
[등급] [영역] 제목
  재현: <명령 또는 절차>
  기대: <근거가 되는 스펙/코드 위치>
  실제: <관측>
  분류: BUG | DATA | CONFIG
```

마지막에 **한 줄 판정**: `GO` / `조건부 GO(조건 명시)` / `NO-GO(사유)`
