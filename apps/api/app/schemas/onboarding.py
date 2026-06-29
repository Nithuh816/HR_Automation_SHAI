"""Schemas for the GreytHR onboarding handoff (M8)."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import OfferStatus, OnboardingStatus


class OnboardingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    status: OnboardingStatus
    greythr_employee_id: str | None
    retries: int
    last_error: str | None
    pushed_at: datetime | None
    joined_at: datetime | None
    created_by_id: int


class OnboardingDetail(OnboardingRead):
    candidate_id: int
    candidate_name: str
    candidate_email: str
    requisition_id: int
    requisition_title: str
    designation: str
    annual_ctc: int
    joining_date: date
    documents_required: int
    documents_verified: int


class OnboardingQueueItem(BaseModel):
    """A candidate whose offer was accepted and who is ready for GreytHR."""

    application_id: int
    candidate_id: int
    candidate_name: str
    requisition_id: int
    requisition_title: str
    designation: str
    joining_date: date
    offer_status: OfferStatus
    handoff_id: int | None
    handoff_status: OnboardingStatus | None
    greythr_employee_id: str | None
    documents_required: int
    documents_verified: int
