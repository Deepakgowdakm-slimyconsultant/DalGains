"""Recipe CRUD + nutrition computation routes."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.auth.dependencies import get_current_user
from src.auth.schemas import User
from src.core.ingredients import load_ingredients
from src.core.schemas import NutritionTotals, Recipe
from src.recipes.builder import (
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
def post_recipe(recipe: Recipe, current_user: User = Depends(get_current_user)) -> Recipe:
    # Recipes are shared catalog data, not owned by one user -- this only
    # requires *being* logged in, not an ownership check, but it must
    # require that much: recipe create/update/delete used to have no
    # auth at all, which on a publicly reachable deployment would let
    # any anonymous caller mutate the shared catalog.
    try:
        load_recipe(recipe.recipe_id)
    except FileNotFoundError:
        pass
    else:
        raise HTTPException(status_code=409, detail=f"recipe_id {recipe.recipe_id!r} already exists")
    create_recipe(recipe)
    return recipe


@router.put("/{recipe_id}", response_model=Recipe)
def put_recipe(recipe_id: str, recipe: Recipe, current_user: User = Depends(get_current_user)) -> Recipe:
    if recipe.recipe_id != recipe_id:
        raise HTTPException(status_code=400, detail="recipe_id in body must match path")
    try:
        load_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")
    create_recipe(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204, response_class=Response)
def delete_recipe_route(recipe_id: str, current_user: User = Depends(get_current_user)) -> None:
    try:
        delete_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")


@router.get("/{recipe_id}/nutrition", response_model=NutritionTotals)
def get_recipe_nutrition(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    servings: float = Query(default=1, gt=0),
) -> NutritionTotals:
    try:
        recipe = load_recipe(recipe_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown recipe_id {recipe_id!r}")

    try:
        return compute_nutrition(
            recipe, servings=servings, ingredients=load_ingredients(), user_id=current_user.id
        )
    except KeyError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
