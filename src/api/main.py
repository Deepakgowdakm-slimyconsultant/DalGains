"""FastAPI app entry point.

Security posture: magic-link auth, invite-only, since Phase 5 (see
README.md's "Security posture" section). Every route with a {user_id}
path param is gated by src.auth.dependencies.require_own_user.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import auth, beverages, ingredients, insights, logs, profile, units
from src.api.routes import recipes as recipes_routes
from src.auth import invitation
from src.config import get_settings
from src.core.ingredients import load_ingredients
from src.i18n.loader import load_all_locales
from src.recipes.builder import list_recipes

APP_VERSION = "0.4.0"  # Phase 5

# "On app start, assert every key in en.json exists in hi.json and
# kn.json" (Phase 3 brief) -- runs at import time, before the app object
# is even usable, and raises rather than letting an incomplete locale
# silently fall back to English string-by-string.
load_all_locales()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    admin_email = get_settings().ADMIN_EMAIL
    if admin_email:
        admin_email = admin_email.lower()
        if not invitation.is_invited(admin_email):
            invitation.invite(admin_email, invited_by="system")
    yield


app = FastAPI(title="DalGains API", version=APP_VERSION, lifespan=_lifespan)

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
app.include_router(auth.router)
app.include_router(auth.admin_router)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "ingredient_count": len(load_ingredients()),
        "recipe_count": len(list_recipes()),
        "version": APP_VERSION,
    }
