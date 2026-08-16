"""Fuzz every POST endpoint with hypothesis-generated random JSON payloads.

No payload may crash the server -- every response must be 2xx or a valid
4xx, never 5xx (an unhandled exception escaping the route).
"""
import shutil

import pytest
from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import src.core.profiles as profiles
import src.core.units as units
import src.logging.store as store
import src.recipes.builder as builder

REAL_RECIPES_DIR = builder.RECIPES_DIR

_json_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(10**6), max_value=10**6),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=20),
)
_json_value = st.recursive(
    _json_scalar,
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(max_size=10), children, max_size=3),
    ),
    max_leaves=8,
)
random_payload = st.dictionaries(st.text(min_size=1, max_size=15), _json_value, max_size=6)

POST_ENDPOINTS = [
    "/recipes",
    "/beverages/build/chai",
    "/beverages/build/coffee",
    "/beverages/build/lassi",
    "/beverages/build/buttermilk",
    "/beverages/build/nimbu_paani",
    "/beverages/build/juice",
    "/beverages/build/alcohol",
    "/beverages/build/protein_shake",
    "/profile",
    "/units/fuzzuser",
    "/logs/fuzzuser/entries",
]


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(profiles, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")
    isolated_recipes = tmp_path / "recipes"
    shutil.copytree(REAL_RECIPES_DIR, isolated_recipes)
    monkeypatch.setattr(builder, "RECIPES_DIR", isolated_recipes)


@pytest.fixture
def client():
    from src.api.main import app

    return TestClient(app)


@pytest.mark.parametrize("endpoint", POST_ENDPOINTS)
@given(payload=random_payload)
@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
    max_examples=25,
)
def test_random_payload_never_crashes_the_server(client, endpoint, payload):
    response = client.post(endpoint, json=payload)
    assert response.status_code < 500, (
        f"{endpoint} returned {response.status_code} for payload {payload!r}: "
        f"{response.text[:500]}"
    )


@pytest.mark.parametrize("endpoint", POST_ENDPOINTS)
def test_empty_object_payload_never_crashes(client, endpoint):
    response = client.post(endpoint, json={})
    assert response.status_code < 500


@pytest.mark.parametrize("endpoint", POST_ENDPOINTS)
def test_non_object_payload_never_crashes(client, endpoint):
    for payload in [[], "a string", 42, None, True]:
        response = client.post(endpoint, json=payload)
        assert response.status_code < 500, f"{endpoint} crashed on payload {payload!r}"
