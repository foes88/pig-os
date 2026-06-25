"""
ARQ Worker 설정.

실행:
  arq app.jobs.worker.WorkerSettings

또는 Docker에서:
  command: arq app.jobs.worker.WorkerSettings
"""
from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.jobs.keepalive import db_keepalive
from app.jobs.kpi import (
    daily_kpi_aggregation,
    monthly_kpi_aggregation,
    recalculate_farm_kpi,
    weekly_kpi_aggregation,
)
from app.jobs.notifications import generate_notifications_job
from app.jobs.tasks import generate_tasks_job


async def startup(ctx: dict) -> None:
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger(__name__).info("[ARQ] Worker started")


async def shutdown(ctx: dict) -> None:
    import logging
    logging.getLogger(__name__).info("[ARQ] Worker stopped")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

    functions = [
        daily_kpi_aggregation,
        weekly_kpi_aggregation,
        monthly_kpi_aggregation,
        recalculate_farm_kpi,
        generate_tasks_job,
        generate_notifications_job,
        db_keepalive,
    ]

    cron_jobs = [
        # 매일 12:00 UTC — DB keep-alive (Supabase 무료 auto-pause 방지)
        cron(db_keepalive, hour=12, minute=0),
        # 매일 00:05 UTC — 전날 일별 KPI 집계
        cron(daily_kpi_aggregation, hour=0, minute=5),
        # 매주 월요일 00:10 UTC — 지난 주 KPI
        cron(weekly_kpi_aggregation, weekday=0, hour=0, minute=10),
        # 매월 1일 00:15 UTC — 지난 달 KPI
        cron(monthly_kpi_aggregation, day=1, hour=0, minute=15),
        # 매일 05:30 UTC — alert 기반 Task 자동배정
        cron(generate_tasks_job, hour=5, minute=30),
        # 매일 06:00 UTC — alert→IN_APP 영구 알림 생성
        cron(generate_notifications_job, hour=6, minute=0),
    ]

    on_startup = startup
    on_shutdown = shutdown

    max_jobs = 10
    job_timeout = 300       # 5분 — KPI 집계 최대 허용 시간
    keep_result = 3600      # 1시간 — 잡 결과 Redis 보관
