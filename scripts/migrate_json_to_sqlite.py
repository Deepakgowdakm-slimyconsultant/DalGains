#!/usr/bin/env python3
"""One-time migration: data/users/**/*.json + data/logs/**/*.json -> SQLite.

Idempotent -- every write goes through src.db.repositories, whose
save_* functions upsert (delete-then-insert) rather than insert-only, so
running this script twice just re-writes the same rows, never
duplicates or errors on a second run.

Malformed files are reported and skipped, never allowed to abort the
whole run -- one bad file shouldn't block migrating everything else.
Run with: venv/bin/python scripts/migrate_json_to_sqlite.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import ValidationError

from src.core.schemas import HouseholdUnit, MealLog, UserProfile, WeightEntry
from src.db import repositories

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
USERS_DIR = DATA_DIR / "users"
LOGS_DIR = DATA_DIR / "logs"


def migrate_profiles() -> tuple[int, int]:
    migrated = 0
    skipped = 0
    for profile_path in sorted(USERS_DIR.glob("*/profile.json")):
        try:
            profile = UserProfile(**json.loads(profile_path.read_text()))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            print(f"  SKIP {profile_path}: {exc}")
            skipped += 1
            continue
        repositories.save_profile(profile)
        migrated += 1
    return migrated, skipped


def migrate_household_units() -> tuple[int, int]:
    migrated = 0
    skipped = 0
    for units_path in sorted(USERS_DIR.glob("*/household_units.json")):
        try:
            data = json.loads(units_path.read_text())
        except json.JSONDecodeError as exc:
            print(f"  SKIP {units_path}: {exc}")
            skipped += 1
            continue
        for unit_name, entry in data.items():
            try:
                unit = HouseholdUnit(**entry)
            except (ValidationError, TypeError, ValueError) as exc:
                print(f"  SKIP {units_path}:{unit_name}: {exc}")
                skipped += 1
                continue
            repositories.save_calibration(unit)
            migrated += 1
    return migrated, skipped


def migrate_weight_logs() -> tuple[int, int]:
    migrated = 0
    skipped = 0
    for weight_path in sorted(USERS_DIR.glob("*/weight_log.json")):
        user_id = weight_path.parent.name
        try:
            data = json.loads(weight_path.read_text())
        except json.JSONDecodeError as exc:
            print(f"  SKIP {weight_path}: {exc}")
            skipped += 1
            continue
        for date, weight_kg in data.items():
            try:
                entry = WeightEntry(user_id=user_id, date=date, weight_kg=weight_kg)
            except (ValidationError, TypeError, ValueError) as exc:
                print(f"  SKIP {weight_path}:{date}: {exc}")
                skipped += 1
                continue
            repositories.save_weight(entry)
            migrated += 1
    return migrated, skipped


def migrate_meal_logs() -> tuple[int, int]:
    migrated = 0
    skipped = 0
    for log_path in sorted(LOGS_DIR.glob("*/*.json")):
        try:
            meal_log = MealLog(**json.loads(log_path.read_text()))
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
            print(f"  SKIP {log_path}: {exc}")
            skipped += 1
            continue
        repositories.save_meal_log(meal_log)
        migrated += 1
    return migrated, skipped


def main() -> None:
    print("Migrating profiles...")
    p_migrated, p_skipped = migrate_profiles()
    print(f"  {p_migrated} migrated, {p_skipped} skipped")

    print("Migrating household unit calibrations...")
    u_migrated, u_skipped = migrate_household_units()
    print(f"  {u_migrated} migrated, {u_skipped} skipped")

    print("Migrating weight logs...")
    w_migrated, w_skipped = migrate_weight_logs()
    print(f"  {w_migrated} migrated, {w_skipped} skipped")

    print("Migrating meal logs...")
    m_migrated, m_skipped = migrate_meal_logs()
    print(f"  {m_migrated} migrated, {m_skipped} skipped")

    total_migrated = p_migrated + u_migrated + w_migrated + m_migrated
    total_skipped = p_skipped + u_skipped + w_skipped + m_skipped
    print(f"\nDone: {total_migrated} rows migrated, {total_skipped} skipped.")


if __name__ == "__main__":
    main()
