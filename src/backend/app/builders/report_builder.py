from __future__ import annotations

from app.schemas.counselor_llm import InitialReadingLLMOutput
from app.schemas.profiles import PersonProfile
from app.schemas.report import ReportSection, SajuReport
from app.schemas.saju import SajuData


def build_saju_report(
    profile: PersonProfile,
    saju_data: SajuData,
    llm_out: InitialReadingLLMOutput,
) -> SajuReport:
    """오행 분포 등 팩트는 `saju_data`, 서술은 LLM 출력으로 채운다."""

    name = profile.display_name or "Your"
    title = f"{name}'s Full Saju Report" if profile.display_name else "Your Full Saju Report"
    keywords = llm_out.keywords[:3]

    return SajuReport(
        id=f"saju_report_{profile.id}",
        title=title,
        overall_summary=llm_out.overall_summary,
        elements=saju_data.elements,
        dominant_elements=saju_data.dominant_elements,
        lacking_elements=saju_data.lacking_elements,
        keywords=keywords,
        personality=ReportSection(title="Personality", summary=llm_out.personality),
        relationship_style=ReportSection(title="Relationship Style", summary=llm_out.relationship_style),
        career_style=ReportSection(title="Career Style", summary=llm_out.career_style),
        emotional_pattern=ReportSection(title="Emotional Pattern", summary=llm_out.emotional_pattern),
        strengths=llm_out.strengths[:3],
        cautions=llm_out.cautions[:3],
        one_line_verdict=llm_out.one_line_verdict,
        chart_identity=saju_data.chart_identity,
        chart_digest=saju_data.chart_digest,
    )
