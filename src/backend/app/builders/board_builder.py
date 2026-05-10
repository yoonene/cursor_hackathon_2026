from __future__ import annotations

from app.schemas.profiles import PersonProfile
from app.schemas.report import SajuReport
from app.schemas.view_models import CounselingBoard, ProfileSummary


def build_initial_counseling_board(profile: PersonProfile, report: SajuReport) -> CounselingBoard:
    """Build the initial board state shown alongside the full report."""

    title = f"{profile.display_name}'s Base Flow" if profile.display_name else "Your Base Flow"
    profile_summary = ProfileSummary(
        id=f"profile_{profile.id}",
        title=title,
        one_line_summary=report.overall_summary,
        elements=report.elements,
        dominant_elements=report.dominant_elements,
        lacking_elements=report.lacking_elements,
        keywords=report.keywords,
    )
    return CounselingBoard(
        profile_summary=profile_summary,
        active_reading=None,
        insight_summaries=[],
        history=[],
    )
