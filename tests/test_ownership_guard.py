"""Cross-user access must return 403 on every route scoped by user_id --
this is the systematic sweep backing src/auth/dependencies.py's
require_own_user. Without it, an authenticated user could read or write
another user's profile/logs/calibrations just by changing the ID in the
URL. Each entry below is one real route from src/api/routes/{profile,
units,logs,insights}.py.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.auth import store
from src.auth.jwt import SESSION_COOKIE_NAME, create_session_token

ME = "attacker"
VICTIM = "victim"


@pytest.fixture
def client():
    if store.get_user_by_id(ME) is None:
        store.create_user(ME, "attacker@example.com")
    c = TestClient(app)
    c.cookies.set(SESSION_COOKIE_NAME, create_session_token(ME))
    return c


# (method, path templated against VICTIM's id, json body or None)
PROTECTED_ROUTES = [
    ("GET", f"/profile/{VICTIM}", None),
    ("PUT", f"/profile/{VICTIM}", {
        "user_id": VICTIM, "name": "X", "age": 30, "sex": "male", "height_cm": 170, "weight_kg": 70,
        "body_type": "mesomorph", "activity_level": "moderate", "goal": "maintain",
        "dietary_pattern": "vegetarian", "eating_phase": "maintenance",
    }),
    ("DELETE", f"/profile/{VICTIM}", None),
    ("GET", f"/profile/{VICTIM}/plan", None),
    ("GET", f"/profile/{VICTIM}/weight", None),
    ("POST", f"/profile/{VICTIM}/weight", {"user_id": VICTIM, "date": "2026-01-01", "weight_kg": 65}),
    ("GET", f"/units/{VICTIM}", None),
    ("POST", f"/units/{VICTIM}", {"unit_name": "katori", "volume_ml": 180, "method": "measured"}),
    ("POST", f"/logs/{VICTIM}/entries", {"ingredient_id": "B021", "qty": 100, "unit": "g"}),
    ("GET", f"/logs/{VICTIM}/day/2026-01-01", None),
    ("POST", f"/logs/{VICTIM}/day/2026-01-01/tags", {"tag": "diwali"}),
    ("GET", f"/logs/{VICTIM}/dates", None),
    ("GET", f"/logs/{VICTIM}/range/2026-01-01/2026-01-07", None),
    ("GET", f"/logs/{VICTIM}/category_breakdown/2026-01-01/2026-01-07", None),
    ("GET", f"/logs/{VICTIM}/week/2026-01-07", None),
    ("DELETE", f"/logs/{VICTIM}/entries/2026-01-01/0", None),
    ("GET", f"/insights/{VICTIM}", None),
]


@pytest.mark.parametrize("method,path,body", PROTECTED_ROUTES, ids=[f"{m} {p}" for m, p, _ in PROTECTED_ROUTES])
def test_cross_user_access_returns_403(client, method, path, body):
    response = client.request(method, path, json=body)
    assert response.status_code == 403, f"{method} {path} -> {response.status_code}, expected 403"


def test_post_profile_for_another_user_returns_403(client):
    """POST /profile has no {user_id} path param -- the ownership check
    is against the body's user_id instead (see src/api/routes/profile.py)."""
    r = client.post(
        "/profile",
        json={
            "user_id": VICTIM, "name": "X", "age": 30, "sex": "male", "height_cm": 170, "weight_kg": 70,
            "body_type": "mesomorph", "activity_level": "moderate", "goal": "maintain",
            "dietary_pattern": "vegetarian", "eating_phase": "maintenance",
        },
    )
    assert r.status_code == 403


def test_own_user_id_is_not_blocked(client):
    """Sanity check that require_own_user isn't blocking everything --
    only mismatched IDs. Full route-level behavior is covered in
    test_api.py; this just confirms the guard passes through correctly."""
    r = client.get(f"/profile/{ME}")
    assert r.status_code == 404  # no profile yet, but NOT 403


def test_unauthenticated_request_returns_401_not_403():
    """No session at all is a 401 (not authenticated), distinct from a
    403 (authenticated as someone else)."""
    anon = TestClient(app)
    r = anon.get(f"/profile/{VICTIM}")
    assert r.status_code == 401
