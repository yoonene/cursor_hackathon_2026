from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.intake import GenderType

ElementName = Literal["wood", "fire", "earth", "metal", "water"]


class ElementBalance(BaseModel):
    """Five-element balance used throughout the product."""

    wood: int = Field(ge=0, le=9)
    fire: int = Field(ge=0, le=9)
    earth: int = Field(ge=0, le=9)
    metal: int = Field(ge=0, le=9)
    water: int = Field(ge=0, le=9)

    def as_dict(self) -> dict[str, int]:
        return self.model_dump()


class PillarData(BaseModel):
    """Lightweight pillar data for the deterministic MVP engine."""

    stem_name: str
    stem_element: ElementName
    branch_name: str
    branch_element: ElementName


class SajuData(BaseModel):
    """Deterministic structured saju facts derived from intake data."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    display_name: str | None = None
    birth_date: date
    birth_time: time | None = None
    birth_time_known: bool = True
    gender: GenderType | None = None
    year_pillar: PillarData
    month_pillar: PillarData
    day_pillar: PillarData
    hour_pillar: PillarData
    day_master: ElementName
    elements: ElementBalance
    dominant_elements: list[ElementName]
    lacking_elements: list[ElementName]
    core_keywords: list[str]
    overall_summary_seed: str
    personality_summary: str
    relationship_style: str
    career_style: str
    emotional_pattern: str
    strengths: list[str]
    cautions: list[str]
    calculation_notes: list[str] = Field(default_factory=list)
