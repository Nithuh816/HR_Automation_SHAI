"""Pipeline board + application stage transitions + L1 link generation."""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.assessment import AssessmentAttempt, AssessmentTemplate
from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import ApplicationStatus, AttemptStatus, MagicLinkScope, Role, Stage
from app.models.requisition import Requisition
from app.schemas.assessment import AttemptRead, IssueAssessmentRequest
from app.schemas.candidate import (
    ApplicationRead,
    MagicLinkResponse,
    PipelineCard,
    RejectRequest,
    StageMoveRequest,
)
from app.services import audit, magic_links, pipeline

router = APIRouter(prefix="/api/v1", tags=["pipeline"])

CAN_MOVE = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER}
L1_LINK_TTL = timedelta(days=7)
ASSESSMENT_LINK_TTL = timedelta(hours=48)


def _get_app(db: SessionDep, app_id: int) -> CandidateApplication:
    app = db.get(CandidateApplication, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="application not found")
    return app


@router.get("/pipeline/{req_id}", response_model=list[PipelineCard])
def pipeline_board(req_id: int, db: SessionDep, _: CurrentUser) -> list[PipelineCard]:
    if db.get(Requisition, req_id) is None:
        raise HTTPException(status_code=404, detail="requisition not found")
    rows = db.execute(
        select(CandidateApplication, Candidate.name)
        .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
        .where(CandidateApplication.requisition_id == req_id)
        .order_by(CandidateApplication.stage_entered_at.asc())
    ).all()
    return [
        PipelineCard(
            application_id=app.id,
            candidate_id=app.candidate_id,
            candidate_name=name,
            stage=app.stage,
            status=app.status,
        )
        for app, name in rows
    ]


@router.post("/applications/{app_id}/stage", response_model=ApplicationRead)
def move_stage(
    app_id: int, payload: StageMoveRequest, db: SessionDep, user: CurrentUser
) -> CandidateApplication:
    if user.role not in CAN_MOVE:
        raise HTTPException(status_code=403, detail="TA members only")
    app = _get_app(db, app_id)
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    pipeline.set_stage(app, payload.stage)
    audit.record(
        db,
        actor=user,
        action="application.stage_changed",
        entity_type="application",
        entity_id=app.id,
        summary=f"Moved to {payload.stage.value}",
        meta={"stage": payload.stage.value},
    )
    db.commit()
    db.refresh(app)
    return app


@router.post("/applications/{app_id}/reject", response_model=ApplicationRead)
def reject_application(
    app_id: int, payload: RejectRequest, db: SessionDep, user: CurrentUser
) -> CandidateApplication:
    if user.role not in CAN_MOVE:
        raise HTTPException(status_code=403, detail="TA members only")
    app = _get_app(db, app_id)
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    pipeline.reject(app, payload.reason)
    audit.record(
        db,
        actor=user,
        action="application.rejected",
        entity_type="application",
        entity_id=app.id,
        summary=f"Rejected at {app.stage.value}",
        meta={"reason": payload.reason},
    )
    db.commit()
    db.refresh(app)
    return app


@router.post("/applications/{app_id}/l1-link", response_model=MagicLinkResponse)
def create_l1_link(app_id: int, db: SessionDep, user: CurrentUser) -> MagicLinkResponse:
    if user.role not in CAN_MOVE:
        raise HTTPException(status_code=403, detail="TA members only")
    app = _get_app(db, app_id)
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    token, link = magic_links.create_link(db, MagicLinkScope.L1_APPLY, app.id, L1_LINK_TTL)
    db.commit()
    return MagicLinkResponse(url=magic_links.build_url(token, "apply"), expires_at=link.expires_at)


@router.post("/applications/{app_id}/assessment", response_model=MagicLinkResponse)
def issue_assessment(
    app_id: int, payload: IssueAssessmentRequest, db: SessionDep, user: CurrentUser
) -> MagicLinkResponse:
    if user.role not in CAN_MOVE:
        raise HTTPException(status_code=403, detail="TA members only")
    app = _get_app(db, app_id)
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    if db.get(AssessmentTemplate, payload.template_id) is None:
        raise HTTPException(status_code=422, detail="unknown template")

    attempt = AssessmentAttempt(
        application_id=app.id,
        template_id=payload.template_id,
        status=AttemptStatus.NOT_STARTED,
    )
    db.add(attempt)
    db.flush()
    token, link = magic_links.create_link(
        db, MagicLinkScope.L2_ASSESSMENT, app.id, ASSESSMENT_LINK_TTL
    )
    # Sending the assessment moves the candidate into the L2 stage.
    if app.stage in (Stage.SOURCED, Stage.L1_APPLICATION):
        pipeline.set_stage(app, Stage.L2_ASSESSMENT)
    db.commit()
    return MagicLinkResponse(
        url=magic_links.build_url(token, "assessment"), expires_at=link.expires_at
    )


@router.get("/applications/{app_id}/attempts", response_model=list[AttemptRead])
def list_attempts(app_id: int, db: SessionDep, _: CurrentUser) -> list[AssessmentAttempt]:
    _get_app(db, app_id)
    stmt = (
        select(AssessmentAttempt)
        .where(AssessmentAttempt.application_id == app_id)
        .order_by(AssessmentAttempt.id.desc())
    )
    return list(db.scalars(stmt))
