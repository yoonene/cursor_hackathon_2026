from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.intake import GenderType


class PersonProfile(BaseModel):
    """Reusable person profile used for the user and related people."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=120)
    relationship_to_user: str | None = Field(default=None, max_length=80)
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    birth_date: date | None = None
    birth_time: time | None = None
    gender: GenderType | None = None

    @field_validator("display_name", "relationship_to_user")
    @classmethod
    def empty_strings_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def preferred_name(self) -> str:
        return self.display_name or "You"
