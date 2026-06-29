"""F1 — 오프라인 sync 멱등성 by-id 조회가 농장 미스코프라 교차농장 PK 충돌이
무성 데이터 손실(merge로 둔갑)·전역 PK 유니크 충돌(500)을 유발하던 결함.

농장 A가 농장 B의 mating UUID를 자기 item.id로 보내면, 과거엔 'merged'로 응답하며
A의 정상 레코드가 조용히 사라졌다. 이제 ID_CONFLICT로 거부(B 데이터는 불변).
"""
import uuid
from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Mating
from app.db.models.platform import Farm, Organization
from app.db.models.sow import Sow
from app.schemas.sync import SyncMating
from app.services.sync_service import _process_mating

pytestmark = pytest.mark.anyio


async def _farm(db, org) -> Farm:
    f = Farm(org_id=org.id, farm_code=f"F-{uuid.uuid4().hex[:6].upper()}",
             name="F", country="KR", timezone="Asia/Seoul", active=True)
    db.add(f)
    await db.flush()
    return f


async def _sow(db, farm) -> Sow:
    s = Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=0,
            status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    return s


async def test_foreign_farm_pk_rejected_not_merged(
    db: AsyncSession, test_org: Organization, test_farm: Farm,
):
    farm_b = await _farm(db, test_org)
    sow_b = await _sow(db, farm_b)
    # 농장 B의 기존 교배
    mating_b = Mating(farm_id=farm_b.id, sow_id=sow_b.id, mating_date=date(2026, 5, 1),
                      mating_type="AI", mating_number=1)
    db.add(mating_b)
    await db.flush()

    # 농장 A가 B의 mating UUID를 자기 신규 교배 id로 사용
    sow_a = await _sow(db, test_farm)
    item = SyncMating(id=mating_b.id, sow_id=sow_a.id, mating_date="2026-05-02",
                      mating_type="AI", client_created_at=datetime(2026, 5, 2, tzinfo=UTC))
    accepted, rejected, conflict = await _process_mating(db, test_farm.id, item, dry_run=False)

    assert accepted is None, "교차농장 PK는 merge로 수용되면 안 됨(무성 손실)"
    assert rejected is not None and rejected.reason == "ID_CONFLICT", rejected
    # 농장 B의 원본은 그대로
    assert (await db.get(Mating, mating_b.id)).farm_id == farm_b.id


async def test_same_farm_pk_still_merges(
    db: AsyncSession, test_org: Organization, test_farm: Farm,
):
    sow_a = await _sow(db, test_farm)
    mating = Mating(farm_id=test_farm.id, sow_id=sow_a.id, mating_date=date(2026, 5, 1),
                    mating_type="AI", mating_number=1)
    db.add(mating)
    await db.flush()
    # 같은 농장 동일 UUID 재전송 → 멱등 merge 유지
    item = SyncMating(id=mating.id, sow_id=sow_a.id, mating_date="2026-05-01",
                      mating_type="AI", client_created_at=datetime(2026, 5, 1, tzinfo=UTC))
    accepted, rejected, conflict = await _process_mating(db, test_farm.id, item, dry_run=False)
    assert rejected is None
    assert accepted is not None and accepted.action == "merged"
