"""운영자 어드민 콘솔 — 기반(overview/me/data-monitor).

SUPER_ADMIN 전용. 전사(cross-tenant) 조회/운영. 라우터 전체 require_super_admin 가드.
프리픽스: /api/v1/admin. 회원 관리는 admin/users.py, 콘텐츠는 admin/content.py 등으로 분리.
"""
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.db.models.platform import User

router = APIRouter(
    prefix="/admin",
    tags=["Admin Console"],
    dependencies=[Depends(require_super_admin)],
)

# ── Farm Data Monitor 공용 쿼리 ──────────────────────────────────────────────
# 농가 데이터 입력 활동(created_at) 기준 — 7개 이벤트 테이블 UNION → 농장별 집계.
_EVENT_UNION = """
  SELECT farm_id, created_at FROM matings
  UNION ALL SELECT farm_id, created_at FROM farrowings
  UNION ALL SELECT farm_id, created_at FROM weanings
  UNION ALL SELECT farm_id, created_at FROM health_events
  UNION ALL SELECT farm_id, created_at FROM removals
  UNION ALL SELECT farm_id, created_at FROM piglet_events
  UNION ALL SELECT farm_id, created_at FROM feed_records
"""

_FARM_ACTIVITY_SQL = f"""
WITH ev AS ({_EVENT_UNION}),
agg AS (
  SELECT farm_id,
         max(created_at) AS last_event_at,
         count(*) FILTER (WHERE created_at >= now() - interval '7 days')  AS events_7d,
         count(*) FILTER (WHERE created_at >= now() - interval '30 days') AS events_30d,
         count(*) AS events_total
  FROM ev GROUP BY farm_id
),
sowc AS (
  SELECT farm_id, count(*) AS sows FROM sows WHERE deleted_at IS NULL GROUP BY farm_id
)
SELECT f.id::text AS farm_id, f.name AS farm_name, f.country,
       COALESCE(sc.sows, 0)         AS sows,
       a.last_event_at,
       COALESCE(a.events_7d, 0)     AS events_7d,
       COALESCE(a.events_30d, 0)    AS events_30d,
       COALESCE(a.events_total, 0)  AS events_total
FROM farms f
LEFT JOIN agg  a  ON a.farm_id = f.id
LEFT JOIN sowc sc ON sc.farm_id = f.id
WHERE f.active = true
ORDER BY a.last_event_at DESC NULLS LAST
"""


def _farm_status(last_event_at: datetime | None, events_total: int) -> str:
    """농장 데이터 입력 상태: onboarding(입력 0) / active(7일내) / idle(30일내) / stale(30일+)."""
    if not events_total or last_event_at is None:
        return "onboarding"
    delta = datetime.now(UTC) - last_event_at
    if delta <= timedelta(days=7):
        return "active"
    if delta <= timedelta(days=30):
        return "idle"
    return "stale"


# ── Overview ────────────────────────────────────────────────────────────────
class AdminOverview(BaseModel):
    organizations: int
    farms: int             # 활성 농장
    users: int
    sows: int
    signups_7d: int        # 최근 7일 가입
    activated_farms: int   # 모돈≥1 AND 이벤트≥1 (실사용)
    stale_farms: int       # 활성 농장 중 30일+ 미입력


@router.get("/overview", response_model=AdminOverview)
async def get_overview(db: DbDep, _admin: SuperAdmin) -> AdminOverview:
    """플랫폼 전사 개요 + 활성화 지표 — 어드민 대시보드 상단 카드."""
    orgs = await db.scalar(text("SELECT count(*) FROM organizations"))
    farms = await db.scalar(text("SELECT count(*) FROM farms WHERE active = true"))
    users = await db.scalar(text("SELECT count(*) FROM users"))
    sows = await db.scalar(text("SELECT count(*) FROM sows WHERE deleted_at IS NULL"))
    signups_7d = await db.scalar(
        text("SELECT count(*) FROM users WHERE created_at >= now() - interval '7 days'")
    )
    rows = (await db.execute(text(_FARM_ACTIVITY_SQL))).mappings().all()
    activated = sum(1 for r in rows if r["sows"] >= 1 and r["events_total"] >= 1)
    stale = sum(
        1 for r in rows if _farm_status(r["last_event_at"], r["events_total"]) == "stale"
    )
    return AdminOverview(
        organizations=orgs or 0,
        farms=farms or 0,
        users=users or 0,
        sows=sows or 0,
        signups_7d=signups_7d or 0,
        activated_farms=activated,
        stale_farms=stale,
    )


# ── Farm Data Monitor ─────────────────────────────────────────────────────────
class DataMonitorRow(BaseModel):
    farm_id: str
    farm_name: str
    country: str
    sows: int
    last_event_at: datetime | None
    events_7d: int
    events_30d: int
    events_total: int
    status: str  # onboarding | active | idle | stale


@router.get("/data-monitor", response_model=list[DataMonitorRow])
async def data_monitor(db: DbDep, _admin: SuperAdmin) -> list[DataMonitorRow]:
    """농장별 데이터 입력 현황 — 마지막 입력일·최근 건수·상태. 미입력/방치 농장 식별용."""
    rows = (await db.execute(text(_FARM_ACTIVITY_SQL))).mappings().all()
    return [
        DataMonitorRow(
            farm_id=r["farm_id"],
            farm_name=r["farm_name"],
            country=r["country"],
            sows=r["sows"],
            last_event_at=r["last_event_at"],
            events_7d=r["events_7d"],
            events_30d=r["events_30d"],
            events_total=r["events_total"],
            status=_farm_status(r["last_event_at"], r["events_total"]),
        )
        for r in rows
    ]


class AdminWhoAmI(BaseModel):
    id: str
    email: str
    name: str
    role: str


@router.get("/me", response_model=AdminWhoAmI)
async def admin_me(admin: Annotated[User, Depends(require_super_admin)]) -> AdminWhoAmI:
    """현재 운영자 정보 — 어드민 셸 헤더용 + 게이트 동작 확인."""
    return AdminWhoAmI(id=str(admin.id), email=admin.email, name=admin.name, role=admin.role)
