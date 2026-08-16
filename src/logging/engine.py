"""Meal logging engine: append/read/delete entries in a user's day-by-day log."""
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from src.core.schemas import Beverage, LogEntry, MealLog, NutritionTotals, QuarantinedLog, WeeklySummary
from src.logging import aggregation, store
from src.logging.fasting_integration import is_within_eating_window
from src.recipes.builder import create_recipe

_ZERO_TOTALS = NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0)


def log_entry(user_id: str, entry: LogEntry, when: Optional[datetime] = None) -> MealLog:
    """Appends `entry` to the user's log for `when`'s date (default: now).

    Stamps the entry with `when` and whether it falls inside the user's
    fasting eating window (never blocks the log, just flags it -- see
    src.logging.fasting_integration).
    """
    timestamp = when or datetime.now(timezone.utc)
    stamped_entry = entry.model_copy(
        update={
            "timestamp": timestamp,
            "outside_eating_window": not is_within_eating_window(user_id, timestamp),
        }
    )

    date_str = timestamp.date().isoformat()
    existing = store.load_day(user_id, date_str)
    if isinstance(existing, QuarantinedLog):
        raise ValueError(
            f"Cannot append to a quarantined log for {user_id!r} on {date_str}: {existing.error}"
        )

    entries = (existing.entries if existing else []) + [stamped_entry]
    draft = MealLog(
        log_id=date_str,
        user_id=user_id,
        timestamp=timestamp,
        entries=entries,
        computed_totals=_ZERO_TOTALS,
    )
    meal_log = draft.model_copy(update={"computed_totals": aggregation.daily_totals(draft)})
    store.save_day(meal_log)
    return meal_log


def log_recipe(
    user_id: str, recipe_id: str, servings: float, when: Optional[datetime] = None
) -> MealLog:
    """Convenience: log `servings` servings of a saved recipe."""
    return log_entry(user_id, LogEntry(recipe_id=recipe_id, qty=servings, unit="serving"), when=when)


def log_beverage(user_id: str, beverage: Beverage, when: Optional[datetime] = None) -> MealLog:
    """Convenience: persist an ad-hoc Beverage (src.recipes.beverages) and log 1 serving of it."""
    create_recipe(beverage)
    return log_entry(user_id, LogEntry(recipe_id=beverage.recipe_id, qty=1, unit="serving"), when=when)


def log_ingredient(
    user_id: str, ingredient_id: str, qty: float, unit: str, when: Optional[datetime] = None
) -> MealLog:
    """Convenience: log a raw ingredient quantity (e.g. "1 katori curd")."""
    return log_entry(
        user_id, LogEntry(ingredient_id=ingredient_id, qty=qty, unit=unit), when=when
    )


def delete_entry(user_id: str, log_id: str, entry_index: int) -> Optional[MealLog]:
    """Removes entries[entry_index] from the log_id (date) file and re-saves.

    Returns None if that was the day's last entry -- MealLog.entries
    requires at least one, so an emptied day's file is deleted rather than
    left as an unconstructable zero-entry log.
    """
    existing = store.load_day(user_id, log_id)
    if existing is None:
        raise FileNotFoundError(f"No log for {user_id!r} on {log_id!r}")
    if isinstance(existing, QuarantinedLog):
        raise ValueError(
            f"Cannot delete from a quarantined log for {user_id!r} on {log_id!r}: {existing.error}"
        )
    if not (0 <= entry_index < len(existing.entries)):
        raise IndexError(f"entry_index {entry_index} out of range for {user_id!r}/{log_id!r}")

    remaining = existing.entries[:entry_index] + existing.entries[entry_index + 1 :]
    if not remaining:
        store.delete_day(user_id, log_id)
        return None

    draft = existing.model_copy(update={"entries": remaining})
    meal_log = draft.model_copy(update={"computed_totals": aggregation.daily_totals(draft)})
    store.save_day(meal_log)
    return meal_log


def get_day(user_id: str, date: str) -> Union[MealLog, QuarantinedLog, None]:
    return store.load_day(user_id, date)


def tag_day(user_id: str, date: str, tag: str) -> MealLog:
    """Adds a free-form label (e.g. "diwali") to a day's log -- used by
    src/insights/engine.py's festival_flex rule. The day must already
    have at least one entry logged; MealLog has nothing to attach a tag
    to otherwise.
    """
    existing = store.load_day(user_id, date)
    if existing is None:
        raise FileNotFoundError(f"No log for {user_id!r} on {date!r} to tag")
    if isinstance(existing, QuarantinedLog):
        raise ValueError(f"Cannot tag a quarantined log for {user_id!r} on {date!r}: {existing.error}")

    if tag in existing.tags:
        return existing
    meal_log = existing.model_copy(update={"tags": existing.tags + [tag]})
    store.save_day(meal_log)
    return meal_log


def get_week(user_id: str, week_ending_date: str) -> WeeklySummary:
    return aggregation.weekly_totals(user_id, week_ending_date)


def get_range(user_id: str, start: str, end: str) -> list[Union[MealLog, QuarantinedLog]]:
    """All logs from `start` to `end` (both "YYYY-MM-DD", inclusive). Skips missing days."""
    start_d = date_cls.fromisoformat(start)
    end_d = date_cls.fromisoformat(end)

    results: list[Union[MealLog, QuarantinedLog]] = []
    d = start_d
    while d <= end_d:
        log = store.load_day(user_id, d.isoformat())
        if log is not None:
            results.append(log)
        d += timedelta(days=1)
    return results
