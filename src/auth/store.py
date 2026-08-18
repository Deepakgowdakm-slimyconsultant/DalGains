"""User/Invitation persistence -- the src.auth equivalent of
src.db.repositories: typed CRUD in, pydantic models out, never a
SQLAlchemy row leaking past this module.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from src.auth.models import InvitationRow, UserRow
from src.auth.schemas import Invitation, User
from src.db.session import get_session


def _as_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _row_to_user(row: UserRow) -> User:
    return User(id=row.id, email=row.email, is_admin=row.is_admin, created_at=_as_utc(row.created_at))


def get_user_by_id(user_id: str) -> Optional[User]:
    with get_session() as session:
        row = session.get(UserRow, user_id)
        return _row_to_user(row) if row is not None else None


def get_user_by_email(email: str) -> Optional[User]:
    with get_session() as session:
        row = session.scalar(select(UserRow).where(UserRow.email == email))
        return _row_to_user(row) if row is not None else None


def create_user(user_id: str, email: str, is_admin: bool = False) -> User:
    user = User(id=user_id, email=email, is_admin=is_admin, created_at=datetime.now(timezone.utc))
    with get_session() as session:
        session.add(UserRow(id=user.id, email=user.email, is_admin=user.is_admin, created_at=user.created_at))
    return user


def _row_to_invitation(row: InvitationRow) -> Invitation:
    return Invitation(
        email=row.email,
        invited_by=row.invited_by,
        created_at=_as_utc(row.created_at),
        accepted_at=_as_utc(row.accepted_at) if row.accepted_at else None,
        revoked_at=_as_utc(row.revoked_at) if row.revoked_at else None,
    )


def get_invitation(email: str) -> Optional[Invitation]:
    with get_session() as session:
        row = session.scalar(select(InvitationRow).where(InvitationRow.email == email))
        return _row_to_invitation(row) if row is not None else None


def create_invitation(email: str, invited_by: str) -> Invitation:
    with get_session() as session:
        existing = session.scalar(select(InvitationRow).where(InvitationRow.email == email))
        if existing is not None:
            existing.revoked_at = None  # re-inviting a revoked email reactivates it
            session.flush()
            return _row_to_invitation(existing)
        row = InvitationRow(email=email, invited_by=invited_by, created_at=datetime.now(timezone.utc))
        session.add(row)
        session.flush()
        return _row_to_invitation(row)


def list_invitations() -> list[Invitation]:
    with get_session() as session:
        rows = session.scalars(select(InvitationRow).order_by(InvitationRow.created_at.desc())).all()
        return [_row_to_invitation(row) for row in rows]


def revoke_invitation(email: str) -> Optional[Invitation]:
    with get_session() as session:
        row = session.scalar(select(InvitationRow).where(InvitationRow.email == email))
        if row is None:
            return None
        row.revoked_at = datetime.now(timezone.utc)
        session.flush()
        return _row_to_invitation(row)


def mark_invitation_accepted(email: str) -> None:
    with get_session() as session:
        row = session.scalar(select(InvitationRow).where(InvitationRow.email == email))
        if row is not None and row.accepted_at is None:
            row.accepted_at = datetime.now(timezone.utc)
