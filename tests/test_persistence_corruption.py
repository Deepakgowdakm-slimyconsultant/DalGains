"""Corrupted meal-log rows must quarantine, never crash the app.

Broader/more exhaustive than the couple of quarantine checks already in
tests/test_logging.py -- this file is the dedicated corruption suite the
Phase 3 brief asks for. Since Phase 5's SQLite migration, "corruption"
can no longer mean hand-edited invalid JSON text on disk (there's no
file to truncate) -- instead these tests insert a MealLogRow directly
via the ORM, bypassing pydantic validation entirely, to simulate
whatever real-world bug or manual DB edit could leave a row that fails
MealLog's own validation on read.
"""
from datetime import datetime, timezone

import pytest

from src.core.schemas import QuarantinedLog
from src.db.models import MealLogRow
from src.db.session import get_session
from src.logging import engine
from src.logging.aggregation import weekly_totals
from src.logging.store import load_day


def _write_invalid_row(user_id: str, date: str, *, entries=None, computed_totals=None) -> None:
    with get_session() as session:
        session.add(
            MealLogRow(
                user_id=user_id,
                log_id=date,
                timestamp=datetime.now(timezone.utc),
                entries=entries if entries is not None else [],
                computed_totals=computed_totals if computed_totals is not None else {},
                notes=None,
                tags=[],
            )
        )


VALID_TOTALS = {"energy_kcal": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0, "fiber_g": 0}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"entries": [], "computed_totals": VALID_TOTALS},  # MealLog requires >=1 entry
        {"entries": [{"recipe_id": "x", "qty": 1, "unit": "serving"}], "computed_totals": {}},  # missing totals fields
        {"entries": [{"qty": 1, "unit": "g"}], "computed_totals": VALID_TOTALS},  # entry with neither recipe_id nor ingredient_id
        {
            "entries": [{"recipe_id": "x", "ingredient_id": "y", "qty": 1, "unit": "g"}],
            "computed_totals": VALID_TOTALS,
        },  # entry with both recipe_id and ingredient_id
        {"entries": [{"recipe_id": "x", "qty": -5, "unit": "serving"}], "computed_totals": VALID_TOTALS},  # negative qty
        {"entries": "not-a-list", "computed_totals": VALID_TOTALS},  # wrong shape entirely
        {
            "entries": [{"recipe_id": "x", "qty": 1, "unit": "serving"}],
            "computed_totals": {**VALID_TOTALS, "protein_g": -10},
        },  # negative computed total
        {"entries": [{"recipe_id": "", "qty": 1, "unit": "serving"}], "computed_totals": VALID_TOTALS},  # empty recipe_id
    ],
)
def test_corrupted_row_quarantines_instead_of_crashing(kwargs):
    _write_invalid_row("alice", "2026-01-01", **kwargs)
    result = load_day("alice", "2026-01-01")
    assert isinstance(result, QuarantinedLog)
    assert result.error
    assert result.path == "sqlite:meal_logs/alice/2026-01-01"


def test_quarantined_log_preserves_raw_content():
    _write_invalid_row("alice", "2026-01-01", entries=[], computed_totals=VALID_TOTALS)
    result = load_day("alice", "2026-01-01")
    assert isinstance(result, QuarantinedLog)
    assert '"user_id": "alice"' in result.raw_content


def test_get_day_returns_quarantine_object_not_a_crash():
    _write_invalid_row("alice", "2026-01-01", entries=[], computed_totals=VALID_TOTALS)
    result = engine.get_day("alice", "2026-01-01")
    assert isinstance(result, QuarantinedLog)


def test_log_entry_on_quarantined_day_raises_cleanly_not_crashes():
    _write_invalid_row("alice", "2026-01-01", entries=[], computed_totals=VALID_TOTALS)
    with pytest.raises(ValueError, match="quarantined"):
        engine.log_ingredient(
            "alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        )


def test_delete_entry_on_quarantined_day_raises_cleanly_not_crashes():
    _write_invalid_row("alice", "2026-01-01", entries=[], computed_totals=VALID_TOTALS)
    with pytest.raises(ValueError, match="quarantined"):
        engine.delete_entry("alice", "2026-01-01", 0)


def test_tag_day_on_quarantined_day_raises_cleanly_not_crashes():
    _write_invalid_row("alice", "2026-01-01", entries=[], computed_totals=VALID_TOTALS)
    with pytest.raises(ValueError, match="quarantined"):
        engine.tag_day("alice", "2026-01-01", "diwali")


def test_get_range_skips_quarantine_gracefully_when_mixed_with_valid_days():
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    _write_invalid_row("alice", "2026-01-02", entries=[], computed_totals=VALID_TOTALS)
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 3, 12, tzinfo=timezone.utc))

    results = engine.get_range("alice", "2026-01-01", "2026-01-03")
    assert len(results) == 3
    kinds = [r.__class__.__name__ for r in results]
    assert kinds == ["MealLog", "QuarantinedLog", "MealLog"]


def test_weekly_totals_does_not_crash_with_a_quarantined_day_in_the_window():
    engine.log_ingredient("alice", "B021", 100, "g", when=datetime(2026, 1, 1, 12, tzinfo=timezone.utc))
    _write_invalid_row("alice", "2026-01-03", entries=[], computed_totals=VALID_TOTALS)

    # Should not raise -- a corrupted day just counts as zero for that day.
    summary = weekly_totals("alice", "2026-01-07")
    assert len(summary.days) == 7
    corrupted_day = next(d for d in summary.days if d.date == "2026-01-03")
    assert corrupted_day.entry_count == 0
    assert corrupted_day.totals.energy_kcal == 0
