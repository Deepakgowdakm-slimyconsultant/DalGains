from typing import get_args

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from src.core.schemas import Ingredient, IngredientCategory, IngredientSource

SOURCES = list(get_args(IngredientSource))
CATEGORIES = list(get_args(IngredientCategory))

# Bounded to schema limits: each macro <= 26.25 keeps the sum comfortably
# under the 105g tolerance, so these strategies only ever produce valid
# ingredients.
_macro = st.floats(min_value=0, max_value=26, allow_nan=False)


@given(
    ingredient_id=st.text(min_size=1, max_size=12),
    name=st.text(min_size=1, max_size=40),
    aliases=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    energy=st.floats(min_value=0, max_value=999, allow_nan=False),
    protein=_macro,
    fat=_macro,
    carbs=_macro,
    fiber=_macro,
    source=st.sampled_from(SOURCES),
    category=st.sampled_from(CATEGORIES),
)
def test_ingredient_roundtrips_through_json(
    ingredient_id, name, aliases, energy, protein, fat, carbs, fiber, source, category
):
    ingredient = Ingredient(
        ingredient_id=ingredient_id,
        name=name,
        aliases=aliases,
        energy_kcal_per_100g=energy,
        protein_g_per_100g=protein,
        fat_g_per_100g=fat,
        carbs_g_per_100g=carbs,
        fiber_g_per_100g=fiber,
        source=source,
        category=category,
    )
    restored = Ingredient.model_validate_json(ingredient.model_dump_json())
    assert restored == ingredient


@given(
    protein=st.floats(min_value=30, max_value=100, allow_nan=False),
    fat=st.floats(min_value=30, max_value=100, allow_nan=False),
    carbs=st.floats(min_value=30, max_value=100, allow_nan=False),
    fiber=st.floats(min_value=30, max_value=100, allow_nan=False),
)
def test_ingredient_rejects_macro_sum_over_105(protein, fat, carbs, fiber):
    # Each field is individually within [0, 100], but four values >= 30
    # always sum to >= 120 > 105, so this must always raise.
    with pytest.raises(ValidationError):
        Ingredient(
            ingredient_id="X",
            name="X",
            energy_kcal_per_100g=100,
            protein_g_per_100g=protein,
            fat_g_per_100g=fat,
            carbs_g_per_100g=carbs,
            fiber_g_per_100g=fiber,
            source="IFCT",
            category="other",
        )


@given(energy=st.floats(min_value=999.01, max_value=100_000, allow_nan=False))
def test_ingredient_rejects_energy_over_999(energy):
    with pytest.raises(ValidationError):
        Ingredient(
            ingredient_id="X",
            name="X",
            energy_kcal_per_100g=energy,
            protein_g_per_100g=0,
            fat_g_per_100g=0,
            carbs_g_per_100g=0,
            fiber_g_per_100g=0,
            source="IFCT",
            category="other",
        )
