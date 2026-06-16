"""
이벤트 입력 즉시 분석 (Event Insight).

사용자가 분만/이유/교배를 저장하는 순간 그 레코드를 분석해 normal/warning/critical 판정.
원칙(스펙 docs/specs/2026-06-16_event-insight-mapping.md):
- 임계값은 effective_metric_values()(default_metric_values)에서 읽음 → 코드 하드코딩 0.
- null 임계값 = 해당 레벨 판정 skip (GPT 리서치 원칙).
- WEANING_AGE는 LOW(below)/HIGH(above) 2메트릭으로 양방향 밴드.
- 분석 실패가 입력 자체를 막지 않게 호출부에서 격리.
- 문구는 구조화(EventInsight)만 반환 — 자연어는 프론트 i18n(무료) / LLM(addon).
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.config import DefaultMetricValue
from app.db.models.events import Farrowing, Mating, Weaning
from app.db.models.platform import Farm
from app.engine.rule_engine import Severity
from app.engine.rules.base import _severity_from_bench
from app.schemas.insight import EventInsight

# scope 우선순위: 농장 > 지역(국가) > 시스템(글로벌). effective_metric_values()와 동일 체인.
_SCOPE_RANK = {"farm": 0, "region": 1, "market": 2, "system": 3}

# metric 중요도(작을수록 우선) — 동일 severity·gap일 때 메인 선정 tiebreaker
_METRIC_PRIORITY = {
    "PRE_WEANING_MORTALITY": 10,
    "STILLBORN_RATE": 20,
    "BORN_ALIVE": 30,
    "WEANED_COUNT": 40,
    "WSI": 50,
    "RTS_RATE": 55,
    "WEANING_AGE_LOW": 70,
    "WEANING_AGE_HIGH": 70,
}


async def _load_benchmark(db: AsyncSession, metric_code: str, farm: Farm) -> dict | None:
    """default_metric_values를 우선순위 체인으로 직접 조회 (DB 함수 비의존, 테스트 가능).
    해당 메트릭 임계값 + 글로벌(system) 폴백 여부. 행 없으면 None."""
    rows = list(await db.scalars(
        select(DefaultMetricValue).where(
            DefaultMetricValue.metric_code == metric_code,
            DefaultMetricValue.scope_code.in_([str(farm.id), farm.country, "SYSTEM"]),
        )
    ))
    # 농장/국가/시스템 중 가장 구체적인 scope 선택
    rows = [r for r in rows if (
        (r.scope_type == "farm" and r.scope_code == str(farm.id))
        or (r.scope_type == "region" and r.scope_code == farm.country)
        or (r.scope_type == "system" and r.scope_code == "SYSTEM")
    )]
    if not rows:
        return None
    best = min(rows, key=lambda r: _SCOPE_RANK.get(r.scope_type, 9))
    return {
        "warning": float(best.warning_threshold) if best.warning_threshold is not None else None,
        "critical": float(best.critical_threshold) if best.critical_threshold is not None else None,
        "avg": float(best.benchmark_avg) if best.benchmark_avg is not None else None,
        "top25": float(best.benchmark_top25) if best.benchmark_top25 is not None else None,
        "direction": best.alert_direction or "below",
        "unit": best.unit_code or "",
        "confidence": best.confidence,
        "is_proxy": bool(best.is_proxy),
        "source": best.source_ref,
        "is_global_fallback": best.scope_type == "system",
    }


async def _load_price(db: AsyncSession, farm: Farm) -> dict | None:
    """출하 두당가격(MARKET_PRICE_HEAD) — 손실 계산용. 없으면 None(금액 표시 안 함)."""
    rows = list(await db.scalars(
        select(DefaultMetricValue).where(
            DefaultMetricValue.metric_code == "MARKET_PRICE_HEAD",
            DefaultMetricValue.scope_code.in_([str(farm.id), farm.country, "SYSTEM"]),
        )
    ))
    rows = [r for r in rows if (
        (r.scope_type == "farm" and r.scope_code == str(farm.id))
        or (r.scope_type == "region" and r.scope_code == farm.country)
        or (r.scope_type == "system" and r.scope_code == "SYSTEM")
    )]
    if not rows:
        return None
    best = min(rows, key=lambda r: _SCOPE_RANK.get(r.scope_type, 9))
    if best.default_value is None:
        return None
    return {
        "price": float(best.default_value),
        "currency": best.unit_code or "",
        # 가격이 저신뢰/프록시/글로벌 폴백이면 Demo 표시
        "demo": bool(best.is_proxy) or best.confidence == "low" or best.scope_type == "system",
    }


def _loss(lost_pigs: float, price: dict) -> dict:
    """손실두수 × 출하두당가격 = 손실액(LOSS_CALC). price 없으면 호출 안 함."""
    return {
        "amount": round(lost_pigs * price["price"]),
        "currency": price["currency"],
        "lost_pigs": round(lost_pigs, 1),
        "basis": "lost_market_pigs",  # 손실두수 × 출하두당가
        "demo": price["demo"],
    }


async def _evaluate(db: AsyncSession, farm: Farm, metric_code: str, value: float | None,
                    direction_override: str | None = None) -> EventInsight | None:
    """값 + 임계값 → severity. 임계 없거나 정상이면 None."""
    if value is None:
        return None
    bench = await _load_benchmark(db, metric_code, farm)
    if bench is None:
        return None
    direction = direction_override or bench["direction"]
    sev = _severity_from_bench(value, bench, direction)
    if sev is None or sev == Severity.OK:
        return None
    threshold = bench["critical"] if sev == Severity.CRITICAL else bench["warning"]
    # normalized_gap = 임계 대비 초과 정도(클수록 심각). 메인 선정 정렬용(백엔드 계산).
    gap = None
    if threshold not in (None, 0):
        gap = round((value - threshold) / threshold if direction == "above"
                    else (threshold - value) / threshold, 4)
    # 상대판정 슬롯(#3): 전국 상위25% 벤치마크 있을 때만 보조 표시. gap_worse>0 = top25보다 나쁨.
    relative = None
    if bench["top25"] is not None:
        top25 = bench["top25"]
        gap_worse = round((value - top25) if direction == "above" else (top25 - value), 2)
        relative = {
            "top25": top25,
            "gap": gap_worse,           # +면 상위25%보다 나쁨, -면 나음
            "better": gap_worse <= 0,
            "unit": bench["unit"],
            "demo": bool(bench["is_proxy"]) or bench["confidence"] == "low",
        }
    return EventInsight(
        metric_code=metric_code, severity=sev.value, judgment_type="absolute",
        normalized_gap=gap, priority=_METRIC_PRIORITY.get(metric_code, 50),
        value=round(value, 2), threshold=threshold, unit=bench["unit"], direction=direction,
        confidence=bench["confidence"], is_proxy=bench["is_proxy"], source=bench["source"],
        is_global_fallback=bench["is_global_fallback"], relative=relative,
    )


# ── 이벤트별 분석 ────────────────────────────────────────────────────────────
async def analyze_farrowing(db: AsyncSession, farm: Farm, f: Farrowing) -> list[EventInsight]:
    out: list[EventInsight] = []
    tb = (f.total_born or 0)
    dead = (f.stillborn or 0) + (f.mummified or 0)
    price = await _load_price(db, farm)
    if tb > 0:
        sr = await _evaluate(db, farm, "STILLBORN_RATE", (dead / tb) * 100)
        if sr and price and dead > 0:
            sr.loss = _loss(dead, price)   # 사산+미라 = 잃은 돼지
        out.append(sr)
    out.append(await _evaluate(db, farm, "BORN_ALIVE", float(f.born_alive) if f.born_alive is not None else None))
    return [i for i in out if i]


async def analyze_weaning(db: AsyncSession, farm: Farm, w: Weaning) -> list[EventInsight]:
    out: list[EventInsight] = []
    out.append(await _evaluate(db, farm, "WEANED_COUNT",
                               float(w.weaned_count) if w.weaned_count is not None else None))
    # 포유폐사율 = (생존산자 - 이유두수)/생존산자 — 연결된 분만의 born_alive 필요
    born_alive = None
    if w.farrowing_id:
        born_alive = await db.scalar(select(Farrowing.born_alive).where(Farrowing.id == w.farrowing_id))
    if born_alive and born_alive > 0 and w.weaned_count is not None:
        dead = born_alive - w.weaned_count
        pwm = (dead / born_alive) * 100
        pwm_ins = await _evaluate(db, farm, "PRE_WEANING_MORTALITY", pwm)
        if pwm_ins and dead > 0:
            price = await _load_price(db, farm)
            if price:
                pwm_ins.loss = _loss(dead, price)   # 포유 중 폐사 = 잃은 돼지
        out.append(pwm_ins)
    # 이유일령 밴드: LOW(below) / HIGH(above) 동일 값
    if w.weaning_age_days is not None:
        age = float(w.weaning_age_days)
        out.append(await _evaluate(db, farm, "WEANING_AGE_LOW", age, direction_override="below"))
        out.append(await _evaluate(db, farm, "WEANING_AGE_HIGH", age, direction_override="above"))
    return [i for i in out if i]


async def analyze_mating(db: AsyncSession, farm: Farm, m: Mating) -> list[EventInsight]:
    out: list[EventInsight] = []
    # WSI = 직전 이유일 ~ 이번 교배일 간격 (재교배 시점)
    last_wean = await db.scalar(
        select(Weaning.weaning_date)
        .where(Weaning.sow_id == m.sow_id, Weaning.deleted_at.is_(None),
               Weaning.weaning_date <= m.mating_date)
        .order_by(Weaning.weaning_date.desc()).limit(1)
    )
    if last_wean is not None:
        wsi = (m.mating_date - last_wean).days
        if wsi >= 0:
            out.append(await _evaluate(db, farm, "WSI", float(wsi)))
    return [i for i in out if i]


async def analyze_event(db: AsyncSession, farm: Farm, event_type: str, event) -> list[EventInsight]:
    """이벤트 타입별 분석 진입점. 호출부에서 try/except로 격리."""
    if event_type == "farrowing":
        return await analyze_farrowing(db, farm, event)
    if event_type == "weaning":
        return await analyze_weaning(db, farm, event)
    if event_type == "mating":
        return await analyze_mating(db, farm, event)
    return []


async def persist_insights(db: AsyncSession, farm: Farm, sow_id: UUID | None,
                           insights: list[EventInsight]) -> None:
    """WARNING↑ insight를 농장 OWNER/MANAGER에게 IN_APP 알림으로 적재.
    멱등: 같은 (user, INSIGHT_{metric}, sow)의 미읽음 알림 있으면 skip."""
    from app.db.models.ops import Notification
    from app.services import notification_service

    serious = [i for i in insights if i.severity in ("WARNING", "CRITICAL")]
    if not serious:
        return
    recipients = await notification_service.farm_recipients(db, farm.id)
    if not recipients:
        return

    alert_types = [f"INSIGHT_{i.metric_code}" for i in serious]
    existing_rows = await db.execute(
        select(Notification.user_id, Notification.alert_type, Notification.related_entity_id)
        .where(Notification.user_id.in_(recipients),
               Notification.alert_type.in_(alert_types),
               Notification.related_entity_id == sow_id,
               Notification.read_at.is_(None))
    )
    existing = {(r[0], r[1], r[2]) for r in existing_rows.all()}

    created = 0
    for uid in recipients:
        for i in serious:
            atype = f"INSIGHT_{i.metric_code}"
            key = (uid, atype, sow_id)
            if key in existing:
                continue
            db.add(Notification(
                farm_id=farm.id, user_id=uid, type="IN_APP",
                title=f"{i.metric_code} {i.severity}",
                body=f"{i.metric_code} {i.severity}: {i.value}{i.unit} (기준 {i.threshold}{i.unit})",
                alert_type=atype, severity=i.severity,
                related_entity_type="sow", related_entity_id=sow_id,
            ))
            existing.add(key)
            created += 1
    if created:
        await db.commit()
