"""ORM models package.

Every model must be imported here so that ``Base.metadata`` is fully populated
for Alembic autogenerate and ``create_all`` (tests).
"""

from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTemplate,
    Question,
    TemplateQuestion,
)
from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
    MagicLink,
)
from app.models.department import Department
from app.models.document import Document, DocumentChecklist
from app.models.enums import (
    ApplicationStatus,
    AttemptStatus,
    CandidateSource,
    ChecklistType,
    DocumentStatus,
    DocumentType,
    InterviewMode,
    InterviewRound,
    InterviewStatus,
    MagicLinkScope,
    OfferStatus,
    RequisitionStatus,
    Role,
    ScorecardDecision,
    Stage,
    Team,
    Urgency,
)
from app.models.interview import (
    Interview,
    RubricCriterion,
    RubricTemplate,
    Scorecard,
    ScorecardScore,
)
from app.models.offer import Offer, OfferTemplate
from app.models.requisition import Requisition, RequisitionComment
from app.models.user import User

__all__ = [
    "ApplicationFormL1",
    "ApplicationStatus",
    "AssessmentAnswer",
    "AssessmentAttempt",
    "AssessmentTemplate",
    "AttemptStatus",
    "Candidate",
    "CandidateApplication",
    "CandidateSource",
    "ChecklistType",
    "Department",
    "Document",
    "DocumentChecklist",
    "DocumentStatus",
    "DocumentType",
    "Interview",
    "InterviewMode",
    "InterviewRound",
    "InterviewStatus",
    "MagicLink",
    "MagicLinkScope",
    "Offer",
    "OfferStatus",
    "OfferTemplate",
    "Question",
    "Requisition",
    "RequisitionComment",
    "RequisitionStatus",
    "Role",
    "RubricCriterion",
    "RubricTemplate",
    "Scorecard",
    "ScorecardDecision",
    "ScorecardScore",
    "Stage",
    "Team",
    "TemplateQuestion",
    "Urgency",
    "User",
]
