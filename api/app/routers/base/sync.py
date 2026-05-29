"""
POST /api/v1/sync

Single endpoint for bidirectional offline sync.
  PUSH: client changes → server validation → accepted / rejected / conflict
  PULL: server changes since last_sync_at → client

dry_run=true: validate everything, write nothing.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_farm_context
from app.db.models.platform import Farm
from app.schemas.sync import SyncRequest, SyncResponse
from app.services.sync_service import process_sync

router = APIRouter(prefix="/farms", tags=["Sync"])


@router.post("/{farm_id}/sync", response_model=SyncResponse)
async def sync(
    body: SyncRequest,
    farm: Farm = Depends(get_farm_context),  # validates JWT + farm membership
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
    return await process_sync(db, farm, body)
