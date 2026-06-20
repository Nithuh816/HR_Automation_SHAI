"""Authentication routes.

- ``POST /dev-login`` — dev-only stub: mint a token for any seeded user.
- ``GET  /login``     — return the Microsoft authorization URL (M1b).
- ``GET  /callback``  — exchange an MS auth code, match a provisioned user (M1b).
- ``GET  /me``        — the current authenticated user.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.auth.jwt import mint_access_token
from app.auth.msal_client import authorization_url, exchange_code
from app.auth.service import get_user_by_email
from app.config import settings
from app.deps import CurrentUser, SessionDep
from app.schemas.auth import AuthUrlResponse, DevLoginRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/dev-login", response_model=TokenResponse)
def dev_login(payload: DevLoginRequest, db: SessionDep) -> TokenResponse:
    if settings.app_env == "production":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="dev login is disabled")
    user = get_user_by_email(db, payload.email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unknown or inactive user"
        )
    return TokenResponse(access_token=mint_access_token(user.id))


@router.get("/login", response_model=AuthUrlResponse)
def login() -> AuthUrlResponse:
    return AuthUrlResponse(authorization_url=authorization_url())


@router.get("/callback", response_model=TokenResponse)
def callback(code: str, db: SessionDep) -> TokenResponse:
    result = exchange_code(code)
    claims = result.get("id_token_claims", {})
    email = claims.get("preferred_username") or claims.get("email")
    oid = claims.get("oid")
    user = get_user_by_email(db, email) if email else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="this Microsoft account is not provisioned for the app",
        )
    if user.ms_oid is None and oid:
        user.ms_oid = oid
        db.commit()
    return TokenResponse(access_token=mint_access_token(user.id))


@router.get("/me", response_model=UserRead)
def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
