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
- Every new module gets a corresponding test in tests/ before being
  considered done.
- Commit in small, single-purpose chunks with clear messages; do not
  bundle multiple phases into one commit.

## Cloud dependency policy (amended, Phase 5)

The original "no cloud dependency" rule is now scoped to **no cloud
dependency for data or business logic**: nutrition computation, recipe
resolution, and the pydantic/SQLAlchemy data layer must keep working
against a local SQLite file with zero external services. What's
permitted is deployment infrastructure — hosting, CDN, DNS — chosen
under a hard constraint of zero payment and no credit card anywhere.

Chosen hosts (do not re-litigate without a stated reason):
- **Frontend:** Vercel free tier (no card, no sleeping, generous
  bandwidth).
- **Backend:** Hugging Face Spaces, Docker SDK, free CPU tier (no
  card, no sleeping, persistent storage via the Space's `/data`
  volume or HF Datasets).
- **Email (magic-link auth):** Resend free tier (no card, 100
  emails/day).
- **Uptime monitoring:** UptimeRobot free tier (no card).

Auth is permitted from Phase 5 onward (magic-link, invite-only) since
the app now has a real deployment target with more than one user
reachable over the network. This does not relax the local-first data
rule above — user data still lives in this app's own SQLite file, not
a third-party data store.

## Stop conditions

Do not begin Phase 2 (recipe builder), Phase 3 (logging UX), Phase 5
(deployment), Phase 6, or later phases until the project owner
explicitly says the current phase is approved.
