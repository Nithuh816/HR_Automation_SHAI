"""M9 notifications: outbox for email / WhatsApp / in-app

Revision ID: 0009_m9_notifications
Revises: 0008_m8_onboarding
Create Date: 2026-06-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_m9_notifications"
down_revision: str | None = "0008_m8_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Created explicitly below; _create_events=False stops create_table from
# re-emitting CREATE TYPE (Postgres rejects the duplicate).
CHANNEL_ENUM = sa.Enum(
    "EMAIL", "WHATSAPP", "IN_APP", name="notification_channel_enum", _create_events=False
)
STATUS_ENUM = sa.Enum(
    "QUEUED", "SENT", "FAILED", name="notification_status_enum", _create_events=False
)


def upgrade() -> None:
    bind = op.get_bind()
    CHANNEL_ENUM.create(bind, checkfirst=True)
    STATUS_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("channel", CHANNEL_ENUM, nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=True),
        sa.Column("to_address", sa.String(length=255), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", STATUS_ENUM, nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=True),
        sa.Column("related_application_id", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("retries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"], ["users.id"], name="fk_notification_recipient"
        ),
        sa.ForeignKeyConstraint(
            ["related_application_id"],
            ["candidate_applications.id"],
            name="fk_notification_application",
        ),
        sa.UniqueConstraint("dedupe_key", name="uq_notifications_dedupe_key"),
    )
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications")
    op.drop_table("notifications")
    STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    CHANNEL_ENUM.drop(op.get_bind(), checkfirst=True)
