# PigOS 검증 핸드오프 (→ Codex)

> 작성: 2026-06-25 · **갱신: 2026-08-25** (DB 이전 · 성능 · 에러계약 반영)
>
> ⚠️ **6월 판의 전제 두 개가 무효다.**
> ① DB 가 Supabase 가 아니다 → **같은 EC2 의 자체설치 PostgreSQL 17**(§9).
> ② UI 텍스트가 7개어가 아니라 **8개어**(ru 추가, 1,774키).
>
> 원 작성 세션: Claude Opus 4.8 (1M)
> 목적: 밤샘 QA + 정합성 수정 + i18n/단위/통화 작업의 **검증 내역**을 Codex 세션이 이어받아 참조하도록 전달.
> 원칙: 데이터 **정합성 최우선**(꼬임 금지) · KPI/손실값 위조 금지 · 한국어=admin 전용 · UI텍스트=**8개어** 동시.

---

## 0. TL;DR (2026-08-25 기준)

- **운영 정상.** web/api 200, 대시보드 **0.57초**, 에러 로그 0건.
- **게이트**: 백엔드 `pytest 1136 passed, 1 skipped` · 프론트 `vitest 34 passed`(신규분)
  · `tsc 0 errors` · i18n **8개어 1,774키 누락 0**.
- alembic head = **`e2b5d7c9a1f3`** (프로덕션 marker 동일).
- 사람 결정 대기: Entitlement Matrix 결재 · S3 버킷 수명주기 설정.

### 6월 판에서 달라진 것 (읽기 전 확인)

| 항목 | 2026-06-25 | 2026-08-25 |
|---|---|---|
| DB | Supabase 관리형(풀러) | **EC2 자체설치 PG17, 포트 5434** |
| 언어 | 7개어 1,337키 | **8개어 1,774키**(ru 추가) |
| 백엔드 테스트 | 488 | **1136** |
| alembic head | `b3d5f7091a2c` | **`e2b5d7c9a1f3`** |
| 프론트 테스트 | `npm run test:run` | **기본 Node 로 실행 불가** — §1 |

---

## 1. 검증 실행 방법 (재현용) — ★ 2026-08-25 실측으로 갱신

```bash
# 백엔드 (로컬 Docker postgres 필요 — 운영 DB 아님)
cd c:/dev/PigOS && docker compose up -d postgres redis
cd api && uv run pytest tests/ -q          # 기대: 1136 passed, 1 skipped
cd api && uv run ruff check app tests      # 기존 9건(다른 테스트 파일) 외 신규 0
```

```bash
# 타입체크
cd c:/dev/PigOS/src && npx tsc --noEmit    # 기대: 0 errors
```

### ★ 프론트 테스트는 기본 Node 로 **실행되지 않는다** (환경 문제, 코드 문제 아님)

이 머신의 기본 Node 는 **v20.11.1** 인데 vitest 가 쓰는 rolldown 이 `node:util` 의
`styleText` 를 요구한다(**Node 20.12+**). 그래서 `npm run test:run` 은 테스트가 하나도
돌기 전에 `SyntaxError: ... does not provide an export named 'styleText'` 로 죽는다.
**이걸 모르면 "테스트가 전부 깨졌다"고 오판한다.**

nvm 에 v22.11.0 이 설치돼 있다. 시스템 기본을 바꾸지 말고 그 바이너리로 직접 돌린다:

```bash
cd c:/dev/PigOS/src
export PATH="$APPDATA/nvm/v22.11.0:$PATH"
node node_modules/vitest/vitest.mjs run tests/apiErrors.test.ts tests/i18n.test.ts \
     --environment node --pool=threads
# 기대: 34 passed (apiErrors 26 + i18n 8)
```

- `--environment node` — 기본 jsdom 은 `html-encoding-sniffer` 의 `ERR_REQUIRE_ESM` 로 죽는다.
  DOM 이 필요 없는 테스트는 이걸로 우회한다.
  **컴포넌트 테스트(`tests/components/*`)는 이 방법으로 못 돈다 — 미해결 과제다.**
- `--pool=threads` — 기본 forks 풀이 이 조합에서 worker 를 못 띄운다.

### ⚠️ 메모리 (이번에 실제로 당한 함정)

`tsc` 가 `Fatal process out of memory: Zone` 으로 죽으면 **힙 옵션 문제가 아니라 시스템
메모리 부족**이다(VS Code 다중 창 + Docker Desktop). `--max-old-space-size` 를 올려도
해결되지 않는다. Docker 를 내리고 재시도한다.

★ 2026-08-25 에 이 상태의 **빈 출력을 "통과"로 오독**했다가 진짜 타입 버그를 놓칠 뻔했다
(`code && BY_CODE[code]` 가 빈 문자열을 kind 로 만드는 버그). **exit code 를 반드시 확인한다.**

```bash
npx tsc --noEmit; echo "exit=$?"     # 0 이 아니면 통과가 아니다
```

> ⚠️ Docker Desktop 이 간헐적으로 다운된다. pytest 에서 대량 `setup ERROR` 가 나오면
> 코드 문제가 아니라 postgres 연결 끊김이다. `docker compose up -d postgres redis` 후 재실행.

### i18n 파리티 (툴체인 없이 확인하는 법)

```bash
cd c:/dev/PigOS && python - <<'PY'
import io, json, os
langs = ["en","ko","zh","es","vi","th","pt","ru"]
def flat(d, p=""):
    out = {}
    for k, v in d.items():
        key = f"{p}.{k}" if p else k
        out.update(flat(v, key)) if isinstance(v, dict) else out.update({key: v})
    return out
data = {l: flat(json.load(io.open(f"src/messages/{l}.json", encoding="utf-8"))) for l in langs}
ref = set(data["en"])
for l in langs:
    miss, extra = ref - set(data[l]), set(data[l]) - ref
    print(l, len(data[l]), "누락", len(miss), "초과", len(extra))
PY
# 기대: 전부 1774 / 누락 0 / 초과 0
```

---

## 2. 정합성 버그 5건 (밤샘 QA 발견 → 수정 완료)
회귀테스트: `api/tests/integration/test_integrity_fixes.py`

| ID | 심각도 | 증상 | 근본원인 | 수정 |
|----|--------|------|----------|------|
| **INTEG-1** | 🔴 블로커 | 현실적 길이 ear_tag(예: `KR-FARM-SOW-0001-2025` 21자)로 **이유(weaning) 시 500** → 사이클 데드락 | 자돈그룹 `group_code` 생성식 `WG-{date}-{ear_tag}-{id}`가 `VARCHAR(30)` 초과 | `event_service.py` → `WG-{weaning_date:%y%m%d}-{id[:8]}` 로 단축 |
| **C3** | 🟠 | 포유두수보다 많은 FOSTER_OUT 허용 → **음수 포유두수** | 전출 시 잔여 포유 capacity 미검증 | `record_piglet_event` DEATH/FOSTER_OUT capacity 가드 + 라벨 |
| **TENANT#1** | 🟠 | 양자(foster) target이 **타 농장** 모돈 지정 가능 | target_farrowing_id 농장 소속 미검증 | foster 블록에 farm 소속 검증 추가 |
| **INTEG-2** | 🟡 | 분만율(farrowing_rate)에 **soft-delete된 교배/분만 포함** | count 쿼리에 `deleted_at IS NULL` 누락 | `get_dashboard` 카운트에 `Mating/Farrowing.deleted_at.is_(None)` 추가 |
| **BUG-3** | 🟡 | 이유 삭제 후 자동생성 자돈그룹이 **유령 재고로 잔존** | delete_weaning이 그룹 미정리 | 매칭 `WG-{date}-{id[:8]}` PigletGroup soft-delete |

> 삭제 시 sow.status 롤백 규칙(검증됨): mating삭제 PREGNANT→OPEN · farrowing삭제 LACTATING→PREGNANT · weaning삭제 OPEN→LACTATING.

---

## 3. 단위/통화 (QA #6) — 사실 데이터 시드
이전: `market_defaults`/`region_defaults`가 비어 **모든 국가 kg/USD 폴백** → 미국 농장도 kg 표시되는 버그.
수정: alembic `b3d5f7091a2c` 로 국가별 **ISO 사실값** 시드 (추정 KPI 아님).

```
US:lb/USD  KR:kg/KRW  CN:kg/CNY  VN:kg/VND  TH:kg/THB  PH:kg/PHP  BR:kg/BRL  MX:kg/MXN
```
- resolve 우선순위: country → region_defaults → market_defaults → 하드코딩(kg/USD).
- `schemas/farm.py CURRENCY_SYMBOLS` 에 `MXN: "Mex$"` 추가.

---

## 4. i18n / 번역 (~~7개어~~ → **8개어**, ru 추가 · 1,774키)
- **공개어 6**: en/zh/es/vi/th/pt · **admin 전용 1**: ko (`admin.` 호스트에서만 노출, `i18n/request.ts` 게이팅).
- `src/messages/*.json` 7파일 **각 1337키, 누락 0** (검증됨).
- 이번 작업분: onboarding 페이지 전체 현지화(이전 전부 영어 하드코딩) · BottomNav th/pt 추가 · 임신감정(pregnancy-check) 키 · 자돈 연령별 폐사(pigletByAge) 키.
- 규칙: UI 텍스트 추가/변경 시 **7파일 동시 갱신 필수**.

---

## 5. Rule Engine 현황 (참고)
- **40룰** 운영 라이브(이전 8 → PigPlan 참조로 확장). 도메인: reproduction7·litter12·grow_finish3·sow_herd6·boar1·loss4·composite2·batch1·health/inventory2.
- 임계 해석 우선순위: `rule_configs(operator)` → `benchmarks/default_metric_values(country/region scope)` → 코드 기본값 (`engine/rules/_common.py resolve()`).
- **국가차이는 시드데이터로만** 처리 (`if country==` 하드코딩 금지).
- 카탈로그: `docs/RULE_ENGINE_CATALOG.md`.
- **데이터 없으면 룰은 [] 반환**(경보 안 만듦) — 위조 금지 원칙. benchmark 미시드 → 침묵 = PASS.

---

## 6. 남은 작업 (비블로커 폴리시 — 이월)
1. **#7b 챗 cause/action 코드 현지화** — 비영어에서 raw snake_case 노출(~80코드×7어). 챗 보조화면, Addon 인접. 가장 가치 높은 잔여 i18n.
2. **M3 / F4 PigPlan 패리티(LOW)** — M3=AI 방식 슬롯 시퀀스 검증, F4=사인별 폐사 25 상한. 집계 경계는 이미 유지됨(마진).
3. **PeriodLockedError 409→423 데드코드 정리**(외형, 실동작 423 정상).

## 7. 사람 결정 대기 2건
- **국가 KPI 수치(앵커마켓)**: 1차자료(PigCHAMP/Agriness/AHDB/한돈팜스) 수치 확보 후 verified 시드. **위조 금지 — 사용자가 자료 가져오는 중.** 설계도: `handoff/.../PROMPT_kpi_benchmark_structure.md` + `docs/verification/2026-06-24_country_kpi_audit.md`(Q1~10).
- **DB 티어**: 현재 Supabase **무료**로 출시 → 가입자 증가 시 Pro($25/8GB) 전환(코드 0, DATABASE_URL 동일). auto-pause는 worker 일일 cron(KPI집계/알림)이 DB를 쳐서 사실상 방지됨. 한도 500MB·백업7일만 모니터링.

---

## 8. 배포 메모 (운영 = 공유 EC2 52.78.65.6, ubuntu, key: C:\dev_env\keyfile\wiselake-app-key.ppk)

> ⚠️ **2026-08-25 이후**: DB 는 Supabase 가 아니라 같은 EC2 의 PG17(포트 5434)이다.
> 배포는 `ops/deploy.sh [api|web|worker]`(백업·롤백태그·헬스체크 포함)를 쓴다.
> **alembic 단계는 deploy.sh 에 없다 — 수동이다.** 마이그레이션을 추가했으면
> 이미지 재빌드까지 해야 `alembic current` 가 리비전을 찾는다(§9-1).
- pigos는 docker compose(web:3010·api:8010·worker·redis), 호스트 nginx가 프록시. pigsignal/dawoon/topic-lab/pigos-landing와 **포트·nginx 분리** — 건드리지 말 것.
- DB = Supabase pooler. **운영 alembic은 빌드 이후 실행**(이미지 갱신 후) — 순서 틀리면 마이그레이션 누락(b3d5f7091a2c 한번 누락→재적용한 전례).
- 배포 순서: tar(api+src, `--exclude='.venv*'`) → scp → extract → build → up → **빌드 후 alembic upgrade** → force-recreate → 3도메인 200 스모크.
- ⚠️ **worker는 `pigos-worker` 자체 이미지**(compose `worker.build: ./api`, api와 별개). 백엔드 코드 바꾸면 **`build api` + `build worker` 둘 다** 해야 worker에 반영됨. `build api`만 하고 `up worker` 하면 worker는 옛 코드 유지(2026-06-25 db_keepalive 배포 시 이 함정으로 2회 헛돌았음).
- docker 명령은 prod에서 **sudo 필요**. compose 파일 2개 항상 같이: `-f docker-compose.prod.yml -f docker-compose.deploy.yml`.

---

## 9. 2026-08-25 세션 — DB 이전 · 성능 · 에러계약

> 이 절이 6월 판의 DB·인프라 서술을 **대체**한다.

### 9-1. DB 이전 (Supabase 관리형 → EC2 자체설치)

**비용 절감이 아니라 운영 불가 때문이다.** Supavisor 풀러가 단계적으로 악화되다가
`ConnectionDoesNotExistError: connection was closed in the middle of operation`
— **쿼리 실행 도중** 연결을 끊는 상태가 됐다. 앱에서 고칠 수 없다.

| 항목 | 값 |
|---|---|
| DB | PostgreSQL **17.11**, 같은 EC2(52.78.65.6) 자체설치 |
| 포트 | **5434** ⚠️ 5432 는 타 프로젝트 PG16(`dawoon_dev`·`topic_lab`)이 쓴다 |
| 접속 | 컨테이너 `172.18.0.1:5434` / 호스트 도구 `127.0.0.1:5434` |
| 노출 | 도커 브리지만 ufw 허용 — **인터넷 비노출** |
| 백업 | `~/pigos-backups/` 크론 + **S3 `pigos-db-backup`** (IAM 역할 `pigos-ec2-backup-role`) |

실측 비교:

| 지표 | Supabase 풀러 | EC2 로컬 PG17 |
|---|---|---|
| 커넥션 획득 + `SELECT 1` | 쿼리 도중 절단 | **0.001s** |
| 동일 143M 전체 덤프 | **67분 35초** | 29초 |
| 로그인 | 17초 / 500 | 0.34초 |
| 동시 클라이언트 한도 | 15 | 200 |

**데이터 손실 0 확정** — Supabase 마지막 쓰기 08:26:12 KST, 덤프 09:43 보다 1h17m 전.
근거는 `audit_log`(`after_dump = 0`)이고, REST 이벤트·오프라인 sync·모돈 등록
**모든 쓰기 경로가 같은 트랜잭션에 AuditLog 를 남기는 것**을 코드로 확인했다.

정본 문서: `docs/INFRA_DB_STRATEGY.md` · 장애 대응: `ops/ROLLBACK.md`

### 9-2. 대시보드 5.67초 → 0.57초

★ **DB 를 옮기고도 느렸다 — 원인이 둘이었고 하나만 고친 상태였다.**

`_NPD_SQL` 의 `lact_open` LATERAL 이 모돈마다 `MAX(farrowing_date)` 를 조회하는데
`farrowings` 에만 `(sow_id, farrowing_date)` 인덱스가 없어 단일 노드에서 **3,691ms** 를 썼다
(`matings`·`weanings` 는 2026-07 에 같은 이유로 이미 받았고 farrowings 만 누락).

| | 전 | 후 |
|---|---|---|
| NPD (10,251두) | 5.447s | **0.269s** |
| NPD (1,508두, 중앙값) | 2.634s | **0.056s** |
| `get_dashboard` | 5.673s | **0.570s** |

인덱스만 추가했고 쿼리·정의는 불변 → **NPD 값 불변**. 마이그레이션 `e2b5d7c9a1f3`.

### 9-3. WEI 뷰 fast-path — **시도했다가 되돌림** (재시도 금지)

`as_of == 오늘`인 핫패스에서만 `v_sow_npd` 를 쓰는 최적화를 넣었다가 **같은 세션에서
되돌렸다. 프로덕션에는 나가지 않았다.** 되돌린 이유 둘 다 남긴다 — 그럴듯해서 또 나온다.

**① 이득이 없다.** farrowings by-sow 인덱스 추가 후 프로덕션 실측:

| 농장 | 인라인 | 뷰 |
|---|---|---|
| 10,251두 | 0.030s | 0.029s |
| 1,508두(중앙값) | 0.011s | 0.011s |

값도 동일했다. 느렸던 건 `_NPD_SQL` 의 `lact_open`(3.7s)이지 이 쿼리가 아니었다.

**② 틀릴 수 있고, 테스트로는 못 잡힌다.**
등가성 전제는 "뷰의 `CURRENT_DATE` == `as_of`" 인데 운영 실측은:

```
API 컨테이너 TZ = UTC        (date.today())
DB TZ          = Asia/Seoul  (CURRENT_DATE)
```

★ 매일 **00:00~09:00 KST 9시간** 동안 DB 날짜가 하루 앞선다. 그 창에서 뷰의 cap 조건이
`weaning_date <= as_of - 59` 로 느슨해져, 이유 후 59일 된 모돈이 하루 일찍 cap 60 으로
잡히고 평균 WEI 가 달라진다. **테스트 환경은 두 TZ 가 같아 재현되지 않는다** —
"테스트가 통과했으니 등가"라는 근거가 성립하지 않는 종류의 결함이었다.

가드: `api/tests/unit/test_npd_calc_path_isolation.py` — 값 비교가 아니라
**계산 SQL 이 뷰·CURRENT_DATE 를 참조하지 않는다는 구조**를 잠근다.

> 🔎 **Codex 확인 요망**: 이 TZ 불일치가 fast-path 말고 **다른 곳에도 영향을 주는지.**
> `date.today()`(컨테이너=UTC)와 `CURRENT_DATE`/`now()`(DB=KST)가 한 계산 안에 섞이면
> 같은 방식으로 하루가 어긋난다. 특히 "이번주 이벤트 건수"(`get_dashboard` 의 week_start),
> 알림·리포트 기간 경계, 월마감 판정. **전수 grep 이 필요하다.**

### 9-4. 에러 계약

예상 못 한 예외에 `code` 가 없어서 프론트가 "일시적 장애 / 진짜 버그 / 네트워크 끊김"을
구분하지 못하고 전부 `Server error. Please try again.` 하나로 보여주고 있었다.

- 백엔드 `app/core/exceptions.py`: catch-all + `request_id`, DB 장애는 **503 DB_UNAVAILABLE**
  로 분리(500 과 섞으면 "재시도하면 되는 상황"과 "코드 결함"이 뭉친다).
- 프론트 `src/lib/api/errors.ts`: `resolveApiError` — code 우선 → status 폴백 → generic.
- 계약 테스트: `api/tests/unit/test_error_contract.py`(19) · `src/tests/apiErrors.test.ts`(26)

### 9-5. 이 세션 커밋

| 커밋 | 내용 |
|---|---|
| `c262f5f` | farrowings by-sow 인덱스 — 대시보드 5.67s → 0.57s |
| `7417b01` | WEI 뷰 fast-path + 등가성 회귀 테스트 |
| `fa1ef3d` | 에러 종류 정형화(백엔드 code 계약 + 프론트 매퍼 + 8개어) |
| `de4e68d` | 백업 대상을 라이브 DB 로 (죽은 Supabase 를 백업할 뻔했다) |
| `e530dca` | S3 오프사이트 백업 활성화 |
| `640b745` `ea13fd7` | 롤백 런북 개정 + 복원 리허설 절차 |
| `694ff1a` | 인프라 전략 개정 + 커넥션 예산 테스트 교체 |

### 9-6. 알려진 미해결

1. **컴포넌트 테스트 실행 불가** — jsdom 환경이 `ERR_REQUIRE_ESM` 로 죽는다(§1).
   `--environment node` 로는 DOM 테스트를 못 돌린다. 의존성 정리 필요.
2. **S3 복원 경로 미검증** — 업로드는 확인했으나 다운로드가 훅 정책(AWS 조회만 허용)에
   막혀 `head-object` 크기 대조까지만 했다.
3. **버킷 수명주기·버전관리 미설정** — 매일 143MB 누적(1년 ≈ 52GB).
4. **이중화 부재** — DB 가 죽으면 복구 시간만큼 서비스 정지.
5. ruff 기존 경고 9건(다른 테스트 파일의 미사용 import·변수). 이번 변경분은 clean.
