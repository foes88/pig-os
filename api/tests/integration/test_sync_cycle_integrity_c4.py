"""C4/H1 — sync(모바일) 번식 무결성: BreedingCycle 생성·연결 + 부분이유 + PigletGroup.

버그:
  - C4: sync mating/farrowing/weaning이 breeding_cycle_id를 NULL로 둬서 parity별 KPI
        (P1/P2 ABA 등, kpi_service가 breeding_cycles JOIN)에서 동기화 데이터 전량 누락.
  - H1: sync weaning이 잔여 무관하게 sow=OPEN으로 바꾸고 PigletGroup 미생성.
수정: REST event_service 로직 미러.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import BreedingCycle, PigletGroup, Sow
from app.schemas.sync import (
    SyncChanges,
    SyncFarrowing,
    SyncMating,
    SyncRequest,
    SyncWeaning,
)
from app.services import sync_service

pytestmark = pytest.mark.anyio


def _req(test_farm, **changes):
    return SyncRequest(
        farm_id=test_farm.id, client_id=uuid4(), last_sync_at=None, dry_run=False,
        changes=SyncChanges(**changes),
    )


async def test_sync_creates_and_links_breeding_cycle(
    db: AsyncSession, test_farm: Farm, test_sow: Sow
):
    """C4: sync 교배→분만이 같은 BreedingCycle에 연결되고 상태가 진행돼야 함."""
    now = datetime.now(UTC)
    resp = await sync_service.process_sync(db, test_farm, _req(
        test_farm,
        matings=[SyncMating(id=uuid4(), sow_id=test_sow.id, mating_date="2026-01-01",
                            mating_type="AI", mating_number=1, client_created_at=now)],
        farrowings=[SyncFarrowing(id=uuid4(), sow_id=test_sow.id, farrowing_date="2026-04-25",
                                  total_born=13, born_alive=12, born_dead=1, mummies=0,
                                  client_created_at=now)],
    ))
    assert resp.rejected == [], f"unexpected: {resp.rejected}"

    mating = await db.scalar(select(Mating).where(Mating.sow_id == test_sow.id))
    farrowing = await db.scalar(select(Farrowing).where(Farrowing.sow_id == test_sow.id))
    assert mating.breeding_cycle_id is not None
    assert farrowing.breeding_cycle_id == mating.breeding_cycle_id  # 동일 사이클 연결

    cycle = await db.get(BreedingCycle, mating.breeding_cycle_id)
    assert cycle.cycle_status == "FARROWED"


async def test_sync_full_weaning_completes_cycle_and_makes_group(
    db: AsyncSession, test_farm: Farm, test_sow: Sow
):
    """H1: 전량이유 → 사이클 WEANED + PigletGroup 생성 + sow OPEN."""
    now = datetime.now(UTC)
    resp = await sync_service.process_sync(db, test_farm, _req(
        test_farm,
        matings=[SyncMating(id=uuid4(), sow_id=test_sow.id, mating_date="2026-01-01",
                            mating_type="AI", mating_number=1, client_created_at=now)],
        farrowings=[SyncFarrowing(id=uuid4(), sow_id=test_sow.id, farrowing_date="2026-04-25",
                                  total_born=12, born_alive=12, born_dead=0, mummies=0,
                                  client_created_at=now)],
        weanings=[SyncWeaning(id=uuid4(), sow_id=test_sow.id, weaning_date="2026-05-16",
                              weaned_count=12, avg_weight_kg=6.0, client_created_at=now)],
    ))
    assert resp.rejected == [], f"unexpected: {resp.rejected}"

    weaning = await db.scalar(select(Weaning).where(Weaning.sow_id == test_sow.id))
    assert weaning.breeding_cycle_id is not None
    cycle = await db.get(BreedingCycle, weaning.breeding_cycle_id)
    assert cycle.cycle_status == "WEANED" and cycle.ended_at is not None

    group = await db.scalar(select(PigletGroup).where(PigletGroup.farm_id == test_farm.id))
    assert group is not None and group.head_count_in == 12

    await db.refresh(test_sow)
    assert test_sow.status == "OPEN"


async def test_sync_partial_weaning_keeps_lactating(
    db: AsyncSession, test_farm: Farm, test_sow: Sow
):
    """H1: 부분이유(잔여>0) → sow LACTATING 유지 + 사이클 FARROWED 유지."""
    now = datetime.now(UTC)
    resp = await sync_service.process_sync(db, test_farm, _req(
        test_farm,
        matings=[SyncMating(id=uuid4(), sow_id=test_sow.id, mating_date="2026-01-01",
                            mating_type="AI", mating_number=1, client_created_at=now)],
        farrowings=[SyncFarrowing(id=uuid4(), sow_id=test_sow.id, farrowing_date="2026-04-25",
                                  total_born=12, born_alive=12, born_dead=0, mummies=0,
                                  client_created_at=now)],
        weanings=[SyncWeaning(id=uuid4(), sow_id=test_sow.id, weaning_date="2026-05-16",
                              weaned_count=8, avg_weight_kg=6.0, client_created_at=now)],
    ))
    assert resp.rejected == [], f"unexpected: {resp.rejected}"

    await db.refresh(test_sow)
    assert test_sow.status == "LACTATING"  # 4두 남음 → 포유 유지
    weaning = await db.scalar(select(Weaning).where(Weaning.sow_id == test_sow.id))
    cycle = await db.get(BreedingCycle, weaning.breeding_cycle_id)
    assert cycle.cycle_status == "FARROWED"  # 사이클 미완료
