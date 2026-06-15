"""
알림 발송 잡 — Rule Engine 알림 + 시스템 알림.
현재: 스켈레톤 (Phase 2에서 FCM/APNs/이메일 구현)
"""
from __future__ import annotations

import logging

from sqlalchemy import select

from app.db.models.platform import Farm
from app.db.session import AsyncSessionLocal
from app.services import notification_service

log = logging.getLogger(__name__)


async def send_push_notification(
    ctx: dict,
    user_id: str,
    title: str,
    body: str,
    alert_type: str = "SYSTEM",
    farm_id: str | None = None,
) -> str:
    """FCM/APNs 푸시 발송. Phase 2 구현 예정."""
    log.info("PUSH [stub] user=%s title=%s", user_id, title)
    # TODO Phase 2: FCM HTTP v1 API 연동
    return f"stub:push:{user_id}"


async def send_rule_alert(
    ctx: dict,
    farm_id: str,
    rule_id: str,
    severity: str,
    message: str,
) -> str:
    """
    Rule Engine CRITICAL/WARNING 알림 발송.
    대상: farm의 OWNER + MANAGER 역할 사용자.
    """
    log.info("RULE_ALERT [stub] farm=%s rule=%s severity=%s", farm_id, rule_id, severity)
    # TODO Phase 2:
    #   1. DB에서 farm_id + role IN (OWNER, MANAGER) 사용자 조회
    #   2. send_push_notification 잡 enqueue
    #   3. severity==CRITICAL → 이메일도 발송
    return f"stub:rule_alert:{farm_id}:{rule_id}"


async def generate_notifications_job(ctx: dict) -> str:
    """전 활성 농장 순회 — alert(과기한/도태/KPI) → IN_APP 영구 알림 멱등 생성 (P12-6).

    스케줄: 매일 06:00 UTC (worker.py cron_jobs).
    """
    async with AsyncSessionLocal() as db:
        farm_ids = list(await db.scalars(
            select(Farm.id).where(Farm.deleted_at.is_(None))
        ))

    processed = 0
    errors = 0
    total_created = 0
    for farm_id in farm_ids:
        try:
            async with AsyncSessionLocal() as db:
                total_created += await notification_service.create_from_alerts(db, farm_id)
            processed += 1
        except Exception as e:  # noqa: BLE001 — 한 농장 실패 격리
            log.error("generate_notifications farm=%s error=%s", farm_id, e)
            errors += 1

    result = f"notification generation done: {processed} farms, {total_created} created, {errors} errors"
    log.info(result)
    return result
