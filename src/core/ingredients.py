"""Lookup helpers over the processed ingredients table.

Loading always validates every row through schemas.Ingredient. Rows that
fail validation are excluded from the returned set and written to
data/processed/ingredients_rejected.json with the failure reason instead
of being silently dropped.
"""
import json
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import ValidationError

from src.core.schemas import Ingredient

INGREDIENTS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "ingredients.parquet"
REJECTED_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "ingredients_rejected.json"

logger = logging.getLogger(__name__)


def load_ingredients(path: Path = INGREDIENTS_PATH) -> dict[str, Ingredient]:
    """Load and validate all ingredients, keyed by ingredient_id.

    Any row that fails Ingredient validation is excluded from the return
    value and appended to ingredients_rejected.json alongside the reason.
    """
    raw_df = pd.read_parquet(path)
    validated: dict[str, Ingredient] = {}
    rejected: list[dict] = []

    for record in raw_df.to_dict(orient="records"):
        record = dict(record)
        aliases = record.get("aliases")
        record["aliases"] = list(aliases) if aliases is not None else []
        # pandas stores a missing optional numeric as NaN, not None -- a
        # bare NaN fails Ingredient.per_piece_g's gt=0 constraint (NaN
        # compares False to everything). Normalize to None, its true value.
        per_piece_g = record.get("per_piece_g")
        if per_piece_g is not None and pd.isna(per_piece_g):
            record["per_piece_g"] = None
        try:
            ingredient = Ingredient(**record)
        except ValidationError as exc:
            reason = str(exc)
            rejected.append(
                {
                    "ingredient_id": record.get("ingredient_id"),
                    "name": record.get("name"),
                    "reason": reason,
                }
            )
            logger.warning(
                "Rejected ingredient %s (%s): %s",
                record.get("ingredient_id"),
                record.get("name"),
                reason,
            )
            continue
        validated[ingredient.ingredient_id] = ingredient

    REJECTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    REJECTED_PATH.write_text(json.dumps(rejected, indent=2))

    return validated


def find_ingredient(ingredients: dict[str, Ingredient], query: str) -> Optional[Ingredient]:
    """Look up an ingredient by id, exact name, or alias (case-insensitive)."""
    if query in ingredients:
        return ingredients[query]

    query_lower = query.strip().lower()

    for ingredient in ingredients.values():
        if ingredient.name.lower() == query_lower:
            return ingredient

    for ingredient in ingredients.values():
        if any(alias.lower() == query_lower for alias in ingredient.aliases):
            return ingredient

    return None
