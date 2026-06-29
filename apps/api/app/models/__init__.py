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
from app.models.audit import AuditLog
from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
    MagicLink,
)
from app.models.consent import Consent
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
    NotificationChannel,
    NotificationStatus,
    OfferStatus,
    OnboardingStatus,
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
from app.models.notification import Notification
from app.models.offer import Offer, OfferTemplate
from app.models.onboarding import OnboardingHandoff
from app.models.requisition import Requisition, RequisitionComment
from app.models.user import User

__all__ = [
    "ApplicationFormL1",
    "ApplicationStatus",
    "AssessmentAnswer",
    "AssessmentAttempt",
    "AssessmentTemplate",
    "AttemptStatus",
    "AuditLog",
    "Candidate",
    "CandidateApplication",
    "CandidateSource",
    "ChecklistType",
    "Consent",
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
    "Notification",
    "NotificationChannel",
    "NotificationStatus",
    "Offer",
    "OfferStatus",
    "OfferTemplate",
    "OnboardingHandoff",
    "OnboardingStatus",
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
