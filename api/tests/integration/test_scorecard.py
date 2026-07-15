"""무가입 스코어카드(공개) — 국가 벤치마크 대비 등급/기회 산정.

주의: 테스트 DB엔 벤치마크 시드가 없음(운영 seed 스크립트 별도) → 테스트가 KR 벤치를
default_metric_values에 직접 심고 검증. effective_metric_values 함수가 이를 읽음.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio

URL = "/api/v1/scorecard"

_SEED = text("""
INSERT INTO default_metric_values
  (scope_type, scope_code, metric_code, benchmark_avg, benchmark_top25, target_value,
   alert_direction, is_proxy, benchmark_status)
VALUES
  ('region','KR','PSY',            24.3, 27, 22, 'below', false, 'verified'),
  ('region','KR','NPD',            30,   22, 35, 'above', false, 'verified'),
  ('region','KR','FARROWING_RATE', 85,   90, 80, 'below', false, 'verified')
ON CONFLICT DO NOTHING
""")


async def _seed_kr(db: AsyncSession):
    await db.execute(_SEED)
    await db.flush()


async def test_requires_at_least_one_metric(client: AsyncClient):
    r = await client.post(URL, json={"country": "KR"})
    assert r.status_code == 422, r.text


async def test_kr_high_psy_scores_top(client: AsyncClient, db: AsyncSession):
    await _seed_kr(db)
    r = await client.post(URL, json={"country": "KR", "psy": 28})  # >top25(27)
    assert r.status_code == 200, r.text
    d = r.json()
    psy = next(m for m in d["metrics"] if m["code"] == "PSY")
    assert psy["band"] == "TOP" and psy["score"] == 100
    assert d["overall_band"] in ("TOP", "GOOD")


async def test_low_psy_becomes_opportunity(client: AsyncClient, db: AsyncSession):
    await _seed_kr(db)
    r = await client.post(URL, json={"country": "KR", "psy": 18, "npd": 40})
    assert r.status_code == 200, r.text
    d = r.json()
    assert "PSY" in [o["code"] for o in d["opportunities"]]
    psy = next(m for m in d["metrics"] if m["code"] == "PSY")
    assert psy["band"] in ("LOW", "FAIR")
    assert psy["gap_to_avg"] is not None and psy["gap_to_avg"] > 0
    npd = next(m for m in d["metrics"] if m["code"] == "NPD")
    assert npd["band"] == "LOW"  # 40 > target 35 (lower-better)


async def test_unknown_country_grades_na(client: AsyncClient):
    r = await client.post(URL, json={"country": "ZZ", "psy": 25})
    assert r.status_code == 200, r.text
    psy = next(m for m in r.json()["metrics"] if m["code"] == "PSY")
    assert psy["band"] == "NA"
