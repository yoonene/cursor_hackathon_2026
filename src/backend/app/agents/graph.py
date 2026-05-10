"""LangGraph 멀티-에이전트 그래프 정의 및 실행.

그래프 구조:
    START
      └─ router_node          (상태 복구 + 의도 분류 + 다음 에이전트 결정)
           ├─ collect_partner  → END   (상대 정보 수집 대기)
           ├─ saju_agent       (상대방 사주 계산)
           │    └─ compat_agent → END  (사주 에이전트 결과 받아 궁합 계산)
           ├─ fortune_agent    → END   (영역별 운세)
           ├─ timing_agent     → END   (행동 타이밍)
           └─ END              (general — 도구 없음)

외부에서는 `run_counselor_graph()`만 호출한다.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.agents.graph_state import AgentGraphState
from app.agents.nodes import (
    collect_partner_node,
    compat_agent_node,
    fortune_agent_node,
    router_node,
    saju_agent_node,
    timing_agent_node,
)
from app.schemas.view_models import TabRecommendedEvent


def _route_selector(state: AgentGraphState) -> str:
    """router_node가 설정한 next_node 값으로 다음 에이전트를 선택한다."""
    return state.get("next_node") or "end"


def _build_graph() -> StateGraph:
    g = StateGraph(AgentGraphState)

    # 노드 등록
    g.add_node("router", router_node)
    g.add_node("collect_partner", collect_partner_node)
    g.add_node("saju_agent", saju_agent_node)
    g.add_node("compat_agent", compat_agent_node)
    g.add_node("fortune_agent", fortune_agent_node)
    g.add_node("timing_agent", timing_agent_node)

    # 진입점
    g.set_entry_point("router")

    # 라우터 → 조건 분기
    g.add_conditional_edges(
        "router",
        _route_selector,
        {
            "collect_partner": "collect_partner",
            "saju_agent": "saju_agent",
            "fortune_agent": "fortune_agent",
            "timing_agent": "timing_agent",
            "end": END,
        },
    )

    # saju_agent 완료 후 반드시 compat_agent 실행 (에이전트 간 위임)
    g.add_edge("saju_agent", "compat_agent")

    # 각 터미널 노드 → END
    g.add_edge("compat_agent", END)
    g.add_edge("collect_partner", END)
    g.add_edge("fortune_agent", END)
    g.add_edge("timing_agent", END)

    return g.compile()


# 모듈 로드 시 한 번만 컴파일
_graph = _build_graph()


def run_counselor_graph(settings, conversation_state, message: str, *, structured_partner=None):
    """LangGraph 멀티-에이전트 그래프를 실행하고 FollowUpToolingResult를 반환한다.

    - router_node: 상태 복구 + 의도 분류
    - saju_agent_node: 상대방 사주 계산 (필요 시)
    - compat_agent_node: 사주 에이전트 결과를 받아 궁합 계산
    - fortune/timing_agent_node: 운세·타이밍 계산
    """
    from app.services.followup_pipeline import FollowUpToolingResult  # 순환 임포트 방지

    initial: AgentGraphState = {
        "settings": settings,
        "conversation_state": conversation_state,
        "message": message,
        "structured_partner": structured_partner,
        "intent": None,
        "next_node": "",
        "resolved_partner_birth": None,
        "resolved_partner_name": None,
        "resolved_partner_time": None,
        "resolved_partner_gender": None,
        "partner_profile": None,
        "partner_saju": None,
        "compat_result": None,
        "fortune_result": None,
        "timing_result": None,
        "supplemental_context": None,
        "ui_event": None,
        "partner_intake_requested": False,
        "agent_traces": [],
    }

    result = _graph.invoke(initial)

    ui_event = result.get("ui_event") or TabRecommendedEvent(
        type="tab_recommended", recommended_tab="counseling_board"
    )

    return FollowUpToolingResult(
        supplemental_context=result.get("supplemental_context"),
        extra_traces=result.get("agent_traces") or [],
        ui_event=ui_event,
        partner_intake_requested=bool(result.get("partner_intake_requested", False)),
    )
