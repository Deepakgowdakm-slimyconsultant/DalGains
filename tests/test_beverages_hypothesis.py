import pytest
from hypothesis import given
from hypothesis import strategies as st

from src.core.ingredients import load_ingredients
from src.recipes import beverages as bev
from src.recipes.builder import compute_nutrition

INGREDIENTS = load_ingredients()


@given(size_ml=st.floats(min_value=50, max_value=500, allow_nan=False))
def test_chai_with_zero_milk_and_sugar_equals_plain_tea_macros(size_ml):
    chai = bev.build_chai(milk_ml=0, milk_type="none", sugar_tsp=0, size_ml=size_ml)
    totals = compute_nutrition(chai, servings=1, ingredients=INGREDIENTS)
    assert totals.energy_kcal == 0
    assert totals.protein_g == 0
    assert totals.fat_g == 0
    assert totals.carbs_g == 0


@given(
    volume_ml=st.floats(min_value=50, max_value=500, allow_nan=False),
    sugar_g=st.floats(min_value=0, max_value=50, allow_nan=False),
)
def test_nimbu_paani_doubling_volume_doubles_macros_exactly(volume_ml, sugar_g):
    base = bev.build_nimbu_paani(volume_ml=volume_ml, sugar_g=sugar_g)
    doubled = bev.build_nimbu_paani(volume_ml=volume_ml * 2, sugar_g=sugar_g * 2)
    base_totals = compute_nutrition(base, servings=1, ingredients=INGREDIENTS)
    doubled_totals = compute_nutrition(doubled, servings=1, ingredients=INGREDIENTS)

    assert doubled_totals.energy_kcal == pytest.approx(base_totals.energy_kcal * 2, rel=1e-9)
    assert doubled_totals.carbs_g == pytest.approx(base_totals.carbs_g * 2, rel=1e-9)


@given(volume_ml=st.floats(min_value=100, max_value=500, allow_nan=False))
def test_buttermilk_doubling_volume_doubles_macros_exactly(volume_ml):
    base = bev.build_buttermilk(volume_ml=volume_ml)
    doubled = bev.build_buttermilk(volume_ml=volume_ml * 2)
    base_totals = compute_nutrition(base, servings=1, ingredients=INGREDIENTS)
    doubled_totals = compute_nutrition(doubled, servings=1, ingredients=INGREDIENTS)

    assert doubled_totals.energy_kcal == pytest.approx(base_totals.energy_kcal * 2, rel=1e-9)
    assert doubled_totals.protein_g == pytest.approx(base_totals.protein_g * 2, rel=1e-9)


@given(
    volume_ml=st.floats(min_value=30, max_value=1000, allow_nan=False),
    alcohol_type=st.sampled_from(list(bev.RESIDUAL_CARBS_G_PER_100ML)),
)
def test_alcohol_zero_abv_contributes_zero_ethanol_regardless_of_volume(volume_ml, alcohol_type):
    drink = bev.build_alcohol(type=alcohol_type, volume_ml=volume_ml, abv_pct=0)
    ethanol_row = next(ri for ri in drink.ingredients if ri.ingredient_id == "MANUAL004")
    assert ethanol_row.qty == pytest.approx(0)


@given(
    volume_ml=st.floats(min_value=30, max_value=1000, allow_nan=False),
    abv_pct=st.floats(min_value=0.1, max_value=100, allow_nan=False),
    alcohol_type=st.sampled_from(list(bev.RESIDUAL_CARBS_G_PER_100ML)),
)
def test_alcohol_kcal_increases_with_abv(volume_ml, abv_pct, alcohol_type):
    zero = bev.build_alcohol(type=alcohol_type, volume_ml=volume_ml, abv_pct=0)
    some = bev.build_alcohol(type=alcohol_type, volume_ml=volume_ml, abv_pct=abv_pct)
    zero_kcal = compute_nutrition(zero, servings=1, ingredients=INGREDIENTS).energy_kcal
    some_kcal = compute_nutrition(some, servings=1, ingredients=INGREDIENTS).energy_kcal
    assert some_kcal > zero_kcal
