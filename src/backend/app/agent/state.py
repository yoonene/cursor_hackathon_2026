from __future__ import annotations

from typing import TypedDict

from app.schemas.state import ConversationState
from app.schemas.view_models import AgentTraceStep


class CounselingGraphState(TypedDict, total=False):
    """Runtime state passed through the counseling graph."""

    session_id: str
    user_message: str
    conversation: ConversationState
    routing_decision: str
    assistant_message: str
    agent_trace: list[AgentTraceStep]
