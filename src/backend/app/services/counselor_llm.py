"""CLōD / OpenAI 호환 Chat Completions로 초기 리딩 문구 생성."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.counselor_llm import InitialReadingLLMOutput
from app.schemas.profiles import PersonProfile
from app.schemas.saju import SajuData
from app.schemas.state import ConversationState
from app.saju.trad_chart_digest import summarize_digest_for_prompt


_SYSTEM_PROMPT = """You are a warm, articulate saju (Four Pillars) counselor speaking in polished English.

You NEVER invent raw chart facts that contradict the provided JSON snapshot. Interpret and narrate ONLY from:
- lunar-accurate pillars and scores
- the deterministic interpretation_signals (these are factual rule hits, not fluff)
- optional `traditional_chart`: Hanja pillar pairs plus English labels (day stem, romanized day pillar, branch animal) and `signals_gloss_en`

When `traditional_chart` / `traditional_chart_plain_en` is present, ground your prose in those facts (Hanja pillars are allowed as-is). All user-visible coaching copy must remain in English.

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
        payload["traditional_chart_plain_en"] = summarize_digest_for_prompt(saju_data.chart_digest)
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
        hanja_kv = "; ".join(f"{k}: {v}" for k, v in sorted(d.pillars_hanja.items()))
        trad_open.append(
            f"Four pillars (Hanja): {hanja_kv}. Day stem: {d.day_stem_label_en}; "
            f"day pillar (romanized): {d.day_pillar_reading_en}; day-branch animal: {d.day_branch_animal_label}."
        )
        if d.day_master_strength_en:
            trad_open.append(f"(Day-master strength: {d.day_master_strength_en})")

    en_signal_lines: list[str] = []
    if saju_data.chart_digest and saju_data.chart_digest.signals_gloss_en:
        for sec, glosses in saju_data.chart_digest.signals_gloss_en.items():
            for g in glosses[:4]:
                en_signal_lines.append(f"[{sec}] {g}")

    parts: list[str] = []
    for section in ("personality", "career", "love", "wealth", "cautions"):
        hits = signals_by_section.get(section, [])
        if hits:
            readable = "; ".join(h.replace("_", " ") for h in hits[:8])
            parts.append(f"[{section}] {readable}")

    joined_signals = ". ".join(parts) if parts else ""
    gloss_block = (" " + " ".join(en_signal_lines)) if en_signal_lines else ""
    if gloss_block and joined_signals:
        joined = f"{joined_signals}.{gloss_block}"
    elif gloss_block:
        joined = gloss_block.strip()
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


_FOLLOWUP_SYSTEM = """You are a warm, articulate Four Pillars (saju) counselor continuing an ongoing chat in polished English only.

Hard rules:
- Never contradict deterministic chart facts supplied in CHART FACTS SNAPSHOT below (pillars, element counts, chart_identity).
- Interpretation signals are factual rule-engine hits—not suggestions to ignore silently.
- If the user asks something not answered by supplied data, say so plainly and invite them to clarify.
- Prefer concise, practical replies (typically 2–6 short paragraphs) unless they ask for depth.

Output plain assistant prose only — no markdown code fences or JSON blobs."""


def _partner_intake_addon(supplemental_context: str | None) -> str:
    """When JSON tool payloads ask for counterpart birth data — short polite Korean replies."""
    if not supplemental_context:
        return ""
    try:
        blob = json.loads(supplemental_context)
    except json.JSONDecodeError:
        return ""
    tool = blob.get("tool")

    overrides = (
        "\nLANGUAGE OVERRIDE FOR THIS MESSAGE ONLY:\n"
        "- Write in polite Korean regardless of instructions above mentioning English.\n"
        "- No markdown. At most four short sentences (no headings, no bullets).\n"
        "- Do NOT give long chart-deep interpretation limited to only the querent.\n\n"
        "TASK:\n"
    )

    if tool == "compatibility_pending":
        reopen = blob.get("re_prompt_ui")
        reopen_line = (
            "- 사용자가 입력 팝업/폼 다시 표시를 요청한 경우에는, 그 의도를 짧게 수긍합니다.\n"
            if reopen
            else ""
        )
        return overrides + reopen_line + (
            "- The user asks about fit/compatibility.\n"
            "- Say plainly that 두 사람 원국을 비교하려면 상대의 생년월일이 필요하다.\n"
            "- 이름·별명은 선택이라고 안내하고, 생년월일 입력을 부드럽게 요청한다.\n"
            "- 형식 안내 한 문장: YYYY-MM-DD 또는 yyyy년 m월 d일.\n"
        )

    if tool == "compatibility_collect" and not blob.get("parsed_birth_date"):
        return overrides + "- Birth date 아직 확인되지 않았어요. 같은 형식으로 다시 적어달라 간단히 안내합니다.\n"

    if tool == "analyze_compatibility":
        return (
            "\nLANGUAGE OVERRIDE FOR THIS MESSAGE ONLY:\n"
            "- Write in polite Korean.\n"
            "- Stay strictly grounded in the compatibility JSON (+ counterpart_element_emphasis / "
            "counterpart_profile_for_llm entries if present).\n"
            "- Do NOT ask for birthplace, country, timezone, or city correction — unsupported in this pipeline.\n"
            "- counterpart birth time is OPTIONAL: if `birth_time_known`/`hour_pillar_known` indicates unknown, "
            "do NOT insist on 시간·장소 입력; 간단히 '시까지 알면 더 정밀하지만 현재 결과는 생년월일 기준 원국입니다' 같은 한 문장으로만 언급하거나 생략해도 된다.\n"
            "- Do NOT invent zodiac-year-only animal stories beyond the deterministic JSON snapshots.\n"
            "- Keep it modest (typically 3–7 short sentences), practical, compassionate.\n\n"
            "TASK: Summarize the deterministic compatibility snapshot for the user conversationally.\n"
        )

    return ""


def _chat_url(settings: Settings) -> str:
    base = settings.clod_base_url or ""
    base = base.rstrip("/")
    return f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"


def _chart_facts_compact(state: ConversationState) -> str:
    ud = state.user_saju
    rp = state.saju_report
    parts: list[str] = [
        json.dumps(ud.elements.as_dict(), ensure_ascii=False),
        f"dominant: {ud.dominant_elements}; lacking: {ud.lacking_elements}",
        f"interpretation_signals: {json.dumps(ud.interpretation_signals, ensure_ascii=False)}",
    ]
    if rp.chart_identity is not None:
        parts.append("chart_identity: " + rp.chart_identity.model_dump_json(exclude_none=True))
    parts.append(rp.one_line_verdict)
    parts.append(rp.overall_summary[:2400])
    return "\n".join(parts)


def _fallback_followup(state: ConversationState) -> tuple[str, str]:
    dn = state.user_profile.display_name or "You"
    dom = ", ".join(state.user_saju.dominant_elements)
    return (
        f"{dn}, I’m running without an active language-model connection from the server config. "
        f"Using your snapshot, {dom.capitalize()} energies still headline the dialogue. "
        "Tell me what you’d like to unpack—timing, partnerships, career emphasis, emotional patterns—and we can build on that.",
        "fallback_no_credentials",
    )


def _followup_fallback_text(state: ConversationState, supplemental_context: str | None) -> tuple[str, str]:
    fb, tag = _fallback_followup(state)
    if supplemental_context:
        return (
            fb
            + "\n\n"
            + "Engine note (prepared for you; integrate if relevant):\n"
            + supplemental_context[:1800],
            tag,
        )
    return fb, tag


def _build_follow_up_chat_messages(state: ConversationState, supplemental_context: str | None) -> list[dict[str, str]]:
    snapshot = "CHART FACTS SNAPSHOT (authoritative):\n" + _chart_facts_compact(state)
    if supplemental_context:
        snapshot += (
            "\n\nTOOL / READING OUTPUT (ground your reply in these facts; do not contradict scores):\n"
            + supplemental_context[:8000]
        )
    turns: list[dict[str, str]] = []
    for m in state.messages:
        if m.role not in ("user", "assistant"):
            continue
        turns.append({"role": m.role, "content": m.content})
    tail = turns[-24:] if len(turns) > 24 else turns

    system_block = _FOLLOWUP_SYSTEM + "\n\n" + snapshot + _partner_intake_addon(supplemental_context)
    messages: list[dict[str, str]] = [{"role": "system", "content": system_block}]
    messages.extend(tail)
    return messages


def generate_followup_counseling_reply(
    settings: Settings,
    state: ConversationState,
    *,
    supplemental_context: str | None = None,
) -> tuple[str, str]:
    """Follow-up conversational turn via CLōD / OpenAI-style chat completions (plain text)."""

    if not settings.clod_api_key or not settings.clod_base_url or not settings.clod_strong_model:
        return _followup_fallback_text(state, supplemental_context)

    url = _chat_url(settings)
    messages = _build_follow_up_chat_messages(state, supplemental_context)

    body = {
        "model": settings.clod_strong_model,
        "messages": messages,
        "temperature": 0.55,
        "max_tokens": 1200,
    }
    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, json=body, headers=headers, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("empty assistant content")
        return text, "llm_ok"
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        fb, lab = _fallback_followup(state)
        if supplemental_context:
            return (
                fb
                + "\n\n"
                + "Engine note (deterministic):\n"
                + supplemental_context[:1800],
                "fallback_llm_failed",
            )
        return fb, lab


def _sse_openai_collect_delta(line_suffix: str) -> str | None:
    """Return text fragment from one `data: {...}` SSE line body, if any."""
    if line_suffix.strip() == "[DONE]":
        return None
    try:
        blob = json.loads(line_suffix)
    except json.JSONDecodeError:
        return None
    choices = blob.get("choices")
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    content = delta.get("content") or ""
    return content if content else None


async def stream_follow_up_counselor_text(
    settings: Settings,
    state: ConversationState,
    *,
    supplemental_context: str | None = None,
) -> AsyncIterator[tuple[str, str]]:
    """Yield ``("delta", text)`` fragments, then a single ``("end", llm_tag)``.

    Mirrors :func:`generate_followup_counseling_reply` tagging; fallback emits one bundled ``delta``.
    """

    if not settings.clod_api_key or not settings.clod_base_url or not settings.clod_strong_model:
        fb, tag = _followup_fallback_text(state, supplemental_context)
        yield "delta", fb
        yield "end", tag
        return

    url = _chat_url(settings)
    messages = _build_follow_up_chat_messages(state, supplemental_context)
    body = {
        "model": settings.clod_strong_model,
        "messages": messages,
        "temperature": 0.55,
        "max_tokens": 1200,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }

    aggregated = ""
    try:
        timeout = httpx.Timeout(120.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=body, headers=headers) as response:
                response.raise_for_status()
                async for raw_line in response.aiter_lines():
                    if not raw_line.startswith("data: "):
                        continue
                    payload = raw_line.removeprefix("data: ").strip()
                    if payload == "[DONE]":
                        break
                    frag = _sse_openai_collect_delta(payload)
                    if frag:
                        aggregated += frag
                        yield "delta", frag
        final_text = aggregated.strip()
        if not final_text:
            raise ValueError("empty streamed assistant content")
        yield "end", "llm_ok"
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError):
        fb, lab = _fallback_followup(state)
        if supplemental_context:
            fb = fb + "\n\nEngine note (deterministic):\n" + supplemental_context[:1800]
            yield "delta", fb
            yield "end", "fallback_llm_failed"
        else:
            yield "delta", fb
            yield "end", lab
