"""DB 커넥션 풀 예산 가드.

── 배경 (제약이 두 번 바뀌었다) ─────────────────────────────────────────────
2026-08-20  마이그레이션 반복 실패의 원인은 Supabase Supavisor 세션 모드 한도였다.
            실측 `EMAXCONNSESSION: max clients are limited to pool_size: 15`.
            앱 혼자 최대 30 을 요구해 마이그레이션·백업이 들어갈 자리가 없었다.
2026-08-25  그 풀러가 결국 쿼리 도중 연결을 끊는 상태(ConnectionDoesNotExistError)
            까지 가서 **같은 EC2 의 로컬 PostgreSQL 17** 로 이전했다.
            → 풀러가 경로에서 사라졌고 한도는 PG 의 max_connections(실측 200)다.

★ 그래서 이 파일이 지키는 것이 바뀌었다.
    이전  "풀러 15 슬롯을 넘지 마라"      (외부 서비스의 하드 한도)
    이후  "PG 한도 안에서, 운영 몫을 남기고, 메모리를 넘겨쓰지 마라"

한도가 13배 늘었다고 예산을 없애면 안 된다. 로컬 PG 는 커넥션마다 백엔드 프로세스와
work_mem 을 잡으므로, 한도를 다 쓰면 풀러 때와 다른 방식으로(메모리 압박) 무너진다.
"""
from app.core.config import Settings

# ── 실측값 (2026-08-25, 프로덕션 EC2) ───────────────────────────────────────
PG_MAX_CONNECTIONS = 200   # show max_connections
PG_WORK_MEM_MB = 32        # show work_mem
SERVER_RAM_GB = 15         # free -g / total. ※ 이 EC2 는 PG16(타 프로젝트)과 공유한다
PG_SHARED_BUFFERS_GB = 4   # show shared_buffers

# 앱이 쓰지 않고 남겨야 하는 몫 — 마이그레이션·백업(pg_dump)·psql·모니터링.
# 이 여유가 없으면 운영 작업을 할 때마다 서비스와 충돌한다.
RESERVED_FOR_OPS = 20

# 프로덕션 .env 가 주입하는 값(2026-08-25 이전 시 상향).
# compose 는 이보다 낮은 기본값을 두어 env 가 없을 때 안전한 쪽으로 뜨게 한다.
API_BUDGET = (20, 10)    # pool_size, max_overflow → 최대 30
WORKER_BUDGET = (5, 5)   # → 최대 10


def _max_conns(pool_size: int, max_overflow: int) -> int:
    return pool_size + max_overflow


APP_TOTAL = _max_conns(*API_BUDGET) + _max_conns(*WORKER_BUDGET)


def test_total_budget_leaves_room_for_ops():
    """★ api + worker 합이 PG 한도에서 운영 몫을 뺀 값을 넘지 않는다."""
    allowed = PG_MAX_CONNECTIONS - RESERVED_FOR_OPS
    assert APP_TOTAL <= allowed, (
        f"앱 최대 커넥션 {APP_TOTAL} > 허용 {allowed} "
        f"(PG max_connections {PG_MAX_CONNECTIONS} - 운영 몫 {RESERVED_FOR_OPS}). "
        "풀 크기를 줄이거나, PG max_connections 를 올린 뒤 이 상수를 갱신하십시오."
    )


def test_app_pools_fit_in_memory():
    """★ 커넥션 수 × work_mem 이 남은 메모리를 넘지 않는다.

    로컬 PG 로 옮기면서 새로 생긴 제약이다. 풀러를 쓸 때는 커넥션이 늘어도 DB 서버
    메모리와 무관했지만, 이제는 커넥션 하나가 백엔드 프로세스 하나이고 정렬·해시마다
    work_mem 을 잡는다. shared_buffers 를 뺀 나머지 안에 들어와야 한다.

    ※ 이 EC2 에는 PG16(타 프로젝트)과 다른 서비스도 함께 산다 — 절반만 우리 몫으로 본다.
    """
    budget_mb = (SERVER_RAM_GB - PG_SHARED_BUFFERS_GB) * 1024 * 0.5
    worst_case_mb = APP_TOTAL * PG_WORK_MEM_MB
    assert worst_case_mb <= budget_mb, (
        f"최악 {worst_case_mb}MB > 예산 {budget_mb:.0f}MB "
        f"(커넥션 {APP_TOTAL} × work_mem {PG_WORK_MEM_MB}MB). "
        "풀을 줄이거나 work_mem 을 낮추십시오."
    )


def test_code_defaults_are_conservative():
    """env 주입이 없어도 안전한 쪽으로 뜬다 — 기본값이 운영 예산을 넘지 않는다.

    (같아야 한다고 고정하지 않는다: 운영 예산은 .env 로 올리는 값이고, 코드 기본값은
     로컬 개발·테스트에서도 뜨는 값이라 더 작아야 한다.)"""
    s = Settings(_env_file=None)
    assert _max_conns(s.db_pool_size, s.db_max_overflow) <= _max_conns(*API_BUDGET)


def test_worker_budget_is_smaller_than_api():
    """워커는 배치성 — 커넥션을 사용자 트래픽에 양보해야 한다."""
    assert _max_conns(*WORKER_BUDGET) < _max_conns(*API_BUDGET)


def test_pool_timeout_fails_fast():
    """슬롯을 못 잡으면 매달리지 말고 빠르게 실패해야 한다.

    SQLAlchemy 기본 pool_timeout 은 30초라 요청이 줄줄이 밀린다."""
    s = Settings(_env_file=None)
    assert 0 < s.db_pool_timeout <= 15


def test_pool_recycle_set():
    """묵은 커넥션을 무한정 재사용하지 않도록 recycle 이 있어야 한다."""
    s = Settings(_env_file=None)
    assert 0 < s.db_pool_recycle <= 3600


def test_env_can_raise_budget_without_code_change(monkeypatch):
    """예산 상향이 코드 수정 없이 env 로 가능해야 한다.

    compose 가 DB_POOL_SIZE / DB_MAX_OVERFLOW 를 컨테이너별로 주입한다."""
    monkeypatch.setenv("DB_POOL_SIZE", "20")
    monkeypatch.setenv("DB_MAX_OVERFLOW", "10")
    s = Settings(_env_file=None)
    assert (s.db_pool_size, s.db_max_overflow) == (20, 10)
