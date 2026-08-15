"""TDEE and macro target calculator using the Mifflin-St Jeor equation."""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

# calorie_adjustment: fraction applied to TDEE to get target calories.
# protein_per_kg: grams of protein per kg bodyweight.
# fat_pct_of_calories: share of target calories from fat; remainder is carbs.
GOAL_PRESETS = {
    "cut": {"calorie_adjustment": -0.20, "protein_per_kg": 2.2, "fat_pct_of_calories": 0.25},
    "maintain": {"calorie_adjustment": 0.0, "protein_per_kg": 1.8, "fat_pct_of_calories": 0.28},
    "lean_bulk": {"calorie_adjustment": 0.12, "protein_per_kg": 1.8, "fat_pct_of_calories": 0.25},
    "recomp": {"calorie_adjustment": -0.05, "protein_per_kg": 2.2, "fat_pct_of_calories": 0.25},
}

KCAL_PER_G_PROTEIN = 4
KCAL_PER_G_FAT = 9
KCAL_PER_G_CARBS = 4

# Floors implausible/negative BMR from extreme-but-schema-valid inputs (e.g.
# UserProfile technically allows age=120 + weight_kg=10 together, which
# Mifflin-St Jeor alone drives negative). 600 is chosen with margin: it
# keeps compute_calorie_target's cutting-vs-maintenance ordering strictly
# correct even at the lowest activity multiplier (sedentary, 1.2x) --
# see tests/test_tdee_hypothesis.py.
MIN_BMR_KCAL = 600.0


def calculate_bmr(age: int, sex: str, height_cm: float, weight_kg: float) -> float:
    """Mifflin-St Jeor BMR, floored at MIN_BMR_KCAL. sex is 'male' or 'female'."""
    sex = sex.lower()
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if sex == "male":
        bmr = base + 5
    elif sex == "female":
        bmr = base - 161
    else:
        raise ValueError(f"sex must be 'male' or 'female', got {sex!r}")
    return max(bmr, MIN_BMR_KCAL)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise ValueError(
            f"activity_level must be one of {list(ACTIVITY_MULTIPLIERS)}, got {activity_level!r}"
        )
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def calculate_targets(
    age: int,
    sex: str,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
) -> dict:
    """Return BMR, TDEE, and target calories/protein/fat/carbs for a goal."""
    if goal not in GOAL_PRESETS:
        raise ValueError(f"goal must be one of {list(GOAL_PRESETS)}, got {goal!r}")

    bmr = calculate_bmr(age, sex, height_cm, weight_kg)
    tdee = calculate_tdee(bmr, activity_level)

    preset = GOAL_PRESETS[goal]
    target_calories = tdee * (1 + preset["calorie_adjustment"])

    protein_g = preset["protein_per_kg"] * weight_kg
    protein_kcal = protein_g * KCAL_PER_G_PROTEIN

    fat_kcal = target_calories * preset["fat_pct_of_calories"]
    fat_g = fat_kcal / KCAL_PER_G_FAT

    carbs_kcal = target_calories - protein_kcal - fat_kcal
    carbs_g = carbs_kcal / KCAL_PER_G_CARBS

    return {
        "bmr": round(bmr, 1),
        "tdee": round(tdee, 1),
        "target_calories": round(target_calories, 1),
        "target_protein_g": round(protein_g, 1),
        "target_fat_g": round(fat_g, 1),
        "target_carbs_g": round(carbs_g, 1),
    }
