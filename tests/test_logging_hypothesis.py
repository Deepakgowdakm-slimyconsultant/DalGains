"""Hypothesis property tests for src/logging/."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import src.core.profiles as profiles
import src.core.units as units
import src.logging.store as store
from src.core.ingredients import load_ingredients
from src.logging import engine
from src.logging.aggregation import weekly_totals

INGREDIENTS = load_ingredients()
INGREDIENT_IDS = list(INGREDIENTS.keys())

_ingredient_id = st.sampled_from(INGREDIENT_IDS)
_qty = st.floats(min_value=0.1, max_value=500, allow_nan=False)


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(profiles, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")


def _fresh_user_id() -> str:
    # Generated fresh inside the test body (NOT as a @given-controlled
    # parameter) so it's unique on every call, including hypothesis's
    # shrinking retries. log_ingredient APPENDS to a day's file rather
    # than overwriting it, so if a user_id were reused across shrink
    # attempts (hypothesis keeps parameters it isn't actively shrinking
    # fixed across many retries, and UUIDs aren't shrinkable), entries
    # from unrelated attempts would silently accumulate into the same
    # file and corrupt the "before/after" comparison below.
    return str(uuid.uuid4())


@given(entries=st.lists(st.tuples(_ingredient_id, _qty), min_size=1, max_size=5))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_log_entry_sequence_totals_equal_manual_sum(entries):
    user_id = _fresh_user_id()
    when = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    for ingredient_id, qty in entries:
        engine.log_ingredient(user_id, ingredient_id, qty, "g", when=when)

    log = engine.get_day(user_id, "2026-01-01")
    expected_kcal = sum(INGREDIENTS[i].energy_kcal_per_100g * q / 100 for i, q in entries)
    assert log.computed_totals.energy_kcal == pytest.approx(expected_kcal, abs=0.5)


@given(
    entries=st.lists(st.tuples(_ingredient_id, _qty), min_size=2, max_size=5),
    delete_index=st.integers(min_value=0),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
def test_delete_entry_reduces_totals_by_exact_contribution(entries, delete_index):
    user_id = _fresh_user_id()
    delete_index = delete_index % len(entries)
    when = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    for ingredient_id, qty in entries:
        engine.log_ingredient(user_id, ingredient_id, qty, "g", when=when)

    before = engine.get_day(user_id, "2026-01-01")
    removed_ingredient_id, removed_qty = entries[delete_index]
    removed_kcal = INGREDIENTS[removed_ingredient_id].energy_kcal_per_100g * removed_qty / 100

    after = engine.delete_entry(user_id, "2026-01-01", delete_index)
    assert after is not None  # min_size=2 guarantees at least one entry remains
    assert after.computed_totals.energy_kcal == pytest.approx(
        before.computed_totals.energy_kcal - removed_kcal, abs=0.5
    )


@given(daily_entries=st.lists(st.tuples(_ingredient_id, _qty), min_size=1, max_size=3))
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None, max_examples=20
)
def test_weekly_aggregation_equals_sum_of_daily_totals(daily_entries):
    user_id = _fresh_user_id()
    # Log the same entries every day for a clean 7x multiple to check against.
    base = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
    for day_offset in range(7):
        when = base + timedelta(days=day_offset)
        for ingredient_id, qty in daily_entries:
            engine.log_ingredient(user_id, ingredient_id, qty, "g", when=when)

    week = weekly_totals(user_id, "2026-01-07")
    manual_daily_kcal = sum(INGREDIENTS[i].energy_kcal_per_100g * q / 100 for i, q in daily_entries)

    assert week.averages.energy_kcal == pytest.approx(manual_daily_kcal, abs=0.5)
    total_week_kcal = sum(day.totals.energy_kcal for day in week.days)
    assert total_week_kcal == pytest.approx(manual_daily_kcal * 7, abs=3.5)
