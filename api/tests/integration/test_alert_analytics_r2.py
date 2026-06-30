"""R2 헌터 — alert 타임존(P1) + analytics PRRS 소프트삭제 분자 누수(P2).

P1: get_overdue_sows/get_cull_candidates가 UTC 서버 날짜를 써서 비-UTC 농장이
날짜 경계에서 days-overdue를 1일 과소계산. 농장 tz 기준 today로 교정(_farm_today).
P2: prrs_by_genetics 분자(HealthEvent→Sow 조인)가 소프트삭제 모돈을 제외하지 않아
발생률이 100%를 초과할 수 있었음. 분모와 동일하게 deleted_at 필터 추가.
"""
import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health import HealthEvent
from app.db.models.platform import Farm, Organization
from app.db.models.sow import Sow
from app.services.alert_service import _farm_today
from app.services.analytics_service import prrs_by_genetics

pytestmark = pytest.mark.anyio


async def _farm(db, org, tz) -> Farm:
    f = Farm(org_id=org.id, farm_code=f"F-{uuid.uuid4().hex[:6].upper()}",
             name="F", country="KR", timezone=tz, active=True)
    db.add(f)
    await db.flush()
    return f


# ── P1: 농장 타임존 기준 today ───────────────────────────────────────
async def test_farm_today_honors_timezone(db: AsyncSession, test_org: Organization):
    far = await _farm(db, test_org, "Pacific/Kiritimati")  # UTC+14
    got = await _farm_today(db, far.id)
    assert got == datetime.now(ZoneInfo("Pacific/Kiritimati")).date(), \
        "농장 tz가 아니라 UTC 서버 날짜를 쓰면 경계에서 1일 어긋남"


async def test_farm_today_unknown_tz_falls_back_utc(db: AsyncSession, test_org: Organization):
    f = await _farm(db, test_org, "Not/AZone")
    got = await _farm_today(db, f.id)
    assert got == datetime.now(ZoneInfo("UTC")).date()


# ── P2: PRRS 분석 소프트삭제 모돈 제외 ───────────────────────────────
async def test_prrs_excludes_soft_deleted_sow(db: AsyncSession, test_org: Organization):
    farm = await _farm(db, test_org, "Asia/Seoul")
    # 동일 유전자 그룹 모돈 1두 + PRRS 이벤트, 이후 모돈 소프트삭제
    sow = Sow(farm_id=farm.id, ear_tag="P-1", parity=1, status="OPEN", breed="LY",
              entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(sow)
    await db.flush()
    db.add(HealthEvent(farm_id=farm.id, sow_id=sow.id, event_date=date(2026, 5, 1),
                       event_type="DISEASE", disease_code="PRRS"))
    await db.flush()
    sow.deleted_at = datetime.now(UTC)  # 소프트삭제 → 분모에서 빠짐
    await db.flush()

    report = await prrs_by_genetics(db, farm.id)
    # 삭제된 모돈의 이벤트가 분자에 남으면 affected/events>0 이면서 total=0 → 모순/>100%
    assert report["total_affected"] == 0, "소프트삭제 모돈의 PRRS 이벤트는 분자에서 제외돼야 함"
    assert report["total_events"] == 0
    for row in report["rows"]:
        assert row["total_sows"] >= row["affected_sows"]
        assert row.get("incidence_rate", 0) <= 100.0
