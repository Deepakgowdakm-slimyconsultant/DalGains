import pytest

from src.core.planning import (
    compute_calorie_target,
    compute_eating_window,
    compute_macros,
    generate_plan,
    generate_warnings,
)
from src.core.schemas import FastingWindow, UserProfile
from src.core.tdee import calculate_bmr


def _profile(**overrides):
    kwargs = dict(
        user_id="u1",
        name="Test User",
        age=28,
        sex="male",
        height_cm=175,
        weight_kg=70,
        body_type="mesomorph",
        activity_level="moderate",
        goal="maintain",
        dietary_pattern="vegetarian",
        eating_phase="maintenance",
    )
    kwargs.update(overrides)
    return UserProfile(**kwargs)


# --- compute_calorie_target ----------------------------------------------

def test_cutting_is_less_than_maintenance():
    cutting, _, _ = compute_calorie_target(_profile(eating_phase="cutting"))
    maintenance, _, _ = compute_calorie_target(_profile(eating_phase="maintenance"))
    assert cutting < maintenance


def test_bulking_is_greater_than_maintenance():
    bulking, _, _ = compute_calorie_target(_profile(eating_phase="bulking"))
    maintenance, _, _ = compute_calorie_target(_profile(eating_phase="maintenance"))
    assert bulking > maintenance


def test_cutting_never_drops_below_bmr_plus_100():
    # Even a very low-weight, sedentary profile should be floored.
    profile = _profile(
        weight_kg=40, height_cm=150, activity_level="sedentary", eating_phase="cutting"
    )
    target, bmr, _ = compute_calorie_target(profile)
    assert target >= bmr + 100 - 1e-9


def test_unhandled_eating_phase_raises():
    profile = _profile()
    # Bypass schema validation to exercise compute_calorie_target's own
    # exhaustiveness check (pydantic doesn't validate on plain attribute
    # assignment unless validate_assignment=True is set).
    profile.eating_phase = "not_a_real_phase"
    with pytest.raises(ValueError):
        compute_calorie_target(profile)


# --- compute_macros --------------------------------------------------------

def test_recomp_protein_is_2g_per_kg():
    profile = _profile(eating_phase="recomp", weight_kg=70)
    target, _, _ = compute_calorie_target(profile)
    protein_g, _, _ = compute_macros(profile, target)
    assert protein_g == pytest.approx(140)


def test_refeed_bumps_carbs_relative_to_maintenance():
    maint_profile = _profile(eating_phase="maintenance")
    refeed_profile = _profile(eating_phase="refeed")
    maint_target, _, _ = compute_calorie_target(maint_profile)
    refeed_target, _, _ = compute_calorie_target(refeed_profile)
    _, maint_fat, maint_carbs = compute_macros(maint_profile, maint_target)
    _, refeed_fat, refeed_carbs = compute_macros(refeed_profile, refeed_target)
    assert refeed_carbs > maint_carbs
    # fat should NOT scale with the inflated refeed total.
    assert refeed_fat == pytest.approx(maint_fat, rel=0.05)


def test_macros_never_go_negative_even_at_low_calories():
    profile = _profile(weight_kg=150, eating_phase="cutting")
    target, _, _ = compute_calorie_target(profile)
    protein_g, fat_g, carbs_g = compute_macros(profile, target)
    assert protein_g >= 0
    assert fat_g >= 0
    assert carbs_g >= 0


# --- compute_eating_window -------------------------------------------------

def test_16_8_window():
    window = compute_eating_window(_profile(fasting_protocol="16_8"))
    assert window.end_hour - window.start_hour == 8


def test_none_protocol_is_unrestricted():
    window = compute_eating_window(_profile(fasting_protocol="none"))
    assert window.start_hour == 0
    assert window.end_hour == 24


def test_day_based_protocol_returns_unrestricted_with_note():
    window = compute_eating_window(_profile(fasting_protocol="ekadashi"))
    assert window.start_hour == 0
    assert window.end_hour == 24
    assert window.note is not None


def test_custom_protocol_uses_profile_fasting_window():
    profile = _profile(
        fasting_protocol="custom",
        fasting_window=FastingWindow(start_hour=10, end_hour=18),
    )
    window = compute_eating_window(profile)
    assert window.start_hour == 10
    assert window.end_hour == 18


def test_custom_protocol_without_window_falls_back_to_unrestricted():
    window = compute_eating_window(_profile(fasting_protocol="custom"))
    assert window.start_hour == 0
    assert window.end_hour == 24
    assert window.note is not None


# --- generate_warnings ------------------------------------------------------

def test_low_calorie_target_triggers_warning():
    profile = _profile()
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    warnings = generate_warnings(profile, target_kcal=bmr * 0.5, bmr=bmr)
    assert any(w.code == "low_calorie_target" for w in warnings)


def test_adequate_calorie_target_does_not_trigger_low_calorie_warning():
    profile = _profile()
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    warnings = generate_warnings(profile, target_kcal=bmr * 1.5, bmr=bmr)
    assert not any(w.code == "low_calorie_target" for w in warnings)


def test_medical_flags_produce_warnings():
    profile = _profile(medical_flags=["diabetes_t2", "hypertension"])
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    warnings = generate_warnings(profile, target_kcal=bmr * 1.5, bmr=bmr)
    medical = [w for w in warnings if w.code == "medical_flag"]
    assert len(medical) == 2


def test_aggressive_fasting_cut_combination_warns():
    profile = _profile(fasting_protocol="omad", eating_phase="cutting")
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    warnings = generate_warnings(profile, target_kcal=bmr * 1.5, bmr=bmr)
    assert any(w.code == "aggressive_combination" for w in warnings)


# --- generate_plan (integration) -------------------------------------------

def test_generate_plan_happy_path_returns_positive_kcal():
    plan = generate_plan(_profile())
    assert plan.daily_kcal > 0
    assert plan.protein_g > 0
    assert plan.fiber_g_min > 0
    assert plan.water_ml_min > 0
    assert len(plan.guidance_notes) >= 3


def test_generate_plan_reverse_diet_adds_weekly_increment_note():
    plan = generate_plan(_profile(eating_phase="reverse_diet"))
    assert any("2%" in note for note in plan.guidance_notes)


def test_generate_plan_body_type_does_not_affect_daily_kcal():
    base = _profile(body_type="ectomorph")
    other = _profile(body_type="endomorph")
    plan_a = generate_plan(base)
    plan_b = generate_plan(other)
    assert plan_a.daily_kcal == plan_b.daily_kcal
