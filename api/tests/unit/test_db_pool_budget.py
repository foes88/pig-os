"""DB 커넥션 풀 예산 가드.

2026-08-20 프로덕션 마이그레이션이 반복 실패한 실제 원인:
  Supabase Supavisor 세션 모드 한도 = 동시 클라이언트 15
  (실측: `EMAXCONNSESSION: max clients are limited to pool_size: 15`)
  그런데 앱은 api·worker 가 같은 엔진 설정을 공유하면서 각각 최대 15(5+10)를 요구했다.
  → 앱 혼자 최대 30. 마이그레이션·백업·모니터링이 들어갈 자리가 없었다.

이 테스트는 그 설정이 다시 풀러 한도를 넘지 못하게 막는다.
풀러 pool_size 를 대시보드에서 올렸다면 POOLER_MAX_CLIENTS 를 함께 올린다.
"""
from app.core.config import Settings

# 운영 풀러의 세션 모드 동시 클라이언트 한도(실측값). 대시보드에서 바꾸면 여기도 갱신.
POOLER_MAX_CLIENTS = 15

# 앱이 쓰지 않고 남겨야 하는 몫 — 마이그레이션·백업·psql·모니터링.
# 이 여유가 없으면 운영 작업을 할 때마다 서비스와 충돌한다.
RESERVED_FOR_OPS = 7

# compose 가 컨테이너별로 주입하는 값(docker-compose.prod.yml 과 일치해야 함)
API_BUDGET = (3, 2)      # pool_size, max_overflow → 최대 5
WORKER_BUDGET = (2, 1)   # → 최대 3


def _max_conns(pool_size: int, max_overflow: int) -> int:
    return pool_size + max_overflow


def test_default_settings_match_api_budget():
    """코드 기본값이 api 예산과 일치 — compose env 가 없어도 안전한 쪽으로 뜬다."""
    s = Settings(_env_file=None)
    assert (s.db_pool_size, s.db_max_overflow) == API_BUDGET


def test_total_budget_leaves_room_for_ops():
    """★ api + worker 합이 풀러 한도에서 운영 몫을 뺀 값을 넘지 않는다."""
    total = _max_conns(*API_BUDGET) + _max_conns(*WORKER_BUDGET)
    allowed = POOLER_MAX_CLIENTS - RESERVED_FOR_OPS
    assert total <= allowed, (
        f"앱 최대 커넥션 {total} > 허용 {allowed} "
        f"(풀러 한도 {POOLER_MAX_CLIENTS} - 운영 몫 {RESERVED_FOR_OPS}). "
        "풀 크기를 줄이거나 풀러 pool_size 를 올린 뒤 POOLER_MAX_CLIENTS 를 갱신하십시오."
    )


def test_worker_budget_is_smaller_than_api():
    """워커는 배치성 — 풀러 슬롯을 사용자 트래픽에 양보해야 한다."""
    assert _max_conns(*WORKER_BUDGET) < _max_conns(*API_BUDGET)


def test_pool_timeout_fails_fast():
    """슬롯을 못 잡으면 매달리지 말고 빠르게 실패해야 한다.

    SQLAlchemy 기본 pool_timeout 은 30초라 요청이 줄줄이 밀린다."""
    s = Settings(_env_file=None)
    assert 0 < s.db_pool_timeout <= 15


def test_pool_recycle_set():
    """풀러가 끊어버린 묵은 커넥션을 재사용하지 않도록 recycle 이 있어야 한다."""
    s = Settings(_env_file=None)
    assert 0 < s.db_pool_recycle <= 3600


def test_env_can_raise_budget_without_code_change(monkeypatch):
    """대시보드에서 풀러를 키운 뒤 코드 수정 없이 env 로 상향 가능해야 한다.

    compose 가 DB_POOL_SIZE / DB_MAX_OVERFLOW 를 컨테이너별로 주입한다."""
    monkeypatch.setenv("DB_POOL_SIZE", "8")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "4")
    s = Settings(_env_file=None)
    assert (s.db_pool_size, s.db_max_overflow) == (8, 4)
