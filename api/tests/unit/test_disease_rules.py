"""질병 유병률 룰 (app/engine/rules/disease.py) — 기존 직접 테스트 없음.

ctx.extra['recent_notifiable_diseases'] + ctx.country 로 심각도 판정:
ENDEMIC/EPIDEMIC→CRITICAL, MODERATE/SPORADIC→WARNING, FREE/ABSENT→INFO(수입의심), 그외 skip.
DB 불필요 — RuleContext 직접 구성.
"""
import uuid

import pytest

from app.engine.rule_engine import RuleContext, Severity
from app.engine.rules.disease import _disease_endemic_risk

pytestmark = pytest.mark.anyio


def _ctx(country: str, diseases: list[dict]) -> RuleContext:
    return RuleContext(
        farm_id=uuid.UUID("00000000-0000-0000-0000-0000000000d1"),
        country=country,
        kpi={},
        benchmarks={},
        sow_counts={},
        extra={"recent_notifiable_diseases": diseases},
    )


def _one(code="ASF", prevalence=None, count=3):
    return {"disease_code": code, "label_en": code, "prevalence": prevalence or {}, "event_count": count}


async def test_no_events_returns_empty():
    assert await _disease_endemic_risk(_ctx("KR", [])) == []


async def test_endemic_is_critical():
    f = await _disease_endemic_risk(_ctx("KR", [_one("ASF", {"KR": "ENDEMIC"})]))
    assert len(f) == 1
    assert f[0].severity == Severity.CRITICAL
    assert f[0].detail["prevalence_status"] == "ENDEMIC"
    assert "notify_veterinary_authority" in f[0].recommended_actions


async def test_epidemic_is_critical():
    f = await _disease_endemic_risk(_ctx("KR", [_one("FMD", {"KR": "EPIDEMIC"})]))
    assert f[0].severity == Severity.CRITICAL


async def test_moderate_and_sporadic_are_warning():
    for st in ("MODERATE", "SPORADIC"):
        f = await _disease_endemic_risk(_ctx("KR", [_one("PRRS", {"KR": st})]))
        assert f[0].severity == Severity.WARNING


async def test_free_region_is_info_import_case():
    f = await _disease_endemic_risk(_ctx("KR", [_one("CSF", {"KR": "FREE"})]))
    assert f[0].severity == Severity.INFO
    assert "verify_animal_origin_and_import_health_certificates" in f[0].recommended_actions


async def test_unknown_or_other_country_skipped():
    # 해당국 유병률 데이터 없음(다른 나라만) → UNKNOWN → skip
    f = await _disease_endemic_risk(_ctx("KR", [_one("ASF", {"US": "ENDEMIC"})]))
    assert f == []


async def test_country_specific_and_multiple_events():
    diseases = [
        _one("ASF", {"KR": "ENDEMIC"}),
        _one("PRRS", {"KR": "SPORADIC"}),
        _one("FMD", {"US": "ENDEMIC"}),  # KR 데이터 없음 → skip
    ]
    f = await _disease_endemic_risk(_ctx("KR", diseases))
    sev = {finding.detail["disease_code"]: finding.severity for finding in f}
    assert sev == {"ASF": Severity.CRITICAL, "PRRS": Severity.WARNING}
