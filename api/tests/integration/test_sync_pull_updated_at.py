"""#7 — 오프라인 sync pull이 서버측 수정·소프트삭제를 감지한다(updated_at 기반).

이벤트 모델에 updated_at이 없던 시절엔 created_at만 봐서, since 이전에 생성됐지만
이후 수정/삭제된 행이 모바일로 내려가지 않았음. updated_at(onupdate) 추가로 해소.
"""
from datetime import UTC, date, datetime

import pytest

from app.db.models.events import Mating, ReproductiveEvent
from app.services.sync_service import _pull_server_changes

pytestmark = pytest.mark.anyio


async def _old_mating(db, farm, sow):
    m = Mating(farm_id=farm.id, sow_id=sow.id, mating_date=date(2026, 1, 10),
               mating_type="AI", mating_number=1,
               created_at=datetime(2026, 1, 10, tzinfo=UTC),
               updated_at=datetime(2026, 1, 10, tzinfo=UTC))
    db.add(m)
    await db.flush()
    return m


async def test_pull_detects_server_side_edit(db, test_farm, test_sow):
    m = await _old_mating(db, test_farm, test_sow)
    since = datetime(2026, 6, 1, tzinfo=UTC)  # 생성(1/10) 이후

    # 서버측 수정 → onupdate가 updated_at를 now로 갱신
    m.mating_type = "NATURAL"
    await db.flush()

    changes = await _pull_server_changes(db, test_farm.id, since)
    assert any(str(x["id"]) == str(m.id) for x in changes.matings), \
        "since 이전 생성·이후 수정된 교배는 pull되어야 함(created_at만 봤다면 누락)"


async def test_pull_detects_server_side_softdelete(db, test_farm, test_sow):
    m = await _old_mating(db, test_farm, test_sow)
    since = datetime(2026, 6, 1, tzinfo=UTC)

    # 소프트삭제도 UPDATE → updated_at 갱신 → 삭제 tombstone이 deleted_ids에 잡힘
    m.deleted_at = datetime(2026, 6, 15, tzinfo=UTC)
    await db.flush()

    changes = await _pull_server_changes(db, test_farm.id, since)
    assert str(m.id) in changes.deleted_ids, "since 이후 소프트삭제는 deleted_ids에 포함되어야 함"


async def test_pull_reproductive_softdelete_in_deleted_ids(db, test_farm, test_sow):
    """코드리뷰 #1 — repro/health/piglet 소프트삭제도 deleted_ids로 전파(과거 누락)."""
    r = ReproductiveEvent(farm_id=test_farm.id, sow_id=test_sow.id, event_type="ABORTION",
                          event_date=date(2026, 1, 10),
                          created_at=datetime(2026, 1, 10, tzinfo=UTC),
                          updated_at=datetime(2026, 1, 10, tzinfo=UTC))
    db.add(r)
    await db.flush()
    since = datetime(2026, 6, 1, tzinfo=UTC)
    r.deleted_at = datetime(2026, 6, 15, tzinfo=UTC)
    await db.flush()

    changes = await _pull_server_changes(db, test_farm.id, since)
    assert str(r.id) in changes.deleted_ids, "repro 소프트삭제 tombstone이 모바일로 전파돼야 함"
