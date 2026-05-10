"""LangGraph 에이전트 노드 함수들.

그래프 흐름:
  router_node
    ├─ collect_partner_node   (상대 정보 수집 대기)
    ├─ saju_agent_node        (상대방 사주 계산)
    │    └─ compat_agent_node (궁합 에이전트 — saju_agent에 의존)
    ├─ fortune_agent_node     (영역별 운세)
    └─ timing_agent_node      (행동 타이밍)

각 노드는 AgentGraphState의 일부 키만 업데이트한 dict를 반환한다.
"""

from __future__ import annotations

import json
import logging
from datetime import date

logger = logging.getLogger("agents.nodes")

from app.agents.graph_state import AgentGraphState
from app.builders.followup_board_updates import (
    attach_compatibility_pending,
    attach_compatibility_result,
    attach_domain_fortune,
    attach_timing,
)
from app.schemas.state import PendingToolCall, ToolCallRecord
from app.schemas.view_models import AgentTraceStep, TabRecommendedEvent, TemplateChangedEvent
from app.services.date_extract import extract_first_birth_date
from app.services.followup_intent_classifier import classify_follow_up_intent
from app.services.followup_pipeline import (
    _compat_supplement_with_counterpart_facts,
    _ensure_compat_intake_coherence,
    _extract_partner_hint_name,
    _partner_profile,
    _prime_state_for_partner_request,
    _prior_active_template,
    _remember_related,
    _user_requests_partner_ui_refresh,
)
from app.saju.compatibility import analyze_compatibility
from app.saju.compute_saju import analyze_base_saju
from app.saju.domain_fortune import analyze_domain_fortune
from app.saju.favorable_timing import analyze_favorable_timing


# ──────────────────────────────────────────────────────────────
# 1. 라우터 에이전트
# ──────────────────────────────────────────────────────────────

def router_node(state: AgentGraphState) -> dict:
    """상태 복구 → 의도 분류 → 다음 에이전트 결정."""
    cs = state["conversation_state"]
    settings = state["settings"]
    message = state["message"]
    structured_partner = state.get("structured_partner")
    board = cs.counseling_board
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])

    # 1-a. 상태 정합성 복구
    _ensure_compat_intake_coherence(cs, board, traces)

    # 1-b. partner 페이로드가 있으면 수집 상태로 강제 정렬
    if structured_partner is not None:
        _prime_state_for_partner_request(cs, board, traces)

    # 1-c. 팝업 재요청 감지 (날짜 없이 "팝업 다시" 등)
    if _user_requests_partner_ui_refresh(message):
        if (
            _prior_active_template(board) == "compatibility_pending"
            and cs.current_stage == "collecting_compatibility_info"
        ):
            partner_birth = (
                structured_partner.birth_date
                if structured_partner
                else extract_first_birth_date(message)
            )
            if partner_birth is None:
                reading = getattr(board, "active_reading", None)
                board_sk = (
                    getattr(reading, "semantic_key", None) or "compatibility:user:partner_pending"
                )
                supplemental = json.dumps(
                    {
                        "tool": "compatibility_pending",
                        "semantic_key": board_sk,
                        "re_prompt_ui": True,
                        "instructions": (
                            "Client asked to reopen the partner intake UI. "
                            "Keep context and politely invite filling the intake again."
                        ),
                    },
                    ensure_ascii=False,
                )
                traces.append(
                    AgentTraceStep(
                        step="routing",
                        label="partner_intake_ui_re_requested",
                        status="completed",
                    ),
                )
                return {
                    "conversation_state": cs,
                    "agent_traces": traces,
                    "supplemental_context": supplemental,
                    "ui_event": TabRecommendedEvent(
                        type="tab_recommended", recommended_tab="counseling_board"
                    ),
                    "partner_intake_requested": True,
                    "next_node": "end",
                }

    # 1-d. 이미 수집 중인 경우 → 데이터 유무에 따라 분기
    if cs.current_stage == "collecting_compatibility_info":
        partner_birth = (
            structured_partner.birth_date
            if structured_partner
            else extract_first_birth_date(message)
        )
        resolved_name = (
            structured_partner.display_name
            if structured_partner
            else _extract_partner_hint_name(message)
        )
        resolved_time = structured_partner.birth_time if structured_partner else None
        resolved_gender = structured_partner.gender if structured_partner else None

        traces.append(
            AgentTraceStep(
                step="tool_call",
                label="Compatibility counterpart intake processed",
                tool_name="counsel.intake.compatibility_partner",
                status="completed",
            )
        )

        if partner_birth is not None:
            return {
                "conversation_state": cs,
                "agent_traces": traces,
                "resolved_partner_birth": partner_birth,
                "resolved_partner_name": resolved_name,
                "resolved_partner_time": resolved_time,
                "resolved_partner_gender": resolved_gender,
                "next_node": "saju_agent",
            }
        # 날짜 미확인 → 다시 수집
        return {
            "conversation_state": cs,
            "agent_traces": traces,
            "next_node": "collect_partner",
        }

    # 1-e. 신규 요청 의도 분류
    intent = classify_follow_up_intent(settings, message)
    logger.info("router_node — route=%s", intent.route)
    traces.append(
        AgentTraceStep(
            step="routing",
            label=f"classified_followup route={intent.route}",
            status="completed",
        )
    )

    if intent.route == "domain_fortune":
        return {
            "conversation_state": cs,
            "intent": intent,
            "agent_traces": traces,
            "next_node": "fortune_agent",
        }

    if intent.route == "favorable_timing":
        return {
            "conversation_state": cs,
            "intent": intent,
            "agent_traces": traces,
            "next_node": "timing_agent",
        }

    if intent.route == "compatibility":
        partner_birth = (
            structured_partner.birth_date
            if structured_partner
            else (intent.partner_birth_date or extract_first_birth_date(message))
        )
        resolved_name = (
            structured_partner.display_name if structured_partner else intent.partner_name
        )
        resolved_time = structured_partner.birth_time if structured_partner else None
        resolved_gender = structured_partner.gender if structured_partner else None

        if partner_birth is not None:
            return {
                "conversation_state": cs,
                "intent": intent,
                "agent_traces": traces,
                "resolved_partner_birth": partner_birth,
                "resolved_partner_name": resolved_name,
                "resolved_partner_time": resolved_time,
                "resolved_partner_gender": resolved_gender,
                "next_node": "saju_agent",
            }
        return {
            "conversation_state": cs,
            "intent": intent,
            "agent_traces": traces,
            "next_node": "collect_partner",
        }

    # general — 도구 없음
    return {
        "conversation_state": cs,
        "intent": intent,
        "agent_traces": traces,
        "supplemental_context": None,
        "ui_event": TabRecommendedEvent(
            type="tab_recommended", recommended_tab="counseling_board"
        ),
        "partner_intake_requested": False,
        "next_node": "end",
    }


# ──────────────────────────────────────────────────────────────
# 2. 상대 정보 수집 노드
# ──────────────────────────────────────────────────────────────

def collect_partner_node(state: AgentGraphState) -> dict:
    """상대방 생년월일이 없을 때 수집 대기 상태를 설정하거나 재요청한다."""
    cs = state["conversation_state"]
    board = cs.counseling_board
    intent = state.get("intent")
    message = state.get("message", "")
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])
    pending = cs.pending_tool_call
    prev = _prior_active_template(board)

    # 이름 힌트가 있으면 수집 입력에 저장
    name_hint = _extract_partner_hint_name(message)
    collected = dict(pending.collected_inputs if pending else {})
    if name_hint:
        collected["partner_name_hint"] = name_hint

    # 이미 pending 상태 → 재요청(날짜 파싱 실패)
    if pending is not None and pending.tool_name == "analyze_compatibility":
        cs.pending_tool_call = pending.model_copy(update={"collected_inputs": collected})
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
        traces.append(
            AgentTraceStep(
                step="tool_call",
                label="Compatibility counterpart intake — date not found, re-prompting",
                tool_name="counsel.intake.compatibility_partner",
                status="completed",
            )
        )
        return {
            "conversation_state": cs,
            "agent_traces": traces,
            "supplemental_context": supplemental,
            "ui_event": TabRecommendedEvent(
                type="tab_recommended", recommended_tab="counseling_board"
            ),
            "partner_intake_requested": True,
        }

    # 최초 수집 — pending 상태 생성 + 보드 카드 생성
    init_collected: dict = {}
    if intent and intent.partner_name:
        init_collected["partner_name_hint"] = intent.partner_name

    cs.current_stage = "collecting_compatibility_info"
    cs.pending_tool_call = PendingToolCall(
        tool_name="analyze_compatibility",
        semantic_key="compatibility:user:partner_pending",
        missing_fields=["counterpart_birth_date"],
        collected_inputs=init_collected,
    )
    rd, _ = attach_compatibility_pending(board, cs.user_profile.display_name)
    if board.active_reading is not None:
        cs.readings_by_semantic_key[cs.pending_tool_call.semantic_key] = board.active_reading

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label="Entered compatibility_pending (await counterpart birth)",
            tool_name="compatibility.await_partner_birth_date",
            status="completed",
        )
    )
    ui = TemplateChangedEvent(
        type="template_changed",
        from_template=prev,
        to_template="compatibility_pending",
        target_id=rd,
    )
    supplemental = json.dumps(
        {
            "tool": "compatibility_pending",
            "semantic_key": cs.pending_tool_call.semantic_key,
            "instructions": (
                "The user wants compatibility but no counterpart birth date is available yet. "
                "Ask warmly for YYYY-MM-DD (or yyyy년 m월 d일) and an optional nickname."
            ),
        },
        ensure_ascii=False,
    )
    return {
        "conversation_state": cs,
        "agent_traces": traces,
        "supplemental_context": supplemental,
        "ui_event": ui,
        "partner_intake_requested": True,
    }


# ──────────────────────────────────────────────────────────────
# 3. 사주 에이전트 — 상대방 원국 계산
# ──────────────────────────────────────────────────────────────

def saju_agent_node(state: AgentGraphState) -> dict:
    """사주 에이전트: 상대방의 사주 원국을 결정론적으로 계산한다.

    라우터로부터 resolved_partner_birth 등을 받아 PersonProfile을 만들고
    analyze_base_saju를 실행한다. 결과는 partner_profile / partner_saju로 저장되며
    이후 compat_agent_node가 이를 받아 궁합을 계산한다.
    """
    cs = state["conversation_state"]
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])

    birth = state.get("resolved_partner_birth")
    name = state.get("resolved_partner_name")
    birth_time = state.get("resolved_partner_time")
    gender = state.get("resolved_partner_gender")

    # 이름 힌트는 pending 수집 입력에도 있을 수 있음
    pending = cs.pending_tool_call
    if name is None and pending and pending.collected_inputs:
        raw = pending.collected_inputs.get("partner_name_hint")
        if isinstance(raw, str):
            name = raw.strip() or None

    if birth is None:
        logger.error("saju_agent_node — resolved_partner_birth missing (session=%s)", cs.session_id)
        raise ValueError("saju_agent_node: resolved_partner_birth is required but missing.")

    partner = _partner_profile(
        cs.session_id, name, birth, birth_time=birth_time, gender=gender
    )
    logger.info("saju_agent_node — computing saju for partner=%s", partner.display_name)
    partner_saju = analyze_base_saju(partner)

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label=f"saju_agent: analyze_base_saju for {partner.display_name}",
            tool_name="saju_agent.analyze_base_saju",
            status="completed",
        )
    )

    return {
        "partner_profile": partner,
        "partner_saju": partner_saju,
        "agent_traces": traces,
    }


# ──────────────────────────────────────────────────────────────
# 4. 궁합 에이전트 — 사주 에이전트 결과를 받아 궁합 분석
# ──────────────────────────────────────────────────────────────

def compat_agent_node(state: AgentGraphState) -> dict:
    """궁합 에이전트: saju_agent가 계산한 상대 사주와 유저 사주로 궁합을 분석한다.

    에이전트 간 협력 흐름:
        라우터 → 사주 에이전트(상대 사주 계산) → 궁합 에이전트(궁합 결과 생성)
    """
    cs = state["conversation_state"]
    board = cs.counseling_board
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])

    partner = state.get("partner_profile")
    partner_saju = state.get("partner_saju")
    if partner is None or partner_saju is None:
        logger.error("compat_agent_node — partner_profile or partner_saju missing (session=%s)", cs.session_id)
        raise ValueError("compat_agent_node: partner_profile and partner_saju are required.")

    prev = _prior_active_template(board)
    logger.info("compat_agent_node — analyzing compatibility (session=%s)", cs.session_id)
    compat = analyze_compatibility(cs.user_saju, partner_saju)
    _remember_related(cs, partner, partner_saju)

    cs.current_stage = "open_counseling"
    cs.pending_tool_call = None

    rd, supplemental = attach_compatibility_result(board, compat)
    supplemental = _compat_supplement_with_counterpart_facts(supplemental, partner, partner_saju)
    if board.active_reading is not None:
        cs.readings_by_semantic_key[compat.semantic_key] = board.active_reading

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label=f"compat_agent: analyze_compatibility ({compat.semantic_key})",
            tool_name="compat_agent.analyze_compatibility",
            status="completed",
        )
    )
    ui = TemplateChangedEvent(
        type="template_changed",
        from_template=prev,
        to_template="compatibility_result",
        target_id=rd,
    )
    cs.completed_tool_calls.append(
        ToolCallRecord(
            tool_name="analyze_compatibility",
            semantic_key=compat.semantic_key,
            result_summary=compat.summary,
        )
    )

    return {
        "conversation_state": cs,
        "compat_result": compat,
        "agent_traces": traces,
        "supplemental_context": supplemental,
        "ui_event": ui,
        "partner_intake_requested": False,
    }


# ──────────────────────────────────────────────────────────────
# 5. 운세 에이전트
# ──────────────────────────────────────────────────────────────

def fortune_agent_node(state: AgentGraphState) -> dict:
    """운세 에이전트: 특정 영역·기간의 운세를 분석한다."""
    cs = state["conversation_state"]
    board = cs.counseling_board
    intent = state.get("intent")
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])

    prev = _prior_active_template(board)
    fd = (intent.fortune_domain if intent else None) or "overall"
    fp = (intent.fortune_period if intent else None) or "this_week"

    logger.info("fortune_agent_node — domain=%s period=%s (session=%s)", fd, fp, cs.session_id)
    res = analyze_domain_fortune(cs.user_saju, fd, fp, date.today())
    rd, supplemental = attach_domain_fortune(board, res)
    if board.active_reading is not None:
        cs.readings_by_semantic_key[res.semantic_key] = board.active_reading

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label=f"fortune_agent: {res.semantic_key}",
            tool_name="fortune_agent.analyze_domain_fortune",
            status="completed",
        )
    )
    ui = TemplateChangedEvent(
        type="template_changed",
        from_template=prev,
        to_template="fortune_flow",
        target_id=rd,
    )
    cs.completed_tool_calls.append(
        ToolCallRecord(
            tool_name="analyze_domain_fortune",
            semantic_key=res.semantic_key,
            result_summary=res.summary,
        )
    )

    return {
        "conversation_state": cs,
        "fortune_result": res,
        "agent_traces": traces,
        "supplemental_context": supplemental,
        "ui_event": ui,
        "partner_intake_requested": False,
    }


# ──────────────────────────────────────────────────────────────
# 6. 타이밍 에이전트
# ──────────────────────────────────────────────────────────────

def timing_agent_node(state: AgentGraphState) -> dict:
    """타이밍 에이전트: 행동 타이밍·최적 시기를 분석한다."""
    cs = state["conversation_state"]
    board = cs.counseling_board
    intent = state.get("intent")
    traces: list[AgentTraceStep] = list(state.get("agent_traces") or [])

    prev = _prior_active_template(board)
    td = (intent.timing_domain if intent else None) or "general"
    at = (intent.action_type if intent else None) or "other"

    logger.info("timing_agent_node — domain=%s action=%s (session=%s)", td, at, cs.session_id)
    res = analyze_favorable_timing(cs.user_saju, td, at, date.today())
    rd, supplemental = attach_timing(board, res)
    if board.active_reading is not None:
        cs.readings_by_semantic_key[res.semantic_key] = board.active_reading

    traces.append(
        AgentTraceStep(
            step="tool_call",
            label=f"timing_agent: {res.semantic_key}",
            tool_name="timing_agent.analyze_favorable_timing",
            status="completed",
        )
    )
    ui = TemplateChangedEvent(
        type="template_changed",
        from_template=prev,
        to_template="timing_recommendation",
        target_id=rd,
    )
    cs.completed_tool_calls.append(
        ToolCallRecord(
            tool_name="analyze_favorable_timing",
            semantic_key=res.semantic_key,
            result_summary=res.summary,
        )
    )

    return {
        "conversation_state": cs,
        "timing_result": res,
        "agent_traces": traces,
        "supplemental_context": supplemental,
        "ui_event": ui,
        "partner_intake_requested": False,
    }
