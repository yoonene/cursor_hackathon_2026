from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.builders.board_builder import build_initial_counseling_board
from app.builders.report_builder import build_saju_report
from app.core.config import get_settings
from app.schemas.intake import StartReadingRequest
from app.schemas.profiles import PersonProfile
from app.schemas.responses import InitialReadingResponse
from app.schemas.state import ConversationMessage, ConversationState, ToolCallRecord
from app.schemas.view_models import AgentTraceStep, ReportInitializedEvent
from app.services.counselor_llm import generate_initial_counseling_copy, stream_initial_counseling_copy
from app.saju.compute_saju import analyze_base_saju
from app.services.session_store import InMemorySessionStore

logger = logging.getLogger("reading_svc")


def _build_response(
    request: StartReadingRequest,
    user_profile: PersonProfile,
    user_saju: Any,
    llm_out: Any,
    llm_status: str,
) -> tuple[InitialReadingResponse, ConversationState]:
    """saju/llm 결과로 응답과 세션 상태를 생성한다."""
    saju_report = build_saju_report(user_profile, user_saju, llm_out)
    counseling_board = build_initial_counseling_board(user_profile, saju_report)
    assistant_message = llm_out.assistant_message

    completed_tool_calls = [
        ToolCallRecord(
            tool_name="analyze_base_saju",
            status="completed",
            result_summary="Computed lunar four-pillars profile and rule-engine signals.",
        ),
    ]
    conversation_state = ConversationState(
        session_id=request.session_id,
        user_profile=user_profile,
        user_saju=user_saju,
        saju_report=saju_report,
        counseling_board=counseling_board,
        messages=[ConversationMessage(role="assistant", content=assistant_message)],
        current_stage="initial_report",
        completed_tool_calls=completed_tool_calls,
        active_topics=[],
        current_focus_key=None,
        thinking_state=None,
    )
    conversation_state.memory.recent_insights.append(saju_report.one_line_verdict)

    agent_trace = [
        AgentTraceStep(
            step="tool_call",
            label="Computed four pillars (lunar-python) + YAML rule signals",
            tool_name="analyze_base_saju",
            status="completed",
        ),
        AgentTraceStep(
            step="llm_call",
            label=f"Drafted counselor copy ({llm_status})",
            tool_name="counselor_llm.initial_reading",
            status="completed" if llm_status == "llm_ok" else "skipped",
        ),
        AgentTraceStep(
            step="view_model",
            label="Built full saju report",
            status="completed",
        ),
    ]

    response = InitialReadingResponse(
        session_id=request.session_id,
        assistant_message=assistant_message,
        current_stage="initial_report",
        recommended_tab="saju_report",
        thinking_state=None,
        saju_report=saju_report,
        counseling_board=counseling_board,
        ui_event=ReportInitializedEvent(type="report_initialized", target_id=saju_report.id),
        agent_trace=agent_trace,
    )
    return response, conversation_state


def _user_profile_id(session_id: str) -> str:
    safe_session_id = session_id.strip().lower().replace("-", "_").replace(" ", "_")
    return f"user_{safe_session_id}"


def build_user_profile(request: StartReadingRequest) -> PersonProfile:
    return PersonProfile(
        id=_user_profile_id(request.session_id),
        display_name=request.display_name,
        birth_date=request.birth_date,
        birth_time=request.birth_time,
        gender=request.gender,
    )


def start_reading(
    request: StartReadingRequest,
    store: InMemorySessionStore,
) -> InitialReadingResponse:
    """인테이크 → 규칙 계산 → LLM 초기 해석 → 스냅샷."""

    settings = get_settings()
    user_profile = build_user_profile(request)

    logger.info(
        "saju calc start — session=%s birth_date=%s",
        request.session_id,
        request.birth_date,
    )
    user_saju = analyze_base_saju(user_profile)
    logger.info(
        "saju calc done — session=%s dominant=%s lacking=%s",
        request.session_id,
        user_saju.dominant_elements,
        user_saju.lacking_elements,
    )

    logger.info("LLM initial reading start — session=%s", request.session_id)
    llm_out, llm_status = generate_initial_counseling_copy(settings, user_profile, user_saju)
    if llm_status == "llm_ok":
        logger.info("LLM initial reading done — session=%s tag=%s", request.session_id, llm_status)
    else:
        logger.warning(
            "LLM initial reading fallback — session=%s tag=%s",
            request.session_id,
            llm_status,
        )

    response, conversation_state = _build_response(request, user_profile, user_saju, llm_out, llm_status)
    store.set(conversation_state)
    logger.info("session created — session=%s", request.session_id)
    return response


async def start_reading_stream(
    request: StartReadingRequest,
    store: InMemorySessionStore,
) -> AsyncIterator[tuple[str, Any]]:
    """스트리밍 버전. SSE 이벤트를 yield한다.

    이벤트:
        ``("prelude", {"session_id": str})``  — 사주 계산 완료 직후
        ``("delta", str)``                    — LLM 텍스트 조각
        ``("complete", InitialReadingResponse)`` — 최종 응답
    """
    settings = get_settings()
    user_profile = build_user_profile(request)

    logger.info(
        "saju calc start (stream) — session=%s birth_date=%s",
        request.session_id,
        request.birth_date,
    )
    user_saju = analyze_base_saju(user_profile)
    logger.info(
        "saju calc done (stream) — session=%s dominant=%s lacking=%s",
        request.session_id,
        user_saju.dominant_elements,
        user_saju.lacking_elements,
    )

    yield "prelude", {"session_id": request.session_id}

    logger.info("LLM initial reading stream start — session=%s", request.session_id)
    llm_out = None
    llm_status = "fallback_llm_failed"

    async for event_type, *event_data in stream_initial_counseling_copy(settings, user_profile, user_saju):
        if event_type == "delta":
            yield "delta", event_data[0]
        elif event_type == "result":
            llm_out, llm_status = event_data[0], event_data[1]

    if llm_status == "llm_ok":
        logger.info("LLM initial reading stream done — session=%s tag=%s", request.session_id, llm_status)
    else:
        logger.warning(
            "LLM initial reading stream fallback — session=%s tag=%s",
            request.session_id,
            llm_status,
        )

    response, conversation_state = _build_response(request, user_profile, user_saju, llm_out, llm_status)
    store.set(conversation_state)
    logger.info("session created (stream) — session=%s", request.session_id)
    yield "complete", response
