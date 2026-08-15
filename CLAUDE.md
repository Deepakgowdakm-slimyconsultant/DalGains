# DalGains — Project Rules

DalGains is an ingredient-first Indian household nutrition tracker.

## Data sources

- Primary: IFCT 2017 (Indian Food Composition Tables, ICMR-National
  Institute of Nutrition).
- USDA is fallback ONLY for ingredients absent from IFCT.

## Architecture rule (non-negotiable)

NEVER hardcode dish-level calorie values. All nutrition is computed from
ingredient quantities via recipes:

```
recipe = { name, aliases[], ingredients: [{ingredient_id, qty, unit}],
           oil_ghee_qty, servings, region_tag }
```

Calories/macros are always derived by summing ingredient-level nutrition,
scaled by quantity.

## UX rules (non-negotiable — app is used by ages ~13 to 80+)

- One question / one decision per screen — no multi-field forms.
- Plain language only — no "enter portion in grams," ask "how much,
  roughly?" using household units (katori, spoon, mutthi).
- Every AI-generated estimate (portion size, dish identification) must be
  shown as EDITABLE before being logged — never silently accepted.
- Support a Kannada/English language toggle from the start, not
  retrofitted later.

## Engineering conventions

- Python 3.11+, use Parquet (not CSV) for any table over ~1000 rows.
- No auth system, no external database server, no cloud dependency until
  explicitly requested — this is a local-first, family-scale app.
- Every new module gets a corresponding test in tests/ before being
  considered done.
- Commit in small, single-purpose chunks with clear messages; do not
  bundle multiple phases into one commit.

## Stop conditions

Do not begin Phase 2 (recipe builder), Phase 3 (logging UX), or later
phases until the project owner explicitly says the current phase is
approved.
