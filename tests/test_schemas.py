from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.core.schemas import (
    Beverage,
    FastingWindow,
    HouseholdUnit,
    Ingredient,
    LogEntry,
    MealLog,
    NutritionTotals,
    OilGhee,
    Recipe,
    RecipeIngredient,
    UserProfile,
)


def _valid_ingredient_kwargs(**overrides):
    kwargs = dict(
        ingredient_id="B021",
        name="Red gram, dal",
        aliases=["toor dal"],
        energy_kcal_per_100g=330.8,
        protein_g_per_100g=21.7,
        fat_g_per_100g=1.56,
        carbs_g_per_100g=55.23,
        fiber_g_per_100g=9.06,
        source="IFCT",
        category="dal",
    )
    kwargs.update(overrides)
    return kwargs


def test_ingredient_happy_path():
    ing = Ingredient(**_valid_ingredient_kwargs())
    assert ing.ingredient_id == "B021"
    assert ing.category == "dal"


def test_ingredient_rejects_macro_sum_over_tolerance():
    with pytest.raises(ValidationError):
        Ingredient(
            **_valid_ingredient_kwargs(
                protein_g_per_100g=40,
                fat_g_per_100g=40,
                carbs_g_per_100g=40,
                fiber_g_per_100g=0,
            )
        )


def test_ingredient_rejects_energy_over_999():
    with pytest.raises(ValidationError):
        Ingredient(**_valid_ingredient_kwargs(energy_kcal_per_100g=1000))


def test_ingredient_rejects_unknown_source():
    with pytest.raises(ValidationError):
        Ingredient(**_valid_ingredient_kwargs(source="FOO"))


def test_ingredient_rejects_unknown_category():
    with pytest.raises(ValidationError):
        Ingredient(**_valid_ingredient_kwargs(category="junk_food"))


def test_ingredient_rejects_empty_id():
    with pytest.raises(ValidationError):
        Ingredient(**_valid_ingredient_kwargs(ingredient_id=""))


def _valid_recipe_kwargs(**overrides):
    kwargs = dict(
        recipe_id="dal_tadka",
        name="Dal Tadka",
        ingredients=[RecipeIngredient(ingredient_id="B021", qty=100, unit="g")],
        oil_ghee=OilGhee(type="ghee", qty_g=10),
        servings=2,
        region_tag="north",
        meal_type="lunch",
        created_by="system",
    )
    kwargs.update(overrides)
    return kwargs


def test_recipe_happy_path():
    recipe = Recipe(**_valid_recipe_kwargs())
    assert recipe.oil_ghee.type == "ghee"
    assert recipe.is_fasting_safe is False


def test_recipe_rejects_zero_servings():
    with pytest.raises(ValidationError):
        Recipe(**_valid_recipe_kwargs(servings=0))


def test_recipe_ingredient_allows_zero_qty():
    # qty=0 is legal (a no-op ingredient); recipe math must treat it as inert.
    ri = RecipeIngredient(ingredient_id="B021", qty=0, unit="g")
    assert ri.qty == 0


def test_recipe_ingredient_rejects_negative_qty():
    with pytest.raises(ValidationError):
        RecipeIngredient(ingredient_id="B021", qty=-5, unit="g")


def test_beverage_defaults_region_and_meal_type():
    bev = Beverage(
        recipe_id="masala_chai",
        name="Masala Chai",
        ingredients=[],
        servings=1,
        created_by="system",
        base="tea",
        milk_ml=100,
        volume_ml=150,
    )
    assert bev.region_tag == "pan_india"
    assert bev.meal_type == "beverage"


def test_beverage_rejects_zero_volume():
    with pytest.raises(ValidationError):
        Beverage(
            recipe_id="x",
            name="x",
            servings=1,
            created_by="system",
            base="water",
            volume_ml=0,
        )


def _valid_profile_kwargs(**overrides):
    kwargs = dict(
        user_id="u1",
        name="Test User",
        age=28,
        sex="male",
        height_cm=175,
        weight_kg=70,
        body_type="mesomorph",
        activity_level="moderate",
        goal="maintain",
        dietary_pattern="vegetarian",
        eating_phase="maintenance",
    )
    kwargs.update(overrides)
    return kwargs


def test_user_profile_happy_path():
    profile = UserProfile(**_valid_profile_kwargs())
    assert profile.fasting_protocol == "none"
    assert profile.fasting_window is None


def test_user_profile_rejects_out_of_range_age():
    with pytest.raises(ValidationError):
        UserProfile(**_valid_profile_kwargs(age=200))


def test_user_profile_accepts_fasting_window():
    profile = UserProfile(
        **_valid_profile_kwargs(
            fasting_protocol="16_8",
            fasting_window=FastingWindow(start_hour=12, end_hour=20),
        )
    )
    assert profile.fasting_window.start_hour == 12


def test_household_unit_happy_path():
    unit = HouseholdUnit(
        user_id="u1",
        unit_name="katori",
        volume_ml=160,
        calibrated_at=datetime.now(timezone.utc),
        calibration_method="measured",
    )
    assert unit.volume_ml == 160


def test_household_unit_rejects_non_positive_volume():
    with pytest.raises(ValidationError):
        HouseholdUnit(
            user_id="u1",
            unit_name="katori",
            volume_ml=0,
            calibrated_at=datetime.now(timezone.utc),
            calibration_method="estimated",
        )


def test_log_entry_requires_exactly_one_reference():
    with pytest.raises(ValidationError):
        LogEntry(qty=1, unit="katori")
    with pytest.raises(ValidationError):
        LogEntry(recipe_id="dal_tadka", ingredient_id="B021", qty=1, unit="katori")


def test_log_entry_valid_with_recipe_id_only():
    entry = LogEntry(recipe_id="dal_tadka", qty=1, unit="katori")
    assert entry.ingredient_id is None


def test_meal_log_happy_path():
    log = MealLog(
        log_id="log1",
        user_id="u1",
        timestamp=datetime.now(timezone.utc),
        entries=[LogEntry(recipe_id="dal_tadka", qty=1, unit="katori")],
        computed_totals=NutritionTotals(
            energy_kcal=200, protein_g=10, fat_g=5, carbs_g=25, fiber_g=3
        ),
    )
    assert len(log.entries) == 1


def test_meal_log_rejects_empty_entries():
    with pytest.raises(ValidationError):
        MealLog(
            log_id="log1",
            user_id="u1",
            timestamp=datetime.now(timezone.utc),
            entries=[],
            computed_totals=NutritionTotals(
                energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0
            ),
        )
