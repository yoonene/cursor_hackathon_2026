"""English-first chart identity payloads for frontend visualization (day pillar · day master)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

"""Aligned with app.schemas.saju.ElementName (avoid importing saju ↔ circular deps)."""

ElementKey = Literal["wood", "fire", "earth", "metal", "water"]

PolarityToken = Literal["yin", "yang"]


class DayPillarIdentity(BaseModel):
    ganji_hanja: str
    ganji_hangul: str
    stem_hanja: str
    branch_hanja: str
    english_name: str
    animal: str
    animal_label: str
    color: str


class DayMasterIdentity(BaseModel):
    stem_hanja: str
    stem_hangul: str
    element: ElementKey
    element_label: str
    polarity: PolarityToken
    english_name: str
    display_label: str


class ChartVisualTokens(BaseModel):
    theme: ElementKey
    accent: str
    animal: str


class ChartIdentity(BaseModel):
    day_pillar: DayPillarIdentity
    day_master: DayMasterIdentity
    visual_tokens: ChartVisualTokens


class ChartIdentitySummary(BaseModel):
    """Compact strip for Counseling Board profile header."""

    day_pillar_hanja: str
    day_pillar_label: str
    day_master_label: str
    display_label: str
    theme: ElementKey
    accent: str
    animal: str
