"""Candidate management and per-candidate applications."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.candidate import Candidate, CandidateApplication
from app.models.consent import Consent
from app.models.enums import ApplicationStatus, Role, Stage
from app.models.requisition import Requisition
from app.schemas.candidate import (
    ApplicationCreate,
    ApplicationRead,
    CandidateCreate,
    CandidateRead,
    CandidateUpdate,
)
from app.schemas.consent import ConsentRead
from app.services import consent as consent_svc

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])

CAN_EDIT = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER}


def _require_edit(role: Role) -> None:
    if role not in CAN_EDIT:
        raise HTTPException(status_code=403, detail="TA members only")


def _new_application(candidate_id: int, requisition_id: int) -> CandidateApplication:
    return CandidateApplication(
        candidate_id=candidate_id,
        requisition_id=requisition_id,
        stage=Stage.SOURCED,
        status=ApplicationStatus.ACTIVE,
        stage_entered_at=datetime.now(UTC),
    )


@router.post("", response_model=CandidateRead, status_code=status.HTTP_201_CREATED)
def create_candidate(payload: CandidateCreate, db: SessionDep, user: CurrentUser) -> Candidate:
    _require_edit(user.role)
    if payload.requisition_id is not None and db.get(Requisition, payload.requisition_id) is None:
        raise HTTPException(status_code=422, detail="unknown requisition")

    data = payload.model_dump(exclude={"requisition_id"})
    candidate = Candidate(**data, created_by_id=user.id)
    db.add(candidate)
    db.flush()
    if payload.requisition_id is not None:
        db.add(_new_application(candidate.id, payload.requisition_id))
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[CandidateRead])
def list_candidates(db: SessionDep, _: CurrentUser) -> list[Candidate]:
    return list(db.scalars(select(Candidate).order_by(Candidate.created_at.desc())))


@router.get("/{candidate_id}", response_model=CandidateRead)
def get_candidate(candidate_id: int, db: SessionDep, _: CurrentUser) -> Candidate:
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateRead)
def update_candidate(
    candidate_id: int, payload: CandidateUpdate, db: SessionDep, user: CurrentUser
) -> Candidate:
    _require_edit(user.role)
    candidate = db.get(Candidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return candidate


@router.get("/{candidate_id}/applications", response_model=list[ApplicationRead])
def list_applications(
    candidate_id: int, db: SessionDep, _: CurrentUser
) -> list[CandidateApplication]:
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    stmt = select(CandidateApplication).where(CandidateApplication.candidate_id == candidate_id)
    return list(db.scalars(stmt))


@router.post(
    "/{candidate_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def attach_application(
    candidate_id: int, payload: ApplicationCreate, db: SessionDep, user: CurrentUser
) -> CandidateApplication:
    _require_edit(user.role)
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    if db.get(Requisition, payload.requisition_id) is None:
        raise HTTPException(status_code=422, detail="unknown requisition")
    existing = db.scalar(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == candidate_id)
        .where(CandidateApplication.requisition_id == payload.requisition_id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="already applied to this requisition")
    app = _new_application(candidate_id, payload.requisition_id)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


@router.get("/{candidate_id}/consents", response_model=list[ConsentRead])
def list_consents(candidate_id: int, db: SessionDep, _: CurrentUser) -> list[Consent]:
    """DPDPA consent records captured from this candidate's pages."""
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    return consent_svc.for_candidate(db, candidate_id)
