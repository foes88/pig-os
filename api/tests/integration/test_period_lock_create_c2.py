"""C2 — REST create 경로의 월마감 잠금(period_lock) 적용.

버그: _ensure_period_unlocked가 update/delete에만 걸려 있어, 잠긴 달로 백데이트한
신규 이벤트(교배/분만/이유 등)가 REST create로 무검사 삽입됐다(확정 KPI 무효화).
수정: record_* create 경로 6곳에 period-lock 검사 추가.
"""
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PeriodLockedError
from app.db.models.ops import PeriodLock
from app.db.models.platform import Farm, User
from app.db.models.sow import Sow
from app.schemas.events import MatingCreate
from app.services import event_service

pytestmark = pytest.mark.anyio


async def _lock(db, farm, user, *, y=2026, m=3):
    db.add(PeriodLock(farm_id=farm.id, period_year=y, period_month=m, locked_by=user.id))
    await db.flush()


async def test_create_mating_in_locked_period_blocked(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    with pytest.raises(PeriodLockedError) as ei:
        await event_service.record_mating(
            db, test_farm.id, test_user.id,
            MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 3, 15), mating_type="AI"))
    assert ei.value.status_code == 423


async def test_create_mating_in_unlocked_period_passes(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User
):
    await _lock(db, test_farm, test_user, y=2026, m=3)
    # 잠기지 않은 달(4월)은 통과
    m = await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 4, 10), mating_type="AI"))
    assert m.id is not None
