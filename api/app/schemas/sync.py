"""
Offline sync schemas — request / response contract.

Design principles:
  - Client generates UUIDs → server idempotency
  - Per-item result (accepted / rejected / conflict) — not all-or-nothing
  - dry_run=true → validate only, no DB writes
  - sync_token → server clock for next last_sync_at
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

# ── Push payloads (client → server) ──────────────────────────────────────────

class SyncMating(BaseModel):
    id: UUID
    sow_id: UUID
    mating_date: str          # ISO date "2026-05-01"
    mating_type: str          # AI | NATURAL
    boar_id: UUID | None = None
    semen_batch: str | None = None
    mating_number: int = 1
    notes: str | None = None
    client_created_at: datetime


class SyncFarrowing(BaseModel):
    id: UUID
    sow_id: UUID
    farrowing_date: str
    total_born: int
    born_alive: int
    born_dead: int = 0
    mummies: int = 0
    farrowing_type: str = "NORMAL"
    notes: str | None = None
    client_created_at: datetime


class SyncWeaning(BaseModel):
    id: UUID
    sow_id: UUID
    weaning_date: str
    weaned_count: int
    avg_weight_kg: float | None = None
    notes: str | None = None
    client_created_at: datetime


class SyncReproductiveEvent(BaseModel):
    id: UUID
    sow_id: UUID
    # 스키마 하드제약 대신 _process_reproductive에서 항목별 검증(배치 전체 422 방지) — Codex P1
    event_type: str
    event_date: str
    notes: str | None = None
    client_created_at: datetime


class SyncHealthEvent(BaseModel):
    id: UUID
    sow_id: UUID | None = None   # None = herd-level event
    event_date: str
    disease_code: str | None = None
    vaccine_code: str | None = None
    active_substance: str | None = None
    dose_mg: float | None = None
    severity: str | None = None
    notes: str | None = None
    client_created_at: datetime


class SyncPigletEvent(BaseModel):
    id: UUID
    sow_id: UUID
    farrowing_id: UUID | None = None   # None → server auto-looks up latest farrowing
    event_date: str
    # 스키마 하드제약 대신 _process_piglet_event에서 항목별 검증(배치 전체 422 방지) — Codex P1
    event_type: str
    piglet_count: int
    reason: str | None = None
    target_sow_id: UUID | None = None
    notes: str | None = None
    client_created_at: datetime


class SyncChanges(BaseModel):
    matings:             list[SyncMating]            = Field(default_factory=list)
    farrowings:          list[SyncFarrowing]         = Field(default_factory=list)
    weanings:            list[SyncWeaning]           = Field(default_factory=list)
    reproductive_events: list[SyncReproductiveEvent] = Field(default_factory=list)
    health_events:       list[SyncHealthEvent]       = Field(default_factory=list)
    piglet_events:       list[SyncPigletEvent]       = Field(default_factory=list)


# ── Sync request ──────────────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    farm_id: UUID
    client_id: UUID                       # device UUID, stable per install
    last_sync_at: datetime | None = None  # None = first sync (full pull)
    changes: SyncChanges = Field(default_factory=SyncChanges)
    dry_run: bool = Field(
        default=False,
        description="Validate without writing. Returns what would be accepted/rejected.",
    )


# ── Per-item results ──────────────────────────────────────────────────────────

class SyncAccepted(BaseModel):
    id: UUID
    entity: str   # "mating" | "farrowing" | "weaning" | ...
    action: Literal["created", "merged"]   # merged = idempotent duplicate


class SyncRejected(BaseModel):
    id: UUID
    entity: str
    reason: str   # error code: PERIOD_LOCKED | SOW_NOT_FOUND | STATUS_CONFLICT | FUTURE_DATE | …
    detail: dict[str, Any] = Field(default_factory=dict)


class SyncConflict(BaseModel):
    id: UUID
    entity: str
    conflict_type: str   # DUPLICATE_EVENT | CYCLE_CONFLICT
    client_record: dict[str, Any]
    server_record: dict[str, Any]
    # Unresolved conflicts are stored in conflict_queue and surfaced in the app


# ── Server changes (pull) ─────────────────────────────────────────────────────

class ServerChanges(BaseModel):
    """Records created/updated on server since client's last_sync_at."""
    sows:                list[dict] = Field(default_factory=list)
    matings:             list[dict] = Field(default_factory=list)
    farrowings:          list[dict] = Field(default_factory=list)
    weanings:            list[dict] = Field(default_factory=list)
    reproductive_events: list[dict] = Field(default_factory=list)
    health_events:       list[dict] = Field(default_factory=list)
    piglet_events:       list[dict] = Field(default_factory=list)
    removals:            list[dict] = Field(default_factory=list)   # sow removals (CULLED/DEAD/SOLD/TRANSFER)
    period_locks:        list[dict] = Field(default_factory=list)   # locked months
    deleted_ids:         list[str]  = Field(default_factory=list)   # soft-deleted UUIDs


# ── Sync response ─────────────────────────────────────────────────────────────

class SyncResponse(BaseModel):
    sync_token: str             # server UTC timestamp → store as next last_sync_at
    dry_run: bool

    accepted:  list[SyncAccepted]  = Field(default_factory=list)
    rejected:  list[SyncRejected]  = Field(default_factory=list)
    conflicts: list[SyncConflict]  = Field(default_factory=list)

    server_changes: ServerChanges = Field(default_factory=ServerChanges)

    require_full_sync: bool = False   # True when last_sync_at > 30 days ago
    stats: dict[str, int] = Field(default_factory=dict)
    # stats: {"pushed": 5, "accepted": 4, "rejected": 1, "conflicts": 0, "pulled": 12}
