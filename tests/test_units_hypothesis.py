import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import src.core.units as units
from src.core.ingredients import load_ingredients

INGREDIENTS = load_ingredients()
INGREDIENT_LIST = list(INGREDIENTS.values())


@given(
    ingredient=st.sampled_from(INGREDIENT_LIST),
    volume_ml=st.floats(min_value=1, max_value=2000, allow_nan=False),
)
def test_convert_to_grams_is_proportional_to_volume(ingredient, volume_ml):
    grams = units.convert_to_grams(ingredient, volume_ml)
    per_100ml = grams * (100 / volume_ml)
    # Density is fixed per ingredient, so grams-per-100ml should be the
    # same regardless of which volume_ml we actually converted.
    reference = units.convert_to_grams(ingredient, 100)
    assert per_100ml == pytest.approx(reference, rel=1e-9)


@given(
    # Unique per example so examples never collide on disk -- each example
    # is still a self-contained calibrate-then-read within one call.
    user_id=st.uuids().map(str),
    unit_name=st.uuids().map(str),
    volume_ml=st.floats(min_value=0.01, max_value=5000, allow_nan=False),
    method=st.sampled_from(["photo_reference", "measured", "estimated"]),
)
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_calibrate_then_resolve_roundtrips(user_id, unit_name, volume_ml, method, tmp_path, monkeypatch):
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")
    units.calibrate_unit(user_id, unit_name, volume_ml=volume_ml, method=method)
    value, source = units.resolve_unit(user_id, unit_name)
    assert value == pytest.approx(volume_ml)
    assert source == "calibrated"
