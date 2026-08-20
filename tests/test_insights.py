"""Tests for src/insights/. Each rule function is tested directly with
synthetic data (per the Phase 3 brief: "each as a separately testable
function") plus a handful of generate_insights() integration checks for
the festival_flex suppression behavior.
"""
from datetime import datetime, timedelta, timezone

import pytest

import src.core.profiles as profiles
import src.recipes.builder as builder
from src.core.schemas import LogEntry, MealLog, NutritionTotals, UserProfile
from src.insights import engine as insights_engine
from src.insights.engine import (
    check_beverage_calorie_surprise,
    check_calorie_surplus_streak,
    check_festival_flex,
    check_fiber_low_week,
    check_hydration_reminder,
    check_protein_deficit_3day,
    check_streak_celebration,
    check_undereating_warning,
    generate_insights,
)
from src.logging import engine as log_engine


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "RECIPES_DIR", tmp_path / "recipes_unused")


def _totals(kcal=0, protein=0, fat=0, carbs=0, fiber=0) -> NutritionTotals:
    return NutritionTotals(energy_kcal=kcal, protein_g=protein, fat_g=fat, carbs_g=carbs, fiber_g=fiber)


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
        goal="cut",
        dietary_pattern="vegetarian",
        eating_phase="cutting",
    )
    kwargs.update(overrides)
    return UserProfile(**kwargs)


# --- check_protein_deficit_3day ---------------------------------------


def test_protein_deficit_fires_after_3_low_days():
    day_totals = [_totals(protein=10)] * 3
    result = check_protein_deficit_3day(day_totals, target_protein_g=100, user_id="alice", as_of_date="2026-01-03")
    assert result is not None
    assert result.severity == "suggest"
    assert result.kind == "swap"


def test_protein_deficit_does_not_fire_for_exactly_2_low_days():
    day_totals = [_totals(protein=10)] * 2
    result = check_protein_deficit_3day(day_totals, target_protein_g=100, user_id="alice", as_of_date="2026-01-02")
    assert result is None


def test_protein_deficit_does_not_fire_if_one_day_is_adequate():
    day_totals = [_totals(protein=10), _totals(protein=10), _totals(protein=90)]
    result = check_protein_deficit_3day(day_totals, target_protein_g=100, user_id="alice", as_of_date="2026-01-03")
    assert result is None


# --- check_calorie_surplus_streak -------------------------------------


def test_calorie_surplus_fires_after_5_day_streak_while_cutting():
    day_totals = [_totals(kcal=2400)] * 5  # target 2000, 120% of target
    result = check_calorie_surplus_streak(day_totals, target_kcal=2000, eating_phase="cutting")
    assert result is not None
    assert result.evidence["streak_days"] == 5


def test_calorie_surplus_does_not_fire_for_4_day_streak():
    day_totals = [_totals(kcal=2400)] * 4
    result = check_calorie_surplus_streak(day_totals, target_kcal=2000, eating_phase="cutting")
    assert result is None


def test_calorie_surplus_does_not_fire_outside_cut_or_recomp():
    day_totals = [_totals(kcal=2400)] * 6
    result = check_calorie_surplus_streak(day_totals, target_kcal=2000, eating_phase="maintenance")
    assert result is None


def test_calorie_surplus_streak_breaks_on_an_on_target_day():
    day_totals = [_totals(kcal=2400)] * 3 + [_totals(kcal=2000)] + [_totals(kcal=2400)] * 3
    result = check_calorie_surplus_streak(day_totals, target_kcal=2000, eating_phase="cutting")
    # trailing streak is only the last 3 days
    assert result is None


# --- check_undereating_warning ------------------------------------------


def test_undereating_fires_for_a_single_low_day():
    dated = [("2026-01-01", _totals(kcal=1000))]
    result = check_undereating_warning(dated, bmr=1500)  # threshold 1200
    assert result is not None
    assert result.severity == "warn"


def test_undereating_does_not_fire_at_exactly_80pct_bmr():
    # exactly at the threshold, not under it
    dated = [("2026-01-01", _totals(kcal=1200))]
    result = check_undereating_warning(dated, bmr=1500)
    assert result is None


def test_undereating_escalates_to_urgent_after_3_consecutive_days():
    dated = [(f"2026-01-0{i}", _totals(kcal=1000)) for i in range(1, 4)]
    result = check_undereating_warning(dated, bmr=1500)
    assert result.severity == "urgent"


def test_undereating_ignores_unlogged_zero_kcal_days():
    dated = [("2026-01-01", _totals(kcal=0))]  # no log that day, not "ate zero"
    result = check_undereating_warning(dated, bmr=1500)
    assert result is None


# --- check_fiber_low_week -----------------------------------------------


def test_fiber_low_week_fires_under_25g():
    result = check_fiber_low_week(20)
    assert result is not None
    assert "bajra" in " ".join(result.suggested_actions).lower()


def test_fiber_low_week_does_not_fire_at_exactly_25g():
    assert check_fiber_low_week(25) is None


def test_fiber_low_week_does_not_fire_above_25g():
    assert check_fiber_low_week(30) is None


# --- check_streak_celebration -------------------------------------------


@pytest.mark.parametrize("milestone", [7, 30, 100])
def test_streak_celebration_fires_on_milestones(milestone):
    assert check_streak_celebration(milestone) is not None


@pytest.mark.parametrize("non_milestone", [1, 6, 8, 29, 31, 99, 101])
def test_streak_celebration_does_not_fire_off_milestone(non_milestone):
    assert check_streak_celebration(non_milestone) is None


# --- check_festival_flex --------------------------------------------------


def test_festival_flex_fires_on_recognized_tag():
    assert check_festival_flex(["diwali"]) is not None


def test_festival_flex_is_case_insensitive():
    assert check_festival_flex(["DIWALI"]) is not None


def test_festival_flex_does_not_fire_without_a_tag():
    assert check_festival_flex([]) is None


def test_festival_flex_does_not_fire_on_unrelated_tags():
    assert check_festival_flex(["travel", "cheat_meal"]) is None


# --- check_hydration_reminder / check_beverage_calorie_surprise (need ingredients) --


@pytest.fixture(scope="module")
def ingredients():
    from src.core.ingredients import load_ingredients

    return load_ingredients()


def test_hydration_reminder_fires_after_gap(ingredients):
    from src.core.planning import EatingWindow

    window = EatingWindow(start_hour=0, end_hour=24)
    now = datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    entries = [
        LogEntry(
            ingredient_id="B021", qty=100, unit="g", timestamp=now - timedelta(hours=8)
        )
    ]
    result = check_hydration_reminder(entries, now, window, ingredients)
    assert result is not None


def test_hydration_reminder_does_not_fire_within_gap(ingredients):
    from src.core.planning import EatingWindow

    window = EatingWindow(start_hour=0, end_hour=24)
    now = datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc)
    entries = [
        LogEntry(
            ingredient_id="USDA004", qty=100, unit="g", timestamp=now - timedelta(hours=2)
        )
    ]
    result = check_hydration_reminder(entries, now, window, ingredients)
    assert result is None


def test_hydration_reminder_silent_outside_eating_window(ingredients):
    from src.core.planning import EatingWindow

    window = EatingWindow(start_hour=12, end_hour=20)
    now = datetime(2026, 1, 1, 3, 0, tzinfo=timezone.utc)  # outside window
    result = check_hydration_reminder([], now, window, ingredients)
    assert result is None


def test_beverage_calorie_surprise_fires_over_threshold(ingredients):
    log = MealLog(
        log_id="2026-01-01",
        user_id="alice",
        timestamp=datetime.now(timezone.utc),
        entries=[
            LogEntry(ingredient_id="USDA004", qty=300, unit="g", timestamp=datetime.now(timezone.utc)),
            LogEntry(ingredient_id="B021", qty=20, unit="g", timestamp=datetime.now(timezone.utc)),
        ],
        computed_totals=_totals(kcal=200),  # arbitrary; real share computed internally
    )
    result = check_beverage_calorie_surprise(log, ingredients, "alice")
    assert result is not None


def test_beverage_calorie_surprise_does_not_fire_under_threshold(ingredients):
    log = MealLog(
        log_id="2026-01-01",
        user_id="alice",
        timestamp=datetime.now(timezone.utc),
        entries=[LogEntry(ingredient_id="B021", qty=200, unit="g", timestamp=datetime.now(timezone.utc))],
        computed_totals=_totals(kcal=200),
    )
    result = check_beverage_calorie_surprise(log, ingredients, "alice")
    assert result is None


# --- generate_insights integration: festival suppression -------------------


def test_generate_insights_festival_flex_suppresses_calorie_warnings():
    profiles.save_profile(_profile())
    today = datetime.now(timezone.utc)

    # Build a 7-day calorie-surplus streak (ghee is 900 kcal/100g).
    for i in range(6, -1, -1):
        log_engine.log_ingredient("alice", "T013", 500, "g", when=today - timedelta(days=i))
    log_engine.tag_day("alice", today.date().isoformat(), "diwali")

    insights = generate_insights("alice", today.date().isoformat())
    assert not any(i.insight_id.startswith("calorie_") for i in insights)
    assert any(i.insight_id == "festival_flex" for i in insights)


def test_generate_insights_without_festival_tag_keeps_calorie_warning():
    profiles.save_profile(_profile())
    today = datetime.now(timezone.utc)
    for i in range(6, -1, -1):
        log_engine.log_ingredient("alice", "T013", 500, "g", when=today - timedelta(days=i))

    insights = generate_insights("alice", today.date().isoformat())
    assert any(i.insight_id == "calorie_surplus_streak" for i in insights)


def test_generate_insights_returns_empty_list_for_user_with_no_data():
    assert generate_insights("nobody", "2026-01-01") == []
