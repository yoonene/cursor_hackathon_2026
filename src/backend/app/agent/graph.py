from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    append_user_message,
    build_assistant_message,
    compatibility_pending,
    direct_counselor_response,
    extract_context,
    general_response_or_clarification,
    load_session_state,
    persist_session,
    rebuild_counseling_board,
    run_compatibility,
    run_domain_fortune,
    run_favorable_timing,
)
from app.agent.routing import route_counseling
from app.agent.state import CounselingGraphState


@lru_cache(maxsize=1)
def build_counseling_graph():
    """Create the explicit counseling graph used for follow-up chat turns."""

    graph = StateGraph(CounselingGraphState)

    graph.add_node("load_session_state", load_session_state)
    graph.add_node("append_user_message", append_user_message)
    graph.add_node("extract_context", extract_context)
    graph.add_node("general_response_or_clarification", general_response_or_clarification)
    graph.add_node("compatibility_pending", compatibility_pending)
    graph.add_node("run_compatibility", run_compatibility)
    graph.add_node("run_domain_fortune", run_domain_fortune)
    graph.add_node("run_favorable_timing", run_favorable_timing)
    graph.add_node("direct_counselor_response", direct_counselor_response)
    graph.add_node("build_assistant_message", build_assistant_message)
    graph.add_node("rebuild_counseling_board", rebuild_counseling_board)
    graph.add_node("persist_session", persist_session)

    graph.add_edge(START, "load_session_state")
    graph.add_edge("load_session_state", "append_user_message")
    graph.add_edge("append_user_message", "extract_context")
    graph.add_conditional_edges(
        "extract_context",
        route_counseling,
        {
            "general_response_or_clarification": "general_response_or_clarification",
            "compatibility_pending": "compatibility_pending",
            "run_compatibility": "run_compatibility",
            "run_domain_fortune": "run_domain_fortune",
            "run_favorable_timing": "run_favorable_timing",
            "direct_counselor_response": "direct_counselor_response",
        },
    )

    for node_name in (
        "general_response_or_clarification",
        "compatibility_pending",
        "run_compatibility",
        "run_domain_fortune",
        "run_favorable_timing",
        "direct_counselor_response",
    ):
        graph.add_edge(node_name, "build_assistant_message")

    graph.add_edge("build_assistant_message", "rebuild_counseling_board")
    graph.add_edge("rebuild_counseling_board", "persist_session")
    graph.add_edge("persist_session", END)

    return graph.compile()
