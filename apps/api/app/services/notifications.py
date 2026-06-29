"""Notification service: enqueue to the outbox and deliver it.

The request path only ever *enqueues* (a DB insert). Email/WhatsApp are delivered
out-of-band by the Celery ``outbox.deliver`` task (or the manual flush endpoint),
so a slow or down mail server never blocks an API request.
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.email import EmailError, EmailSender, get_email_sender
from app.integrations.whatsapp import WhatsAppError, WhatsAppSender, get_whatsapp_sender
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import Notification

log = structlog.get_logger()


def enqueue(
    db: Session,
    *,
    kind: str,
    channel: NotificationChannel,
    body: str,
    subject: str | None = None,
    recipient_user_id: int | None = None,
    to_address: str | None = None,
    related_application_id: int | None = None,
    dedupe_key: str | None = None,
) -> Notification | None:
    """Add a message to the outbox. Returns None if ``dedupe_key`` already exists."""
    if dedupe_key is not None and db.scalar(
        select(Notification).where(Notification.dedupe_key == dedupe_key)
    ):
        return None
    immediate = channel == NotificationChannel.IN_APP
    notification = Notification(
        kind=kind,
        channel=channel,
        body=body,
        subject=subject,
        recipient_user_id=recipient_user_id,
        to_address=to_address,
        related_application_id=related_application_id,
        dedupe_key=dedupe_key,
        status=NotificationStatus.SENT if immediate else NotificationStatus.QUEUED,
        sent_at=datetime.now(UTC) if immediate else None,
    )
    db.add(notification)
    db.flush()
    return notification


def in_app(
    db: Session,
    *,
    kind: str,
    recipient_user_id: int,
    body: str,
    related_application_id: int | None = None,
    dedupe_key: str | None = None,
) -> Notification | None:
    return enqueue(
        db,
        kind=kind,
        channel=NotificationChannel.IN_APP,
        body=body,
        recipient_user_id=recipient_user_id,
        related_application_id=related_application_id,
        dedupe_key=dedupe_key,
    )


def deliver_one(
    db: Session,
    notification: Notification,
    email_sender: EmailSender,
    whatsapp_sender: WhatsAppSender,
) -> bool:
    try:
        if notification.channel == NotificationChannel.EMAIL:
            email_sender.send(
                to=notification.to_address or "",
                subject=notification.subject or "",
                body=notification.body,
            )
        elif notification.channel == NotificationChannel.WHATSAPP:
            whatsapp_sender.send(to=notification.to_address or "", body=notification.body)
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.now(UTC)
        notification.error = None
        return True
    except (EmailError, WhatsAppError) as exc:
        notification.status = NotificationStatus.FAILED
        notification.retries += 1
        notification.error = str(exc)
        log.warning("notification.deliver_failed", id=notification.id, error=str(exc))
        return False


def deliver_outbox(
    db: Session,
    *,
    limit: int = 100,
    email_sender: EmailSender | None = None,
    whatsapp_sender: WhatsAppSender | None = None,
) -> int:
    """Deliver QUEUED email/WhatsApp messages. Returns the count delivered."""
    email_sender = email_sender or get_email_sender()
    whatsapp_sender = whatsapp_sender or get_whatsapp_sender()
    rows = db.scalars(
        select(Notification)
        .where(Notification.status == NotificationStatus.QUEUED)
        .where(Notification.channel != NotificationChannel.IN_APP)
        .order_by(Notification.id.asc())
        .limit(limit)
    ).all()
    delivered = sum(deliver_one(db, n, email_sender, whatsapp_sender) for n in rows)
    db.commit()
    return delivered


# --- event helpers (called from routers) ---

_SIGNOFF = "\n\nWarm regards,\nTalent Acquisition, SHAI Health"


def offer_sent_email(
    db: Session,
    *,
    application_id: int,
    candidate_name: str,
    candidate_email: str,
    designation: str,
    url: str,
) -> None:
    body = (
        f"Dear {candidate_name},\n\nWe are pleased to extend an offer for the position of "
        f"{designation}. Please review and respond to your offer here:\n{url}{_SIGNOFF}"
    )
    enqueue(
        db,
        kind="offer_sent",
        channel=NotificationChannel.EMAIL,
        to_address=candidate_email,
        subject="Your offer from SHAI Health",
        body=body,
        related_application_id=application_id,
    )


def interview_scheduled_email(
    db: Session,
    *,
    application_id: int,
    candidate_name: str,
    candidate_email: str,
    round_label: str,
    when: datetime,
    join_url: str | None = None,
) -> None:
    where = f"Join online: {join_url}" if join_url else "Venue details to follow."
    body = (
        f"Dear {candidate_name},\n\nYour {round_label} interview is scheduled for "
        f"{when:%Y-%m-%d %H:%M} UTC.\n{where}{_SIGNOFF}"
    )
    enqueue(
        db,
        kind="interview_scheduled",
        channel=NotificationChannel.EMAIL,
        to_address=candidate_email,
        subject=f"Interview scheduled — {round_label}",
        body=body,
        related_application_id=application_id,
    )
