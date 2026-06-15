"""
Device 서비스 — 푸시 토큰 등록/조회/해제 (G2).

같은 token은 단말 1개 → upsert. 토큰 소유자가 바뀌면(기기 양도/재로그인)
user_id 갱신. 푸시 전송(push_service)이 활성 토큰을 조회해 사용.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ops import Device


async def register_device(
    db: AsyncSession, user_id: UUID, platform: str, token: str, app_version: str | None = None,
) -> Device:
    """토큰 기준 upsert. 기존 토큰이면 소유자/플랫폼/버전/last_seen 갱신."""
    now = datetime.now(UTC)
    existing = await db.scalar(select(Device).where(Device.token == token))
    if existing:
        existing.user_id = user_id
        existing.platform = platform
        existing.app_version = app_version
        existing.last_seen_at = now
        existing.deleted_at = None
        await db.commit()
        await db.refresh(existing)
        return existing
    device = Device(
        user_id=user_id, platform=platform, token=token,
        app_version=app_version, last_seen_at=now,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def list_user_devices(db: AsyncSession, user_id: UUID) -> list[Device]:
    return list(await db.scalars(
        select(Device).where(Device.user_id == user_id, Device.deleted_at.is_(None))
    ))


async def active_tokens_for_users(db: AsyncSession, user_ids: list[UUID]) -> list[str]:
    """푸시 전송용 — 주어진 유저들의 활성 토큰."""
    if not user_ids:
        return []
    return list(await db.scalars(
        select(Device.token).where(
            Device.user_id.in_(user_ids), Device.deleted_at.is_(None)
        )
    ))


async def unregister_token(db: AsyncSession, user_id: UUID, token: str) -> int:
    """로그아웃/토큰 만료 시 soft-delete. 반환: 0 or 1."""
    device = await db.scalar(
        select(Device).where(
            Device.token == token, Device.user_id == user_id, Device.deleted_at.is_(None)
        )
    )
    if not device:
        return 0
    device.deleted_at = datetime.now(UTC)
    await db.commit()
    return 1
