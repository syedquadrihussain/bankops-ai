import os
from datetime import datetime, timedelta, timezone

import jwt

ALGORITHM = "HS256"
TOKEN_MINUTES = 30
MIN_SECRET_LENGTH = 32


class AuthError(Exception):
    """Raised when a token is missing, invalid, or expired."""


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < MIN_SECRET_LENGTH:
        raise RuntimeError(
            "JWT_SECRET must be set and at least 32 characters long."
        )
    return secret


def create_access_token(username: str, role: str, minutes: int = TOKEN_MINUTES) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
    except jwt.PyJWTError:
        raise AuthError("Invalid or expired token.")
    return {"username": payload["sub"], "role": payload["role"]}
