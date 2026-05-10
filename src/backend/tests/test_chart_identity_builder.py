from __future__ import annotations

import string

import pytest

from app.saju.chart_identity_builder import build_chart_identity, chart_identity_summary
from app.saju.lunar_chart_models import PillarCN


def _is_ascii_public_label(s: str) -> bool:
    allowed = string.ascii_letters + string.digits + string.whitespace + "·-"
    return all(c in allowed for c in s)


STEMS_CYCLE = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCH_CYCLE = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


def _sixty_jiazi_pillars() -> list[PillarCN]:
    out: list[PillarCN] = []
    gi = zi = 0
    for _ in range(60):
        out.append(PillarCN(gan=STEMS_CYCLE[gi], zhi=BRANCH_CYCLE[zi]))
        gi = (gi + 1) % 10
        zi = (zi + 1) % 12
    return out


def test_xin_mao_maps_to_white_rabbit_and_yin_metal() -> None:
    pillar = PillarCN(gan="辛", zhi="卯")
    ci = build_chart_identity(pillar)
    assert ci.day_pillar.ganji_hanja == "辛卯"
    assert ci.day_pillar.stem_hanja == "辛"
    assert ci.day_pillar.branch_hanja == "卯"
    assert ci.day_pillar.ganji_hangul == "신묘"
    assert ci.day_pillar.animal == "rabbit"
    assert ci.day_pillar.animal_label == "Rabbit"
    assert ci.day_pillar.color == "white"
    assert ci.day_pillar.english_name == "White Rabbit"

    dm = ci.day_master
    assert dm.element == "metal"
    assert dm.element_label == "Metal"
    assert dm.polarity == "yin"
    assert dm.stem_hangul == "신"
    assert dm.english_name == "Yin Metal"
    assert dm.display_label == "辛 · Yin Metal"

    vt = ci.visual_tokens
    assert vt.theme == "metal"
    assert vt.accent == "white"
    assert vt.animal == "rabbit"

    summary = chart_identity_summary(ci)
    assert summary.day_pillar_hanja == "辛卯"
    assert summary.day_pillar_label == "White Rabbit"
    assert summary.day_master_label == "Yin Metal"
    assert summary.display_label == "辛卯 · White Rabbit · Yin Metal"
    assert summary.theme == "metal"
    assert summary.accent == "white"
    assert summary.animal == "rabbit"

    assert any(ord(c) > 127 for c in summary.display_label), "display mixes Hanja plus English ASCII"
    for en in (
        ci.day_pillar.english_name,
        ci.day_pillar.animal_label,
        ci.day_master.english_name,
        ci.day_master.element_label,
        summary.day_pillar_label,
        summary.day_master_label,
    ):
        assert _is_ascii_public_label(en), en


@pytest.mark.parametrize(
    ("gan", "zhi", "expected_prefix"),
    [
        ("甲", "子", "Green "),
        ("乙", "丑", "Green "),
        ("庚", "寅", "White "),
        ("辛", "卯", "White "),
        ("壬", "辰", "Black "),
        ("癸", "巳", "Black "),
    ],
)
def test_stem_maps_to_correct_element_palette(gan: str, zhi: str, expected_prefix: str) -> None:
    ci = build_chart_identity(PillarCN(gan=gan, zhi=zhi))
    assert ci.day_pillar.english_name.startswith(expected_prefix)


@pytest.mark.parametrize("pillar", _sixty_jiazi_pillars())
def test_all_standard_sixty_pillars_have_ascii_english_names(pillar: PillarCN) -> None:
    ci = build_chart_identity(pillar)
    assert ci.day_pillar.ganji_hanja == pillar.value
    assert _is_ascii_public_label(ci.day_pillar.english_name)
    assert _is_ascii_public_label(ci.day_master.english_name)
    assert chart_identity_summary(ci).display_label.count(" · ") >= 2
