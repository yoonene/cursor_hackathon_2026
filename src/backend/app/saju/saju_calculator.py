"""월간·양력 처리 및 원국 표준화 계산층 — lunar_python 기반."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from itertools import combinations
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.saju.lunar_chart_models import CalculationResult, Chart, ElementDistribution, PillarCN
from app.saju.lunar_constants import (
    BRANCH_CLASH_PAIRS,
    BRANCH_TO_HIDDEN_STEMS,
    BRANCH_TO_PRIMARY_ELEMENT,
    CONTROLLED_BY,
    CONTROLS,
    GENERATED_BY,
    GENERATES,
    STEM_TO_ELEMENT,
    STEM_TO_KOREAN,
    STEM_TO_POLARITY,
    STEM_TO_ENGLISH_LABEL,
)

try:
    from lunar_python import Lunar, Solar
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "lunar-python is required. Install with `uv sync` (see pyproject dependencies)."
    ) from exc


class CalendarType(str, Enum):
    SOLAR = "solar"
    LUNAR = "lunar"


class Locale(str, Enum):
    EN = "en"
    KO = "ko"


class SajuCalculationRequest(BaseModel):
    """side_projects AnalysisRequest 와 동등한 최소 필드."""

    birth_date: date
    birth_time: time | None = None
    calendar: CalendarType = CalendarType.SOLAR
    timezone: str = Field(default="Asia/Seoul", description="IANA timezone")
    locale: Literal["en", "ko"] = "en"
    gender: str | None = None


class SajuCalculator:
    """만세력 기둥·오행 분포·일간 강약 등 결정론적 팩트."""

    FALLBACK_BIRTH_TIME = time(hour=12, minute=0)

    def calculate(self, request: SajuCalculationRequest) -> CalculationResult:
        birth_time_known = request.birth_time is not None
        birth_time = request.birth_time or self.FALLBACK_BIRTH_TIME

        local_birth_dt = datetime.combine(request.birth_date, birth_time).replace(
            tzinfo=ZoneInfo(request.timezone)
        )
        solar = self._to_solar(request, local_birth_dt)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        year_pillar = self._build_pillar(eight_char.getYearGan(), eight_char.getYearZhi())
        month_pillar = self._build_pillar(eight_char.getMonthGan(), eight_char.getMonthZhi())
        day_pillar = self._build_pillar(eight_char.getDayGan(), eight_char.getDayZhi())
        hour_pillar = (
            self._build_pillar(eight_char.getTimeGan(), eight_char.getTimeZhi())
            if birth_time_known
            else None
        )

        locale = request.locale
        day_stem = day_pillar.gan
        day_master = STEM_TO_ENGLISH_LABEL[day_stem] if locale == "en" else STEM_TO_KOREAN[day_stem]

        chart = Chart(
            year_pillar=year_pillar,
            month_pillar=month_pillar,
            day_pillar=day_pillar,
            hour_pillar=hour_pillar,
            day_master=day_master,
        )

        elements = self._calculate_element_distribution(chart)
        metrics = self._build_metrics(chart, elements, request, birth_time_known)
        return CalculationResult(chart=chart, elements=elements, metrics=metrics)

    def _to_solar(self, request: SajuCalculationRequest, local_birth_dt: datetime):
        if request.calendar == CalendarType.SOLAR:
            return Solar.fromYmdHms(
                local_birth_dt.year,
                local_birth_dt.month,
                local_birth_dt.day,
                local_birth_dt.hour,
                local_birth_dt.minute,
                local_birth_dt.second,
            )

        lunar = Lunar.fromYmdHms(
            local_birth_dt.year,
            local_birth_dt.month,
            local_birth_dt.day,
            local_birth_dt.hour,
            local_birth_dt.minute,
            local_birth_dt.second,
        )
        return lunar.getSolar()

    @staticmethod
    def _build_pillar(gan: str, zhi: str) -> PillarCN:
        return PillarCN(gan=gan, zhi=zhi)

    def _calculate_element_distribution(self, chart: Chart) -> ElementDistribution:
        counts = {element: 0 for element in ("wood", "fire", "earth", "metal", "water")}
        pillars = [chart.year_pillar, chart.month_pillar, chart.day_pillar]
        if chart.hour_pillar is not None:
            pillars.append(chart.hour_pillar)

        for pillar in pillars:
            counts[STEM_TO_ELEMENT[pillar.gan]] += 1
            for hidden_stem in BRANCH_TO_HIDDEN_STEMS[pillar.zhi]:
                counts[STEM_TO_ELEMENT[hidden_stem]] += 1

        return ElementDistribution(**counts)

    def _build_metrics(
        self,
        chart: Chart,
        elements: ElementDistribution,
        request: SajuCalculationRequest,
        birth_time_known: bool,
    ) -> dict[str, object]:
        element_counts = elements.as_dict()
        day_element = STEM_TO_ELEMENT[chart.day_pillar.gan]
        resource_element = GENERATED_BY[day_element]
        output_element = GENERATES[day_element]
        wealth_element = CONTROLS[day_element]
        power_element = CONTROLLED_BY[day_element]
        month_branch_element = BRANCH_TO_PRIMARY_ELEMENT[chart.month_pillar.zhi]
        season_support = month_branch_element in {day_element, resource_element}

        peer_score = element_counts[day_element]
        resource_score = element_counts[resource_element]
        output_score = element_counts[output_element]
        wealth_score = element_counts[wealth_element]
        power_score = element_counts[power_element]

        support_score = peer_score + resource_score + (1 if season_support else 0)
        drain_score = output_score + wealth_score + power_score
        strength_index = support_score - drain_score

        if strength_index >= 2:
            day_master_strength = "strong"
        elif strength_index <= -2:
            day_master_strength = "weak"
        else:
            day_master_strength = "balanced"

        dominant_count = max(element_counts.values())
        dominant_elements = [
            element for element, count in element_counts.items() if count == dominant_count
        ]
        lacking_elements = [element for element, count in element_counts.items() if count == 0]

        branches = [
            chart.year_pillar.zhi,
            chart.month_pillar.zhi,
            chart.day_pillar.zhi,
        ]
        if chart.hour_pillar is not None:
            branches.append(chart.hour_pillar.zhi)

        return {
            "calendar": request.calendar.value,
            "gender_identity": request.gender,
            "timezone": request.timezone,
            "locale": request.locale,
            "birth_time_known": birth_time_known,
            "analysis_depth": "full" if birth_time_known else "date_only",
            "day_master": chart.day_master,
            "day_master_gan": chart.day_pillar.gan,
            "day_master_element": day_element,
            "resource_element": resource_element,
            "output_element": output_element,
            "wealth_element": wealth_element,
            "power_element": power_element,
            "day_master_polarity": STEM_TO_POLARITY[chart.day_pillar.gan],
            "day_master_strength": day_master_strength,
            "strength_index": strength_index,
            "season_support": season_support,
            "month_branch_element": month_branch_element,
            "dominant_elements": dominant_elements,
            "lacking_elements": lacking_elements,
            "peer_score": peer_score,
            "resource_score": resource_score,
            "output_score": output_score,
            "wealth_score": wealth_score,
            "power_score": power_score,
            "support_score": support_score,
            "drain_score": drain_score,
            "clash_count": self._count_branch_clashes(branches),
            "branches": branches,
            "element_distribution": element_counts,
            "year_zhi": chart.year_pillar.zhi,
            "month_zhi": chart.month_pillar.zhi,
            "day_zhi": chart.day_pillar.zhi,
            "hour_zhi": chart.hour_pillar.zhi if chart.hour_pillar else None,
        }

    @staticmethod
    def _count_branch_clashes(branches: list[str]) -> int:
        clash_count = 0
        for left, right in combinations(branches, 2):
            if frozenset({left, right}) in BRANCH_CLASH_PAIRS:
                clash_count += 1
        return clash_count
