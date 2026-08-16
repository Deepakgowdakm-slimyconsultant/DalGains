from hypothesis import given
from hypothesis import strategies as st

from src.core.planning import compute_calorie_target, generate_plan, generate_warnings
from src.core.schemas import UserProfile
from src.core.tdee import calculate_bmr

# Bounded to UserProfile's own schema limits.
profile_strategy = st.builds(
    UserProfile,
    user_id=st.just("hyp_user"),
    name=st.just("Hyp User"),
    age=st.integers(min_value=5, max_value=120),
    sex=st.sampled_from(["male", "female"]),
    height_cm=st.floats(min_value=50, max_value=250, allow_nan=False),
    weight_kg=st.floats(min_value=10, max_value=300, allow_nan=False),
    body_type=st.sampled_from(["ectomorph", "mesomorph", "endomorph", "mixed"]),
    activity_level=st.sampled_from(["sedentary", "light", "moderate", "active", "very_active"]),
    goal=st.just("maintain"),
    dietary_pattern=st.sampled_from(
        ["vegetarian", "vegan", "eggetarian", "non_vegetarian", "jain", "satvik", "custom"]
    ),
    eating_phase=st.sampled_from(
        ["maintenance", "cutting", "bulking", "recomp", "reverse_diet", "refeed"]
    ),
)


@given(profile=profile_strategy)
def test_generate_plan_daily_kcal_always_positive(profile):
    plan = generate_plan(profile)
    assert plan.daily_kcal > 0


@given(profile=profile_strategy)
def test_cutting_strictly_less_than_maintenance(profile):
    cutting_target, _, _ = compute_calorie_target(profile.model_copy(update={"eating_phase": "cutting"}))
    maint_target, _, _ = compute_calorie_target(profile.model_copy(update={"eating_phase": "maintenance"}))
    assert cutting_target < maint_target


@given(profile=profile_strategy)
def test_bulking_strictly_greater_than_maintenance(profile):
    bulking_target, _, _ = compute_calorie_target(profile.model_copy(update={"eating_phase": "bulking"}))
    maint_target, _, _ = compute_calorie_target(profile.model_copy(update={"eating_phase": "maintenance"}))
    assert bulking_target > maint_target


@given(profile=profile_strategy, deficit_fraction=st.floats(min_value=0.1, max_value=0.79))
def test_warning_fires_when_target_below_80pct_bmr(profile, deficit_fraction):
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    low_target = bmr * deficit_fraction
    warnings = generate_warnings(profile, target_kcal=low_target, bmr=bmr)
    assert any(w.code == "low_calorie_target" for w in warnings)


@given(profile=profile_strategy, surplus_fraction=st.floats(min_value=0.81, max_value=3.0))
def test_no_low_calorie_warning_when_target_at_or_above_80pct_bmr(profile, surplus_fraction):
    bmr = calculate_bmr(profile.age, profile.sex, profile.height_cm, profile.weight_kg)
    target = bmr * surplus_fraction
    warnings = generate_warnings(profile, target_kcal=target, bmr=bmr)
    assert not any(w.code == "low_calorie_target" for w in warnings)
