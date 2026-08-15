"""Ad-hoc beverage builders.

Unlike src/recipes/builder.py (recipes authored once and saved to disk),
beverages are usually assembled on the spot from a handful of parameters
("chai with toned milk, half a teaspoon of sugar"). Every builder here
returns an in-memory Beverage; call src.recipes.builder.create_recipe() on
the result if it should be persisted.

All nutrition still flows through src.recipes.builder.compute_nutrition() --
every builder works by choosing real ingredient_ids and quantities, never
by hardcoding a beverage's calories. Alcohol is modeled as an ingredient
(MANUAL004 "Ethanol, pure", 700 kcal/100g = the spec's 7 kcal/g) precisely
so build_alcohol needs no separate nutrition path.

Design decisions not fully specified by the Phase 2 brief (flagged here and
in the Phase 2 summary):
  - milk_type="plant" is ambiguous between soy/almond/oat; builders that
    accept milk_type also take plant_milk_kind (default "soy").
  - build_protein_shake's protein source defaults to whey isolate
    (protein_source="whey_isolate"); concentrate/casein are opt-in.
  - Dilution ratios (coffee's water base, lassi's added water, buttermilk's
    curd fraction, nimbu paani's lemon-juice fraction) are typical
    home-kitchen ratios, not measured values -- see the constants below.
  - Residual carbs for beer/wine/toddy (RESIDUAL_CARBS_G_PER_100ML) are
    typical published averages, not per-brand values.
"""
import uuid
from typing import Literal, Optional

from src.core.ingredients import find_ingredient, load_ingredients
from src.core.schemas import Beverage, Ingredient, RecipeIngredient

TSP_TO_G_SUGAR = 4.2

ETHANOL_KCAL_PER_G = 7.0  # matches MANUAL004's 700 kcal/100g
ETHANOL_DENSITY_G_PER_ML = 0.789

FILTER_COFFEE_BASE_ML = 100.0
LASSI_DILUTION_ML = 50.0
BUTTERMILK_CURD_FRACTION = 0.3
NIMBU_PAANI_LEMON_FRACTION = 0.12
DEFAULT_SHAKE_VOLUME_ML = 250.0

MilkTypeArg = Literal["none", "toned", "full_fat", "skim", "a2", "plant"]
PlantMilkKind = Literal["soy", "almond", "oat"]

MILK_TYPE_INGREDIENT = {
    "toned": "USDA001",
    "full_fat": "L002",  # Milk, whole, Cow (IFCT)
    "skim": "USDA002",
    "a2": "USDA003",
    "none": None,
}
PLANT_MILK_INGREDIENT = {
    "soy": "USDA004",
    "almond": "USDA005",
    "oat": "USDA006",
}

PROTEIN_SOURCE_INGREDIENT = {
    "whey_isolate": "MANUAL001",
    "whey_concentrate": "MANUAL002",
    "casein": "MANUAL003",
}

ALCOHOL_TYPE = Literal["beer", "wine", "whisky", "rum", "vodka", "gin", "feni", "toddy"]
RESIDUAL_CARBS_G_PER_100ML = {
    "beer": 3.6,
    "wine": 2.6,
    "toddy": 3.0,
    "whisky": 0.0,
    "rum": 0.0,
    "vodka": 0.0,
    "gin": 0.0,
    "feni": 0.0,
}


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _milk_ingredient_id(milk_type: MilkTypeArg, plant_milk_kind: PlantMilkKind) -> Optional[str]:
    if milk_type == "plant":
        return PLANT_MILK_INGREDIENT[plant_milk_kind]
    return MILK_TYPE_INGREDIENT[milk_type]


def build_chai(
    milk_ml: float,
    milk_type: MilkTypeArg,
    sugar_tsp: float,
    size_ml: float,
    masala: bool = False,
    plant_milk_kind: PlantMilkKind = "soy",
) -> Beverage:
    ingredients = []
    milk_id = _milk_ingredient_id(milk_type, plant_milk_kind)
    if milk_id and milk_ml > 0:
        ingredients.append(RecipeIngredient(ingredient_id=milk_id, qty=milk_ml, unit="g"))
    if sugar_tsp > 0:
        ingredients.append(
            RecipeIngredient(ingredient_id="USDA009", qty=sugar_tsp * TSP_TO_G_SUGAR, unit="g")
        )

    return Beverage(
        recipe_id=_new_id("chai"),
        name="Masala Chai" if masala else "Chai",
        ingredients=ingredients,
        servings=1,
        created_by="system",
        base="tea",
        milk_type=milk_type,
        milk_ml=milk_ml,
        sugar_g=sugar_tsp * TSP_TO_G_SUGAR,
        additives=["cardamom", "ginger", "cloves"] if masala else [],
        volume_ml=size_ml,
    )


def build_coffee(
    style: Literal["filter", "instant", "espresso"],
    milk_ml: float,
    milk_type: MilkTypeArg,
    sugar_tsp: float,
    plant_milk_kind: PlantMilkKind = "soy",
) -> Beverage:
    ingredients = []
    milk_id = _milk_ingredient_id(milk_type, plant_milk_kind)
    if milk_id and milk_ml > 0:
        ingredients.append(RecipeIngredient(ingredient_id=milk_id, qty=milk_ml, unit="g"))
    if sugar_tsp > 0:
        ingredients.append(
            RecipeIngredient(ingredient_id="USDA009", qty=sugar_tsp * TSP_TO_G_SUGAR, unit="g")
        )

    return Beverage(
        recipe_id=_new_id("coffee"),
        name=f"{style.title()} Coffee",
        ingredients=ingredients,
        servings=1,
        created_by="system",
        tags=[style],
        base="coffee",
        milk_type=milk_type,
        milk_ml=milk_ml,
        sugar_g=sugar_tsp * TSP_TO_G_SUGAR,
        volume_ml=milk_ml + FILTER_COFFEE_BASE_ML,
    )


def build_lassi(
    type: Literal["sweet", "salty", "mango"],
    yogurt_ml: float,
    sugar_g: float,
    fruit_g: float = 0,
) -> Beverage:
    ingredients = [RecipeIngredient(ingredient_id="USDA007", qty=yogurt_ml, unit="g")]
    if sugar_g > 0:
        ingredients.append(RecipeIngredient(ingredient_id="USDA009", qty=sugar_g, unit="g"))
    if type == "mango" and fruit_g > 0:
        ingredients.append(RecipeIngredient(ingredient_id="E037", qty=fruit_g, unit="g"))

    return Beverage(
        recipe_id=_new_id("lassi"),
        name=f"{type.title()} Lassi",
        ingredients=ingredients,
        servings=1,
        created_by="system",
        additives=["roasted cumin", "salt"] if type == "salty" else [],
        base="yogurt",
        sugar_g=sugar_g,
        volume_ml=yogurt_ml + LASSI_DILUTION_ML,
    )


def build_buttermilk(volume_ml: float, salted: bool = True, spiced: bool = True) -> Beverage:
    curd_g = volume_ml * BUTTERMILK_CURD_FRACTION
    additives = []
    if salted:
        additives.append("salt")
    if spiced:
        additives.extend(["cumin", "curry leaves", "asafoetida"])

    return Beverage(
        recipe_id=_new_id("buttermilk"),
        name="Buttermilk",
        aliases=["chaas", "chhaachh"],
        ingredients=[RecipeIngredient(ingredient_id="USDA007", qty=curd_g, unit="g")],
        servings=1,
        created_by="system",
        additives=additives,
        base="yogurt",
        volume_ml=volume_ml,
    )


def build_nimbu_paani(volume_ml: float, sugar_g: float, salt: bool = True) -> Beverage:
    lemon_juice_g = volume_ml * NIMBU_PAANI_LEMON_FRACTION
    ingredients = [RecipeIngredient(ingredient_id="E033", qty=lemon_juice_g, unit="g")]
    if sugar_g > 0:
        ingredients.append(RecipeIngredient(ingredient_id="USDA009", qty=sugar_g, unit="g"))

    return Beverage(
        recipe_id=_new_id("nimbu_paani"),
        name="Nimbu Paani",
        aliases=["shikanji", "lemonade"],
        ingredients=ingredients,
        servings=1,
        created_by="system",
        additives=["salt"] if salt else [],
        base="water",
        sugar_g=sugar_g,
        volume_ml=volume_ml,
    )


def build_juice(
    fruit: str,
    volume_ml: float,
    added_sugar_g: float = 0,
    ingredients: Optional[dict[str, Ingredient]] = None,
) -> Beverage:
    if ingredients is None:
        ingredients = load_ingredients()

    fruit_ingredient = find_ingredient(ingredients, fruit)
    if fruit_ingredient is None:
        raise ValueError(f"build_juice: unknown fruit {fruit!r} (not in ingredient DB)")

    recipe_ingredients = [
        RecipeIngredient(ingredient_id=fruit_ingredient.ingredient_id, qty=volume_ml, unit="g")
    ]
    if added_sugar_g > 0:
        recipe_ingredients.append(
            RecipeIngredient(ingredient_id="USDA009", qty=added_sugar_g, unit="g")
        )

    return Beverage(
        recipe_id=_new_id("juice"),
        name=f"{fruit_ingredient.name} Juice",
        ingredients=recipe_ingredients,
        servings=1,
        created_by="system",
        sugar_g=added_sugar_g,
        base="juice",
        volume_ml=volume_ml,
    )


def build_alcohol(type: ALCOHOL_TYPE, volume_ml: float, abv_pct: float) -> Beverage:
    alcohol_g = volume_ml * (abv_pct / 100) * ETHANOL_DENSITY_G_PER_ML
    residual_carbs_g = volume_ml * RESIDUAL_CARBS_G_PER_100ML[type] / 100

    return Beverage(
        recipe_id=_new_id("alcohol"),
        name=type.title(),
        ingredients=[
            RecipeIngredient(ingredient_id="MANUAL004", qty=alcohol_g, unit="g"),
            RecipeIngredient(ingredient_id="USDA009", qty=residual_carbs_g, unit="g"),
        ],
        servings=1,
        created_by="system",
        tags=[type],
        base="alcohol",
        alcohol_pct=abv_pct,
        volume_ml=volume_ml,
    )


def build_protein_shake(
    protein_g: float,
    milk_ml: float,
    milk_type: MilkTypeArg,
    banana_g: float = 0,
    peanut_butter_g: float = 0,
    protein_source: Literal["whey_isolate", "whey_concentrate", "casein"] = "whey_isolate",
    plant_milk_kind: PlantMilkKind = "soy",
    ingredients: Optional[dict[str, Ingredient]] = None,
) -> Beverage:
    if ingredients is None:
        ingredients = load_ingredients()

    source_id = PROTEIN_SOURCE_INGREDIENT[protein_source]
    source_ingredient = ingredients[source_id]
    powder_g = protein_g / (source_ingredient.protein_g_per_100g / 100)

    recipe_ingredients = [RecipeIngredient(ingredient_id=source_id, qty=powder_g, unit="g")]
    milk_id = _milk_ingredient_id(milk_type, plant_milk_kind)
    if milk_id and milk_ml > 0:
        recipe_ingredients.append(RecipeIngredient(ingredient_id=milk_id, qty=milk_ml, unit="g"))
    if banana_g > 0:
        recipe_ingredients.append(RecipeIngredient(ingredient_id="E009", qty=banana_g, unit="g"))
    if peanut_butter_g > 0:
        recipe_ingredients.append(
            RecipeIngredient(ingredient_id="USDA010", qty=peanut_butter_g, unit="g")
        )

    return Beverage(
        recipe_id=_new_id("protein_shake"),
        name="Protein Shake",
        ingredients=recipe_ingredients,
        servings=1,
        created_by="system",
        tags=["high_protein"],
        base="protein_supplement",
        milk_type=milk_type,
        milk_ml=milk_ml,
        volume_ml=milk_ml if milk_ml > 0 else DEFAULT_SHAKE_VOLUME_ML,
    )
