"""
KPI calculation service — Base tier.

PSY, MSY, NPD from DB views + Rule Engine alerts.
Benchmarks resolved via effective_metric_values() DB function
(farm → region → market → system).
"""
from datetime import date, timedelta
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


async def _all_benchmarks(db: AsyncSession, farm: Farm) -> dict[str, dict]:
    """
    effective_metric_values()의 모든 metric_code를 한 번에 dict로 로드 → ctx.benchmarks.
    국가(region) 행이 있으면 그 값, 없으면 system 기본. 규칙은 resolve()로 코드기본까지 폴백.
    """
    rows = await db.execute(
        text(
            "SELECT * FROM effective_metric_values"
            "(:farm_code, :region_code, :market_code)"
        ),
        {"farm_code": str(farm.id), "region_code": farm.country, "market_code": "SYSTEM"},
    )
    out: dict[str, dict] = {}
    for row in rows:
        out[row.metric_code] = {
            "avg":       float(row.benchmark_avg)      if row.benchmark_avg      else None,
            "top25":     float(row.benchmark_top25)    if row.benchmark_top25    else None,
            "target":    float(row.target_value)       if row.target_value       else None,
            "warning":   float(row.warning_threshold)  if row.warning_threshold  else None,
            "critical":  float(row.critical_threshold) if row.critical_threshold else None,
            "direction": str(row.alert_direction)      if row.alert_direction     else "below",
            "unit":      row.unit_code or "",
        }
    # PWMR 규칙은 키 "PWMR"를 읽지만 시드는 PRE_WEANING_MORTALITY → 별칭으로 국가값 연결
    if "PRE_WEANING_MORTALITY" in out and "PWMR" not in out:
        out["PWMR"] = out["PRE_WEANING_MORTALITY"]
    # FARROWING_RATE 국가행 없으면 코드 기본 임계로 farrowing.low_rate 작동 보장
    fr = out.setdefault("FARROWING_RATE", {"direction": "below"})
    if fr.get("warning") is None:
        fr["warning"] = 85.0
    if fr.get("critical") is None:
        fr["critical"] = 80.0
    if not fr.get("direction"):
        fr["direction"] = "below"
    return out


async def build_herd_kpis(
    db: AsyncSession, farm: Farm, window_days: int = 365
) -> dict[str, float | None]:
    """
    롤링 window의 번식·자돈·비육 herd KPI를 실데이터로 집계해 RuleContext.kpi에 주입한다.
    값이 없으면 None → 규칙은 빈 결과(날조 0). 국가별 임계는 benchmarks/rule_configs가 조정.
    """
    today = date.today()
    p = {"fid": str(farm.id), "s": today - timedelta(days=window_days), "e": today}

    def _f(v) -> float | None:
        return float(v) if v is not None else None

    matings = (await db.execute(text(
        "SELECT count(*) FROM matings WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND mating_date BETWEEN :s AND :e"), p)).scalar() or 0
    far = (await db.execute(text(
        "SELECT count(*) c, sum(total_born) tb, sum(born_alive) ba, sum(stillborn) sb, "
        "sum(mummified) mum, avg(born_alive) aba, avg(total_born) atb, "
        "avg(avg_birth_weight_kg) abw "
        "FROM farrowings WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND farrowing_date BETWEEN :s AND :e"), p)).one()
    wea = (await db.execute(text(
        "SELECT count(*) c, sum(weaned_count) wsum, avg(weaned_count) aw, "
        "avg(weaning_age_days) aage, avg(avg_weaning_weight_kg) aww "
        "FROM weanings WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND weaning_date BETWEEN :s AND :e"), p)).one()
    rts = (await db.execute(text(
        "SELECT count(*) FROM reproductive_events WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND event_type='RETURN_TO_ESTRUS' AND event_date BETWEEN :s AND :e"), p)).scalar() or 0
    abo = (await db.execute(text(
        "SELECT count(*) FROM reproductive_events WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND event_type='ABORTION' AND event_date BETWEEN :s AND :e"), p)).scalar() or 0
    deaths = (await db.execute(text(
        "SELECT coalesce(sum(piglet_count),0) FROM piglet_events WHERE farm_id=:fid "
        "AND deleted_at IS NULL AND event_type='DEATH' AND event_date BETWEEN :s AND :e"), p)).scalar() or 0
    wsi_avg = (await db.execute(text(
        "SELECT avg(wsi) FROM (SELECT (m.mating_date - (SELECT max(w.weaning_date) FROM weanings w "
        "WHERE w.sow_id=m.sow_id AND w.deleted_at IS NULL AND w.weaning_date <= m.mating_date)) AS wsi "
        "FROM matings m WHERE m.farm_id=:fid AND m.deleted_at IS NULL "
        "AND m.mating_date BETWEEN :s AND :e) t WHERE wsi IS NOT NULL AND wsi >= 0"), p)).scalar()
    gf = (await db.execute(text(
        "SELECT coalesce(sum(head_count_in),0) hin, coalesce(sum(head_count_out),0) hout, "
        "coalesce(sum((avg_exit_weight_kg - avg_entry_weight_kg) * head_count_out),0) gain, "
        "coalesce(sum((end_date - start_date) * head_count_out),0) pigdays "
        "FROM finisher_groups WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND end_date IS NOT NULL AND head_count_out IS NOT NULL "
        "AND avg_exit_weight_kg IS NOT NULL AND avg_entry_weight_kg IS NOT NULL "
        "AND end_date BETWEEN :s AND :e"), p)).one()
    feed = (await db.execute(text(
        "SELECT coalesce(sum(fr.quantity_kg),0) FROM feed_records fr "
        "JOIN finisher_groups g ON g.id = fr.group_id AND g.deleted_at IS NULL "
        "WHERE fr.farm_id=:fid AND fr.deleted_at IS NULL "
        "AND g.end_date IS NOT NULL AND g.end_date BETWEEN :s AND :e"), p)).scalar() or 0

    tb = float(far.tb) if far.tb else 0.0
    wsum = float(wea.wsum) if wea.wsum else 0.0
    deaths = float(deaths)
    gain = float(gf.gain) if gf.gain else 0.0
    pigdays = float(gf.pigdays) if gf.pigdays else 0.0
    hin = float(gf.hin) if gf.hin else 0.0

    def _rate(num: float, den: float) -> float | None:
        return round(num / den * 100, 1) if den else None

    pwmr = _rate(deaths, wsum + deaths)
    return {
        # 캐논 metric_code(default_metric_values 시드와 정합 → 국가별 benchmark 자동 적용)
        "FARROWING_RATE":      _rate(float(far.c), float(matings)),
        "RTS_RATE":            _rate(float(rts), float(matings)),
        "ABORTION_RATE":       _rate(float(abo), float(matings)),
        "STILLBORN_RATE":      _rate(float(far.sb) if far.sb else 0.0, tb),
        "MUMMIFIED_RATE":      _rate(float(far.mum) if far.mum else 0.0, tb),
        "PRE_WEANING_MORTALITY": pwmr,
        "PWMR":                pwmr,   # 기존 pwmr.high 규칙 호환(별칭)
        "WSI":                 round(float(wsi_avg), 1) if wsi_avg is not None else None,
        "TOTAL_BORN":          round(_f(far.atb), 1) if far.atb is not None else None,
        "BORN_ALIVE":          round(_f(far.aba), 1) if far.aba is not None else None,
        "WEANED_COUNT":        round(_f(wea.aw), 1) if wea.aw is not None else None,
        "BIRTH_WEIGHT":        round(_f(far.abw), 2) if far.abw is not None else None,
        "WEANING_WEIGHT":      round(_f(wea.aww), 2) if wea.aww is not None else None,
        "WEANING_AGE":         round(_f(wea.aage), 1) if wea.aage is not None else None,
        "ADG":                 round(gain / pigdays * 1000, 1) if pigdays else None,
        "FCR":                 round(float(feed) / gain, 3) if gain else None,
        "FINISH_MORTALITY":    _rate(hin - (float(gf.hout) if gf.hout else 0.0), hin),
    }


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

    # Resolve benchmarks — 전체 metric_code를 국가행 우선으로 한 번에 로드
    benchmarks = await _all_benchmarks(db, farm)

    # KPI values — herd 집계(번식·자돈·비육) + PSY/NPD. explicit가 herd 위에 우선.
    herd = await build_herd_kpis(db, farm)
    if kpi_overrides:
        kpi = {**herd, **kpi_overrides}
    else:
        psy_detail = await calculate_psy(db, farm.id, year)
        npd_detail = await calculate_npd_breakdown(
            db, farm.id, date(today.year, 1, 1), today
        )
        kpi = {
            **herd,
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
        benchmarks=benchmarks,
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
    # herd 집계(번식·자돈·비육) 주입 → 대시보드 알림도 확장 규칙 노출. explicit FR 우선.
    herd = await build_herd_kpis(db, farm)
    benchmarks = await _all_benchmarks(db, farm)
    rule_configs = await load_rule_configs(db)
    ctx = RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi={**herd, "PSY": psy_value, "NPD": npd_detail.avg_npd, "FARROWING_RATE": farrowing_rate},  # noqa: E501
        benchmarks=benchmarks,
        sow_counts=counts,
        extra={"rule_configs": rule_configs},
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
