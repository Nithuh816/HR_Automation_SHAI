"""DPDPA consent records captured on candidate-facing pages (M11)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class Consent(TimestampMixin, Base):
    """One timestamped consent per (application, purpose). The exact text shown
    to the candidate is snapshotted so later policy edits don't rewrite history."""

    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, index=True
    )
    purpose: Mapped[str] = mapped_column(String(64), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    given_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
