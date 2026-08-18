"""JSON-per-day-per-user meal log persistence.

Chosen over SQLite for now because it stays inspectable/editable by hand
and matches the rest of DalGains' file-first philosophy (recipes,
ingredient overrides, household-unit calibrations are all flat JSON/
parquet under data/); it can be migrated to SQLite later without
changing the engine.py/aggregation.py API if a future phase needs it.

Every read goes through MealLog. A log file that fails to parse or
validate is never allowed to crash the caller -- load_day() returns a
QuarantinedLog instead, preserving the raw content and the error.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from pydantic import ValidationError

from src.core.schemas import MealLog, QuarantinedLog

LOGS_DIR = Path(__file__).resolve().parents[2] / "data" / "logs"


def _log_path(user_id: str, date: str) -> Path:
    return LOGS_DIR / user_id / f"{date}.json"


def load_day(user_id: str, date: str) -> Union[MealLog, QuarantinedLog, None]:
    """Loads one day's log. None if no log exists yet for that date."""
    path = _log_path(user_id, date)
    if not path.exists():
        return None

    raw_content = path.read_text()
    try:
        data = json.loads(raw_content)
        if not isinstance(data, dict):
            raise ValueError(f"Expected a JSON object, got {type(data).__name__}")
        return MealLog(**data)
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
        return QuarantinedLog(
            path=str(path),
            raw_content=raw_content,
            error=str(exc),
            quarantined_at=datetime.now(timezone.utc),
        )


def save_day(meal_log: MealLog) -> Path:
    """Persists a validated MealLog to data/logs/{user_id}/{log_id}.json."""
    path = _log_path(meal_log.user_id, meal_log.log_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(meal_log.model_dump_json(indent=2))
    return path


def delete_day(user_id: str, date: str) -> None:
    """Removes a day's log file entirely, if it exists."""
    path = _log_path(user_id, date)
    if path.exists():
        path.unlink()


def list_dates(user_id: str) -> list[str]:
    """Every date (YYYY-MM-DD, most recent first) that has a log file for
    this user -- quarantined or not; callers that only want real logs
    should filter with load_day(). Backs the History timeline's
    infinite scroll, which needs to know what dates exist before it can
    page through them.
    """
    user_dir = LOGS_DIR / user_id
    if not user_dir.exists():
        return []
    return sorted((p.stem for p in user_dir.glob("*.json")), reverse=True)
