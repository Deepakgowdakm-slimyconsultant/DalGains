import pytest

from src.core.ingredients import load_ingredients
from src.core.schemas import OilGhee, Recipe, RecipeIngredient
from src.recipes.builder import (
    RECIPES_DIR,
    compute_nutrition,
    create_recipe,
    list_recipes,
    load_recipe,
)

# recipe_id -> (min_kcal, max_kcal) documented realistic range for one serving.
SEEDED_RECIPE_RANGES = {
    "dal_tadka_north": (150, 230),
    "sambar_south": (150, 230),
    "poha_west": (260, 380),
    "fish_curry_bengali_east": (180, 270),
    "rajma_chawal_north": (380, 520),
    "curd_rice_south": (250, 360),
    "sabudana_khichdi_fasting": (280, 400),
    # Widened in Phase 3: switching to household units (1 whole potato,
    # 1 katori atta) pushed this to ~427 kcal -- a more realistic
    # whole-piece portion than the original raw-gram estimate.
    "aloo_paratha_north": (350, 450),
}


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


@pytest.fixture
def simple_recipe():
    return Recipe(
        recipe_id="test_recipe_tmp",
        name="Test Recipe",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=100, unit="g")],
        oil_ghee=OilGhee(type="ghee", qty_g=10),
        servings=2,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )


def test_create_and_load_recipe_roundtrip(simple_recipe):
    path = create_recipe(simple_recipe)
    try:
        assert path.exists()
        loaded = load_recipe(simple_recipe.recipe_id)
        assert loaded == simple_recipe
    finally:
        path.unlink(missing_ok=True)


def test_load_recipe_missing_raises():
    with pytest.raises(FileNotFoundError):
        load_recipe("does_not_exist_xyz")


def test_compute_nutrition_happy_path(simple_recipe, ingredients):
    totals = compute_nutrition(simple_recipe, servings=1, ingredients=ingredients)
    # 100g toor dal (330.8 kcal/100g) + 10g ghee (900 kcal/100g), / 2 servings
    expected = (330.8 + 90) / 2
    assert totals.energy_kcal == pytest.approx(expected, abs=0.5)


def test_compute_nutrition_scales_with_servings(simple_recipe, ingredients):
    one = compute_nutrition(simple_recipe, servings=1, ingredients=ingredients)
    three = compute_nutrition(simple_recipe, servings=3, ingredients=ingredients)
    assert three.energy_kcal == pytest.approx(one.energy_kcal * 3)


def test_compute_nutrition_resolves_non_gram_units(ingredients):
    # B021 (toor dal) has a density of 1.0 g/ml (src/core/densities.py),
    # and the default katori is 150ml, so "1 katori" == "150g" for it.
    grams_recipe = Recipe(
        recipe_id="grams_version",
        name="Grams",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=150, unit="g")],
        servings=1,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )
    katori_recipe = Recipe(
        recipe_id="katori_version",
        name="Katori",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=1, unit="katori")],
        servings=1,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )
    grams_totals = compute_nutrition(grams_recipe, ingredients=ingredients)
    katori_totals = compute_nutrition(katori_recipe, ingredients=ingredients)
    assert grams_totals == katori_totals


def test_compute_nutrition_unknown_ingredient_raises(ingredients):
    bad_recipe = Recipe(
        recipe_id="bad_recipe",
        name="Bad",
        ingredients=[RecipeIngredient(ingredient_id="ZZZ999", qty=50, unit="g")],
        servings=1,
        region_tag="custom",
        meal_type="lunch",
        created_by="test",
    )
    with pytest.raises(KeyError):
        compute_nutrition(bad_recipe, ingredients=ingredients)


def test_list_recipes_returns_all_seeded():
    recipes = list_recipes()
    ids = {r.recipe_id for r in recipes}
    assert set(SEEDED_RECIPE_RANGES) <= ids


def test_list_recipes_filter_by_region():
    north = list_recipes(filter_by_region="north")
    assert north
    assert all(r.region_tag == "north" for r in north)


def test_list_recipes_filter_by_tag():
    fasting_tagged = list_recipes(filter_by_tag="fasting")
    assert fasting_tagged
    assert all("fasting" in r.tags for r in fasting_tagged)


def test_list_recipes_fasting_only():
    fasting_only = list_recipes(fasting_only=True)
    assert fasting_only
    assert all(r.is_fasting_safe for r in fasting_only)
    assert any(r.recipe_id == "sabudana_khichdi_fasting" for r in fasting_only)


@pytest.mark.parametrize("recipe_id", sorted(SEEDED_RECIPE_RANGES))
def test_seeded_recipe_within_realistic_kcal_range(recipe_id, ingredients):
    recipe = load_recipe(recipe_id)
    totals = compute_nutrition(recipe, servings=1, ingredients=ingredients)
    low, high = SEEDED_RECIPE_RANGES[recipe_id]
    assert low <= totals.energy_kcal <= high, (
        f"{recipe_id}: {totals.energy_kcal:.1f} kcal outside documented "
        f"realistic range [{low}, {high}]"
    )
