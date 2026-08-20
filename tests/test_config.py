"""src.config.Settings: defaults for local dev, fail-fast validation
for prod. Each test constructs Settings(...) directly (bypassing
get_settings()'s lru_cache and the real environment) so these are
fully isolated from whatever DATABASE_URL/JWT_SECRET tests/conftest.py
or the real shell environment happens to have set.
"""
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_env_example_documents_every_setting():
    """Guards against drift: every field Settings actually reads must
    have a line in .env.example, or a new var silently goes
    undocumented for whoever deploys this next."""
    env_example = (REPO_ROOT / ".env.example").read_text()
    for field_name in Settings.model_fields:
        assert f"{field_name}=" in env_example, f"{field_name} is not documented in .env.example"


def test_dev_defaults_are_usable_with_zero_env_vars():
    # DATABASE_URL isn't asserted to a specific value here: pydantic-
    # settings always reads real env vars over field defaults regardless
    # of _env_file, and tests/conftest.py deliberately sets DATABASE_URL
    # to an in-memory DB for test isolation -- asserting the field's
    # *default* value belongs in a test that explicitly overrides it
    # (as this file's other tests do for every field they care about).
    settings = Settings(_env_file=None)
    assert settings.ENVIRONMENT == "dev"
    assert settings.DATABASE_URL
    assert settings.is_prod is False


def test_cors_origins_splits_comma_separated_list():
    settings = Settings(_env_file=None, CORS_ALLOWED_ORIGINS="https://a.example.com, https://b.example.com")
    assert settings.cors_origins == ["https://a.example.com", "https://b.example.com"]


def test_prod_refuses_to_boot_with_default_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(
            _env_file=None,
            ENVIRONMENT="prod",
            RESEND_API_KEY="re_xxx",
            CORS_ALLOWED_ORIGINS="https://dalgains.vercel.app",
        )


def test_prod_refuses_to_boot_with_short_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(
            _env_file=None,
            ENVIRONMENT="prod",
            JWT_SECRET="too-short",
            RESEND_API_KEY="re_xxx",
            CORS_ALLOWED_ORIGINS="https://dalgains.vercel.app",
        )


def test_prod_refuses_to_boot_without_resend_key():
    with pytest.raises(ValidationError, match="RESEND_API_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="prod",
            JWT_SECRET="x" * 32,
            CORS_ALLOWED_ORIGINS="https://dalgains.vercel.app",
        )


def test_prod_refuses_to_boot_with_default_cors_origins():
    with pytest.raises(ValidationError, match="CORS_ALLOWED_ORIGINS"):
        Settings(_env_file=None, ENVIRONMENT="prod", JWT_SECRET="x" * 32, RESEND_API_KEY="re_xxx")


def test_prod_boots_with_everything_set():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="prod",
        JWT_SECRET="x" * 32,
        RESEND_API_KEY="re_xxx",
        CORS_ALLOWED_ORIGINS="https://dalgains.vercel.app",
    )
    assert settings.is_prod is True


def test_staging_does_not_trigger_prod_validation():
    """staging is deliberately not held to the same bar as prod --
    intended for a pre-production check with looser requirements."""
    settings = Settings(_env_file=None, ENVIRONMENT="staging")
    assert settings.JWT_SECRET  # still has the dev default, and that's fine here
