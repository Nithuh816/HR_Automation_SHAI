"""Field-level encryption helpers for PII columns (Aadhaar, PAN, bank accounts).

Uses Fernet (AES-128-CBC + HMAC-SHA256) keyed by ``settings.pii_enc_key``.
Encrypted values are stored as the Fernet token string (URL-safe base64).
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _cipher() -> Fernet:
    key = settings.pii_enc_key
    if not key:
        raise RuntimeError(
            "PII_ENC_KEY is not set. Generate one with:\n"
            '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str | None) -> str | None:
    if plaintext is None or plaintext == "":
        return plaintext
    return _cipher().encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt(token: str | None) -> str | None:
    if token is None or token == "":
        return token
    try:
        return _cipher().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("invalid or tampered PII token") from exc
