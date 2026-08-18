"""SQLAlchemy ORM models -- persistence only.

These mirror the pydantic schemas in src.core.schemas (and src.auth.models
for Phase 5's auth tables) but must never leak outside src/db/: every
caller gets and gives pydantic models, converted at the repositories.py
boundary. SQLAlchemy objects are an implementation detail of how those
pydantic models get to disk, not a second parallel data model callers
need to know about.

MealLog.entries/tags and NutritionTotals are stored as JSON columns
rather than fully normalized child tables. They're always read and
written as a whole unit (one day's log), never queried entry-by-entry,
so normalizing them would add join complexity for no real benefit --
this keeps the migration mechanical (one JSON file -> one row) and the
DB file still trivially inspectable with any SQLite browser.
"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProfileRow(Base):
    __tablename__ = "profiles"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    body_type: Mapped[str] = mapped_column(String, nullable=False)
    activity_level: Mapped[str] = mapped_column(String, nullable=False)
    goal: Mapped[str] = mapped_column(String, nullable=False)
    target_body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    dietary_pattern: Mapped[str] = mapped_column(String, nullable=False)
    eating_phase: Mapped[str] = mapped_column(String, nullable=False)
    fasting_protocol: Mapped[str] = mapped_column(String, nullable=False, default="none")
    # FastingWindow is a small nested object with no independent identity
    # -- flattened to two nullable columns rather than a child table.
    fasting_window_start_hour: Mapped[float | None] = mapped_column(Float, nullable=True)
    fasting_window_end_hour: Mapped[float | None] = mapped_column(Float, nullable=True)
    medical_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class HouseholdUnitRow(Base):
    __tablename__ = "household_units"
    __table_args__ = (UniqueConstraint("user_id", "unit_name", name="uq_household_unit_user_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    unit_name: Mapped[str] = mapped_column(String, nullable=False)
    volume_ml: Mapped[float] = mapped_column(Float, nullable=False)
    calibrated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    calibration_method: Mapped[str] = mapped_column(String, nullable=False)


class WeightEntryRow(Base):
    __tablename__ = "weight_entries"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_weight_entry_user_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    date: Mapped[str] = mapped_column(String, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)


class MealLogRow(Base):
    __tablename__ = "meal_logs"
    __table_args__ = (UniqueConstraint("user_id", "log_id", name="uq_meal_log_user_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    log_id: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    entries: Mapped[list] = mapped_column(JSON, nullable=False)
    computed_totals: Mapped[dict] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
