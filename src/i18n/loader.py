"""Locale loading + load-time key-completeness validation.

Kannada ("kn") is the primary locale (Karnataka-first, per the Phase 3
brief). Hindi ("hi") is secondary. English ("en") is the fallback for
technical strings -- and also the reference key set every other locale
is validated against, since it's expected to always be complete first.
"""
import json
from pathlib import Path
from typing import Optional

LOCALES_DIR = Path(__file__).resolve().parent / "locales"
SUPPORTED_LOCALES = ["kn", "hi", "en"]
PRIMARY_LOCALE = "kn"
FALLBACK_LOCALE = "en"

MISSING_KEYS_REPORT_PATH = Path(__file__).resolve().parent / "missing_keys_report.json"


def _locale_path(locale: str) -> Path:
    return LOCALES_DIR / f"{locale}.json"


def load_locale(locale: str) -> dict[str, str]:
    path = _locale_path(locale)
    if not path.exists():
        raise FileNotFoundError(f"No locale file for {locale!r} at {path}")
    return json.loads(path.read_text())


def validate_locales(report_path: Optional[Path] = None) -> dict[str, list[str]]:
    """Checks every key in en.json exists in every other supported locale.

    Never silently falls back for a missing key -- always writes the
    result (empty dict if everything is complete) to report_path
    (default: MISSING_KEYS_REPORT_PATH), keyed by locale, valued by its
    sorted list of missing keys.
    """
    report_path = report_path or MISSING_KEYS_REPORT_PATH
    reference_keys = set(load_locale(FALLBACK_LOCALE))

    missing: dict[str, list[str]] = {}
    for locale in SUPPORTED_LOCALES:
        if locale == FALLBACK_LOCALE:
            continue
        locale_keys = set(load_locale(locale))
        missing_keys = sorted(reference_keys - locale_keys)
        if missing_keys:
            missing[locale] = missing_keys

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(missing, indent=2))
    return missing


def load_all_locales() -> dict[str, dict[str, str]]:
    """The "on app start" entry point: validates completeness, then loads
    every supported locale. Raises ValueError if any locale is missing
    keys en.json has -- callers that want a non-fatal check should call
    validate_locales() directly instead.
    """
    missing = validate_locales()
    if missing:
        raise ValueError(
            f"Locale files are incomplete (see {MISSING_KEYS_REPORT_PATH}): {missing}"
        )
    return {locale: load_locale(locale) for locale in SUPPORTED_LOCALES}


def translate(key: str, locale: str = PRIMARY_LOCALE) -> str:
    """A single string lookup, falling back to English if the locale is
    missing the key (validate_locales() is what catches that condition
    at startup -- this is just a safe runtime accessor, not a place to
    silently paper over gaps).
    """
    strings = load_locale(locale)
    if key in strings:
        return strings[key]
    return load_locale(FALLBACK_LOCALE)[key]
