"""M5 interviews: rubric templates/criteria, interviews, scorecards

Revision ID: 0005_m5_interviews
Revises: 0004_m4_assessments
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_m5_interviews"
down_revision: str | None = "0004_m4_assessments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# _create_events=False: these types are created explicitly in upgrade(); it stops
# op.create_table from re-emitting CREATE TYPE for a type used by >1 table
# (Postgres rejects the duplicate).
INTERVIEW_ROUND_ENUM = sa.Enum(
    "L3_HR", "L4_TECH1", "L5_TECH2", "L6_SALARY",
    name="interview_round_enum",
    _create_events=False,
)
INTERVIEW_MODE_ENUM = sa.Enum(
    "ONLINE", "IN_PERSON", "PHONE", name="interview_mode_enum", _create_events=False
)
INTERVIEW_STATUS_ENUM = sa.Enum(
    "SCHEDULED", "RESCHEDULED", "COMPLETED", "CANCELLED", "NO_SHOW",
    name="interview_status_enum",
    _create_events=False,
)
SCORECARD_DECISION_ENUM = sa.Enum(
    "STRONG_YES", "YES", "NO", "STRONG_NO",
    name="scorecard_decision_enum",
    _create_events=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    INTERVIEW_ROUND_ENUM.create(bind, checkfirst=True)
    INTERVIEW_MODE_ENUM.create(bind, checkfirst=True)
    INTERVIEW_STATUS_ENUM.create(bind, checkfirst=True)
    SCORECARD_DECISION_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "rubric_templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("round", INTERVIEW_ROUND_ENUM, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_rubric_created_by"),
        sa.UniqueConstraint("name", name="uq_rubric_templates_name"),
    )

    op.create_table(
        "rubric_criteria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rubric_template_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("max_score", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["rubric_template_id"], ["rubric_templates.id"], name="fk_criterion_rubric"),
    )
    op.create_index("ix_rubric_criteria_rubric_template_id", "rubric_criteria", ["rubric_template_id"])

    op.create_table(
        "interviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("round", INTERVIEW_ROUND_ENUM, nullable=False),
        sa.Column("mode", INTERVIEW_MODE_ENUM, nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="45"),
        sa.Column("interviewer_id", sa.Integer(), nullable=False),
        sa.Column("rubric_template_id", sa.Integer(), nullable=True),
        sa.Column("teams_join_url", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("status", INTERVIEW_STATUS_ENUM, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["candidate_applications.id"], name="fk_interview_application"),
        sa.ForeignKeyConstraint(["interviewer_id"], ["users.id"], name="fk_interview_interviewer"),
        sa.ForeignKeyConstraint(["rubric_template_id"], ["rubric_templates.id"], name="fk_interview_rubric"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], name="fk_interview_created_by"),
    )
    op.create_index("ix_interviews_application_id", "interviews", ["application_id"])
    op.create_index("ix_interviews_interviewer_id", "interviews", ["interviewer_id"])

    op.create_table(
        "scorecards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("interview_id", sa.Integer(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("decision", SCORECARD_DECISION_ENUM, nullable=False),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("concerns", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("submitted_by_id", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name="fk_scorecard_interview"),
        sa.ForeignKeyConstraint(["submitted_by_id"], ["users.id"], name="fk_scorecard_submitted_by"),
        sa.UniqueConstraint("interview_id", name="uq_scorecards_interview_id"),
    )

    op.create_table(
        "scorecard_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scorecard_id", sa.Integer(), nullable=False),
        sa.Column("criterion_id", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scorecard_id"], ["scorecards.id"], name="fk_score_scorecard"),
        sa.ForeignKeyConstraint(["criterion_id"], ["rubric_criteria.id"], name="fk_score_criterion"),
    )
    op.create_index("ix_scorecard_scores_scorecard_id", "scorecard_scores", ["scorecard_id"])


def downgrade() -> None:
    op.drop_index("ix_scorecard_scores_scorecard_id", table_name="scorecard_scores")
    op.drop_table("scorecard_scores")
    op.drop_table("scorecards")
    op.drop_index("ix_interviews_interviewer_id", table_name="interviews")
    op.drop_index("ix_interviews_application_id", table_name="interviews")
    op.drop_table("interviews")
    op.drop_index("ix_rubric_criteria_rubric_template_id", table_name="rubric_criteria")
    op.drop_table("rubric_criteria")
    op.drop_table("rubric_templates")
    bind = op.get_bind()
    SCORECARD_DECISION_ENUM.drop(bind, checkfirst=True)
    INTERVIEW_STATUS_ENUM.drop(bind, checkfirst=True)
    INTERVIEW_MODE_ENUM.drop(bind, checkfirst=True)
    INTERVIEW_ROUND_ENUM.drop(bind, checkfirst=True)
