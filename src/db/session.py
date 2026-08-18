"""Engine + session factory. One process-wide engine, one SessionLocal.

DATABASE_URL is read directly from the environment here (not through
src.config) because this module predates Phase 5C's config module in
the commit order -- Part C later refactors this one read to go through
pydantic-settings alongside every other env var, without changing this
module's public API (engine, SessionLocal, get_session).

Importing src.db.session must not have side effects beyond creating the
engine (no table creation here -- that's alembic's job via `alembic
upgrade head`, run once at container start, not on every import).
"""
import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/dalgains.db")

# check_same_thread=False: FastAPI can serve a single request's DB calls
# from more than one thread (it runs sync path operations in a
# threadpool); SQLAlchemy's own Session is not shared across requests
# here (a fresh one is created per get_session() call), so this is safe.
_engine_kwargs: dict = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}
if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
    # A plain sqlite:// in-memory DB is private to the connection that
    # created it -- without StaticPool, every session.py get_session()
    # call would open a fresh connection and see an empty database.
    # StaticPool keeps one connection alive for the engine's lifetime, so
    # the whole test session shares one in-memory DB (see tests/conftest.py).
    _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """One session per unit of work, committed on success, rolled back
    and re-raised on error, always closed."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
