"""Invite-only admission control: business logic over src/auth/store.py's
Invitation persistence. Every function here is meant to be called only
from an admin-gated route (src/api/routes/auth.py's /admin/invitations
routes, via src/auth/dependencies.py's require_admin) -- this module
itself doesn't check who's calling, that's the route layer's job.
"""
from src.auth import store
from src.auth.schemas import Invitation


def invite(email: str, invited_by: str) -> Invitation:
    """Creates (or reactivates, if previously revoked) an invitation."""
    return store.create_invitation(email, invited_by)


def list_all() -> list[Invitation]:
    return store.list_invitations()


def revoke(email: str) -> Invitation:
    """Raises ValueError if there's no invitation for this email."""
    revoked = store.revoke_invitation(email)
    if revoked is None:
        raise ValueError(f"No invitation for {email!r}")
    return revoked


def mark_accepted(email: str) -> None:
    store.mark_invitation_accepted(email)


def is_invited(email: str) -> bool:
    """True if `email` may request a magic link -- has an active
    invitation, or is already a registered user (so re-inviting an
    existing user isn't required for them to keep logging in)."""
    invitation = store.get_invitation(email)
    if invitation is not None and invitation.is_active:
        return True
    return store.get_user_by_email(email) is not None
