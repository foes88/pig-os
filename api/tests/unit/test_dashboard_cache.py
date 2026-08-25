"""대시보드 응답 캐시 (2026-08-24 지연 완화).

대시보드는 요청마다 KPI 30여 개를 실시간 계산해 커넥션을 ~0.5초 붙든다. 화면 하나가
API 를 7개 부르므로 동시성에서 무너졌다(측정: 동시 10건 → 절반 504).

★ 캐시에서 가장 위험한 건 성능이 아니라 **테넌트 간 유출**이다. 농장 A 의 숫자가
  농장 B 에게 보이면 그건 사고다. 그 경계를 먼저 잠근다.
"""
import pytest

from app.core import cache

pytestmark = pytest.mark.anyio


def test_key_always_contains_farm_id():
    """★ 키에 farm_id 가 반드시 들어간다 — 농장이 다르면 키도 달라야 한다."""
    a = cache.farm_key("dashboard", "farm-a")
    b = cache.farm_key("dashboard", "farm-b")
    assert "farm-a" in a and "farm-b" in b
    assert a != b


def test_key_parts_do_not_collide():
    """부가 파트가 달라도 키가 겹치지 않는다."""
    assert cache.farm_key("dashboard", "f1", 2026) != cache.farm_key("dashboard", "f1", 2027)
    assert cache.farm_key("dashboard", "f1") != cache.farm_key("trend", "f1")


def test_key_prefix_is_namespaced():
    """다른 서비스와 Redis 를 공유해도 충돌하지 않게 네임스페이스를 둔다."""
    assert cache.farm_key("dashboard", "f1").startswith("pigos:")


async def test_get_returns_none_when_redis_unavailable(monkeypatch):
    """★ Redis 가 죽어도 기능은 살아야 한다 — 캐시 미스로 취급하고 계속 간다."""
    monkeypatch.setattr(cache, "_get", lambda: None)
    assert await cache.get_json("pigos:dashboard:f1") is None
    await cache.set_json("pigos:dashboard:f1", {"x": 1}, 30)   # 예외가 나면 안 된다
    assert await cache.invalidate_farm("f1") == 0


async def test_get_treats_corrupt_payload_as_miss(monkeypatch):
    """손상된 값이 들어 있어도 500 이 아니라 미스로 처리한다."""
    class _Broken:
        async def get(self, k):
            return "{not json"
    monkeypatch.setattr(cache, "_get", lambda: _Broken())
    assert await cache.get_json("pigos:dashboard:f1") is None


async def test_set_failure_does_not_raise(monkeypatch):
    """저장 실패가 응답을 막으면 안 된다."""
    class _Broken:
        async def set(self, *a, **kw):
            raise RuntimeError("redis down")
    monkeypatch.setattr(cache, "_get", lambda: _Broken())
    await cache.set_json("pigos:dashboard:f1", {"x": 1}, 30)   # 조용히 넘어가야 한다


async def test_roundtrip_with_fake_redis(monkeypatch):
    """정상 경로 — 저장한 값이 그대로 나온다."""
    store: dict[str, str] = {}

    class _Fake:
        async def get(self, k):
            return store.get(k)

        async def set(self, k, v, ex=None):
            store[k] = v

    monkeypatch.setattr(cache, "_get", lambda: _Fake())
    key = cache.farm_key("dashboard", "f1")
    await cache.set_json(key, {"psy": 29.0, "npd": None}, 30)
    assert await cache.get_json(key) == {"psy": 29.0, "npd": None}

    # ★ 다른 농장 키로는 절대 안 나온다
    assert await cache.get_json(cache.farm_key("dashboard", "f2")) is None
