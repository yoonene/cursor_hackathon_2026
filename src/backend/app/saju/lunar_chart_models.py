"""원국 계산 결과용 경량 도메인 모델 (side_projects와 동일 책임)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PillarCN(BaseModel):
    """천간·지지 문자열."""

    gan: str
    zhi: str

    @property
    def value(self) -> str:
        return f"{self.gan}{self.zhi}"


class Chart(BaseModel):
    year_pillar: PillarCN
    month_pillar: PillarCN
    day_pillar: PillarCN
    hour_pillar: PillarCN | None = None
    """출생 시각 미입력 시 None (연월일만 분석)."""
    day_master: str


class ElementDistribution(BaseModel):
    wood: int = 0
    fire: int = 0
    earth: int = 0
    metal: int = 0
    water: int = 0

    def as_dict(self) -> dict[str, int]:
        return self.model_dump()


class CalculationResult(BaseModel):
    chart: Chart
    elements: ElementDistribution
    metrics: dict[str, Any] = Field(default_factory=dict)


class SignalHit(BaseModel):
    code: str
    section: str
    score: int
    priority: int
    source_rule_ids: list[str]


class InterpretationResult(BaseModel):
    hits: dict[str, list[SignalHit]] = Field(default_factory=dict)
    #: 시그널 코드 → 적중시킨 규칙 id 목록
    explanations: dict[str, list[str]] = Field(default_factory=dict)

    def signal_codes(self) -> dict[str, list[str]]:
        return {
            section: [hit.code for hit in section_hits]
            for section, section_hits in self.hits.items()
        }
