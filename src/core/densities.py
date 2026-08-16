"""Physical conversion-factor tables for src.core.units.resolve_to_grams.

Two families of lookup, each with the same two-tier pattern (exact
ingredient_id match first, then a coarser category-level default) and the
same caveat: starting points, not exhaustive. Anything not covered by
either tier falls back to a documented default in units.py, with a logged
warning.
"""

# g/ml density, for converting a resolved ml volume into grams.
DENSITY_BY_INGREDIENT_ID = {
    "A015": 0.85,  # Rice, raw, milled (cooked-rice-equivalent approx)
    "B021": 1.0,  # Red gram, dal (toor dal, cooked)
    "T013": 0.91,  # Ghee
    "L002": 1.03,  # Milk, whole, Cow
    "USDA007": 1.03,  # Curd
    "A019": 0.55,  # Wheat flour, atta (dry, loosely packed)
}
DENSITY_BY_CATEGORY = {
    "oil_fat": 0.92,
    "dairy": 1.03,
    "dal": 1.0,
    "grain": 0.85,
}
DEFAULT_DENSITY_G_PER_ML = 1.0

# Grams per "mutthi" (a dry-ingredient handful) -- a mass, not a volume, so
# it doesn't go through the density tables above at all.
MUTTHI_G_BY_INGREDIENT_ID = {
    "A019": 25.0,  # Wheat flour, atta (dry flour, lighter handful)
    "A018": 25.0,  # Wheat flour, refined
}
MUTTHI_G_BY_CATEGORY = {
    "nut_seed": 20.0,
    "grain": 30.0,
    "dal": 30.0,
}
MUTTHI_DEFAULT_G = 30.0
