from __future__ import annotations

from collections import defaultdict
from datetime import date, time

from app.schemas.profiles import PersonProfile
from app.schemas.saju import ElementBalance, PillarData, SajuData
from app.saju.common import (
    BRANCHES,
    ELEMENT_CAUTIONS,
    ELEMENT_KEYWORDS,
    ELEMENT_OPENINGS,
    ELEMENT_SHADOWS,
    ELEMENT_STRENGTHS,
    SEASONAL_ELEMENT_BY_MONTH,
    STEMS,
    dominant_elements_from_balance,
    lacking_elements_from_balance,
)


def _build_pillar(stem_index: int, branch_index: int) -> PillarData:
    stem_name, stem_element = STEMS[stem_index % len(STEMS)]
    branch_name, branch_element = BRANCHES[branch_index % len(BRANCHES)]
    return PillarData(
        stem_name=stem_name,
        stem_element=stem_element,
        branch_name=branch_name,
        branch_element=branch_element,
    )


def _hour_branch_index(birth_time: time | None) -> int:
    hour = birth_time.hour if birth_time else 12
    return ((hour + 1) // 2) % 12


def _scale_raw_scores(raw_scores: dict[str, float]) -> ElementBalance:
    max_score = max(raw_scores.values())
    scaled: dict[str, int] = {}
    for element, raw in raw_scores.items():
        normalized = 1 + round((raw / max_score) * 4)
        scaled[element] = max(1, min(5, normalized))
    return ElementBalance(**scaled)


def _relationship_style(dominant: str, lacking: str) -> str:
    opening = {
        "wood": "You tend to move toward connection when there is a sense of growth and shared direction.",
        "fire": "You tend to move toward connection quickly when your heart catches warmth.",
        "earth": "You tend to show care through steadiness, presence, and making space for the other person.",
        "metal": "You tend to watch carefully before opening, but once trust forms, your loyalty is clean and deliberate.",
        "water": "You tend to read between the lines and feel the emotional undercurrent before you speak plainly.",
    }[dominant]
    undercurrent = {
        "wood": "Still, when direction is unclear, your patience can thin faster than people expect.",
        "fire": "Still, strong feelings can flare before you have fully decided what you want to say.",
        "earth": "Still, you can stay in an uneven dynamic too long because you want to hold the bond together.",
        "metal": "Still, when hurt, you may become cooler and harder to read than you intend.",
        "water": "Still, your softer worries can remain unspoken until they become heavier inside.",
    }[lacking]
    return f"{opening} {undercurrent}"


def _career_style(dominant: str, lacking: str) -> str:
    opening = {
        "wood": "You do best in work that has movement, learning, and a sense of upward growth.",
        "fire": "You do best in work where your presence matters and momentum can build around your decisions.",
        "earth": "You do best in work that lets you build trust slowly and turn effort into something tangible.",
        "metal": "You do best in work that values judgment, standards, and thoughtful refinement.",
        "water": "You do best in work that rewards intuition, timing, and understanding what is not said aloud.",
    }[dominant]
    undercurrent = {
        "wood": "When structure is too loose, though, your energy can scatter across too many paths.",
        "fire": "When the pace becomes too hot, though, you may commit before the longer rhythm is clear.",
        "earth": "When nothing changes for too long, though, your strength can quietly harden into stagnation.",
        "metal": "When the environment is chaotic, though, your mind can spend too much energy correcting it.",
        "water": "When the atmosphere feels uncertain, though, you may wait longer than necessary to make the move.",
    }[lacking]
    return f"{opening} {undercurrent}"


def _emotional_pattern(dominant: str, lacking: str) -> str:
    opening = {
        "wood": "Emotionally, you move by sensing whether life is still growing or quietly closing in.",
        "fire": "Emotionally, your reactions rise quickly and honestly, even when you try to stay composed.",
        "earth": "Emotionally, you hold yourself together by grounding the people and situations around you.",
        "metal": "Emotionally, you process by sorting what feels true from what feels noisy or excessive.",
        "water": "Emotionally, you absorb atmosphere deeply and often feel more than you show.",
    }[dominant]
    undercurrent = {
        "wood": "If clarity is missing, restlessness can build beneath the surface.",
        "fire": "If the feeling is not answered, heat can stay in the chest longer than it seems from outside.",
        "earth": "If you keep carrying too much, heaviness can arrive only after you have already pushed through.",
        "metal": "If the moment feels messy, the heart can tighten behind a calm face.",
        "water": "If the feeling has nowhere to go, you may drift into quiet overthinking.",
    }[lacking]
    return f"{opening} {undercurrent}"


def _build_keywords(dominant_elements: list[str], lacking_elements: list[str], day_master: str) -> list[str]:
    keywords: list[str] = []
    for element in dominant_elements:
        for keyword in ELEMENT_KEYWORDS[element]:
            if keyword not in keywords:
                keywords.append(keyword)
            if len(keywords) == 2:
                break
        if len(keywords) == 2:
            break
    fallback_keyword = ELEMENT_KEYWORDS[day_master][2]
    if fallback_keyword not in keywords:
        keywords.append(fallback_keyword)
    elif lacking_elements:
        lacking_keyword = ELEMENT_KEYWORDS[lacking_elements[0]][0]
        if lacking_keyword not in keywords:
            keywords.append(lacking_keyword)
    return keywords[:3]


def analyze_base_saju(profile: PersonProfile) -> SajuData:
    """Generate deterministic MVP saju data from the fixed intake form."""

    if profile.birth_date is None:
        raise ValueError("birth_date is required to analyze base saju")

    birth_date = profile.birth_date
    birth_time = profile.birth_time
    birth_time_known = birth_time is not None

    year_stem_index = (birth_date.year - 4) % 10
    year_branch_index = (birth_date.year - 4) % 12
    month_stem_index = ((birth_date.year * 12) + birth_date.month + 3) % 10
    month_branch_index = (birth_date.month + 1) % 12
    ordinal = birth_date.toordinal()
    day_stem_index = (ordinal + 6) % 10
    day_branch_index = (ordinal + 2) % 12
    hour_branch_index = _hour_branch_index(birth_time)
    hour_stem_index = (day_stem_index * 2 + hour_branch_index) % 10

    year_pillar = _build_pillar(year_stem_index, year_branch_index)
    month_pillar = _build_pillar(month_stem_index, month_branch_index)
    day_pillar = _build_pillar(day_stem_index, day_branch_index)
    hour_pillar = _build_pillar(hour_stem_index, hour_branch_index)

    raw_scores: dict[str, float] = defaultdict(float)
    pillar_weights = (
        (year_pillar.stem_element, 1.0),
        (year_pillar.branch_element, 1.0),
        (month_pillar.stem_element, 1.6),
        (month_pillar.branch_element, 1.6),
        (day_pillar.stem_element, 2.0),
        (day_pillar.branch_element, 1.2),
        (hour_pillar.stem_element, 1.0 if birth_time_known else 0.5),
        (hour_pillar.branch_element, 1.0 if birth_time_known else 0.5),
    )
    for element, weight in pillar_weights:
        raw_scores[element] += weight

    seasonal_element = SEASONAL_ELEMENT_BY_MONTH[birth_date.month]
    raw_scores[seasonal_element] += 0.8

    elements = _scale_raw_scores(raw_scores)
    dominant_elements = dominant_elements_from_balance(elements)
    lacking_elements = lacking_elements_from_balance(elements)
    day_master = day_pillar.stem_element

    primary = dominant_elements[0]
    lacking = lacking_elements[0]
    strengths = []
    strengths.extend(ELEMENT_STRENGTHS[primary])
    if len(dominant_elements) > 1:
        strengths.append(ELEMENT_STRENGTHS[dominant_elements[1]][0])
    strengths = list(dict.fromkeys(strengths))[:3]

    cautions = list(dict.fromkeys(ELEMENT_CAUTIONS[lacking] + ELEMENT_CAUTIONS[primary]))[:3]
    core_keywords = _build_keywords(dominant_elements, lacking_elements, day_master)

    overall_summary_seed = (
        f"A chart led by {primary} energy, with {lacking} asking for more room and care."
    )
    personality_summary = (
        f"{ELEMENT_OPENINGS[primary]} At the same time, {ELEMENT_SHADOWS[lacking]}."
    )

    calculation_notes: list[str] = []
    if not birth_time_known:
        calculation_notes.append(
            "Birth time was not provided, so the hour pillar uses a balanced midday reference."
        )

    return SajuData(
        id=profile.id,
        display_name=profile.display_name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_time_known=birth_time_known,
        gender=profile.gender,
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        day_master=day_master,
        elements=elements,
        dominant_elements=dominant_elements,
        lacking_elements=lacking_elements,
        core_keywords=core_keywords,
        overall_summary_seed=overall_summary_seed,
        personality_summary=personality_summary,
        relationship_style=_relationship_style(primary, lacking),
        career_style=_career_style(primary, lacking),
        emotional_pattern=_emotional_pattern(primary, lacking),
        strengths=strengths,
        cautions=cautions,
        calculation_notes=calculation_notes,
    )
