"""GreytHR onboarding integration.

v1 has a single operation: create an employee from an accepted offer. Until SHAI
provides API credentials (``GREYTHR_BASE_URL`` + ``GREYTHR_API_KEY``), a
deterministic *stub* adapter is used so the whole onboarding flow is exercisable
end-to-end locally. The real HTTP adapter is selected automatically once those
env vars are set — no code change required.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
import structlog

from app.config import settings

log = structlog.get_logger()


class GreytHRError(RuntimeError):
    """A GreytHR push failed. Transient failures are safe to retry."""


class GreytHRClient(ABC):
    @abstractmethod
    def create_employee(self, payload: dict[str, Any]) -> str:
        """Create (or upsert) an employee; return the GreytHR employee id."""


class StubGreytHRClient(GreytHRClient):
    """Offline adapter. Deterministic + idempotent: same application -> same id."""

    def create_employee(self, payload: dict[str, Any]) -> str:
        app_id = int(payload["application_id"])
        employee_id = f"GHR-STUB-{app_id:05d}"
        log.info("greythr.stub.create_employee", application_id=app_id, employee_id=employee_id)
        return employee_id


class HttpGreytHRClient(GreytHRClient):
    """Real adapter. Auth is per SHAI's GreytHR plan (bearer key shown here)."""

    def create_employee(self, payload: dict[str, Any]) -> str:
        url = settings.greythr_base_url.rstrip("/") + "/v2/employees"
        headers = {"Authorization": f"Bearer {settings.greythr_api_key}"}
        if settings.greythr_tenant:
            headers["X-Tenant"] = settings.greythr_tenant
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=20.0)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise GreytHRError(str(exc)) from exc
        data = resp.json()
        employee_id = data.get("employee_id") or data.get("id")
        if not employee_id:
            raise GreytHRError("GreytHR response did not include an employee id")
        return str(employee_id)


def get_greythr_client() -> GreytHRClient:
    """Real client when creds are configured, else the offline stub."""
    if settings.greythr_base_url and settings.greythr_api_key:
        return HttpGreytHRClient()
    return StubGreytHRClient()
