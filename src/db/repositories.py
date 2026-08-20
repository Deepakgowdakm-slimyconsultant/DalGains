"""Typed CRUD: every function here takes and returns pydantic models
from src.core.schemas, never a SQLAlchemy row. This is the only module
outside src/db/ that's allowed to import src/db/models.py -- callers
(src/core/profiles.py, src/core/units.py, src/core/weight_log.py,
src/logging/store.py) call these functions and never see a *Row class.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select

from src.core.schemas import HouseholdUnit, MealLog, NutritionTotals, UserProfile, WeightEntry
from src.db.models import HouseholdUnitRow, MealLogRow, ProfileRow, WeightEntryRow
from src.db.session import get_session


def _as_utc(value: datetime) -> datetime:
    """SQLite's DateTime column has no real timezone storage -- it always
    hands back a naive datetime. Every timestamp this app writes is UTC
    (see src/logging/engine.py, src/core/units.py), so naive-on-read
    always means "this was UTC," never ambiguous."""
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)

# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------


def _profile_to_row(profile: UserProfile) -> ProfileRow:
    return ProfileRow(
        user_id=profile.user_id,
        name=profile.name,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        body_type=profile.body_type,
        activity_level=profile.activity_level,
        goal=profile.goal,
        target_body_fat_pct=profile.target_body_fat_pct,
        dietary_pattern=profile.dietary_pattern,
        eating_phase=profile.eating_phase,
        fasting_protocol=profile.fasting_protocol,
        fasting_window_start_hour=profile.fasting_window.start_hour if profile.fasting_window else None,
        fasting_window_end_hour=profile.fasting_window.end_hour if profile.fasting_window else None,
        medical_flags=list(profile.medical_flags),
    )


def _row_to_profile(row: ProfileRow) -> UserProfile:
    fasting_window = None
    if row.fasting_window_start_hour is not None and row.fasting_window_end_hour is not None:
        fasting_window = {"start_hour": row.fasting_window_start_hour, "end_hour": row.fasting_window_end_hour}
    return UserProfile(
        user_id=row.user_id,
        name=row.name,
        age=row.age,
        sex=row.sex,
        height_cm=row.height_cm,
        weight_kg=row.weight_kg,
        body_type=row.body_type,
        activity_level=row.activity_level,
        goal=row.goal,
        target_body_fat_pct=row.target_body_fat_pct,
        dietary_pattern=row.dietary_pattern,
        eating_phase=row.eating_phase,
        fasting_protocol=row.fasting_protocol,
        fasting_window=fasting_window,
        medical_flags=list(row.medical_flags),
    )


def save_profile(profile: UserProfile) -> UserProfile:
    with get_session() as session:
        existing = session.get(ProfileRow, profile.user_id)
        if existing is not None:
            session.delete(existing)
            session.flush()
        session.add(_profile_to_row(profile))
    return profile


def load_profile(user_id: str) -> Optional[UserProfile]:
    with get_session() as session:
        row = session.get(ProfileRow, user_id)
        return _row_to_profile(row) if row is not None else None


def delete_profile(user_id: str) -> None:
    with get_session() as session:
        row = session.get(ProfileRow, user_id)
        if row is None:
            raise FileNotFoundError(f"No profile for {user_id!r}")
        session.delete(row)


# ---------------------------------------------------------------------------
# Household units
# ---------------------------------------------------------------------------


def get_calibrations(user_id: str) -> dict[str, HouseholdUnit]:
    with get_session() as session:
        rows = session.scalars(select(HouseholdUnitRow).where(HouseholdUnitRow.user_id == user_id)).all()
        return {
            row.unit_name: HouseholdUnit(
                user_id=row.user_id,
                unit_name=row.unit_name,
                volume_ml=row.volume_ml,
                calibrated_at=_as_utc(row.calibrated_at),
                calibration_method=row.calibration_method,
            )
            for row in rows
        }


def save_calibration(unit: HouseholdUnit) -> HouseholdUnit:
    with get_session() as session:
        existing = session.scalar(
            select(HouseholdUnitRow).where(
                HouseholdUnitRow.user_id == unit.user_id, HouseholdUnitRow.unit_name == unit.unit_name
            )
        )
        if existing is not None:
            session.delete(existing)
            session.flush()
        session.add(
            HouseholdUnitRow(
                user_id=unit.user_id,
                unit_name=unit.unit_name,
                volume_ml=unit.volume_ml,
                calibrated_at=unit.calibrated_at,
                calibration_method=unit.calibration_method,
            )
        )
    return unit


# ---------------------------------------------------------------------------
# Weight log
# ---------------------------------------------------------------------------


def save_weight(entry: WeightEntry) -> WeightEntry:
    with get_session() as session:
        existing = session.scalar(
            select(WeightEntryRow).where(WeightEntryRow.user_id == entry.user_id, WeightEntryRow.date == entry.date)
        )
        if existing is not None:
            existing.weight_kg = entry.weight_kg
        else:
            session.add(WeightEntryRow(user_id=entry.user_id, date=entry.date, weight_kg=entry.weight_kg))
    return entry


def get_weight_log(user_id: str) -> dict[str, float]:
    with get_session() as session:
        rows = session.scalars(select(WeightEntryRow).where(WeightEntryRow.user_id == user_id)).all()
        return {row.date: row.weight_kg for row in rows}


# ---------------------------------------------------------------------------
# Meal logs
# ---------------------------------------------------------------------------


def _meal_log_to_row(meal_log: MealLog) -> MealLogRow:
    return MealLogRow(
        user_id=meal_log.user_id,
        log_id=meal_log.log_id,
        timestamp=meal_log.timestamp,
        entries=[entry.model_dump(mode="json") for entry in meal_log.entries],
        computed_totals=meal_log.computed_totals.model_dump(mode="json"),
        notes=meal_log.notes,
        tags=list(meal_log.tags),
    )


def _row_to_meal_log(row: MealLogRow) -> MealLog:
    return MealLog(
        log_id=row.log_id,
        user_id=row.user_id,
        timestamp=_as_utc(row.timestamp),
        entries=row.entries,
        computed_totals=NutritionTotals(**row.computed_totals),
        notes=row.notes,
        tags=list(row.tags),
    )


def save_meal_log(meal_log: MealLog) -> MealLog:
    with get_session() as session:
        existing = session.scalar(
            select(MealLogRow).where(MealLogRow.user_id == meal_log.user_id, MealLogRow.log_id == meal_log.log_id)
        )
        if existing is not None:
            session.delete(existing)
            session.flush()
        session.add(_meal_log_to_row(meal_log))
    return meal_log


def load_meal_log(user_id: str, log_id: str) -> Optional[MealLog]:
    with get_session() as session:
        row = session.scalar(select(MealLogRow).where(MealLogRow.user_id == user_id, MealLogRow.log_id == log_id))
        return _row_to_meal_log(row) if row is not None else None


def delete_meal_log(user_id: str, log_id: str) -> None:
    with get_session() as session:
        session.execute(delete(MealLogRow).where(MealLogRow.user_id == user_id, MealLogRow.log_id == log_id))


def list_meal_log_dates(user_id: str) -> list[str]:
    with get_session() as session:
        rows = session.scalars(
            select(MealLogRow.log_id).where(MealLogRow.user_id == user_id).order_by(MealLogRow.log_id.desc())
        ).all()
        return list(rows)
