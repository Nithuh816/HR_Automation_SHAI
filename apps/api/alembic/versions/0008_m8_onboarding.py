"""M8 onboarding: GreytHR handoff records

Revision ID: 0008_m8_onboarding
Revises: 0007_m7_documents
Create Date: 2026-06-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_m8_onboarding"
down_revision: str | None = "0007_m7_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Created explicitly in upgrade() and dropped in downgrade(); _create_events=False
# stops op.create_table from re-emitting CREATE TYPE (Postgres rejects the duplicate).
ONBOARDING_STATUS_ENUM = sa.Enum(
    "PENDING",
    "PUSHED",
    "FAILED",
    "JOINED",
    name="onboarding_status_enum",
    _create_events=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    ONBOARDING_STATUS_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "onboarding_handoffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("status", ONBOARDING_STATUS_ENUM, nullable=False),
        sa.Column("greythr_employee_id", sa.String(length=64), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("pushed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], name="fk_onboarding_application"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_onboarding_created_by"),
        sa.UniqueConstraint("application_id", name="uq_onboarding_application"),
    )
    op.create_index(
        "ix_onboarding_handoffs_application_id", "onboarding_handoffs", ["application_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_onboarding_handoffs_application_id", table_name="onboarding_handoffs")
    op.drop_table("onboarding_handoffs")
    ONBOARDING_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
