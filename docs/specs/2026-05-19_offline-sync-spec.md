# PigOS — 오프라인 동기화 프로토콜 v1.0
> 2026-05-19

---

## 1. 설계 목표

| 목표 | 설명 |
|------|------|
| **데이터 무결성** | 충돌 발생 시 조용히 덮어쓰지 않는다 |
| **멱등성** | 같은 sync 요청을 N번 보내도 결과가 동일하다 |
| **원자성 (per-item)** | 한 레코드가 실패해도 나머지는 정상 처리된다 |
| **감사 추적** | 모든 sync 결과는 `sync_logs` + `audit_log`에 기록된다 |
| **충돌 가시성** | 충돌은 앱에서 사용자에게 반드시 표시되고, 조용히 버려지지 않는다 |

---

## 2. 충돌 시나리오 전체 목록

### 2-1. 중복 이벤트 (DUPLICATE_EVENT)
**상황**: 작업자가 오프라인 중 교배 기록. 다른 작업자가 같은 기간 온라인에서 동일 모돈 교배 기록.

| 케이스 | 판단 기준 | 처리 |
|--------|-----------|------|
| sow_id + event_date + event_type 동일, 타임스탬프 1시간 이내 | 동일 사건으로 간주 | **LWW (최신 기록 유지)** — 멱등 처리 |
| sow_id + event_type 동일, date 다름 | 다른 이벤트 | **CONFLICT 반환** — 사용자 판단 필요 |
| sow_id + event_date 동일, type 다름 | 다른 종류 | 둘 다 accept |

### 2-2. 월마감 잠금 위반 (PERIOD_LOCKED)
**상황**: 작업자가 오프라인 중 4월 데이터 입력. sync 시점에 4월이 이미 잠금됨.

→ **무조건 REJECT**. 사용자에게 "2026-04는 잠금됨" 메시지 표시. 관리자가 잠금 해제 후 재sync.

### 2-3. 존재하지 않는 모돈 (SOW_NOT_FOUND)
**상황**: 오프라인 중 A-001 건강 이벤트 기록. 서버에서는 A-001이 이미 폐사/소프트딜리트됨.

→ **REJECT**. 클라이언트에 최신 모돈 상태 전송. 앱에서 "해당 모돈이 삭제되었습니다" 표시.

### 2-4. 모돈 상태 불일치 (STATUS_CONFLICT)
**상황**: 오프라인 중 분만 기록. 서버에서는 해당 모돈이 이미 도태 처리됨.

| 시도 이벤트 | 서버 상태 | 처리 |
|-------------|-----------|------|
| 교배 기록 | LACTATING | REJECT (임신 중 교배 불가) |
| 분만 기록 | CULLED | REJECT |
| 이유 기록 | GESTATING | REJECT |
| 교배 기록 | ACTIVE / WEANED | ACCEPT |

→ **REJECT + 현재 서버 상태 전송**. 앱에서 사용자가 확인 후 재입력 또는 취소.

### 2-5. 번식 사이클 충돌 (CYCLE_CONFLICT)
**상황**: 오프라인 중 교배 기록. 서버에서는 해당 모돈 동일 사이클에 이미 다른 교배 존재.

| 케이스 | 처리 |
|--------|------|
| 동일 교배일, 동일 정액 배치 | ACCEPT (멱등) |
| 동일 교배일, 다른 정액 배치 | CONFLICT — 어떤 게 맞는지 사용자 판단 |
| 다른 교배일, mating_number 중복 | CONFLICT |

### 2-6. 미래 날짜 이벤트 (FUTURE_DATE)
**상황**: 클라이언트 시계가 잘못 설정되어 미래 날짜로 이벤트 생성.

→ `event_date > server_now + 1day` 이면 **REJECT**.

### 2-7. 오래된 클라이언트 데이터 (STALE_CLIENT)
**상황**: 오프라인 기간이 너무 길어 (> 30일) sync_token이 만료됨.

→ 전체 풀 싱크 강제. 클라이언트에 `require_full_sync: true` 반환.

---

## 3. 동기화 프로토콜

### 흐름
```
Mobile (WatermelonDB)
    │
    │ 1. 변경사항 수집 (sync_queue)
    │
    ▼
POST /api/v1/sync
    {
      farm_id, client_id, last_sync_at,
      changes: { matings[], farrowings[], weanings[], health_events[], ... }
    }
    │
    │ 2. 서버 검증 (per-item)
    │    ├─ 기간 잠금 체크
    │    ├─ 모돈 존재 & 상태 체크
    │    ├─ 중복 체크
    │    └─ 미래 날짜 체크
    │
    │ 3. 결과 반환
    ▼
Response:
    {
      sync_token: "2026-05-19T12:00:00Z",  ← 다음 sync의 last_sync_at
      accepted: [{ id, entity }],
      rejected: [{ id, entity, reason, detail }],
      conflicts: [{ id, entity, conflict_type, server_record }],
      server_changes: { sows[], matings[], ... }  ← 서버에서 변경된 것들
    }
```

### 방향
| 방향 | 설명 |
|------|------|
| **PUSH** | 클라이언트 → 서버 (새 이벤트 전송) |
| **PULL** | 서버 → 클라이언트 (last_sync_at 이후 변경사항 수신) |
| **단일 엔드포인트** | `POST /api/v1/sync` 한 번에 양방향 처리 |

---

## 4. 충돌 해소 규칙 (Resolution Rules)

| conflict_type | 자동 처리 | 사용자 개입 |
|---------------|-----------|-------------|
| DUPLICATE_EVENT (1h 이내) | LWW 자동 merge | 불필요 |
| DUPLICATE_EVENT (날짜 다름) | - | 필요 — 앱에서 선택 |
| PERIOD_LOCKED | 자동 REJECT | 관리자 잠금 해제 필요 |
| SOW_NOT_FOUND | 자동 REJECT | 확인 후 재입력 |
| STATUS_CONFLICT | 자동 REJECT + 서버 상태 전송 | 확인 후 재입력 |
| CYCLE_CONFLICT (동일 배치) | LWW 자동 merge | 불필요 |
| CYCLE_CONFLICT (다른 배치) | - | 필요 |
| FUTURE_DATE | 자동 REJECT | 날짜 수정 후 재시도 |
| STALE_CLIENT | 풀싱크 강제 | 불필요 |

---

## 5. 엔티티별 sync 대상

| 엔티티 | sync 방향 | 충돌 위험도 |
|--------|-----------|-------------|
| matings | 양방향 | 높음 |
| farrowings | 양방향 | 높음 |
| weanings | 양방향 | 높음 |
| reproductive_events | 양방향 | 높음 |
| sows (status만) | 서버→클라 only | - |
| health_events | 양방향 | 중간 |
| feed_records | 양방향 | 낮음 |
| kpi_snapshots | 서버→클라 only | - |
| period_locks | 서버→클라 only | - |

---

## 6. 클라이언트 ID & 멱등 키

- 디바이스별 고정 UUID: `client_id` (앱 설치 시 생성, 로컬 저장)
- 각 레코드는 **클라이언트에서 UUID 생성** → 서버가 그대로 사용
- 동일 UUID로 재전송 시 서버는 멱등 처리 (이미 있으면 ACCEPT + 기존 레코드 반환)

---

## 7. sync_token 관리

```
last_sync_at = 마지막 성공한 sync의 서버 시각 (UTC)
                                                   ↑
                                       서버가 sync_token으로 반환

클라이언트는 sync_token을 로컬 저장.
다음 sync 요청 시 last_sync_at으로 전송.
서버는 last_sync_at 이후 변경된 데이터만 반환 (server_changes).
```

- 만료 기준: `last_sync_at < NOW() - 30days` → `require_full_sync: true`

---

## 8. 오류 코드

| code | HTTP | 의미 |
|------|------|------|
| PERIOD_LOCKED | 423 (item-level) | 해당 기간 잠금 |
| SOW_NOT_FOUND | 404 (item-level) | 모돈 없음/삭제 |
| STATUS_CONFLICT | 409 (item-level) | 모돈 상태 불일치 |
| DUPLICATE_EVENT | 409 (item-level) | 중복 이벤트 |
| CYCLE_CONFLICT | 409 (item-level) | 번식 사이클 충돌 |
| FUTURE_DATE | 422 (item-level) | 미래 날짜 |
| REQUIRE_FULL_SYNC | 200 (response flag) | 풀싱크 필요 |
| FARM_ACCESS_DENIED | 403 | 농장 접근 권한 없음 |

---

## 9. 보안 고려사항

- sync 요청은 반드시 JWT 인증 + farm membership 검증
- `client_id`는 farm과 바인딩 → 다른 농장 데이터 주입 불가
- 대용량 sync (> 1000 items): 분할 전송 권고, 서버는 max 500 items/request 제한
- 모든 sync 결과는 `sync_logs` 테이블에 기록 (direction, records_pushed, records_pulled, conflicts)
