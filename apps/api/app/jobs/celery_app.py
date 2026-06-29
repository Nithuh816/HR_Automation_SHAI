from celery import Celery

from app.config import settings

celery_app = Celery(
    "hr_automation",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    "deliver-outbox": {"task": "outbox.deliver", "schedule": 60.0},
    "expire-assessment-attempts": {"task": "assessment.expire_attempts", "schedule": 300.0},
    "interview-reminders": {"task": "reminders.interviews", "schedule": 900.0},
    "day-before-joining": {"task": "reminders.day_before_joining", "schedule": 3600.0},
    "requisition-sla": {"task": "sla.check_requisitions", "schedule": 3600.0},
    "retention-purge": {"task": "retention.purge_rejected", "schedule": 86400.0},
}


@celery_app.task(name="health.ping")
def ping() -> str:
    return "pong"


# Import task modules so the worker/beat register them (after celery_app exists).
from app.jobs import tasks  # noqa: E402, F401
