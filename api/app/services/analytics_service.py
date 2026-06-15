"""
분석 서비스 — PRRS 유전자(품종) 성과 추적 (Phase 2).

sow.breed / breed_company / genetics_id 별로 health_events(disease_code ILIKE 'PRRS%')를
집계하여 품종(유전자)별 PRRS 발생률을 비교한다.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.health import HealthEvent
from app.db.models.sow import Sow

# disease_code 예: PRRS_1, PRRS_2, PRRS_144C, PRRS_1C5 → 접두사 매칭
_PRRS_PREFIX = "PRRS%"


async def prrs_by_genetics(db: AsyncSession, farm_id: UUID) -> dict:
    """품종/유전자별 PRRS 발생률 집계.

    rows: (breed, breed_company, genetics_id, total_sows, affected_sows, prrs_events, incidence_rate)
    incidence_rate = affected_sows / total_sows * 100 (발생률, 1자리 반올림).
    """
    # 1) 품종/유전자 그룹별 전체 모돈 수
    sow_rows = (await db.execute(
        select(
            Sow.breed, Sow.breed_company, Sow.genetics_id, func.count().label("total"),
        )
        .where(Sow.farm_id == farm_id, Sow.deleted_at.is_(None))
        .group_by(Sow.breed, Sow.breed_company, Sow.genetics_id)
    )).all()

    # 2) PRRS health_event를 모돈 유전자에 조인하여 그룹별 집계
    ev_rows = (await db.execute(
        select(
            Sow.breed, Sow.breed_company, Sow.genetics_id,
            func.count(HealthEvent.id).label("events"),
            func.count(func.distinct(HealthEvent.sow_id)).label("affected"),
        )
        .select_from(HealthEvent)
        .join(Sow, Sow.id == HealthEvent.sow_id)
        .where(
            HealthEvent.farm_id == farm_id,
            HealthEvent.deleted_at.is_(None),
            HealthEvent.disease_code.ilike(_PRRS_PREFIX),
        )
        .group_by(Sow.breed, Sow.breed_company, Sow.genetics_id)
    )).all()
    ev_map = {(b, c, g): (int(events), int(affected)) for b, c, g, events, affected in ev_rows}

    rows: list[dict] = []
    total_sows = total_affected = total_events = 0
    for breed, company, genetics, total in sow_rows:
        events, affected = ev_map.get((breed, company, genetics), (0, 0))
        total = int(total)
        rate = round(affected / total * 100, 1) if total else 0.0
        rows.append({
            "breed": breed,
            "breed_company": company,
            "genetics_id": genetics,
            "total_sows": total,
            "affected_sows": affected,
            "prrs_events": events,
            "incidence_rate": rate,
        })
        total_sows += total
        total_affected += affected
        total_events += events

    rows.sort(key=lambda r: r["incidence_rate"], reverse=True)
    return {
        "farm_id": farm_id,
        "rows": rows,
        "total_sows": total_sows,
        "total_affected": total_affected,
        "total_events": total_events,
    }
