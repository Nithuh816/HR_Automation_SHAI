"""M7 documents: checklists, uploaded documents, encrypted PII

Revision ID: 0007_m7_documents
Revises: 0006_m6_offers
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_m7_documents"
down_revision: str | None = "0006_m6_offers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# _create_events=False: these types are created explicitly in upgrade(); it stops
# op.create_table from re-emitting CREATE TYPE for a type used by >1 table
# (Postgres rejects the duplicate).
CHECKLIST_TYPE_ENUM = sa.Enum(
    "FRESHER", "EXPERIENCED", name="checklist_type_enum", _create_events=False
)
DOCUMENT_TYPE_ENUM = sa.Enum(
    "AADHAAR",
    "PAN",
    "RESUME",
    "MARKSHEET",
    "EXPERIENCE_LETTER",
    "RELIEVING_LETTER",
    "PAYSLIP",
    "PHOTO",
    "BANK_PROOF",
    "OTHER",
    name="document_type_enum",
    _create_events=False,
)
DOCUMENT_STATUS_ENUM = sa.Enum(
    "PENDING",
    "EXTRACTED",
    "NEEDS_REVIEW",
    "VERIFIED",
    "REJECTED",
    name="document_status_enum",
    _create_events=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    CHECKLIST_TYPE_ENUM.create(bind, checkfirst=True)
    DOCUMENT_TYPE_ENUM.create(bind, checkfirst=True)
    DOCUMENT_STATUS_ENUM.create(bind, checkfirst=True)

    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE magic_link_scope_enum ADD VALUE IF NOT EXISTS 'DOC_UPLOAD'")

    op.create_table(
        "document_checklists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("checklist_type", CHECKLIST_TYPE_ENUM, nullable=False),
        sa.Column("document_type", DOCUMENT_TYPE_ENUM, nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_document_checklists_checklist_type", "document_checklists", ["checklist_type"]
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=True),
        sa.Column("document_type", DOCUMENT_TYPE_ENUM, nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", DOCUMENT_STATUS_ENUM, nullable=False),
        sa.Column("extracted_json", sa.Text(), nullable=True),
        sa.Column("aadhaar_enc", sa.Text(), nullable=True),
        sa.Column("pan_enc", sa.Text(), nullable=True),
        sa.Column("bank_account_enc", sa.Text(), nullable=True),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name="fk_document_candidate"),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], name="fk_document_application"
        ),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], name="fk_document_uploaded_by"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], name="fk_document_reviewed_by"),
    )
    op.create_index("ix_documents_candidate_id", "documents", ["candidate_id"])
    op.create_index("ix_documents_application_id", "documents", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_application_id", table_name="documents")
    op.drop_index("ix_documents_candidate_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_document_checklists_checklist_type", table_name="document_checklists")
    op.drop_table("document_checklists")
    bind = op.get_bind()
    DOCUMENT_STATUS_ENUM.drop(bind, checkfirst=True)
    DOCUMENT_TYPE_ENUM.drop(bind, checkfirst=True)
    CHECKLIST_TYPE_ENUM.drop(bind, checkfirst=True)
    # The added magic_link_scope_enum value is intentionally not removed.
