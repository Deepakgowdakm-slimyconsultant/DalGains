"""UserProfile persistence: backed by SQLite via src.db.repositories.

Public API (save_profile/load_profile/delete_profile) is unchanged from
the pre-Phase-5 JSON-file version -- callers (src/api/routes/profile.py,
src/logging/aggregation.py, src/logging/fasting_integration.py,
src/insights/engine.py) needed no changes for this migration.
"""
from typing import Optional

from src.core.schemas import UserProfile
from src.db import repositories


def save_profile(profile: UserProfile) -> UserProfile:
    return repositories.save_profile(profile)


def load_profile(user_id: str) -> Optional[UserProfile]:
    return repositories.load_profile(user_id)


def delete_profile(user_id: str) -> None:
    """Removes a persisted profile. Raises FileNotFoundError if it doesn't exist."""
    repositories.delete_profile(user_id)
