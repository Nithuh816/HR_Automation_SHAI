"""Schemas for interviews, rubric templates, and scorecards."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    InterviewMode,
    InterviewRound,
    InterviewStatus,
    ScorecardDecision,
)


# --- Rubric templates (admin) ---
class RubricCreate(BaseModel):
    name: str
    round: InterviewRound
    description: str | None = None


class RubricUpdate(BaseModel):
    name: str | None = None
    round: InterviewRound | None = None
    description: str | None = None
    is_active: bool | None = None


class RubricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    round: InterviewRound
    description: str | None
    is_active: bool


class CriterionCreate(BaseModel):
    label: str
    weight: int = Field(default=1, ge=1)
    max_score: int = Field(default=5, ge=1)
    position: int = 0


class CriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    weight: int
    max_score: int
    position: int


class RubricDetail(RubricRead):
    criteria: list[CriterionRead]


# --- Interview scheduling ---
class InterviewCreate(BaseModel):
    round: InterviewRound
    mode: InterviewMode = InterviewMode.ONLINE
    scheduled_at: datetime
    duration_minutes: int = Field(default=45, ge=5, le=480)
    interviewer_id: int
    rubric_template_id: int | None = None
    location: str | None = None
    notes: str | None = None


class InterviewReschedule(BaseModel):
    scheduled_at: datetime
    mode: InterviewMode | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=480)


class InterviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    round: InterviewRound
    mode: InterviewMode
    scheduled_at: datetime
    duration_minutes: int
    interviewer_id: int
    rubric_template_id: int | None
    teams_join_url: str | None
    location: str | None
    status: InterviewStatus
    notes: str | None


# Enriched view for list/detail screens.
class InterviewDetail(InterviewRead):
    candidate_id: int
    candidate_name: str
    requisition_id: int
    requisition_title: str
    interviewer_name: str
    scorecard: ScorecardRead | None = None


# --- Scorecards ---
class ScorecardScoreInput(BaseModel):
    criterion_id: int | None = None
    label: str
    score: int = Field(ge=0)
    weight: int = Field(default=1, ge=1)
    comment: str | None = None


class ScorecardSubmit(BaseModel):
    decision: ScorecardDecision
    strengths: str | None = None
    concerns: str | None = None
    recommendation: str | None = None
    scores: list[ScorecardScoreInput] = Field(default_factory=list)


class ScorecardScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    criterion_id: int | None
    label: str
    score: int
    weight: int
    comment: str | None


class ScorecardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interview_id: int
    overall_score: float | None
    decision: ScorecardDecision
    strengths: str | None
    concerns: str | None
    recommendation: str | None
    submitted_by_id: int
    submitted_at: datetime
    scores: list[ScorecardScoreRead] = Field(default_factory=list)


# Resolve the forward reference used in InterviewDetail.
InterviewDetail.model_rebuild()
