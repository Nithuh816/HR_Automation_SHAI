import os

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("APP_SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")


@pytest.fixture()
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_tables():
    """Create all tables on the (sqlite) test DB and tear them down after."""
    import app.models  # noqa: F401  -- populate Base.metadata
    from app.db import Base, engine

    Base.metadata.create_all(engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture()
def db(db_tables):
    from app.db import SessionLocal

    with SessionLocal() as session:
        yield session


@pytest.fixture()
def make_user(db):
    from app.models.enums import Role, Team
    from app.models.user import User

    def _make(email: str, role: Role, team: Team = Team.TA, name: str | None = None) -> User:
        user = User(email=email.lower(), name=name or email, role=role, team=team)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def make_dept(db):
    from app.models.department import Department

    def _make(name: str) -> Department:
        dept = Department(name=name)
        db.add(dept)
        db.commit()
        db.refresh(dept)
        return dept

    return _make


@pytest.fixture()
def auth_header():
    from app.auth.jwt import mint_access_token

    def _header(user_id: int) -> dict[str, str]:
        return {"Authorization": f"Bearer {mint_access_token(user_id)}"}

    return _header
