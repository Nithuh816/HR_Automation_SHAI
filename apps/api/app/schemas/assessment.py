"""Schemas for the assessment engine (admin + candidate-facing)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AttemptStatus


# --- Question bank (admin) ---
class QuestionBase(BaseModel):
    text: str
    options: list[str] = Field(min_length=2)
    correct_index: int = Field(ge=0)
    category: str | None = None
    points: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def _check_index(self) -> QuestionBase:
        if self.correct_index >= len(self.options):
            raise ValueError("correct_index out of range")
        return self


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    text: str | None = None
    options: list[str] | None = None
    correct_index: int | None = None
    category: str | None = None
    points: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    options: list[str]
    correct_index: int
    category: str | None
    points: int
    is_active: bool


# --- Templates (admin) ---
class TemplateCreate(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int = Field(default=30, ge=1)
    pass_pct: int = Field(default=60, ge=0, le=100)


class TemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    pass_pct: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    duration_minutes: int
    pass_pct: int
    is_active: bool


class TemplateDetail(TemplateRead):
    questions: list[QuestionRead]


class AddQuestionRequest(BaseModel):
    question_id: int
    position: int = 0


# --- Issuing + results ---
class IssueAssessmentRequest(BaseModel):
    template_id: int


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    template_id: int
    status: AttemptStatus
    started_at: datetime | None
    submitted_at: datetime | None
    expires_at: datetime | None
    score_pct: float | None
    passed: bool | None


# --- Candidate-facing (token) ---
class PublicQuestion(BaseModel):
    id: int
    text: str
    options: list[str]  # no correct_index exposed


class AssessmentContext(BaseModel):
    template_name: str
    candidate_name: str
    duration_minutes: int
    expires_at: datetime
    already_submitted: bool
    questions: list[PublicQuestion]


class SubmittedAnswer(BaseModel):
    question_id: int
    selected_index: int | None = None


class AssessmentSubmit(BaseModel):
    answers: list[SubmittedAnswer]


class AssessmentResult(BaseModel):
    score_pct: float
    passed: bool
