"""Recipe CRUD + nutrition computation routes."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from src.core.ingredients import load_ingredients
from src.core.schemas import NutritionTotals, Recipe
from src.recipes.builder import (
    RECIPES_DIR,
    compute_nutrition,
    create_recipe,
    delete_recipe,
    list_recipes,
    load_recipe,
)

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[Recipe])
def get_recipes(
    tag: Optional[str] = Query(default=None),
    region: Optional[str] = Query(default=None),
    fasting_only: bool = Query(default=False),
) -> list[Recipe]:
    return list_recipes(filter_by_tag=tag, filter_by_region=region, fasting_only=fasting_only)


@router.get("/{recipe_id}", response_model=Recipe)
def get_recipe(recipe_id: str) -> Recipe:
    try:
        return load_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")


@router.post("", response_model=Recipe, status_code=201)
def post_recipe(recipe: Recipe) -> Recipe:
    if (RECIPES_DIR / f"{recipe.recipe_id}.json").exists():
        raise HTTPException(status_code=409, detail=f"recipe_id {recipe.recipe_id!r} already exists")
    create_recipe(recipe)
    return recipe


@router.put("/{recipe_id}", response_model=Recipe)
def put_recipe(recipe_id: str, recipe: Recipe) -> Recipe:
    if recipe.recipe_id != recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id in body must match path")
    try:
        load_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")
    create_recipe(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204, response_class=Response)
def delete_recipe_route(recipe_id: str) -> None:
    try:
        delete_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")


@router.get("/{recipe_id}/nutrition", response_model=NutritionTotals)
def get_recipe_nutrition(
    recipe_id: str,
    user_id: Optional[str] = Query(default=None),
    servings: float = Query(default=1, gt=0),
) -> NutritionTotals:
    try:
        recipe = load_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")

    try:
        return compute_nutrition(
            recipe, servings=servings, ingredients=load_ingredients(), user_id=user_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
