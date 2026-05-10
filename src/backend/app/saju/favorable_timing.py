from __future__ import annotations

from datetime import date, timedelta

from app.schemas.fortune import (
    ActionType,
    FortuneSegment,
    TimingDomain,
    TimingResult,
    TimingWindow,
)
from app.schemas.saju import SajuData
from app.saju.common import SEASONAL_ELEMENT_BY_MONTH, element_scores, supports

TIMING_FOCUS: dict[tuple[TimingDomain, ActionType], tuple[str, str]] = {
    ("love", "confession"): ("fire", "water"),
    ("career", "job_change"): ("wood", "metal"),
    ("career", "interview"): ("metal", "water"),
    ("relationships", "important_conversation"): ("water", "fire"),
    ("money", "investment_decision"): ("earth", "metal"),
    ("general", "move"): ("wood", "earth"),
    ("general", "start_something"): ("wood", "fire"),
    ("general", "end_something"): ("metal", "water"),
    ("health", "start_something"): ("earth", "water"),
}

ACTION_KEYWORDS: dict[ActionType, tuple[str, str, str]] = {
    "confession": ("Observe", "Speak", "Move Forward"),
    "job_change": ("Prepare", "Reach Out", "Decide"),
    "interview": ("Research", "Present", "Follow Up"),
    "important_conversation": ("Soften", "Name It", "Settle"),
    "investment_decision": ("Review", "Measure", "Commit Carefully"),
    "move": ("Sort", "Prepare", "Transition"),
    "start_something": ("Gather", "Begin", "Build"),
    "end_something": ("Reflect", "Release", "Reset"),
    "other": ("Watch", "Open", "Move"),
}


def _format_date_range(day: date) -> str:
    return f"Around {day.strftime('%B')} {day.day}"


def _score_day(user_saju: SajuData, focus_elements: tuple[str, str], current_day: date) -> int:
    scores = element_scores(user_saju.elements)
    day_element = SEASONAL_ELEMENT_BY_MONTH[current_day.month]
    base = scores[focus_elements[0]] + scores[focus_elements[1]]
    support_bonus = 4 if any(supports(element, day_element) for element in focus_elements) else 0
    date_variation = ((current_day.toordinal() % 7) - 3) * 2
    lacking_penalty = 5 if day_element in user_saju.lacking_elements else 0
    return 45 + (base * 4) + support_bonus + date_variation - lacking_penalty


def analyze_favorable_timing(
    user_saju: SajuData,
    domain: TimingDomain,
    action_type: ActionType,
    current_date: date,
    other_person_saju: SajuData | None = None,
    user_goal: str | None = None,
) -> TimingResult:
    """Recommend a favorable time for a specific intended action."""

    focus_elements = TIMING_FOCUS.get((domain, action_type), ("wood", "water"))
    day_scores: list[tuple[date, int]] = []
    for offset in range(14):
        target_day = current_date + timedelta(days=offset)
        score = _score_day(user_saju, focus_elements, target_day)
        if other_person_saju and domain in {"love", "relationships"}:
            score += len(set(other_person_saju.dominant_elements) & set(user_saju.lacking_elements)) * 2
        day_scores.append((target_day, max(35, min(95, score))))

    best_day, best_score = max(day_scores, key=lambda item: item[1])
    caution_day, caution_score = min(day_scores, key=lambda item: item[1])

    best_reason = {
        "confession": "Your words are more likely to land softly, and the emotional atmosphere feels more open.",
        "job_change": "This window supports movement with structure instead of restless jumping.",
        "interview": "The energy is cleaner for speaking clearly and being read well.",
        "important_conversation": "This timing supports honesty without unnecessary sharpness.",
        "investment_decision": "The mind is steadier here, which helps judgment stay cleaner.",
        "move": "This period favors transition without feeling too scattered.",
        "start_something": "The current rises enough here for a beginning to take root.",
        "end_something": "This timing helps closure feel cleaner and less emotionally tangled.",
        "other": "The flow is more supportive here for acting with confidence.",
    }[action_type]
    if user_goal:
        best_reason = f"{best_reason} It especially suits your goal of {user_goal}."

    caution_reason = {
        "confession": "You may feel more hurried than the moment actually requires.",
        "job_change": "This period can make movement look urgent before the foundation is ready.",
        "interview": "The mind can tighten here, which makes self-expression less natural.",
        "important_conversation": "Emotional timing feels a little harsher here than it needs to.",
        "investment_decision": "Pressure can distort judgment here, even if the idea itself is sound.",
        "move": "Too many details may compete at once in this window.",
        "start_something": "The opening looks less anchored here, so momentum may scatter.",
        "end_something": "Letting go here could feel more reactive than resolved.",
        "other": "This timing asks for more patience than action.",
    }[action_type]

    keywords = ACTION_KEYWORDS[action_type]
    buckets = (
        ("Now", current_date, current_date + timedelta(days=3)),
        ("Soon", current_date + timedelta(days=4), current_date + timedelta(days=8)),
        ("Next", current_date + timedelta(days=9), current_date + timedelta(days=13)),
    )
    timeline: list[FortuneSegment] = []
    for index, (label, start_day, end_day) in enumerate(buckets):
        bucket_scores = [score for day, score in day_scores if start_day <= day <= end_day]
        average_score = sum(bucket_scores) // max(1, len(bucket_scores))
        tone = "strong" if average_score >= 78 else "highlight" if average_score >= 66 else "soft" if average_score >= 54 else "muted"
        timeline.append(
            FortuneSegment(
                label=label,
                keyword=keywords[index],
                tone=tone,
            )
        )

    headline_keyword = {
        "strong": "Forward Momentum",
        "highlight": "Open Window",
        "soft": "Gentle Timing",
        "muted": "Slow and Steady",
    }["strong" if best_score >= 78 else "highlight" if best_score >= 66 else "soft" if best_score >= 54 else "muted"]

    one_line_summary = {
        "confession": "The middle of the next two weeks holds the softest opening for speaking your heart.",
        "job_change": "There is a better window ahead for moving with structure instead of pressure.",
        "interview": "A clearer speaking window is approaching, and it is worth preparing for it.",
        "important_conversation": "There is a better time to speak when the atmosphere feels less sharp.",
        "investment_decision": "The stronger timing is the one that feels measured, not rushed.",
        "move": "The cleaner transition window comes after a little more preparation.",
        "start_something": "The energy builds best when the first step is taken in a steadier window.",
        "end_something": "Closure will feel cleaner if you wait for the calmer opening ahead.",
        "other": "A more favorable window is approaching if you do not force the timing too early.",
    }[action_type]

    semantic_key = f"timing:{domain}:{action_type}"
    summary = f"Best timing score {best_score} for {action_type.replace('_', ' ')}."

    return TimingResult(
        semantic_key=semantic_key,
        domain=domain,
        action_type=action_type,
        headline_keyword=headline_keyword,
        one_line_summary=one_line_summary,
        recommended_window=TimingWindow(
            label="Strongest Window",
            date_range=_format_date_range(best_day),
            reason=best_reason,
            score=best_score,
        ),
        timeline=timeline,
        caution_window=TimingWindow(
            label="Use Caution",
            date_range=_format_date_range(caution_day),
            reason=caution_reason,
            score=caution_score,
        ),
        timing_score=best_score,
        summary=summary,
    )
