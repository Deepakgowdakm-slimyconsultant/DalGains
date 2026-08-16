"""Daily/weekly nutrition aggregation over a user's logged meals."""
from datetime import date as date_cls
from datetime import timedelta
from typing import Optional

from src.core.ingredients import load_ingredients
from src.core.planning import generate_plan
from src.core.profiles import load_profile
from src.core.schemas import (
    DailyBreakdown,
    Ingredient,
    MealLog,
    NutritionTotals,
    WeeklySummary,
)
from src.core.units import resolve_to_grams
from src.logging import store
from src.recipes.builder import compute_nutrition, load_recipe

# A day counts as "on target" if it's within this fraction of the target.
ADHERENCE_TOLERANCE_PCT = 0.10

_ZERO_TOTALS = NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0)


def daily_totals(
    meal_log: MealLog, ingredients: Optional[dict[str, Ingredient]] = None
) -> NutritionTotals:
    """Sums nutrition across every entry in meal_log.

    Recipe/beverage entries (recipe_id set) go through
    src.recipes.builder.compute_nutrition with servings=entry.qty.
    Ingredient entries (ingredient_id set) resolve qty+unit to grams via
    src.core.units.resolve_to_grams, same as a RecipeIngredient.
    """
    if ingredients is None:
        ingredients = load_ingredients()

    kcal = protein = fat = carbs = fiber = 0.0

    for entry in meal_log.entries:
        if entry.recipe_id:
            recipe = load_recipe(entry.recipe_id)
            totals = compute_nutrition(
                recipe, servings=entry.qty, ingredients=ingredients, user_id=meal_log.user_id
            )
        else:
            ingredient = ingredients.get(entry.ingredient_id)
            if ingredient is None:
                raise KeyError(f"Unknown ingredient_id {entry.ingredient_id!r} in log entry")
            qty_g = resolve_to_grams(ingredient, entry.qty, entry.unit, user_id=meal_log.user_id)
            scale = qty_g / 100
            totals = NutritionTotals(
                energy_kcal=ingredient.energy_kcal_per_100g * scale,
                protein_g=ingredient.protein_g_per_100g * scale,
                fat_g=ingredient.fat_g_per_100g * scale,
                carbs_g=ingredient.carbs_g_per_100g * scale,
                fiber_g=ingredient.fiber_g_per_100g * scale,
            )

        kcal += totals.energy_kcal
        protein += totals.protein_g
        fat += totals.fat_g
        carbs += totals.carbs_g
        fiber += totals.fiber_g

    return NutritionTotals(
        energy_kcal=kcal, protein_g=protein, fat_g=fat, carbs_g=carbs, fiber_g=fiber
    )


def _target_kcal_for(user_id: str) -> Optional[float]:
    profile = load_profile(user_id)
    if profile is None:
        return None
    return generate_plan(profile).daily_kcal


def streak(user_id: str, metric: str = "logged_any_meal") -> int:
    """Consecutive days (walking back from today) satisfying `metric`."""
    if metric != "logged_any_meal":
        raise ValueError(f"Unsupported streak metric: {metric!r}")

    count = 0
    d = date_cls.today()
    while True:
        log = store.load_day(user_id, d.isoformat())
        if isinstance(log, MealLog) and log.entries:
            count += 1
            d -= timedelta(days=1)
        else:
            break
    return count


def weekly_totals(user_id: str, week_ending: str) -> WeeklySummary:
    """WeeklySummary for the 7 days ending on (and including) week_ending."""
    end = date_cls.fromisoformat(week_ending)
    start = end - timedelta(days=6)
    target_kcal = _target_kcal_for(user_id)

    days: list[DailyBreakdown] = []
    d = start
    while d <= end:
        date_str = d.isoformat()
        log = store.load_day(user_id, date_str)
        if isinstance(log, MealLog):
            totals = log.computed_totals
            entry_count = len(log.entries)
        else:
            # None (no log yet) or QuarantinedLog: a week view shouldn't
            # crash or stall on one bad/missing day -- count it as zero.
            totals = _ZERO_TOTALS
            entry_count = 0

        adherence_pct = None
        if target_kcal:
            adherence_pct = 100 * (1 - abs(totals.energy_kcal - target_kcal) / target_kcal)

        days.append(
            DailyBreakdown(
                date=date_str,
                totals=totals,
                target_kcal=target_kcal,
                adherence_pct=adherence_pct,
                entry_count=entry_count,
            )
        )
        d += timedelta(days=1)

    n = len(days)
    averages = NutritionTotals(
        energy_kcal=sum(day.totals.energy_kcal for day in days) / n,
        protein_g=sum(day.totals.protein_g for day in days) / n,
        fat_g=sum(day.totals.fat_g for day in days) / n,
        carbs_g=sum(day.totals.carbs_g for day in days) / n,
        fiber_g=sum(day.totals.fiber_g for day in days) / n,
    )

    logged_days = [day for day in days if day.entry_count > 0]
    if target_kcal and logged_days:
        within = sum(
            1
            for day in logged_days
            if abs(day.totals.energy_kcal - target_kcal) <= target_kcal * ADHERENCE_TOLERANCE_PCT
        )
        target_adherence_pct = 100 * within / len(logged_days)
    else:
        target_adherence_pct = 0.0

    notable_days = []
    if logged_days:
        highest = max(logged_days, key=lambda day: day.totals.energy_kcal)
        lowest_protein = min(logged_days, key=lambda day: day.totals.protein_g)
        notable_days.append(f"Highest kcal: {highest.date} ({highest.totals.energy_kcal:.0f} kcal)")
        notable_days.append(
            f"Lowest protein: {lowest_protein.date} ({lowest_protein.totals.protein_g:.0f}g)"
        )
        if target_kcal:
            best = max(logged_days, key=lambda day: day.adherence_pct)
            notable_days.append(f"Best adherence: {best.date} ({best.adherence_pct:.0f}% of target)")

    return WeeklySummary(
        user_id=user_id,
        week_start_date=start.isoformat(),
        week_end_date=end.isoformat(),
        days=days,
        averages=averages,
        target_adherence_pct=target_adherence_pct,
        streak_days=streak(user_id),
        notable_days=notable_days,
        warnings=[],
    )


def target_adherence(user_id: str, days: int = 7) -> dict:
    """% of the last `days` days within +/-10% of target, per NutritionTotals field.

    Returns a dict with *_adherence_pct keys and days_evaluated; all
    percentages are None if the user has no profile or hasn't logged
    anything in the window (adherence to an unknown target is undefined).
    """
    profile = load_profile(user_id)
    if profile is None:
        return {
            "calorie_adherence_pct": None,
            "protein_adherence_pct": None,
            "fat_adherence_pct": None,
            "carbs_adherence_pct": None,
            "days_evaluated": 0,
        }

    plan = generate_plan(profile)
    end = date_cls.today()
    start = end - timedelta(days=days - 1)

    logged_totals: list[NutritionTotals] = []
    d = start
    while d <= end:
        log = store.load_day(user_id, d.isoformat())
        if isinstance(log, MealLog) and log.entries:
            logged_totals.append(log.computed_totals)
        d += timedelta(days=1)

    if not logged_totals:
        return {
            "calorie_adherence_pct": None,
            "protein_adherence_pct": None,
            "fat_adherence_pct": None,
            "carbs_adherence_pct": None,
            "days_evaluated": 0,
        }

    def _pct_within(actual_values: list[float], target: float) -> float:
        within = sum(1 for v in actual_values if abs(v - target) <= target * ADHERENCE_TOLERANCE_PCT)
        return 100 * within / len(actual_values)

    return {
        "calorie_adherence_pct": _pct_within([t.energy_kcal for t in logged_totals], plan.daily_kcal),
        "protein_adherence_pct": _pct_within([t.protein_g for t in logged_totals], plan.protein_g),
        "fat_adherence_pct": _pct_within([t.fat_g for t in logged_totals], plan.fat_g),
        "carbs_adherence_pct": _pct_within([t.carbs_g for t in logged_totals], plan.carbs_g),
        "days_evaluated": len(logged_totals),
    }
