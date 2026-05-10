from __future__ import annotations

from datetime import date

from app.schemas.fortune import DomainFortuneResult, FortuneDomain, FortunePeriod, FortuneSegment
from app.schemas.saju import SajuData
from app.saju.common import SEASONAL_ELEMENT_BY_MONTH, element_scores, supports

DOMAIN_FOCUS: dict[FortuneDomain, tuple[str, str]] = {
    "love": ("fire", "water"),
    "career": ("wood", "metal"),
    "money": ("earth", "metal"),
    "relationships": ("water", "wood"),
    "health": ("earth", "water"),
    "overall": ("wood", "earth"),
}

PERIOD_LABELS: dict[FortunePeriod, tuple[str, str, str]] = {
    "today": ("Morning", "Afternoon", "Evening"),
    "this_week": ("Mon-Tue", "Wed-Thu", "Fri-Sun"),
    "this_month": ("Early Month", "Mid Month", "Late Month"),
    "current_phase": ("What Is Stirring", "What Needs Care", "What Opens Next"),
}

DOMAIN_KEYWORDS: dict[FortuneDomain, tuple[str, str, str, str]] = {
    "love": ("Soft Opening", "Listening", "Warmth", "Honesty"),
    "career": ("Expansion", "Preparation", "Decision", "Positioning"),
    "money": ("Consolidation", "Review", "Discipline", "Containment"),
    "relationships": ("Harmony", "Repair", "Boundaries", "Trust"),
    "health": ("Grounding", "Recovery", "Rhythm", "Care"),
    "overall": ("Shift", "Balance", "Momentum", "Perspective"),
}


def _tone_from_score(score: int) -> str:
    if score >= 78:
        return "strong"
    if score >= 66:
        return "highlight"
    if score >= 54:
        return "soft"
    return "muted"


def analyze_domain_fortune(
    user_saju: SajuData,
    domain: FortuneDomain,
    period: FortunePeriod,
    current_date: date,
) -> DomainFortuneResult:
    """Analyze a domain-specific flow for a selected period."""

    focus_elements = DOMAIN_FOCUS[domain]
    scores = element_scores(user_saju.elements)
    domain_affinity = scores[focus_elements[0]] + scores[focus_elements[1]]

    date_element = SEASONAL_ELEMENT_BY_MONTH[current_date.month]
    support_bonus = 5 if any(supports(element, date_element) for element in focus_elements) else 0
    tension_penalty = 4 if date_element in user_saju.lacking_elements else 0
    period_bonus = {
        "today": current_date.day % 5,
        "this_week": ((current_date.isoweekday() + current_date.day) % 6),
        "this_month": current_date.month % 6,
        "current_phase": (current_date.month + current_date.day) % 7,
    }[period]

    score = 42 + (domain_affinity * 5) + support_bonus + period_bonus - tension_penalty
    score = max(35, min(92, score))

    keyword_pool = DOMAIN_KEYWORDS[domain]
    headline_keyword = keyword_pool[min(3, max(0, (score - 40) // 14))]
    flow_label = {
        "strong": "Open",
        "highlight": "Rising",
        "soft": "Gentle",
        "muted": "Careful",
    }[_tone_from_score(score)]

    segment_labels = PERIOD_LABELS[period]
    segments: list[FortuneSegment] = []
    for index, label in enumerate(segment_labels):
        segment_score = max(35, min(92, score + (index - 1) * 6))
        keyword = keyword_pool[(index + current_date.day) % len(keyword_pool)]
        segments.append(
            FortuneSegment(
                label=label,
                keyword=keyword,
                tone=_tone_from_score(segment_score),
            )
        )

    one_line_summary = {
        "love": "The emotional flow is easier when you stay warm without pushing the moment too hard.",
        "career": "The career flow favors clear positioning over impulsive movement.",
        "money": "Money flow improves when you tighten the small leaks before chasing bigger gains.",
        "relationships": "Relationships soften when you let honesty lead before assumption takes over.",
        "health": "Your energy steadies when rhythm matters more than intensity.",
        "overall": "The overall flow asks for balance first, then movement.",
    }[domain]

    recommended_action = {
        "love": "Speak a little more plainly than usual, but keep the pace gentle.",
        "career": "Review options carefully, then move where momentum genuinely answers you.",
        "money": "Protect your energy and your spending in the same quiet way.",
        "relationships": "Clarify the tone before you try to solve the whole situation.",
        "health": "Choose rest that restores rhythm, not just distraction.",
        "overall": "Stay close to what feels steady, then act where the path opens naturally.",
    }[domain]

    semantic_key = f"fortune_flow:{domain}:{period}"
    summary = f"{flow_label} {domain} flow with a score of {score} for {period.replace('_', ' ')}."

    return DomainFortuneResult(
        semantic_key=semantic_key,
        domain=domain,
        period=period,
        headline_keyword=headline_keyword,
        one_line_summary=one_line_summary,
        segments=segments,
        recommended_action=recommended_action,
        score=score,
        flow_label=flow_label,
        summary=summary,
    )
