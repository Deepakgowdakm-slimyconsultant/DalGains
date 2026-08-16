"""Meal logging routes."""
from typing import Optional, Union

from fastapi import APIRouter, HTTPException

from src.core.schemas import LogEntry, MealLog, QuarantinedLog, WeeklySummary
from src.logging import engine

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("/{user_id}/entries", response_model=MealLog, status_code=201)
def post_entry(user_id: str, entry: LogEntry) -> MealLog:
    try:
        return engine.log_entry(user_id, entry)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{user_id}/day/{date}", response_model=Union[MealLog, QuarantinedLog])
def get_day(user_id: str, date: str) -> Union[MealLog, QuarantinedLog]:
    result = engine.get_day(user_id, date)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No log for {user_id!r} on {date!r}")
    return result


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
