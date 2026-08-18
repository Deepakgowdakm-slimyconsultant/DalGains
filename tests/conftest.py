"""Session-wide test setup: every backend test runs against an
in-memory SQLite database, never the real data/dalgains.db.

DATABASE_URL must be set before src.db.session is first imported by
anything (that's what binds the module-level `engine`), so this file
sets it as the very first statement, ahead of any src import -- pytest
always loads conftest.py before collecting the test files in its
directory, so this ordering is guaranteed regardless of which test
module pytest happens to import first.
"""
import os

os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402

from src.db.models import Base  # noqa: E402
from src.db.session import engine  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_db():
    """Fresh schema before every test -- the equivalent of the old
    per-test tmp_path isolation, now for the DB instead of JSON files."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
