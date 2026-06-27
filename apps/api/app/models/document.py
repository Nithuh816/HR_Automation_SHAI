"""Document checklists and uploaded candidate documents.

ID numbers extracted from documents (Aadhaar / PAN / bank account) are stored
Fernet-encrypted at the column level; the raw file lives in object storage and
is only ever served behind a short-lived, authenticated fetch.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import ChecklistType, DocumentStatus, DocumentType
from app.models.mixins import TimestampMixin


class DocumentChecklist(TimestampMixin, Base):
    """One required document for a checklist type (fresher vs experienced)."""

    __tablename__ = "document_checklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checklist_type: Mapped[ChecklistType] = mapped_column(
        SAEnum(ChecklistType, name="checklist_type_enum"), nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type_enum"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("candidates.id"), nullable=False, index=True
    )
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidate_applications.id"), nullable=True, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType, name="document_type_enum", create_type=False), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status_enum"),
        nullable=False,
        default=DocumentStatus.PENDING,
    )
    # Non-PII auto-extracted facts (JSON: e.g. {"name": "...", "text_found": true}).
    extracted_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Fernet-encrypted ID numbers (never returned raw in API responses).
    aadhaar_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    pan_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    bank_account_enc: Mapped[str | None] = mapped_column(Text, nullable=True)

    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
