"""Rule-engine signal codes → one-line English descriptions for API / LLM."""

from __future__ import annotations

SIGNAL_GLOSS_EN: dict[str, str] = {
    "initiative_high": "Strong drive—you tend to initiate and push forward decisively.",
    "growth_oriented": "Goal-setting, learning, and expansion energies come online easily.",
    "expressive_presence": "Your presence and expressive style read clearly outward.",
    "analytical_focus_high": "Quick to structure ideas, set criteria, and think in frameworks.",
    "emotional_sensitivity_high": "Attuned to atmosphere and moods; feelings may run deeper inside.",
    "stability_high": "Stamina and grounding help you hold the line once you commit.",
    "leadership_fit": "Natural openings for guiding others and owning outcomes.",
    "creative_fit": "High payoff when building new shapes, formats, or experiments.",
    "strategy_fit": "Strength in reading situations and pacing your moves.",
    "operations_fit": "Strong suit in running procedures, refinement, and delivery.",
    "people_oriented_fit": "Results tend to unlock through collaboration and rapport.",
    "affection_direct": "Affection tends to register in a forthright, unambiguous way.",
    "emotional_depth_high": "Emotional intimacy and immersion open without much prompting.",
    "relationship_stability_seek": "You favor predictable rhythms and safety in partnerships.",
    "needs_personal_space": "Periodic distance and pacing help prevent burnout.",
    "wealth_growth_potential": "Meaningful headroom for growth and directional wealth choices.",
    "wealth_planning_strength": "Balanced instincts for budgeting, planning, and allocation.",
    "wealth_opportunity_sense": "You notice windows and mobilize toward opportunity.",
    "stability_low": "When footing is uneven, moods and schedules can wobble.",
    "burnout_risk": "Overload spells may take longer than expected to bounce back from.",
    "overthinking_risk": "Loops of analysis may delay decisive timing.",
    "decision_scatter_risk": "Many options may dilute focus if not curated.",
    "relationship_guardedness": "Holding cards close can accumulate misunderstandings.",
}


def gloss_signals_by_section(raw: dict[str, list[str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for section, codes in raw.items():
        lines: list[str] = []
        for code in codes:
            lines.append(
                SIGNAL_GLOSS_EN.get(code, f"{code}: flagged by the rule engine as a signal.")
            )
        if lines:
            out[section] = lines
    return out
