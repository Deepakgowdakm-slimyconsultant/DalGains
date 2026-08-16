"""Connects fasting_protocol (src.core.planning) to meal logging.

Never blocks a log -- only flags entries logged outside the user's
eating window (log_entry attaches the result as
LogEntry.outside_eating_window). Matches the informative-not-paternalistic
warning policy already established in src.core.planning.generate_warnings.
"""
from datetime import datetime

from src.core.planning import compute_eating_window
from src.core.profiles import load_profile


def _hour_of_day(timestamp: datetime) -> float:
    return timestamp.hour + timestamp.minute / 60 + timestamp.second / 3600


def is_within_eating_window(user_id: str, timestamp: datetime) -> bool:
    """True if `timestamp` falls in the user's fasting-protocol eating window.

    True (never flagged) if the user has no profile on file -- there's
    nothing to check the timestamp against.
    """
    profile = load_profile(user_id)
    if profile is None:
        return True

    window = compute_eating_window(profile)
    hour = _hour_of_day(timestamp)

    if window.start_hour <= window.end_hour:
        return window.start_hour <= hour < window.end_hour
    # Wraps past midnight (e.g. ramadan's dusk-to-dawn approximation).
    return hour >= window.start_hour or hour < window.end_hour
