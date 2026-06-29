"""Schemas for in-app notifications and the outbox (M9)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationChannel, NotificationStatus


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    channel: NotificationChannel
    subject: str | None
    body: str
    status: NotificationStatus
    related_application_id: int | None
    read_at: datetime | None
    created_at: datetime


class NotificationList(BaseModel):
    unread: int
    items: list[NotificationRead]


class OutboxItem(NotificationRead):
    to_address: str | None
    recipient_user_id: int | None
    retries: int
    error: str | None
    sent_at: datetime | None


class FlushResult(BaseModel):
    delivered: int
