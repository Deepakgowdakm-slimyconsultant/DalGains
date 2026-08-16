"""Insight generation: recommendations, warnings, celebrations, nudges.

generate_insights(user_id, as_of_date) is the single entry point; every
rule below is also a standalone function taking plain data (no hidden
global state, no calls back into logging/planning of its own) so each is
independently testable with a synthetic history -- see the Phase 3
brief's "each as a separately testable function".
"""
from datetime import date as date_cls
from datetime import datetime, timedelta
from typing import Optional

from src.core.ingredients import load_ingredients
from src.core.planning import EatingWindow, compute_eating_window, generate_plan
from src.core.profiles import load_profile
from src.core.schemas import Ingredient, LogEntry, MealLog, NutritionTotals
from src.core.tdee import calculate_bmr
from src.core.units import resolve_to_grams
from src.insights.models import Insight
from src.insights.swaps import suggest_protein_swaps
from src.logging import engine as log_engine
from src.logging.aggregation import streak, weekly_totals
from src.recipes.builder import compute_nutrition, load_recipe

_ZERO_TOTALS = NutritionTotals(energy_kcal=0, protein_g=0, fat_g=0, carbs_g=0, fiber_g=0)

FESTIVAL_TAGS = {
    "diwali", "onam", "eid", "sankranti", "holi", "pongal", "festival",
    "navratri", "christmas", "gudi_padwa", "baisakhi",
}
STREAK_MILESTONES = {7, 30, 100}
BEVERAGE_KCAL_SHARE_THRESHOLD = 0.25
HYDRATION_GAP_HOURS = 6.0
LOOKBACK_DAYS = 10


def _last_n_dates(as_of_date: str, n: int) -> list[str]:
    end = date_cls.fromisoformat(as_of_date)
    return [(end - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]


def _hour_of_day(timestamp: datetime) -> float:
    return timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600


def _is_hour_within_window(hour: float, window: EatingWindow) -> bool:
    if window.start_hour <= window.end_hour:
        return window.start_hour <= hour < window.end_hour
    return hour >= window.start_hour or hour < window.end_hour


def _entry_totals(
    entry: LogEntry, ingredients: dict[str, Ingredient], user_id: str
) -> NutritionTotals:
    if entry.recipe_id:
        recipe = load_recipe(entry.recipe_id)
        return compute_nutrition(recipe, servings=entry.qty, ingredients=ingredients, user_id=user_id)
    ingredient = ingredients[entry.ingredient_id]
    qty_g = resolve_to_grams(ingredient, entry.qty, entry.unit, user_id=user_id)
    scale = qty_g / 100
    return NutritionTotals(
        energy_kcal=ingredient.energy_kcal_per_100g * scale,
        protein_g=ingredient.protein_g_per_100g * scale,
        fat_g=ingredient.fat_g_per_100g * scale,
        carbs_g=ingredient.carbs_g_per_100g * scale,
        fiber_g=ingredient.fiber_g_per_100g * scale,
    )


def _is_beverage_entry(entry: LogEntry, ingredients: dict[str, Ingredient]) -> bool:
    if entry.recipe_id:
        try:
            recipe = load_recipe(entry.recipe_id)
        except FileNotFoundError:
            return False
        return recipe.meal_type == "beverage"
    ingredient = ingredients.get(entry.ingredient_id)
    return ingredient is not None and ingredient.category == "beverage_base"


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------


def check_protein_deficit_3day(
    day_totals: list[NutritionTotals], target_protein_g: float, user_id: str, as_of_date: str
) -> Optional[Insight]:
    """day_totals: exactly the 3 most recent days (any order)."""
    if len(day_totals) < 3 or target_protein_g <= 0:
        return None
    if not all(t.protein_g < target_protein_g * 0.8 for t in day_totals):
        return None

    return Insight(
        insight_id="protein_deficit_3day",
        kind="swap",
        severity="suggest",
        title="Protein has been low for 3 days",
        body_en=(
            f"Your protein has been under 80% of your {target_protein_g:.0f}g "
            "target for 3 days running."
        ),
        body_hi=(
            f"आपका प्रोटीन सेवन पिछले 3 दिनों से {target_protein_g:.0f}g लक्ष्य "
            "के 80% से कम रहा है।"
        ),
        body_kn=(
            f"ನಿಮ್ಮ ಪ್ರೋಟೀನ್ ಸೇವನೆ ಕಳೆದ 3 ದಿನಗಳಿಂದ {target_protein_g:.0f}g ಗುರಿಯ "
            "80% ಕ್ಕಿಂತ ಕಡಿಮೆ ಇದೆ."
        ),
        evidence={
            "day_protein_g": [round(t.protein_g, 1) for t in day_totals],
            "target_protein_g": target_protein_g,
        },
        suggested_actions=suggest_protein_swaps(user_id, as_of_date),
    )


def check_calorie_surplus_streak(
    day_totals: list[NutritionTotals], target_kcal: float, eating_phase: str
) -> Optional[Insight]:
    """day_totals: recent days oldest-first; checks the trailing streak."""
    if eating_phase not in ("cutting", "recomp") or target_kcal <= 0:
        return None

    streak_len = 0
    for totals in reversed(day_totals):
        if totals.energy_kcal > target_kcal * 1.15:
            streak_len += 1
        else:
            break
    if streak_len < 5:
        return None

    phase_label = eating_phase.replace("_", " ")
    return Insight(
        insight_id="calorie_surplus_streak",
        kind="warning",
        severity="warn",
        title=f"{streak_len} days over target in a row",
        body_en=(
            f"You've been over 115% of your {target_kcal:.0f} kcal target for "
            f"{streak_len} days straight while on a {phase_label}."
        ),
        body_hi=(
            f"{phase_label} पर होते हुए आप {streak_len} दिनों से लगातार अपने "
            f"{target_kcal:.0f} kcal लक्ष्य के 115% से ऊपर रहे हैं।"
        ),
        body_kn=(
            f"{phase_label} ಹಂತದಲ್ಲಿದ್ದು ನೀವು {streak_len} ದಿನಗಳಿಂದ ನಿರಂತರವಾಗಿ "
            f"{target_kcal:.0f} kcal ಗುರಿಯ 115% ಕ್ಕಿಂತ ಹೆಚ್ಚಿದ್ದೀರಿ."
        ),
        evidence={"streak_days": streak_len, "target_kcal": target_kcal},
        suggested_actions=[
            "Double-check portion sizes for a couple of days -- it's easy for "
            "a deficit to quietly become a surplus.",
        ],
    )


def check_undereating_warning(
    dated_totals: list[tuple[str, NutritionTotals]], bmr: float
) -> Optional[Insight]:
    """dated_totals: recent (date, totals) pairs, oldest first."""
    if bmr <= 0 or not dated_totals:
        return None

    threshold = bmr * 0.8
    under_dates = [d for d, t in dated_totals if 0 < t.energy_kcal < threshold]
    if not under_dates:
        return None

    trailing = dated_totals[-3:]
    persisted = len(trailing) == 3 and all(0 < t.energy_kcal < threshold for _, t in trailing)

    actions = ["This is well below your estimated BMR -- consider eating more, not less."]
    if persisted:
        actions.append(
            "This has happened 3+ days running -- worth talking to a doctor "
            "or dietitian if it continues."
        )

    return Insight(
        insight_id="undereating_warning",
        kind="warning",
        severity="urgent" if persisted else "warn",
        title="Intake has dropped below BMR",
        body_en=(
            f"At least one recent day was under {threshold:.0f} kcal (80% of "
            f"your ~{bmr:.0f} kcal BMR)."
        ),
        body_hi=(
            f"हाल के दिनों में कम से कम एक दिन {threshold:.0f} kcal (आपके "
            f"~{bmr:.0f} kcal BMR के 80%) से कम रहा।"
        ),
        body_kn=(
            f"ಇತ್ತೀಚಿನ ದಿನಗಳಲ್ಲಿ ಕನಿಷ್ಠ ಒಂದು ದಿನ {threshold:.0f} kcal ಗಿಂತ "
            f"(ನಿಮ್ಮ ~{bmr:.0f} kcal BMR ನ 80%) ಕಡಿಮೆ ಇತ್ತು."
        ),
        evidence={"under_threshold_dates": under_dates, "bmr": bmr, "threshold_kcal": threshold},
        suggested_actions=actions,
    )


def check_fiber_low_week(weekly_avg_fiber_g: float) -> Optional[Insight]:
    if weekly_avg_fiber_g >= 25:
        return None
    return Insight(
        insight_id="fiber_low_week",
        kind="swap",
        severity="suggest",
        title="Fiber has been low this week",
        body_en=f"Your weekly average fiber is {weekly_avg_fiber_g:.0f}g, under the 25g guideline.",
        body_hi=f"आपका साप्ताहिक औसत फाइबर {weekly_avg_fiber_g:.0f}g है, जो 25g दिशानिर्देश से कम है।",
        body_kn=f"ನಿಮ್ಮ ವಾರದ ಸರಾಸರಿ ಫೈಬರ್ {weekly_avg_fiber_g:.0f}g, 25g ಮಾರ್ಗಸೂಚಿಗಿಂತ ಕಡಿಮೆ.",
        evidence={"weekly_avg_fiber_g": weekly_avg_fiber_g},
        suggested_actions=[
            "Swap in a bajra or jowar roti instead of one wheat roti a couple of times this week.",
            "Add a methi (fenugreek) sabzi -- high fiber, cooks fast.",
            "A spoon of sattu mixed into water or the roti dough is an easy fiber+protein bump.",
        ],
    )


def check_hydration_reminder(
    today_entries: list[LogEntry],
    as_of_timestamp: datetime,
    window: EatingWindow,
    ingredients: dict[str, Ingredient],
) -> Optional[Insight]:
    if not _is_hour_within_window(_hour_of_day(as_of_timestamp), window):
        return None

    beverage_times = [
        e.timestamp for e in today_entries if e.timestamp and _is_beverage_entry(e, ingredients)
    ]
    if not beverage_times:
        gap_hours = HYDRATION_GAP_HOURS + 1  # no beverage logged at all today
    else:
        gap_hours = (as_of_timestamp - max(beverage_times)).total_seconds() / 3600

    if gap_hours < HYDRATION_GAP_HOURS:
        return None

    return Insight(
        insight_id="hydration_reminder",
        kind="hydration",
        severity="info",
        title="No water or beverage logged in a while",
        body_en=f"It's been about {gap_hours:.0f} hours since your last logged drink.",
        body_hi=f"आपके आखिरी दर्ज पेय को लगभग {gap_hours:.0f} घंटे हो गए हैं।",
        body_kn=f"ನಿಮ್ಮ ಕೊನೆಯ ದಾಖಲಿಸಿದ ಪಾನೀಯದಿಂದ ಸುಮಾರು {gap_hours:.0f} ಗಂಟೆಗಳಾಗಿವೆ.",
        evidence={"hours_since_last_beverage": round(gap_hours, 1)},
        suggested_actions=["A glass of water or buttermilk works fine -- just log it."],
    )


def check_festival_flex(today_tags: list[str]) -> Optional[Insight]:
    matched = [t for t in today_tags if t.lower() in FESTIVAL_TAGS]
    if not matched:
        return None
    return Insight(
        insight_id="festival_flex",
        kind="festival_flex",
        severity="info",
        title="Enjoy the day!",
        body_en="Today's tagged as a festival day -- no calorie warnings today. Enjoy it.",
        body_hi="आज को त्योहार का दिन टैग किया गया है -- आज कोई कैलोरी चेतावनी नहीं। आनंद लें।",
        body_kn="ಇಂದನ್ನು ಹಬ್ಬದ ದಿನ ಎಂದು ಟ್ಯಾಗ್ ಮಾಡಲಾಗಿದೆ -- ಇಂದು ಯಾವುದೇ ಕ್ಯಾಲೋರಿ ಎಚ್ಚರಿಕೆಗಳಿಲ್ಲ. ಆನಂದಿಸಿ.",
        evidence={"matched_tags": matched},
        suggested_actions=[],
    )


def check_streak_celebration(streak_days: int) -> Optional[Insight]:
    if streak_days not in STREAK_MILESTONES:
        return None
    return Insight(
        insight_id="streak_celebration",
        kind="celebration",
        severity="info",
        title=f"{streak_days}-day logging streak!",
        body_en=(
            f"You've logged something every day for {streak_days} days straight. "
            "That consistency is what actually moves the needle."
        ),
        body_hi=(
            f"आपने लगातार {streak_days} दिनों से हर दिन कुछ न कुछ दर्ज किया है। "
            "यही निरंतरता असल में फर्क डालती है।"
        ),
        body_kn=(
            f"ನೀವು ಸತತ {streak_days} ದಿನಗಳಿಂದ ಪ್ರತಿದಿನ ಏನಾದರೂ ದಾಖಲಿಸಿದ್ದೀರಿ. "
            "ಈ ಸ್ಥಿರತೆಯೇ ನಿಜವಾಗಿ ಪರಿಣಾಮ ಬೀರುತ್ತದೆ."
        ),
        evidence={"streak_days": streak_days},
        suggested_actions=[],
    )


def check_beverage_calorie_surprise(
    today_log: MealLog, ingredients: dict[str, Ingredient], user_id: str
) -> Optional[Insight]:
    if today_log.computed_totals.energy_kcal <= 0:
        return None

    beverage_kcal = sum(
        _entry_totals(entry, ingredients, user_id).energy_kcal
        for entry in today_log.entries
        if _is_beverage_entry(entry, ingredients)
    )
    share = beverage_kcal / today_log.computed_totals.energy_kcal
    if share <= BEVERAGE_KCAL_SHARE_THRESHOLD:
        return None

    return Insight(
        insight_id="beverage_calorie_surprise",
        kind="swap",
        severity="suggest",
        title="Beverages are a big chunk of today's calories",
        body_en=f"Beverages make up {share * 100:.0f}% of today's calories so far.",
        body_hi=f"पेय पदार्थ आज की अब तक की कैलोरी का {share * 100:.0f}% हिस्सा हैं।",
        body_kn=f"ಪಾನೀಯಗಳು ಇಂದಿನ ಇಲ್ಲಿಯವರೆಗಿನ ಕ್ಯಾಲೊರಿಗಳಲ್ಲಿ {share * 100:.0f}% ಪಾಲು ಹೊಂದಿವೆ.",
        evidence={"beverage_kcal": round(beverage_kcal, 1), "share_pct": round(share * 100, 1)},
        suggested_actions=[
            "Masala chai without sugar still tastes like chai.",
            "Buttermilk (chaas) instead of a sweet lassi cuts a lot of calories for the same glass.",
        ],
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate_insights(user_id: str, as_of_date: str) -> list[Insight]:
    """All insights for `user_id` as of `as_of_date` ("YYYY-MM-DD")."""
    ingredients = load_ingredients()
    profile = load_profile(user_id)

    lookback_dates = _last_n_dates(as_of_date, LOOKBACK_DAYS)
    logs_by_date: dict[str, MealLog] = {}
    for d in lookback_dates:
        log = log_engine.get_day(user_id, d)
        if isinstance(log, MealLog):
            logs_by_date[d] = log

    def totals_for(dates: list[str]) -> list[NutritionTotals]:
        return [logs_by_date[d].computed_totals if d in logs_by_date else _ZERO_TOTALS for d in dates]

    insights: list[Insight] = []

    if profile is not None:
        plan = generate_plan(profile)
        bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)

        result = check_protein_deficit_3day(
            totals_for(lookback_dates[-3:]), plan.protein_g, user_id, as_of_date
        )
        if result:
            insights.append(result)

        result = check_calorie_surplus_streak(
            totals_for(lookback_dates), plan.daily_kcal, profile.eating_phase
        )
        if result:
            insights.append(result)

        last_7 = lookback_dates[-7:]
        result = check_undereating_warning(list(zip(last_7, totals_for(last_7))), bmr)
        if result:
            insights.append(result)

        week = weekly_totals(user_id, as_of_date)
        result = check_fiber_low_week(week.averages.fiber_g)
        if result:
            insights.append(result)

    today_log = logs_by_date.get(as_of_date)

    if today_log is not None:
        if profile is not None:
            window = compute_eating_window(profile)
            entry_timestamps = [e.timestamp for e in today_log.entries if e.timestamp]
            if entry_timestamps:
                result = check_hydration_reminder(
                    today_log.entries, max(entry_timestamps), window, ingredients
                )
                if result:
                    insights.append(result)

        result = check_beverage_calorie_surprise(today_log, ingredients, user_id)
        if result:
            insights.append(result)

    festival = check_festival_flex(today_log.tags if today_log else [])

    celebration = check_streak_celebration(streak(user_id))
    if celebration:
        insights.append(celebration)

    if festival is not None:
        # "no one wants their tracker scolding them on Diwali" -- suppress
        # calorie-kind warnings for the day, keep the celebration instead.
        insights = [i for i in insights if not i.insight_id.startswith("calorie_")]
        insights.append(festival)

    return insights
