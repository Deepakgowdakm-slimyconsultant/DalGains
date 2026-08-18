"""FastAPI TestClient coverage: every route, valid + invalid inputs."""
import shutil

import pytest
from fastapi.testclient import TestClient

import src.recipes.builder as builder

REAL_RECIPES_DIR = builder.RECIPES_DIR


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    # Copy the real seeded recipes into the isolated dir so read tests
    # (get_recipe, nutrition, ...) see realistic data, while writes
    # (create/update/delete) stay isolated from the real data/recipes/.
    isolated_recipes = tmp_path / "recipes"
    shutil.copytree(REAL_RECIPES_DIR, isolated_recipes)
    monkeypatch.setattr(builder, "RECIPES_DIR", isolated_recipes)


@pytest.fixture
def client():
    from src.api.main import app

    return TestClient(app)


def _profile_payload(user_id="apitest"):
    return {
        "user_id": user_id,
        "name": "API Test",
        "age": 28,
        "sex": "male",
        "height_cm": 175,
        "weight_kg": 70,
        "body_type": "mesomorph",
        "activity_level": "moderate",
        "goal": "maintain",
        "dietary_pattern": "vegetarian",
        "eating_phase": "maintenance",
    }


# --- /health -------------------------------------------------------------


def test_health_returns_expected_shape(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["ingredient_count"] > 0
    assert body["recipe_count"] > 0
    assert "version" in body


# --- /ingredients ----------------------------------------------------------


def test_search_ingredients_no_filter(client):
    r = client.get("/ingredients")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_search_ingredients_by_query(client):
    r = client.get("/ingredients", params={"query": "toor dal"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_search_ingredients_by_category(client):
    r = client.get("/ingredients", params={"category": "dal"})
    assert r.status_code == 200
    assert all(i["category"] == "dal" for i in r.json())


def test_search_ingredients_invalid_category_returns_422(client):
    r = client.get("/ingredients", params={"category": "not_a_real_category"})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], list)  # machine-parseable pydantic error body


def test_get_ingredient_by_id(client):
    r = client.get("/ingredients/B021")
    assert r.status_code == 200
    assert r.json()["name"] == "Red gram, dal"


def test_get_ingredient_missing_returns_404(client):
    r = client.get("/ingredients/NOPE999")
    assert r.status_code == 404


def test_get_ingredient_nutrition_resolves_grams(client):
    # B021 (toor dal) has energy_kcal_per_100g -- 100g should return
    # exactly that value.
    ingredient = client.get("/ingredients/B021").json()
    r = client.get("/ingredients/B021/nutrition", params={"qty": 100, "unit": "g"})
    assert r.status_code == 200
    assert r.json()["energy_kcal"] == pytest.approx(ingredient["energy_kcal_per_100g"])


def test_get_ingredient_nutrition_katori_matches_default_calibration(client):
    grams = client.get("/ingredients/B021/nutrition", params={"qty": 150, "unit": "g"}).json()
    katori = client.get("/ingredients/B021/nutrition", params={"qty": 1, "unit": "katori"}).json()
    assert katori == grams


def test_get_ingredient_nutrition_honors_user_calibration(client):
    client.post(
        "/units/alice", json={"unit_name": "katori", "volume_ml": 200, "method": "measured"}
    )
    default = client.get("/ingredients/B021/nutrition", params={"qty": 1, "unit": "katori"}).json()
    alice = client.get(
        "/ingredients/B021/nutrition", params={"qty": 1, "unit": "katori", "user_id": "alice"}
    ).json()
    assert alice["energy_kcal"] > default["energy_kcal"]


def test_get_ingredient_nutrition_missing_ingredient_returns_404(client):
    r = client.get("/ingredients/NOPE999/nutrition", params={"qty": 100, "unit": "g"})
    assert r.status_code == 404


def test_get_ingredient_nutrition_unresolvable_unit_returns_422(client):
    # B021 (toor dal) has no per_piece_g set.
    r = client.get("/ingredients/B021/nutrition", params={"qty": 1, "unit": "piece"})
    assert r.status_code == 422


# --- /recipes -------------------------------------------------------------


def test_list_recipes(client):
    r = client.get("/recipes")
    assert r.status_code == 200
    assert len(r.json()) == 8


def test_list_recipes_fasting_only(client):
    r = client.get("/recipes", params={"fasting_only": True})
    assert r.status_code == 200
    assert all(recipe["is_fasting_safe"] for recipe in r.json())


def test_get_recipe(client):
    r = client.get("/recipes/dal_tadka_north")
    assert r.status_code == 200
    assert r.json()["name"] == "Dal Tadka"


def test_get_recipe_missing_returns_404(client):
    r = client.get("/recipes/not_a_real_recipe")
    assert r.status_code == 404


def _new_recipe_payload(recipe_id="api_test_recipe"):
    return {
        "recipe_id": recipe_id,
        "name": "API Test Recipe",
        "ingredients": [{"ingredient_id": "B021", "qty": 100, "unit": "g"}],
        "oil_ghee": {"type": "none", "qty_g": 0},
        "servings": 1,
        "region_tag": "custom",
        "meal_type": "lunch",
        "is_fasting_safe": False,
        "tags": [],
        "created_by": "test",
    }


def test_post_recipe_creates_and_returns_201(client):
    r = client.post("/recipes", json=_new_recipe_payload())
    assert r.status_code == 201
    assert r.json()["recipe_id"] == "api_test_recipe"


def test_post_recipe_duplicate_returns_409(client):
    client.post("/recipes", json=_new_recipe_payload())
    r = client.post("/recipes", json=_new_recipe_payload())
    assert r.status_code == 409


def test_post_recipe_invalid_payload_returns_422(client):
    r = client.post("/recipes", json={"recipe_id": "bad"})
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], list)


def test_put_recipe_updates(client):
    client.post("/recipes", json=_new_recipe_payload())
    payload = _new_recipe_payload()
    payload["name"] = "Updated Name"
    r = client.put("/recipes/api_test_recipe", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


def test_put_recipe_mismatched_id_returns_400(client):
    client.post("/recipes", json=_new_recipe_payload())
    r = client.put("/recipes/api_test_recipe", json=_new_recipe_payload(recipe_id="different_id"))
    assert r.status_code == 400


def test_put_recipe_missing_returns_404(client):
    r = client.put("/recipes/nonexistent", json=_new_recipe_payload(recipe_id="nonexistent"))
    assert r.status_code == 404


def test_delete_recipe(client):
    client.post("/recipes", json=_new_recipe_payload())
    r = client.delete("/recipes/api_test_recipe")
    assert r.status_code == 204
    assert client.get("/recipes/api_test_recipe").status_code == 404


def test_delete_recipe_missing_returns_404(client):
    r = client.delete("/recipes/not_a_real_recipe")
    assert r.status_code == 404


def test_get_recipe_nutrition(client):
    r = client.get("/recipes/dal_tadka_north/nutrition", params={"servings": 1})
    assert r.status_code == 200
    assert r.json()["energy_kcal"] > 0


def test_get_recipe_nutrition_invalid_servings_returns_422(client):
    r = client.get("/recipes/dal_tadka_north/nutrition", params={"servings": -1})
    assert r.status_code == 422


def test_get_recipe_nutrition_missing_recipe_returns_404(client):
    r = client.get("/recipes/not_a_real_recipe/nutrition")
    assert r.status_code == 404


def test_get_recipe_nutrition_unknown_ingredient_returns_422(client):
    payload = _new_recipe_payload()
    payload["ingredients"] = [{"ingredient_id": "NOTAREALID", "qty": 100, "unit": "g"}]
    client.post("/recipes", json=payload)
    r = client.get("/recipes/api_test_recipe/nutrition")
    assert r.status_code == 422


# --- /beverages/build/* ------------------------------------------------


def test_build_chai(client):
    r = client.post(
        "/beverages/build/chai",
        json={"milk_ml": 60, "milk_type": "toned", "sugar_tsp": 1, "size_ml": 150},
    )
    assert r.status_code == 200
    assert r.json()["base"] == "tea"


def test_build_chai_missing_field_returns_422(client):
    r = client.post("/beverages/build/chai", json={"milk_ml": 60})
    assert r.status_code == 422


def test_build_coffee(client):
    r = client.post(
        "/beverages/build/coffee",
        json={"style": "filter", "milk_ml": 80, "milk_type": "toned", "sugar_tsp": 1},
    )
    assert r.status_code == 200


def test_build_lassi(client):
    r = client.post(
        "/beverages/build/lassi", json={"type": "sweet", "yogurt_ml": 200, "sugar_g": 20}
    )
    assert r.status_code == 200


def test_build_buttermilk(client):
    r = client.post("/beverages/build/buttermilk", json={"volume_ml": 250})
    assert r.status_code == 200


def test_build_nimbu_paani(client):
    r = client.post(
        "/beverages/build/nimbu_paani", json={"volume_ml": 250, "sugar_g": 15}
    )
    assert r.status_code == 200


def test_build_juice(client):
    r = client.post("/beverages/build/juice", json={"fruit": "mango", "volume_ml": 250})
    assert r.status_code == 200


def test_build_juice_unknown_fruit_returns_422(client):
    r = client.post(
        "/beverages/build/juice", json={"fruit": "not_a_real_fruit_xyz", "volume_ml": 250}
    )
    assert r.status_code == 422


def test_build_alcohol(client):
    r = client.post(
        "/beverages/build/alcohol", json={"type": "beer", "volume_ml": 500, "abv_pct": 5}
    )
    assert r.status_code == 200


def test_build_alcohol_invalid_type_returns_422(client):
    r = client.post(
        "/beverages/build/alcohol", json={"type": "moonshine", "volume_ml": 500, "abv_pct": 5}
    )
    assert r.status_code == 422


def test_build_protein_shake(client):
    r = client.post(
        "/beverages/build/protein_shake",
        json={"protein_g": 25, "milk_ml": 250, "milk_type": "toned"},
    )
    assert r.status_code == 200


# --- /profile ---------------------------------------------------------------


def test_post_profile_creates_201(client):
    r = client.post("/profile", json=_profile_payload())
    assert r.status_code == 201


def test_post_profile_duplicate_returns_409(client):
    client.post("/profile", json=_profile_payload())
    r = client.post("/profile", json=_profile_payload())
    assert r.status_code == 409


def test_post_profile_invalid_age_returns_422(client):
    payload = _profile_payload()
    payload["age"] = 300
    r = client.post("/profile", json=payload)
    assert r.status_code == 422
    assert isinstance(r.json()["detail"], list)


def test_get_profile(client):
    client.post("/profile", json=_profile_payload())
    r = client.get("/profile/apitest")
    assert r.status_code == 200


def test_get_profile_missing_returns_404(client):
    r = client.get("/profile/nobody")
    assert r.status_code == 404


def test_put_profile_updates(client):
    client.post("/profile", json=_profile_payload())
    payload = _profile_payload()
    payload["name"] = "Updated"
    r = client.put("/profile/apitest", json=payload)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"


def test_put_profile_mismatched_id_returns_400(client):
    client.post("/profile", json=_profile_payload())
    r = client.put("/profile/apitest", json=_profile_payload(user_id="someone_else"))
    assert r.status_code == 400


def test_put_profile_missing_returns_404(client):
    r = client.put("/profile/nobody", json=_profile_payload(user_id="nobody"))
    assert r.status_code == 404


def test_delete_profile(client):
    client.post("/profile", json=_profile_payload())
    r = client.delete("/profile/apitest")
    assert r.status_code == 204
    assert client.get("/profile/apitest").status_code == 404


def test_delete_profile_missing_returns_404(client):
    r = client.delete("/profile/nobody")
    assert r.status_code == 404


def test_get_plan(client):
    client.post("/profile", json=_profile_payload())
    r = client.get("/profile/apitest/plan")
    assert r.status_code == 200
    assert r.json()["daily_kcal"] > 0


def test_get_plan_missing_profile_returns_404(client):
    r = client.get("/profile/nobody/plan")
    assert r.status_code == 404


def test_get_weight_empty_for_user_who_never_logged(client):
    r = client.get("/profile/apitest/weight")
    assert r.status_code == 200
    assert r.json() == {}


def test_post_and_get_weight(client):
    r = client.post("/profile/apitest/weight", json={"user_id": "apitest", "date": "2026-01-01", "weight_kg": 70.5})
    assert r.status_code == 201
    r2 = client.get("/profile/apitest/weight")
    assert r2.json() == {"2026-01-01": 70.5}


def test_post_weight_mismatched_user_id_returns_400(client):
    r = client.post("/profile/apitest/weight", json={"user_id": "someone-else", "date": "2026-01-01", "weight_kg": 70})
    assert r.status_code == 400


# --- /units ------------------------------------------------------------


def test_get_units_empty_for_new_user(client):
    r = client.get("/units/apitest")
    assert r.status_code == 200
    assert r.json() == {}


def test_post_unit_calibration(client):
    r = client.post(
        "/units/apitest", json={"unit_name": "katori", "volume_ml": 180, "method": "measured"}
    )
    assert r.status_code == 201
    r2 = client.get("/units/apitest")
    assert "katori" in r2.json()


def test_post_unit_invalid_method_returns_422(client):
    r = client.post(
        "/units/apitest", json={"unit_name": "katori", "volume_ml": 180, "method": "guessed"}
    )
    assert r.status_code == 422


# --- /logs -------------------------------------------------------------


def test_post_log_entry(client):
    r = client.post("/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"})
    assert r.status_code == 201
    assert r.json()["computed_totals"]["energy_kcal"] > 0


def test_post_log_entry_honors_client_supplied_timestamp(client):
    # The frontend's log flow lets a user backfill an entry against a
    # chosen time (e.g. a one-tap meal slot) rather than always "now" --
    # the route must forward entry.timestamp through to the log, not
    # silently overwrite it with the current time.
    r = client.post(
        "/logs/apitest/entries",
        json={
            "ingredient_id": "B021",
            "qty": 100,
            "unit": "g",
            "timestamp": "2026-01-01T13:00:00Z",
        },
    )
    assert r.status_code == 201
    assert r.json()["entries"][0]["timestamp"] == "2026-01-01T13:00:00Z"


def test_post_log_entry_defaults_timestamp_to_now(client):
    r = client.post("/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"})
    assert r.status_code == 201
    assert r.json()["entries"][0]["timestamp"] is not None


def test_post_log_entry_both_ids_returns_422(client):
    r = client.post(
        "/logs/apitest/entries",
        json={"recipe_id": "dal_tadka_north", "ingredient_id": "B021", "qty": 1, "unit": "g"},
    )
    assert r.status_code == 422


def test_post_log_entry_neither_id_returns_422(client):
    r = client.post("/logs/apitest/entries", json={"qty": 1, "unit": "g"})
    assert r.status_code == 422


def test_get_log_day(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.get(f"/logs/apitest/day/{date}")
    assert r.status_code == 200


def test_get_category_breakdown(client):
    post = client.post("/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"})
    date = post.json()["log_id"]
    ingredient = client.get("/ingredients/B021").json()

    r = client.get(f"/logs/apitest/category_breakdown/{date}/{date}")
    assert r.status_code == 200
    body = r.json()
    assert body["by_category"]["dal"]["protein_g"] == pytest.approx(ingredient["protein_g_per_100g"])
    assert body["beverage_kcal_by_date"][date] == pytest.approx(0.0)
    assert body["total_kcal_by_date"][date] == pytest.approx(ingredient["energy_kcal_per_100g"])


def test_get_category_breakdown_invalid_date_returns_422(client):
    r = client.get("/logs/apitest/category_breakdown/not-a-date/2026-01-07")
    assert r.status_code == 422


def test_get_category_breakdown_empty_for_new_user(client):
    r = client.get("/logs/nobody-yet/category_breakdown/2026-01-01/2026-01-07")
    assert r.status_code == 200
    assert r.json() == {"by_category": {}, "beverage_kcal_by_date": {}, "total_kcal_by_date": {}}


def test_get_log_day_missing_returns_404(client):
    r = client.get("/logs/apitest/day/2020-01-01")
    assert r.status_code == 404


def test_post_day_tag(client):
    post = client.post("/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"})
    date = post.json()["log_id"]
    r = client.post(f"/logs/apitest/day/{date}/tags", json={"tag": "diwali"})
    assert r.status_code == 200
    assert "diwali" in r.json()["tags"]


def test_post_day_tag_missing_day_returns_404(client):
    r = client.post("/logs/apitest/day/2020-01-01/tags", json={"tag": "diwali"})
    assert r.status_code == 404


def test_get_logged_dates(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.get("/logs/apitest/dates")
    assert r.status_code == 200
    assert date in r.json()


def test_get_logged_dates_empty_for_new_user(client):
    r = client.get("/logs/nobody-yet/dates")
    assert r.status_code == 200
    assert r.json() == []


def test_get_log_range(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.get(f"/logs/apitest/range/{date}/{date}")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_log_range_skips_missing_days(client):
    r = client.get("/logs/nobody-yet/range/2020-01-01/2020-01-07")
    assert r.status_code == 200
    assert r.json() == []


def test_get_log_range_invalid_date_returns_422(client):
    r = client.get("/logs/apitest/range/not-a-date/2020-01-07")
    assert r.status_code == 422


def test_get_log_week(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.get(f"/logs/apitest/week/{date}")
    assert r.status_code == 200
    assert "averages" in r.json()


def test_get_log_week_invalid_date_returns_422(client):
    r = client.get("/logs/apitest/week/not-a-date")
    assert r.status_code == 422


def test_post_log_entry_on_quarantined_day_returns_409(client):
    # No timestamp in the request body -> defaults to "now", so the
    # quarantined row has to be today's, not a fixed date.
    from datetime import date, datetime, timezone

    from src.db.models import MealLogRow
    from src.db.session import get_session

    with get_session() as session:
        session.add(
            MealLogRow(
                user_id="apitest",
                log_id=date.today().isoformat(),
                timestamp=datetime.now(timezone.utc),
                entries=[],
                computed_totals={"energy_kcal": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0, "fiber_g": 0},
                notes=None,
                tags=[],
            )
        )
    r = client.post("/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"})
    assert r.status_code == 409


def test_delete_log_entry(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.delete(f"/logs/apitest/entries/{date}/0")
    assert r.status_code == 200


def test_delete_log_entry_missing_day_returns_404(client):
    r = client.delete("/logs/apitest/entries/2020-01-01/0")
    assert r.status_code == 404


def test_delete_log_entry_out_of_range_returns_400(client):
    post = client.post(
        "/logs/apitest/entries", json={"ingredient_id": "B021", "qty": 100, "unit": "g"}
    )
    date = post.json()["log_id"]
    r = client.delete(f"/logs/apitest/entries/{date}/99")
    assert r.status_code == 400


# --- /insights ------------------------------------------------------------


def test_get_insights_for_user_with_no_data(client):
    r = client.get("/insights/nobody")
    assert r.status_code == 200
    assert r.json() == []


def test_get_insights_with_as_of_param(client):
    r = client.get("/insights/apitest", params={"as_of": "2026-01-01"})
    assert r.status_code == 200
