"""Pydantic models for every entity DalGains persists to disk.

RULE FOR ALL FUTURE CODE: any function that reads or writes a persisted
Ingredient, Recipe, Beverage, UserProfile, HouseholdUnit, or MealLog MUST
construct/validate it through the corresponding model below before using
its fields. Do not do `row["field"]` or `dict_from_json["field"]` on raw
loaded data -- wrap the row in its model first (`Ingredient(**row)`), then
use attribute access (`ingredient.energy_kcal_per_100g`). This is what
makes bad or malformed data fail loudly at the load boundary instead of
silently propagating into nutrition math.
"""
import logging
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ingredient
# ---------------------------------------------------------------------------

IngredientSource = Literal["IFCT", "USDA", "MANUAL"]
IngredientCategory = Literal[
    "grain",
    "dal",
    "vegetable",
    "fruit",
    "dairy",
    "meat",
    "fish",
    "egg",
    "oil_fat",
    "spice",
    "nut_seed",
    "sweetener",
    "beverage_base",
    "prepared",
    "other",
]

# Small tolerance above 100g/100g for measurement/rounding noise across
# independently-sampled nutrients.
MACRO_SUM_TOLERANCE_G = 105


class Ingredient(BaseModel):
    ingredient_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    energy_kcal_per_100g: float = Field(ge=0, le=999)
    protein_g_per_100g: float = Field(ge=0, le=100)
    fat_g_per_100g: float = Field(ge=0, le=100)
    carbs_g_per_100g: float = Field(ge=0, le=100)
    fiber_g_per_100g: float = Field(ge=0, le=100)
    source: IngredientSource
    category: IngredientCategory
    # Grams per single piece (e.g. one egg, one paratha) -- optional since
    # most ingredients are only ever measured by weight/volume. Required by
    # src.core.units.resolve_to_grams whenever a RecipeIngredient uses
    # unit="piece"; that function raises a clear error if it's missing.
    per_piece_g: Optional[float] = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _check_macro_sum(self) -> "Ingredient":
        total = (
            self.protein_g_per_100g
            + self.fat_g_per_100g
            + self.carbs_g_per_100g
            + self.fiber_g_per_100g
        )
        if total > MACRO_SUM_TOLERANCE_G:
            logger.warning(
                "Ingredient %s (%s): protein+fat+carbs+fiber=%.2fg/100g exceeds "
                "%dg tolerance",
                self.ingredient_id,
                self.name,
                total,
                MACRO_SUM_TOLERANCE_G,
            )
            raise ValueError(
                f"{self.ingredient_id}: macro sum {total:.2f}g/100g exceeds "
                f"{MACRO_SUM_TOLERANCE_G}g tolerance"
            )
        return self


# ---------------------------------------------------------------------------
# Recipe
# ---------------------------------------------------------------------------

RegionTag = Literal["north", "south", "east", "west", "northeast", "pan_india", "custom"]
MealType = Literal["breakfast", "lunch", "dinner", "snack", "beverage", "dessert", "fasting"]
OilGheeType = Literal["oil", "ghee", "butter", "none"]

# "custom" is a fixed sentinel meaning "already grams, no unit lookup" --
# not a way to reference an arbitrarily-named calibrated unit. A named
# custom unit (e.g. "my grandmother's bowl") would need its own field if
# that's wanted later; see src/core/units.py's resolve_to_grams.
UnitName = Literal[
    "g", "ml", "katori", "small_katori", "glass", "large_glass", "tsp",
    "tbsp", "mutthi", "plate", "piece", "custom",
]


class RecipeIngredient(BaseModel):
    ingredient_id: str = Field(min_length=1)
    # Strictly positive: Phase 2 allowed qty=0 as an explicit "inert
    # ingredient" no-op, but Phase 3's household-unit resolution makes a
    # zero-quantity entry meaningless (there's nothing to convert). "No
    # ingredient" is now expressed by omitting it from the list, not by a
    # zero-qty entry -- see beverages.py's builders for the guard pattern.
    qty: float = Field(gt=0)
    unit: UnitName


class OilGhee(BaseModel):
    type: OilGheeType = "none"
    qty_g: float = Field(ge=0, default=0)


class Recipe(BaseModel):
    recipe_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    oil_ghee: OilGhee = Field(default_factory=OilGhee)
    servings: int = Field(ge=1)
    region_tag: RegionTag
    meal_type: MealType
    is_fasting_safe: bool = False
    tags: list[str] = Field(default_factory=list)
    created_by: str = Field(min_length=1)
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Beverage (composes the Recipe shape with beverage-specific fields)
# ---------------------------------------------------------------------------

BeverageBaseKind = Literal[
    "water", "milk", "tea", "coffee", "yogurt", "juice", "alcohol",
    "protein_supplement", "other",
]
MilkType = Literal["none", "toned", "full_fat", "skim", "a2", "plant"]


class Beverage(Recipe):
    base: BeverageBaseKind
    milk_type: MilkType = "none"
    milk_ml: float = Field(ge=0, default=0)
    sugar_g: float = Field(ge=0, default=0)
    additives: list[str] = Field(default_factory=list)
    alcohol_pct: float = Field(ge=0, le=100, default=0)
    volume_ml: float = Field(gt=0)

    # Beverages default to pan-India / beverage meal type unless overridden.
    region_tag: RegionTag = "pan_india"
    meal_type: MealType = "beverage"


# ---------------------------------------------------------------------------
# UserProfile
# ---------------------------------------------------------------------------

Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
# Reused from Phase 1's tdee.py GOAL_PRESETS keys, kept for backward
# compatibility with calculate_targets(). eating_phase (below) is the
# more granular field src/core/planning.py actually drives off of --
# see the design-decision note in the Phase 2 summary.
Goal = Literal["cut", "maintain", "lean_bulk", "recomp"]
BodyType = Literal["ectomorph", "mesomorph", "endomorph", "mixed"]
DietaryPattern = Literal[
    "vegetarian", "vegan", "eggetarian", "non_vegetarian", "jain", "satvik", "custom"
]
EatingPhase = Literal[
    "maintenance", "cutting", "lean_bulk", "recomp", "reverse_diet", "refeed"
]
FastingProtocol = Literal[
    "none", "16_8", "18_6", "20_4", "omad", "5_2", "alternate_day",
    "ramadan", "ekadashi", "navratri", "custom",
]


class FastingWindow(BaseModel):
    start_hour: float = Field(ge=0, lt=24)
    end_hour: float = Field(ge=0, lt=24)


class UserProfile(BaseModel):
    user_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    age: int = Field(ge=5, le=120)
    sex: Sex
    height_cm: float = Field(ge=50, le=250)
    weight_kg: float = Field(ge=10, le=300)
    # Informational only -- see src/core/planning.py, must never feed TDEE math.
    body_type: BodyType
    activity_level: ActivityLevel
    goal: Goal
    target_body_fat_pct: Optional[float] = Field(default=None, ge=3, le=60)
    dietary_pattern: DietaryPattern
    eating_phase: EatingPhase
    fasting_protocol: FastingProtocol = "none"
    fasting_window: Optional[FastingWindow] = None
    medical_flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# HouseholdUnit
# ---------------------------------------------------------------------------

CalibrationMethod = Literal["photo_reference", "measured", "estimated"]


class HouseholdUnit(BaseModel):
    user_id: str = Field(min_length=1)
    unit_name: str = Field(min_length=1)
    volume_ml: float = Field(gt=0)
    calibrated_at: datetime
    calibration_method: CalibrationMethod


# ---------------------------------------------------------------------------
# MealLog
# ---------------------------------------------------------------------------


class LogEntry(BaseModel):
    recipe_id: Optional[str] = None
    ingredient_id: Optional[str] = None
    qty: float = Field(gt=0)
    # Free-form, not schemas.UnitName: for an ingredient_id entry this is a
    # real household unit (resolved via src.core.units.resolve_to_grams);
    # for a recipe_id entry (including beverages) it's the string
    # "serving" and qty is a servings count, which isn't a unit
    # resolve_to_grams has any business converting.
    unit: str = Field(min_length=1)
    # Set by src.logging.engine.log_entry() at log time, not by the
    # caller -- None here just means "not logged yet".
    timestamp: Optional[datetime] = None
    outside_eating_window: bool = False

    @model_validator(mode="after")
    def _check_exactly_one_reference(self) -> "LogEntry":
        if bool(self.recipe_id) == bool(self.ingredient_id):
            raise ValueError(
                "LogEntry must set exactly one of recipe_id or ingredient_id"
            )
        return self


class NutritionTotals(BaseModel):
    energy_kcal: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fiber_g: float = Field(ge=0)


class MealLog(BaseModel):
    # One MealLog per user per calendar day. log_id is that day's
    # "YYYY-MM-DD" string, which is also the filename stem in
    # data/logs/{user_id}/{log_id}.json (src/logging/store.py).
    log_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    # Last-modified time for this day's log, updated on every append/delete
    # -- not a single "when this happened" moment (each entry carries its
    # own timestamp for that).
    timestamp: datetime
    entries: list[LogEntry] = Field(min_length=1)
    computed_totals: NutritionTotals
    notes: Optional[str] = None
    # Free-form day-level labels, e.g. "diwali", "festival", "travel" --
    # src/insights/engine.py's festival_flex rule looks for a festival
    # marker here to suppress calorie warnings on days the user has
    # flagged as a celebration.
    tags: list[str] = Field(default_factory=list)


class QuarantinedLog(BaseModel):
    """What a corrupted-on-disk log file loads into instead of crashing."""

    path: str
    raw_content: str
    error: str
    quarantined_at: datetime


class DailyBreakdown(BaseModel):
    date: str
    totals: NutritionTotals
    target_kcal: Optional[float] = None
    adherence_pct: Optional[float] = None
    entry_count: int = Field(ge=0)


class WeeklySummary(BaseModel):
    user_id: str = Field(min_length=1)
    week_start_date: str
    week_end_date: str
    days: list[DailyBreakdown]
    averages: NutritionTotals
    target_adherence_pct: float = Field(ge=0, le=100)
    streak_days: int = Field(ge=0)
    notable_days: list[str] = Field(default_factory=list)
    # Populated by the insights engine (src/insights/), not by
    # src/logging/aggregation.py -- insights reads logs, so logging must
    # not import insights (would be circular).
    warnings: list[str] = Field(default_factory=list)
