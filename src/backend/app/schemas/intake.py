from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

GenderType = Literal["female", "male", "other", "prefer_not_to_say"]


class StartReadingRequest(BaseModel):
    """Fixed intake form payload for the first phase of the experience."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(min_length=1, max_length=120)
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    birth_date: date
    birth_time: time | None = None
    gender: GenderType | None = None

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
