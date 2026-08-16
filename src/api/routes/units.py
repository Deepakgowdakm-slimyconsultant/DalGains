"""Household-unit calibration routes."""
from fastapi import APIRouter
from pydantic import BaseModel

from src.core.schemas import CalibrationMethod, HouseholdUnit
from src.core.units import calibrate_unit, get_calibrations

router = APIRouter(prefix="/units", tags=["units"])


class CalibrateUnitRequest(BaseModel):
    unit_name: str
    volume_ml: float
    method: CalibrationMethod


@router.get("/{user_id}", response_model=dict[str, HouseholdUnit])
def get_units(user_id: str) -> dict[str, HouseholdUnit]:
    return get_calibrations(user_id)


@router.post("/{user_id}", response_model=HouseholdUnit, status_code=201)
def post_unit(user_id: str, request: CalibrateUnitRequest) -> HouseholdUnit:
    return calibrate_unit(user_id, request.unit_name, request.volume_ml, request.method)
