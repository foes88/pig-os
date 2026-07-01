"""#4 — 분만율 코호트(스펙 §4).

기존 build_herd_kpis FARROWING_RATE = window내 farrowings/matings(서로 다른 개체).
스펙: ref 기준 110~150일 전 초교배(mating_number=1) 중 분만 성공 비율, 교배후 115일 내
폐사 모돈 제외. 두수 변동 시 왜곡되던 비코호트를 코호트로 정정.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating
from app.db.models.health import Removal
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import _cohort_farrowing_rate

pytestmark = pytest.mark.anyio

REF = date(2026, 6, 30)          # 코호트 창: 2026-02-01 ~ 2026-03-12
IN_WINDOW = date(2026, 2, 15)    # 창 안 교배일


async def _sow(db, farm) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=1,
            status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


async def _mating(db, farm, sow, *, num=1, d=IN_WINDOW) -> Mating:
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=d, mating_type="AI", mating_number=num)
    db.add(m)
    await db.flush()
    return m


async def test_cohort_farrowing_rate_first_mating_only(db: AsyncSession, test_farm: Farm):
    # 초교배 10건 중 8건 분만 → 80.0
    for i in range(10):
        s = await _sow(db, test_farm)
        m = await _mating(db, test_farm, s)
        if i < 8:
            db.add(Farrowing(farm_id=test_farm.id, sow_id=s.id, mating_id=m.id,
                             farrowing_date=date(2026, 6, 10), total_born=12, born_alive=11,
                             stillborn=1, mummified=0, nursing_head=11))
    await db.flush()
    assert await _cohort_farrowing_rate(db, test_farm.id, REF) == pytest.approx(80.0)


async def test_cohort_excludes_re_mating_and_dead(db: AsyncSession, test_farm: Farm):
    # 초교배 4건 전부 분만 → 분자4/분모4. 재교배(num=2)·교배후폐사는 분모 제외.
    for _ in range(4):
        s = await _sow(db, test_farm)
        m = await _mating(db, test_farm, s)
        db.add(Farrowing(farm_id=test_farm.id, sow_id=s.id, mating_id=m.id,
                         farrowing_date=date(2026, 6, 10), total_born=12, born_alive=12,
                         stillborn=0, mummified=0, nursing_head=12))
    # 재교배(mating_number=2) — 코호트 제외
    s2 = await _sow(db, test_farm)
    await _mating(db, test_farm, s2, num=2)
    # 교배 후 폐사 모돈 — 분모 제외
    sd = await _sow(db, test_farm)
    await _mating(db, test_farm, sd)
    db.add(Removal(farm_id=test_farm.id, sow_id=sd.id, removal_date=date(2026, 3, 1),
                   removal_type="DEAD"))
    await db.flush()
    assert await _cohort_farrowing_rate(db, test_farm.id, REF) == pytest.approx(100.0)


async def test_cohort_no_matings_is_none(db: AsyncSession, test_farm: Farm):
    assert await _cohort_farrowing_rate(db, test_farm.id, REF) is None
