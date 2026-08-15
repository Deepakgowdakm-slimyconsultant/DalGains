import pytest

from src.core.ingredients import find_ingredient, load_ingredients


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


def test_toor_dal_has_sane_values(ingredients):
    row = find_ingredient(ingredients, "toor dal")
    assert row is not None
    assert 300 < row["energy_kcal_per_100g"] < 360
    assert 18 < row["protein_g_per_100g"] < 25
    assert 0 < row["fat_g_per_100g"] < 5


def test_ghee_has_sane_values(ingredients):
    row = find_ingredient(ingredients, "ghee")
    assert row is not None
    assert 850 < row["energy_kcal_per_100g"] < 920
    assert row["fat_g_per_100g"] == pytest.approx(100, abs=1)
    assert row["protein_g_per_100g"] == 0
    assert row["carbs_g_per_100g"] == 0


def test_white_rice_has_sane_values(ingredients):
    row = find_ingredient(ingredients, "white rice")
    assert row is not None
    assert 330 < row["energy_kcal_per_100g"] < 370
    assert 5 < row["protein_g_per_100g"] < 10
    assert 70 < row["carbs_g_per_100g"] < 85


def test_alias_lookup_resolves_to_same_ingredient_as_canonical_name(ingredients):
    by_alias = find_ingredient(ingredients, "arhar dal")
    by_canonical = find_ingredient(ingredients, "Red gram, dal")
    assert by_alias is not None
    assert by_canonical is not None
    assert by_alias["ingredient_id"] == by_canonical["ingredient_id"]


def test_lookup_is_case_insensitive(ingredients):
    assert find_ingredient(ingredients, "GHEE") is not None
    assert find_ingredient(ingredients, "gHee") is not None


def test_unknown_ingredient_returns_none(ingredients):
    assert find_ingredient(ingredients, "totally not a real food xyz") is None
