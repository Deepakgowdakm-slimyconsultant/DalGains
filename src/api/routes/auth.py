"""Magic-link auth routes: request a link, verify it, log out, check
who's logged in -- plus admin-only invitation management.
"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from src.auth import invitation, store
from src.auth.dependencies import get_current_user, require_admin
from src.auth.email import send_magic_link
from src.auth.jwt import SESSION_COOKIE_NAME, SESSION_EXPIRY, create_session_token
from src.auth.magic_link import generate_link, verify_link
from src.auth.schemas import Invitation, User

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _app_url() -> str:
    return os.environ.get("APP_URL", "http://localhost:5173")


def _is_prod() -> bool:
    return os.environ.get("ENVIRONMENT", "dev") == "prod"


def _cookie_samesite() -> str:
    # Vercel (frontend) and HF Spaces (backend) are two different sites,
    # so the browser's fetch() calls from the SPA to the API are
    # cross-site requests -- SameSite=Lax cookies are withheld from
    # those (Lax only rides along on top-level navigations, which is
    # all local dev needs since both run on localhost). Production
    # needs SameSite=None, which browsers require pairing with Secure.
    # This is a deliberate deviation from a literal "sameSite=lax
    # always" reading of the brief: that setting would leave auth
    # silently broken the moment frontend and backend are on different
    # domains, which is exactly this deployment's shape.
    return "none" if _is_prod() else "lax"


def _set_session_cookie(response: Response, user_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user_id),
        httponly=True,
        secure=_is_prod(),
        samesite=_cookie_samesite(),
        max_age=int(SESSION_EXPIRY.total_seconds()),
    )


class RequestLinkBody(BaseModel):
    email: EmailStr


@router.post("/request-link", status_code=status.HTTP_200_OK)
def request_link(body: RequestLinkBody, request: Request) -> dict:
    """Always returns 200, whether or not the email is invited -- an
    attacker probing this endpoint learns nothing about who has an
    account or an invitation (no account-enumeration leak).

    The link points at *this API's own* /auth/verify -- not the
    frontend's URL -- since that's the route that actually exists and
    sets the cookie. request.base_url (not APP_URL) builds it, so this
    works correctly regardless of the API's own deployed domain without
    needing a second env var just to describe it to itself. APP_URL is
    used separately, only for where /auth/verify redirects *to* once
    the cookie is set.
    """
    email = body.email.lower()
    if invitation.is_invited(email):
        link = f"{str(request.base_url).rstrip('/')}/auth/verify?token={generate_link(email)}"
        send_magic_link(email, link)
    return {"detail": "If that email is invited, a sign-in link has been sent."}


@router.get("/verify")
def verify(token: str) -> RedirectResponse:
    try:
        email = verify_link(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not invitation.is_invited(email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This email is not invited")

    user = store.get_user_by_email(email)
    if user is None:
        is_admin = email == os.environ.get("ADMIN_EMAIL", "").lower()
        user = store.create_user(user_id=str(uuid.uuid4()), email=email, is_admin=is_admin)
        invitation.mark_accepted(email)

    response = RedirectResponse(url=f"{_app_url()}/", status_code=status.HTTP_302_FOUND)
    _set_session_cookie(response, user.id)
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # Attributes must match how the cookie was originally set
    # (_set_session_cookie) -- a mismatched samesite/secure/path makes
    # some clients treat this as a different cookie instead of an
    # override, leaving the real session cookie in place.
    response.delete_cookie(SESSION_COOKIE_NAME, httponly=True, secure=_is_prod(), samesite=_cookie_samesite())


@router.get("/me", response_model=User)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


class InviteBody(BaseModel):
    email: EmailStr


@admin_router.post("/invitations", response_model=Invitation, status_code=status.HTTP_201_CREATED)
def create_invitation(body: InviteBody, current_user: User = Depends(require_admin)) -> Invitation:
    return invitation.invite(body.email.lower(), invited_by=current_user.email)


@admin_router.get("/invitations", response_model=list[Invitation])
def list_invitations(current_user: User = Depends(require_admin)) -> list[Invitation]:
    return invitation.list_all()


@admin_router.delete("/invitations/{email}", response_model=Invitation)
def revoke_invitation(email: str, current_user: User = Depends(require_admin)) -> Invitation:
    try:
        return invitation.revoke(email.lower())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
