"""Fuzz the ingredient validation boundary (src.core.ingredients.load_ingredients).

Feeds deliberately malformed rows through the real load_ingredients() code
path (via a temp parquet file, same as production) and asserts every row
is accounted for: either validated and returned, or excluded and recorded
in ingredients_rejected.json with a reason. Nothing may vanish silently,
and no malformed input may raise an exception other than being cleanly
caught and rejected.
"""
import json

import pandas as pd
import pytest

import src.core.ingredients as ingredients_module

BASE_VALID_ROW = {
    "ingredient_id": "FUZZ001",
    "name": "Fuzz Ingredient",
    "aliases": ["fuzz"],
    "energy_kcal_per_100g": 100.0,
    "protein_g_per_100g": 5.0,
    "fat_g_per_100g": 5.0,
    "carbs_g_per_100g": 5.0,
    "fiber_g_per_100g": 5.0,
    "source": "IFCT",
    "category": "other",
}


def _write_and_load(tmp_path, monkeypatch, rows):
    parquet_path = tmp_path / "fuzz_ingredients.parquet"
    rejected_path = tmp_path / "fuzz_rejected.json"
    monkeypatch.setattr(ingredients_module, "REJECTED_PATH", rejected_path)

    pd.DataFrame.from_records(rows).to_parquet(parquet_path, index=False)

    validated = ingredients_module.load_ingredients(path=parquet_path)
    rejected = json.loads(rejected_path.read_text())
    return validated, rejected


def test_negative_energy_is_rejected_not_silently_accepted(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_NEG", "energy_kcal_per_100g": -50.0}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_NEG" not in validated
    assert any(r["ingredient_id"] == "FUZZ_NEG" for r in rejected)


def test_energy_way_over_bound_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_HUGE", "energy_kcal_per_100g": 50_000.0}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_HUGE" not in validated
    assert any(r["ingredient_id"] == "FUZZ_HUGE" for r in rejected)


def test_infinite_value_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_INF", "energy_kcal_per_100g": float("inf")}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_INF" not in validated
    assert any(r["ingredient_id"] == "FUZZ_INF" for r in rejected)


def test_negative_macro_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_NEGP", "protein_g_per_100g": -1.0}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_NEGP" not in validated
    assert any(r["ingredient_id"] == "FUZZ_NEGP" for r in rejected)


def test_string_in_numeric_field_is_rejected_not_crashed(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_STR", "energy_kcal_per_100g": "not a number"}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_STR" not in validated
    assert any(r["ingredient_id"] == "FUZZ_STR" for r in rejected)


def test_unknown_source_literal_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_SRC", "source": "WIKIPEDIA"}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_SRC" not in validated
    assert any(r["ingredient_id"] == "FUZZ_SRC" for r in rejected)


def test_unknown_category_literal_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_CAT", "category": "junk_food_supreme"}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_CAT" not in validated
    assert any(r["ingredient_id"] == "FUZZ_CAT" for r in rejected)


def test_missing_required_column_entirely_is_rejected(tmp_path, monkeypatch):
    row = {k: v for k, v in BASE_VALID_ROW.items() if k != "category"}
    row["ingredient_id"] = "FUZZ_NOCOL"
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "FUZZ_NOCOL" not in validated
    assert any(r["ingredient_id"] == "FUZZ_NOCOL" for r in rejected)


def test_empty_ingredient_id_is_rejected(tmp_path, monkeypatch):
    row = {**BASE_VALID_ROW, "ingredient_id": ""}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    assert "" not in validated
    assert len(rejected) == 1


def test_extremely_long_alias_list_is_handled_without_crashing(tmp_path, monkeypatch):
    row = {
        **BASE_VALID_ROW,
        "ingredient_id": "FUZZ_LONGALIAS",
        "aliases": [f"alias_{i}" for i in range(5000)],
    }
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    # A huge-but-well-formed alias list has nothing invalid about it, so it
    # must be accepted as-is (not silently truncated or dropped).
    assert "FUZZ_LONGALIAS" in validated
    assert len(validated["FUZZ_LONGALIAS"].aliases) == 5000


@pytest.mark.parametrize(
    "weird_name",
    [
        "\U0001f6362\U0001f525 spicy curry \U0001f336️",
        "अरहर दाल",  # "arhar dal" in Devanagari
        "​Zero​Width​Name",
        "name\twith\ttabs",
        "RTL: ‮example‬",
        "null\x00byte",
    ],
)
def test_unicode_edge_case_names_are_handled_without_crashing(tmp_path, monkeypatch, weird_name):
    row = {**BASE_VALID_ROW, "ingredient_id": "FUZZ_UNICODE", "name": weird_name}
    validated, rejected = _write_and_load(tmp_path, monkeypatch, [row])
    # Structurally valid (non-empty) unicode name: must be accepted or
    # explicitly rejected with a reason, never silently dropped or crash
    # the loader.
    assert ("FUZZ_UNICODE" in validated) or any(
        r["ingredient_id"] == "FUZZ_UNICODE" for r in rejected
    )


def test_mixed_batch_never_raises_and_accounts_for_every_row(tmp_path, monkeypatch):
    rows = [
        BASE_VALID_ROW,
        {**BASE_VALID_ROW, "ingredient_id": "BAD1", "energy_kcal_per_100g": -1},
        {**BASE_VALID_ROW, "ingredient_id": "BAD2", "source": "NOPE"},
        {**BASE_VALID_ROW, "ingredient_id": "GOOD2"},
    ]
    validated, rejected = _write_and_load(tmp_path, monkeypatch, rows)
    accounted_ids = set(validated) | {r["ingredient_id"] for r in rejected}
    assert accounted_ids == {row["ingredient_id"] for row in rows}
