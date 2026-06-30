"""
POST /api/v1/sync

Single endpoint for bidirectional offline sync.
  PUSH: client changes → server validation → accepted / rejected / conflict
  PULL: server changes since last_sync_at → client

dry_run=true: validate everything, write nothing.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, get_farm_context
from app.core.exceptions import ForbiddenError
from app.core.permissions import effective_farm_role
from app.db.models.platform import Farm, User
from app.schemas.sync import SyncRequest, SyncResponse
from app.services.sync_service import process_sync

router = APIRouter(prefix="/farms", tags=["Sync"])

# PUSH(쓰기)는 REST events와 동일하게 입력 역할 필요 — VIEWER/VET 차단. PULL(읽기)은 멤버 전원 허용.
_SYNC_WRITE_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN")


@router.post("/{farm_id}/sync", response_model=SyncResponse)
async def sync(
    body: SyncRequest,
    farm: Farm = Depends(get_farm_context),  # validates JWT + farm membership
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    """
    Bidirectional offline sync.

    **Push** (client → server):
    - Each item validated independently (per-item atomicity)
    - Returns: accepted / rejected / conflicts
    - Unresolved conflicts stored in conflict_queue for manual review

    **Pull** (server → client):
    - Returns all records changed since `last_sync_at`
    - Includes soft-deleted IDs for client to purge

    **dry_run=true**: validate only, no DB writes. Use before first real sync.

    **Conflict types**: DUPLICATE_EVENT | CYCLE_CONFLICT | STATUS_CONFLICT |
    PERIOD_LOCKED | SOW_NOT_FOUND | FUTURE_DATE
    """
    # 권한 패리티: PUSH(changes 존재)는 쓰기 — REST events(_ENTRY_ROLES)와 동일하게 입력 역할 필요.
    # VIEWER/VET가 sync로 교배·분만 등을 생성하던 우회 차단(QA 보안리뷰 H2). PULL만이면 멤버 전원 허용.
    ch = body.changes
    has_push = any((ch.matings, ch.farrowings, ch.weanings, ch.reproductive_events,
                    ch.health_events, ch.piglet_events, ch.pregnancy_checks))
    if has_push:
        role = await effective_farm_role(current_user, farm.id, db)
        if role not in _SYNC_WRITE_ROLES:
            raise ForbiddenError(
                f"Required farm role for sync push: {' or '.join(_SYNC_WRITE_ROLES)}"
            )
    return await process_sync(db, farm, body)
