"""Interview scheduling, the day's board, and scorecards (rounds L3-L6)."""

from __future__ import annotations

from datetime import UTC, datetime, time

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.integrations import graph
from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import (
    POSITIVE_DECISIONS,
    STAGE_ORDER,
    ApplicationStatus,
    InterviewStatus,
    Role,
)
from app.models.interview import Interview, RubricTemplate, Scorecard, ScorecardScore
from app.models.requisition import Requisition
from app.models.user import User
from app.schemas.interview import (
    InterviewCreate,
    InterviewDetail,
    InterviewReschedule,
    ScorecardRead,
    ScorecardScoreRead,
    ScorecardSubmit,
)
from app.services import audit, notifications, pipeline
from app.services import interviews as svc

router = APIRouter(prefix="/api/v1", tags=["interviews"])

CAN_SCHEDULE = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER}
LIVE_STATUSES = (InterviewStatus.SCHEDULED, InterviewStatus.RESCHEDULED)


def _require_schedule(role: Role) -> None:
    if role not in CAN_SCHEDULE:
        raise HTTPException(status_code=403, detail="TA members only")


def _get_app(db: SessionDep, app_id: int) -> CandidateApplication:
    app = db.get(CandidateApplication, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="application not found")
    return app


def _get_interview(db: SessionDep, interview_id: int) -> Interview:
    interview = db.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(status_code=404, detail="interview not found")
    return interview


def _scorecard_read(db: SessionDep, scorecard: Scorecard) -> ScorecardRead:
    scores = db.scalars(
        select(ScorecardScore)
        .where(ScorecardScore.scorecard_id == scorecard.id)
        .order_by(ScorecardScore.id.asc())
    )
    return ScorecardRead(
        id=scorecard.id,
        interview_id=scorecard.interview_id,
        overall_score=scorecard.overall_score,
        decision=scorecard.decision,
        strengths=scorecard.strengths,
        concerns=scorecard.concerns,
        recommendation=scorecard.recommendation,
        submitted_by_id=scorecard.submitted_by_id,
        submitted_at=scorecard.submitted_at,
        scores=[ScorecardScoreRead.model_validate(s) for s in scores],
    )


def _detail(db: SessionDep, interview: Interview) -> InterviewDetail:
    app = db.get(CandidateApplication, interview.application_id)
    candidate = db.get(Candidate, app.candidate_id) if app else None
    req = db.get(Requisition, app.requisition_id) if app else None
    interviewer = db.get(User, interview.interviewer_id)
    if app is None or candidate is None or req is None or interviewer is None:
        raise HTTPException(status_code=404, detail="interview context missing")
    scorecard = db.scalar(select(Scorecard).where(Scorecard.interview_id == interview.id))
    return InterviewDetail(
        id=interview.id,
        application_id=interview.application_id,
        round=interview.round,
        mode=interview.mode,
        scheduled_at=interview.scheduled_at,
        duration_minutes=interview.duration_minutes,
        interviewer_id=interview.interviewer_id,
        rubric_template_id=interview.rubric_template_id,
        teams_join_url=interview.teams_join_url,
        location=interview.location,
        status=interview.status,
        notes=interview.notes,
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        requisition_id=req.id,
        requisition_title=req.title,
        interviewer_name=interviewer.name,
        scorecard=_scorecard_read(db, scorecard) if scorecard else None,
    )


@router.post("/applications/{app_id}/interviews", response_model=InterviewDetail, status_code=201)
def schedule_interview(
    app_id: int, payload: InterviewCreate, db: SessionDep, user: CurrentUser
) -> InterviewDetail:
    _require_schedule(user.role)
    app = _get_app(db, app_id)
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    interviewer = db.get(User, payload.interviewer_id)
    if interviewer is None or not interviewer.is_active:
        raise HTTPException(status_code=422, detail="unknown interviewer")
    if (
        payload.rubric_template_id is not None
        and db.get(RubricTemplate, payload.rubric_template_id) is None
    ):
        raise HTTPException(status_code=422, detail="unknown rubric")

    candidate = db.get(Candidate, app.candidate_id)
    join_url = None
    if payload.mode.value == "online":
        subject = f"{payload.round.value.upper()} — {candidate.name if candidate else 'Candidate'}"
        join_url = graph.create_teams_meeting(
            subject, payload.scheduled_at, payload.duration_minutes
        )

    interview = Interview(
        application_id=app.id,
        round=payload.round,
        mode=payload.mode,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        interviewer_id=payload.interviewer_id,
        rubric_template_id=payload.rubric_template_id,
        teams_join_url=join_url,
        location=payload.location,
        notes=payload.notes,
        created_by_id=user.id,
    )
    db.add(interview)

    # Move the application into the round's stage (never backwards).
    target = svc.round_stage(payload.round)
    if STAGE_ORDER.index(target) > STAGE_ORDER.index(app.stage):
        pipeline.set_stage(app, target)

    if candidate is not None:
        notifications.interview_scheduled_email(
            db,
            application_id=app.id,
            candidate_name=candidate.name,
            candidate_email=candidate.email,
            round_label=payload.round.value.upper(),
            when=payload.scheduled_at,
            join_url=join_url,
        )

    db.flush()
    audit.record(
        db,
        actor=user,
        action="interview.scheduled",
        entity_type="interview",
        entity_id=interview.id,
        summary=f"{payload.round.value.upper()} · {interviewer.name}",
        meta={"round": payload.round.value},
    )
    db.commit()
    db.refresh(interview)
    return _detail(db, interview)


@router.get("/applications/{app_id}/interviews", response_model=list[InterviewDetail])
def list_application_interviews(
    app_id: int, db: SessionDep, _: CurrentUser
) -> list[InterviewDetail]:
    _get_app(db, app_id)
    rows = db.scalars(
        select(Interview)
        .where(Interview.application_id == app_id)
        .order_by(Interview.scheduled_at.asc())
    )
    return [_detail(db, i) for i in rows]


@router.get("/interviews/today", response_model=list[InterviewDetail])
def todays_interviews(db: SessionDep, user: CurrentUser) -> list[InterviewDetail]:
    """Upcoming, still-live interviews from the start of today (UTC).

    TA staff see every interview; an interviewer sees only their own.
    """
    start_of_day = datetime.combine(datetime.now(UTC).date(), time.min, tzinfo=UTC)
    stmt = (
        select(Interview)
        .where(Interview.status.in_(LIVE_STATUSES))
        .where(Interview.scheduled_at >= start_of_day)
        .order_by(Interview.scheduled_at.asc())
    )
    if user.role not in CAN_SCHEDULE:
        stmt = stmt.where(Interview.interviewer_id == user.id)
    return [_detail(db, i) for i in db.scalars(stmt)]


@router.get("/interviews/{interview_id}", response_model=InterviewDetail)
def get_interview(interview_id: int, db: SessionDep, _: CurrentUser) -> InterviewDetail:
    return _detail(db, _get_interview(db, interview_id))


@router.post("/interviews/{interview_id}/reschedule", response_model=InterviewDetail)
def reschedule_interview(
    interview_id: int, payload: InterviewReschedule, db: SessionDep, user: CurrentUser
) -> InterviewDetail:
    _require_schedule(user.role)
    interview = _get_interview(db, interview_id)
    if interview.status not in LIVE_STATUSES:
        raise HTTPException(status_code=409, detail="interview is not reschedulable")
    interview.scheduled_at = payload.scheduled_at
    if payload.mode is not None:
        interview.mode = payload.mode
    if payload.duration_minutes is not None:
        interview.duration_minutes = payload.duration_minutes
    interview.status = InterviewStatus.RESCHEDULED
    if interview.mode.value == "online":
        candidate = db.get(
            Candidate,
            db.get(CandidateApplication, interview.application_id).candidate_id,  # type: ignore[union-attr]
        )
        subject = (
            f"{interview.round.value.upper()} — {candidate.name if candidate else 'Candidate'}"
        )
        interview.teams_join_url = graph.create_teams_meeting(
            subject, interview.scheduled_at, interview.duration_minutes
        )
    audit.record(
        db,
        actor=user,
        action="interview.rescheduled",
        entity_type="interview",
        entity_id=interview.id,
    )
    db.commit()
    db.refresh(interview)
    return _detail(db, interview)


@router.post("/interviews/{interview_id}/cancel", response_model=InterviewDetail)
def cancel_interview(interview_id: int, db: SessionDep, user: CurrentUser) -> InterviewDetail:
    _require_schedule(user.role)
    interview = _get_interview(db, interview_id)
    if interview.status == InterviewStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="completed interview cannot be cancelled")
    interview.status = InterviewStatus.CANCELLED
    audit.record(
        db,
        actor=user,
        action="interview.cancelled",
        entity_type="interview",
        entity_id=interview.id,
    )
    db.commit()
    db.refresh(interview)
    return _detail(db, interview)


@router.post("/interviews/{interview_id}/scorecard", response_model=InterviewDetail)
def submit_scorecard(
    interview_id: int, payload: ScorecardSubmit, db: SessionDep, user: CurrentUser
) -> InterviewDetail:
    interview = _get_interview(db, interview_id)
    # Only the assigned interviewer (or HR Head) may rate the round.
    if user.id != interview.interviewer_id and user.role != Role.HR_HEAD:
        raise HTTPException(status_code=403, detail="only the interviewer may submit a scorecard")
    if interview.status == InterviewStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="interview was cancelled")
    if db.scalar(select(Scorecard).where(Scorecard.interview_id == interview.id)) is not None:
        raise HTTPException(status_code=409, detail="scorecard already submitted")

    overall = svc.weighted_overall([(s.score, s.weight) for s in payload.scores])
    scorecard = Scorecard(
        interview_id=interview.id,
        overall_score=overall,
        decision=payload.decision,
        strengths=payload.strengths,
        concerns=payload.concerns,
        recommendation=payload.recommendation,
        submitted_by_id=user.id,
        submitted_at=datetime.now(UTC),
    )
    db.add(scorecard)
    db.flush()
    for s in payload.scores:
        db.add(
            ScorecardScore(
                scorecard_id=scorecard.id,
                criterion_id=s.criterion_id,
                label=s.label,
                score=s.score,
                weight=s.weight,
                comment=s.comment,
            )
        )

    interview.status = InterviewStatus.COMPLETED

    # A passing scorecard advances the candidate; a rejecting one ends the app.
    app = db.get(CandidateApplication, interview.application_id)
    if app is not None and app.status == ApplicationStatus.ACTIVE:
        if payload.decision in POSITIVE_DECISIONS:
            target = svc.next_stage_after(interview.round)
            if STAGE_ORDER.index(target) > STAGE_ORDER.index(app.stage):
                pipeline.set_stage(app, target)
        else:
            pipeline.reject(app, payload.recommendation or payload.concerns)

    audit.record(
        db,
        actor=user,
        action="scorecard.submitted",
        entity_type="interview",
        entity_id=interview.id,
        summary=f"{interview.round.value.upper()} — {payload.decision.value}",
        meta={"decision": payload.decision.value, "overall_score": overall},
    )
    db.commit()
    db.refresh(interview)
    return _detail(db, interview)
