"""
KPI calculation service — Base tier.

PSY, MSY, NPD from DB views + Rule Engine alerts.
Benchmarks resolved via effective_metric_values() DB function
(farm → region → market → system).
"""
from datetime import date
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health import HealthEvent
from app.db.models.master import DiseaseCode
from app.db.models.platform import Farm
from app.db.models.sow import Sow
from app.engine import RuleContext, RuleEngine, StructuredResult
from app.engine.rules import (
    base as _base_rules,  # ensure rules are registered  # noqa: F401
)
from app.engine.rules import (
    disease as _disease_rules,  # noqa: F401
)
from app.schemas.kpi import Alert, DashboardKpi, KpiBenchmark, KpiTrend, NpdBreakdown, PsyDetail
from app.services.rule_config_service import load_rule_configs


async def _get_benchmark(db: AsyncSession, metric_code: str, farm: Farm) -> dict:
    rows = await db.execute(
        text(
            "SELECT * FROM effective_metric_values"
            "(:farm_code, :region_code, :market_code)"
        ),
        {"farm_code": str(farm.id), "region_code": farm.country, "market_code": "SYSTEM"},  # noqa: E501
    )
    for row in rows:
        if row.metric_code == metric_code:
            return {
                "avg":       float(row.benchmark_avg)      if row.benchmark_avg      else None,  # noqa: E501
                "top25":     float(row.benchmark_top25)    if row.benchmark_top25    else None,  # noqa: E501
                "target":    float(row.target_value)       if row.target_value       else None,  # noqa: E501
                "warning":   float(row.warning_threshold)  if row.warning_threshold  else None,  # noqa: E501
                "critical":  float(row.critical_threshold) if row.critical_threshold else None,  # noqa: E501
                "direction": str(row.alert_direction)      if row.alert_direction     else "below",  # noqa: E501
                "unit":      row.unit_code or "",
            }
    return {
        "avg": None, "top25": None, "target": None,
        "warning": None, "critical": None, "direction": "below", "unit": "",
    }



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


async def _recent_notifiable_diseases(db: AsyncSession, farm_id: UUID) -> list[dict]:
    """
    Query health events from the last 30 days that have a notifiable disease_code.
    Returns aggregated list for disease rule injection.
    """
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=30)
    rows = await db.execute(
        select(
            HealthEvent.disease_code,
            func.count().label("event_count"),
        )
        .where(
            HealthEvent.farm_id == farm_id,
            HealthEvent.disease_code.isnot(None),
            HealthEvent.event_date >= cutoff,
            HealthEvent.deleted_at.is_(None),
        )
        .group_by(HealthEvent.disease_code)
    )
    disease_events = {row.disease_code: row.event_count for row in rows}
    if not disease_events:
        return []

    disease_rows = await db.scalars(
        select(DiseaseCode).where(
            DiseaseCode.disease_code.in_(list(disease_events.keys())),
            DiseaseCode.notifiable.is_(True),
        )
    )
    return [
        {
            "disease_code": d.disease_code,
            "label_en": d.label_en,
            "prevalence": d.regional_prevalence or {},
            "event_count": disease_events[d.disease_code],
        }
        for d in disease_rows
    ]


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

    # Disease prevalence extra context
    notifiable_diseases = await _recent_notifiable_diseases(db, farm.id)

    # 운영자 규칙 설정(임계/활성) — 행 없으면 빈 dict → 엔진이 코드 기본값으로 폴백
    rule_configs = await load_rule_configs(db)

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
        extra={"recent_notifiable_diseases": notifiable_diseases, "rule_configs": rule_configs},
    )


async def get_trend(db: AsyncSession, farm_id: UUID, months: int = 6) -> list[KpiTrend]:
    """
    Monthly KPI trend for the last N months.
    PSY is annualized from monthly weanings / current active sow count.
    """
    months = max(1, min(months, 24))
    rows = await db.execute(
        text(
            """
            WITH months AS (
                SELECT (date_trunc('month', CURRENT_DATE)
                    - make_interval(months => s))::date AS m
                FROM generate_series(0, :months - 1) AS s
            ),
            sow_cnt AS (
                SELECT COUNT(*)::float AS n
                FROM sows
                WHERE farm_id = :farm_id AND deleted_at IS NULL
            ),
            weans_by_month AS (
                SELECT date_trunc('month', weaning_date)::date AS m,
                       COUNT(*)::float AS cnt
                FROM weanings
                WHERE farm_id = :farm_id
                  AND weaning_date >= (date_trunc('month', CURRENT_DATE)
                      - make_interval(months => :months - 1))
                GROUP BY 1
            ),
            farrows_by_month AS (
                SELECT date_trunc('month', farrowing_date)::date AS m,
                       COUNT(*)::float AS cnt
                FROM farrowings
                WHERE farm_id = :farm_id
                  AND farrowing_date >= (date_trunc('month', CURRENT_DATE)
                      - make_interval(months => :months - 1))
                GROUP BY 1
            ),
            matings_by_month AS (
                SELECT date_trunc('month', mating_date)::date AS m,
                       COUNT(*)::float AS cnt
                FROM matings
                WHERE farm_id = :farm_id
                  AND mating_date >= (date_trunc('month', CURRENT_DATE)
                      - make_interval(months => :months - 1))
                GROUP BY 1
            ),
            npd_by_month AS (
                SELECT date_trunc('month', weaning_date)::date AS m,
                       AVG(wei_days) AS avg_npd
                FROM v_sow_npd
                WHERE farm_id = :farm_id
                  AND weaning_date >= (date_trunc('month', CURRENT_DATE)
                      - make_interval(months => :months - 1))
                  AND wei_days IS NOT NULL
                GROUP BY 1
            )
            SELECT
                to_char(months.m, 'YYYY-MM') AS period,
                CASE
                    WHEN sow_cnt.n > 0 AND weans_by_month.cnt IS NOT NULL
                    THEN ROUND(((weans_by_month.cnt / sow_cnt.n) * 12)::numeric, 1)
                    ELSE NULL
                END AS psy,
                ROUND(npd_by_month.avg_npd::numeric, 1) AS npd,
                CASE
                    WHEN matings_by_month.cnt > 0 AND farrows_by_month.cnt IS NOT NULL
                    THEN ROUND(
                        (farrows_by_month.cnt / matings_by_month.cnt * 100)::numeric, 1
                    )
                    ELSE NULL
                END AS farrowing_rate
            FROM months
            CROSS JOIN sow_cnt
            LEFT JOIN weans_by_month   ON weans_by_month.m   = months.m
            LEFT JOIN farrows_by_month ON farrows_by_month.m = months.m
            LEFT JOIN matings_by_month ON matings_by_month.m = months.m
            LEFT JOIN npd_by_month     ON npd_by_month.m     = months.m
            ORDER BY months.m
            """
        ),
        {"farm_id": str(farm_id), "months": months},
    )
    return [
        KpiTrend(
            period=row.period,
            psy=float(row.psy) if row.psy is not None else None,
            npd=float(row.npd) if row.npd is not None else None,
            farrowing_rate=(
                float(row.farrowing_rate) if row.farrowing_rate is not None else None
            ),
        )
        for row in rows
    ]


async def get_dashboard(db: AsyncSession, farm: Farm) -> DashboardKpi:
    today = date.today()
    year  = today.year

    # PSY
    psy_detail = await calculate_psy(db, farm.id, year)
    psy_bench  = await _get_benchmark(db, "PSY", farm)
    psy_value  = psy_detail.psy if psy_detail else None

    # NPD (year-to-date)
    npd_detail = await calculate_npd_breakdown(  # noqa: E501
        db, farm.id, date(today.year, 1, 1), today
    )
    npd_bench  = await _get_benchmark(db, "NPD", farm)

    # Sow counts
    counts = await _sow_counts(db, farm.id)

    # Farrowing rate (year-to-date): farrowings / matings
    from datetime import timedelta

    from app.db.models.events import Farrowing, Mating, Weaning
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
    fr_bench = await _get_benchmark(db, "FARROWING_RATE", farm)

    # 이번주(월요일~오늘) 이벤트 건수 — soft-delete 제외
    week_start = today - timedelta(days=today.weekday())
    week_matings = await db.scalar(
        select(func.count()).select_from(Mating).where(
            Mating.farm_id == farm.id,
            Mating.mating_date >= week_start,
            Mating.deleted_at.is_(None),
        )
    ) or 0
    week_farrowings = await db.scalar(
        select(func.count()).select_from(Farrowing).where(
            Farrowing.farm_id == farm.id,
            Farrowing.farrowing_date >= week_start,
            Farrowing.deleted_at.is_(None),
        )
    ) or 0
    week_weanings = await db.scalar(
        select(func.count()).select_from(Weaning).where(
            Weaning.farm_id == farm.id,
            Weaning.weaning_date >= week_start,
            Weaning.deleted_at.is_(None),
        )
    ) or 0

    # Rule Engine — base tier only (no addon subscriptions needed)
    ctx = RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi={"PSY": psy_value, "NPD": npd_detail.avg_npd, "FARROWING_RATE": farrowing_rate},  # noqa: E501
        benchmarks={"PSY": psy_bench, "NPD": npd_bench},
        sow_counts=counts,
    )
    result: StructuredResult = await RuleEngine.evaluate(ctx, intent="dashboard")

    alerts = [
        Alert(
            rule_id=f.rule_id,
            kpi=f.kpi,
            severity=f.severity,
            message=f.kpi + (  # noqa: E501
                f": {f.current_value:.1f}" if f.current_value is not None else ""
            ),
            current_value=f.current_value,
            target_value=f.target_value,
        )
        for f in result.findings
        if f.severity in ("WARNING", "CRITICAL")
    ]

    # LOSS_CALC — 올해 누적 자돈 손실(사산+미라 + 자돈폐사) × 출하두당가. 실데이터×실가격(날조 0).
    from app.db.models.events import PigletEvent as _PE
    from app.services.insight_service import _load_price
    estimated_loss = None
    price = await _load_price(db, farm)
    if price:
        ytd = date(year, 1, 1)
        lost_sb = await db.scalar(
            select(func.coalesce(func.sum(Farrowing.stillborn + Farrowing.mummified), 0))
            .where(Farrowing.farm_id == farm.id, Farrowing.farrowing_date >= ytd, Farrowing.deleted_at.is_(None))
        ) or 0
        lost_pd = await db.scalar(
            select(func.coalesce(func.sum(_PE.piglet_count), 0))
            .where(_PE.farm_id == farm.id, _PE.event_type == "DEATH",
                   _PE.event_date >= ytd, _PE.deleted_at.is_(None))
        ) or 0
        lost = int(lost_sb) + int(lost_pd)
        if lost > 0:
            estimated_loss = {
                "amount": round(lost * price["price"]), "currency": price["currency"],
                "lost_pigs": lost, "basis": "ytd_lost_piglets", "demo": price["demo"],
            }

    return DashboardKpi(
        farm_id=farm.id,
        as_of=today,
        psy=psy_value,
        npd=npd_detail.avg_npd,
        # API는 비율(0~1)로 반환 — 프론트가 ×100해 % 표시. (RuleEngine 내부는 위 percent값 사용)
        farrowing_rate=(farrowing_rate / 100) if farrowing_rate is not None else None,
        active_sows=sum(
            counts.get(s, 0)
            for s in ("GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT")
        ),
        # 응답 필드명은 모바일 호환 유지: gestating=임신(PREGNANT), weaned=공태 계열(OPEN+ACCIDENT)
        gestating=counts.get("PREGNANT", 0),
        lactating=counts.get("LACTATING", 0),
        weaned=counts.get("OPEN", 0) + counts.get("ACCIDENT", 0),
        week_matings=week_matings,
        week_farrowings=week_farrowings,
        week_weanings=week_weanings,
        country=farm.country,
        benchmarks={
            "PSY": KpiBenchmark(avg=psy_bench.get("avg"), top25=psy_bench.get("top25"), target=psy_bench.get("target")),
            "NPD": KpiBenchmark(avg=npd_bench.get("avg"), top25=npd_bench.get("top25"), target=npd_bench.get("target")),
            "FARROWING_RATE": KpiBenchmark(avg=fr_bench.get("avg"), top25=fr_bench.get("top25"), target=fr_bench.get("target")),
        },
        alerts=alerts,
        estimated_loss=estimated_loss,
    )
