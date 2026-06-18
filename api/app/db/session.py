from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    # 무료티어 Supabase 풀러(NANO, max_connections ~60) 보호:
    # api+worker가 같은 엔진 설정을 공유하므로 보수적으로. 부하 늘면 상향.
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    echo=not settings.is_production,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
