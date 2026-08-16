import pytest

from src.core.tdee import GOAL_PRESETS, calculate_bmr, calculate_targets, calculate_tdee


def test_bmr_male_reference_case():
    # 25yo male, 180cm, 80kg: 10*80 + 6.25*180 - 5*25 + 5 = 1805
    bmr = calculate_bmr(age=25, sex="male", height_cm=180, weight_kg=80)
    assert bmr == pytest.approx(1805, abs=0.1)


def test_bmr_female_reference_case():
    # 30yo female, 165cm, 65kg: 10*65 + 6.25*165 - 5*30 - 161 = 1370.25
    bmr = calculate_bmr(age=30, sex="female", height_cm=165, weight_kg=65)
    assert bmr == pytest.approx(1370.25, abs=0.1)


def test_bmr_second_male_reference_case():
    # 40yo male, 175cm, 90kg: 10*90 + 6.25*175 - 5*40 + 5 = 1798.75
    bmr = calculate_bmr(age=40, sex="male", height_cm=175, weight_kg=90)
    assert bmr == pytest.approx(1798.75, abs=0.1)


def test_bmr_rejects_unknown_sex():
    with pytest.raises(ValueError):
        calculate_bmr(age=30, sex="other", height_cm=170, weight_kg=70)


def test_tdee_applies_activity_multiplier():
    assert calculate_tdee(1805, "sedentary") == pytest.approx(1805 * 1.2)
    assert calculate_tdee(1805, "very_active") == pytest.approx(1805 * 1.9)


def test_tdee_rejects_unknown_activity_level():
    with pytest.raises(ValueError):
        calculate_tdee(1800, "hyperactive")


@pytest.mark.parametrize("goal", list(GOAL_PRESETS))
def test_calculate_targets_returns_sane_macros(goal):
    result = calculate_targets(
        age=28,
        sex="female",
        height_cm=160,
        weight_kg=60,
        activity_level="moderate",
        goal=goal,
    )
    assert result["bmr"] > 0
    assert result["tdee"] > result["bmr"]
    assert result["target_calories"] > 0
    assert result["target_protein_g"] > 0
    assert result["target_fat_g"] > 0
    assert result["target_carbs_g"] > 0

    macro_kcal = (
        result["target_protein_g"] * 4
        + result["target_fat_g"] * 9
        + result["target_carbs_g"] * 4
    )
    assert macro_kcal == pytest.approx(result["target_calories"], abs=2)


def test_cut_has_lower_calories_than_maintain_and_lean_bulk():
    common = dict(age=28, sex="male", height_cm=175, weight_kg=75, activity_level="active")
    cut = calculate_targets(**common, goal="cut")
    maintain = calculate_targets(**common, goal="maintain")
    lean_bulk = calculate_targets(**common, goal="lean_bulk")
    assert cut["target_calories"] < maintain["target_calories"] < lean_bulk["target_calories"]


def test_calculate_targets_rejects_unknown_goal():
    with pytest.raises(ValueError):
        calculate_targets(
            age=30,
            sex="male",
            height_cm=175,
            weight_kg=75,
            activity_level="active",
            goal="shred",
        )
