from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.intake import GenderType, StartReadingRequest


class PartnerCompatibilityPayload(BaseModel):
    """궁합용 상대 1명 — `collecting_compatibility_info` 단계에서 `POST /chat` 본문에 함께 보냅니다."""

    model_config = ConfigDict(str_strip_whitespace=True)

    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    birth_date: date
    birth_time: time | None = None
    gender: GenderType | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def _empty_display_to_none(cls, value: object) -> str | None:
        if value is None:
            return None
        s = str(value).strip()
        return s or None


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(min_length=1, max_length=120)
    message: str = Field(default="", max_length=4000)
    partner: PartnerCompatibilityPayload | None = None

    @field_validator("message", mode="before")
    @classmethod
    def _coerce_message(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @model_validator(mode="after")
    def require_message_or_partner(self) -> ChatRequest:
        if not self.message and self.partner is None:
            raise ValueError("메시지가 비었으면 partner 객체가 필요합니다.")
        return self


class ResetSessionRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)


class LoadDemoRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=120)
    scenario: Literal[
        "fresh_start",
        "after_initial_report",
        "romance_demo",
        "career_demo",
    ]


__all__ = [
    "ChatRequest",
    "LoadDemoRequest",
    "PartnerCompatibilityPayload",
    "ResetSessionRequest",
    "StartReadingRequest",
]
