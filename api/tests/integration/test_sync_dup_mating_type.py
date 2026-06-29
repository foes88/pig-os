"""#3 — sync 중복 교배 판정이 mating_type까지 일치해야 함.

같은 모돈·같은 날이라도 교배유형이 다르면(AI vs NATURAL) 서로 다른 교배 → 중복 아님.
type을 빼면 무음 병합(merged)으로 데이터 손실. (상태가드 때문에 실제 재현은 제한적이나
중복 분류 로직 자체를 직접 검증.)
"""
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.db.models.events import Mating
from app.schemas.sync import SyncMating
from app.services.sync_service import _process_mating

pytestmark = pytest.mark.anyio


def _item(sow_id, mtype, when):
    return SyncMating(id=uuid4(), sow_id=sow_id, mating_date="2026-05-01",
                      mating_type=mtype, mating_number=1, client_created_at=when)


async def test_same_date_different_type_not_duplicate(db, test_farm, test_sow):
    test_sow.status = "OPEN"
    # 기존 AI 교배(서버측, 2시간 전 생성)
    db.add(Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 5, 1),
                  mating_type="AI", mating_number=1,
                  created_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC)))
    await db.flush()

    # NATURAL 같은 날 → 다른 유형이라 중복 아님 → 수용(dry_run, 미작성)
    acc, rej, con = await _process_mating(
        db, test_farm.id, _item(test_sow.id, "NATURAL", datetime(2026, 5, 1, 5, 0, tzinfo=UTC)),
        dry_run=True)
    assert acc is not None and con is None, f"NATURAL should not be a duplicate of AI (rej={rej})"


async def test_same_date_same_type_is_duplicate_conflict(db, test_farm, test_sow):
    test_sow.status = "OPEN"
    db.add(Mating(farm_id=test_farm.id, sow_id=test_sow.id, mating_date=date(2026, 5, 1),
                  mating_type="AI", mating_number=1,
                  created_at=datetime(2026, 5, 1, 0, 0, tzinfo=UTC)))
    await db.flush()

    # AI 같은 날(병합창 밖, 5시간 차) → 같은 유형이라 중복 → 충돌
    acc, rej, con = await _process_mating(
        db, test_farm.id, _item(test_sow.id, "AI", datetime(2026, 5, 1, 5, 0, tzinfo=UTC)),
        dry_run=True)
    assert con is not None and con.conflict_type == "DUPLICATE_EVENT"
