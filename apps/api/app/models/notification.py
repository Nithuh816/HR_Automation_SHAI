"""Notification outbox: email / WhatsApp / in-app messages (M9)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.mixins import TimestampMixin


class Notification(TimestampMixin, Base):
    """A single message. Email/WhatsApp start QUEUED and are delivered by the
    outbox worker; in-app messages are created already SENT and read in place."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        SAEnum(NotificationChannel, name="notification_channel_enum"), nullable=False
    )
    recipient_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus, name="notification_status_enum"),
        nullable=False,
        default=NotificationStatus.QUEUED,
    )
    # Idempotency guard for scheduled jobs (e.g. "interview_reminder:7:24h").
    dedupe_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    related_application_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
