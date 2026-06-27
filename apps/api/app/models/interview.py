"""Interview scheduling, rubric templates, and scorecards (rounds L3-L6)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import (
    InterviewMode,
    InterviewRound,
    InterviewStatus,
    ScorecardDecision,
)
from app.models.mixins import TimestampMixin


class RubricTemplate(TimestampMixin, Base):
    """A reusable set of scoring criteria for a given interview round."""

    __tablename__ = "rubric_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    round: Mapped[InterviewRound] = mapped_column(
        SAEnum(InterviewRound, name="interview_round_enum"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class RubricCriterion(TimestampMixin, Base):
    __tablename__ = "rubric_criteria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rubric_template_id: Mapped[int] = mapped_column(
        ForeignKey("rubric_templates.id"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Interview(TimestampMixin, Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=False, index=True
    )
    round: Mapped[InterviewRound] = mapped_column(
        SAEnum(InterviewRound, name="interview_round_enum", create_type=False), nullable=False
    )
    mode: Mapped[InterviewMode] = mapped_column(
        SAEnum(InterviewMode, name="interview_mode_enum"),
        nullable=False,
        default=InterviewMode.ONLINE,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    interviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    rubric_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("rubric_templates.id"), nullable=True
    )
    teams_join_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[InterviewStatus] = mapped_column(
        SAEnum(InterviewStatus, name="interview_status_enum"),
        nullable=False,
        default=InterviewStatus.SCHEDULED,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


class Scorecard(TimestampMixin, Base):
    __tablename__ = "scorecards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interview_id: Mapped[int] = mapped_column(
        ForeignKey("interviews.id"), nullable=False, unique=True
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[ScorecardDecision] = mapped_column(
        SAEnum(ScorecardDecision, name="scorecard_decision_enum"), nullable=False
    )
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ScorecardScore(TimestampMixin, Base):
    """One per-criterion rating; the label is snapshotted so later rubric edits
    don't rewrite history."""

    __tablename__ = "scorecard_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scorecard_id: Mapped[int] = mapped_column(
        ForeignKey("scorecards.id"), nullable=False, index=True
    )
    criterion_id: Mapped[int | None] = mapped_column(
        ForeignKey("rubric_criteria.id"), nullable=True
    )
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
