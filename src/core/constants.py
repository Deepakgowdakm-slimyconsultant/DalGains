"""Cross-module constants shared by src/core/tdee.py and src/core/planning.py."""

# Floors implausible/negative BMR from extreme-but-schema-valid inputs (e.g.
# UserProfile technically allows age=120 + weight_kg=10 together, which
# Mifflin-St Jeor alone drives negative). 600 is chosen with margin: it
# keeps compute_calorie_target's cutting-vs-maintenance ordering strictly
# correct even at the lowest activity multiplier (sedentary, 1.2x). Found
# by tests/test_tdee_hypothesis.py during Phase 2 development.
MIN_SAFE_BMR_KCAL = 600.0
