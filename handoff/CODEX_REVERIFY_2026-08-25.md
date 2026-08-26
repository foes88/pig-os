# Codex 재검증 프롬프트 — NO-GO 지적 15건 수정분

> 목적: `CODEX_RESULT_2026-08-25.md` 의 **BLOCKER 1 · MAJOR 12 · MINOR 2** 에 대한 수정이
> (a) 실제로 고쳤는지 (b) **새 결함을 만들지 않았는지** 를 적대적으로 재검증.
> 추측 금지 · 창작 금지 · 코드/실측 근거만. **수정 금지(검증만)**.
>
> 이전 보고서는 정확했다. 특히 "통합 테스트가 `create_all()` 을 써서 드리프트를 숨긴다",
> "오탐 6건이 진짜 드리프트 6건을 묻고 있었다"는 지적이 결정적이었다. 같은 강도로 봐 달라.

---

## 0. CONTEXT

- repo `C:\dev\PigOS` — 백엔드 `api/`(FastAPI, uv), 프론트 `src/`(Next.js 15)
- 수정 커밋: `32b032d`(삭제 API) · `8476d16`(해시 fail-closed) · `200b27e`(BLOCKER) ·
  `90d5534`(MAJOR 12 + MINOR 2)
- alembic head = **`f3c6a8d0b2e4`** (드리프트 보정 마이그레이션 신설)

### 실행 (이전 보고서 §환경 과 동일 + 갱신된 수치)

```bash
cd api && uv run pytest tests/ -q              # 기대 1179 passed, 1 skipped
cd api && uv run alembic check                 # 기대 "No new upgrade operations detected."
cd api && uv run alembic upgrade head && uv run alembic downgrade -2 && uv run alembic upgrade head
```

```bash
cd src && export PATH="$APPDATA/nvm/v22.11.0:$PATH"
node node_modules/vitest/vitest.mjs run tests/i18n.test.ts tests/apiErrors.test.ts \
     --environment node --pool=threads         # 기대 34 passed
NODE_OPTIONS="--max-old-space-size=8192" node node_modules/typescript/lib/tsc.js --noEmit
```

⚠️ 기본 Node(20.11)로는 vitest 가 안 뜨고, `tsc` 는 힙을 안 올리면 `Zone` OOM 으로 죽는다.
**빈 출력은 통과가 아니다 — exit code 를 봐라.**

---

## 1. BLOCKER 수정 — 삭제 화면 (`200b27e`)

버튼에 `onClick` 이 없었고 `ownerOnly` 가 일반 구성원을 막고 있었다.

- [ ] **실제로 호출되는가.** `/settings/delete-account` 에서 확인문구 + 비밀번호를 넣고
      눌렀을 때 `DELETE /api/v1/auth/me` 가 나가는가. 성공 시 세션이 비워지고 `/login` 으로 가는가.
- [ ] ★ **axios DELETE 본문이 실제로 전송되는가.** `apiClient.delete(url, {data})` 로 보냈다.
      프록시·서버가 DELETE 본문을 버리면 서버는 422(비밀번호 누락)를 낸다.
      **네트워크 레벨에서 본문이 붙는지** 확인하라. 안 붙으면 이 수정은 무의미하다.
- [ ] **비소유자가 정말 지울 수 있는가.** FARM_WORKER/VIEWER 로 화면 진입·삭제 완주.
- [ ] 403(비밀번호 불일치)이 "권한 없음"이 아니라 비밀번호 문구로 뜨는가.
      나머지 오류는 `resolveApiError` 문구 + request_id 가 뜨는가.
- [ ] **문구가 서버 동작과 일치하는가** (8개어). `deleteAccount` 블록에서 `recovery`·`l4`·
      `ownerOnly` 를 지우고 `keptTitle`/`k1~k3` 를 넣었다. **지울 수 없는 것을 지운다고
      말하는 문구가 아직 남아 있는가.** 특히 `l1~l3` 와 실제 삭제 대상 대조.

---

## 2. 스키마 드리프트 (`90d5534`)

`f3c6a8d0b2e4` 신설 + 모델 선언 5개 + `env.py` 비교 제외 3개.

- [ ] ★ **제외 목록이 진짜 드리프트를 가리지 않는가** — 여기가 이번 수정의 최대 위험이다.
      `alembic/env.py` 의 `_UNCOMPARABLE_INDEXES` 3개가 **정말 원리적으로 대조 불가**인지
      각각 확인하라(부분 인덱스 / 표현식 인덱스). 하나라도 비교 가능하다면
      "check 를 통과시키려고 숨긴 것"이 된다.
- [ ] **빈 DB 에서 base → head 로 올린 스키마**가 `create_all()` 결과와 같은가.
      `alembic check` 는 현재 DB 기준이라 이 왕복을 안 본다. 직접 비교하라.
- [ ] `f3c6a8d0b2e4` 를 **운영 스냅샷 복사본**에 적용해 보라. NOT NULL 13건 중
      실제 NULL 이 있는 컬럼이 있으면 UPDATE 가 먼저 도는지, 실패 시 트랜잭션이 온전한지.
- [ ] `downgrade` 가 인덱스·컬럼을 지우지 않는다. **의도한 비대칭**인데,
      그 결과 downgrade 후 재-upgrade 가 안전한지(멱등).
- [ ] `pilot_signups.email` 의 `unique=True` 를 걷었다. **애플리케이션 레벨에서 중복
      가입이 뚫리지 않는가** — 유일성은 `lower(email)` 인덱스가 강제하는데, 대소문자
      다른 이메일이 이제 어떻게 처리되는지 확인하라(이전보다 느슨해졌는가?).

---

## 3. 에러 계약 (`90d5534`)

연결 실패를 예외 체인으로 판정 + 500/503 에 CORS 직접 부착.

- [ ] ★ **실제 DB 를 내리고** 로그인 → 503 · `DB_UNAVAILABLE` · `Retry-After` · **CORS 있음**.
      복구 후 정상화. 이전 재현 절차 그대로.
- [ ] ★ **체인 판정이 너무 넓지 않은가.** `_is_db_connection_failure` 가
      `ConnectionError`·`TimeoutError` 를 잡는다. **DB 와 무관한** 코드 결함
      (예: 외부 API 호출 타임아웃, 소켓 오류)이 503 으로 둔갑하면 진짜 버그가 묻힌다.
      그런 경로가 실제로 있는지 찾아라 — 있으면 MAJOR 다.
- [ ] `_cors_headers` 의 Origin 검증이 **와일드카드 우회**를 허용하지 않는가.
      비프로덕션에서 `allow_origins=["*"]` 인데 credentials 도 true 다 — 위험한 조합인지 판단.
- [ ] 500 응답에 여전히 스택·SQL·비밀 문자열이 없는가(헤더 포함).

---

## 4. 타임존 (`90d5534`)

feed 경로 · PSY 기본연도 · tz 검증 · sync/REST 통일 · 스냅샷 기간.

- [ ] ★ **sync/REST 판정 통일 방식이 안전한가.** `process_sync` 가 농장 기준일을
      **ContextVar** 로 넘기도록 했다. ContextVar 는 async 태스크 경계에서 새는·안 새는
      규칙이 미묘하다 — **동시에 여러 농장의 sync 가 처리될 때 서로 값이 섞이지 않는가.**
      섞이면 A농장 기준으로 B농장 이벤트를 판정한다(BLOCKER 급).
      설정되지 않았을 때의 폴백이 무엇인지도 확인하라.
- [ ] **스냅샷이 매일 돌면서 중복·과부하를 만들지 않는가.** 주간·월간을 매일 실행으로
      바꿨다. `_upsert_snapshot` 은 SELECT 후 INSERT 라 **원자적이지 않다**(이전 보고서 지적).
      매일 실행 × 농장 수만큼 도는데 동시 실행 시 경합이 나는가. 잡 1회 소요시간은?
- [ ] `_last_completed_period` 의 경계: 월초·연초·윤년·DST 전환일.
- [ ] **PSY 기본연도**를 None 으로 받게 바꿨다. year 를 생략한 요청이 실제로 농장 현지
      연도를 쓰는가. 명시한 요청은 그대로인가.
- [ ] **timezone 검증**을 추가했다. 기존 운영 데이터 5종이 전부 통과하는가.
      검증 실패 시 어떤 응답인가(422?). 기존 농장 수정 시 막히지 않는가.
- [ ] 폴백 경고가 **값 단위 1회**만 나는가(로그 폭주 방지) — 그러면서도 놓치지 않는가.

---

## 5. 계정 삭제 (`90d5534` · `8476d16`)

고아 농장(active join) · 해시 fail-closed.

- [ ] **고아 농장이 정말 안 생기는가.** active 사용자만 세도록 했다.
      조직 계층 역할(`effective_farm_role`)로만 접근 가능한 사용자는 `user_farms` 행이
      없을 수 있다 — 그런 사용자가 있는 농장을 **비활성화해 버리지 않는가**(반대 방향 결함).
- [ ] `verify_password` fail-closed 가 **정상 인증을 약화시키지 않는가**.
      깨진 해시로 로그인이 되면 안 되고, 정상 해시는 그대로여야 한다.
- [ ] 삭제 후 **기존 access token** 차단(이전 지적). 실제 요청으로 확인하라 —
      테스트는 `get_current_user` 소스에 "active" 문자열이 있는지만 본다(구조 검사).

---

## 6. 백업 (`90d5534`)

grep 무출력 종료 · 증분 부분 성공.

- [ ] `MIGRATION_DATABASE_URL` 만 있는 env, 둘 다 없는 env, 6543 만 있는 env —
      **각각 의도한 메시지와 exit code** 가 나오는가.
- [ ] 증분: 테이블 하나 실패 시 **exit 1 + 파일명에 `-INCOMPLETE`**. 그 파일이 S3 에
      올라가는가(올라가야 하나?) — **부분 백업을 올리는 게 맞는 설계인지** 판단해 달라.
- [ ] 성공 경로가 회귀하지 않았는가(정상 백업이 여전히 exit 0 · S3 업로드).

---

## 7. 새로 생긴 위험 (자유 탐색)

이번 수정은 **8개 파일 이상의 동작을 바꿨다.** 지적 목록에 없던 회귀를 찾아 달라.
특히:

- KPI 값이 바뀌었는가(TZ·스냅샷 기간 변경). 바뀌었다면 **바뀌는 게 맞는가**.
- 테넌트 격리가 유지되는가.
- `governance_today()` 도입으로 정책 발효 시점이 바뀌었다 — 이미 발효된 정책이
  다시 미발효로 돌아가는 경우는 없는가.

---

## 8. 산출물

`handoff/CODEX_RESULT_2026-08-25_REVERIFY.md` 에 이전과 같은 형식.
각 항목을 **[해결] / [부분해결(사유)] / [미해결] / [새 결함]** 으로 판정하고,
마지막에 한 줄: `GO` / `조건부 GO(조건)` / `NO-GO(사유)`.
