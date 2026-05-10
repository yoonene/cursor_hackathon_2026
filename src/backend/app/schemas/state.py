from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.profiles import PersonProfile
from app.schemas.report import SajuReport
from app.schemas.saju import SajuData
from app.schemas.view_models import ActiveReading, CounselingBoard

CurrentStage = Literal[
    "initial_report",
    "open_counseling",
    "collecting_compatibility_info",
    "collecting_tool_inputs",
]


class ToolCallRecord(BaseModel):
    tool_name: str
    semantic_key: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    status: Literal["pending", "completed", "failed"] = "completed"
    result_summary: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PendingToolCall(BaseModel):
    tool_name: str
    semantic_key: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    collected_inputs: dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CounselorMemory(BaseModel):
    user_concerns: list[str] = Field(default_factory=list)
    relationship_context: list[str] = Field(default_factory=list)
    recent_insights: list[str] = Field(default_factory=list)


class ConversationState(BaseModel):
    session_id: str
    user_profile: PersonProfile
    user_saju: SajuData
    saju_report: SajuReport
    counseling_board: CounselingBoard | None = None
    related_people: list[PersonProfile] = Field(default_factory=list)
    related_people_saju: dict[str, SajuData] = Field(default_factory=dict)
    messages: list[ConversationMessage] = Field(default_factory=list)
    current_stage: CurrentStage = "initial_report"
    pending_tool_call: PendingToolCall | None = None
    completed_tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    active_topics: list[str] = Field(default_factory=list)
    readings_by_semantic_key: dict[str, ActiveReading] = Field(default_factory=dict)
    current_focus_key: str | None = None
    memory: CounselorMemory = Field(default_factory=CounselorMemory)
    thinking_state: str | None = None
