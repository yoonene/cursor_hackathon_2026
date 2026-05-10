"""Execute deterministic tools before the follow-up counselor LLM."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, time
from typing import Any

from app.builders.followup_board_updates import (
    attach_compatibility_pending,
    attach_compatibility_result,
    attach_domain_fortune,
    attach_timing,
)
from app.core.config import Settings
from app.schemas.intake import GenderType
from app.schemas.profiles import PersonProfile
from app.schemas.requests import PartnerCompatibilityPayload
from app.schemas.state import ConversationState, PendingToolCall, ToolCallRecord
from app.schemas.view_models import (
    ActiveTemplate,
    AgentTraceStep,
    TabRecommendedEvent,
    TemplateChangedEvent,
    UIEvent,
)
from app.services.date_extract import extract_first_birth_date
from app.services.followup_intent_classifier import classify_follow_up_intent
from app.saju.compatibility import analyze_compatibility
from app.saju.compute_saju import analyze_base_saju
from app.saju.domain_fortune import analyze_domain_fortune
from app.saju.favorable_timing import analyze_favorable_timing


def _slug_id(text: str) -> str:
    raw = text.strip().lower().replace(" ", "_")
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in raw).strip("_")
    return cleaned[:96] if cleaned else "partner"


def _partner_profile(
    session_id: str,
    display_name: str | None,
    birth: date,
    *,
    birth_time: time | None = None,
    gender: GenderType | None = None,
) -> PersonProfile:
    slug = _slug_id(display_name or "partner")
    tail = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in session_id)[-24:]
    tail = tail or "session"
    return PersonProfile(
        id=f"related_{slug}_{tail}",
        display_name=(display_name or "Partner"),
        birth_date=birth,
        birth_time=birth_time,
        gender=gender,
    )


_SIMPLE_NAME_HINT = re.compile(
    r"(?:상대(?:방)?|partner)\s*(?:은|는|의|)?\s*[:：]\s*(?P<name>[\w가-힣]{2,16})",
    re.IGNORECASE,
)


def _extract_partner_hint_name(message: str) -> str | None:
    m = _SIMPLE_NAME_HINT.search(message)
    return m.group("name").strip() if m else None


def _prior_active_template(board) -> ActiveTemplate | None:
    reading = getattr(board, "active_reading", None)
    if reading is None:
        return None
    return getattr(reading, "template", None)


def _ensure_compat_intake_coherence(
    state: ConversationState,
    board,
    traces: list[AgentTraceStep],
) -> None:
    """Keep `pending_tool_call`/`current_stage` aligned with a pending compatibility UI card."""
    reading = getattr(board, "active_reading", None)
    tmpl = getattr(reading, "template", None) if reading is not None else None
    pending = state.pending_tool_call

    semantic_key = "compatibility:user:partner_pending"
    if tmpl == "compatibility_pending" and reading is not None:
        sk = getattr(reading, "semantic_key", None)
        if isinstance(sk, str) and sk.strip():
            semantic_key = sk
        inconsistent = (
            state.current_stage != "collecting_compatibility_info"
            or pending is None
            or pending.tool_name != "analyze_compatibility"
            or getattr(pending, "semantic_key", None) != semantic_key
        )
    elif pending is not None and pending.tool_name == "analyze_compatibility":
        if pending.semantic_key:
            semantic_key = pending.semantic_key
        inconsistent = state.current_stage != "collecting_compatibility_info"
    else:
        return

    if not inconsistent:
        return

    preserved_inputs: dict[str, Any] = {}
    if pending and pending.collected_inputs:
        preserved_inputs.update(pending.collected_inputs)
    mf: list[str] = ["counterpart_birth_date"]
    if pending is not None and pending.tool_name == "analyze_compatibility" and pending.missing_fields:
        mf = list(pending.missing_fields)

    state.current_stage = "collecting_compatibility_info"
    state.pending_tool_call = PendingToolCall(
        tool_name="analyze_compatibility",
        semantic_key=semantic_key,
        missing_fields=mf,
        collected_inputs=preserved_inputs,
    )
    traces.append(
        AgentTraceStep(
            step="routing",
            label="repair_compatibility_intake_state",
            status="completed",
        ),
    )


def _user_requests_partner_ui_refresh(message: str) -> bool:
    t = message.strip()
    if not t:
        return False
    needles = ("팝업", "다시 입력", "다시 적", "입력창", "입력 창", "양식", "다이얼로그", "다시 열")
    return any(n in t for n in needles)


def _prime_state_for_partner_request(
    state: ConversationState,
    board,
    traces: list[AgentTraceStep],
) -> None:
    """POST `partner`는 항상 궁합 수집 분기에서 소비되어야 한다 (세션/카드 상태가 순간적으로 어긋나도)."""
    pend = state.pending_tool_call
    if (
        state.current_stage == "collecting_compatibility_info"
        and pend is not None
        and pend.tool_name == "analyze_compatibility"
    ):
        return

    semantic_key = "compatibility:user:partner_pending"
    reading = getattr(board, "active_reading", None)
    if reading is not None and getattr(reading, "template", None) == "compatibility_pending":
        sk = getattr(reading, "semantic_key", None)
        if isinstance(sk, str) and sk.strip():
            semantic_key = sk
    elif pend is not None and pend.semantic_key:
        semantic_key = pend.semantic_key

    preserved: dict[str, Any] = {}
    if pend is not None and pend.collected_inputs:
        preserved.update(pend.collected_inputs)

    state.current_stage = "collecting_compatibility_info"
    state.pending_tool_call = PendingToolCall(
        tool_name="analyze_compatibility",
        semantic_key=semantic_key,
        missing_fields=["counterpart_birth_date"],
        collected_inputs=preserved,
    )
    traces.append(
        AgentTraceStep(
            step="routing",
            label="prime_compat_intake_for_partner_payload",
            status="completed",
        ),
    )


def _compat_supplement_with_counterpart_facts(
    supplemental: str, partner_profile: PersonProfile, partner_saju
) -> str:
    """LLM이 상대 시·출생지를 필수처럼 요구하지 않도록 엔진 사실을 명시한다."""
    try:
        blob: dict[str, Any] = json.loads(supplemental)
    except json.JSONDecodeError:
        return supplemental
    blob["counterpart_profile_for_llm_en"] = {
        "birth_date": str(partner_profile.birth_date),
        "birth_time_known": getattr(partner_saju, "birth_time_known", True),
        "display_name": partner_profile.display_name,
    }
    blob["counterpart_element_emphasis_en"] = {
        "day_master": partner_saju.day_master,
        "dominant_elements": partner_saju.dominant_elements,
        "lacking_elements": partner_saju.lacking_elements,
        "hour_pillar_known": partner_saju.hour_pillar is not None,
    }
    blob["deterministic_compat_policy_en"] = (
        "The counterpart saju snapshot was computed with the SAME deterministic engine as intake. "
        "When birth_time_known is false (or hour_pillar_known is false), the hour pillar is intentionally omitted "
        "— comparable to querent minus birth time / default-noon midpoint rules. "
        "Do NOT ask for birthplace, country, timezone, or city for chart correction — this product path does not "
        "use geolocation-based solar time. Do NOT insist on counterpart birth time; it is optional refinement only."
    )
    return json.dumps(blob, ensure_ascii=False)


@dataclass
class FollowUpToolingResult:
    supplemental_context: str | None
    extra_traces: list[AgentTraceStep]
    ui_event: UIEvent
    partner_intake_requested: bool = False


def _remember_related(state: ConversationState, partner: PersonProfile, partner_saju) -> None:
    if any(p.id == partner.id for p in state.related_people):
        return
    state.related_people.append(partner.model_copy(deep=True))
    state.related_people_saju[partner.id] = partner_saju


def _compat_collection_turn(
    state: ConversationState,
    latest_message: str,
    board,
    traces: list[AgentTraceStep],
    *,
    structured_partner: PartnerCompatibilityPayload | None = None,
) -> FollowUpToolingResult | None:
    pending = state.pending_tool_call
    if pending is None or state.current_stage != "collecting_compatibility_info":
        return None

    if structured_partner is not None:
        partner_dt = structured_partner.birth_date
        partner_name_hint = structured_partner.display_name
    else:
        partner_dt = extract_first_birth_date(latest_message)
        partner_name_hint = _extract_partner_hint_name(latest_message)
    traces.append(
        AgentTraceStep(
            step="tool_call",
            label="Compatibility counterpart intake processed",
            tool_name="counsel.intake.compatibility_partner",
            status="completed",
        ),
    )
    prev = _prior_active_template(board)

    if partner_dt is None:
        collected = dict(pending.collected_inputs or {})
        if partner_name_hint:
            collected["partner_name_hint"] = partner_name_hint
        state.pending_tool_call = pending.model_copy(update={"collected_inputs": collected})
        supplemental = json.dumps(
            {
                "tool": "compatibility_collect",
                "parsed_birth_date": None,
                "instructions": (
                    "The user wants compatibility but no usable birth date was parsed. "
                    "Ask politely for YYYY-MM-DD or yyyy년 m월 d일 format."
                ),
            },
            ensure_ascii=False,
        )
        return FollowUpToolingResult(
            supplemental,
            traces,
            TabRecommendedEvent(type="tab_recommended", recommended_tab="counseling_board"),
            partner_intake_requested=True,
        )

    hint_name = None
    if pending.collected_inputs:
        raw = pending.collected_inputs.get("partner_name_hint")
        if isinstance(raw, str):
            hint_name = raw.strip() or None
    partner_nm = partner_name_hint or hint_name
    if structured_partner is not None:
        partner = _partner_profile(
            state.session_id,
            partner_nm or structured_partner.display_name,
            partner_dt,
            birth_time=structured_partner.birth_time,
            gender=structured_partner.gender,
        )
    else:
        partner = _partner_profile(state.session_id, partner_nm, partner_dt)
    other_saju = analyze_base_saju(partner)
    compat = analyze_compatibility(state.user_saju, other_saju)
    _remember_related(state, partner, other_saju)

    state.current_stage = "open_counseling"
    state.pending_tool_call = None

    rd, supplemental = attach_compatibility_result(board, compat)
    supplemental = _compat_supplement_with_counterpart_facts(supplemental, partner, other_saju)
    if board.active_reading is not None:
        state.readings_by_semantic_key[compat.semantic_key] = board.active_reading

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label=f"analyze_compatibility completed ({compat.semantic_key})",
            tool_name="analyze_compatibility",
            status="completed",
        ),
    )
    ui = TemplateChangedEvent(
        type="template_changed",
        from_template=prev,
        to_template="compatibility_result",
        target_id=rd,
    )
    state.completed_tool_calls.append(
        ToolCallRecord(
            tool_name="analyze_compatibility",
            semantic_key=compat.semantic_key,
            result_summary=compat.summary,
        ),
    )

    return FollowUpToolingResult(supplemental, traces, ui)


def prepare_follow_up_tooling(
    settings: Settings,
    state: ConversationState,
    latest_message: str,
    *,
    structured_partner: PartnerCompatibilityPayload | None = None,
) -> FollowUpToolingResult:
    """LangGraph 멀티-에이전트 그래프를 실행하는 진입점.

    chat_service.py 인터페이스는 유지하면서 내부 오케스트레이션은
    LangGraph 그래프(app.agents.graph)에 위임한다.
    """
    if state.counseling_board is None:
        raise RuntimeError("counseling_board is required.")

    from app.agents.graph import run_counselor_graph  # 순환 임포트 방지

    return run_counselor_graph(
        settings,
        state,
        latest_message,
        structured_partner=structured_partner,
    )
