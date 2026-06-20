"""Requisition domain logic: codes, status transitions, summary."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import RequisitionStatus as RS
from app.models.enums import Urgency
from app.models.requisition import Requisition

# Allowed manual status transitions via the /status endpoint.
# Moving to ASSIGNED happens through /assign, not here.
ALLOWED_TRANSITIONS: dict[RS, set[RS]] = {
    RS.DRAFT: {RS.SUBMITTED, RS.CANCELLED},
    RS.SUBMITTED: {RS.ON_HOLD, RS.CANCELLED},
    RS.ASSIGNED: {RS.ON_HOLD, RS.FILLED, RS.CANCELLED, RS.SUBMITTED},
    RS.ON_HOLD: {RS.SUBMITTED, RS.CANCELLED},
    RS.FILLED: set(),
    RS.CANCELLED: set(),
}

OPEN_STATUSES = (RS.SUBMITTED, RS.ASSIGNED, RS.ON_HOLD)


def can_transition(current: RS, target: RS) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def make_code(req_id: int) -> str:
    return f"REQ-{req_id:05d}"


def build_summary(db: Session) -> dict[str, object]:
    counts: dict[RS, int] = {
        row[0]: int(row[1])
        for row in db.execute(
            select(Requisition.status, func.count()).group_by(Requisition.status)
        ).all()
    }
    by_status = {s: counts.get(s, 0) for s in RS}

    open_headcount = (
        db.scalar(
            select(func.coalesce(func.sum(Requisition.headcount), 0)).where(
                Requisition.status.in_(OPEN_STATUSES)
            )
        )
        or 0
    )

    urgency_counts: dict[Urgency, int] = {
        row[0]: int(row[1])
        for row in db.execute(
            select(Requisition.urgency, func.count())
            .where(Requisition.status.in_(OPEN_STATUSES))
            .group_by(Requisition.urgency)
        ).all()
    }

    return {
        "total": sum(by_status.values()),
        "submitted": by_status[RS.SUBMITTED],
        "assigned": by_status[RS.ASSIGNED],
        "on_hold": by_status[RS.ON_HOLD],
        "filled": by_status[RS.FILLED],
        "cancelled": by_status[RS.CANCELLED],
        "open_headcount": int(open_headcount),
        "by_urgency": {u: int(urgency_counts.get(u, 0)) for u in Urgency},
    }
