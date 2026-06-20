"""Department model — a SHAI operating unit that raises requisitions."""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import TimestampMixin


class Department(TimestampMixin, Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    # Plain integer (not a DB-level FK) to avoid a users<->departments FK cycle
    # that SQLite cannot satisfy via ALTER. Referential integrity is enforced in
    # the service layer when assigning a department head.
    head_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
