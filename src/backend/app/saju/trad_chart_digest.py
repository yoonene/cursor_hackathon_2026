"""PillarCN(한자) → 한글 읽기·띠·일주 요약 생성."""

from __future__ import annotations

import json

from app.saju.lunar_chart_models import CalculationResult
from app.saju.lunar_constants import STEM_TO_KOREAN
from app.schemas.tradition import TraditionalChartDigest
from app.saju.signal_gloss_ko import gloss_signals_by_section


# 지지 한 글자 음(간지 호칭용, 申≠辛 구분 위해 지지 표기 고정)
ZHI_SYLLABLE_KO: dict[str, str] = {
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

ZHI_ANIMAL_KO: dict[str, str] = {
    "子": "쥐",
    "丑": "소",
    "寅": "호랑이",
    "卯": "토끼",
    "辰": "용",
    "巳": "뱀",
    "午": "말",
    "未": "양",
    "申": "원숭이",
    "酉": "닭",
    "戌": "개",
    "亥": "돼지",
}


def _stem_syllable(gan: str) -> str:
    """예: 신금 → 신"""
    label = STEM_TO_KOREAN[gan]
    return label[0] if label else gan


def _pillar_hangul_pair(p_gan: str, p_zhi: str) -> str:
    return f"{_stem_syllable(p_gan)}{ZHI_SYLLABLE_KO.get(p_zhi, p_zhi)}"


def _pillar_line_ko(name: str, gan: str, zhi: str, hanja_pair: str) -> str:
    stem_ko = STEM_TO_KOREAN[gan]
    zi = ZHI_SYLLABLE_KO.get(zhi, zhi)
    animal = ZHI_ANIMAL_KO.get(zhi, "")
    animal_part = f" · 띠 {animal}" if animal else ""
    return f"{name}주 {hanja_pair} — 천간 {stem_ko}, 지지 {zi}({animal}){animal_part}"


def build_traditional_chart_digest(
    calculation: CalculationResult,
    signals_by_section: dict[str, list[str]],
) -> TraditionalChartDigest:
    chart = calculation.chart
    metrics = calculation.metrics

    pillars_hanja: dict[str, str] = {
        "year": chart.year_pillar.value,
        "month": chart.month_pillar.value,
        "day": chart.day_pillar.value,
    }
    if chart.hour_pillar is not None:
        pillars_hanja["hour"] = chart.hour_pillar.value

    day_gan, day_zhi = chart.day_pillar.gan, chart.day_pillar.zhi
    ilgan_oheng = STEM_TO_KOREAN[day_gan]
    ilju_hangul = _pillar_hangul_pair(day_gan, day_zhi)
    animal = ZHI_ANIMAL_KO.get(day_zhi, "")

    lines: list[str] = []
    mapping = (
        ("연", chart.year_pillar),
        ("월", chart.month_pillar),
        ("일", chart.day_pillar),
    )
    for label, p in mapping:
        lines.append(_pillar_line_ko(label, p.gan, p.zhi, p.value))
    if chart.hour_pillar:
        hp = chart.hour_pillar
        lines.append(_pillar_line_ko("시", hp.gan, hp.zhi, hp.value))

    strength_raw = metrics.get("day_master_strength", "")
    idx_raw = metrics.get("strength_index")
    strength_ko = ""
    if isinstance(strength_raw, str) and strength_raw:
        kor_map = {"strong": "신강", "weak": "신약", "balanced": "중화"}
        strength_ko = kor_map.get(strength_raw, strength_raw)
        if isinstance(idx_raw, int):
            strength_ko = f"{strength_ko} (지표 {idx_raw:+d}: 토생·설기 대비)"

    return TraditionalChartDigest(
        pillars_hanja=pillars_hanja,
        day_stem_oheng_ko=ilgan_oheng,
        ilju_ganji_hangul=ilju_hangul,
        ilju_branch_animal_ko=animal,
        pillar_lines_ko=lines,
        day_master_strength_ko=strength_ko,
        signals_ko=gloss_signals_by_section(signals_by_section),
    )


def summarize_digest_for_prompt(digest: TraditionalChartDigest) -> str:
    """LLM 에 넣기 좋은 압축 텍스트."""
    parts = [
        f"네 기둥(한자): {digest.pillars_hanja}",
        f"일간(오행): {digest.day_stem_oheng_ko}",
        f"일주 한글 간지음: {digest.ilju_ganji_hangul}",
        f"일지 동물 띠: {digest.ilju_branch_animal_ko}",
    ]
    if digest.day_master_strength_ko:
        parts.append(f"일간 강약 참고: {digest.day_master_strength_ko}")
    parts.append("기둥별 요약(한글): " + " | ".join(digest.pillar_lines_ko))
    if digest.signals_ko:
        parts.append("규칙 엔진 신호(한글): " + json.dumps(digest.signals_ko, ensure_ascii=False))
    return "\n".join(parts)
