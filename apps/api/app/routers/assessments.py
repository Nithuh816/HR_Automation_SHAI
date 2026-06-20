"""Assessment administration: question bank and templates (HR Head / TA TL)."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import SessionDep, require_roles
from app.models.assessment import (
    AssessmentTemplate,
    Question,
    TemplateQuestion,
)
from app.models.enums import Role
from app.models.user import User
from app.schemas.assessment import (
    AddQuestionRequest,
    QuestionCreate,
    QuestionRead,
    QuestionUpdate,
    TemplateCreate,
    TemplateDetail,
    TemplateRead,
    TemplateUpdate,
)
from app.services import assessments as svc

router = APIRouter(prefix="/api/v1/assessment", tags=["assessment"])

Manager = Annotated[User, Depends(require_roles(Role.HR_HEAD, Role.TA_TL))]


def _to_question_read(q: Question) -> QuestionRead:
    return QuestionRead(
        id=q.id,
        text=q.text,
        options=svc.options_of(q),
        correct_index=q.correct_index,
        category=q.category,
        points=q.points,
        is_active=q.is_active,
    )


# --- Questions ---
@router.post("/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(payload: QuestionCreate, db: SessionDep, user: Manager) -> QuestionRead:
    q = Question(
        text=payload.text,
        options_json=json.dumps(payload.options),
        correct_index=payload.correct_index,
        category=payload.category,
        points=payload.points,
        created_by_id=user.id,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return _to_question_read(q)


@router.get("/questions", response_model=list[QuestionRead])
def list_questions(db: SessionDep, _: Manager) -> list[QuestionRead]:
    return [_to_question_read(q) for q in db.scalars(select(Question).order_by(Question.id))]


@router.patch("/questions/{question_id}", response_model=QuestionRead)
def update_question(
    question_id: int, payload: QuestionUpdate, db: SessionDep, _: Manager
) -> QuestionRead:
    q = db.get(Question, question_id)
    if q is None:
        raise HTTPException(status_code=404, detail="question not found")
    data = payload.model_dump(exclude_unset=True)
    if "options" in data:
        q.options_json = json.dumps(data.pop("options"))
    for field, value in data.items():
        setattr(q, field, value)
    if q.correct_index >= len(svc.options_of(q)):
        raise HTTPException(status_code=422, detail="correct_index out of range")
    db.commit()
    db.refresh(q)
    return _to_question_read(q)


# --- Templates ---
@router.post("/templates", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreate, db: SessionDep, user: Manager) -> AssessmentTemplate:
    template = AssessmentTemplate(
        name=payload.name,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        pass_pct=payload.pass_pct,
        created_by_id=user.id,
    )
    db.add(template)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="template name already exists") from exc
    db.refresh(template)
    return template


@router.get("/templates", response_model=list[TemplateRead])
def list_templates(db: SessionDep, _: Manager) -> list[AssessmentTemplate]:
    return list(db.scalars(select(AssessmentTemplate).order_by(AssessmentTemplate.name)))


@router.get("/templates/{template_id}", response_model=TemplateDetail)
def get_template(template_id: int, db: SessionDep, _: Manager) -> TemplateDetail:
    template = db.get(AssessmentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    questions = [_to_question_read(q) for q in svc.template_questions(db, template_id)]
    return TemplateDetail(
        id=template.id,
        name=template.name,
        description=template.description,
        duration_minutes=template.duration_minutes,
        pass_pct=template.pass_pct,
        is_active=template.is_active,
        questions=questions,
    )


@router.patch("/templates/{template_id}", response_model=TemplateRead)
def update_template(
    template_id: int, payload: TemplateUpdate, db: SessionDep, _: Manager
) -> AssessmentTemplate:
    template = db.get(AssessmentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template


@router.post("/templates/{template_id}/questions", status_code=status.HTTP_204_NO_CONTENT)
def add_question_to_template(
    template_id: int, payload: AddQuestionRequest, db: SessionDep, _: Manager
) -> None:
    if db.get(AssessmentTemplate, template_id) is None:
        raise HTTPException(status_code=404, detail="template not found")
    if db.get(Question, payload.question_id) is None:
        raise HTTPException(status_code=422, detail="unknown question")
    exists = db.scalar(
        select(TemplateQuestion)
        .where(TemplateQuestion.template_id == template_id)
        .where(TemplateQuestion.question_id == payload.question_id)
    )
    if exists is None:
        db.add(
            TemplateQuestion(
                template_id=template_id,
                question_id=payload.question_id,
                position=payload.position,
            )
        )
        db.commit()


@router.delete(
    "/templates/{template_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_question_from_template(
    template_id: int, question_id: int, db: SessionDep, _: Manager
) -> None:
    link = db.scalar(
        select(TemplateQuestion)
        .where(TemplateQuestion.template_id == template_id)
        .where(TemplateQuestion.question_id == question_id)
    )
    if link is not None:
        db.delete(link)
        db.commit()
