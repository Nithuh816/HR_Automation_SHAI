"""Email delivery. Provider-agnostic so SHAI can use their own M365 SMTP.

- ``smtp``    — default; in dev it points at MailHog (captures everything).
- ``resend``  — Resend HTTP API (used when an API key is configured).
- ``console`` — logs only; used in tests and when no transport is wanted.
"""

from __future__ import annotations

import smtplib
from abc import ABC, abstractmethod
from email.message import EmailMessage

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


class EmailError(RuntimeError):
    """Delivery failed; safe to retry."""


class EmailSender(ABC):
    @abstractmethod
    def send(self, *, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailSender(EmailSender):
    def send(self, *, to: str, subject: str, body: str) -> None:
        log.info("email.console", to=to, subject=subject)


class SMTPEmailSender(EmailSender):
    def send(self, *, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = settings.email_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_username:
                    server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(msg)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailError(str(exc)) from exc


class ResendEmailSender(EmailSender):
    def send(self, *, to: str, subject: str, body: str) -> None:
        try:
            resp = httpx.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": settings.email_from, "to": [to], "subject": subject, "text": body},
                timeout=20.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmailError(str(exc)) from exc


def get_email_sender() -> EmailSender:
    if settings.email_provider == "console":
        return ConsoleEmailSender()
    if settings.email_provider == "resend" and settings.resend_api_key:
        return ResendEmailSender()
    return SMTPEmailSender()
