"""Optional daily weight logging, backed by SQLite via src.db.repositories
(one row per user per date). Logging weight is entirely opt-in -- History's
weight trend chart just shows nothing for a user who never calls save_weight.
"""
from src.core.schemas import WeightEntry
from src.db import repositories


def save_weight(entry: WeightEntry) -> WeightEntry:
    return repositories.save_weight(entry)


def get_weight_log(user_id: str) -> dict[str, float]:
    """All of a user's logged weights, keyed by date. Empty dict if
    they've never logged one."""
    return repositories.get_weight_log(user_id)
