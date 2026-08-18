"""Ingredient search/lookup routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.auth.dependencies import get_current_user
from src.auth.schemas import User
from src.core.ingredients import load_ingredients
from src.core.schemas import Ingredient, IngredientCategory, NutritionTotals
from src.core.units import resolve_to_grams

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[Ingredient])
def search_ingredients(
    query: Optional[str] = Query(default=None, description="Substring match against name/aliases"),
    category: Optional[IngredientCategory] = Query(default=None),
) -> list[Ingredient]:
    results = list(load_ingredients().values())

    if category is not None:
        results = [i for i in results if i.category == category]

    if query:
        q = query.lower()
        results = [
            i for i in results if q in i.name.lower() or any(q in a.lower() for a in i.aliases)
        ]

    return results


@router.get("/{ingredient_id}", response_model=Ingredient)
def get_ingredient(ingredient_id: str) -> Ingredient:
    ingredient = load_ingredients().get(ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail=f"Unknown ingredient_id {ingredient_id!r}")
    return ingredient


@router.get("/{ingredient_id}/nutrition", response_model=NutritionTotals)
def get_ingredient_nutrition(
    ingredient_id: str,
    qty: float = Query(..., gt=0),
    unit: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> NutritionTotals:
    """Preview-only: the same qty+unit -> grams resolution the logging
    engine uses (src.core.units.resolve_to_grams, honoring the user's
    calibrated units), without writing anything. Lets the frontend show
    real nutrition before a log entry is confirmed (CLAUDE.md: AI/derived
    estimates must be shown before being logged, never silently accepted).

    Calibration always comes from the caller's own session, never a
    client-supplied user_id -- that used to be an optional query param,
    which would have let any caller read another user's calibrated
    household-unit sizes through this endpoint.
    """
    ingredient = load_ingredients().get(ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail=f"Unknown ingredient_id {ingredient_id!r}")

    try:
        qty_g = resolve_to_grams(ingredient, qty, unit, user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    scale = qty_g / 100
    return NutritionTotals(
        energy_kcal=ingredient.energy_kcal_per_100g * scale,
        protein_g=ingredient.protein_g_per_100g * scale,
        fat_g=ingredient.fat_g_per_100g * scale,
        carbs_g=ingredient.carbs_g_per_100g * scale,
        fiber_g=ingredient.fiber_g_per_100g * scale,
    )
