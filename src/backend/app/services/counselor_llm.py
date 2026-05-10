"""CLōD / OpenAI 호환 Chat Completions로 초기 리딩 문구 생성."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.counselor_llm import InitialReadingLLMOutput
from app.schemas.profiles import PersonProfile
from app.schemas.saju import SajuData
from app.saju.trad_chart_digest import summarize_digest_for_prompt


_SYSTEM_PROMPT = """You are a warm, articulate saju (Four Pillars) counselor speaking in polished English.

You NEVER invent raw chart facts that contradict the provided JSON snapshot. Interpret and narrate ONLY from:
- lunar-accurate pillars and scores
- the deterministic interpretation_signals (these are factual rule hits, not fluff)
- optional `traditional_chart`: Hanja pillar pairs plus Korean labels — day stem 오행 이름 (e.g., 신금), day pillar 한글 간지음 (e.g., 신묘), branch animal (띠), and `signals_ko` glossed lines

When `traditional_chart` / `traditional_chart_plain_ko` is present, weave in terse Korean astrology labels alongside English (parentheses fine), especially day stem and day pillar; do not mistranslate or contradict them.

Produce believable counselor prose: grounded, nuanced, compassionate. Avoid fortune-cookie fluff.
Return a single JSON object with exactly these keys and string/list types:

{
  "assistant_message": "2-5 short paragraphs for chat; natural voice; cite patterns from data",
  "overall_summary": "one compact paragraph headline for the dashboard",
  "keywords": ["three core trait chips, lowercase hyphenated okay"],
  "personality": "one paragraph summary for Personality section",
  "relationship_style": "one paragraph for Relationship Style section",
  "career_style": "one paragraph for Career Style section",
  "emotional_pattern": "one paragraph for Emotional Pattern section",
  "strengths": ["bullet", "bullet", "bullet"],
  "cautions": ["bullet", "bullet", "bullet"],
  "one_line_verdict": "single memorable coaching line under 220 characters"
}

No markdown fences. Output JSON only."""

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def _payload_for_llm(
    profile: PersonProfile,
    saju_data: SajuData,
    calculation_metrics: dict[str, Any],
    interpretation_signals: dict[str, list[str]],
) -> dict[str, Any]:
    pillars = {
        "year": saju_data.year_pillar.model_dump(),
        "month": saju_data.month_pillar.model_dump(),
        "day": saju_data.day_pillar.model_dump(),
        "hour": saju_data.hour_pillar.model_dump() if saju_data.hour_pillar else None,
    }
    payload: dict[str, Any] = {
        "reader_context": {
            "display_name": profile.display_name,
            "birth_date": str(profile.birth_date),
            "birth_time_known": bool(profile.birth_time),
            "gender_shared": profile.gender,
        },
        "pillars": pillars,
        "element_counts_stem_and_hidden_stems": saju_data.elements.as_dict(),
        "dominant_elements": saju_data.dominant_elements,
        "lacking_elements": saju_data.lacking_elements,
        "calculation_notes": saju_data.calculation_notes,
        "engine_metrics_snapshot": calculation_metrics,
        "interpretation_signals_by_section": interpretation_signals,
        "hints": (
            "day_master_element is canonical element of day stem for ten-gods style reasoning; "
            "day_master_strength is strong | weak | balanced (support vs drain counter)."
        ),
    }
    if saju_data.chart_digest is not None:
        payload["traditional_chart"] = saju_data.chart_digest.model_dump()
        payload["traditional_chart_plain_ko"] = summarize_digest_for_prompt(saju_data.chart_digest)
    return payload


def _parse_json_response(content: str) -> InitialReadingLLMOutput:
    match = _JSON_OBJECT_RE.search(content.strip())
    if not match:
        raise ValueError("No JSON object in model response")
    return InitialReadingLLMOutput.model_validate_json(match.group())


def _fallback_copy(
    profile: PersonProfile,
    saju_data: SajuData,
    signals_by_section: dict[str, list[str]],
) -> InitialReadingLLMOutput:
    name = profile.display_name or "You"
    trad_open: list[str] = []
    if saju_data.chart_digest:
        d = saju_data.chart_digest
        hanja_kv = "; ".join(f"{k}:{v}" for k, v in sorted(d.pillars_hanja.items()))
        trad_open.append(
            f"네 기둥(한자) {hanja_kv}. 일간 {d.day_stem_oheng_ko}, 일주 {d.ilju_ganji_hangul} "
            f"({d.ilju_branch_animal_ko} 띠에 해당하는 일지)."
        )
        if d.day_master_strength_ko:
            trad_open.append(f"(일간 강약 참고: {d.day_master_strength_ko}.)")

    ko_signal_lines: list[str] = []
    if saju_data.chart_digest and saju_data.chart_digest.signals_ko:
        for sec, glosses in saju_data.chart_digest.signals_ko.items():
            for g in glosses[:4]:
                ko_signal_lines.append(f"[{sec}] {g}")

    parts: list[str] = []
    for section in ("personality", "career", "love", "wealth", "cautions"):
        hits = signals_by_section.get(section, [])
        if hits:
            readable = "; ".join(h.replace("_", " ") for h in hits[:8])
            parts.append(f"[{section}] {readable}")

    joined_signals = ". ".join(parts) if parts else ""
    ko_block = (" " + " ".join(ko_signal_lines)) if ko_signal_lines else ""
    if ko_block and joined_signals:
        joined = f"{joined_signals}.{ko_block}"
    elif ko_block:
        joined = ko_block.strip()
    else:
        joined = joined_signals if joined_signals else "Chart signals are understated; clarify in follow-up."

    trad_prefix = (" ".join(trad_open) + " ") if trad_open else ""

    verdict = (
        f"{name}," if profile.display_name else "You,"
    ) + (
        " lean into rhythms that honor both your strengths and blind spots signaled by the pillars."
    )
    return InitialReadingLLMOutput(
        assistant_message=(
            trad_prefix
            + f"Based on your elemental emphasis ({', '.join(saju_data.dominant_elements)} most visible), "
            + (f"rule-based signals flagged: {joined}. " if joined else "")
            + "Ask me anything you want to go deeper — love timing, compatibility, career flow, "
            "or today's emotional weather."
        ),
        overall_summary=(
            "A nuanced chart with patterned emphasis from the elemental distribution "
            "(see dominant vs lacking elements)."
        ),
        keywords=[k for k in saju_data.core_keywords][:3],
        personality=joined,
        relationship_style=joined,
        career_style=joined,
        emotional_pattern=joined,
        strengths=saju_data.strengths[:3] or ["earnestness", "self-awareness", "willingness to reflect"],
        cautions=saju_data.cautions[:3] or ["rush-to-close loops", "self-pressure", "over-analysis"],
        one_line_verdict=verdict,
    )


def generate_initial_counseling_copy(
    settings: Settings,
    profile: PersonProfile,
    saju_data: SajuData,
) -> tuple[InitialReadingLLMOutput, str]:
    """LLM 또는 폴백으로 `InitialReadingLLMOutput` 을 준비한다.

    두 번째 값은 상태 라벨: ``llm_ok`` | ``fallback_no_credentials`` | ``fallback_llm_failed``.
    """

    calculation_metrics = saju_data.calculation_metrics or {}
    signals_by_section = saju_data.interpretation_signals or {}

    if not settings.clod_api_key or not settings.clod_base_url or not settings.clod_strong_model:
        return (
            _fallback_copy(profile, saju_data, signals_by_section),
            "fallback_no_credentials",
        )

    def _chat_url(base_url: str) -> str:
        base = base_url.rstrip("/")
        return f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"

    url = _chat_url(settings.clod_base_url)

    user_prompt = json.dumps(
        _payload_for_llm(profile, saju_data, calculation_metrics, signals_by_section),
        ensure_ascii=False,
    )

    body = {
        "model": settings.clod_strong_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Chart JSON follows. Produce the counselor JSON described.\n" + user_prompt,
            },
        ],
        "temperature": 0.65,
        "max_tokens": 1800,
    }

    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, json=body, headers=headers, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]["content"]
        return _parse_json_response(choice), "llm_ok"
    except (httpx.HTTPError, KeyError, ValueError, ValidationError, json.JSONDecodeError):
        return (
            _fallback_copy(profile, saju_data, signals_by_section),
            "fallback_llm_failed",
        )
