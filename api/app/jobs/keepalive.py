"""
DB keep-alive job — Supabase 무료 티어 auto-pause 방지.

Supabase 무료 프로젝트는 7일간 DB 활동이 없으면 자동 일시정지(pause)된다.
운영 서버는 항상 떠 있어야 하므로, 매일 가벼운 `SELECT 1`로 활동을 발생시켜 정지를 막는다.
(KPI 집계 cron이 이미 DB를 치지만, 농장 데이터가 없으면 일부 쿼리가 비어 무활동으로 분류될 수 있어
 명시적 keep-alive를 별도로 둔다. 비용 무시 가능, 부작용 없음.)

유료(Pro/RDS) 전환 후에도 무해하므로 그대로 둬도 된다.
"""
from __future__ import annotations

import logging

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

log = logging.getLogger(__name__)


async def db_keepalive(ctx: dict) -> str:
    """매일 1회 DB에 가벼운 쿼리를 보내 Supabase 무료 티어 auto-pause를 방지."""
    async with AsyncSessionLocal() as db:
        result = await db.scalar(text("SELECT 1"))
    log.info("[keepalive] db ping ok (SELECT 1 -> %s)", result)
    return "ok"
