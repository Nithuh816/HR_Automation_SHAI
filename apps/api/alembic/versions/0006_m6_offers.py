"""M6 offers: offer templates, offers, approval lifecycle

Revision ID: 0006_m6_offers
Revises: 0005_m5_interviews
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_m6_offers"
down_revision: str | None = "0005_m5_interviews"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# _create_events=False: the type is created explicitly in upgrade(); this stops
# op.create_table from re-emitting CREATE TYPE (Postgres rejects the duplicate).
OFFER_STATUS_ENUM = sa.Enum(
    "DRAFT",
    "PENDING_APPROVAL",
    "APPROVED",
    "SENT",
    "ACCEPTED",
    "DECLINED",
    "REVOKED",
    name="offer_status_enum",
    _create_events=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    OFFER_STATUS_ENUM.create(bind, checkfirst=True)

    # New magic-link scope value (Postgres native enum needs ALTER TYPE; SQLite
    # stores enum columns as VARCHAR so no change is required).
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE magic_link_scope_enum ADD VALUE IF NOT EXISTS 'OFFER'")

    op.create_table(
        "offer_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_md", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["users.id"], name="fk_offer_template_created_by"
        ),
        sa.UniqueConstraint("name", name="uq_offer_templates_name"),
    )

    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("designation", sa.String(length=160), nullable=False),
        sa.Column("annual_ctc", sa.Integer(), nullable=False),
        sa.Column("components_json", sa.Text(), nullable=False),
        sa.Column("joining_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", OFFER_STATUS_ENUM, nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["application_id"], ["candidate_applications.id"], name="fk_offer_application"
        ),
        sa.ForeignKeyConstraint(["template_id"], ["offer_templates.id"], name="fk_offer_template"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_offer_created_by"),
        sa.ForeignKeyConstraint(["approved_by_id"], ["users.id"], name="fk_offer_approved_by"),
    )
    op.create_index("ix_offers_application_id", "offers", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_offers_application_id", table_name="offers")
    op.drop_table("offers")
    op.drop_table("offer_templates")
    OFFER_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    # The added magic_link_scope_enum value is intentionally not removed
    # (Postgres cannot drop enum values without recreating the type).
