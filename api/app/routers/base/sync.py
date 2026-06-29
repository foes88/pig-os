"""
POST /api/v1/sync

Single endpoint for bidirectional offline sync.
  PUSH: client changes → server validation → accepted / rejected / conflict
  PULL: server changes since last_sync_at → client

dry_run=true: validate everything, write nothing.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_farm_context, require_farm_role
from app.db.models.platform import Farm
from app.schemas.sync import SyncRequest, SyncResponse
from app.services.sync_service import process_sync

router = APIRouter(prefix="/farms", tags=["Sync"])

# sync는 오프라인 데이터 입력(교배/분만/이유 등 insert + 상태변경) → 쓰기 권한 필요.
# 과거엔 get_farm_context(멤버십)만 있어 VIEWER/VET가 sync로 write 가능했음(BUG-ACC-SYNC-RBAC).
_ENTRY_ROLES = ("FARM_OWNER", "FARM_MANAGER", "FARM_WORKER", "SUPER_ADMIN",
                "VENDOR_ADMIN", "DISTRIBUTOR_ADMIN", "DEALER_ADMIN")


@router.post("/{farm_id}/sync", response_model=SyncResponse,
             dependencies=[require_farm_role(*_ENTRY_ROLES)])
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
