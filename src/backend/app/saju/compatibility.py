from __future__ import annotations

from app.schemas.fortune import CompatibilityPersonSnapshot, CompatibilityResult
from app.schemas.saju import SajuData
from app.saju.common import controls, supports


def _slug(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def analyze_compatibility(user_saju: SajuData, other_saju: SajuData) -> CompatibilityResult:
    """Analyze relationship flow between two saju profiles deterministically."""

    score = 58
    user_primary = user_saju.dominant_elements[0]
    other_primary = other_saju.dominant_elements[0]

    if user_saju.day_master == other_saju.day_master:
        score += 8
    if supports(user_primary, other_primary) or supports(other_primary, user_primary):
        score += 14
    if controls(user_primary, other_primary) or controls(other_primary, user_primary):
        score -= 9

    complement_bonus = len(set(user_saju.lacking_elements) & set(other_saju.dominant_elements)) * 7
    complement_bonus += len(set(other_saju.lacking_elements) & set(user_saju.dominant_elements)) * 7
    score += complement_bonus

    overlap_penalty = len(set(user_saju.lacking_elements) & set(other_saju.lacking_elements)) * 4
    score -= overlap_penalty

    score = max(35, min(95, score))

    if score >= 80:
        label = "Strong attraction with real support"
        connection_type = "supportive"
        connection_label = "Supportive Flow"
    elif score >= 66:
        label = "Warm connection with room to deepen"
        connection_type = "balanced"
        connection_label = "Balanced Flow"
    else:
        label = "Meaningful pull with some friction"
        connection_type = "tense"
        connection_label = "Tense Flow"

    strengths = []
    if supports(user_primary, other_primary) or supports(other_primary, user_primary):
        strengths.append("One person naturally feeds the other's confidence and movement.")
    if complement_bonus:
        strengths.append("What feels thin in one chart is partly steadied by the other.")
    if user_saju.day_master == other_saju.day_master:
        strengths.append("There is a familiar rhythm in how both of you process life.")
    if not strengths:
        strengths.append("The connection grows stronger when both people stay honest about pace.")

    friction_points = []
    if controls(user_primary, other_primary) or controls(other_primary, user_primary):
        friction_points.append("One person's natural tempo can press too hard on the other.")
    if overlap_penalty:
        friction_points.append("You may trigger the same soft spots instead of balancing them.")
    if not friction_points:
        friction_points.append("This bond needs steady timing more than dramatic intensity.")

    one_line_advice = {
        "supportive": "Let the connection deepen steadily rather than rushing to define everything at once.",
        "balanced": "There is warmth here, but the bond becomes clearer when each person speaks a little more plainly.",
        "tense": "The pull is real, but pacing and emotional timing will matter more than chemistry alone.",
    }[connection_type]

    other_name = other_saju.display_name or "this person"
    semantic_key = f"compatibility:user:{_slug(other_name)}"
    summary = f"{score} points with a {connection_type} emotional current."

    return CompatibilityResult(
        semantic_key=semantic_key,
        score=score,
        label=label,
        people=[
            CompatibilityPersonSnapshot(
                name=user_saju.display_name or "You",
                dominant_element=user_primary,
            ),
            CompatibilityPersonSnapshot(
                name=other_name,
                dominant_element=other_primary,
            ),
        ],
        connection_type=connection_type,
        connection_label=connection_label,
        strengths=strengths[:3],
        friction_points=friction_points[:3],
        one_line_advice=one_line_advice,
        summary=summary,
    )
