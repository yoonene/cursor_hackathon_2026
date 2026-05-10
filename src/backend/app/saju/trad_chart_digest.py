"""PillarCN (Hanja) → English-readable digest lines for APIs and prompting."""

from __future__ import annotations

import json

from app.saju.lunar_chart_models import CalculationResult
from app.saju.lunar_constants import (
    GAN_TO_STEM_ROMAN,
    STEM_TO_ENGLISH_LABEL,
    ZHI_TO_BRANCH_EN,
    ZHI_TO_ROMAN,
)
from app.schemas.tradition import TraditionalChartDigest
from app.saju.signal_gloss_en import gloss_signals_by_section


def ganzhi_reading_en(gan: str, zhi: str) -> str:
    """Romanized stem + branch, e.g. Xin Mao."""
    gr = GAN_TO_STEM_ROMAN.get(gan, gan)
    zr = ZHI_TO_ROMAN.get(zhi, zhi)
    return f"{gr} {zr}"


def _pillar_line_en(kind: str, gan: str, zhi: str, hanja_pair: str) -> str:
    stem_en = STEM_TO_ENGLISH_LABEL[gan]
    branch_animal = ZHI_TO_BRANCH_EN[zhi]
    stem_r = GAN_TO_STEM_ROMAN[gan]
    zhi_r = ZHI_TO_ROMAN[zhi]
    return (
        f"{kind} pillar {hanja_pair} — stem {stem_r} ({stem_en}), "
        f"branch {zhi_r} ({branch_animal})"
    )


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
    day_stem_en = STEM_TO_ENGLISH_LABEL[day_gan]
    day_pair_en = ganzhi_reading_en(day_gan, day_zhi)
    animal = ZHI_TO_BRANCH_EN.get(day_zhi, "")

    lines: list[str] = []
    mapping = (
        ("Year", chart.year_pillar),
        ("Month", chart.month_pillar),
        ("Day", chart.day_pillar),
    )
    for label, p in mapping:
        lines.append(_pillar_line_en(label, p.gan, p.zhi, p.value))
    if chart.hour_pillar:
        hp = chart.hour_pillar
        lines.append(_pillar_line_en("Hour", hp.gan, hp.zhi, hp.value))

    strength_raw = metrics.get("day_master_strength", "")
    idx_raw = metrics.get("strength_index")
    strength_en = ""
    if isinstance(strength_raw, str) and strength_raw:
        label_map = {"strong": "Strong", "weak": "Weak", "balanced": "Balanced"}
        strength_en = label_map.get(strength_raw, strength_raw.title())
        if isinstance(idx_raw, int):
            strength_en += f" (index {idx_raw:+d}: support vs drain balance)"

    return TraditionalChartDigest(
        pillars_hanja=pillars_hanja,
        day_stem_label_en=day_stem_en,
        day_pillar_reading_en=day_pair_en,
        day_branch_animal_label=animal,
        pillar_lines_en=lines,
        day_master_strength_en=strength_en,
        signals_gloss_en=gloss_signals_by_section(signals_by_section),
    )


def summarize_digest_for_prompt(digest: TraditionalChartDigest) -> str:
    """Flatten digest for LLM context (ASCII English copy)."""
    parts = [
        f"Hanja pillars: {digest.pillars_hanja}",
        f"Day stem (English label): {digest.day_stem_label_en}",
        f"Romanized day pillar: {digest.day_pillar_reading_en}",
        f"Day branch animal: {digest.day_branch_animal_label}",
    ]
    if digest.day_master_strength_en:
        parts.append(f"Day-master strength note: {digest.day_master_strength_en}")
    parts.append("Pillar lines: " + " | ".join(digest.pillar_lines_en))
    if digest.signals_gloss_en:
        parts.append("Rule-engine signals: " + json.dumps(digest.signals_gloss_en, ensure_ascii=False))
    return "\n".join(parts)
