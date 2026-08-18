"""Meal logging routes."""
from typing import Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.schemas import LogEntry, MealLog, NutritionTotals, QuarantinedLog, WeeklySummary
from src.logging import engine

router = APIRouter(prefix="/logs", tags=["logs"])


class TagDayRequest(BaseModel):
    tag: str


class CategoryBreakdown(BaseModel):
    by_category: dict[str, NutritionTotals]
    beverage_kcal_by_date: dict[str, float]
    total_kcal_by_date: dict[str, float]


@router.post("/{user_id}/entries", response_model=MealLog, status_code=201)
def post_entry(user_id: str, entry: LogEntry) -> MealLog:
    # entry.timestamp is the client's chosen "when" (e.g. logging lunch
    # after the fact, or against a one-tap meal-slot time) -- honor it
    # when given, same as engine.log_entry's own default of "now".
    try:
        return engine.log_entry(user_id, entry, when=entry.timestamp)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{user_id}/day/{date}", response_model=Union[MealLog, QuarantinedLog])
def get_day(user_id: str, date: str) -> Union[MealLog, QuarantinedLog]:
    result = engine.get_day(user_id, date)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No log for {user_id!r} on {date!r}")
    return result


@router.post("/{user_id}/day/{date}/tags", response_model=MealLog)
def post_day_tag(user_id: str, date: str, request: TagDayRequest) -> MealLog:
    """Adds a free-form tag (e.g. "diwali") to a day that already has at
    least one entry -- e.g. History's "mark as a festival day" action.
    Backs src.insights.engine's festival_flex rule and History's
    festival-days filter, neither of which had any way to actually set a
    tag before this route existed.
    """
    try:
        return engine.tag_day(user_id, date, request.tag)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{user_id}/dates", response_model=list[str])
def get_logged_dates(user_id: str) -> list[str]:
    """Every date this user has a log for, most recent first -- backs
    History's infinite-scroll timeline (paging through real dates
    instead of guessing how far back logs exist)."""
    return engine.list_logged_dates(user_id)


@router.get("/{user_id}/range/{start}/{end}", response_model=list[Union[MealLog, QuarantinedLog]])
def get_range(user_id: str, start: str, end: str) -> list[Union[MealLog, QuarantinedLog]]:
    """All logs between start and end (both YYYY-MM-DD, inclusive) --
    backs History's trend charts and personal-patterns stats, which need
    many days at once rather than one day per request."""
    try:
        return engine.get_range(user_id, start, end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("/{user_id}/category_breakdown/{start}/{end}", response_model=CategoryBreakdown)
def get_category_breakdown(user_id: str, start: str, end: str) -> CategoryBreakdown:
    """True per-ingredient-category nutrition attribution across a date
    range -- backs History's Patterns tab (protein sources, beverage-day
    %). Every entry resolves down to its actual ingredient composition
    (recipes ingredient-by-ingredient, same math compute_nutrition
    uses) rather than guessing a category from the entry's display name.
    """
    try:
        result = engine.category_breakdown(user_id, start, end)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return CategoryBreakdown(**result)


@router.get("/{user_id}/week/{week_ending}", response_model=WeeklySummary)
def get_week(user_id: str, week_ending: str) -> WeeklySummary:
    try:
        return engine.get_week(user_id, week_ending)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.delete("/{user_id}/entries/{log_id}/{index}", response_model=Optional[MealLog])
def delete_entry(user_id: str, log_id: str, index: int) -> Optional[MealLog]:
    try:
        return engine.delete_entry(user_id, log_id, index)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except (ValueError, IndexError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
