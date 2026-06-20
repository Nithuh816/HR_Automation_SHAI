"""Pipeline stage transitions for candidate applications."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.candidate import CandidateApplication
from app.models.enums import STAGE_ORDER, ApplicationStatus, Stage


def set_stage(app: CandidateApplication, stage: Stage) -> None:
    app.stage = stage
    app.stage_entered_at = datetime.now(UTC)


def advance(app: CandidateApplication) -> Stage:
    idx = STAGE_ORDER.index(app.stage)
    if idx + 1 >= len(STAGE_ORDER):
        raise ValueError("already at the final stage")
    set_stage(app, STAGE_ORDER[idx + 1])
    return app.stage


def reject(app: CandidateApplication, reason: str | None) -> None:
    app.status = ApplicationStatus.REJECTED
    app.rejection_stage = app.stage
    app.rejection_reason = reason
