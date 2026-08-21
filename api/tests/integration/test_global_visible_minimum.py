"""GLOBAL = 미결정 국가의 최소 안전값 (D-10-1 A).

이번 발견의 핵심: **프론트 구현 한계가 정책처럼 보이고 있었다.**
GLOBAL seed 는 14개를 전부 visible 로 뒀는데 프론트가 4개만 그릴 수 있어서
화면상 문제가 없었다. metrics 맵 노출로 그 한계가 사라지자 결정한 적 없는 지표가
11개국에 자동 노출되는 상태가 드러났다.

★ 그래서 이 파일이 잠그는 계약은 이것이다:
    프론트 capability 가 늘어도 제품 노출은 늘지 않는다.
    확대는 COUNTRY 명시 승인으로만 일어난다.

주의: GLOBAL visible 3개는 "카드를 표시할 수 있다"까지만이다. "3개는 모든 나라에서
현지 기준까지 검증됐다"는 뜻이 아니다 — 정의/근거/benchmark/entitlement 축은 별개다.
"""
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.global_policy_defaults import GLOBAL_HIDDEN, GLOBAL_VISIBLE
from app.db.models.kpi_policy import CountryKpiPolicy
from app.services.kpi_policy_resolver import resolve_display_kpis

pytestmark = pytest.mark.anyio

# 프로덕션 실측(2026-08-21): BR 외 11개국은 COUNTRY 정책이 없다.
UNDECIDED_COUNTRIES = ("US", "CN", "KR", "MX", "VN", "PH", "TH", "DE", "ES", "DK", "NL")


def _global(kpi: str, role: str) -> CountryKpiPolicy:
    return CountryKpiPolicy(
        scope_level="GLOBAL", kpi_code=kpi, compute_enabled=True, display_role=role,
        rule_enabled=True, benchmark_exposure="CONTEXT_ONLY", prediction_feature=False,
        api_export_policy="TENANT_ONLY", decision_status="APPROVED", decided_by="test",
    )


async def _seed_global(db: AsyncSession) -> None:
    """마이그레이션 d1a4c6e8b2f5 적용 후의 GLOBAL 형상을 재현."""
    for kpi in GLOBAL_VISIBLE:
        db.add(_global(kpi, "PRIMARY"))
    for kpi in GLOBAL_HIDDEN:
        db.add(_global(kpi, "HIDDEN"))
    await db.flush()


async def test_undecided_country_sees_only_minimum(db: AsyncSession):
    """★ COUNTRY 정책이 없는 나라는 최소 3개만 본다."""
    await _seed_global(db)
    for country in UNDECIDED_COUNTRIES:
        rows = await resolve_display_kpis(db, country=country)
        got = {r.kpi_code for r in rows}
        assert got == set(GLOBAL_VISIBLE), f"{country}: {sorted(got)}"


async def test_unknown_country_code_also_minimum(db: AsyncSession):
    """분류 안 된 국가(D-10-3 UNKNOWN)도 동일 — 새 나라가 들어와도 자동 확대 없음."""
    await _seed_global(db)
    rows = await resolve_display_kpis(db, country="ZZ")
    assert {r.kpi_code for r in rows} == set(GLOBAL_VISIBLE)


async def test_hidden_kpis_are_still_computed(db: AsyncSession):
    """숨긴다고 계산까지 끄지 않는다 — 룰엔진 판정·벤치마크는 계속 돌아야 한다."""
    await _seed_global(db)
    rows = (await db.execute(select(CountryKpiPolicy).where(
        CountryKpiPolicy.scope_level == "GLOBAL",
        CountryKpiPolicy.display_role == "HIDDEN",
    ))).scalars().all()
    assert rows, "HIDDEN 시드가 있어야 의미 있는 검증"
    assert all(r.compute_enabled for r in rows), "표시만 숨기고 계산은 유지해야 한다"


# ── ★ 이번 사고의 회귀 테스트 ────────────────────────────────────────────────

async def test_new_kpi_does_not_auto_expose_in_undecided_country(db: AsyncSession):
    """★★ 새 KPI 를 시스템에 추가해도 미결정 국가의 노출은 늘지 않는다.

    이번 문제가 정확히 "프론트가 그릴 수 있게 되자 노출이 늘어난" 것이었다.
    새 지표는 GLOBAL 에 HIDDEN 으로 들어와야 하고, 켜는 것은 COUNTRY 결정이다."""
    await _seed_global(db)
    before = len(await resolve_display_kpis(db, country="US"))

    # 신규 지표 등장(metrics 맵에 새 코드가 생긴 상황을 모사)
    db.add(_global("NEW_METRIC_X", "HIDDEN"))
    await db.flush()

    after = len(await resolve_display_kpis(db, country="US"))
    assert after == before == len(GLOBAL_VISIBLE), (
        f"새 KPI 추가로 노출이 {before} → {after} 로 늘었다. "
        "신규 지표는 GLOBAL HIDDEN 으로 들어와야 하고 확대는 COUNTRY 명시 승인으로만.")


async def test_country_can_opt_in_explicitly(db: AsyncSession):
    """확대 경로는 열려 있어야 한다 — COUNTRY 에서 명시적으로 켜면 보인다."""
    await _seed_global(db)
    db.add(CountryKpiPolicy(
        scope_level="COUNTRY", country_code="BR", kpi_code="BORN_ALIVE",
        display_role="PRIMARY", decision_status="APPROVED", decided_by="test"))
    await db.flush()

    br = {r.kpi_code for r in await resolve_display_kpis(db, country="BR")}
    us = {r.kpi_code for r in await resolve_display_kpis(db, country="US")}
    assert "BORN_ALIVE" in br, "명시 승인한 국가에서는 켜져야 한다"
    assert "BORN_ALIVE" not in us, "다른 나라로 새면 안 된다"


async def test_seed_lists_are_disjoint_and_complete(db: AsyncSession):
    """SSOT 무결성 — visible/hidden 이 겹치거나 비지 않아야 한다."""
    assert not (set(GLOBAL_VISIBLE) & set(GLOBAL_HIDDEN)), "visible 과 hidden 이 겹친다"
    assert set(GLOBAL_VISIBLE) == {"PSY", "NPD", "FARROWING_RATE"}, "D-10-1 결정값"
