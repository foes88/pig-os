"""F1-F4 — 오프라인 sync 경로가 REST와 동일한 번식 검증을 강제한다.

기존: sync 처리기가 REST의 임신기간(100~130일)·날짜순서(분만>교배, 이유>분만)·
포유기간(10~60일)·국가 이유일령·사이클당 교배횟수 상한을 건너뛰어, 오프라인(저신뢰)
채널이 온라인이 거부하는 데이터를 삽입할 수 있었음(채널 간 불일치). 모두 REJECTED로 교정.
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import BreedingCycle, Sow
from app.schemas.sync import SyncFarrowing, SyncMating, SyncWeaning
from app.services.sync_service import _process_farrowing, _process_mating, _process_weaning

pytestmark = pytest.mark.anyio


async def _sow(db, farm, status) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=1,
            status=status, entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


def _now():
    return datetime(2026, 5, 1, tzinfo=UTC)


# ── F1: 분만 임신기간 100~130일 ─────────────────────────────────────
async def test_sync_farrowing_short_gestation_rejected(db: AsyncSession, test_farm: Farm):
    sow = await _sow(db, test_farm, "PREGNANT")
    db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2026, 4, 1),
                  mating_type="AI", mating_number=1))
    await db.flush()
    # 분만 4/06 → 임신 5일(<100) → 거부
    item = SyncFarrowing(id=uuid.uuid4(), sow_id=sow.id, farrowing_date="2026-04-06",
                         total_born=10, born_alive=10, client_created_at=_now())
    accepted, rejected, conflict = await _process_farrowing(db, test_farm.id, item, dry_run=False)
    assert accepted is None and rejected is not None and rejected.reason == "VALIDATION_FAILED", rejected
    assert "gestation_days" in (rejected.detail or {})


# ── F2: 이유 날짜순서 + 포유기간 ────────────────────────────────────
async def _lactating_with_farrowing(db, farm) -> tuple[Sow, Farrowing]:
    sow = await _sow(db, farm, "LACTATING")
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2026, 1, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 20),
                  total_born=12, born_alive=12, stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    return sow, f


async def test_sync_weaning_before_farrowing_rejected(db: AsyncSession, test_farm: Farm):
    sow, _f = await _lactating_with_farrowing(db, test_farm)
    item = SyncWeaning(id=uuid.uuid4(), sow_id=sow.id, weaning_date="2026-04-10",  # 분만(4/20) 이전
                       weaned_count=10, client_created_at=_now())
    accepted, rejected, conflict = await _process_weaning(db, test_farm.id, item, dry_run=False)
    assert accepted is None and rejected is not None and rejected.reason == "VALIDATION_FAILED", rejected


async def test_sync_weaning_nursing_too_long_rejected(db: AsyncSession, test_farm: Farm):
    sow, _f = await _lactating_with_farrowing(db, test_farm)
    # 분만 4/20 → 이유 6/25 = 66일(>60), 단 미래(today 6/30) 아님 → 포유기간 초과로 거부
    item = SyncWeaning(id=uuid.uuid4(), sow_id=sow.id, weaning_date="2026-06-25",
                       weaned_count=10, client_created_at=_now())
    accepted, rejected, conflict = await _process_weaning(db, test_farm.id, item, dry_run=False)
    assert accepted is None and rejected is not None and rejected.reason == "VALIDATION_FAILED", rejected
    assert (rejected.detail or {}).get("nursing_days") == 66


# ── F3: 사이클당 교배횟수 상한(5) ───────────────────────────────────
async def test_sync_mating_exceeds_cycle_cap_rejected(db: AsyncSession, test_farm: Farm):
    sow = await _sow(db, test_farm, "OPEN")
    cyc = BreedingCycle(farm_id=test_farm.id, sow_id=sow.id, parity=2, cycle_status="MATED",
                        started_at=datetime(2026, 4, 1, tzinfo=UTC), mating_count=5)
    db.add(cyc)
    await db.flush()
    for i in range(5):  # 이미 5건 — 상한 도달
        db.add(Mating(farm_id=test_farm.id, sow_id=sow.id, breeding_cycle_id=cyc.id,
                      mating_date=date(2026, 4, 1 + i), mating_type="AI", mating_number=i + 1))
    await db.flush()
    item = SyncMating(id=uuid.uuid4(), sow_id=sow.id, mating_date="2026-04-15",
                      mating_type="AI", client_created_at=_now())
    accepted, rejected, conflict = await _process_mating(db, test_farm.id, item, dry_run=False)
    assert accepted is None and rejected is not None and rejected.reason == "VALIDATION_FAILED", rejected
    assert "5 matings" in (rejected.detail or {}).get("message", "")


# ── F4: 재교배일 < 직전 이유일 ──────────────────────────────────────
async def test_sync_mating_before_last_weaning_rejected(db: AsyncSession, test_farm: Farm):
    sow = await _sow(db, test_farm, "OPEN")
    m = Mating(farm_id=test_farm.id, sow_id=sow.id, mating_date=date(2026, 1, 1),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=test_farm.id, sow_id=sow.id, mating_id=m.id, farrowing_date=date(2026, 4, 20),
                  total_born=12, born_alive=12, stillborn=0, mummified=0, nursing_head=12)
    db.add(f)
    await db.flush()
    db.add(Weaning(farm_id=test_farm.id, sow_id=sow.id, farrowing_id=f.id,
                   weaning_date=date(2026, 5, 11), weaned_count=11))
    await db.flush()
    # 재교배 5/05 < 직전 이유 5/11 → 거부
    item = SyncMating(id=uuid.uuid4(), sow_id=sow.id, mating_date="2026-05-05",
                      mating_type="AI", client_created_at=_now())
    accepted, rejected, conflict = await _process_mating(db, test_farm.id, item, dry_run=False)
    assert accepted is None and rejected is not None and rejected.reason == "VALIDATION_FAILED", rejected
