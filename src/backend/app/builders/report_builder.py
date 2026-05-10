from __future__ import annotations

from app.schemas.profiles import PersonProfile
from app.schemas.report import ReportSection, SajuReport
from app.schemas.saju import ElementName, SajuData
from app.saju.common import ELEMENT_SHADOWS, format_element_list

VERDICT_MAP: dict[ElementName, str] = {
    "wood": "You become strongest when growth is guided rather than rushed.",
    "fire": "You become strongest when you pause without losing your fire.",
    "earth": "You become strongest when care includes you as well.",
    "metal": "You become strongest when clarity stays warm instead of severe.",
    "water": "You become strongest when feeling is given movement instead of silence.",
}


def _display_name(profile: PersonProfile) -> str:
    return profile.display_name or "Your"


def build_saju_report(profile: PersonProfile, saju_data: SajuData) -> SajuReport:
    """Build the static full report shown after the fixed intake phase."""

    name = profile.display_name or "Your"
    title = f"{name}'s Full Saju Report" if profile.display_name else "Your Full Saju Report"
    dominant = saju_data.dominant_elements[0]
    lacking_text = format_element_list(saju_data.lacking_elements)
    overall_summary = (
        f"{saju_data.overall_summary_seed} The chart feels most alive when {dominant} can move naturally."
    )

    personality = ReportSection(
        title="Personality",
        summary=saju_data.personality_summary,
    )
    relationship_style = ReportSection(
        title="Relationship Style",
        summary=saju_data.relationship_style,
    )
    career_style = ReportSection(
        title="Career Style",
        summary=saju_data.career_style,
    )
    emotional_pattern = ReportSection(
        title="Emotional Pattern",
        summary=saju_data.emotional_pattern,
    )

    one_line_verdict = VERDICT_MAP[dominant]
    if saju_data.lacking_elements:
        one_line_verdict = (
            f"{one_line_verdict[:-1]}, especially when {lacking_text} is given more room."
        )

    return SajuReport(
        id=f"saju_report_{profile.id}",
        title=title,
        overall_summary=overall_summary,
        elements=saju_data.elements,
        dominant_elements=saju_data.dominant_elements,
        lacking_elements=saju_data.lacking_elements,
        keywords=saju_data.core_keywords,
        personality=personality,
        relationship_style=relationship_style,
        career_style=career_style,
        emotional_pattern=emotional_pattern,
        strengths=saju_data.strengths,
        cautions=saju_data.cautions,
        one_line_verdict=one_line_verdict,
    )


def build_initial_interpretation(profile: PersonProfile, saju_data: SajuData, report: SajuReport) -> str:
    """Create the first natural English reading for the chat area."""

    dominant = saju_data.dominant_elements[0]
    lacking = saju_data.lacking_elements[0]
    first_sentence = {
        "wood": "Your chart leans toward movement and growth. Once your heart sees a direction, you rarely stay still for long.",
        "fire": "Your fire energy is quite alive. When your heart moves, you tend to act before you overthink.",
        "earth": "There is steady earth in the way your chart holds itself. You often carry more quietly than people first notice.",
        "metal": "There is clear metal energy running through your chart. You notice tone, intention, and inconsistency very quickly.",
        "water": "Your water energy runs deep. You tend to feel the atmosphere of a moment before anyone has named it.",
    }[dominant]
    second_sentence = {
        "wood": "At the same time, when too many paths open at once, your energy can scatter and start to feel restless.",
        "fire": "At the same time, when intensity rises too quickly, your feelings can outrun your clarity for a while.",
        "earth": "At the same time, when you keep holding everything together, heaviness can arrive later than expected.",
        "metal": "At the same time, when the situation feels messy, the mind can become stricter than the moment truly needs.",
        "water": "At the same time, with softer areas in the chart, feelings can linger inside longer than people realize.",
    }[lacking]

    third_sentence = report.relationship_style.summary
    fourth_sentence = (
        f"In work and direction, {report.career_style.summary.lower()} "
        f"Your chart's deeper lesson is that {ELEMENT_SHADOWS[lacking]}."
    )
    closing = "When you are ready, tell me what part of life you want to look at more deeply."

    return " ".join(
        sentence.strip()
        for sentence in (first_sentence, second_sentence, third_sentence, fourth_sentence, closing)
    )
