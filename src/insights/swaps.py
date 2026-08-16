"""Swap suggestions: draw from the user's own logged history first.

Only falls back to the seeded recipe library (data/recipes/) if the user
has fewer than MIN_LOGGED_FOR_PERSONAL_SWAPS unique foods (recipe or
ingredient) logged in the lookback window -- there isn't enough personal
history yet to suggest from. This is the "recommend from foods you
actually eat" principle from the Phase 3 brief.
"""
from datetime import date as date_cls
from datetime import timedelta
from typing import Optional

from src.core.ingredients import load_ingredients
from src.core.schemas import Ingredient, MealLog
from src.logging import engine
from src.recipes.builder import compute_nutrition, list_recipes, load_recipe

MIN_LOGGED_FOR_PERSONAL_SWAPS = 20
LOOKBACK_DAYS = 30


def _recent_unique_food_refs(user_id: str, as_of_date: str) -> list[tuple[str, str]]:
    """Distinct ("recipe"|"ingredient", id) pairs logged in the lookback window."""
    end = date_cls.fromisoformat(as_of_date)
    start = end - timedelta(days=LOOKBACK_DAYS)
    logs = engine.get_range(user_id, start.isoformat(), end.isoformat())

    seen: list[tuple[str, str]] = []
    for log in logs:
        if not isinstance(log, MealLog):
            continue
        for entry in log.entries:
            ref = ("recipe", entry.recipe_id) if entry.recipe_id else ("ingredient", entry.ingredient_id)
            if ref not in seen:
                seen.append(ref)
    return seen


def _protein_per_serving(
    ref: tuple[str, str], ingredients: dict[str, Ingredient]
) -> Optional[tuple[str, float]]:
    kind, food_id = ref
    if kind == "recipe":
        try:
            recipe = load_recipe(food_id)
        except FileNotFoundError:
            return None
        totals = compute_nutrition(recipe, servings=1, ingredients=ingredients)
        return recipe.name, totals.protein_g

    ingredient = ingredients.get(food_id)
    if ingredient is None:
        return None
    return ingredient.name, ingredient.protein_g_per_100g


def suggest_protein_swaps(user_id: str, as_of_date: str, limit: int = 3) -> list[str]:
    """Concrete protein-boosting swap suggestions, highest-protein first."""
    ingredients = load_ingredients()
    refs = _recent_unique_food_refs(user_id, as_of_date)

    if len(refs) >= MIN_LOGGED_FOR_PERSONAL_SWAPS:
        source_label = "you've logged before"
        candidates = [c for c in (_protein_per_serving(r, ingredients) for r in refs) if c]
    else:
        source_label = "DalGains recipes"
        candidates = [
            (recipe.name, compute_nutrition(recipe, servings=1, ingredients=ingredients).protein_g)
            for recipe in list_recipes()
        ]

    candidates.sort(key=lambda c: c[1], reverse=True)
    return [
        f"{name} ({source_label}) adds about {protein:.0f}g protein per serving"
        for name, protein in candidates[:limit]
        if protein > 0
    ]
