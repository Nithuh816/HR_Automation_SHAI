"""Candidate-facing pages — authenticated by magic-link token, no account.

All routes live under ``/api/v1/c`` and take a token in the path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import SessionDep
from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTemplate,
)
from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
)
from app.models.enums import AttemptStatus, MagicLinkScope, Stage
from app.models.requisition import Requisition
from app.schemas.assessment import (
    AssessmentContext,
    AssessmentResult,
    AssessmentSubmit,
    PublicQuestion,
)
from app.schemas.candidate import L1Context, L1Submit
from app.services import assessments, magic_links

router = APIRouter(prefix="/api/v1/c", tags=["candidate-portal"])


def _resolve(
    db: SessionDep, token: str, scope: MagicLinkScope
) -> tuple[CandidateApplication, Candidate, Requisition]:
    try:
        link = magic_links.verify(db, token, scope)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    app = db.get(CandidateApplication, link.application_id)
    candidate = db.get(Candidate, app.candidate_id) if app else None
    req = db.get(Requisition, app.requisition_id) if app else None
    if app is None or candidate is None or req is None:
        raise HTTPException(status_code=404, detail="application not found")
    return app, candidate, req


@router.get("/l1/{token}", response_model=L1Context)
def get_l1_form(token: str, db: SessionDep) -> L1Context:
    app, candidate, req = _resolve(db, token, MagicLinkScope.L1_APPLY)
    existing = db.scalar(
        select(ApplicationFormL1).where(ApplicationFormL1.application_id == app.id)
    )
    return L1Context(
        candidate_name=candidate.name,
        requisition_title=req.title,
        already_submitted=existing is not None,
        payload=json.loads(existing.payload_json) if existing else None,
    )


@router.post("/l1/{token}", response_model=L1Context)
def submit_l1_form(token: str, payload: L1Submit, db: SessionDep) -> L1Context:
    app, candidate, req = _resolve(db, token, MagicLinkScope.L1_APPLY)
    if db.scalar(select(ApplicationFormL1).where(ApplicationFormL1.application_id == app.id)):
        raise HTTPException(status_code=409, detail="form already submitted")

    form = ApplicationFormL1(
        application_id=app.id,
        payload_json=json.dumps(payload.payload),
        submitted_at=datetime.now(UTC),
    )
    db.add(form)
    # Submitting the L1 form moves a freshly sourced candidate into L1.
    if app.stage == Stage.SOURCED:
        app.stage = Stage.L1_APPLICATION
        app.stage_entered_at = datetime.now(UTC)
    # Single-use: burn the link.
    link = magic_links.verify(db, token, MagicLinkScope.L1_APPLY)
    magic_links.consume(link)
    db.commit()

    return L1Context(
        candidate_name=candidate.name,
        requisition_title=req.title,
        already_submitted=True,
        payload=payload.payload,
    )


def _latest_attempt(db: SessionDep, application_id: int) -> AssessmentAttempt:
    attempt = db.scalar(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.application_id == application_id)
        .order_by(AssessmentAttempt.id.desc())
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="no assessment for this link")
    return attempt


@router.get("/assessment/{token}", response_model=AssessmentContext)
def get_assessment(token: str, db: SessionDep) -> AssessmentContext:
    app, candidate, _ = _resolve(db, token, MagicLinkScope.L2_ASSESSMENT)
    attempt = _latest_attempt(db, app.id)
    template = db.get(AssessmentTemplate, attempt.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")

    # Start the clock on first open.
    if attempt.status == AttemptStatus.NOT_STARTED:
        now = datetime.now(UTC)
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.started_at = now
        attempt.expires_at = now + timedelta(minutes=template.duration_minutes)
        db.commit()

    questions = [
        PublicQuestion(id=q.id, text=q.text, options=assessments.options_of(q))
        for q in assessments.template_questions(db, template.id)
    ]
    return AssessmentContext(
        template_name=template.name,
        candidate_name=candidate.name,
        duration_minutes=template.duration_minutes,
        expires_at=attempt.expires_at or datetime.now(UTC),
        already_submitted=attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED),
        questions=questions,
    )


@router.post("/assessment/{token}", response_model=AssessmentResult)
def submit_assessment(token: str, payload: AssessmentSubmit, db: SessionDep) -> AssessmentResult:
    app, _, _ = _resolve(db, token, MagicLinkScope.L2_ASSESSMENT)
    attempt = _latest_attempt(db, app.id)
    if attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):
        raise HTTPException(status_code=409, detail="assessment already completed")

    valid_ids = {q.id for q in assessments.template_questions(db, attempt.template_id)}
    for ans in payload.answers:
        if ans.question_id in valid_ids:
            db.add(
                AssessmentAnswer(
                    attempt_id=attempt.id,
                    question_id=ans.question_id,
                    selected_index=ans.selected_index,
                )
            )
    db.flush()

    score_pct, passed = assessments.grade(db, attempt)
    attempt.score_pct = score_pct
    attempt.passed = passed
    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_at = datetime.now(UTC)

    # Passing L2 advances the candidate to the HR round.
    if passed and app.stage in (
        Stage.SOURCED,
        Stage.L1_APPLICATION,
        Stage.L2_ASSESSMENT,
    ):
        app.stage = Stage.L3_HR
        app.stage_entered_at = datetime.now(UTC)

    link = magic_links.verify(db, token, MagicLinkScope.L2_ASSESSMENT)
    magic_links.consume(link)
    db.commit()
    return AssessmentResult(score_pct=score_pct, passed=passed)
