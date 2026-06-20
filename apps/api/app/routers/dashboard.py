"""Dashboard aggregates."""

from __future__ import annotations

from fastapi import APIRouter

from app.deps import CurrentUser, SessionDep
from app.schemas.requisition import RequisitionSummary
from app.services import requisitions as svc

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/requisitions", response_model=RequisitionSummary)
def requisition_summary(db: SessionDep, _: CurrentUser) -> RequisitionSummary:
    return RequisitionSummary.model_validate(svc.build_summary(db))
