from __future__ import annotations

from typing import Literal

from app.agent.state import CounselingGraphState

RouteName = Literal[
    "general_response_or_clarification",
    "compatibility_pending",
    "run_compatibility",
    "run_domain_fortune",
    "run_favorable_timing",
    "direct_counselor_response",
]


def route_counseling(state: CounselingGraphState) -> RouteName:
    """Placeholder router for the next implementation phase of /chat."""

    routing_decision = state.get("routing_decision")
    if routing_decision in {
        "general_response_or_clarification",
        "compatibility_pending",
        "run_compatibility",
        "run_domain_fortune",
        "run_favorable_timing",
        "direct_counselor_response",
    }:
        return routing_decision
    return "general_response_or_clarification"
