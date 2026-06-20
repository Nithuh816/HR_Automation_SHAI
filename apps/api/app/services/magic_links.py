"""Magic-link tokens for candidate-facing pages (no account).

A 32-byte URL-safe token is handed to the candidate; only its HMAC-SHA256
digest is stored, so a leaked DB row cannot reconstruct a usable link. Links are
scoped, time-boxed, and single-use.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.candidate import MagicLink
from app.models.enums import MagicLinkScope


def _digest(token: str) -> str:
    return hmac.new(
        settings.magic_link_hmac_key.encode(), token.encode(), hashlib.sha256
    ).hexdigest()


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def create_link(
    db: Session, scope: MagicLinkScope, application_id: int, ttl: timedelta
) -> tuple[str, MagicLink]:
    token = secrets.token_urlsafe(32)
    link = MagicLink(
        token_hash=_digest(token),
        scope=scope,
        application_id=application_id,
        expires_at=datetime.now(UTC) + ttl,
    )
    db.add(link)
    db.flush()
    return token, link


def verify(db: Session, token: str, scope: MagicLinkScope) -> MagicLink:
    """Return the link for ``token`` or raise ``ValueError``."""
    link = db.scalar(select(MagicLink).where(MagicLink.token_hash == _digest(token)))
    if link is None or link.scope != scope:
        raise ValueError("invalid link")
    if link.used_at is not None:
        raise ValueError("this link has already been used")
    if _aware(link.expires_at) < datetime.now(UTC):
        raise ValueError("this link has expired")
    return link


def consume(link: MagicLink) -> None:
    link.used_at = datetime.now(UTC)


def build_url(token: str, path: str) -> str:
    """e.g. build_url(tok, 'apply') -> '<magic_link_base_url>/apply/<tok>'."""
    return f"{settings.magic_link_base_url.rstrip('/')}/{path}/{token}"
