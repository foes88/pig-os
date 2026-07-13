"""운영자 어드민 콘솔 — 기반(overview/me/data-monitor).

SUPER_ADMIN 전용. 전사(cross-tenant) 조회/운영. 라우터 전체 require_super_admin 가드.
프리픽스: /api/v1/admin. 회원 관리는 admin/users.py, 콘텐츠는 admin/content.py 등으로 분리.
"""
from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text

from app.core.dependencies import DbDep, SuperAdmin, require_super_admin
from app.core.exceptions import NotFoundError
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


# ── Farm Data Monitor 상세 드릴다운 ──────────────────────────────────────────
# 농장 클릭 → 이벤트 유형별 분해 · 모돈 상태분포 · 최근 활동 · KPI. "깊게 보기".
_FARM_EVENTS_UNION = """
  SELECT 'mating'    AS t, mating_date    AS d, created_at AS c FROM matings           WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'farrowing', farrowing_date, created_at FROM farrowings             WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'weaning',   weaning_date,   created_at FROM weanings               WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'health',    event_date,     created_at FROM health_events          WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'removal',   removal_date,   created_at FROM removals               WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'piglet',    event_date,     created_at FROM piglet_events          WHERE farm_id=:f AND deleted_at IS NULL
  UNION ALL SELECT 'feed',      record_date,    created_at FROM feed_records           WHERE farm_id=:f AND deleted_at IS NULL
"""


class SowStatusCount(BaseModel):
    status: str
    count: int


class EventTypeBreakdown(BaseModel):
    type: str
    total: int
    count_30d: int
    last_at: date | None


class RecentEvent(BaseModel):
    type: str
    date: date | None


class FarmDataDetail(BaseModel):
    farm_id: str
    farm_name: str
    country: str
    org_name: str | None = None
    timezone: str | None = None
    currency: str | None = None
    created_at: datetime | None = None
    total_sows: int
    sows_by_status: list[SowStatusCount]
    event_breakdown: list[EventTypeBreakdown]
    recent_events: list[RecentEvent]
    psy: float | None = None
    total_weaned_ytd: int = 0
    avg_sows_ytd: float | None = None


@router.get("/data-monitor/{farm_id}", response_model=FarmDataDetail)
async def data_monitor_detail(farm_id: str, db: DbDep, _admin: SuperAdmin) -> FarmDataDetail:
    """농장 상세 — 이벤트 유형별 분해·모돈 상태분포·최근 활동·PSY. 운영자 심층 조회."""
    meta = (await db.execute(text(
        "SELECT f.name, f.country, f.timezone, f.currency, f.created_at, o.name AS org_name "
        "FROM farms f LEFT JOIN organizations o ON o.id = f.org_id WHERE f.id = :f"),
        {"f": farm_id})).mappings().first()
    if not meta:
        raise NotFoundError(f"Farm {farm_id} not found")

    sbs = (await db.execute(text(
        "SELECT status, count(*) AS c FROM sows WHERE farm_id=:f AND deleted_at IS NULL "
        "GROUP BY status ORDER BY 2 DESC"), {"f": farm_id})).all()
    sows_by_status = [SowStatusCount(status=s, count=c) for s, c in sbs]
    total_sows = sum(x.count for x in sows_by_status)

    brk = (await db.execute(text(
        f"SELECT t, count(*) AS total, "
        f"count(*) FILTER (WHERE c >= now() - interval '30 days') AS c30, max(d) AS last_at "
        f"FROM ({_FARM_EVENTS_UNION}) x GROUP BY t ORDER BY total DESC"), {"f": farm_id})).mappings().all()
    event_breakdown = [
        EventTypeBreakdown(type=r["t"], total=r["total"], count_30d=r["c30"], last_at=r["last_at"])
        for r in brk
    ]

    rec = (await db.execute(text(
        f"SELECT t, d FROM ({_FARM_EVENTS_UNION}) x WHERE d IS NOT NULL ORDER BY d DESC LIMIT 15"),
        {"f": farm_id})).all()
    recent_events = [RecentEvent(type=t, date=d) for t, d in rec]

    # PSY(당해년도) — 기존 KPI 엔진 재사용(대시보드 값과 동일 정의)
    psy = total_weaned = 0
    avg_sows = None
    try:
        from app.services.kpi_service import calculate_psy
        detail = await calculate_psy(db, farm_id, datetime.now(UTC).year)  # type: ignore[arg-type]
    except Exception:  # noqa: BLE001 — KPI 실패해도 나머지 상세는 반환
        detail = None
    if detail:
        psy = detail.psy
        total_weaned = detail.total_weaned
        avg_sows = detail.avg_sow_count

    return FarmDataDetail(
        farm_id=farm_id,
        farm_name=meta["name"],
        country=meta["country"],
        org_name=meta["org_name"],
        timezone=meta["timezone"],
        currency=meta["currency"],
        created_at=meta["created_at"],
        total_sows=total_sows,
        sows_by_status=sows_by_status,
        event_breakdown=event_breakdown,
        recent_events=recent_events,
        psy=psy,
        total_weaned_ytd=total_weaned,
        avg_sows_ytd=avg_sows,
    )


class AdminWhoAmI(BaseModel):
    id: str
    email: str
    name: str
    role: str


@router.get("/me", response_model=AdminWhoAmI)
async def admin_me(admin: Annotated[User, Depends(require_super_admin)]) -> AdminWhoAmI:
    """현재 운영자 정보 — 어드민 셸 헤더용 + 게이트 동작 확인."""
    return AdminWhoAmI(id=str(admin.id), email=admin.email, name=admin.name, role=admin.role)
