"""Household-unit calibration and volume/mass conversion.

Calibrations are persisted per-user to data/users/{user_id}/household_units.json,
following the same "flat file under data/" convention as src/recipes/builder.py.

DEFAULT_UNITS_ML values are ml for every unit except "mutthi": a dry-grains
handful has no stable volume, so it's resolved as a mass directly (see
resolve_to_grams and src/core/densities.py's MUTTHI_G_* tables), not a
volume needing density conversion.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.core.densities import (
    DEFAULT_DENSITY_G_PER_ML,
    DENSITY_BY_CATEGORY,
    DENSITY_BY_INGREDIENT_ID,
    MUTTHI_DEFAULT_G,
    MUTTHI_G_BY_CATEGORY,
    MUTTHI_G_BY_INGREDIENT_ID,
)
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
    "mutthi": MUTTHI_DEFAULT_G,
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


def resolve_unit(user_id: Optional[str], unit_name: str) -> tuple[float, str]:
    """Resolves unit_name to (value, source).

    source is "calibrated" if user_id is given and has its own calibration
    on file, else "default". user_id=None skips the calibration lookup
    entirely (used by resolve_to_grams when no user is in context). The
    value is ml for every unit except "mutthi", which is grams (see module
    docstring).
    """
    if user_id is not None:
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
            "No known density for %s (%s, category=%s); falling back to %.1f g/ml",
            ingredient.ingredient_id,
            ingredient.name,
            ingredient.category,
            DEFAULT_DENSITY_G_PER_ML,
        )
        density = DEFAULT_DENSITY_G_PER_ML

    return volume_ml * density


def resolve_to_grams(
    ingredient: Ingredient, qty: float, unit: str, user_id: Optional[str] = None
) -> float:
    """Converts qty of `unit` for `ingredient` into grams.

    This is the single entry point recipe/log math should call before
    scaling nutrition by weight -- it's what actually connects a recipe's
    "1 katori dal" to the ingredient DB's per-100g values, resolving the
    user's own calibration when user_id is given (else the default table).

    - "g": returned as-is.
    - "piece": qty * ingredient.per_piece_g; raises ValueError if the
      ingredient has no per_piece_g set.
    - "mutthi": a mass lookup (by ingredient_id, then category, then a
      flat default) -- never goes through density, since a handful isn't
      a fixed volume.
    - "custom": treated as already-grams (documented sentinel -- see
      schemas.UnitName).
    - anything else ("ml" or a named household unit): resolved to ml via
      resolve_unit(), then to grams via convert_to_grams()'s density
      lookup.
    """
    if unit == "g":
        return qty

    if unit == "piece":
        if ingredient.per_piece_g is None:
            raise ValueError(
                f"{ingredient.ingredient_id} ({ingredient.name}) has no "
                "per_piece_g set; can't resolve unit='piece'"
            )
        return qty * ingredient.per_piece_g

    if unit == "mutthi":
        grams_per_mutthi = (
            MUTTHI_G_BY_INGREDIENT_ID.get(ingredient.ingredient_id)
            or MUTTHI_G_BY_CATEGORY.get(ingredient.category)
            or MUTTHI_DEFAULT_G
        )
        return qty * grams_per_mutthi

    if unit == "custom":
        return qty

    if unit == "ml":
        volume_ml = qty
    else:
        unit_ml, _source = resolve_unit(user_id, unit)
        volume_ml = qty * unit_ml

    return convert_to_grams(ingredient, volume_ml)
