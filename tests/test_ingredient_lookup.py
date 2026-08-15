import pytest

from src.core.ingredients import find_ingredient, load_ingredients


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


def test_toor_dal_has_sane_values(ingredients):
    ing = find_ingredient(ingredients, "toor dal")
    assert ing is not None
    assert 300 < ing.energy_kcal_per_100g < 360
    assert 18 < ing.protein_g_per_100g < 25
    assert 0 < ing.fat_g_per_100g < 5


def test_ghee_has_sane_values(ingredients):
    ing = find_ingredient(ingredients, "ghee")
    assert ing is not None
    assert 850 < ing.energy_kcal_per_100g < 920
    assert ing.fat_g_per_100g == pytest.approx(100, abs=1)
    assert ing.protein_g_per_100g == 0
    assert ing.carbs_g_per_100g == 0


def test_white_rice_has_sane_values(ingredients):
    ing = find_ingredient(ingredients, "white rice")
    assert ing is not None
    assert 330 < ing.energy_kcal_per_100g < 370
    assert 5 < ing.protein_g_per_100g < 10
    assert 70 < ing.carbs_g_per_100g < 85


def test_alias_lookup_resolves_to_same_ingredient_as_canonical_name(ingredients):
    by_alias = find_ingredient(ingredients, "arhar dal")
    by_canonical = find_ingredient(ingredients, "Red gram, dal")
    assert by_alias is not None
    assert by_canonical is not None
    assert by_alias.ingredient_id == by_canonical.ingredient_id


def test_lookup_is_case_insensitive(ingredients):
    assert find_ingredient(ingredients, "GHEE") is not None
    assert find_ingredient(ingredients, "gHee") is not None


def test_unknown_ingredient_returns_none(ingredients):
    assert find_ingredient(ingredients, "totally not a real food xyz") is None


def test_lookup_by_ingredient_id(ingredients):
    ing = find_ingredient(ingredients, "T013")
    assert ing is not None
    assert ing.name == "Ghee"


def test_all_loaded_ingredients_have_a_category(ingredients):
    assert all(ing.category for ing in ingredients.values())


def test_rejected_ingredients_file_is_written(ingredients):
    from src.core.ingredients import REJECTED_PATH

    assert REJECTED_PATH.exists()
