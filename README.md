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

Phase 2: pydantic schema layer, recipe builder, beverages, body-type/
eating-phase/fasting planning, household unit calibration.

## License

DalGains is licensed under **AGPL-3.0** (see [LICENSE](./LICENSE)).

This is deliberate, not a default. DalGains bundles the IFCT 2017 nutrient
dataset via the [nodef/ifct2017](https://github.com/nodef/ifct2017) export,
which is itself AGPL-3.0 (see `data/raw/ifct2017/NOTICE.md`). Combining
that data with this codebase means the combined work carries AGPL-3.0
obligations: anyone who redistributes DalGains, or runs a modified version
as a network service, must also release their source under AGPL-3.0.

The goal is that every improvement to this project — better recipes, more
accurate ingredient data, new household-unit calibrations — stays available
to Indian households, rather than being absorbed into a closed, proprietary
fork.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
```
