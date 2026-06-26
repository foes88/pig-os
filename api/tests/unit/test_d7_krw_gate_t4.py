"""
TRACK4 게이트 B — D-7 원화누수 게이트.
loss.sow_culling(SOW_RESIDUAL/SALVAGE, KRW)은 country='KR'일 때만 발화. 非KR 침묵.
보편 손실룰(preweaning/pregnancy_accident/npd)은 country 무관 유지(회귀).
"""
from uuid import uuid4

import pytest

from app.engine.rule_engine import RuleContext
from app.engine.rules.loss import _loss_sow_culling

pytestmark = pytest.mark.anyio

_BENCH = {
    "SOW_RESIDUAL_P0": {"target": 8400000, "unit": "KRW"},
    "SOW_RESIDUAL_P1": {"target": 7100000},
    "SOW_SALVAGE_CULL": {"target": 300000},
    "SOW_SALVAGE_DEATH": {"target": 0},
}
_LI = {"cull_by_parity": [{"parity": 1, "status": "CULLED", "count": 1}]}


def _ctx(country):
    return RuleContext(farm_id=uuid4(), country=country, kpi={}, benchmarks=_BENCH,
                       sow_counts={}, extra={"loss_inputs": _LI})


async def test_kr_sow_culling_fires():
    out = await _loss_sow_culling(_ctx("KR"))
    assert len(out) == 1 and out[0].rule_id == "loss.sow_culling"


@pytest.mark.parametrize("country", ["US", "BR", "VN", "default", ""])
async def test_non_kr_sow_culling_silent(country):
    """非KR: 원화 잔존가 누수 차단 → 발화 0."""
    assert await _loss_sow_culling(_ctx(country)) == []


async def test_kr_lowercase_also_fires():
    """country 'kr' 소문자도 KR로 인정(대소문자 무관)."""
    out = await _loss_sow_culling(_ctx("kr"))
    assert len(out) == 1
