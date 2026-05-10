from __future__ import annotations

from pydantic import BaseModel

from app.schemas.chart_identity import ChartIdentity
from app.schemas.saju import ElementBalance, ElementName
from app.schemas.tradition import TraditionalChartDigest


class ReportSection(BaseModel):
    title: str
    summary: str


class SajuReport(BaseModel):
    id: str
    title: str
    overall_summary: str
    elements: ElementBalance
    dominant_elements: list[ElementName]
    lacking_elements: list[ElementName]
    keywords: list[str]
    personality: ReportSection
    relationship_style: ReportSection
    career_style: ReportSection
    emotional_pattern: ReportSection
    strengths: list[str]
    cautions: list[str]
    one_line_verdict: str
    chart_identity: ChartIdentity | None = None
    """English-first day pillar / day master payload for UI (optional for legacy fixtures)."""
    chart_digest: TraditionalChartDigest | None = None
    """표시 계층용 전통 간지 요약 (`SajuData` 와 동기). 미구현·구버전 응답은 None."""
