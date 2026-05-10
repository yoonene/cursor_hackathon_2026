from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.intake import StartReadingRequest


class ChatRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must not be empty")
        return normalized


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


__all__ = ["ChatRequest", "LoadDemoRequest", "ResetSessionRequest", "StartReadingRequest"]
