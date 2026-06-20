"""Assessment domain logic: question ordering and grading."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTemplate,
    Question,
    TemplateQuestion,
)


def options_of(question: Question) -> list[str]:
    return list(json.loads(question.options_json))


def template_questions(db: Session, template_id: int) -> list[Question]:
    """Questions for a template, in their configured order."""
    rows = db.execute(
        select(Question)
        .join(TemplateQuestion, TemplateQuestion.question_id == Question.id)
        .where(TemplateQuestion.template_id == template_id)
        .order_by(TemplateQuestion.position.asc(), TemplateQuestion.id.asc())
    ).scalars()
    return list(rows)


def grade(db: Session, attempt: AssessmentAttempt) -> tuple[float, bool]:
    """Score an attempt against the question bank; return (pct, passed)."""
    questions = {q.id: q for q in template_questions(db, attempt.template_id)}
    total_points = sum(q.points for q in questions.values())
    if total_points == 0:
        return 0.0, False

    answers = db.scalars(select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt.id))
    earned = 0
    for ans in answers:
        q = questions.get(ans.question_id)
        if q is not None and ans.selected_index == q.correct_index:
            earned += q.points

    pct = round(earned / total_points * 100, 2)
    template = db.get(AssessmentTemplate, attempt.template_id)
    pass_pct = template.pass_pct if template else 100
    return pct, pct >= pass_pct
