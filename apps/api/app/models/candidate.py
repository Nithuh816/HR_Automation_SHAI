"""Candidate, application, L1 form, and magic-link models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import (
    ApplicationStatus,
    CandidateSource,
    MagicLinkScope,
    Stage,
)
from app.models.mixins import TimestampMixin


class Candidate(TimestampMixin, Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)

    is_fresher: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_experience_years: Mapped[float | None] = mapped_column(nullable=True)
    relevant_experience_years: Mapped[float | None] = mapped_column(nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_ctc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_ctc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source: Mapped[CandidateSource] = mapped_column(
        SAEnum(CandidateSource, name="candidate_source_enum"),
        nullable=False,
        default=CandidateSource.OTHER,
    )
    referred_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    resume_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    # Set once DPDPA retention has anonymised this candidate's PII (M11).
    redacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CandidateApplication(TimestampMixin, Base):
    __tablename__ = "candidate_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), nullable=False, index=True
    )
    requisition_id: Mapped[int] = mapped_column(
        ForeignKey("requisitions.id"), nullable=False, index=True
    )
    stage: Mapped[Stage] = mapped_column(
        SAEnum(Stage, name="stage_enum"), nullable=False, default=Stage.SOURCED
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum"),
        nullable=False,
        default=ApplicationStatus.ACTIVE,
    )
    stage_entered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rejection_stage: Mapped[Stage | None] = mapped_column(
        SAEnum(Stage, name="stage_enum", create_type=False), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ApplicationFormL1(TimestampMixin, Base):
    __tablename__ = "application_form_l1"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, unique=True
    )
    # Free-form JSON payload mirroring the paper Word form (stored as text).
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MagicLink(TimestampMixin, Base):
    __tablename__ = "magic_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    scope: Mapped[MagicLinkScope] = mapped_column(
        SAEnum(MagicLinkScope, name="magic_link_scope_enum"), nullable=False
    )
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
