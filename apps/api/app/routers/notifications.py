"""In-app notification feed + outbox inspection/flush (M9)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.enums import NotificationChannel, Role
from app.models.notification import Notification
from app.schemas.notification import (
    FlushResult,
    NotificationList,
    NotificationRead,
    OutboxItem,
)
from app.services import notifications as svc

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList)
def my_notifications(db: SessionDep, user: CurrentUser) -> NotificationList:
    rows = db.scalars(
        select(Notification)
        .where(Notification.recipient_user_id == user.id)
        .where(Notification.channel == NotificationChannel.IN_APP)
        .order_by(Notification.id.desc())
        .limit(100)
    ).all()
    unread = sum(1 for n in rows if n.read_at is None)
    return NotificationList(unread=unread, items=[NotificationRead.model_validate(n) for n in rows])


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(notification_id: int, db: SessionDep, user: CurrentUser) -> NotificationRead:
    n = db.get(Notification, notification_id)
    if n is None or n.recipient_user_id != user.id:
        raise HTTPException(status_code=404, detail="notification not found")
    if n.read_at is None:
        n.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(n)
    return NotificationRead.model_validate(n)


@router.post("/flush", response_model=FlushResult)
def flush_outbox(db: SessionDep, user: CurrentUser) -> FlushResult:
    """Deliver queued email/WhatsApp now (dev/admin convenience)."""
    if user.role != Role.HR_HEAD:
        raise HTTPException(status_code=403, detail="HR Head only")
    return FlushResult(delivered=svc.deliver_outbox(db))


@router.get("/outbox", response_model=list[OutboxItem])
def outbox(db: SessionDep, user: CurrentUser) -> list[OutboxItem]:
    if user.role != Role.HR_HEAD:
        raise HTTPException(status_code=403, detail="HR Head only")
    rows = db.scalars(select(Notification).order_by(Notification.id.desc()).limit(200)).all()
    return [OutboxItem.model_validate(n) for n in rows]
