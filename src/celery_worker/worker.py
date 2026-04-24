import os
from celery import Celery

import celery_worker.tasks # noqa

celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379")
