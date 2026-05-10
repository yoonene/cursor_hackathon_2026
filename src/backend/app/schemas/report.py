from __future__ import annotations

from pydantic import BaseModel

from app.schemas.saju import ElementBalance, ElementName


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
