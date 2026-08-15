import pytest

from src.core.ingredients import load_ingredients
from src.recipes import beverages as bev
from src.recipes.builder import compute_nutrition


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


def _kcal(beverage, ingredients):
    return compute_nutrition(beverage, servings=1, ingredients=ingredients).energy_kcal


# --- build_chai -------------------------------------------------------

def test_chai_matches_real_world_reference_range(ingredients):
    # Standard 150ml cup, toned milk, 1 tsp sugar: commonly cited ~40-70 kcal.
    chai = bev.build_chai(milk_ml=60, milk_type="toned", sugar_tsp=1, size_ml=150)
    assert 40 <= _kcal(chai, ingredients) <= 70


def test_chai_light_variant_matches_reference_range(ingredients):
    # Skim milk, no sugar: a light chai, commonly cited ~15-30 kcal.
    chai = bev.build_chai(milk_ml=60, milk_type="skim", sugar_tsp=0, size_ml=150)
    assert 15 <= _kcal(chai, ingredients) <= 30


def test_chai_zero_milk_zero_sugar_has_no_macro_contribution(ingredients):
    chai = bev.build_chai(milk_ml=0, milk_type="none", sugar_tsp=0, size_ml=150)
    totals = compute_nutrition(chai, servings=1, ingredients=ingredients)
    assert totals.energy_kcal == 0
    assert totals.protein_g == 0


def test_chai_masala_adds_additives():
    chai = bev.build_chai(milk_ml=60, milk_type="toned", sugar_tsp=1, size_ml=150, masala=True)
    assert "cardamom" in chai.additives


# --- build_coffee -------------------------------------------------------

def test_filter_coffee_matches_real_world_reference_range(ingredients):
    # South Indian filter coffee, toned milk, 2 tsp sugar: ~60-100 kcal.
    coffee = bev.build_coffee(style="filter", milk_ml=80, milk_type="toned", sugar_tsp=2)
    assert 60 <= _kcal(coffee, ingredients) <= 100


def test_black_coffee_no_milk_no_sugar_is_near_zero_kcal(ingredients):
    coffee = bev.build_coffee(style="instant", milk_ml=0, milk_type="none", sugar_tsp=0)
    assert _kcal(coffee, ingredients) == 0


# --- build_lassi -------------------------------------------------------

def test_sweet_lassi_matches_real_world_reference_range(ingredients):
    # 200ml yogurt + 20g sugar glass: commonly cited ~150-250 kcal.
    lassi = bev.build_lassi(type="sweet", yogurt_ml=200, sugar_g=20)
    assert 150 <= _kcal(lassi, ingredients) <= 250


def test_mango_lassi_matches_real_world_reference_range(ingredients):
    lassi = bev.build_lassi(type="mango", yogurt_ml=200, sugar_g=10, fruit_g=100)
    assert 180 <= _kcal(lassi, ingredients) <= 300


def test_salty_lassi_has_less_sugar_than_sweet_lassi(ingredients):
    salty = bev.build_lassi(type="salty", yogurt_ml=200, sugar_g=0)
    sweet = bev.build_lassi(type="sweet", yogurt_ml=200, sugar_g=20)
    totals_salty = compute_nutrition(salty, servings=1, ingredients=ingredients)
    totals_sweet = compute_nutrition(sweet, servings=1, ingredients=ingredients)
    assert totals_salty.carbs_g < totals_sweet.carbs_g


# --- build_buttermilk ----------------------------------------------------

def test_buttermilk_matches_real_world_reference_range(ingredients):
    # 250ml glass of chaas: commonly cited ~30-60 kcal.
    chaas = bev.build_buttermilk(volume_ml=250)
    assert 30 <= _kcal(chaas, ingredients) <= 60


def test_buttermilk_scales_with_volume(ingredients):
    small = bev.build_buttermilk(volume_ml=200)
    large = bev.build_buttermilk(volume_ml=400)
    assert _kcal(large, ingredients) == pytest.approx(_kcal(small, ingredients) * 2)


# --- build_nimbu_paani -----------------------------------------------------

def test_nimbu_paani_matches_real_world_reference_range(ingredients):
    # 250ml glass with 15g sugar: commonly cited ~60-100 kcal.
    np_drink = bev.build_nimbu_paani(volume_ml=250, sugar_g=15)
    assert 60 <= _kcal(np_drink, ingredients) <= 100


def test_nimbu_paani_no_sugar_is_low_kcal(ingredients):
    np_drink = bev.build_nimbu_paani(volume_ml=250, sugar_g=0)
    assert _kcal(np_drink, ingredients) < 20


# --- build_juice -------------------------------------------------------

def test_mango_juice_matches_real_world_reference_range(ingredients):
    juice = bev.build_juice(fruit="mango", volume_ml=250, ingredients=ingredients)
    assert 90 <= _kcal(juice, ingredients) <= 160


def test_orange_juice_matches_real_world_reference_range(ingredients):
    juice = bev.build_juice(fruit="orange", volume_ml=250, added_sugar_g=10, ingredients=ingredients)
    assert 100 <= _kcal(juice, ingredients) <= 160


def test_juice_unknown_fruit_raises(ingredients):
    with pytest.raises(ValueError):
        bev.build_juice(fruit="totally not a fruit xyz", volume_ml=250, ingredients=ingredients)


# --- build_alcohol -------------------------------------------------------

def test_beer_matches_real_world_reference_range(ingredients):
    # 500ml can, 5% ABV: commonly cited ~200-215 kcal.
    beer = bev.build_alcohol(type="beer", volume_ml=500, abv_pct=5)
    assert 190 <= _kcal(beer, ingredients) <= 230


def test_wine_matches_real_world_reference_range(ingredients):
    # 150ml glass, 12% ABV: commonly cited ~120-125 kcal.
    wine = bev.build_alcohol(type="wine", volume_ml=150, abv_pct=12)
    assert 100 <= _kcal(wine, ingredients) <= 140


def test_whisky_shot_matches_real_world_reference_range(ingredients):
    # 45ml shot, 40% ABV: commonly cited ~97-100 kcal.
    whisky = bev.build_alcohol(type="whisky", volume_ml=45, abv_pct=40)
    assert 85 <= _kcal(whisky, ingredients) <= 115


def test_alcohol_zero_abv_has_zero_alcohol_kcal_but_keeps_residual_sugar(ingredients):
    beer = bev.build_alcohol(type="beer", volume_ml=500, abv_pct=0)
    totals = compute_nutrition(beer, servings=1, ingredients=ingredients)
    # residual carbs (beer's RESIDUAL_CARBS_G_PER_100ML) still contribute.
    assert totals.energy_kcal == pytest.approx(500 * 3.6 / 100 * 3.87, rel=0.05)


def test_spirit_has_no_residual_carbs(ingredients):
    vodka = bev.build_alcohol(type="vodka", volume_ml=45, abv_pct=40)
    totals = compute_nutrition(vodka, servings=1, ingredients=ingredients)
    assert totals.carbs_g == 0


# --- build_protein_shake -------------------------------------------------

def test_protein_shake_hits_target_protein(ingredients):
    shake = bev.build_protein_shake(
        protein_g=25, milk_ml=250, milk_type="toned", ingredients=ingredients
    )
    totals = compute_nutrition(shake, servings=1, ingredients=ingredients)
    # 25g from powder + whatever the 250ml toned milk itself contributes.
    assert totals.protein_g >= 25


def test_protein_shake_matches_real_world_reference_range(ingredients):
    # 25g whey isolate + 250ml toned milk: commonly cited ~200-300 kcal.
    shake = bev.build_protein_shake(
        protein_g=25, milk_ml=250, milk_type="toned", ingredients=ingredients
    )
    assert 200 <= _kcal(shake, ingredients) <= 300


def test_protein_shake_with_banana_and_peanut_butter_has_more_kcal(ingredients):
    plain = bev.build_protein_shake(
        protein_g=25, milk_ml=200, milk_type="skim", ingredients=ingredients
    )
    loaded = bev.build_protein_shake(
        protein_g=25,
        milk_ml=200,
        milk_type="skim",
        banana_g=100,
        peanut_butter_g=15,
        ingredients=ingredients,
    )
    assert _kcal(loaded, ingredients) > _kcal(plain, ingredients)


def test_protein_shake_zero_milk_falls_back_to_default_volume(ingredients):
    shake = bev.build_protein_shake(
        protein_g=25, milk_ml=0, milk_type="none", ingredients=ingredients
    )
    assert shake.volume_ml == bev.DEFAULT_SHAKE_VOLUME_ML
