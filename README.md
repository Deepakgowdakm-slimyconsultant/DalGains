# DalGains

Ingredient-first calorie and nutrition tracker for Indian households.

## Why

Existing calorie trackers (MyFitnessPal, Cronometer) rely on USDA-only food
databases and don't recognize Indian home-cooked dishes, don't account for
oil/ghee variance between households, and treat units like "1 roti" or
"1 katori" as fixed, meaningless values. DalGains is built for Indian
households from teenagers to grandparents, in plain language, using
household measurement units.

## Core principle: ingredient-first, not dish-lookup-first

Dishes are never hardcoded with fixed calorie values. Every dish is a
recipe made of ingredients:

```
recipe = {
  name, aliases[],
  ingredients: [{ingredient_id, qty, unit}],
  oil_ghee_qty, servings, region_tag
}
```

Calories and macros are always computed by summing ingredient-level
nutrition, scaled by quantity. This lets the app handle any home-cooked
variant without needing every dish pre-catalogued.

See [CLAUDE.md](./CLAUDE.md) for full project rules and conventions.

## Status

Phase 1: ingredient database (IFCT-based) + TDEE calculator.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```
