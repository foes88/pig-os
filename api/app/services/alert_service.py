"""
Alert service — overdue sows & cull recommendations.

Reference: docs/SCREEN_MENU_SPEC.md → "Alerts / Tasks" (6 overdue types + 3 cull criteria).

Design: the classification logic is pure (``classify_overdue`` / ``classify_cull``)
so it unit-tests without a DB. ``get_overdue_sows`` / ``get_cull_candidates`` are
thin async wrappers that load the rows and apply the pure classifiers.

Note: the ``sows`` table has no date-of-birth column, so "gilt age" is approximated
by days since ``entry_date``. Thresholds come from ``farm_configs`` (key/value),
falling back to PigPlan defaults.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.config import FarmConfig
from app.db.models.events import Farrowing, Mating, ReproductiveEvent, Weaning
from app.db.models.sow import Sow

# Reproductive events that count as a "return to service" (non-productive).
RTS_EVENT_TYPES = ("RETURN_TO_ESTRUS", "ABORTION", "EMPTY", "INFERTILE")
ACTIVE_STATUSES = ("GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT")
OVERDUE_TYPES = (
    "gilt_no_estrus",
    "gilt_overdue_mating",
    "pregnant_overdue_farrowing",
    "lactating_overdue_weaning",
    "open_overdue_mating",
    "accident_overdue_mating",
)


@dataclass(frozen=True)
class AlertThresholds:
    gestation_days: int = 114
    lactation_days: int = 21
    wsi_days: int = 7
    gilt_estrus_check_age: int = 180
    gilt_first_mating_age: int = 240
    gilt_unmated_alert_age: int = 300
    cull_parity_threshold: int = 7
    cull_min_weaned: int = 9
    cull_consecutive_rts: int = 3


def _days_since(today: date, ref: date | None) -> int | None:
    return (today - ref).days if ref is not None else None


def _as_date(value):
    if value is None:
        return None
    return value.date() if isinstance(value, datetime) else value


# ── Pure classifiers ──────────────────────────────────────────────────────────

def classify_overdue(
    *,
    status: str,
    today: date,
    age_days: int | None = None,
    has_heat: bool = False,
    last_mating: date | None = None,
    last_farrowing: date | None = None,
    last_weaning: date | None = None,
    last_rts: date | None = None,
    th: AlertThresholds = AlertThresholds(),
) -> tuple[str, int] | None:
    """Return ``(overdue_type, overdue_days)`` or ``None`` if the sow is on schedule."""
    if status == "GILT":
        if last_mating is None and age_days is not None and age_days > th.gilt_first_mating_age:
            return "gilt_overdue_mating", age_days - th.gilt_first_mating_age
        if not has_heat and age_days is not None and age_days >= th.gilt_estrus_check_age:
            return "gilt_no_estrus", age_days - th.gilt_estrus_check_age
        return None
    if status == "PREGNANT":
        d = _days_since(today, last_mating)
        if d is not None and d > th.gestation_days:
            return "pregnant_overdue_farrowing", d - th.gestation_days
        return None
    if status == "LACTATING":
        d = _days_since(today, last_farrowing)
        if d is not None and d > th.lactation_days:
            return "lactating_overdue_weaning", d - th.lactation_days
        return None
    if status == "OPEN":
        d = _days_since(today, last_weaning)
        if d is not None and d > th.wsi_days:
            return "open_overdue_mating", d - th.wsi_days
        return None
    if status == "ACCIDENT":
        d = _days_since(today, last_rts)
        if d is not None and d > th.wsi_days:
            return "accident_overdue_mating", d - th.wsi_days
        return None
    return None


def classify_cull(
    *,
    status: str,
    parity: int | None,
    age_days: int | None = None,
    last_mating: date | None = None,
    last_weaned_count: int | None = None,
    consecutive_rts: int = 0,
    th: AlertThresholds = AlertThresholds(),
) -> list[str]:
    """Return a list of cull-recommendation reason codes (empty if none apply)."""
    reasons: list[str] = []
    if consecutive_rts >= th.cull_consecutive_rts:
        reasons.append("repeat_rts")
    if (
        parity is not None
        and parity > th.cull_parity_threshold
        and last_weaned_count is not None
        and last_weaned_count < th.cull_min_weaned
    ):
        reasons.append("aged_low_performer")
    if (
        status == "GILT"
        and last_mating is None
        and age_days is not None
        and age_days > th.gilt_unmated_alert_age
    ):
        reasons.append("overdue_gilt")
    return reasons


# ── DB layer ──────────────────────────────────────────────────────────────────

async def _load_thresholds(db: AsyncSession, farm_id: UUID) -> AlertThresholds:
    rows = await db.scalars(select(FarmConfig).where(FarmConfig.farm_id == farm_id))
    cfg = {r.config_key: r.config_value for r in rows}

    def _int(key: str, default: int) -> int:
        try:
            return int(cfg[key])
        except (KeyError, ValueError, TypeError):
            return default

    return AlertThresholds(
        gestation_days=_int("GESTATION_DAYS", 114),
        lactation_days=_int("LACTATION_DAYS", 21),
        wsi_days=_int("WEI_TARGET_DAYS", 7),
        gilt_first_mating_age=_int("GILT_FIRST_MATING_AGE", 240),
        gilt_unmated_alert_age=_int("GILT_UNMATED_ALERT_AGE", 300),
        cull_parity_threshold=_int("SOW_CULL_PARITY_THRESHOLD", 7),
    )


async def _latest_date_map(db: AsyncSession, farm_id: UUID, model, date_col) -> dict[UUID, date]:
    q = (
        select(model.sow_id, func.max(date_col))
        .where(model.farm_id == farm_id, model.deleted_at.is_(None))
        .group_by(model.sow_id)
    )
    return {sid: d for sid, d in (await db.execute(q)).all()}


async def get_overdue_sows(
    db: AsyncSession, farm_id: UUID, today: date | None = None
) -> list[dict]:
    th = await _load_thresholds(db, farm_id)
    today = today or datetime.now(UTC).date()

    sows = list(
        await db.scalars(
            select(Sow).where(
                Sow.farm_id == farm_id,
                Sow.deleted_at.is_(None),
                Sow.status.in_(ACTIVE_STATUSES),
            )
        )
    )
    last_mating = await _latest_date_map(db, farm_id, Mating, Mating.mating_date)
    last_farrowing = await _latest_date_map(db, farm_id, Farrowing, Farrowing.farrowing_date)
    last_weaning = await _latest_date_map(db, farm_id, Weaning, Weaning.weaning_date)

    rts_q = (
        select(ReproductiveEvent.sow_id, func.max(ReproductiveEvent.event_date))
        .where(
            ReproductiveEvent.farm_id == farm_id,
            ReproductiveEvent.deleted_at.is_(None),
            ReproductiveEvent.event_type.in_(RTS_EVENT_TYPES),
        )
        .group_by(ReproductiveEvent.sow_id)
    )
    last_rts = {sid: d for sid, d in (await db.execute(rts_q)).all()}

    heat_q = (
        select(ReproductiveEvent.sow_id)
        .where(
            ReproductiveEvent.farm_id == farm_id,
            ReproductiveEvent.deleted_at.is_(None),
            ReproductiveEvent.event_type == "HEAT_DETECTED",
        )
        .distinct()
    )
    heat_set = set((await db.scalars(heat_q)).all())

    results: list[dict] = []
    for s in sows:
        entry = _as_date(s.entry_date)
        age_days = (today - entry).days if entry else None
        cls = classify_overdue(
            status=s.status,
            today=today,
            age_days=age_days,
            has_heat=s.id in heat_set,
            last_mating=last_mating.get(s.id),
            last_farrowing=last_farrowing.get(s.id),
            last_weaning=last_weaning.get(s.id),
            last_rts=last_rts.get(s.id),
            th=th,
        )
        if cls:
            otype, overdue_days = cls
            results.append(
                {
                    "type": otype,
                    "sow_id": s.id,
                    "ear_tag": s.ear_tag,
                    "status": s.status,
                    "parity": s.parity,
                    "overdue_days": overdue_days,
                }
            )
    return results


async def get_cull_candidates(db: AsyncSession, farm_id: UUID, today: date | None = None) -> list[dict]:
    th = await _load_thresholds(db, farm_id)
    today = today or datetime.now(UTC).date()

    sows = list(
        await db.scalars(
            select(Sow).where(
                Sow.farm_id == farm_id,
                Sow.deleted_at.is_(None),
                Sow.status.in_(ACTIVE_STATUSES),
            )
        )
    )
    last_farrowing = await _latest_date_map(db, farm_id, Farrowing, Farrowing.farrowing_date)
    last_mating = await _latest_date_map(db, farm_id, Mating, Mating.mating_date)

    # Latest weaning weaned_count per sow.
    wean_rows = (
        await db.execute(
            select(Weaning.sow_id, Weaning.weaning_date, Weaning.weaned_count).where(
                Weaning.farm_id == farm_id, Weaning.deleted_at.is_(None)
            )
        )
    ).all()
    last_weaned: dict[UUID, tuple[date, int]] = {}
    for sid, wdate, wcount in wean_rows:
        if sid not in last_weaned or wdate > last_weaned[sid][0]:
            last_weaned[sid] = (wdate, wcount)

    # RTS events (for consecutive-since-last-farrowing count).
    rts_rows = (
        await db.execute(
            select(ReproductiveEvent.sow_id, ReproductiveEvent.event_date).where(
                ReproductiveEvent.farm_id == farm_id,
                ReproductiveEvent.deleted_at.is_(None),
                ReproductiveEvent.event_type.in_(RTS_EVENT_TYPES),
            )
        )
    ).all()
    rts_by_sow: dict[UUID, list[date]] = {}
    for sid, edate in rts_rows:
        rts_by_sow.setdefault(sid, []).append(edate)

    results: list[dict] = []
    for s in sows:
        entry = _as_date(s.entry_date)
        age_days = (today - entry).days if entry else None
        farrow_cut = last_farrowing.get(s.id)
        consecutive_rts = sum(
            1 for d in rts_by_sow.get(s.id, []) if farrow_cut is None or d > farrow_cut
        )
        weaned = last_weaned.get(s.id, (None, None))[1]
        reasons = classify_cull(
            status=s.status,
            parity=s.parity,
            age_days=age_days,
            last_mating=last_mating.get(s.id),
            last_weaned_count=weaned,
            consecutive_rts=consecutive_rts,
            th=th,
        )
        if reasons:
            results.append(
                {
                    "sow_id": s.id,
                    "ear_tag": s.ear_tag,
                    "status": s.status,
                    "parity": s.parity,
                    "reasons": reasons,
                    "last_weaned": weaned,
                }
            )
    return results
