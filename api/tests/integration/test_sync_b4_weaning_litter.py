"""
B4 회귀 가드 — /sync 이유두수 ≤ 잔여 유효복당 + 처리순서 재정렬(piglet_events → weanings).

핵심:
- 과잉이유(weaned > 유효복당) 차단(두수 오염 방지).
- nurse sow(양자 받음)가 자기 born_alive보다 많이 이유해도 **오거부 안 됨**(양자가 이유보다 먼저 처리).
- 폐사가 이유보다 먼저 반영돼 유효복당이 줄어든 경우도 정확히 차단.
"""
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.schemas.sync import (
    SyncChanges,
    SyncFarrowing,
    SyncMating,
    SyncPigletEvent,
    SyncRequest,
    SyncWeaning,
)
from app.services import sync_service

NOW = datetime.now(UTC)


def _mating(sid):
    return SyncMating(id=uuid4(), sow_id=sid, mating_date="2026-01-01",
                      mating_type="AI", mating_number=1, client_created_at=NOW)


def _farrowing(sid, ba):
    return SyncFarrowing(id=uuid4(), sow_id=sid, farrowing_date="2026-04-25",
                         total_born=ba, born_alive=ba, born_dead=0, mummies=0, client_created_at=NOW)


def _piglet(sid, etype, n):
    return SyncPigletEvent(id=uuid4(), sow_id=sid, event_date="2026-05-05",
                           event_type=etype, piglet_count=n,
                           reason="CRUSHING" if etype == "DEATH" else None, client_created_at=NOW)


def _weaning(sid, wc):
    return SyncWeaning(id=uuid4(), sow_id=sid, weaning_date="2026-05-16",
                       weaned_count=wc, client_created_at=NOW)


async def _run(db, farm, sow, *, ba, piglets=None, weaned):
    req = SyncRequest(
        farm_id=farm.id, client_id=uuid4(), last_sync_at=None, dry_run=False,
        changes=SyncChanges(
            matings=[_mating(sow.id)],
            farrowings=[_farrowing(sow.id, ba)],
            piglet_events=[_piglet(sow.id, t, n) for (t, n) in (piglets or [])],
            weanings=[_weaning(sow.id, weaned)],
        ),
    )
    return await sync_service.process_sync(db, farm, req)


def _weaning_rejected(resp):
    return [r for r in resp.rejected if r.entity == "weaning"]


async def test_over_weaning_rejected(db: AsyncSession, test_farm: Farm, test_sow: Sow):
    """farrow BA=10, wean 15 → 유효복당 10 초과 → REJECTED(두수 오염 차단)."""
    resp = await _run(db, test_farm, test_sow, ba=10, weaned=15)
    rej = _weaning_rejected(resp)
    assert rej and rej[0].reason == "VALIDATION_FAILED", f"expected reject, got {resp.accepted}"
    # 영속 안 됨
    w = await db.scalar(select(Weaning).where(Weaning.sow_id == test_sow.id, Weaning.deleted_at.is_(None)))
    assert w is None


async def test_normal_weaning_accepted(db: AsyncSession, test_farm: Farm, test_sow: Sow):
    """farrow BA=12, wean 10 → 정상 → ACCEPTED."""
    resp = await _run(db, test_farm, test_sow, ba=12, weaned=10)
    assert _weaning_rejected(resp) == []
    w = await db.scalar(select(Weaning).where(Weaning.sow_id == test_sow.id, Weaning.deleted_at.is_(None)))
    assert w is not None and w.weaned_count == 10


async def test_nurse_sow_foster_in_not_falsely_rejected(db: AsyncSession, test_farm: Farm, test_sow: Sow):
    """farrow BA=10, FOSTER_IN 5 → 유효 15, wean 14 → ACCEPTED.
    처리순서 재정렬(piglet_events→weanings)로 양자가 먼저 반영돼야 오거부되지 않는다."""
    resp = await _run(db, test_farm, test_sow, ba=10, piglets=[("FOSTER_IN", 5)], weaned=14)
    assert _weaning_rejected(resp) == [], f"nurse sow falsely rejected: {resp.rejected}"
    w = await db.scalar(select(Weaning).where(Weaning.sow_id == test_sow.id, Weaning.deleted_at.is_(None)))
    assert w is not None and w.weaned_count == 14


async def test_death_reduces_effective_litter(db: AsyncSession, test_farm: Farm, test_sow: Sow):
    """farrow BA=12, DEATH 5 → 유효 7, wean 8 → REJECTED.
    폐사가 이유보다 먼저 처리돼 유효복당이 줄어야 한다."""
    resp = await _run(db, test_farm, test_sow, ba=12, piglets=[("DEATH", 5)], weaned=8)
    rej = _weaning_rejected(resp)
    assert rej and rej[0].reason == "VALIDATION_FAILED", f"expected reject, got {resp.accepted}"
