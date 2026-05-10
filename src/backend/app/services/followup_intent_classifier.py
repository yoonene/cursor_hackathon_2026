"""Route follow-up user text to general vs deterministic saju tools."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import Settings
from app.schemas.followup_intent import ClassifiedFollowUpIntent
from app.schemas.fortune import ActionType, FortunePeriod, TimingDomain

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")

_INTENT_SYSTEM = """You route one user message for a Four Pillars (saju) counselor API.

Choose exactly one `route`:
- general — greetings, thanks, vague chat, or questions already answered by prior context with no new reading type.
- domain_fortune — luck/flow for a life area (love career money relationships health overall) over a time window; user is NOT asking which calendar day to act.
- favorable_timing — WHEN to do something: best day/window, scheduling, confession timing, interview timing, moving, investment timing, opening a sensitive conversation.
- compatibility — 두 사람 맞춤/궁합/partner synergy; needs counterpart birth facts if absent. Also use for **relationship fit**, “저랑 어울릴까/잘 맞을까”, “썸/상대/연인 과 잘 맞는지?” without asking *when to act*.
- **Do NOT** choose `general` when the user is clearly asking whether they fit with a named or implied counterpart (연애 관계 장문 조언 금지; 먼저 상대 정보가 필요하면 `compatibility`).

Enums (use spelled literals only):
FortuneDomain: love | career | money | relationships | health | overall
FortunePeriod: today | this_week | this_month | current_phase
TimingDomain: love | career | money | relationships | health | general
ActionType: confession | job_change | interview | important_conversation | investment_decision | move | start_something | end_something | other

If route is compatibility and the message states a counterpart birth date, set partner_birth_date as "YYYY-MM-DD". Otherwise null.
Optional partner_name if clearly stated.

Default when unsure: general.

Return JSON ONLY with keys:
route, fortune_domain, fortune_period, timing_domain, action_type, partner_birth_date, partner_name
(use null where not applicable).
"""


def _chat_url(settings: Settings) -> str | None:
    base = settings.clod_base_url
    if not base:
        return None
    b = base.rstrip("/")
    return f"{b}/chat/completions" if b.endswith("/v1") else f"{b}/v1/chat/completions"


def _llm_classify(settings: Settings, message: str) -> ClassifiedFollowUpIntent | None:
    if not settings.clod_api_key or not settings.clod_base_url:
        return None
    model = settings.clod_fast_model or settings.clod_strong_model
    if not model:
        return None
    url = _chat_url(settings)
    if url is None:
        return None
    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": _INTENT_SYSTEM},
            {"role": "user", "content": f"LATEST USER MESSAGE:\n{message}"},
        ],
        "temperature": 0.0,
        "max_tokens": 400,
    }
    headers = {
        "Authorization": f"Bearer {settings.clod_api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=45.0)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        match = _JSON_OBJECT_RE.search(str(raw).strip())
        if not match:
            return None
        return ClassifiedFollowUpIntent.model_validate_json(match.group())
    except (
        httpx.HTTPError,
        KeyError,
        IndexError,
        ValidationError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
    ):
        return None


def _detect_period(msg_lower: str) -> FortunePeriod:
    if any(k in msg_lower for k in ("오늘", "today")):
        return "today"
    if any(k in msg_lower for k in ("이번 주", "금주", "this week", "요즘")):
        return "this_week"
    if any(k in msg_lower for k in ("이번 달", "this month", "한 달")):
        return "this_month"
    if any(k in msg_lower for k in ("지금", "phase", "흐름")):
        return "current_phase"
    return "this_week"


def _infer_timing_action(msg_lower: str) -> tuple[TimingDomain, ActionType]:
    if any(k in msg_lower for k in ("고백", "confess", "썸")):
        return "love", "confession"
    if any(k in msg_lower for k in ("면접", "interview")):
        return "career", "interview"
    if any(k in msg_lower for k in ("이직", "job change", "퇴사")):
        return "career", "job_change"
    if any(k in msg_lower for k in ("투자", "investment")):
        return "money", "investment_decision"
    if any(k in msg_lower for k in ("이사", "move", "이동")):
        return "general", "move"
    if any(k in msg_lower for k in ("시작", "start something")):
        return "general", "start_something"
    if any(k in msg_lower for k in ("정리", "끊", "end something")):
        return "general", "end_something"
    if any(k in msg_lower for k in ("중요한 대화", "difficult conversation", "솔직히")):
        return "relationships", "important_conversation"
    if any(k in msg_lower for k in ("연애", "love", "romance")):
        return "love", "confession"
    return "general", "other"


def _keyword_signals_compatibility(message: str) -> bool:
    t = message
    tl = t.lower()
    if "궁합" in t or "compatibility" in tl:
        return True

    counterpart = any(
        p in t
        for p in (
            "상대",
            "연인",
            "썸",
            "애인",
            "남친",
            "여친",
            "좋아하는 사람",
            "이 사람",
            "그 사람",
            "저 사람",
        )
    )
    fit_query = (
        ("잘 맞" in t)
        or ("어울" in t and "까" in t)
        or ("맞을까" in t)
        or ("성향 맞" in t)
        or ("찰떡" in t)
    )

    return bool(counterpart and fit_query)


def classify_follow_up_intent_keywords(message: str) -> ClassifiedFollowUpIntent:
    """Deterministic routing when LLM is unavailable or fails."""
    text = message.strip()
    lower = text.lower()

    timing_cue = any(
        k in text
        for k in (
            "언제",
            "좋은 날",
            "날짜",
            "타이밍",
            "추천",
            "며칠",
        )
    ) or any(
        k in lower
        for k in (
            "when should",
            "best day",
            "best time",
            "what day",
            "timing",
        )
    )

    if timing_cue or any(k in lower for k in ("고백", "confess")):
        td, at = _infer_timing_action(lower)
        return ClassifiedFollowUpIntent(route="favorable_timing", timing_domain=td, action_type=at)

    if _keyword_signals_compatibility(text):
        return ClassifiedFollowUpIntent(route="compatibility")

    if any(k in text for k in ("연애운",)) or "love fortune" in lower or "romance luck" in lower:
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="love",
            fortune_period=_detect_period(lower),
        )
    if any(k in text for k in ("직업운", "커리어")) or "career" in lower and "flow" in lower:
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="career",
            fortune_period=_detect_period(lower),
        )
    if any(k in text for k in ("금전", "재물운", "돈")) or "money" in lower:
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="money",
            fortune_period=_detect_period(lower),
        )
    if "건강" in text or "health" in lower:
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="health",
            fortune_period=_detect_period(lower),
        )
    if any(k in text for k in ("인간관계", "사람들")):
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="relationships",
            fortune_period=_detect_period(lower),
        )

    if "운" in text and any(k in text for k in ("어때", "알려", "봐줘")):
        return ClassifiedFollowUpIntent(
            route="domain_fortune",
            fortune_domain="overall",
            fortune_period=_detect_period(lower),
        )

    return ClassifiedFollowUpIntent(route="general")


def normalize_classified_intent(intent: ClassifiedFollowUpIntent) -> ClassifiedFollowUpIntent:
    """Fill required enum fields for tool runners."""
    if intent.route == "domain_fortune":
        return intent.model_copy(
            update={
                "fortune_domain": intent.fortune_domain or "overall",
                "fortune_period": intent.fortune_period or "this_week",
            },
        )
    if intent.route == "favorable_timing":
        return intent.model_copy(
            update={
                "timing_domain": intent.timing_domain or "general",
                "action_type": intent.action_type or "other",
            },
        )
    return intent


def classify_follow_up_intent(settings: Settings, user_message: str) -> ClassifiedFollowUpIntent:
    msg = user_message.strip()
    if not msg:
        return ClassifiedFollowUpIntent(route="general")
    llm = _llm_classify(settings, msg)
    if llm is not None:
        return normalize_classified_intent(llm)
    return normalize_classified_intent(classify_follow_up_intent_keywords(msg))
