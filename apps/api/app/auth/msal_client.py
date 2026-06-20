"""Microsoft Entra ID (Azure AD) auth-code helper.

Inert until ``MS_TENANT_ID`` / ``MS_CLIENT_ID`` / ``MS_CLIENT_SECRET`` are set
(M1b). Until then the dev-login stub in ``routers/auth.py`` is used instead.
"""

from __future__ import annotations

from typing import Any

import msal

from app.config import settings


def _client() -> msal.ConfidentialClientApplication:
    if not (settings.ms_tenant_id and settings.ms_client_id and settings.ms_client_secret):
        raise RuntimeError(
            "Microsoft SSO is not configured (set MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET)."
        )
    authority = f"https://login.microsoftonline.com/{settings.ms_tenant_id}"
    return msal.ConfidentialClientApplication(
        settings.ms_client_id,
        authority=authority,
        client_credential=settings.ms_client_secret,
    )


def authorization_url() -> str:
    url: str = _client().get_authorization_request_url(
        settings.ms_scopes.split(),
        redirect_uri=settings.ms_redirect_uri,
    )
    return url


def exchange_code(code: str) -> dict[str, Any]:
    result: dict[str, Any] = _client().acquire_token_by_authorization_code(
        code,
        scopes=settings.ms_scopes.split(),
        redirect_uri=settings.ms_redirect_uri,
    )
    if "error" in result:
        raise RuntimeError(str(result.get("error_description", "token exchange failed")))
    return result
