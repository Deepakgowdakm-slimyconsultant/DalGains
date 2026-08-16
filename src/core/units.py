"""Household-unit calibration and volume/mass conversion.

Calibrations are persisted per-user to data/users/{user_id}/household_units.json,
following the same "flat file under data/" convention as src/recipes/builder.py.

DEFAULT_UNITS_ML values are ml for every unit except "mutthi": a dry-grains
handful has no stable volume, so its default (30) is grams directly, not ml.
resolve_unit() and convert_to_grams() both treat it as a mass, not a volume
needing density conversion.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.core.schemas import CalibrationMethod, HouseholdUnit, Ingredient

logger = logging.getLogger(__name__)

USERS_DIR = Path(__file__).resolve().parents[2] / "data" / "users"

DEFAULT_UNITS_ML = {
    "katori": 150.0,
    "small_katori": 100.0,
    "glass": 200.0,
    "large_glass": 300.0,
    "tsp": 5.0,
    "tbsp": 15.0,
    "plate": 400.0,
}
# mutthi (a dry handful) is measured as a mass, not a volume -- see the
# module docstring. Kept in its own table so callers that iterate
# DEFAULT_UNITS_ML don't have to guard against a stray g-vs-ml unit.
MASS_ONLY_UNITS_G = {
    "mutthi": 30.0,
}

# Density (g/ml), keyed by ingredient_id for a curated set of common items
# named directly in the Phase 2 brief, with a coarser category-level table
# underneath. Starting point, not exhaustive -- anything not covered by
# either falls back to 1.0 g/ml (water-equivalent) with a logged warning.
DENSITY_BY_INGREDIENT_ID = {
    "A015": 0.85,  # Rice, raw, milled (cooked-rice-equivalent approx)
    "B021": 1.0,  # Red gram, dal (toor dal, cooked)
    "T013": 0.91,  # Ghee
    "L002": 1.03,  # Milk, whole, Cow
    "USDA007": 1.03,  # Curd
}
DENSITY_BY_CATEGORY = {
    "oil_fat": 0.92,
    "dairy": 1.03,
    "dal": 1.0,
    "grain": 0.85,
}


def _units_path(user_id: str) -> Path:
    return USERS_DIR / user_id / "household_units.json"


def _load_calibrations(user_id: str) -> dict[str, dict]:
    path = _units_path(user_id)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def calibrate_unit(
    user_id: str, unit_name: str, volume_ml: float, method: CalibrationMethod
) -> HouseholdUnit:
    """Records a user-specific calibration for unit_name, persisted to disk."""
    unit = HouseholdUnit(
        user_id=user_id,
        unit_name=unit_name,
        volume_ml=volume_ml,
        calibrated_at=datetime.now(timezone.utc),
        calibration_method=method,
    )

    path = _units_path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _load_calibrations(user_id)
    data[unit_name] = json.loads(unit.model_dump_json())
    path.write_text(json.dumps(data, indent=2))

    return unit


def resolve_unit(user_id: str, unit_name: str) -> tuple[float, str]:
    """Resolves unit_name to (value, source).

    source is "calibrated" if the user has their own calibration on file,
    else "default". The value is ml for every unit except "mutthi", which
    is grams (see module docstring).
    """
    data = _load_calibrations(user_id)
    if unit_name in data:
        return HouseholdUnit(**data[unit_name]).volume_ml, "calibrated"

    if unit_name in DEFAULT_UNITS_ML:
        return DEFAULT_UNITS_ML[unit_name], "default"
    if unit_name in MASS_ONLY_UNITS_G:
        return MASS_ONLY_UNITS_G[unit_name], "default"

    raise KeyError(f"Unknown household unit {unit_name!r} and no calibration on file for {user_id!r}")


def convert_to_grams(
    ingredient: Ingredient, volume_ml: float, density_g_per_ml: Optional[float] = None
) -> float:
    """Converts a volume (ml) of `ingredient` to grams via a density lookup.

    Falls back to 1.0 g/ml (water-equivalent) with a logged warning if no
    density is known for this ingredient or its category.
    """
    if density_g_per_ml is not None:
        density = density_g_per_ml
    elif ingredient.ingredient_id in DENSITY_BY_INGREDIENT_ID:
        density = DENSITY_BY_INGREDIENT_ID[ingredient.ingredient_id]
    elif ingredient.category in DENSITY_BY_CATEGORY:
        density = DENSITY_BY_CATEGORY[ingredient.category]
    else:
        logger.warning(
            "No known density for %s (%s, category=%s); falling back to 1.0 g/ml",
            ingredient.ingredient_id,
            ingredient.name,
            ingredient.category,
        )
        density = 1.0

    return volume_ml * density
