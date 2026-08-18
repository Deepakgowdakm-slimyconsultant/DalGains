"""Central settings: the single source of truth for every environment
variable this app reads. Every other module that used to read
os.environ directly (src/db/session.py's DATABASE_URL, src/auth/
{jwt,magic_link}.py's JWT_SECRET, src/api/routes/auth.py's APP_URL/
ADMIN_EMAIL/ENVIRONMENT) is unaffected by this file existing -- they
keep their own os.environ.get(...) reads with the same variable names,
so nothing behaves differently. What this module adds is the one
thing a scattered set of os.environ.get() calls can't give you: a
single fail-fast check, at import time, that a production deployment
has everything it actually needs before it starts serving requests.

get_settings() is called once at import time below (module-level
singleton) -- if validation fails in prod, the app never boots far
enough to accept a request with a missing secret.
"""
import sys
from functools import lru_cache
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Loads a local .env file if one exists (harmless no-op otherwise --
# production sets real env vars directly, e.g. HF Spaces' Settings ->
# Variables and secrets, never via a checked-in or uploaded .env file).
load_dotenv()

Environment = Literal["dev", "staging", "prod"]

_DEV_INSECURE_JWT_SECRET = "dev-insecure-secret-do-not-use-in-production"
_MIN_JWT_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/dalgains.db"
    JWT_SECRET: str = _DEV_INSECURE_JWT_SECRET
    RESEND_API_KEY: Optional[str] = None
    APP_URL: str = "http://localhost:5173"
    ADMIN_EMAIL: Optional[str] = None
    ENVIRONMENT: Environment = "dev"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def is_prod(self) -> bool:
        return self.ENVIRONMENT == "prod"

    @model_validator(mode="after")
    def _refuse_to_boot_in_prod_without_real_secrets(self) -> "Settings":
        if self.ENVIRONMENT != "prod":
            return self

        missing_or_invalid: list[str] = []
        if len(self.JWT_SECRET) < _MIN_JWT_SECRET_LENGTH or self.JWT_SECRET == _DEV_INSECURE_JWT_SECRET:
            missing_or_invalid.append(f"JWT_SECRET (must be set, at least {_MIN_JWT_SECRET_LENGTH} characters)")
        if not self.RESEND_API_KEY:
            missing_or_invalid.append("RESEND_API_KEY (magic-link emails would otherwise silently never send)")
        if self.CORS_ALLOWED_ORIGINS == "http://localhost:3000,http://localhost:5173":
            missing_or_invalid.append("CORS_ALLOWED_ORIGINS (still the localhost dev default)")

        if missing_or_invalid:
            raise ValueError(
                "Refusing to start in production with missing/invalid settings:\n  - "
                + "\n  - ".join(missing_or_invalid)
            )
        return self


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:  # pydantic ValidationError wrapping our ValueError
        print(f"FATAL: invalid configuration -- {exc}", file=sys.stderr)
        raise


settings = get_settings()
