"""Per-ingredient-category nutrition breakdown across a date range --
backs History's Patterns tab (protein sources, beverage-day %).

CLAUDE.md's "never hardcode dish-level calories" rule extends here: a
recipe's protein doesn't get attributed to a single category by
guessing from its name -- it gets split ingredient-by-ingredient, the
same way src.recipes.builder.compute_nutrition itself scales each
RecipeIngredient, just bucketed by Ingredient.category instead of
summed into one total.
"""
from datetime import date as date_cls
from datetime import timedelta
from typing import Optional

from src.core.ingredients import load_ingredients
from src.core.schemas import Ingredient, MealLog, NutritionTotals
from src.core.units import resolve_to_grams
from src.logging import store
from src.recipes.builder import OIL_GHEE_PROFILES, load_recipe

_ZERO = NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0)

# Recipe oil/ghee/butter doesn't correspond to a specific Ingredient row,
# but IngredientCategory already has an "oil_fat" bucket that's the
# natural home for it rather than leaving it uncategorized.
OIL_GHEE_CATEGORY = "oil_fat"


def _add(totals: NutritionTotals, kcal: float, protein: float, fat: float, carbs: float) -> NutritionTotals:
    return NutritionTotals(
        energy_kcal=totals.energy_kcal + kcal,
        protein_g=totals.protein_g + protein,
        fat_g=totals.fat_g + fat,
        carbs_g=totals.carbs_g + carbs,
        fiber_g=totals.fiber_g,
    )


def _entry_category_contributions(
    entry, ingredients: dict[str, Ingredient], user_id: str
) -> dict[str, NutritionTotals]:
    """category -> nutrition this one LogEntry contributed. Silently
    skips references to a recipe/ingredient that's since been deleted
    (an orphaned log entry) rather than failing the whole breakdown --
    same "don't let one bad day take down the page" posture as
    src.logging.aggregation.weekly_totals.
    """
    contributions: dict[str, NutritionTotals] = {}

    if entry.recipe_id:
        try:
            recipe = load_recipe(entry.recipe_id)
        except FileNotFoundError:
            return contributions

        per_serving_scale = entry.qty / recipe.servings
        for ri in recipe.ingredients:
            ingredient = ingredients.get(ri.ingredient_id)
            if ingredient is None:
                continue
            qty_g = resolve_to_grams(ingredient, ri.qty, ri.unit, user_id=user_id)
            scale = (qty_g / 100) * per_serving_scale
            existing = contributions.get(ingredient.category, _ZERO)
            contributions[ingredient.category] = _add(
                existing,
                ingredient.energy_kcal_per_100g * scale,
                ingredient.protein_g_per_100g * scale,
                ingredient.fat_g_per_100g * scale,
                ingredient.carbs_g_per_100g * scale,
            )

        if recipe.oil_ghee.qty_g > 0:
            oil_scale = (recipe.oil_ghee.qty_g / 100) * per_serving_scale
            profile = OIL_GHEE_PROFILES[recipe.oil_ghee.type]
            existing = contributions.get(OIL_GHEE_CATEGORY, _ZERO)
            contributions[OIL_GHEE_CATEGORY] = _add(
                existing, profile["kcal_per_100g"] * oil_scale, 0, profile["fat_g_per_100g"] * oil_scale, 0
            )
    else:
        ingredient = ingredients.get(entry.ingredient_id)
        if ingredient is None:
            return contributions
        qty_g = resolve_to_grams(ingredient, entry.qty, entry.unit, user_id=user_id)
        scale = qty_g / 100
        contributions[ingredient.category] = _add(
            _ZERO,
            ingredient.energy_kcal_per_100g * scale,
            ingredient.protein_g_per_100g * scale,
            ingredient.fat_g_per_100g * scale,
            ingredient.carbs_g_per_100g * scale,
        )

    return contributions


def _entry_is_beverage(entry, ingredients: dict[str, Ingredient]) -> bool:
    if entry.recipe_id:
        try:
            return load_recipe(entry.recipe_id).meal_type == "beverage"
        except FileNotFoundError:
            return False
    ingredient = ingredients.get(entry.ingredient_id)
    return ingredient is not None and ingredient.category == "beverage_base"


def category_breakdown(user_id: str, start: str, end: str, ingredients: Optional[dict[str, Ingredient]] = None) -> dict:
    """Sums nutrition by Ingredient.category across [start, end]
    (inclusive), plus a per-day beverage-kcal split -- an entry counts
    as "beverage" if it's a recipe with meal_type == "beverage" (the
    beverage-builder path) or a raw ingredient with category ==
    "beverage_base".
    """
    if ingredients is None:
        ingredients = load_ingredients()

    start_d = date_cls.fromisoformat(start)
    end_d = date_cls.fromisoformat(end)

    by_category: dict[str, NutritionTotals] = {}
    beverage_kcal_by_date: dict[str, float] = {}
    total_kcal_by_date: dict[str, float] = {}

    d = start_d
    while d <= end_d:
        date_str = d.isoformat()
        log = store.load_day(user_id, date_str)
        if isinstance(log, MealLog):
            total_kcal_by_date[date_str] = log.computed_totals.energy_kcal
            bev_kcal = 0.0
            for entry in log.entries:
                contributions = _entry_category_contributions(entry, ingredients, user_id)
                is_beverage = _entry_is_beverage(entry, ingredients)
                for category, totals in contributions.items():
                    existing = by_category.get(category, _ZERO)
                    by_category[category] = _add(
                        existing, totals.energy_kcal, totals.protein_g, totals.fat_g, totals.carbs_g
                    )
                    if is_beverage:
                        bev_kcal += totals.energy_kcal
            beverage_kcal_by_date[date_str] = bev_kcal
        d += timedelta(days=1)

    return {
        "by_category": by_category,
        "beverage_kcal_by_date": beverage_kcal_by_date,
        "total_kcal_by_date": total_kcal_by_date,
    }
