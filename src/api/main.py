"""FastAPI app entry point.

Security posture: no auth. See README.md's "Security posture (current)"
section -- DalGains is a local-first, single-household app; this API is
meant to run on localhost for a local frontend, not to be exposed on a
public network without adding authentication first.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import beverages, ingredients, insights, logs, profile, units
from src.api.routes import recipes as recipes_routes
from src.core.ingredients import load_ingredients
from src.i18n.loader import load_all_locales
from src.recipes.builder import list_recipes

APP_VERSION = "0.3.0"  # Phase 3

# "On app start, assert every key in en.json exists in hi.json and
# kn.json" (Phase 3 brief) -- runs at import time, before the app object
# is even usable, and raises rather than letting an incomplete locale
# silently fall back to English string-by-string.
load_all_locales()

app = FastAPI(title="DalGains API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingredients.router)
app.include_router(recipes_routes.router)
app.include_router(beverages.router)
app.include_router(profile.router)
app.include_router(units.router)
app.include_router(logs.router)
app.include_router(insights.router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "ingredient_count": len(load_ingredients()),
        "recipe_count": len(list_recipes()),
        "version": APP_VERSION,
    }
