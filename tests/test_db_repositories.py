"""Round-trip tests for src/db/repositories.py -- every pydantic model
that crosses the SQLite boundary must come back exactly as it went in.
"""
from datetime import datetime, timezone

from src.core.schemas import FastingWindow, HouseholdUnit, LogEntry, MealLog, NutritionTotals, UserProfile, WeightEntry
from src.db import repositories


def _profile(**overrides) -> UserProfile:
    kwargs = dict(
        user_id="alice",
        name="Alice",
        age=28,
        sex="female",
        height_cm=165,
        weight_kg=60,
        body_type="mesomorph",
        activity_level="moderate",
        goal="maintain",
        dietary_pattern="vegetarian",
        eating_phase="maintenance",
    )
    kwargs.update(overrides)
    return UserProfile(**kwargs)


def test_profile_round_trips_exactly():
    original = _profile(fasting_protocol="16_8", fasting_window=FastingWindow(start_hour=8, end_hour=16), medical_flags=["diabetes"])
    repositories.save_profile(original)
    loaded = repositories.load_profile("alice")
    assert loaded == original


def test_profile_without_fasting_window_round_trips():
    original = _profile()
    repositories.save_profile(original)
    loaded = repositories.load_profile("alice")
    assert loaded.fasting_window is None
    assert loaded == original


def test_save_profile_overwrites_existing():
    repositories.save_profile(_profile(weight_kg=60))
    repositories.save_profile(_profile(weight_kg=62))
    assert repositories.load_profile("alice").weight_kg == 62


def test_load_profile_missing_returns_none():
    assert repositories.load_profile("nobody") is None


def test_delete_profile_removes_row():
    repositories.save_profile(_profile())
    repositories.delete_profile("alice")
    assert repositories.load_profile("alice") is None


def test_household_unit_round_trips():
    unit = HouseholdUnit(
        user_id="alice",
        unit_name="katori",
        volume_ml=180,
        calibrated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        calibration_method="measured",
    )
    repositories.save_calibration(unit)
    loaded = repositories.get_calibrations("alice")["katori"]
    assert loaded == unit


def test_household_unit_recalibration_overwrites():
    repositories.save_calibration(
        HouseholdUnit(user_id="alice", unit_name="tsp", volume_ml=5, calibrated_at=datetime.now(timezone.utc), calibration_method="estimated")
    )
    repositories.save_calibration(
        HouseholdUnit(user_id="alice", unit_name="tsp", volume_ml=6, calibrated_at=datetime.now(timezone.utc), calibration_method="measured")
    )
    calibrations = repositories.get_calibrations("alice")
    assert len(calibrations) == 1
    assert calibrations["tsp"].volume_ml == 6


def test_household_units_isolated_per_user():
    repositories.save_calibration(
        HouseholdUnit(user_id="alice", unit_name="katori", volume_ml=180, calibrated_at=datetime.now(timezone.utc), calibration_method="measured")
    )
    repositories.save_calibration(
        HouseholdUnit(user_id="bob", unit_name="katori", volume_ml=220, calibrated_at=datetime.now(timezone.utc), calibration_method="measured")
    )
    assert repositories.get_calibrations("alice")["katori"].volume_ml == 180
    assert repositories.get_calibrations("bob")["katori"].volume_ml == 220


def test_weight_entry_round_trips():
    repositories.save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    assert repositories.get_weight_log("alice") == {"2026-01-01": 65.5}


def test_weight_entry_upserts_same_date():
    repositories.save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    repositories.save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=66.0))
    assert repositories.get_weight_log("alice") == {"2026-01-01": 66.0}


def test_meal_log_round_trips_exactly():
    original = MealLog(
        log_id="2026-01-01",
        user_id="alice",
        timestamp=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        entries=[LogEntry(ingredient_id="B021", qty=100, unit="g", timestamp=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))],
        computed_totals=NutritionTotals(energy_kcal=100, protein_g=10, fat_g=2, carbs_g=15, fiber_g=3),
        notes="post-workout",
        tags=["diwali"],
    )
    repositories.save_meal_log(original)
    loaded = repositories.load_meal_log("alice", "2026-01-01")
    assert loaded == original


def test_meal_log_upsert_overwrites_same_day():
    base = dict(
        log_id="2026-01-01",
        user_id="alice",
        timestamp=datetime(2026, 1, 1, 12, tzinfo=timezone.utc),
        computed_totals=NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0),
    )
    repositories.save_meal_log(MealLog(entries=[LogEntry(ingredient_id="B021", qty=100, unit="g")], **base))
    repositories.save_meal_log(
        MealLog(entries=[LogEntry(ingredient_id="B021", qty=100, unit="g"), LogEntry(ingredient_id="T013", qty=10, unit="g")], **base)
    )
    loaded = repositories.load_meal_log("alice", "2026-01-01")
    assert len(loaded.entries) == 2


def test_meal_log_missing_returns_none():
    assert repositories.load_meal_log("alice", "2026-01-01") is None


def test_delete_meal_log():
    repositories.save_meal_log(
        MealLog(
            log_id="2026-01-01",
            user_id="alice",
            timestamp=datetime.now(timezone.utc),
            entries=[LogEntry(ingredient_id="B021", qty=100, unit="g")],
            computed_totals=NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0),
        )
    )
    repositories.delete_meal_log("alice", "2026-01-01")
    assert repositories.load_meal_log("alice", "2026-01-01") is None


def test_list_meal_log_dates_most_recent_first():
    for date in ["2026-01-01", "2026-01-03", "2026-01-02"]:
        repositories.save_meal_log(
            MealLog(
                log_id=date,
                user_id="alice",
                timestamp=datetime.now(timezone.utc),
                entries=[LogEntry(ingredient_id="B021", qty=100, unit="g")],
                computed_totals=NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0),
            )
        )
    assert repositories.list_meal_log_dates("alice") == ["2026-01-03", "2026-01-02", "2026-01-01"]


def test_list_meal_log_dates_empty_for_new_user():
    assert repositories.list_meal_log_dates("nobody") == []
