"""
KPI calculation service — Base tier.

PSY, MSY, NPD from DB views + Rule Engine alerts.
Benchmarks resolved via effective_metric_values() DB function (farm → region → market → system).
"""
from datetime import date
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.config import FarmConfig
from app.db.models.sow import Sow
from app.db.models.platform import Farm
from app.engine import RuleContext, RuleEngine, StructuredResult
from app.engine.rules import base as _base_rules  # ensure rules are registered  # noqa: F401
from app.schemas.kpi import Alert, DashboardKpi, NpdBreakdown, PsyDetail

_DEFAULT_NPD_ALERT = 35


async def _get_benchmark(db: AsyncSession, metric_code: str, farm: Farm) -> dict:
    rows = await db.execute(
        text(
            "SELECT * FROM effective_metric_values(:farm_code, :region_code, :market_code)"
        ),
        {"farm_code": str(farm.id), "region_code": farm.country, "market_code": "SYSTEM"},
    )
    for row in rows:
        if row.metric_code == metric_code:
            return {
                "avg":    float(row.benchmark_avg)  if row.benchmark_avg  else None,
                "top25":  float(row.benchmark_top25) if row.benchmark_top25 else None,
                "target": float(row.target_value)   if row.target_value   else None,
                "unit":   row.unit_code or "",
            }
    return {"avg": None, "top25": None, "target": None, "unit": ""}



async def calculate_psy(db: AsyncSession, farm_id: UUID, year: int) -> PsyDetail | None:
    """Annual PSY from v_farm_psy DB view."""
    row = await db.execute(
        text(
            """
            SELECT avg_sow_count, total_weaned, psy
            FROM v_farm_psy
            WHERE farm_id = :farm_id
              AND EXTRACT(YEAR FROM year_start) = :year
            """
        ),
        {"farm_id": str(farm_id), "year": year},
    )
    result = row.fetchone()
    if not result:
        return None
    return PsyDetail(
        farm_id=farm_id,
        year=year,
        avg_sow_count=result.avg_sow_count or 0,
        total_weaned=result.total_weaned or 0,
        psy=float(result.psy) if result.psy else None,
        benchmark_avg=None,
        target_value=None,
    )


async def calculate_npd_breakdown(
    db: AsyncSession,
    farm_id: UUID,
    period_start: date,
    period_end: date,
) -> NpdBreakdown:
    """Average NPD (weaning→mating) from v_sow_npd view."""
    row = await db.execute(
        text(
            """
            SELECT AVG(wei_days) AS avg_wei_days
            FROM v_sow_npd
            WHERE farm_id = :farm_id
              AND weaning_date BETWEEN :start AND :end
              AND wei_days IS NOT NULL
            """
        ),
        {"farm_id": str(farm_id), "start": period_start, "end": period_end},
    )
    result = row.fetchone()
    avg_npd = float(result.avg_wei_days) if result and result.avg_wei_days else None

    return NpdBreakdown(
        farm_id=farm_id,
        period_start=period_start,
        period_end=period_end,
        avg_npd=avg_npd,
        weaning_to_mating_days=avg_npd,
        return_to_estrus_days=None,
        empty_days=None,
        npd_target=None,
        benchmark_avg=None,
    )


async def _sow_counts(db: AsyncSession, farm_id: UUID) -> dict[str, int]:
    rows = await db.execute(
        select(Sow.status, func.count().label("cnt"))
        .where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        .group_by(Sow.status)
    )
    return {row.status: row.cnt for row in rows}


async def build_rule_context(
    db: AsyncSession,
    farm: Farm,
    kpi_overrides: dict | None = None,
) -> RuleContext:
    """
    Assemble RuleContext from live KPI values and benchmarks.
    kpi_overrides lets callers pass pre-computed KPI values (e.g. from snapshots).
    """
    today = date.today()
    year  = today.year

    # Sow counts
    counts = await _sow_counts(db, farm.id)

    # Resolve benchmarks
    psy_bench = await _get_benchmark(db, "PSY", farm)
    npd_bench = await _get_benchmark(db, "NPD", farm)

    # KPI values
    if kpi_overrides:
        kpi = kpi_overrides
    else:
        psy_detail = await calculate_psy(db, farm.id, year)
        npd_detail = await calculate_npd_breakdown(
            db, farm.id, date(today.year, 1, 1), today
        )
        kpi = {
            "PSY": psy_detail.psy if psy_detail else None,
            "NPD": npd_detail.avg_npd,
        }

    return RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi=kpi,
        benchmarks={
            "PSY": psy_bench,
            "NPD": npd_bench,
        },
        sow_counts=counts,
        as_of=today,
    )


async def get_dashboard(db: AsyncSession, farm: Farm) -> DashboardKpi:
    today = date.today()
    year  = today.year

    # NPD alert threshold from farm config
    cfg = await db.scalar(
        select(FarmConfig).where(
            FarmConfig.farm_id == farm.id,
            FarmConfig.config_key == "NPD_ALERT_THRESHOLD",
        )
    )
    npd_threshold = int(cfg.config_value) if cfg else _DEFAULT_NPD_ALERT

    # PSY
    psy_detail = await calculate_psy(db, farm.id, year)
    psy_bench  = await _get_benchmark(db, "PSY", farm)
    psy_value  = psy_detail.psy if psy_detail else None

    # NPD (year-to-date)
    npd_detail = await calculate_npd_breakdown(db, farm.id, date(today.year, 1, 1), today)
    npd_bench  = await _get_benchmark(db, "NPD", farm)

    # Sow counts
    counts = await _sow_counts(db, farm.id)

    # Farrowing rate (year-to-date): farrowings / matings
    from app.db.models.events import Farrowing, Mating
    mating_count = await db.scalar(
        select(func.count()).select_from(Mating).where(
            Mating.farm_id == farm.id,
            Mating.mating_date >= date(today.year, 1, 1),
        )
    )
    farrowing_count = await db.scalar(
        select(func.count()).select_from(Farrowing).where(
            Farrowing.farm_id == farm.id,
            Farrowing.farrowing_date >= date(today.year, 1, 1),
        )
    )
    farrowing_rate = (farrowing_count / mating_count * 100) if mating_count else None

    # Rule Engine — base tier only (no addon subscriptions needed)
    ctx = RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi={"PSY": psy_value, "NPD": npd_detail.avg_npd, "FARROWING_RATE": farrowing_rate},
        benchmarks={"PSY": psy_bench, "NPD": npd_bench},
        sow_counts=counts,
    )
    result: StructuredResult = await RuleEngine.evaluate(ctx, intent="dashboard")

    alerts = [
        Alert(
            rule_id=f.rule_id,
            kpi=f.kpi,
            severity=f.severity,
            message=f.kpi + (f": {f.current_value:.1f}" if f.current_value is not None else ""),
            current_value=f.current_value,
            target_value=f.target_value,
        )
        for f in result.findings
        if f.severity in ("WARNING", "CRITICAL")
    ]

    return DashboardKpi(
        farm_id=farm.id,
        as_of=today,
        psy=psy_value,
        npd=npd_detail.avg_npd,
        farrowing_rate=farrowing_rate,
        active_sows=sum(counts.get(s, 0) for s in ("ACTIVE", "GESTATING", "LACTATING", "WEANED", "DRY")),
        gestating=counts.get("GESTATING", 0),
        lactating=counts.get("LACTATING", 0),
        weaned=counts.get("WEANED", 0),
        alerts=alerts,
    )
