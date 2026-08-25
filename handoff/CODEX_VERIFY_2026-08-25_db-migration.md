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
3. 백엔드: `cd api && uv run pytest tests/ -q` → 기대 **1163 passed, 1 skipped**.
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

### `7417b01`(도입) → `26a28d2`(제거) WEI 뷰 fast-path

`as_of == 오늘`이면 `v_sow_npd` 를 쓰는 최적화를 넣었다가 **같은 세션에 되돌렸다.**
프로덕션에는 나가지 않았다. 되돌린 근거 두 가지를 검증하라.

- [ ] **이득이 없다는 주장**: 프로덕션 실측 1만두 인라인 0.030s / 뷰 0.029s. 재측정하라.
- [ ] **틀릴 수 있다는 주장**: 뷰의 `CURRENT_DATE`(DB=Asia/Seoul)와 `as_of`(컨테이너=UTC)가
      어긋난다. 아래 TZ 항목과 같은 뿌리다.
- [ ] 가드 `tests/unit/test_npd_calc_path_isolation.py` 가 **실제로 재도입을 막는지**
      (fast-path 를 되살려 보고 빨간불이 뜨는지).

### `011c972` `bfa8774` ★★ 타임존 — 이번 세션 최대 변경

**운영 중이던 결함 두 개**를 고쳤다. 컨테이너는 UTC 로 뜨는데 농장은 자기 현지 날짜로
사건을 기록한다. 프로덕션 농장 tz: UTC 47 · Asia/Seoul 12 · America/Chicago 4 ·
America/Mexico_City 3 · Asia/Manila 1.

| 결함 | 재현 | 영향 |
|---|---|---|
| ① 입력 거부 | 서울 2026-08-26 07:00 → 입력 `08-26` vs `date.today()`(UTC) `08-25` → "cannot be in the future" | 서울 12농장이 매일 **00:00~09:00 등록 불가** |
| ② 주 경계 밀림 | 시카고 일요일 19:00 → 서버는 이미 월요일 → 대시보드 '이번주'가 다음 주 | 일요일 저녁 실적이 **0으로 보임** |

- [ ] **두 결함을 먼저 재현하라.** 재현이 안 되면 전제가 틀린 것이니 거기서 보고.
- [ ] ★ **놓친 경로가 있는가.** `date.today()`/`datetime.now()` 를 전수로 다시 훑고,
      각각이 (a) 사용자에게 보이는 날짜인지 (b) 농장 맥락이 있는지 판정하라.
      특히 `period_locks` 월마감 판정, 알림 잡, 리포트 기간 경계.
- [ ] **안 고친 것의 근거가 타당한가** — 이쪽이 더 중요하다:
      - `sync_service._is_future_date`: "최대 오프셋 UTC+14 이므로 TOLERANCE=1 이 정확히
        덮는다"고 주장한다. **UTC+14 가 맞는가**(Kiribati/Line Islands), DST 로 +15 가
        되는 지역은 없는가. 틀리면 sync 도 같은 결함이 있다.
      - `kpi_policy_resolver.ref`: "정책 발효일은 회사 기준이라 농장 현지로 바꾸면
        오히려 틀린다"고 주장한다. **이 논리가 맞는가** — 반례를 찾아보라.
- [ ] **KPI 값이 바뀌는가.** `ref_date` 가 하루 달라질 수 있다. 비-UTC 농장에서 수정
      전후 PSY/NPD 를 비교하라. 바뀐다면 **바뀌는 게 맞는지**까지 판정하라(옳은 방향인가).
- [ ] `jobs/kpi.py` 가 농장별 기간으로 바뀌었다. **같은 농장에 중복 스냅샷**이 생기거나
      `_upsert_snapshot` 의 유니크 키와 충돌하지 않는가. 잡 1회 실행 시간이 늘지 않는가.
- [ ] `farm_today` 의 UTC 폴백이 **결함을 조용히 숨기지 않는가** — tz 오타가 있는 농장은
      예전 동작으로 되돌아간다. 로그·경고가 필요한가?

### `32b032d` 계정 삭제 `DELETE /auth/me` — iOS 심사 블로커

익명화 방식(행 보존 + 식별값 파기), 농장은 `active=false`, 비밀번호 재확인 필수.

- [ ] ★ **삭제 후 정말로 접근이 불가능한가.** access token 은 만료 전까지 유효하다 —
      `active=false` 만으로 기존 토큰이 차단되는지 `get_current_user` 경로를 확인하라.
      **차단되지 않으면 토큰 수명만큼 삭제된 계정이 살아 있다 = BLOCKER.**
- [ ] **재가입 후 예전 데이터에 접근되는가** — 같은 이메일로 다시 가입했을 때 이전
      계정의 농장·감사이력과 연결이 생기면 안 된다.
- [ ] **소유 판정이 맞는가**: `role_override or user.role in (FARM_OWNER, OWNER)`.
      조직 계층 역할(`effective_farm_role`)로 소유자인 사용자를 놓치지 않는가 —
      놓치면 그 농장은 비활성화되지 않고 orphan 이 된다.
- [ ] **부분 실패**: 중간에 예외가 나면 트랜잭션이 통째로 롤백되는가. 라우터가
      `await db.commit()` 을 서비스 밖에서 한다 — flush 만 하고 커밋 전 실패 시 상태.
- [ ] **동시 요청**: 같은 계정으로 DELETE 를 두 번 보내면? 두 번째는 어떻게 되는가.
- [ ] `consent_ledger` 를 남긴다. **처리방침 제9조가 실제로 이를 허용하는가**
      (`[OPEN — COUNSEL]` 표기 상태다). 남긴 항목·기간이 방침에 명시돼 있는가.
- [ ] **앱 문구 충돌**: 앱은 "영구 삭제, 복구 불가"를 약속하는데 서버는 법정보존
      5년/3년·동의증빙을 남긴다. 어느 쪽을 고쳐야 하는지 판정하라.

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
2. **미래 날짜 주입**: sync 페이로드로 `mating_date = 내일` 을 밀어 넣고 거부되는지.
   REST 는 농장 현지 기준으로 바뀌었고 sync 는 서버+1일 여유다 — **두 경로의 판정이
   달라지는 조합**을 찾아라(같은 이벤트가 한쪽은 통과, 한쪽은 거부).
2b. **삭제된 계정의 잔존 토큰**: DELETE /auth/me 직후 기존 access token 으로 API 호출 →
   차단되는가. 안 되면 BLOCKER.
3. **DB 순단**: DB 를 잠깐 내리고 요청 → **503 + Retry-After** 인지(500 이면 결함).
   복구 후 자동으로 정상화되는지(풀이 죽은 커넥션을 붙잡지 않는지).
4. **테넌트 격리 회귀**: 인덱스·fast-path 변경이 `farm_id` 필터를 우회하지 않는지 —
   A 농장 자격으로 B 농장 KPI 조회.
5. **표시 정책**: `d1a4c6e8b2f5` 적용 후 **미결정 국가에서 3개만** 나오는지,
   `compute_enabled` 는 14개 전부 유지인지(숨김 ≠ 계산 중단).
6. **자정 경계 × 농장 tz**: Asia/Seoul 농장으로 08:59 / 09:01 KST 에 이벤트 등록과
   대시보드 조회를 하고 값이 튀지 않는지. 시카고 농장으로 18:59 / 19:01 CDT 도 동일.

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
