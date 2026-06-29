"""Scheduled Celery tasks. All tasks are idempotent and open their own session.

Beat schedule lives in ``app.jobs.celery_app``. Dedupe via Notification.dedupe_key
keeps reminders from firing twice.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.jobs.celery_app import celery_app
from app.models.assessment import AssessmentAttempt
from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import (
    AttemptStatus,
    InterviewStatus,
    NotificationChannel,
    OfferStatus,
    RequisitionStatus,
    Role,
)
from app.models.interview import Interview
from app.models.offer import Offer
from app.models.requisition import Requisition
from app.models.user import User
from app.services import notifications, retention


@celery_app.task(name="outbox.deliver")
def deliver_outbox() -> int:
    with SessionLocal() as db:
        return notifications.deliver_outbox(db)


@celery_app.task(name="assessment.expire_attempts")
def expire_assessment_attempts() -> int:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        rows = db.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.status == AttemptStatus.IN_PROGRESS)
            .where(AssessmentAttempt.expires_at.is_not(None))
            .where(AssessmentAttempt.expires_at < now)
        ).all()
        for attempt in rows:
            attempt.status = AttemptStatus.EXPIRED
        db.commit()
        return len(rows)


@celery_app.task(name="sla.check_requisitions")
def check_requisition_sla() -> int:
    today = datetime.now(UTC).date()
    with SessionLocal() as db:
        overdue = db.scalars(
            select(Requisition)
            .where(Requisition.due_by.is_not(None))
            .where(Requisition.due_by < today)
            .where(
                Requisition.status.in_([RequisitionStatus.SUBMITTED, RequisitionStatus.ASSIGNED])
            )
        ).all()
        heads = db.scalars(
            select(User).where(User.role == Role.HR_HEAD).where(User.is_active.is_(True))
        ).all()
        count = 0
        for req in overdue:
            for head in heads:
                made = notifications.in_app(
                    db,
                    kind="sla_breach",
                    recipient_user_id=head.id,
                    body=f"Requisition {req.code} ({req.title}) is past its due date.",
                    dedupe_key=f"sla:{req.id}:{today.isoformat()}:{head.id}",
                )
                count += 1 if made else 0
        db.commit()
        return count


@celery_app.task(name="reminders.interviews")
def interview_reminders() -> int:
    now = datetime.now(UTC)
    horizon = now + timedelta(hours=24)
    with SessionLocal() as db:
        rows = db.scalars(
            select(Interview)
            .where(Interview.status.in_([InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED]))
            .where(Interview.scheduled_at >= now)
            .where(Interview.scheduled_at <= horizon)
        ).all()
        count = 0
        for iv in rows:
            app = db.get(CandidateApplication, iv.application_id)
            cand = db.get(Candidate, app.candidate_id) if app else None
            if cand is None:
                continue
            made = notifications.enqueue(
                db,
                kind="interview_reminder",
                channel=NotificationChannel.EMAIL,
                to_address=cand.email,
                subject="Reminder: your upcoming interview",
                body=(
                    f"Dear {cand.name},\n\nThis is a reminder of your {iv.round.value.upper()} "
                    f"interview on {iv.scheduled_at:%Y-%m-%d %H:%M} UTC.\n\nSHAI Health"
                ),
                related_application_id=iv.application_id,
                dedupe_key=f"interview_reminder:{iv.id}:24h",
            )
            count += 1 if made else 0
        db.commit()
        return count


@celery_app.task(name="reminders.day_before_joining")
def day_before_joining() -> int:
    tomorrow = datetime.now(UTC).date() + timedelta(days=1)
    with SessionLocal() as db:
        rows = db.scalars(
            select(Offer)
            .where(Offer.status == OfferStatus.ACCEPTED)
            .where(Offer.joining_date == tomorrow)
        ).all()
        count = 0
        for offer in rows:
            app = db.get(CandidateApplication, offer.application_id)
            cand = db.get(Candidate, app.candidate_id) if app else None
            if cand is None:
                continue
            made = notifications.enqueue(
                db,
                kind="joining_reminder",
                channel=NotificationChannel.EMAIL,
                to_address=cand.email,
                subject="See you tomorrow at SHAI Health",
                body=(
                    f"Dear {cand.name},\n\nWe look forward to welcoming you tomorrow "
                    f"({offer.joining_date}) as {offer.designation}.\n\nSHAI Health"
                ),
                related_application_id=offer.application_id,
                dedupe_key=f"joining:{offer.id}",
            )
            count += 1 if made else 0
        db.commit()
        return count


@celery_app.task(name="retention.purge_rejected")
def purge_rejected_candidates() -> int:
    now = datetime.now(UTC)
    with SessionLocal() as db:
        return retention.purge_rejected(db, now=now, retention_days=settings.retention_days)
