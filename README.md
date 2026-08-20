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

Phase 5 (in progress): zero-cost deployment to Vercel (frontend) and
Render (backend) -- SQLite persistence, magic-link auth, production
config/CORS/security headers. Phases 1-4 shipped household-unit-aware
recipe math, meal logging, an insights engine, a FastAPI service
layer, and the full React/PWA frontend with dark mode and
accessibility coverage.

## Deployment

DalGains supports two parallel deployment paths, both from `main`
branch, sharing the same backend (`src/`):

- **React + FastAPI edition** (`frontend/` + `src/api/`) -- deploys to
  Render + Vercel. See `scripts/deploy_render.md` and
  `scripts/deploy_vercel.md`.
- **Streamlit edition** (`streamlit_app/`) -- deploys to Streamlit
  Community Cloud for free with persistent storage. See
  `scripts/deploy_streamlit.md` (added in a future session).

## Security posture (current)

**The API (`src/api/`) requires magic-link auth, invite-only, since
Phase 5.** No passwords, no OAuth, no third-party auth service lock-in
-- see `src/auth/`. Every route scoped by `user_id` checks the
authenticated session's own id against it
(`src.auth.dependencies.require_own_user`) and 403s on a mismatch; a
route is never protected merely because `user_id` appears in its URL.

Sessions live in an httpOnly cookie (`dalgains_session`), never
readable by frontend JS. In production the cookie is `Secure` and
`SameSite=None` (required for the frontend/backend split-domain
deployment -- see `src/api/routes/auth.py`'s `_cookie_samesite`
docstring for why this deliberately isn't `Lax` in prod); local dev
uses `SameSite=Lax` since both run on `localhost` there. CORS
(`src/api/main.py`) only allows the exact origins in
`CORS_ALLOWED_ORIGINS` — no wildcard, which browsers refuse to pair
with credentialed requests anyway. `src/api/security.py` adds HSTS
(prod only), `X-Content-Type-Options`, `X-Frame-Options: DENY`,
`Referrer-Policy`, and a restrictive CSP to every response.

`src/config.py` refuses to boot in production without a real
`JWT_SECRET`, `RESEND_API_KEY`, and a non-default `CORS_ALLOWED_ORIGINS`
-- see `.env.example` for the full list of what's configurable and
what production requires.

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
alembic upgrade head   # creates/updates data/dalgains.db
pytest
```

Backend data (profiles, logs, calibrations) lives in a SQLite database
at `data/dalgains.db` (path configurable via `DATABASE_URL`), managed
through [alembic](https://alembic.sqlalchemy.org/) migrations under
`src/db/migrations/`. Tests never touch this file -- they run against
an in-memory database (see `tests/conftest.py`).
