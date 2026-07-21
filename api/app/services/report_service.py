"""
Report service — reproduction & grow-finish performance, sow history.

Aggregation is split into pure builders (``build_*``) that take primitive rows so
they unit-test without a DB, and thin async wrappers that query and delegate.

Reproduction metrics are derived directly from event tables (matings/farrowings/
weanings/reproductive_events/piglet_events) rather than kpi_snapshots, because the
snapshot table does not carry per-period TB/BA/weaned/RTS breakdowns.
"""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import bindparam, case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.health import FeedRecord, Removal
from app.db.models.ops import FinisherGroup
from app.db.models.sow import Boar, BreedingCycle, Sow

RTS_EVENT_TYPES = ("RETURN_TO_ESTRUS", "ABORTION", "EMPTY", "INFERTILE")
VALID_PERIODS = ("monthly", "quarterly", "annual")


def period_key(d: date, period: str) -> str:
    if period == "monthly":
        return f"{d.year}-{d.month:02d}"
    if period == "quarterly":
        return f"{d.year}-Q{(d.month - 1) // 3 + 1}"
    if period == "annual":
        return f"{d.year}"
    raise ValueError(f"period must be one of {VALID_PERIODS}")


def _avg(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def enumerate_period_keys(start: date, end: date, period: str) -> list[str]:
    """[start, end] 범위의 모든 기간 키(연속). 이벤트 없는 기간도 빈 행으로 채우기 위함(M4).
    트렌드(generate_series)와 동일하게 보고서도 연속 기간을 반환해 뷰 간 불일치 제거."""
    keys: list[str] = []
    if period == "monthly":
        y, m = start.year, start.month
        while (y, m) <= (end.year, end.month):
            keys.append(f"{y}-{m:02d}")
            m += 1
            if m > 12:
                m, y = 1, y + 1
    elif period == "quarterly":
        y, q = start.year, (start.month - 1) // 3 + 1
        endq = (end.month - 1) // 3 + 1
        while (y, q) <= (end.year, endq):
            keys.append(f"{y}-Q{q}")
            q += 1
            if q > 4:
                q, y = 1, y + 1
    elif period == "annual":
        keys = [str(y) for y in range(start.year, end.year + 1)]
    return keys


# ── Reproduction ──────────────────────────────────────────────────────────────

def build_reproduction_rows(
    period: str,
    matings: list[date],
    farrowings: list[tuple[date, int, int]],          # (date, total_born, born_alive)
    weanings: list[tuple[date, int, int | None]],     # (date, weaned_count, lactation_days)
    rts: list[date],
    deaths: list[tuple[date, int]],                   # (date, piglet_death_count)
    *,
    group_by: str = "period",
    # 확장 입력(미전달 시 기존 동작 유지 — 신규 필드만 0/None). 각 리스트는 동일 인덱스로 paired.
    mating_breeds: list[str | None] | None = None,    # parallel to matings
    farrowing_breeds: list[str | None] | None = None, # parallel to farrowings
    weaning_breeds: list[str | None] | None = None,   # parallel to weanings
    weaning_litter_ids: list[str | None] | None = None,  # parallel to weanings — 복(farrowing) 키(#5 부분이유 집계)
    rts_breeds: list[str | None] | None = None,       # parallel to rts
    death_breeds: list[str | None] | None = None,     # parallel to deaths
    mating_numbers: list[int] | None = None,          # parallel to matings (1~5)
    mating_types: list[str] | None = None,            # parallel to matings (AI/NATURAL)
    stillborn: list[int] | None = None,               # parallel to farrowings
    mummified: list[int] | None = None,               # parallel to farrowings
    farrowing_weaned: list[int | None] | None = None,  # parallel to farrowings — 그 복의 총 이유두수(#7 pwmr_b 복단위)
    fill_periods: list[str] | None = None,            # 빈 기간도 행 생성(M4, group_by="period"만)
) -> list[dict]:
    """기간별(period) 또는 품종별(breed) 번식성적 집계.

    group_by="breed"이면 버킷 키 = 품종(breed) 라벨(None→"unknown"). 그 외는 period_key.
    확장 인자가 주어지면 사산/미라/교배회차·방식 분해 지표를 함께 산출한다.
    """
    UNKNOWN = "unknown"

    def gkey(d: date, breed: str | None) -> str:
        if group_by == "breed":
            return breed or UNKNOWN
        return period_key(d, period)

    buckets: dict[str, dict] = {}

    def b(key: str) -> dict:
        return buckets.setdefault(
            key,
            {"matings": 0, "farrowings": 0, "rts": 0,
             "tb": [], "ba": [], "weaned_litters": {}, "lact": [], "deaths": 0,
             "pwmrb": [],  # 복단위 (tb-weaned)/tb (#7)
             "sb": 0, "mum": 0, "m1": 0, "m2": 0, "m3plus": 0, "ai": 0, "nat": 0},
        )

    for i, d in enumerate(matings):
        breed = mating_breeds[i] if mating_breeds and i < len(mating_breeds) else None
        x = b(gkey(d, breed)); x["matings"] += 1
        if mating_numbers and i < len(mating_numbers):
            n = mating_numbers[i]
            if n == 1:
                x["m1"] += 1
            elif n == 2:
                x["m2"] += 1
            elif n is not None and n >= 3:
                x["m3plus"] += 1
        if mating_types and i < len(mating_types):
            t = (mating_types[i] or "").upper()
            if t == "AI":
                x["ai"] += 1
            elif t == "NATURAL":
                x["nat"] += 1
    for i, (d, tb, ba) in enumerate(farrowings):
        breed = farrowing_breeds[i] if farrowing_breeds and i < len(farrowing_breeds) else None
        x = b(gkey(d, breed)); x["farrowings"] += 1; x["tb"].append(tb); x["ba"].append(ba)
        if stillborn and i < len(stillborn):
            x["sb"] += stillborn[i] or 0
        if mummified and i < len(mummified):
            x["mum"] += mummified[i] or 0
        # #7: 이 복의 총 이유두수로 복단위 손실률 — 분만/이유를 같은 복끼리 비교(무관 세트 평균 방지).
        if farrowing_weaned and i < len(farrowing_weaned):
            fw = farrowing_weaned[i]
            if fw is not None and tb and tb > 0:
                x["pwmrb"].append((tb - fw) / tb * 100)
    for i, (d, wc, lact) in enumerate(weanings):
        breed = weaning_breeds[i] if weaning_breeds and i < len(weaning_breeds) else None
        x = b(gkey(d, breed))
        # 부분이유(#5): 같은 복(farrowing)의 여러 이유를 복단위로 합산. litter_id 미전달 시 행 자체를 1복으로(구동작).
        lid = weaning_litter_ids[i] if weaning_litter_ids and i < len(weaning_litter_ids) else None
        litter_key = lid if lid is not None else f"__row{i}"
        x["weaned_litters"][litter_key] = x["weaned_litters"].get(litter_key, 0) + (wc or 0)
        x["lact"].append(lact)
    for i, d in enumerate(rts):
        breed = rts_breeds[i] if rts_breeds and i < len(rts_breeds) else None
        b(gkey(d, breed))["rts"] += 1
    for i, (d, n) in enumerate(deaths):
        breed = death_breeds[i] if death_breeds and i < len(death_breeds) else None
        b(gkey(d, breed))["deaths"] += n

    # M4: 이벤트 없는 기간도 빈 버킷 생성(연속 기간) — group_by="period"일 때만.
    if fill_periods and group_by != "breed":
        for p in fill_periods:
            b(p)

    rows = []
    for key in sorted(buckets):
        x = buckets[key]
        avg_tb = _avg(x["tb"])
        # 복(litter)단위 집계: 부분이유 여러 건을 한 복으로 합산해 평균/복수를 낸다(#5).
        litter_sums = list(x["weaned_litters"].values())
        total_weanings = len(litter_sums)          # 이유 '복' 수(이유 '건'수 아님)
        avg_weaned = _avg(litter_sums)              # 복당 이유두수 평균
        total_weaned = sum(litter_sums)
        tb_sum = sum(t for t in x["tb"] if t is not None)
        ba_sum = sum(t for t in x["ba"] if t is not None)
        fr = round(x["farrowings"] / x["matings"] * 100, 1) if x["matings"] else None
        rts_rate = round(x["rts"] / x["matings"] * 100, 1) if x["matings"] else None
        # #7: 복단위 손실 데이터가 있으면 복단위 평균(분만↔이유 같은 복). 없으면(구 호출) 기존 근사식.
        if farrowing_weaned is not None:
            pwmr_b = round(sum(x["pwmrb"]) / len(x["pwmrb"]), 1) if x["pwmrb"] else None
        else:
            pwmr_b = (
                round((avg_tb - avg_weaned) / avg_tb * 100, 1)
                if avg_tb and avg_weaned is not None and avg_tb > 0
                else None
            )
        denom_a = total_weaned + x["deaths"]
        pwmr_a = round(x["deaths"] / denom_a * 100, 1) if denom_a > 0 else None
        sb_rate = round(x["sb"] / tb_sum * 100, 1) if tb_sum > 0 else None
        mum_rate = round(x["mum"] / tb_sum * 100, 1) if tb_sum > 0 else None
        loss_rate = round((x["sb"] + x["mum"]) / tb_sum * 100, 1) if tb_sum > 0 else None
        rows.append({
            "period": key,
            "total_matings": x["matings"],
            "total_farrowings": x["farrowings"],
            "total_weanings": total_weanings,
            "fr": fr,
            "avg_tb": avg_tb,
            "avg_ba": _avg(x["ba"]),
            "avg_weaned": avg_weaned,
            "avg_lactation_days": _avg(x["lact"]),
            "pwmr_a": pwmr_a,
            "pwmr_b": pwmr_b,
            "rts_rate": rts_rate,
            # ── 확장 지표 (R3) ──
            "total_born_sum": tb_sum,
            "born_alive_sum": ba_sum,
            "total_stillborn": x["sb"],
            "total_mummified": x["mum"],
            "stillborn_rate": sb_rate,
            "mummified_rate": mum_rate,
            "birth_loss_rate": loss_rate,
            "mating_1_count": x["m1"],
            "mating_2_count": x["m2"],
            "mating_3plus_count": x["m3plus"],
            "ai_count": x["ai"],
            "natural_count": x["nat"],
        })
    return rows


def benchmark_values_from_effective(effective: list[dict]) -> list[dict]:
    """threshold_service.list_effective() 출력 → 보고서 동봉용 BenchmarkValue dict 리스트.

    순수 변환(판정 없음). 프론트는 이 값과 행 값을 '비교'만 한다(판정 재구현 금지).
    """
    out = []
    for e in effective:
        out.append({
            "metric_code": e["metric_code"],
            "target": e.get("target"),
            "benchmark_avg": e.get("avg"),
            "benchmark_top25": e.get("top25"),
            "warning": e.get("warning"),
            "critical": e.get("critical"),
            "alert_direction": e.get("direction"),
            "unit": e.get("unit"),
            "source_ref": e.get("source"),
            "confidence": e.get("confidence"),
        })
    return out


async def get_production_summary(
    db: AsyncSession, farm, start: date, end: date, period: str, group_by: str = "period"
) -> dict:
    """피그플랜식 통합표: 번식성적 rows + 농장 country 기준값 동봉."""
    from app.services import threshold_service  # 지연 임포트(순환 방지)

    rows = await get_reproduction_report(db, farm.id, start, end, period, group_by)
    effective = await threshold_service.list_effective(db, farm)
    return {
        "group_by": group_by,
        "period": period,
        "country_scope": getattr(farm, "country", None),
        "benchmarks": benchmark_values_from_effective(effective),
        "rows": rows,
    }


# 벤치마크 병기 대상 국가 — 농장국가 + 글로벌 참조(한국/미국/브라질). 중복 제거.
_BENCH_REF_COUNTRIES = ("KR", "US", "BR")


async def _country_kpi_benchmarks(db: AsyncSession, farm) -> list[dict]:
    """PSY/NPD/분만율 목표값을 국가별로 병기(읽기전용 비교 기준).

    default_metric_values의 region 행을 직접 조회(effective 함수는 단일 농장 국가만 반환).
    농장 국가를 맨 앞에 두고 KR/US/BR 참조를 뒤에 붙인다(중복 국가는 1회만).
    """
    scope = getattr(farm, "country", None)
    ordered: list[str] = []
    for c in ([scope] if scope else []) + list(_BENCH_REF_COUNTRIES):
        if c and c not in ordered:
            ordered.append(c)
    if not ordered:
        return []
    rows = await db.execute(
        text(
            """
            SELECT scope_code, metric_code, target_value
            FROM default_metric_values
            WHERE scope_type = 'region'
              AND scope_code IN :countries
              AND metric_code IN ('PSY', 'NPD', 'FARROWING_RATE')
            """
        ).bindparams(bindparam("countries", expanding=True)),
        {"countries": ordered},
    )
    by_country: dict[str, dict] = {c: {"country": c, "psy": None, "npd": None,
                                       "farrowing_rate": None} for c in ordered}
    key = {"PSY": "psy", "NPD": "npd", "FARROWING_RATE": "farrowing_rate"}
    for r in rows:
        tgt = float(r.target_value) if r.target_value is not None else None
        by_country[r.scope_code][key[r.metric_code]] = tgt
    return [by_country[c] for c in ordered]


async def get_annual_kpi_trend(db: AsyncSession, farm, years: int, end_year: int) -> dict:
    """PSY/NPD 연도별 추세 + 국가 벤치마크 병기.

    번식 연간집계(교배/분만/분만율)는 1회 조회, PSY/NPD는 연도별 계산.
    데이터 없는 연도는 null(추세선에서 끊김 처리는 프론트 몫).
    """
    from app.services import kpi_service  # 지연 임포트(순환 방지)

    start_year = end_year - years + 1
    repro = await get_reproduction_report(
        db, farm.id, date(start_year, 1, 1), date(end_year, 12, 31), "annual", "period"
    )
    repro_by_year = {str(r["period"])[:4]: r for r in repro}

    rows: list[dict] = []
    for y in range(start_year, end_year + 1):
        psy = await kpi_service.calculate_psy(db, farm.id, min(date(y, 12, 31), date.today()))
        npd = await kpi_service.calculate_npd_breakdown(
            db, farm.id, date(y, 1, 1), date(y, 12, 31)
        )
        rr = repro_by_year.get(str(y), {})
        rows.append({
            "year": y,
            "psy": psy.psy if psy else None,
            "npd": round(npd.avg_npd, 1) if npd and npd.avg_npd is not None else None,
            "avg_sows": psy.avg_sow_count if psy else None,
            "total_weaned": psy.total_weaned if psy else 0,
            "total_farrowings": rr.get("total_farrowings", 0) or 0,
            "total_matings": rr.get("total_matings", 0) or 0,
            "farrowing_rate": rr.get("fr"),
        })

    return {
        "country_scope": getattr(farm, "country", None),
        "rows": rows,
        "country_benchmarks": await _country_kpi_benchmarks(db, farm),
    }


# ── Grow-finish ───────────────────────────────────────────────────────────────

def build_grow_finish_rows(
    groups: list[dict],                 # group_code, start_date, end_date, head_in, head_out, entry_w, exit_w
    feed_by_group: dict[str, float],    # group_code → total feed kg
) -> list[dict]:
    rows = []
    for g in groups:
        days = (g["end_date"] - g["start_date"]).days if g.get("end_date") else None
        entry_w, exit_w = g.get("entry_w"), g.get("exit_w")
        adg_g = (
            round((exit_w - entry_w) / days * 1000, 1)
            if days and days > 0 and entry_w is not None and exit_w is not None
            else None
        )
        head_in = g.get("head_in") or 0
        head_out = g.get("head_out")
        mortality = (
            round((head_in - head_out) / head_in * 100, 1)
            if head_out is not None and head_in > 0
            else None
        )
        gain_total = (
            (exit_w - entry_w) * (head_out if head_out is not None else head_in)
            if entry_w is not None and exit_w is not None
            else None
        )
        feed_total = feed_by_group.get(g["group_code"])
        fcr = (
            round(feed_total / gain_total, 3)
            if feed_total and gain_total and gain_total > 0
            else None
        )
        rows.append({
            "group_code": g["group_code"],
            "start_date": g["start_date"].isoformat(),
            "end_date": g["end_date"].isoformat() if g.get("end_date") else None,
            "head_in": head_in,
            "head_out": head_out,
            "avg_entry_weight_kg": entry_w,
            "avg_exit_weight_kg": exit_w,
            "adg_g": adg_g,
            "fcr": fcr,
            "mortality_rate": mortality,
        })
    return rows


# ── Sow history ───────────────────────────────────────────────────────────────

def build_sow_history(
    cycles: list[dict],          # parity, status
    matings: list[dict],         # cycle_id, date, boar_id
    farrowings: list[dict],      # cycle_id, date, tb, ba, sb, mum
    weanings: list[dict],        # cycle_id, date, weaned, lactation_days
) -> list[dict]:
    m_by = {}
    for m in matings:
        m_by.setdefault(m["cycle_id"], []).append(m)
    f_by = {f["cycle_id"]: f for f in farrowings}
    # 부분이유(#6): 사이클당 이유가 여러 건일 수 있어 dict가 아니라 리스트로 모아 합산.
    w_by: dict = {}
    for w in weanings:
        w_by.setdefault(w["cycle_id"], []).append(w)

    out = []
    for c in sorted(cycles, key=lambda c: c["parity"]):
        cid = c["cycle_id"]
        ms = sorted(m_by.get(cid, []), key=lambda m: m["date"])
        f = f_by.get(cid)
        ws = sorted(w_by.get(cid, []), key=lambda w: w["date"])
        last_w = ws[-1] if ws else None
        total_weaned = sum(w["weaned"] for w in ws if w["weaned"] is not None) if ws else None
        # 완료 판정은 사이클 상태(WEANED) 기준 — 첫 부분이유에 '완료' 오표기 방지.
        completed = c.get("status") == "WEANED"
        out.append({
            "parity": c["parity"],
            "mating_date": ms[0]["date"].isoformat() if ms else None,
            "boar_ids": [m["boar_id"] for m in ms if m.get("boar_id")],
            "farrowing_date": f["date"].isoformat() if f else None,
            "tb": f["tb"] if f else None,
            "ba": f["ba"] if f else None,
            "sb": f["sb"] if f else None,
            "mum": f["mum"] if f else None,
            "weaned": total_weaned,                                    # 부분이유 합산
            "weaning_date": last_w["date"].isoformat() if last_w else None,  # 최종 이유일
            "lactation_days": last_w["lactation_days"] if last_w else None,
            "status": "completed" if completed else "in_progress",
        })
    return out


# ── DB wrappers ───────────────────────────────────────────────────────────────

async def get_reproduction_report(
    db: AsyncSession, farm_id: UUID, start: date, end: date, period: str,
    group_by: str = "period",
) -> list[dict]:
    # Sow 조인으로 breed 동봉 (group_by="breed" 지원 + 사산/미라/교배회차·방식 분해)
    mrows = (await db.execute(
        select(Mating.mating_date, Mating.mating_number, Mating.mating_type, Sow.breed)
        .join(Sow, Mating.sow_id == Sow.id)
        .where(Mating.farm_id == farm_id, Mating.deleted_at.is_(None),
               Mating.mating_date >= start, Mating.mating_date <= end)
    )).all()
    frows = (await db.execute(
        select(Farrowing.farrowing_date, Farrowing.total_born, Farrowing.born_alive,
               Farrowing.stillborn, Farrowing.mummified, Sow.breed, Farrowing.id)
        .join(Sow, Farrowing.sow_id == Sow.id)
        .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None),
               Farrowing.farrowing_date >= start, Farrowing.farrowing_date <= end)
    )).all()
    # #7 pwmr_b 복단위: 각 분만(litter)의 총 이유두수 — 기간 무관 전량(이유가 다음 달로 넘어가도 귀속).
    wsum_by_farrowing = (await db.execute(
        select(Weaning.farrowing_id, func.coalesce(func.sum(Weaning.weaned_count), 0))
        .where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None),
               Weaning.farrowing_id.in_([r[6] for r in frows]) if frows else False)
        .group_by(Weaning.farrowing_id)
    )).all() if frows else []
    weaned_by_farrowing = {fid: int(s) for fid, s in wsum_by_farrowing}
    wrows = (await db.execute(
        select(Weaning.weaning_date, Weaning.weaned_count, Weaning.weaning_age_days, Sow.breed,
               Weaning.farrowing_id)
        .join(Sow, Weaning.sow_id == Sow.id)
        .where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None),
               Weaning.weaning_date >= start, Weaning.weaning_date <= end)
    )).all()
    rrows = (await db.execute(
        select(ReproductiveEvent.event_date, Sow.breed)
        .join(Sow, ReproductiveEvent.sow_id == Sow.id)
        .where(ReproductiveEvent.farm_id == farm_id, ReproductiveEvent.deleted_at.is_(None),
               ReproductiveEvent.event_type.in_(RTS_EVENT_TYPES),
               ReproductiveEvent.event_date >= start, ReproductiveEvent.event_date <= end)
    )).all()
    drows = (await db.execute(
        select(PigletEvent.event_date, PigletEvent.piglet_count, Sow.breed)
        .join(Sow, PigletEvent.sow_id == Sow.id)
        .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
               PigletEvent.event_type == "DEATH",
               PigletEvent.event_date >= start, PigletEvent.event_date <= end)
    )).all()

    return build_reproduction_rows(
        period,
        [r[0] for r in mrows],
        [(r[0], r[1], r[2]) for r in frows],
        [(r[0], r[1], r[2]) for r in wrows],
        [r[0] for r in rrows],
        [(r[0], r[1]) for r in drows],
        group_by=group_by,
        mating_numbers=[r[1] for r in mrows],
        mating_types=[r[2] for r in mrows],
        mating_breeds=[r[3] for r in mrows],
        farrowing_breeds=[r[5] for r in frows],
        stillborn=[r[3] for r in frows],
        mummified=[r[4] for r in frows],
        farrowing_weaned=[weaned_by_farrowing.get(r[6]) for r in frows],  # #7 복단위 pwmr_b
        weaning_breeds=[r[3] for r in wrows],
        weaning_litter_ids=[str(r[4]) if r[4] is not None else None for r in wrows],  # #5 복단위 집계
        rts_breeds=[r[1] for r in rrows],
        death_breeds=[r[2] for r in drows],
        # M4: 기간 단위 보고서는 빈 기간도 연속으로 채움(트렌드와 일치).
        fill_periods=enumerate_period_keys(start, end, period) if group_by == "period" else None,
    )


async def get_daily_report(db: AsyncSession, farm_id: UUID, day: date) -> dict:
    """일일 사육현황 — 그날의 이벤트 요약 + 현재 돈군 스냅샷. (PigPlan '일일보고서')"""
    matings = await db.scalar(
        select(func.count()).select_from(Mating)
        .where(Mating.farm_id == farm_id, Mating.deleted_at.is_(None), Mating.mating_date == day)
    )
    f = (await db.execute(
        select(func.count(), func.coalesce(func.sum(Farrowing.total_born), 0),
               func.coalesce(func.sum(Farrowing.born_alive), 0))
        .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None), Farrowing.farrowing_date == day)
    )).one()
    w = (await db.execute(
        select(func.count(), func.coalesce(func.sum(Weaning.weaned_count), 0))
        .where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None), Weaning.weaning_date == day)
    )).one()
    accidents = await db.scalar(
        select(func.count()).select_from(ReproductiveEvent)
        .where(ReproductiveEvent.farm_id == farm_id, ReproductiveEvent.deleted_at.is_(None),
               ReproductiveEvent.event_date == day)
    )
    pd = (await db.execute(
        select(func.count(), func.coalesce(func.sum(PigletEvent.piglet_count), 0))
        .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
               PigletEvent.event_type == "DEATH", PigletEvent.event_date == day)
    )).one()
    removals = await db.scalar(
        select(func.count()).select_from(Removal)
        .where(Removal.farm_id == farm_id, Removal.removal_date == day)
    )
    herd_rows = (await db.execute(
        select(Sow.status, func.count()).where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        .group_by(Sow.status)
    )).all()
    herd = {s: c for s, c in herd_rows}
    active = ("GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT")

    return {
        "date": day.isoformat(),
        "herd": {
            "active_sows": sum(herd.get(s, 0) for s in active),
            "gilts": herd.get("GILT", 0), "open": herd.get("OPEN", 0),
            "pregnant": herd.get("PREGNANT", 0), "lactating": herd.get("LACTATING", 0),
            "accident": herd.get("ACCIDENT", 0),
        },
        "matings": matings or 0,
        "farrowings": {"count": f[0], "total_born": int(f[1]), "born_alive": int(f[2])},
        "weanings": {"count": w[0], "weaned": int(w[1])},
        "accidents": accidents or 0,
        "piglet_deaths": {"count": pd[0], "piglets": int(pd[1])},
        "removals": removals or 0,
    }


async def get_grow_finish_report(
    db: AsyncSession, farm_id: UUID, start: date, end: date, group_id: UUID | None = None
) -> list[dict]:
    q = select(FinisherGroup).where(
        FinisherGroup.farm_id == farm_id, FinisherGroup.deleted_at.is_(None),
        FinisherGroup.start_date >= start, FinisherGroup.start_date <= end)
    if group_id is not None:
        q = q.where(FinisherGroup.id == group_id)
    groups = list(await db.scalars(q))

    feed_rows = (await db.execute(
        select(FeedRecord.group_id, FeedRecord.quantity_kg).where(
            FeedRecord.farm_id == farm_id, FeedRecord.deleted_at.is_(None),
            FeedRecord.group_id.isnot(None))
    )).all()
    feed_by_id: dict[UUID, float] = {}
    for gid, qty in feed_rows:
        feed_by_id[gid] = feed_by_id.get(gid, 0.0) + float(qty or 0)

    payload = [{
        "group_code": g.group_code,
        "start_date": g.start_date,
        "end_date": g.end_date,
        "head_in": g.head_count_in,
        "head_out": g.head_count_out,
        "entry_w": float(g.avg_entry_weight_kg) if g.avg_entry_weight_kg is not None else None,
        "exit_w": float(g.avg_exit_weight_kg) if g.avg_exit_weight_kg is not None else None,
    } for g in groups]
    feed_by_code = {g.group_code: feed_by_id.get(g.id, 0.0) for g in groups}
    return build_grow_finish_rows(payload, feed_by_code)


async def get_sow_history(db: AsyncSession, farm_id: UUID, sow_id: UUID) -> list[dict]:
    # M2: 모돈이 이 농장 소속인지 먼저 검증 — farm_id 경로파라미터가 장식이 되어
    # 타 농장 모돈 이력이 조회되던 크로스테넌트 누수 차단. + 서브쿼리도 farm_id로 스코프.
    sow_in_farm = await db.scalar(
        select(Sow.id).where(Sow.id == sow_id, Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
    )
    if not sow_in_farm:
        raise NotFoundError("Sow not found in this farm")
    cycles = list(await db.scalars(
        select(BreedingCycle).where(BreedingCycle.sow_id == sow_id, BreedingCycle.farm_id == farm_id)
    ))
    matings = (await db.execute(
        select(Mating.breeding_cycle_id, Mating.mating_date, Mating.boar_id).where(
            Mating.sow_id == sow_id, Mating.farm_id == farm_id, Mating.deleted_at.is_(None))
    )).all()
    farrowings = (await db.execute(
        select(Farrowing.breeding_cycle_id, Farrowing.farrowing_date, Farrowing.total_born,
               Farrowing.born_alive, Farrowing.stillborn, Farrowing.mummified).where(
            Farrowing.sow_id == sow_id, Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None))
    )).all()
    weanings = (await db.execute(
        select(Weaning.breeding_cycle_id, Weaning.weaning_date, Weaning.weaned_count,
               Weaning.weaning_age_days).where(
            Weaning.sow_id == sow_id, Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None))
    )).all()

    return build_sow_history(
        [{"cycle_id": c.id, "parity": c.parity, "status": c.cycle_status} for c in cycles],
        [{"cycle_id": r[0], "date": r[1], "boar_id": str(r[2]) if r[2] else None} for r in matings],
        [{"cycle_id": r[0], "date": r[1], "tb": r[2], "ba": r[3], "sb": r[4], "mum": r[5]} for r in farrowings],
        [{"cycle_id": r[0], "date": r[1], "weaned": r[2], "lactation_days": r[3]} for r in weanings],
    )


# ── 종합일보 (Comprehensive Daily Report) — PigPlan .mrd 6섹션 → PigOS ──────────
# 일계(당일) + 월계(당월 1일~당일). 출처 매핑: docs/specs/2026-06-19_comprehensive-daily-report-spec.md
async def get_comprehensive_daily_report(db: AsyncSession, farm_id: UUID, day: date) -> dict:
    from datetime import date as _date
    month_start = _date(day.year, day.month, 1)

    def _rng(col, monthly: bool):
        return (col >= month_start, col <= day) if monthly else (col == day,)

    # ── ① 돈군 현황(당일 스냅샷) ──
    herd_rows = (await db.execute(
        select(Sow.status, func.count()).where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        .group_by(Sow.status)
    )).all()
    herd = {s: c for s, c in herd_rows}
    boars = await db.scalar(select(func.count()).select_from(Boar).where(Boar.farm_id == farm_id, Boar.status == "ACTIVE")) or 0
    # 포유자돈: 포유 중(미이유) 분만들의 잔여 = born_alive + foster_in - foster_out - deaths - weaned
    lact_farrows = list(await db.scalars(
        select(Farrowing).join(Sow, Sow.id == Farrowing.sow_id)
        .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None), Sow.status == "LACTATING")
    ))
    nursing = 0
    for f in lact_farrows:
        pe = (await db.execute(
            select(PigletEvent.event_type, func.coalesce(func.sum(PigletEvent.piglet_count), 0))
            .where(PigletEvent.farrowing_id == f.id, PigletEvent.deleted_at.is_(None))
            .group_by(PigletEvent.event_type)
        )).all()
        adj = {t: int(n) for t, n in pe}
        fi, fo, dd = adj.get("FOSTER_IN", 0), adj.get("FOSTER_OUT", 0), adj.get("DEATH", 0)
        wn = await db.scalar(select(func.coalesce(func.sum(Weaning.weaned_count), 0)).where(
            Weaning.farrowing_id == f.id, Weaning.deleted_at.is_(None))) or 0
        nursing += max(0, f.born_alive + fi - fo - dd - int(wn))
    finishers = await db.scalar(select(func.coalesce(func.sum(FinisherGroup.head_count_in - func.coalesce(FinisherGroup.head_count_out, 0)), 0))
        .where(FinisherGroup.farm_id == farm_id, FinisherGroup.deleted_at.is_(None), FinisherGroup.end_date.is_(None))) or 0
    herd_block = {
        "gilt": herd.get("GILT", 0), "open": herd.get("OPEN", 0), "pregnant": herd.get("PREGNANT", 0),
        "lactating": herd.get("LACTATING", 0), "accident": herd.get("ACCIDENT", 0),
        "sows_total": sum(herd.get(s, 0) for s in ("GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT")),
        "boars": int(boars), "nursing_piglets": nursing, "finishers": int(finishers),
    }

    # ── ③ 교배현황 (후보/경산/재교배) 일계·월계 ──
    async def mating_block(monthly: bool):
        rows = (await db.execute(
            select(Mating.mating_number, BreedingCycle.parity)
            .outerjoin(BreedingCycle, BreedingCycle.id == Mating.breeding_cycle_id)
            .where(Mating.farm_id == farm_id, Mating.deleted_at.is_(None), *_rng(Mating.mating_date, monthly))
        )).all()
        total = len(rows)
        gilt = sum(1 for mn, p in rows if mn == 1 and (p or 0) <= 1)
        sow = sum(1 for mn, p in rows if mn == 1 and (p or 0) >= 2)
        re = sum(1 for mn, _ in rows if (mn or 1) >= 2)
        return {"total": total, "gilt": gilt, "sow": sow, "rebreed": re}

    # ── ④ 임신사고 (유형별) 일계·월계 ──
    async def accident_block(monthly: bool):
        rows = (await db.execute(
            select(ReproductiveEvent.event_type, func.count())
            .where(ReproductiveEvent.farm_id == farm_id, ReproductiveEvent.deleted_at.is_(None),
                   ReproductiveEvent.event_type.in_(RTS_EVENT_TYPES), *_rng(ReproductiveEvent.event_date, monthly))
            .group_by(ReproductiveEvent.event_type)
        )).all()
        by = {t: c for t, c in rows}
        return {"total": sum(by.values()), "rts": by.get("RETURN_TO_ESTRUS", 0),
                "abortion": by.get("ABORTION", 0), "empty": by.get("EMPTY", 0), "infertile": by.get("INFERTILE", 0)}

    # ── ⑤ 생산현황 (분만/이유/자돈폐사) 일계·월계 ──
    async def production_block(monthly: bool):
        f = (await db.execute(
            select(func.count(), func.coalesce(func.sum(Farrowing.total_born), 0),
                   func.coalesce(func.sum(Farrowing.born_alive), 0), func.coalesce(func.sum(Farrowing.stillborn), 0),
                   func.coalesce(func.sum(Farrowing.mummified), 0), func.avg(Farrowing.avg_birth_weight_kg))
            .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None), *_rng(Farrowing.farrowing_date, monthly))
        )).one()
        w = (await db.execute(
            select(func.count(), func.coalesce(func.sum(Weaning.weaned_count), 0),
                   func.avg(Weaning.avg_weaning_weight_kg), func.avg(Weaning.weaning_age_days))
            .where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None), *_rng(Weaning.weaning_date, monthly))
        )).one()
        pd = (await db.execute(
            select(func.coalesce(func.sum(PigletEvent.piglet_count), 0))
            .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
                   PigletEvent.event_type == "DEATH", *_rng(PigletEvent.event_date, monthly))
        )).one()
        return {
            "farrowings": f[0], "total_born": int(f[1]), "born_alive": int(f[2]),
            "stillborn": int(f[3]), "mummified": int(f[4]),
            "avg_birth_weight": round(float(f[5]), 2) if f[5] is not None else None,
            "weanings": w[0], "weaned": int(w[1]),
            "avg_weaning_weight": round(float(w[2]), 2) if w[2] is not None else None,
            "avg_weaning_age": round(float(w[3]), 1) if w[3] is not None else None,
            "piglet_deaths": int(pd[0]),
        }

    # ── ⑥ 전입출·폐사 일계·월계 ──
    async def inout_block(monthly: bool):
        sow_in = (await db.execute(
            select(Sow.entry_type, func.count()).where(Sow.farm_id == farm_id, *_rng(func.date(Sow.entry_date), monthly))
            .group_by(Sow.entry_type)
        )).all()
        in_map = {et: c for et, c in sow_in}
        rm = (await db.execute(
            select(Removal.removal_type, func.count()).where(Removal.farm_id == farm_id, Removal.deleted_at.is_(None),
                   *_rng(Removal.removal_date, monthly)).group_by(Removal.removal_type)
        )).all()
        rm_map = {t: c for t, c in rm}
        boar_in = await db.scalar(select(func.count()).select_from(Boar).where(
            Boar.farm_id == farm_id, *_rng(func.date(Boar.entry_date), monthly))) or 0
        return {
            "gilt_in": in_map.get("GILT", 0), "sow_in": sum(c for et, c in in_map.items() if et != "GILT"),
            "dead": rm_map.get("DEAD", 0), "culled": rm_map.get("CULLED", 0),
            "sold": rm_map.get("SOLD", 0), "transfer": rm_map.get("TRANSFER", 0),
            "boar_in": int(boar_in),
        }

    return {
        "date": day.isoformat(),
        "herd": herd_block,
        "mating": {"day": await mating_block(False), "month": await mating_block(True)},
        "accidents": {"day": await accident_block(False), "month": await accident_block(True)},
        "production": {"day": await production_block(False), "month": await production_block(True)},
        "inout": {"day": await inout_block(False), "month": await inout_block(True)},
    }


# ── #1 모돈 현재 상태표 (DEV_GUIDE §5-C) ──────────────────────────────────────
ACTIVE_STATUSES = ("GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT")


async def get_sow_status_report(db: AsyncSession, farm_id: UUID) -> dict:
    """현재 모돈 상태별 두수 + 모돈 목록 (활성 개체만)."""
    rows = list(await db.scalars(
        select(Sow).where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        .order_by(Sow.status, Sow.ear_tag)
    ))
    by_status = {s: 0 for s in ACTIVE_STATUSES}
    sows = []
    for s in rows:
        if s.status in by_status:
            by_status[s.status] += 1
        sows.append({
            "sow_id": str(s.id), "ear_tag": s.ear_tag, "status": s.status,
            "parity": s.parity,
            "entry_date": _as_iso(s.entry_date),
        })
    return {"total": len(rows), "by_status": by_status, "sows": sows}


def _as_iso(v) -> str | None:
    if v is None:
        return None
    return v.date().isoformat() if hasattr(v, "date") else v.isoformat()


# ── #3 분만·포유·이유 성적표 (산차별) ─────────────────────────────────────────
def build_farrowing_rows(farrowings: list[dict], weanings_by_f: dict) -> list[dict]:
    """산차별 분만/이유 성적 집계 (pure)."""
    buckets: dict[int, dict] = {}
    for f in farrowings:
        p = f["parity"] or 0
        b = buckets.setdefault(p, {
            "parity": p, "_n": 0, "tb": [], "ba": [], "sb": [], "mum": [],
            "weaned": [], "lact": [],
        })
        b["_n"] += 1
        b["tb"].append(f["tb"]); b["ba"].append(f["ba"])
        b["sb"].append(f["sb"]); b["mum"].append(f["mum"])
        w = weanings_by_f.get(f["id"])
        if w:
            b["weaned"].append(w["weaned"])
            if w["lact"] is not None:
                b["lact"].append(w["lact"])
    rows = []
    for p in sorted(buckets):
        b = buckets[p]
        rows.append({
            "parity": p, "farrowings": b["_n"],
            "avg_total_born": _avg(b["tb"]), "avg_born_alive": _avg(b["ba"]),
            "avg_stillborn": _avg(b["sb"]), "avg_mummified": _avg(b["mum"]),
            "avg_weaned": _avg(b["weaned"]), "avg_lactation_days": _avg(b["lact"]),
            "litters_weaned": len(b["weaned"]),
        })
    return rows


async def get_farrowing_report(db: AsyncSession, farm_id: UUID, start: date, end: date) -> list[dict]:
    """산차별 분만/포유/이유 성적표 (기간 내 분만 기준)."""
    f_rows = (await db.execute(
        select(Farrowing.id, BreedingCycle.parity, Farrowing.total_born, Farrowing.born_alive,
               Farrowing.stillborn, Farrowing.mummified)
        .outerjoin(BreedingCycle, BreedingCycle.id == Farrowing.breeding_cycle_id)
        .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None),
               Farrowing.farrowing_date >= start, Farrowing.farrowing_date <= end)
    )).all()
    farrowings = [
        {"id": r[0], "parity": r[1], "tb": r[2], "ba": r[3], "sb": r[4], "mum": r[5]}
        for r in f_rows
    ]
    f_ids = [f["id"] for f in farrowings]
    weanings_by_f: dict = {}
    if f_ids:
        for r in (await db.execute(
            select(Weaning.farrowing_id, Weaning.weaned_count, Weaning.weaning_age_days)
            .where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None),
                   Weaning.farrowing_id.in_(f_ids))
        )).all():
            weanings_by_f[r[0]] = {"weaned": r[1], "lact": r[2]}
    return build_farrowing_rows(farrowings, weanings_by_f)


# ── #4 도폐사 / 포유폐사 리포트 ───────────────────────────────────────────────
async def get_mortality_report(db: AsyncSession, farm_id: UUID, start: date, end: date) -> dict:
    """기간 내 모돈 도폐사(유형·사유별) + 포유자돈 폐사(사유별) + 이유전 폐사율."""
    by_type = [
        {"key": k, "count": c} for k, c in (await db.execute(
            select(Removal.removal_type, func.count())
            .where(Removal.farm_id == farm_id, Removal.deleted_at.is_(None),
                   Removal.removal_date >= start, Removal.removal_date <= end)
            .group_by(Removal.removal_type).order_by(func.count().desc())
        )).all()
    ]
    by_reason = [
        {"key": k or "UNKNOWN", "count": c} for k, c in (await db.execute(
            select(Removal.reason_category, func.count())
            .where(Removal.farm_id == farm_id, Removal.deleted_at.is_(None),
                   Removal.removal_date >= start, Removal.removal_date <= end)
            .group_by(Removal.reason_category).order_by(func.count().desc())
        )).all()
    ]
    pd_rows = (await db.execute(
        select(PigletEvent.reason, func.count(), func.coalesce(func.sum(PigletEvent.piglet_count), 0))
        .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
               PigletEvent.event_type == "DEATH",
               PigletEvent.event_date >= start, PigletEvent.event_date <= end)
        .group_by(PigletEvent.reason).order_by(func.count().desc())
    )).all()
    piglet_deaths_by_reason = [
        {"key": r[0] or "UNKNOWN", "count": r[1], "piglets": int(r[2])} for r in pd_rows
    ]
    # 일령대별 포유자돈 폐사(D2) — age_days(서버 자동계산) 구간 분해
    _band = case(
        (PigletEvent.age_days <= 3, "0-3"),
        (PigletEvent.age_days <= 7, "4-7"),
        (PigletEvent.age_days <= 14, "8-14"),
        (PigletEvent.age_days <= 21, "15-21"),
        else_="22+",
    )
    age_rows = {
        r[0]: (int(r[1]), int(r[2])) for r in (await db.execute(
            select(_band.label("band"), func.count(),
                   func.coalesce(func.sum(PigletEvent.piglet_count), 0))
            .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
                   PigletEvent.event_type == "DEATH", PigletEvent.age_days.isnot(None),
                   PigletEvent.event_date >= start, PigletEvent.event_date <= end)
            .group_by(_band)
        )).all()
    }
    piglet_deaths_by_age = [
        {"key": b, "count": age_rows[b][0], "piglets": age_rows[b][1]}
        for b in ("0-3", "4-7", "8-14", "15-21", "22+") if age_rows.get(b)
    ]
    total_removals = sum(x["count"] for x in by_type)
    total_piglet_deaths = sum(x["piglets"] for x in piglet_deaths_by_reason)

    # 이유전 폐사율 = 기간 내 포유폐사 / 기간 내 실산 × 100 (근사)
    born_alive = await db.scalar(
        select(func.coalesce(func.sum(Farrowing.born_alive), 0))
        .where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None),
               Farrowing.farrowing_date >= start, Farrowing.farrowing_date <= end)
    ) or 0
    pre_wean_rate = round(total_piglet_deaths / born_alive * 100, 1) if born_alive else None

    return {
        "removals_by_type": by_type,
        "removals_by_reason": by_reason,
        "piglet_deaths_by_reason": piglet_deaths_by_reason,
        "piglet_deaths_by_age": piglet_deaths_by_age,
        "total_removals": total_removals,
        "total_piglet_deaths": total_piglet_deaths,
        "born_alive_in_period": int(born_alive),
        "preweaning_mortality_rate": pre_wean_rate,
    }


# ── 원가/수익 리포트 (#4) ─────────────────────────────────────────────────────
# 사료비(feed_records.unit_cost×quantity_kg) + 판매수익(removals.sale_price)을
# 통화별·기간별로 집계. 원가 미입력분은 net에서 제외하되 물량(feed_qty_kg)엔 포함,
# 완전성(coverage)을 함께 반환해 "입력 안 된 원가"를 숨기지 않는다(날조 금지 원칙).


def _round2(v) -> float | None:
    return round(float(v), 2) if v is not None else None


async def get_cost_summary(
    db: AsyncSession, farm, start: date, end: date, period: str
) -> dict:
    """기간 내 사료비·판매수익 집계. 통화 NULL은 농장 기본통화로 귀속."""
    default_ccy = farm.currency or "USD"

    # 사료비: 통화×기간별 Σ(qty×cost) 및 Σqty, 그리고 원가 입력 여부 카운트
    ccy = func.coalesce(FeedRecord.currency, default_ccy)
    feed_rows = (await db.execute(
        select(
            ccy.label("ccy"),
            FeedRecord.record_date,
            func.sum(FeedRecord.quantity_kg * FeedRecord.unit_cost),
            func.sum(FeedRecord.quantity_kg),
            func.count(),
            func.count(FeedRecord.unit_cost),
        )
        .where(FeedRecord.farm_id == farm.id, FeedRecord.deleted_at.is_(None),
               FeedRecord.record_date >= start, FeedRecord.record_date <= end)
        .group_by(ccy, FeedRecord.record_date)
    )).all()

    # 판매수익: 통화×기간별 Σsale_price, 두수, Σbody_weight (removal_type='SOLD')
    sccy = func.coalesce(Removal.sale_currency, default_ccy)
    sale_rows = (await db.execute(
        select(
            sccy.label("ccy"),
            Removal.removal_date,
            func.sum(Removal.sale_price),
            func.count(),
            func.sum(Removal.body_weight_kg),
        )
        .where(Removal.farm_id == farm.id, Removal.deleted_at.is_(None),
               Removal.removal_type == "SOLD",
               Removal.removal_date >= start, Removal.removal_date <= end)
        .group_by(sccy, Removal.removal_date)
    )).all()

    # (period, ccy) → 누적 집계
    cells: dict[tuple[str, str], dict] = {}
    feed_total = feed_with_cost = 0

    def _cell(pk: str, cur: str) -> dict:
        return cells.setdefault((pk, cur), {
            "feed_cost": None, "feed_qty_kg": 0.0,
            "sale_revenue": None, "sale_head": 0, "sale_weight_kg": None,
        })

    for cur, d, cost, qty, cnt, cnt_cost in feed_rows:
        c = _cell(period_key(d, period), cur)
        c["feed_qty_kg"] += float(qty or 0)
        if cost is not None:
            c["feed_cost"] = (c["feed_cost"] or 0.0) + float(cost)
        feed_total += int(cnt or 0)
        feed_with_cost += int(cnt_cost or 0)

    for cur, d, rev, head, wt in sale_rows:
        c = _cell(period_key(d, period), cur)
        c["sale_head"] += int(head or 0)
        if rev is not None:
            c["sale_revenue"] = (c["sale_revenue"] or 0.0) + float(rev)
        if wt is not None:
            c["sale_weight_kg"] = (c["sale_weight_kg"] or 0.0) + float(wt)

    def _net(cell: dict) -> float | None:
        if cell["sale_revenue"] is None and cell["feed_cost"] is None:
            return None
        return round((cell["sale_revenue"] or 0.0) - (cell["feed_cost"] or 0.0), 2)

    rows = [
        {
            "period": pk, "currency": cur,
            "feed_cost": _round2(cell["feed_cost"]),
            "feed_qty_kg": round(cell["feed_qty_kg"], 1),
            "sale_revenue": _round2(cell["sale_revenue"]),
            "sale_head": cell["sale_head"],
            "net": _net(cell),
        }
        for (pk, cur), cell in sorted(cells.items())
    ]

    # 통화별 총계
    by_ccy: dict[str, dict] = {}
    for (_pk, cur), cell in cells.items():
        agg = by_ccy.setdefault(cur, {
            "feed_cost": None, "feed_qty_kg": 0.0,
            "sale_revenue": None, "sale_head": 0, "sale_weight_kg": None,
        })
        agg["feed_qty_kg"] += cell["feed_qty_kg"]
        agg["sale_head"] += cell["sale_head"]
        for k in ("feed_cost", "sale_revenue", "sale_weight_kg"):
            if cell[k] is not None:
                agg[k] = (agg[k] or 0.0) + cell[k]

    by_currency = [
        {
            "currency": cur,
            "feed_cost": _round2(agg["feed_cost"]),
            "feed_qty_kg": round(agg["feed_qty_kg"], 1),
            "sale_revenue": _round2(agg["sale_revenue"]),
            "sale_head": agg["sale_head"],
            "sale_weight_kg": _round2(agg["sale_weight_kg"]),
            "net": _net(agg),
        }
        for cur, agg in sorted(by_ccy.items())
    ]

    coverage = round(feed_with_cost / feed_total * 100, 1) if feed_total else None
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "period": period,
        "by_currency": by_currency,
        "rows": rows,
        "feed_cost_coverage": coverage,
        "feed_records_total": feed_total,
        "feed_records_with_cost": feed_with_cost,
    }


# ── 데이터 품질/정합성 리포트 (#5 — DEV_GUIDE §5-C) ───────────────────────────
# "두수 안 꼬임"을 가시화: 두수 불일치·날짜 역전·상태 고아·입력 누락(과기한) 탐지.
# 검증이 막는 신규 입력 외에, 레거시/sync 경로로 들어온 부정합을 사후 점검한다.

GESTATION_OVERDUE_DAYS = 130   # 임신 후 이 일수 초과 미분만 → 분만 입력 누락 의심
LACTATION_OVERDUE_DAYS = 60    # 분만 후 이 일수 초과 미이유 → 이유 입력 누락 의심


async def get_data_quality_report(db: AsyncSession, farm_id: UUID, today: date) -> list[dict]:
    """농장의 데이터 정합성 이슈 목록. severity: CRITICAL(두수/역전) | WARNING(누락/고아)."""
    issues: list[dict] = []

    def add(issue_type, severity, sow_id, ear_tag, detail, event_date=None):
        issues.append({
            "issue_type": issue_type, "severity": severity,
            "sow_id": str(sow_id) if sow_id else None, "ear_tag": ear_tag,
            "detail": detail, "event_date": event_date.isoformat() if event_date else None,
        })

    # 모돈 메타 (ear_tag/status/entry/exit)
    sows = {
        s.id: s for s in await db.scalars(
            select(Sow).where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        )
    }

    # 1) 분만 두수 불일치 (total != BA+SB+MUM)
    farrowings = list(await db.scalars(
        select(Farrowing).where(Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None))
    ))
    for f in farrowings:
        if f.total_born != f.born_alive + f.stillborn + f.mummified:
            tag = sows[f.sow_id].ear_tag if f.sow_id in sows else "?"
            add("LITTER_MISMATCH", "CRITICAL", f.sow_id, tag,
                f"total_born {f.total_born} ≠ BA {f.born_alive}+SB {f.stillborn}+MUM {f.mummified}",
                f.farrowing_date)

    # 2) 분만 < 교배 날짜 역전
    mate_dates = {
        r[0]: r[1] for r in (await db.execute(
            select(Mating.id, Mating.mating_date).where(
                Mating.farm_id == farm_id, Mating.deleted_at.is_(None))
        )).all()
    }
    for f in farrowings:
        md = mate_dates.get(f.mating_id)
        if md and f.farrowing_date < md:
            tag = sows[f.sow_id].ear_tag if f.sow_id in sows else "?"
            add("DATE_REVERSAL", "CRITICAL", f.sow_id, tag,
                f"farrowing {f.farrowing_date} before mating {md}", f.farrowing_date)

    # 3) 이유두수 > 유효 복당두수 (born_alive + foster_in - foster_out - deaths)
    pe_rows = (await db.execute(
        select(PigletEvent.farrowing_id, PigletEvent.event_type,
               func.coalesce(func.sum(PigletEvent.piglet_count), 0))
        .where(PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None))
        .group_by(PigletEvent.farrowing_id, PigletEvent.event_type)
    )).all()
    adj: dict = {}
    for fid, et, n in pe_rows:
        d = adj.setdefault(fid, {"FOSTER_IN": 0, "FOSTER_OUT": 0, "DEATH": 0})
        if et in d:
            d[et] = int(n)
    ba_by_f = {f.id: (f.born_alive, f.sow_id, f.farrowing_date) for f in farrowings}
    weanings = list(await db.scalars(
        select(Weaning).where(Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None))
    ))
    # 부분이유 대비: farrowing별 이유두수 합계가 유효복당두수 초과 시 불일치
    weaned_sum_by_f: dict = {}
    last_wean_date: dict = {}
    for w in weanings:
        weaned_sum_by_f[w.farrowing_id] = weaned_sum_by_f.get(w.farrowing_id, 0) + w.weaned_count
        if w.farrowing_id not in last_wean_date or w.weaning_date > last_wean_date[w.farrowing_id]:
            last_wean_date[w.farrowing_id] = w.weaning_date
        base = ba_by_f.get(w.farrowing_id)
        if base and base[2] and w.weaning_date < base[2]:
            tag = sows[base[1]].ear_tag if base[1] in sows else "?"
            add("DATE_REVERSAL", "CRITICAL", base[1], tag,
                f"weaning {w.weaning_date} before farrowing {base[2]}", w.weaning_date)
    for fid, total_weaned in weaned_sum_by_f.items():
        base = ba_by_f.get(fid)
        if not base:
            continue
        ba, sow_id, _ = base
        a = adj.get(fid, {"FOSTER_IN": 0, "FOSTER_OUT": 0, "DEATH": 0})
        effective = max(0, ba + a["FOSTER_IN"] - a["FOSTER_OUT"] - a["DEATH"])
        if total_weaned > effective:
            tag = sows[sow_id].ear_tag if sow_id in sows else "?"
            add("WEANED_MISMATCH", "CRITICAL", sow_id, tag,
                f"total weaned {total_weaned} > effective litter {effective}", last_wean_date.get(fid))

    # 4) 입력 누락(과기한): PREGNANT인데 최근 교배 후 130일↑ 미분만 / LACTATING인데 분만 후 60일↑ 미이유
    last_mate: dict = {}
    for r in (await db.execute(
        select(Mating.sow_id, func.max(Mating.mating_date)).where(
            Mating.farm_id == farm_id, Mating.deleted_at.is_(None)).group_by(Mating.sow_id)
    )).all():
        last_mate[r[0]] = r[1]
    last_farrow: dict = {}
    for r in (await db.execute(
        select(Farrowing.sow_id, func.max(Farrowing.farrowing_date)).where(
            Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None)).group_by(Farrowing.sow_id)
    )).all():
        last_farrow[r[0]] = r[1]

    for sow in sows.values():
        if sow.status == "PREGNANT":
            md = last_mate.get(sow.id)
            if md is None:
                add("STATUS_ORPHAN", "WARNING", sow.id, sow.ear_tag,
                    "status PREGNANT but no mating recorded")
            elif (today - md).days > GESTATION_OVERDUE_DAYS:
                add("MISSING_FARROWING", "WARNING", sow.id, sow.ear_tag,
                    f"{(today - md).days}d since mating, farrowing not recorded", md)
        elif sow.status == "LACTATING":
            fd = last_farrow.get(sow.id)
            if fd is None:
                add("STATUS_ORPHAN", "WARNING", sow.id, sow.ear_tag,
                    "status LACTATING but no farrowing recorded")
            elif (today - fd).days > LACTATION_OVERDUE_DAYS:
                add("MISSING_WEANING", "WARNING", sow.id, sow.ear_tag,
                    f"{(today - fd).days}d since farrowing, weaning not recorded", fd)

    severity_rank = {"CRITICAL": 0, "WARNING": 1}
    issues.sort(key=lambda i: (severity_rank.get(i["severity"], 9), i["issue_type"]))
    return issues
