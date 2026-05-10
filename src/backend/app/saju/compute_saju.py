"""lunar_python 원국 계산 + YAML 규칙 엔진. 서술(NLG)은 LLM 레이어가 담당한다."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.schemas.profiles import PersonProfile
from app.schemas.saju import ElementBalance, ElementName, PillarData, SajuData
from app.saju.common import (
    ELEMENT_CAUTIONS,
    ELEMENT_KEYWORDS,
    ELEMENT_OPENINGS,
    ELEMENT_SHADOWS,
    ELEMENT_STRENGTHS,
    lacking_elements_from_balance,
)
from app.saju.lunar_chart_models import CalculationResult, PillarCN
from app.saju.lunar_constants import (
    BRANCH_TO_PRIMARY_ELEMENT,
    GAN_TO_STEM_ROMAN,
    STEM_TO_ELEMENT,
    ZHI_TO_BRANCH_EN,
)
from app.saju.rule_engine import RuleEngine
from app.saju.saju_calculator import SajuCalculationRequest, SajuCalculator
from app.saju.chart_identity_builder import build_chart_identity
from app.saju.trad_chart_digest import build_traditional_chart_digest


def _raw_distribution_as_balance(calculation: CalculationResult) -> ElementBalance:
    """lunar 계산층 원시 카운트를 그대로 담는다 (side_projects API `elements` 와 같은 척도)."""
    dist = calculation.elements.model_dump()
    return ElementBalance(
        wood=dist["wood"],
        fire=dist["fire"],
        earth=dist["earth"],
        metal=dist["metal"],
        water=dist["water"],
    )


def _lacking_fallback_from_balance(balance: ElementBalance) -> list[ElementName]:
    """원시 분포에서 0건인 오행이 없을 때 규약용으로 최소 카운트를 부족으로 본다."""
    return lacking_elements_from_balance(balance)


def _pillar_cn_to_schema(pc: PillarCN) -> PillarData:
    return PillarData(
        stem_name=GAN_TO_STEM_ROMAN.get(pc.gan, pc.gan),
        stem_element=STEM_TO_ELEMENT[pc.gan],
        branch_name=ZHI_TO_BRANCH_EN.get(pc.zhi, pc.zhi),
        branch_element=BRANCH_TO_PRIMARY_ELEMENT[pc.zhi],
    )


def _build_keywords(
    dominant_elements: list[ElementName], lacking_elements: list[ElementName], day_master: str
) -> list[str]:
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


_calculator: SajuCalculator | None = None
_rule_engine: RuleEngine | None = None


def _get_calculator() -> SajuCalculator:
    global _calculator
    if _calculator is None:
        _calculator = SajuCalculator()
    return _calculator


def _get_rule_engine() -> RuleEngine:
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine


def analyze_base_saju(profile: PersonProfile, *, timezone: str | None = None) -> SajuData:
    """만세력·오행·규칙 시그널까지 결정론적으로 계산한다."""

    if profile.birth_date is None:
        raise ValueError("birth_date is required to analyze base saju")

    settings = get_settings()
    tz = timezone or settings.default_timezone

    req = SajuCalculationRequest(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        timezone=tz,
        gender=profile.gender,
        locale="en",
    )
    calculation = _get_calculator().calculate(req)
    interpretation = _get_rule_engine().evaluate(calculation)
    chart_digest = build_traditional_chart_digest(calculation, interpretation.signal_codes())
    chart_identity = build_chart_identity(calculation.chart.day_pillar)

    balance = _raw_distribution_as_balance(calculation)
    raw_dom: list[str] = list(calculation.metrics["dominant_elements"])  # type: ignore[assignment]
    raw_lacking: list[str] = list(calculation.metrics["lacking_elements"])  # type: ignore[assignment]
    dominant_elements: list[ElementName] = raw_dom  # type: ignore[assignment]
    lacking_elements: list[ElementName] = raw_lacking or _lacking_fallback_from_balance(balance)
    day_master: ElementName = calculation.metrics["day_master_element"]  # type: ignore[assignment]

    primary = dominant_elements[0]
    lacking = lacking_elements[0]

    strengths: list[str] = []
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

    chart = calculation.chart
    notes: list[str] = []
    if not calculation.metrics.get("birth_time_known"):
        notes.append(
            "Birth time was not provided; hour pillar is omitted and analysis depth is date-only."
        )

    metrics_dump: dict[str, Any] = dict(calculation.metrics)

    return SajuData(
        id=profile.id,
        display_name=profile.display_name,
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        birth_time_known=bool(calculation.metrics.get("birth_time_known")),
        gender=profile.gender,
        year_pillar=_pillar_cn_to_schema(chart.year_pillar),
        month_pillar=_pillar_cn_to_schema(chart.month_pillar),
        day_pillar=_pillar_cn_to_schema(chart.day_pillar),
        hour_pillar=_pillar_cn_to_schema(chart.hour_pillar) if chart.hour_pillar else None,
        day_master=day_master,
        elements=balance,
        dominant_elements=dominant_elements,
        lacking_elements=lacking_elements,
        core_keywords=core_keywords,
        overall_summary_seed=overall_summary_seed,
        personality_summary=personality_summary,
        relationship_style=personality_summary,
        career_style=personality_summary,
        emotional_pattern=personality_summary,
        strengths=strengths,
        cautions=cautions,
        calculation_notes=notes,
        calculation_metrics=metrics_dump,
        interpretation_signals=interpretation.signal_codes(),
        chart_digest=chart_digest,
        chart_identity=chart_identity,
    )
