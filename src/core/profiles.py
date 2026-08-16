"""UserProfile persistence: one JSON file per user under data/users/.

Mirrors src.core.units' calibration storage convention (flat, inspectable
JSON under data/users/{user_id}/). Needed by src/logging/aggregation.py's
target-adherence calculations, which have to look up a user's calorie
target by user_id alone; src/api/routes/profile.py (Part E) is a thin
CRUD wrapper over these same two functions.
"""
import json
from pathlib import Path
from typing import Optional

from src.core.schemas import UserProfile

USERS_DIR = Path(__file__).resolve().parents[2] / "data" / "users"


def _profile_path(user_id: str) -> Path:
    return USERS_DIR / user_id / "profile.json"


def save_profile(profile: UserProfile) -> Path:
    path = _profile_path(profile.user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=2))
    return path


def load_profile(user_id: str) -> Optional[UserProfile]:
    path = _profile_path(user_id)
    if not path.exists():
        return None
    return UserProfile(**json.loads(path.read_text()))


def delete_profile(user_id: str) -> None:
    """Removes a persisted profile. Raises FileNotFoundError if it doesn't exist."""
    path = _profile_path(user_id)
    if not path.exists():
        raise FileNotFoundError(f"No profile for {user_id!r}")
    path.unlink()
