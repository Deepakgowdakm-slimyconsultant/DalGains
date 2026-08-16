import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.core.ingredients import load_ingredients
from src.core.schemas import Recipe, RecipeIngredient
from src.recipes.builder import compute_nutrition

INGREDIENTS = load_ingredients()
INGREDIENT_LIST = list(INGREDIENTS.values())

# Bounded input space: real ingredients from the loaded DB, quantities
# capped at a generous but finite 1000g.
_ingredient = st.sampled_from(INGREDIENT_LIST)
_qty = st.floats(min_value=0.01, max_value=1000, allow_nan=False)


def _recipe(ingredients: list[RecipeIngredient], servings: int = 1) -> Recipe:
    return Recipe(
        recipe_id="hyp",
        name="hyp",
        ingredients=ingredients,
        servings=servings,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )


@given(ingredient=_ingredient, qty=_qty)
def test_single_ingredient_kcal_matches_manual_calculation(ingredient, qty):
    recipe = _recipe([RecipeIngredient(ingredient_id=ingredient.ingredient_id, qty=qty, unit="g")])
    totals = compute_nutrition(recipe, servings=1, ingredients=INGREDIENTS)
    expected_kcal = ingredient.energy_kcal_per_100g * qty / 100
    assert totals.energy_kcal == pytest.approx(expected_kcal, abs=0.5)


@given(
    items=st.lists(st.tuples(_ingredient, _qty), min_size=1, max_size=6),
)
def test_multi_ingredient_kcal_matches_sum_of_contributions(items):
    recipe = _recipe(
        [RecipeIngredient(ingredient_id=ing.ingredient_id, qty=qty, unit="g") for ing, qty in items]
    )
    totals = compute_nutrition(recipe, servings=1, ingredients=INGREDIENTS)
    expected_kcal = sum(ing.energy_kcal_per_100g * qty / 100 for ing, qty in items)
    assert totals.energy_kcal == pytest.approx(expected_kcal, abs=0.5)


@given(
    ingredient=_ingredient,
    qty=_qty,
    n=st.floats(min_value=0.1, max_value=10, allow_nan=False),
)
def test_nutrition_scales_linearly_with_servings(ingredient, qty, n):
    recipe = _recipe([RecipeIngredient(ingredient_id=ingredient.ingredient_id, qty=qty, unit="g")])
    one = compute_nutrition(recipe, servings=1, ingredients=INGREDIENTS)
    scaled = compute_nutrition(recipe, servings=n, ingredients=INGREDIENTS)

    assert scaled.energy_kcal == pytest.approx(one.energy_kcal * n, rel=1e-9)
    assert scaled.protein_g == pytest.approx(one.protein_g * n, rel=1e-9)
    assert scaled.fat_g == pytest.approx(one.fat_g * n, rel=1e-9)
    assert scaled.carbs_g == pytest.approx(one.carbs_g * n, rel=1e-9)
    assert scaled.fiber_g == pytest.approx(one.fiber_g * n, rel=1e-9)


@given(ingredient=_ingredient, qty=_qty, zero_ingredient=_ingredient)
def test_adding_zero_qty_ingredient_does_not_change_totals(ingredient, qty, zero_ingredient):
    base = _recipe([RecipeIngredient(ingredient_id=ingredient.ingredient_id, qty=qty, unit="g")])
    with_zero = base.model_copy(
        update={
            "ingredients": base.ingredients
            + [RecipeIngredient(ingredient_id=zero_ingredient.ingredient_id, qty=0, unit="g")]
        }
    )
    base_totals = compute_nutrition(base, ingredients=INGREDIENTS)
    zero_totals = compute_nutrition(with_zero, ingredients=INGREDIENTS)
    assert base_totals == zero_totals
