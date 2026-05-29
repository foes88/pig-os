"""
알림 발송 잡 — Rule Engine 알림 + 시스템 알림.
현재: 스켈레톤 (Phase 2에서 FCM/APNs/이메일 구현)
"""
from __future__ import annotations

import logging

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
