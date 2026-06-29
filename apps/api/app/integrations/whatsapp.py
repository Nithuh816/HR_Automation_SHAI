"""WhatsApp Cloud API delivery.

A stub sender (logs only) is used until SHAI provides a WhatsApp Business phone
number id + access token, at which point the real HTTP sender is selected
automatically. Templates are pre-approved in Meta Business Manager.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


class WhatsAppError(RuntimeError):
    """Delivery failed; safe to retry."""


class WhatsAppSender(ABC):
    @abstractmethod
    def send(self, *, to: str, body: str) -> None: ...


class StubWhatsAppSender(WhatsAppSender):
    def send(self, *, to: str, body: str) -> None:
        log.info("whatsapp.stub.send", to=to)


class HttpWhatsAppSender(WhatsAppSender):
    def send(self, *, to: str, body: str) -> None:
        url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"
        try:
            resp = httpx.post(
                url,
                headers={"Authorization": f"Bearer {settings.whatsapp_access_token}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": body},
                },
                timeout=20.0,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise WhatsAppError(str(exc)) from exc


def get_whatsapp_sender() -> WhatsAppSender:
    if settings.whatsapp_phone_number_id and settings.whatsapp_access_token:
        return HttpWhatsAppSender()
    return StubWhatsAppSender()
