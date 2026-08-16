import logging

import pytest

import src.core.units as units
from src.core.ingredients import load_ingredients


@pytest.fixture(autouse=True)
def isolated_users_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")


@pytest.fixture(scope="module")
def ingredients():
    return load_ingredients()


# --- resolve_unit / calibrate_unit ----------------------------------------

def test_resolve_unit_returns_default_when_uncalibrated():
    value, source = units.resolve_unit("alice", "katori")
    assert value == 150.0
    assert source == "default"


def test_calibrate_then_resolve_returns_calibrated_value():
    units.calibrate_unit("alice", "katori", volume_ml=180, method="measured")
    value, source = units.resolve_unit("alice", "katori")
    assert value == 180
    assert source == "calibrated"


def test_calibration_is_per_user():
    units.calibrate_unit("alice", "katori", volume_ml=180, method="measured")
    value, source = units.resolve_unit("bob", "katori")
    assert value == 150.0
    assert source == "default"


def test_mutthi_default_is_a_mass_not_a_volume():
    value, source = units.resolve_unit("alice", "mutthi")
    assert value == 30.0
    assert source == "default"


def test_unknown_unit_with_no_calibration_raises():
    with pytest.raises(KeyError):
        units.resolve_unit("alice", "not_a_real_unit")


def test_calibrate_unit_persists_to_disk():
    unit = units.calibrate_unit("alice", "glass", volume_ml=220, method="photo_reference")
    path = units._units_path("alice")
    assert path.exists()
    assert unit.calibration_method == "photo_reference"


def test_recalibration_overwrites_previous_value():
    units.calibrate_unit("alice", "tsp", volume_ml=5, method="estimated")
    units.calibrate_unit("alice", "tsp", volume_ml=6, method="measured")
    value, source = units.resolve_unit("alice", "tsp")
    assert value == 6
    assert source == "calibrated"


# --- convert_to_grams -------------------------------------------------

def test_convert_to_grams_known_ingredient_id_density(ingredients):
    ghee = ingredients["T013"]
    grams = units.convert_to_grams(ghee, volume_ml=100)
    assert grams == pytest.approx(91.0)


def test_convert_to_grams_known_category_density(ingredients):
    # L002 (whole cow milk) isn't in DENSITY_BY_INGREDIENT_ID but its
    # category ("dairy") is.
    an_egg = next(i for i in ingredients.values() if i.category == "dairy" and i.ingredient_id != "L002")
    grams = units.convert_to_grams(an_egg, volume_ml=100)
    assert grams == pytest.approx(103.0)


def test_convert_to_grams_unknown_density_falls_back_to_water(ingredients, caplog):
    fruit = next(i for i in ingredients.values() if i.category == "fruit")
    with caplog.at_level(logging.WARNING):
        grams = units.convert_to_grams(fruit, volume_ml=100)
    assert grams == 100.0
    assert "falling back to 1.0" in caplog.text


def test_convert_to_grams_explicit_density_overrides_lookup(ingredients):
    ghee = ingredients["T013"]
    grams = units.convert_to_grams(ghee, volume_ml=100, density_g_per_ml=2.0)
    assert grams == 200.0


def test_convert_to_grams_zero_volume_is_zero_grams(ingredients):
    ghee = ingredients["T013"]
    assert units.convert_to_grams(ghee, volume_ml=0) == 0
