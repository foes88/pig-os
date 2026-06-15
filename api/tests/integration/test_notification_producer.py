"""
N1 통합 테스트 — notification_service.create_from_alerts (P12-6 Producer).

과기한 모돈 → OWNER/MANAGER 멤버에게 IN_APP 영구 알림 생성 + 멱등성 검증.
DB 필요(pigos_test). 샌드박스(DB 없음)에서는 서비스 import-smoke로 대체 검증됨.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from app.db.models.events import Mating
from app.db.models.ops import Notification
from app.db.models.platform import UserFarm
from app.services import notification_service

pytestmark = pytest.mark.asyncio


async def _setup_overdue(db, farm, user, sow):
    """OWNER 멤버십 + PREGNANT 130일 경과 교배 → pregnant_overdue_farrowing."""
    db.add(UserFarm(user_id=user.id, farm_id=farm.id, role_override="FARM_OWNER"))
    today = date(2026, 6, 1)
    sow.status = "PREGNANT"
    db.add(Mating(farm_id=farm.id, sow_id=sow.id, mating_date=today - timedelta(days=130)))
    await db.flush()
    return today


async def test_create_from_alerts_generates_for_owner(db, test_farm, test_user, test_sow):
    today = await _setup_overdue(db, test_farm, test_user, test_sow)

    created = await notification_service.create_from_alerts(db, test_farm.id, today=today)
    assert created >= 1

    n = await db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == test_user.id,
            Notification.type == "IN_APP",
            Notification.related_entity_id == test_sow.id,
        )
    )
    assert n == 1


async def test_create_from_alerts_is_idempotent(db, test_farm, test_user, test_sow):
    today = await _setup_overdue(db, test_farm, test_user, test_sow)

    first = await notification_service.create_from_alerts(db, test_farm.id, today=today)
    assert first >= 1

    # 2회차 — 미읽음 동일 알림은 재생성하지 않음
    second = await notification_service.create_from_alerts(db, test_farm.id, today=today)
    assert second == 0


async def test_no_recipients_no_notifications(db, test_farm, test_sow):
    """OWNER/MANAGER 멤버가 없으면 생성 0건."""
    today = date(2026, 6, 1)
    test_sow.status = "PREGNANT"
    db.add(Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=today - timedelta(days=130)))
    await db.flush()

    created = await notification_service.create_from_alerts(db, test_farm.id, today=today)
    assert created == 0
