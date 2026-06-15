"""
Notification 서비스 — 인앱 알림 목록/읽음 처리 (P12-6 + 모바일).

수신자(user_id) 스코프. read_at IS NULL = 미읽음.
IN_APP 채널만 노출 (PUSH/EMAIL/SMS 전송로그는 목록에서 제외).
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.ops import Notification

# 목록에 노출하는 채널 (전송 추적 로그 제외)
_INAPP_TYPES = ("IN_APP",)


async def _unread_count(db: AsyncSession, user_id: UUID, farm_id: UUID | None) -> int:
    q = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id,
        Notification.type.in_(_INAPP_TYPES),
        Notification.read_at.is_(None),
    )
    if farm_id:
        q = q.where(Notification.farm_id == farm_id)
    return int(await db.scalar(q) or 0)


async def list_notifications(
    db: AsyncSession, user_id: UUID, farm_id: UUID | None = None,
    unread_only: bool = False, limit: int = 50, offset: int = 0,
) -> tuple[list[Notification], int, int]:
    """(items, unread_count, total) 반환. 최신순."""
    base = [
        Notification.user_id == user_id,
        Notification.type.in_(_INAPP_TYPES),
    ]
    if farm_id:
        base.append(Notification.farm_id == farm_id)
    if unread_only:
        base.append(Notification.read_at.is_(None))

    total = int(await db.scalar(
        select(func.count()).select_from(Notification).where(*base)
    ) or 0)

    rows = list(await db.scalars(
        select(Notification).where(*base)
        .order_by(Notification.created_at.desc())
        .limit(limit).offset(offset)
    ))
    unread = await _unread_count(db, user_id, farm_id)
    return rows, unread, total


async def mark_read(db: AsyncSession, user_id: UUID, notification_id: UUID) -> int:
    notif = await db.scalar(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id,
        )
    )
    if not notif:
        raise NotFoundError(f"Notification {notification_id} not found")
    if notif.read_at is None:
        notif.read_at = datetime.now(UTC)
        await db.commit()
        return 1
    return 0


async def mark_all_read(db: AsyncSession, user_id: UUID, farm_id: UUID | None = None) -> int:
    conds = [
        Notification.user_id == user_id,
        Notification.type.in_(_INAPP_TYPES),
        Notification.read_at.is_(None),
    ]
    if farm_id:
        conds.append(Notification.farm_id == farm_id)
    result = await db.execute(
        update(Notification).where(*conds).values(read_at=datetime.now(UTC))
    )
    await db.commit()
    return result.rowcount or 0
