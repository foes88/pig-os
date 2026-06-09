# PigOS 모바일 API 변경 명세서
> 작성일: 2026-06-09 | 적용 대상: iOS (pigos-ios) + Android (pigos-android)
> 백엔드 기준 커밋: `0adfa23` (main)

---

## 요약 — 우선순위별 작업 목록

| 우선순위 | 항목 | iOS | Android |
|---------|------|-----|---------|
| 🔴 P0 | Sync 포맷 근본 불일치 수정 | 필수 | 필수 |
| 🔴 P0 | `CullRequest` 필드명 수정 | 필수 | 필수 |
| 🟠 P1 | `piglet_events` sync push 추가 | 필수 | 필수 |
| 🟠 P1 | `removals` server pull 처리 추가 | 필수 | 필수 |
| 🟠 P1 | `/boars` 웅돈 API 신규 구현 | 필수 | 필수 |
| 🟡 P2 | `boar_id` 교배 기록에 선택 추가 | 권장 | 권장 |

---

## 1. 🔴 P0 — Sync 포맷 근본 불일치

### 문제

현재 모바일이 보내는 포맷:
```json
{
  "client_id": "device-uuid",
  "last_sync_at": "2026-06-01T00:00:00Z",
  "changes": [
    { "entity": "matings", "operation": "CREATE", "id": "uuid", "payload": {...} }
  ]
}
```

**백엔드가 기대하는 포맷** (`POST /api/v1/farms/{farm_id}/sync`):
```json
{
  "farm_id": "farm-uuid",
  "client_id": "device-uuid",
  "last_sync_at": "2026-06-01T00:00:00Z",
  "dry_run": false,
  "changes": {
    "matings": [ { "id": "uuid", "sow_id": "...", "mating_date": "2026-06-01", ... } ],
    "farrowings": [],
    "weanings": [],
    "reproductive_events": [],
    "health_events": [],
    "piglet_events": []
  }
}
```

### 변경 요점

| 항목 | 기존 (틀림) | 정확한 값 |
|------|-----------|---------|
| `changes` 타입 | `Array<SyncChange>` (배열) | Object (엔티티별 배열을 담은 객체) |
| URL의 `farm_id` | 없음 | Path parameter 필수 `/sync` → `/farms/{farm_id}/sync` |
| `farm_id` 필드 | body에 없음 | body에도 포함 |
| `dry_run` | 없음 | 선택, 기본값 `false` |

---

## 2. 🔴 P0 — Sync 응답(Response) 포맷 불일치

### 백엔드 실제 응답

```json
{
  "sync_token": "2026-06-09T12:00:00Z",
  "dry_run": false,
  "accepted": [
    { "id": "uuid", "entity": "mating", "action": "created" }
  ],
  "rejected": [
    { "id": "uuid", "entity": "mating", "reason": "SOW_NOT_FOUND", "detail": {} }
  ],
  "conflicts": [
    {
      "id": "uuid",
      "entity": "mating",
      "conflict_type": "DUPLICATE_EVENT",
      "client_record": {},
      "server_record": {}
    }
  ],
  "server_changes": {
    "sows": [ { "id": "...", "ear_tag": "A-001", "status": "GESTATING", ... } ],
    "matings": [],
    "farrowings": [],
    "weanings": [],
    "reproductive_events": [],
    "health_events": [],
    "piglet_events": [],
    "removals": [
      { "id": "...", "sow_id": "...", "removal_date": "2026-06-01",
        "removal_type": "CULLED", "reason_category": "AGE", ... }
    ],
    "period_locks": [],
    "deleted_ids": ["uuid1", "uuid2"]
  },
  "require_full_sync": false,
  "stats": { "pushed": 3, "accepted": 3, "rejected": 0, "conflicts": 0, "pulled": 5 }
}
```

### 변경 요점

| 항목 | 기존 (틀림) | 정확한 값 |
|------|-----------|---------|
| `accepted` 타입 | `Array<String>` (UUID 문자열 배열) | `Array<{id, entity, action}>` |
| `rejected` 타입 | `Array<String>` | `Array<{id, entity, reason, detail}>` |
| `server_changes` 타입 | `Array<ServerChange>` (배열) | Object (엔티티별 배열 객체) |
| `server_changes.removals` | 없음 | **신규 추가** — 도폐사 이력 |
| `server_changes.piglet_events` | 없음 | **신규 추가** — 포유자돈폐사 |
| `sync_token` | `syncToken` (카멜케이스) | `sync_token` (스네이크케이스) |
| `require_full_sync` | 없음 | 신규 — `true`면 `last_sync_at=null`로 재전송 |

---

## 3. 🔴 P0 — Push 페이로드 필드명 확인

### `SyncMating` (교배 push)
```json
{
  "id": "client-generated-uuid",
  "sow_id": "uuid",
  "mating_date": "2026-06-01",
  "mating_type": "AI",
  "boar_id": null,
  "semen_batch": null,
  "mating_number": 1,
  "notes": null,
  "client_created_at": "2026-06-01T08:00:00Z"
}
```

### `SyncFarrowing` (분만 push)
```json
{
  "id": "uuid",
  "sow_id": "uuid",
  "farrowing_date": "2026-06-01",
  "total_born": 13,
  "born_alive": 12,
  "born_dead": 1,
  "mummies": 0,
  "farrowing_type": "NORMAL",
  "notes": null,
  "client_created_at": "..."
}
```
> ⚠️ 주의: iOS 코드의 `stillborn` → 서버 필드명은 `born_dead`

### `SyncWeaning` (이유 push)
```json
{
  "id": "uuid",
  "sow_id": "uuid",
  "weaning_date": "2026-06-22",
  "weaned_count": 11,
  "avg_weight_kg": 6.2,
  "notes": null,
  "client_created_at": "..."
}
```

### `SyncReproductiveEvent` (번식이벤트 push)
```json
{
  "id": "uuid",
  "sow_id": "uuid",
  "event_type": "CULLED",
  "event_date": "2026-06-01",
  "notes": null,
  "client_created_at": "..."
}
```
> ⚠️ 주의: **도폐사는 `reproductive_events`에 `event_type: CULLED/DEAD`로 push**한다.
> iOS의 `enqueueCull()`이 `sow UPDATE`로 보내는 건 틀린 패턴.

**`event_type` 허용값:**
`RETURN_TO_ESTRUS | ABORTION | EMPTY | INFERTILE | CULLED | DEAD | TRANSFER_OUT | SOLD | HEAT_DETECTED`

---

## 4. 🔴 P0 — `CullRequest` 필드명 수정

### 기존 (틀림)
```swift
// iOS SowDTO.swift
enum CullType: String, Codable { case cull = "CULL", dead = "DEAD" }

struct CullRequest: Encodable {
    let sowId: String
    let cullType: CullType   // ← 틀림
    let cullDate: String     // ← 틀림
    let reason: String?
}
```

### 정확한 계약 (`POST /api/v1/farms/{farm_id}/sows/{sow_id}/cull`)
```json
{
  "removal_type": "CULLED",
  "removal_date": "2026-06-09",
  "reason_category": "AGE",
  "reason_detail": "노령 도태",
  "body_weight_kg": 185.0,
  "sale_price": 350000,
  "sale_currency": "KRW",
  "notes": null
}
```

**`removal_type` 허용값:** `CULLED | DEAD | SOLD | TRANSFER`

**`reason_category` 허용값:**
`REPRODUCTIVE | LAMENESS | DISEASE | AGE | PERFORMANCE | INJURY | BEHAVIOR | UNKNOWN | OTHER`

---

## 5. 🟠 P1 — `piglet_events` Sync Push 신규 추가

### Push 페이로드 (`changes.piglet_events[]`)
```json
{
  "id": "client-uuid",
  "sow_id": "uuid",
  "farrowing_id": null,
  "event_date": "2026-06-09",
  "event_type": "DEATH",
  "piglet_count": 2,
  "reason": "CRUSHING",
  "target_sow_id": null,
  "notes": null,
  "client_created_at": "2026-06-09T09:30:00Z"
}
```

**`event_type` 허용값:** `STILLBORN_REMOVAL | DEATH | FOSTER_IN | FOSTER_OUT`

**`reason` 허용값:** `CRUSHING | SCOURS | STARVATION | CONGENITAL | HYPOTHERMIA | OTHER`

> 참고: `farrowing_id = null`이면 서버가 해당 모돈의 가장 최근 분만을 자동 조회함.

---

## 6. 🟠 P1 — `removals` Server Pull 처리 신규 추가

`server_changes.removals[]` 배열에서 받은 데이터를 로컬 DB에 저장해야 함.

```json
{
  "id": "uuid",
  "sow_id": "uuid",
  "removal_date": "2026-06-01",
  "removal_type": "CULLED",
  "reason_category": "AGE",
  "reason_detail": null,
  "body_weight_kg": 185.0,
  "sale_price": null,
  "sale_currency": null,
  "created_at": "2026-06-01T10:00:00Z"
}
```

---

## 7. 🟠 P1 — `/boars` 웅돈 API 신규 구현

### GET 목록
```
GET /api/v1/farms/{farm_id}/boars?status=ACTIVE&limit=100
Authorization: Bearer {token}
```

응답:
```json
[
  {
    "id": "uuid",
    "farm_id": "uuid",
    "ear_tag": "B-001",
    "breed": "Duroc",
    "breed_company": "PIC",
    "status": "ACTIVE",
    "entry_date": "2026-01-01T00:00:00Z",
    "entry_type": "PURCHASE",
    "semen_quality": "EXCELLENT",
    "created_at": "2026-01-01T..."
  }
]
```

**`status` 필터 허용값:** `ACTIVE | CULLED | DEAD | TRANSFERRED`

### POST 등록
```
POST /api/v1/farms/{farm_id}/boars
Content-Type: application/json

{
  "ear_tag": "B-002",
  "breed": "Yorkshire",
  "breed_company": "Genesus",
  "entry_date": "2026-06-09",
  "entry_type": "PURCHASE",
  "semen_quality": "GOOD"
}
```

**`entry_type` 허용값:** `PURCHASE | BORN | TRANSFER`
**`semen_quality` 허용값:** `EXCELLENT | GOOD | FAIR | POOR`

### PATCH 상태/품질 수정
```
PATCH /api/v1/farms/{farm_id}/boars/{boar_id}

{
  "status": "CULLED",
  "semen_quality": "FAIR"
}
```

---

## 8. 🟡 P2 — 교배 기록에 `boar_id` 선택 추가

`changes.matings[]`에 `boar_id` 필드 선택적으로 포함 가능.

```json
{
  "id": "uuid",
  "sow_id": "uuid",
  "mating_date": "2026-06-09",
  "mating_type": "AI",
  "boar_id": "웅돈-uuid",
  ...
}
```

---

## 9. 신규 REST 엔드포인트 목록

| 메서드 | URL | 용도 | 추가 시점 |
|--------|-----|------|---------|
| GET | `/api/v1/farms/{id}/boars` | 웅돈 목록 | 이번 세션 |
| POST | `/api/v1/farms/{id}/boars` | 웅돈 등록 | 이번 세션 |
| GET | `/api/v1/farms/{id}/boars/{boar_id}` | 웅돈 상세 | 이번 세션 |
| PATCH | `/api/v1/farms/{id}/boars/{boar_id}` | 웅돈 상태 수정 | 이번 세션 |
| GET | `/api/v1/farms/{id}/events/piglet_events` | 포유자돈폐사 목록 | 이번 세션 |
| POST | `/api/v1/farms/{id}/events/piglet_events` | 포유자돈폐사 기록 | 이번 세션 |
| GET | `/api/v1/farms/{id}/kpi/trend?kpi=psy&months=6` | KPI 월별 추세 | 이전 세션 |

---

## 10. 모바일 수정 체크리스트

### iOS (pigos-ios)

- [ ] `SyncDTO.swift` — `SyncRequest.changes`를 배열→객체로 교체, `farm_id`·`dry_run` 추가
- [ ] `SyncDTO.swift` — `SyncResponse` 재작성 (accepted/rejected/conflicts 타입 변경, server_changes 객체화)
- [ ] `SyncDTO.swift` — `SyncPigletEvent` 구조체 추가
- [ ] `SyncDTO.swift` — `ServerChanges`에 `piglet_events`, `removals` 추가
- [ ] `SyncService.swift` — `buildSyncChanges()` 메서드: 큐 아이템을 엔티티별 배열로 분류
- [ ] `SyncService.swift` — `applyServerChanges(ServerChanges)`: 객체 파라미터로 변경, removals 저장 추가
- [ ] `SyncService.swift` — `applyResult()`: accepted/rejected가 String→Object로 변경
- [ ] `SyncRepository.swift` — `enqueueCull()`: `sow UPDATE` → `reproductive_events`로 변경
- [ ] `SyncRepository.swift` — `enqueuePigletEvent()` 추가
- [ ] `SowDTO.swift` — `CullRequest` 필드명 수정 (removal_type, removal_date, reason_category)
- [ ] `EventForms.swift` — `CullFormView` 수정 (새 필드 반영)
- [ ] 신규 `BoarDTO.swift`, `Boar.swift`, `BoarRepository.swift` 생성
- [ ] `Entities.swift` — `BoarEntity`, `PigletEventEntity`, `SyncEntityType.pigletEvent` 추가

### Android (pigos-android)

- [ ] `SyncRequest` data class — `changes` 타입을 Map → typed object로 변경
- [ ] `SyncResponse` data class — `accepted`/`rejected` 타입 변경, `server_changes` 객체화
- [ ] `ServerChanges` data class — `removals`, `piglet_events` 필드 추가
- [ ] `SyncChanges` data class — `piglet_events` 필드 추가
- [ ] `CullRequest` data class — 필드명 수정
- [ ] `BoarDto`, `BoarRepository` 신규 구현
- [ ] `PigletEventDto`, sync enqueue 메서드 추가
- [ ] Room Entity — `BoarEntity`, `PigletEventEntity` 추가

---

## 참고: 백엔드 코드 위치

| 변경 파일 | 경로 |
|---------|------|
| Sync 스키마 | `api/app/schemas/sync.py` |
| Sync 서비스 로직 | `api/app/services/sync_service.py` |
| 웅돈 라우터 | `api/app/routers/base/boars.py` |
| 웅돈 스키마 | `api/app/schemas/boar.py` |
| 도폐사 스키마 | `api/app/schemas/sow.py` → `SowCullRequest` |
| 이벤트 스키마 | `api/app/schemas/events.py` → `PigletEventCreate` |
