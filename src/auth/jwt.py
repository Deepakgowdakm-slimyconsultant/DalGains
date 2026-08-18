"""Session JWTs: what actually authenticates a logged-in request, via
an httpOnly cookie (never readable by frontend JS -- XSS on the SPA
can't steal it). Distinct from magic_link.py's short-lived,
single-purpose login tokens; this is the longer-lived "you're logged
in" credential.
"""
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

_ALGORITHM = "HS256"
_PURPOSE = "session"
SESSION_EXPIRY = timedelta(days=7)
SESSION_COOKIE_NAME = "dalgains_session"

_DEV_INSECURE_SECRET = "dev-insecure-secret-do-not-use-in-production"


def _secret() -> str:
    return os.environ.get("JWT_SECRET", _DEV_INSECURE_SECRET)


def create_session_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "purpose": _PURPOSE,
        "exp": datetime.now(timezone.utc) + SESSION_EXPIRY,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def verify_session_token(token: str) -> str:
    """Returns the user_id a valid, unexpired session token was issued
    for. Raises ValueError for anything else."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid or expired session: {exc}") from exc
    if payload.get("purpose") != _PURPOSE:
        raise ValueError("Token is not a session token")
    return payload["sub"]
