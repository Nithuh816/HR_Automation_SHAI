"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr


class DevLoginRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUrlResponse(BaseModel):
    authorization_url: str
