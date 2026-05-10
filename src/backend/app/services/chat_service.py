"""Follow-up counselor turns keyed by intake session."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import AsyncIterator

from app.core.config import Settings, get_settings
from app.schemas.requests import ChatRequest
from app.schemas.responses import ChatResponse
from app.schemas.state import ConversationMessage
from app.schemas.view_models import AgentTraceStep, CounselingBoard
from app.services.counselor_llm import generate_followup_counseling_reply, stream_follow_up_counselor_text
from app.services.followup_pipeline import prepare_follow_up_tooling
from app.services.session_store import InMemorySessionStore

logger = logging.getLogger("chat_svc")


def bootstrap_chat_turn(
    store: InMemorySessionStore,
    request: ChatRequest,
    *,
    settings: Settings | None = None,
):
    """Load session; append user message; run tooling router. Returns ``None`` when session missing."""

    if settings is None:
        settings = get_settings()

    baseline = store.get(request.session_id)
    if baseline is None:
        return None

    state = baseline.model_copy(deep=True)
    user_line = request.message.strip()
    if request.partner is not None and not user_line:
        user_line = "(상대 사주 정보 폼 제출)"
    state.messages.append(ConversationMessage(role="user", content=user_line))
    if state.current_stage == "initial_report":
        state.current_stage = "open_counseling"

    tooling = prepare_follow_up_tooling(
        settings,
        state,
        request.message.strip(),
        structured_partner=request.partner,
    )
    return state, tooling, settings


def continue_chat(store: InMemorySessionStore, request: ChatRequest) -> ChatResponse | None:
    """Append user message, run deterministic intent routing/tools, then counselor reply."""

    bootstrap = bootstrap_chat_turn(store, request)
    if bootstrap is None:
        return None

    state, tooling, settings = bootstrap

    logger.info("follow-up LLM start — session=%s", request.session_id)
    t0 = time.perf_counter()
    reply, llm_tag = generate_followup_counseling_reply(
        settings,
        state,
        supplemental_context=tooling.supplemental_context,
    )
    duration_ms = int((time.perf_counter() - t0) * 1000)

    if llm_tag == "llm_ok":
        logger.info(
            "follow-up LLM done — session=%s tag=%s duration_ms=%d",
            request.session_id,
            llm_tag,
            duration_ms,
        )
    else:
        logger.warning(
            "follow-up LLM fallback — session=%s tag=%s duration_ms=%d",
            request.session_id,
            llm_tag,
            duration_ms,
        )

    state.messages.append(ConversationMessage(role="assistant", content=reply))
    thinking = None if llm_tag == "llm_ok" else llm_tag
    state.thinking_state = thinking

    if state.counseling_board is None:
        raise RuntimeError("Session has no counseling_board; call POST /reading/start first.")
    board: CounselingBoard = state.counseling_board

    store.set(state)

    agent_trace = list(tooling.extra_traces)
    agent_trace.append(
        AgentTraceStep(
            step="llm_call",
            label=f"Follow-up counselor turn ({llm_tag})",
            tool_name="counselor_llm.follow_up",
            status="completed" if llm_tag == "llm_ok" else "skipped",
        ),
    )

    return ChatResponse(
        session_id=request.session_id,
        assistant_message=reply,
        current_stage=state.current_stage,
        recommended_tab="counseling_board",
        thinking_state=thinking,
        saju_report=state.saju_report,
        counseling_board=board,
        ui_event=tooling.ui_event,
        agent_trace=agent_trace,
        partner_intake_requested=tooling.partner_intake_requested,
    )


def _sse_pack(event_name: str, payload: dict) -> bytes:
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


async def iterate_continue_chat_sse(store: InMemorySessionStore, request: ChatRequest) -> AsyncIterator[bytes]:
    """Server-Sent Events: prelude (session snapshot after tools), delta tokens, then complete payload."""

    bootstrap = bootstrap_chat_turn(store, request)
    if bootstrap is None:
        return

    state, tooling, settings = bootstrap

    if state.counseling_board is None:
        raise RuntimeError("Session has no counseling_board; call POST /reading/start first.")

    board = state.counseling_board
    prelude = {
        "session_id": request.session_id,
        "current_stage": state.current_stage,
        "recommended_tab": "counseling_board",
        "partner_intake_requested": tooling.partner_intake_requested,
        "saju_report": state.saju_report.model_dump(mode="json"),
        "counseling_board": board.model_dump(mode="json"),
        "ui_event": tooling.ui_event.model_dump(mode="json") if tooling.ui_event else None,
        "tool_agent_trace": [s.model_dump(mode="json") for s in tooling.extra_traces],
    }
    yield _sse_pack("prelude", prelude)

    logger.info("follow-up stream start — session=%s", request.session_id)
    t0 = time.perf_counter()
    accumulated = ""
    llm_tag = "skipped"
    async for kind, payload in stream_follow_up_counselor_text(
        settings,
        state,
        supplemental_context=tooling.supplemental_context,
    ):
        if kind == "delta":
            accumulated += payload
            yield _sse_pack("delta", {"text": payload})
        elif kind == "end":
            llm_tag = payload

    duration_ms = int((time.perf_counter() - t0) * 1000)
    if llm_tag == "llm_ok":
        logger.info(
            "follow-up stream done — session=%s tag=%s duration_ms=%d",
            request.session_id,
            llm_tag,
            duration_ms,
        )
    else:
        logger.warning(
            "follow-up stream fallback — session=%s tag=%s duration_ms=%d",
            request.session_id,
            llm_tag,
            duration_ms,
        )

    assistant_text = accumulated.strip() or "(empty response)"
    state.messages.append(ConversationMessage(role="assistant", content=assistant_text))
    thinking = None if llm_tag == "llm_ok" else llm_tag
    state.thinking_state = thinking
    store.set(state)

    agent_trace = list(tooling.extra_traces)
    agent_trace.append(
        AgentTraceStep(
            step="llm_call",
            label=f"Follow-up counselor turn ({llm_tag}, stream)",
            tool_name="counselor_llm.follow_up_stream",
            status="completed" if llm_tag == "llm_ok" else "skipped",
        ),
    )

    response = ChatResponse(
        session_id=request.session_id,
        assistant_message=assistant_text,
        current_stage=state.current_stage,
        recommended_tab="counseling_board",
        thinking_state=thinking,
        saju_report=state.saju_report,
        counseling_board=board,
        ui_event=tooling.ui_event,
        agent_trace=agent_trace,
        partner_intake_requested=tooling.partner_intake_requested,
    )
    yield _sse_pack("complete", response.model_dump(mode="json"))
