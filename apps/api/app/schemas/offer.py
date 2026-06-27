"""Schemas for offer templates, offers, and the candidate-facing offer page."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OfferStatus


# --- Offer templates (admin) ---
class OfferTemplateCreate(BaseModel):
    name: str
    subject: str
    body_md: str


class OfferTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    body_md: str | None = None
    is_active: bool | None = None


class OfferTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    subject: str
    body_md: str
    is_active: bool


# --- Offers ---
class SalaryComponent(BaseModel):
    label: str
    annual: int
    monthly: int


class OfferCreate(BaseModel):
    annual_ctc: int = Field(gt=0)
    joining_date: date
    designation: str | None = None  # defaults to the requisition title
    template_id: int | None = None
    notes: str | None = None


class OfferUpdate(BaseModel):
    annual_ctc: int | None = Field(default=None, gt=0)
    joining_date: date | None = None
    designation: str | None = None
    template_id: int | None = None
    notes: str | None = None


class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    template_id: int | None
    designation: str
    annual_ctc: int
    joining_date: date
    notes: str | None
    status: OfferStatus
    created_by_id: int
    approved_by_id: int | None
    approved_at: datetime | None
    sent_at: datetime | None
    responded_at: datetime | None
    decline_reason: str | None


class OfferDetail(OfferRead):
    candidate_id: int
    candidate_name: str
    requisition_id: int
    requisition_title: str
    components: list[SalaryComponent]


class OfferDeclineRequest(BaseModel):
    reason: str | None = None


class OfferSendResult(BaseModel):
    url: str
    expires_at: datetime
    offer: OfferDetail


# --- Candidate-facing (token) ---
class OfferPublicContext(BaseModel):
    candidate_name: str
    designation: str
    employer: str
    annual_ctc: int
    joining_date: date
    components: list[SalaryComponent]
    subject: str
    letter_html: str
    status: OfferStatus
    already_responded: bool


class OfferResponseResult(BaseModel):
    status: OfferStatus
