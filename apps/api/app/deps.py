from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db


def db_dep() -> Iterator[Session]:
    yield from get_db()


DB = Depends(db_dep)
