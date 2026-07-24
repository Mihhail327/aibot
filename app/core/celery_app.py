from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "aibot_worker",
    broker=settings.REDIS_CELERY_URL,
    backend=settings.REDIS_CELERY_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_time_limit=1800,
    task_soft_time_limit=1500,
    worker_prefetch_multiplier=1,
    result_expires=86400,
)

celery_app.autodiscover_tasks([
    "app.domains.sources",
    "app.domains.news",
    "app.domains.posts",
])

# Настройка периодических задач согласно ТЗ (каждые 30 минут)
celery_app.conf.beat_schedule = {
    "parse-all-channels-every-30-mins": {
        "task": "news.parse_channels",
        "schedule": crontab(minute="*/30"),
    },
}