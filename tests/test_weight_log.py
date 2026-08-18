import pytest

from src.core.schemas import WeightEntry
from src.core.weight_log import get_weight_log, save_weight


@pytest.fixture(autouse=True)
def isolated_users_dir(tmp_path, monkeypatch):
    import src.core.weight_log as weight_log

    monkeypatch.setattr(weight_log, "USERS_DIR", tmp_path / "users")


def test_get_weight_log_empty_for_new_user():
    assert get_weight_log("alice") == {}


def test_save_and_get_weight():
    save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    assert get_weight_log("alice") == {"2026-01-01": 65.5}


def test_save_weight_overwrites_same_date():
    save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=66.0))
    assert get_weight_log("alice") == {"2026-01-01": 66.0}


def test_save_weight_accumulates_across_dates():
    save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    save_weight(WeightEntry(user_id="alice", date="2026-01-02", weight_kg=65.3))
    assert get_weight_log("alice") == {"2026-01-01": 65.5, "2026-01-02": 65.3}


def test_weight_logs_are_isolated_per_user():
    save_weight(WeightEntry(user_id="alice", date="2026-01-01", weight_kg=65.5))
    save_weight(WeightEntry(user_id="bob", date="2026-01-01", weight_kg=80.0))
    assert get_weight_log("alice") == {"2026-01-01": 65.5}
    assert get_weight_log("bob") == {"2026-01-01": 80.0}


def test_weight_entry_rejects_non_positive_weight():
    with pytest.raises(ValueError):
        WeightEntry(user_id="alice", date="2026-01-01", weight_kg=0)


def test_weight_entry_rejects_unreasonably_high_weight():
    with pytest.raises(ValueError):
        WeightEntry(user_id="alice", date="2026-01-01", weight_kg=500)
