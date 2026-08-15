"""Ingredients absent from the 542-item IFCT 2017 export.

Per CLAUDE.md's data-source rule, USDA is the fallback for common foods
IFCT doesn't cover (curd/dahi, sago/sabudana, milk sub-types, plant milks);
values below are typical USDA FoodData Central figures for the closest
matching item. Protein-powder entries have no IFCT or USDA equivalent, so
they're marked source="MANUAL" -- values are typical unflavored-product
label figures (protein/fat/carbs), with energy_kcal_per_100g back-derived
from those macros via Atwater factors (4/9/4) so the ingredient is
internally consistent for recipe math. Real products vary by brand; treat
these as reasonable defaults, not measured values.

IDs use a "USDA"/"MANUAL" + number scheme to avoid colliding with IFCT's
single-letter-group codes (e.g. B021).
"""

SUPPLEMENT_INGREDIENTS = [
    # --- USDA fallback: dairy variants and gaps in the 542-item IFCT set ---
    {
        "ingredient_id": "USDA001",
        "name": "Milk, toned",
        "aliases": ["toned milk", "3% fat milk"],
        "energy_kcal_per_100g": 58.0,
        "protein_g_per_100g": 3.1,
        "fat_g_per_100g": 3.0,
        "carbs_g_per_100g": 4.4,
        "fiber_g_per_100g": 0.0,
        "source": "USDA",
        "category": "dairy",
    },
    {
        "ingredient_id": "USDA002",
        "name": "Milk, skimmed",
        "aliases": ["skim milk", "fat-free milk"],
        "energy_kcal_per_100g": 35.0,
        "protein_g_per_100g": 3.4,
        "fat_g_per_100g": 0.2,
        "carbs_g_per_100g": 5.0,
        "fiber_g_per_100g": 0.0,
        "source": "USDA",
        "category": "dairy",
    },
    {
        "ingredient_id": "USDA003",
        "name": "Milk, A2, whole",
        "aliases": ["a2 milk", "a2 gir cow milk"],
        "energy_kcal_per_100g": 61.0,
        "protein_g_per_100g": 3.2,
        "fat_g_per_100g": 3.6,
        "carbs_g_per_100g": 4.7,
        "fiber_g_per_100g": 0.0,
        "source": "USDA",
        "category": "dairy",
    },
    {
        "ingredient_id": "USDA004",
        "name": "Soy milk, unsweetened",
        "aliases": ["soya milk"],
        "energy_kcal_per_100g": 33.0,
        "protein_g_per_100g": 3.3,
        "fat_g_per_100g": 1.8,
        "carbs_g_per_100g": 1.8,
        "fiber_g_per_100g": 0.6,
        "source": "USDA",
        "category": "beverage_base",
    },
    {
        "ingredient_id": "USDA005",
        "name": "Almond milk, unsweetened",
        "aliases": [],
        "energy_kcal_per_100g": 15.0,
        "protein_g_per_100g": 0.6,
        "fat_g_per_100g": 1.2,
        "carbs_g_per_100g": 0.6,
        "fiber_g_per_100g": 0.3,
        "source": "USDA",
        "category": "beverage_base",
    },
    {
        "ingredient_id": "USDA006",
        "name": "Oat milk, unsweetened",
        "aliases": [],
        "energy_kcal_per_100g": 47.0,
        "protein_g_per_100g": 1.0,
        "fat_g_per_100g": 1.5,
        "carbs_g_per_100g": 7.5,
        "fiber_g_per_100g": 0.8,
        "source": "USDA",
        "category": "beverage_base",
    },
    {
        "ingredient_id": "USDA007",
        "name": "Curd, plain, whole milk",
        "aliases": ["dahi", "yogurt", "yoghurt", "curd"],
        "energy_kcal_per_100g": 61.0,
        "protein_g_per_100g": 3.5,
        "fat_g_per_100g": 3.3,
        "carbs_g_per_100g": 4.7,
        "fiber_g_per_100g": 0.0,
        "source": "USDA",
        "category": "dairy",
    },
    {
        "ingredient_id": "USDA008",
        "name": "Sabudana, dry",
        "aliases": ["sago pearls", "tapioca pearls", "sabakki"],
        "energy_kcal_per_100g": 351.0,
        "protein_g_per_100g": 0.2,
        "fat_g_per_100g": 0.1,
        "carbs_g_per_100g": 86.4,
        "fiber_g_per_100g": 0.9,
        "source": "USDA",
        "category": "other",
    },
    # --- MANUAL: protein supplements, typical unflavored-label values ---
    {
        "ingredient_id": "MANUAL001",
        "name": "Whey protein isolate",
        "aliases": ["whey isolate", "wpi"],
        "energy_kcal_per_100g": 377.0,
        "protein_g_per_100g": 90.0,
        "fat_g_per_100g": 1.0,
        "carbs_g_per_100g": 2.0,
        "fiber_g_per_100g": 0.0,
        "source": "MANUAL",
        "category": "other",
    },
    {
        "ingredient_id": "MANUAL002",
        "name": "Whey protein concentrate",
        "aliases": ["whey concentrate", "wpc"],
        "energy_kcal_per_100g": 385.0,
        "protein_g_per_100g": 75.0,
        "fat_g_per_100g": 5.0,
        "carbs_g_per_100g": 10.0,
        "fiber_g_per_100g": 1.0,
        "source": "MANUAL",
        "category": "other",
    },
    {
        "ingredient_id": "MANUAL003",
        "name": "Casein protein, micellar",
        "aliases": ["casein"],
        "energy_kcal_per_100g": 361.5,
        "protein_g_per_100g": 80.0,
        "fat_g_per_100g": 1.5,
        "carbs_g_per_100g": 7.0,
        "fiber_g_per_100g": 0.0,
        "source": "MANUAL",
        "category": "other",
    },
    # --- USDA fallback: needed by src/recipes/beverages.py builders ---
    {
        "ingredient_id": "USDA009",
        "name": "Sugar, white, refined",
        "aliases": ["sugar", "table sugar", "cane sugar", "white sugar"],
        "energy_kcal_per_100g": 387.0,
        "protein_g_per_100g": 0.0,
        "fat_g_per_100g": 0.0,
        "carbs_g_per_100g": 100.0,
        "fiber_g_per_100g": 0.0,
        "source": "USDA",
        "category": "sweetener",
    },
    {
        "ingredient_id": "USDA010",
        "name": "Peanut butter, natural",
        "aliases": [],
        "energy_kcal_per_100g": 588.0,
        "protein_g_per_100g": 25.0,
        "fat_g_per_100g": 50.0,
        "carbs_g_per_100g": 20.0,
        "fiber_g_per_100g": 6.0,
        "source": "USDA",
        "category": "other",
    },
    {
        # Lets build_alcohol reuse compute_nutrition() unmodified: alcohol
        # is represented as an ingredient (700 kcal/100g == the spec's
        # 7 kcal/g) instead of a special-cased nutrition path.
        "ingredient_id": "MANUAL004",
        "name": "Ethanol, pure",
        "aliases": ["alcohol", "ethanol"],
        "energy_kcal_per_100g": 700.0,
        "protein_g_per_100g": 0.0,
        "fat_g_per_100g": 0.0,
        "carbs_g_per_100g": 0.0,
        "fiber_g_per_100g": 0.0,
        "source": "MANUAL",
        "category": "other",
    },
]
