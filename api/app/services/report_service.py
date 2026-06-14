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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.events import (
    Farrowing,
    Mating,
    PigletEvent,
    ReproductiveEvent,
    Weaning,
)
from app.db.models.ops import FinisherGroup
from app.db.models.health import FeedRecord
from app.db.models.sow import BreedingCycle

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


# ── Reproduction ──────────────────────────────────────────────────────────────

def build_reproduction_rows(
    period: str,
    matings: list[date],
    farrowings: list[tuple[date, int, int]],          # (date, total_born, born_alive)
    weanings: list[tuple[date, int, int | None]],     # (date, weaned_count, lactation_days)
    rts: list[date],
    deaths: list[tuple[date, int]],                   # (date, piglet_death_count)
) -> list[dict]:
    buckets: dict[str, dict] = {}

    def b(key: str) -> dict:
        return buckets.setdefault(
            key,
            {"matings": 0, "farrowings": 0, "weanings": 0, "rts": 0,
             "tb": [], "ba": [], "weaned": [], "lact": [], "deaths": 0},
        )

    for d in matings:
        b(period_key(d, period))["matings"] += 1
    for d, tb, ba in farrowings:
        x = b(period_key(d, period)); x["farrowings"] += 1; x["tb"].append(tb); x["ba"].append(ba)
    for d, wc, lact in weanings:
        x = b(period_key(d, period)); x["weanings"] += 1; x["weaned"].append(wc); x["lact"].append(lact)
    for d in rts:
        b(period_key(d, period))["rts"] += 1
    for d, n in deaths:
        b(period_key(d, period))["deaths"] += n

    rows = []
    for key in sorted(buckets):
        x = buckets[key]
        avg_tb = _avg(x["tb"])
        avg_weaned = _avg(x["weaned"])
        total_weaned = sum(w for w in x["weaned"] if w is not None)
        fr = round(x["farrowings"] / x["matings"] * 100, 1) if x["matings"] else None
        rts_rate = round(x["rts"] / x["matings"] * 100, 1) if x["matings"] else None
        pwmr_b = (
            round((avg_tb - avg_weaned) / avg_tb * 100, 1)
            if avg_tb and avg_weaned is not None and avg_tb > 0
            else None
        )
        denom_a = total_weaned + x["deaths"]
        pwmr_a = round(x["deaths"] / denom_a * 100, 1) if denom_a > 0 else None
        rows.append({
            "period": key,
            "total_matings": x["matings"],
            "total_farrowings": x["farrowings"],
            "total_weanings": x["weanings"],
            "fr": fr,
            "avg_tb": avg_tb,
            "avg_ba": _avg(x["ba"]),
            "avg_weaned": avg_weaned,
            "avg_lactation_days": _avg(x["lact"]),
            "pwmr_a": pwmr_a,
            "pwmr_b": pwmr_b,
            "rts_rate": rts_rate,
        })
    return rows


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
    w_by = {w["cycle_id"]: w for w in weanings}

    out = []
    for c in sorted(cycles, key=lambda c: c["parity"]):
        cid = c["cycle_id"]
        ms = sorted(m_by.get(cid, []), key=lambda m: m["date"])
        f = f_by.get(cid)
        w = w_by.get(cid)
        completed = w is not None
        out.append({
            "parity": c["parity"],
            "mating_date": ms[0]["date"].isoformat() if ms else None,
            "boar_ids": [m["boar_id"] for m in ms if m.get("boar_id")],
            "farrowing_date": f["date"].isoformat() if f else None,
            "tb": f["tb"] if f else None,
            "ba": f["ba"] if f else None,
            "sb": f["sb"] if f else None,
            "mum": f["mum"] if f else None,
            "weaned": w["weaned"] if w else None,
            "weaning_date": w["date"].isoformat() if w else None,
            "lactation_days": w["lactation_days"] if w else None,
            "status": "completed" if completed else "in_progress",
        })
    return out


# ── DB wrappers ───────────────────────────────────────────────────────────────

async def get_reproduction_report(
    db: AsyncSession, farm_id: UUID, start: date, end: date, period: str
) -> list[dict]:
    mrows = (await db.execute(
        select(Mating.mating_date).where(
            Mating.farm_id == farm_id, Mating.deleted_at.is_(None),
            Mating.mating_date >= start, Mating.mating_date <= end)
    )).all()
    frows = (await db.execute(
        select(Farrowing.farrowing_date, Farrowing.total_born, Farrowing.born_alive).where(
            Farrowing.farm_id == farm_id, Farrowing.deleted_at.is_(None),
            Farrowing.farrowing_date >= start, Farrowing.farrowing_date <= end)
    )).all()
    wrows = (await db.execute(
        select(Weaning.weaning_date, Weaning.weaned_count, Weaning.weaning_age_days).where(
            Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None),
            Weaning.weaning_date >= start, Weaning.weaning_date <= end)
    )).all()
    rrows = (await db.execute(
        select(ReproductiveEvent.event_date).where(
            ReproductiveEvent.farm_id == farm_id, ReproductiveEvent.deleted_at.is_(None),
            ReproductiveEvent.event_type.in_(RTS_EVENT_TYPES),
            ReproductiveEvent.event_date >= start, ReproductiveEvent.event_date <= end)
    )).all()
    drows = (await db.execute(
        select(PigletEvent.event_date, PigletEvent.piglet_count).where(
            PigletEvent.farm_id == farm_id, PigletEvent.deleted_at.is_(None),
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
    )


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
    cycles = list(await db.scalars(
        select(BreedingCycle).where(BreedingCycle.sow_id == sow_id, BreedingCycle.farm_id == farm_id)
    ))
    matings = (await db.execute(
        select(Mating.breeding_cycle_id, Mating.mating_date, Mating.boar_id).where(
            Mating.sow_id == sow_id, Mating.deleted_at.is_(None))
    )).all()
    farrowings = (await db.execute(
        select(Farrowing.breeding_cycle_id, Farrowing.farrowing_date, Farrowing.total_born,
               Farrowing.born_alive, Farrowing.stillborn, Farrowing.mummified).where(
            Farrowing.sow_id == sow_id, Farrowing.deleted_at.is_(None))
    )).all()
    weanings = (await db.execute(
        select(Weaning.breeding_cycle_id, Weaning.weaning_date, Weaning.weaned_count,
               Weaning.weaning_age_days).where(
            Weaning.sow_id == sow_id, Weaning.deleted_at.is_(None))
    )).all()

    return build_sow_history(
        [{"cycle_id": c.id, "parity": c.parity, "status": c.cycle_status} for c in cycles],
        [{"cycle_id": r[0], "date": r[1], "boar_id": str(r[2]) if r[2] else None} for r in matings],
        [{"cycle_id": r[0], "date": r[1], "tb": r[2], "ba": r[3], "sb": r[4], "mum": r[5]} for r in farrowings],
        [{"cycle_id": r[0], "date": r[1], "weaned": r[2], "lactation_days": r[3]} for r in weanings],
    )
