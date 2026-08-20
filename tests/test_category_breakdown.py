"""Exact-math coverage for src.logging.category_breakdown -- History's
Patterns tab depends on this being true gram-level attribution, not an
approximation, so these tests hand-compute the expected numbers rather
than just asserting "something non-zero came back".
"""
from datetime import datetime, timezone

import pytest

import src.recipes.builder as builder
from src.core.ingredients import load_ingredients
from src.core.schemas import OilGhee, Recipe, RecipeIngredient
from src.logging import engine
from src.logging.category_breakdown import category_breakdown
from src.recipes.builder import OIL_GHEE_PROFILES, create_recipe


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "RECIPES_DIR", tmp_path / "recipes")


def _dt(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)


def test_raw_ingredient_entries_attribute_exactly_by_category():
    ingredients = load_ingredients()
    dal = ingredients["B021"]  # category "dal"
    milk = ingredients["L001"]  # category "dairy"
    egg = ingredients["M001"]  # category "egg"

    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "L001", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "M001", 100, "g", when=_dt("2026-01-01"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["by_category"]["dal"].protein_g == pytest.approx(dal.protein_g_per_100g)
    assert result["by_category"]["dairy"].protein_g == pytest.approx(milk.protein_g_per_100g)
    assert result["by_category"]["egg"].protein_g == pytest.approx(egg.protein_g_per_100g)
    assert result["by_category"]["dal"].energy_kcal == pytest.approx(dal.energy_kcal_per_100g)


def test_raw_ingredient_entry_scales_with_quantity():
    ingredients = load_ingredients()
    dal = ingredients["B021"]

    engine.log_ingredient("alice", "B021", 250, "g", when=_dt("2026-01-01"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["by_category"]["dal"].protein_g == pytest.approx(dal.protein_g_per_100g * 2.5)


def test_recipe_entry_attributes_ingredient_by_ingredient():
    ingredients = load_ingredients()
    dal = ingredients["B021"]
    milk = ingredients["L001"]

    # A hand-built recipe with a known, simple composition: 200g dal +
    # 50g milk + 10g ghee, yielding 2 servings -- so logging 1 serving
    # should attribute exactly half of each ingredient's contribution.
    recipe = Recipe(
        recipe_id="hand_built",
        name="Test recipe",
        ingredients=[
            RecipeIngredient(ingredient_id="B021", qty=200, unit="g"),
            RecipeIngredient(ingredient_id="L001", qty=50, unit="g"),
        ],
        oil_ghee=OilGhee(type="ghee", qty_g=10),
        servings=2,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )
    create_recipe(recipe)

    engine.log_recipe("alice", "hand_built", servings=1, when=_dt("2026-01-01"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")
    scale = 0.5  # 1 serving of a 2-serving recipe

    assert result["by_category"]["dal"].protein_g == pytest.approx(dal.protein_g_per_100g * 2 * scale)
    assert result["by_category"]["dairy"].protein_g == pytest.approx(milk.protein_g_per_100g * 0.5 * scale)

    ghee_profile = OIL_GHEE_PROFILES["ghee"]
    assert result["by_category"]["oil_fat"].fat_g == pytest.approx(ghee_profile["fat_g_per_100g"] * 0.1 * scale)
    assert result["by_category"]["oil_fat"].energy_kcal == pytest.approx(ghee_profile["kcal_per_100g"] * 0.1 * scale)


def test_category_totals_accumulate_across_days_in_range():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-03"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-03")
    dal = load_ingredients()["B021"]

    assert result["by_category"]["dal"].protein_g == pytest.approx(dal.protein_g_per_100g * 2)


def test_days_outside_range_are_excluded():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-02-01"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-31")
    dal = load_ingredients()["B021"]

    assert result["by_category"]["dal"].protein_g == pytest.approx(dal.protein_g_per_100g)


def test_beverage_day_flags_beverage_meal_type_recipe():
    recipe = Recipe(
        recipe_id="chai_test",
        name="Chai",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=5, unit="g")],
        servings=1,
        region_tag="custom",
        meal_type="beverage",
        created_by="test",
    )
    create_recipe(recipe)
    engine.log_recipe("alice", "chai_test", servings=1, when=_dt("2026-01-01"))
    engine.log_recipe("alice", "chai_test", servings=1, when=_dt("2026-01-01"))  # not a beverage-day test double-count concern -- see next test for a non-beverage entry mixed in

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["beverage_kcal_by_date"]["2026-01-01"] == pytest.approx(result["total_kcal_by_date"]["2026-01-01"])


def test_beverage_day_excludes_non_beverage_ingredient_entries():
    engine.log_ingredient("alice", "B021", 100, "g", when=_dt("2026-01-01"))  # dal, not a beverage

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["beverage_kcal_by_date"]["2026-01-01"] == pytest.approx(0.0)


def test_beverage_day_flags_raw_beverage_base_ingredient():
    ingredients = load_ingredients()
    beverage_base_id = next(iid for iid, ing in ingredients.items() if ing.category == "beverage_base")

    engine.log_ingredient("alice", beverage_base_id, 50, "g", when=_dt("2026-01-01"))

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["beverage_kcal_by_date"]["2026-01-01"] > 0
    assert result["beverage_kcal_by_date"]["2026-01-01"] == pytest.approx(result["total_kcal_by_date"]["2026-01-01"])


def test_orphaned_recipe_reference_is_skipped_not_raised():
    # Log against a recipe, then delete the recipe -- the log entry
    # becomes an orphaned reference (this happens in practice: a user
    # deletes/renames a custom recipe after logging it). The breakdown
    # should skip it gracefully, not crash the whole endpoint.
    recipe = Recipe(
        recipe_id="temp_recipe",
        name="Temp",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=100, unit="g")],
        servings=1,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )
    create_recipe(recipe)
    engine.log_recipe("alice", "temp_recipe", servings=1, when=_dt("2026-01-01"))
    builder.delete_recipe("temp_recipe")

    result = category_breakdown("alice", "2026-01-01", "2026-01-01")

    assert result["by_category"] == {}
    assert result["beverage_kcal_by_date"]["2026-01-01"] == 0.0


def test_empty_range_for_user_with_no_logs():
    result = category_breakdown("nobody", "2026-01-01", "2026-01-07")

    assert result["by_category"] == {}
    assert result["beverage_kcal_by_date"] == {}
    assert result["total_kcal_by_date"] == {}
