"""Beverage builder routes.

One concrete path per builder (chai, coffee, ...) rather than a single
dynamically-dispatched {kind} handler, so each request body gets full
FastAPI/pydantic validation and shows up correctly-typed in the OpenAPI
schema -- the {kind} segment from the Phase 3 brief's route description
is realized as these 8 literal sub-paths under /beverages/build/.
"""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.ingredients import load_ingredients
from src.core.schemas import Beverage
from src.recipes import beverages as bev

router = APIRouter(prefix="/beverages/build", tags=["beverages"])


class ChaiRequest(BaseModel):
    milk_ml: float
    milk_type: bev.MilkTypeArg
    sugar_tsp: float
    size_ml: float
    masala: bool = False
    plant_milk_kind: bev.PlantMilkKind = "soy"


class CoffeeRequest(BaseModel):
    style: Literal["filter", "instant", "espresso"]
    milk_ml: float
    milk_type: bev.MilkTypeArg
    sugar_tsp: float
    plant_milk_kind: bev.PlantMilkKind = "soy"


class LassiRequest(BaseModel):
    type: Literal["sweet", "salty", "mango"]
    yogurt_ml: float
    sugar_g: float
    fruit_g: float = 0


class ButtermilkRequest(BaseModel):
    volume_ml: float
    salted: bool = True
    spiced: bool = True


class NimbuPaaniRequest(BaseModel):
    volume_ml: float
    sugar_g: float
    salt: bool = True


class JuiceRequest(BaseModel):
    fruit: str
    volume_ml: float
    added_sugar_g: float = 0


class AlcoholRequest(BaseModel):
    type: Literal["beer", "wine", "whisky", "rum", "vodka", "gin", "feni", "toddy"]
    volume_ml: float
    abv_pct: float


class ProteinShakeRequest(BaseModel):
    protein_g: float
    milk_ml: float
    milk_type: bev.MilkTypeArg
    banana_g: float = 0
    peanut_butter_g: float = 0
    protein_source: Literal["whey_isolate", "whey_concentrate", "casein"] = "whey_isolate"
    plant_milk_kind: bev.PlantMilkKind = "soy"


@router.post("/chai", response_model=Beverage)
def build_chai(request: ChaiRequest) -> Beverage:
    return bev.build_chai(**request.model_dump())


@router.post("/coffee", response_model=Beverage)
def build_coffee(request: CoffeeRequest) -> Beverage:
    return bev.build_coffee(**request.model_dump())


@router.post("/lassi", response_model=Beverage)
def build_lassi(request: LassiRequest) -> Beverage:
    return bev.build_lassi(**request.model_dump())


@router.post("/buttermilk", response_model=Beverage)
def build_buttermilk(request: ButtermilkRequest) -> Beverage:
    return bev.build_buttermilk(**request.model_dump())


@router.post("/nimbu_paani", response_model=Beverage)
def build_nimbu_paani(request: NimbuPaaniRequest) -> Beverage:
    return bev.build_nimbu_paani(**request.model_dump())


@router.post("/juice", response_model=Beverage)
def build_juice(request: JuiceRequest) -> Beverage:
    try:
        return bev.build_juice(**request.model_dump(), ingredients=load_ingredients())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/alcohol", response_model=Beverage)
def build_alcohol(request: AlcoholRequest) -> Beverage:
    return bev.build_alcohol(**request.model_dump())


@router.post("/protein_shake", response_model=Beverage)
def build_protein_shake(request: ProteinShakeRequest) -> Beverage:
    return bev.build_protein_shake(**request.model_dump(), ingredients=load_ingredients())
