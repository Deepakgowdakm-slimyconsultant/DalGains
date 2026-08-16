"""Body-type / eating-phase / fasting-protocol planning.

IMPORTANT: body_type is informational only. It drives guidance_notes text
below and MUST NEVER be wired into calorie/macro math -- BMR and TDEE come
from src.core.tdee's Mifflin-St Jeor implementation, which takes no
body_type input. If you're adding a numeric adjustment, it belongs on
eating_phase (see EATING_PHASE_* below), not body_type.

eating_phase (schemas.EatingPhase) is the field that actually adjusts the
calorie target. Section E of the Phase 2 brief wrote one of its six phases
as "lean_bulk" in prose, but schemas.UserProfile.eating_phase's enum only
defines "bulking" -- that's a naming slip in the brief, not a second
phase; "bulking" is what's implemented and what gets the +10% adjustment
described under "lean_bulk". UserProfile.goal (cut/maintain/lean_bulk/
recomp, reused from Phase 1's tdee.GOAL_PRESETS) still exists on the
profile for backward compatibility with tdee.calculate_targets(), but
generate_plan() below is driven entirely by eating_phase, which is more
granular (adds reverse_diet/refeed).
"""
from typing import Optional

from pydantic import BaseModel, Field

from src.core.schemas import EatingPhase, FastingProtocol, UserProfile
from src.core.tdee import calculate_bmr, calculate_tdee

FAT_PCT_OF_CALORIES = 0.25
FIBER_G_PER_1000_KCAL = 14.0  # IOM general guideline
WATER_ML_PER_KG = 35.0

EATING_PHASE_PROTEIN_PER_KG = {
    "maintenance": 1.6,
    "cutting": 2.2,
    "bulking": 1.8,
    "recomp": 2.0,  # explicitly bumped per the Phase 2 brief
    "reverse_diet": 1.8,
    "refeed": 1.8,
}

# Fixed daily eating window, in hours, for protocols that are naturally
# hour-based. Protocols that restrict by day rather than by hour (5_2,
# alternate_day, ekadashi, navratri) aren't here -- compute_eating_window
# returns the unrestricted 0-24 window with an explanatory note for those.
# ramadan's window wraps past midnight (end_hour < start_hour) and is a
# rough sunset-to-dawn approximation, not a real per-location calculation.
FASTING_PROTOCOL_WINDOWS: dict[str, tuple[float, float]] = {
    "none": (0.0, 24.0),
    "16_8": (12.0, 20.0),
    "18_6": (13.0, 19.0),
    "20_4": (14.0, 18.0),
    "omad": (18.0, 19.0),
    "ramadan": (18.0, 5.0),
}

BODY_TYPE_GUIDANCE = {
    "ectomorph": (
        "As an ectomorph, you likely tolerate carbs well -- lean on rice, roti, "
        "and fruit to hit your calorie target without feeling overly full."
    ),
    "endomorph": (
        "As an endomorph, favor protein and fat over carb-heavy portions -- dal, "
        "paneer, curd, and nuts go further than extra rice or roti."
    ),
    "mesomorph": (
        "As a mesomorph, a balanced plate (grain + dal/protein + vegetable + a "
        "little fat) should get you to target without much fuss."
    ),
    "mixed": (
        "Your body type is mixed, so treat these targets as a starting point and "
        "adjust the protein/carb balance based on how you actually feel over a "
        "couple of weeks."
    ),
}

DIETARY_GUIDANCE = {
    "vegetarian": (
        "As a vegetarian, prioritize dal, curd, paneer, and nuts/seeds to hit "
        "your protein target without over-relying on carbs."
    ),
    "vegan": (
        "As a vegan, combine dal/legumes with rice or roti (they complement each "
        "other's amino acids), and consider a fortified plant milk or protein "
        "powder to close any protein gap."
    ),
    "eggetarian": (
        "As an eggetarian, eggs are your easiest lever for extra protein without "
        "extra cooking complexity -- dal and paneer still do most of the work."
    ),
    "non_vegetarian": (
        "Fish, chicken, and eggs make it straightforward to hit your protein "
        "target; keep dal and vegetables in the mix for fiber and micronutrients."
    ),
    "jain": (
        "As Jain, root vegetables (onion, garlic, potato) are off the table -- "
        "lean on dal, paneer, curd, and nuts for protein, and use ginger/"
        "asafoetida for flavor instead of onion-garlic."
    ),
    "satvik": (
        "A satvik diet excludes onion, garlic, and excess spice -- dal, curd, "
        "paneer, fruit, and mild vegetable preparations should carry most of "
        "your plate."
    ),
    "custom": (
        "Your dietary pattern is custom -- treat these macro targets as the goal "
        "and fit your usual foods to them."
    ),
}

PHASE_GUIDANCE = {
    "maintenance": (
        "You're eating at maintenance -- aim to hit these numbers consistently "
        "rather than exactly every single day."
    ),
    "cutting": (
        "You're in a cut -- prioritize protein at every meal so you hold onto "
        "muscle while in a deficit; hunger will be real, plan for it."
    ),
    "bulking": (
        "You're in a lean bulk -- the surplus is intentionally modest, so expect "
        "slow, steady weight gain, not a rapid jump on the scale."
    ),
    "recomp": (
        "You're recomping at maintenance calories with protein bumped to "
        "2.0g/kg -- this trades speed for keeping fat gain near zero while you "
        "build muscle."
    ),
    "reverse_diet": (
        "You're reverse dieting -- increase calories gradually (~2% per week) "
        "rather than jumping straight to a higher number, and watch the scale "
        "trend over weeks, not days."
    ),
    "refeed": (
        "This is a short refeed (1-2 days only) -- the extra calories are carbs "
        "on purpose, meant to refill glycogen and ease diet fatigue, not to "
        "become the new normal."
    ),
}


class EatingWindow(BaseModel):
    start_hour: float = Field(ge=0, lt=24)
    end_hour: float = Field(ge=0, le=24)
    note: Optional[str] = None


class PlanWarning(BaseModel):
    code: str
    message: str


class PlanRecommendation(BaseModel):
    daily_kcal: float = Field(gt=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fiber_g_min: float = Field(ge=0)
    water_ml_min: float = Field(ge=0)
    eating_window: EatingWindow
    warnings: list[PlanWarning] = Field(default_factory=list)
    guidance_notes: list[str] = Field(default_factory=list)


def compute_calorie_target(profile: UserProfile) -> tuple[float, float, float]:
    """Returns (target_kcal, bmr, tdee) for profile.eating_phase."""
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    tdee = calculate_tdee(bmr, profile.activity_level)
    phase: EatingPhase = profile.eating_phase

    if phase == "maintenance":
        target = tdee
    elif phase == "cutting":
        target = max(tdee * 0.8, bmr + 100)
    elif phase == "bulking":
        target = tdee * 1.10
    elif phase == "recomp":
        target = tdee
    elif phase == "reverse_diet":
        # This call's answer is "this week's" number; see generate_plan's
        # guidance_notes for the +2%/week increment plan. There's no
        # profile field for "current calories," so a first call starts
        # from TDEE.
        target = tdee
    elif phase == "refeed":
        target = tdee * 1.15
    else:  # pragma: no cover -- exhaustive over EatingPhase's Literal values
        raise ValueError(f"Unhandled eating_phase: {phase!r}")

    return target, bmr, tdee


def compute_macros(profile: UserProfile, target_kcal: float) -> tuple[float, float, float]:
    """Returns (protein_g, fat_g, carbs_g) for target_kcal calories."""
    protein_per_kg = EATING_PHASE_PROTEIN_PER_KG[profile.eating_phase]
    protein_g = protein_per_kg * profile.weight_kg
    protein_kcal = protein_g * 4

    if profile.eating_phase == "refeed":
        # The refeed surplus is a carbs-only bump: fat stays at the
        # underlying (pre-refeed) budget's share, not 25% of the inflated
        # refeed total.
        baseline_kcal = target_kcal / 1.15
        fat_kcal = baseline_kcal * FAT_PCT_OF_CALORIES
    else:
        fat_kcal = target_kcal * FAT_PCT_OF_CALORIES
    fat_g = fat_kcal / 9

    carbs_kcal = target_kcal - protein_kcal - fat_kcal
    carbs_g = max(carbs_kcal, 0) / 4

    return protein_g, fat_g, carbs_g


def compute_eating_window(profile: UserProfile) -> EatingWindow:
    protocol: FastingProtocol = profile.fasting_protocol

    if protocol == "custom":
        if profile.fasting_window is None:
            return EatingWindow(
                start_hour=0,
                end_hour=24,
                note="No custom fasting window set; defaulting to unrestricted eating.",
            )
        return EatingWindow(
            start_hour=profile.fasting_window.start_hour,
            end_hour=profile.fasting_window.end_hour,
            note="Custom window as set on the profile.",
        )

    fixed = FASTING_PROTOCOL_WINDOWS.get(protocol)
    if fixed is None:
        return EatingWindow(
            start_hour=0,
            end_hour=24,
            note=(
                f"{protocol} is a day-based fasting pattern, not an hourly eating "
                "window -- no daily time restriction applied here."
            ),
        )
    return EatingWindow(start_hour=fixed[0], end_hour=fixed[1])


def generate_warnings(profile: UserProfile, target_kcal: float, bmr: float) -> list[PlanWarning]:
    """Non-blocking warnings. Never raises, never modifies target_kcal."""
    warnings = []

    if target_kcal < bmr * 0.8:
        warnings.append(
            PlanWarning(
                code="low_calorie_target",
                message=(
                    f"Target of {target_kcal:.0f} kcal/day is below 80% of "
                    f"estimated BMR ({bmr:.0f} kcal). This is an aggressive "
                    "deficit -- consider easing up unless under medical supervision."
                ),
            )
        )

    for flag in profile.medical_flags:
        warnings.append(
            PlanWarning(
                code="medical_flag",
                message=(
                    f"Profile lists '{flag}'. This is not medical advice -- check "
                    "with a doctor before starting a new eating or fasting pattern."
                ),
            )
        )

    if profile.fasting_protocol in ("omad", "20_4") and profile.eating_phase == "cutting":
        warnings.append(
            PlanWarning(
                code="aggressive_combination",
                message=(
                    "Combining a tight eating window with a calorie deficit is a "
                    "common way to under-eat by accident -- track for a week "
                    "before assuming this is sustainable."
                ),
            )
        )

    return warnings


def generate_plan(profile: UserProfile) -> PlanRecommendation:
    target_kcal, bmr, tdee = compute_calorie_target(profile)
    protein_g, fat_g, carbs_g = compute_macros(profile, target_kcal)

    guidance_notes = [
        PHASE_GUIDANCE[profile.eating_phase],
        BODY_TYPE_GUIDANCE[profile.body_type],
        DIETARY_GUIDANCE[profile.dietary_pattern],
    ]
    if profile.eating_phase == "reverse_diet":
        guidance_notes.append(
            f"This week: aim for ~{target_kcal:.0f} kcal. If hunger and energy "
            f"stay stable, increase by ~2% to ~{target_kcal * 1.02:.0f} kcal next "
            "week, and repeat."
        )

    return PlanRecommendation(
        daily_kcal=target_kcal,
        protein_g=protein_g,
        fat_g=fat_g,
        carbs_g=carbs_g,
        fiber_g_min=target_kcal / 1000 * FIBER_G_PER_1000_KCAL,
        water_ml_min=profile.weight_kg * WATER_ML_PER_KG,
        eating_window=compute_eating_window(profile),
        warnings=generate_warnings(profile, target_kcal, bmr),
        guidance_notes=guidance_notes,
    )
