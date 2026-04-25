import os
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab

import celery_worker.tasks # noqa

celery_app = Celery(__name__)
celery_app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379")
celery_app.conf.task_ignore_result = True

celery_app.conf.beat_schedule = {
    "delete_expired_activation_tokens": {
        "task": "celery_worker.tasks.delete_activation_token",
        "schedule": crontab(minute="*"),
    }
}
