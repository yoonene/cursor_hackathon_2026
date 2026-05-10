"""Traditional chart digest (English labels) for API and LLM context."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TraditionalChartDigest(BaseModel):
    """Structured traditional-chart notes paired with Hanja pillar pairs."""

    pillars_hanja: dict[str, str] = Field(
        ...,
        description="year, month, day, optional hour → Hanja pillar string (e.g. year=Wu Yin)",
    )

    day_stem_label_en: str = Field(
        ...,
        description="Day stem element label in English (e.g. Sin Metal, Byeong Fire).",
    )
    day_pillar_reading_en: str = Field(
        ...,
        description="Romanized day pillar pair e.g. “Xin Mao”, “Bing Wu”.",
    )
    day_branch_animal_label: str = Field(
        ...,
        description="Earthly-branch animal in English e.g. Rabbit, Horse.",
    )
    pillar_lines_en: list[str] = Field(
        ...,
        description="One-line English summary per Year / Month / Day / (Hour) pillar.",
    )
    day_master_strength_en: str = Field(
        default="",
        description="Plain-English note on day-master strength when metrics supply it.",
    )
    signals_gloss_en: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Rule-engine signals with one-line English gloss per hit.",
    )
