from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# ★ Supavisor 트랜잭션 모드(포트 6543) 대응.
# 세션 모드(5432)는 클라이언트 1명이 서버 커넥션 1개를 독점해 동시 15명이 천장이고,
# 재기동으로 남은 유령 세션이 슬롯을 계속 먹는다(2026-08-24 반복 장애).
# 트랜잭션 모드는 쿼리 단위로 돌려써 동시 200까지 간다.
#
# 단, 트랜잭션 모드에서는 서버 커넥션이 매 트랜잭션마다 바뀌므로 prepared statement 를
# 재사용할 수 없다 → asyncpg 의 statement 캐시를 꺼야 한다. 켜두면
# "prepared statement does not exist" 가 산발적으로 터진다.
_TRANSACTION_MODE = ":6543" in settings.database_url
_URL = settings.database_url
_CONNECT_ARGS: dict = {}
if _TRANSACTION_MODE:
    _CONNECT_ARGS["statement_cache_size"] = 0
    if "prepared_statement_cache_size" not in _URL:
        _URL += ("&" if "?" in _URL else "?") + "prepared_statement_cache_size=0"

engine = create_async_engine(
    _URL,
    connect_args=_CONNECT_ARGS,
    # 풀 크기는 settings 경유(env 로 컨테이너별 조정). 근거·예산은 config.py 주석 참조.
    # 실측(2026-08-20): Supavisor 세션 모드 한도 = pool_size:15 동시 클라이언트.
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    echo=not settings.is_production,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
