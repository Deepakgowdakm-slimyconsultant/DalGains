"""Pydantic models for auth entities -- same validate-at-the-boundary
rule as src.core.schemas: never touch a UserRow/InvitationRow field
directly outside src/auth/store.py.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    id: str = Field(min_length=1)
    email: EmailStr
    is_admin: bool = False
    created_at: datetime


class Invitation(BaseModel):
    email: EmailStr
    invited_by: str = Field(min_length=1)
    created_at: datetime
    accepted_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
