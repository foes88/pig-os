"""DashboardKpi.metrics — 정본 kpi_code → 값 일반 맵.

왜 필요한가: 스키마가 KPI 4개(psy/npd/farrowing_rate/sow_turnover)로 고정돼 있어서
KPI 를 하나 더 보여주려면 백엔드 스키마와 프론트를 같이 고쳐야 했다. 그러면
"국가 확장 = 데이터 추가" 가 여기서 깨진다(BR full target 7개 중 3개가 값이 없어
정책에 넣지도 못하던 상태 — COUNTRY_PRODUCT_SPEC_BR.md §2.1).

★ metrics 는 룰엔진이 판정에 쓰는 dict 를 그대로 노출한다. 화면 숫자와 경고 숫자가
  다른 소스에서 나오면 "카드는 정상인데 경고는 뜬다" 같은 모순이 생긴다.
"""
import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.services.kpi_service import get_dashboard

pytestmark = pytest.mark.anyio

# BR full target 중 그동안 페이로드에 없어 카드로 못 그리던 3종
BR_PENDING = ("BORN_ALIVE", "PWMR", "STILLBORN_RATE")


async def _farrowed_sow(db, farm, *, born_alive: int, stillborn: int) -> Sow:
    ref = date.today() - timedelta(days=40)
    s = Sow(farm_id=farm.id, ear_tag=f"M-{uuid.uuid4().hex[:6].upper()}", parity=2,
            status="OPEN", entry_date=datetime(2024, 1, 1, tzinfo=UTC), entry_type="GILT")
    db.add(s)
    await db.flush()
    m = Mating(farm_id=farm.id, sow_id=s.id, mating_date=ref - timedelta(days=115),
               mating_type="AI", mating_number=1)
    db.add(m)
    await db.flush()
    f = Farrowing(farm_id=farm.id, sow_id=s.id, mating_id=m.id, farrowing_date=ref,
                  total_born=born_alive + stillborn, born_alive=born_alive,
                  stillborn=stillborn, mummified=0, nursing_head=born_alive)
    db.add(f)
    await db.flush()
    db.add(Weaning(farm_id=farm.id, sow_id=s.id, farrowing_id=f.id,
                   weaning_date=ref + timedelta(days=25), weaned_count=born_alive - 1))
    await db.flush()
    return s


async def test_metrics_exposes_pending_br_kpis(db: AsyncSession, test_farm: Farm):
    """★ BR full target 3종이 페이로드에 실제로 실린다(값이 없어 못 쓰던 제약 해소)."""
    await _farrowed_sow(db, test_farm, born_alive=12, stillborn=1)
    await _farrowed_sow(db, test_farm, born_alive=11, stillborn=1)

    dash = await get_dashboard(db, test_farm)
    for code in BR_PENDING:
        assert code in dash.metrics, f"{code} 가 metrics 에 없다"
    assert dash.metrics["BORN_ALIVE"] == pytest.approx(11.5, abs=0.1)  # (12+11)/2
    assert dash.metrics["STILLBORN_RATE"] == pytest.approx(8.0, abs=0.5)  # 2/25


async def test_metrics_matches_flat_fields(db: AsyncSession, test_farm: Farm):
    """기존 평면 필드와 metrics 값이 일치 — 같은 숫자를 두 곳에서 보여주면 안 된다."""
    await _farrowed_sow(db, test_farm, born_alive=12, stillborn=1)
    dash = await get_dashboard(db, test_farm)
    for code, flat in (("PSY", dash.psy), ("NPD", dash.npd),
                       ("FARROWING_RATE", dash.farrowing_rate),
                       ("SOW_TURNOVER", dash.sow_turnover)):
        assert dash.metrics.get(code) == flat, f"{code}: metrics={dash.metrics.get(code)} flat={flat}"


async def test_metrics_is_same_source_as_rule_engine(db: AsyncSession, test_farm: Farm):
    """★ 경고를 낸 값과 카드에 보이는 값이 같아야 한다.

    알림(finding)이 들고 있는 current_value 가 metrics 의 같은 코드 값과 일치하는지 확인."""
    await _farrowed_sow(db, test_farm, born_alive=6, stillborn=4)  # 낮은 산자수 → 경고 유발
    dash = await get_dashboard(db, test_farm)
    checked = 0
    for a in dash.alerts:
        if a.current_value is None or a.kpi not in dash.metrics:
            continue
        if dash.metrics[a.kpi] is None:
            continue
        assert a.current_value == pytest.approx(dash.metrics[a.kpi], abs=0.05), (
            f"{a.kpi}: 경고값 {a.current_value} vs 표시값 {dash.metrics[a.kpi]}")
        checked += 1
    assert checked > 0, "대조할 알림이 없어 검증이 무의미 — 픽스처가 경고를 내야 한다"


async def test_metrics_absent_values_are_none_not_dropped(db: AsyncSession, test_farm: Farm):
    """데이터가 없으면 키를 빼는 게 아니라 None — 프론트가 '없음'을 구분할 수 있어야 한다."""
    dash = await get_dashboard(db, test_farm)  # 이벤트 0건 농장
    assert dash.metrics, "빈 농장이어도 metrics 자체는 있어야 한다"
    assert any(v is None for v in dash.metrics.values())
