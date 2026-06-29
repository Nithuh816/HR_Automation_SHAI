"""Dashboards & reports (M10). Management-facing, read-only."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.deps import CurrentUser, SessionDep
from app.models.enums import Role
from app.schemas.report import (
    DropOff,
    FunnelReport,
    RecruiterPerformance,
    ReportSummary,
    SourceCount,
    TimeToFillReport,
)
from app.services import reports

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

CAN_VIEW = {Role.HR_HEAD, Role.TA_TL}


def _require_view(role: Role) -> None:
    if role not in CAN_VIEW:
        raise HTTPException(status_code=403, detail="reports are for HR Head and TA Team Lead")


@router.get("/summary", response_model=ReportSummary)
def summary(db: SessionDep, user: CurrentUser) -> ReportSummary:
    _require_view(user.role)
    return reports.summary(db)


@router.get("/funnel", response_model=FunnelReport)
def funnel(db: SessionDep, user: CurrentUser) -> FunnelReport:
    _require_view(user.role)
    return reports.funnel(db)


@router.get("/sources", response_model=list[SourceCount])
def sources(db: SessionDep, user: CurrentUser) -> list[SourceCount]:
    _require_view(user.role)
    return reports.sources(db)


@router.get("/drop-offs", response_model=list[DropOff])
def drop_offs(db: SessionDep, user: CurrentUser) -> list[DropOff]:
    _require_view(user.role)
    return reports.drop_offs(db)


@router.get("/time-to-fill", response_model=TimeToFillReport)
def time_to_fill(db: SessionDep, user: CurrentUser) -> TimeToFillReport:
    _require_view(user.role)
    return reports.time_to_fill(db)


@router.get("/recruiter-performance", response_model=list[RecruiterPerformance])
def recruiter_performance(db: SessionDep, user: CurrentUser) -> list[RecruiterPerformance]:
    _require_view(user.role)
    return reports.recruiter_performance(db)
