#!/usr/bin/env python3
"""Manual timestamped SQLite dump to data/backups/. Run before anything
risky (a migration, a bulk edit): `venv/bin/python scripts/backup_db.py`.

Uses SQLite's own backup API (not a plain file copy) so a backup taken
while the app is running never captures a half-written page -- safe to
run against a live DB. Automated/scheduled backups are a Phase 6
candidate; this is the manual "before I do something risky" tool for
now.
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.session import DATABASE_URL

BACKUPS_DIR = Path(__file__).resolve().parents[1] / "data" / "backups"


def main() -> None:
    if not DATABASE_URL.startswith("sqlite:///"):
        print(f"backup_db.py only backs up file-based SQLite; DATABASE_URL is {DATABASE_URL!r}. Nothing to do.")
        return

    db_path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    if not db_path.exists():
        print(f"No database file at {db_path} yet -- nothing to back up.")
        return

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = BACKUPS_DIR / f"dalgains-{stamp}.db"

    source = sqlite3.connect(db_path)
    dest = sqlite3.connect(backup_path)
    with dest:
        source.backup(dest)
    source.close()
    dest.close()

    print(f"Backed up {db_path} -> {backup_path} ({backup_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
