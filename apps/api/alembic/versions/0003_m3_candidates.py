"""M3 candidates: candidates, applications, L1 form, magic links

Revision ID: 0003_m3_candidates
Revises: 0002_m2_requisitions
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_m3_candidates"
down_revision: str | None = "0002_m2_requisitions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCE_ENUM = sa.Enum(
    "LINKEDIN", "NAUKRI", "REFERRAL", "INSTITUTION", "COLD_CALL", "OTHER",
    name="candidate_source_enum",
)
STAGE_ENUM = sa.Enum(
    "SOURCED", "L1_APPLICATION", "L2_ASSESSMENT", "L3_HR", "L4_TECH1",
    "L5_TECH2", "L6_SALARY", "OFFER", "JOINED",
    name="stage_enum",
)
APP_STATUS_ENUM = sa.Enum(
    "ACTIVE", "REJECTED", "WITHDRAWN", name="application_status_enum"
)
SCOPE_ENUM = sa.Enum("L1_APPLY", name="magic_link_scope_enum")


def _stage(create: bool) -> sa.Enum:
    return sa.Enum(name="stage_enum", create_type=create, _create_events=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (SOURCE_ENUM, STAGE_ENUM, APP_STATUS_ENUM, SCOPE_ENUM):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("is_fresher", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total_experience_years", sa.Float(), nullable=True),
        sa.Column("relevant_experience_years", sa.Float(), nullable=True),
        sa.Column("current_company", sa.String(length=160), nullable=True),
        sa.Column("current_ctc", sa.Integer(), nullable=True),
        sa.Column("expected_ctc", sa.Integer(), nullable=True),
        sa.Column("notice_period_days", sa.Integer(), nullable=True),
        sa.Column("source", SOURCE_ENUM, nullable=False),
        sa.Column("referred_by", sa.String(length=160), nullable=True),
        sa.Column("resume_url", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_candidate_created_by"),
    )
    op.create_index("ix_candidates_email", "candidates", ["email"])

    op.create_table(
        "candidate_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("requisition_id", sa.Integer(), nullable=False),
        sa.Column("stage", _stage(False), nullable=False),
        sa.Column("status", APP_STATUS_ENUM, nullable=False),
        sa.Column("stage_entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rejection_stage", _stage(False), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], name="fk_app_candidate"),
        sa.ForeignKeyConstraint(["requisition_id"], ["requisitions.id"], name="fk_app_requisition"),
    )
    op.create_index("ix_candidate_applications_candidate_id", "candidate_applications", ["candidate_id"])
    op.create_index("ix_candidate_applications_requisition_id", "candidate_applications", ["requisition_id"])

    op.create_table(
        "application_form_l1",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], name="fk_l1_application"),
        sa.UniqueConstraint("application_id", name="uq_l1_application"),
    )

    op.create_table(
        "magic_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("scope", SCOPE_ENUM, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], name="fk_magiclink_application"),
        sa.UniqueConstraint("token_hash", name="uq_magic_links_token_hash"),
    )
    op.create_index("ix_magic_links_token_hash", "magic_links", ["token_hash"])
    op.create_index("ix_magic_links_application_id", "magic_links", ["application_id"])


def downgrade() -> None:
    op.drop_table("magic_links")
    op.drop_table("application_form_l1")
    op.drop_table("candidate_applications")
    op.drop_index("ix_candidates_email", table_name="candidates")
    op.drop_table("candidates")
    bind = op.get_bind()
    for enum in (SCOPE_ENUM, APP_STATUS_ENUM, STAGE_ENUM, SOURCE_ENUM):
        enum.drop(bind, checkfirst=True)
