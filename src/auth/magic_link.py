"""Magic-link tokens: short-lived signed JWTs, not stored server-side --
verifying one is just checking the signature and expiry, no DB lookup
needed to know it's genuine (the DB lookup that follows is for invite/
account status, a separate question from "is this token real").
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from src.config import get_settings

_ALGORITHM = "HS256"
_PURPOSE = "magic_link"
MAGIC_LINK_EXPIRY = timedelta(hours=24)


def _secret() -> str:
    return get_settings().JWT_SECRET


def generate_link(email: str) -> str:
    """Returns a signed JWT proving "this email requested a login,
    within the last 24h" -- the caller turns this into a clickable URL
    (see src/api/routes/auth.py) and emails it."""
    payload = {
        "email": email,
        "purpose": _PURPOSE,
        "exp": datetime.now(timezone.utc) + MAGIC_LINK_EXPIRY,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def verify_link(token: str) -> str:
    """Returns the email a valid, unexpired magic-link token was issued
    for. Raises ValueError for anything else (expired, tampered,
    wrong purpose) -- callers turn that into a 400, never a 500."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=[_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"Invalid or expired magic link: {exc}") from exc
    if payload.get("purpose") != _PURPOSE:
        raise ValueError("Token is not a magic-link token")
    return payload["email"]
