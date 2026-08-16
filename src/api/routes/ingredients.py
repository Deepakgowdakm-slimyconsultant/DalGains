"""Ingredient search/lookup routes."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.core.ingredients import load_ingredients
from src.core.schemas import Ingredient, IngredientCategory

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
