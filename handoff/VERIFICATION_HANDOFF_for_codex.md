# PigOS 검증 핸드오프 (→ Codex)

> 작성: 2026-06-25 · 작성자 세션: Claude Opus 4.8 (1M)
> 목적: 밤샘 QA + 정합성 수정 + i18n/단위/통화 작업의 **검증 내역**을 Codex 세션이 이어받아 참조하도록 전달.
> 원칙: 데이터 **정합성 최우선**(꼬임 금지) · KPI/손실값 위조 금지 · 한국어=admin 전용 · UI텍스트=7개어 동시.

---

## 0. TL;DR (현재 상태)
- **출시 블로커 0건.** 밤샘 QA에서 터질 뻔한 블로커(INTEG-1) 포함 정합성 버그 5건 발견 → 전부 수정·회귀테스트·**운영 배포 완료**.
- **재검증 결과(2026-06-25)**: `pytest 488 passed` · i18n 7개어 1337키 **누락 0** · 단위/통화 국가별 정상.
- 남은 건 **비블로커 폴리시 3건**(이월) + 사람 결정 2건(국가 KPI 수치 / DB 티어).
- 운영 3도메인 모두 200: `app.pigos.io/login` · `api.../health` · `admin.pigos.io/login`. alembic head = `b3d5f7091a2c`.

---

## 1. 검증 실행 방법 (재현용)
```bash
# 백엔드 (Docker postgres + pigos_test 필요)
cd c:/dev/PigOS && docker compose up -d postgres redis
cd api && uv run pytest tests/ -q          # 기대: 488 passed
# 타입체크
cd c:/dev/PigOS/src && npx tsc --noEmit    # 기대: 0 errors
# i18n 키 패리티: en 1337키 기준 ko/zh/es/vi/th/pt 누락 0
# 단위/통화 시드 확인
docker exec pigos-postgres psql -U pigos -d pigos -c \
  "SELECT region_code,weight_unit,currency_code FROM region_defaults ORDER BY region_code;"
```
> ⚠️ 환경 주의: 이 환경의 **Docker Desktop이 간헐적으로 다운**됨. pytest에서 대량 `setup ERROR`(예: 199 errors)가 나오면 코드 문제가 아니라 **postgres 연결 끊김**. Docker 재기동 → `docker compose up -d postgres redis` → `pg_isready` 확인 후 재실행하면 488 통과.

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

## 4. i18n / 번역 (7개어)
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
- pigos는 docker compose(web:3010·api:8010·worker·redis), 호스트 nginx가 프록시. pigsignal/dawoon/topic-lab/pigos-landing와 **포트·nginx 분리** — 건드리지 말 것.
- DB = Supabase pooler. **운영 alembic은 빌드 이후 실행**(이미지 갱신 후) — 순서 틀리면 마이그레이션 누락(b3d5f7091a2c 한번 누락→재적용한 전례).
- 배포 순서: tar(api+src, `--exclude='.venv*'`) → scp → extract → build → up → **빌드 후 alembic upgrade** → force-recreate → 3도메인 200 스모크.
- ⚠️ **worker는 `pigos-worker` 자체 이미지**(compose `worker.build: ./api`, api와 별개). 백엔드 코드 바꾸면 **`build api` + `build worker` 둘 다** 해야 worker에 반영됨. `build api`만 하고 `up worker` 하면 worker는 옛 코드 유지(2026-06-25 db_keepalive 배포 시 이 함정으로 2회 헛돌았음).
- docker 명령은 prod에서 **sudo 필요**. compose 파일 2개 항상 같이: `-f docker-compose.prod.yml -f docker-compose.deploy.yml`.
