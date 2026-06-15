"""
Notifications router — 인앱 알림 목록/읽음 (P12-6 + 모바일 공용).

수신자(현재 유저) 스코프. 선택적 farm_id 필터.
"""
from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbDep
from app.schemas.notification import MarkReadResult, NotificationList, NotificationResponse
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationList)
async def list_notifications(
    user: CurrentUser, db: DbDep,
    farm_id: UUID | None = None, unread_only: bool = False,
    limit: int = 50, offset: int = 0,
) -> NotificationList:
    rows, unread, total = await notification_service.list_notifications(
        db, user.id, farm_id=farm_id, unread_only=unread_only, limit=limit, offset=offset,
    )
    return NotificationList(
        items=[NotificationResponse.model_validate(r) for r in rows],
        unread_count=unread, total=total,
    )


@router.patch("/{notification_id}/read", response_model=MarkReadResult)
async def mark_read(notification_id: UUID, user: CurrentUser, db: DbDep) -> MarkReadResult:
    updated = await notification_service.mark_read(db, user.id, notification_id)
    _, unread, _ = await notification_service.list_notifications(db, user.id, limit=0)
    return MarkReadResult(updated=updated, unread_count=unread)


@router.post("/read-all", response_model=MarkReadResult)
async def mark_all_read(user: CurrentUser, db: DbDep, farm_id: UUID | None = None) -> MarkReadResult:
    updated = await notification_service.mark_all_read(db, user.id, farm_id=farm_id)
    _, unread, _ = await notification_service.list_notifications(db, user.id, farm_id=farm_id, limit=0)
    return MarkReadResult(updated=updated, unread_count=unread)
