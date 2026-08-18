from datetime import datetime, timedelta, timezone

import pytest

import src.core.profiles as profiles
import src.core.units as units
import src.logging.store as store
import src.recipes.builder as builder
from src.core.schemas import LogEntry, UserProfile
from src.logging import engine
from src.logging.aggregation import daily_totals, streak, target_adherence, weekly_totals
from src.logging.fasting_integration import is_within_eating_window


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(profiles, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")


def _profile(**overrides):
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


def _dt(date_str: str, hour: int = 12) -> datetime:
    return datetime.fromisoformat(f"{date_str}T{hour:02d}:00:00+00:00")


# --- store.py: quarantine on corruption ------------------------------------


def test_load_day_returns_none_for_missing_file():
    assert store.load_day("alice", "2026-01-01") is None


def test_load_day_quarantines_malformed_json():
    path = store._log_path("alice", "2026-01-01")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")

    result = store.load_day("alice", "2026-01-01")
    assert result.__class__.__name__ == "QuarantinedLog"
    assert "not valid json" in result.raw_content


def test_load_day_quarantines_schema_invalid_json():
    path = store._log_path("alice", "2026-01-01")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"log_id": "2026-01-01", "user_id": "alice"}')

    result = store.load_day("alice", "2026-01-01")
    assert result.__class__.__name__ == "QuarantinedLog"
    assert "validation error" in result.error.lower()


# --- engine.py: log_entry / convenience wrappers ---------------------------


def test_log_ingredient_creates_a_day_log():
    log = engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    assert log.log_id == "2026-01-01"
    assert len(log.entries) == 1
    assert log.computed_totals.energy_kcal > 0


def test_log_entry_accumulates_across_multiple_calls():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    second = engine.log_ingredient("alice", "T013", 10, "g", when=_dt("2026-01-01", hour=19))
    assert len(second.entries) == 2


def test_log_recipe_convenience(monkeypatch):
    # load_recipe reads from the real RECIPES_DIR (seeded dishes are
    # committed, not test fixtures) -- fine to hit directly here.
    log = engine.log_recipe("alice", "dal_tadka_north", servings=1, when=_dt("2026-01-01"))
    assert log.entries[0].recipe_id == "dal_tadka_north"
    assert log.entries[0].unit == "serving"


def test_log_beverage_convenience(tmp_path, monkeypatch):
    from src.recipes import beverages as bev

    # log_beverage persists the ad-hoc Beverage via create_recipe(), which
    # writes through builder.RECIPES_DIR -- isolate it here so this test
    # doesn't pollute the real data/recipes/ directory with a uuid-named
    # chai file.
    monkeypatch.setattr(builder, "RECIPES_DIR", tmp_path / "recipes")

    chai = bev.build_chai(milk_ml=60, milk_type="toned", sugar_tsp=1, size_ml=150)
    log = engine.log_beverage("alice", chai, when=_dt("2026-01-01"))
    assert log.entries[0].recipe_id == chai.recipe_id
    assert log.computed_totals.energy_kcal > 0


# --- engine.py: delete_entry -------------------------------------------


def test_delete_entry_removes_and_recomputes_totals():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "T013", 10, "g", when=_dt("2026-01-01", hour=19))

    after = engine.delete_entry("alice", "2026-01-01", 0)
    assert len(after.entries) == 1
    assert after.entries[0].ingredient_id == "T013"


def test_delete_last_entry_removes_the_file():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    result = engine.delete_entry("alice", "2026-01-01", 0)
    assert result is None
    assert engine.get_day("alice", "2026-01-01") is None


def test_delete_entry_missing_day_raises():
    with pytest.raises(FileNotFoundError):
        engine.delete_entry("alice", "2026-01-01", 0)


def test_delete_entry_out_of_range_raises():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    with pytest.raises(IndexError):
        engine.delete_entry("alice", "2026-01-01", 5)


def test_delete_entry_on_quarantined_day_raises():
    path = store._log_path("alice", "2026-01-01")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(ValueError):
        engine.delete_entry("alice", "2026-01-01", 0)


def test_log_entry_on_quarantined_day_raises():
    path = store._log_path("alice", "2026-01-01")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    with pytest.raises(ValueError):
        engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))


# --- engine.py: get_day / get_range / get_week -----------------------------


def test_get_day_returns_none_for_missing_day():
    assert engine.get_day("alice", "2026-01-01") is None


def test_get_range_skips_missing_days():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-03"))

    results = engine.get_range("alice", "2026-01-01", "2026-01-03")
    assert len(results) == 2
    assert {r.log_id for r in results} == {"2026-01-01", "2026-01-03"}


def test_list_logged_dates_most_recent_first():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-03"))
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-02"))

    assert engine.list_logged_dates("alice") == ["2026-01-03", "2026-01-02", "2026-01-01"]


def test_list_logged_dates_empty_for_new_user():
    assert engine.list_logged_dates("nobody-yet") == []


def test_get_week_returns_weekly_summary():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    summary = engine.get_week("alice", "2026-01-07")
    assert summary.week_start_date == "2026-01-01"
    assert summary.week_end_date == "2026-01-07"
    assert len(summary.days) == 7


# --- aggregation.py: daily_totals ------------------------------------------


def test_daily_totals_matches_manual_sum():
    log = engine.log_ingredient("alice", "B021", 200, "g", when=_dt("2026-01-01"))
    # B021 (toor dal) is 330.8 kcal/100g.
    assert log.computed_totals.energy_kcal == pytest.approx(661.6, abs=0.5)


def test_daily_totals_deleting_reduces_by_exact_contribution():
    before = engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    combined = engine.log_ingredient("alice", "T013", 10, "g", when=_dt("2026-01-01", hour=19))
    after = engine.delete_entry("alice", "2026-01-01", 1)

    removed_kcal = combined.computed_totals.energy_kcal - before.computed_totals.energy_kcal
    assert after.computed_totals.energy_kcal == pytest.approx(
        combined.computed_totals.energy_kcal - removed_kcal, abs=0.01
    )


# --- aggregation.py: streak -------------------------------------------------


def test_streak_counts_consecutive_days_ending_today():
    today = datetime.now(timezone.utc)
    engine.log_ingredient("alice", "B021", 100, "g", when=today)
    engine.log_ingredient("alice", "B021", 100, "g", when=today - timedelta(days=1))
    engine.log_ingredient("alice", "B021", 100, "g", when=today - timedelta(days=2))
    assert streak("alice") == 3


def test_streak_breaks_on_a_gap():
    today = datetime.now(timezone.utc)
    engine.log_ingredient("alice", "B021", 100, "g", when=today)
    engine.log_ingredient("alice", "B021", 100, "g", when=today - timedelta(days=2))
    assert streak("alice") == 1


def test_streak_rejects_unknown_metric():
    with pytest.raises(ValueError):
        streak("alice", metric="not_a_real_metric")


# --- aggregation.py: target_adherence ---------------------------------------


def test_target_adherence_without_profile_returns_none():
    result = target_adherence("alice")
    assert result["calorie_adherence_pct"] is None
    assert result["days_evaluated"] == 0


def test_target_adherence_with_profile_and_logs():
    profiles.save_profile(_profile())
    today = datetime.now(timezone.utc)
    engine.log_ingredient("alice", "B021", 100, "g", when=today)

    result = target_adherence("alice", days=1)
    assert result["days_evaluated"] == 1
    assert result["calorie_adherence_pct"] is not None


# --- fasting_integration.py --------------------------------------------------


def test_is_within_eating_window_true_without_profile():
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=3)) is True


def test_is_within_eating_window_respects_16_8_protocol():
    profiles.save_profile(_profile(fasting_protocol="16_8"))
    # Default 16:8 window is 12:00-20:00.
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=15)) is True
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=3)) is False


def test_is_within_eating_window_handles_wraparound():
    profiles.save_profile(_profile(fasting_protocol="ramadan"))
    # ramadan's window is 18:00-05:00, wrapping past midnight.
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=22)) is True
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=2)) is True
    assert is_within_eating_window("alice", _dt("2026-01-01", hour=10)) is False


def test_log_entry_flags_entries_outside_eating_window():
    profiles.save_profile(_profile(fasting_protocol="16_8"))
    log = engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01", hour=3))
    assert log.entries[0].outside_eating_window is True


def test_log_entry_does_not_flag_entries_inside_eating_window():
    profiles.save_profile(_profile(fasting_protocol="16_8"))
    log = engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01", hour=15))
    assert log.entries[0].outside_eating_window is False
