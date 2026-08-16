"""Insight: a single generated recommendation/warning/celebration.

Not persisted -- generate_insights() computes these fresh from logs on
every call, the same way src.core.planning.PlanRecommendation is computed
fresh rather than stored.
"""
from typing import Literal

from pydantic import BaseModel, Field

InsightKind = Literal[
    "swap", "warning", "celebration", "nudge", "hydration", "fasting_reminder", "festival_flex"
]
InsightSeverity = Literal["info", "suggest", "warn", "urgent"]


class Insight(BaseModel):
    insight_id: str = Field(min_length=1)
    kind: InsightKind
    severity: InsightSeverity
    title: str = Field(min_length=1)
    # Pre-translated stubs for now (best-effort, not professionally
    # reviewed) -- real i18n infrastructure is src/i18n/ (Part F), which
    # is a separate mechanism for UI strings; these are insight-specific
    # generated text, not static locale keys.
    body_en: str = Field(min_length=1)
    body_hi: str = Field(min_length=1)
    body_kn: str = Field(min_length=1)
    evidence: dict = Field(default_factory=dict)
    suggested_actions: list[str] = Field(default_factory=list)
