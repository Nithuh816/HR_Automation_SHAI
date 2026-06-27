"""Schemas for document checklists, documents, and the upload portal."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import ChecklistType, DocumentStatus, DocumentType


# --- Checklist admin ---
class ChecklistItemCreate(BaseModel):
    checklist_type: ChecklistType
    document_type: DocumentType
    label: str
    required: bool = True
    position: int = 0


class ChecklistItemUpdate(BaseModel):
    label: str | None = None
    required: bool | None = None
    position: int | None = None


class ChecklistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checklist_type: ChecklistType
    document_type: DocumentType
    label: str
    required: bool
    position: int


# --- Documents (internal) ---
class DocumentRead(BaseModel):
    """Document metadata — never carries the raw file or raw ID numbers."""

    id: int
    candidate_id: int
    application_id: int | None
    document_type: DocumentType
    original_filename: str
    content_type: str
    size_bytes: int
    status: DocumentStatus
    extracted: dict[str, Any] | None
    aadhaar_masked: str | None
    pan_masked: str | None
    review_note: str | None
    uploaded_by_id: int | None
    reviewed_by_id: int | None
    reviewed_at: datetime | None
    created_at: datetime


class DocumentReviewRequest(BaseModel):
    note: str | None = None


# --- Candidate upload portal (token) ---
class ChecklistItemPublic(BaseModel):
    document_type: DocumentType
    label: str
    required: bool


class UploadedDocPublic(BaseModel):
    id: int
    document_type: DocumentType
    original_filename: str
    status: DocumentStatus


class DocUploadContext(BaseModel):
    candidate_name: str
    checklist_type: ChecklistType
    consent_text: str
    items: list[ChecklistItemPublic]
    uploaded: list[UploadedDocPublic]
