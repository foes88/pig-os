import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.db.models  # noqa: F401 — registers all models for autogenerate
from alembic import context
from app.core.config import settings
from app.db.base import Base

config = context.config
# offline(sql 덤프): sync URL / online(실제 실행): async URL
config.set_main_option("sqlalchemy.url", settings.sync_database_url)
_async_url = settings.database_url  # postgresql+asyncpg://...

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ★ autogenerate 가 **비교할 수 없는** 인덱스들.
#   부분 인덱스(WHERE 절)와 표현식 인덱스는 alembic 이 DB 정의를 모델과 대조하지 못해
#   매번 "removed index" 로 오탐한다. 실제로는 모델·마이그레이션·DB 모두에 존재한다.
#   여기서 제외하지 않으면 `alembic check` 가 영구히 실패해 **진짜 드리프트를 가린다**
#   (독립검증 2026-08-25: 이 오탐들 때문에 진짜 드리프트 6건이 묻혀 있었다).
#
#   ⚠️ 이 목록에 추가할 때는 "정말 비교 불가능한가"를 확인한다. 단순히 시끄럽다고
#      넣으면 그 객체의 드리프트를 영영 못 잡는다.
_UNCOMPARABLE_INDEXES = {
    "uq_ckp_north_star",      # 부분 unique (WHERE display_role='NORTH_STAR')
    "uq_ckpres_scope_kpi",    # COALESCE 표현식 포함 unique
    "idx_pilot_signups_email",  # lower(email) 표현식 unique — 대소문자 무시 유일성
}


def _include_object(obj, name, type_, reflected, compare_to):  # noqa: ANN001, ANN202
    if type_ == "index" and name in _UNCOMPARABLE_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=_include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        {**config.get_section(config.config_ini_section, {}),
         "sqlalchemy.url": _async_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
