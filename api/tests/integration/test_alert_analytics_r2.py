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

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.health import HealthEvent
from app.db.models.platform import Farm, Organization
from app.db.models.sow import Sow
from app.services.alert_service import _farm_today, get_cull_candidates
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


# ── P3: 동일날짜 이유 tie-break 결정성(cull aged_low_performer) ─────────
async def test_last_weaned_tiebreak_deterministic(db: AsyncSession, test_org: Organization):
    farm = await _farm(db, test_org, "Asia/Seoul")
    sow = Sow(farm_id=farm.id, ear_tag="C-1", parity=8, status="OPEN",
              entry_date=datetime(2020, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(sow)
    await db.flush()  # sow.id 확정 후 참조
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2026, 1, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 1),
                  total_born=16, born_alive=15, stillborn=1, mummified=0, nursing_head=15)
    db.add(f)
    await db.flush()
    # 동일 이유일, count 상이 — 나중에 생성된(더 늦은 created_at) 8두가 '최신'이어야 함
    db.add(Weaning(farm_id=farm.id, sow_id=sow.id, farrowing_id=f.id, weaning_date=date(2026, 4, 22),
                   weaned_count=15, created_at=datetime(2026, 4, 22, 9, 0, tzinfo=UTC)))
    db.add(Weaning(farm_id=farm.id, sow_id=sow.id, farrowing_id=f.id, weaning_date=date(2026, 4, 22),
                   weaned_count=8, created_at=datetime(2026, 4, 22, 18, 0, tzinfo=UTC)))
    await db.flush()

    cands = await get_cull_candidates(db, farm.id)
    me = next((c for c in cands if str(c.get("sow_id")) == str(sow.id)), None)
    # 최신 이유두수=8(<9) + parity 8(>7) → aged_low_performer 권고. 15두가 채택됐다면 미권고.
    assert me is not None and "aged_low_performer" in me.get("reasons", []), \
        "동일날짜 이유 tie-break이 최신(8두)을 결정적으로 선택해야 함"
