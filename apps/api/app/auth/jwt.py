"""Mint and verify our own short-lived access tokens.

Regardless of how a user authenticates (dev stub or Microsoft SSO), the rest of
the app only ever sees one of these JWTs. Swapping the identity provider does not
touch token verification or any route.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_TTL = timedelta(hours=8)


def mint_access_token(user_id: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TOKEN_TTL).timestamp()),
    }
    return jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int:
    """Return the user id encoded in ``token`` or raise ``ValueError``."""
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("invalid token") from exc
    sub = payload.get("sub")
    if sub is None:
        raise ValueError("token missing subject")
    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid subject") from exc
