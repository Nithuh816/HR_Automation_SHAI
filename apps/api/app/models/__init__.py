"""ORM models package.

Every model must be imported here so that ``Base.metadata`` is fully populated
for Alembic autogenerate and ``create_all`` (tests).
"""

from app.models.department import Department
from app.models.enums import Role, Team
from app.models.user import User

__all__ = ["Department", "Role", "Team", "User"]
