from __future__ import annotations

from datetime import date, time
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chart_identity import ChartIdentity
from app.schemas.intake import GenderType
from app.schemas.tradition import TraditionalChartDigest

ElementName = Literal["wood", "fire", "earth", "metal", "water"]


class ElementBalance(BaseModel):
    """천간+지장간 기준 오행 발생 횟수 (side_projects `ElementDistribution` 와 동일 의미의 정수합)."""

    wood: int = Field(ge=0, le=32)
    fire: int = Field(ge=0, le=32)
    earth: int = Field(ge=0, le=32)
    metal: int = Field(ge=0, le=32)
    water: int = Field(ge=0, le=32)

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
    hour_pillar: PillarData | None = None
    """출생 시각 미입력 시 None."""
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
    calculation_metrics: dict[str, Any] = Field(default_factory=dict)
    """lunar_python + 일간 판정 등 엔진 팩트 (LLM 입력)."""
    interpretation_signals: dict[str, list[str]] = Field(default_factory=dict)
    """규칙 엔진이 섹션별로 발화한 시그널 코드 (LLM 입력)."""
    chart_digest: TraditionalChartDigest | None = None
    """Traditional chart digest with English glosses (Hanja pillars preserved)."""
    chart_identity: ChartIdentity | None = None
    """English-first visualization identity (day pillar / day master)."""
