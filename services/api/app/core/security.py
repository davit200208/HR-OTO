import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pyotp
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_token(user_id: uuid.UUID, session_id: uuid.UUID, token_type: str, expires: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "sid": str(session_id), "type": token_type,
               "iat": now, "exp": now + expires}
    settings = get_settings()
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str = "access") -> dict:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise ValueError("invalid token type")
    return payload


def new_refresh_secret() -> str:
    return secrets.token_urlsafe(48)


def new_mfa_secret() -> str:
    return pyotp.random_base32()


def verify_mfa(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
