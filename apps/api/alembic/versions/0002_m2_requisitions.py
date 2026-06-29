"""M2 requisitions: requisitions and comments

Revision ID: 0002_m2_requisitions
Revises: 0001_m1_identity
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_m2_requisitions"
down_revision: str | None = "0001_m1_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

URGENCY_ENUM = sa.Enum("LOW", "NORMAL", "HIGH", "URGENT", name="urgency_enum")
STATUS_ENUM = sa.Enum(
    "DRAFT",
    "SUBMITTED",
    "ASSIGNED",
    "ON_HOLD",
    "FILLED",
    "CANCELLED",
    name="requisition_status_enum",
)


def upgrade() -> None:
    op.create_table(
        "requisitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("jd_md", sa.Text(), nullable=True),
        sa.Column("headcount", sa.Integer(), nullable=False),
        sa.Column("min_experience_years", sa.Integer(), nullable=True),
        sa.Column("max_experience_years", sa.Integer(), nullable=True),
        sa.Column("min_budget", sa.Integer(), nullable=True),
        sa.Column("max_budget", sa.Integer(), nullable=True),
        sa.Column("urgency", URGENCY_ENUM, nullable=False),
        sa.Column("status", STATUS_ENUM, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("assigned_recruiter_id", sa.Integer(), nullable=True),
        sa.Column("due_by", sa.Date(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_req_department"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_req_created_by"),
        sa.ForeignKeyConstraint(["assigned_recruiter_id"], ["users.id"], name="fk_req_recruiter"),
        sa.UniqueConstraint("code", name="uq_requisitions_code"),
    )
    op.create_index("ix_requisitions_code", "requisitions", ["code"])

    op.create_table(
        "requisition_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("requisition_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["requisition_id"], ["requisitions.id"], name="fk_reqcomment_req"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name="fk_reqcomment_author"),
    )
    op.create_index(
        "ix_requisition_comments_requisition_id",
        "requisition_comments",
        ["requisition_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_requisition_comments_requisition_id", table_name="requisition_comments")
    op.drop_table("requisition_comments")
    op.drop_index("ix_requisitions_code", table_name="requisitions")
    op.drop_table("requisitions")
    STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    URGENCY_ENUM.drop(op.get_bind(), checkfirst=True)
