"""Maps lunar day pillar / day stem → ChartIdentity (English labels for UI)."""

from __future__ import annotations

from typing import cast

from app.saju.lunar_chart_models import PillarCN
from app.saju.lunar_constants import STEM_TO_ELEMENT, STEM_TO_POLARITY, STEM_TO_KOREAN, ZHI_TO_BRANCH_EN
from app.schemas.chart_identity import (
    ChartIdentity,
    ChartIdentitySummary,
    ChartVisualTokens,
    DayMasterIdentity,
    DayPillarIdentity,
    PolarityToken,
)
from app.schemas.saju import ElementName

# Heavenly stems → Yin/Yang + element (five phases) visualization palette
_ELEMENT_DISPLAY_EN: dict[str, str] = {
    "wood": "Wood",
    "fire": "Fire",
    "earth": "Earth",
    "metal": "Metal",
    "water": "Water",
}

_ELEMENT_COLOR_ADJ_EN: dict[str, str] = {
    "wood": "Green",
    "fire": "Red",
    "earth": "Yellow",
    "metal": "White",
    "water": "Black",
}

_ELEMENT_COLOR_TOKEN: dict[str, str] = {
    "wood": "green",
    "fire": "red",
    "earth": "yellow",
    "metal": "white",
    "water": "black",
}

_ZHI_SYLLABLE_KO: dict[str, str] = {
    "子": "자",
    "丑": "축",
    "寅": "인",
    "卯": "묘",
    "辰": "진",
    "巳": "사",
    "午": "오",
    "未": "미",
    "申": "신",
    "酉": "유",
    "戌": "술",
    "亥": "해",
}


def _stem_korean_initial(gan: str) -> str:
    ko = STEM_TO_KOREAN[gan]
    return ko[0] if ko else gan


def _ganji_hangul(gan: str, zhi: str) -> str:
    return f"{_stem_korean_initial(gan)}{_ZHI_SYLLABLE_KO.get(zhi, zhi)}"


def _animal_slug(animal_label: str) -> str:
    return animal_label.lower()


def build_chart_identity(pillar: PillarCN) -> ChartIdentity:
    """Derive identities from calendar day pillar (일주 한자 간지).

    Day pillar symbolic English name follows “{Element color adj.} {Branch animal}”
    (covers all 60 Jiazi-cycle pairs deterministically — same pattern as Xin Mao → White Rabbit).
    """
    gan, zhi = pillar.gan, pillar.zhi
    element = cast(ElementName, STEM_TO_ELEMENT[gan])
    polarity = cast(PolarityToken, STEM_TO_POLARITY[gan])

    polarity_en = "Yin" if polarity == "yin" else "Yang"
    element_cap = _ELEMENT_DISPLAY_EN[element]

    stem_hangul = _stem_korean_initial(gan)
    branch_label = ZHI_TO_BRANCH_EN[zhi]
    color_adj = _ELEMENT_COLOR_ADJ_EN[element]
    color_token = _ELEMENT_COLOR_TOKEN[element]
    pillar_en = f"{color_adj} {branch_label}"

    day_pillar = DayPillarIdentity(
        ganji_hanja=pillar.value,
        ganji_hangul=_ganji_hangul(gan, zhi),
        stem_hanja=gan,
        branch_hanja=zhi,
        english_name=pillar_en,
        animal=_animal_slug(branch_label),
        animal_label=branch_label,
        color=color_token,
    )

    dm_en = f"{polarity_en} {element_cap}"
    day_master = DayMasterIdentity(
        stem_hanja=gan,
        stem_hangul=stem_hangul,
        element=element,
        element_label=element_cap,
        polarity=polarity,
        english_name=dm_en,
        display_label=f"{gan} · {dm_en}",
    )

    visual = ChartVisualTokens(
        theme=element,
        accent=color_token,
        animal=_animal_slug(branch_label),
    )

    return ChartIdentity(day_pillar=day_pillar, day_master=day_master, visual_tokens=visual)


def chart_identity_summary(identity: ChartIdentity) -> ChartIdentitySummary:
    dp = identity.day_pillar
    dm = identity.day_master
    display_label = f"{dp.ganji_hanja} · {dp.english_name} · {dm.english_name}"
    return ChartIdentitySummary(
        day_pillar_hanja=dp.ganji_hanja,
        day_pillar_label=dp.english_name,
        day_master_label=dm.english_name,
        display_label=display_label,
        theme=identity.visual_tokens.theme,
        accent=identity.visual_tokens.accent,
        animal=identity.visual_tokens.animal,
    )
