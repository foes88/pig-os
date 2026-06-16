"""
Regression guard — /sync farrowing + piglet_event MUST persist (BACKEND_FIXES #8).

This path regressed twice: `_process_farrowing` used wrong ORM kwargs
(born_dead/mummies/farrowing_type vs model stillborn/mummified/farrowing_ease) and omitted
mating_id, so mobile /sync farrowings were silently rejected. The direct POST /events path was
covered by tests but the /sync path was not — hence the silent regressions.
"""
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, PigletEvent
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.schemas.sync import (
    SyncChanges,
    SyncFarrowing,
    SyncMating,
    SyncPigletEvent,
    SyncRequest,
)
from app.services import sync_service


async def test_sync_mating_farrowing_piglet_roundtrip(db: AsyncSession, test_farm: Farm, test_sow: Sow):
    """One /sync batch: mating→farrowing→piglet_event all accepted + persisted (no silent reject)."""
    assert test_sow.status == "GILT"
    now = datetime.now(UTC)
    req = SyncRequest(
        farm_id=test_farm.id,
        client_id=uuid4(),
        last_sync_at=None,
        dry_run=False,
        changes=SyncChanges(
            matings=[SyncMating(
                id=uuid4(), sow_id=test_sow.id, mating_date="2026-01-01",
                mating_type="AI", mating_number=1, client_created_at=now,
            )],
            farrowings=[SyncFarrowing(
                id=uuid4(), sow_id=test_sow.id, farrowing_date="2026-04-25",
                total_born=13, born_alive=12, born_dead=1, mummies=0,
                farrowing_type="NORMAL", client_created_at=now,
            )],
            piglet_events=[SyncPigletEvent(
                id=uuid4(), sow_id=test_sow.id, event_date="2026-04-26",
                event_type="DEATH", piglet_count=1, reason="CRUSHING", client_created_at=now,
            )],
        ),
    )

    resp = await sync_service.process_sync(db, test_farm, req)

    # #8 regression guard: nothing silently rejected
    assert resp.rejected == [], f"unexpected rejects: {resp.rejected}"
    assert len(resp.accepted) == 3

    # persisted with correct column mapping (born_dead -> stillborn)
    farrowing = await db.scalar(
        select(Farrowing).where(Farrowing.sow_id == test_sow.id, Farrowing.deleted_at.is_(None))
    )
    assert farrowing is not None
    assert farrowing.stillborn == 1
    assert farrowing.mating_id is not None        # NOT NULL FK linked

    piglet = await db.scalar(select(PigletEvent).where(PigletEvent.sow_id == test_sow.id))
    assert piglet is not None
    assert piglet.farrowing_id == farrowing.id     # auto-linked to the same-batch farrowing

    await db.refresh(test_sow)
    assert test_sow.status == "LACTATING"          # farrowing advanced status
