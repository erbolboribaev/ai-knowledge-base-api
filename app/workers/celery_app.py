from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ai_knowledge_base",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],  # Qaysi modulda vazifalar (tasks) borligini ko'rsatadi
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
)
