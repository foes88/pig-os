"""C3 — 번식 무결성 partial unique index (DB 레벨).

버그: 모델 주석에만 있던 idx_one_weaning_per_farrowing / idx_one_active_cycle 가
실제 마이그레이션에 누락 → 동시요청 시 이중 이유·이중 활성사이클(KPI 손상).
수정: 마이그레이션 c9f1a3b5d7e2 로 두 partial unique index 생성.

여기서는 앱 레벨 가드를 우회해 모델 직삽입으로 DB 인덱스 자체가 작동하는지 검증.
"""
from datetime import UTC, date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Weaning
from app.db.models.platform import Farm, User
from app.db.models.sow import Sow
from app.schemas.events import FarrowingCreate, MatingCreate
from app.services import event_service

pytestmark = pytest.mark.anyio


async def _mate_and_farrow(db, farm, user, sow):
    await event_service.record_mating(
        db, farm.id, user.id,
        MatingCreate(sow_id=sow.id, mating_date=date(2026, 1, 10), mating_type="AI"))
    f = await event_service.record_farrowing(
        db, farm.id, user.id,
        FarrowingCreate(sow_id=sow.id, farrowing_date=date(2026, 5, 5), born_alive=11))
    return f


async def test_multiple_weanings_per_farrowing_allowed(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User
):
    """부분이유 회귀 가드: 한 분만에 이유 이벤트 다건이 허용돼야 한다.
    (분만당 이유 1건 unique 인덱스를 잘못 추가하면 이 테스트가 깨진다)."""
    f = await _mate_and_farrow(db, test_farm, test_user, test_sow)
    db.add(Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                   weaning_date=date(2026, 5, 26), weaned_count=5))
    await db.flush()
    db.add(Weaning(farm_id=test_farm.id, sow_id=test_sow.id, farrowing_id=f.id,
                   weaning_date=date(2026, 5, 27), weaned_count=5))
    await db.flush()  # 두 번째도 정상 — 예외 없어야 함


async def test_double_active_cycle_per_sow_rejected(
    db: AsyncSession, test_farm: Farm, test_sow: Sow, test_user: User
):
    from datetime import datetime

    from app.db.models.sow import BreedingCycle
    # 첫 활성 사이클 — record_mating이 생성
    await event_service.record_mating(
        db, test_farm.id, test_user.id,
        MatingCreate(sow_id=test_sow.id, mating_date=date(2026, 1, 10), mating_type="AI"))
    # 동일 모돈에 두 번째 활성(MATED) 사이클 직삽입 → unique index 위반
    db.add(BreedingCycle(farm_id=test_farm.id, sow_id=test_sow.id, parity=2,
                         cycle_status="MATED",
                         started_at=datetime(2026, 2, 1, tzinfo=UTC)))
    with pytest.raises(IntegrityError):
        await db.flush()
