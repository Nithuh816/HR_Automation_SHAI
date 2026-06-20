"""M1 identity: users and departments

Revision ID: 0001_m1_identity
Revises:
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_m1_identity"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Enum labels are the Python member NAMES (SQLAlchemy's default storage form).
ROLE_ENUM = sa.Enum(
    "HR_HEAD", "TA_TL", "TA_RECRUITER", "DEPT_LEAD", "DEPT_HEAD", "PR", name="role_enum"
)
TEAM_ENUM = sa.Enum("TA", "PR", "MGMT", "DEPT", name="team_enum")


def upgrade() -> None:
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("head_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_departments_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ms_oid", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("role", ROLE_ENUM, nullable=False),
        sa.Column("team", TEAM_ENUM, nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("manager_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_users_department"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name="fk_users_manager"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("ms_oid", name="uq_users_ms_oid"),
    )
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("departments")
    TEAM_ENUM.drop(op.get_bind(), checkfirst=True)
    ROLE_ENUM.drop(op.get_bind(), checkfirst=True)
