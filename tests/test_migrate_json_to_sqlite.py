"""Migration correctness: a Phase-3-style JSON log must load into
SQLite with byte-identical nutrition totals -- not just "some value
came back," the exact floats, since this is what the WHEN-DONE report
for Phase 5 claims.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import migrate_json_to_sqlite as migrate  # noqa: E402

from src.core.schemas import UserProfile
from src.logging.store import load_day


@pytest.fixture(autouse=True)
def isolated_source_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(migrate, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(migrate, "LOGS_DIR", tmp_path / "logs")
    return tmp_path


def _profile_json(**overrides) -> dict:
    data = dict(
        user_id="alice",
        name="Alice",
        age=28,
        sex="female",
        height_cm=165,
        weight_kg=60,
        body_type="mesomorph",
        activity_level="moderate",
        goal="maintain",
        dietary_pattern="vegetarian",
        eating_phase="maintenance",
        fasting_protocol="none",
        medical_flags=[],
    )
    data.update(overrides)
    return data


def test_migrate_meal_log_preserves_nutrition_totals_exactly(isolated_source_dirs):
    tmp_path = isolated_source_dirs
    computed_totals = {
        "energy_kcal": 201.10375000000002,
        "protein_g": 9.515125000000001,
        "fat_g": 6.023875,
        "carbs_g": 26.101,
        "fiber_g": 5.2958750000000006,
    }
    log_json = {
        "log_id": "2026-08-17",
        "user_id": "alice",
        "timestamp": "2026-08-17T13:00:00+00:00",
        "entries": [
            {
                "recipe_id": "dal_tadka_north",
                "ingredient_id": None,
                "qty": 1,
                "unit": "serving",
                "timestamp": "2026-08-17T13:00:00+00:00",
                "outside_eating_window": False,
            }
        ],
        "computed_totals": computed_totals,
        "notes": None,
        "tags": [],
    }
    log_dir = tmp_path / "logs" / "alice"
    log_dir.mkdir(parents=True)
    (log_dir / "2026-08-17.json").write_text(json.dumps(log_json))

    migrated, skipped = migrate.migrate_meal_logs()
    assert migrated == 1
    assert skipped == 0

    loaded = load_day("alice", "2026-08-17")
    assert loaded.computed_totals.model_dump() == computed_totals


def test_migrate_profile_round_trips(isolated_source_dirs):
    tmp_path = isolated_source_dirs
    user_dir = tmp_path / "users" / "alice"
    user_dir.mkdir(parents=True)
    (user_dir / "profile.json").write_text(json.dumps(_profile_json()))

    migrated, skipped = migrate.migrate_profiles()
    assert migrated == 1
    assert skipped == 0

    from src.core.profiles import load_profile

    loaded = load_profile("alice")
    assert loaded == UserProfile(**_profile_json())


def test_migrate_is_idempotent(isolated_source_dirs):
    tmp_path = isolated_source_dirs
    user_dir = tmp_path / "users" / "alice"
    user_dir.mkdir(parents=True)
    (user_dir / "profile.json").write_text(json.dumps(_profile_json()))

    migrate.migrate_profiles()
    migrate.migrate_profiles()  # running twice must not duplicate or error

    from src.core.profiles import load_profile

    assert load_profile("alice") == UserProfile(**_profile_json())


def test_migrate_skips_malformed_file_without_aborting(isolated_source_dirs):
    tmp_path = isolated_source_dirs
    good_dir = tmp_path / "users" / "alice"
    good_dir.mkdir(parents=True)
    (good_dir / "profile.json").write_text(json.dumps(_profile_json()))

    bad_dir = tmp_path / "users" / "bob"
    bad_dir.mkdir(parents=True)
    (bad_dir / "profile.json").write_text("{not valid json")

    migrated, skipped = migrate.migrate_profiles()
    assert migrated == 1
    assert skipped == 1

    from src.core.profiles import load_profile

    assert load_profile("alice") is not None
    assert load_profile("bob") is None
