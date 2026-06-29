"""M11 consent & retention: consents table + candidate redaction marker

Revision ID: 0010_m11_consent_retention
Revises: 0009_m9_notifications
Create Date: 2026-06-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_m11_consent_retention"
down_revision: str | None = "0009_m9_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "candidates",
        sa.Column("redacted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "consents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], name="fk_consent_application"
        ),
    )
    op.create_index("ix_consents_application_id", "consents", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_consents_application_id", table_name="consents")
    op.drop_table("consents")
    op.drop_column("candidates", "redacted_at")
