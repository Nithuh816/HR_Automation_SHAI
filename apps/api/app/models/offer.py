"""Offer letters: templates, the offer itself, and its approval lifecycle."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import OfferStatus
from app.models.mixins import TimestampMixin


class OfferTemplate(TimestampMixin, Base):
    """A Jinja2 letter body with placeholders like ``{{ candidate_name }}``."""

    __tablename__ = "offer_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class Offer(TimestampMixin, Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, index=True
    )
    template_id: Mapped[int | None] = mapped_column(ForeignKey("offer_templates.id"), nullable=True)
    designation: Mapped[str] = mapped_column(String(160), nullable=False)
    annual_ctc: Mapped[int] = mapped_column(Integer, nullable=False)
    # Computed salary breakdown (JSON list of {label, annual, monthly}).
    components_json: Mapped[str] = mapped_column(Text, nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[OfferStatus] = mapped_column(
        SAEnum(OfferStatus, name="offer_status_enum"),
        nullable=False,
        default=OfferStatus.DRAFT,
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decline_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
