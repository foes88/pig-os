"""모돈폐사율·도태율·MSY 분모/소스 정정 — 라이브 발견 무결성 버그.

버그: build_herd_kpis가 도폐사를 sows에서 deleted_at IS NULL로 셌으나 도폐사 모돈은
소프트삭제(deleted_at 설정)라 항상 0 → 모돈폐사율/도태율이 상시 0(라이브: CULLED 32두인데 0).
수정: removals 원장에서 집계 + 분모를 평균 재고(스펙 §7)로.
"""
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health import Removal
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import _avg_active_inventory, build_herd_kpis

pytestmark = pytest.mark.anyio


def _sow(farm, **kw):
    kw.setdefault("status", "OPEN")
    return Sow(farm_id=farm.id, ear_tag=f"S-{uuid.uuid4().hex[:6].upper()}", parity=3,
               entry_date=datetime(2025, 6, 1, tzinfo=UTC), entry_type="GILT", **kw)


async def test_avg_inventory_counts_active_over_window(db: AsyncSession, test_farm: Farm):
    for _ in range(10):
        db.add(_sow(test_farm))
    await db.flush()
    today = date.today()
    inv = await _avg_active_inventory(db, test_farm.id, today - timedelta(days=365), today)
    assert inv == pytest.approx(10.0, abs=0.01), f"미퇴출 10두 → 평균재고 10, got {inv}"


async def test_mortality_culling_sourced_from_removals(db: AsyncSession, test_farm: Farm):
    for _ in range(10):
        db.add(_sow(test_farm))  # 활성 10두
    await db.flush()
    now = datetime.now(UTC)
    # 도폐사 5두: 현실대로 소프트삭제(deleted_at)+exit_date, removals 원장 기록
    for rt in ("DEAD", "DEAD", "CULLED", "CULLED", "CULLED"):
        s = _sow(test_farm, status=rt, exit_date=now, deleted_at=now)
        db.add(s)
        await db.flush()
        db.add(Removal(farm_id=test_farm.id, sow_id=s.id, removal_date=date(2026, 3, 1),
                       removal_type=rt))
    await db.flush()

    k = await build_herd_kpis(db, test_farm)
    # 옛 코드: sows deleted_at IS NULL 필터라 removed=0 → 폐사율/도태율 0.0. 이제 removals에서 집계 → >0.
    assert k["SOW_MORTALITY"] is not None and k["SOW_MORTALITY"] > 0, k["SOW_MORTALITY"]
    assert k["CULLING_RATE"] is not None and k["CULLING_RATE"] > 0, k["CULLING_RATE"]
