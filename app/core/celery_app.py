from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("gogogo", broker=redis_url, backend=redis_url)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.services.tasks.*": {"queue": "gogogo_queue"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.services"])
