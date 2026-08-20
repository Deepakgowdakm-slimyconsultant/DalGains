"""Insights routes."""
from datetime import date as date_cls
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import require_own_user
from src.insights.engine import generate_insights
from src.insights.models import Insight

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/{user_id}", response_model=list[Insight])
def get_insights(as_of: Optional[str] = Query(default=None), user_id: str = Depends(require_own_user)) -> list[Insight]:
    as_of_date = as_of or date_cls.today().isoformat()
    return generate_insights(user_id, as_of_date)
