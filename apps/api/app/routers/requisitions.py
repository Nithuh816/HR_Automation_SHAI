"""Requisition routes: create, triage inbox, assign, status, comments."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.department import Department
from app.models.enums import RequisitionStatus, Role
from app.models.requisition import Requisition, RequisitionComment
from app.models.user import User
from app.schemas.requisition import (
    AssignRequest,
    CommentCreate,
    CommentRead,
    RequisitionCreate,
    RequisitionRead,
    RequisitionUpdate,
    StatusChangeRequest,
)
from app.services import audit
from app.services import requisitions as svc

router = APIRouter(prefix="/api/v1/requisitions", tags=["requisitions"])

CAN_CREATE = {Role.HR_HEAD, Role.DEPT_HEAD, Role.TA_TL}
CAN_TRIAGE = {Role.HR_HEAD, Role.TA_TL}
RECRUITER_ROLES = {Role.TA_RECRUITER, Role.TA_TL}


def _get_or_404(db: SessionDep, req_id: int) -> Requisition:
    req = db.get(Requisition, req_id)
    if req is None:
        raise HTTPException(status_code=404, detail="requisition not found")
    return req


@router.post("", response_model=RequisitionRead, status_code=status.HTTP_201_CREATED)
def create_requisition(
    payload: RequisitionCreate, db: SessionDep, user: CurrentUser
) -> Requisition:
    if user.role not in CAN_CREATE:
        raise HTTPException(status_code=403, detail="not allowed to raise requisitions")
    if db.get(Department, payload.department_id) is None:
        raise HTTPException(status_code=422, detail="unknown department")

    req = Requisition(
        code="",  # set after flush, when id is known
        title=payload.title,
        department_id=payload.department_id,
        jd_md=payload.jd_md,
        headcount=payload.headcount,
        min_experience_years=payload.min_experience_years,
        max_experience_years=payload.max_experience_years,
        min_budget=payload.min_budget,
        max_budget=payload.max_budget,
        urgency=payload.urgency,
        status=RequisitionStatus.SUBMITTED,
        created_by_id=user.id,
        due_by=payload.due_by,
    )
    db.add(req)
    db.flush()
    req.code = svc.make_code(req.id)
    audit.record(
        db,
        actor=user,
        action="requisition.created",
        entity_type="requisition",
        entity_id=req.id,
        summary=f"{req.code} · {req.title}",
    )
    db.commit()
    db.refresh(req)
    return req


@router.get("", response_model=list[RequisitionRead])
def list_requisitions(
    db: SessionDep,
    user: CurrentUser,
    status_filter: Annotated[RequisitionStatus | None, Query(alias="status")] = None,
    department_id: int | None = None,
    mine: bool = False,
) -> list[Requisition]:
    stmt = select(Requisition).order_by(Requisition.created_at.desc())
    # Recruiters only ever see their own assigned requisitions.
    if user.role == Role.TA_RECRUITER or mine:
        stmt = stmt.where(Requisition.assigned_recruiter_id == user.id)
    if status_filter is not None:
        stmt = stmt.where(Requisition.status == status_filter)
    if department_id is not None:
        stmt = stmt.where(Requisition.department_id == department_id)
    return list(db.scalars(stmt))


@router.get("/inbox", response_model=list[RequisitionRead])
def triage_inbox(db: SessionDep, user: CurrentUser) -> list[Requisition]:
    if user.role not in CAN_TRIAGE:
        raise HTTPException(status_code=403, detail="triage is HR Head / TA TL only")
    stmt = (
        select(Requisition)
        .where(Requisition.status == RequisitionStatus.SUBMITTED)
        .where(Requisition.assigned_recruiter_id.is_(None))
        .order_by(Requisition.created_at.asc())
    )
    return list(db.scalars(stmt))


@router.get("/{req_id}", response_model=RequisitionRead)
def get_requisition(req_id: int, db: SessionDep, _: CurrentUser) -> Requisition:
    return _get_or_404(db, req_id)


@router.patch("/{req_id}", response_model=RequisitionRead)
def update_requisition(
    req_id: int, payload: RequisitionUpdate, db: SessionDep, user: CurrentUser
) -> Requisition:
    req = _get_or_404(db, req_id)
    if user.role != Role.HR_HEAD and user.id != req.created_by_id:
        raise HTTPException(status_code=403, detail="only HR Head or the creator may edit")
    data = payload.model_dump(exclude_unset=True)
    if "department_id" in data and db.get(Department, data["department_id"]) is None:
        raise HTTPException(status_code=422, detail="unknown department")
    for field, value in data.items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return req


@router.post("/{req_id}/assign", response_model=RequisitionRead)
def assign_requisition(
    req_id: int, payload: AssignRequest, db: SessionDep, user: CurrentUser
) -> Requisition:
    if user.role not in CAN_TRIAGE:
        raise HTTPException(status_code=403, detail="assignment is HR Head / TA TL only")
    req = _get_or_404(db, req_id)
    if req.status in (RequisitionStatus.FILLED, RequisitionStatus.CANCELLED):
        raise HTTPException(status_code=409, detail="requisition is closed")
    recruiter = db.get(User, payload.recruiter_id)
    if recruiter is None or not recruiter.is_active or recruiter.role not in RECRUITER_ROLES:
        raise HTTPException(status_code=422, detail="recruiter must be an active TA member")
    req.assigned_recruiter_id = recruiter.id
    req.status = RequisitionStatus.ASSIGNED
    audit.record(
        db,
        actor=user,
        action="requisition.assigned",
        entity_type="requisition",
        entity_id=req.id,
        summary=f"Assigned to {recruiter.name}",
        meta={"recruiter_id": recruiter.id},
    )
    db.commit()
    db.refresh(req)
    return req


@router.post("/{req_id}/status", response_model=RequisitionRead)
def change_status(
    req_id: int, payload: StatusChangeRequest, db: SessionDep, user: CurrentUser
) -> Requisition:
    req = _get_or_404(db, req_id)
    allowed = user.role in CAN_TRIAGE or user.id == req.assigned_recruiter_id
    if not allowed:
        raise HTTPException(status_code=403, detail="not allowed to change status")
    if not svc.can_transition(req.status, payload.status):
        raise HTTPException(
            status_code=409,
            detail=f"cannot move from {req.status} to {payload.status}",
        )
    req.status = payload.status
    if payload.status == RequisitionStatus.SUBMITTED:
        req.assigned_recruiter_id = None
    audit.record(
        db,
        actor=user,
        action="requisition.status_changed",
        entity_type="requisition",
        entity_id=req.id,
        summary=f"Status → {payload.status.value}",
        meta={"status": payload.status.value},
    )
    db.commit()
    db.refresh(req)
    return req


@router.get("/{req_id}/comments", response_model=list[CommentRead])
def list_comments(req_id: int, db: SessionDep, _: CurrentUser) -> list[RequisitionComment]:
    _get_or_404(db, req_id)
    stmt = (
        select(RequisitionComment)
        .where(RequisitionComment.requisition_id == req_id)
        .order_by(RequisitionComment.created_at.asc())
    )
    return list(db.scalars(stmt))


@router.post(
    "/{req_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    req_id: int, payload: CommentCreate, db: SessionDep, user: CurrentUser
) -> RequisitionComment:
    _get_or_404(db, req_id)
    comment = RequisitionComment(requisition_id=req_id, author_id=user.id, body=payload.body)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment
