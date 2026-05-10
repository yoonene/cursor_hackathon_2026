"""TraditionalChartDigest is English-only aside from Hanja pillar strings."""

from __future__ import annotations

import pytest

from app.saju.chart_identity_builder import build_chart_identity
from app.saju.lunar_chart_models import CalculationResult, Chart, ElementDistribution, PillarCN
from app.saju.trad_chart_digest import build_traditional_chart_digest


def _minimal_chart() -> Chart:
    y = PillarCN(gan="戊", zhi="寅")
    m = PillarCN(gan="甲", zhi="子")
    d = PillarCN(gan="丙", zhi="午")
    h = PillarCN(gan="壬", zhi="辰")
    return Chart(
        year_pillar=y,
        month_pillar=m,
        day_pillar=d,
        hour_pillar=h,
        day_master="Bing Fire",
    )


def test_chart_digest_strings_are_mostly_ascii_english() -> None:
    calc = CalculationResult(
        chart=_minimal_chart(),
        elements=ElementDistribution(wood=1, fire=1, earth=1, metal=1, water=1),
        metrics={
            "day_master_strength": "strong",
            "strength_index": 3,
            "birth_time_known": True,
            "gender_identity": None,
        },
    )
    digest = build_traditional_chart_digest(calc, {})
    assert digest.day_branch_animal_label == "Horse"
    assert digest.day_pillar_reading_en == "Bing Wu"
    assert "Fire" in digest.day_stem_label_en  # stem label names the element

    def _has_hangul(s: str) -> bool:
        return any("\uac00" <= ch <= "\ud7af" for ch in s)

    for fld in (
        digest.day_stem_label_en,
        digest.day_pillar_reading_en,
        digest.day_branch_animal_label,
        digest.day_master_strength_en,
    ):
        assert not _has_hangul(fld), fld

    assert not _has_hangul(" ".join(digest.pillar_lines_en))
    for glosses in digest.signals_gloss_en.values():
        assert not _has_hangul(" ".join(glosses))


def test_gan_identity_matches_roman_pair() -> None:
    dp = build_chart_identity(PillarCN(gan="丙", zhi="午")).day_pillar
    assert dp.ganji_reading_en == "Bing Wu"
