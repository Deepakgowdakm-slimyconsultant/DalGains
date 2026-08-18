"""Optional daily weight logging: one flat JSON dict per user, mapping
"YYYY-MM-DD" -> weight_kg. Same data/users/{user_id}/ convention as
src.core.profiles and src.core.units. Logging weight is entirely
opt-in -- History's weight trend chart just shows nothing for a user
who never calls save_weight.
"""
import json
from pathlib import Path

from src.core.schemas import WeightEntry

USERS_DIR = Path(__file__).resolve().parents[2] / "data" / "users"


def _weight_log_path(user_id: str) -> Path:
    return USERS_DIR / user_id / "weight_log.json"


def save_weight(entry: WeightEntry) -> WeightEntry:
    path = _weight_log_path(entry.user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(path.read_text()) if path.exists() else {}
    existing[entry.date] = entry.weight_kg
    path.write_text(json.dumps(existing, indent=2))
    return entry


def get_weight_log(user_id: str) -> dict[str, float]:
    """All of a user's logged weights, keyed by date. Empty dict if
    they've never logged one."""
    path = _weight_log_path(user_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text())
