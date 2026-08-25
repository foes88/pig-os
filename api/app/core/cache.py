"""농장 단위 응답 캐시 — 대시보드 지연 완화 (2026-08-24).

왜 필요한가: 대시보드는 요청마다 KPI 30여 개를 실시간 계산한다(build_herd_kpis).
쿼리 하나하나는 빠르지만(합 ~0.5초) 그동안 DB 커넥션을 붙들고 있고, 화면 하나가
API 를 7개 부르므로 사용자 한 명이 커넥션 7개를 0.5초씩 점유한다. Nano 등급의 좁은
파이프에서는 이것만으로 동시성이 무너진다(측정: 동시 10건 → 절반 504).

★ 이건 임시 완화다. 근본 해법은 CLAUDE.md 설계대로 kpi_snapshots 조회로 바꾸는 것.
  캐시는 그때까지 버티는 용도이며, 스냅샷 전환 후에도 얇게 남겨두면 도움이 된다.

안전 규칙:
- 키에 farm_id 를 반드시 포함한다. 테넌트 간 유출은 절대 안 된다.
- 권한 검사를 통과한 뒤(FarmDep 해석 후)에만 캐시를 조회/저장한다.
- Redis 가 죽어도 기능은 살아야 한다 — 모든 실패는 캐시 미스로 취급한다.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

log = logging.getLogger(__name__)

_client: aioredis.Redis | None = None
_disabled = False


def _get() -> aioredis.Redis | None:
    """지연 초기화. 연결 실패가 요청을 깨뜨리지 않게 None 을 돌려준다."""
    global _client, _disabled
    if _disabled:
        return None
    if _client is None:
        try:
            _client = aioredis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=1,   # 캐시 때문에 요청이 느려지면 본말전도
                socket_timeout=1,
            )
        except Exception:
            log.warning("cache: redis 초기화 실패 — 캐시 없이 동작", exc_info=True)
            _disabled = True
            return None
    return _client


def farm_key(prefix: str, farm_id: Any, *parts: Any) -> str:
    """★ farm_id 를 반드시 포함하는 키. 다른 농장 데이터가 섞이면 안 된다."""
    tail = ":".join(str(p) for p in parts if p is not None)
    return f"pigos:{prefix}:{farm_id}" + (f":{tail}" if tail else "")


async def get_json(key: str) -> Any | None:
    """캐시 조회. 미스·장애·손상 데이터 모두 None(=미스)."""
    c = _get()
    if c is None:
        return None
    try:
        raw = await c.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        log.debug("cache get 실패: %s", key, exc_info=True)
        return None


async def set_json(key: str, value: Any, ttl: int) -> None:
    """캐시 저장. 실패해도 조용히 넘어간다 — 저장 실패가 응답을 막으면 안 된다."""
    c = _get()
    if c is None:
        return
    try:
        await c.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        log.debug("cache set 실패: %s", key, exc_info=True)


async def invalidate_farm(farm_id: Any) -> int:
    """해당 농장 캐시 전부 무효화. 이벤트 입력 직후 최신값을 보이게 한다."""
    c = _get()
    if c is None:
        return 0
    try:
        n = 0
        async for k in c.scan_iter(match=f"pigos:*:{farm_id}*", count=100):
            n += await c.delete(k)
        return n
    except Exception:
        log.debug("cache invalidate 실패: %s", farm_id, exc_info=True)
        return 0
