"""M4 assessments: question bank, templates, attempts, answers

Revision ID: 0004_m4_assessments
Revises: 0003_m3_candidates
Create Date: 2026-06-20
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_m4_assessments"
down_revision: str | None = "0003_m3_candidates"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# _create_events=False: the type is created explicitly in upgrade(); this stops
# op.create_table from re-emitting CREATE TYPE (Postgres rejects the duplicate).
ATTEMPT_STATUS_ENUM = sa.Enum(
    "NOT_STARTED", "IN_PROGRESS", "SUBMITTED", "EXPIRED",
    name="attempt_status_enum",
    _create_events=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    ATTEMPT_STATUS_ENUM.create(bind, checkfirst=True)

    # New magic-link scope value (Postgres native enum needs ALTER TYPE; on
    # SQLite enum columns are plain VARCHAR so no change is required).
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TYPE magic_link_scope_enum ADD VALUE IF NOT EXISTS 'L2_ASSESSMENT'"
        )

    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options_json", sa.Text(), nullable=False),
        sa.Column("correct_index", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_question_created_by"),
    )

    op.create_table(
        "assessment_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("pass_pct", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_template_created_by"),
        sa.UniqueConstraint("name", name="uq_assessment_templates_name"),
    )

    op.create_table(
        "template_questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["assessment_templates.id"], name="fk_tq_template"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_tq_question"),
    )
    op.create_index("ix_template_questions_template_id", "template_questions", ["template_id"])
    op.create_index("ix_template_questions_question_id", "template_questions", ["question_id"])

    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("status", ATTEMPT_STATUS_ENUM, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_pct", sa.Float(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], name="fk_attempt_application"),
        sa.ForeignKeyConstraint(["template_id"], ["assessment_templates.id"], name="fk_attempt_template"),
    )
    op.create_index("ix_assessment_attempts_application_id", "assessment_attempts", ["application_id"])

    op.create_table(
        "assessment_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("selected_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["attempt_id"], ["assessment_attempts.id"], name="fk_answer_attempt"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_answer_question"),
    )
    op.create_index("ix_assessment_answers_attempt_id", "assessment_answers", ["attempt_id"])


def downgrade() -> None:
    op.drop_table("assessment_answers")
    op.drop_table("assessment_attempts")
    op.drop_index("ix_template_questions_question_id", table_name="template_questions")
    op.drop_index("ix_template_questions_template_id", table_name="template_questions")
    op.drop_table("template_questions")
    op.drop_table("assessment_templates")
    op.drop_table("questions")
    ATTEMPT_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    # The added enum value is intentionally not removed (Postgres cannot drop
    # enum values without recreating the type).
