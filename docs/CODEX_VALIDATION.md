# PigOS — Codex 교차검증 체크리스트

> **목적**: 이 문서는 Codex(또는 다른 AI)가 PigOS 코드베이스를 독립적으로 검증할 수 있도록 작성된 점검 목록입니다.
> 각 항목을 직접 코드를 읽어서 확인하고, 이상 발견 시 구체적인 파일 경로와 줄 번호와 함께 보고하세요.

---

## 1. 백엔드 API 계약 — 프론트엔드 타입 정합성

### 1-A. `LoginResponse` 필드 일치 확인

| 확인 항목 | 백엔드 파일 | 프론트 파일 |
|----------|-----------|-----------|
| `access_token`, `refresh_token`, `token_type`, `expires_in` | `api/app/schemas/auth.py` → `LoginResponse` | `src/types/api.types.ts` → `LoginResponse` |
| `user_id`, `name`, `email`, `role`, `farm_ids` | 위 동일 | 위 동일 |

**확인 포인트**:
- 프론트 `LoginResponse`에 `expires_in` 필드가 없다. 인터셉터에서 토큰 만료 계산에 쓰이는지 확인할 것.
- `src/lib/api/client.ts` 인터셉터가 `expires_in`을 사용하면 런타임 오류 가능.

---

### 1-B. `FarrowingResponse` — `mating_id` NOT NULL vs UI 선택 없이 분만 기록

**백엔드 DB 모델** (`api/app/db/models/events.py`):
```python
mating_id: Mapped[UUID] = mapped_column(..., nullable=False)  # NOT NULL
```

**백엔드 스키마** (`api/app/schemas/events.py`):
```python
class FarrowingCreate:
    mating_id: UUID | None = None  # 선택적
```

**확인 포인트**:
1. `api/app/services/event_service.py` → `record_farrowing()` 함수를 읽어서, `mating_id=None`일 때 **최근 교배를 자동 조회**하는지 확인.
2. 자동 조회 없이 `None`을 DB에 INSERT하면 `NOT NULL` 제약 위반으로 500 오류 발생.
3. 자동 조회 로직이 있다면 OK. 없으면 버그 — `mating_id`를 `Optional`로 바꾸거나 자동 조회 추가 필요.

---

### 1-C. `WeaningResponse` — `farrowing_id` NOT NULL 동일 문제

**백엔드 스키마** (`api/app/schemas/events.py`):
```python
class WeaningCreate:
    farrowing_id: UUID | None = None  # 선택적

class WeaningResponse:
    farrowing_id: UUID  # 비옵셔널 — None이면 직렬화 실패
```

**확인 포인트**:
- `event_service.record_weaning()`이 `farrowing_id=None`일 때 최근 분만을 자동 조회하는지 확인.
- `WeaningResponse`가 `farrowing_id: UUID | None`이어야 하는지 검토.

---

### 1-D. `Farrowing` 필드명 — 프론트 vs 백엔드 `FarrowingResponse`

| 필드 | 프론트 타입 (`api.types.ts`) | 백엔드 스키마 (`schemas/events.py`) |
|------|---------------------------|---------------------------------|
| `stillborn` | ✅ | ✅ `stillborn` |
| `mummified` | ✅ | ✅ `mummified` |
| `farrowing_ease` | `"EASY"\|"ASSISTED"\|"DIFFICULT"\|null` | `str \| None` |

**확인 포인트**:
- `/farrowing` 페이지가 `f.stillborn`을 렌더링하는지 확인 (`src/app/(app)/farrowing/page.tsx`).
- 실제 `FarrowingResponse`에 `stillborn` 필드가 포함되는지 — 누락되면 항상 0으로 표시.

---

### 1-E. Sync 계약 — `SyncChanges.piglet_events` 누락

**백엔드** (`api/app/schemas/sync.py`):
```python
class SyncChanges:
    piglet_events: list[SyncPigletEvent] = []  # 최근 추가
```

**프론트 타입** (`src/types/api.types.ts`):
```typescript
// 방금 추가됨:
piglet_events?: SyncPigletEvent[];
```

**확인 포인트**:
- `src/lib/api/endpoints/sync.ts`에서 `SyncChanges` 타입을 올바르게 import하는지 확인.
- Sync push 로직에서 `piglet_events`가 포함되는지 확인.

---

### 1-F. `ServerChanges` — `piglet_events`, `removals` 최근 추가 확인

**백엔드** (`api/app/schemas/sync.py`):
```python
class ServerChanges:
    piglet_events: list[dict] = []
    removals: list[dict] = []
```

**프론트 타입** (`src/types/api.types.ts`):
```typescript
// 방금 추가됨:
piglet_events: Record<string, unknown>[];
removals: Record<string, unknown>[];
```

**확인 포인트**:
- `src/lib/api/endpoints/sync.ts`의 응답 처리 코드가 새 필드를 무시 없이 처리하는지 확인.

---

## 2. 사업 로직 검증

### 2-A. 모돈 상태 전환 규칙

모든 상태 전환은 `api/app/services/event_service.py`에 있어야 한다.

| 이벤트 | 허용 선행 상태 | 결과 상태 |
|--------|-------------|---------|
| 교배 (mating) | ACTIVE, WEANED, DRY | GESTATING |
| 분만 (farrowing) | GESTATING | LACTATING, parity+1 |
| 이유 (weaning) | LACTATING | WEANED |
| 귀환발정 (RETURN_TO_ESTRUS) | any | ACTIVE |
| 공태 (EMPTY) | any | DRY |
| 도태 (CULLED/DEAD/SOLD) | any | CULLED/DEAD/SOLD |

**확인 포인트**:
1. 각 `record_*` 함수에서 선행 상태 체크가 존재하는지 확인.
2. 비허용 상태에서 이벤트 기록 시 적절한 에러 코드(`STATUS_CONFLICT`)가 반환되는지 확인.
3. `record_reproductive_event()`에서 `CULLED/DEAD` 시 `sow.deleted_at`이 설정되는지 확인.

---

### 2-B. `_process_farrowing` 상태 체크 — sync 경로

`api/app/services/sync_service.py` → `_process_farrowing()`:
```python
if sow.status != "GESTATING":
    return None, SyncRejected(...)
```

**확인 포인트**:
- `record_farrowing` (event_service 경로)는 어떤 상태 체크를 하는가? sync와 일치하는가?
- 두 경로(직접 API vs sync)에서 상태 전환 로직이 다르면 버그.

---

### 2-C. KPI 계산 — NPD/PSY/FR 공식 검증

**파일**: `api/app/engine/rules/base.py` 또는 `api/app/jobs/kpi.py`

**공식** (검증 기준: `docs/specs/2026-03-19_kpi-calculation-specs.md`):
```
PSY = (연간 이유두수) / (평균 활성 모돈수)
NPD = 비번식일 / 모돈 수 (낮을수록 좋음)
FR  = 분만수 / 교배수
```

**확인 포인트**:
1. `kpi.py`의 계산 로직이 위 공식과 일치하는지 확인.
2. 분모가 0일 때 ZeroDivisionError가 발생하지 않는지 — `if n == 0: return None` 패턴 확인.
3. `kpi_snapshots` 테이블이 존재하는지, ARQ 잡이 실제로 기록하는지 확인.

---

### 2-D. 교배-분만 사이클 완결성

`api/app/db/models/events.py`의 `BreedingCycle` 모델이 있다면:

**확인 포인트**:
- `record_mating()` → `BreedingCycle` 생성 또는 재사용하는지 확인.
- `record_farrowing()` → `BreedingCycle`에 연결하는지 확인.
- `record_weaning()` → `BreedingCycle.closed_at` 업데이트하는지 확인.
- 사이클 미완결 시 NPD 계산에서 누락되는 모돈이 생기는지 확인.

---

## 3. DB 모델 vs 마이그레이션 정합성

### 3-A. `Removal` 모델 — `updated_at` 컬럼 존재 여부

**확인 포인트**:
- `api/app/db/models/health.py` → `Removal` 모델에 `updated_at` 컬럼이 있는가?
- `sync_service.py`의 `_pull_server_changes()`에서 `Removal` 조회 시 `updated_at` 대신 `created_at`을 기준으로 쓰는지 확인 (실제 코드 확인).

---

### 3-B. `PigletEvent` 모델 — `deleted_at` 존재 여부

**파일**: `api/app/db/models/events.py`

**확인 포인트**:
- `PigletEvent` 모델에 `deleted_at` 컬럼이 있는가?
- `_pull_server_changes()`에서 `p.deleted_at`으로 필터링하는데 컬럼이 없으면 AttributeError 발생.

---

### 3-C. `Boar` 모델 — `updated_at` 컬럼

**파일**: `api/app/db/models/sow.py`

**확인 포인트**:
- `Boar` 모델에 `updated_at` 컬럼이 있는지 확인.
- 없으면 PATCH 응답이 변경 시각을 추적하지 못함.

---

## 4. 보안 — Multi-tenant 격리

### 4-A. 모든 쿼리에 `farm_id` 필터 존재

**확인 파일**: `api/app/routers/base/` 의 모든 라우터

**확인 포인트**: 각 GET/POST/PATCH 엔드포인트가 반드시 `FarmDep`을 사용하고, 조회 조건에 `farm_id == farm.id`가 포함되는지 확인.

특별히 확인할 파일:
- `boars.py` — `list_boars`, `get_boar`, `update_boar` 모두 `Boar.farm_id == farm.id` 확인
- `events.py` — `list_matings`, `list_farrowings`, `list_weanings`, `list_piglet_events` 모두 확인
- `sows.py` — `GET /sows/{sow_id}` 에서 타 농장 모돈 조회 불가한지 확인

**버그 패턴**:
```python
# 위험: farm_id 없이 ID만으로 조회
sow = await db.get(Sow, sow_id)  # farm_id 미검증!

# 안전:
sow = await db.scalar(select(Sow).where(Sow.id == sow_id, Sow.farm_id == farm.id))
```

---

### 4-B. `AuditLog`에 `user_id` 누락 없는지

**확인 포인트**: `boars.py`의 `create_boar`/`update_boar`가 `current_user.id`를 AuditLog에 포함하는지 확인 (현재 `user_id` 파라미터 없이 작성된 경우 있음).

---

## 5. 타입스크립트 타입 안전성

```bash
# 프로젝트 루트에서 실행
cd src && npx tsc --noEmit
```

**알려진 허용 에러**: 없어야 함 (이전 세션에서 0 에러 확인)

**확인 포인트**:
- `src/app/(app)/farrowing/page.tsx`에서 `f.stillborn` 접근이 `Farrowing` 타입에 맞는지
- `src/lib/api/endpoints/sync.ts`의 `SyncChanges` import가 새 `piglet_events`를 포함하는지

---

## 6. Sync 프로토콜 엣지 케이스

### 6-A. `last_sync_at = null` (최초 동기화)

**파일**: `api/app/services/sync_service.py` → `_pull_server_changes()`

**확인 포인트**:
```python
if since is None:
    return ServerChanges()  # 빈 응답 반환 — 올바른가?
```
- 최초 동기화 시 서버의 기존 데이터를 모두 내려줘야 하는 것 아닌지 검토.
- 현재는 `since=None`이면 빈 `ServerChanges` 반환 — 신규 디바이스는 데이터를 받지 못함.
- 의도된 설계라면 OK (온보딩 시 별도 full-pull API 필요), 버그라면 `since = datetime(2000, 1, 1)` 처리 필요.

---

### 6-B. `require_full_sync = True` 처리

**확인 포인트**:
- 클라이언트가 `require_full_sync: true` 응답을 받았을 때 재전송하는 로직이 있는가?
- `src/lib/api/endpoints/sync.ts`에서 응답의 `require_full_sync` 필드를 처리하는지 확인.

---

## 7. 실행 가능한 검증 명령

```bash
# 백엔드 lint (E501 제외)
cd api && uv run ruff check --select=F,E1,E2,E3,E4,E7,E9,W app/

# 백엔드 unit test
cd api && uv run pytest tests/ --ignore=tests/integration -q

# 프론트 타입체크
cd .. && npx tsc --noEmit

# OpenAPI vs 실제 라우터 비교
# docs/api/openapi-v1.yaml 의 paths와 main.py의 include_router 목록 비교
```

---

## 8. 우선순위 요약

| 우선순위 | 항목 | 예상 위험도 |
|---------|------|-----------|
| P0 | 1-B: mating_id NOT NULL 검증 | DB 오류 (500) |
| P0 | 1-C: farrowing_id NOT NULL 검증 | DB 오류 (500) |
| P0 | 3-B: PigletEvent.deleted_at 존재 여부 | AttributeError (500) |
| P1 | 2-A: 상태 전환 규칙 직접 API vs sync 일치 여부 | 데이터 정합성 |
| P1 | 4-A: farm_id 격리 전수검사 | 보안 (테넌트 간 데이터 노출) |
| P1 | 6-A: last_sync_at=null 처리 | 모바일 초기화 실패 |
| P2 | 2-C: KPI 계산 공식 검증 | 잘못된 KPI 표시 |
| P2 | 1-A: expires_in 미사용 확인 | 토큰 만료 미감지 |
