"""Onboarding handoff: pushing an accepted candidate into GreytHR."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import OnboardingStatus
from app.models.mixins import TimestampMixin


class OnboardingHandoff(TimestampMixin, Base):
    """One new-hire handoff per application; idempotent via the GreytHR id."""

    __tablename__ = "onboarding_handoffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, unique=True, index=True
    )
    status: Mapped[OnboardingStatus] = mapped_column(
        SAEnum(OnboardingStatus, name="onboarding_status_enum"),
        nullable=False,
        default=OnboardingStatus.PENDING,
    )
    greythr_employee_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Snapshot of the payload pushed to GreytHR (JSON, for audit/debug).
    payload_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
