from datetime import datetime, timedelta, timezone

import pytest

import src.core.profiles as profiles
import src.core.units as units
import src.logging.store as store
from src.core.ingredients import load_ingredients
from src.insights.swaps import (
    MIN_LOGGED_FOR_PERSONAL_SWAPS,
    _protein_per_serving,
    _recent_unique_food_refs,
    suggest_protein_swaps,
)
from src.logging import engine


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(profiles, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


def test_suggest_protein_swaps_falls_back_below_threshold():
    # No logs at all -- well under the 20-unique-foods threshold.
    suggestions = suggest_protein_swaps("alice", "2026-01-15")
    assert len(suggestions) > 0
    assert all("DalGains recipes" in s for s in suggestions)


def test_suggest_protein_swaps_uses_own_history_at_threshold(ingredients):
    # Log 20 distinct ingredients to cross MIN_LOGGED_FOR_PERSONAL_SWAPS.
    ingredient_ids = list(ingredients.keys())[:MIN_LOGGED_FOR_PERSONAL_SWAPS]
    when = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    for ingredient_id in ingredient_ids:
        engine.log_ingredient("alice", ingredient_id, 100, "g", when=when)

    refs = _recent_unique_food_refs("alice", "2026-01-15")
    assert len(refs) == MIN_LOGGED_FOR_PERSONAL_SWAPS

    suggestions = suggest_protein_swaps("alice", "2026-01-15")
    assert len(suggestions) > 0
    assert all("you've logged before" in s for s in suggestions)


def test_recent_unique_food_refs_deduplicates_and_ignores_quarantined_days():
    when = datetime(2026, 1, 15, 12, tzinfo=timezone.utc)
    engine.log_ingredient("alice", "B021", 100, "g", when=when)
    engine.log_ingredient("alice", "B021", 50, "g", when=when + timedelta(hours=1))  # dup ref
    engine.log_ingredient("alice", "T013", 10, "g", when=when + timedelta(days=1))

    corrupt_path = store._log_path("alice", "2026-01-17")
    corrupt_path.write_text("{corrupt")

    refs = _recent_unique_food_refs("alice", "2026-01-17")
    assert refs.count(("ingredient", "B021")) == 1
    assert ("ingredient", "T013") in refs


def test_recent_unique_food_refs_includes_recipe_entries():
    engine.log_recipe("alice", "dal_tadka_north", servings=1, when=datetime(2026, 1, 15, tzinfo=timezone.utc))
    refs = _recent_unique_food_refs("alice", "2026-01-15")
    assert ("recipe", "dal_tadka_north") in refs


def test_protein_per_serving_for_ingredient_ref(ingredients):
    result = _protein_per_serving(("ingredient", "B021"), ingredients)
    assert result is not None
    name, protein = result
    assert name == "Red gram, dal"
    assert protein > 0


def test_protein_per_serving_for_recipe_ref(ingredients):
    result = _protein_per_serving(("recipe", "dal_tadka_north"), ingredients)
    assert result is not None
    name, protein = result
    assert name == "Dal Tadka"
    assert protein > 0


def test_protein_per_serving_missing_recipe_returns_none(ingredients):
    assert _protein_per_serving(("recipe", "not_a_real_recipe"), ingredients) is None


def test_protein_per_serving_unknown_ingredient_returns_none(ingredients):
    assert _protein_per_serving(("ingredient", "NOTAREALID"), ingredients) is None


def test_suggest_protein_swaps_respects_limit():
    suggestions = suggest_protein_swaps("alice", "2026-01-15", limit=1)
    assert len(suggestions) <= 1
