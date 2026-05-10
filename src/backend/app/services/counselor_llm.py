"""CLōD / OpenAI 호환 Chat Completions로 초기 리딩 문구 생성."""

from __future__ import annotations

import json
import logging
import re
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx
from pydantic import ValidationError

logger = logging.getLogger("counselor_llm")

from app.core.config import Settings
from app.schemas.counselor_llm import InitialReadingLLMOutput
from app.schemas.profiles import PersonProfile
from app.schemas.saju import SajuData
from app.schemas.state import ConversationState
from app.saju.trad_chart_digest import summarize_digest_for_prompt


_SYSTEM_PROMPT = """You are a warm, gifted saju (Four Pillars of Destiny) counselor speaking in friendly, accessible English.

Your goal: make someone who has never heard of saju feel genuinely seen and understood.

STRICT RULES:
- NEVER contradict the deterministic chart facts in the JSON (pillars, element counts, signals).
- NEVER use raw Hanja/Chinese characters, romanized technical stems (e.g. "Xin", "Ren"), or jargon like "day master", "branches", "ganzhi" in the assistant_message or any user-facing copy.
- DO use the plain-English labels provided: animal names (Rabbit, Dog, Tiger…), element names (Fire, Water, Wood, Metal, Earth), and polarity (Yin/Yang) naturally woven into prose.
- Ground every claim in the supplied data (interpretation_signals, element counts, chart_identity).

assistant_message FORMAT — write it in this exact narrative flow, using markdown headers:

**Your Chart Identity**
Open with one warm sentence naming the day-pillar animal and element colour in plain English, e.g.  
"You were born under the sign of the White Rabbit — a Yin Metal soul whose quiet elegance runs far deeper than it first appears."
Then 1–2 sentences on what that energy archetype generally means.

**Personality**
2–3 sentences drawn from dominant elements and personality signals. Speak directly to the person ("You…"). No bullet lists — flowing prose.

**Career & Purpose**
2–3 sentences on career strengths, drive, and ideal working style sourced from career signals. Practical, grounded.

**Love & Relationships**
2–3 sentences on how this person loves, connects, and what they need in relationships. Warm, honest.

**Health & Energy**
1–2 sentences on physical/emotional tendencies and self-care rhythms tied to element balance.

**Your Guiding Rhythm**
One closing sentence — poetic but concrete — about the conditions under which this person thrives.

Each section should flow naturally. Avoid bullet lists inside assistant_message. Total length: 250–420 words.

Return a single JSON object with exactly these keys (string/list types):

{
  "assistant_message": "<full structured reading in markdown as described above>",
  "overall_summary": "one compact paragraph headline for the dashboard (no Hanja, plain English)",
  "keywords": ["three core trait chips, lowercase hyphenated okay"],
  "personality": "one paragraph for Personality section (plain English, no jargon)",
  "relationship_style": "one paragraph for Relationship Style section",
  "career_style": "one paragraph for Career Style section",
  "emotional_pattern": "one paragraph for Emotional Pattern section",
  "strengths": ["bullet", "bullet", "bullet"],
  "cautions": ["bullet", "bullet", "bullet"],
  "one_line_verdict": "single memorable coaching line under 220 characters (no Hanja)"
}

No markdown fences. Output JSON only."""

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")

_AMSG_KEY = '"assistant_message"'


class _AssistantMessageExtractor:
    """LLM이 스트리밍으로 내보내는 JSON에서 assistant_message 필드 값을 실시간 추출한다."""

    SEEK_KEY = 0
    SEEK_COLON = 1
    SEEK_QUOTE = 2
    IN_VALUE = 3
    DONE = 4

    def __init__(self) -> None:
        self._buf = ""
        self._state = self.SEEK_KEY
        self._pos = 0

    def feed(self, chunk: str) -> str:
        """새 청크를 받아 assistant_message 값 중 이번에 드러난 부분을 반환한다."""
        if self._state == self.DONE:
            return ""
        self._buf += chunk
        return self._scan()

    def _scan(self) -> str:
        result: list[str] = []
        buf = self._buf
        i = self._pos

        if self._state == self.SEEK_KEY:
            idx = buf.find(_AMSG_KEY, i)
            if idx < 0:
                self._pos = max(0, len(buf) - len(_AMSG_KEY))
                return ""
            i = idx + len(_AMSG_KEY)
            self._state = self.SEEK_COLON

        if self._state == self.SEEK_COLON:
            while i < len(buf):
                if buf[i] == ":":
                    i += 1
                    self._state = self.SEEK_QUOTE
                    break
                i += 1
            else:
                self._pos = i
                return ""

        if self._state == self.SEEK_QUOTE:
            while i < len(buf):
                if buf[i] == '"':
                    i += 1
                    self._state = self.IN_VALUE
                    break
                i += 1
            else:
                self._pos = i
                return ""

        if self._state == self.IN_VALUE:
            while i < len(buf):
                c = buf[i]
                if c == "\\" and i + 1 < len(buf):
                    nc = buf[i + 1]
                    if nc == "n":
                        result.append("\n")
                    elif nc == "t":
                        result.append("\t")
                    elif nc == '"':
                        result.append('"')
                    elif nc == "\\":
                        result.append("\\")
                    elif nc == "r":
                        result.append("\r")
                    else:
                        result.append("\\")
                        result.append(nc)
                    i += 2
                    continue
                if c == '"':
                    self._state = self.DONE
                    self._pos = i + 1
                    break
                result.append(c)
                i += 1
            else:
                self._pos = i

        return "".join(result)


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
    if saju_data.chart_identity is not None:
        ci = saju_data.chart_identity
        payload["chart_identity_plain_en"] = {
            "day_pillar_english_name": ci.day_pillar.english_name,
            "day_pillar_animal": ci.day_pillar.animal_label,
            "day_pillar_color": ci.day_pillar.color,
            "day_master_element": ci.day_master.element_label,
            "day_master_polarity": ci.day_master.polarity,
            "day_master_label": ci.day_master.english_name,
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

    identity_intro = ""
    if saju_data.chart_identity:
        ci = saju_data.chart_identity
        animal = ci.day_pillar.animal_label
        pillar_name = ci.day_pillar.english_name
        dm_label = ci.day_master.english_name
        identity_intro = (
            f"**Your Chart Identity**\n"
            f"You were born under the sign of the {pillar_name} — "
            f"a {dm_label} soul with the spirit of the {animal}.\n\n"
        )

    dominant = ", ".join(e.capitalize() for e in saju_data.dominant_elements) or "a balanced mix of elements"
    lacking = ", ".join(e.capitalize() for e in saju_data.lacking_elements) if saju_data.lacking_elements else None

    personality_signals = "; ".join(
        h.replace("_", " ") for h in signals_by_section.get("personality", [])[:4]
    )
    career_signals = "; ".join(
        h.replace("_", " ") for h in signals_by_section.get("career", [])[:4]
    )
    love_signals = "; ".join(
        h.replace("_", " ") for h in signals_by_section.get("love", [])[:4]
    )

    personality_para = (
        f"**Personality**\n"
        f"Your chart is led by {dominant} energy"
        + (f", with {lacking} asking for more room and care" if lacking else "")
        + (f". Patterns in your chart suggest: {personality_signals}." if personality_signals else ".")
        + "\n\n"
    )
    career_para = (
        f"**Career & Purpose**\n"
        + (f"Your career signals point to: {career_signals}." if career_signals else
           f"Your {dominant} nature brings drive and focus to your professional path.")
        + "\n\n"
    )
    love_para = (
        f"**Love & Relationships**\n"
        + (f"In relationships, your chart highlights: {love_signals}." if love_signals else
           f"Your {dominant} energy shapes how you connect and what you seek in others.")
        + "\n\n"
    )
    health_para = (
        f"**Health & Energy**\n"
        f"Tending to your {(saju_data.lacking_elements[0].capitalize() + ' element') if saju_data.lacking_elements else 'inner balance'} "
        f"is key to keeping your energy steady.\n\n"
    )
    closing = (
        f"**Your Guiding Rhythm**\n"
        f"You thrive when you honor both the strengths your chart gives you and the gaps it asks you to fill.\n"
    )

    assistant_message = identity_intro + personality_para + career_para + love_para + health_para + closing
    assistant_message += "\nAsk me anything to go deeper — love timing, compatibility, career flow, or today's emotional weather."

    verdict = (
        (f"{name}, " if profile.display_name else "You, ")
        + "lean into rhythms that honor both your strengths and the balance your chart is asking for."
    )
    return InitialReadingLLMOutput(
        assistant_message=assistant_message,
        overall_summary=(
            f"A chart led by {dominant} energy"
            + (f", with {lacking} as the area calling for more attention" if lacking else "")
            + "."
        ),
        keywords=[k for k in saju_data.core_keywords][:3],
        personality=personality_para.replace("**Personality**\n", "").strip(),
        relationship_style=love_para.replace("**Love & Relationships**\n", "").strip(),
        career_style=career_para.replace("**Career & Purpose**\n", "").strip(),
        emotional_pattern=health_para.replace("**Health & Energy**\n", "").strip(),
        strengths=saju_data.strengths[:3] or ["earnestness", "self-awareness", "willingness to reflect"],
        cautions=saju_data.cautions[:3] or ["rushing to conclusions", "self-pressure", "over-analysis"],
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
        logger.warning("initial reading fallback — reason=no_credentials")
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
        "max_tokens": 2400,
    }

    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }

    logger.debug("initial reading LLM call — url=%s model=%s max_tokens=2400", url, settings.clod_strong_model)
    t0 = time.perf_counter()
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]["content"]
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.info("initial reading LLM ok — model=%s duration_ms=%d", settings.clod_strong_model, duration_ms)
        return _parse_json_response(choice), "llm_ok"
    except (httpx.HTTPError, KeyError, ValueError, ValidationError, json.JSONDecodeError) as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.error(
            "initial reading LLM failed — %s: %s (duration_ms=%d)",
            type(exc).__name__,
            exc,
            duration_ms,
        )
        logger.warning("initial reading fallback — reason=llm_failed")
        return (
            _fallback_copy(profile, saju_data, signals_by_section),
            "fallback_llm_failed",
        )


async def stream_initial_counseling_copy(
    settings: Settings,
    profile: PersonProfile,
    saju_data: SajuData,
) -> AsyncIterator[tuple[str, Any]]:
    """초기 리딩을 SSE 스트리밍으로 생성한다.

    Yields:
        ``("delta", str)``           — assistant_message 텍스트 조각
        ``("result", output, tag)``  — 최종 파싱 결과 (llm_ok | fallback_*)
    """
    calculation_metrics = saju_data.calculation_metrics or {}
    signals_by_section = saju_data.interpretation_signals or {}

    if not settings.clod_api_key or not settings.clod_base_url or not settings.clod_strong_model:
        logger.warning("initial reading stream fallback — reason=no_credentials")
        yield "result", _fallback_copy(profile, saju_data, signals_by_section), "fallback_no_credentials"
        return

    def _chat_url_inner(base_url: str) -> str:
        base = base_url.rstrip("/")
        return f"{base}/chat/completions" if base.endswith("/v1") else f"{base}/v1/chat/completions"

    url = _chat_url_inner(settings.clod_base_url)
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
        "max_tokens": 2400,
        "stream": True,
    }
    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }

    logger.debug("initial reading stream LLM call — url=%s model=%s", url, settings.clod_strong_model)
    t0 = time.perf_counter()
    full_text = ""
    extractor = _AssistantMessageExtractor()

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
                        full_text += frag
                        delta = extractor.feed(frag)
                        if delta:
                            yield "delta", delta

        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "initial reading stream LLM ok — model=%s duration_ms=%d",
            settings.clod_strong_model,
            duration_ms,
        )
        try:
            result = _parse_json_response(full_text)
            yield "result", result, "llm_ok"
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            logger.error("initial reading stream JSON parse failed — %s: %s", type(exc).__name__, exc)
            yield "result", _fallback_copy(profile, saju_data, signals_by_section), "fallback_llm_failed"

    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.error(
            "initial reading stream LLM failed — %s: %s (duration_ms=%d)",
            type(exc).__name__,
            exc,
            duration_ms,
        )
        yield "result", _fallback_copy(profile, saju_data, signals_by_section), "fallback_llm_failed"


_FOLLOWUP_SYSTEM = """You are a warm, articulate Four Pillars (saju) counselor continuing an ongoing chat in polished English only.

Hard rules:
- Never contradict deterministic chart facts supplied in CHART FACTS SNAPSHOT below (pillars, element counts, chart_identity).
- Interpretation signals are factual rule-engine hits—not suggestions to ignore silently.
- If the user asks something not answered by supplied data, say so plainly and invite them to clarify.
- Prefer concise, practical replies (typically 2–6 short paragraphs) unless they ask for depth.

Output plain assistant prose only — no markdown code fences or JSON blobs."""


def _partner_intake_addon(supplemental_context: str | None) -> str:
    """When JSON tool payloads ask for counterpart birth data — always reply in English."""
    if not supplemental_context:
        return ""
    try:
        blob = json.loads(supplemental_context)
    except json.JSONDecodeError:
        return ""
    tool = blob.get("tool")

    overrides = (
        "\nLANGUAGE: English only — no Korean, no matter what.\n"
        "- No markdown. At most four short sentences (no headings, no bullets).\n"
        "- Do NOT give long chart-deep interpretation limited to only the querent.\n\n"
        "TASK:\n"
    )

    if tool == "compatibility_pending":
        reopen = blob.get("re_prompt_ui")
        reopen_line = (
            "- The user requested the input form again; briefly acknowledge that.\n"
            if reopen
            else ""
        )
        return overrides + reopen_line + (
            "- The user is asking about compatibility.\n"
            "- Respond in ONE short sentence inviting them to enter the other person's info via the form that just appeared.\n"
            "- Do NOT mention date formats, nicknames, or any instructions — the form handles that.\n"
            "- Keep it warm and brief, like 'Let's check your compatibility! Go ahead and fill in their info.'\n"
        )

    if tool == "compatibility_collect" and not blob.get("parsed_birth_date"):
        return overrides + "- The birth date wasn't recognized. Politely ask them to re-enter it in YYYY-MM-DD format.\n"

    if tool == "analyze_compatibility":
        return (
            "\nLANGUAGE: English only — no Korean, no matter what.\n"
            "- Stay strictly grounded in the compatibility JSON (+ counterpart_element_emphasis / "
            "counterpart_profile_for_llm entries if present).\n"
            "- Do NOT ask for birthplace, country, timezone, or city correction — unsupported in this pipeline.\n"
            "- counterpart birth time is OPTIONAL: if `birth_time_known`/`hour_pillar_known` indicates unknown, "
            "mention in one sentence that more precision is possible with the birth hour, then move on.\n"
            "- Do NOT invent zodiac-year-only animal stories beyond the deterministic JSON snapshots.\n"
            "- Keep it concise (typically 3–7 short sentences), practical, compassionate.\n\n"
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
        logger.warning("follow-up fallback — reason=no_credentials")
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

    logger.debug("follow-up LLM call — url=%s model=%s max_tokens=1200", url, settings.clod_strong_model)
    t0 = time.perf_counter()
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=120.0)
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        if not text:
            raise ValueError("empty assistant content")
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.info("follow-up LLM ok — model=%s duration_ms=%d", settings.clod_strong_model, duration_ms)
        return text, "llm_ok"
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.error(
            "follow-up LLM failed — %s: %s (duration_ms=%d)",
            type(exc).__name__,
            exc,
            duration_ms,
        )
        logger.warning("follow-up fallback — reason=llm_failed")
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
        logger.warning("follow-up stream fallback — reason=no_credentials")
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

    logger.debug("follow-up stream LLM call — url=%s model=%s", url, settings.clod_strong_model)
    t0 = time.perf_counter()
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
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "follow-up stream LLM ok — model=%s duration_ms=%d chars=%d",
            settings.clod_strong_model,
            duration_ms,
            len(final_text),
        )
        yield "end", "llm_ok"
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
        duration_ms = int((time.perf_counter() - t0) * 1000)
        logger.error(
            "follow-up stream LLM failed — %s: %s (duration_ms=%d)",
            type(exc).__name__,
            exc,
            duration_ms,
        )
        logger.warning("follow-up stream fallback — reason=llm_failed")
        fb, lab = _fallback_followup(state)
        if supplemental_context:
            fb = fb + "\n\nEngine note (deterministic):\n" + supplemental_context[:1800]
            yield "delta", fb
            yield "end", "fallback_llm_failed"
        else:
            yield "delta", fb
            yield "end", lab
