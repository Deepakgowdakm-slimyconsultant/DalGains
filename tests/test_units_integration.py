"""End-to-end coverage for the Phase 3 unit-integration fix: recipes now
resolve qty+unit through src.core.units.resolve_to_grams before scaling
nutrition, instead of treating qty as always-grams (the Phase 2 bug this
phase fixes).
"""
import pytest

from src.core.ingredients import load_ingredients
from src.core.schemas import Recipe, RecipeIngredient
from src.core.units import calibrate_unit
from src.recipes.builder import compute_nutrition


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


def _recipe(ingredient_id: str, qty: float, unit: str) -> Recipe:
    return Recipe(
        recipe_id="hyp",
        name="hyp",
        ingredients=[RecipeIngredient(ingredient_id=ingredient_id, qty=qty, unit=unit)],
        servings=1,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )


def test_katori_dal_equals_150g_dal_for_default_calibration(ingredients):
    # Default katori is 150ml, and B021 (toor dal) has a density of 1.0
    # g/ml in src/core/densities.py, so "1 katori" == "150g" for it.
    katori_recipe = _recipe("B021", 1, "katori")
    grams_recipe = _recipe("B021", 150, "g")

    katori_totals = compute_nutrition(katori_recipe, ingredients=ingredients)
    grams_totals = compute_nutrition(grams_recipe, ingredients=ingredients)

    assert katori_totals == grams_totals


def test_nutrition_changes_with_users_own_katori_calibration(ingredients):
    calibrate_unit("alice", "katori", volume_ml=200, method="measured")
    recipe = _recipe("B021", 1, "katori")

    default_totals = compute_nutrition(recipe, ingredients=ingredients, user_id=None)
    alice_totals = compute_nutrition(recipe, ingredients=ingredients, user_id="alice")

    assert alice_totals.energy_kcal > default_totals.energy_kcal


def test_nutrition_unaffected_for_user_without_custom_calibration(ingredients):
    calibrate_unit("alice", "katori", volume_ml=200, method="measured")
    recipe = _recipe("B021", 1, "katori")

    default_totals = compute_nutrition(recipe, ingredients=ingredients, user_id=None)
    bob_totals = compute_nutrition(recipe, ingredients=ingredients, user_id="bob")

    assert bob_totals == default_totals


def test_piece_unit_resolves_via_per_piece_g(ingredients):
    # F006 (Potato, brown skin, big) has per_piece_g=100.
    piece_recipe = _recipe("F006", 1, "piece")
    grams_recipe = _recipe("F006", 100, "g")

    assert compute_nutrition(piece_recipe, ingredients=ingredients) == compute_nutrition(
        grams_recipe, ingredients=ingredients
    )


def test_piece_unit_without_per_piece_g_raises(ingredients):
    # B021 (toor dal) has no per_piece_g set.
    recipe = _recipe("B021", 1, "piece")
    with pytest.raises(ValueError):
        compute_nutrition(recipe, ingredients=ingredients)


def test_mutthi_unit_uses_category_mass_table(ingredients):
    # H012 (Ground nut) is category "nut_seed" -> 20g/mutthi.
    mutthi_recipe = _recipe("H012", 1, "mutthi")
    grams_recipe = _recipe("H012", 20, "g")

    assert compute_nutrition(mutthi_recipe, ingredients=ingredients) == compute_nutrition(
        grams_recipe, ingredients=ingredients
    )


def test_tsp_and_tbsp_resolve_consistently(ingredients):
    # 3 tsp == 1 tbsp by volume (5ml vs 15ml), so nutrition should match
    # exactly for the same ingredient.
    tsp_recipe = _recipe("G033", 3, "tsp")
    tbsp_recipe = _recipe("G033", 1, "tbsp")

    assert compute_nutrition(tsp_recipe, ingredients=ingredients) == compute_nutrition(
        tbsp_recipe, ingredients=ingredients
    )
