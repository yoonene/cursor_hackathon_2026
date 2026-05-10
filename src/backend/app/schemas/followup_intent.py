"""Structured output for follow-up utterance routing (intent classification)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.fortune import ActionType, FortuneDomain, FortunePeriod, TimingDomain

FollowUpRouteName = Literal["general", "domain_fortune", "favorable_timing", "compatibility"]


class ClassifiedFollowUpIntent(BaseModel):
    """Normalized router output consumed by `/chat`."""

    model_config = ConfigDict(str_strip_whitespace=True)

    route: FollowUpRouteName
    fortune_domain: FortuneDomain | None = None
    fortune_period: FortunePeriod | None = None
    timing_domain: TimingDomain | None = None
    action_type: ActionType | None = None
    partner_birth_date: date | None = None
    partner_name: str | None = Field(default=None, max_length=80)

    @field_validator("partner_birth_date", mode="before")
    @classmethod
    def coerce_partner_birth_date(cls, value: object) -> date | None:
        if value is None or value == "":
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value.strip())
        raise TypeError(f"partner_birth_date expects date or ISO string, got {type(value)}")
