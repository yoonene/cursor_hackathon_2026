from __future__ import annotations

from app.agent.state import CounselingGraphState
from app.schemas.view_models import AgentTraceStep


def _append_trace(state: CounselingGraphState, label: str) -> list[AgentTraceStep]:
    trace = list(state.get("agent_trace", []))
    trace.append(AgentTraceStep(step="graph_node", label=label, status="completed"))
    return trace


def load_session_state(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Loaded session state")}


def append_user_message(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Recorded follow-up user message")}


def extract_context(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Prepared context for counseling router")}


def general_response_or_clarification(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to general counseling or clarification")}


def compatibility_pending(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to compatibility pending collection")}


def run_compatibility(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to compatibility analysis")}


def run_domain_fortune(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to domain fortune analysis")}


def run_favorable_timing(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to favorable timing analysis")}


def direct_counselor_response(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Routed to direct counselor response")}


def build_assistant_message(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Prepared assistant response payload")}


def rebuild_counseling_board(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Rebuilt counseling board snapshot")}


def persist_session(state: CounselingGraphState) -> CounselingGraphState:
    return {"agent_trace": _append_trace(state, "Persisted conversation state")}
