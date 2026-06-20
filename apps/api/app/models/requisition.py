"""Requisition models — a hiring request raised against a department."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import RequisitionStatus, Urgency
from app.models.mixins import TimestampMixin


class Requisition(TimestampMixin, Base):
    __tablename__ = "requisitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), nullable=False)
    jd_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    headcount: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    min_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)

    urgency: Mapped[Urgency] = mapped_column(
        SAEnum(Urgency, name="urgency_enum"), nullable=False, default=Urgency.NORMAL
    )
    status: Mapped[RequisitionStatus] = mapped_column(
        SAEnum(RequisitionStatus, name="requisition_status_enum"),
        nullable=False,
        default=RequisitionStatus.SUBMITTED,
    )

    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_by: Mapped[date | None] = mapped_column(Date, nullable=True)


class RequisitionComment(TimestampMixin, Base):
    __tablename__ = "requisition_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requisition_id: Mapped[int] = mapped_column(
        ForeignKey("requisitions.id"), nullable=False, index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
