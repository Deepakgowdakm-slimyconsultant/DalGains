"""Recipe persistence and nutrition computation.

CLAUDE.md architecture rule: dish-level calories are NEVER hardcoded here.
compute_nutrition always derives calories/macros by summing ingredient-level
values scaled by quantity, plus a documented Atwater-derived oil/ghee/butter
factor -- see OIL_GHEE_PROFILES below.
"""
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from src.core.ingredients import load_ingredients
from src.core.schemas import Ingredient, NutritionTotals, Recipe

RECIPES_DIR = Path(__file__).resolve().parents[2] / "data" / "recipes"

logger = logging.getLogger(__name__)

# Atwater-derived energy (kcal/100g) and fat fraction for the oil_ghee field.
# Oil and ghee are ~100% fat. Butter is ~81% fat (water/protein/lactose make
# up the rest); its factor is this session's design decision -- oil (884)
# and ghee (900) were specified directly, butter was not. See the Phase 2
# summary for this and other unspecified design choices.
OIL_GHEE_PROFILES = {
    "oil": {"kcal_per_100g": 884.0, "fat_g_per_100g": 100.0},
    "ghee": {"kcal_per_100g": 900.0, "fat_g_per_100g": 100.0},
    "butter": {"kcal_per_100g": 717.0, "fat_g_per_100g": 81.0},
    "none": {"kcal_per_100g": 0.0, "fat_g_per_100g": 0.0},
}


def create_recipe(recipe: Recipe) -> Path:
    """Persist a validated recipe to data/recipes/{recipe_id}.json."""
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    path = RECIPES_DIR / f"{recipe.recipe_id}.json"
    path.write_text(recipe.model_dump_json(indent=2))
    return path


def load_recipe(recipe_id: str) -> Recipe:
    """Load and validate a single recipe by id."""
    path = RECIPES_DIR / f"{recipe_id}.json"
    data = json.loads(path.read_text())
    return Recipe(**data)


def compute_nutrition(
    recipe: Recipe,
    servings: float = 1,
    ingredients: Optional[dict[str, Ingredient]] = None,
) -> NutritionTotals:
    """Nutrition totals for `servings` servings of `recipe` (default: one).

    Sums ingredient.per_100g_values * qty_g / 100 for every recipe
    ingredient (qty is interpreted as grams -- see the Phase 2 summary's
    design-decision note on unit handling), adds the oil_ghee contribution
    via OIL_GHEE_PROFILES, then scales the whole-recipe total down to a
    single serving (recipe.servings) and back up by the requested
    `servings` count. Values are left unrounded so
    nutrition(recipe, N) == nutrition(recipe, 1) * N exactly.
    """
    if ingredients is None:
        ingredients = load_ingredients()

    kcal = protein = fat = carbs = fiber = 0.0

    for ri in recipe.ingredients:
        ingredient = ingredients.get(ri.ingredient_id)
        if ingredient is None:
            raise KeyError(
                f"Recipe {recipe.recipe_id!r} references unknown "
                f"ingredient_id {ri.ingredient_id!r}"
            )
        scale = ri.qty / 100
        kcal += ingredient.energy_kcal_per_100g * scale
        protein += ingredient.protein_g_per_100g * scale
        fat += ingredient.fat_g_per_100g * scale
        carbs += ingredient.carbs_g_per_100g * scale
        fiber += ingredient.fiber_g_per_100g * scale

    profile = OIL_GHEE_PROFILES[recipe.oil_ghee.type]
    oil_scale = recipe.oil_ghee.qty_g / 100
    kcal += profile["kcal_per_100g"] * oil_scale
    fat += profile["fat_g_per_100g"] * oil_scale

    per_serving_scale = servings / recipe.servings

    return NutritionTotals(
        energy_kcal=kcal * per_serving_scale,
        protein_g=protein * per_serving_scale,
        fat_g=fat * per_serving_scale,
        carbs_g=carbs * per_serving_scale,
        fiber_g=fiber * per_serving_scale,
    )


def list_recipes(
    filter_by_tag: Optional[str] = None,
    filter_by_region: Optional[str] = None,
    fasting_only: bool = False,
) -> list[Recipe]:
    """List recipes in data/recipes/, optionally filtered."""
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    recipes = []
    for path in sorted(RECIPES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text())
            recipe = Recipe(**data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("Skipping invalid recipe file %s: %s", path, exc)
            continue
        if filter_by_tag is not None and filter_by_tag not in recipe.tags:
            continue
        if filter_by_region is not None and recipe.region_tag != filter_by_region:
            continue
        if fasting_only and not recipe.is_fasting_safe:
            continue
        recipes.append(recipe)
    return recipes
