"""Corrupted-on-disk meal logs must quarantine, never crash the app.

Broader/more exhaustive than the couple of quarantine checks already in
tests/test_logging.py -- this file is the dedicated corruption suite the
Phase 3 brief asks for.
"""
from datetime import datetime, timezone

import pytest

import src.core.profiles as profiles
import src.core.units as units
import src.logging.store as store
from src.core.schemas import QuarantinedLog
from src.logging import engine
from src.logging.aggregation import weekly_totals


@pytest.fixture(autouse=True)
def isolated_data_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(profiles, "USERS_DIR", tmp_path / "users")
    monkeypatch.setattr(units, "USERS_DIR", tmp_path / "users")


def _write_raw(user_id: str, date: str, content: str) -> None:
    path = store._log_path(user_id, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.mark.parametrize(
    "raw_content",
    [
        "",  # empty file
        "not json at all",
        "{",  # truncated
        '{"log_id": "2026-01-01"',  # truncated mid-object
        "[]",  # valid JSON, wrong shape (array, not object)
        '{"log_id": "2026-01-01", "user_id": "alice"}',  # missing required fields
        '{"log_id": "2026-01-01", "user_id": "alice", "timestamp": "not-a-timestamp", "entries": [], "computed_totals": {}}',
        '{"log_id": "", "user_id": "alice", "timestamp": "2026-01-01T00:00:00Z", "entries": [], "computed_totals": {"energy_kcal": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0, "fiber_g": 0}}',
    ],
)
def test_corrupted_log_quarantines_instead_of_crashing(raw_content):
    _write_raw("alice", "2026-01-01", raw_content)
    result = store.load_day("alice", "2026-01-01")
    assert isinstance(result, QuarantinedLog)
    assert result.raw_content == raw_content
    assert result.error
    assert result.path.endswith("2026-01-01.json")


def test_quarantined_log_preserves_raw_content_verbatim():
    weird_content = '{"log_id": "2026-01-01", "user_id": "alice", "extra_junk": [1, 2, {"a": "b"}]'
    _write_raw("alice", "2026-01-01", weird_content)
    result = store.load_day("alice", "2026-01-01")
    assert result.raw_content == weird_content


def test_get_day_returns_quarantine_object_not_a_crash():
    _write_raw("alice", "2026-01-01", "{corrupt")
    result = engine.get_day("alice", "2026-01-01")
    assert isinstance(result, QuarantinedLog)


def test_log_entry_on_quarantined_day_raises_cleanly_not_crashes():
    _write_raw("alice", "2026-01-01", "{corrupt")
    with pytest.raises(ValueError, match="quarantined"):
        engine.log_ingredient(
            "alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        )


def test_delete_entry_on_quarantined_day_raises_cleanly_not_crashes():
    _write_raw("alice", "2026-01-01", "{corrupt")
    with pytest.raises(ValueError, match="quarantined"):
        engine.delete_entry("alice", "2026-01-01", 0)


def test_tag_day_on_quarantined_day_raises_cleanly_not_crashes():
    _write_raw("alice", "2026-01-01", "{corrupt")
    with pytest.raises(ValueError, match="quarantined"):
        engine.tag_day("alice", "2026-01-01", "diwali")


def test_get_range_skips_quarantine_gracefully_when_mixed_with_valid_days():
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    _write_raw("alice", "2026-01-02", "{corrupt")
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 3, 12, tzinfo=timezone.utc))

    results = engine.get_range("alice", "2026-01-01", "2026-01-03")
    assert len(results) == 3
    kinds = [r.__class__.__name__ for r in results]
    assert kinds == ["MealLog", "QuarantinedLog", "MealLog"]


def test_weekly_totals_does_not_crash_with_a_quarantined_day_in_the_window():
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    _write_raw("alice", "2026-01-03", "{corrupt")

    # Should not raise -- a corrupted day just counts as zero for that day.
    summary = weekly_totals("alice", "2026-01-07")
    assert len(summary.days) == 7
    corrupted_day = next(d for d in summary.days if d.date == "2026-01-03")
    assert corrupted_day.entry_count == 0
    assert corrupted_day.totals.energy_kcal == 0
