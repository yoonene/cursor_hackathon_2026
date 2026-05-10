from __future__ import annotations

from app.schemas.saju import ElementBalance, ElementName

ELEMENT_ORDER: tuple[ElementName, ...] = ("wood", "fire", "earth", "metal", "water")

STEMS: tuple[tuple[str, ElementName], ...] = (
    ("Jia", "wood"),
    ("Yi", "wood"),
    ("Bing", "fire"),
    ("Ding", "fire"),
    ("Wu", "earth"),
    ("Ji", "earth"),
    ("Geng", "metal"),
    ("Xin", "metal"),
    ("Ren", "water"),
    ("Gui", "water"),
)

BRANCHES: tuple[tuple[str, ElementName], ...] = (
    ("Rat", "water"),
    ("Ox", "earth"),
    ("Tiger", "wood"),
    ("Rabbit", "wood"),
    ("Dragon", "earth"),
    ("Snake", "fire"),
    ("Horse", "fire"),
    ("Goat", "earth"),
    ("Monkey", "metal"),
    ("Rooster", "metal"),
    ("Dog", "earth"),
    ("Pig", "water"),
)

SUPPORTS: dict[ElementName, ElementName] = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

CONTROLS: dict[ElementName, ElementName] = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}

ELEMENT_KEYWORDS: dict[ElementName, tuple[str, str, str]] = {
    "wood": ("growth-oriented", "future-minded", "flexible"),
    "fire": ("direct", "warm-hearted", "momentum-driven"),
    "earth": ("steady", "protective", "grounding"),
    "metal": ("clear-minded", "refined", "principled"),
    "water": ("deep-feeling", "intuitive", "adaptable"),
}

ELEMENT_STRENGTHS: dict[ElementName, tuple[str, str]] = {
    "wood": ("renewal", "vision"),
    "fire": ("drive", "presence"),
    "earth": ("stability", "care"),
    "metal": ("discernment", "focus"),
    "water": ("sensitivity", "instinct"),
}

ELEMENT_CAUTIONS: dict[ElementName, tuple[str, str]] = {
    "wood": ("scattered momentum", "frustration when growth stalls"),
    "fire": ("emotional overheating", "moving faster than the heart can process"),
    "earth": ("absorbing too much of other people's weight", "staying too long in the familiar"),
    "metal": ("becoming too sharp under pressure", "holding yourself to impossible standards"),
    "water": ("holding things in too long", "drifting into overthinking"),
}

ELEMENT_OPENINGS: dict[ElementName, str] = {
    "wood": "Your energy leans toward growth, movement, and looking ahead.",
    "fire": "Your energy is lively, quick to respond, and hard to keep hidden.",
    "earth": "Your energy settles around steadiness, care, and quiet endurance.",
    "metal": "Your energy is precise, observant, and naturally drawn to clarity.",
    "water": "Your energy runs deep, sensitive, and quietly perceptive.",
}

ELEMENT_SHADOWS: dict[ElementName, str] = {
    "wood": "direction can blur when too many possibilities open at once",
    "fire": "intensity can rise before the heart has had time to settle",
    "earth": "you can carry more than is truly yours to hold",
    "metal": "the mind can become stricter than the moment requires",
    "water": "feelings can stay inside longer than people realize",
}

SEASONAL_ELEMENT_BY_MONTH: dict[int, ElementName] = {
    1: "water",
    2: "wood",
    3: "wood",
    4: "wood",
    5: "fire",
    6: "fire",
    7: "earth",
    8: "earth",
    9: "metal",
    10: "metal",
    11: "water",
    12: "water",
}


def element_scores(balance: ElementBalance) -> dict[ElementName, int]:
    return {
        "wood": balance.wood,
        "fire": balance.fire,
        "earth": balance.earth,
        "metal": balance.metal,
        "water": balance.water,
    }


def dominant_elements_from_balance(balance: ElementBalance) -> list[ElementName]:
    scores = element_scores(balance)
    highest = max(scores.values())
    ordered = sorted(scores.items(), key=lambda item: (-item[1], ELEMENT_ORDER.index(item[0])))
    dominant = [element for element, score in ordered if score == highest]
    if len(dominant) == 1 and len(ordered) > 1 and ordered[1][1] >= highest - 1:
        dominant.append(ordered[1][0])
    return dominant[:2]


def lacking_elements_from_balance(balance: ElementBalance) -> list[ElementName]:
    scores = element_scores(balance)
    lowest = min(scores.values())
    lacking = [element for element, score in scores.items() if score == lowest or score <= 2]
    ordered = sorted(set(lacking), key=ELEMENT_ORDER.index)
    return ordered[:2] or [min(scores, key=scores.get)]


def supports(left: ElementName, right: ElementName) -> bool:
    return SUPPORTS[left] == right


def controls(left: ElementName, right: ElementName) -> bool:
    return CONTROLS[left] == right


def format_element_list(elements: list[ElementName]) -> str:
    if not elements:
        return ""
    if len(elements) == 1:
        return elements[0]
    return ", ".join(elements[:-1]) + f", and {elements[-1]}"
