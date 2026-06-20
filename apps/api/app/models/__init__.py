"""ORM models package.

Every model must be imported here so that ``Base.metadata`` is fully populated
for Alembic autogenerate and ``create_all`` (tests).
"""

from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
    MagicLink,
)
from app.models.department import Department
from app.models.enums import (
    ApplicationStatus,
    CandidateSource,
    MagicLinkScope,
    RequisitionStatus,
    Role,
    Stage,
    Team,
    Urgency,
)
from app.models.requisition import Requisition, RequisitionComment
from app.models.user import User

__all__ = [
    "ApplicationFormL1",
    "ApplicationStatus",
    "Candidate",
    "CandidateApplication",
    "CandidateSource",
    "Department",
    "MagicLink",
    "MagicLinkScope",
    "Requisition",
    "RequisitionComment",
    "RequisitionStatus",
    "Role",
    "Stage",
    "Team",
    "Urgency",
    "User",
]
