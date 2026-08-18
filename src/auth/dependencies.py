"""FastAPI auth dependencies.

require_own_user is the one every route with a {user_id} path param
must use (replace `user_id: str` with `user_id: str = Depends(require_own_user)`)
-- FastAPI resolves a dependency's own path-parameter-shaped argument
from the same path parameter automatically, so this is a drop-in
per-route change, not a rewrite. Without it, any authenticated user
could read or write another user's logs/profile/calibrations by
guessing or enumerating IDs in the URL.
"""
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status

from src.auth import store
from src.auth.jwt import SESSION_COOKIE_NAME, verify_session_token
from src.auth.schemas import User


def get_current_user(
    session_token: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        user_id = verify_session_token(session_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    user = store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


def require_own_user(user_id: str, current_user: User = Depends(get_current_user)) -> str:
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another user's data")
    return user_id
