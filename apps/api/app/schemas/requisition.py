"""Pydantic schemas for requisitions and comments."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RequisitionStatus, Urgency


class RequisitionCreate(BaseModel):
    title: str
    department_id: int
    jd_md: str | None = None
    headcount: int = Field(default=1, ge=1)
    min_experience_years: int | None = Field(default=None, ge=0)
    max_experience_years: int | None = Field(default=None, ge=0)
    min_budget: int | None = Field(default=None, ge=0)
    max_budget: int | None = Field(default=None, ge=0)
    urgency: Urgency = Urgency.NORMAL
    due_by: date | None = None


class RequisitionUpdate(BaseModel):
    title: str | None = None
    department_id: int | None = None
    jd_md: str | None = None
    headcount: int | None = Field(default=None, ge=1)
    min_experience_years: int | None = Field(default=None, ge=0)
    max_experience_years: int | None = Field(default=None, ge=0)
    min_budget: int | None = Field(default=None, ge=0)
    max_budget: int | None = Field(default=None, ge=0)
    urgency: Urgency | None = None
    due_by: date | None = None


class RequisitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    department_id: int
    jd_md: str | None
    headcount: int
    min_experience_years: int | None
    max_experience_years: int | None
    min_budget: int | None
    max_budget: int | None
    urgency: Urgency
    status: RequisitionStatus
    created_by_id: int
    assigned_recruiter_id: int | None
    due_by: date | None
    created_at: datetime


class AssignRequest(BaseModel):
    recruiter_id: int


class StatusChangeRequest(BaseModel):
    status: RequisitionStatus


class CommentCreate(BaseModel):
    body: str


class CommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    requisition_id: int
    author_id: int
    body: str
    created_at: datetime


class RequisitionSummary(BaseModel):
    total: int
    submitted: int  # in triage
    assigned: int
    on_hold: int
    filled: int
    cancelled: int
    open_headcount: int  # sum of headcount for submitted+assigned+on_hold
    by_urgency: dict[str, int]
