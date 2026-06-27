"""Microsoft Graph integration — Teams online meetings.

Real Graph calls require the Entra ID app registration wired in M1b
(``ms_client_id`` / ``ms_client_secret`` / ``ms_tenant_id``). Until those creds
exist we run in *stub* mode: a deterministic-looking join URL is generated
locally so the rest of the interview flow (scheduling, scorecards) works
end-to-end. Swap ``_real_meeting`` in once creds land — the call site does not
change.
"""

from __future__ import annotations

import secrets
from datetime import datetime

import structlog

from app.config import settings

log = structlog.get_logger()


def graph_configured() -> bool:
    """True once the Entra ID app credentials are present (M1b)."""
    return bool(settings.ms_client_id and settings.ms_client_secret and settings.ms_tenant_id)


def _stub_meeting(subject: str) -> str:
    token = secrets.token_urlsafe(18)
    log.info("graph.teams_meeting.stub", subject=subject)
    return f"https://teams.microsoft.com/l/meetup-join/stub/{token}"


def create_teams_meeting(subject: str, start: datetime, duration_minutes: int) -> str:
    """Create a Teams online meeting and return its join URL.

    Falls back to a stub URL when Graph is not yet configured.
    """
    if not graph_configured():
        return _stub_meeting(subject)
    # Real implementation lands with M1b creds:
    #   POST https://graph.microsoft.com/v1.0/me/onlineMeetings
    #   { subject, startDateTime, endDateTime } -> response["joinWebUrl"]
    return _stub_meeting(subject)  # pragma: no cover  — until creds exist
