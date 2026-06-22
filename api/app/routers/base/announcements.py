"""공지 — 고객(로그인 사용자) 읽기. 게시중 + 게시기간 내만 노출."""
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import and_, func, or_, select

from app.core.dependencies import CurrentUser, DbDep
from app.db.models.content import Announcement
from app.schemas.content import AnnouncementOut

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.get("", response_model=list[AnnouncementOut])
async def list_announcements(
    db: DbDep,
    _user: CurrentUser,
    lang: Annotated[str | None, Query(description="언어 필터(해당 언어 + 전체 대상)")] = None,
) -> list[AnnouncementOut]:
    now = func.now()
    conds = [
        Announcement.published.is_(True),
        or_(Announcement.publish_from.is_(None), Announcement.publish_from <= now),
        or_(Announcement.publish_until.is_(None), Announcement.publish_until >= now),
    ]
    if lang:
        conds.append(or_(Announcement.lang.is_(None), Announcement.lang == lang))
    rows = (
        await db.execute(
            select(Announcement).where(and_(*conds))
            .order_by(Announcement.pinned.desc(), Announcement.created_at.desc())
        )
    ).scalars().all()
    return [
        AnnouncementOut(
            id=str(a.id), title=a.title, body=a.body, category=a.category, pinned=a.pinned,
            published=a.published, publish_from=a.publish_from, publish_until=a.publish_until,
            lang=a.lang, created_at=a.created_at,
        )
        for a in rows
    ]
