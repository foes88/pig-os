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

from app.core.config import settings
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
from app.engine.threshold_resolver import load_operational_defaults_map
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
    """연간 PSY = SUM(weaned_count) / AVG(활성 모돈 재고) — KPI 스펙 §1.

    분모는 해당 연도 12개월 각 월초의 활성 모돈수 평균(입식~퇴출 윈도우). 옛 v_farm_psy 뷰는
    분모를 '그 해 이유한 모돈수'로 잘못 계산해 PSY를 과대평가했음(뷰 사용 중단).
    엣지: 이유 0건 → PSY=0(NULL 아님) / 활성 재고 0 → PSY=NULL.
    """
    row = await db.execute(
        text(
            """
            WITH months AS (
                SELECT generate_series(make_date(:year,1,1), make_date(:year,12,1),
                                       interval '1 month')::date AS m
            ),
            inv AS (
                SELECT mo.m, COUNT(s.id) AS cnt
                FROM months mo
                LEFT JOIN sows s ON s.farm_id = :farm_id
                    AND s.entry_date <= mo.m
                    AND (s.deleted_at IS NULL
                         OR (s.exit_date IS NOT NULL AND s.exit_date >= mo.m))
                GROUP BY mo.m
            ),
            num AS (
                SELECT COALESCE(SUM(w.weaned_count), 0) AS total_weaned
                FROM weanings w
                WHERE w.farm_id = :farm_id AND w.deleted_at IS NULL
                  AND EXTRACT(YEAR FROM w.weaning_date) = :year
            )
            SELECT (SELECT AVG(cnt) FROM inv) AS avg_sow_count,
                   (SELECT total_weaned FROM num) AS total_weaned
            """
        ),
        {"farm_id": str(farm_id), "year": year},
    )
    result = row.fetchone()
    avg_inv = float(result.avg_sow_count) if result and result.avg_sow_count else 0.0
    total_weaned = int(result.total_weaned) if result and result.total_weaned else 0
    if avg_inv <= 0:
        # 활성 모돈 0두 → PSY NULL + 경고(스펙 §1 엣지)
        return PsyDetail(farm_id=farm_id, year=year, avg_sow_count=0, total_weaned=total_weaned,
                         psy=None, benchmark_avg=None, target_value=None)
    return PsyDetail(
        farm_id=farm_id,
        year=year,
        avg_sow_count=round(avg_inv, 2),
        total_weaned=total_weaned,
        psy=round(total_weaned / avg_inv, 2),  # 이유 0 → 0.0 (NULL 아님)
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
    # 비육 FCR용 사료: 입력일(record_date) 기준 기간 합산. 모돈(sow_id) 사료는 번식군이므로 제외,
    # 비육군/건물/농장단위(group_id NULL 포함) 사료는 모두 포함 — UI는 group_id 없이 입력하므로
    # JOIN 강제 시 전량 누락됐던 버그(C5) 수정.
    feed = (await db.execute(text(
        "SELECT coalesce(sum(quantity_kg),0) FROM feed_records "
        "WHERE farm_id=:fid AND deleted_at IS NULL AND sow_id IS NULL "
        "AND record_date BETWEEN :s AND :e"), p)).scalar() or 0
    herd = (await db.execute(text(
        "SELECT count(*) FILTER (WHERE status IN ('GILT','OPEN','PREGNANT','LACTATING','ACCIDENT')) active, "
        "count(*) FILTER (WHERE status IN ('GILT','OPEN','PREGNANT','LACTATING','ACCIDENT') AND parity >= 7) hp "
        "FROM sows WHERE farm_id=:fid AND deleted_at IS NULL"), p)).one()
    removed = (await db.execute(text(
        "SELECT count(*) FILTER (WHERE status='CULLED') culled, count(*) FILTER (WHERE status='DEAD') dead "
        "FROM sows WHERE farm_id=:fid AND deleted_at IS NULL AND exit_date BETWEEN :s AND :e"), p)).one()
    gilt_in = (await db.execute(text(
        "SELECT count(*) FROM sows WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND entry_type='GILT' AND entry_date BETWEEN :s AND :e"), p)).scalar() or 0
    # 산차별 실산(분만시점 산차 = breeding_cycles.parity 조인)
    par = {row.parity: row.aba for row in (await db.execute(text(
        "SELECT bc.parity parity, avg(f.born_alive) aba FROM farrowings f "
        "JOIN breeding_cycles bc ON bc.id = f.breeding_cycle_id "
        "WHERE f.farm_id=:fid AND f.deleted_at IS NULL AND f.farrowing_date BETWEEN :s AND :e "
        "AND bc.parity IN (1,2) GROUP BY bc.parity"), p)).all()}
    acc = (await db.execute(text(
        "SELECT count(*) total, count(*) FILTER (WHERE bc.parity=1) p1 "
        "FROM reproductive_events re JOIN breeding_cycles bc ON bc.id = re.breeding_cycle_id "
        "WHERE re.farm_id=:fid AND re.deleted_at IS NULL "
        "AND re.event_type IN ('RETURN_TO_ESTRUS','ABORTION','EMPTY','INFERTILE') "
        "AND re.event_date BETWEEN :s AND :e"), p)).one()
    # 여름(6~8월) 교배 cohort 분만율 vs 그 외 (farrowings.mating_id → mating 월)
    smat = (await db.execute(text(
        "SELECT count(*) FILTER (WHERE extract(month from mating_date) IN (6,7,8)) summer, "
        "count(*) FILTER (WHERE extract(month from mating_date) NOT IN (6,7,8)) other "
        "FROM matings WHERE farm_id=:fid AND deleted_at IS NULL AND mating_date BETWEEN :s AND :e"), p)).one()
    sfar = (await db.execute(text(
        "SELECT count(*) FILTER (WHERE extract(month from m.mating_date) IN (6,7,8)) summer, "
        "count(*) FILTER (WHERE extract(month from m.mating_date) NOT IN (6,7,8)) other "
        "FROM farrowings f JOIN matings m ON m.id = f.mating_id "
        "WHERE f.farm_id=:fid AND f.deleted_at IS NULL AND m.mating_date BETWEEN :s AND :e"), p)).one()
    # 임신감정 수태율(D1) — 양성/(양성+음성), 표본 부족 None
    pc = (await db.execute(text(
        "SELECT count(*) FILTER (WHERE result='POSITIVE') pos, count(*) FILTER (WHERE result='NEGATIVE') neg "
        "FROM pregnancy_checks WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND check_date BETWEEN :s AND :e"), p)).one()
    # 자돈 폐사 사유/일령 분해(D2) — reason·age_days(서버 자동계산) 집계
    pd = (await db.execute(text(
        "SELECT coalesce(sum(piglet_count) FILTER (WHERE reason='CRUSHING'),0) crushing, "
        "coalesce(sum(piglet_count) FILTER (WHERE age_days <= 3),0) age0_3, "
        "coalesce(sum(piglet_count),0) total "
        "FROM piglet_events WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND event_type='DEATH' AND event_date BETWEEN :s AND :e"), p)).one()
    # 배치(AIAO) 요일집중도(D4) — 최다 요일 교배수 / 전체 (표본 ≥16)
    bdow = (await db.execute(text(
        "SELECT max(cnt) maxd, sum(cnt) total FROM ("
        "SELECT extract(dow from mating_date) d, count(*) cnt FROM matings "
        "WHERE farm_id=:fid AND deleted_at IS NULL AND mating_date BETWEEN :s AND :e "
        "GROUP BY 1) t"), p)).one()

    tb = float(far.tb) if far.tb else 0.0
    wsum = float(wea.wsum) if wea.wsum else 0.0
    deaths = float(deaths)
    gain = float(gf.gain) if gf.gain else 0.0
    pigdays = float(gf.pigdays) if gf.pigdays else 0.0
    hin = float(gf.hin) if gf.hin else 0.0

    def _rate(num: float, den: float) -> float | None:
        return round(num / den * 100, 1) if den else None

    pwmr = _rate(deaths, wsum + deaths)
    active_herd = float(herd.active) if herd.active else 0.0
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
        # 모돈군 구조(롤링 window 제거율 = 연간 근사, window=365)
        "CULLING_RATE":        _rate(float(removed.culled), active_herd),
        "SOW_MORTALITY":       _rate(float(removed.dead), active_herd),
        "HIGH_PARITY_RATIO":   _rate(float(herd.hp) if herd.hp else 0.0, active_herd),
        "REPLACEMENT_RATE":    _rate(float(gilt_in), active_herd),
        # 2산차 슬럼프 = P1 실산 − P2 실산 (양쪽 데이터 있을 때만)
        "SECOND_LITTER_DROP":  (round(float(par[1]) - float(par[2]), 1)
                                if par.get(1) is not None and par.get(2) is not None else None),
        # 임신사고 P1 편중 = P1 사고 / 전체 사고 (최소 5건 이상일 때만)
        "ACCIDENT_P1_RATIO":   (_rate(float(acc.p1), float(acc.total))
                                if acc.total and acc.total >= 5 else None),
        # 여름 분만율 하락(pp) = 비여름 cohort FR − 여름 cohort FR (양 cohort ≥5건)
        "SUMMER_FARROW_DROP":  _summer_drop(smat, sfar),
        # 임신감정 수태율 = 양성/(양성+음성), 표본 ≥5
        "CONCEPTION_RATE":     (_rate(float(pc.pos), float(pc.pos) + float(pc.neg))
                                if (pc.pos + pc.neg) >= 5 else None),
        # 자돈 폐사 사유/일령(D2) — 압사율(실산 대비), 0~3일 폐사 편중(분만관리)
        "CRUSHING_RATE":       (_rate(float(pd.crushing), float(far.ba))
                                if far.ba else None),
        "DEATH_AGE_0_3_RATIO": (_rate(float(pd.age0_3), float(pd.total))
                                if pd.total and pd.total >= 5 else None),
        # MSY(D3) = 연간 출하두수(비육 완료 head_out) / 활성 모돈. 출하 데이터 없으면 None(오발화 방지)
        "MSY":                 (round((float(gf.hout) if gf.hout else 0.0) / active_herd, 1)
                                if active_herd and gf.hout else None),
        # 배치 요일집중도(D4) — 최다 요일 교배 비중 % (표본 ≥16)
        "BATCH_DOW_CONCENTRATION": (_rate(float(bdow.maxd), float(bdow.total))
                                    if bdow.total and bdow.total >= 16 else None),
    }


def _summer_drop(smat, sfar) -> float | None:
    """여름(6~8월) 교배 cohort 분만율 하락(pp). 표본 부족(<5)이면 None."""
    s_m, o_m = float(smat.summer or 0), float(smat.other or 0)
    if s_m < 5 or o_m < 5:
        return None
    summer_fr = float(sfar.summer or 0) / s_m * 100
    other_fr = float(sfar.other or 0) / o_m * 100
    return round(other_fr - summer_fr, 1)


async def build_loss_inputs(db: AsyncSession, farm: Farm, window_days: int = 365) -> dict:
    """손실계산 입력(실 count + 출하두당가). 가격 없으면 price=None → 손실룰 미발화(위조 0)."""
    from app.services.insight_service import _load_price
    today = date.today()
    p = {"fid": str(farm.id), "s": today - timedelta(days=window_days), "e": today}
    pw_deaths = (await db.execute(text(
        "SELECT coalesce(sum(piglet_count),0) FROM piglet_events WHERE farm_id=:fid "
        "AND deleted_at IS NULL AND event_type='DEATH' AND event_date BETWEEN :s AND :e"), p)).scalar() or 0
    accidents = (await db.execute(text(
        "SELECT count(*) FROM reproductive_events WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND event_type='ABORTION' AND event_date BETWEEN :s AND :e"), p)).scalar() or 0
    # 도태/폐사 모돈 산차별 카운트(잔여가치 손실용)
    cull_rows = (await db.execute(text(
        "SELECT status, parity, count(*) cnt FROM sows WHERE farm_id=:fid AND deleted_at IS NULL "
        "AND status IN ('CULLED','DEAD') AND exit_date BETWEEN :s AND :e GROUP BY status, parity"), p)).all()
    cull_by_parity = [{"status": r.status, "parity": int(r.parity or 0), "count": int(r.cnt)} for r in cull_rows]
    # NPD(WEI) 총 지연일 합 — S9 ① 이유→교배 (보수적, v_sow_npd)
    wei_total = (await db.execute(text(
        "SELECT coalesce(sum(wei_days),0) FROM v_sow_npd WHERE farm_id=:fid "
        "AND wei_days IS NOT NULL AND wei_days > 0"), {"fid": str(farm.id)})).scalar() or 0
    price = await _load_price(db, farm)
    return {
        "price": price["price"] if price else None,
        "currency": price["currency"] if price else "",
        "demo": price["demo"] if price else True,
        "pw_deaths": float(pw_deaths),
        "accident_count": float(accidents),
        "cull_by_parity": cull_by_parity,
        "wei_total_days": float(wei_total),
    }


async def build_boar_stats(
    db: AsyncSession, farm: Farm, window_days: int = 365, min_matings: int = 10
) -> list[dict]:
    """웅돈별 분만율(farrowings/matings) — 멀티개체 룰(boar.farrow_rate_low)용. 표본 부족 제외."""
    today = date.today()
    rows = (await db.execute(text(
        "SELECT m.boar_id, b.ear_tag, count(DISTINCT m.id) matings, count(DISTINCT f.id) farrows "
        "FROM matings m JOIN boars b ON b.id = m.boar_id "
        "LEFT JOIN farrowings f ON f.mating_id = m.id AND f.deleted_at IS NULL "
        "WHERE m.farm_id=:fid AND m.deleted_at IS NULL AND m.boar_id IS NOT NULL "
        "AND m.mating_date BETWEEN :s AND :e "
        "GROUP BY m.boar_id, b.ear_tag HAVING count(DISTINCT m.id) >= :mm"),
        {"fid": str(farm.id), "s": today - timedelta(days=window_days), "e": today, "mm": min_matings},
    )).all()
    return [
        {"boar_id": str(r.boar_id), "ear_tag": r.ear_tag,
         "matings": int(r.matings), "fr": round(int(r.farrows) / int(r.matings) * 100, 1)}
        for r in rows
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
    boar_stats = await build_boar_stats(db, farm)
    loss_inputs = await build_loss_inputs(db, farm)

    extra = {"recent_notifiable_diseases": notifiable_diseases, "rule_configs": rule_configs,
             "boar_stats": boar_stats, "loss_inputs": loss_inputs}
    if settings.use_governance_benchmarks:  # flag ON: Threshold Resolver용 레지스트리 주입
        extra["operational_defaults"] = await load_operational_defaults_map(db, farm.country)
    return RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi=kpi,
        benchmarks=benchmarks,
        sow_counts=counts,
        as_of=today,
        extra=extra,
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
            Mating.deleted_at.is_(None),  # INTEG-2: soft-delete 제외(드리프트 방지)
        )
    )
    farrowing_count = await db.scalar(
        select(func.count()).select_from(Farrowing).where(
            Farrowing.farm_id == farm.id,
            Farrowing.farrowing_date >= date(today.year, 1, 1),
            Farrowing.deleted_at.is_(None),  # INTEG-2: soft-delete 제외
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
    boar_stats = await build_boar_stats(db, farm)
    loss_inputs = await build_loss_inputs(db, farm)
    dash_extra = {"rule_configs": rule_configs, "boar_stats": boar_stats, "loss_inputs": loss_inputs}
    if settings.use_governance_benchmarks:
        dash_extra["operational_defaults"] = await load_operational_defaults_map(db, farm.country)
    ctx = RuleContext(
        farm_id=farm.id,
        country=farm.country or "default",
        kpi={**herd, "PSY": psy_value, "NPD": npd_detail.avg_npd, "FARROWING_RATE": farrowing_rate},  # noqa: E501
        benchmarks=benchmarks,
        sow_counts=counts,
        extra=dash_extra,
    )
    result: StructuredResult = await RuleEngine.evaluate(ctx, intent="dashboard")
    if settings.use_governance_benchmarks:  # flag ON: verified 평균을 비교 맥락으로 첨부 + §7 trace
        from app.services.benchmark_service import enrich_findings_with_governance
        await enrich_findings_with_governance(db, farm.country or "default", result.findings)

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
        # 스케일 SSOT: percent(0~100) 단일 통일(2026-06-25). 시드 benchmarks(f3a7c2e9b5d1)가 percent
        # (KR target 85.0, unit "%")이고 RuleEngine 입력(L654)·trend 모두 percent → 출력도 percent로 통일해
        # 이중표현(ratio↔percent) 제거. ÷100 금지(과거 ratio 반환이 클라 스케일 꼬임의 근인이었음).
        farrowing_rate=farrowing_rate,
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
