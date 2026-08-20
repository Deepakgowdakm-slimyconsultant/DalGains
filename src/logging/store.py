"""Meal log persistence: backed by SQLite via src.db.repositories.

Public API (load_day/save_day/delete_day/list_dates) is unchanged from
the pre-Phase-5 JSON-per-day-file version -- engine.py, aggregation.py,
and category_breakdown.py needed no changes for this migration.

Every read goes through MealLog. A row that fails to validate is never
allowed to crash the caller -- load_day() returns a QuarantinedLog
instead, preserving the raw content and the error, same contract as the
JSON-file version (a "path" is still reported, now a synthetic
sqlite: locator rather than a filesystem path, since that's what a
human debugging a quarantined row needs to go find it).
"""
import json
from datetime import datetime, timezone
from typing import Optional, Union

from pydantic import ValidationError
from sqlalchemy import select

from src.core.schemas import MealLog, QuarantinedLog
from src.db import repositories
from src.db.models import MealLogRow
from src.db.session import get_session


def load_day(user_id: str, date: str) -> Union[MealLog, QuarantinedLog, None]:
    """Loads one day's log. None if no log exists yet for that date."""
    with get_session() as session:
        row = session.scalar(select(MealLogRow).where(MealLogRow.user_id == user_id, MealLogRow.log_id == date))
        if row is None:
            return None
        raw = {
            "log_id": row.log_id,
            "user_id": row.user_id,
            # SQLite's DateTime column always hands back a naive datetime
            # -- every timestamp this app writes is UTC, so naive-on-read
            # always means "this was UTC" (see repositories._as_utc).
            "timestamp": row.timestamp if row.timestamp.tzinfo else row.timestamp.replace(tzinfo=timezone.utc),
            "entries": row.entries,
            "computed_totals": row.computed_totals,
            "notes": row.notes,
            "tags": row.tags,
        }
        try:
            return MealLog(**raw)
        except ValidationError as exc:
            return QuarantinedLog(
                path=f"sqlite:meal_logs/{user_id}/{date}",
                raw_content=json.dumps(raw, default=str),
                error=str(exc),
                quarantined_at=datetime.now(timezone.utc),
            )


def save_day(meal_log: MealLog) -> str:
    """Persists a validated MealLog. Returns its sqlite: locator."""
    repositories.save_meal_log(meal_log)
    return f"sqlite:meal_logs/{meal_log.user_id}/{meal_log.log_id}"


def delete_day(user_id: str, date: str) -> None:
    """Removes a day's log entirely, if it exists."""
    repositories.delete_meal_log(user_id, date)


def list_dates(user_id: str) -> list[str]:
    """Every date (YYYY-MM-DD, most recent first) that has a log for
    this user -- quarantined or not; callers that only want real logs
    should filter with load_day(). Backs the History timeline's
    infinite scroll, which needs to know what dates exist before it can
    page through them.
    """
    return repositories.list_meal_log_dates(user_id)
