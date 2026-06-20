"""Pydantic schemas for candidates, applications, pipeline, and the L1 form."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import ApplicationStatus, CandidateSource, Stage


class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    location: str | None = None
    is_fresher: bool = False
    total_experience_years: float | None = None
    relevant_experience_years: float | None = None
    current_company: str | None = None
    current_ctc: int | None = None
    expected_ctc: int | None = None
    notice_period_days: int | None = None
    source: CandidateSource = CandidateSource.OTHER
    referred_by: str | None = None
    resume_url: str | None = None


class CandidateCreate(CandidateBase):
    # Optionally attach to a requisition on creation (creates an application).
    requisition_id: int | None = None


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    is_fresher: bool | None = None
    total_experience_years: float | None = None
    relevant_experience_years: float | None = None
    current_company: str | None = None
    current_ctc: int | None = None
    expected_ctc: int | None = None
    notice_period_days: int | None = None
    source: CandidateSource | None = None
    referred_by: str | None = None
    resume_url: str | None = None


class CandidateRead(CandidateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_by_id: int
    created_at: datetime


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    requisition_id: int
    stage: Stage
    status: ApplicationStatus
    stage_entered_at: datetime
    rejection_stage: Stage | None
    rejection_reason: str | None


class ApplicationCreate(BaseModel):
    requisition_id: int


class StageMoveRequest(BaseModel):
    stage: Stage


class RejectRequest(BaseModel):
    reason: str | None = None


# Pipeline board: one entry per application, enriched with the candidate name.
class PipelineCard(BaseModel):
    application_id: int
    candidate_id: int
    candidate_name: str
    stage: Stage
    status: ApplicationStatus


class MagicLinkResponse(BaseModel):
    url: str
    expires_at: datetime


# --- Candidate-facing L1 form (token auth, no account) ---
class L1Context(BaseModel):
    candidate_name: str
    requisition_title: str
    already_submitted: bool
    payload: dict[str, Any] | None = None


class L1Submit(BaseModel):
    payload: dict[str, Any]
