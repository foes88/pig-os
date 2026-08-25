"""DB 커넥션 keepalive — 응답시간 스파이크 제거 (2026-08-25).

증상: 평소 0.42초인 로그인이 간헐적으로 2~20초로 튄다. 계측해 보면 쿼리는 빠르고
(대시보드 전 단계 합 ~0.5초) 튀는 구간은 **커넥션 재수립**이다.

원인: Supabase 풀러는 유휴 커넥션을 끊는다. 앱 풀에 남아 있던 핸들은 죽어 있고,
pool_pre_ping 이 그걸 감지해 새로 연결하는데 풀러 경유 신규 연결이 수 초 걸린다.
결과적으로 "한동안 안 쓰다가 열면 느림"이 된다.

대책: 주기적으로 풀의 커넥션을 가볍게 건드려 유휴로 판정되지 않게 한다.
pool_size 만큼 동시에 핑을 보내 특정 하나만 살아있는 상황을 피한다.

★ 이건 완화책이다. 근본은 DB 를 앱과 같은 호스트에 두거나(커넥션 비용 ~0)
  대시보드를 kpi_snapshots 조회로 바꿔 커넥션 점유를 줄이는 것이다.
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

log = logging.getLogger(__name__)

_task: asyncio.Task | None = None


async def _ping_once() -> None:
    """풀의 커넥션 여러 개를 동시에 건드린다.

    순차로 하면 같은 커넥션 하나만 계속 재사용돼 나머지가 유휴로 끊긴다."""
    n = max(1, settings.db_pool_size)

    async def one() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    await asyncio.gather(*(one() for _ in range(n)), return_exceptions=True)


async def _loop() -> None:
    interval = settings.db_keepalive_interval
    while True:
        try:
            await asyncio.sleep(interval)
            await _ping_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            # keepalive 실패가 서비스를 막으면 안 된다. 다음 주기에 다시 시도한다.
            log.debug("db keepalive 실패", exc_info=True)


def start() -> None:
    """앱 시작 시 호출. interval<=0 이면 비활성."""
    global _task
    if settings.db_keepalive_interval <= 0 or _task is not None:
        return
    _task = asyncio.create_task(_loop())
    log.info("db keepalive 시작 (%ss 주기)", settings.db_keepalive_interval)


async def stop() -> None:
    """앱 종료 시 호출."""
    global _task
    if _task is None:
        return
    _task.cancel()
    try:
        await _task
    except (asyncio.CancelledError, Exception):
        pass
    _task = None
